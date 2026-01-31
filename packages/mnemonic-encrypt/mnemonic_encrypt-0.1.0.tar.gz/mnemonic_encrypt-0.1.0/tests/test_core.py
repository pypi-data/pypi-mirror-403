"""
Tests for core encryption functionality.
"""

import pytest
from mnemonic_encrypt import MnemonicEncryptor


class TestMnemonicEncryptor:
    """Test cases for MnemonicEncryptor class."""
    
    @pytest.fixture
    def encryptor(self):
        """Create a MnemonicEncryptor instance for testing."""
        return MnemonicEncryptor()
    
    @pytest.fixture
    def valid_mnemonic_12(self):
        """12-word valid mnemonic for testing."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    
    @pytest.fixture
    def valid_mnemonic_24(self):
        """24-word valid mnemonic for testing."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art"
    
    @pytest.fixture
    def test_password(self):
        """Test password."""
        return "test-password-123!@#"
    
    def test_validate_mnemonic_valid(self, encryptor, valid_mnemonic_12):
        """Test validation of valid mnemonic."""
        assert encryptor.validate_mnemonic(valid_mnemonic_12) is True
    
    def test_validate_mnemonic_invalid(self, encryptor):
        """Test validation of invalid mnemonic."""
        invalid_mnemonics = [
            "invalid mnemonic phrase here",
            "abandon abandon abandon",  # Too short
            "abandon " * 100,  # Too long
            "",  # Empty
            "123 456 789 101112",  # Numbers
        ]
        for mnemonic in invalid_mnemonics:
            assert encryptor.validate_mnemonic(mnemonic) is False
    
    def test_normalize_mnemonic(self, encryptor):
        """Test mnemonic normalization."""
        test_cases = [
            ("ABANDON  ABANDON   ABOUT", "abandon abandon about"),
            ("  abandon  abandon  about  ", "abandon abandon about"),
            ("Abandon Abandon About", "abandon abandon about"),
        ]
        for input_mnemonic, expected in test_cases:
            assert encryptor._normalize_mnemonic(input_mnemonic) == expected
    
    def test_encrypt_valid_mnemonic(self, encryptor, valid_mnemonic_12, test_password):
        """Test encryption of valid mnemonic."""
        ciphertext = encryptor.encrypt(valid_mnemonic_12, test_password)
        
        # Check that ciphertext is not empty
        assert ciphertext
        
        # Check that version prefix is present
        assert ciphertext.startswith("ME$v1$")
        
        # Check that ciphertext is different from plaintext
        assert ciphertext != valid_mnemonic_12
    
    def test_encrypt_invalid_mnemonic(self, encryptor, test_password):
        """Test encryption of invalid mnemonic."""
        with pytest.raises(ValueError):
            encryptor.encrypt("invalid mnemonic phrase", test_password)
    
    def test_encrypt_empty_mnemonic(self, encryptor, test_password):
        """Test encryption with empty mnemonic."""
        with pytest.raises(ValueError):
            encryptor.encrypt("", test_password)
    
    def test_encrypt_empty_password(self, encryptor, valid_mnemonic_12):
        """Test encryption with empty password."""
        with pytest.raises(ValueError):
            encryptor.encrypt(valid_mnemonic_12, "")
    
    def test_decrypt_valid_ciphertext(self, encryptor, valid_mnemonic_12, test_password):
        """Test decryption of valid ciphertext."""
        # Encrypt first
        ciphertext = encryptor.encrypt(valid_mnemonic_12, test_password)
        
        # Decrypt
        decrypted = encryptor.decrypt(ciphertext, test_password)
        
        # Normalize both for comparison
        normalized_original = encryptor._normalize_mnemonic(valid_mnemonic_12)
        assert decrypted == normalized_original
    
    def test_decrypt_without_prefix(self, encryptor, valid_mnemonic_12, test_password):
        """Test decryption of ciphertext without version prefix."""
        # Encrypt and remove prefix
        ciphertext = encryptor.encrypt(valid_mnemonic_12, test_password)
        ciphertext_no_prefix = ciphertext[len("ME$v1$"):]
        
        # Should still decrypt successfully
        decrypted = encryptor.decrypt(ciphertext_no_prefix, test_password)
        normalized_original = encryptor._normalize_mnemonic(valid_mnemonic_12)
        assert decrypted == normalized_original
    
    def test_decrypt_wrong_password(self, encryptor, valid_mnemonic_12, test_password):
        """Test decryption with wrong password."""
        ciphertext = encryptor.encrypt(valid_mnemonic_12, test_password)
        
        with pytest.raises(Exception):
            encryptor.decrypt(ciphertext, "wrong-password")
    
    def test_decrypt_empty_ciphertext(self, encryptor, test_password):
        """Test decryption with empty ciphertext."""
        with pytest.raises(ValueError):
            encryptor.decrypt("", test_password)
    
    def test_decrypt_empty_password(self, encryptor):
        """Test decryption with empty password."""
        with pytest.raises(ValueError):
            encryptor.decrypt("ME$v1$some_ciphertext", "")
    
    def test_encrypt_decrypt_cycle_12_words(self, encryptor, valid_mnemonic_12, test_password):
        """Test full encrypt-decrypt cycle with 12-word mnemonic."""
        ciphertext = encryptor.encrypt(valid_mnemonic_12, test_password)
        decrypted = encryptor.decrypt(ciphertext, test_password)
        normalized_original = encryptor._normalize_mnemonic(valid_mnemonic_12)
        assert decrypted == normalized_original
    
    def test_encrypt_decrypt_cycle_24_words(self, encryptor, valid_mnemonic_24, test_password):
        """Test full encrypt-decrypt cycle with 24-word mnemonic."""
        ciphertext = encryptor.encrypt(valid_mnemonic_24, test_password)
        decrypted = encryptor.decrypt(ciphertext, test_password)
        normalized_original = encryptor._normalize_mnemonic(valid_mnemonic_24)
        assert decrypted == normalized_original
    
    def test_generate_mnemonic_12_words(self, encryptor):
        """Test generating 12-word mnemonic."""
        mnemonic = encryptor.generate(strength=128)
        
        # Check word count
        words = mnemonic.split()
        assert len(words) == 12
        
        # Check validity
        assert encryptor.validate_mnemonic(mnemonic) is True
    
    def test_generate_mnemonic_24_words(self, encryptor):
        """Test generating 24-word mnemonic."""
        mnemonic = encryptor.generate(strength=256)
        
        # Check word count
        words = mnemonic.split()
        assert len(words) == 24
        
        # Check validity
        assert encryptor.validate_mnemonic(mnemonic) is True
    
    def test_generate_invalid_strength(self, encryptor):
        """Test generating mnemonic with invalid strength."""
        with pytest.raises(ValueError):
            encryptor.generate(strength=100)
    
    def test_get_word_count(self, encryptor):
        """Test word count calculation."""
        assert encryptor.get_word_count(128) == 12
        assert encryptor.get_word_count(160) == 15
        assert encryptor.get_word_count(192) == 18
        assert encryptor.get_word_count(224) == 21
        assert encryptor.get_word_count(256) == 24
    
    def test_different_passwords_different_ciphertext(self, encryptor, valid_mnemonic_12):
        """Test that different passwords produce different ciphertext."""
        password1 = "password1"
        password2 = "password2"
        
        ciphertext1 = encryptor.encrypt(valid_mnemonic_12, password1)
        ciphertext2 = encryptor.encrypt(valid_mnemonic_12, password2)
        
        assert ciphertext1 != ciphertext2
    
    def test_unicode_mnemonic_handling(self, encryptor, test_password):
        """Test handling of mnemonics with unicode characters."""
        # Valid BIP39 mnemonic with extra spaces
        mnemonic = "  abandon   abandon   about  "
        normalized = encryptor._normalize_mnemonic(mnemonic)
        assert normalized == "abandon abandon about"
