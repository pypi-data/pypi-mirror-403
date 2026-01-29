# -*- coding: utf-8 -*-
# @Time    : 2026/1/25 14:55
# @Author  : Chris
# @Email   : 10512@qq.com
# @File    : text.py
# @Software: PyCharm
import random
import string


def text_mid(target_str: str, front_str: str, back_str: str, start_position: int = 0) -> str:
    """老一辈的易语言用户的心中, 一定有一个文本取中间...哈哈哈"""
    try:
        front_pos = target_str.index(front_str, start_position) + len(front_str)
        back_pos = target_str.index(back_str, front_pos)
        return target_str[front_pos: back_pos]
    except ValueError:
        return ""


def text_mid_batch(target_str: str, front_str: str, back_str: str, start_position: int = 0) -> list[str]:
    results = []
    current_position = start_position
    while True:
        try:
            front_pos = target_str.index(front_str, current_position) + len(front_str)
            back_pos = target_str.index(back_str, front_pos)
            results.append(target_str[front_pos: back_pos])
            current_position = back_pos + len(back_str)
        except ValueError:
            break
    return results


def text_random_str(count: int = 1) -> str:
    first_char = random.choice(string.ascii_letters)
    if count == 1:
        return first_char
    remaining_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=count - 1))
    return first_char + remaining_chars


if __name__ == '__main__':
    pass
