# -*- coding: utf-8 -*-
# @Time    : 2024/8/14 16:01
# @Author  : Chris
# @Email   : 10512@qq.com
# @File    : crypto.py
# @Software: PyCharm
import hmac
from hashlib import md5, sha1, sha256, sha512
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend


def crypto_md5(originString: str) -> str:
    return md5(originString.encode("utf-8")).hexdigest()


def crypto_sha1(originString: str) -> str:
    return sha1(originString.encode("utf-8")).hexdigest()


def crypto_sha256(originString: str) -> str:
    return sha256(originString.encode("utf-8")).hexdigest()


def crypto_sha512(originString: str) -> str:
    return sha512(originString.encode("utf-8")).hexdigest()


def crypto_HMAC_MD5(key: str, originString: str) -> str:
    return hmac.new(key.encode("utf-8"), originString.encode("utf-8"), md5).hexdigest()


class VariantAES:
    def __init__(self, password: str):
        self.password = password.encode('utf-8')
        self.iterations = 100000
        self.key_length = 32

        self.salt = os.urandom(16)
        self.iv = os.urandom(16)
        self.key = self._derive_key(self.salt)

    def _derive_key(self, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=self.key_length,
            salt=salt,
            iterations=self.iterations,
            backend=default_backend()
        )
        return kdf.derive(self.password)

    def encrypt(self, plaintext: str) -> str:

        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()

        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        combined = self.salt + self.iv + ciphertext
        return combined.hex()

    def decrypt(self, encrypted_hex: str) -> str:
        try:
            data = bytes.fromhex(encrypted_hex)

            salt = data[:16]
            iv = data[16:32]
            ciphertext = data[32:]

            key = self._derive_key(salt)

            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

            return plaintext.decode('utf-8')

        except Exception as e:
            return f"解密失败: 密码错误或数据损坏 ({str(e)})"


if __name__ == "__main__":
    # 1. 设定密码
    my_password = "1"
    crypto_tool = VariantAES(my_password)

    # 2. 原文
    original_text = "Ddr4和ddr5的插槽是一样的吗？"
    print(f"原文: {original_text}")
    print(f"密码: {my_password}")

    # 3. 加密
    # 注意：你会发现这步稍微有点慢，因为在跑 10万次 哈希
    encrypted_data = crypto_tool.encrypt(original_text)
    print(f"\n加密后 (Base64): {encrypted_data}")

    # 4. 解密
    decrypted_text = crypto_tool.decrypt(encrypted_data)
    print(f"\n解密后: {decrypted_text}")

    # 5. 测试密码错误的情况
    print("\n--- 测试错误密码 ---")
    hacker_tool = VariantAES("2")
    print(f"尝试用错误密码解密: {hacker_tool.decrypt(encrypted_data)}")
