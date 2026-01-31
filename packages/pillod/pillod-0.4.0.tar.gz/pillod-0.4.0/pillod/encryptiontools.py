import base64
import hashlib


def encode_base64(text):
    """Encode text to base64."""
    return base64.b64encode(text.encode()).decode()


def decode_base64(encoded_text):
    """Decode base64 to text."""
    try:
        return base64.b64decode(encoded_text).decode()
    except Exception:
        return None


def encode_base64_file(file_path):
    """Encode a file to base64."""
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def decode_base64_file(encoded_data, file_path):
    """Decode base64 and write to file."""
    try:
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(encoded_data))
        return True
    except Exception:
        return False


def simple_cipher(text, shift=3):
    """Simple Caesar cipher for text obfuscation (not secure!).
    
    Args:
        text: Text to encrypt
        shift: Number of positions to shift (default: 3)
    """
    result = ""
    for char in text:
        if char.isalpha():
            if char.isupper():
                result += chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
            else:
                result += chr((ord(char) - ord('a') + shift) % 26 + ord('a'))
        else:
            result += char
    return result


def simple_decipher(text, shift=3):
    """Decrypt simple cipher (reverse the shift)."""
    return simple_cipher(text, -shift)


def hash_password(password, algorithm='sha256'):
    """Hash a password securely.
    
    Args:
        password: Password to hash
        algorithm: 'sha256' (default), 'sha512', or 'md5'
    """
    if algorithm == 'sha256':
        return hashlib.sha256(password.encode()).hexdigest()
    elif algorithm == 'sha512':
        return hashlib.sha512(password.encode()).hexdigest()
    elif algorithm == 'md5':
        return hashlib.md5(password.encode()).hexdigest()
    return None


def verify_password(password, hash_value, algorithm='sha256'):
    """Verify a password against its hash."""
    return hash_password(password, algorithm) == hash_value


def hash_password_salted(password, salt=''):
    """Hash password with salt for additional security."""
    return hashlib.sha256((password + salt).encode()).hexdigest()


def generate_random_salt(length=16):
    """Generate a random salt for password hashing."""
    import secrets
    return secrets.token_hex(length // 2)


def xor_cipher(text, key):
    """Simple XOR cipher for text (not secure!).
    
    Args:
        text: Text to encrypt/decrypt
        key: Encryption key
    """
    result = ""
    for i, char in enumerate(text):
        key_char = key[i % len(key)]
        result += chr(ord(char) ^ ord(key_char))
    return result


def encode_hex(text):
    """Encode text to hexadecimal."""
    return text.encode().hex()


def decode_hex(hex_text):
    """Decode hexadecimal to text."""
    try:
        return bytes.fromhex(hex_text).decode()
    except Exception:
        return None
