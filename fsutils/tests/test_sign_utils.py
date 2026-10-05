import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from fsutils.sign_utils import (
    validate_filename,
    validate_repo,
    validate_run_id,
    handle_get_setup_files,
    handle_prepare_file,
)


class TestSignUtils(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_validate_filename_valid(self):
        self.assertEqual(validate_filename("Firestorm_Setup.exe"), "Firestorm_Setup.exe")
        self.assertEqual(validate_filename("/path/to/Firestorm_Setup.exe"), "Firestorm_Setup.exe")

    def test_validate_filename_invalid(self):
        with self.assertRaises(ValueError):
            validate_filename("file;rm -rf")
        with self.assertRaises(ValueError):
            validate_filename("bad|file.exe")

    def test_validate_repo(self):
        self.assertEqual(validate_repo("owner/repo"), "owner/repo")
        with self.assertRaises(ValueError):
            validate_repo("invalid_repo")

    def test_validate_run_id(self):
        self.assertEqual(validate_run_id("12345678"), "12345678")
        with self.assertRaises(ValueError):
            validate_run_id("abc123")

    def test_handle_get_setup_files(self):
        artifacts_dir = os.path.join(self.test_dir, "artifacts")
        output_dir = os.path.join(self.test_dir, "setup_exe_files")
        os.makedirs(os.path.join(artifacts_dir, "subfolder"), exist_ok=True)

        setup_file = os.path.join(artifacts_dir, "subfolder", "Firestorm_Setup.exe")
        with open(setup_file, "w", encoding="utf-8") as f:
            f.write("dummy setup content")

        handle_get_setup_files(artifacts_dir=artifacts_dir, output_dir=output_dir)

        copied_file = os.path.join(output_dir, "Firestorm_Setup.exe")
        self.assertTrue(os.path.exists(copied_file))

    def test_handle_prepare_file(self):
        src_dir = os.path.join(self.test_dir, "setup_exe_files")
        dst_dir = os.path.join(self.test_dir, "to_sign")
        os.makedirs(src_dir, exist_ok=True)

        dummy_file = os.path.join(src_dir, "Firestorm_Setup.exe")
        with open(dummy_file, "w", encoding="utf-8") as f:
            f.write("content")

        handle_prepare_file("Firestorm_Setup.exe", source_dir=src_dir, target_dir=dst_dir)

        self.assertTrue(os.path.exists(os.path.join(dst_dir, "Firestorm_Setup.exe")))

    def test_handle_prepare_file_path_traversal(self):
        src_dir = os.path.join(self.test_dir, "setup_exe_files")
        dst_dir = os.path.join(self.test_dir, "to_sign")
        os.makedirs(src_dir, exist_ok=True)

        with self.assertRaises(ValueError):
            handle_prepare_file("../secret.txt", source_dir=src_dir, target_dir=dst_dir)


if __name__ == "__main__":
    unittest.main()
