import re
from datetime import datetime
from typing import List

import numpy as np

from devbricksxai.generativeai.roles.artisans.analysts.news.news_analyst import News
from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.website_analyst import WebsiteAnalyst
from devbricksx.development.log import info, debug, warn

__THE_PAPER_BASE_URL__ = "https://www.thepaper.cn/"
__THE_PAPER_PROVIDER__ = "The Paper"
ANALYST_THE_PAPER = "ThePaper"
HOSTNAME_THE_PAPER = "www.thepaper.cn"
HOSTNAME_THE_PAPER_TOP_LEVEL = "thepaper.cn"

class ThePaperAnalyst(WebsiteAnalyst):

    def get_support_hostnames(self) -> List[str]:
        return [
            HOSTNAME_THE_PAPER,
            HOSTNAME_THE_PAPER_TOP_LEVEL
        ]

    def __init__(self):
        super().__init__(ANALYST_THE_PAPER, __THE_PAPER_PROVIDER__)

    def identify_news_nodes(self, soup):
        top_list_img_divs = soup.select('div[class^="index_rebangtop"]')
        debug(f"top_list_img_divs: {top_list_img_divs}")
        if top_list_img_divs is None or len(top_list_img_divs) == 0:
            warn(f"top list image div cannot found.")
            return None

        top_list_div = top_list_img_divs[0].find_next_sibling()
        debug(f"top_list_div: {top_list_div}")
        if top_list_div is None:
            warn(f"top list div cannot found.")
            return None

        li_elements = top_list_div.find_all('li')
        debug(f"li_elements: {li_elements}")
        if li_elements is None or len(li_elements) == 0:
            return None

        a_tags = [li.find('a') for li in li_elements]

        return a_tags

    def news_node_to_news_item(self, node_of_soup):
        news_item = News()
        news_item.provider = self.provider

        debug(f'href: {node_of_soup["href"]}')
        debug(f'title: {node_of_soup.get_text()}')
        if node_of_soup['href'] is None:
            return None

        headline = node_of_soup.get_text()
        if headline is None:
            return None

        link = node_of_soup['href']
        if not link.startswith("https://"):
            link = "https://" + HOSTNAME_THE_PAPER + link

        news_item.link = link
        news_item.title = headline.strip()
        news_item.datetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        return news_item

    def extract_datetime(self, soup):
        dt = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        pub_time_block = soup.find('div', class_='ant-space-item')
        if pub_time_block is not None:
            time_span = pub_time_block.find('span')
            if time_span is not None:
                dt = (datetime.strptime(time_span.get_text(), '%Y-%m-%d %H:%M')
                      .strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

        debug('datetime: {}'.format(dt))

        return dt

    def extract_content(self, soup):
        texts_blocks = []
        num_of_text_blocks = 0

        content_nodes = soup.select('div[class^="index_cententWrap"]')
        if content_nodes is None or len(content_nodes) == 0:
            debug('div[index_cententWrap] not found, try p[header_desc] ...')
            content_nodes = soup.select('p[class^="header_desc"]')

        if content_nodes is None or len(content_nodes) == 0:
            warn(f"content node cannot found.")
            return None

        content_node = content_nodes[0]
        debug(f"content_node: {content_node}")
        if content_node is not None:
            if content_node.name == 'p':
                texts_blocks = [content_node]
            else:
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
