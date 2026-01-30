"""Tests for cryptography module."""

from __future__ import annotations

import pytest
from cryptography.fernet import InvalidToken

from triagent.security.crypto import decrypt_data, derive_key, encrypt_data


class TestKeyDerivation:
    """Test key derivation."""

    def test_key_derivation_deterministic(self) -> None:
        """Same input should produce same key."""
        key1 = derive_key("us.deloitte.com")
        key2 = derive_key("us.deloitte.com")
        assert key1 == key2

    def test_key_derivation_case_insensitive(self) -> None:
        """Key derivation should normalize to lowercase."""
        key1 = derive_key("US.DELOITTE.COM")
        key2 = derive_key("us.deloitte.com")
        assert key1 == key2

    def test_key_derivation_strips_whitespace(self) -> None:
        """Key derivation should strip whitespace."""
        key1 = derive_key("  us.deloitte.com  ")
        key2 = derive_key("us.deloitte.com")
        assert key1 == key2

    def test_key_derivation_different_inputs(self) -> None:
        """Different inputs should produce different keys."""
        key1 = derive_key("deloitte.com")
        key2 = derive_key("acme.com")
        assert key1 != key2

    def test_key_is_valid_fernet_format(self) -> None:
        """Derived key should be valid 44-byte base64 Fernet key."""
        key = derive_key("test.domain.com")
        # Fernet keys are 32 bytes base64 encoded = 44 characters
        assert len(key) == 44


class TestEncryption:
    """Test encryption and decryption."""

    def test_encrypt_decrypt_roundtrip(self) -> None:
        """Encrypt then decrypt should recover original data."""
        key = derive_key("us.deloitte.com")
        original = b"test data with unicode: \xc3\xa9\xc3\xa0\xc3\xb9"

        encrypted = encrypt_data(original, key)
        decrypted = decrypt_data(encrypted, key)

        assert decrypted == original
        assert encrypted != original

    def test_encrypt_produces_different_output(self) -> None:
        """Each encryption should produce different ciphertext (due to IV)."""
        key = derive_key("us.deloitte.com")
        data = b"same data"

        encrypted1 = encrypt_data(data, key)
        encrypted2 = encrypt_data(data, key)

        # Fernet uses random IV, so ciphertexts should differ
        assert encrypted1 != encrypted2

        # But both should decrypt to same plaintext
        assert decrypt_data(encrypted1, key) == data
        assert decrypt_data(encrypted2, key) == data

    def test_decrypt_wrong_key_fails(self) -> None:
        """Decrypt with wrong key should raise InvalidToken."""
        key1 = derive_key("deloitte.com")
        key2 = derive_key("acme.com")

        encrypted = encrypt_data(b"secret data", key1)

        with pytest.raises(InvalidToken):
            decrypt_data(encrypted, key2)

    def test_decrypt_corrupted_data_fails(self) -> None:
        """Decrypt corrupted data should raise InvalidToken."""
        key = derive_key("us.deloitte.com")
        encrypted = encrypt_data(b"test data", key)

        # Corrupt the ciphertext
        corrupted = encrypted[:-5] + b"XXXXX"

        with pytest.raises(InvalidToken):
            decrypt_data(corrupted, key)

    def test_encrypt_empty_data(self) -> None:
        """Should handle empty data."""
        key = derive_key("us.deloitte.com")
        encrypted = encrypt_data(b"", key)
        decrypted = decrypt_data(encrypted, key)
        assert decrypted == b""

    def test_encrypt_large_data(self) -> None:
        """Should handle large data."""
        key = derive_key("us.deloitte.com")
        # 1MB of data
        large_data = b"x" * (1024 * 1024)

        encrypted = encrypt_data(large_data, key)
        decrypted = decrypt_data(encrypted, key)

        assert decrypted == large_data
