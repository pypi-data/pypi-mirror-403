from datetime import datetime
from typing import List

from devbricksxai.generativeai.roles.artisans.analyst import LOW_PRIORITY
from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.website_analyst import WebsiteAnalyst
from devbricksx.development.log import debug

__UNIVERSAL_PROVIDER__ = "DailyStudio"
ANALYST_UNIVERSAL = "universal"

class UniversalAnalyst(WebsiteAnalyst):

    def __init__(self):
        super().__init__(ANALYST_UNIVERSAL, __UNIVERSAL_PROVIDER__, priority=LOW_PRIORITY)


    def can_analyze(self, input_data, **kwargs) -> bool:
        if kwargs.get("action", None) is not None:
            action = kwargs["action"]
        else:
            action = WebsiteAnalyst.ACTION_EXTRACT_ITEMS
        debug(f"Action: {action}")

        if action == WebsiteAnalyst.ACTION_EXTRACT_ITEMS:
            return False
        else:
            return super().can_analyze(input_data, **kwargs)


    def get_support_hostnames(self) -> List[str]:
        return []

    def identify_news_nodes(self, soup):
        return None

    def news_node_to_news_item(self, node_of_soup):
        pass

    def extract_datetime(self, soup):
        return datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    def extract_content(self, soup):
        main_content = soup.find('div')

        if not main_content:
            return None

        # Remove unwanted tags such as scripts, styles, ads, etc.
        for unwanted in main_content(['script', 'style', 'aside', 'nav', 'footer', 'header', 'form', 'noscript']):
            if unwanted is None:
                continue

            unwanted.decompose()

        # Optionally, remove list items, tables, and ads if they are not considered primary content
        for unwanted in main_content(['li', 'table', 'iframe', 'ins', 'div']):
            if unwanted is None:
                continue

            if  unwanted.attrs is not None and 'class' in unwanted.attrs:
                if 'ad' in unwanted.get('class', []) or 'ads' in unwanted.get('class', []):
                    unwanted.decompose()

        # Extract the text and clean it up
        primary_text = main_content.get_text(separator=' ', strip=True)

        # Remove extra whitespaces
        content = ' '.join(primary_text.split())

        debug("content dumped: {}".format(content))
        if len(content) <= 0:
            return None

        return content

    def extract_title(self, soup):
        return ""

    def extract_cover_image(self, soup):
        return None
