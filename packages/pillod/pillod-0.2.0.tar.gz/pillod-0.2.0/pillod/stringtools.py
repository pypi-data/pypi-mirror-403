def trim_whitespace(text):
    """Remove leading and trailing whitespace from text."""
    return text.strip()


def to_title_case(text):
    """Convert text to title case."""
    return text.title()


def to_snake_case(text):
    """Convert text to snake_case."""
    import re
    # Replace spaces and hyphens with underscores
    text = re.sub(r'[-\s]+', '_', text)
    # Insert underscores before capital letters and convert to lowercase
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
    return text.lower()


def to_camel_case(text):
    """Convert text to camelCase."""
    words = text.replace('_', ' ').replace('-', ' ').split()
    if not words:
        return ''
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])


def reverse_string(text):
    """Reverse a string."""
    return text[::-1]


def count_words(text):
    """Count the number of words in text."""
    return len(text.split())


def truncate(text, max_length, suffix='...'):
    """Truncate text to a maximum length, adding suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def remove_punctuation(text):
    """Remove punctuation from text."""
    import string
    return text.translate(str.maketrans('', '', string.punctuation))


def is_palindrome(text):
    """Check if text is a palindrome (ignoring case and spaces)."""
    cleaned = text.lower().replace(' ', '')
    return cleaned == cleaned[::-1]


def count_char(text, char):
    """Count occurrences of a character in text."""
    return text.count(char)


def replace_all(text, old, new):
    """Replace all occurrences of old with new in text."""
    return text.replace(old, new)


def split_by_delimiter(text, delimiter):
    """Split text by a delimiter and return a list."""
    return text.split(delimiter)


def join_with_delimiter(items, delimiter):
    """Join a list of items with a delimiter."""
    return delimiter.join(str(item) for item in items)
