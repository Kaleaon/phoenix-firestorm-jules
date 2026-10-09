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
from fsutils.parse_workflow_inputs import (
    validate_version,
    validate_build_number,
    validate_release_type,
    validate_channel,
    validate_project,
    validate_sha,
    validate_dry_run,
)


class TestParseWorkflowInputs(unittest.TestCase):

    def test_validate_version_valid(self):
        self.assertEqual(validate_version("7.1.10"), "7.1.10")

    def test_validate_version_invalid(self):
        with self.assertRaises(ValueError):
            validate_version("7.1")
        with self.assertRaises(ValueError):
            validate_version("7.1.10; rm -rf")

    def test_validate_build_number(self):
        self.assertEqual(validate_build_number("799999"), "799999")
        with self.assertRaises(ValueError):
            validate_build_number("799999a")

    def test_validate_release_type(self):
        self.assertEqual(validate_release_type("Release"), "Release")
        self.assertEqual(validate_release_type("Nightly"), "Nightly")
        with self.assertRaises(ValueError):
            validate_release_type("Release; invalid")

    def test_validate_channel(self):
        self.assertEqual(validate_channel("Test"), "Test")
        self.assertEqual(validate_channel("Release"), "Release")

    def test_validate_project(self):
        self.assertEqual(validate_project("hippo"), "hippo")
        with self.assertRaises(ValueError):
            validate_project("hippo; command")

    def test_validate_sha(self):
        self.assertEqual(validate_sha("a" * 40), "a" * 40)
        with self.assertRaises(ValueError):
            validate_sha("123")

    def test_validate_dry_run(self):
        self.assertEqual(validate_dry_run("true"), "true")
        self.assertEqual(validate_dry_run("false"), "false")
        with self.assertRaises(ValueError):
            validate_dry_run("invalid")


if __name__ == "__main__":
    unittest.main()
