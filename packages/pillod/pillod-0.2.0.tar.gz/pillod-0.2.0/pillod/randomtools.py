import random
import string


def random_int(min_value, max_value):
    """Generate a random integer between min and max (inclusive)."""
    return random.randint(min_value, max_value)


def random_float(min_value=0.0, max_value=1.0):
    """Generate a random float between min and max."""
    return random.uniform(min_value, max_value)


def random_choice(items):
    """Select a random item from a list."""
    return random.choice(items)


def random_sample(items, n):
    """Select n random items from a list without replacement."""
    return random.sample(items, min(n, len(items)))


def shuffle_list(items):
    """Shuffle a list in place and return it."""
    random.shuffle(items)
    return items


def random_string(length, include_digits=True, include_special=False):
    """Generate a random string of specified length.
    
    Args:
        length: Length of the string
        include_digits: Include digits (default: True)
        include_special: Include special characters (default: False)
    """
    chars = string.ascii_letters
    if include_digits:
        chars += string.digits
    if include_special:
        chars += string.punctuation
    
    return ''.join(random.choice(chars) for _ in range(length))


def random_password(length=12):
    """Generate a random secure password."""
    if length < 4:
        length = 4
    
    # Ensure at least one of each type
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice(string.punctuation)
    ]
    
    # Fill the rest randomly
    all_chars = string.ascii_letters + string.digits + string.punctuation
    password.extend(random.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle to avoid predictable pattern
    random.shuffle(password)
    return ''.join(password)


def random_hex_color():
    """Generate a random hex color code."""
    return f"#{random.randint(0, 0xFFFFFF):06x}"


def random_boolean():
    """Generate a random boolean value."""
    return random.choice([True, False])


def weighted_choice(items, weights):
    """Select a random item with weighted probabilities.
    
    Args:
        items: List of items to choose from
        weights: List of weights corresponding to each item
    """
    return random.choices(items, weights=weights)[0]


def coin_flip():
    """Simulate a coin flip. Returns 'heads' or 'tails'."""
    return random.choice(['heads', 'tails'])


def dice_roll(sides=6):
    """Simulate rolling a dice with specified number of sides."""
    return random.randint(1, sides)


def random_date(start_year=2020, end_year=2026):
    """Generate a random date between start and end year."""
    from datetime import datetime, timedelta
    
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    
    time_between = end - start
    days_between = time_between.days
    random_days = random.randrange(days_between)
    
    random_date = start + timedelta(days=random_days)
    return random_date.strftime('%Y-%m-%d')
