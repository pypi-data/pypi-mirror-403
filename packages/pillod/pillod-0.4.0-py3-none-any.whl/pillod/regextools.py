import re


def find_all_matches(pattern, text):
    """Find all matches of a regex pattern in text."""
    return re.findall(pattern, text)


def find_first_match(pattern, text):
    """Find the first match of a regex pattern."""
    match = re.search(pattern, text)
    return match.group(0) if match else None


def replace_pattern(pattern, replacement, text):
    """Replace all matches of a pattern with replacement."""
    return re.sub(pattern, replacement, text)


def replace_pattern_count(pattern, replacement, text, count=1):
    """Replace first n matches of a pattern."""
    return re.sub(pattern, replacement, text, count=count)


def validate_pattern(pattern, text):
    """Check if a pattern matches text (full match)."""
    return bool(re.fullmatch(pattern, text))


def contains_pattern(pattern, text):
    """Check if text contains the pattern."""
    return bool(re.search(pattern, text))


def extract_groups(pattern, text):
    """Extract capturing groups from a pattern match.
    
    Returns: Tuple of groups, or None if no match
    """
    match = re.search(pattern, text)
    return match.groups() if match else None


def extract_named_groups(pattern, text):
    """Extract named capturing groups from a pattern.
    
    Returns: Dict of group names to values
    """
    match = re.search(pattern, text)
    return match.groupdict() if match else None


def split_by_pattern(pattern, text):
    """Split text by a regex pattern."""
    return re.split(pattern, text)


def remove_pattern(pattern, text):
    """Remove all matches of a pattern from text."""
    return re.sub(pattern, '', text)


def escape_pattern(text):
    """Escape special regex characters in text."""
    return re.escape(text)


def compile_pattern(pattern):
    """Compile a regex pattern for reuse."""
    return re.compile(pattern)


def find_all_with_compiled(compiled_pattern, text):
    """Find all matches using a compiled pattern."""
    return compiled_pattern.findall(text)


def case_insensitive_search(pattern, text):
    """Search for pattern ignoring case."""
    return re.search(pattern, text, re.IGNORECASE)


def multiline_search(pattern, text):
    """Search with multiline mode (^ and $ match lines)."""
    return re.search(pattern, text, re.MULTILINE)


def find_emails(text):
    """Find all email addresses in text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return find_all_matches(pattern, text)


def find_urls(text):
    """Find all URLs in text."""
    pattern = r'https?://[^\s]+'
    return find_all_matches(pattern, text)


def find_phone_numbers(text):
    """Find all phone numbers in text."""
    pattern = r'\+?1?\d{9,15}'
    return find_all_matches(pattern, text)


def find_numbers(text):
    """Find all numbers in text."""
    pattern = r'-?\d+\.?\d*'
    return find_all_matches(pattern, text)
