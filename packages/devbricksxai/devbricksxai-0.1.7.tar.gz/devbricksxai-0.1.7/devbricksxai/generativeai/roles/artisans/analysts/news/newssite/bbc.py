from datetime import datetime
from typing import List
import re

import numpy as np

from devbricksxai.generativeai.roles.artisans.analysts.news.news_analyst import News
from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.website_analyst import WebsiteAnalyst
from devbricksx.development.log import info, debug, warn

__BBC_BASE_URL__ = "https://bbc.com"
__BBC_PROVIDER__ = "BBC News"
ANALYST_BBC = "BBC"
HOSTNAME_BBC = "bbc.com"
HOSTNAME_BBC_UK = "bbc.co.uk"

class BBCAnalyst(WebsiteAnalyst):

    def get_support_hostnames(self) -> List[str]:
        return [
            HOSTNAME_BBC,
            HOSTNAME_BBC_UK
        ]

    def __init__(self):
        super().__init__(ANALYST_BBC, __BBC_PROVIDER__)

    def identify_news_nodes(self, soup):
        nodes = soup.find_all('a', attrs={'data-testid': 'internal-link'})
        if nodes is None or len(nodes) == 0:
            debug(f"no nodes a['data-testid'] found, try a[class^='ssrcss-']")
            class_regex = re.compile(r'^ssrcss-.*-ContentStack$')
            parents = soup.find_all('div', class_=class_regex)
            if parents is not None:
                debug(f"parent div['^ssrcss-.*-ContentStack$']: {len(parents)}")

                for parent in parents:
                    class_regex = re.compile(r'^ssrcss-.*-PromoLink$')
                    nodes += parent.find_all('a', class_=class_regex)

        return nodes

    def news_node_to_news_item(self, node_of_soup):
        news_item = News()
        news_item.provider = self.provider

        if node_of_soup['href'] is None:
            return None

        headline = node_of_soup.find('h2', attrs={'data-testid': 'card-headline'})
        if headline is None:
            headline = node_of_soup.find('p')

        if headline is None:
            return None

        link = node_of_soup['href']
        if not link.startswith("https://"):
            link = __BBC_BASE_URL__ + link

        news_item.link = link
        news_item.title = headline.get_text().strip()
        news_item.datetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        return news_item

    def extract_datetime(self, soup):
        dt = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        datetime_block = soup.find('time')
        debug('date: {}'.format(datetime_block))
        if datetime_block is not None:
            if 'datetime' in datetime_block.attrs:
                time_str = datetime_block.attrs['datetime']
                dt = time_str
        debug('datetime: {}'.format(dt))

        return dt

    def extract_content(self, soup):
        texts_blocks = soup.find_all('div', attrs={'data-component': 'text-block'})
        texts_blocks += soup.find_all('section', attrs={'data-component': 'text-block'})
        num_of_text_blocks = len(texts_blocks)
        debug("[div/section, data-component: text-block]: {} text blocks found.".format(num_of_text_blocks))

        if num_of_text_blocks == 0:
            texts_blocks = soup.find_all('div', class_='body-text-card__text')
            num_of_text_blocks = len(texts_blocks)
            debug("[div, class: body-text-card__text]: {} text blocks found.".format(num_of_text_blocks))

        if num_of_text_blocks == 0:
            texts_blocks_1 = soup.find_all('li', class_='lx-c-summary-points__item')
            texts_blocks_2 = soup.find_all('div', class_='lx-stream-post-body')
            texts_blocks = texts_blocks_1 + texts_blocks_2
            num_of_text_blocks = len(texts_blocks)
            debug("[li/div, class: lx-c-summary-points__item, lx-stream-post-body']: {} text blocks found.".format(
                num_of_text_blocks))

        debug("{} text blocks found.".format(num_of_text_blocks))

        content = ""
        for b in np.arange(0, num_of_text_blocks):
            all_paragraphs = texts_blocks[b].find_all('p')
            num_of_paragraphs = len(all_paragraphs)
            debug("{} paragraphs found in text block {}".format(num_of_paragraphs, b))

            if num_of_paragraphs > 0:
                for p in np.arange(0, num_of_paragraphs):
                    content = content + "\n" + all_paragraphs[p].get_text()
            else:
                content = content + "\n" + texts_blocks[b].get_text()

        debug("content dumped: [{}]".format(content))
        if len(content) <= 0:
            return None

        return content

    def extract_title(self, soup):
        return ""

    def extract_cover_image(self, soup):
        return None
