from __future__ import annotations

import click
import os
import re
from dataclasses import dataclass

import frontmatter
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import (
    DataTable,
    Footer,
    Input,
    Static,
    Tab,
    Tabs,
)

from skget.settings import AgentConfig, get_agents
from skget.skills import (
    LOCAL_LABEL_SUFFIX,
    skills,
    skills_install,
    skills_list,
    skills_uninstall,
)

LOGO = r"""
███████╗██╗  ██╗ ██████╗ ███████╗████████╗
██╔════╝██║ ██╔╝██╔════╝ ██╔════╝╚══██╔══╝
███████╗█████╔╝ ██║  ███╗█████╗     ██║   
╚════██║██╔═██╗ ██║   ██║██╔══╝     ██║   
███████║██║  ██╗╚██████╔╝███████╗   ██║   
╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   
"""


class SkillsTable(DataTable):
    BINDINGS = DataTable.BINDINGS + [
        Binding("j", "cursor_down", "Down", show=True),
        Binding("k", "cursor_up", "Up", show=True),
        Binding("d", "page_down", "Page down", show=True),
        Binding("u", "page_up", "Page up", show=True),
    ]


class SkgetApp(App):
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Screen {
        background: $surface;
    }

    #header {
        text-style: bold;
        text-align: center;
        color: $primary;
        background: $boost;
        height: auto;
    }

    DataTable {
        height: 1fr;
        padding: 1 2;
    }

    #search-bar {
        height: 3;
        padding: 0 2;
        display: none;
    }

    #skills-tabs {
        height: 3;
        padding: 0 2;
        display: none;
    }

    #skill-info {
        height: auto;
        padding: 1 2;
        color: $text;
        background: $panel;
        display: none;
    }
    """

    BINDINGS = [
        Binding("enter", "select_row", "Select", show=False, priority=True),
        Binding("space", "select_row_alt", "Select", show=True, priority=True),
        Binding("escape", "go_back", "Back", show=False),
        Binding("backspace", "go_back_alt", "Back", show=True),
        Binding("/", "focus_search", "Search", show=True),
        Binding("tab", "cycle_tab", "Tab", show=True, priority=True),
        Binding("shift+tab", "cycle_tab_reverse", "Tab Back", show=False, priority=True),
        ("q", "quit", "Quit"),
        ("ctrl+q", "ignore", ""),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(
                LOGO,
                id="header",
            )
            yield Tabs(
                Tab("Skills", id="skills"),
                Tab("Installed", id="installed"),
                id="skills-tabs",
            )
            yield Input(placeholder="Press / to search", id="search-bar")
            yield Static("", id="skill-info")
            yield SkillsTable(id="main-table")
            yield Footer()

    def on_mount(self) -> None:
        self.view_stack: list[str] = []
        self.current_skill: str | None = None
        self.current_skill_path: str | None = None
        self.current_skill_destinations: list[str] | None = None
        self.skill_destinations: dict[str, list[str]] = {}
        self.pending_action: tuple[str, str, str] | None = None
        self.all_skills_data: list[tuple[str, str, list[str]]] = []
        self.active_tab: str = "skills"
        self._show_skills_view()

    def _show_skills_view(self, refresh: bool = False) -> None:
        if not refresh:
            self.view_stack.append("skills")
        self.current_skill = None

        # Load all skills data
        self.all_skills_data = list(skills_list())
        self.skill_destinations.clear()
        for skill_name, _, destinations in self.all_skills_data:
            self.skill_destinations[skill_name] = destinations

        # Show search bar
        search_bar = self.query_one("#search-bar", Input)
        search_bar.value = ""
        search_bar.styles.display = "block"
        tabs = self.query_one("#skills-tabs", Tabs)
        tabs.styles.display = "block"
        tabs.active = self.active_tab
        self.query_one("#skill-info", Static).styles.display = "none"

        # Populate table
        self._filter_skills("", focus_table=True)

    def _filter_skills(self, search_query: str, focus_table: bool = False) -> None:
        table = self.query_one("#main-table", DataTable)
        table.clear(columns=True)
        table.add_columns("skill", "installed", "path")
        table.cursor_type = "row"
        self.row_key_to_skill: dict[str, str] = {}
        self.row_key_to_path: dict[str, str] = {}
        self.row_key_to_destinations: dict[str, list[str]] = {}

        search_lower = search_query.lower()
        for skill_name, skill_path, destinations in self.all_skills_data:
            if search_lower and not (
                search_lower in skill_name.lower()
                or search_lower in skill_path.lower()
            ):
                continue
            if self.active_tab == "installed" and not destinations:
                continue
            installed = ", ".join(destinations) if destinations else "-"
            row_key = f"{skill_name}::{skill_path}"
            self.row_key_to_skill[row_key] = skill_name
            self.row_key_to_path[row_key] = skill_path
            self.row_key_to_destinations[row_key] = destinations
            table.add_row(skill_name, installed, skill_path, key=row_key)

        if table.row_count > 0:
            table.move_cursor(row=0)

        if focus_table:
            table.focus()

    def _show_commands_view(self, refresh: bool = False) -> None:
        if not refresh:
            self.view_stack.append("commands")
        # Hide search bar
        search_bar = self.query_one("#search-bar", Input)
        search_bar.styles.display = "none"
        tabs = self.query_one("#skills-tabs", Tabs)
        tabs.styles.display = "none"
        skill_info = self.query_one("#skill-info", Static)
        if self.current_skill:
            description = self._read_skill_description(self.current_skill_path)
            path_value = self.current_skill_path or "-"
            desc_value = description or "-"
            skill_info.update(
                f"Skill: {self.current_skill}\n\nDescription: {desc_value}\n\nPath: {path_value}"
            )
            skill_info.styles.display = "block"
        else:
            skill_info.styles.display = "none"
        self.query_one("#skill-info", Static).styles.display = "none"

        table = self.query_one("#main-table", DataTable)
        table.clear(columns=True)
        table.add_columns("message")
        table.cursor_type = "none"
        table.add_row("No commands found")

    def _show_agents_view(self, refresh: bool = False) -> None:
        if not refresh:
            self.view_stack.append("agents")
        # Hide search bar
        search_bar = self.query_one("#search-bar", Input)
        search_bar.styles.display = "none"
        tabs = self.query_one("#skills-tabs", Tabs)
        tabs.styles.display = "none"
        self.query_one("#skill-info", Static).styles.display = "none"

        table = self.query_one("#main-table", DataTable)
        table.clear(columns=True)
        table.add_columns("agent", "global base", "local base")
        table.cursor_type = "none"
        agents = get_agents()
        if not agents:
            table.add_row("No agents found", "-", "-")
            return
        for agent, config in agents.items():
            table.add_row(
                agent,
                config.base_path or "-",
                config.local_base_path or "-",
            )

    def _show_action_view(self, skill_name: str, refresh: bool = False) -> None:
        if not refresh:
            self.view_stack.append("actions")
        self.current_skill = skill_name

        # Hide search bar
        search_bar = self.query_one("#search-bar", Input)
        search_bar.styles.display = "none"
        tabs = self.query_one("#skills-tabs", Tabs)
        tabs.styles.display = "none"
        self.query_one("#skill-info", Static).styles.display = "none"

        destinations = (
            self.current_skill_destinations
            if self.current_skill == skill_name and self.current_skill_destinations is not None
            else self.skill_destinations.get(skill_name, [])
        )
        agents = self._collect_agent_status(destinations)

        description = self._read_skill_description(self.current_skill_path)
        skill_info = self.query_one("#skill-info", Static)
        path_value = self.current_skill_path or "-"
        desc_value = description or "-"
        skill_info.update(
            f"Skill: {skill_name}\n\nDescription: {desc_value}\n\nPath: {path_value}"
        )
        skill_info.styles.display = "block"

        table = self.query_one("#main-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Actions")
        table.cursor_type = "row"

        actions: list[tuple[str, str]] = []

        # Build action list based on installation status
        self._append_scope_actions(
            actions,
            scope="global",
            agents=agents,
            scope_label="globally",
        )
        self._append_scope_actions(
            actions,
            scope="local",
            agents=agents,
            scope_label="locally (project)",
        )

        for action_id, action_name in actions:
            table.add_row(action_name, key=action_id)

        if table.row_count > 0:
            table.move_cursor(row=0)
        table.focus()

    def _show_confirm_view(
        self, action: str, scope: str, dest: str, refresh: bool = False
    ) -> None:
        if not refresh:
            self.view_stack.append("confirm")
        self.pending_action = (action, scope, dest)

        # Hide search bar
        search_bar = self.query_one("#search-bar", Input)
        search_bar.styles.display = "none"
        tabs = self.query_one("#skills-tabs", Tabs)
        tabs.styles.display = "none"

        table = self.query_one("#main-table", DataTable)
        table.clear(columns=True)
        label = "all" if dest == "all" else self._agent_display_name(dest)
        label = f"{scope} {label}"
        table.add_columns(f"Confirm {action} for {label}?")
        table.cursor_type = "row"
        table.add_row("Yes", key="confirm")
        table.add_row("No", key="cancel")
        table.move_cursor(row=0)
        table.focus()

    def _dest_label(self, agent: str, scope: str) -> str:
        if scope == "local":
            return f"{agent}{LOCAL_LABEL_SUFFIX}"
        return agent

    def _has_destination(self, destinations: list[str], agent: str, scope: str) -> bool:
        return self._dest_label(agent, scope) in destinations

    def _append_scope_actions(
        self,
        actions: list[tuple[str, str]],
        scope: str,
        agents: list["AgentStatus"],
        scope_label: str,
    ) -> None:
        available = [agent for agent in agents if agent.scope_root(scope)]
        if len(available) >= 2:
            any_installed = any(agent.scope_installed(scope) for agent in available)
            all_installed = all(agent.scope_installed(scope) for agent in available)
            if all_installed:
                actions.append(
                    (f"uninstall_{scope}_all", f"Uninstall {scope_label} for all")
                )
            elif not any_installed:
                actions.append(
                    (f"install_{scope}_all", f"Install {scope_label} for all")
                )
            else:
                actions.append(
                    (f"install_{scope}_all", f"Install {scope_label} for all")
                )
                actions.append(
                    (f"uninstall_{scope}_all", f"Uninstall {scope_label} for all")
                )

        for agent in available:
            agent_name = agent.name
            display = agent.display
            installed = agent.scope_installed(scope)
            if installed:
                actions.append(
                    (
                        f"uninstall_{scope}_{agent_name}",
                        f"Uninstall {scope_label} for {display}",
                    )
                )
            else:
                actions.append(
                    (
                        f"install_{scope}_{agent_name}",
                        f"Install {scope_label} for {display}",
                    )
                )

    def _parse_action_target(self, action_id: str) -> tuple[str | None, str | None]:
        parts = action_id.split("_", 2)
        if len(parts) != 3:
            return None, None
        _, scope, dest = parts
        return scope, dest

    def action_ignore(self) -> None:
        pass

    def action_focus_search(self) -> None:
        if self.view_stack[-1] == "skills":
            search_bar = self.query_one("#search-bar", Input)
            search_bar.focus()

    def _collect_agent_status(self, destinations: list[str]) -> list["AgentStatus"]:
        agents: list[AgentStatus] = []
        for agent, config in get_agents().items():
            agents.append(self._build_agent_status(agent, config, destinations))
        return agents

    def _build_agent_status(
        self, agent: str, config: AgentConfig, destinations: list[str]
    ) -> "AgentStatus":
        display = self._agent_display_name(agent)
        global_base = config.base_path
        local_base = config.local_base_path
        return AgentStatus(
            name=agent,
            display=display,
            global_root=bool(global_base and os.path.isdir(global_base)),
            local_root=bool(local_base),
            global_installed=self._has_destination(destinations, agent, "global"),
            local_installed=self._has_destination(destinations, agent, "local"),
        )

    def _agent_display_name(self, agent: str) -> str:
        return agent.replace("_", " ").replace("-", " ").title()

    def action_cycle_tab(self) -> None:
        if self.view_stack[-1] != "skills":
            return
        self._set_active_tab("installed" if self.active_tab == "skills" else "skills")

    def action_cycle_tab_reverse(self) -> None:
        self.action_cycle_tab()

    def action_select_row(self) -> None:
        # Check if search bar currently has focus
        focused = self.focused
        if focused and focused.id == "search-bar":
            # Move focus to table instead of selecting
            table = self.query_one("#main-table", DataTable)
            table.focus()
            return
        table = self.query_one("#main-table", DataTable)
        table.action_select_cursor()

    def action_select_row_alt(self) -> None:
        self.action_select_row()

    def action_go_back_alt(self) -> None:
        self.action_go_back()

    def action_go_back(self) -> None:
        # If search bar has focus in skills view, clear search and return to table
        focused = self.focused
        if focused and focused.id == "search-bar" and self.view_stack[-1] == "skills":
            search_bar = self.query_one("#search-bar", Input)
            search_bar.value = ""
            self._filter_skills("", focus_table=True)
            return

        if len(self.view_stack) == 1:
            return
        self.view_stack.pop()
        if self.view_stack[-1] == "skills":
            self._show_skills_view(refresh=True)
        elif self.view_stack[-1] == "actions" and self.current_skill:
            self._show_action_view(self.current_skill, refresh=True)
        elif self.view_stack[-1] == "commands":
            self._show_commands_view(refresh=True)
        elif self.view_stack[-1] == "agents":
            self._show_agents_view(refresh=True)
        elif self.view_stack[-1] == "confirm" and self.pending_action:
            action, scope, dest = self.pending_action
            self._show_confirm_view(action, scope, dest, refresh=True)

    def _handle_skill_selection(self, row_key) -> None:
        skill_key = row_key.value
        skill_name = self.row_key_to_skill.get(skill_key, skill_key)
        self.current_skill_path = self.row_key_to_path.get(skill_key)
        self.current_skill_destinations = self.row_key_to_destinations.get(skill_key)
        self._show_action_view(skill_name)

    def _handle_action_selection(self, row_key) -> None:
        action_id = row_key.value

        # Parse action
        if action_id.startswith("install_"):
            action = "install"
            scope, dest = self._parse_action_target(action_id)
            if scope is None:
                return
            # Install doesn't need confirmation
            self._execute_action(action, dest, scope)
        elif action_id.startswith("uninstall_"):
            action = "uninstall"
            scope, dest = self._parse_action_target(action_id)
            if scope is None:
                return
            # Uninstall needs confirmation
            self._show_confirm_view(action, scope, dest)

    def _handle_confirm_selection(self, row_key) -> None:
        key_value = row_key.value
        if key_value == "confirm" and self.pending_action:
            action, scope, dest = self.pending_action
            self.pending_action = None
            self._execute_action(action, dest, scope)
        else:
            # Cancel
            self.action_go_back()

    def _execute_action(self, action: str, dest: str, scope: str) -> None:
        if not self.current_skill:
            return
        try:
            if action == "install":
                source_root = (
                    os.path.dirname(self.current_skill_path)
                    if self.current_skill_path
                    else None
                )
                skills_install(
                    self.current_skill,
                    "auto" if dest == "all" else dest,
                    source_root=source_root,
                    scope=scope,
                )
            elif action == "uninstall":
                source_root = (
                    os.path.dirname(self.current_skill_path)
                    if self.current_skill_path
                    else None
                )
                skills_uninstall(
                    self.current_skill,
                    "auto" if dest == "all" else dest,
                    source_root=source_root,
                    scope=scope,
                )
            else:
                return
            # Refresh skill data
            matches = skills_list(pattern=f"^{re.escape(self.current_skill)}$")
            if matches:
                chosen = None
                if self.current_skill_path:
                    for _, skill_path, destinations in matches:
                        if skill_path == self.current_skill_path:
                            chosen = destinations
                            break
                if chosen is None:
                    _, _, chosen = matches[0]
                self.skill_destinations[self.current_skill] = chosen
                self.current_skill_destinations = chosen
            # Go back to skills view
            while len(self.view_stack) > 1:
                self.view_stack.pop()
            self._show_skills_view(refresh=True)
        except (RuntimeError, ValueError) as exc:
            # Show error in the table
            table = self.query_one("#main-table", DataTable)
            table.clear(columns=True)
            table.add_columns("Error Message", "Details")
            table.cursor_type = "none"
            error_msg = str(exc)
            table.add_row("Action failed", error_msg)
            # Add a helpful message row
            table.add_row("Press ESC", "to go back")
            table.focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if self.view_stack[-1] == "skills":
            self._handle_skill_selection(event.row_key)
        elif self.view_stack[-1] == "actions":
            self._handle_action_selection(event.row_key)
        elif self.view_stack[-1] == "confirm":
            self._handle_confirm_selection(event.row_key)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-bar" and self.view_stack[-1] == "skills":
            self._filter_skills(event.value)

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if self.view_stack[-1] != "skills":
            return
        if event.tab.id:
            self._set_active_tab(event.tab.id)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Enter key handling is done in action_select_row
        pass

    def _read_skill_description(self, skill_path: str | None) -> str:
        if not skill_path:
            return ""
        skill_file = os.path.join(skill_path, "SKILL.md")
        try:
            with open(skill_file, "r", encoding="utf-8") as handle:
                contents = handle.read()
        except OSError:
            return ""

        try:
            post = frontmatter.loads(contents)
        except Exception:
            return ""
        description = post.get("description")
        if description is None:
            return ""
        return str(description).strip()
        return ""

    def _set_active_tab(self, tab_id: str) -> None:
        if tab_id not in {"skills", "installed"}:
            return
        self.active_tab = tab_id
        tabs = self.query_one("#skills-tabs", Tabs)
        tabs.active = tab_id
        search_bar = self.query_one("#search-bar", Input)
        self._filter_skills(search_bar.value)


@dataclass(frozen=True)
class AgentStatus:
    """Resolved agent installation state for the UI."""

    name: str
    display: str
    global_root: bool
    local_root: bool
    global_installed: bool
    local_installed: bool

    def scope_root(self, scope: str) -> bool:
        if scope == "local":
            return self.local_root
        return self.global_root

    def scope_installed(self, scope: str) -> bool:
        if scope == "local":
            return self.local_installed
        return self.global_installed


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        app = SkgetApp()
        app.run()


cli.add_command(skills)


if __name__ == "__main__":
    cli()
