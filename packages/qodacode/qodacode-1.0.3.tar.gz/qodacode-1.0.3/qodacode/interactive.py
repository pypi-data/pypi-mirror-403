"""
Qodacode Interactive CLI.

REPL with slash commands and autocomplete like Claude Code / Gemini CLI.
Type / to see available commands.
"""

import json
import os
import getpass
from pathlib import Path
from typing import Optional, List

from prompt_toolkit import prompt
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from textual.app import App, ComposeResult
from textual.widgets import Input, Static, OptionList, RichLog
from textual.widgets.option_list import Option
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.binding import Binding
from textual import work

from qodacode import __version__
from qodacode.scanner import Scanner, ScanResult
from qodacode.reporter import Reporter
from qodacode.rules.base import Severity
from qodacode.utils.verdict import calculate_scan_summary

console = Console()
reporter = Reporter()
scanner = Scanner()

# Config paths
CONFIG_DIR = Path.home() / ".qodacode"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Slash commands definition (clean list)
COMMANDS = {
    "/check": "Quick scan (syntax + secrets)",
    "/audit": "Full audit (all engines)",
    "/typosquat": "Check dependencies for typosquatting",
    "/ready": "Production ready?",
    "/mode": "Junior/Senior mode",
    "/api": "Set/remove API key",
    "/export": "Save last scan to file",
    "/clean": "Clear screen",
    "/help": "Show commands",
    "/exit": "Exit",
}


def load_global_config() -> dict:
    """Load global Qodacode config."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_global_config(config: dict):
    """Save global Qodacode config."""
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def is_trusted(path: str) -> bool:
    """Check if path is already trusted."""
    config = load_global_config()
    trusted = config.get("trusted_paths", [])
    return os.path.abspath(path) in trusted


def add_trusted_path(path: str):
    """Add path to trusted list."""
    config = load_global_config()
    trusted = config.get("trusted_paths", [])
    abs_path = os.path.abspath(path)
    if abs_path not in trusted:
        trusted.append(abs_path)
    config["trusted_paths"] = trusted
    save_global_config(config)


def get_project_config(path: str) -> dict:
    """Get project-specific config, create default if not exists."""
    project_config = Path(path) / ".qodacode" / "config.json"
    if project_config.exists():
        with open(project_config) as f:
            return json.load(f)
    # Create default config
    default_config = {
        "language": "en",
        "mode": "senior",
        "ai": {},
        "exclude": [".git", ".qodacode", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"],
    }
    save_project_config(path, default_config)
    return default_config


def save_project_config(path: str, config: dict):
    """Save project-specific config."""
    project_dir = Path(path) / ".qodacode"
    project_dir.mkdir(exist_ok=True)
    with open(project_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)


def get_username() -> str:
    """Get current username."""
    return getpass.getuser().capitalize()


def show_banner():
    """Display the Qodacode banner - BIG with gradient colors."""
    banner = """
[bold #FF8C42]   ██████╗ [/][bold #F97316] ██████╗ [/][bold #EA580C]██████╗ [/][bold #DC2626] █████╗ [/][bold #B91C1C] ██████╗[/][bold #991B1B]██████╗ [/][bold #7F1D1D]██████╗ [/][bold #7F1D1D]███████╗[/]
[bold #FF8C42]  ██╔═══██╗[/][bold #F97316]██╔═══██╗[/][bold #EA580C]██╔══██╗[/][bold #DC2626]██╔══██╗[/][bold #B91C1C]██╔════╝[/][bold #991B1B]██╔═══██╗[/][bold #7F1D1D]██╔══██╗[/][bold #7F1D1D]██╔════╝[/]
[bold #FF8C42]  ██║   ██║[/][bold #F97316]██║   ██║[/][bold #EA580C]██║  ██║[/][bold #DC2626]███████║[/][bold #B91C1C]██║     [/][bold #991B1B]██║   ██║[/][bold #7F1D1D]██║  ██║[/][bold #7F1D1D]█████╗  [/]
[bold #FF8C42]  ██║▄▄ ██║[/][bold #F97316]██║   ██║[/][bold #EA580C]██║  ██║[/][bold #DC2626]██╔══██║[/][bold #B91C1C]██║     [/][bold #991B1B]██║   ██║[/][bold #7F1D1D]██║  ██║[/][bold #7F1D1D]██╔══╝  [/]
[bold #FF8C42]  ╚██████╔╝[/][bold #F97316]╚██████╔╝[/][bold #EA580C]██████╔╝[/][bold #DC2626]██║  ██║[/][bold #B91C1C]╚██████╗[/][bold #991B1B]╚██████╔╝[/][bold #7F1D1D]██████╔╝[/][bold #7F1D1D]███████╗[/]
[bold #FF8C42]   ╚══▀▀═╝ [/][bold #F97316] ╚═════╝ [/][bold #EA580C]╚═════╝ [/][bold #DC2626]╚═╝  ╚═╝[/][bold #B91C1C] ╚═════╝[/][bold #991B1B] ╚═════╝ [/][bold #7F1D1D]╚═════╝ [/][bold #7F1D1D]╚══════╝[/]

                    [dim]v{version}[/]  [#DA7028]│[/]  [dim]Type[/] [#DA7028]/[/] [dim]for commands[/]
"""
    console.print(banner.format(version=__version__))


def show_welcome(path: str):
    """Display welcome screen with commands."""
    abs_path = os.path.abspath(path)
    project_name = os.path.basename(abs_path)
    username = get_username()

    # Truncar path si es muy largo
    display_path = abs_path
    if len(display_path) > 25:
        display_path = "..." + abs_path[-22:]

    # Build welcome panel content
    table = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    table.add_column("Left", ratio=1)
    table.add_column("Right", ratio=1)

    # Row 1: Welcome + Commands header
    table.add_row(
        f"[bold white]Welcome {username}![/bold white]",
        "[#FF6B35]Commands[/#FF6B35]"
    )
    # Row 2: empty + /check
    table.add_row("", "[#DA7028]/check[/#DA7028]   Scan code")
    # Row 3: Project + /watch
    table.add_row(
        f"[dim]Project:[/dim] [#DA7028]{project_name}[/#DA7028]",
        "[#DA7028]/watch[/#DA7028]   Real-time monitor"
    )
    # Row 4: Path + /status
    table.add_row(
        f"[dim]Path:[/dim] [dim]{display_path}[/dim]",
        "[#DA7028]/status[/#DA7028]  Project health"
    )
    # Row 5: empty + /ready
    table.add_row("", "[#DA7028]/ready[/#DA7028]   Production check")
    # Row 6: empty + /config
    table.add_row("", "[#DA7028]/config[/#DA7028]  Settings")

    console.print(Panel(
        table,
        border_style="orange1",
        box=box.SQUARE,
        padding=(1, 2),
    ))


def prompt_trust(path: str) -> bool:
    """Show trust prompt."""
    abs_path = os.path.abspath(path)

    console.print()
    console.print(Panel(
        f"[bold orange1]Do you trust the files in this folder?[/bold orange1]\n\n"
        f"[white]{abs_path}[/white]\n\n"
        f"[dim]Qodacode will analyze files in this directory.[/dim]",
        border_style="orange1",
        box=box.ROUNDED,
    ))

    response = prompt("Trust this folder? (y/n): ").strip().lower()

    if response in ["y", "yes"]:
        add_trusted_path(path)
        return True
    return False


# Command handlers

def cmd_init(path: str, config: dict):
    """Initialize project."""
    qodacode_dir = Path(path) / ".qodacode"

    if qodacode_dir.exists():
        console.print("[yellow]Project already initialized.[/yellow]")
        return

    console.print("[#DA7028]Initializing...[/#DA7028]")
    qodacode_dir.mkdir(exist_ok=True)
    (qodacode_dir / "cache").mkdir(exist_ok=True)

    # Run initial scan
    result = scanner.scan(path)

    # Save index
    index_data = {
        "version": __version__,
        "files_scanned": result.files_scanned,
        "issues_found": len(result.issues),
    }
    with open(qodacode_dir / "index.json", "w") as f:
        json.dump(index_data, f, indent=2)

    console.print(f"[green]✓ Initialized[/green] - {result.files_scanned} files, {len(result.issues)} issues\n")


def cmd_check(path: str, config: dict):
    """Scan code for issues."""
    mode = config.get("mode", "senior")

    console.print("\n[#DA7028]Scanning...[/#DA7028]\n")
    result = scanner.scan(path)

    if not result.issues:
        console.print(Panel(
            "[bold green]✓ No issues found![/bold green]",
            border_style="green",
        ))
    else:
        # Summary
        console.print(f"[bold]Found {len(result.issues)} issue(s)[/bold]\n")

        if result.critical_count:
            console.print(f"  [red]● {result.critical_count} critical[/red]")
        if result.high_count:
            console.print(f"  [yellow]● {result.high_count} high[/yellow]")
        if result.medium_count:
            console.print(f"  [blue]● {result.medium_count} medium[/blue]")
        if result.low_count:
            console.print(f"  [dim]● {result.low_count} low[/dim]")

        console.print()
        reporter.report_scan_result(result, show_fixes=True, mode=mode)

    console.print()


def cmd_watch(path: str, config: dict):
    """Start file watching."""
    console.print("\n[#DA7028]Starting watch mode...[/#DA7028]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    from qodacode.cli import watch
    import click

    try:
        ctx = click.Context(watch)
        ctx.invoke(watch, path=path, severity="high", mode=config.get("mode", "senior"))
    except KeyboardInterrupt:
        console.print("\n[dim]Watch stopped.[/dim]\n")


def cmd_status(path: str, config: dict):
    """Show project status."""
    qodacode_dir = Path(path) / ".qodacode"

    if not qodacode_dir.exists():
        console.print("[yellow]Not initialized. Run /init first.[/yellow]\n")
        return

    result = scanner.scan(path)

    # Calculate grade
    if result.critical_count > 0:
        grade, color = "F", "red"
    elif result.high_count > 0:
        grade, color = "C", "yellow"
    elif len(result.issues) > 10:
        grade, color = "B", "blue"
    elif len(result.issues) > 0:
        grade, color = "A", "green"
    else:
        grade, color = "A+", "green"

    console.print(Panel(
        f"[bold {color}]Grade: {grade}[/bold {color}]\n\n"
        f"Files: {result.files_scanned}\n"
        f"Issues: {len(result.issues)}\n"
        f"[red]Critical: {result.critical_count}[/red]\n"
        f"[yellow]High: {result.high_count}[/yellow]",
        title="[bold]Project Status[/bold]",
        border_style=color,
    ))
    console.print()


def cmd_ready(path: str, config: dict):
    """Check if production ready."""
    console.print("\n[#DA7028]Checking production readiness...[/#DA7028]\n")

    result = scanner.scan(path)

    blockers = result.critical_count + result.high_count

    if blockers == 0:
        console.print(Panel(
            "[bold green]✓ READY FOR PRODUCTION[/bold green]\n\n"
            "[dim]No critical or high severity issues found.[/dim]",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold red]✗ NOT READY[/bold red]\n\n"
            f"[red]{result.critical_count} critical[/red] + "
            f"[yellow]{result.high_count} high[/yellow] = "
            f"[bold]{blockers} blockers[/bold]\n\n"
            "[dim]Fix these issues before deploying.[/dim]",
            border_style="red",
        ))
    console.print()


def cmd_help():
    """Show all commands."""
    console.print("\n[bold]Available Commands[/bold]\n")
    for cmd, desc in COMMANDS.items():
        console.print(f"  [#DA7028]{cmd:12}[/#DA7028] {desc}")
    console.print()


def detect_api_provider(api_key: str) -> str:
    """Auto-detect API provider from key prefix."""
    if api_key.startswith("sk-ant-"):
        return "anthropic"
    elif api_key.startswith("xai-"):
        return "grok"
    elif api_key.startswith("AIza"):
        return "gemini"
    elif api_key.startswith("sk-"):
        return "openai"
    elif api_key.startswith("ollama") or api_key.startswith("http://localhost"):
        return "ollama"
    return "unknown"


def cmd_api(path: str, config: dict, api_key: str = None) -> str:
    """Set or remove API key with auto-detection.

    Usage:
        /api          - Show current status
        /api <key>    - Set new key (auto-detects provider)
        /api clear    - Remove API key and disable AI features
        /api remove   - Same as clear
    """
    if not api_key:
        # Show current status
        current = config.get("ai", {})
        if current.get("api_key"):
            provider = current.get("provider", "unknown")
            masked = current["api_key"][:8] + "..." + current["api_key"][-4:]
            return f"[#DA7028]API:[/] {provider} ({masked})\n[dim]/api <key> to change | /api clear to remove[/]"
        else:
            return "[dim]No API key configured[/]\n[#DA7028]Usage:[/] /api <key>\n[dim]sk-ant-* → Anthropic | sk-* → OpenAI | xai-* → Grok | AIza* → Gemini | ollama → Ollama[/]"

    # Handle clear/remove commands
    if api_key.lower() in ("clear", "remove", "none", "delete"):
        config["ai"] = {}
        # Also switch back to senior mode since junior requires API
        if config.get("mode") == "junior":
            config["mode"] = "senior"
        save_project_config(path, config)
        return "[green]✓ API key removed[/]\n[dim]Mode: senior (AI features disabled)[/]"

    # Detect provider
    provider = detect_api_provider(api_key)
    if provider == "unknown":
        return "[yellow]Warning: Unknown API key format[/]\n[dim]Expected: sk-ant-* (Anthropic), sk-* (OpenAI), xai-* (Grok), AIza* (Gemini), ollama (Ollama)[/]"

    # Save
    config["ai"] = {"provider": provider, "api_key": api_key}
    save_project_config(path, config)

    return f"[green]✓ API configured:[/] {provider}"


def cmd_language(path: str, config: dict, lang: str = None) -> str:
    """Change language."""
    if not lang:
        current = config.get("language", "en")
        return f"[#DA7028]Language:[/] {current}\n[dim]Use /language en or /language es[/]"

    lang = lang.lower()
    if lang not in ["en", "es"]:
        return "[red]Invalid language.[/] Use: en, es"

    config["language"] = lang
    save_project_config(path, config)
    return f"[green]✓ Language:[/] {lang}"


class CommandInput(Input):
    """Custom input with slash command suggestions."""

    BINDINGS = [
        Binding("escape", "clear_input", "Clear"),
    ]

    def __init__(self, commands: dict, **kwargs):
        super().__init__(**kwargs)
        self.commands = commands
        self.suggestions_visible = False

    def action_clear_input(self):
        self.value = ""

    def on_input_changed(self, event: Input.Changed) -> None:
        """Show suggestions when typing /"""
        app = self.app
        if hasattr(app, 'suggestions'):
            if event.value.startswith("/"):
                # Filter commands
                filtered = [
                    (cmd, desc) for cmd, desc in self.commands.items()
                    if cmd.startswith(event.value.lower())
                ]
                app.update_suggestions(filtered)
                app.suggestions.display = True
            else:
                app.suggestions.display = False


class QodacodeApp(App):
    """Qodacode Interactive TUI."""

    CSS = """
    Screen {
        background: #1a1a1a;
    }

    #banner {
        text-align: center;
        padding: 1 0 0 0;
    }

    #welcome-box {
        border: solid #DA7028;
        padding: 1 2;
        margin: 0 2;
        background: #2d2d2d;
    }

    #input-container {
        height: auto;
        margin: 0 2;
        padding: 0;
    }

    #top-line, #bottom-line {
        color: #DA7028;
        height: 1;
        margin: 0;
        padding: 0;
    }

    #command-input {
        border: none;
        background: #1a1a1a;
        padding: 0;
        margin: 0;
        height: 1;
        color: #e0e0e0;
    }

    #command-input:focus {
        border: none;
    }

    #command-input > .input--placeholder {
        color: #707070;
    }

    #hint {
        color: #707070;
        padding: 0 2;
        height: 1;
        margin: 0;
    }

    #suggestions {
        background: #2d2d2d;
        border: solid #DA7028;
        margin: 0 2;
        max-height: 12;
        padding: 0;
    }

    OptionList > .option-list--option {
        padding: 0 2;
        color: #e0e0e0;
    }

    OptionList > .option-list--option-highlighted {
        background: #DA7028;
        color: #ffffff;
    }

    #output {
        margin: 1 2;
        height: 1fr;
        background: #1a1a1a;
        padding: 1 2;
        scrollbar-size: 1 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Exit"),
    ]

    def __init__(self, path: str, config: dict):
        super().__init__()
        self.path = path
        self.config = config
        self.command_result = None
        self.scanning = False
        self.last_learn_why = None  # AI insights from last scan

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        # Banner - QODACODE with gradient colors
        banner = """
[bold #FF8C42]   ██████╗ [/][bold #F97316] ██████╗ [/][bold #EA580C]██████╗ [/][bold #DC2626] █████╗ [/][bold #B91C1C] ██████╗[/][bold #991B1B]██████╗ [/][bold #7F1D1D]██████╗ [/][bold #7F1D1D]███████╗[/]
[bold #FF8C42]  ██╔═══██╗[/][bold #F97316]██╔═══██╗[/][bold #EA580C]██╔══██╗[/][bold #DC2626]██╔══██╗[/][bold #B91C1C]██╔════╝[/][bold #991B1B]██╔═══██╗[/][bold #7F1D1D]██╔══██╗[/][bold #7F1D1D]██╔════╝[/]
[bold #FF8C42]  ██║   ██║[/][bold #F97316]██║   ██║[/][bold #EA580C]██║  ██║[/][bold #DC2626]███████║[/][bold #B91C1C]██║     [/][bold #991B1B]██║   ██║[/][bold #7F1D1D]██║  ██║[/][bold #7F1D1D]█████╗  [/]
[bold #FF8C42]  ██║▄▄ ██║[/][bold #F97316]██║   ██║[/][bold #EA580C]██║  ██║[/][bold #DC2626]██╔══██║[/][bold #B91C1C]██║     [/][bold #991B1B]██║   ██║[/][bold #7F1D1D]██║  ██║[/][bold #7F1D1D]██╔══╝  [/]
[bold #FF8C42]  ╚██████╔╝[/][bold #F97316]╚██████╔╝[/][bold #EA580C]██████╔╝[/][bold #DC2626]██║  ██║[/][bold #B91C1C]╚██████╗[/][bold #991B1B]╚██████╔╝[/][bold #7F1D1D]██████╔╝[/][bold #7F1D1D]███████╗[/]
[bold #FF8C42]   ╚══▀▀═╝ [/][bold #F97316] ╚═════╝ [/][bold #EA580C]╚═════╝ [/][bold #DC2626]╚═╝  ╚═╝[/][bold #B91C1C] ╚═════╝[/][bold #991B1B] ╚═════╝ [/][bold #7F1D1D]╚═════╝ [/][bold #7F1D1D]╚══════╝[/]

                    [dim]v{version}[/]  [#DA7028]│[/]  [dim]Type[/] [#DA7028]/[/] [dim]for commands[/]
"""
        yield Static(banner.format(version=__version__), id="banner")

        username = get_username()
        project_name = os.path.basename(os.path.abspath(self.path))
        mode = self.config.get("mode", "senior")
        ai_config = self.config.get("ai", {})
        has_api = bool(ai_config.get("api_key"))

        if has_api:
            provider = ai_config.get("provider", "unknown")
            api_line = f"[dim]AI:[/] [green]●[/] [#DA7028]{provider}[/]"
        else:
            api_line = "[dim]AI:[/] [#DA7028]None[/]"

        # Welcome content with two-column layout (Scan | Config)
        welcome_content = f"""[bold white]Welcome {username}![/]

[dim]Project:[/] [#DA7028]{project_name}[/]
[dim]Mode:[/] [#DA7028]{mode}[/]
{api_line}

[#FF6B35]Scan[/]                    [#FF6B35]Config[/]
[#DA7028]/check[/]     Quick scan      [#DA7028]/mode[/]   Junior/Senior
[#DA7028]/audit[/]     Full audit      [#DA7028]/api[/]    API Keys
[#DA7028]/typosquat[/]  Supply chain   [#DA7028]/help[/]   Commands
[#DA7028]/ready[/]     Production?"""

        yield Static(welcome_content, id="welcome-box")

        # Input area with lines
        with Vertical(id="input-container"):
            yield Static("─" * 70, id="top-line")
            yield CommandInput(COMMANDS, placeholder="Type / for commands", id="command-input")
            yield Static("─" * 70, id="bottom-line")
            yield Static("  Type / for commands", id="hint")

        # Suggestions list (hidden by default)
        self.suggestions = OptionList(id="suggestions")
        self.suggestions.display = False
        yield self.suggestions

        # Output area (scrollable para respuestas)
        yield RichLog(id="output", highlight=True, markup=True, wrap=True)

    def update_suggestions(self, items: list):
        """Update the suggestions list."""
        self.suggestions.clear_options()
        for cmd, desc in items:
            self.suggestions.add_option(Option(f"[#DA7028]{cmd:12}[/] [dim]{desc}[/]", id=cmd))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        value = event.value.strip()

        if not value:
            return

        # Hide suggestions
        self.suggestions.display = False

        # Clear input
        event.input.value = ""

        # Parse command and args
        parts = value.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else None

        # Process command
        if cmd == "/exit":
            self.exit()
        elif cmd == "/help":
            self.show_output(self.get_help_text())
        elif cmd == "/api":
            result = cmd_api(self.path, self.config, args)
            self.show_output(result)
            # Auto-switch to Junior mode after successful API config
            if args and self.config.get("ai", {}).get("api_key"):
                self.config["mode"] = "junior"
                save_project_config(self.path, self.config)
                self.show_output("[#DA7028]Mode: junior[/] [dim](auto-activated)[/]")
            self.refresh_welcome_box()
        elif cmd == "/check":
            self._start_scan()
        elif cmd == "/audit":
            self._start_audit()
        elif cmd == "/clean":
            # Clear output
            output = self.query_one("#output", RichLog)
            output.clear()
        elif cmd == "/mode":
            # Set mode explicitly or toggle
            current = self.config.get("mode", "senior")
            if args and args.lower() in ("junior", "senior"):
                new_mode = args.lower()
            else:
                # Toggle if no valid argument
                new_mode = "junior" if current == "senior" else "senior"

            # Require API key for Junior mode (AI-powered explanations)
            ai_config = self.config.get("ai", {})
            if new_mode == "junior" and not ai_config.get("api_key"):
                self.show_output("[yellow]⚠️ Junior Mode requires API key for AI explanations.[/]\n   Run [#DA7028]/api <key>[/] first.")
                return

            self.config["mode"] = new_mode
            save_project_config(self.path, self.config)
            self.show_output(f"[#DA7028]Mode: {new_mode}[/]")
            self.refresh_welcome_box()
        elif cmd == "/typosquat":
            self._check_typosquat()
        elif cmd == "/ready":
            self._check_ready()
        elif cmd == "/export":
            self._export_results()
        elif cmd.startswith("/"):
            self.show_output(f"[red]Unknown command: {cmd}[/]\n[dim]Type /help for available commands[/]")
        else:
            self.show_output("[dim]Type / to see commands[/]")

    def refresh_welcome_box(self):
        """Refresh the welcome box to show updated status."""
        welcome_box = self.query_one("#welcome-box", Static)
        username = get_username()
        project_name = os.path.basename(os.path.abspath(self.path))
        mode = self.config.get("mode", "senior")
        ai_config = self.config.get("ai", {})
        has_api = bool(ai_config.get("api_key"))

        if has_api:
            provider = ai_config.get("provider", "unknown")
            api_line = f"[dim]AI:[/] [green]●[/] [#DA7028]{provider}[/]"
        else:
            api_line = "[dim]AI:[/] [#DA7028]None[/]"

        welcome_content = f"""[bold white]Welcome {username}![/]

[dim]Project:[/] [#DA7028]{project_name}[/]
[dim]Mode:[/] [#DA7028]{mode}[/]
{api_line}

[#FF6B35]Scan[/]                    [#FF6B35]Config[/]
[#DA7028]/check[/]     Quick scan      [#DA7028]/mode[/]   Junior/Senior
[#DA7028]/audit[/]     Full audit      [#DA7028]/api[/]    API Keys
[#DA7028]/typosquat[/]  Supply chain   [#DA7028]/help[/]   Commands
[#DA7028]/ready[/]     Production?"""

        welcome_box.update(welcome_content)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle suggestion selection."""
        cmd_input = self.query_one("#command-input", Input)
        cmd_input.value = event.option.id
        cmd_input.focus()
        self.suggestions.display = False

    def get_help_text(self) -> str:
        """Generate help text."""
        lines = ["[bold]Available Commands[/]\n"]
        for cmd, desc in COMMANDS.items():
            lines.append(f"  [#DA7028]{cmd:12}[/] {desc}")
        return "\n".join(lines)

    def show_output(self, text: str):
        """Show output with ● prefix conversacional."""
        output = self.query_one("#output", RichLog)
        output.write(f"[#DA7028]●[/] {text}\n")

    def _is_test_file(self, filepath: str) -> bool:
        """Detect if a file is a test file."""
        name = os.path.basename(filepath).lower()
        path_lower = filepath.lower()

        # Test file patterns
        test_patterns = [
            name.startswith("test_"),
            name.endswith("_test.py"),
            name.endswith(".test.js"),
            name.endswith(".test.ts"),
            name.endswith(".spec.js"),
            name.endswith(".spec.ts"),
            "/tests/" in path_lower,
            "/__tests__/" in path_lower,
            "/test/" in path_lower,
            "/spec/" in path_lower,
        ]
        return any(test_patterns)

    def _export_results(self):
        """Export FULL scan results to file (all files, not truncated)."""
        if not hasattr(self, 'last_result') or not self.last_result:
            self.show_output("[yellow]No scan results to export. Run /check or /audit first.[/]")
            return

        result = self.last_result
        mode = self.config.get("mode", "senior")

        # Create export directory
        export_dir = Path(self.path) / ".qodacode"
        export_dir.mkdir(exist_ok=True)
        export_file = export_dir / "last-scan.txt"

        # Build full report
        lines = []
        lines.append("Qodacode Scan Results")
        lines.append(f"Project: {os.path.basename(self.path)}")
        lines.append("=" * 50)
        lines.append("")

        if not result.issues:
            lines.append("🟢🟢🟢  All clear!")
            lines.append("✅ READY FOR PRODUCTION")
        else:
            total = len(result.issues)

            # Semaphore
            if result.critical_count > 0:
                semaphore = "🔴🔴🔴"
            elif result.high_count > 0:
                semaphore = "🔴🟡⚪"
            elif result.medium_count > 0:
                semaphore = "🟡🟡⚪"
            else:
                semaphore = "🟡⚪⚪"

            lines.append(f"{semaphore}  Found {total} issues in {result.files_scanned} files")
            lines.append("")

            # Group by file
            by_file = {}
            for issue in result.issues:
                fp = issue.location.filepath
                if fp not in by_file:
                    by_file[fp] = []
                by_file[fp].append(issue)

            # Sort by severity
            def file_priority(fp):
                issues = by_file[fp]
                c = sum(1 for i in issues if i.severity.value == "critical")
                h = sum(1 for i in issues if i.severity.value == "high")
                return (-c, -h)

            sorted_files = sorted(by_file.keys(), key=file_priority)
            sev_emoji = {"critical": "🔴", "high": "🟡", "medium": "🔵", "low": "⚪"}

            # ALL files (no truncation for export)
            for filepath in sorted_files:
                issues = by_file[filepath]
                short = os.path.basename(filepath)
                is_test = self._is_test_file(filepath)
                test_tag = " [test]" if is_test else ""

                lines.append(f"\n{short}{test_tag}")

                for idx, issue in enumerate(issues):
                    sev = issue.severity.value
                    emoji = sev_emoji.get(sev, "⚪")
                    is_last = idx == len(issues) - 1
                    prefix = "└─" if is_last else "├─"

                    lines.append(f"{prefix} L{issue.location.line}  {emoji} {issue.message}")

                    if issue.fix_suggestion and (mode == "junior" or sev in ["critical", "high"]):
                        fix_prefix = "   " if is_last else "│  "
                        lines.append(f"{fix_prefix}    → {issue.fix_suggestion}")

            # Summary
            lines.append("")
            lines.append("─" * 50)
            summary_parts = []
            if result.critical_count:
                summary_parts.append(f"🔴 {result.critical_count}")
            if result.high_count:
                summary_parts.append(f"🟡 {result.high_count}")
            if result.medium_count:
                summary_parts.append(f"🔵 {result.medium_count}")
            if result.low_count:
                summary_parts.append(f"⚪ {result.low_count}")

            lines.append("   ".join(summary_parts))

            # Verdict: Use shared logic (same as CLI/MCP)
            summary = calculate_scan_summary(result.issues)
            lines.append("")
            lines.append("PRODUCTION:")
            lines.append(f"  Critical: {summary.production.critical}, High: {summary.production.high}, Medium: {summary.production.medium}, Low: {summary.production.low}")
            if summary.tests.total > 0:
                lines.append("TESTS (excluded from verdict):")
                lines.append(f"  Critical: {summary.tests.critical}, High: {summary.tests.high}, Medium: {summary.tests.medium}, Low: {summary.tests.low}")
            lines.append(f"\n{summary.message}")

            # Add Learn Why if available
            if hasattr(self, 'last_learn_why') and self.last_learn_why:
                lines.append("\n" + "=" * 50)
                lines.append("📚 LEARN WHY")
                lines.append("=" * 50)
                lines.append(self.last_learn_why)

        # Write to file
        with open(export_file, "w") as f:
            f.write("\n".join(lines))

        total_files = len(by_file) if result.issues else 0
        self.show_output(f"[green]Exported {total_files} files to .qodacode/last-scan.txt[/]")

    def _start_scan(self):
        """Inicia escaneo en background (Tree-sitter + Gitleaks)."""
        if self.scanning:
            self.show_output("[yellow]Scan in progress...[/]")
            return
        self.scanning = True
        output = self.query_one("#output", RichLog)
        output.write("[#DA7028]⟳[/] [bold #F97316]Scanning...[/] [dim](syntax + secrets)[/]\n")
        self._run_scan()

    def _start_audit(self):
        """Start full audit in background."""
        if self.scanning:
            self.show_output("[yellow]A scan is already in progress...[/]")
            return
        self.scanning = True
        output = self.query_one("#output", RichLog)
        output.write("[#DA7028]⟳[/] [bold #F97316]Full Audit...[/] [dim](All Qodacode engines)[/]\n")
        self._run_audit()

    @work(thread=True)
    def _run_audit(self):
        """Execute full audit in background."""
        try:
            from qodacode.mcp_server import full_audit
            import json
            result_json = full_audit(self.path)
            result = json.loads(result_json)
            self.call_from_thread(self._show_audit_results, result)
        except Exception as e:
            self.call_from_thread(self._scan_error, str(e))

    def _show_audit_results(self, result: dict):
        """Show audit results."""
        output = self.query_one("#output", RichLog)
        summary = result.get("summary", {})
        total = summary.get("total_issues", 0)
        by_sev = summary.get("by_severity", {})
        engines = summary.get("engines", {})

        # Engines status
        engine_status = []
        for eng, info in engines.items():
            status = info.get("status", "unknown")
            count = info.get("count", 0)
            if status == "success":
                engine_status.append(f"[green]✓[/] {eng}: {count}")
            else:
                engine_status.append(f"[dim]○[/] {eng}: {status}")
        output.write(f"[#DA7028]●[/] Engines: {' · '.join(engine_status)}\n")

        if total == 0:
            output.write(f"[#DA7028]●[/] [green]Todo limpio![/] Sin issues detectados.\n\n")
        else:
            output.write(f"[#DA7028]●[/] [bold]{total} issues[/]: ")
            parts = []
            if by_sev.get("critical"):
                parts.append(f"[red]{by_sev['critical']} critical[/]")
            if by_sev.get("high"):
                parts.append(f"[yellow]{by_sev['high']} high[/]")
            if by_sev.get("medium"):
                parts.append(f"[blue]{by_sev['medium']} medium[/]")
            if by_sev.get("low"):
                parts.append(f"[dim]{by_sev['low']} low[/]")
            output.write(" · ".join(parts) + "\n\n")

        self.scanning = False

    @work(thread=True)
    def _run_scan(self):
        """Ejecuta scan en background thread (Tree-sitter + Gitleaks)."""
        try:
            # Tree-sitter scan (syntax analysis)
            local_scanner = Scanner()
            result = local_scanner.scan(self.path)

            # Gitleaks scan (secrets detection)
            try:
                from qodacode.engines import GitleaksRunner
                gitleaks = GitleaksRunner()
                if gitleaks.is_available():
                    gitleaks_issues = gitleaks.run(self.path)
                    result.issues.extend(gitleaks_issues)
            except Exception:
                pass  # Gitleaks not available, continue with Tree-sitter results

            self.call_from_thread(self._show_results, result)
        except Exception as e:
            self.call_from_thread(self._scan_error, str(e))

    def _scan_error(self, msg: str):
        """Muestra error de scan."""
        output = self.query_one("#output", RichLog)
        output.write(f"[#DA7028]●[/] [red]Error: {msg}[/]\n")
        self.scanning = False

    def _show_results(self, result: ScanResult):
        """Show results with enhanced visual design."""
        output = self.query_one("#output", RichLog)
        mode = self.config.get("mode", "senior")

        # Store last result for /export
        self.last_result = result
        self.last_result_text = []

        if not result.issues:
            # All clear - green semaphore
            output.write("\n🟢🟢🟢  All clear! Scanned {} files\n".format(result.files_scanned))
            output.write("\n[green bold]✅ READY FOR PRODUCTION[/]\n\n")
            self.last_result_text = ["🟢🟢🟢  All clear!", "✅ READY FOR PRODUCTION"]
            self.scanning = False
            return

        total = len(result.issues)

        # Semaphore based on severity
        if result.critical_count > 0:
            semaphore = "🔴🔴🔴"
        elif result.high_count > 0:
            semaphore = "🔴🟡⚪"
        elif result.medium_count > 0:
            semaphore = "🟡🟡⚪"
        else:
            semaphore = "🟡⚪⚪"

        # Header
        header = f"\n{semaphore}  Found {total} issues in {result.files_scanned} files\n"
        output.write(header)
        self.last_result_text.append(header.strip())

        output.write("─" * 50 + "\n")

        # Group by file
        by_file = {}
        for issue in result.issues:
            fp = issue.location.filepath
            if fp not in by_file:
                by_file[fp] = []
            by_file[fp].append(issue)

        # Sort by severity
        def file_priority(fp):
            issues = by_file[fp]
            c = sum(1 for i in issues if i.severity.value == "critical")
            h = sum(1 for i in issues if i.severity.value == "high")
            return (-c, -h)

        sorted_files = sorted(by_file.keys(), key=file_priority)

        # Emoji map for severity
        sev_emoji = {"critical": "🔴", "high": "🟡", "medium": "🔵", "low": "⚪"}

        # Show issues with tree structure
        for filepath in sorted_files[:8]:
            issues = by_file[filepath]
            short = os.path.basename(filepath)
            is_test = self._is_test_file(filepath)
            test_tag = " [dim][test][/]" if is_test else ""
            output.write(f"\n[bold]{short}[/]{test_tag}\n")
            self.last_result_text.append(f"\n{short}{' [test]' if is_test else ''}")

            for idx, issue in enumerate(issues):
                sev = issue.severity.value
                emoji = sev_emoji.get(sev, "⚪")
                is_last = idx == len(issues) - 1
                prefix = "└─" if is_last else "├─"

                line_text = f"{prefix} L{issue.location.line}  {emoji} {issue.message}"
                output.write(f"{prefix} L{issue.location.line}  {emoji} {issue.message}\n")
                self.last_result_text.append(line_text)

                # Show fix suggestion
                if issue.fix_suggestion and (mode == "junior" or sev in ["critical", "high"]):
                    fix_prefix = "   " if is_last else "│  "
                    fix_text = f"{fix_prefix}    → {issue.fix_suggestion}"
                    output.write(f"{fix_prefix}    [green]→ {issue.fix_suggestion}[/]\n")
                    self.last_result_text.append(fix_text)

        if len(by_file) > 8:
            more_text = f"\n...and {len(by_file) - 8} more files"
            output.write(f"\n[dim]{more_text}[/]\n")
            self.last_result_text.append(more_text)

        # Summary line
        output.write("\n" + "─" * 50 + "\n")
        summary_parts = []
        if result.critical_count:
            summary_parts.append(f"🔴 {result.critical_count}")
        if result.high_count:
            summary_parts.append(f"🟡 {result.high_count}")
        if result.medium_count:
            summary_parts.append(f"🔵 {result.medium_count}")
        if result.low_count:
            summary_parts.append(f"⚪ {result.low_count}")

        summary_line = "   ".join(summary_parts)
        output.write(f"\n{summary_line}\n")
        self.last_result_text.append(summary_line)

        # Verdict: Use shared logic (same as CLI/MCP)
        summary = calculate_scan_summary(result.issues)

        # Show production vs tests breakdown
        output.write(f"\n[bold]Production:[/bold] 🔴 {summary.production.critical}  🟠 {summary.production.high}  🟡 {summary.production.medium}  🔵 {summary.production.low}\n")
        if summary.tests.total > 0:
            output.write(f"[dim]Tests (excluded):[/dim] 🔴 {summary.tests.critical}  🟠 {summary.tests.high}  🟡 {summary.tests.medium}  🔵 {summary.tests.low}\n")

        if summary.ready:
            output.write(f"\n[green bold]{summary.message}[/]\n\n")
        else:
            output.write(f"\n[red bold]{summary.message}[/]\n\n")

        self.last_result_text.append(summary.message.strip())

        # Junior Mode: Show "Learn Why" with AI batch call
        # Reload config from file to ensure we have latest API key
        self.config = get_project_config(self.path)
        ai_config = self.config.get("ai", {})
        mode = self.config.get("mode", "senior")

        # Special message when project is clean (Junior Mode)
        if mode == "junior" and summary.production.total == 0:
            output.write("\n[bold green]🎉 Congratulations![/]\n")
            output.write("[dim]" + "─" * 40 + "[/]\n")
            if summary.tests.total > 0:
                output.write("[white]Your production code is clean.\n")
                output.write(f"Only {summary.tests.total} issues in test files.[/]\n\n")
            else:
                output.write("[white]Your code is spotless. Zero issues.\n")
                output.write("Keep it up! 🚀[/]\n\n")
        elif mode == "junior" and ai_config.get("api_key") and result.issues:
            output.write(f"[dim]📚 Generating Learn Why... (provider: {ai_config.get('provider')})[/]\n")
            try:
                from qodacode.ai_explainer import batch_learn_why
                # Add language to ai_config for prompt generation
                ai_config["language"] = self.config.get("language", "en")
                learn_text = batch_learn_why(result.issues, ai_config)
                if learn_text:
                    output.write("\n[bold #DA7028]📚 Learn Why[/]\n")
                    output.write("[dim]" + "─" * 40 + "[/]\n")
                    output.write(f"[white]{learn_text}[/]\n\n")
                    self.last_learn_why = learn_text
                else:
                    output.write("[yellow]📚 AI returned empty response[/]\n\n")
            except Exception as e:
                output.write(f"[yellow]📚 Error: {type(e).__name__}: {str(e)[:100]}[/]\n\n")
        elif not ai_config.get("api_key"):
            # API Key gatekeeper: show message if no API key configured
            output.write("[dim]🔒 AI Insights locked. Run[/] [#DA7028]/api <key>[/] [dim]to unlock Junior Mode explanations.[/]\n\n")

        self.scanning = False

    def _check_ready(self):
        """Check if ready for production."""
        output = self.query_one("#output", RichLog)
        output.write("[#DA7028]⟳[/] [bold #F97316]Checking...[/] [dim](production readiness)[/]\n")
        local_scanner = Scanner()
        result = local_scanner.scan(self.path)

        # Verdict: Use shared logic (same as CLI/MCP)
        summary = calculate_scan_summary(result.issues)

        # Show breakdown
        output.write(f"[bold]Production:[/bold] 🔴 {summary.production.critical}  🟠 {summary.production.high}  🟡 {summary.production.medium}  🔵 {summary.production.low}\n")
        if summary.tests.total > 0:
            output.write(f"[dim]Tests (excluded):[/dim] 🔴 {summary.tests.critical}  🟠 {summary.tests.high}  🟡 {summary.tests.medium}  🔵 {summary.tests.low}\n")

        if summary.ready:
            if summary.production.high > 0:
                output.write(f"[#DA7028]●[/] [green bold]✓ READY FOR PRODUCTION[/] [dim]({summary.production.high} warnings)[/]\n")
            else:
                output.write(f"[#DA7028]●[/] [green bold]✓ READY FOR PRODUCTION[/]\n")
            output.write(f"   [dim]No critical issues in production code.[/]\n\n")
        else:
            output.write(f"[#DA7028]●[/] [red bold]✗ NOT READY[/]\n")
            output.write(f"   [dim]{summary.production.critical} critical issues must be fixed.[/]\n\n")

    def _check_typosquat(self):
        """Check dependencies for typosquatting attacks."""
        output = self.query_one("#output", RichLog)
        output.write("[#DA7028]⟳[/] [bold #F97316]Checking dependencies...[/] [dim](typosquatting detection)[/]\n")

        try:
            from qodacode.typosquatting.detector import scan_directory, TyposquatMatch, RiskLevel

            results = scan_directory(self.path)

            if not results:
                output.write("\n[green bold]✓ SUPPLY CHAIN SAFE[/]\n")
                output.write("[dim]No suspicious packages detected in dependencies.[/]\n\n")
                return

            # Count by severity
            total = sum(len(matches) for matches in results.values())
            critical = sum(1 for matches in results.values() for m in matches if m.risk_level == RiskLevel.CRITICAL)
            high = sum(1 for matches in results.values() for m in matches if m.risk_level == RiskLevel.HIGH)
            medium = sum(1 for matches in results.values() for m in matches if m.risk_level == RiskLevel.MEDIUM)

            # Header with severity
            if critical > 0:
                output.write(f"\n[red bold]🚨 SUPPLY CHAIN ATTACK DETECTED[/]\n")
            elif high > 0:
                output.write(f"\n[yellow bold]⚠️ SUSPICIOUS PACKAGES FOUND[/]\n")
            else:
                output.write(f"\n[blue bold]ℹ️ POTENTIAL TYPOS DETECTED[/]\n")

            output.write("─" * 50 + "\n")

            # Show findings
            sev_emoji = {"critical": "🔴", "high": "🟡", "medium": "🔵", "low": "⚪"}
            sev_color = {"critical": "red", "high": "yellow", "medium": "blue", "low": "dim"}

            for filepath, matches in results.items():
                filename = os.path.basename(filepath)
                output.write(f"\n[bold]{filename}[/]\n")

                for idx, match in enumerate(matches):
                    sev = match.risk_level.value
                    emoji = sev_emoji.get(sev, "⚪")
                    color = sev_color.get(sev, "white")
                    is_last = idx == len(matches) - 1
                    prefix = "└─" if is_last else "├─"

                    output.write(f"{prefix} {emoji} [{color}]{match.suspicious_package}[/] → [green]{match.legitimate_package}[/]\n")

                    fix_prefix = "   " if is_last else "│  "
                    output.write(f"{fix_prefix}    [dim]{match.reason}[/]\n")

            # Summary
            output.write("\n" + "─" * 50 + "\n")
            summary_parts = []
            if critical:
                summary_parts.append(f"[red]🔴 {critical} critical[/]")
            if high:
                summary_parts.append(f"[yellow]🟡 {high} high[/]")
            if medium:
                summary_parts.append(f"[blue]🔵 {medium} medium[/]")

            output.write("  ".join(summary_parts) + "\n")

            # Recommendation
            if critical > 0:
                output.write("\n[red bold]⛔ CRITICAL:[/] Remove malicious packages immediately!\n")
                output.write("[dim]These are known attack packages that steal credentials.[/]\n\n")
            elif high > 0:
                output.write("\n[yellow]⚠️  Verify these packages before installing.[/]\n\n")
            else:
                output.write("\n[dim]Review these packages - they may be typos.[/]\n\n")

        except ImportError:
            output.write("[red]Error: Typosquatting module not found[/]\n\n")
        except Exception as e:
            output.write(f"[red]Error: {str(e)}[/]\n\n")


def run_interactive(path: str = "."):
    """Main TUI entry point.

    Flow:
    1. $ qodacode
    2. Trust this folder? [Yes/No]
    3. UI con banner y /commands
    4. Todos los comandos corren DENTRO de la TUI
    """
    # Trust prompt (primera vez)
    if not is_trusted(path):
        if not prompt_trust(path):
            console.print("\n[dim]Cancelled.[/dim]\n")
            return

    # Get config
    config = get_project_config(path)

    # Run TUI (single session)
    app = QodacodeApp(path, config)
    app.run()
    console.print("\n[dim]Goodbye![/dim]\n")
