import unittest
from unittest.mock import patch
import commitgen.git_utils as git_utils

class TestGitUtils(unittest.TestCase):

    @patch("commitgen.git_utils.subprocess.run")
    def test_verify_repo_true(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(git_utils.verify_repo())

    @patch("commitgen.git_utils.subprocess.run")
    def test_verify_repo_false(self, mock_run):
        mock_run.return_value.returncode = 1
        self.assertFalse(git_utils.verify_repo())

    @patch("commitgen.git_utils.subprocess.run")
    def test_stage_all_changes(self, mock_run):
        git_utils.stage_all_changes()
        mock_run.assert_called_once_with(["git", "add", "."])

    @patch("commitgen.git_utils.subprocess.run")
    def test_has_staged_changes_true(self, mock_run):
        mock_run.return_value.returncode = 1
        self.assertTrue(git_utils.has_staged_changes())

    @patch("commitgen.git_utils.subprocess.run")
    def test_has_staged_changes_false(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertFalse(git_utils.has_staged_changes())

    @patch("commitgen.git_utils.subprocess.run")
    def test_get_staged_diff_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "diff --git a/file b/file"
        self.assertEqual(git_utils.get_staged_diff(), "diff --git a/file b/file")

    @patch("commitgen.git_utils.subprocess.run")
    def test_get_staged_diff_failure(self, mock_run):
        mock_run.return_value.returncode = 1
        self.assertEqual(git_utils.get_staged_diff(), "")

    @patch("commitgen.git_utils.subprocess.run")
    def test_commit_changes(self, mock_run):
        git_utils.commit_changes("feat: test")
        mock_run.assert_called_once_with(["git", "commit", "-m", "feat: test"], check=True)

    @patch("commitgen.git_utils.subprocess.run")
    def test_push_changes(self, mock_run):
        git_utils.push_changes()
        mock_run.assert_called_once()

    @patch("commitgen.git_utils.subprocess.run")
    def test_get_modified_files(self, mock_run):
        mock_run.return_value.stdout = " M file1\n?? file2\n"
        files = git_utils.get_modified_files()
        self.assertEqual(files, ["file1", "file2"])

    @patch("commitgen.git_utils.subprocess.run")
    def test_stage_file(self, mock_run):
        git_utils.stage_file("file1")
        mock_run.assert_called_once_with(["git", "add", "file1"])
