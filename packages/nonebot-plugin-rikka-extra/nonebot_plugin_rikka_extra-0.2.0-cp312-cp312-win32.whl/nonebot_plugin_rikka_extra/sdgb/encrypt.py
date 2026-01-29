import hashlib
import random

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

AesKey = "o2U8F6<adcYl25f_qwx_n]5_qxRcbLN>"
AesIV = "AL<G:k:X6Vu7@_U]"
ObfuscateParam = "LatuAa81"

# 1.50 -> 1.52 -- 舞萌 DX 2025
# AesKey = "a>32bVP7v<63BVLkY[xM>daZ1s9MBP<R"
# AesIV = "d6xHIKq]1J]Dt^ue"
# ObfuscateParam = "B44df8yT"

# 1.40 -- 舞萌 DX 2024
# AesKey = "n7bx6:@Fg_:2;5E89Phy7AyIcpxEQ:R@"
# AesIV = ";;KjR1C3hgB1ovXa"
# ObfuscateParam = "BEs2D5vW"


class aes_pkcs7(object):
    def __init__(self, key: str, iv: str):
        self.key = key.encode("utf-8")
        self.iv = iv.encode("utf-8")
        self.mode = AES.MODE_CBC

    def encrypt(self, content: bytes) -> bytes:
        cipher = AES.new(self.key, self.mode, self.iv)  # type: ignore
        content_padded = pad(content, AES.block_size)
        encrypted_bytes = cipher.encrypt(content_padded)
        return encrypted_bytes

    def decrypt(self, content):
        cipher = AES.new(self.key, self.mode, self.iv)  # type: ignore
        decrypted_padded = cipher.decrypt(content)
        decrypted = unpad(decrypted_padded, AES.block_size)
        return decrypted

    def pkcs7unpadding(self, text):
        length = len(text)
        unpadding = ord(text[length - 1])
        return text[0 : length - unpadding]

    def pkcs7padding(self, text):
        bs = 16
        length = len(text)
        bytes_length = len(text.encode("utf-8"))
        padding_size = length if (bytes_length == length) else bytes_length
        padding = bs - padding_size % bs
        padding_text = chr(padding) * padding
        return text + padding_text


def get_hash_api(api):
    return hashlib.md5((api + "MaimaiChn" + ObfuscateParam).encode()).hexdigest()


def CalcRandom():
    max = 1037933
    num2 = random.randint(1, max) * 2069

    num2 += 1024  # specialnum
    num3 = 0
    for i in range(0, 32):
        num3 <<= 1
        num3 += num2 % 2
        num2 >>= 1

    return num3
