"""Tests for socialia feed CLI commands."""

from unittest.mock import patch

from socialia.cli import create_parser, main


class TestFeedCommandParsing:
    """Test feed command argument parsing."""

    def test_feed_default(self):
        """Test feed command with defaults."""
        parser = create_parser()
        args = parser.parse_args(["feed"])
        assert args.command == "feed"
        assert args.platform is None
        assert args.limit == 5
        assert args.mentions is False
        assert args.replies is False

    def test_feed_with_platform(self):
        """Test feed command with specific platform."""
        parser = create_parser()
        args = parser.parse_args(["feed", "twitter"])
        assert args.platform == "twitter"

    def test_feed_with_limit(self):
        """Test feed command with limit."""
        parser = create_parser()
        args = parser.parse_args(["feed", "--limit", "10"])
        assert args.limit == 10

    def test_feed_mentions_flag(self):
        """Test feed command with --mentions flag."""
        parser = create_parser()
        args = parser.parse_args(["feed", "--mentions"])
        assert args.mentions is True

    def test_feed_replies_flag(self):
        """Test feed command with --replies flag."""
        parser = create_parser()
        args = parser.parse_args(["feed", "--replies"])
        assert args.replies is True

    def test_feed_detail_flag(self):
        """Test feed command with --detail flag."""
        parser = create_parser()
        args = parser.parse_args(["feed", "--detail"])
        assert args.detail is True


class TestCheckCommandParsing:
    """Test check command argument parsing."""

    def test_check_default(self):
        """Test check command with defaults."""
        parser = create_parser()
        args = parser.parse_args(["check"])
        assert args.command == "check"
        assert args.platform is None

    def test_check_with_platform(self):
        """Test check command with specific platform."""
        parser = create_parser()
        args = parser.parse_args(["check", "twitter"])
        assert args.platform == "twitter"


class TestMeCommandParsing:
    """Test me command argument parsing."""

    def test_me_command(self):
        """Test me command."""
        parser = create_parser()
        args = parser.parse_args(["me", "twitter"])
        assert args.command == "me"
        assert args.platform == "twitter"


class TestScheduleCommandParsing:
    """Test schedule command argument parsing."""

    def test_schedule_list(self):
        """Test schedule list command."""
        parser = create_parser()
        args = parser.parse_args(["schedule", "list"])
        assert args.command == "schedule"
        assert args.schedule_command == "list"

    def test_schedule_cancel(self):
        """Test schedule cancel command."""
        parser = create_parser()
        args = parser.parse_args(["schedule", "cancel", "job-123"])
        assert args.schedule_command == "cancel"
        assert args.job_id == "job-123"

    def test_schedule_run(self):
        """Test schedule run command."""
        parser = create_parser()
        args = parser.parse_args(["schedule", "run"])
        assert args.schedule_command == "run"

    def test_schedule_daemon(self):
        """Test schedule daemon command."""
        parser = create_parser()
        args = parser.parse_args(["schedule", "daemon", "--interval", "30"])
        assert args.schedule_command == "daemon"
        assert args.interval == 30

    def test_post_with_schedule(self):
        """Test post command with --schedule flag."""
        parser = create_parser()
        args = parser.parse_args(["post", "twitter", "Hello", "--schedule", "+1h"])
        assert args.schedule == "+1h"


class TestMCPCommandParsing:
    """Test MCP command argument parsing."""

    def test_mcp_start(self):
        """Test mcp start command."""
        parser = create_parser()
        args = parser.parse_args(["mcp", "start"])
        assert args.command == "mcp"
        assert args.mcp_command == "start"

    def test_mcp_doctor(self):
        """Test mcp doctor command."""
        parser = create_parser()
        args = parser.parse_args(["mcp", "doctor"])
        assert args.mcp_command == "doctor"

    def test_mcp_list_tools(self):
        """Test mcp list-tools command."""
        parser = create_parser()
        args = parser.parse_args(["mcp", "list-tools"])
        assert args.mcp_command == "list-tools"

    def test_mcp_installation(self):
        """Test mcp installation command."""
        parser = create_parser()
        args = parser.parse_args(["mcp", "installation"])
        assert args.mcp_command == "installation"


class TestMCPCommands:
    """Test MCP command execution."""

    def test_mcp_doctor(self, capsys):
        """Test mcp doctor command output."""
        result = main(["mcp", "doctor"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Health Check" in captured.out
        assert "Twitter" in captured.out

    def test_mcp_installation(self, capsys):
        """Test mcp installation command output."""
        result = main(["mcp", "installation"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Claude Desktop" in captured.out
        assert "mcpServers" in captured.out
        assert "socialia" in captured.out


class TestScheduleCommands:
    """Test schedule command execution."""

    def test_schedule_list_empty(self, capsys, tmp_path):
        """Test schedule list with no jobs."""
        schedule_file = tmp_path / "scheduled.json"
        schedule_file.write_text("[]")

        with patch("socialia.scheduler.SCHEDULE_FILE", schedule_file):
            result = main(["schedule", "list"])

        assert result == 0
        captured = capsys.readouterr()
        assert "No scheduled" in captured.out or "pending" in captured.out.lower()

    def test_schedule_cancel_nonexistent(self, capsys, tmp_path):
        """Test schedule cancel with non-existent job."""
        schedule_file = tmp_path / "scheduled.json"
        schedule_file.write_text("[]")

        with patch("socialia.scheduler.SCHEDULE_FILE", schedule_file):
            result = main(["schedule", "cancel", "nonexistent"])

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower() or "error" in captured.err.lower()
