"""
MnemonicEncrypt - Secure cryptocurrency mnemonic phrase encryption tool.

This package provides a secure way to encrypt and decrypt BIP39 mnemonic phrases
using the AnyEncrypt encryption library.
"""

from .core import MnemonicEncryptor
from .__version__ import __version__

__all__ = ["MnemonicEncryptor", "__version__"]
