# $LicenseInfo:firstyear=2026&license=viewerlgpl$
# Second Life Viewer Source Code
# Copyright (C) 2026, Linden Research, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation;
# version 2.1 of the License only.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Linden Research, Inc., 945 Battery Street, San Francisco, CA  94111  USA
# $/LicenseInfo$

import unittest
from unittest.mock import MagicMock, patch
import json
import urllib.error

from fsutils.tag_release import (
    validate_repo,
    validate_sha,
    validate_tag_name,
    create_git_ref,
)


class TestTagRelease(unittest.TestCase):

    def test_validate_repo_valid(self):
        self.assertEqual(validate_repo("owner/repo"), "owner/repo")
        self.assertEqual(validate_repo("Kaleaon/phoenix-firestorm-jules"), "Kaleaon/phoenix-firestorm-jules")

    def test_validate_repo_invalid(self):
        with self.assertRaises(ValueError):
            validate_repo("invalid_repo_without_slash")
        with self.assertRaises(ValueError):
            validate_repo("owner/repo/extra")
        with self.assertRaises(ValueError):
            validate_repo("owner/repo; rm -rf /")

    def test_validate_sha_valid(self):
        self.assertEqual(validate_sha("1234567"), "1234567")
        self.assertEqual(validate_sha("a" * 40), "a" * 40)

    def test_validate_sha_invalid(self):
        with self.assertRaises(ValueError):
            validate_sha("123")  # too short
        with self.assertRaises(ValueError):
            validate_sha("g" * 40)  # non-hex
        with self.assertRaises(ValueError):
            validate_sha("1234567; echo injection")

    def test_validate_tag_name_valid(self):
        self.assertEqual(validate_tag_name("Second_Life_Test#12345678-hippo"), "Second_Life_Test#12345678-hippo")
        self.assertEqual(validate_tag_name("Firestorm_Release_7.1.10.799999"), "Firestorm_Release_7.1.10.799999")

    def test_validate_tag_name_invalid(self):
        with self.assertRaises(ValueError):
            validate_tag_name("tag with spaces")
        with self.assertRaises(ValueError):
            validate_tag_name("tag;rm -rf")

    @patch("urllib.request.urlopen")
    def test_create_git_ref_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"ref": "refs/tags/my-tag", "object": {"sha": "a" * 40}}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = create_git_ref(
            repo="owner/repo",
            tag_name="my-tag",
            sha="a" * 40,
            token="secret_token",
        )
        self.assertEqual(res["ref"], "refs/tags/my-tag")

    def test_create_git_ref_missing_token(self):
        with self.assertRaises(ValueError):
            create_git_ref(repo="owner/repo", tag_name="my-tag", sha="a" * 40, token="")


if __name__ == "__main__":
    unittest.main()
