def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple.
    
    Example: '#FF5733' -> (255, 87, 51)
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return None


def rgb_to_hex(r, g, b):
    """Convert RGB values to hex color.
    
    Example: (255, 87, 51) -> '#FF5733'
    """
    return f"#{r:02x}{g:02x}{b:02x}".upper()


def is_valid_color(color):
    """Check if a color is valid (hex, rgb, or named)."""
    import re
    
    # Check hex
    if re.match(r'^#?[0-9a-fA-F]{6}$', color):
        return True
    # Check rgb format
    if re.match(r'^rgb\(\d{1,3},\s*\d{1,3},\s*\d{1,3}\)$', color):
        return True
    # Check named colors
    named_colors = ['red', 'blue', 'green', 'black', 'white', 'yellow', 'cyan', 'magenta']
    if color.lower() in named_colors:
        return True
    
    return False


def random_color():
    """Generate a random hex color."""
    import random
    return f"#{random.randint(0, 0xFFFFFF):06x}"


def color_name_to_hex(color_name):
    """Convert color name to hex code."""
    colors = {
        'red': '#FF0000',
        'green': '#00FF00',
        'blue': '#0000FF',
        'white': '#FFFFFF',
        'black': '#000000',
        'yellow': '#FFFF00',
        'cyan': '#00FFFF',
        'magenta': '#FF00FF',
        'orange': '#FFA500',
        'purple': '#800080',
        'pink': '#FFC0CB',
        'brown': '#A52A2A',
        'gray': '#808080',
        'grey': '#808080',
    }
    return colors.get(color_name.lower())


def lighten_color(hex_color, amount=0.2):
    """Lighten a hex color by a percentage (0-1)."""
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return None
    
    r, g, b = rgb
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    
    return rgb_to_hex(r, g, b)


def darken_color(hex_color, amount=0.2):
    """Darken a hex color by a percentage (0-1)."""
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return None
    
    r, g, b = rgb
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))
    
    return rgb_to_hex(r, g, b)


def complementary_color(hex_color):
    """Get the complementary (opposite) color."""
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return None
    
    r, g, b = rgb
    return rgb_to_hex(255 - r, 255 - g, 255 - b)


def get_color_brightness(hex_color):
    """Get brightness of a color (0-255 scale)."""
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return None
    
    r, g, b = rgb
    return (r * 299 + g * 587 + b * 114) // 1000


def is_light_color(hex_color):
    """Check if a color is light (brightness > 128)."""
    brightness = get_color_brightness(hex_color)
    return brightness is not None and brightness > 128


def is_dark_color(hex_color):
    """Check if a color is dark (brightness <= 128)."""
    brightness = get_color_brightness(hex_color)
    return brightness is not None and brightness <= 128
