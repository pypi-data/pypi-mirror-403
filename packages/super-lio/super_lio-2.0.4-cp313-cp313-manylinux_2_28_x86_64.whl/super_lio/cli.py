"""
CLI Commands for Super-LIO

Provides command-line interfaces for:
- super_lio: Run the main LIO node
- super_reloc: Run the relocation node
- super_lio_config: Manage YAML configuration files
"""

import os
import signal
import shutil
import sys
from pathlib import Path
from typing import Optional, Tuple

import click
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.markup import escape

from .config import (
    load_yaml,
    save_yaml,
    get_nested,
    set_nested,
    parse_value,
    format_yaml,
    list_keys,
)

console = Console()

# ============================================================================
# Config Presets & Resolution
# ============================================================================

# Map of preset names to config file basenames
CONFIG_PRESETS = {
    # LIO configs
    "mid360": "mid_360.yaml",
    "mid_360": "mid_360.yaml",
    "hesai": "hesai.yaml",
    "livox": "livox_360.yaml",
    "livox_360": "livox_360.yaml",
    "r3live": "r3live.yaml",
    "m2dgr": "M2DGR.yaml",
    "mcd": "MCD_ATH.yaml",
    "mcd_ath": "MCD_ATH.yaml",
    "nclt": "NCLT.yaml",
    "ntu": "NTU.yaml",
    # Relocation configs
    "reloc": "relocation.yaml",
    "relocation": "relocation.yaml",
    "reloc_standalone": "relocation_standalone.yaml",
}

# Default preset for each command
DEFAULT_LIO_PRESET = "mid360"
DEFAULT_RELOC_PRESET = "relocation"


def get_config_dir() -> Path:
    """Get the config directory path."""
    # Try relative to package source
    pkg_config = Path(__file__).parent.parent.parent / "src" / "super_lio" / "config"
    if pkg_config.exists():
        return pkg_config
    
    # Try installed locations
    for search_path in [
        Path(__file__).parent.parent / "share" / "super_lio" / "config",
        Path("/usr/local/share/super_lio/config"),
        Path("/usr/share/super_lio/config"),
        Path.home() / ".local/share/super_lio/config",
    ]:
        print(f"Checking {search_path} - exists: {search_path.exists()}")
        if search_path.exists():
            return search_path
    
    return pkg_config  # Return default even if not exists


def resolve_config(name_or_path: str) -> Path:
    """Resolve a config name or path to an actual file path.
    
    Args:
        name_or_path: Either a preset name (e.g., 'mid360') or a file path
        
    Returns:
        Absolute path to the config file
    """
    # Check if it's a direct path
    path = Path(name_or_path)
    if path.exists():
        return path.resolve()
    
    # Check if it's a preset name
    preset_lower = name_or_path.lower()
    if preset_lower in CONFIG_PRESETS:
        config_file = CONFIG_PRESETS[preset_lower]
        config_path = get_config_dir() / config_file
        if config_path.exists():
            return config_path.resolve()
        raise click.ClickException(
            f"Config preset '{name_or_path}' maps to '{config_file}' "
            f"but file not found at {config_path}"
        )
    
    # Check if adding .yaml makes it valid
    yaml_path = get_config_dir() / f"{name_or_path}.yaml"
    if yaml_path.exists():
        return yaml_path.resolve()
    
    raise click.ClickException(
        f"Config not found: '{name_or_path}'\n"
        f"Available presets: {', '.join(sorted(set(CONFIG_PRESETS.keys())))}"
    )


def list_available_configs() -> list:
    """List all available config files."""
    config_dir = get_config_dir()
    if not config_dir.exists():
        return []
    return sorted([f.stem for f in config_dir.glob("*.yaml")])


# ============================================================================
# super_lio command
# ============================================================================

@click.command()
@click.argument('config_name', default=DEFAULT_LIO_PRESET, required=False)
@click.option(
    '--save-map/--no-save-map',
    default=None,
    help='Override map saving setting'
)
@click.option(
    '--map-dir',
    type=click.Path(),
    help='Override map save directory'
)
@click.option(
    '--list', '-l', 'list_configs',
    is_flag=True,
    help='List available config presets'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.version_option(version='2.0.0', prog_name='super_lio')
def main_lio(config_name: str, save_map: Optional[bool], 
             map_dir: Optional[str], list_configs: bool, verbose: bool):
    """Super-LIO: LiDAR-Inertial Odometry
    
    Run the main LIO node for real-time odometry estimation.
    
    CONFIG_NAME can be a preset name (mid360, hesai, livox, etc.) or a file path.
    
    Examples:
    
        super_lio                    # Use default (mid360)
        
        super_lio mid360             # Use mid360 preset
        
        super_lio hesai              # Use hesai preset
        
        super_lio ./my_config.yaml   # Use custom config file
        
        super_lio --list             # Show available presets
    """
    if list_configs:
        console.print("[bold]Available config presets:[/bold]")
        for name in list_available_configs():
            console.print(f"  • {name}")
        return
    
    try:
        from . import SuperLIORunner, params
        
        if SuperLIORunner is None:
            console.print(
                "[red]Error:[/red] Native module not available. "
                "Please ensure the package was built correctly."
            )
            sys.exit(1)
        
        config_path = resolve_config(config_name)
        console.print(f"[green]Config:[/green] {config_path}")
        
        runner = SuperLIORunner()
        
        if not runner.init(str(config_path)):
            console.print("[red]Failed to initialize Super-LIO[/red]")
            sys.exit(1)
        
        if save_map is not None:
            params.set_save_map(save_map)
        
        # Set root dir to current directory for map storage
        params.set_root_dir(str(Path.cwd()) + "/")
        
        console.print("[green]Super-LIO initialized[/green]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]")
        
        def signal_handler(sig, frame):
            console.print("\n[yellow]Shutting down...[/yellow]")
            runner.stop()
            runner.save_map()
            runner.print_time_record()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        runner.start()
        
        while runner.is_running():
            signal.pause()
            
    except ImportError as e:
        console.print(f"[red]Import error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {escape(str(e))}")
        sys.exit(1)


# ============================================================================
# super_reloc command
# ============================================================================

@click.command()
@click.argument('config_name', default=DEFAULT_RELOC_PRESET, required=False)
@click.option(
    '--map', '-m',
    type=click.Path(exists=True),
    help='Path to pre-built map file (PCD)'
)
@click.option(
    '--init-pose',
    type=str,
    help='Initial pose as "x,y,z,roll,pitch,yaw" (degrees)'
)
@click.option(
    '--update-map/--no-update-map',
    default=None,
    help='Whether to update the map during relocation'
)
@click.option(
    '--list', '-l', 'list_configs',
    is_flag=True,
    help='List available config presets'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.version_option(version='2.0.0', prog_name='super_reloc')
def main_reloc(config_name: str, map: Optional[str],
               init_pose: Optional[str], update_map: Optional[bool],
               list_configs: bool, verbose: bool):
    """Super-LIO Relocation
    
    Run the relocation node for localization in a pre-built map.
    
    CONFIG_NAME can be a preset name or a file path.
    
    Examples:
    
        super_reloc                      # Use default relocation config
        
        super_reloc reloc_standalone     # Use standalone relocation
        
        super_reloc --map map.pcd        # Specify map file
        
        super_reloc -m map.pcd --init-pose "0,0,0,0,0,90"
    """
    if list_configs:
        console.print("[bold]Available config presets:[/bold]")
        for name in list_available_configs():
            if 'reloc' in name.lower():
                console.print(f"  • {name}")
        return
    
    try:
        from . import SuperRelocRunner, params
        
        if SuperRelocRunner is None:
            console.print(
                "[red]Error:[/red] Native module not available. "
                "Please ensure the package was built correctly."
            )
            sys.exit(1)
        
        config_path = resolve_config(config_name)
        console.print(f"[green]Config:[/green] {config_path}")
        
        runner = SuperRelocRunner()
        
        if not runner.init(str(config_path)):
            console.print("[red]Failed to initialize Super-LIO Relocation[/red]")
            sys.exit(1)
        
        if update_map is not None:
            params.set_update_map(update_map)
            
        # Set root dir to current directory for map storage
        params.set_root_dir(str(Path.cwd()) + "/")
        
        if init_pose:
            try:
                parts = [float(x) for x in init_pose.split(',')]
                if len(parts) == 6:
                    params.set_init_pose(*parts)
            except ValueError:
                console.print("[yellow]Warning:[/yellow] Could not parse init-pose")
        
        console.print("[green]Super-LIO Relocation initialized[/green]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]")
        
        def signal_handler(sig, frame):
            console.print("\n[yellow]Shutting down...[/yellow]")
            runner.stop()
            runner.save_map()
            runner.print_time_record()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        runner.start()
        
        while runner.is_running():
            signal.pause()
            
    except ImportError as e:
        console.print(f"[red]Import error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


# ============================================================================
# super_lio_config command
# ============================================================================

@click.group()
@click.version_option(version='2.0.0', prog_name='super_lio_config')
def main_config():
    """Super-LIO Configuration Manager
    
    Manage YAML configuration files for Super-LIO.
    
    Use preset names (mid360, hesai, etc.) or file paths.
    
    Examples:
    
        super_lio_config cat mid360
        
        super_lio_config get mid360 lio.sensor.blind
        
        super_lio_config set mid360 lio.sensor.blind 3.0
        
        super_lio_config new mid360           # Copy to current dir
        
        super_lio_config edit mid360 lio.sensor.blind 3.0  # Edit default
    """
    pass


@main_config.command('list')
def config_list():
    """List all available config presets.
    
    Examples:
    
        super_lio_config list
    """
    config_dir = get_config_dir()
    console.print(f"[dim]Config directory: {config_dir}[/dim]\n")
    
    table = Table(title="Available Configurations")
    table.add_column("Name", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Aliases", style="yellow")
    
    # Group presets by file
    file_to_aliases = {}
    for alias, filename in CONFIG_PRESETS.items():
        if filename not in file_to_aliases:
            file_to_aliases[filename] = []
        file_to_aliases[filename].append(alias)
    
    for config_file in sorted(config_dir.glob("*.yaml")):
        name = config_file.stem
        aliases = file_to_aliases.get(config_file.name, [])
        alias_str = ", ".join(aliases) if aliases else "-"
        table.add_row(name, config_file.name, alias_str)
    
    console.print(table)


@main_config.command('new')
@click.argument('config_name')
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output filename (default: same as source)'
)
def config_new(config_name: str, output: Optional[str]):
    """Copy a config preset to current directory for editing.
    
    This creates a local copy that you can modify and use.
    
    Examples:
    
        super_lio_config new mid360              # Creates ./mid_360.yaml
        
        super_lio_config new mid360 -o my.yaml   # Creates ./my.yaml
    """
    try:
        source_path = resolve_config(config_name)
        
        if output:
            dest_path = Path(output)
        else:
            dest_path = Path.cwd() / source_path.name
        
        if dest_path.exists():
            if not click.confirm(f"'{dest_path}' already exists. Overwrite?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        shutil.copy2(source_path, dest_path)
        console.print(f"[green]Created:[/green] {dest_path}")
        console.print(f"[dim]Source: {source_path}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main_config.command('edit')
@click.argument('config_name')
@click.argument('key')
@click.argument('value')
def config_edit(config_name: str, key: str, value: str):
    """Edit a config preset's default value (modifies the source file).
    
    This directly modifies the default config file. A backup is created.
    
    Use dot notation for nested keys: lio.sensor.blind
    
    Examples:
    
        super_lio_config edit mid360 lio.sensor.blind 3.0
        
        super_lio_config edit mid360 lio.map.save_map true
    """
    try:
        config_path = resolve_config(config_name)
        
        # Warn if modifying a system file
        if '/share/' in str(config_path) or config_path.is_relative_to('/usr'):
            console.print(f"[yellow]Warning:[/yellow] Modifying system config: {config_path}")
            if not click.confirm("Continue?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        data = load_yaml(config_path)
        old_value = get_nested(data, key)
        parsed_value = parse_value(value)
        
        set_nested(data, key, parsed_value)
        save_yaml(config_path, data, backup=True)
        
        console.print(f"[green]Updated[/green] {config_path.name}: {key}")
        console.print(f"  [dim]Old:[/dim] {old_value}")
        console.print(f"  [green]New:[/green] {parsed_value}")
        console.print(f"[dim]Backup created[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main_config.command('cat')
@click.argument('config_name')
@click.option(
    '--section', '-s',
    help='Only show specific section (dot notation)'
)
@click.option(
    '--no-color',
    is_flag=True,
    help='Disable syntax highlighting'
)
def config_cat(config_name: str, section: Optional[str], no_color: bool):
    """Display YAML configuration file contents.
    
    Examples:
    
        super_lio_config cat mid360
        
        super_lio_config cat mid360 -s lio.sensor
    """
    try:
        config_path = resolve_config(config_name)
        data = load_yaml(config_path)
        
        console.print(f"[dim]# {config_path}[/dim]\n")
        
        if section:
            data = get_nested(data, section)
            if data is None:
                console.print(f"[red]Section not found:[/red] {section}")
                sys.exit(1)
        
        yaml_str = format_yaml(data if isinstance(data, dict) else {section: data})
        
        if no_color:
            console.print(yaml_str)
        else:
            syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main_config.command('get')
@click.argument('config_name')
@click.argument('key')
def config_get(config_name: str, key: str):
    """Get a configuration value.
    
    Use dot notation for nested keys: lio.sensor.blind
    
    Examples:
    
        super_lio_config get mid360 lio.sensor.blind
        
        super_lio_config get mid360 lio.extrinsic.lidar_imu
    """
    try:
        config_path = resolve_config(config_name)
        data = load_yaml(config_path)
        value = get_nested(data, key)
        
        if value is None:
            console.print(f"[yellow]Key not found:[/yellow] {key}")
            sys.exit(1)
        
        if isinstance(value, (dict, list)):
            console.print(format_yaml(value))
        else:
            console.print(value)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main_config.command('set')
@click.argument('yaml_file', type=click.Path(exists=True))
@click.argument('key')
@click.argument('value')
@click.option(
    '--apply', '-a',
    type=str,
    help='Apply changes to default config and delete local file'
)
@click.option(
    '--no-backup',
    is_flag=True,
    help='Do not create backup'
)
def config_set(yaml_file: str, key: str, value: str, 
               apply: Optional[str], no_backup: bool):
    """Set a value in a local YAML file.
    
    Use --apply to copy changes to default config and delete local file.
    
    Examples:
    
        super_lio_config set ./my.yaml lio.sensor.blind 3.0
        
        super_lio_config set ./my.yaml lio.sensor.blind 3.0 --apply mid360
    """
    try:
        local_path = Path(yaml_file)
        data = load_yaml(local_path)
        old_value = get_nested(data, key)
        parsed_value = parse_value(value)
        
        set_nested(data, key, parsed_value)
        save_yaml(local_path, data, backup=not no_backup)
        
        console.print(f"[green]Updated[/green] {local_path.name}: {key}")
        console.print(f"  [dim]Old:[/dim] {old_value}")
        console.print(f"  [green]New:[/green] {parsed_value}")
        
        # Apply to default config if requested
        if apply:
            default_path = resolve_config(apply)
            default_data = load_yaml(default_path)
            set_nested(default_data, key, parsed_value)
            save_yaml(default_path, default_data, backup=True)
            
            console.print(f"[green]Applied to:[/green] {default_path}")
            
            # Delete local file
            local_path.unlink()
            console.print(f"[dim]Deleted local file: {local_path}[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main_config.command('keys')
@click.argument('config_name')
@click.option(
    '--section', '-s',
    help='Only show keys in specific section'
)
def config_keys(config_name: str, section: Optional[str]):
    """List all keys in a configuration file.
    
    Examples:
    
        super_lio_config keys mid360
        
        super_lio_config keys mid360 -s lio.sensor
    """
    try:
        config_path = resolve_config(config_name)
        data = load_yaml(config_path)
        
        if section:
            data = get_nested(data, section)
            if data is None or not isinstance(data, dict):
                console.print(f"[red]Section not found:[/red] {section}")
                sys.exit(1)
            prefix = section
        else:
            prefix = ""
        
        keys = list_keys(data, prefix)
        
        table = Table(title=f"Keys in {config_path.name}")
        table.add_column("Key", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Value", style="yellow", max_width=50)
        
        full_data = load_yaml(config_path)
        for key in keys:
            value = get_nested(full_data, key)
            type_name = type(value).__name__
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
            table.add_row(key, type_name, value_str)
        
        console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main_config.command('diff')
@click.argument('config1')
@click.argument('config2')
def config_diff(config1: str, config2: str):
    """Show differences between two configurations.
    
    Examples:
    
        super_lio_config diff mid360 hesai
        
        super_lio_config diff mid360 ./my_config.yaml
    """
    try:
        path1 = resolve_config(config1)
        path2 = resolve_config(config2)
        
        data1 = load_yaml(path1)
        data2 = load_yaml(path2)
        
        keys1 = set(list_keys(data1))
        keys2 = set(list_keys(data2))
        all_keys = sorted(keys1 | keys2)
        
        table = Table(title=f"Diff: {path1.name} vs {path2.name}")
        table.add_column("Key", style="cyan")
        table.add_column(path1.name, style="yellow")
        table.add_column(path2.name, style="green")
        
        for key in all_keys:
            val1 = get_nested(data1, key)
            val2 = get_nested(data2, key)
            
            if val1 != val2:
                str1 = str(val1) if val1 is not None else "[dim]<missing>[/dim]"
                str2 = str(val2) if val2 is not None else "[dim]<missing>[/dim]"
                table.add_row(key, str1, str2)
        
        if table.row_count == 0:
            console.print("[green]Configurations are identical[/green]")
        else:
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main_config()
