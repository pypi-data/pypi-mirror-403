import json
import os


def _get_nested_value(data: dict, keys: list[str]):
    """Retrieve a value from a nested dictionary using dot notation."""
    for key in keys:
        if isinstance(data, list):
            key = int(key)  # Convert to integer if accessing a list
        data = data[key]
    return data


def _set_nested_value(data: dict, keys: list[str], value):
    """Set a value in a nested dictionary using dot notation."""
    for key in keys[:-1]:
        if isinstance(data, list):
            key = int(key)  # Convert to integer if accessing a list
        if key not in data:
            data[key] = {} if keys[keys.index(key) + 1] not in data else []
        data = data[key]
    if isinstance(data, list) and isinstance(value, dict):
        data.append(value)
    else:
        data[keys[-1]] = value


def get_from_json(filename: str, field: str):
    """Get a value from a JSON file using dot notation."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist.")

    with open(filename, "r") as file:
        data = json.load(file)

    keys = field.split(".")
    return _get_nested_value(data, keys)


def set_json_value(filename: str, field: str, value):
    """Set a value in a JSON file using dot notation."""
    if os.path.exists(filename):
        with open(filename, "r") as file:
            data = json.load(file)
    else:
        data = {}

    keys = field.split(".")
    _set_nested_value(data, keys, value)

    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
