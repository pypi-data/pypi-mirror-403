"""Tests for feature gating on Pro/Enterprise features.

Tests that @require_feature decorators are properly applied to commands
and that the upgrade prompt is shown when features are not available.
"""

from unittest.mock import patch, MagicMock
import pytest

from bpsai_pair.licensing.core import FeatureNotAvailable


class TestTrelloGating:
    """Tests for Trello feature gating."""

    def test_trello_connect_requires_feature(self):
        """Trello connect command should require 'trello' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.trello.connection import connect

            with pytest.raises(FeatureNotAvailable) as exc_info:
                connect(api_key="test", token="test")

            assert exc_info.value.feature == "trello"

    def test_trello_status_requires_feature(self):
        """Trello status command should require 'trello' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.trello.connection import status

            with pytest.raises(FeatureNotAvailable) as exc_info:
                status()

            assert exc_info.value.feature == "trello"

    def test_ttask_start_requires_feature(self):
        """ttask start command should require 'trello' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.trello.task_lifecycle import task_start

            with pytest.raises(FeatureNotAvailable) as exc_info:
                task_start(card_id="test-123")

            assert exc_info.value.feature == "trello"

    def test_ttask_done_requires_feature(self):
        """ttask done command should require 'trello' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.trello.task_lifecycle import task_done

            with pytest.raises(FeatureNotAvailable) as exc_info:
                task_done(card_id="test-123")

            assert exc_info.value.feature == "trello"

    def test_ttask_list_requires_feature(self):
        """ttask list command should require 'trello' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.trello.task_display import task_list

            with pytest.raises(FeatureNotAvailable) as exc_info:
                task_list()

            assert exc_info.value.feature == "trello"


class TestGitHubGating:
    """Tests for GitHub feature gating."""

    def test_github_status_requires_feature(self):
        """GitHub status command should require 'github' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.github.commands import status

            with pytest.raises(FeatureNotAvailable) as exc_info:
                status()

            assert exc_info.value.feature == "github"

    def test_github_pr_requires_feature(self):
        """GitHub pr command should require 'github' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.github.commands import pr_status

            with pytest.raises(FeatureNotAvailable) as exc_info:
                pr_status()

            assert exc_info.value.feature == "github"

    def test_github_create_pr_requires_feature(self):
        """GitHub create command should require 'github' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.github.commands import create_pr

            with pytest.raises(FeatureNotAvailable) as exc_info:
                create_pr(task_id="T30.1")

            assert exc_info.value.feature == "github"


class TestBudgetGating:
    """Tests for token budget feature gating."""

    def test_budget_estimate_requires_feature(self):
        """Budget estimate command should require 'token_budget' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.commands.budget import budget_estimate

            with pytest.raises(FeatureNotAvailable) as exc_info:
                budget_estimate(task_id="T30.1")

            assert exc_info.value.feature == "token_budget"

    def test_budget_status_requires_feature(self):
        """Budget status command should require 'token_budget' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.commands.budget import budget_status

            with pytest.raises(FeatureNotAvailable) as exc_info:
                budget_status()

            assert exc_info.value.feature == "token_budget"

    def test_budget_check_requires_feature(self):
        """Budget check command should require 'token_budget' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.commands.budget import budget_check

            with pytest.raises(FeatureNotAvailable) as exc_info:
                budget_check(task_id="T30.1")

            assert exc_info.value.feature == "token_budget"


class TestTimerGating:
    """Tests for timer feature gating."""

    def test_timer_start_requires_feature(self):
        """Timer start command should require 'timer' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.commands.timer import timer_start

            with pytest.raises(FeatureNotAvailable) as exc_info:
                timer_start(task_id="T30.1")

            assert exc_info.value.feature == "timer"

    def test_timer_stop_requires_feature(self):
        """Timer stop command should require 'timer' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.commands.timer import timer_stop

            with pytest.raises(FeatureNotAvailable) as exc_info:
                timer_stop()

            assert exc_info.value.feature == "timer"

    def test_timer_status_requires_feature(self):
        """Timer status command should require 'timer' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.commands.timer import timer_status

            with pytest.raises(FeatureNotAvailable) as exc_info:
                timer_status()

            assert exc_info.value.feature == "timer"


class TestMCPGating:
    """Tests for MCP feature gating."""

    def test_mcp_run_server_requires_feature(self):
        """MCP run_server should require 'mcp' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.mcp.server import run_server

            with pytest.raises(FeatureNotAvailable) as exc_info:
                run_server()

            assert exc_info.value.feature == "mcp"

    def test_mcp_create_server_requires_feature(self):
        """MCP create_server should require 'mcp' feature."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.mcp.server import create_server

            with pytest.raises(FeatureNotAvailable) as exc_info:
                create_server()

            assert exc_info.value.feature == "mcp"


class TestUpgradePrompt:
    """Tests for upgrade prompt display."""

    def test_feature_not_available_includes_feature_name(self):
        """FeatureNotAvailable should include the feature name."""
        exc = FeatureNotAvailable("trello", "solo")
        assert "trello" in str(exc)
        assert exc.feature == "trello"

    def test_feature_not_available_includes_tier(self):
        """FeatureNotAvailable should include the tier."""
        exc = FeatureNotAvailable("trello", "solo")
        assert exc.tier == "solo"

    def test_feature_not_available_suggests_upgrade(self):
        """FeatureNotAvailable message should suggest upgrade."""
        exc = FeatureNotAvailable("trello", "solo")
        assert "upgrade" in str(exc).lower() or "Upgrade" in str(exc)


class TestGracefulDegradation:
    """Tests that feature gating results in graceful degradation."""

    def test_allowed_when_feature_available(self):
        """Commands should work when feature is available."""
        # Test that decorators allow execution when feature is available
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=True):
            # The decorator should not raise when feature is available
            from bpsai_pair.licensing.core import require_feature

            @require_feature("trello")
            def test_fn():
                return "success"

            result = test_fn()
            assert result == "success"

    def test_exception_type_is_correct(self):
        """Feature gating should raise FeatureNotAvailable, not generic Exception."""
        with patch("bpsai_pair.licensing.core.has_feature_api", return_value=False):
            from bpsai_pair.licensing.core import require_feature

            @require_feature("test_feature")
            def test_fn():
                return "success"

            with pytest.raises(FeatureNotAvailable):
                test_fn()

            # Should not raise generic Exception
            try:
                test_fn()
            except FeatureNotAvailable:
                pass
            except Exception:
                pytest.fail("Should raise FeatureNotAvailable, not generic Exception")


class TestUpgradePromptDisplay:
    """Tests for the CLI upgrade prompt display."""

    def test_upgrade_prompt_shows_pricing_link(self):
        """Upgrade prompt should include paircoder.ai/pricing link."""
        from io import StringIO
        from bpsai_pair.cli import _show_upgrade_prompt
        from bpsai_pair.licensing.core import FeatureNotAvailable

        exc = FeatureNotAvailable("trello", "solo")

        # Capture console output
        from rich.console import Console
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        # Temporarily replace console
        import bpsai_pair.cli as cli_module
        original_console = cli_module.console
        cli_module.console = test_console

        try:
            _show_upgrade_prompt(exc)
            result = output.getvalue()
            assert "paircoder.ai/pricing" in result
        finally:
            cli_module.console = original_console

    def test_upgrade_prompt_shows_license_install(self):
        """Upgrade prompt should include license install command."""
        from io import StringIO
        from bpsai_pair.cli import _show_upgrade_prompt
        from bpsai_pair.licensing.core import FeatureNotAvailable

        exc = FeatureNotAvailable("github", "solo")

        from rich.console import Console
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        import bpsai_pair.cli as cli_module
        original_console = cli_module.console
        cli_module.console = test_console

        try:
            _show_upgrade_prompt(exc)
            result = output.getvalue()
            assert "license install" in result
        finally:
            cli_module.console = original_console
