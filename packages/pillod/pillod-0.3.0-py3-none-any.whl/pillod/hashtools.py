import hashlib


def md5_hash(text):
    """Generate MD5 hash of a string."""
    return hashlib.md5(text.encode()).hexdigest()


def sha256_hash(text):
    """Generate SHA256 hash of a string."""
    return hashlib.sha256(text.encode()).hexdigest()


def sha1_hash(text):
    """Generate SHA1 hash of a string."""
    return hashlib.sha1(text.encode()).hexdigest()


def file_md5(file_path):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def file_sha256(file_path):
    """Calculate SHA256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def compare_hashes(hash1, hash2):
    """Compare two hashes for equality. Case-insensitive."""
    return hash1.lower() == hash2.lower()


def verify_file_hash(file_path, expected_hash, algorithm='sha256'):
    """Verify a file matches an expected hash.
    
    Args:
        file_path: Path to file
        expected_hash: Expected hash value
        algorithm: 'md5', 'sha256', or 'sha1'
    """
    if algorithm == 'md5':
        actual = file_md5(file_path)
    elif algorithm == 'sha256':
        actual = file_sha256(file_path)
    elif algorithm == 'sha1':
        hash_sha1 = hashlib.sha1()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha1.update(chunk)
        actual = hash_sha1.hexdigest()
    else:
        return False
    
    return compare_hashes(actual, expected_hash)


def hash_password(password, algorithm='sha256'):
    """Hash a password using specified algorithm."""
    if algorithm == 'sha256':
        return sha256_hash(password)
    elif algorithm == 'md5':
        return md5_hash(password)
    elif algorithm == 'sha1':
        return sha1_hash(password)
    else:
        return None


def quick_hash(text):
    """Quick hash using Python's built-in hash (not cryptographic)."""
    return str(hash(text))
