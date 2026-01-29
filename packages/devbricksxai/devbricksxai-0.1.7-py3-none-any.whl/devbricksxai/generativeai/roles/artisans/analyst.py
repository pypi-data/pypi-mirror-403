from abc import ABC, abstractmethod
from typing import Optional

from devbricksxai.generativeai.roles.artisan import Artisan, SKILL_ANALYZING

HIGH_PRIORITY = 99
LOW_PRIORITY = 1

class Analyst(Artisan, ABC):
    PARAM_DATA = "data"

    priority: int = 0

    def __init__(self, name, provider, priority=HIGH_PRIORITY):
        super().__init__(name, provider, SKILL_ANALYZING)
        self.priority = priority

    @abstractmethod
    def analyze(self, input_data, **kwargs) ->  Optional[object]:
        pass

    @abstractmethod
    def can_analyze(self, input_data, **kwargs) -> bool:
        pass

    def craft(self, **kwargs) -> Optional[object]:
        kwargs.update(self.parameters)
        data = kwargs.pop(Analyst.PARAM_DATA, None)

        if data is None:
            raise ValueError(
                f"craft() of {self.__class__.__name__} must include [{Analyst.PARAM_DATA}] in arguments.")

        return self.analyze(data, **kwargs)


def init_analysts():
    from devbricksxai.generativeai.roles.character import register_character
    from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.bbc import BBCAnalyst
    from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.ccn import CNNAnalyst
    from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.universal import UniversalAnalyst
    from devbricksxai.generativeai.roles.artisans.analysts.news.rss.reddit import RedditAnalyst
    from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.chinanews import ChinaNewsAnalyst
    from devbricksxai.generativeai.roles.artisans.analysts.news.news_ai_analyst import NewsAIAnalyst
    from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.thepaper import ThePaperAnalyst
    from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.toutiao import ToutiaoAnalyst
    from devbricksxai.generativeai.roles.artisans.analysts.news.newssite.googleplay import GooglePlayAnalyst

    # International News
    register_character(BBCAnalyst())
    register_character(CNNAnalyst())
    register_character(RedditAnalyst())

    # Chinese News
    register_character(ChinaNewsAnalyst())
    register_character(ThePaperAnalyst())
    register_character(ToutiaoAnalyst())

    # Universal Crawler
    register_character(UniversalAnalyst())

    # AI Analyst
    register_character(NewsAIAnalyst())

    # App Website
    register_character(GooglePlayAnalyst())
