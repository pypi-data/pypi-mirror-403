import random
from datetime import datetime
from typing import List

from devbricksxai.generativeai.roles.artisans.analysts.news.news_analyst import News
from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.website_analyst import WebsiteAnalyst
from devbricksx.development.log import info, debug, warn

__GOOGLE_PLAY_BASE_URL__ = "https://play.google.com"
__GOOGLE_PLAY_PROVIDER__ = "Google Play"
ANALYST_GOOGLE_PLAY = "GooglePlay"
HOSTNAME_GOOGLE_PLAY = "google.com"



class GooglePlayAnalyst(WebsiteAnalyst):

    def extract_content(self, soup):
        meta_tag = soup.find('meta', itemprop="description")
        if meta_tag:
            sibling_div = meta_tag.find_next_sibling('div')
            if sibling_div:
                return sibling_div.get_text(separator='.', strip=True)

        return ""

    def extract_title(self, soup):
        h1_tag = soup.find('h1', itemprop="name")
        if h1_tag:
            return h1_tag.get_text(strip=True)

        return ""

    def extract_cover_image(self, soup):
        img_tags = soup.find_all('img', alt="Screenshot image",
                            src=lambda src: src and src.startswith("https://play-lh.googleusercontent.com"))


        if img_tags is not None:
            cover_image_strategy = self.get_parameter("cover-image-strategy")
            debug(f"cover image strategy: {cover_image_strategy}")

            if cover_image_strategy is not None:
                if cover_image_strategy == 'random':
                    debug(f"randomly pick an cover image...")
                    img_tag = random.choice(img_tags)
                else:
                    img_index = convert_to_number(cover_image_strategy)
                    if is_in_range(img_index, len(img_tags)):
                        debug(f"pick cover image [{img_index}]...")
                        img_tag = img_tags[img_index]
                    else:
                        debug(f"pick cover image [0]...")
                        img_tag = img_tags[0]
            else:
                debug(f"pick cover image [0]...")
                img_tag = img_tags[0]

            debug(f"img_tag = {img_tag}")

            return img_tag['src'].replace("w526-h296", "w5120-h2880")

        return None

    def extract_datetime(self, soup):
        dt = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        updated_on_div = soup.find('div', string="Updated on")
        if updated_on_div:
            sibling_div = updated_on_div.find_next_sibling('div')
            if sibling_div:
                try:
                    dt = (datetime.strptime(sibling_div.get_text(strip=True), "%b %d, %Y")
                          .strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
                except ValueError:
                    dt = None


        return dt

    def __init__(self):
        super().__init__(ANALYST_GOOGLE_PLAY, __GOOGLE_PLAY_PROVIDER__, time_out=60)

    def get_support_hostnames(self) -> List[str]:
        return [
            HOSTNAME_GOOGLE_PLAY
        ]


    def identify_news_nodes(self, soup):
        app_tags = soup.find_all('a', href=lambda href: href and href.startswith('/store/apps/details?id='))

        return app_tags

    def news_node_to_news_item(self, node_of_soup):
        news_item = News()
        news_item.provider = self.provider

        if node_of_soup['href'] is None:
            return None

        headline = None

        span_tag = node_of_soup.find('span')
        debug(f"<span> in <a>: {span_tag}")
        if span_tag:
            headline = span_tag.text

        link = node_of_soup['href']
        if not link.startswith("https://"):
            link = __GOOGLE_PLAY_BASE_URL__ + link

        news_item.link = link
        news_item.title = headline.strip()
        news_item.datetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        return news_item

def convert_to_number(s):
    try:
        # Try converting to an integer
        return int(s)
    except ValueError:
        return 0

def is_in_range(number, size):
    return 0 <= number < size
