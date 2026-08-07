"""
Reddit Fetcher — trending posts from configured subreddits.
Create app: https://www.reddit.com/prefs/apps → "script" type.
"""
import logging
import asyncio

logger = logging.getLogger("trend-pipeline.reddit")

class RedditFetcher:
    def __init__(self, client_id, client_secret, user_agent, subreddits):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.subreddits = subreddits
        self._reddit = None

    async def _get_reddit(self):
        """Lazy init Reddit client."""
        if self._reddit is None:
            import praw
            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
                check_for_async=False,
            )
        return self._reddit

    async def fetch(self):
        """Fetch hot posts from all configured subreddits."""
        if not self.client_id:
            logger.warning("Reddit API keys not configured — skipping")
            return []

        posts = []
        try:
            reddit = await self._get_reddit()
            for sub_name in self.subreddits:
                try:
                    sub = reddit.subreddit(sub_name)
                    for post in sub.hot(limit=8):
                        if not post.stickied:
                            posts.append({
                                "title": post.title,
                                "url": f"https://reddit.com{post.permalink}",
                                "score": post.score,
                                "num_comments": post.num_comments,
                                "subreddit": sub_name,
                                "created_utc": post.created_utc,
                            })
                    logger.info(f"Reddit/r/{sub_name}: {min(8, sub._fetch_count if hasattr(sub, '_fetch_count') else 8)} posts")
                except Exception as e:
                    logger.warning(f"Reddit/r/{sub_name}: {e}")
                await asyncio.sleep(2)  # Rate limit: 30 req/min without auth
        except Exception as e:
            logger.error(f"Reddit init failed: {e}")

        # Sort by engagement (score + comments)
        posts.sort(key=lambda p: p["score"] + p["num_comments"] * 2, reverse=True)
        return posts[:60]
