#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
# author： NearlyHeadlessJack
# email: wang@rjack.cn
# datetime： 2026/1/17 01:44
# ide： PyCharm
# file: bilibili_comment.py
from bilibili_api import Credential, comment
from bilibili_rater.exceptions import DescHandlerError
from bilibili_rater.cache import Cache
import logging
import os


class BilibiliComment:
    def __init__(self, credential: Credential, resource_cn_name: str):
        """
        :param credential: 登录凭证
        :param resource_cn_name:  节目中文名
        """
        logging.debug("创建BilibiliComment实例")
        self.credential: Credential = credential
        self.cn_name = resource_cn_name

    def create_comment(
        self,
        s: int,
        e: int,
        rate: str,
        title=None,
        release_date=None,
        ranking=None,
        average=None,
        median=None,
    ) -> str:
        # 季-集
        msg1 = f"本集是《{self.cn_name}》第{s}季，第{e}集。"
        # 标题
        msg2 = ""
        # 评分
        msg3 = f"本集imdb评分为{rate}。"
        # 排名
        msg4 = ""
        # 平均分
        msg5 = ""
        # 中位数
        msg6 = ""
        # 首播日期
        msg7 = ""

        try:
            if title is not None:
                msg2 = f"本集的标题是：{title}。"
            if ranking is not None:
                msg4 = f"本集评分在本季的排名为{ranking}。"
            if average is not None:
                msg5 = f"本季的平均分是{average}。"
            if median is not None:
                msg6 = f"本季评分的中位数是{median}。"
            if release_date is not None:
                msg7 = f"本集首播于{release_date}。"
            msg = msg1 + msg2 + msg7 + "\n" + msg3 + msg4 + "\n" + msg5 + msg6
            logging.info(f"准备发送评论: {msg}")
            return msg
        except Exception as e:
            logging.error(f"发生错误:{e}")
            raise DescHandlerError(f"准备评论文本时发生错误:{e}")

    async def post_comment(self, bvid: str, msg: str, cache: Cache):
        logging.info("正在发送评论")
        try:
            is_debug = os.environ.get("IS_DEBUG")
        except KeyError:
            is_debug = "0"
        try:
            is_sd_msg = os.environ.get("IS_SD_MSG")
        except KeyError:
            is_sd_msg = "0"

        if is_debug == "1" and is_sd_msg == "1":
            logging.debug("debug模式，但是发送评论")
        elif is_debug == "1" and is_sd_msg != "1":
            logging.debug("debug模式，不发送评论")
            return
        try:
            resp = await comment.send_comment(
                text=msg,
                oid=bvid,
                credential=self.credential,
                type_=comment.CommentResourceType.VIDEO,
            )
            logging.info("评论发送成功！", resp)
            logging.debug(f"更新缓存, bvid: {bvid}")
            cache.update_cache(bvid=bvid)
            logging.info(f"缓存更新成功, bvid: {bvid}")

        except Exception as e:
            logging.error(f"评论发送失败，错误信息：{e}")
            raise DescHandlerError(f"评论发送失败，错误信息：{e}")
