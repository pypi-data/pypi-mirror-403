#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
# author： NearlyHeadlessJack
# email: wang@rjack.cn
# datetime： 2026/1/26 17:11
# ide： PyCharm
# file: imdbinfo_fetcher.py
from imdbinfo import get_movie, get_season_episodes
from bilibili_rater._internal.imdb.fetch_imdb import ImdbFetcher
import logging
from typing import Dict, Optional


class DirectFetcher(ImdbFetcher):
    def __init__(
        self,
        is_show_ranking=False,
        is_show_title=False,
        is_show_release_date=False,
        is_show_average=False,
        is_show_median=False,
    ):
        """
        直接从imdb获取信息
        :param is_show_ranking: 是否获取本季的评分排名
        :param is_show_title: 是否获取本集标题
        :param is_show_median:  是否获取本季评分中位数
        :param is_show_average: 是否获取本季平均评分
        """
        super().__init__(
            is_show_ranking,
            is_show_title,
            is_show_release_date,
            is_show_average,
            is_show_median,
        )
        self.is_show_title = is_show_title
        self.is_show_release_date = is_show_release_date
        self.is_show_ranking = is_show_ranking
        self.is_show_median = is_show_median
        self.is_show_average = is_show_average

    def fetch(
        self, resource_id: str, season: int, episode: int
    ) -> Dict[str, Optional[str]]:
        logging.info(
            f"正在获取IMDB评分，\nIMDB ID：{resource_id}，\n季号：{season}，集号：{episode}，\n显示标题：{self.is_show_title},\n显示首播日期:{self.is_show_release_date},\n显示排名:{self.is_show_ranking},\n显示平均分:{self.is_show_average},\n显示中位数:{self.is_show_median}"
        )
        resource = get_movie(resource_id)
        resource_season = get_season_episodes(resource.imdb_id, season=season).episodes
        season_episodes_num = len(resource_season)
        requested_episode = resource_season[episode - 1]
        requested_episode_rating, requested_episode_title, requested_release_date = (
            requested_episode.rating,
            requested_episode.title,
            requested_episode.release_date,
        )
        logging.info(
            f"找到目标资源信息, 本集标题为{requested_episode_title}, 本集评分为{requested_episode_rating}, 本季首播于{requested_release_date}"
        )
        result: Dict[str, Optional[str]] = {
            "title": None,
            "rating": f"{requested_episode_rating}",
            "ranking": None,
            "average": None,
            "median": None,
            "release_date": None,
        }

        sorted_season = []
        if self.is_show_title:
            result["title"] = requested_episode_title
        if self.is_show_release_date:
            result["release_date"] = requested_release_date
        if self.is_show_ranking or self.is_show_average or self.is_show_median:
            sorted_season = sorted(
                resource_season, key=lambda x: x.rating, reverse=True
            )
        if self.is_show_ranking:
            idx = 1
            for _episode in sorted_season:
                if _episode.episode == episode:
                    break
                idx += 1
            logging.info(f"本集排名为 {idx}/{season_episodes_num}")
            result["ranking"] = f"{idx}/{season_episodes_num}"
        if self.is_show_average:
            total_rating = sum(float(epi.rating) for epi in resource_season)
            average: float = total_rating / season_episodes_num
            logging.info(f"本季平均分: {average:.1f}")
            result["average"] = f"{average:.1f}"
        if self.is_show_median:
            mid = int(season_episodes_num / 2)
            for idx, epi in enumerate(sorted_season):
                if idx == mid:
                    logging.info(f"本季评分中位数: {epi.rating}")
                    result["median"] = f"{epi.rating}"
                    break

        return result
