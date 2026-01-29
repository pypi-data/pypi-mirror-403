"""Base class for social media clients."""

from abc import ABC, abstractmethod


class BasePoster(ABC):
    """Abstract base class for social media clients with CRUD operations."""

    # Platform identifier
    platform_name: str = "unknown"

    @abstractmethod
    def post(self, text: str, **kwargs) -> dict:
        """Create: Post content to the platform."""
        pass

    @abstractmethod
    def delete(self, post_id: str) -> dict:
        """Delete: Remove a post by ID."""
        pass

    def feed(self, limit: int = 10, **kwargs) -> dict:
        """Read: Get recent posts/content from the platform."""
        return {"success": False, "error": "Feed not implemented for this platform"}

    def mentions(self, limit: int = 10, **kwargs) -> dict:
        """Read: Get mentions/notifications."""
        return {"success": False, "error": "Mentions not implemented for this platform"}

    def update(self, post_id: str, **kwargs) -> dict:
        """Update: Edit an existing post."""
        return {"success": False, "error": "Update not implemented for this platform"}

    def me(self) -> dict:
        """Get authenticated user info."""
        return {
            "success": False,
            "error": "User info not implemented for this platform",
        }

    def validate_credentials(self) -> bool:
        """Check if credentials are configured."""
        return True

    def check(self) -> dict:
        """Quick status check - validates connection and returns basic info."""
        if not self.validate_credentials():
            return {
                "success": False,
                "platform": self.platform_name,
                "status": "not_configured",
                "error": "Missing credentials",
            }

        user_info = self.me()
        if user_info.get("success"):
            return {
                "success": True,
                "platform": self.platform_name,
                "status": "connected",
                "user": user_info,
            }
        return {
            "success": False,
            "platform": self.platform_name,
            "status": "error",
            "error": user_info.get("error", "Unknown error"),
        }
