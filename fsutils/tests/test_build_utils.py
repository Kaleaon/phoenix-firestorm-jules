import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from fsutils.build_utils import (
    set_grid_flags,
    find_channel,
    check_codesigning,
    define_platform,
    find_most_recent_bundle,
    set_expiry_args,
    add_custom_ua,
    extract_version,
    resolve_deploy_env,
    create_build_info,
)


class TestBuildUtils(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_set_grid_flags_sl(self):
        with patch("fsutils.build_utils.export_variable") as mock_export:
            set_grid_flags("sl")
            mock_export.assert_called_once_with("FS_GRID", "-DOPENSIM:BOOL=OFF -DHAVOK_TPV:BOOL=ON")

    def test_set_grid_flags_os(self):
        with patch("fsutils.build_utils.export_variable") as mock_export:
            set_grid_flags("os")
            mock_export.assert_called_once_with("FS_GRID", "-DOPENSIM:BOOL=ON -DHAVOK_TPV:BOOL=OFF")

    def test_set_grid_flags_invalid(self):
        with self.assertRaises(ValueError):
            set_grid_flags("invalid_grid")

    def test_find_channel_release(self):
        with patch("fsutils.build_utils.export_variable") as mock_export:
            find_channel(ref_name="Firestorm_7.1.10", event_name="push", variant="regular")
            mock_export.assert_any_call("FS_RELEASE_TYPE", "Release")
            mock_export.assert_any_call("FS_RELEASE_CHAN", "Release")

    def test_find_channel_avx(self):
        with patch("fsutils.build_utils.export_variable") as mock_export:
            find_channel(ref_name="Firestorm_7.1.10", event_name="push", variant="avx")
            mock_export.assert_any_call("FS_RELEASE_CHAN", "Releasex64")

    def test_check_codesigning_windows_release(self):
        with patch("fsutils.build_utils.export_variable") as mock_export:
            check_codesigning(runner_os="Windows", release_type="Release")
            mock_export.assert_called_once_with("CODESIGNING_ENABLED", "true")

    def test_check_codesigning_linux(self):
        with patch("fsutils.build_utils.export_variable") as mock_export:
            check_codesigning(runner_os="Linux", release_type="Release")
            mock_export.assert_called_once_with("CODESIGNING_ENABLED", "false")

    def test_define_platform_windows(self):
        with patch("fsutils.build_utils.export_variable") as mock_export:
            define_platform(runner_os="Windows", addrsize="64")
            mock_export.assert_any_call("fallback_platform", "windows")
            mock_export.assert_any_call("platform", "windows64")

    def test_find_most_recent_bundle(self):
        bundle1 = os.path.join(self.test_dir, "fmodstudio-1.0-windows64_100.tar.bz2")
        bundle2 = os.path.join(self.test_dir, "fmodstudio-1.0-windows64_200.tar.bz2")

        with open(bundle1, "w") as f:
            f.write("a")
        with open(bundle2, "w") as f:
            f.write("b")

        # Set modification time on bundle2 newer
        os.utime(bundle1, (100, 100))
        os.utime(bundle2, (200, 200))

        result = find_most_recent_bundle(self.test_dir, "fmodstudio", "windows64")
        self.assertEqual(result, os.path.basename(bundle2))

    def test_set_expiry_args_nightly(self):
        with patch("fsutils.build_utils.export_variable") as mock_export:
            set_expiry_args(release_type="Nightly", current_extra_args="-DUSE_FMODSTUDIO=ON")
            mock_export.assert_called_once_with("EXTRA_ARGS", "-DUSE_FMODSTUDIO=ON --testbuild=14")

    def test_add_custom_ua(self):
        with patch("fsutils.build_utils.export_variable") as mock_export:
            add_custom_ua(custom_ua="MyCustomUA/1.0", current_extra_args="-DUSE_FMODSTUDIO=ON")
            mock_export.assert_called_once_with("EXTRA_ARGS", '-DUSE_FMODSTUDIO=ON -DFS_PF_USER_AGENT="MyCustomUA/1.0"')

    def test_extract_version(self):
        version_file = os.path.join(self.test_dir, "VIEWER_VERSION.txt")
        with open(version_file, "w") as f:
            f.write("7.1.10")

        with patch("subprocess.run") as mock_run, patch("fsutils.build_utils.export_variable") as mock_export:
            mock_run.return_value = MagicMock(returncode=0, stdout="80000\n")
            extract_version(version_file=version_file, release_chan="Releasex64", release_type="Release")

            mock_export.assert_any_call("viewer_version", "7.1.10")
            mock_export.assert_any_call("viewer_build", "80000")
            mock_export.assert_any_call("viewer_channel", "Releasex64")

    def test_resolve_deploy_env_release(self):
        with patch("fsutils.build_utils.export_variable") as mock_export:
            resolve_deploy_env(release_type="Release", release_webhook="https://webhook.url")
            mock_export.assert_any_call("FS_RELEASE_FOLDER", "release")
            mock_export.assert_any_call("FS_BUILD_WEBHOOK_URL", "https://webhook.url")

    def test_create_build_info(self):
        output_file = os.path.join(self.test_dir, "build_info.json")
        create_build_info(
            run_number="12345",
            release_type="Release",
            viewer_version="7.1.10",
            viewer_build="80000",
            output_file=output_file,
        )

        self.assertTrue(os.path.exists(output_file))
        with open(output_file, "r") as f:
            data = json.load(f)
            self.assertEqual(data["build_run_number"], "12345")
            self.assertEqual(data["release_type"], "Release")


if __name__ == "__main__":
    unittest.main()
