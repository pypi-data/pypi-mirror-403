import time
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from devbricksx.common.quality_ops import retry_calls
from devbricksx.development.log import debug, warn
from devbricksxai.generativeai.roles.artisans.analysts.news.news_analyst import News
from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.website_analyst import WebsiteAnalyst

__TOUTIAO_BASE_URL__ = "https://www.toutiao.com/"
__TOUTIAO_PROVIDER__ = "Toutiao.com"
ANALYST_TOUTIAO = "Toutiao"
HOSTNAME_TOUTIAO = "toutiao.com"


class ToutiaoAnalyst(WebsiteAnalyst):

    MAX_REFRESH_TIMES = 5
    MAX_ITEMS_PER_REFRESH = 10

    def __init__(self):
        super().__init__(ANALYST_TOUTIAO, __TOUTIAO_PROVIDER__, time_out=60)

    def get_support_hostnames(self) -> List[str]:
        return [
            HOSTNAME_TOUTIAO
        ]

    def analyze(self, input_data, **kwargs) -> Optional[object]:
        if kwargs.get("action", None) is not None:
            action = kwargs["action"]
        else:
            action = WebsiteAnalyst.ACTION_EXTRACT_ITEMS

        debug(f"analyzing toutiao website: [{input_data}], action: {action}")

        if action == WebsiteAnalyst.ACTION_EXTRACT_ITEMS:
            if kwargs.get("limit", None) is not None:
                limit = kwargs["limit"]
            else:
                limit = WebsiteAnalyst.MAX_ITEMS

            debug(f"expecting item: {limit}")
            requested_limit = limit

            feeds = []

            num_of_items = 0
            # start_round = random.randint(0, self.MAX_REFRESH_TIMES - 1)
            start_round = 0
            kwargs.update({"limit": self.MAX_ITEMS_PER_REFRESH})
            for i in range(self.MAX_REFRESH_TIMES):
                if i < start_round:
                    debug(f"skip round {i}, start is {start_round}")
                    continue
                feeds_in_round = self.extract_news_items(input_data, round=i, **kwargs)
                if feeds_in_round is not None:
                    debug(f"items extracted in round[{i}]: {len(feeds_in_round)}")
                    feeds += feeds_in_round

                num_of_items = len(feeds)
                debug(f"total items after round [{i}]: {num_of_items}")

                if num_of_items >= limit * 1.5:
                    debug(f"sufficient items extracted, break: {num_of_items} item(s) extracted.")
                    break

            if num_of_items >= requested_limit:
                debug(f"too many items extracted, only pick first {requested_limit} item(s).")
                feeds = feeds[:requested_limit]

            return feeds

        else:
            return super().analyze(input_data, **kwargs)


    def perform_navigations(self, driver: webdriver.Chrome, **kwargs):
        if kwargs.get("action", None) is not None:
            action = kwargs["action"]
        else:
            action = WebsiteAnalyst.ACTION_EXTRACT_ITEMS

        if action != WebsiteAnalyst.ACTION_EXTRACT_ITEMS:
            return

        analyze_round = 0
        if kwargs.get("round", None) is not None:
            analyze_round = kwargs["round"]
        debug(f"performing navigations, round = {analyze_round}")

        for i in range(analyze_round):
            debug(f"click refresh for {i} time...")
            element_to_click = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="ttp-hot-board"]//button[@class="refresh"]'))
            )
            debug(f"hot news element found: {element_to_click}")
            driver.execute_script("arguments[0].click();", element_to_click)
            debug("element clicked, waiting for hot news loaded: ...")
            time.sleep(5)

    def identify_news_nodes(self, soup):
        hot_news_area = soup.find('div', class_="ttp-hot-board")

        if hot_news_area is None:
            warn(f"hot news area is not found.")
            return None

        news_list = hot_news_area.find('ol')
        if news_list is None:
            warn(f"hot news list is not found.")
            return None

        li_elements = news_list.find_all('li')
        if li_elements is None or len(li_elements) == 0:
            return None

        a_tags = [li.find('a') for li in li_elements]

        return a_tags

    def is_kind_of_node(self, url, kind):
        parsed_url = urlparse(url)

        path_segments = parsed_url.path.strip('/').split('/')
        if path_segments[0] == kind:
            return True
        else:
            return False

    def is_trending_node(self, url):
        return self.is_kind_of_node(url, 'trending')

    def is_article_node(self, url):
        return self.is_kind_of_node(url, 'article')

    def dig_link_in_details(self, dig_soup):
        # Filtering divs to find the one with the specific content
        title_divs = dig_soup.find_all('div', class_='block-title', text='事件详情')
        if title_divs is None or len(title_divs) == 0:
            return None

        title_div = title_divs[0]
        debug(f'title_div found: {title_div}')

        content_div = title_div.find_next_sibling('div', class_='block-content')
        if content_div is None:
            return None

        debug(f'content_div found: {content_div}')

        target_a_tags = content_div.find_all('a')
        if target_a_tags is None or len(target_a_tags) == 0:
            return None

        target_a_tag = target_a_tags[0]
        debug(f'target_a_tag found: {target_a_tag}')

        potential_link = target_a_tag.get('href')
        if self.is_article_node(potential_link):
            return potential_link

        return None
    def dig_link_in_related(self, dig_soup):
        # Filtering divs to find the one with the specific content
        title_divs = dig_soup.find_all('div', class_='block-title', text='相关内容')
        if title_divs is None or len(title_divs) == 0:
            return None

        title_div = title_divs[0]
        debug(f'title_div found: {title_div}')

        content_div = title_div.find_next_sibling('div', class_='block-content')
        if content_div is None:
            return None

        debug(f'content_div found: {content_div}')

        target_article_divs = content_div.find_all('div', class_='feed-card-article')
        if target_article_divs is None or len(target_article_divs) == 0:
            return None

        target_article_div = target_article_divs[0]
        debug(f'target_article_div found: {target_article_div}')

        target_a_tags = target_article_div.find_all('a')
        if target_a_tags is None or len(target_a_tags) == 0:
            return None

        target_a_tag = target_a_tags[0]
        debug(f'target_a_tag found: {target_a_tag}')

        potential_link = target_a_tag.get('href')
        if self.is_article_node(potential_link):
            return potential_link

        return None

    def deep_dig_link(self, url):
        page_content = retry_calls(
            self.get_html_by_url, 3, url,
            self.get_request_timeout())
        if page_content is None:
            return None

        soup = BeautifulSoup(page_content, "html.parser")

        dug_link = self.dig_link_in_details(soup)
        debug(f'dug_link in details: {dug_link}')
        if dug_link is not None:
            return dug_link

        dug_link = self.dig_link_in_related(soup)
        debug(f'dug_link in related: {dug_link}')
        if dug_link is not None:
            return dug_link

        return None

    def news_node_to_news_item(self, node_of_soup):
        news_item = News()
        news_item.provider = self.provider

        debug(f'href: {node_of_soup["href"]}')
        debug(f'title: {node_of_soup.get("aria-label")}')
        if node_of_soup['href'] is None:
            return None

        headline = node_of_soup.get('aria-label')
        if headline is None:
            return None

        link = node_of_soup['href']
        if not link.startswith("https://"):
            link = "https://" + HOSTNAME_TOUTIAO + link

        if self.is_trending_node(link):
            dug_link = self.deep_dig_link(link)
            if dug_link is None:
                warn(f'cannot find root link of trending news: {link}, skip it')
                return None
            link = dug_link

        news_item.link = link
        news_item.title = headline.strip()
        news_item.datetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        return news_item

    def extract_datetime(self, soup):
        dt = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        article_meta_node = soup.find('div', class_="article-meta")
        if article_meta_node is not None:
            time_spans = article_meta_node.find_all('span', recursive=False)
            for time_span in time_spans:
                try:
                    dt = (datetime.strptime(time_span.get_text(), '%Y-%m-%d %H:%M')
                          .strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
                except ValueError:
                    dt = None

                if dt is not None:
                    break

        debug('datetime: {}'.format(dt))

        return dt

    def extract_content(self, soup):
        texts_blocks = []
        num_of_text_blocks = 0

        main_content_node = soup.find('div', class_="article-content")
        if main_content_node is None:
            return None

        texts_blocks = main_content_node.find_all('p')
        num_of_text_blocks = len(texts_blocks)

        debug("{} text blocks found.".format(num_of_text_blocks))

        content = ""
        for b in np.arange(0, num_of_text_blocks):
            content = content + "\n" + texts_blocks[b].get_text()

        debug("content dumped: [{}]".format(content))
        if len(content) <= 0:
            return None

        return content

    def extract_title(self, soup):
        main_content_node = soup.find('div', class_="article-content")
        if main_content_node is None:
            return None

        h1 = main_content_node.find('h1')
        if h1 is None:
            return None

        return h1.get_text().strip()

    def extract_cover_image(self, soup):
        return None

