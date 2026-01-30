import unittest
from commitgen.cli import editor_template

class TestEditorTemplate(unittest.TestCase):

    def test_editor_template_includes_comments(self):
        msg = "Initial commit"
        template = editor_template(msg)
        self.assertIn("Save the file before closing", template)
        self.assertIn(msg, template)

    def test_comment_lines_removed_after_edit(self):
        msg = "Initial commit"
        template = editor_template(msg)
        lines = template.splitlines()
        # Simulate user edited and kept comments
        final_msg = "\n".join(line for line in lines if not line.strip().startswith("#")).strip()
        self.assertEqual(final_msg, msg)
