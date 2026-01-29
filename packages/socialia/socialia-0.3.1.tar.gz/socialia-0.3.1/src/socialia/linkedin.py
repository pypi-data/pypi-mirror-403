"""LinkedIn API client."""

from typing import Optional
import requests

from .base import BasePoster
from ._branding import get_env


class LinkedIn(BasePoster):
    """LinkedIn API client using OAuth 2.0."""

    platform_name = "linkedin"

    BASE_URL = "https://api.linkedin.com/v2"
    ME_ENDPOINT = f"{BASE_URL}/me"
    USERINFO_ENDPOINT = f"{BASE_URL}/userinfo"  # OpenID Connect endpoint
    UGC_POSTS_ENDPOINT = f"{BASE_URL}/ugcPosts"
    POSTS_ENDPOINT = f"{BASE_URL}/posts"
    SHARES_ENDPOINT = f"{BASE_URL}/shares"

    def __init__(
        self,
        access_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.access_token = access_token or get_env("LINKEDIN_ACCESS_TOKEN")
        self.client_id = client_id or get_env("LINKEDIN_CLIENT_ID")
        self.client_secret = client_secret or get_env("LINKEDIN_CLIENT_SECRET")
        self._user_urn: Optional[str] = None

    def _get_headers(self) -> dict:
        """Get headers for LinkedIn API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202501",
            "Content-Type": "application/json",
        }

    def validate_credentials(self) -> bool:
        """Check if access token is set."""
        return bool(self.access_token)

    def _get_user_urn(self) -> Optional[str]:
        """Get the authenticated user's URN."""
        if self._user_urn:
            return self._user_urn

        if not self.validate_credentials():
            return None

        # Try OpenID Connect userinfo endpoint first (requires openid scope)
        response = requests.get(
            self.USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        if response.status_code == 200:
            user_data = response.json()
            # OpenID returns 'sub' as the user identifier
            if "sub" in user_data:
                self._user_urn = f"urn:li:person:{user_data['sub']}"
                return self._user_urn

        # Fallback to /me endpoint (requires r_liteprofile scope)
        response = requests.get(self.ME_ENDPOINT, headers=self._get_headers())
        if response.status_code == 200:
            user_data = response.json()
            self._user_urn = f"urn:li:person:{user_data['id']}"
            return self._user_urn

        return None

    def post(
        self,
        text: str,
        visibility: str = "PUBLIC",
    ) -> dict:
        """
        Post to LinkedIn feed.

        Args:
            text: Post content
            visibility: PUBLIC, CONNECTIONS, or LOGGED_IN

        Returns:
            dict with 'success', 'id', 'url' or 'error'
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing access token"}

        author_urn = self._get_user_urn()
        if not author_urn:
            return {"success": False, "error": "Could not get user URN"}

        # Using UGC Posts API (more widely available)
        post_data = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }

        response = requests.post(
            self.UGC_POSTS_ENDPOINT, headers=self._get_headers(), json=post_data
        )

        if response.status_code == 201:
            post_id = response.headers.get("X-RestLi-Id", "")
            return {
                "success": True,
                "id": post_id,
                "url": f"https://www.linkedin.com/feed/update/{post_id}/",
            }
        else:
            return {
                "success": False,
                "error": f"{response.status_code}: {response.text}",
            }

    def delete(self, post_id: str) -> dict:
        """
        Delete a LinkedIn post.

        Note: LinkedIn API has limited delete support.

        Args:
            post_id: Post URN/ID to delete

        Returns:
            dict with 'success' or 'error'
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing access token"}

        # LinkedIn delete endpoint
        url = f"{self.UGC_POSTS_ENDPOINT}/{post_id}"
        response = requests.delete(url, headers=self._get_headers())

        if response.status_code in (200, 204):
            return {"success": True, "deleted": True}
        else:
            return {
                "success": False,
                "error": f"{response.status_code}: {response.text}",
            }

    def get_token_info(self) -> dict:
        """Get information about the current access token."""
        if not self.validate_credentials():
            return {"valid": False, "error": "No access token"}

        response = requests.get(self.ME_ENDPOINT, headers=self._get_headers())
        if response.status_code == 200:
            return {"valid": True, "user": response.json()}
        else:
            return {"valid": False, "error": response.text}

    def me(self) -> dict:
        """
        Get authenticated user information.

        Returns:
            dict with 'success', user info or 'error'
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing access token"}

        # Try userinfo endpoint first
        response = requests.get(
            self.USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "id": data.get("sub"),
                "name": data.get("name"),
                "email": data.get("email"),
                "picture": data.get("picture"),
                "url": f"https://www.linkedin.com/in/{data.get('sub', '')}",
            }

        # Fallback to /me endpoint
        response = requests.get(self.ME_ENDPOINT, headers=self._get_headers())
        if response.status_code == 200:
            data = response.json()
            name = f"{data.get('localizedFirstName', '')} {data.get('localizedLastName', '')}".strip()
            return {
                "success": True,
                "id": data.get("id"),
                "name": name,
                "url": f"https://www.linkedin.com/in/{data.get('vanityName', data.get('id', ''))}",
            }

        return {"success": False, "error": f"{response.status_code}: {response.text}"}

    def feed(self, limit: int = 10) -> dict:
        """
        Get user's recent posts/shares.

        Note: LinkedIn API has limited support for reading posts.
        Requires r_organization_social or w_member_social scopes.

        Args:
            limit: Maximum number of posts to return

        Returns:
            dict with 'success', 'posts' list or 'error'
        """
        if not self.validate_credentials():
            return {"success": False, "error": "Missing access token"}

        author_urn = self._get_user_urn()
        if not author_urn:
            return {"success": False, "error": "Could not get user URN"}

        # Try to get shares
        params = {
            "q": "owners",
            "owners": author_urn,
            "count": limit,
        }

        response = requests.get(
            self.SHARES_ENDPOINT,
            headers=self._get_headers(),
            params=params,
        )

        if response.status_code == 200:
            data = response.json()
            posts = []
            for element in data.get("elements", []):
                post_id = element.get("id", "")
                text = element.get("text", {}).get("text", "")
                posts.append(
                    {
                        "id": post_id,
                        "text": text[:200] + "..." if len(text) > 200 else text,
                        "created_at": element.get("created", {}).get("time"),
                        "url": f"https://www.linkedin.com/feed/update/{post_id}/",
                    }
                )
            return {"success": True, "posts": posts, "count": len(posts)}

        # API may not support this with current scopes
        return {
            "success": False,
            "error": f"Feed access requires additional scopes: {response.status_code}",
        }
