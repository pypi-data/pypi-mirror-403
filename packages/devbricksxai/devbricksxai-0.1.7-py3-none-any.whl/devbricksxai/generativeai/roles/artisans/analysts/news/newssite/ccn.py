import re
from datetime import datetime, timezone
from typing import List

import numpy as np
import pytz

from devbricksxai.generativeai.roles.artisans.analysts.news.news_analyst import News
from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.website_analyst import WebsiteAnalyst
from devbricksx.development.log import info, debug, warn

__CNN_BASE_URL__ = "https://edition.cnn.com"
__CNN_PROVIDER__ = "CNN News"
ANALYST_CNN = "CNN"
HOSTNAME_CNN = "cnn.com"

class CNNAnalyst(WebsiteAnalyst):

    def __init__(self):
        super().__init__(ANALYST_CNN, __CNN_PROVIDER__)

    def get_support_hostnames(self) -> List[str]:
        return [
            HOSTNAME_CNN
        ]

    def identify_news_nodes(self, soup):
        containers = soup.find_all('a', class_='container__link')

        links = set()
        filtered = []
        for container in containers:
            link = container.attrs['href']

            headline = container.find('div', class_='container__headline')
            if headline is None:
                continue

            if links.__contains__(link):
                warn("skip duplicated link: {}".format(link))
                continue
            links.add(link)

            filtered.append(container)

        return filtered

    def news_node_to_news_item(self, node_of_soup):
        news_item = News()
        news_item.provider = self.provider

        if node_of_soup['href'] is None:
            return None

        link = node_of_soup['href']
        if not link.startswith("https://"):
            link = __CNN_BASE_URL__ + link

        news_item.link = link

        headline = node_of_soup.find('div', class_='container__headline')
        news_item.title = headline.get_text().strip()
        news_item.datetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        # print("crawled news: {}[{}]".format(title, link))

        return news_item

    def extract_datetime(self, soup):
        dt = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        datetime_block = soup.find('div', class_='timestamp')
        debug('date: {}'.format(datetime_block))
        if datetime_block is not None:
            time_str = datetime_block.get_text().strip()
            dt = time_reformat(time_str)

        return dt

    def extract_content(self, soup):
        texts_blocks = soup.find_all('p', class_='paragraph')
        num_of_text_blocks = len(texts_blocks)
        debug("[p, class: paragraph]: {} text blocks found".format(num_of_text_blocks))

        if num_of_text_blocks == 0:
            article_blocks = soup.find_all('article')
            for article_block in article_blocks:
                texts_blocks += article_block.find_all('p')

            num_of_text_blocks = len(texts_blocks)
            debug("[article > p]: {} text blocks found".format(num_of_text_blocks))

        content = ""
        for b in np.arange(0, num_of_text_blocks):
            content = content + "\n" + texts_blocks[b].get_text().strip()

        debug("content dumped: {}".format(content))
        if len(content) <= 0:
            return None

        return content

    def extract_title(self, soup):
        return ""

    def extract_cover_image(self, soup):
        return None

def time_reformat(time_str):
    if time_str.__contains__("Updated") or time_str.__contains__("Published"):
        time_str = time_str.replace("Updated", "").strip()
        time_str = time_str.replace("Published", "").strip()

    abbreviations = re.findall(r"\b[A-Z]{3}\b", time_str)

    new_time_str = time_str
    for abbr in abbreviations:
        try:
            name = pytz.timezone(abbr).zone
        except pytz.exceptions.UnknownTimeZoneError:
            name = "UTC"
        new_time_str = new_time_str.replace(abbr, name)

    try:
        parsed_time = datetime.strptime(new_time_str, "%I:%M %p %Z, %a %b %d, %Y")
    except Exception as err:
        info('title completion failed: {}'.format(err))
        parsed_time = datetime.now()

    utc_time = parsed_time.astimezone(timezone.utc)

    reformatted = utc_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    debug("re-format time: [{}] -> [{}]".format(time_str, reformatted))
    return reformatted
