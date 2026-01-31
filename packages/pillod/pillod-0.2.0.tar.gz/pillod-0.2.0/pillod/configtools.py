import json
import os


def configloader(config_path):
    """Load configuration file as raw text."""
    with open(config_path, 'r') as file:
        config_data = file.read()
    return config_data


def load_json_config(config_path):
    """Load JSON configuration file and return as dictionary."""
    with open(config_path, 'r') as file:
        return json.load(file)


def save_json_config(config_path, config_dict):
    """Save dictionary as JSON configuration file."""
    with open(config_path, 'w') as file:
        json.dump(config_dict, file, indent=4)


def parse_key_value_config(config_path, delimiter='='):
    """Parse a key=value style configuration file.
    
    Args:
        config_path: Path to the config file
        delimiter: Character separating keys and values (default: '=')
        
    Returns:
        Dictionary of configuration key-value pairs
    """
    config = {}
    with open(config_path, 'r') as file:
        for line in file:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            if delimiter in line:
                key, value = line.split(delimiter, 1)
                config[key.strip()] = value.strip()
    
    return config


def save_key_value_config(config_path, config_dict, delimiter='='):
    """Save dictionary as key=value style configuration file."""
    with open(config_path, 'w') as file:
        for key, value in config_dict.items():
            file.write(f"{key}{delimiter}{value}\n")


def config_exists(config_path):
    """Check if a configuration file exists."""
    return os.path.exists(config_path)