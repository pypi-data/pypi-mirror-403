"""
lana1028 - A lightweight educational encryption module.

Provides:
- Key generation
- Encryption
- Decryption

⚠️ WARNING: Not suitable for production use or sensitive data protection.
"""

__version__ = "2.0.0"

from lana1028.main import generate_lana1028_key, lana1028_encrypt, lana1028_decrypt

__all__ = [
    "generate_lana1028_key",
    "lana1028_encrypt",
    "lana1028_decrypt",
]
