#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
# author： NearlyHeadlessJack
# email: wang@rjack.cn
# datetime： 2026/1/17 00:40
# ide： PyCharm
# file: bilibili_fetcher.py
from bilibili_api import video, user
import logging
from bilibili_rater.exceptions import DescHandlerError


def process_desc(result: dict):
    try:
        if len(result["desc"]) <= 1:
            return {"desc": None, "bvid": None}
        if "\n" not in result["desc"]:
            return result
        result["desc"] = result["desc"].split("\n")[0]
        return result
    except Exception as e:
        logging.error(f"获取简介第一行时发生错误:{e}")
        raise DescHandlerError


class BilibiliFetcher:
    def __init__(self, uploader: int):
        logging.debug("创建BilibiliFetcher实例")
        self.uploader: int = uploader

    async def fetch(self):
        logging.info("正在获取最新视频信息")
        logging.info(f"uid: {self.uploader}")
        result = await get_latest_video_desc(uid=self.uploader)
        if result["desc"] is None:
            raise DescHandlerError("获取简介时发生错误")
        return process_desc(result)


async def get_latest_video_desc(uid: int) -> dict:
    """
    获取指定UP主最新视频的简介
    :param uid: UP主的UID（可以在其主页URL中找到）
    :returns {"desc":视频简介,"bvid":BV号}
    """
    try:
        u = user.User(uid=uid)
        video_list = await u.get_videos()
        latest_video = video_list["list"]["vlist"][0]
        logging.info(f"最新视频标题：{latest_video['title']}")
        logging.info(f"最新视频BV号：{latest_video['bvid']}")

        v = video.Video(bvid=latest_video["bvid"])
        # v = video.Video(bvid="BV1trk7BqEVJ")
        video_info = await v.get_info()
        logging.debug(f"视频简介：{video_info['desc']}")
        return {"desc": video_info["desc"], "bvid": latest_video["bvid"]}
        # return {"desc": video_info["desc"], "bvid": "BV1trk7BqEVJ"}

    except Exception as e:
        logging.error(f"在获取最新视频简介时发生错误：{e}")
        return {"desc": None, "bvid": None}
