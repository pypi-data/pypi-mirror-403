# -*- coding: utf-8 -*-
# @Time    : 2024/8/8 10:37
# @Author  : Chris
# @Email   : 10512@qq.com
# @File    : tools.py
# @Software: PyCharm
import asyncio
import datetime
import io
import os
import signal
import threading
import time
import traceback
from typing import Callable
import msoffcrypto
import pandas as pd
from loguru import logger


def retry_with_method(max_attempts=9, retry_method=None, log=False, *closer_args, **closer_kwargs):
    """try to run the function for max_attempts times, if failed, run the retry_method"""

    def decorator(func):
        def _handle_error(func_name, attempts):
            """处理错误的公共逻辑"""
            logger.error(f"{func_name}运行过程错误正在重试第{attempts + 1}次!")
            if log:
                logger.error(traceback.format_exc())
            if attempts == max_attempts - 1:
                logger.error(f"{func_name}重试超过{attempts + 1}次,放弃任务!")

        def wrapper(*args, **kwargs):
            for attempts in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except BaseException:
                    _handle_error(func.__name__, attempts)
                    if retry_method:
                        retry_method(*args, *closer_args, **kwargs, **closer_kwargs)
                    if attempts < max_attempts - 1:
                        time.sleep(3)
            return None

        async def async_wrapper(*args, **kwargs):
            for attempts in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except BaseException:
                    _handle_error(func.__name__, attempts)
                    if retry_method:
                        retry_method(*args, *closer_args, **kwargs, **closer_kwargs)
                    if attempts < max_attempts - 1:
                        await asyncio.sleep(3)
            return None

        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    return decorator


def wait_for_next_google_effect():
    t = datetime.datetime.now().second
    if t < 30:
        while datetime.datetime.now().second < 30:
            time.sleep(1)
    else:
        while datetime.datetime.now().second >= 30:
            time.sleep(1)


async def wait_for_next_google_effect_async():
    t = datetime.datetime.now().second
    if t < 30:
        while datetime.datetime.now().second < 30:
            await asyncio.sleep(1)
    else:
        while datetime.datetime.now().second >= 30:
            await asyncio.sleep(1)


def over(endingFunc: Callable = None) -> None:
    """结束程序"""
    if endingFunc:
        if asyncio.iscoroutinefunction(endingFunc):
            hasattr(
                asyncio, "WindowsSelectorEventLoopPolicy"
            ) and asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy()
            )
            asyncio.run(endingFunc())
        else:
            endingFunc()
    logger.warning("Process finished with exit code 15")
    os.kill(os.getpid(), signal.SIGTERM)


def _decrypt_excel_file(path, password):
    """
    解密Excel文件的公共函数

    参数:
    path: Excel文件路径
    password: 密码

    返回:
    pd.DataFrame: 解密后读取的DataFrame
    """
    if not os.path.exists(path):
        logger.error(f"错误: 文件不存在 - {path}")
        return None

    try:
        decrypted = io.BytesIO()
        with open(path, 'rb') as f:
            office_file = msoffcrypto.OfficeFile(f)
            office_file.load_key(password=password)
            office_file.decrypt(decrypted)

        decrypted.seek(0)
        df = pd.read_excel(decrypted, engine='openpyxl', header=None)
        logger.debug(f"成功读取文件: {path}")
        logger.debug(f"数据形状: {df.shape}")
        return df
    except msoffcrypto.exceptions.DecryptionError:
        logger.error(f"错误: 密码错误或文件未加密")
        return None
    except Exception as e:
        logger.error(f"错误: 读取文件时出现问题 - {str(e)}")
        return None


class SetInterval:
    def __init__(self, func, interval, *args, **kwargs):
        self.func = func
        self.func(*args, **kwargs)
        self.interval = interval
        self.args = args
        self.kwargs = kwargs
        self.timer = None
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.func(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self.timer = threading.Timer(self.interval, self._run)
            self.timer.start()
            self.is_running = True

    def stop(self):
        if self.timer:
            self.timer.cancel()
        self.is_running = False

    def cancel(self):
        self.stop()


def open_excel_with_columns(path, password, address_col=None, key_col=None):
    """
    打开带密码保护的Excel文件并使用指定的列名返回列表

    参数:
    path: Excel文件路径
    password: 密码
    address_col: 地址列的索引（从0开始，因为没有列名）
    key_col: 密钥列的索引（从0开始，因为没有列名）

    返回:
    list: ['address----key', 'address1----key2', ...] 格式的列表
    """
    df = _decrypt_excel_file(path, password)
    if df is None:
        return None

    try:
        logger.debug(f"列名: {df.columns.tolist()}")

        # 如果没有指定列，使用前两列
        if address_col is None:
            address_col = 0
        if key_col is None:
            key_col = 1

        # 获取指定列的数据
        col1 = df.iloc[:, address_col]
        col2 = df.iloc[:, key_col]

        # 组合成 'address----key' 格式
        result_list = []
        for i in range(len(df)):
            addr = str(col1.iloc[i]) if pd.notna(col1.iloc[i]) else ''
            key = str(col2.iloc[i]) if pd.notna(col2.iloc[i]) else ''

            if addr and key:  # 只添加非空的记录
                result_list.append(f"{addr}----{key}")

        logger.debug(f"成功转换 {len(result_list)} 条记录")
        return result_list

    except IndexError as e:
        logger.error(f"错误: 列索引超出范围 - {str(e)}")
        return None
    except Exception as e:
        logger.error(f"错误: 处理数据时出现问题 - {str(e)}")
        return None


def open_excel_single_text(path, password, lines=1):
    """
    打开带密码保护的Excel文件并读取第一行第一列的长文本

    参数:
    path: Excel文件路径
    password: 密码
    lines: 读取的行数，默认为1

    返回:
    str: 第一行第一列的文本内容
    """
    df = _decrypt_excel_file(path, password)
    if df is None:
        return None

    try:
        # 获取第一行第一列的内容
        if not df.empty and len(df.columns) > 0:
            text_content = []
            for i in range(lines):
                text_content.append(str(df.iloc[0, i]) if pd.notna(df.iloc[0, i]) else '')
            return '----'.join(text_content)
        else:
            logger.error("错误: Excel文件为空")
            return None

    except Exception as e:
        logger.error(f"错误: 处理数据时出现问题 - {str(e)}")
        return None
