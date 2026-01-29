from abc import ABC
from typing import Optional

from devbricksxai.generativeai.roles.artisans.analysts.news.news_analyst import NewsAnalyst
from devbricksx.development.log import debug, warn

class RSSAnalyst(NewsAnalyst, ABC):

    def analyze(self, input_data, **kwargs) -> Optional[object]:
        if kwargs.get("action", None) is not None:
            action = kwargs["action"]
        else:
            action = NewsAnalyst.ACTION_EXTRACT_ITEMS

        debug(f"analyzing news website: [{input_data}], action: {action}")

        if action == NewsAnalyst.ACTION_EXTRACT_ITEMS:
            return self.retrieve_news_items(input_data, **kwargs)
        else:
            warn(f"unsupported action [{action}] for analyst.")

            return None

    def retrieve_news_items(self, input_data, **kwargs):
        pass