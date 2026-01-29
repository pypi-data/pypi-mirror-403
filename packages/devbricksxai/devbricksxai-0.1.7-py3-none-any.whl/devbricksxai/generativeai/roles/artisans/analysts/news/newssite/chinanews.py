import re
from datetime import datetime
from typing import List

import numpy as np

from devbricksxai.generativeai.roles.artisans.analysts.news.news_analyst import News
from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.website_analyst import WebsiteAnalyst
from devbricksx.development.log import info, debug, warn

__CHINA_NEWS_BASE_URL__ = "https://www.chinanews.com"
__CHINA_NEWS_PROVIDER__ = "CHINA News"
ANALYST_CHINA_NEWS = "ChinaNews"
HOSTNAME_CHINA_NEWS = "chinanews.com"
HOSTNAME_CHINA_NEWS_CN = "chinanews.com.cn"

class ChinaNewsAnalyst(WebsiteAnalyst):

    def get_support_hostnames(self) -> List[str]:
        return [
            HOSTNAME_CHINA_NEWS,
            HOSTNAME_CHINA_NEWS_CN,
        ]

    def __init__(self):
        super().__init__(ANALYST_CHINA_NEWS, __CHINA_NEWS_PROVIDER__)

    def identify_news_nodes(self, soup):
        rd_list = soup.find_all('div', class_='rdph-list')
        if rd_list is None:
            return None

        # Find all <li> elements
        li_elements = rd_list[0].find_all('li')
        if li_elements is None or len(li_elements) == 0:
            return None

        a_tags = [li.find('a') for li in li_elements]

        return a_tags

    def news_node_to_news_item(self, node_of_soup):
        news_item = News()
        news_item.provider = self.provider

        debug(f'href: {node_of_soup["href"]}')
        debug(f'title: {node_of_soup["title"]}')
        if node_of_soup['href'] is None:
            return None

        headline = node_of_soup["title"]
        if headline is None:
            return None

        link = node_of_soup['href']
        if not link.startswith("https://"):
            link = "https:" + link

        news_item.link = link
        news_item.title = headline.strip()
        news_item.datetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        return news_item

    def extract_datetime(self, soup):
        dt = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        pub_time_block = soup.find('div', class_='content_left_time')
        if pub_time_block is not None:
            datetime_str = ''.join(t for t in pub_time_block.children if isinstance(t, str)).strip()

            if datetime_str is not None and len(datetime_str) > 0:
                regex = r'(\d{4})年(\d{2})月(\d{2})日 (\d{2}):(\d{2})'

                # Extract and parse date and time from string1
                match = re.search(regex, datetime_str)
                if match:
                    date_time_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}:{match.group(5)}"
                    debug('date_time_str: {}'.format(date_time_str))
                    dt = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M').strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        debug('datetime: {}'.format(dt))

        return dt

    def extract_content(self, soup):
        texts_blocks = []
        num_of_text_blocks = 0

        content_node = soup.find('div', class_='left_zw')
        debug(f"content_node: {content_node}")
        if content_node is not None:
            texts_blocks = content_node.find_all('p')
            num_of_text_blocks = len(texts_blocks)
        debug("[div/content p]: {} text blocks found.".format(num_of_text_blocks))

        debug("{} text blocks found.".format(num_of_text_blocks))

        content = ""
        for b in np.arange(0, num_of_text_blocks):
            content = content + "\n" + texts_blocks[b].get_text()

        debug("content dumped: [{}]".format(content))
        if len(content) <= 0:
            return None

        return content

    def extract_title(self, soup):
        return ""

    def extract_cover_image(self, soup):
        return None
