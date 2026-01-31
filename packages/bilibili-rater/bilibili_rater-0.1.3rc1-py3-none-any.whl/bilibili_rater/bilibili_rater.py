#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
# author： NearlyHeadlessJack
# email: wang@rjack.cn
# datetime： 2026/1/16 04:12
# ide： PyCharm
# file: bilibili_rater.py
import logging
from bilibili_api import Credential
from ._internal.bilibili import BilibiliFetcher, BilibiliComment
from ._internal.imdb import ImdbFetcher
from .exceptions import DescHandlerError, ImdbItemNotFound
from .cache import Cache


class BilibiliRater:
    def __init__(
        self,
        uploader_uid: int,
        credential: Credential,
        handler,
        resource_id: str,
        imdb_fetchers: list[ImdbFetcher],
        resource_cn_name: str,
    ):
        """
        :param uploader_uid: 被跟踪up主的uid
        :param credential: 登录凭证
        :param handler: 简介第一行信息的解析函数
        :param resource_id: 节目的imdb的id(注意是总节目的id，不是单集的id)
        :param resource_cn_name: 节目中文名，用于评论区
        :param imdb_fetchers: imdb获取器, 目前仅支持omdbapi方式
        """

        logging.debug("创建BilibiliRater实例")

        # 上传者uid
        self._uploader: int = uploader_uid

        # 视频资源id
        self._resource_id: str = resource_id

        # 匹配模式（简介第一行）
        self._handler = handler

        # 视频资源中文名
        self._resource_cn_name: str = resource_cn_name

        self._credential: Credential = credential

        self._imdb_fetchers: list[ImdbFetcher] = imdb_fetchers

        self._commenter = BilibiliComment(
            credential=self._credential, resource_cn_name=resource_cn_name
        )
        self._cache = Cache(uid=self._uploader, handler_name=handler.__qualname__)

        self.job_name = (
            f"{self._uploader}-{self._handler.__qualname__}-{self._resource_cn_name}"
        )

        logging.debug(f"resource_cn_name:{self._resource_cn_name}")
        logging.debug(f"uid:{self._uploader}")
        logging.debug(f"handler: {self._handler.__qualname__}")

    async def _run_fetch_new_video_desc(self):
        """
        获取最新视频的简介并解析信息
        :return: 最新视频的季、集信息
        """
        latest_video = await BilibiliFetcher(uploader=self._uploader).fetch()
        logging.debug(f"最新视频简介：{repr(latest_video['desc'])}")
        logging.debug(f"最新视频BVID: {latest_video['bvid']}")
        try:
            season, episode = self._handler(desc=latest_video["desc"])
            if season == 0:
                logging.error("简介解析失败")
                raise DescHandlerError
            return season, episode, latest_video["bvid"]
        except Exception as e:
            logging.error(f"在解析简介时发生错误:{e}")
            raise DescHandlerError

    def _fetch_imdb_rating(self, season: int, episode: int):
        logging.info(f"准备获取imdb信息，季号:{season},集号:{episode}")
        for fetcher in self._imdb_fetchers:
            logging.info(f"使用:{fetcher.__class__} 来获取imdb信息")
            try:
                result = fetcher.fetch(
                    resource_id=self._resource_id, season=season, episode=episode
                )
                msg = self._commenter.create_comment(
                    s=season,
                    e=episode,
                    rate=result["rating"],
                    title=result["title"],
                    release_date=result["release_date"],
                    ranking=result["ranking"],
                    average=result["average"],
                    median=result["median"],
                )
                return msg
            except ImdbItemNotFound:
                logging.error(f"未找到该资源imdb信息, 方法:{fetcher.__class__}")
                continue
            except Exception as e:
                logging.error(
                    f"获取IMDB信息过程中发生不可预料的错误：{e}, 方法:{fetcher.__class__}"
                )
                continue
        logging.error("最终无法获取imdb信息, 结束获取，跳过一次更新")
        raise DescHandlerError

    async def run(self):
        try:
            # 获取up主最新视频信息
            s, e, bvid = await self._run_fetch_new_video_desc()
            logging.info(
                f"解析到节目为：{self._resource_cn_name} 第{s}季 第{e}集，BV号：{bvid}"
            )

            if self._cache.use_cache(bvid=bvid):
                logging.info("缓存命中，本次更新已跳过")
                return

            # 搜刮imdb信息并创建评论文本
            msg = self._fetch_imdb_rating(season=s, episode=e)
            # 发送评论
            await self._commenter.post_comment(bvid=bvid, msg=msg, cache=self._cache)

        except DescHandlerError as ee:
            logging.error(f"发生错误:{ee}，本次更新已跳过")
            return
        except Exception as e:
            logging.error(f"发生未知错误：{e}")
            return
