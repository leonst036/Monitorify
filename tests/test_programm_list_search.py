import unittest
import asyncio
from unittest.mock import patch

from textual.app import App, ComposeResult
from textual.widgets import Input, ListView, ListItem, Static
from monitorify.ui.tui.widgets.programmListWidget import ProgrammListWidget


MOCK_PROCESSES = [
    {"pid": 101, "name": "systemd", "ram_ussage": 15.0, "cpu_ussage": 0.1, "state": "Running", "running_time": "10:00"},
    {"pid": 202, "name": "python3", "ram_ussage": 45.2, "cpu_ussage": 5.4, "state": "Running", "running_time": "02:15"},
    {"pid": 303, "name": "chrome", "ram_ussage": 350.0, "cpu_ussage": 12.0, "state": "Sleeping", "running_time": "01:00"},
    {"pid": 404, "name": "bash", "ram_ussage": 8.0, "cpu_ussage": 0.0, "state": "Sleeping", "running_time": "05:30"},
    {"pid": 505, "name": "python_worker", "ram_ussage": 60.0, "cpu_ussage": 8.0, "state": "Running", "running_time": "00:45"},
]


class SearchTestApp(App):
    CSS_PATH = "../src/monitorify/ui/tui/css/tui.css"
    BINDINGS = [
        ("slash", "search_process"),
    ]

    def compose(self) -> ComposeResult:
        yield ProgrammListWidget(id="programmList_widget")

    def action_search_process(self) -> None:
        try:
            programm_widget = self.query_one(ProgrammListWidget)
            if programm_widget.display:
                search_input = programm_widget.query_one("#proc_search_input", Input)
                search_input.focus()
        except Exception:
            pass


class TestProgrammListSearch(unittest.IsolatedAsyncioTestCase):

    @patch("monitorify.ui.tui.widgets.programmListWidget.get_latest_process_items_data")
    async def test_search_filtering_by_name(self, mock_get_data):
        mock_get_data.return_value = (1, len(MOCK_PROCESSES), list(MOCK_PROCESSES))

        app = SearchTestApp()
        async with app.run_test() as pilot:
            widget = app.query_one(ProgrammListWidget)
            search_input = widget.query_one("#proc_search_input", Input)
            info_static = widget.query_one("#programm_list_info", Static)

            # Initially all 5 processes should be loaded
            self.assertEqual(len(widget.current_sorted_data), 5)
            self.assertIn("Processes: 5", str(info_static.content))

            # Search for 'python'
            search_input.focus()
            await pilot.press("p", "y", "t", "h", "o", "n")
            await pilot.pause()

            # Should match 'python3' and 'python_worker'
            self.assertEqual(len(widget.current_sorted_data), 2)
            names = [d["name"] for d in widget.current_sorted_data]
            self.assertIn("python3", names)
            self.assertIn("python_worker", names)
            self.assertIn("2/5", str(info_static.content))

    @patch("monitorify.ui.tui.widgets.programmListWidget.get_latest_process_items_data")
    async def test_search_filtering_by_pid(self, mock_get_data):
        mock_get_data.return_value = (1, len(MOCK_PROCESSES), list(MOCK_PROCESSES))

        app = SearchTestApp()
        async with app.run_test() as pilot:
            widget = app.query_one(ProgrammListWidget)
            search_input = widget.query_one("#proc_search_input", Input)

            # Search by PID '303'
            search_input.focus()
            await pilot.press("3", "0", "3")
            await pilot.pause()

            self.assertEqual(len(widget.current_sorted_data), 1)
            self.assertEqual(widget.current_sorted_data[0]["pid"], 303)
            self.assertEqual(widget.current_sorted_data[0]["name"], "chrome")

    @patch("monitorify.ui.tui.widgets.programmListWidget.get_latest_process_items_data")
    async def test_escape_clears_search_and_focuses_list(self, mock_get_data):
        mock_get_data.return_value = (1, len(MOCK_PROCESSES), list(MOCK_PROCESSES))

        app = SearchTestApp()
        async with app.run_test() as pilot:
            widget = app.query_one(ProgrammListWidget)
            search_input = widget.query_one("#proc_search_input", Input)
            list_view = widget.query_one(ListView)

            search_input.focus()
            await pilot.press("b", "a", "s", "h")
            await pilot.pause()
            self.assertEqual(len(widget.current_sorted_data), 1)

            # Press Escape: clears query and focuses list_view
            await pilot.press("escape")
            await pilot.pause()

            self.assertEqual(search_input.value, "")
            self.assertEqual(len(widget.current_sorted_data), 5)
            self.assertTrue(list_view.has_focus)

    @patch("monitorify.ui.tui.widgets.programmListWidget.get_latest_process_items_data")
    async def test_slash_and_enter_navigation(self, mock_get_data):
        mock_get_data.return_value = (1, len(MOCK_PROCESSES), list(MOCK_PROCESSES))

        app = SearchTestApp()
        async with app.run_test() as pilot:
            widget = app.query_one(ProgrammListWidget)
            search_input = widget.query_one("#proc_search_input", Input)
            list_view = widget.query_one(ListView)

            # Focus list view
            list_view.focus()
            await pilot.pause()
            self.assertTrue(list_view.has_focus)

            # Press '/' to trigger search focus
            await pilot.press("slash")
            await pilot.pause()
            self.assertTrue(search_input.has_focus)

            # Type and press Enter to return focus to list view
            await pilot.press("c", "h", "r", "o", "m", "e")
            await pilot.press("enter")
            await pilot.pause()

            self.assertTrue(list_view.has_focus)
            self.assertEqual(list_view.index, 0)
            self.assertEqual(len(widget.current_sorted_data), 1)


if __name__ == "__main__":
    unittest.main()
