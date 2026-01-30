import unittest
from unittest.mock import patch, MagicMock
from commitgen import ai

class TestAI(unittest.TestCase):

    def test_build_prompt_without_context(self):
        diff = "diff --git a/file b/file"
        prompt = ai._build_prompt(diff, "")
        self.assertIn("GIT DIFF:", prompt)
        self.assertIn(diff, prompt)
        self.assertNotIn("ADDITIONAL CONTEXT", prompt)

    def test_build_prompt_with_context(self):
        diff = "diff"
        context = "Fix crash"
        prompt = ai._build_prompt(diff, context)
        self.assertIn("ADDITIONAL CONTEXT", prompt)
        self.assertIn(context, prompt)

    @patch("commitgen.ai.ensure_api_key", return_value="fake-key")
    @patch("commitgen.ai.OpenAI")
    def test_generate_commit_message(self, mock_openai, _):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.output_text = "[FEAT]: add login"
        mock_client.responses.create.return_value = mock_response
        mock_openai.return_value = mock_client

        msg = ai.generate_commit_message("diff", "")
        self.assertEqual(msg, "[FEAT]: add login")

    def test_generate_commit_message_empty_diff(self):
        msg = ai.generate_commit_message("", "")
        self.assertEqual(msg, "chore: no changes detected")

    def test_fallback_commit_message_no_context(self):
        msg = ai._fallback_commit_message("some diff", "")
        self.assertIn("[FEAT]:", msg)

    def test_fallback_commit_message_with_context(self):
        msg = ai._fallback_commit_message("diff", "extra context")
        self.assertIn("Context: extra context", msg)

    @patch("commitgen.ai.ensure_api_key", return_value="fake-key")
    @patch("commitgen.ai.OpenAI")
    def test_refine_commit_message_preserves_structure(self, mock_openai, _):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.output_text = "[FEAT]: refined message"
        mock_client.responses.create.return_value = mock_response
        mock_openai.return_value = mock_client

        msg = ai.refine_commit_message("[FEAT]: add login", "fix bug")
        self.assertEqual(msg, "[FEAT]: refined message")
