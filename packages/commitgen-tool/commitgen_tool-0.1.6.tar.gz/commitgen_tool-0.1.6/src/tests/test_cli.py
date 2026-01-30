import unittest
from unittest.mock import patch
from typer.testing import CliRunner
from commitgen.cli import app

runner = CliRunner()


class TestCLI(unittest.TestCase):

    @patch("commitgen.cli.git_utils.verify_repo", return_value=False)
    def test_commit_not_git_repo(self, mock_verify_repo):
        result = runner.invoke(app, ["commit"])
        self.assertNotEqual(result.exit_code, 0)

    @patch("commitgen.cli.git_utils.verify_repo", return_value=True)
    @patch("commitgen.cli.git_utils.has_staged_changes", return_value=False)
    @patch("commitgen.cli.typer.prompt", return_value="q")
    def test_commit_no_staged_changes_abort(self, *_):
        result = runner.invoke(app, ["commit"])
        self.assertNotEqual(result.exit_code, 0)

    @patch("commitgen.cli.git_utils.push_changes")
    @patch("commitgen.cli.git_utils.commit_changes")
    @patch("commitgen.cli.ai.generate_commit_message", return_value="[FEAT]: add login")
    @patch("commitgen.cli.git_utils.get_staged_diff", return_value="diff --git a b")
    @patch("commitgen.cli.git_utils.has_staged_changes", return_value=True)
    @patch("commitgen.cli.git_utils.verify_repo", return_value=True)
    @patch("commitgen.cli.typer.prompt", side_effect=["a", "n"])
    def test_commit_accept_flow(self, *_):
        result = runner.invoke(app, ["commit"])
        self.assertEqual(result.exit_code, 0)

    @patch("commitgen.cli.git_utils.push_changes")
    @patch("commitgen.cli.git_utils.commit_changes")
    @patch("commitgen.cli.ai.generate_commit_message", return_value="[FEAT]: initial")
    @patch("commitgen.cli.typer.edit", return_value="[FEAT]: edited message")
    @patch("commitgen.cli.git_utils.get_staged_diff", return_value="diff")
    @patch("commitgen.cli.git_utils.has_staged_changes", return_value=True)
    @patch("commitgen.cli.git_utils.verify_repo", return_value=True)
    @patch(
        "commitgen.cli.typer.prompt",
        side_effect=[
            "e",  # choose editor
            "n",  # do not push after commit
        ],
    )
    @patch("commitgen.cli.typer.confirm", return_value=True)
    def test_commit_editor_flow(self, *_):
        result = runner.invoke(app, ["commit"])
        self.assertEqual(result.exit_code, 0)

    def test_version_command(self):
        result = runner.invoke(app, ["version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("CommitGen version", result.output)

    @patch("commitgen.cli.CONFIG_FILE")
    @patch("commitgen.cli.CONFIG_DIR")
    @patch("commitgen.cli.typer.prompt", return_value="fake-key")
    def test_config_command(self, *_):
        result = runner.invoke(app, ["config"])
        self.assertEqual(result.exit_code, 0)

    @patch("commitgen.cli.git_utils.verify_repo", return_value=True)
    @patch("commitgen.cli.git_utils.has_staged_changes", return_value=True)
    @patch("commitgen.cli.git_utils.get_staged_diff", return_value="diff --git a b")
    @patch("commitgen.cli.ai.generate_commit_message", return_value="[FEAT]: auto commit")
    @patch("commitgen.cli.ai._fallback_commit_message", return_value="[FEAT]: fallback commit")
    @patch("commitgen.cli.git_utils.commit_changes")
    @patch("commitgen.cli.git_utils.push_changes")
    def test_commit_auto_flag(self, mock_push, mock_commit, mock_fallback, mock_generate, mock_diff, mock_staged, mock_verify):
        """Test that --auto flag commits and pushes automatically."""
        result = runner.invoke(app, ["commit", "--auto"])

        # Should exit after auto commit
        self.assertEqual(result.exit_code, 0)

        # Ensure commit_changes is called once with generated message
        mock_commit.assert_called_once_with("[FEAT]: auto commit")

        # Ensure push_changes is called once
        mock_push.assert_called_once()

    @patch("commitgen.cli.git_utils.verify_repo", return_value=True)
    @patch("commitgen.cli.git_utils.has_staged_changes", return_value=False)
    @patch("commitgen.cli.git_utils.stage_all_changes")
    @patch("commitgen.cli.git_utils.get_staged_diff", return_value="diff --git a b")
    @patch("commitgen.cli.ai.generate_commit_message", return_value="[FEAT]: auto staged commit")
    @patch("commitgen.cli.git_utils.commit_changes")
    @patch("commitgen.cli.git_utils.push_changes")
    def test_commit_auto_flag_stages_changes(self, mock_push, mock_commit, mock_generate, mock_diff, mock_stage_all, mock_staged, mock_verify):
        """Test that --auto stages all changes if nothing is staged."""
        result = runner.invoke(app, ["commit", "--auto"])

        self.assertEqual(result.exit_code, 0)
        mock_stage_all.assert_called_once()
        mock_commit.assert_called_once_with("[FEAT]: auto staged commit")
        mock_push.assert_called_once()
