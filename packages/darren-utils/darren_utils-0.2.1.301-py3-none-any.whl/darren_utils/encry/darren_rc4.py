

class RC4:
    """
    RC4加密算法实现
    """

    def __init__(self, key: str):
        """
        初始化RC4算法

        Args:
            key (str): 加密密钥
        """
        self.key = key.encode('utf-8')
        self.S = self._ksa()

    def _ksa(self):
        """
        密钥调度算法(Key Scheduling Algorithm)

        Returns:
            list: 初始化的S盒
        """
        key_length = len(self.key)
        S = list(range(256))
        j = 0
        for i in range(256):
            j = (j + S[i] + self.key[i % key_length]) % 256
            S[i], S[j] = S[j], S[i]
        return S

    def _prga(self):
        """
        伪随机生成算法(Pseudo-Random Generation Algorithm)

        Yields:
            int: 生成的密钥流字节
        """
        i = 0
        j = 0
        S = self.S[:]
        while True:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            K = S[(S[i] + S[j]) % 256]
            yield K

    def encrypt(self, plaintext: str) -> bytes:
        """
        RC4加密

        Args:
            plaintext (str): 明文

        Returns:
            bytes: 加密后的字节数据
        """
        keystream = self._prga()
        plaintext_bytes = plaintext.encode('utf-8')
        ciphertext = bytearray()
        for byte in plaintext_bytes:
            ciphertext.append(byte ^ next(keystream))
        return bytes(ciphertext)

    def decrypt(self, ciphertext: bytes) -> str:
        """
        RC4解密

        Args:
            ciphertext (bytes): 密文

        Returns:
            str: 解密后的明文
        """
        # RC4加密和解密使用相同的过程
        keystream = self._prga()
        plaintext = bytearray()
        for byte in ciphertext:
            plaintext.append(byte ^ next(keystream))
        return plaintext.decode('utf-8')

class Rc4Utils:
    @staticmethod
    def rc4_encrypt_string(plaintext: str, key: str) -> str:
        """
        RC4加密，返回十六进制字符串

        Args:
            plaintext (str): 明文
            key (str): 加密密钥

        Returns:
            str: 十六进制格式的密文
        """
        rc4 = RC4(key)
        ciphertext = rc4.encrypt(plaintext)
        return ciphertext.hex()

    @staticmethod
    def rc4_decrypt_string(ciphertext_hex: str, key: str) -> str:
        """
        RC4解密十六进制字符串

        Args:
            ciphertext_hex (str): 十六进制格式的密文
            key (str): 解密密钥

        Returns:
            str: 解密后的明文
        """
        rc4 = RC4(key)
        ciphertext = bytes.fromhex(ciphertext_hex)
        return rc4.decrypt(ciphertext)

