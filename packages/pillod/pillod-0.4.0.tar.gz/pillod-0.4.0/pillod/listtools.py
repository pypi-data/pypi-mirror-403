def remove_duplicates(items):
    """Remove duplicate items from a list while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def chunk_list(items, chunk_size):
    """Split a list into chunks of specified size."""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def flatten(nested_list):
    """Flatten a nested list one level deep."""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


def deep_flatten(nested_list):
    """Recursively flatten a deeply nested list."""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(deep_flatten(item))
        else:
            result.append(item)
    return result


def rotate_list(items, n):
    """Rotate a list by n positions to the right."""
    if not items:
        return items
    n = n % len(items)
    return items[-n:] + items[:-n]


def find_duplicates(items):
    """Find all duplicate items in a list."""
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)


def group_by(items, key_func):
    """Group items by a key function.
    
    Args:
        items: List of items to group
        key_func: Function that returns the grouping key for each item
        
    Returns:
        Dictionary mapping keys to lists of items
    """
    groups = {}
    for item in items:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups


def intersection(list1, list2):
    """Find common elements in two lists."""
    return list(set(list1) & set(list2))


def union(list1, list2):
    """Combine two lists removing duplicates."""
    return list(set(list1) | set(list2))


def difference(list1, list2):
    """Find elements in list1 that are not in list2."""
    return list(set(list1) - set(list2))


def partition(items, predicate):
    """Partition a list into two lists based on a predicate function.
    
    Returns:
        Tuple of (items where predicate is True, items where predicate is False)
    """
    true_items = []
    false_items = []
    for item in items:
        if predicate(item):
            true_items.append(item)
        else:
            false_items.append(item)
    return true_items, false_items


def take(items, n):
    """Take the first n items from a list."""
    return items[:n]


def drop(items, n):
    """Drop the first n items from a list."""
    return items[n:]


def compact(items):
    """Remove None, False, 0, and empty strings from a list."""
    return [item for item in items if item]
