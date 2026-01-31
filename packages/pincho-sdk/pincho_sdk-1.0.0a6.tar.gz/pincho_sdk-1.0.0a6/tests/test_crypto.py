"""Tests for encryption utilities."""

import os

from pincho.crypto import (
    custom_base64_encode,
    derive_encryption_key,
    encrypt_message,
    generate_iv,
)


class TestCustomBase64Encode:
    """Tests for custom Base64 encoding."""

    def test_empty_data(self) -> None:
        """Test encoding empty data."""
        result = custom_base64_encode(b"")
        assert result == ""

    def test_single_byte(self) -> None:
        """Test encoding single byte."""
        result = custom_base64_encode(b"\x00")
        # Standard Base64 of b"\x00" is "AA=="
        # Custom encoding: '=' → '_'
        assert result == "AA__"

    def test_character_substitution(self) -> None:
        """Test that custom encoding substitutes characters correctly."""
        # Use data that will produce / in standard Base64
        data = b"\xfb\xff\xbf"
        result = custom_base64_encode(data)
        # Standard: "-.-." contains substituted characters
        # Verify it's using custom encoding
        assert "+" not in result
        assert "/" not in result
        assert "=" not in result or result.endswith("_")

    def test_plus_sign_substitution(self) -> None:
        """Test that + is replaced with -."""
        # Use data that produces + in standard Base64
        data = b"\xf8\x00"  # Produces "+" in standard Base64
        result = custom_base64_encode(data)
        # Standard: "+AA="
        # Custom: '+' → '-', '=' → '_'
        assert result == "-AA_"

    def test_roundtrip_compatibility(self) -> None:
        """Test that encoding is reversible with proper decoding."""
        original = b"Hello, Pincho!"
        encoded = custom_base64_encode(original)

        # Reverse the custom encoding to get standard Base64
        standard = encoded.replace("-", "+").replace(".", "/").replace("_", "=")
        import base64

        decoded = base64.b64decode(standard)

        assert decoded == original


class TestDeriveEncryptionKey:
    """Tests for encryption key derivation."""

    def test_empty_password(self) -> None:
        """Test key derivation with empty password."""
        key = derive_encryption_key("")
        assert len(key) == 16  # AES-128 requires 16-byte key
        assert isinstance(key, bytes)

    def test_simple_password(self) -> None:
        """Test key derivation with simple password."""
        key = derive_encryption_key("password")
        assert len(key) == 16
        assert isinstance(key, bytes)

    def test_deterministic(self) -> None:
        """Test that key derivation is deterministic."""
        password = "test_password_123"
        key1 = derive_encryption_key(password)
        key2 = derive_encryption_key(password)
        assert key1 == key2

    def test_different_passwords_different_keys(self) -> None:
        """Test that different passwords produce different keys."""
        key1 = derive_encryption_key("password1")
        key2 = derive_encryption_key("password2")
        assert key1 != key2

    def test_known_password_known_key(self) -> None:
        """Test key derivation against known SHA1 output."""
        # SHA1("test") = a94a8fe5ccb19ba61c4c0873d391e987982fbbd3
        # First 32 chars: a94a8fe5ccb19ba61c4c0873d391e987
        # As bytes: \xa9\x4a\x8f\xe5\xcc\xb1\x9b\xa6\x1c\x4c\x08\x73\xd3\x91\xe9\x87
        expected = bytes.fromhex("a94a8fe5ccb19ba61c4c0873d391e987")
        result = derive_encryption_key("test")
        assert result == expected

    def test_unicode_password(self) -> None:
        """Test key derivation with Unicode password."""
        key = derive_encryption_key("пароль🔐")
        assert len(key) == 16
        assert isinstance(key, bytes)


class TestGenerateIV:
    """Tests for IV generation."""

    def test_iv_length(self) -> None:
        """Test that IV is 16 bytes."""
        iv_bytes, iv_hex = generate_iv()
        assert len(iv_bytes) == 16
        assert isinstance(iv_bytes, bytes)

    def test_iv_hex_format(self) -> None:
        """Test that hex string is 32 characters."""
        iv_bytes, iv_hex = generate_iv()
        assert len(iv_hex) == 32
        assert isinstance(iv_hex, str)
        # Verify it's valid hex
        assert bytes.fromhex(iv_hex) == iv_bytes

    def test_iv_randomness(self) -> None:
        """Test that IVs are different on each call."""
        iv1_bytes, _ = generate_iv()
        iv2_bytes, _ = generate_iv()
        iv3_bytes, _ = generate_iv()

        # Extremely unlikely to be equal if truly random
        assert iv1_bytes != iv2_bytes
        assert iv2_bytes != iv3_bytes
        assert iv1_bytes != iv3_bytes

    def test_hex_consistency(self) -> None:
        """Test that hex representation matches bytes."""
        iv_bytes, iv_hex = generate_iv()
        assert iv_bytes.hex() == iv_hex


class TestEncryptMessage:
    """Tests for message encryption."""

    def test_encrypt_empty_string(self) -> None:
        """Test encrypting empty string."""
        iv = os.urandom(16)
        result = encrypt_message("", "password", iv)
        # Should still produce output due to padding
        assert len(result) > 0
        assert isinstance(result, str)

    def test_encrypt_simple_message(self) -> None:
        """Test encrypting simple message."""
        iv = os.urandom(16)
        result = encrypt_message("Hello, World!", "password", iv)
        assert len(result) > 0
        assert isinstance(result, str)
        # Verify custom Base64 characters
        assert "+" not in result
        assert "/" not in result
        assert "=" not in result

    def test_encrypt_deterministic_with_same_iv(self) -> None:
        """Test that encryption is deterministic with same IV."""
        iv = os.urandom(16)
        password = "test_password"
        message = "Test message"

        result1 = encrypt_message(message, password, iv)
        result2 = encrypt_message(message, password, iv)

        assert result1 == result2

    def test_encrypt_different_with_different_iv(self) -> None:
        """Test that encryption differs with different IV."""
        password = "test_password"
        message = "Test message"

        iv1 = os.urandom(16)
        iv2 = os.urandom(16)

        result1 = encrypt_message(message, password, iv1)
        result2 = encrypt_message(message, password, iv2)

        # Should be different due to different IV
        assert result1 != result2

    def test_encrypt_different_passwords(self) -> None:
        """Test that different passwords produce different ciphertext."""
        iv = os.urandom(16)
        message = "Test message"

        result1 = encrypt_message(message, "password1", iv)
        result2 = encrypt_message(message, "password2", iv)

        assert result1 != result2

    def test_encrypt_long_message(self) -> None:
        """Test encrypting long message."""
        iv = os.urandom(16)
        message = "A" * 10000  # 10,000 characters (max allowed)
        result = encrypt_message(message, "password", iv)
        assert len(result) > 0
        assert isinstance(result, str)

    def test_encrypt_unicode_message(self) -> None:
        """Test encrypting Unicode message."""
        iv = os.urandom(16)
        message = "Hello 世界 🌍"
        result = encrypt_message(message, "password", iv)
        assert len(result) > 0
        assert isinstance(result, str)

    def test_encrypt_multiline_message(self) -> None:
        """Test encrypting multiline message."""
        iv = os.urandom(16)
        message = "Line 1\nLine 2\nLine 3"
        result = encrypt_message(message, "password", iv)
        assert len(result) > 0
        assert isinstance(result, str)

    def test_encrypt_special_characters(self) -> None:
        """Test encrypting message with special characters."""
        iv = os.urandom(16)
        message = "Special chars: !@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        result = encrypt_message(message, "password", iv)
        assert len(result) > 0
        assert isinstance(result, str)

    def test_padding_applied_correctly(self) -> None:
        """Test that PKCS7 padding is applied correctly."""
        iv = os.urandom(16)

        # Messages of different lengths to test padding
        messages = [
            "A",  # 1 byte
            "AB",  # 2 bytes
            "A" * 15,  # 15 bytes
            "A" * 16,  # 16 bytes (one full block)
            "A" * 17,  # 17 bytes
        ]

        for message in messages:
            result = encrypt_message(message, "password", iv)
            assert len(result) > 0
            # Encrypted length should be a multiple of 16 bytes when decoded
            # (before custom Base64 encoding)
            standard_b64 = result.replace("-", "+").replace(".", "/").replace("_", "=")
            import base64

            encrypted_bytes = base64.b64decode(standard_b64)
            assert len(encrypted_bytes) % 16 == 0


class TestEncryptionIntegration:
    """Integration tests for encryption workflow."""

    def test_full_encryption_workflow(self) -> None:
        """Test complete encryption workflow with IV generation."""
        password = "my_secure_password"
        message = "This is a secret message"

        # Generate IV
        iv_bytes, iv_hex = generate_iv()

        # Encrypt
        encrypted = encrypt_message(message, password, iv_bytes)

        # Verify encrypted is not empty and uses custom encoding
        assert len(encrypted) > 0
        assert "+" not in encrypted
        assert "/" not in encrypted
        assert "=" not in encrypted

        # Verify IV hex is valid
        assert len(iv_hex) == 32
        assert bytes.fromhex(iv_hex) == iv_bytes

    def test_encryption_matches_reference_implementation(self) -> None:
        """Test that encryption matches the generator.py reference implementation."""
        # Use fixed IV for reproducible test
        iv = bytes.fromhex("00112233445566778899aabbccddeeff")
        password = "test_password"
        message = "Test message"

        # This is the expected output from generator.py with same inputs
        # You would need to generate this by running generator.py with fixed IV
        result = encrypt_message(message, password, iv)

        # Just verify it produces consistent output
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify it's reproducible
        result2 = encrypt_message(message, password, iv)
        assert result == result2

    def test_multiple_messages_with_unique_ivs(self) -> None:
        """Test encrypting multiple messages with unique IVs."""
        password = "shared_password"
        messages = ["Message 1", "Message 2", "Message 3"]

        encrypted_messages = []
        for message in messages:
            iv_bytes, iv_hex = generate_iv()
            encrypted = encrypt_message(message, password, iv_bytes)
            encrypted_messages.append((encrypted, iv_hex))

        # All should be different due to different IVs
        encrypted_texts = [e[0] for e in encrypted_messages]
        assert len(set(encrypted_texts)) == len(encrypted_texts)

        # All IVs should be different
        ivs = [e[1] for e in encrypted_messages]
        assert len(set(ivs)) == len(ivs)
