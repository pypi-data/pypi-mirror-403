"""
AnyEncrypt - 一个简单易用的加密解密工具
"""

__version__ = "0.3.0"
__author__ = "Lindsay Wat"
__email__ = "llindsaywat1985@gmail.com"

from .crypto import encrypt_text, decrypt_text, encrypt_file, decrypt_file

__all__ = [
    "encrypt_text",
    "decrypt_text",
    "encrypt_file",
    "decrypt_file",
]
