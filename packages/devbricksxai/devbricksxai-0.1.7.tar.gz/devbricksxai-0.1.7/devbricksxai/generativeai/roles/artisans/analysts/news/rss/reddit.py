import re
from datetime import datetime
import praw

from devbricksxai.generativeai.roles.artisans.analysts.news.news_analyst import NewsAnalyst, News
from devbricksxai.generativeai.roles.artisans.analysts.news.rss.rss_analyst import RSSAnalyst
from devbricksx.development.log import info, debug, warn

__REDDIT_BASE_URL__ = "https://www.reddit.com"
__REDDIT_PROVIDER__ = "Reddit"
ANALYST_REDDIT = "Reddit"
HOSTNAME_REDDIT = "reddit.com"
HOSTNAME_REDD_IT = "redd.it"

__USER_AGENT__ = "CreativePulse / 1.0 DailyStudio"
__POST_LIMIT__ = 20

class RedditAnalyst(RSSAnalyst):

    def __init__(self):
        super().__init__(ANALYST_REDDIT, __REDDIT_PROVIDER__)

    def can_analyze(self, input_data, **kwargs) -> bool:
        if isinstance(input_data, str):
            return RedditAnalyst.is_reddit_url(input_data)
        else:
            return False

    @staticmethod
    def is_reddit_url(url):
        # Define the pattern for the URL format
        pattern = r'https?://(?:www\.)?reddit\.com/r/([^/]+)/(\w+)'

        match = re.match(pattern, url)
        debug(f"url: [{url}], match: {match}")
        if match:
            return True
        else:
            return False

    @staticmethod
    def should_skip_post(post, **kwargs) -> bool:
        image_post_pattern = r'\.jpg$'

        # Use re.search() to find the pattern at the end of the URL
        match_image_post = re.search(image_post_pattern, post.url)
        if match_image_post is not None:
            warn(f"skip reddit image post: {post.url}")
            return True

        if post.selftext is None or len(post.selftext) == 0 and RedditAnalyst.is_reddit_url(post.url):
            warn(f"skip empty reddit internal url: {post.url}")
            return True

        return False

    def retrieve_news_items(self, url, **kwargs):
        debug(f"analyzing news items on: {url}")

        if kwargs.get("limit", None) is not None:
            limit = kwargs["limit"]
        else:
            limit = NewsAnalyst.MAX_ITEMS

        news_items = []

        reddit = praw.Reddit(client_id=aiSettings.reddit_client_id,
                             client_secret=aiSettings.reddit_client_secret,
                             user_agent=__USER_AGENT__)

        match = re.match(r'https?://(?:www\.)?reddit\.com/r/([^/]+)/(\w+)', url)
        if match:
            subreddit_name = match.group(1)
            sort_method = match.group(2)
        else:
            # If no subreddit name is present, assume top posts from all subreddits
            subreddit_name = 'all'
            # Extract sorting method from URL
            match = re.match(r'https?://(?:www\.)?reddit\.com/(\w+)', url)
            if match:
                sort_method = match.group(1)
            else:
                warn(f'invalid url: {url}')
                return news_items

        # Get subreddit instance
        subreddit = reddit.subreddit(subreddit_name)

        # Fetch top posts based on sorting method
        if sort_method == 'top':
            top_posts = subreddit.top(time_filter="day", limit=__POST_LIMIT__)  # You can adjust the limit as needed
        elif sort_method == 'hot':
            top_posts = subreddit.hot(time_filter="day", limit=__POST_LIMIT__)
        else:
            warn(f'invalid type: {sort_method}')
            return news_items

        skip_hostnames = [
            HOSTNAME_REDDIT,
            HOSTNAME_REDD_IT,
        ]
        for post in top_posts:
            debug(f"extracting news items for {post.title}: link = {post.url}")
            if RedditAnalyst.should_skip_post(post):
                continue

            news_item = News()

            news_item.title = post.title
            news_item.link = post.url
            news_item.provider = self.provider
            news_item.content = post.selftext

            created_utc = post.created_utc
            timestamp = int(datetime.utcfromtimestamp(created_utc).timestamp())
            news_item.datetime = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

            news_items.append(news_item)
            if len(news_items) >= limit:
                break

        return news_items
