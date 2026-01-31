"""
Core encryption and decryption functionality for mnemonic phrases.

This module provides the MnemonicEncryptor class which handles:
- BIP39 mnemonic validation
- Mnemonic encryption using AnyEncrypt
- Mnemonic decryption
- New mnemonic generation
"""

from typing import Optional
from mnemonic import Mnemonic
from anyencrypt import encrypt_text, decrypt_text


class MnemonicEncryptor:
    """
    Encryptor for BIP39 mnemonic phrases using AnyEncrypt.
    
    This class provides secure encryption and decryption of cryptocurrency
    mnemonic phrases following the BIP39 standard.
    
    Attributes:
        VERSION_PREFIX: Version prefix for encrypted mnemonics (for future compatibility)
        mnemo: Mnemonic instance for BIP39 operations
    
    Example:
        >>> encryptor = MnemonicEncryptor()
        >>> mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"
        >>> password = "my-secure-password"
        >>> ciphertext = encryptor.encrypt(mnemonic, password)
        >>> decrypted = encryptor.decrypt(ciphertext, password)
        >>> assert mnemonic == decrypted
    """
    
    VERSION_PREFIX = "ME$v1$"
    
    def __init__(self, language: str = "english") -> None:
        """
        Initialize the MnemonicEncryptor.
        
        Args:
            language: Language for mnemonic words (default: "english")
        """
        self.mnemo = Mnemonic(language)
    
    def validate_mnemonic(self, mnemonic: str) -> bool:
        """
        Validate if a mnemonic phrase follows BIP39 standard.
        
        Args:
            mnemonic: Space-separated mnemonic phrase
        
        Returns:
            True if valid, False otherwise
        
        Example:
            >>> encryptor = MnemonicEncryptor()
            >>> encryptor.validate_mnemonic("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about")
            True
            >>> encryptor.validate_mnemonic("invalid mnemonic phrase")
            False
        """
        try:
            # Normalize the mnemonic
            normalized = self._normalize_mnemonic(mnemonic)
            return self.mnemo.check(normalized)
        except Exception:
            return False
    
    def _normalize_mnemonic(self, mnemonic: str) -> str:
        """
        Normalize mnemonic phrase (lowercase, single spaces).
        
        Args:
            mnemonic: Raw mnemonic phrase
        
        Returns:
            Normalized mnemonic phrase
        """
        return " ".join(mnemonic.lower().strip().split())
    
    def encrypt(self, mnemonic: str, password: str) -> str:
        """
        Encrypt a mnemonic phrase with a password.
        
        The encrypted output includes a version prefix (ME$v1$) for future
        compatibility with potential algorithm upgrades.
        
        Args:
            mnemonic: BIP39 mnemonic phrase to encrypt
            password: Encryption password (recommend 16+ characters)
        
        Returns:
            Encrypted ciphertext with version prefix
        
        Raises:
            ValueError: If mnemonic is invalid or empty
            Exception: If encryption fails
        
        Example:
            >>> encryptor = MnemonicEncryptor()
            >>> mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"
            >>> ciphertext = encryptor.encrypt(mnemonic, "strong-password-123")
            >>> print(ciphertext)
            ME$v1$gAAAAAB...
        """
        if not mnemonic or not mnemonic.strip():
            raise ValueError("Mnemonic cannot be empty")
        
        if not password or not password.strip():
            raise ValueError("Password cannot be empty")
        
        # Normalize mnemonic
        normalized = self._normalize_mnemonic(mnemonic)
        
        # Validate BIP39 format
        if not self.validate_mnemonic(normalized):
            raise ValueError(
                "Invalid mnemonic format, please ensure it's a valid BIP39 mnemonic"
            )
        
        # Encrypt using AnyEncrypt
        try:
            ciphertext = encrypt_text(normalized, password)
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
        
        # Add version prefix
        return f"{self.VERSION_PREFIX}{ciphertext}"
    
    def decrypt(self, ciphertext: str, password: str) -> str:
        """
        Decrypt an encrypted mnemonic phrase.
        
        Args:
            ciphertext: Encrypted mnemonic (with or without version prefix)
            password: Decryption password
        
        Returns:
            Decrypted mnemonic phrase
        
        Raises:
            ValueError: If ciphertext or password is empty
            Exception: If decryption fails or result is invalid
        
        Example:
            >>> encryptor = MnemonicEncryptor()
            >>> ciphertext = "ME$v1$gAAAAAB..."
            >>> mnemonic = encryptor.decrypt(ciphertext, "strong-password-123")
            >>> print(mnemonic)
            abandon ability able about above absent absorb abstract absurd abuse access accident
        """
        if not ciphertext or not ciphertext.strip():
            raise ValueError("Ciphertext cannot be empty")
        
        if not password or not password.strip():
            raise ValueError("Password cannot be empty")
        
        # Remove version prefix if present
        clean_ciphertext = ciphertext
        if ciphertext.startswith(self.VERSION_PREFIX):
            clean_ciphertext = ciphertext[len(self.VERSION_PREFIX):]
        
        # Decrypt using AnyEncrypt
        try:
            plaintext = decrypt_text(clean_ciphertext, password)
        except Exception as e:
            raise Exception(f"Decryption failed (password may be incorrect): {str(e)}")
        
        # Validate decrypted result
        if not self.validate_mnemonic(plaintext):
            raise ValueError(
                "Decrypted result is not a valid mnemonic"
            )
        
        return plaintext
    
    def generate(self, strength: int = 128) -> str:
        """
        Generate a new BIP39 mnemonic phrase.
        
        Args:
            strength: Mnemonic strength in bits (128, 160, 192, 224, or 256)
                     - 128 bits = 12 words
                     - 160 bits = 15 words
                     - 192 bits = 18 words
                     - 224 bits = 21 words
                     - 256 bits = 24 words
        
        Returns:
            Generated mnemonic phrase
        
        Raises:
            ValueError: If strength is not valid
        
        Example:
            >>> encryptor = MnemonicEncryptor()
            >>> mnemonic_12 = encryptor.generate(128)  # 12 words
            >>> mnemonic_24 = encryptor.generate(256)  # 24 words
        """
        valid_strengths = [128, 160, 192, 224, 256]
        if strength not in valid_strengths:
            raise ValueError(
                f"Invalid strength, must be one of: {valid_strengths}"
            )
        
        return self.mnemo.generate(strength=strength)
    
    def get_word_count(self, strength: int) -> int:
        """
        Get the number of words for a given strength.
        
        Args:
            strength: Mnemonic strength in bits
        
        Returns:
            Number of words
        
        Example:
            >>> encryptor = MnemonicEncryptor()
            >>> encryptor.get_word_count(128)
            12
            >>> encryptor.get_word_count(256)
            24
        """
        return strength // 32 * 3
