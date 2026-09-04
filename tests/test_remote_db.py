import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from monitorify.storage.db import Database
from monitorify.remote.addRemote import add_remote, list_hosts, remove_host, handle_host_action
from monitorify.main import parse_args
from monitorify.remote.connector import RemoteConnector, connect_and_run
from monitorify.storage import keyring_helper


class TestRemoteDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.db")
        self.db = Database(self.db_path)
        self.db.connect()

        self._keyring_store = {}
        self._patch_set = patch(
            "monitorify.storage.keyring_helper.set_host_password",
            side_effect=lambda hid, pwd: self._keyring_store.__setitem__(hid, pwd) or True,
        )
        self._patch_get = patch(
            "monitorify.storage.keyring_helper.get_host_password",
            side_effect=lambda hid: self._keyring_store.get(hid),
        )
        self._patch_del = patch(
            "monitorify.storage.keyring_helper.delete_host_password",
            side_effect=lambda hid: bool(self._keyring_store.pop(hid, None)),
        )
        self._patch_set.start()
        self._patch_get.start()
        self._patch_del.start()

    def tearDown(self):
        self._patch_set.stop()
        self._patch_get.stop()
        self._patch_del.stop()
        self.db.disconnect()
        self.temp_dir.cleanup()

    def test_file_permissions(self):
        db_mode = stat.S_IMODE(os.stat(self.db_path).st_mode)
        dir_mode = stat.S_IMODE(os.stat(self.temp_dir.name).st_mode)
        self.assertEqual(db_mode, 0o600)
        self.assertEqual(dir_mode, 0o700)

    def test_save_and_get_hosts(self):
        host_id = self.db.save_host(
            ip="192.168.1.100",
            port=2222,
            username="admin",
            password="secretpassword",
            key_filename=None,
        )
        self.assertGreater(host_id, 0)

        # Verify password is NOT stored in plain text SQLite table
        cursor = self.db._connection.cursor()
        cursor.execute("SELECT password FROM hosts WHERE id = ?", (host_id,))
        row = cursor.fetchone()
        self.assertIsNone(row["password"])

        # Verify password is in keyring store
        self.assertEqual(self._keyring_store[host_id], "secretpassword")

        hosts = self.db.get_hosts()
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0]["ip"], "192.168.1.100")
        self.assertEqual(hosts[0]["port"], 2222)
        self.assertEqual(hosts[0]["username"], "admin")
        self.assertEqual(hosts[0]["password"], "secretpassword")
        self.assertIsNone(hosts[0]["key_filename"])

    def test_legacy_password_migration(self):
        # Insert host directly with plaintext password in SQLite
        cursor = self.db._connection.cursor()
        cursor.execute(
            "INSERT INTO hosts (ip, port, username, password, key_filename) VALUES (?, ?, ?, ?, ?)",
            ("10.0.0.99", 22, "legacy_user", "legacy_plain_pass", None),
        )
        self.db._connection.commit()
        legacy_id = cursor.lastrowid

        # Fetch host to trigger migration
        host = self.db.get_host(legacy_id)
        self.assertEqual(host["password"], "legacy_plain_pass")
        self.assertEqual(self._keyring_store.get(legacy_id), "legacy_plain_pass")

        # Verify SQLite row was cleared
        cursor.execute("SELECT password FROM hosts WHERE id = ?", (legacy_id,))
        self.assertIsNone(cursor.fetchone()["password"])

    def test_get_and_delete_host(self):
        host_id = self.db.save_host(
            ip="10.0.0.1",
            port=22,
            username="root",
            password="pwd",
            key_filename="/home/user/.ssh/id_rsa",
        )
        host = self.db.get_host(host_id)
        self.assertIsNotNone(host)
        self.assertEqual(host["ip"], "10.0.0.1")
        self.assertEqual(host["key_filename"], "/home/user/.ssh/id_rsa")
        self.assertEqual(host["password"], "pwd")

        deleted = self.db.delete_host(host_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.db.get_host(host_id))
        self.assertNotIn(host_id, self._keyring_store)

    def test_add_remote_interactive_simulation(self):
        inputs = iter(["192.168.1.50", "22", "ubuntu", "/path/to/key"])
        with patch("builtins.input", lambda _: next(inputs)):
            with patch("getpass.getpass", return_value=""):
                with patch("monitorify.remote.addRemote.Database", return_value=self.db):
                    host_id = add_remote()
                    self.assertGreater(host_id, 0)
                    host = self.db.get_host(host_id)
                    self.assertEqual(host["ip"], "192.168.1.50")
                    self.assertEqual(host["username"], "ubuntu")
                    self.assertEqual(host["key_filename"], "/path/to/key")

    def test_add_remote_empty_ip(self):
        with patch("builtins.input", return_value="   "):
            host_id = add_remote(db=self.db)
            self.assertEqual(host_id, -1)

    def test_add_remote_key_expansion(self):
        host_id = add_remote(
            ip="1.2.3.4",
            port=22,
            username="test",
            key_filename="~/.ssh/test_key",
            db=self.db,
        )
        host = self.db.get_host(host_id)
        self.assertFalse(host["key_filename"].startswith("~"))

    def test_remote_connector_init_expansion(self):
        connector = RemoteConnector(
            host="1.2.3.4",
            key_filename="~/.ssh/test_key",
            timeout=5.0,
        )
        self.assertEqual(connector.timeout, 5.0)
        self.assertFalse(connector.key_filename.startswith("~"))

    def test_connect_and_run_connection_error(self):
        with patch.object(RemoteConnector, "connect", side_effect=ConnectionError("Auth failed")):
            success = connect_and_run(host="10.0.0.1", port=22, pause_on_exit=False)
            self.assertFalse(success)

    def test_connect_and_run_keyboard_interrupt(self):
        with patch.object(RemoteConnector, "connect", side_effect=KeyboardInterrupt):
            success = connect_and_run(host="10.0.0.1", port=22, pause_on_exit=False)
            self.assertFalse(success)

    def test_list_hosts(self):
        self.db.save_host(ip="192.168.1.10", port=22, username="root")
        hosts = list_hosts(db=self.db)
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0]["ip"], "192.168.1.10")

    def test_remove_host(self):
        host_id = self.db.save_host(ip="192.168.1.20", port=22, username="root")
        result = remove_host(host_id=host_id, db=self.db)
        self.assertTrue(result)
        self.assertIsNone(self.db.get_host(host_id))

    def test_handle_host_action_add(self):
        with patch("monitorify.remote.addRemote.Database", return_value=self.db):
            with patch("sys.argv", ["monitorify", "--host", "add", "--ip", "10.10.10.10", "--port", "22", "--username", "user", "--password", "pass"]):
                args = parse_args()
                self.assertEqual(args.host, "add")
                self.assertEqual(args.ip, "10.10.10.10")
                handle_host_action("add", args)

                hosts = self.db.get_hosts()
                self.assertEqual(len(hosts), 1)
                self.assertEqual(hosts[0]["ip"], "10.10.10.10")
                self.assertEqual(hosts[0]["username"], "user")
                self.assertEqual(hosts[0]["password"], "pass")


class TestKeyringHelper(unittest.TestCase):
    def test_keyring_helper_error_resilience(self):
        with patch("keyring.set_password", side_effect=Exception("DBus error")):
            saved = keyring_helper.set_host_password(999, "pwd")
            self.assertFalse(saved)

        with patch("keyring.get_password", side_effect=Exception("DBus error")):
            pwd = keyring_helper.get_host_password(999)
            self.assertIsNone(pwd)

        with patch("keyring.delete_password", side_effect=Exception("DBus error")):
            deleted = keyring_helper.delete_host_password(999)
            self.assertFalse(deleted)


if __name__ == "__main__":
    unittest.main()
