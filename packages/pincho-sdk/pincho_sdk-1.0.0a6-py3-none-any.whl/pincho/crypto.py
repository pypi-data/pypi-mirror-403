"""Encryption utilities for Pincho library.

Provides AES-128-CBC encryption with custom Base64 encoding to match
the Pincho app's decryption implementation.
"""

import base64
import hashlib
import os
from typing import Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def custom_base64_encode(data: bytes) -> str:
    """Encode bytes using custom Base64 encoding matching Pincho app.

    Converts standard Base64 characters to custom encoding:
    - '+' → '-'
    - '/' → '.'
    - '=' → '_'

    Args:
        data: Bytes to encode

    Returns:
        Custom Base64 encoded string
    """
    standard = base64.b64encode(data).decode("utf-8")
    return standard.replace("+", "-").replace("/", ".").replace("=", "_")


def derive_encryption_key(password: str) -> bytes:
    """Derive AES encryption key from password using SHA1.

    Key derivation process:
    1. SHA1 hash of password
    2. Lowercase hexadecimal string
    3. Truncate to 32 characters
    4. Convert hex string to bytes

    Args:
        password: Encryption password

    Returns:
        16-byte AES-128 key
    """
    sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest()
    key_hex = sha1_hash.lower()[:32]  # Truncate to 32 chars (16 bytes when converted)
    return bytes.fromhex(key_hex)


def encrypt_message(plaintext: str, password: str, iv: bytes) -> str:
    """Encrypt text using AES-128-CBC with custom Base64 encoding.

    Encryption process matching Pincho app:
    1. Derive key from password using SHA1
    2. Apply PKCS7 padding to plaintext
    3. Encrypt using AES-128-CBC with provided IV
    4. Encode with custom Base64

    Args:
        plaintext: Text to encrypt
        password: Encryption password
        iv: 16-byte initialization vector

    Returns:
        Encrypted and custom Base64 encoded string
    """
    # Derive encryption key
    key = derive_encryption_key(password)

    # Encode plaintext to bytes
    plaintext_bytes = plaintext.encode("utf-8")

    # Apply PKCS7 padding
    pad_length = 16 - (len(plaintext_bytes) % 16)
    padded = plaintext_bytes + bytes([pad_length] * pad_length)

    # Create AES cipher in CBC mode
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Encrypt
    encrypted = encryptor.update(padded) + encryptor.finalize()

    # Return custom Base64 encoded result
    return custom_base64_encode(encrypted)


def generate_iv() -> Tuple[bytes, str]:
    """Generate a random 16-byte initialization vector.

    Returns:
        Tuple of (iv_bytes, iv_hex_string) where:
        - iv_bytes: 16 random bytes
        - iv_hex_string: Hexadecimal string representation (32 characters)
    """
    iv_bytes = os.urandom(16)
    iv_hex = iv_bytes.hex()
    return iv_bytes, iv_hex
