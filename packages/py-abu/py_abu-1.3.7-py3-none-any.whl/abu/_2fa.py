# -*- coding: utf-8 -*-
# @Time    : 2024/8/7 20:58
# @Author  : Chris
# @Email   : 10512@qq.com
# @File    : _2fa.py
# @Software: PyCharm

import base64
import hmac
import time
from hashlib import sha1


def byte_secret(secret):
    missing_padding = len(secret) % 8

    if missing_padding != 0:
        secret += "=" * (8 - missing_padding)
    return base64.b32decode(secret, casefold=True)


def int_to_byte_string(i, padding=8):
    return i.to_bytes(padding, byteorder='big')


def get_2fa(secret):
    input_integer = int(time.time() / 30)
    digits = 6
    if input_integer < 0:
        raise ValueError("input must be positive integer")
    hasher = hmac.new(byte_secret(secret),
                      int_to_byte_string(input_integer), sha1)
    hmac_hash = bytearray(hasher.digest())
    offset = hmac_hash[-1] & 0xF
    code = (
            (hmac_hash[offset] & 0x7F) << 24
            | (hmac_hash[offset + 1] & 0xFF) << 16
            | (hmac_hash[offset + 2] & 0xFF) << 8
            | (hmac_hash[offset + 3] & 0xFF)
    )
    return str(code % 10 ** digits).zfill(digits)
