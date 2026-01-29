"""Tests for socialia scheduler module."""

import json
import pytest
from datetime import datetime, timedelta

from socialia.scheduler import (
    parse_schedule_time,
    schedule_post,
    list_scheduled,
    cancel_scheduled,
    run_due_jobs,
)


class TestParseScheduleTime:
    """Test schedule time parsing."""

    def test_parse_relative_hours(self):
        """Test parsing '+1h' format."""
        result = parse_schedule_time("+1h")
        expected = datetime.now() + timedelta(hours=1)
        # Allow 1 second difference for execution time
        assert abs((result - expected).total_seconds()) < 2

    def test_parse_relative_minutes(self):
        """Test parsing '+30m' format."""
        result = parse_schedule_time("+30m")
        expected = datetime.now() + timedelta(minutes=30)
        assert abs((result - expected).total_seconds()) < 2

    def test_parse_time_only(self):
        """Test parsing '10:00' format."""
        result = parse_schedule_time("10:00")
        now = datetime.now()
        expected = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if expected <= now:
            expected += timedelta(days=1)
        assert result.hour == 10
        assert result.minute == 0

    def test_parse_full_datetime(self):
        """Test parsing '2026-01-25 14:30' format."""
        result = parse_schedule_time("2026-01-25 14:30")
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 25
        assert result.hour == 14
        assert result.minute == 30

    def test_parse_invalid_format(self):
        """Test parsing invalid format raises error."""
        with pytest.raises(ValueError):
            parse_schedule_time("invalid-time-format")


class TestSchedulePost:
    """Test schedule_post function."""

    def test_schedule_post_success(self, tmp_path, monkeypatch):
        """Test scheduling a post successfully."""
        schedule_dir = tmp_path / ".socialia"
        schedule_dir.mkdir(parents=True, exist_ok=True)
        schedule_file = schedule_dir / "scheduled.json"

        import socialia.scheduler

        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_DIR", schedule_dir)
        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_FILE", schedule_file)
        result = schedule_post("twitter", "Test post", "+1h")

        assert result["success"] is True
        assert "job_id" in result
        assert "scheduled_for" in result

    def test_schedule_post_invalid_time(self):
        """Test scheduling with invalid time."""
        result = schedule_post("twitter", "Test", "invalid")
        assert result["success"] is False
        assert "error" in result


class TestListScheduled:
    """Test list_scheduled function."""

    def test_list_empty(self, tmp_path, monkeypatch):
        """Test listing when no jobs exist."""
        schedule_dir = tmp_path / ".socialia"
        schedule_dir.mkdir(parents=True, exist_ok=True)
        schedule_file = schedule_dir / "scheduled.json"
        schedule_file.write_text("[]")

        import socialia.scheduler

        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_DIR", schedule_dir)
        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_FILE", schedule_file)
        result = list_scheduled()

        assert result == []

    def test_list_with_jobs(self, tmp_path, monkeypatch):
        """Test listing existing jobs."""
        schedule_dir = tmp_path / ".socialia"
        schedule_dir.mkdir(parents=True, exist_ok=True)
        schedule_file = schedule_dir / "scheduled.json"
        jobs = [
            {
                "id": "test-123",
                "platform": "twitter",
                "text": "Test",
                "scheduled_for": "2026-01-25 10:00:00",
                "created_at": "2026-01-22 09:00:00",
                "status": "pending",
                "kwargs": {},
            }
        ]
        schedule_file.write_text(json.dumps(jobs))

        import socialia.scheduler

        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_DIR", schedule_dir)
        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_FILE", schedule_file)
        result = list_scheduled()

        assert len(result) == 1
        assert result[0]["id"] == "test-123"


class TestCancelScheduled:
    """Test cancel_scheduled function."""

    def test_cancel_nonexistent(self, tmp_path, monkeypatch):
        """Test cancelling non-existent job."""
        schedule_dir = tmp_path / ".socialia"
        schedule_dir.mkdir(parents=True, exist_ok=True)
        schedule_file = schedule_dir / "scheduled.json"
        schedule_file.write_text("[]")

        import socialia.scheduler

        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_DIR", schedule_dir)
        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_FILE", schedule_file)
        result = cancel_scheduled("nonexistent-id")

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_cancel_existing(self, tmp_path, monkeypatch):
        """Test cancelling existing job."""
        schedule_dir = tmp_path / ".socialia"
        schedule_dir.mkdir(parents=True, exist_ok=True)
        schedule_file = schedule_dir / "scheduled.json"
        jobs = [
            {
                "id": "test-123",
                "platform": "twitter",
                "text": "Test",
                "scheduled_for": "2026-01-25 10:00:00",
                "created_at": "2026-01-22 09:00:00",
                "status": "pending",
                "kwargs": {},
            }
        ]
        schedule_file.write_text(json.dumps(jobs))

        import socialia.scheduler

        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_DIR", schedule_dir)
        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_FILE", schedule_file)
        result = cancel_scheduled("test-123")

        assert result["success"] is True

        # Verify job was cancelled (status changed)
        remaining = list_scheduled()
        assert len(remaining) == 0


class TestRunDueJobs:
    """Test run_due_jobs function."""

    def test_run_no_jobs(self, tmp_path, monkeypatch):
        """Test running when no jobs exist."""
        schedule_dir = tmp_path / ".socialia"
        schedule_dir.mkdir(parents=True, exist_ok=True)
        schedule_file = schedule_dir / "scheduled.json"
        schedule_file.write_text("[]")

        import socialia.scheduler

        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_DIR", schedule_dir)
        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_FILE", schedule_file)
        results = run_due_jobs()

        assert results == []

    def test_run_future_jobs_not_executed(self, tmp_path, monkeypatch):
        """Test that future jobs are not executed."""
        schedule_dir = tmp_path / ".socialia"
        schedule_dir.mkdir(parents=True, exist_ok=True)
        schedule_file = schedule_dir / "scheduled.json"
        future_time = (datetime.now() + timedelta(hours=24)).isoformat()
        jobs = [
            {
                "id": "future-job",
                "platform": "twitter",
                "text": "Future post",
                "scheduled_for": future_time,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "kwargs": {},
            }
        ]
        schedule_file.write_text(json.dumps(jobs))

        import socialia.scheduler

        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_DIR", schedule_dir)
        monkeypatch.setattr(socialia.scheduler, "SCHEDULE_FILE", schedule_file)
        results = run_due_jobs()

        assert results == []

        # Verify job still exists
        remaining = list_scheduled()
        assert len(remaining) == 1
