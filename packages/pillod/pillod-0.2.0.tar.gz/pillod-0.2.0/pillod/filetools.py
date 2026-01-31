import os
import shutil


def read_file(file_path):
    """Read and return the contents of a file."""
    with open(file_path, 'r') as file:
        return file.read()


def write_file(file_path, content):
    """Write content to a file, creating it if it doesn't exist."""
    with open(file_path, 'w') as file:
        file.write(content)


def append_file(file_path, content):
    """Append content to a file."""
    with open(file_path, 'a') as file:
        file.write(content)


def read_lines(file_path):
    """Read a file and return a list of lines."""
    with open(file_path, 'r') as file:
        return file.readlines()


def write_lines(file_path, lines):
    """Write a list of lines to a file."""
    with open(file_path, 'w') as file:
        file.writelines(lines)


def file_exists(file_path):
    """Check if a file exists."""
    return os.path.isfile(file_path)


def dir_exists(dir_path):
    """Check if a directory exists."""
    return os.path.isdir(dir_path)


def create_dir(dir_path):
    """Create a directory if it doesn't exist."""
    os.makedirs(dir_path, exist_ok=True)


def copy_file(src, dst):
    """Copy a file from src to dst."""
    shutil.copy2(src, dst)


def move_file(src, dst):
    """Move a file from src to dst."""
    shutil.move(src, dst)


def delete_file(file_path):
    """Delete a file if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)


def get_file_size(file_path):
    """Get the size of a file in bytes."""
    return os.path.getsize(file_path)


def list_files(dir_path, extension=None):
    """List all files in a directory, optionally filtered by extension.
    
    Args:
        dir_path: Directory path to list files from
        extension: Optional file extension to filter (e.g., '.txt', '.py')
        
    Returns:
        List of file paths
    """
    files = []
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isfile(item_path):
            if extension is None or item.endswith(extension):
                files.append(item_path)
    return files
