"""YouTube API integration for video uploads and community posts."""

import os
from typing import Optional

from .base import BasePoster
from ._branding import get_env

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    HAS_YOUTUBE = True
except ImportError:
    HAS_YOUTUBE = False


# OAuth scopes for YouTube
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


class YouTube(BasePoster):
    """
    YouTube API client for video uploads and management.

    Supports:
    - Video uploads with metadata
    - Update video metadata
    - Delete videos
    - Community posts (if channel eligible)

    Environment Variables:
        YOUTUBE_CLIENT_SECRETS_FILE: Path to OAuth client secrets JSON
        YOUTUBE_TOKEN_FILE: Path to store OAuth tokens (default: ~/.youtube_token.json)
    """

    platform_name = "youtube"

    def __init__(
        self,
        client_secrets_file: Optional[str] = None,
        token_file: Optional[str] = None,
    ):
        """
        Initialize YouTube client.

        Args:
            client_secrets_file: Path to OAuth client secrets JSON from Google Console
            token_file: Path to store/load OAuth tokens
        """
        self.client_secrets_file = client_secrets_file or get_env(
            "YOUTUBE_CLIENT_SECRETS_FILE"
        )
        self.token_file = token_file or (
            get_env("YOUTUBE_TOKEN_FILE") or os.path.expanduser("~/.youtube_token.json")
        )
        self._youtube = None
        self._credentials = None

    def validate_credentials(self) -> bool:
        """Check if credentials are available."""
        if not HAS_YOUTUBE:
            return False

        # Check for existing token
        if os.path.exists(self.token_file):
            return True

        # Check for client secrets to initiate OAuth
        if self.client_secrets_file and os.path.exists(self.client_secrets_file):
            return True

        return False

    def _get_credentials(self) -> Optional["Credentials"]:
        """Get or refresh OAuth credentials."""
        if not HAS_YOUTUBE:
            return None

        creds = None

        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif self.client_secrets_file and os.path.exists(self.client_secrets_file):
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            else:
                return None

            # Save credentials
            with open(self.token_file, "w") as f:
                f.write(creds.to_json())

        return creds

    def _get_client(self):
        """Get authenticated YouTube client."""
        if self._youtube:
            return self._youtube

        creds = self._get_credentials()
        if not creds:
            return None

        self._youtube = build("youtube", "v3", credentials=creds)
        return self._youtube

    def post(
        self,
        text: str,
        video_path: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list] = None,
        category_id: str = "22",  # People & Blogs
        privacy_status: str = "public",
        thumbnail_path: Optional[str] = None,
    ) -> dict:
        """
        Upload a video or create a community post.

        Args:
            text: Description text (or community post text if no video)
            video_path: Path to video file (required for video upload)
            title: Video title (uses first line of text if not provided)
            description: Video description (uses text if not provided)
            tags: List of tags for the video
            category_id: YouTube category ID (default: 22 = People & Blogs)
            privacy_status: 'public', 'private', or 'unlisted'
            thumbnail_path: Path to custom thumbnail image

        Returns:
            dict with 'success', 'id', 'url' or 'error'
        """
        if not HAS_YOUTUBE:
            return {
                "success": False,
                "error": "YouTube libraries not installed. Run: pip install google-api-python-client google-auth-oauthlib",
            }

        if not self.validate_credentials():
            return {"success": False, "error": "Missing YouTube credentials"}

        youtube = self._get_client()
        if not youtube:
            return {"success": False, "error": "Could not create YouTube client"}

        # Video upload
        if video_path:
            return self._upload_video(
                youtube,
                video_path=video_path,
                title=title or text.split("\n")[0][:100],
                description=description or text,
                tags=tags or [],
                category_id=category_id,
                privacy_status=privacy_status,
                thumbnail_path=thumbnail_path,
            )

        # Community post (text only)
        return self._create_community_post(youtube, text)

    def _upload_video(
        self,
        youtube,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        category_id: str,
        privacy_status: str,
        thumbnail_path: Optional[str] = None,
    ) -> dict:
        """Upload a video to YouTube."""
        if not os.path.exists(video_path):
            return {"success": False, "error": f"Video file not found: {video_path}"}

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        try:
            media = MediaFileUpload(
                video_path,
                chunksize=1024 * 1024,  # 1MB chunks
                resumable=True,
            )

            request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()

            video_id = response["id"]

            # Set custom thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path),
                    ).execute()
                except Exception:
                    pass  # Thumbnail upload is optional

            return {
                "success": True,
                "id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": title,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_community_post(self, youtube, text: str) -> dict:
        """
        Create a community post.

        Note: Community posts require channel to be eligible (usually 500+ subscribers).
        This uses the YouTube Data API's activities endpoint.
        """
        try:
            # Community posts via API have limited support
            # This is a placeholder - full implementation requires channel eligibility
            return {
                "success": False,
                "error": "Community posts require channel eligibility (500+ subscribers) and manual posting via YouTube Studio",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete(self, video_id: str) -> dict:
        """
        Delete a video.

        Args:
            video_id: YouTube video ID

        Returns:
            dict with 'success' or 'error'
        """
        if not HAS_YOUTUBE:
            return {"success": False, "error": "YouTube libraries not installed"}

        if not self.validate_credentials():
            return {"success": False, "error": "Missing credentials"}

        youtube = self._get_client()
        if not youtube:
            return {"success": False, "error": "Could not create YouTube client"}

        try:
            youtube.videos().delete(id=video_id).execute()
            return {"success": True, "deleted": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list] = None,
        privacy_status: Optional[str] = None,
    ) -> dict:
        """
        Update video metadata.

        Args:
            video_id: YouTube video ID
            title: New title (optional)
            description: New description (optional)
            tags: New tags (optional)
            privacy_status: New privacy status (optional)

        Returns:
            dict with 'success' or 'error'
        """
        if not HAS_YOUTUBE:
            return {"success": False, "error": "YouTube libraries not installed"}

        youtube = self._get_client()
        if not youtube:
            return {"success": False, "error": "Could not create YouTube client"}

        try:
            # Get current video details
            current = (
                youtube.videos()
                .list(
                    part="snippet,status",
                    id=video_id,
                )
                .execute()
            )

            if not current.get("items"):
                return {"success": False, "error": f"Video not found: {video_id}"}

            video = current["items"][0]
            snippet = video["snippet"]
            status = video["status"]

            # Update fields
            if title:
                snippet["title"] = title
            if description:
                snippet["description"] = description
            if tags:
                snippet["tags"] = tags
            if privacy_status:
                status["privacyStatus"] = privacy_status

            # Update video
            youtube.videos().update(
                part="snippet,status",
                body={
                    "id": video_id,
                    "snippet": snippet,
                    "status": status,
                },
            ).execute()

            return {
                "success": True,
                "id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_channel_info(self) -> dict:
        """
        Get authenticated user's channel information.

        Returns:
            dict with channel info or error
        """
        if not HAS_YOUTUBE:
            return {"success": False, "error": "YouTube libraries not installed"}

        youtube = self._get_client()
        if not youtube:
            return {"success": False, "error": "Could not create YouTube client"}

        try:
            response = (
                youtube.channels()
                .list(
                    part="snippet,statistics",
                    mine=True,
                )
                .execute()
            )

            if not response.get("items"):
                return {"success": False, "error": "No channel found"}

            channel = response["items"][0]
            return {
                "success": True,
                "id": channel["id"],
                "title": channel["snippet"]["title"],
                "description": channel["snippet"].get("description", ""),
                "subscribers": channel["statistics"].get("subscriberCount", "hidden"),
                "videos": channel["statistics"].get("videoCount", 0),
                "views": channel["statistics"].get("viewCount", 0),
                "url": f"https://www.youtube.com/channel/{channel['id']}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_videos(self, max_results: int = 10) -> dict:
        """
        List user's uploaded videos.

        Args:
            max_results: Maximum number of videos to return

        Returns:
            dict with videos list or error
        """
        if not HAS_YOUTUBE:
            return {"success": False, "error": "YouTube libraries not installed"}

        youtube = self._get_client()
        if not youtube:
            return {"success": False, "error": "Could not create YouTube client"}

        try:
            # Get uploads playlist ID
            channels = (
                youtube.channels()
                .list(
                    part="contentDetails",
                    mine=True,
                )
                .execute()
            )

            if not channels.get("items"):
                return {"success": False, "error": "No channel found"}

            uploads_id = channels["items"][0]["contentDetails"]["relatedPlaylists"][
                "uploads"
            ]

            # Get videos from uploads playlist
            videos_response = (
                youtube.playlistItems()
                .list(
                    part="snippet",
                    playlistId=uploads_id,
                    maxResults=max_results,
                )
                .execute()
            )

            videos = []
            for item in videos_response.get("items", []):
                snippet = item["snippet"]
                video_id = snippet["resourceId"]["videoId"]
                videos.append(
                    {
                        "id": video_id,
                        "title": snippet["title"],
                        "description": snippet.get("description", "")[:100],
                        "published_at": snippet["publishedAt"],
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                    }
                )

            return {
                "success": True,
                "videos": videos,
                "count": len(videos),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def me(self) -> dict:
        """
        Get authenticated user's channel information.

        Returns:
            dict with 'success', channel info or 'error'
        """
        return self.get_channel_info()

    def feed(self, limit: int = 10) -> dict:
        """
        Get user's recent videos.

        Args:
            limit: Maximum number of videos to return

        Returns:
            dict with 'success', 'posts' (videos) list or 'error'
        """
        result = self.list_videos(max_results=limit)
        if result.get("success"):
            # Rename 'videos' to 'posts' for consistency
            return {
                "success": True,
                "posts": result.get("videos", []),
                "count": result.get("count", 0),
            }
        return result
