#pyright: reportPrivateImportUsage=false
from __future__ import annotations
import io
import json
import os
import re
import sys
import requests
import rich
import click
import functools
import pytz
from typing import NoReturn

from relationalai.util.constants import TOP_LEVEL_PROFILE_NAME
from relationalai.errors import RAIException
from rich.table import Table
from typing import Callable, Dict, Any, List, cast
from ..clients import config
from click.core import Context
from rich.console import Console
from rich import box as rich_box
from collections import defaultdict
from packaging.version import Version
from ..clients.config import ConfigFile
from datetime import datetime, timedelta
from click.formatting import HelpFormatter
from ..clients.client import ResourcesBase
from relationalai.tools.constants import GlobalProfile, SHOW_FULL_TRACES
from relationalai.tools.cli_controls import divider
from relationalai.util.format import humanized_bytes, humanized_duration
from InquirerPy.base.control import Choice

#--------------------------------------------------
# Helpers
#--------------------------------------------------

@functools.cache
def get_config(profile:str|Dict[str, Any]|None = None):
    return config.Config(profile or GlobalProfile.get())

@functools.cache
def get_resource_provider(platform:str|None=None, _cfg:config.Config|None = None) -> ResourcesBase:
    cfg = _cfg or get_config()
    platform = platform or cfg.get("platform", "snowflake")
    if platform == "snowflake":
        from relationalai.clients.resources.snowflake.cli_resources import CLIResources
        provider = CLIResources(config=cfg)
    elif platform == "azure":
        from relationalai.clients.resources.azure.azure import Resources
        provider = Resources(config=cfg)
    else:
        from .. import Resources
        provider = Resources(config=cfg)
    return provider

def unexpand_user_path(path):
    """Inverse of os.path.expanduser"""
    home_dir = os.path.expanduser('~')
    if path.startswith(home_dir):
        return '~' + path[len(home_dir):]
    return path

def account_from_url(account_or_url:str):
    regex = r"https://app.snowflake.com/([^/]+)/([^/]+)/?.*"
    match = re.match(regex, account_or_url)
    if match:
        org = match.group(1)
        account = match.group(2)
        return f"{org}-{account}"
    elif "app.snowflake.com" in account_or_url or "https://" in account_or_url:
        raise ValueError("URL not of the form https://app.snowflake.com/[org]/[account]")
    else:
        return account_or_url

def supports_platform(*platform_names: str):
    def decorator(cmd: click.Command):
        setattr(cmd, "__available_platforms", platform_names)
        cb = cmd.callback
        assert cb
        def checked(*args, **kwargs):
            assert cmd.name
            assert_command_available(cmd.name, command_available(cmd))
            return cb(*args, **kwargs)

        cmd.callback = checked
        return cmd
    return decorator

def command_available(cmd: click.Command) -> bool:
    available_platforms = getattr(cmd, "__available_platforms", ())
    platform = get_config().get("platform", "")
    return not available_platforms or not platform or platform in available_platforms

def assert_command_available(name: str, available: bool, plural=False):
    if not available:
        platform = get_config().get("platform", "")
        rich.print(f"[yellow]{name} {'are' if plural else 'is'} not available for {platform}")
        divider()
        sys.exit(1)

def coming_soon():
    rich.print("[yellow]This isn't quite ready yet, but it's coming soon!")
    divider()
    sys.exit(1)

def issue_top_level_profile_warning():
    rich.print("[yellow]Warning: Using a top-level profile is not recommended")
    rich.print("[yellow]Consider naming the profile by adding \\[profile.<name>] to your raiconfig.toml file\n")
    rich.print("[yellow]Example:")
    rich.print("[yellow]\\[profile.default]")
    rich.print("[yellow]platform = \"snowflake\"")
    rich.print("[yellow]account = ...")
    divider()

def ensure_config(profile:str|None=None) -> config.Config:
    cfg = get_config(profile)
    if not cfg.file_path:
        rich.print("[yellow bold]No configuration file found.")
        rich.print("To create one, run: [green bold]rai init[/green bold]")
        divider()
        sys.exit(1)
    return cfg

def latest_version(package_name):
    """Get the current version of a package on PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        version = data['info']['version']
        return version
    else:
        return None

def is_latest_cli_version():
    from .. import __version__
    latest_ver_str = latest_version("relationalai")
    latest_ver = Version(latest_ver_str) if latest_ver_str else Version("0.0.0")
    version = Version(__version__)
    return version >= latest_ver, version, latest_ver

#--------------------------------------------------
# Validation
#--------------------------------------------------

EMPTY_STRING_REGEX = re.compile(r'^\S+$')
ENGINE_NAME_REGEX = re.compile(r'^[a-zA-Z]\w{2,}$')
COMPUTE_POOL_REGEX = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
PASSCODE_REGEX = re.compile(r'^(\d{6})?$')
ENGINE_NAME_ERROR = "Min 3 chars, start with letter, only letters, numbers, underscores allowed."
UUID = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

def validate_engine_name(name:str) -> tuple[bool, str|None]:
    if not ENGINE_NAME_REGEX.match(name):
        return False, ENGINE_NAME_ERROR
    return True, None

#--------------------------------------------------
# Engine types & selection helpers (Snowflake)
#--------------------------------------------------

def format_state_with_color(state: str) -> str:
    """Format engine state with colors for display."""
    if not state:
        return ""
    state_upper = state.upper()
    if state_upper == "READY":
        return f"[green]{state_upper}[/green]"
    if state_upper == "SUSPENDED":
        return f"[yellow]{state_upper}[/yellow]"
    if state_upper in ("PENDING", "SYNCING", "PROCESSING"):
        return f"[bold yellow]{state_upper}[/bold yellow]"
    if state_upper in ("ABORTED", "QUARANTINED", "GONE"):
        return f"[red]{state_upper}[/red]"
    return state_upper

def _get_engine_type_api():
    # Local import to avoid importing snowflake modules for non-snowflake usage
    from relationalai.clients.resources.snowflake import EngineType
    return EngineType

def _get_internal_engine_sizes() -> list[str]:
    # Local import to avoid snowflake imports for non-snowflake usage
    from relationalai.clients.resources.snowflake import INTERNAL_ENGINE_SIZES
    return list(INTERNAL_ENGINE_SIZES)

def get_engine_type_choices(cfg: config.Config, exclude_types: List[str] | None = None) -> List[Choice]:
    """Get sorted list of engine type choices for interactive selection."""
    EngineType = _get_engine_type_api()
    if exclude_types is None:
        exclude_types = []
    exclude_types_upper = [et.upper() for et in exclude_types]
    engine_types_list = [EngineType.LOGIC, EngineType.ML, EngineType.SOLVER]
    engine_types_list = [et for et in engine_types_list if et.upper() not in exclude_types_upper]
    engine_types_list.sort(key=lambda et: EngineType.get_label(et))
    return [
        Choice(value=et, name=f"{EngineType.get_label(et)}: {EngineType.get_description(et)}")
        for et in engine_types_list
    ]

def select_engine_type_interactive(cfg: config.Config) -> str:
    """Show interactive engine type selection and return the selected type."""
    from . import cli_controls as controls
    rich.print("")
    engine_type_choices = get_engine_type_choices(cfg)
    return controls.select("Engine type:", cast("list[str | Choice]", engine_type_choices), None, newline=True)

def select_engine_interactive(
    provider: ResourcesBase,
    prompt: str = "Select an engine:",
    engine_name: str | None = None,
    engines: List[Dict[str, Any]] | None = None,
) -> tuple[str, str | None] | None:
    """Interactive engine picker returning (name, type)."""
    from . import cli_controls as controls

    engine_map: Dict[str, tuple[str, str | None]] = {}

    def get_engines():
        engine_list = engines if engines is not None else provider.list_engines()
        engine_map.clear()
        items: List[str] = []
        EngineType = _get_engine_type_api()
        for engine in engine_list:
            eng_name = engine.get("name", "")
            if engine_name and eng_name.upper() != engine_name.upper():
                continue
            eng_type = engine.get("type", "")
            eng_size = engine.get("size", "")
            if eng_type:
                label = f"{EngineType.get_label(eng_type)} ({eng_type})" if EngineType.is_valid(eng_type) else f"{eng_type} ({eng_type})"
                display = f"{eng_name}, {label}, {eng_size}"
            else:
                display = f"{eng_name}, {eng_size}" if eng_size else eng_name
            engine_map[display] = (eng_name, eng_type or None)
            items.append(display)
        return items

    # Auto-select when engine_name uniquely identifies an engine
    if engine_name:
        engine_list = engines if engines is not None else provider.list_engines()
        matches = [e for e in engine_list if e.get("name", "").upper() == engine_name.upper()]
        if len(matches) == 1:
            e = matches[0]
            return (e.get("name", ""), e.get("type"))
        if len(matches) == 0:
            return None

    selected = controls.fuzzy_with_refetch(prompt, "engines", get_engines)
    if not selected or isinstance(selected, Exception):
        return None
    return engine_map.get(selected)

def select_engine_with_state_filter(
    provider: ResourcesBase,
    engine_name: str | None,
    engine_type: str | None,
    state_filter: str,
    prompt_no_name: str,
    prompt_with_name: str,
    error_no_engines: str,
    error_no_matching: str,
) -> tuple[str, str | None] | None:
    """Select an engine with optional state filtering + optional name filtering."""
    EngineType = _get_engine_type_api()

    if not engine_name:
        filtered = provider.list_engines(state_filter)
        if not filtered:
            exit_with_error(error_no_engines)
        return select_engine_interactive(provider, prompt_no_name, engines=filtered)

    # If type provided and valid, return directly
    if engine_type and EngineType.is_valid(engine_type):
        return (engine_name, engine_type)

    # Filter by name + state; selection handles (name,type)
    filtered = provider.list_engines(state_filter, name=engine_name)
    if not filtered:
        exit_with_error(error_no_matching)
    return select_engine_interactive(provider, prompt_with_name, engine_name=engine_name, engines=filtered)

def ensure_engine_type_for_snowflake(
    provider: ResourcesBase,
    engine_name: str,
    engine_type: str | None,
    error_message: str,
) -> str:
    """Ensure engine_type is provided and valid; default to LOGIC if omitted."""
    EngineType = _get_engine_type_api()
    # If --type was omitted, default to LOGIC for backwards compatibility
    if engine_type is None:
        return EngineType.LOGIC
    assert isinstance(engine_type, str)
    if engine_type == "" or not EngineType.is_valid(engine_type):
        cfg = get_config()
        if engine_type == "":
            rich.print(f"[yellow]Empty engine type provided for engine '{engine_name}'.")
        else:
            rich.print(f"[yellow]Invalid engine type '{engine_type}' for engine '{engine_name}'.")
        return select_engine_type_interactive(cfg)
    return engine_type

def build_engine_operation_messages(
    provider: ResourcesBase,
    engine_name: str,
    engine_type: str | None,
    action: str,
    action_past: str,
) -> tuple[str, str]:
    EngineType = _get_engine_type_api()
    if engine_type:
        label = EngineType.get_label(engine_type) if EngineType.is_valid(engine_type) else engine_type
        return (f"{action} {label} engine '{engine_name}'", f"{label} Engine '{engine_name}' {action_past.lower()}")
    return (f"{action} '{engine_name}' engine", f"Engine '{engine_name}' {action_past.lower()}")

def prompt_and_validate_engine_name(name: str | None) -> str:
    """Prompt for engine name if missing; validate using ENGINE_NAME_REGEX."""
    from . import cli_controls as controls
    if not name:
        name = controls.prompt(
            "Engine name:",
            name,
            validator=ENGINE_NAME_REGEX.match,
            invalid_message=ENGINE_NAME_ERROR,
            newline=True,
        )
    assert isinstance(name, str)
    return name

def validate_auto_suspend_mins(auto_suspend_mins: int | str | None) -> int | None:
    if auto_suspend_mins is None:
        return None
    if isinstance(auto_suspend_mins, int):
        return auto_suspend_mins
    error_msg = f"[yellow]Error: auto_suspend_mins must be an integer instead of {type(auto_suspend_mins)}"
    try:
        return int(auto_suspend_mins)
    except ValueError:
        exit_with_error(error_msg)
    return None

def get_engine_type_for_creation(provider: ResourcesBase, cfg: config.Config, engine_type: str | None) -> str | None:
    """Get engine type for engine creation; defaults to LOGIC when omitted."""
    EngineType = _get_engine_type_api()
    if engine_type is None:
        return EngineType.LOGIC
    if engine_type == "" or not EngineType.is_valid(engine_type):
        if engine_type == "":
            rich.print("[yellow]Empty engine type provided.")
        else:
            valid_types_display = ", ".join(EngineType.get_all_types())
            rich.print(f"[yellow]Invalid engine type '{engine_type}'. Valid types: {valid_types_display}")
        return select_engine_type_interactive(cfg)
    return engine_type

def get_and_validate_engine_size(
    provider: ResourcesBase,
    cfg: config.Config,
    size: str | None,
    engine_type: str | None = None,
) -> str:
    from . import cli_controls as controls
    EngineType = _get_engine_type_api()
    internal_sizes = set(_get_internal_engine_sizes())

    cloud_provider = provider.get_cloud_provider()
    valid_sizes = provider.get_engine_sizes(cloud_provider)

    # Engine-type-aware filtering:
    # Internal sizes (XS/S/M/L) are only valid for LOGIC engines (and only on some accounts).
    # For ML/SOLVER, hide them to avoid presenting invalid options.
    if engine_type and EngineType.is_valid(engine_type) and engine_type != EngineType.LOGIC:
        valid_sizes = [s for s in valid_sizes if s not in internal_sizes]

    # Ask if missing and not in config
    if not size and not cfg.get("engine_size", None):
        rich.print("")
        # This refers to the cloud backing your Snowflake account (AWS/Azure), not the engine "platform".
        size = controls.fuzzy(f"Engine size (Snowflake cloud: {cloud_provider.upper()}):", choices=valid_sizes)
    elif size is None and cfg.get("engine_size", None):
        size = cfg.get("engine_size", None)
    if not isinstance(size, str) or size not in valid_sizes:
        exit_with_error(f"\nInvalid engine size [yellow]{size}[/yellow] provided. Please check your config.\n\nValid sizes: [green]{valid_sizes}[/green]")
    return size

def create_engine_with_spinner(
    provider: ResourcesBase,
    engine_name: str,
    engine_size: str,
    engine_type: str | None,
    auto_suspend_mins: int | None,
) -> None:
    """Create an engine with appropriate spinner messages and error handling."""
    from .cli_controls import Spinner

    EngineType = _get_engine_type_api()
    # Build creation message with engine type when available
    if engine_type:
        creation_message = (
            f"Creating {EngineType.get_label(engine_type)} engine '{engine_name}' with size {engine_size}... "
            f"(this may take several minutes)"
        )
    else:
        creation_message = (
            f"Creating engine '{engine_name}' with size {engine_size}... "
            f"(this may take several minutes)"
        )

    with Spinner(
        creation_message,
        f"Engine '{engine_name}' created!",
        failed_message=None,  # We handle error display ourselves below
    ):
        try:
            provider.create_engine(
                engine_name,
                type=engine_type,
                size=engine_size,
                auto_suspend_mins=auto_suspend_mins,
            )
        except Exception as e:
            # Prefer richer error messages when available
            error_msg = None

            # EngineProvisioningFailed has a format_message() method that provides better error details
            if hasattr(e, "format_message"):
                try:
                    error_msg = getattr(e, "format_message")()
                except Exception:
                    pass

            # Try content/message fallbacks
            if not error_msg and hasattr(e, "content"):
                error_msg = getattr(e, "content", None)
            if not error_msg and hasattr(e, "message"):
                error_msg = str(getattr(e, "message", ""))
            if not error_msg:
                error_msg = str(e)

            raise Exception(error_msg)

#--------------------------------------------------
# Tables
#--------------------------------------------------

def get_color_by_state(state: str) -> str:
    if state and isinstance(state, str):
        state_lower = state.lower()
        if state_lower in ("aborted", "quarantined"):
            return "red"
        elif state_lower == "completed":
            return "white"
        elif state_lower in ("running", "cancelling", "syncing", "pending", "processing"):
            return "bold yellow"
        elif state_lower == "suspended":
            return "dim"
        else:
            return ""
    return ""

def format_value(value) -> str:
    if value is None:
        return "N/A"
    elif isinstance(value, (int, float)):
        return f"{value}"
    elif isinstance(value, list):
        return ", ".join(map(str, value))
    elif isinstance(value, bool):
        return f"{value}"
    elif isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(value, timedelta):
        return humanized_duration(int(value.total_seconds() * 1000))
    else:
        return str(value)

def format_row(key: str, value) -> dict:
    result = {}
    result[key] = value
    if "status" in key.lower() or "state" in key.lower():
        result["style"] = get_color_by_state(value)
    if key == "query_size" and isinstance(value, int):
        result[key] = humanized_bytes(value)
    else:
        result[key] = format_value(value)
    return result

def show_dictionary_table(dict, format_fn:Callable|None=None):
    table = Table(show_header=True, border_style="dim", header_style="bold", box=rich_box.SIMPLE_HEAD)
    table.add_column("Field")
    table.add_column("Value")
    for key, value in dict.items():
        if format_fn:
            row = format_fn(key, value)
            table.add_row(key, row.get(key), style=row.get("style"))
        else:
            table.add_row(key, value)
    rich.print(table)

#--------------------------------------------------
# Custom help printer
#--------------------------------------------------


class RichGroup(click.Group):
    def invoke(self, ctx: Context) -> Any:
        """Invoke the CLI command, suppressing tracebacks for handled RAIExceptions.

        Any `RAIException` is expected to already know how to render itself nicely via
        `pprint()`. When such an exception bubbles up to the top-level Click runner,
        Click will otherwise print a full Python traceback, which is noisy for users.
        """
        try:
            return super().invoke(ctx)
        except RAIException as exc:
            # Respect config-based full-trace setting when available.
            try:
                show_full_traces = get_config().get("show_full_traces", SHOW_FULL_TRACES)
            except Exception:
                show_full_traces = SHOW_FULL_TRACES

            if show_full_traces:
                raise

            exc.pprint()
            raise click.exceptions.Exit(1) from None

    def format_help(self, ctx: Context, formatter: HelpFormatter) -> None:
        is_latest, current_ver, latest_ver = is_latest_cli_version()

        global PROFILE
        # @NOTE: I couldn't find a sane way to access the --profile option from here, so insane it is.
        if "--profile" in sys.argv:
            ix = sys.argv.index("--profile") + 1
            if ix < len(sys.argv):
                PROFILE = sys.argv[ix]

        profile = get_config().profile
        if profile == TOP_LEVEL_PROFILE_NAME:
            profile = "[yellow bold]None[/yellow bold]" if not get_config().get("platform", "") else "[ROOT]"

        sio = io.StringIO()
        console = Console(file=sio, force_terminal=True)
        divider(console)
        console.print(f"[bold]Welcome to [green]RelationalAI[/bold] ({current_ver})!")
        console.print()
        if not is_latest:
            console.print(f"[yellow]A new version of RelationalAI is available: {latest_ver}[/yellow] ")
            console.print()
        console.print("rai [magenta]\\[options][/magenta] [cyan]command[/cyan]")

        console.print()
        console.print(f"[magenta]--profile[/magenta][dim] - which config profile to use (current: [/dim][cyan]{profile}[/cyan][dim])")

        unavailable_commands = []
        groups = defaultdict(list)
        for command in self.commands.keys():
            if ":" in command:
                group, _, _ = command.rpartition(":")
                groups[group].append(command)
            else:
                groups[""].append(command)

        console.print()
        for command in groups[""]:
            console.print(f"[cyan]{command}[/cyan][dim] - {self.commands[command].help}")

        for group, commands in groups.items():
            if not group:
                continue

            empty = True
            for command in commands:
                if command_available(self.commands[command]):
                    if empty:
                        empty = False
                        console.print()

                    console.print(f"[cyan]{command}[/cyan][dim] - {self.commands[command].help}")
                else:
                    unavailable_commands.append(command)

        if unavailable_commands:
            platform = get_config().get("platform", "")
            console.print()
            console.print(f"[yellow]Not available on {platform}[/yellow]")
            console.print()
            for command in unavailable_commands:
                console.print(f"[dim yellow]{command} - {self.commands[command].help}")

        divider(console)
        formatter.write(sio.getvalue())
        sio.close()

def filter_profiles_by_platform(config:ConfigFile, platform:str):
    filtered_config = {}
    for profile, props in config.get_combined_profiles().items():
        if profile == TOP_LEVEL_PROFILE_NAME:
            continue
        if props.get("platform") == platform or (
            props.get("platform") is None
            and platform == "azure"
        ):
            filtered_config[profile] = props
    return filtered_config

#--------------------------------------------------
# Imports list
#--------------------------------------------------

def show_imports(imports, showId=False):
    ensure_config()
    if len(imports):
        table = Table(show_header=True, border_style="dim", header_style="bold", box=rich_box.SIMPLE_HEAD)
        cols = {"#": "index"}
        if showId and len(imports) and "id" in imports[0]:
            cols["ID"] = "id"
        if len(imports) and "name" in imports[0]:
            cols["Name"] = "name"
        if len(imports) and "model" in imports[0]:
            cols["Model"] = "model"
        if len(imports) and "created" in imports[0]:
            cols["Created"] = "created"
        if len(imports) and "creator" in imports[0]:
            cols["Creator"] = "creator"
        if len(imports) and "batches" in imports[0]:
            cols["Batches"] = "batches"
        if len(imports) and "status" in imports[0]:
            cols["Status"] = "status"
        if len(imports) and "errors" in imports[0]:
            cols["Errors"] = "errors"

        for label in cols.keys():
            table.add_column(label)

        for index, imp in enumerate(imports):
            imp["index"] = f"{index+1}"
            style = get_color_by_state(imp["status"])
            if imp["created"]:
                imp["created"] = format_value(imp["created"])
            table.add_row(*[imp.get(attr, None) for attr in cols.values()], style=style)
        rich.print(table)
    else:
        rich.print("[yellow]No imports found")

#--------------------------------------------------
# Transactions
#--------------------------------------------------

def show_transactions(transactions, limit):
    if len(transactions):
        table = Table(show_header=True, border_style="dim", header_style="bold", box=rich_box.SIMPLE_HEAD)
        table.add_column("#")
        table.add_column("ID")
        table.add_column("Schema")
        table.add_column("Engine")
        table.add_column("State")
        table.add_column("Created")
        table.add_column("Duration", justify="right")

        added = 0
        for i, txn in enumerate(transactions):
            if added >= limit:
                break

            state = txn.get("state", "")
            duration = txn.get("duration")
            created_on = txn.get("created_on")

            if isinstance(created_on, int):
                created_on = datetime.fromtimestamp(created_on / 1000, tz=pytz.utc)
            if duration is None:
                duration = (datetime.now(created_on.tzinfo) - created_on).total_seconds() * 1000

            table.add_row(
                f"{i+1}",
                txn.get("id"),
                txn.get("database", ""),
                txn.get("engine", ""),
                state,
                created_on.strftime("%Y-%m-%d %H:%M:%S"),
                humanized_duration(int(duration)),
                style=get_color_by_state(state)
            )
            added += 1
        rich.print(table)
    else:
        rich.print("[yellow]No transactions found")

def show_engines(engines):
    if len(engines):
        table = Table(show_header=True, border_style="dim", header_style="bold", box=rich_box.SIMPLE_HEAD)
        table.add_column("#")
        table.add_column("Name")
        # Show type column if present
        table.add_column("Type")
        table.add_column("Size")
        table.add_column("State")
        table.add_column("Created By")
        table.add_column("Created On")
        EngineType = _get_engine_type_api()
        for index, engine in enumerate(engines):
            engine_type = engine.get("type", "")
            type_display = EngineType.get_label_with_value(engine_type) if engine_type and EngineType.is_valid(engine_type) else (engine_type or "")
            created_on = format_value(engine.get("created_on"))
            state_display = format_state_with_color(engine.get("state", ""))
            table.add_row(
                f"{index+1}",
                engine.get("name"),
                type_display,
                engine.get("size"),
                state_display,
                engine.get("created_by", ""),
                created_on,
            )
        rich.print(table)


def show_engine_details(engine: dict[str, Any]) -> None:
    """Print a vertical table of engine details (one field per row)."""
    from relationalai.clients.resources.snowflake import EngineType as _EngineType

    table = Table(
        show_header=True,
        border_style="dim",
        header_style="bold",
        box=rich_box.SIMPLE_HEAD,
    )
    table.add_column("Field")
    table.add_column("Value", overflow="fold")

    engine_type_from_db = engine.get("type", "")
    type_display = (
        _EngineType.get_label_with_value(engine_type_from_db)
        if engine_type_from_db and _EngineType.is_valid(engine_type_from_db)
        else engine_type_from_db
    )

    rows: list[tuple[str, str]] = [
        ("Name", str(engine.get("name", ""))),
        ("Type", str(type_display)),
        ("Size", str(engine.get("size", ""))),
        ("State", str(format_state_with_color(engine.get("state", "")))),
        ("Created By", str(engine.get("created_by", ""))),
        ("Created On", str(format_value(engine.get("created_on")))),
    ]

    # Optional fields (may not exist on older backends).
    for key, label, formatter in [
        ("version", "Version", lambda v: "" if v is None else str(v)),
        ("updated_on", "Updated On", format_value),
        ("suspends_at", "Suspends At", format_value),
    ]:
        if key in engine:
            try:
                val = engine.get(key)
                rows.append((label, str(formatter(val))))
            except Exception:
                rows.append((label, str(engine.get(key))))

    # Auto-suspend minutes is represented differently across backends:
    # - list_engines tends to return auto_suspend_mins
    # - get_engine (Snowflake EngineServiceSQL) returns auto_suspend
    if "auto_suspend_mins" in engine or "auto_suspend" in engine:
        auto_suspend_val = engine.get("auto_suspend_mins", engine.get("auto_suspend"))
        rows.append(("Auto Suspend (mins)", "" if auto_suspend_val is None else str(auto_suspend_val)))

    settings = engine.get("settings")
    if settings in (None, {}, ""):
        settings_str = ""
    elif isinstance(settings, dict):
        settings_str = json.dumps(settings, indent=2, sort_keys=True)
    else:
        settings_str = str(settings)
    rows.append(("Settings", settings_str))

    for field, value in rows:
        table.add_row(field, value)

    rich.print(table)

def exit_with_error(message: str) -> NoReturn:
    rich.print(message, file=sys.stderr)
    exit_with_divider(1)

def exit_with_handled_exception(context: str, exc: Exception) -> NoReturn:
    """Exit with a nicely formatted message for handled RAIExceptions.

    - If `exc` is a RAIException (i.e. produced by an error handler), print its rich
        formatted content via `exc.pprint()`.
    - Otherwise, print a raw one-line error including the context and exception string.
    """
    if isinstance(exc, RAIException):
        exc.pprint()
        sys.exit(1)
    exit_with_error(f"\n\n[yellow]{context}: {exc}")

def exit_with_divider(exit_code: int = 0) -> NoReturn:
    divider()
    sys.exit(exit_code)
