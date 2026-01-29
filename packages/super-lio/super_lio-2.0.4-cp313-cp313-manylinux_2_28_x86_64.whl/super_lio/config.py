"""
YAML Configuration Utilities for Super-LIO

Provides functions to read, modify, and write YAML configuration files.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import shutil
from datetime import datetime


def load_yaml(path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML configuration file.
    
    Args:
        path: Path to the YAML file
        
    Returns:
        Parsed YAML content as a dictionary
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def save_yaml(path: Union[str, Path], data: Dict[str, Any], 
              backup: bool = True) -> None:
    """Save data to a YAML configuration file.
    
    Args:
        path: Path to the YAML file
        data: Data to save
        backup: Whether to create a backup of the original file
    """
    path = Path(path)
    
    # Create backup if file exists and backup is requested
    if backup and path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(f".{timestamp}.yaml.bak")
        shutil.copy2(path, backup_path)
    
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False, indent=2)


def get_nested(data: Dict[str, Any], key: str, 
               default: Any = None) -> Any:
    """Get a nested value from a dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        key: Dot-separated key path (e.g., 'lio.sensor.blind')
        default: Default value if key not found
        
    Returns:
        The value at the specified path, or default if not found
        
    Examples:
        >>> data = {'lio': {'sensor': {'blind': 2.0}}}
        >>> get_nested(data, 'lio.sensor.blind')
        2.0
    """
    keys = key.split('.')
    value = data
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def set_nested(data: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
    """Set a nested value in a dictionary using dot notation.
    
    Args:
        data: Dictionary to modify (will be modified in place)
        key: Dot-separated key path (e.g., 'lio.sensor.blind')
        value: Value to set
        
    Returns:
        The modified dictionary
        
    Examples:
        >>> data = {'lio': {'sensor': {'blind': 2.0}}}
        >>> set_nested(data, 'lio.sensor.blind', 3.0)
        {'lio': {'sensor': {'blind': 3.0}}}
    """
    keys = key.split('.')
    current = data
    
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value
    return data


def parse_value(value_str: str) -> Any:
    """Parse a string value to its appropriate Python type.
    
    Args:
        value_str: String representation of a value
        
    Returns:
        Parsed value (bool, int, float, list, or string)
    """
    value_str = value_str.strip()
    
    # Boolean
    if value_str.lower() in ('true', 'yes', 'on'):
        return True
    if value_str.lower() in ('false', 'no', 'off'):
        return False
    
    # Integer
    try:
        return int(value_str)
    except ValueError:
        pass
    
    # Float
    try:
        return float(value_str)
    except ValueError:
        pass
    
    # List (comma-separated)
    if ',' in value_str:
        items = [parse_value(item) for item in value_str.split(',')]
        return items
    
    # String
    return value_str


def format_yaml(data: Dict[str, Any], indent: int = 0) -> str:
    """Format YAML data for display with proper indentation.
    
    Args:
        data: Dictionary to format
        indent: Current indentation level
        
    Returns:
        Formatted string representation
    """
    return yaml.dump(data, default_flow_style=False, allow_unicode=True,
                     sort_keys=False, indent=2)


def list_keys(data: Dict[str, Any], prefix: str = "") -> List[str]:
    """List all keys in a nested dictionary using dot notation.
    
    Args:
        data: Dictionary to list keys from
        prefix: Current key prefix
        
    Returns:
        List of all keys in dot notation
    """
    keys = []
    
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else k
        keys.append(full_key)
        
        if isinstance(v, dict):
            keys.extend(list_keys(v, full_key))
    
    return keys
