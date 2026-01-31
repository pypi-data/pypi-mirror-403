# Pillod - Python Utility Library

A comprehensive Python utility library providing 17 powerful modules with 200+ functions for common programming tasks.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Modules Overview](#modules-overview)
- [Module Documentation](#module-documentation)
- [Examples](#examples)

## Installation

Simply import the pillod package in your Python code:

```python
import pillod
```

All submodules are automatically loaded, making all utilities accessible via `pillod.modulename.function()`.

## Quick Start

```python
import pillod

# Parser tools - validated user input
age = pillod.parsertools.ask_int("Enter your age: ", 0, 150)

# String tools - string manipulation
name = pillod.stringtools.to_title_case("john doe")

# Math tools - mathematical operations
result = pillod.mathtools.factorial(5)

# Validators - check if data is valid
if pillod.validators.is_email("user@example.com"):
    print("Valid email!")

# Random tools - generate random data
password = pillod.randomtools.random_password()

# Date tools - date/time operations
today = pillod.datetools.current_date()

# List tools - work with lists
unique = pillod.listtools.remove_duplicates([1, 2, 2, 3])

# File tools - file operations
content = pillod.filetools.read_file("path/to/file.txt")

# Config tools - configuration management
config = pillod.configtools.load_json_config("config.json")
```

## Modules Overview

| Module | Purpose | Functions |
|--------|---------|-----------|
| **parsertools** | User input with validation | `ask_int()`, `ask_float()`, `ask_yes_no()`, `ask_choice()`, `ask_string()` |
| **stringtools** | String manipulation | 14 functions for case conversion, truncation, palindromes, etc. |
| **mathtools** | Math operations | 15 functions for statistics, primes, temperature conversion, etc. |
| **listtools** | List operations | 15 functions for grouping, chunking, filtering, set operations, etc. |
| **validators** | Data validation | 15 functions for emails, URLs, passwords, credit cards, postal codes, etc. |
| **datetools** | Date/time utilities | 18 functions for formatting, parsing, calculating differences, etc. |
| **randomtools** | Random generation | 15 functions for random numbers, strings, passwords, colors, dates, etc. |
| **filetools** | File operations | 13 functions for reading, writing, copying, deleting files, etc. |
| **configtools** | Configuration tools | 6 functions for loading/saving JSON, key-value configs, etc. |
| **dicttools** | Dictionary operations | 15 functions for merging, filtering, flattening, nested access, etc. |
| **hashtools** | Hashing and checksums | 8 functions for MD5, SHA256, file hashing, password hashing, etc. |
| **jsontools** | JSON utilities | 11 functions for formatting, validation, file operations, etc. |
| **pathtools** | Path operations | 17 functions for cross-platform path handling, extensions, etc. |
| **regextools** | Regex helpers | 19 functions for pattern matching, extraction, replacement, etc. |
| **colortools** | Color utilities | 10 functions for hex/RGB conversion, brightness, complementary colors, etc. |
| **sorttools** | Advanced sorting | 11 functions for custom sorting, natural sort, multi-key sort, etc. |
| **encryptiontools** | Encryption utilities | 12 functions for base64, ciphers, password hashing, etc. |

---

## Module Documentation

### parsertools

**Purpose**: Safely get validated input from users

```python
# Get integer with range validation
age = pillod.parsertools.ask_int("Enter age: ", 0, 120)

# Get float with optional bounds
height = pillod.parsertools.ask_float("Enter height (m): ", 0, 3)

# Get yes/no answer
proceed = pillod.parsertools.ask_yes_no("Continue?")  # Returns True/False

# Get choice from list
color = pillod.parsertools.ask_choice("Pick a color:", ["Red", "Blue", "Green"])

# Get string with length validation
name = pillod.parsertools.ask_string("Enter name: ", min_length=2, max_length=50)
```

### stringtools

**Purpose**: String manipulation and transformations

```python
# Case conversions
pillod.stringtools.to_title_case("hello world")        # "Hello World"
pillod.stringtools.to_snake_case("HelloWorld")         # "hello_world"
pillod.stringtools.to_camel_case("hello_world")        # "helloWorld"

# String operations
pillod.stringtools.reverse_string("hello")             # "olleh"
pillod.stringtools.count_words("hello world")          # 2
pillod.stringtools.truncate("hello world", 8)          # "hello..."
pillod.stringtools.remove_punctuation("hello, world!")  # "hello world"

# Validation
pillod.stringtools.is_palindrome("racecar")            # True
pillod.stringtools.count_char("hello", "l")            # 2

# Utilities
pillod.stringtools.trim_whitespace("  hello  ")        # "hello"
pillod.stringtools.replace_all("aaa", "a", "b")        # "bbb"
pillod.stringtools.split_by_delimiter("a,b,c", ",")    # ["a", "b", "c"]
pillod.stringtools.join_with_delimiter(["a", "b"], "-") # "a-b"
```

### mathtools

**Purpose**: Mathematical calculations and operations

```python
# Statistics
pillod.mathtools.average([1, 2, 3])                    # 2.0
pillod.mathtools.median([1, 2, 3])                     # 2
pillod.mathtools.std_deviation([1, 2, 3])              # 1.0

# Number checks
pillod.mathtools.is_prime(17)                          # True
pillod.mathtools.clamp(150, 0, 100)                    # 100

# Calculations
pillod.mathtools.percentage(25, 100)                   # 25.0
pillod.mathtools.percentage_change(100, 150)           # 50.0
pillod.mathtools.factorial(5)                          # 120
pillod.mathtools.fibonacci(7)                          # [0, 1, 1, 2, 3, 5, 8]

# GCD/LCM
pillod.mathtools.gcd(12, 8)                            # 4
pillod.mathtools.lcm(12, 8)                            # 24

# Conversions
pillod.mathtools.convert_temperature(32, 'F', 'C')     # 0.0
pillod.mathtools.distance_2d(0, 0, 3, 4)               # 5.0
```

### listtools

**Purpose**: List manipulation and transformations

```python
# Remove duplicates
pillod.listtools.remove_duplicates([1, 2, 2, 3])       # [1, 2, 3]

# Chunking and slicing
pillod.listtools.chunk_list([1, 2, 3, 4, 5], 2)       # [[1, 2], [3, 4], [5]]
pillod.listtools.take([1, 2, 3, 4], 2)                 # [1, 2]
pillod.listtools.drop([1, 2, 3, 4], 2)                 # [3, 4]

# Flattening
pillod.listtools.flatten([[1, 2], [3, 4]])             # [1, 2, 3, 4]
pillod.listtools.deep_flatten([[1, [2]], [3, [4]]])    # [1, 2, 3, 4]

# Set operations
pillod.listtools.intersection([1, 2, 3], [2, 3, 4])    # [2, 3]
pillod.listtools.union([1, 2], [2, 3])                 # [1, 2, 3]
pillod.listtools.difference([1, 2, 3], [2])            # [1, 3]

# Finding
pillod.listtools.find_duplicates([1, 2, 2, 3, 3])     # [2, 3]
pillod.listtools.rotate_list([1, 2, 3, 4], 2)         # [3, 4, 1, 2]

# Grouping and partitioning
pillod.listtools.group_by([1, 2, 3, 4], lambda x: x % 2)  # {0: [2, 4], 1: [1, 3]}
true_items, false_items = pillod.listtools.partition([1, 2, 3, 4], lambda x: x > 2)

# Utilities
pillod.listtools.compact([1, None, 2, "", 0, 3])       # [1, 2, 3]
pillod.listtools.shuffle_list([1, 2, 3, 4])            # Shuffled list
```

### validators

**Purpose**: Validate various data formats

```python
# Email and URL
pillod.validators.is_email("user@example.com")         # True
pillod.validators.is_url("https://github.com")         # True

# Phone and postal codes
pillod.validators.is_phone_number("(123) 456-7890")    # True (US)
pillod.validators.is_zipcode("2000", "AU")             # True (Australia)
# Supports: US, CA, UK, AU, DE, FR, JP, IN, NL, BE, ES, IT, BR, MX, ZA, NZ

# Password and username
pillod.validators.is_strong_password("P@ssw0rd!")      # True
pillod.validators.is_username("john_doe")              # True

# Credit card and IP
pillod.validators.is_credit_card("4532-1234-5678-9999") # True (with Luhn check)
pillod.validators.is_ip_address("192.168.1.1")         # True (IPv4)
pillod.validators.is_ip_address("::1", 6)              # True (IPv6)

# Colors and types
pillod.validators.is_hex_color("#FF5733")              # True
pillod.validators.is_numeric("123.45")                 # True
pillod.validators.is_alpha("hello")                    # True
pillod.validators.is_alphanumeric("hello123")          # True
```

### datetools

**Purpose**: Date and time operations

```python
# Current date/time
pillod.datetools.current_date()                        # "2026-01-30"
pillod.datetools.current_time()                        # "14:30:45"
pillod.datetools.current_datetime()                    # "2026-01-30 14:30:45"

# Formatting and parsing
dt = pillod.datetools.parse_datetime("2026-01-30 14:30:45")
pillod.datetools.format_datetime(dt, '%d/%m/%Y')      # "30/01/2026"

# Date arithmetic
pillod.datetools.add_days("2026-01-30", 5)             # 2026-02-04
pillod.datetools.add_hours("2026-01-30 14:00:00", 3)   # 2026-01-30 17:00:00
pillod.datetools.add_minutes("2026-01-30 14:00:00", 30) # 2026-01-30 14:30:00

# Comparisons
pillod.datetools.days_between("2026-01-01", "2026-01-30") # 29
pillod.datetools.is_weekend("2026-01-31")              # True (Saturday)
pillod.datetools.is_leap_year(2024)                    # True

# Utilities
pillod.datetools.get_day_name("2026-01-30")            # "Friday"
pillod.datetools.get_month_name("2026-01-30")          # "January"
pillod.datetools.time_ago("2026-01-30 12:00:00")       # "2 hours ago"
pillod.datetools.start_of_day("2026-01-30 14:30:45")   # 2026-01-30 00:00:00
pillod.datetools.end_of_day("2026-01-30 14:30:45")     # 2026-01-30 23:59:59
```

### randomtools

**Purpose**: Generate random data

```python
# Random numbers
pillod.randomtools.random_int(1, 10)                   # Random int 1-10
pillod.randomtools.random_float(0, 1)                  # Random float 0-1
pillod.randomtools.random_boolean()                    # True or False

# Random selections
pillod.randomtools.random_choice([1, 2, 3, 4])         # Random item
pillod.randomtools.random_sample([1, 2, 3, 4], 2)     # 2 random items
pillod.randomtools.shuffle_list([1, 2, 3, 4])          # Shuffled list

# Random strings
pillod.randomtools.random_string(10)                   # Random alphanumeric
pillod.randomtools.random_password()                   # Secure password
pillod.randomtools.random_hex_color()                  # Random color like "#FF5733"

# Games and simulations
pillod.randomtools.coin_flip()                         # "heads" or "tails"
pillod.randomtools.dice_roll()                         # 1-6
pillod.randomtools.dice_roll(20)                       # 1-20

# Weighted choice
pillod.randomtools.weighted_choice([1, 2, 3], [0.5, 0.3, 0.2])

# Random dates
pillod.randomtools.random_date(2020, 2026)             # Random date 2020-2026
```

### filetools

**Purpose**: File and directory operations

```python
# Read/Write
content = pillod.filetools.read_file("file.txt")
pillod.filetools.write_file("file.txt", "Hello World")
pillod.filetools.append_file("file.txt", "\nNew line")

# Read/Write lines
lines = pillod.filetools.read_lines("file.txt")
pillod.filetools.write_lines("file.txt", ["line1\n", "line2\n"])

# File checks
pillod.filetools.file_exists("file.txt")               # True/False
pillod.filetools.dir_exists("folder")                  # True/False
pillod.filetools.get_file_size("file.txt")             # Size in bytes

# Directory operations
pillod.filetools.create_dir("path/to/folder")
pillod.filetools.list_files("folder")                  # List all files
pillod.filetools.list_files("folder", ".txt")          # List .txt files only

# File operations
pillod.filetools.copy_file("source.txt", "dest.txt")
pillod.filetools.move_file("old.txt", "new.txt")
pillod.filetools.delete_file("file.txt")
```

### configtools

**Purpose**: Configuration file management

```python
# Text config
config = pillod.configtools.configloader("config.txt")

# JSON config
config = pillod.configtools.load_json_config("config.json")
pillod.configtools.save_json_config("config.json", {"key": "value"})

# Key-value config (key=value format)
config = pillod.configtools.parse_key_value_config("config.ini")
pillod.configtools.save_key_value_config("config.ini", {"host": "localhost", "port": "8080"})

# Check if exists
exists = pillod.configtools.config_exists("config.json")
```

### dicttools

**Purpose**: Dictionary manipulation and transformations

```python
# Merge dictionaries
pillod.dicttools.merge_dicts({'a': 1}, {'b': 2})                      # {'a': 1, 'b': 2}

# Filter dictionary
pillod.dicttools.filter_dict({'a': 1, 'b': 2, 'c': 3}, ['a', 'c'])   # {'a': 1, 'c': 3}

# Invert dictionary
pillod.dicttools.invert_dict({'a': 1, 'b': 2})                        # {1: 'a', 2: 'b'}

# Flatten nested dictionary
pillod.dicttools.flatten_dict({'a': {'b': {'c': 1}}})                # {'a_b_c': 1}

# Access nested values
pillod.dicttools.get_nested({'a': {'b': 1}}, ['a', 'b'])              # 1

# Set nested values
pillod.dicttools.set_nested({}, ['a', 'b'], 1)                        # {'a': {'b': 1}}

# Remove None values
pillod.dicttools.remove_none_values({'a': 1, 'b': None})              # {'a': 1}
```

### hashtools

**Purpose**: Cryptographic hashing and checksums

```python
# Hash strings
pillod.hashtools.md5_hash("hello")                                    # "5d41402abc4b2a76b9719d911017c592"
pillod.hashtools.sha256_hash("hello")                                 # "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

# Hash files
pillod.hashtools.file_sha256("document.pdf")                           # "abc123..."

# Verify files match expected hash
pillod.hashtools.verify_file_hash("file.zip", "abc123...", 'sha256')  # True/False

# Password hashing
pillod.hashtools.hash_password("mypassword", 'sha256')                # Hashed password
```

### jsontools

**Purpose**: JSON parsing and formatting utilities

```python
# Pretty print JSON
json_str = '{"name":"John","age":30}'
pillod.jsontools.pretty_print_json(json_str)                          # Formatted with indentation

# Minify JSON
pillod.jsontools.minify_json(json_str)                                # Compact format

# Validate JSON
pillod.jsontools.validate_json(json_str)                              # True/False

# Convert between JSON and dict
pillod.jsontools.json_to_dict(json_str)                               # {'name': 'John', 'age': 30}
pillod.jsontools.dict_to_json({'name': 'John'})                       # '{"name": "John"}'

# Work with JSON files
pillod.jsontools.json_to_file({'key': 'value'}, "config.json")
pillod.jsontools.json_from_file("config.json")                        # Returns dict
```

### pathtools

**Purpose**: Cross-platform path operations

```python
# Path joining (cross-platform)
pillod.pathtools.join_path("home", "user", "file.txt")                # "home/user/file.txt" or "home\\user\\file.txt"

# Path operations
pillod.pathtools.normalize_path("../folder/./file.txt")               # "folder/file.txt"
pillod.pathtools.get_filename("/path/to/file.txt")                    # "file.txt"
pillod.pathtools.get_extension("/path/to/file.txt")                   # ".txt"
pillod.pathtools.get_directory("/path/to/file.txt")                   # "/path/to"

# Absolute/relative paths
pillod.pathtools.resolve_path("./file.txt")                           # "/current/dir/file.txt"
pillod.pathtools.get_relative_path("/home/user/file", "/home")        # "user/file"

# Path checks
pillod.pathtools.path_exists("file.txt")                              # True/False
pillod.pathtools.is_file("file.txt")                                  # True/False
pillo50+ utility functions**  
✅ **17 comprehensive modules**  
✅ **Multi-country support (validators)

**Purpose**: Regular expression helpers

```python
# Find matches
pillod.regextools.find_all_matches(r'\d+', "a1b2c3")                 # ['1', '2', '3']
pillod.regextools.find_first_match(r'\d+', "a1b2c3")                 # '1'

# Replace patterns
pillod.regextools.replace_pattern(r'\d+', 'X', "a1b2c3")             # "aXbXcX"

# Validate and check
pillod.regextools.validate_pattern(r'^\d{3}$', "123")                 # True
pillod.regextools.contains_pattern(r'@', "user@example.com")          # True

# Extract groups
pillod.regextools.extract_groups(r'(\w+)@(\w+)', "user@example")      # ('user', 'example')

# Special finders
pillod.regextools.find_emails("Contact me@example.com or user@test.org") # ['me@example.com', 'user@test.org']
pillod.regextools.find_urls("Visit https://github.com for code")      # ['https://github.com']
```

### colortools

**Purpose**: Color conversion and manipulation

```python
# Color conversions
pillod.colortools.hex_to_rgb("#FF5733")                               # (255, 87, 51)
pillod.colortools.rgb_to_hex(255, 87, 51)                             # "#FF5733"

# Color operations
pillod.colortools.lighten_color("#FF5733", 0.2)                       # Lighter version
pillod.colortools.darken_color("#FF5733", 0.2)                        # Darker version
pillod.colortools.complementary_color("#FF5733")                      # "#00A8CC" (opposite)

# Color checks
pillod.colortools.is_valid_color("#FF5733")                           # True
pillod.colortools.is_light_color("#FFFFFF")                           # True
pillod.colortools.is_dark_color("#000000")                            # True

# Random colors
pillod.colortools.random_color()                                      # "#A1B2C3"
pillod.colortools.color_name_to_hex("red")                            # "#FF0000"
```

### sorttools

**Purpose**: Advanced sorting operations

```python
# Basic sorting
pillod.sorttools.sort_ascending([3, 1, 2])                            # [1, 2, 3]
pillod.sorttools.sort_descending([3, 1, 2])                           # [3, 2, 1]

# Custom sorting
pillod.sorttools.sort_by_key([1, 2, 3], lambda x: -x)                 # [3, 2, 1]
pillod.sorttools.natural_sort(['item1', 'item10', 'item2'])           # ['item1', 'item2', 'item10']
pillod.sorttools.custom_sort(['a', 'b', 'c'], ['c', 'b', 'a'])       # ['c', 'b', 'a']

# Dictionary sorting
pillod.sorttools.sort_dict_by_keys({'c': 1, 'a': 2})                  # {'a': 2, 'c': 1}
pillod.sorttools.sort_dict_by_values({'a': 2, 'b': 1})                # {'b': 1, 'a': 2}

# Special sorts
pillod.sorttools.sort_by_length(['a', 'aaa', 'aa'])                   # ['a', 'aa', 'aaa']
pillod.sorttools.case_insensitive_sort(['Apple', 'apple', 'APPLE'])  # ['Apple', 'apple', 'APPLE']
```

---

## Examples

### Example 1: User Survey Program

```python
import pillod

print("=== Quick Survey ===")

name = pillod.parsertools.ask_string("What's your name? ", min_length=1)
age = pillod.parsertools.ask_int("How old are you? ", 0, 150)
email = pillod.parsertools.ask_string("What's your email? ", min_length=5)

if pillod.validators.is_email(email):
    print(f"Thanks {name}! We'll contact you at {email}")
else:
    print("Invalid email address")

# Save to file
pillod.filetools.write_file("survey_response.txt", 
    f"Name: {name}\nAge: {age}\nEmail: {email}")
```

### Example 2: Password Generator

```python
import pillod

print("=== Password Generator ===")

length = pillod.parsertools.ask_int("Password length (8-32): ", 8, 32)
count = pillod.parsertools.ask_int("How many passwords? ", 1, 10)

passwords = [pillod.randomtools.random_password(length) for _ in range(count)]

for i, pwd in enumerate(passwords, 1):
    print(f"{i}. {pwd}")

# Verify strength
for pwd in passwords:
    is_strong = pillod.validators.is_strong_password(pwd)
    print(f"{pwd} - Strong: {is_strong}")
```

### Example 3: List Analyzer

```python
import pillod

numbers = [1, 2, 2, 3, 4, 4, 5, 6, 6, 7]

print(f"Original: {numbers}")
print(f"Unique: {pillod.listtools.remove_duplicates(numbers)}")
print(f"Duplicates: {pillod.listtools.find_duplicates(numbers)}")
print(f"Average: {pillod.mathtools.average(numbers)}")
print(f"Median: {pillod.mathtools.median(numbers)}")
print(f"Std Dev: {pillod.mathtools.std_deviation(numbers)}")

# Split into even/odd
evens, odds = pillod.listtools.partition(numbers, lambda x: x % 2 == 0)
print(f"Evens: {evens}")
print(f"Odds: {odds}")
```

### Example 4: Configuration Management

```python
import pillod

# Create config
config = {
    "app_name": "MyApp",
    "version": "1.0.0",
    "debug": True,
    "port": 8080
}

# Save to JSON
pillod.configtools.save_json_config("app_config.json", config)

# Load and use
loaded = pillod.configtools.load_json_config("app_config.json")
print(f"Running {loaded['app_name']} v{loaded['version']} on port {loaded['port']}")
```

---

## Features

✅ **100+ utility functions**  
✅ **9 comprehensive modules**  
✅ **Data validation for multiple countries**  
✅ **Easy-to-use API**  
✅ **No external dependencies** (except standard library)  
✅ **Well-documented**  
✅ **Beginner-friendly**  

---

## License

Free to use and modify for any purpose.
