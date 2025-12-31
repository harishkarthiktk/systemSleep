"""Simple config loader for systemSleep project - functions only, no classes"""
import json
import sys
from pathlib import Path


def load_config(config_path="config.json"):
    """Load config from JSON file, return empty dict on failure"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Config file '{config_path}' not found, using defaults", file=sys.stderr)
        return {}
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in '{config_path}': {e}, using defaults", file=sys.stderr)
        return {}


def get_script_config(script_name, config_path="config.json"):
    """Get config section for specific script"""
    config = load_config(config_path)
    return config.get(script_name, {})


def get_setting(script_name, setting_key, default_value, config_path="config.json"):
    """Get single setting with fallback"""
    script_config = get_script_config(script_name, config_path)
    return script_config.get(setting_key, default_value)
