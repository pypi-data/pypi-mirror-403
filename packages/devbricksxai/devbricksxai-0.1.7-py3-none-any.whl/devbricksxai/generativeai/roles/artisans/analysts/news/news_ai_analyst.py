from abc import ABC
from typing import Optional

from devbricksx.common.json_convert import JsonConvert
from devbricksx.common.quality_ops import retry_calls
from devbricksx.development.log import debug, warn, error
from devbricksxai.generativeai.roles.advisor import Advisor
from devbricksxai.generativeai.roles.artisans.analyst import Analyst
from devbricksxai.generativeai.roles.artisans.analysts.news.news_analyst import News
from devbricksxai.generativeai.roles.character import get_character_by_name

__NEWS_AI_PROVIDER__ = "DailyStudio"
ANALYST_NEWS_AI = "newsai"

class NewsAIAnalyst(Analyst, ABC):

    TOPIC_DOMAIN = [
        "Agriculture",
        "Athletes",
        "Construction",
        "Arts",
        "Business",
        "Education",
        "Finance",
        "Government",
        "Healthcare",
        "Hospitality",
        "Services",
        "IT",
        "Law",
        "Manufacturing",
        "Marketing",
        "STEM",
        "Transportation",
        "Catering",
        "Application",
        "Game",
    ]

    SUMMARIZE_NEWS_REQUIREMENT = (
        "Here is a news content: {}. "
        "Summarize it, and provide me a title, an abstraction, tags of it."
        "Keep in mind that: "
        "- both the title and the abstraction should keep the same language as the original content."
        "- the content might include some useless information, like tab title, ads., meta data, skip those information."
        "- the abstraction is no more than 5 sentences."
        "- the tags is keywords that directly what the category the news belongs to. They should be in English."
        "   - The first tag must be the topic domain. It should be one of following items: [{}]."
        "   - The second tag must be the country that the news happened."
    )

    SUMMARIZE_NEWS_OUTPUT = (
        "Return me a JSON object that includes the following fields: "
        "1. title. The title of the news."
        "2. abstract. Briefly describe what is the news talking about. "
        "3. tags. A list of 5 string that reflects the categories of the news."
        "Return me JSON only in plain text not code format, "
        "do not add any extra information or explanation."
    )

    def __init__(self):
        super().__init__(ANALYST_NEWS_AI, __NEWS_AI_PROVIDER__)

    def can_analyze(self, input_data, **kwargs) -> bool:
        return isinstance(input_data, News)

    def summarize_news(self, news_item: News, advisor: Advisor) -> News:
        debug(f"summarizing news: {news_item}")
        if news_item.content is None:
            return news_item

        content_requirement = self.SUMMARIZE_NEWS_REQUIREMENT.format(
            news_item.content,
            self.TOPIC_DOMAIN,
        )

        output_requirement = self.SUMMARIZE_NEWS_OUTPUT.format()

        prompts =[content_requirement, output_requirement]

        summary = retry_calls(self.generate_output_,
                              3,
                              advisor,
                              prompts)
        debug(f"summary: {summary}")

        if summary is not None:
            if news_item.title is None or len(news_item.title) == 0:
                news_item.title = summary.title

            news_item.abstract = summary.abstract
            news_item.tags = summary.tags

        return news_item

    def generate_output_(self, advisor, prompts) -> News:
        result = advisor.craft(
            prompt=prompts
        )

        debug(f"result = {result}")

        try:
            result = JsonConvert.from_json(f'''{result}''', News)
        except Exception as err:
            error(f"failed to parse news from [{result}]: {err}")
            result = None

        return result

    def analyze(self, input_data, **kwargs) -> Optional[object]:
        if not isinstance(input_data, News):
            return input_data

        advisor_name = kwargs.get('advisor', None)
        if advisor_name is None:
            return input_data
        advisor = get_character_by_name(advisor_name)
        if advisor is None:
            return input_data

        debug(f"using advisor: {advisor_name}")

        updated_news = self.summarize_news(input_data, advisor)
        if updated_news is not None:
            return updated_news

        return input_data