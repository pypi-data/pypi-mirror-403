import os
import platform


def join_path(*parts):
    """Join path components into a single path (cross-platform)."""
    return os.path.join(*parts)


def normalize_path(path):
    """Normalize a path (handles .., ., and separators)."""
    return os.path.normpath(path)


def get_filename(path):
    """Get the filename from a path."""
    return os.path.basename(path)


def get_directory(path):
    """Get the directory path from a file path."""
    return os.path.dirname(path)


def get_extension(path):
    """Get the file extension (including the dot)."""
    return os.path.splitext(path)[1]


def get_filename_without_extension(path):
    """Get filename without extension."""
    return os.path.splitext(os.path.basename(path))[0]


def resolve_path(path):
    """Get the absolute path."""
    return os.path.abspath(path)


def expand_user(path):
    """Expand ~ to user home directory."""
    return os.path.expanduser(path)


def is_absolute_path(path):
    """Check if a path is absolute."""
    return os.path.isabs(path)


def combine_paths(base, relative):
    """Combine a base path with a relative path intelligently."""
    return os.path.normpath(os.path.join(base, relative))


def get_common_path(paths):
    """Get the common directory path for multiple paths."""
    return os.path.commonpath(paths)


def change_extension(path, new_extension):
    """Change the extension of a file path."""
    if not new_extension.startswith('.'):
        new_extension = '.' + new_extension
    base = os.path.splitext(path)[0]
    return base + new_extension


def split_path(path):
    """Split a path into all its components."""
    parts = []
    while path:
        head, tail = os.path.split(path)
        if tail:
            parts.insert(0, tail)
        elif head:
            parts.insert(0, head)
            break
        else:
            break
        path = head
    return parts


def path_exists(path):
    """Check if a path exists."""
    return os.path.exists(path)


def is_file(path):
    """Check if path is a file."""
    return os.path.isfile(path)


def is_directory(path):
    """Check if path is a directory."""
    return os.path.isdir(path)


def get_relative_path(path, start):
    """Get relative path from start to path."""
    return os.path.relpath(path, start)


def get_parent_directory(path, levels=1):
    """Get parent directory, optionally multiple levels up."""
    for _ in range(levels):
        path = os.path.dirname(path)
    return path


def is_same_path(path1, path2):
    """Check if two paths point to the same file/directory."""
    return os.path.samefile(path1, path2) if os.path.exists(path1) and os.path.exists(path2) else False
