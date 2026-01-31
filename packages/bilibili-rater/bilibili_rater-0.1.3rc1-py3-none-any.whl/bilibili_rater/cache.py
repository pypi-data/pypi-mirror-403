#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
# author： NearlyHeadlessJack
# email: wang@rjack.cn
# datetime： 2026/1/17 10:25
# ide： PyCharm
# file: _cache.py
import logging
import os
from .exceptions import DescHandlerError


class Cache:
    def __init__(self, uid: int, handler_name: str):
        self.uid: int = uid
        self.handler_name: str = handler_name
        logging.info(f"创建缓存实例, uid:{uid}, handler_name: {handler_name}")
        self.path = f"./.bilibiliratercache/{uid}_{handler_name}"

    def use_cache(self, bvid: str) -> bool:
        file_path = self.path
        logging.info("正在检查缓存")
        try:
            # 检查缓存是否存在
            if os.path.exists(file_path):
                # 缓存存在
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content != bvid:
                        # 缓存存在但是不一致
                        logging.info("缓存未命中")
                        return False
                    # 缓存存在且一致
                    logging.info("缓存命中")
                    return True
            else:
                # 缓存不存在
                return False
        except Exception as e:
            logging.error(f"使用缓存时发生错误:{e}")
            raise DescHandlerError(f"使用缓存时发生错误:{e}")

    def update_cache(self, bvid: str):
        file_path = self.path
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"{bvid}")
            logging.info("新建缓存")
        except Exception as e:
            logging.error(f"创建缓存时发生错误:{e}")
            raise DescHandlerError(f"创建缓存时发生错误:{e}")
