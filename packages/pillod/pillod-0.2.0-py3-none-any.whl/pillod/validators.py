import re


def is_email(email):
    """Validate if a string is a valid email address."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_url(url):
    """Validate if a string is a valid URL."""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def is_phone_number(phone, country='US'):
    """Validate if a string is a valid phone number.
    
    Args:
        phone: Phone number string
        country: 'US' for US format (default), 'INTL' for international
    """
    if country == 'US':
        # Matches: (123) 456-7890, 123-456-7890, 1234567890
        pattern = r'^(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}$'
    else:
        # Basic international format
        pattern = r'^\+?[1-9]\d{1,14}$'
    
    return bool(re.match(pattern, phone.strip()))


def is_zipcode(zipcode, country='US'):
    """Validate if a string is a valid ZIP/postal code.
    
    Args:
        zipcode: ZIP code string
        country: Country code - 'US', 'CA', 'UK', 'AU', 'DE', 'FR', 'JP', 'IN', 'NL', 'BE'
                 'US' is default
    """
    zipcode = zipcode.strip()
    
    patterns = {
        'US': r'^\d{5}(-\d{4})?$',                              # 12345 or 12345-6789
        'CA': r'^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$',          # A1A 1A1
        'UK': r'^[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}$',             # SW1A 1AA
        'AU': r'^\d{4}$',                                       # 2000
        'DE': r'^\d{5}$',                                       # 10115
        'FR': r'^\d{5}$',                                       # 75001
        'JP': r'^\d{3}-\d{4}$',                                 # 100-0001
        'IN': r'^\d{6}$',                                       # 110001
        'NL': r'^\d{4}\s?[A-Z]{2}$',                            # 1012 AB
        'BE': r'^\d{4}$',                                       # 1000
        'ES': r'^\d{5}$',                                       # 28001
        'IT': r'^\d{5}$',                                       # 00100
        'BR': r'^\d{5}-?\d{3}$',                                # 01310-100
        'MX': r'^\d{5}$',                                       # 06500
        'ZA': r'^\d{4}$',                                       # 0001
        'NZ': r'^\d{4}$',                                       # 1010
    }
    
    if country not in patterns:
        return False
    
    return bool(re.match(patterns[country], zipcode))


def is_credit_card(card_number):
    """Validate credit card number using Luhn algorithm."""
    card_number = card_number.replace(' ', '').replace('-', '')
    
    if not card_number.isdigit() or len(card_number) < 13 or len(card_number) > 19:
        return False
    
    # Luhn algorithm
    total = 0
    reverse_digits = card_number[::-1]
    
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    
    return total % 10 == 0


def is_ip_address(ip, version=4):
    """Validate if a string is a valid IP address.
    
    Args:
        ip: IP address string
        version: 4 for IPv4 (default), 6 for IPv6
    """
    if version == 4:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    elif version == 6:
        # Simplified IPv6 validation
        pattern = r'^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|::)$'
        return bool(re.match(pattern, ip))
    
    return False


def is_strong_password(password, min_length=8):
    """Check if a password is strong.
    
    Strong password criteria:
    - At least min_length characters
    - Contains uppercase and lowercase letters
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(password) < min_length:
        return False
    
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    
    return has_upper and has_lower and has_digit and has_special


def is_username(username, min_length=3, max_length=20):
    """Validate username (alphanumeric, underscores, hyphens only)."""
    pattern = f'^[a-zA-Z0-9_-]{{{min_length},{max_length}}}$'
    return bool(re.match(pattern, username))


def is_hex_color(color):
    """Validate if a string is a valid hex color code."""
    pattern = r'^#?([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$'
    return bool(re.match(pattern, color))


def is_numeric(value):
    """Check if a string represents a numeric value."""
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_alpha(text):
    """Check if a string contains only alphabetic characters."""
    return text.isalpha()


def is_alphanumeric(text):
    """Check if a string contains only alphanumeric characters."""
    return text.isalnum()
