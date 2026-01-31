"""
SM4 encryption algorithm implementation wrapper
Based on the gmssl library
"""

import binascii
from gmssl import sm4


class SM4Cipher:
    """
    SM4 encryption/decryption wrapper class
    """

    def __init__(self, key: str, mode: str = 'ECB'):
        """
        Initialize SM4 cipher
        
        :param key: Encryption key (16 bytes)
        :param mode: Encryption mode ('ECB' or 'CBC')
        """
        self.key = key.encode('utf-8') if isinstance(key, str) else key
        self.mode = mode.upper()
        if self.mode not in ['ECB', 'CBC']:
            raise ValueError("Mode must be 'ECB' or 'CBC'")
        self.sm4_crypto = sm4.CryptSM4()

    def encrypt(self, plaintext: str, iv=None) -> str:
        """
        Encrypt plaintext using SM4 algorithm
        
        :param plaintext: Text to encrypt
        :param iv: Initialization vector (required for CBC mode)
        :return: Encrypted ciphertext in hexadecimal format
        """
        data = plaintext.encode('utf-8')
        
        if self.mode == 'ECB':
            self.sm4_crypto.set_key(self.key, sm4.SM4_ENCRYPT)
            encrypted = self.sm4_crypto.crypt_ecb(data)
        elif self.mode == 'CBC':
            if not iv:
                raise ValueError("IV is required for CBC mode")
            iv_bytes = iv.encode('utf-8') if isinstance(iv, str) else iv
            self.sm4_crypto.set_key(self.key, sm4.SM4_ENCRYPT)
            encrypted = self.sm4_crypto.crypt_cbc(iv_bytes, data)
            
        return binascii.b2a_hex(encrypted).decode('utf-8')

    def decrypt(self, ciphertext: str, iv=None) -> str:
        """
        Decrypt ciphertext using SM4 algorithm
        
        :param ciphertext: Ciphertext in hexadecimal format
        :param iv: Initialization vector (required for CBC mode)
        :return: Decrypted plaintext
        """
        data = binascii.a2b_hex(ciphertext)
        
        if self.mode == 'ECB':
            self.sm4_crypto.set_key(self.key, sm4.SM4_DECRYPT)
            decrypted = self.sm4_crypto.crypt_ecb(data)
        elif self.mode == 'CBC':
            if not iv:
                raise ValueError("IV is required for CBC mode")
            iv_bytes = iv.encode('utf-8') if isinstance(iv, str) else iv
            self.sm4_crypto.set_key(self.key, sm4.SM4_DECRYPT)
            decrypted = self.sm4_crypto.crypt_cbc(iv_bytes, data)
            
        return decrypted.decode('utf-8')

class SM4Utils:
    @staticmethod
    def sm4_encrypt_string(plaintext: str, key: str, mode: str = 'ECB', iv=None) -> str:
        """
        Encrypt string using SM4 algorithm

        :param plaintext: Text to encrypt
        :param key: Encryption key (16 bytes)
        :param mode: Encryption mode ('ECB' or 'CBC')
        :param iv: Initialization vector (required for CBC mode)
        :return: Encrypted ciphertext in hexadecimal format
        """
        cipher = SM4Cipher(key, mode)
        return cipher.encrypt(plaintext, iv)

    @staticmethod
    def sm4_decrypt_string(ciphertext: str, key: str, mode: str = 'ECB', iv=None) -> str:
        """
        Decrypt string using SM4 algorithm

        :param ciphertext: Ciphertext in hexadecimal format
        :param key: Encryption key (16 bytes)
        :param mode: Encryption mode ('ECB' or 'CBC')
        :param iv: Initialization vector (required for CBC mode)
        :return: Decrypted plaintext
        """
        cipher = SM4Cipher(key, mode)
        return cipher.decrypt(ciphertext, iv)

