from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np
from bs4 import BeautifulSoup

from devbricksx.common.quality_ops import retry_calls
from devbricksx.development.log import debug, warn
from devbricksxai.generativeai.roles.artisans.analyst import HIGH_PRIORITY
from devbricksxai.generativeai.roles.artisans.analysts.news.news_analyst import NewsAnalyst, News


class WebsiteAnalyst(NewsAnalyst, ABC):

    DEFAULT_TIMEOUT = 20
    LONG_TIMEOUT = 40
    SHORT_TIMEOUT = 10

    request_timeout: int = 5

    def __init__(self, name, provider, time_out=DEFAULT_TIMEOUT, priority=HIGH_PRIORITY):
        super().__init__(name, provider, priority)
        self.request_timeout = time_out

    def analyze(self, input_data, **kwargs) -> Optional[object]:
        if kwargs.get("action", None) is not None:
            action = kwargs["action"]
        else:
            action = WebsiteAnalyst.ACTION_EXTRACT_ITEMS

        debug(f"analyzing news website: [{input_data}], action: {action}")

        if action == WebsiteAnalyst.ACTION_EXTRACT_ITEMS:
            return self.extract_news_items(input_data, **kwargs)
        elif action == WebsiteAnalyst.ACTION_ANALYZE_ITEM:
            if isinstance(input_data, News):
                return self.analyze_news_item(input_data, **kwargs)
            elif isinstance(input_data, str):
                return self.analyze_url(input_data, **kwargs)
            else:
               raise ValueError(
                    f"unsupported input data [{input_data}] for analyst.")
        else:
            warn(f"unsupported action [{action}] for analyst.")

            return None

    def get_request_timeout(self):
        timeout_in_param = self.get_parameter("timeout")
        if timeout_in_param is not None:
            debug(f"using timeout in parameter: {timeout_in_param}")
            timeout = int(timeout_in_param)
        else:
            debug(f"using default timeout in scribe: {self.request_timeout}")
            timeout = self.request_timeout

        return timeout

    def extract_news_items(self, url, **kwargs):
        page_content = retry_calls(
            self.get_html_by_url,3,url,
            self.get_request_timeout(), **kwargs)
        # debug(f"extract_news_items page: {page_content}")

        if kwargs.get("limit", None) is not None:
            limit = kwargs["limit"]
        else:
            limit = WebsiteAnalyst.MAX_ITEMS

        soup = BeautifulSoup(page_content, "html.parser")

        nodes = self.identify_news_nodes(soup)
        num_of_items = 0
        if nodes is not None:
            num_of_items = len(nodes)
        debug("extracted nodes: {}".format(num_of_items))

        news_feed = []
        for n in np.arange(0, num_of_items):
            news_item = self.news_node_to_news_item(nodes[n])

            if news_item is None:
                continue

            news_feed.append(news_item)
            # debug("adding extracted news: {}".format(news_item))

            if len(news_feed) >= limit:
                break

        return news_feed

    def analyze_url(self, url, **kwargs):
        page_content = retry_calls(
            self.get_html_by_url, 3, url,
            self.get_request_timeout(), **kwargs)
        if page_content is None:
            return None

        soup = BeautifulSoup(page_content, "html.parser")

        news = News()

        news.provider = self.provider
        news.title = self.extract_title(soup)
        news.content = self.extract_content(soup)
        news.datetime = self.extract_datetime(soup)
        news.cover_image = self.extract_cover_image(soup)

        copied_url = self.copy_cover_image(news.cover_image, **kwargs)
        if copied_url is not None:
            news.cover_image = copied_url

        return news

    def analyze_news_item(self, news, **kwargs):
        url = news.link

        updated_news = self.analyze_url(url, **kwargs)
        if updated_news is None:
            return news

        if updated_news.title is not None:
            news.title = updated_news.title

        if updated_news.content is not None:
            news.content = updated_news.content

        if updated_news.datetime is not None:
            news.datetime = updated_news.datetime

        if updated_news.cover_image is not None:
            news.cover_image = updated_news.cover_image

        news.provider = self.provider

        return news

    def can_analyze(self, input_data, **kwargs) -> bool:
        url = None
        if isinstance(input_data, News):
            url = input_data.link
        elif isinstance(input_data, str):
            url = input_data

        if url is None:
            return False

        hostname = self.get_hostname(input_data)
        support_hostnames = self.get_support_hostnames()
        debug(f"hostname: {hostname}, support_hostnames: [{support_hostnames}")

        if len(support_hostnames) == 0:
            return True

        return self.get_hostname(input_data) in self.get_support_hostnames()

    @staticmethod
    def is_valid_item(item):
        if item.content is None or len(item.content) == 0:
            return False

        return True

    @abstractmethod
    def identify_news_nodes(self, soup):
        pass
    @abstractmethod
    def news_node_to_news_item(self, node_of_soup):
        pass

    @abstractmethod
    def extract_content(self, soup):
        pass

    @abstractmethod
    def extract_title(self, soup):
        pass

    @abstractmethod
    def extract_cover_image(self, soup):
        pass

    @abstractmethod
    def extract_datetime(self, soup):
        pass

    @abstractmethod
    def get_support_hostnames(self) -> List[str]:
        pass
