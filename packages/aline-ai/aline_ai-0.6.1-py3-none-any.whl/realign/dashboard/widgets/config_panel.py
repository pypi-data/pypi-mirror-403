"""Config Panel Widget for viewing and editing configuration."""

import threading
import webbrowser
from dataclasses import fields
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Static, Switch

from ..tmux_manager import _run_outer_tmux, OUTER_SESSION
from ...auth import (
    load_credentials,
    save_credentials,
    clear_credentials,
    open_login_page,
    is_logged_in,
    get_current_user,
    find_free_port,
    start_callback_server,
    validate_cli_token,
)
from ...config import ReAlignConfig
from ...logging_config import setup_logger

logger = setup_logger("realign.dashboard.widgets.config_panel", "dashboard.log")


class ConfigPanel(Static):
    """Panel for viewing and editing Aline configuration."""

    DEFAULT_CSS = """
    ConfigPanel {
        height: 100%;
        padding: 1;
    }

    ConfigPanel .config-path {
        margin-bottom: 1;
    }

    ConfigPanel .section-title {
        text-style: bold;
        margin-bottom: 1;
    }

    ConfigPanel DataTable {
        height: 1fr;
        max-height: 20;
    }

    ConfigPanel .edit-section {
        height: 5;
        margin-top: 1;
        padding: 1;
        border: solid $primary;
    }

    ConfigPanel .edit-section Input {
        width: 1fr;
    }

    ConfigPanel .button-row {
        height: 3;
        margin-top: 1;
    }

    ConfigPanel .button-row Button {
        margin-right: 1;
    }

    ConfigPanel .tmux-settings {
        height: auto;
        margin-top: 1;
        padding: 1;
        border: solid $secondary;
    }

    ConfigPanel .tmux-settings .setting-row {
        height: 3;
        align: left middle;
    }

    ConfigPanel .tmux-settings .setting-label {
        width: auto;
        margin-right: 1;
    }

    ConfigPanel .tmux-settings Switch {
        width: auto;
    }

    ConfigPanel .account-section {
        height: auto;
        margin-top: 1;
        padding: 1;
        border: solid $success;
    }

    ConfigPanel .account-section .account-status {
        margin-bottom: 1;
    }

    ConfigPanel .account-section Button {
        margin-right: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._config_path: Optional[Path] = None
        self._config_data: dict = {}
        self._selected_key: Optional[str] = None
        self._border_resize_enabled: bool = True  # Track tmux border resize state
        self._syncing_switch: bool = False  # Flag to prevent recursive switch updates
        self._login_in_progress: bool = False  # Track login state
        self._refresh_timer = None  # Timer for auto-refresh

    def compose(self) -> ComposeResult:
        """Compose the config panel layout."""
        yield Static(id="config-path", classes="config-path")
        yield Static("[bold]Configuration[/bold]", classes="section-title")
        yield DataTable(id="config-table")
        with Horizontal(classes="edit-section"):
            yield Static("Selected: ", id="selected-label")
            yield Input(id="edit-input", placeholder="Select a config item to edit...")
        with Horizontal(classes="button-row"):
            yield Button("Save", id="save-btn", variant="primary")
            yield Button("Reload", id="reload-btn", variant="default")

        # Account section
        with Static(classes="account-section"):
            yield Static("[bold]Account[/bold]", classes="section-title")
            yield Static(id="account-status", classes="account-status")
            with Horizontal(classes="button-row"):
                yield Button("Login", id="login-btn", variant="primary")
                yield Button("Logout", id="logout-btn", variant="warning")

        # Tmux settings section
        with Static(classes="tmux-settings"):
            yield Static("[bold]Tmux Settings[/bold]", classes="section-title")
            with Horizontal(classes="setting-row"):
                yield Static("Allow border resize:", classes="setting-label")
                yield Switch(value=True, id="border-resize-switch")

    def on_mount(self) -> None:
        """Set up the panel on mount."""
        table = self.query_one("#config-table", DataTable)
        table.add_columns("Setting", "Value")
        table.cursor_type = "row"

        # Load initial data
        self.refresh_data()

        # Update account status display
        self._update_account_status()

        # Query and set the actual tmux border resize state
        self._sync_border_resize_switch()

        # Start timer to periodically refresh account status (every 5 seconds)
        self._refresh_timer = self.set_interval(5.0, self._update_account_status)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the config table."""
        table = self.query_one("#config-table", DataTable)

        # Get the selected row data
        row_key = event.row_key
        if row_key is not None:
            row_data = table.get_row(row_key)
            if row_data and len(row_data) >= 2:
                key = str(row_data[0])
                value = str(row_data[1])

                self._selected_key = key

                # Update the edit section
                selected_label = self.query_one("#selected-label", Static)
                selected_label.update(f"Selected: [bold]{key}[/bold]")

                edit_input = self.query_one("#edit-input", Input)
                # Don't show masked values in input
                if "api_key" in key and value.endswith("..."):
                    edit_input.value = ""
                    edit_input.placeholder = "(enter new API key)"
                else:
                    edit_input.value = value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "save-btn":
            self._save_config()
        elif event.button.id == "reload-btn":
            self.refresh_data()
            self._update_account_status()
            self.app.notify("Configuration reloaded", title="Config")
        elif event.button.id == "login-btn":
            self._handle_login()
        elif event.button.id == "logout-btn":
            self._handle_logout()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch toggle events."""
        if self._syncing_switch:
            return  # Ignore events during sync
        if event.switch.id == "border-resize-switch":
            self._toggle_border_resize(event.value)

    def _update_account_status(self) -> None:
        """Update the account status display."""
        try:
            status_widget = self.query_one("#account-status", Static)
            login_btn = self.query_one("#login-btn", Button)
            logout_btn = self.query_one("#logout-btn", Button)
        except Exception:
            # Widget not ready yet
            return

        # Don't update if login is in progress
        if self._login_in_progress:
            return

        credentials = get_current_user()
        if credentials:
            status_widget.update(
                f"[green]Logged in as:[/green] [bold]{credentials.email}[/bold]"
            )
            login_btn.disabled = True
            logout_btn.disabled = False
        else:
            status_widget.update("[yellow]Not logged in[/yellow]")
            login_btn.disabled = False
            logout_btn.disabled = True

    def _handle_login(self) -> None:
        """Handle login button click - start login flow in background."""
        if self._login_in_progress:
            self.app.notify("Login already in progress...", title="Login")
            return

        self._login_in_progress = True

        # Update UI to show login in progress
        login_btn = self.query_one("#login-btn", Button)
        login_btn.disabled = True
        status_widget = self.query_one("#account-status", Static)
        status_widget.update("[cyan]Opening browser for login...[/cyan]")

        # Start login flow in background thread
        def do_login():
            try:
                port = find_free_port()
                open_login_page(callback_port=port)

                # Wait for callback (up to 5 minutes)
                cli_token, error = start_callback_server(port, timeout=300)

                if error:
                    self.app.call_from_thread(
                        self.app.notify, f"Login failed: {error}", title="Login", severity="error"
                    )
                    self.app.call_from_thread(self._update_account_status)
                    return

                if not cli_token:
                    self.app.call_from_thread(
                        self.app.notify, "No token received", title="Login", severity="error"
                    )
                    self.app.call_from_thread(self._update_account_status)
                    return

                # Validate token
                credentials = validate_cli_token(cli_token)
                if not credentials:
                    self.app.call_from_thread(
                        self.app.notify, "Invalid token", title="Login", severity="error"
                    )
                    self.app.call_from_thread(self._update_account_status)
                    return

                # Save credentials
                if save_credentials(credentials):
                    # Sync Supabase uid to local config
                    try:
                        config = ReAlignConfig.load()
                        old_uid = config.uid
                        config.uid = credentials.user_id
                        if not config.user_name:
                            config.user_name = credentials.email.split("@")[0]
                        config.save()
                        logger.info(f"Synced Supabase uid to config: {credentials.user_id[:8]}...")

                        # V18: Upsert user info to users table
                        try:
                            from ...db import get_database
                            db = get_database()
                            db.upsert_user(config.uid, config.user_name)
                        except Exception as e:
                            logger.debug(f"Failed to upsert user to users table: {e}")
                    except Exception as e:
                        logger.warning(f"Failed to sync uid to config: {e}")

                    self.app.call_from_thread(
                        self.app.notify, f"Logged in as {credentials.email}", title="Login"
                    )
                else:
                    self.app.call_from_thread(
                        self.app.notify, "Failed to save credentials", title="Login", severity="error"
                    )

                self.app.call_from_thread(self._update_account_status)

            finally:
                self._login_in_progress = False

        thread = threading.Thread(target=do_login, daemon=True)
        thread.start()

        self.app.notify("Complete login in browser...", title="Login")

    def _handle_logout(self) -> None:
        """Handle logout button click - clear credentials."""
        credentials = load_credentials()
        email = credentials.email if credentials else "user"

        if clear_credentials():
            self._update_account_status()
            self.app.notify(f"Logged out: {email}", title="Account")
        else:
            self.app.notify("Failed to logout", title="Account", severity="error")

    def _sync_border_resize_switch(self) -> None:
        """Query tmux state and sync the switch to match."""
        try:
            # Check if MouseDrag1Border is bound by listing keys
            result = _run_outer_tmux(["list-keys", "-T", "root"], capture=True)
            output = result.stdout or ""

            # If MouseDrag1Border is in the output, resize is enabled
            is_enabled = "MouseDrag1Border" in output
            self._border_resize_enabled = is_enabled

            # Update switch without triggering the toggle action
            self._syncing_switch = True
            try:
                switch = self.query_one("#border-resize-switch", Switch)
                switch.value = is_enabled
            finally:
                self._syncing_switch = False
        except Exception:
            # If we can't query, assume enabled (default tmux behavior)
            pass

    def _toggle_border_resize(self, enabled: bool) -> None:
        """Enable or disable tmux border resize functionality."""
        try:
            if enabled:
                # Re-enable border resize by binding MouseDrag1Border to default resize behavior
                _run_outer_tmux([
                    "bind", "-n", "MouseDrag1Border", "resize-pane", "-M"
                ])
                self._border_resize_enabled = True
                self.app.notify("Border resize enabled", title="Tmux")
            else:
                # Disable border resize by unbinding MouseDrag1Border
                _run_outer_tmux([
                    "unbind", "-n", "MouseDrag1Border"
                ])
                self._border_resize_enabled = False
                self.app.notify("Border resize disabled", title="Tmux")
        except Exception as e:
            self.app.notify(f"Error toggling border resize: {e}", title="Tmux", severity="error")

    def _save_config(self) -> None:
        """Save the edited configuration."""
        if not self._selected_key:
            self.app.notify("No config item selected", title="Config", severity="warning")
            return

        edit_input = self.query_one("#edit-input", Input)
        new_value = edit_input.value

        try:
            from ...config import ReAlignConfig

            config = ReAlignConfig.load()
            key = self._selected_key

            # Validate and convert value
            if not hasattr(config, key):
                self.app.notify(f"Unknown config key: {key}", title="Config", severity="error")
                return

            # Type conversion
            field_type = ReAlignConfig.__annotations__.get(key)
            if field_type is int:
                new_value = int(new_value)
            elif field_type is float:
                new_value = float(new_value)
            elif field_type is bool:
                new_value = new_value.lower() in ("true", "1", "yes")

            # Special validation for llm_provider
            if key == "llm_provider" and new_value not in ("auto", "claude", "openai"):
                self.app.notify(
                    "Invalid llm_provider value. Use: auto, claude, openai",
                    title="Config",
                    severity="error",
                )
                return

            setattr(config, key, new_value)
            config.save()

            self.app.notify(f"Saved: {key}", title="Config")
            self.refresh_data()

        except Exception as e:
            self.app.notify(f"Error saving config: {e}", title="Config", severity="error")

    def refresh_data(self) -> None:
        """Refresh configuration data."""
        self._load_config()
        self._update_display()

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            from ...config import ReAlignConfig

            self._config_path = Path.home() / ".aline" / "config.yaml"
            config = ReAlignConfig.load()

            self._config_data = {}
            for field in fields(ReAlignConfig):
                key = field.name
                value = getattr(config, key)

                # Mask API keys for display
                if "api_key" in key and value:
                    if len(str(value)) > 8:
                        value = str(value)[:4] + "..." + str(value)[-4:]
                    else:
                        value = "***"

                self._config_data[key] = value

        except Exception as e:
            self._config_data = {"error": str(e)}

    def _update_display(self) -> None:
        """Update the display with current data."""
        # Update config path
        path_widget = self.query_one("#config-path", Static)
        if self._config_path:
            path_widget.update(f"[bold]Config file:[/bold] {self._config_path}")
        else:
            path_widget.update("[bold]Config file:[/bold] (not found)")

        # Update table
        table = self.query_one("#config-table", DataTable)
        table.clear()

        for key, value in self._config_data.items():
            # Color-code certain values
            if key == "llm_provider":
                if value == "auto":
                    value_display = "[cyan]auto[/cyan]"
                elif value == "claude":
                    value_display = "[yellow]claude[/yellow]"
                elif value == "openai":
                    value_display = "[green]openai[/green]"
                else:
                    value_display = str(value)
            elif isinstance(value, bool):
                value_display = "[green]true[/green]" if value else "[red]false[/red]"
            elif "api_key" in key and value and value != "None":
                value_display = f"[dim]{value}[/dim]"
            else:
                value_display = str(value) if value is not None else "[dim]None[/dim]"

            table.add_row(key, value_display)

        # Reset edit section
        selected_label = self.query_one("#selected-label", Static)
        selected_label.update("Selected: (none)")
        edit_input = self.query_one("#edit-input", Input)
        edit_input.value = ""
        edit_input.placeholder = "Select a config item to edit..."
        self._selected_key = None
