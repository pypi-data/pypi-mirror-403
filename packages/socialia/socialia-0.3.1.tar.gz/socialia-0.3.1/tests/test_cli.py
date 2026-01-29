"""Tests for socialia CLI."""

import pytest
from socialia.cli import create_parser, main


class TestCLIParser:
    """Test CLI argument parsing."""

    def test_parser_creation(self):
        """Test parser is created successfully."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "socialia"

    def test_version_argument(self, capsys):
        """Test --version argument."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_post_command_parsing(self):
        """Test post command parsing."""
        parser = create_parser()
        args = parser.parse_args(["post", "twitter", "Hello World"])
        assert args.command == "post"
        assert args.platform == "twitter"
        assert args.text == "Hello World"

    def test_post_dry_run(self):
        """Test post dry-run flag."""
        parser = create_parser()
        args = parser.parse_args(["post", "twitter", "Test", "--dry-run"])
        assert args.dry_run is True

    def test_delete_command_parsing(self):
        """Test delete command parsing."""
        parser = create_parser()
        args = parser.parse_args(["delete", "twitter", "123456"])
        assert args.command == "delete"
        assert args.platform == "twitter"
        assert args.post_id == "123456"

    def test_analytics_track_parsing(self):
        """Test analytics track command parsing."""
        parser = create_parser()
        args = parser.parse_args(["analytics", "track", "test_event"])
        assert args.command == "analytics"
        assert args.analytics_command == "track"
        assert args.event_name == "test_event"


class TestCLIDryRun:
    """Test CLI dry-run functionality."""

    def test_post_dry_run_twitter(self, capsys):
        """Test dry-run post to Twitter."""
        result = main(["post", "twitter", "Test message", "--dry-run"])
        assert result == 0
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        assert "twitter" in captured.out.lower()

    def test_post_dry_run_linkedin(self, capsys):
        """Test dry-run post to LinkedIn."""
        result = main(["post", "linkedin", "Test message", "--dry-run"])
        assert result == 0
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        assert "linkedin" in captured.out.lower()


class TestCLIMain:
    """Test CLI main function."""

    def test_no_command_shows_help(self, capsys):
        """Test that no command shows help."""
        result = main([])
        assert result == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "socialia" in captured.out.lower()

    def test_help_recursive(self, capsys):
        """Test --help-recursive option."""
        result = main(["--help-recursive"])
        assert result == 0
        captured = capsys.readouterr()
        assert "SOCIALIA" in captured.out
        assert "post" in captured.out.lower()
        assert "delete" in captured.out.lower()

    def test_post_missing_text_error(self, capsys):
        """Test post without text shows error."""
        result = main(["post", "twitter"])
        assert result == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()

    def test_status_command(self, capsys):
        """Test status command."""
        result = main(["status"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Socialia" in captured.out
        assert "TWITTER" in captured.out or "twitter" in captured.out.lower()

    def test_mcp_list_tools_command(self, capsys):
        """Test mcp list-tools command."""
        result = main(["mcp", "list-tools"])
        assert result == 0
        captured = capsys.readouterr()
        assert "MCP" in captured.out or "Tools" in captured.out
        assert "social_post" in captured.out


class TestCLICompletion:
    """Test CLI completion commands."""

    def test_completion_bash(self, capsys):
        """Test completion bash command."""
        result = main(["completion", "bash"])
        assert result == 0
        captured = capsys.readouterr()
        assert "argcomplete" in captured.out.lower() or "compdef" in captured.out

    def test_completion_zsh(self, capsys):
        """Test completion zsh command."""
        result = main(["completion", "zsh"])
        assert result == 0
        captured = capsys.readouterr()
        assert "compdef" in captured.out or "bashcompinit" in captured.out

    def test_completion_status(self, capsys):
        """Test completion status command."""
        result = main(["completion", "status"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Completion Status" in captured.out
        assert "Bash" in captured.out
        assert "Zsh" in captured.out
