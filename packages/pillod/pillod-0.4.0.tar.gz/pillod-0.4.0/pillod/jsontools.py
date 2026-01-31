import json


def pretty_print_json(json_string, indent=2):
    """Pretty print JSON string with indentation.
    
    Args:
        json_string: JSON string to format
        indent: Number of spaces to indent (default: 2)
    """
    try:
        parsed = json.loads(json_string)
        return json.dumps(parsed, indent=indent)
    except json.JSONDecodeError:
        return None


def minify_json(json_string):
    """Remove whitespace from JSON string to minimize size."""
    try:
        parsed = json.loads(json_string)
        return json.dumps(parsed, separators=(',', ':'))
    except json.JSONDecodeError:
        return None


def validate_json(json_string):
    """Check if a string is valid JSON."""
    try:
        json.loads(json_string)
        return True
    except json.JSONDecodeError:
        return False


def json_to_dict(json_string):
    """Convert JSON string to Python dictionary."""
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        return None


def dict_to_json(dictionary, indent=None):
    """Convert Python dictionary to JSON string.
    
    Args:
        dictionary: Dict to convert
        indent: None for compact, or number for pretty (e.g., 2)
    """
    try:
        return json.dumps(dictionary, indent=indent)
    except (TypeError, ValueError):
        return None


def json_to_file(data, file_path, indent=2):
    """Write Python object to JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent)


def json_from_file(file_path):
    """Read JSON file and return as Python object."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def merge_json(json1, json2):
    """Merge two JSON objects/dicts."""
    dict1 = json_to_dict(json1) if isinstance(json1, str) else json1
    dict2 = json_to_dict(json2) if isinstance(json2, str) else json2
    
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        result = dict1.copy()
        result.update(dict2)
        return result
    return None


def get_json_value(json_string, path):
    """Get a value from JSON using dot notation path.
    
    Example: get_json_value('{"a": {"b": 1}}', 'a.b') -> 1
    """
    data = json_to_dict(json_string) if isinstance(json_string, str) else json_string
    keys = path.split('.')
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


def json_file_size(file_path):
    """Get size of a JSON file in bytes."""
    import os
    return os.path.getsize(file_path)
