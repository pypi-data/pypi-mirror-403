#!/usr/bin/env python3
"""Tests for org mode draft management."""

from datetime import datetime, timedelta

import pytest

from socialia.org import OrgParser, OrgDraft, OrgDraftManager


@pytest.fixture
def sample_org_content():
    """Sample org file content for testing."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    return f"""#+TITLE: Test Drafts
#+AUTHOR: test

* Drafts [0/3]

** TODO [#A] Future Post
   SCHEDULED: <{tomorrow} 10:00>
   :PROPERTIES:
   :PLATFORM: twitter
   :ID: draft-001
   :END:

This is a future post.

** TODO [#B] Due Post
   SCHEDULED: <{yesterday} 10:00>
   :PROPERTIES:
   :PLATFORM: twitter
   :ID: draft-002
   :END:

This post is due.

** DONE [#C] Completed Post
   SCHEDULED: <{yesterday} 09:00>
   :PROPERTIES:
   :PLATFORM: linkedin
   :ID: draft-003
   :END:

This was already posted.

* Archive
# Completed posts go here
"""


@pytest.fixture
def org_file(sample_org_content, tmp_path):
    """Create a temporary org file."""
    filepath = tmp_path / "test_drafts.org"
    filepath.write_text(sample_org_content)
    return filepath


class TestOrgParser:
    """Tests for OrgParser."""

    def test_parse_drafts(self, org_file):
        """Test parsing drafts from org file."""
        parser = OrgParser(org_file)
        drafts = parser.parse()

        assert len(drafts) == 3
        assert drafts[0].headline == "Future Post"
        assert drafts[1].headline == "Due Post"
        assert drafts[2].headline == "Completed Post"

    def test_parse_status(self, org_file):
        """Test parsing TODO/DONE status."""
        parser = OrgParser(org_file)
        drafts = parser.parse()

        assert drafts[0].status == "TODO"
        assert drafts[1].status == "TODO"
        assert drafts[2].status == "DONE"

    def test_parse_priority(self, org_file):
        """Test parsing priority levels."""
        parser = OrgParser(org_file)
        drafts = parser.parse()

        assert drafts[0].priority == "A"
        assert drafts[1].priority == "B"
        assert drafts[2].priority == "C"

    def test_parse_platform(self, org_file):
        """Test parsing platform from properties."""
        parser = OrgParser(org_file)
        drafts = parser.parse()

        assert drafts[0].platform == "twitter"
        assert drafts[1].platform == "twitter"
        assert drafts[2].platform == "linkedin"

    def test_parse_scheduled(self, org_file):
        """Test parsing scheduled timestamp."""
        parser = OrgParser(org_file)
        drafts = parser.parse()

        assert drafts[0].scheduled is not None
        assert drafts[0].scheduled.hour == 10
        assert drafts[0].scheduled.minute == 0

    def test_parse_content(self, org_file):
        """Test parsing draft content."""
        parser = OrgParser(org_file)
        drafts = parser.parse()

        assert "future post" in drafts[0].content.lower()
        assert "due" in drafts[1].content.lower()

    def test_skip_level_one_headings(self, tmp_path):
        """Test that level 1 headings are skipped."""
        content = """* Level One
This should be skipped.

** TODO Level Two
   :PROPERTIES:
   :PLATFORM: twitter
   :END:

This should be parsed.
"""
        filepath = tmp_path / "test.org"
        filepath.write_text(content)

        parser = OrgParser(filepath)
        drafts = parser.parse()

        assert len(drafts) == 1
        assert drafts[0].headline == "Level Two"


class TestOrgDraft:
    """Tests for OrgDraft dataclass."""

    def test_is_pending(self):
        """Test is_pending property."""
        draft = OrgDraft(
            headline="Test",
            status="TODO",
            priority="A",
            scheduled=None,
            platform="twitter",
            draft_id="001",
            content="Test content",
            line_number=0,
        )
        assert draft.is_pending is True

        draft.status = "DONE"
        assert draft.is_pending is False

    def test_is_due(self):
        """Test is_due property."""
        past = datetime.now() - timedelta(hours=1)
        future = datetime.now() + timedelta(hours=1)

        draft_past = OrgDraft(
            headline="Past",
            status="TODO",
            priority="A",
            scheduled=past,
            platform="twitter",
            draft_id="001",
            content="Test",
            line_number=0,
        )
        assert draft_past.is_due is True

        draft_future = OrgDraft(
            headline="Future",
            status="TODO",
            priority="A",
            scheduled=future,
            platform="twitter",
            draft_id="002",
            content="Test",
            line_number=0,
        )
        assert draft_future.is_due is False

        draft_done = OrgDraft(
            headline="Done",
            status="DONE",
            priority="A",
            scheduled=past,
            platform="twitter",
            draft_id="003",
            content="Test",
            line_number=0,
        )
        assert draft_done.is_due is False


class TestOrgDraftManager:
    """Tests for OrgDraftManager."""

    def test_list_drafts(self, org_file):
        """Test listing all drafts."""
        manager = OrgDraftManager(org_file)
        drafts = manager.list_drafts()

        assert len(drafts) == 3

    def test_list_drafts_filtered(self, org_file):
        """Test filtering drafts by status."""
        manager = OrgDraftManager(org_file)

        pending = manager.list_drafts(status="TODO")
        assert len(pending) == 2

        done = manager.list_drafts(status="DONE")
        assert len(done) == 1

    def test_get_pending(self, org_file):
        """Test getting pending drafts."""
        manager = OrgDraftManager(org_file)
        pending = manager.get_pending()

        assert len(pending) == 2
        assert all(d.status == "TODO" for d in pending)

    def test_get_due(self, org_file):
        """Test getting due drafts."""
        manager = OrgDraftManager(org_file)
        due = manager.get_due()

        # One draft is scheduled for yesterday
        assert len(due) == 1
        assert due[0].headline == "Due Post"

    def test_get_scheduled(self, org_file):
        """Test getting future scheduled drafts."""
        manager = OrgDraftManager(org_file)
        scheduled = manager.get_scheduled()

        # One draft is scheduled for tomorrow
        assert len(scheduled) == 1
        assert scheduled[0].headline == "Future Post"

    def test_status_report(self, org_file):
        """Test status report generation."""
        manager = OrgDraftManager(org_file)
        report = manager.status_report()

        assert report["total"] == 3
        assert report["pending"] == 2
        assert report["done"] == 1
        assert report["due_now"] == 1
        assert report["scheduled"] == 1

    def test_post_draft_dry_run(self, org_file):
        """Test posting a draft in dry-run mode."""
        manager = OrgDraftManager(org_file)
        draft = manager.get_pending()[0]

        result = manager.post_draft(draft, dry_run=True)

        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["platform"] == "twitter"


class TestOrgCLI:
    """Tests for org CLI commands."""

    def test_org_status_command(self, org_file):
        """Test org status CLI command."""
        from socialia.cli import main

        result = main(["org", "status", str(org_file)])
        assert result == 0

    def test_org_list_command(self, org_file):
        """Test org list CLI command."""
        from socialia.cli import main

        result = main(["org", "list", str(org_file)])
        assert result == 0

    def test_org_schedule_dry_run(self, org_file):
        """Test org schedule CLI command with dry-run."""
        from socialia.cli import main

        result = main(["org", "schedule", str(org_file), "--dry-run"])
        assert result == 0

    def test_org_post_dry_run(self, org_file):
        """Test org post CLI command with dry-run."""
        from socialia.cli import main

        result = main(["org", "post", str(org_file), "--dry-run"])
        assert result == 0

    def test_org_init_command(self, tmp_path):
        """Test org init CLI command."""
        from socialia.cli import main

        filepath = tmp_path / "new_drafts.org"
        result = main(["org", "init", str(filepath)])

        assert result == 0
        assert filepath.exists()
        content = filepath.read_text()
        assert "#+TITLE:" in content
        assert "TODO" in content
