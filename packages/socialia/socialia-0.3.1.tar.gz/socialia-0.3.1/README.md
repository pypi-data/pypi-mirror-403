# Socialia

**Unified social media management — posting, analytics, and insights**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

Part of [**SciTeX**](https://scitex.ai) for scientific research automation.

## Installation

```bash
pip install socialia

# Or with optional dependencies
pip install socialia[reddit]      # Reddit support
pip install socialia[youtube]     # YouTube support
pip install socialia[analytics]   # Google Analytics Data API
pip install socialia[all]         # Everything
```

## Quick Start

```python
from socialia import Twitter, LinkedIn, Reddit, YouTube, GoogleAnalytics

# Post to Twitter
twitter = Twitter()
twitter.post("Hello World!")

# Post to LinkedIn
linkedin = LinkedIn()
linkedin.post("Professional update!")

# Track analytics
ga = GoogleAnalytics()
ga.track_event("page_view", {"page": "/docs"})
```

<details>
<summary><b>CLI Usage</b></summary>

```bash
# Check all platform connections at once
socialia check

# Get recent posts from all platforms
socialia feed
socialia feed --detail        # Full text with URLs
socialia feed --mentions      # Get mentions/notifications
socialia feed --replies       # Get replies to your posts (Twitter)

# Get user profile info
socialia me twitter

# Post to Twitter
socialia post twitter "Hello World!"

# Schedule a post for later
socialia post twitter "Hello!" --schedule "10:00"
socialia post twitter "Hello!" --schedule "2026-01-23 10:00"
socialia post twitter "Hello!" --schedule "+1h"

# Manage scheduled posts
socialia schedule list        # View pending posts
socialia schedule cancel ID   # Cancel a scheduled post
socialia schedule daemon      # Run scheduler in background

# Post to LinkedIn
socialia post linkedin "Professional update!"

# Post to Reddit
socialia post reddit "Post body" --subreddit python --title "Post Title"

# Post to YouTube (video upload)
socialia post youtube "Description" --video video.mp4 --title "My Video"

# Analytics tracking
socialia analytics track page_view --param page /docs

# Get realtime users
socialia analytics realtime

# Post from file
socialia post twitter --file tweet.txt

# Delete a post
socialia delete twitter 1234567890

# Post a thread (separate posts with ---)
socialia thread twitter --file thread.txt

# Dry run (preview without posting)
socialia post twitter "Test" --dry-run

# Show all commands
socialia --help-recursive

# JSON output
socialia feed --json

# Shell completion
socialia completion bash      # Print bash completion script
socialia completion zsh       # Print zsh completion script
socialia completion install   # Auto-install to shell config
socialia completion status    # Check installation status

# Org mode draft management (Emacs integration)
socialia org init drafts.org              # Create template
socialia org status drafts.org            # Show draft status
socialia org list drafts.org              # List all drafts
socialia org schedule drafts.org          # Schedule future posts
socialia org post drafts.org              # Post due drafts
socialia org post drafts.org --dry-run    # Preview without posting
```

</details>

<details>
<summary><b>Org Mode Integration</b></summary>

Manage social media drafts in Emacs org mode files:

```org
* Twitter Drafts [0/2]

** TODO [#A] My First Post
   SCHEDULED: <2026-01-24 Fri 10:00>
   :PROPERTIES:
   :PLATFORM: twitter
   :END:

Post content goes here.
Multiple lines supported.

** TODO [#B] Second Post
   SCHEDULED: <2026-01-25 Sat 10:00>
   :PROPERTIES:
   :PLATFORM: linkedin
   :END:

Another draft for LinkedIn.
```

**Features:**
- Parse org files with TODO/DONE status
- Support SCHEDULED timestamps
- Platform selection via :PLATFORM: property
- Automatic status update after posting
- Dry-run mode for previewing

```bash
# Create a new drafts file
socialia org init ~/drafts/january.org --platform twitter

# Check status of all drafts
socialia org status ~/drafts/january.org

# Schedule all future posts
socialia org schedule ~/drafts/january.org

# Post all due drafts (scheduled time passed)
socialia org post ~/drafts/january.org

# Run scheduler daemon to auto-post
socialia schedule daemon
```

```python
from socialia import OrgDraftManager

manager = OrgDraftManager("drafts.org")
manager.status_report()      # Get overview
manager.get_pending()        # List TODO drafts
manager.get_due()            # Get drafts ready to post
manager.schedule_all()       # Schedule future posts
manager.post_draft(draft, dry_run=True)  # Post with preview
```

</details>

<details>
<summary><b>Python API</b></summary>

```python
from socialia import Twitter, LinkedIn, Reddit, YouTube, GoogleAnalytics

# Check connection and get user info
twitter = Twitter()
twitter.check()      # Verify connection
twitter.me()         # Get user profile
twitter.feed()       # Get recent tweets
twitter.mentions()   # Get mentions
twitter.replies()    # Get replies to your posts

# Post content
twitter.post("Hello World!")
twitter.post_thread(["First", "Second", "Third"])
twitter.delete("1234567890")

# LinkedIn
linkedin = LinkedIn()
linkedin.post("Professional update!")
linkedin.me()        # Get user info

# Reddit (requires: pip install socialia[reddit])
reddit = Reddit()
reddit.post("Post body", subreddit="test", title="Title")
reddit.feed()        # Get recent posts
reddit.mentions()    # Get inbox mentions
reddit.update("post_id", "Updated text")  # Edit post

# YouTube (requires: pip install socialia[youtube])
youtube = YouTube()
youtube.post("Description", video_path="video.mp4", title="My Video")
youtube.feed()       # Get recent videos
youtube.update("video_id", title="New Title")

# Google Analytics (requires: pip install socialia[analytics])
ga = GoogleAnalytics()
ga.track_event("social_post", {"platform": "twitter", "post_id": "123"})
ga.get_page_views(start_date="7daysAgo", end_date="today")
```

</details>

<details>
<summary><b>MCP Server</b></summary>

```bash
# Check server health and credentials
socialia mcp doctor

# List available MCP tools
socialia mcp list-tools

# Show Claude Desktop configuration
socialia mcp installation

# Start the MCP server
socialia mcp start
```

Add to Claude Code settings:

```json
{
  "mcpServers": {
    "socialia": {
      "command": "socialia",
      "args": ["mcp", "start"],
      "env": {
        "SOCIALIA_X_CONSUMER_KEY": "...",
        "SOCIALIA_X_CONSUMER_KEY_SECRET": "...",
        "SOCIALIA_X_ACCESSTOKEN": "...",
        "SOCIALIA_X_ACCESSTOKEN_SECRET": "..."
      }
    }
  }
}
```

</details>

<details>
<summary><b>Environment Variables</b></summary>

```bash
# Twitter/X
export SOCIALIA_X_CONSUMER_KEY="your_consumer_key"
export SOCIALIA_X_CONSUMER_KEY_SECRET="your_consumer_secret"
export SOCIALIA_X_ACCESSTOKEN="your_access_token"
export SOCIALIA_X_ACCESSTOKEN_SECRET="your_access_token_secret"

# LinkedIn
export SOCIALIA_LINKEDIN_ACCESS_TOKEN="your_access_token"

# Reddit
export SOCIALIA_REDDIT_CLIENT_ID="your_client_id"
export SOCIALIA_REDDIT_CLIENT_SECRET="your_client_secret"
export SOCIALIA_REDDIT_USERNAME="your_username"
export SOCIALIA_REDDIT_PASSWORD="your_password"

# YouTube
export SOCIALIA_YOUTUBE_CLIENT_SECRETS_FILE="path/to/client_secrets.json"

# Google Analytics
export SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID="G-XXXXXXXXXX"
export SOCIALIA_GOOGLE_ANALYTICS_API_SECRET="your_api_secret"
export SOCIALIA_GOOGLE_ANALYTICS_PROPERTY_ID="123456789"  # Optional, for Data API
```

**Detailed setup guide:** `socialia setup` or see [docs/SETUP.md](docs/SETUP.md)

</details>

<details>
<summary><b>Supported Platforms</b></summary>

| Platform | Status | API | Install |
|----------|--------|-----|---------|
| Twitter/X | Ready | v2 OAuth 1.0a | `pip install socialia` |
| LinkedIn | Ready | v2 OAuth 2.0 | `pip install socialia` |
| Reddit | Ready | PRAW | `pip install socialia[reddit]` |
| YouTube | Ready | Data API v3 | `pip install socialia[youtube]` |
| Google Analytics | Ready | GA4 + Data API | `pip install socialia[analytics]` |

</details>

<details>
<summary><b>Project Structure</b></summary>

```
socialia/
├── src/socialia/         # Python package
│   ├── cli/              # CLI with argparse
│   ├── twitter.py        # Twitter/X API
│   ├── linkedin.py       # LinkedIn API
│   ├── reddit.py         # Reddit API (PRAW)
│   ├── youtube.py        # YouTube API
│   ├── analytics.py      # Google Analytics
│   ├── scheduler.py      # Post scheduling system
│   ├── org.py            # Org mode draft management
│   ├── mcp_server.py     # MCP server (delegates to CLI)
│   └── base.py           # Base class
├── docs/
│   ├── platforms/        # Platform API documentation
│   └── SETUP.md          # Step-by-step setup guide
├── examples/             # Usage examples
├── Makefile              # Command dispatcher
├── pyproject.toml
└── .env                  # Credentials (gitignored)
```

</details>

<details>
<summary><b>SciTeX Integration</b></summary>

Socialia is part of the SciTeX ecosystem:

```bash
# Install via scitex
pip install scitex[social]

# Use in research workflows
import scitex as stx
from socialia import Twitter

@stx.session
def share_results(twitter=stx.INJECTED):
    # Auto-configured from scitex settings
    twitter.post("New research results!")
```

</details>

---

<p align="center">
  <a href="https://scitex.ai" target="_blank"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
  <br>
  AGPL-3.0
</p>
