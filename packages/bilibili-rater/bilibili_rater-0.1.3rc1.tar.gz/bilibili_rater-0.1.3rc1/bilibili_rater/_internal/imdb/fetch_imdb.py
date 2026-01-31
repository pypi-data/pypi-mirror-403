#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
# author： NearlyHeadlessJack
# email: wang@rjack.cn
# datetime： 2026/1/16 23:54
# ide： PyCharm
# file: fetch_imdb.py
import requests
import logging
from bilibili_rater.exceptions import DescHandlerError, ImdbItemNotFound
from abc import ABC
from typing import Dict, Optional


def omdb_get_imdb_rating_no_ranking(
    imdb_id: str, season: int, _episode: int, api: str, is_show_title: bool
) -> dict:
    """
    获取IMDB评分
    :param imdb_id: IMDB ID  一般以tt开头
    :param season: 剧集季号
    :param _episode: 集号
    :param api: OMDB网站的api
    :param is_show_title: 是否需要单集标题
    :return: 评分信息及标题信息(如需要)
    """

    url = f"http://www.omdbapi.com/?apikey={api}&i={imdb_id}&Season={str(season)}"
    response = requests.get(url).json()

    result: Dict[str, Optional[str]] = {
        "title": None,
        "rating": None,
        "ranking": None,
        "average": None,
        "median": None,
        "release_date": None,
    }

    for episode in response["Episodes"]:
        if episode["Episode"] == str(_episode):
            logging.info(
                f"找到目标资源imdb信息: S{season}E{episode['Episode']} 标题: {episode['Title']} 评分: {episode['imdbRating']}"
            )
            result["rating"] = episode["imdbRating"]
            if is_show_title:
                result["title"] = episode["Title"]
            return result

    logging.error(f"未找到S{season}E{_episode}的imdb信息")
    raise ImdbItemNotFound(f"未找到S{season}E{_episode}的imdb信息")


# def omdb_get_imdb_rating_with_ranking(
#     imdb_id: str, season: int, _episode: int, api: str, is_show_title=False
# ) -> dict:
#     url = f"http://www.omdbapi.com/?apikey={api}&i={imdb_id}&Season={str(season)}"
#     response = requests.get(url).json()
#     a = response["Episodes"]
#     try:
#         sorted_movies = sorted(a, key=lambda x: float(x["imdbRating"]), reverse=True)
#         i = 0
#         total = len(sorted_movies)
#         for episode in sorted_movies:
#             i += 1
#             if episode["Episode"] == str(_episode):
#                 rank = f"{i}/{total}"
#                 logging.info(
#                     f"找到目标资源imdb信息: S{season}E{episode['Episode']} 评分: {episode['imdbRating']} 排名: {rank}"
#                 )
#                 return {
#                     "title": episode["Title"],
#                     "rating": episode["imdbRating"],
#                     "ranking": rank,
#                 }
#
#     except ValueError:
#         logging.error("本季有无法解析的IMDB评分, 不提供ranking排名")
#         return omdb_get_imdb_rating_no_ranking(
#             imdb_id=imdb_id, season=season, _episode=_episode, api=api
#         )
#     except Exception as e:
#         logging.error(f"获取IMDB信息过程中发生错误：{e}")
#         raise ImdbItemNotFound(f"获取IMDB信息过程中发生错误：{e}")
#     logging.error(f"未找到S{season}E{_episode}的imdb信息")
#     raise ImdbItemNotFound(f"未找到S{season}E{_episode}的imdb信息")


class ImdbFetcher(ABC):
    def __init__(
        self,
        is_show_ranking=False,
        is_show_title=False,
        is_show_release_date=False,
        is_show_average=False,
        is_show_median=False,
    ):
        self.is_show_title = is_show_title
        self.is_show_release_date = is_show_release_date
        self.is_show_ranking = is_show_ranking
        self.is_show_average = is_show_average
        self.is_show_median = is_show_median

    def fetch(
        self, resource_id: str, season: int, episode: int
    ) -> Dict[str, Optional[str]]:
        pass


class OmdbFetcher(ImdbFetcher):
    def __init__(self, api_key: str, is_show_title=False):
        """
        从omdb数据库获取imdb信息
        :param api_key: omdb的api key
        :param is_show_title: 是否获取本集标题
        """
        super().__init__(
            is_show_ranking=False,
            is_show_title=False,
            is_show_release_date=False,
            is_show_median=False,
            is_show_average=False,
        )
        self.api_key = api_key

    def fetch(
        self, resource_id: str, season: int, episode: int
    ) -> Dict[str, Optional[str]]:
        logging.info(
            f"正在获取IMDB评分，IMDB ID：{resource_id}，季号：{season}，集号：{episode}，显示标题：{self.is_show_title},显示排名:{self.is_show_ranking}"
        )
        try:
            result = omdb_get_imdb_rating_no_ranking(
                resource_id,
                season,
                episode,
                self.api_key,
                is_show_title=self.is_show_title,
            )
            return result
        except ImdbItemNotFound:
            raise ImdbItemNotFound(f"未找到S{season}E{episode}的imdb信息")
        except Exception as e:
            logging.error(f"获取IMDB信息过程中发生错误：{e}")
            raise DescHandlerError(f"获取IMDB信息过程中发生错误：{e}")
