"""Main NspecTUI application."""

from __future__ import annotations

from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Input, OptionList

from .detail_screen import DetailViewScreen
from .report_screen import ReportScreen
from .state import FollowModeState, NspecData
from .table import NspecTable
from .utils import clean_title
from .widgets import (
    EpicBanner,
    EpicSelector,
    HelpModal,
    MoveStoryModal,
    SearchBar,
    StatusIndicator,
    StoryDetailPanel,
)


class NspecTUI(App):
    """Main TUI application for nspec management."""

    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        dock: top;
        height: 1;
        background: #1a1a2e;
        color: #00d9ff;
        text-style: bold;
    }

    HeaderTitle {
        text-style: bold;
        padding: 0 1;
    }

    #main-container {
        height: 100%;
    }

    #search-container {
        height: 3;
        padding: 0 1;
        display: none;
    }

    #search-container.visible {
        display: block;
    }

    #search-bar {
        width: 100%;
    }

    #content-container {
        height: 1fr;
    }

    #table-container {
        width: 3fr;
        height: 100%;
        border: none;
    }

    NspecTable.compact {
        scrollbar-size: 0 1;
    }

    #detail-container {
        width: 1fr;
        min-width: 35;
        max-width: 45;
        height: 100%;
        border: solid $secondary;
        padding: 1;
        display: none;
    }

    #detail-container.visible {
        display: block;
    }

    #status-bar {
        height: 1;
        padding: 0 1;
        background: $surface-darken-1;
    }

    #epic-banner {
        height: auto;
        padding: 0 1;
        display: none;
    }

    #epic-banner.visible {
        display: block;
        background: #1e3a5f;
    }

    #epic-selector {
        display: none;
        layer: overlay;
        width: 60;
        height: auto;
        max-height: 20;
        padding: 1;
        border: solid $primary;
        background: $surface;
    }

    #epic-selector.visible {
        display: block;
        align: center middle;
    }

    #epic-list {
        height: auto;
        max-height: 15;
    }

    #move-story-modal {
        display: none;
        layer: overlay;
        width: 65;
        height: auto;
        max-height: 22;
        padding: 1;
        border: solid $secondary;
        background: $surface;
    }

    #move-story-modal.visible {
        display: block;
        align: center middle;
    }

    #move-epic-list {
        height: auto;
        max-height: 15;
    }

    NspecTable {
        height: 100%;
    }

    #help-modal {
        display: none;
        layer: overlay;
        width: 60;
        height: auto;
        padding: 1 2;
        border: solid #00d9ff;
        background: #1a1a2e;
    }

    #help-modal.visible {
        display: block;
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "clear_search", "Clear", priority=True),
        Binding("/", "focus_search", "Search"),
        Binding("n", "next_match", "Next"),
        Binding("shift+n", "prev_match", "Prev", key_display="N"),
        Binding("enter", "toggle_details", "Details"),
        Binding("r", "refresh", "Refresh"),
        Binding("e", "set_epic_filter", "Epic Filter"),
        Binding("m", "move_story", "Move"),
        Binding("s", "show_reports", "Reports"),
        Binding("f", "toggle_follow_mode", "Follow"),
        Binding("b", "toggle_compact", "Compact"),
        Binding("h", "show_help", "Help"),
        Binding("question_mark", "toggle_footer", "More", key_display="?"),
    ]

    def __init__(self, docs_root: Path | None = None, project_root: Path | None = None) -> None:
        """Initialize the TUI."""
        super().__init__()
        self.docs_root = docs_root or Path("docs")
        self.project_root = project_root
        self.data = NspecData(self.docs_root, project_root=self.project_root)
        self.search_query = ""
        self.epic_filter: str | None = None
        self.detail_visible = False
        self.last_mtime = 0.0
        self.follow_mode = FollowModeState(project_root=self.project_root)
        self.show_extended_footer = False
        self.compact_table = False
        self.title = "novaspec"

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Vertical(id="main-container"):
            with Container(id="search-container"):
                yield SearchBar(id="search-bar")
            yield EpicBanner(id="epic-banner")
            with Horizontal(id="content-container"):
                with Container(id="table-container"):
                    yield NspecTable(id="nspec-table")
                with Container(id="detail-container"):
                    yield StoryDetailPanel(id="detail-panel")
            with Container(id="status-bar"):
                yield StatusIndicator(id="status-indicator")
        yield EpicSelector(id="epic-selector")
        yield MoveStoryModal(id="move-story-modal")
        yield HelpModal(id="help-modal")
        yield Footer()

    def on_mount(self) -> None:
        """Handle mount - load initial data and start refresh timer."""
        self.load_data()
        self.set_interval(2, self.check_for_changes)

        table = self.query_one("#nspec-table", NspecTable)
        table.focus()
        if table.row_count > 0:
            table.move_cursor(row=0)

    def load_data(self) -> None:
        """Load nspec data and populate table."""
        self.data.load()
        self.last_mtime = self.data.get_mtime()
        self.refresh_table()

    @work(exclusive=True, thread=True)
    def check_for_changes(self) -> None:
        """Check if files have changed and reload if needed."""
        current_mtime = self.data.get_mtime()
        if current_mtime > self.last_mtime:
            self.last_mtime = current_mtime
            self.data.load()
            self.app.call_from_thread(self.refresh_table)

        if self.follow_mode.enabled and self.follow_mode.check_for_changes():
            story_id = self.follow_mode.current_story_id
            if story_id:
                self.app.call_from_thread(self._follow_mode_navigate, story_id)

    def _follow_mode_navigate(self, story_id: str) -> None:
        """Navigate to story in follow mode (called from thread)."""
        if self.data.datasets:
            fr = self.data.datasets.get_fr(story_id)
            if not fr:
                if story_id in self.data.datasets.completed_frs:
                    self.notify(f"Story {story_id} completed! Follow mode continues.", timeout=3)
                else:
                    self.notify(f"Story {story_id} not found", severity="warning", timeout=2)
                return

        while len(self.screen_stack) > 1:
            self.pop_screen()
        self._open_detail_view(story_id)
        self.notify(f"Following -> Story {story_id}", timeout=2)

    def refresh_table(self) -> None:
        """Refresh the table display."""
        if len(self.screen_stack) > 1:
            return

        try:
            table = self.query_one("#nspec-table", NspecTable)
            viewport_width = self.console.size.width
            count = table.populate(self.data, self.search_query, self.epic_filter, viewport_width)
            self._update_status_bar(count)

            if self.data.error:
                self.notify(f"Error: {self.data.error}", severity="error")
        except Exception:
            pass

    def _update_status_bar(self, count: int | None = None) -> None:
        """Update status bar with current state."""
        try:
            if count is None:
                table = self.query_one("#nspec-table", NspecTable)
                count = table.row_count

            status = self.query_one("#status-indicator", StatusIndicator)
            status.update_status(
                count,
                self.epic_filter,
                follow_mode=self.follow_mode.enabled,
                follow_story=self.follow_mode.current_story_id,
            )
        except Exception:
            pass

    def _is_search_focused(self) -> bool:
        """Check if the search bar currently has focus."""
        try:
            search = self.query_one("#search-bar", SearchBar)
            return search.has_focus
        except Exception:
            return False

    def action_quit(self) -> None:
        """Quit the application."""
        if self._is_search_focused():
            return
        self.exit()

    def action_focus_search(self) -> None:
        """Focus the search bar."""
        container = self.query_one("#search-container", Container)
        container.add_class("visible")
        search = self.query_one("#search-bar", SearchBar)
        search.focus()

    def action_clear_search(self) -> None:
        """Clear search/epic filter and return to table."""
        if len(self.screen_stack) > 1:
            self.pop_screen()
            return

        try:
            move_modal = self.query_one("#move-story-modal", MoveStoryModal)
            if "visible" in move_modal.classes:
                move_modal.remove_class("visible")
                table = self.query_one("#nspec-table", NspecTable)
                table.focus()
                return
        except Exception:
            pass

        try:
            selector = self.query_one("#epic-selector", EpicSelector)
            if "visible" in selector.classes:
                selector.remove_class("visible")
                table = self.query_one("#nspec-table", NspecTable)
                table.focus()
                return
        except Exception:
            pass

        if self.epic_filter:
            self.action_set_epic_filter()
            return

        try:
            search = self.query_one("#search-bar", SearchBar)
            search.value = ""
            self.search_query = ""
            container = self.query_one("#search-container", Container)
            container.remove_class("visible")
            self.refresh_table()
            table = self.query_one("#nspec-table", NspecTable)
            table.focus()
        except Exception:
            pass

    def action_next_match(self) -> None:
        """Jump to next search match."""
        if self._is_search_focused():
            return
        table = self.query_one("#nspec-table", NspecTable)
        if table.row_count > 0:
            current = table.cursor_row
            next_row = (current + 1) % table.row_count
            table.move_cursor(row=next_row)

    def action_prev_match(self) -> None:
        """Jump to previous search match."""
        if self._is_search_focused():
            return
        table = self.query_one("#nspec-table", NspecTable)
        if table.row_count > 0:
            current = table.cursor_row
            prev_row = (current - 1) % table.row_count
            table.move_cursor(row=prev_row)

    def action_toggle_details(self) -> None:
        """Open full-screen detail view for selected story."""
        table = self.query_one("#nspec-table", NspecTable)
        if table.row_count == 0:
            self.notify("No stories to view", severity="warning", timeout=2)
            return

        row_key = table.cursor_row
        if row_key is None:
            return

        row_data = table.get_row_at(row_key)
        if not row_data:
            return

        story_id = str(row_data[0])
        self._open_detail_view(story_id)

    def _open_detail_view(self, story_id: str) -> None:
        """Open the detail view screen for a story."""
        fr = None
        impl = None

        if self.data.datasets:
            fr = self.data.datasets.get_fr(story_id)
            impl = self.data.datasets.get_impl(story_id)

            if not fr and story_id in self.data.datasets.completed_frs:
                fr = self.data.datasets.completed_frs[story_id]
            if not impl and story_id in self.data.datasets.completed_impls:
                impl = self.data.datasets.completed_impls[story_id]

        if not fr:
            self.notify(f"Story {story_id} not found", severity="error", timeout=2)
            return

        is_follow_target = (
            self.follow_mode.enabled and self.follow_mode.current_story_id == story_id
        )

        screen = DetailViewScreen(
            story_id=story_id,
            fr=fr,
            impl=impl,
            data=self.data,
            is_follow_target=is_follow_target,
        )
        self.push_screen(screen)

    def action_refresh(self) -> None:
        """Manual refresh."""
        if self._is_search_focused():
            return
        self.load_data()
        self.notify("Refreshed", timeout=1)

    def action_set_epic_filter(self) -> None:
        """Show epic selector."""
        if self._is_search_focused():
            return

        # Pop back to main screen if in detail/report view
        while len(self.screen_stack) > 1:
            self.pop_screen()

        selector = self.query_one("#epic-selector", EpicSelector)

        if selector.has_class("visible"):
            selector.remove_class("visible")
            table = self.query_one("#nspec-table", NspecTable)
            table.focus()
            return

        priority_rank = {"E0": 0, "E1": 1, "E2": 2, "E3": 3}
        epics: list[tuple[str, str, int, str]] = []
        if self.data.datasets:
            for story_id, fr in self.data.datasets.active_frs.items():
                if fr.priority.startswith("E"):
                    count = len(fr.deps) if fr.deps else 0
                    title = clean_title(fr.title)
                    epics.append((story_id, title, count, fr.priority))

        nspec_order = {sid: idx for idx, sid in enumerate(self.data.ordered_stories)}
        epics.sort(key=lambda x: (priority_rank.get(x[3], 9), nspec_order.get(x[0], 9999)))

        selector.set_epics(epics)
        selector.add_class("visible")
        option_list = selector.query_one("#epic-list", OptionList)
        option_list.focus()
        if option_list.option_count > 1:
            option_list.highlighted = 1
        elif option_list.option_count > 0:
            option_list.highlighted = 0

    def action_show_reports(self) -> None:
        """Show the reports screen."""
        if self._is_search_focused():
            return
        self.push_screen(ReportScreen(self.docs_root))

    def action_toggle_follow_mode(self) -> None:
        """Toggle Claude Follow Mode."""
        if self._is_search_focused():
            return

        self.follow_mode.enabled = not self.follow_mode.enabled

        if self.follow_mode.enabled:
            story_id = self.follow_mode.read_current_story()
            if story_id:
                self.follow_mode.current_story_id = story_id
                self.follow_mode.last_current_story_mtime = (
                    self.follow_mode.current_story_file.stat().st_mtime
                    if self.follow_mode.current_story_file.exists()
                    else 0.0
                )
                self._open_detail_view(story_id)
                self.notify(f"Follow mode ON - Story {story_id}", timeout=2)
            else:
                self.notify("Follow mode ON - No active story", severity="warning", timeout=2)
        else:
            self.notify("Follow mode OFF", timeout=1)

        self._update_status_bar()

    def action_toggle_footer(self) -> None:
        """Toggle between normal and extended footer bindings."""
        if self._is_search_focused():
            return
        # Footer toggle not implemented with built-in Footer
        pass

    def action_toggle_compact(self) -> None:
        """Toggle compact table mode (borderless)."""
        if self._is_search_focused():
            return
        self.compact_table = not self.compact_table
        try:
            table = self.query_one("#nspec-table", NspecTable)
            container = self.query_one("#table-container", Container)
            if self.compact_table:
                table.add_class("compact")
                container.add_class("compact")
            else:
                table.remove_class("compact")
                container.remove_class("compact")
        except Exception:
            pass

    def action_show_help(self) -> None:
        """Toggle help modal."""
        try:
            modal = self.query_one("#help-modal", HelpModal)
            if modal.has_class("visible"):
                modal.remove_class("visible")
                table = self.query_one("#nspec-table", NspecTable)
                table.focus()
            else:
                modal.add_class("visible")
        except Exception:
            pass

    def action_move_story(self) -> None:
        """Show move story modal."""
        if self._is_search_focused():
            return
        modal = self.query_one("#move-story-modal", MoveStoryModal)

        if modal.has_class("visible"):
            modal.remove_class("visible")
            table = self.query_one("#nspec-table", NspecTable)
            table.focus()
            return

        table = self.query_one("#nspec-table", NspecTable)
        if table.row_count == 0:
            self.notify("No stories to move", severity="warning", timeout=2)
            return

        row_key = table.cursor_row
        if row_key is None:
            self.notify("No story selected", severity="warning", timeout=2)
            return

        row_data = table.get_row_at(row_key)
        if not row_data:
            return

        story_id = str(row_data[0])
        story_title = str(row_data[6])

        if self.data.datasets:
            fr = self.data.datasets.get_fr(story_id)
            if fr and fr.priority.startswith("E"):
                self.notify("Cannot move epics", severity="warning", timeout=2)
                return

        current_epic: str | None = None
        if self.data.datasets:
            for epic_id, epic_fr in self.data.datasets.active_frs.items():
                if epic_fr.priority.startswith("E") and story_id in epic_fr.deps:
                    current_epic = epic_id
                    break

        priority_rank = {"E0": 0, "E1": 1, "E2": 2, "E3": 3}
        epics: list[tuple[str, str, int, str]] = []
        if self.data.datasets:
            for epic_id, fr in self.data.datasets.active_frs.items():
                if fr.priority.startswith("E"):
                    count = len(fr.deps) if fr.deps else 0
                    title = clean_title(fr.title)
                    epics.append((epic_id, title, count, fr.priority))

        nspec_order = {sid: idx for idx, sid in enumerate(self.data.ordered_stories)}
        epics.sort(key=lambda x: (priority_rank.get(x[3], 9), nspec_order.get(x[0], 9999)))

        modal.set_story(story_id, story_title)
        modal.set_epics(epics, current_epic)
        modal.add_class("visible")
        option_list = modal.query_one("#move-epic-list", OptionList)
        option_list.focus()
        if option_list.option_count > 0:
            option_list.highlighted = 0

    def _apply_epic_filter(self, epic_id: str | None) -> None:
        """Apply epic filter and update UI."""
        self.epic_filter = epic_id

        banner = self.query_one("#epic-banner", EpicBanner)
        if epic_id and self.data.datasets:
            fr = self.data.datasets.get_fr(epic_id)
            if fr:
                title = clean_title(fr.title)
                scope = self._get_epic_scope(epic_id)
                banner.show_epic(epic_id, title, len(scope) - 1)
                banner.add_class("visible")
        else:
            banner.hide()
            banner.remove_class("visible")

        self.refresh_table()

    def _get_epic_scope(self, epic_id: str) -> set[str]:
        """Get the epic and its direct dependencies (no transitive traversal).

        Stories should only appear under their direct parent epic,
        not under grandparent epics.
        """
        result = {epic_id}
        fr = self.data.datasets.get_fr(epic_id) if self.data.datasets else None
        if fr and fr.deps:
            result.update(fr.deps)
        return result

    @on(Input.Changed, "#search-bar")
    def handle_search_change(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        self.search_query = event.value
        self.refresh_table()

    @on(Input.Submitted, "#search-bar")
    def handle_search_submit(self, event: Input.Submitted) -> None:
        """Handle search submission - focus table."""
        table = self.query_one("#nspec-table", NspecTable)
        table.focus()

    @on(NspecTable.StorySelected)
    def handle_story_selected(self, event: NspecTable.StorySelected) -> None:
        """Handle story selection - navigate to epic or open detail view."""
        story_id = event.story_id

        # Check if selected story is an epic
        is_epic = False
        if self.data.datasets:
            fr = self.data.datasets.get_fr(story_id)
            if fr and fr.priority.startswith("E"):
                is_epic = True

        # If it's an epic and different from current filter, navigate to it
        if is_epic and story_id != self.epic_filter:
            # Clear search query so epic filter works correctly
            self.search_query = ""
            search_bar = self.query_one("#search-bar", SearchBar)
            search_bar.value = ""
            self._apply_epic_filter(story_id)
            self.notify(f"Navigated to Epic {story_id}", timeout=2)
        else:
            # Same epic or not an epic - show detail
            self._open_detail_view(story_id)

    @on(DataTable.RowHighlighted)
    def handle_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlight (cursor movement)."""
        if self.detail_visible and event.row_key:
            self._update_detail_panel(str(event.row_key.value))

    @on(EpicSelector.EpicSelected)
    def handle_epic_selected(self, event: EpicSelector.EpicSelected) -> None:
        """Handle epic selection from selector."""
        selector = self.query_one("#epic-selector", EpicSelector)
        selector.remove_class("visible")
        self._apply_epic_filter(event.epic_id)
        table = self.query_one("#nspec-table", NspecTable)
        table.focus()

        if event.epic_id:
            self.notify(f"Filtered to Epic {event.epic_id}", timeout=2)
        else:
            self.notify("Showing all stories", timeout=1)

    @on(MoveStoryModal.StoryMoved)
    def handle_story_moved(self, event: MoveStoryModal.StoryMoved) -> None:
        """Handle story moved from modal."""
        from nspec.operations import move_story

        modal = self.query_one("#move-story-modal", MoveStoryModal)
        modal.remove_class("visible")

        result = move_story(event.story_id, event.target_epic, self.docs_root)

        if result.success:
            self.load_data()

            msg = f"Moved {event.story_id} to Epic {event.target_epic}"
            if result.removed_from:
                msg += f" (from {', '.join(result.removed_from)})"
            if result.priority_bumped:
                msg += f" [priority -> {result.priority_bumped}]"

            self.notify(msg, timeout=3)
        else:
            self.notify(f"Move failed: {result.error}", severity="error", timeout=4)

        table = self.query_one("#nspec-table", NspecTable)
        table.focus()

    def _update_detail_panel(self, story_id: str) -> None:
        """Update the detail panel with story info."""
        panel = self.query_one("#detail-panel", StoryDetailPanel)
        if self.data.datasets:
            fr = self.data.datasets.get_fr(story_id)
            impl = self.data.datasets.get_impl(story_id)
            panel.show_story(story_id, fr, impl)
        else:
            panel.clear_story()


def main(docs_root: Path | None = None, project_root: Path | None = None) -> None:
    """Run the TUI application."""
    app = NspecTUI(docs_root=docs_root, project_root=project_root)
    app.run()
