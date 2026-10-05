import os
import unittest
from unittest.mock import MagicMock, patch

from fsutils.manage_tags import (
    validate_tag_name,
    validate_dry_run,
    handle_determine,
    handle_check,
    handle_create,
    handle_push,
    handle_confirm,
)


class TestManageTags(unittest.TestCase):

    def test_validate_tag_name_valid(self):
        self.assertEqual(validate_tag_name("Firestorm_Release_7.1.10.7000"), "Firestorm_Release_7.1.10.7000")

    def test_validate_tag_name_invalid(self):
        with self.assertRaises(ValueError):
            validate_tag_name("invalid tag name")
        with self.assertRaises(ValueError):
            validate_tag_name("tag$name")

    def test_validate_dry_run(self):
        self.assertTrue(validate_dry_run("true"))
        self.assertTrue(validate_dry_run("1"))
        self.assertFalse(validate_dry_run("false"))
        self.assertFalse(validate_dry_run("0"))
        with self.assertRaises(ValueError):
            validate_dry_run("maybe")

    @patch("subprocess.run")
    def test_handle_check_exists(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        exists = handle_check("v1.0.0")
        self.assertTrue(exists)
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "v1.0.0"],
            stdout=-1,
            stderr=-1,
            text=True,
            check=False,
        )

    @patch("subprocess.run")
    def test_handle_check_not_exists(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        exists = handle_check("v1.0.0")
        self.assertFalse(exists)

    @patch("subprocess.run")
    def test_handle_create_dry_run(self, mock_run):
        handle_create("v1.0.0", dry_run="true")
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_handle_create_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        handle_create("v1.0.0", dry_run="false")
        mock_run.assert_called_once_with(["git", "tag", "v1.0.0"], capture_output=True, text=True)

    @patch("subprocess.run")
    def test_handle_push_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        handle_push("v1.0.0", remote="origin", dry_run="false")
        mock_run.assert_called_once_with(["git", "push", "origin", "v1.0.0"], capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
