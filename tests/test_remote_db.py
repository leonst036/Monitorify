import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from monitorify.storage.db import Database
from monitorify.remote.addRemote import add_remote, list_hosts, remove_host, handle_host_action
from monitorify.main import parse_args


class TestRemoteDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.db")
        self.db = Database(self.db_path)
        self.db.connect()

    def tearDown(self):
        self.db.disconnect()
        self.temp_dir.cleanup()

    def test_save_and_get_hosts(self):
        host_id = self.db.save_host(
            ip="192.168.1.100",
            port=2222,
            username="admin",
            password="secretpassword",
            key_filename=None,
        )
        self.assertGreater(host_id, 0)

        hosts = self.db.get_hosts()
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0]["ip"], "192.168.1.100")
        self.assertEqual(hosts[0]["port"], 2222)
        self.assertEqual(hosts[0]["username"], "admin")
        self.assertEqual(hosts[0]["password"], "secretpassword")
        self.assertIsNone(hosts[0]["key_filename"])

    def test_get_and_delete_host(self):
        host_id = self.db.save_host(
            ip="10.0.0.1",
            port=22,
            username="root",
            password=None,
            key_filename="/home/user/.ssh/id_rsa",
        )
        host = self.db.get_host(host_id)
        self.assertIsNotNone(host)
        self.assertEqual(host["ip"], "10.0.0.1")
        self.assertEqual(host["key_filename"], "/home/user/.ssh/id_rsa")

        deleted = self.db.delete_host(host_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.db.get_host(host_id))

    def test_add_remote_interactive_simulation(self):
        inputs = iter(["192.168.1.50", "22", "ubuntu", "", "/path/to/key"])
        with patch("builtins.input", lambda _: next(inputs)):
            with patch("monitorify.remote.addRemote.Database", return_value=self.db):
                host_id = add_remote()
                self.assertGreater(host_id, 0)
                host = self.db.get_host(host_id)
                self.assertEqual(host["ip"], "192.168.1.50")
                self.assertEqual(host["username"], "ubuntu")
                self.assertEqual(host["key_filename"], "/path/to/key")

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


if __name__ == "__main__":
    unittest.main()
