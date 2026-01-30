"""Cryptographic operations for prompt encryption.

This module provides PBKDF2 key derivation and Fernet symmetric encryption
for protecting sensitive prompts.
"""

from __future__ import annotations

import base64
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .constants import EMBEDDED_SALT_BYTES, KEY_ITERATIONS

# Re-export InvalidToken for use in other modules
__all__ = ["derive_key", "encrypt_data", "decrypt_data", "InvalidToken"]


def derive_key(corporate_id: str) -> bytes:
    """Derive a Fernet-compatible key from corporate identifier.

    Args:
        corporate_id: Corporate identifier (DNS domain, Kerberos realm, etc.)

    Returns:
        32-byte key encoded as base64 URL-safe string (Fernet format)
    """
    # Normalize the corporate ID
    normalized = corporate_id.lower().strip()

    # Create password by combining corporate ID with salt
    password = f"{normalized}:{EMBEDDED_SALT_BYTES.hex()}".encode()

    # Derive key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=EMBEDDED_SALT_BYTES,
        iterations=KEY_ITERATIONS,
    )

    key_bytes = kdf.derive(password)
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt data using Fernet symmetric encryption.

    Args:
        data: Plaintext data to encrypt
        key: Fernet key from derive_key()

    Returns:
        Encrypted data
    """
    return Fernet(key).encrypt(data)


def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """Decrypt data using Fernet symmetric encryption.

    Args:
        encrypted_data: Encrypted data from encrypt_data()
        key: Fernet key from derive_key()

    Returns:
        Decrypted plaintext data

    Raises:
        InvalidToken: If key is incorrect or data is corrupted
    """
    return Fernet(key).decrypt(encrypted_data)


def encrypt_file(input_path: Path, output_path: Path, key: bytes) -> None:
    """Encrypt a file and write to output path.

    Args:
        input_path: Path to plaintext file
        output_path: Path to write encrypted file
        key: Fernet key from derive_key()
    """
    plaintext = input_path.read_bytes()
    encrypted = encrypt_data(plaintext, key)
    output_path.write_bytes(encrypted)


def decrypt_file(input_path: Path, key: bytes) -> bytes:
    """Decrypt a file and return contents.

    Args:
        input_path: Path to encrypted file
        key: Fernet key from derive_key()

    Returns:
        Decrypted file contents

    Raises:
        InvalidToken: If key is incorrect or data is corrupted
    """
    encrypted = input_path.read_bytes()
    return decrypt_data(encrypted, key)
