#!/usr/bin/env python3
"""
@file test_download_list.py
@brief Unit tests for download_list.py manifest generation utilities.

$LicenseInfo:firstyear=2026&license=viewerlgpl$
Second Life Viewer Source Code
Copyright (C) 2026, Linden Research, Inc.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation;
version 2.1 of the License only.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

Linden Research, Inc., 945 Battery Street, San Francisco, CA  94111  USA
$/LicenseInfo$
"""

import hashlib
import os
import shutil
import tempfile
import unittest

from fsutils.download_list import generate_sha256_manifest


class TestDownloadList(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.win_dir = os.path.join(self.test_dir, "win")
        os.makedirs(self.win_dir)

        self.sample_file = os.path.join(self.win_dir, "Phoenix_Setup.exe")
        with open(self.sample_file, "wb") as f:
            f.write(b"installer_dummy_content")

        self.expected_hash = hashlib.sha256(b"installer_dummy_content").hexdigest()

        self.build_info = {
            "build_type_fullpath": self.test_dir,
            "os_folders": ["win"],
            "downloadable_artifacts": {
                "SL-regular-win": {
                    "file_path": self.sample_file,
                    "file_download_URI": "https://example.com/win/Phoenix_Setup.exe",
                    "grid": "SL",
                    "variant": "regular",
                    "md5": "dummy_md5",
                }
            },
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_generate_sha256_manifest(self):
        generate_sha256_manifest(self.build_info)

        root_manifest = os.path.join(self.test_dir, "SHA256SUMS.txt")
        self.assertTrue(os.path.isfile(root_manifest))

        with open(root_manifest, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(self.expected_hash, content)
        self.assertIn("win/Phoenix_Setup.exe", content)

        platform_manifest = os.path.join(self.win_dir, "SHA256SUMS.txt")
        self.assertTrue(os.path.isfile(platform_manifest))

        with open(platform_manifest, "r", encoding="utf-8") as f:
            p_content = f.read()

        self.assertIn(self.expected_hash, p_content)
        self.assertIn("Phoenix_Setup.exe", p_content)


if __name__ == "__main__":
    unittest.main()
