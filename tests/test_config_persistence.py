import asyncio
import json
import os
import tempfile
import unittest

from monitorify import config
from monitorify.config.configManager import configManager
from monitorify.ui.tui.tui import MonitorifyApp


class ConfigManagerPersistenceTest(unittest.TestCase):
    def test_save_and_load_persists_menu_settings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "monitorify.json")
            manager = configManager(config_path)

            manager.save_config({
                "update_interval": 2.5,
                "history_duration": 120.0,
                "visible_widgets": ["cpu_widget", "ram_widget"],
            })

            reloaded = configManager(config_path)
            self.assertEqual(reloaded.get("update_interval"), 2.5)
            self.assertEqual(reloaded.get("history_duration"), 120.0)
            self.assertEqual(reloaded.get("visible_widgets"), ["cpu_widget", "ram_widget"])

    def test_startup_keeps_hidden_widget_state(self):
        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = os.path.join(tmpdir, "monitorify.json")
                with open(config_path, "w", encoding="utf-8") as file:
                    json.dump({
                        "update_interval": 1.0,
                        "history_duration": 60.0,
                        "visible_widgets": ["ram_widget", "programmList_widget", "network_widget", "disk_widget"],
                    }, file)

                original_path = config.CONFIG_PATH
                config.CONFIG_PATH = config_path
                try:
                    app = MonitorifyApp()
                    async with app.run_test() as pilot:
                        self.assertFalse(app.query_one("#cpu_widget").display)
                        with open(config_path, "r", encoding="utf-8") as file:
                            data = json.load(file)
                        self.assertNotIn("cpu_widget", data["visible_widgets"])
                finally:
                    config.CONFIG_PATH = original_path

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
