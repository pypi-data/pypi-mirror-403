import math
import statistics


def average(numbers):
    """Calculate the average of a list of numbers."""
    return sum(numbers) / len(numbers) if numbers else 0


def median(numbers):
    """Calculate the median of a list of numbers."""
    return statistics.median(numbers)


def mode(numbers):
    """Calculate the mode of a list of numbers."""
    try:
        return statistics.mode(numbers)
    except statistics.StatisticsError:
        return None


def std_deviation(numbers):
    """Calculate the standard deviation of a list of numbers."""
    return statistics.stdev(numbers) if len(numbers) > 1 else 0


def clamp(value, min_value, max_value):
    """Clamp a value between min and max."""
    return max(min_value, min(value, max_value))


def percentage(part, whole):
    """Calculate what percentage 'part' is of 'whole'."""
    return (part / whole * 100) if whole != 0 else 0


def percentage_change(old_value, new_value):
    """Calculate the percentage change from old to new value."""
    if old_value == 0:
        return float('inf') if new_value != 0 else 0
    return ((new_value - old_value) / old_value) * 100


def round_to_nearest(value, nearest):
    """Round a value to the nearest multiple of 'nearest'."""
    return round(value / nearest) * nearest


def is_prime(n):
    """Check if a number is prime."""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True


def factorial(n):
    """Calculate the factorial of n."""
    return math.factorial(n)


def fibonacci(n):
    """Generate the first n Fibonacci numbers."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib


def gcd(a, b):
    """Calculate the greatest common divisor of two numbers."""
    return math.gcd(a, b)


def lcm(a, b):
    """Calculate the least common multiple of two numbers."""
    return abs(a * b) // math.gcd(a, b) if a and b else 0


def convert_temperature(value, from_unit, to_unit):
    """Convert temperature between Celsius, Fahrenheit, and Kelvin.
    
    Args:
        value: Temperature value
        from_unit: 'C', 'F', or 'K'
        to_unit: 'C', 'F', or 'K'
    """
    # Convert to Celsius first
    if from_unit == 'F':
        celsius = (value - 32) * 5/9
    elif from_unit == 'K':
        celsius = value - 273.15
    else:
        celsius = value
    
    # Convert from Celsius to target
    if to_unit == 'F':
        return celsius * 9/5 + 32
    elif to_unit == 'K':
        return celsius + 273.15
    else:
        return celsius


def distance_2d(x1, y1, x2, y2):
    """Calculate the Euclidean distance between two 2D points."""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
