def sort_by_key(items, key_func, reverse=False):
    """Sort a list by a key function.
    
    Args:
        items: List to sort
        key_func: Function that returns sort key for each item
        reverse: Sort descending if True
    """
    return sorted(items, key=key_func, reverse=reverse)


def sort_descending(items):
    """Sort a list in descending order."""
    return sorted(items, reverse=True)


def sort_ascending(items):
    """Sort a list in ascending order."""
    return sorted(items)


def multi_key_sort(items, key_funcs):
    """Sort by multiple keys in order.
    
    Args:
        items: List to sort
        key_funcs: List of (key_function, reverse) tuples
        
    Example: multi_key_sort(people, [(lambda x: x['age'], False), (lambda x: x['name'], False)])
    """
    result = items
    for key_func, reverse in reversed(key_funcs):
        result = sorted(result, key=key_func, reverse=reverse)
    return result


def natural_sort(items):
    """Sort strings naturally (1, 2, 10 instead of 1, 10, 2).
    
    Example: natural_sort(['item1', 'item10', 'item2']) -> ['item1', 'item2', 'item10']
    """
    import re
    
    def natural_key(text):
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(text))]
    
    return sorted(items, key=natural_key)


def custom_sort(items, order):
    """Sort items by a custom order list.
    
    Args:
        items: List to sort
        order: List defining the sort order
        
    Example: custom_sort(['a', 'c', 'b'], ['c', 'b', 'a']) -> ['c', 'b', 'a']
    """
    order_map = {item: idx for idx, item in enumerate(order)}
    return sorted(items, key=lambda x: order_map.get(x, len(order)))


def sort_dict_by_keys(dictionary, reverse=False):
    """Sort dictionary by keys."""
    return dict(sorted(dictionary.items(), key=lambda x: x[0], reverse=reverse))


def sort_dict_by_values(dictionary, reverse=False):
    """Sort dictionary by values."""
    return dict(sorted(dictionary.items(), key=lambda x: x[1], reverse=reverse))


def sort_with_none_last(items, reverse=False):
    """Sort list with None values at the end."""
    return sorted([x for x in items if x is not None], reverse=reverse) + [x for x in items if x is None]


def reverse_sort(items):
    """Reverse the order of items (same as reverse=True in sorted)."""
    return items[::-1]


def case_insensitive_sort(items):
    """Sort strings case-insensitively."""
    return sorted(items, key=str.lower)


def sort_by_length(items, reverse=False):
    """Sort items by length."""
    return sorted(items, key=len, reverse=reverse)
