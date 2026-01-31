def ask_int(prompt, min_value, max_value):
    while True:
        try:
            value = int(input(prompt))
            if min_value <= value <= max_value:
                return value
            else:
                print(f"Please enter an integer between {min_value} and {max_value}.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")


def ask_float(prompt, min_value=None, max_value=None):
    """Ask user for a float input with optional min/max validation."""
    while True:
        try:
            value = float(input(prompt))
            if min_value is not None and value < min_value:
                print(f"Please enter a number >= {min_value}.")
            elif max_value is not None and value > max_value:
                print(f"Please enter a number <= {max_value}.")
            else:
                return value
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def ask_yes_no(prompt):
    """Ask user for a yes/no answer. Returns True for yes, False for no."""
    while True:
        response = input(prompt + " (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'.")


def ask_choice(prompt, choices):
    """Ask user to choose from a list of options.
    
    Args:
        prompt: The question to ask
        choices: List of valid choices
        
    Returns:
        The selected choice from the list
    """
    print(prompt)
    for i, choice in enumerate(choices, 1):
        print(f"{i}. {choice}")
    
    while True:
        try:
            selection = int(input("Enter choice number: "))
            if 1 <= selection <= len(choices):
                return choices[selection - 1]
            else:
                print(f"Please enter a number between 1 and {len(choices)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def ask_string(prompt, min_length=0, max_length=None):
    """Ask user for a string input with optional length validation."""
    while True:
        value = input(prompt).strip()
        if len(value) < min_length:
            print(f"Input must be at least {min_length} characters long.")
        elif max_length is not None and len(value) > max_length:
            print(f"Input must be at most {max_length} characters long.")
        else:
            return value