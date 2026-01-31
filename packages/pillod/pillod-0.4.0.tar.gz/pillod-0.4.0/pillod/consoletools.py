import logging
import sys
from datetime import datetime


def setup_logger(name='app', level='INFO', log_file=None):
    """Set up a basic logger with console and optional file output.
    
    Args:
        name: Logger name (default: 'app')
        level: Log level - 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        log_file: Optional file path to write logs to
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_info(message, logger_name='app'):
    """Quick info log."""
    logging.getLogger(logger_name).info(message)


def log_warning(message, logger_name='app'):
    """Quick warning log."""
    logging.getLogger(logger_name).warning(message)


def log_error(message, logger_name='app'):
    """Quick error log."""
    logging.getLogger(logger_name).error(message)


def log_debug(message, logger_name='app'):
    """Quick debug log."""
    logging.getLogger(logger_name).debug(message)


def print_box(text, width=None, padding=1):
    """Print text in a box.
    
    Args:
        text: Text to display
        width: Box width (None for auto)
        padding: Padding inside box
    """
    lines = text.split('\n')
    max_length = max(len(line) for line in lines)
    
    if width is None:
        width = max_length + (padding * 2)
    
    top = '┌' + '─' * (width + 2) + '┐'
    bottom = '└' + '─' * (width + 2) + '┘'
    
    print(top)
    for line in lines:
        padded = ' ' * padding + line.ljust(max_length) + ' ' * padding
        print(f'│ {padded} │')
    print(bottom)


def print_table(headers, rows, align='left'):
    """Print data as a formatted table.
    
    Args:
        headers: List of column headers
        rows: List of lists containing row data
        align: 'left', 'right', or 'center'
    """
    if not rows:
        print("Empty table")
        return
    
    # Calculate column widths
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Alignment functions
    align_funcs = {
        'left': str.ljust,
        'right': str.rjust,
        'center': str.center
    }
    align_func = align_funcs.get(align, str.ljust)
    
    # Print top border
    top = '┌' + '┬'.join('─' * (w + 2) for w in col_widths) + '┐'
    print(top)
    
    # Print headers
    header_row = '│'
    for i, header in enumerate(headers):
        header_row += ' ' + align_func(str(header), col_widths[i]) + ' │'
    print(header_row)
    
    # Print separator
    separator = '├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤'
    print(separator)
    
    # Print rows
    for row in rows:
        row_str = '│'
        for i, cell in enumerate(row):
            row_str += ' ' + align_func(str(cell), col_widths[i]) + ' │'
        print(row_str)
    
    # Print bottom border
    bottom = '└' + '┴'.join('─' * (w + 2) for w in col_widths) + '┘'
    print(bottom)


def print_colored(text, color='white', background=None):
    """Print colored text (works on terminals that support ANSI codes).
    
    Args:
        text: Text to print
        color: 'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'
        background: Optional background color (same options as color)
    """
    colors = {
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
    }
    
    bg_colors = {
        'black': '\033[40m',
        'red': '\033[41m',
        'green': '\033[42m',
        'yellow': '\033[43m',
        'blue': '\033[44m',
        'magenta': '\033[45m',
        'cyan': '\033[46m',
        'white': '\033[47m',
    }
    
    reset = '\033[0m'
    
    color_code = colors.get(color.lower(), colors['white'])
    bg_code = bg_colors.get(background.lower(), '') if background else ''
    
    print(f"{bg_code}{color_code}{text}{reset}")


def print_success(message):
    """Print success message in green."""
    print_colored(f'✓ {message}', 'green')


def print_error(message):
    """Print error message in red."""
    print_colored(f'✗ {message}', 'red')


def print_warning(message):
    """Print warning message in yellow."""
    print_colored(f'⚠ {message}', 'yellow')


def print_info(message):
    """Print info message in blue."""
    print_colored(f'ℹ {message}', 'blue')


def print_header(text):
    """Print a prominent header."""
    print()
    print('=' * len(text))
    print(text)
    print('=' * len(text))
    print()


def print_separator(char='-', length=50):
    """Print a separator line."""
    print(char * length)


def print_progress_bar(current, total, bar_length=40, prefix='Progress'):
    """Print a progress bar.
    
    Args:
        current: Current progress value
        total: Total value
        bar_length: Length of the progress bar
        prefix: Text before the bar
    """
    percent = 100 * (current / float(total))
    filled = int(bar_length * current // total)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    print(f'\r{prefix}: |{bar}| {percent:.1f}% ({current}/{total})', end='', flush=True)
    
    if current == total:
        print()


def print_key_value(key, value, separator=' : ', key_width=20):
    """Print key-value pairs in aligned format.
    
    Args:
        key: The key/label
        value: The value
        separator: Separator between key and value
        key_width: Width to pad the key to
    """
    print(f"{str(key).ljust(key_width)}{separator}{value}")


def print_list(items, bullet='•', indent=2):
    """Print a bulleted list.
    
    Args:
        items: List of items to print
        bullet: Bullet character
        indent: Spaces before bullet
    """
    for item in items:
        print(' ' * indent + f'{bullet} {item}')


def clear_screen():
    """Clear the console screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def print_timestamp(message='', format='%Y-%m-%d %H:%M:%S'):
    """Print current timestamp with optional message."""
    timestamp = datetime.now().strftime(format)
    if message:
        print(f"[{timestamp}] {message}")
    else:
        print(timestamp)
