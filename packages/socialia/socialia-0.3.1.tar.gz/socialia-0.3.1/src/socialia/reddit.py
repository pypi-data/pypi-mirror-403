"""Reddit API client using PRAW."""

from typing import Optional

from ._branding import get_env
from .base import BasePoster

try:
    import praw

    HAS_PRAW = True
except ImportError:
    HAS_PRAW = False


class Reddit(BasePoster):
    """Reddit API client using PRAW (Python Reddit API Wrapper)."""

    platform_name = "reddit"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        self.client_id = client_id or get_env("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or get_env("REDDIT_CLIENT_SECRET")
        self.username = username or get_env("REDDIT_USERNAME")
        self.password = password or get_env("REDDIT_PASSWORD")
        self.user_agent = user_agent or (
            get_env("REDDIT_USER_AGENT") or "Socialia v0.1"
        )
        self._reddit: Optional["praw.Reddit"] = None

    def _get_client(self) -> Optional["praw.Reddit"]:
        """Get authenticated Reddit client."""
        if not HAS_PRAW:
            return None

        if self._reddit:
            return self._reddit

        if not self.validate_credentials():
            return None

        self._reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            username=self.username,
            password=self.password,
            user_agent=self.user_agent,
        )
        return self._reddit

    def validate_credentials(self) -> bool:
        """Check if all credentials are set."""
        if not HAS_PRAW:
            return False
        return all(
            [
                self.client_id,
                self.client_secret,
                self.username,
                self.password,
            ]
        )

    def post(
        self,
        text: str,
        subreddit: str = "test",
        title: Optional[str] = None,
        url: Optional[str] = None,
        flair_id: Optional[str] = None,
    ) -> dict:
        """
        Post to a subreddit.

        Args:
            text: Post body (for self posts) or ignored for link posts
            subreddit: Target subreddit name (without r/)
            title: Post title (required for Reddit)
            url: URL for link posts (makes it a link post instead of self post)
            flair_id: Optional flair ID

        Returns:
            dict with 'success', 'id', 'url' or 'error'
        """
        if not HAS_PRAW:
            return {
                "success": False,
                "error": "PRAW not installed. Run: pip install praw",
            }

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        if not title:
            # Use first line or truncated text as title
            title = text.split("\n")[0][:300]

        reddit = self._get_client()
        if not reddit:
            return {"success": False, "error": "Could not create Reddit client"}

        try:
            sub = reddit.subreddit(subreddit)

            if url:
                # Link post
                submission = sub.submit(
                    title=title,
                    url=url,
                    flair_id=flair_id,
                )
            else:
                # Self/text post
                submission = sub.submit(
                    title=title,
                    selftext=text,
                    flair_id=flair_id,
                )

            return {
                "success": True,
                "id": submission.id,
                "url": f"https://reddit.com{submission.permalink}",
            }

        except praw.exceptions.APIException as e:
            return {"success": False, "error": f"Reddit API error: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete(self, post_id: str) -> dict:
        """
        Delete a Reddit post.

        Args:
            post_id: Reddit submission ID

        Returns:
            dict with 'success' or 'error'
        """
        if not HAS_PRAW:
            return {"success": False, "error": "PRAW not installed"}

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        reddit = self._get_client()
        if not reddit:
            return {"success": False, "error": "Could not create Reddit client"}

        try:
            submission = reddit.submission(id=post_id)
            submission.delete()
            return {"success": True, "deleted": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def comment(
        self,
        post_id: str,
        text: str,
    ) -> dict:
        """
        Add a comment to a post.

        Args:
            post_id: Reddit submission ID
            text: Comment text

        Returns:
            dict with 'success', 'id' or 'error'
        """
        if not HAS_PRAW:
            return {"success": False, "error": "PRAW not installed"}

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        reddit = self._get_client()
        if not reddit:
            return {"success": False, "error": "Could not create Reddit client"}

        try:
            submission = reddit.submission(id=post_id)
            comment = submission.reply(text)
            return {
                "success": True,
                "id": comment.id,
                "url": f"https://reddit.com{comment.permalink}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def me(self) -> dict:
        """
        Get authenticated user information.

        Returns:
            dict with 'success', user info or 'error'
        """
        if not HAS_PRAW:
            return {"success": False, "error": "PRAW not installed"}

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        reddit = self._get_client()
        if not reddit:
            return {"success": False, "error": "Could not create Reddit client"}

        try:
            user = reddit.user.me()
            return {
                "success": True,
                "id": user.id,
                "username": user.name,
                "name": user.name,
                "karma": user.link_karma + user.comment_karma,
                "link_karma": user.link_karma,
                "comment_karma": user.comment_karma,
                "created_utc": user.created_utc,
                "url": f"https://reddit.com/user/{user.name}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def feed(self, limit: int = 10) -> dict:
        """
        Get user's recent submissions.

        Args:
            limit: Maximum number of posts to return

        Returns:
            dict with 'success', 'posts' list or 'error'
        """
        if not HAS_PRAW:
            return {"success": False, "error": "PRAW not installed"}

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        reddit = self._get_client()
        if not reddit:
            return {"success": False, "error": "Could not create Reddit client"}

        try:
            posts = []
            for submission in reddit.user.me().submissions.new(limit=limit):
                posts.append(
                    {
                        "id": submission.id,
                        "title": submission.title,
                        "text": (submission.selftext[:200] + "...")
                        if len(submission.selftext) > 200
                        else submission.selftext,
                        "subreddit": submission.subreddit.display_name,
                        "score": submission.score,
                        "upvote_ratio": submission.upvote_ratio,
                        "num_comments": submission.num_comments,
                        "created_utc": submission.created_utc,
                        "url": f"https://reddit.com{submission.permalink}",
                    }
                )
            return {"success": True, "posts": posts, "count": len(posts)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mentions(self, limit: int = 10) -> dict:
        """
        Get recent inbox mentions.

        Args:
            limit: Maximum number of mentions to return

        Returns:
            dict with 'success', 'mentions' list or 'error'
        """
        if not HAS_PRAW:
            return {"success": False, "error": "PRAW not installed"}

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        reddit = self._get_client()
        if not reddit:
            return {"success": False, "error": "Could not create Reddit client"}

        try:
            mentions = []
            for item in reddit.inbox.mentions(limit=limit):
                mentions.append(
                    {
                        "id": item.id,
                        "text": item.body[:200] + "..."
                        if len(item.body) > 200
                        else item.body,
                        "author": item.author.name if item.author else "[deleted]",
                        "subreddit": item.subreddit.display_name
                        if item.subreddit
                        else None,
                        "created_utc": item.created_utc,
                        "context": item.context,
                    }
                )
            return {"success": True, "mentions": mentions, "count": len(mentions)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update(self, post_id: str, text: str) -> dict:
        """
        Edit a Reddit post.

        Args:
            post_id: Reddit submission ID
            text: New text content

        Returns:
            dict with 'success' or 'error'
        """
        if not HAS_PRAW:
            return {"success": False, "error": "PRAW not installed"}

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        reddit = self._get_client()
        if not reddit:
            return {"success": False, "error": "Could not create Reddit client"}

        try:
            submission = reddit.submission(id=post_id)
            submission.edit(text)
            return {
                "success": True,
                "id": post_id,
                "url": f"https://reddit.com{submission.permalink}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
