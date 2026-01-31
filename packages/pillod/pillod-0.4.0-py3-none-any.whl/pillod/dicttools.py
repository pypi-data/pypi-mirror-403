def merge_dicts(*dicts):
    """Merge multiple dictionaries into one. Later dicts override earlier ones."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def filter_dict(dictionary, keys):
    """Filter a dictionary to only include specified keys."""
    return {k: v for k, v in dictionary.items() if k in keys}


def invert_dict(dictionary):
    """Invert a dictionary (swap keys and values)."""
    return {v: k for k, v in dictionary.items()}


def flatten_dict(dictionary, parent_key='', sep='_'):
    """Flatten a nested dictionary.
    
    Example: {'a': {'b': 1}} -> {'a_b': 1}
    """
    items = []
    for k, v in dictionary.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_nested(dictionary, keys, default=None):
    """Get a nested value from a dictionary using a list of keys.
    
    Example: get_nested({'a': {'b': {'c': 1}}}, ['a', 'b', 'c']) -> 1
    """
    value = dictionary
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return default
        else:
            return default
    return value


def set_nested(dictionary, keys, value):
    """Set a nested value in a dictionary using a list of keys.
    
    Example: set_nested({}, ['a', 'b', 'c'], 1) -> {'a': {'b': {'c': 1}}}
    """
    for key in keys[:-1]:
        dictionary = dictionary.setdefault(key, {})
    dictionary[keys[-1]] = value


def get_dict_values(dictionary, keys, default=None):
    """Get multiple values from a dictionary at once."""
    return [dictionary.get(k, default) for k in keys]


def dict_to_list(dictionary, key_name='key', value_name='value'):
    """Convert a dictionary to a list of dicts with key/value pairs.
    
    Example: {'a': 1, 'b': 2} -> [{'key': 'a', 'value': 1}, {'key': 'b', 'value': 2}]
    """
    return [{key_name: k, value_name: v} for k, v in dictionary.items()]


def list_to_dict(items, key_field, value_field):
    """Convert a list of dicts to a dictionary using specified fields.
    
    Example: [{'id': 1, 'name': 'a'}] with key_field='id', value_field='name' -> {1: 'a'}
    """
    return {item[key_field]: item[value_field] for item in items}


def filter_dict_by_value(dictionary, value):
    """Get all keys that have a specific value."""
    return [k for k, v in dictionary.items() if v == value]


def remove_none_values(dictionary):
    """Remove all entries with None values."""
    return {k: v for k, v in dictionary.items() if v is not None}


def remove_empty_values(dictionary):
    """Remove all entries with empty/falsy values."""
    return {k: v for k, v in dictionary.items() if v}


def dict_difference(dict1, dict2):
    """Find keys that differ between two dictionaries."""
    all_keys = set(dict1.keys()) | set(dict2.keys())
    return {k for k in all_keys if dict1.get(k) != dict2.get(k)}


def dict_intersection(dict1, dict2):
    """Get keys that exist in both dictionaries with same values."""
    return {k: dict1[k] for k in dict1 if k in dict2 and dict1[k] == dict2[k]}
