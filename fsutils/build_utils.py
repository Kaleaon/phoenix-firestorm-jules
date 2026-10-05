#!/usr/bin/env python3
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

"""
build_utils.py

Helper module containing build automation tasks extracted from build_viewer.yml.
Replaces inline shell scripts and direct expression expansion in workflow YAML.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from typing import Optional

GRID_ALLOWED = {"sl", "os"}
VARIANT_ALLOWED = {"regular", "avx"}
RELEASE_TYPES_ALLOWED = {
    "Release",
    "Beta",
    "Alpha",
    "Nightly",
    "Manual",
    "Profiling",
    "Unknown",
}

OS_MAP = {
    "Windows": "windows",
    "Linux": "linux",
    "macOS": "darwin",
    "MacOS": "darwin",
    "windows": "windows",
    "linux": "linux",
    "darwin": "darwin",
}


def export_variable(key: str, value: str) -> None:
    """Print variable and export to GITHUB_ENV and GITHUB_OUTPUT if set."""
    print(f"{key}={value}")

    env_file = os.getenv("GITHUB_ENV")
    if env_file:
        with open(env_file, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")

    output_file = os.getenv("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def test_llsd() -> None:
    try:
        import llsd  # type: ignore # noqa: F401

        print("Hello from extracted Python script testing llsd!")
    except ImportError as err:
        print(f"Failed to import llsd: {err}", file=sys.stderr)
        sys.exit(1)


def set_grid_flags(grid: str) -> None:
    grid = grid.strip().lower()
    if grid not in GRID_ALLOWED:
        raise ValueError(f"Invalid grid '{grid}'. Must be one of {GRID_ALLOWED}")

    opensim_flag = "ON" if grid == "os" else "OFF"
    havok_flag = "ON" if grid == "sl" else "OFF"
    fs_grid = f"-DOPENSIM:BOOL={opensim_flag} -DHAVOK_TPV:BOOL={havok_flag}"

    export_variable("FS_GRID", fs_grid)


def find_channel(
    ref_name: str,
    event_name: str,
    include_tracy: str = "false",
    variant: str = "regular",
) -> None:
    ref_name = ref_name.strip()
    event_name = event_name.strip()
    tracy = str(include_tracy).strip().lower() in ("true", "1", "yes")
    var = variant.strip().lower()

    fs_release_type = "Unknown"

    if ref_name.startswith("Firestorm"):
        fs_release_type = "Release"
    elif "review" in ref_name:
        fs_release_type = "Beta"
    elif "alpha" in ref_name:
        fs_release_type = "Alpha"
    elif "nightly" in ref_name or event_name == "schedule":
        fs_release_type = "Nightly"
    elif event_name == "workflow_dispatch":
        fs_release_type = "Profiling" if tracy else "Manual"

    if var == "avx":
        fs_release_chan = f"{fs_release_type}x64"
    else:
        fs_release_chan = fs_release_type

    print(f"Building for channel {fs_release_chan}")
    export_variable("FS_RELEASE_TYPE", fs_release_type)
    export_variable("FS_RELEASE_CHAN", fs_release_chan)
    export_variable("viewer_channel", fs_release_chan)


def check_codesigning(runner_os: str, release_type: str) -> None:
    runner_os_clean = runner_os.strip()
    release_type_clean = release_type.strip()

    enabled = (
        runner_os_clean.lower() == "windows"
        and release_type_clean in ("Release", "Beta")
    )
    flag_str = "true" if enabled else "false"

    export_variable("CODESIGNING_ENABLED", flag_str)
    print(f"Codesigning enabled: {flag_str}")


def define_platform(runner_os: str, addrsize: str = "64") -> None:
    clean_os = runner_os.strip()
    if clean_os not in OS_MAP:
        raise ValueError(f"Unknown runner OS '{runner_os}'. Expected one of {list(OS_MAP.keys())}")

    fallback = OS_MAP[clean_os]
    platform = f"{fallback}{addrsize.strip()}"

    export_variable("fallback_platform", fallback)
    export_variable("platform", platform)


def find_most_recent_bundle(workspace: str, package: str, platform_str: str) -> Optional[str]:
    pattern = re.compile(rf"^{re.escape(package)}-.*{re.escape(platform_str)}[-_]+.*")
    matching_files = []

    try:
        entries = os.listdir(workspace)
    except FileNotFoundError:
        return None

    for entry in entries:
        if pattern.match(entry):
            full_path = os.path.join(workspace, entry)
            if os.path.isfile(full_path):
                matching_files.append((os.path.getmtime(full_path), entry))

    if not matching_files:
        return None

    matching_files.sort(key=lambda x: x[0], reverse=True)
    return matching_files[0][1]


def test_macos_bundles(workspace: str) -> None:
    pattern = os.path.join(workspace, "*")
    matching = glob.glob(pattern)
    print(f"Directory listing for workspace ({workspace}):")
    for item in matching:
        print(f"  {item}")


def edit_installables(
    workspace: str,
    runner_os: str,
    platform: str,
    fallback_platform: str,
    autobuild_cmd: str = "autobuild",
) -> None:
    path_sep = "\\" if runner_os.strip().lower() == "windows" else "/"
    packages = ["fmodstudio", "llphysicsextensions_tpv", "kdu"]

    for package in packages:
        package_file = find_most_recent_bundle(workspace, package, platform)
        chosen_platform = platform

        if not package_file:
            print(f"No bundle found for {package} on {platform}")
            package_file = find_most_recent_bundle(workspace, package, fallback_platform)
            chosen_platform = fallback_platform

        if package_file:
            full_package_path = f"{workspace}{path_sep}{package_file}"
            print(f"Installing {package_file} for platform {chosen_platform}")
            subprocess.run([autobuild_cmd, "installables", "remove", package], check=False)
            subprocess.run(
                [
                    autobuild_cmd,
                    "installables",
                    "add",
                    package,
                    f"platform={chosen_platform}",
                    f"url=file:///{full_package_path}",
                ],
                check=False,
            )
        else:
            print(f"No bundle found for {package} on {fallback_platform}. Package will not be available for build.")


def set_expiry_args(release_type: str, current_extra_args: str) -> None:
    rel_type = release_type.strip()
    expire_days = ""

    if rel_type in ("Nightly", "Manual", "Profiling", "Alpha"):
        expire_days = "14"
    elif rel_type == "Beta":
        expire_days = "28"

    if expire_days:
        print(f"This {rel_type} build will expire in {expire_days} days.")
        new_extra = f"{current_extra_args.strip()} --testbuild={expire_days}".strip()
    else:
        print(f"This {rel_type} has no built in expiry.")
        new_extra = current_extra_args.strip()

    export_variable("EXTRA_ARGS", new_extra)


def add_custom_ua(custom_ua: str, current_extra_args: str) -> None:
    ua = custom_ua.strip()
    if ua:
        print("Building with custom user-agent string.")
        new_extra = f'{current_extra_args.strip()} -DFS_PF_USER_AGENT="{ua}"'.strip()
    else:
        print("No custom user-agent string provided.")
        new_extra = current_extra_args.strip()

    export_variable("EXTRA_ARGS", new_extra)


def extract_version(
    version_file: str = "indra/newview/VIEWER_VERSION.txt",
    release_chan: str = "",
    release_type: str = "",
) -> None:
    viewer_version = "0.0.0"
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as f:
            viewer_version = f.read().strip()

    viewer_build = "0"
    try:
        res = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            viewer_build = res.stdout.strip()
    except Exception as exc:
        print(f"Warning: Failed to retrieve git commit count: {exc}", file=sys.stderr)

    export_variable("viewer_version", viewer_version)
    export_variable("viewer_build", viewer_build)
    export_variable("viewer_channel", release_chan)
    export_variable("viewer_release_type", release_type)


def resolve_deploy_env(
    release_type: str,
    event_name: str = "",
    release_webhook: str = "",
    beta_webhook: str = "",
    nightly_webhook: str = "",
    manual_webhook: str = "",
) -> None:
    rel_type = release_type.strip()
    evt = event_name.strip()

    if rel_type == "Release":
        release_folder = "release"
        webhook_url = release_webhook
    elif rel_type == "Beta":
        release_folder = "preview"
        webhook_url = beta_webhook
    elif rel_type == "Alpha":
        release_folder = "test"
        webhook_url = beta_webhook
    elif rel_type == "Nightly" or evt == "schedule":
        release_folder = "nightly"
        webhook_url = nightly_webhook
    elif rel_type == "Manual":
        release_folder = "test"
        webhook_url = manual_webhook
    else:
        release_folder = "test"
        webhook_url = ""

    export_variable("FS_RELEASE_FOLDER", release_folder)
    export_variable("FS_BUILD_WEBHOOK_URL", webhook_url)


def create_build_info(
    run_number: str,
    release_type: str,
    viewer_version: str,
    viewer_build: str,
    output_file: str = "build_info.json",
) -> None:
    info = {
        "build_run_number": str(run_number).strip(),
        "release_type": str(release_type).strip(),
        "viewer_version": str(viewer_version).strip(),
        "viewer_build": str(viewer_build).strip(),
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)

    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        print(f"Build info created: {content.strip()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Firestorm build pipeline helper functions.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("test_llsd", help="Test importing llsd.")

    p_grid = subparsers.add_parser("set_grid_flags", help="Set FS_GRID flags.")
    p_grid.add_argument("--grid", help="Target grid (sl or os).")

    p_chan = subparsers.add_parser("find_channel", help="Resolve channel and release type.")
    p_chan.add_argument("--ref-name", help="GitHub ref name.")
    p_chan.add_argument("--event-name", help="GitHub event name.")
    p_chan.add_argument("--include-tracy", default="false", help="Tracy profiling flag.")
    p_chan.add_argument("--variant", default="regular", help="Build variant.")

    p_sign = subparsers.add_parser("check_codesigning", help="Check if codesigning is enabled.")
    p_sign.add_argument("--runner-os", help="Runner OS.")
    p_sign.add_argument("--release-type", help="FS release type.")

    p_plat = subparsers.add_parser("define_platform", help="Define platform environment variables.")
    p_plat.add_argument("--runner-os", help="Runner OS.")
    p_plat.add_argument("--addrsize", default="64", help="Architecture address size.")

    p_mac = subparsers.add_parser("test_macos_bundles", help="List macOS bundle directory contents.")
    p_mac.add_argument("--workspace", help="Workspace path.")

    p_inst = subparsers.add_parser("edit_installables", help="Configure autobuild installables.")
    p_inst.add_argument("--workspace", help="Workspace path.")
    p_inst.add_argument("--runner-os", help="Runner OS.")
    p_inst.add_argument("--platform", help="Target platform.")
    p_inst.add_argument("--fallback-platform", help="Fallback platform.")

    p_exp = subparsers.add_parser("set_expiry_args", help="Set build expiration flags.")
    p_exp.add_argument("--release-type", help="FS release type.")
    p_exp.add_argument("--extra-args", default="", help="Current EXTRA_ARGS.")

    p_ua = subparsers.add_parser("add_custom_ua", help="Add custom user agent string.")
    p_ua.add_argument("--custom-ua", default="", help="Custom user-agent string.")
    p_ua.add_argument("--extra-args", default="", help="Current EXTRA_ARGS.")

    p_ver = subparsers.add_parser("extract_version", help="Extract viewer version and build number.")
    p_ver.add_argument("--version-file", default="indra/newview/VIEWER_VERSION.txt", help="Path to version file.")
    p_ver.add_argument("--release-chan", default="", help="Release channel.")
    p_ver.add_argument("--release-type", default="", help="Release type.")

    p_dep = subparsers.add_parser("resolve_deploy_env", help="Resolve deployment folder and webhook URL.")
    p_dep.add_argument("--release-type", help="Release type.")
    p_dep.add_argument("--event-name", default="", help="Event name.")

    p_info = subparsers.add_parser("create_build_info", help="Create build_info.json file.")
    p_info.add_argument("--run-number", help="GitHub run number.")
    p_info.add_argument("--release-type", help="Release type.")
    p_info.add_argument("--viewer-version", help="Viewer version.")
    p_info.add_argument("--viewer-build", help="Viewer build number.")

    args = parser.parse_args()

    try:
        if args.command == "test_llsd":
            test_llsd()
        elif args.command == "set_grid_flags":
            grid = args.grid or os.getenv("GRID") or ""
            set_grid_flags(grid)
        elif args.command == "find_channel":
            ref_name = args.ref_name or os.getenv("GITHUB_REF_NAME") or ""
            event_name = args.event_name or os.getenv("GITHUB_EVENT_NAME") or ""
            include_tracy = args.include_tracy or os.getenv("INCLUDE_TRACY") or "false"
            variant = args.variant or os.getenv("VARIANT") or "regular"
            find_channel(ref_name, event_name, include_tracy, variant)
        elif args.command == "check_codesigning":
            runner_os = args.runner_os or os.getenv("RUNNER_OS") or ""
            release_type = args.release_type or os.getenv("FS_RELEASE_TYPE") or ""
            check_codesigning(runner_os, release_type)
        elif args.command == "define_platform":
            runner_os = args.runner_os or os.getenv("RUNNER_OS") or ""
            addrsize = args.addrsize or os.getenv("ADDRSIZE", "64")
            define_platform(runner_os, addrsize)
        elif args.command == "test_macos_bundles":
            workspace = args.workspace or os.getenv("GITHUB_WORKSPACE") or "."
            test_macos_bundles(workspace)
        elif args.command == "edit_installables":
            workspace = args.workspace or os.getenv("GITHUB_WORKSPACE") or "."
            runner_os = args.runner_os or os.getenv("RUNNER_OS") or ""
            platform = args.platform or os.getenv("PLATFORM") or ""
            fallback_platform = args.fallback_platform or os.getenv("FALLBACK_PLATFORM") or ""
            edit_installables(workspace, runner_os, platform, fallback_platform)
        elif args.command == "set_expiry_args":
            release_type = args.release_type or os.getenv("FS_RELEASE_TYPE") or ""
            extra_args = args.extra_args or os.getenv("EXTRA_ARGS") or ""
            set_expiry_args(release_type, extra_args)
        elif args.command == "add_custom_ua":
            custom_ua = args.custom_ua or os.getenv("FS_PF_UA") or ""
            extra_args = args.extra_args or os.getenv("EXTRA_ARGS") or ""
            add_custom_ua(custom_ua, extra_args)
        elif args.command == "extract_version":
            version_file = args.version_file or os.getenv("VERSION_FILE", "indra/newview/VIEWER_VERSION.txt")
            release_chan = args.release_chan or os.getenv("FS_RELEASE_CHAN") or ""
            release_type = args.release_type or os.getenv("FS_RELEASE_TYPE") or ""
            extract_version(version_file, release_chan, release_type)
        elif args.command == "resolve_deploy_env":
            release_type = args.release_type or os.getenv("VIEWER_RELEASE_TYPE") or os.getenv("FS_RELEASE_TYPE") or ""
            event_name = args.event_name or os.getenv("GITHUB_EVENT_NAME") or ""
            release_webhook = os.getenv("RELEASE_WEBHOOK_URL", "")
            beta_webhook = os.getenv("BETA_WEBHOOK_URL", "")
            nightly_webhook = os.getenv("NIGHTLY_WEBHOOK_URL", "")
            manual_webhook = os.getenv("MANUAL_WEBHOOK_URL", "")
            resolve_deploy_env(release_type, event_name, release_webhook, beta_webhook, nightly_webhook, manual_webhook)
        elif args.command == "create_build_info":
            run_number = args.run_number or os.getenv("GITHUB_RUN_NUMBER") or ""
            release_type = args.release_type or os.getenv("VIEWER_RELEASE_TYPE") or ""
            viewer_version = args.viewer_version or os.getenv("VIEWER_VERSION") or ""
            viewer_build = args.viewer_build or os.getenv("VIEWER_BUILD") or ""
            create_build_info(run_number, release_type, viewer_version, viewer_build)
    except Exception as exc:
        print(f"Error in build_utils ({args.command}): {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
