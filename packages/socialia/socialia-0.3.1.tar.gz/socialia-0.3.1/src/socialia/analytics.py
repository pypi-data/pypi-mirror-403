"""Google Analytics integration for tracking and metrics."""

import os
import requests
from typing import Optional
from datetime import datetime

from ._branding import get_env


class GoogleAnalytics:
    """
    Google Analytics 4 integration.

    Supports:
    - Measurement Protocol (sending events)
    - Data API (retrieving metrics) - requires service account

    Environment Variables (use branded prefix, e.g., SOCIALIA_):
        GOOGLE_ANALYTICS_MEASUREMENT_ID: GA4 Measurement ID (G-XXXXXXXXXX)
        GOOGLE_ANALYTICS_API_SECRET: Measurement Protocol API secret
        GOOGLE_ANALYTICS_PROPERTY_ID: Property ID (numeric, for Data API)
        GOOGLE_APPLICATION_CREDENTIALS: Path to service account JSON (for Data API)
    """

    def __init__(
        self,
        measurement_id: Optional[str] = None,
        api_secret: Optional[str] = None,
        property_id: Optional[str] = None,
    ):
        """
        Initialize Google Analytics client.

        Args:
            measurement_id: GA4 Measurement ID (G-XXXXXXXXXX)
            api_secret: Measurement Protocol API secret
            property_id: GA4 Property ID (numeric, for Data API)
        """
        # Google Analytics credentials (use branding-aware get_env)
        self.measurement_id = measurement_id or (
            get_env("GOOGLE_ANALYTICS_MEASUREMENT_ID") or get_env("GA_MEASUREMENT_ID")
        )
        self.api_secret = api_secret or (
            get_env("GOOGLE_ANALYTICS_API_SECRET") or get_env("GA_API_SECRET")
        )
        self.property_id = property_id or (
            get_env("GOOGLE_ANALYTICS_PROPERTY_ID") or get_env("GA_PROPERTY_ID")
        )

        # Google Application Credentials (for Data API service account)
        credentials_path = get_env("GOOGLE_APPLICATION_CREDENTIALS") or get_env(
            "GA_CREDENTIALS"
        )
        if credentials_path and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expandvars(
                credentials_path
            )

        # Measurement Protocol endpoint
        self.mp_endpoint = "https://www.google-analytics.com/mp/collect"

    def validate_credentials(self) -> dict:
        """Check which features are available based on credentials."""
        return {
            "measurement_protocol": bool(self.measurement_id and self.api_secret),
            "data_api": bool(self.property_id),
        }

    def track_event(
        self,
        name: str,
        params: Optional[dict] = None,
        client_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict:
        """
        Send event to Google Analytics via Measurement Protocol.

        Args:
            name: Event name (e.g., 'social_post', 'social_share')
            params: Event parameters dict
            client_id: Client ID (generated if not provided)
            user_id: Optional user ID for cross-device tracking

        Returns:
            dict with 'success' and details

        Example:
            ga.track_event('social_post', {
                'platform': 'twitter',
                'post_id': '123456',
                'content_length': 280,
            })
        """
        if not self.measurement_id or not self.api_secret:
            return {
                "success": False,
                "error": "Missing GA_MEASUREMENT_ID or GA_API_SECRET",
            }

        # Generate client_id if not provided
        if not client_id:
            import uuid

            client_id = str(uuid.uuid4())

        # Build payload
        payload = {
            "client_id": client_id,
            "events": [
                {
                    "name": name,
                    "params": params or {},
                }
            ],
        }

        if user_id:
            payload["user_id"] = user_id

        # Add timestamp
        payload["events"][0]["params"]["engagement_time_msec"] = "100"

        try:
            url = f"{self.mp_endpoint}?measurement_id={self.measurement_id}&api_secret={self.api_secret}"
            response = requests.post(url, json=payload, timeout=10)

            # Measurement Protocol returns 204 on success (no content)
            if response.status_code in (200, 204):
                return {
                    "success": True,
                    "client_id": client_id,
                    "event": name,
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def track_social_post(
        self,
        platform: str,
        post_id: str,
        content_type: str = "text",
        success: bool = True,
    ) -> dict:
        """
        Track a social media post event.

        Args:
            platform: Platform name (twitter, linkedin, reddit)
            post_id: Post ID from the platform
            content_type: Type of content (text, link, image, thread)
            success: Whether the post was successful

        Returns:
            dict with tracking result
        """
        return self.track_event(
            "social_post",
            {
                "platform": platform,
                "post_id": post_id,
                "content_type": content_type,
                "success": str(success).lower(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def track_social_delete(self, platform: str, post_id: str) -> dict:
        """Track a social media delete event."""
        return self.track_event(
            "social_delete",
            {
                "platform": platform,
                "post_id": post_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def get_realtime_users(self) -> dict:
        """
        Get realtime active users (requires Data API setup).

        Returns:
            dict with 'success' and 'active_users' count
        """
        if not self.property_id:
            return {
                "success": False,
                "error": "Missing GA_PROPERTY_ID for Data API",
            }

        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.analytics.data_v1beta.types import (
                RunRealtimeReportRequest,
                Metric,
            )

            client = BetaAnalyticsDataClient()
            request = RunRealtimeReportRequest(
                property=f"properties/{self.property_id}",
                metrics=[Metric(name="activeUsers")],
            )
            response = client.run_realtime_report(request)

            active_users = 0
            if response.rows:
                active_users = int(response.rows[0].metric_values[0].value)

            return {
                "success": True,
                "active_users": active_users,
            }

        except ImportError:
            return {
                "success": False,
                "error": "google-analytics-data not installed. Run: pip install google-analytics-data",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_page_views(
        self,
        start_date: str = "7daysAgo",
        end_date: str = "today",
        page_path: Optional[str] = None,
    ) -> dict:
        """
        Get page view metrics (requires Data API setup).

        Args:
            start_date: Start date (YYYY-MM-DD or relative like '7daysAgo')
            end_date: End date (YYYY-MM-DD or 'today')
            page_path: Optional page path filter

        Returns:
            dict with 'success' and metrics
        """
        if not self.property_id:
            return {
                "success": False,
                "error": "Missing GA_PROPERTY_ID for Data API",
            }

        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.analytics.data_v1beta.types import (
                RunReportRequest,
                DateRange,
                Metric,
                Dimension,
                FilterExpression,
                Filter,
            )

            client = BetaAnalyticsDataClient()

            request_params = {
                "property": f"properties/{self.property_id}",
                "date_ranges": [DateRange(start_date=start_date, end_date=end_date)],
                "metrics": [
                    Metric(name="screenPageViews"),
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                ],
                "dimensions": [Dimension(name="pagePath")],
            }

            if page_path:
                request_params["dimension_filter"] = FilterExpression(
                    filter=Filter(
                        field_name="pagePath",
                        string_filter=Filter.StringFilter(
                            match_type=Filter.StringFilter.MatchType.CONTAINS,
                            value=page_path,
                        ),
                    )
                )

            response = client.run_report(RunReportRequest(**request_params))

            pages = []
            for row in response.rows:
                pages.append(
                    {
                        "path": row.dimension_values[0].value,
                        "page_views": int(row.metric_values[0].value),
                        "sessions": int(row.metric_values[1].value),
                        "users": int(row.metric_values[2].value),
                    }
                )

            return {
                "success": True,
                "date_range": f"{start_date} to {end_date}",
                "pages": pages,
            }

        except ImportError:
            return {
                "success": False,
                "error": "google-analytics-data not installed. Run: pip install google-analytics-data",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_traffic_sources(
        self,
        start_date: str = "7daysAgo",
        end_date: str = "today",
    ) -> dict:
        """
        Get traffic source breakdown (requires Data API setup).

        Returns:
            dict with traffic sources and their metrics
        """
        if not self.property_id:
            return {
                "success": False,
                "error": "Missing GA_PROPERTY_ID for Data API",
            }

        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.analytics.data_v1beta.types import (
                RunReportRequest,
                DateRange,
                Metric,
                Dimension,
            )

            client = BetaAnalyticsDataClient()
            response = client.run_report(
                RunReportRequest(
                    property=f"properties/{self.property_id}",
                    date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                    metrics=[
                        Metric(name="sessions"),
                        Metric(name="totalUsers"),
                    ],
                    dimensions=[
                        Dimension(name="sessionSource"),
                        Dimension(name="sessionMedium"),
                    ],
                )
            )

            sources = []
            for row in response.rows:
                sources.append(
                    {
                        "source": row.dimension_values[0].value,
                        "medium": row.dimension_values[1].value,
                        "sessions": int(row.metric_values[0].value),
                        "users": int(row.metric_values[1].value),
                    }
                )

            # Sort by sessions descending
            sources.sort(key=lambda x: x["sessions"], reverse=True)

            return {
                "success": True,
                "date_range": f"{start_date} to {end_date}",
                "sources": sources,
            }

        except ImportError:
            return {
                "success": False,
                "error": "google-analytics-data not installed. Run: pip install google-analytics-data",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
