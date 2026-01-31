#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
# author： NearlyHeadlessJack
# email: wang@rjack.cn
# datetime： 2026/1/17 01:16
# ide： PyCharm
# file: _handler.py
from abc import ABC
import re


class SeasonEpisodeHandler(ABC):
    @staticmethod
    def handle(desc: str) -> tuple[int, int]:
        pass


class OnlyNumberHandler(SeasonEpisodeHandler):
    @staticmethod
    def handle(desc: str) -> tuple[int, int]:
        # 用于处理 10-3  9-2  1-4这种类型
        try:
            result = desc.split("-")
        except Exception:
            return 0, 0
        return int(result[0]), int(result[1])


class NormalLetterHandler(SeasonEpisodeHandler):
    @staticmethod
    def handle(desc: str) -> tuple[int, int]:
        # 用于处理 S01E32  S2E2  S5E16这种类型
        pattern = r"S(\d+)E(\d+)"
        match = re.search(pattern, desc, re.IGNORECASE)

        if match:
            return int(match.group(1)), int(match.group(2))
        else:
            return 0, 0


class DotHandler(SeasonEpisodeHandler):
    @staticmethod
    def handle(desc: str) -> tuple[int, int]:
        # 用于处理 1.1  1.2  1.3这种类型
        pattern = r"(\d+)\.(\d+)"
        match = re.search(pattern, desc, re.IGNORECASE)

        if match:
            return int(match.group(1)), int(match.group(2))
        else:
            return 0, 0
