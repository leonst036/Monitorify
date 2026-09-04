import unittest
from textual.widgets import Select, SelectionList
from monitorify.ui.tui.tui import MonitorifyApp


class TestMenuIntegration(unittest.IsolatedAsyncioTestCase):

    async def test_menu_hotkey_and_geometry(self):
        called = []
        app = MonitorifyApp()
        app.connect_to_remote = lambda host_id: called.append(host_id)
        async with app.run_test(size=(80, 24)) as pilot:
            # Verify hotkey 'm' opens the menu from startup
            await pilot.press("m")
            await pilot.pause()
            menu = app.query_one("Menu")
            self.assertTrue(menu.display, "Menu should be displayed after pressing 'm'")

            # Verify geometry fits within 24 rows
            rem_select = app.query_one("#remote_select", Select)
            bottom_y = rem_select.region.y + rem_select.region.height
            self.assertLessEqual(bottom_y, 24, "Remote select must fit within screen height")

            # Verify remote selection
            rem_select.value = "3"
            await pilot.pause(0.1)
            self.assertEqual(called, [3])

            # Verify hotkey 'm' closes the menu
            await pilot.press("m")
            await pilot.pause()
            self.assertFalse(menu.display, "Menu should be hidden after pressing 'm' again")

    async def test_menu_options_change(self):
        app = MonitorifyApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("m")
            await pilot.pause()

            # Test changing update interval
            int_select = app.query_one("#interval_select", Select)
            int_select.value = 2.0
            await pilot.pause()
            self.assertEqual(app.update_interval, 2.0)

            # Test widget toggling
            sel_list = app.query_one(SelectionList)
            sel_list.deselect("CPU")
            await pilot.pause()
            self.assertNotIn("CPU", sel_list.selected)
            self.assertFalse(app.query_one("#cpu_widget").display)

    async def test_remote_session_exit_terminates_app(self):
        from contextlib import nullcontext
        from unittest.mock import patch

        app = MonitorifyApp()
        async with app.run_test(size=(80, 24)) as pilot:
            with patch.object(app, "suspend", return_value=nullcontext()):
                with patch("monitorify.remote.connector.connect_and_run", return_value=True):
                    app.connect_to_remote(3)
                    await pilot.pause(0.1)
                    self.assertFalse(app.is_running, "App should terminate after remote session ends")

    async def test_remote_session_failure_resumes_app(self):
        from contextlib import nullcontext
        from unittest.mock import patch

        app = MonitorifyApp()
        async with app.run_test(size=(80, 24)) as pilot:
            with patch.object(app, "suspend", return_value=nullcontext()):
                with patch("monitorify.remote.connector.connect_and_run", return_value=False):
                    app.connect_to_remote(3)
                    await pilot.pause(0.1)
                    self.assertTrue(app.is_running, "App should keep running if remote connection failed")
