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
manage_tags.py

CLI utility to inspect, create, push, and verify Git tags for Firestorm builds safely,
eliminating inline shell scripts and direct expression expansion in workflow YAML.
"""

import argparse
import os
import re
import subprocess
import sys

# Pattern for Firestorm build tags or standard git tags
TAG_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.\#\/]+$")


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


def validate_tag_name(tag_name: str) -> str:
    tag_name = str(tag_name).strip()
    if not tag_name or not TAG_REGEX.match(tag_name):
        raise ValueError(
            f"Invalid tag name '{tag_name}'. Must contain only alphanumeric characters, '-', '_', '.', '#', '/'"
        )
    return tag_name


def validate_dry_run(dry_run_val: str) -> bool:
    dry_run_str = str(dry_run_val).strip().lower()
    if dry_run_str in ("true", "1", "yes"):
        return True
    if dry_run_str in ("false", "0", "no"):
        return False
    raise ValueError(f"Invalid dry_run value '{dry_run_val}'. Must be boolean true/false.")


def handle_determine(tag_name: str) -> None:
    validated_tag = validate_tag_name(tag_name)
    print(f"Proposed Tag: {validated_tag}")
    export_variable("tag_name", validated_tag)


def handle_check(tag_name: str) -> bool:
    validated_tag = validate_tag_name(tag_name)
    try:
        res = subprocess.run(
            ["git", "rev-parse", validated_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        exists = res.returncode == 0
    except Exception as exc:
        raise RuntimeError(f"Error checking git tag '{validated_tag}': {exc}") from exc

    if exists:
        print(f"Tag {validated_tag} already exists.")
        export_variable("tag_exists", "true")
    else:
        print(f"Tag {validated_tag} does not exist.")
        export_variable("tag_exists", "false")

    return exists


def handle_create(tag_name: str, dry_run: str = "false") -> None:
    validated_tag = validate_tag_name(tag_name)
    is_dry = validate_dry_run(dry_run)

    if is_dry:
        print(f"Dry run mode enabled. Tag '{validated_tag}' was not created.")
        return

    print(f"Creating tag: {validated_tag}")
    res = subprocess.run(["git", "tag", validated_tag], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to create tag '{validated_tag}': {res.stderr.strip()}")


def handle_push(tag_name: str, remote: str = "origin", dry_run: str = "false") -> None:
    validated_tag = validate_tag_name(tag_name)
    is_dry = validate_dry_run(dry_run)

    if is_dry:
        print(f"Dry run mode enabled. Tag '{validated_tag}' was not pushed.")
        return

    print(f"Pushing tag '{validated_tag}' to '{remote}'...")
    res = subprocess.run(["git", "push", remote, validated_tag], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to push tag '{validated_tag}': {res.stderr.strip()}")


def handle_confirm(tag_name: str, tag_exists: str, dry_run: str) -> None:
    is_dry = validate_dry_run(dry_run)
    exists = str(tag_exists).strip().lower() in ("true", "1", "yes")

    if is_dry:
        print(f"Dry run mode enabled. Tag '{tag_name}' was not created or pushed.")
    elif exists:
        print(f"Tag '{tag_name}' already exists. No new tag was created.")
    else:
        print(f"Tag '{tag_name}' has been created and pushed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Git tag management utilities for release workflows.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_determine = subparsers.add_parser("determine", help="Determine and export tag name.")
    p_determine.add_argument("--tag-name", help="Proposed tag name.")

    p_check = subparsers.add_parser("check", help="Check if git tag exists.")
    p_check.add_argument("--tag-name", help="Tag name to check.")

    p_create = subparsers.add_parser("create", help="Create a local git tag.")
    p_create.add_argument("--tag-name", help="Tag name to create.")
    p_create.add_argument("--dry-run", default="false", help="Dry run flag.")

    p_push = subparsers.add_parser("push", help="Push git tag to remote.")
    p_push.add_argument("--tag-name", help="Tag name to push.")
    p_push.add_argument("--remote", default="origin", help="Git remote name.")
    p_push.add_argument("--dry-run", default="false", help="Dry run flag.")

    p_confirm = subparsers.add_parser("confirm", help="Print tagging confirmation status.")
    p_confirm.add_argument("--tag-name", help="Tag name.")
    p_confirm.add_argument("--tag-exists", default="false", help="Whether tag already existed.")
    p_confirm.add_argument("--dry-run", default="false", help="Dry run flag.")

    args = parser.parse_args()

    try:
        if args.command == "determine":
            tag_name = args.tag_name or os.getenv("TAG_NAME") or ""
            handle_determine(tag_name)
        elif args.command == "check":
            tag_name = args.tag_name or os.getenv("TAG_NAME") or ""
            handle_check(tag_name)
        elif args.command == "create":
            tag_name = args.tag_name or os.getenv("TAG_NAME") or ""
            dry_run = args.dry_run if args.dry_run != "false" else os.getenv("DRY_RUN", "false")
            handle_create(tag_name, dry_run)
        elif args.command == "push":
            tag_name = args.tag_name or os.getenv("TAG_NAME") or ""
            dry_run = args.dry_run if args.dry_run != "false" else os.getenv("DRY_RUN", "false")
            remote = args.remote or os.getenv("GIT_REMOTE", "origin")
            handle_push(tag_name, remote, dry_run)
        elif args.command == "confirm":
            tag_name = args.tag_name or os.getenv("TAG_NAME") or ""
            tag_exists = args.tag_exists if args.tag_exists != "false" else os.getenv("TAG_EXISTS", "false")
            dry_run = args.dry_run if args.dry_run != "false" else os.getenv("DRY_RUN", "false")
            handle_confirm(tag_name, tag_exists, dry_run)
    except Exception as exc:
        print(f"Error in tag management ({args.command}): {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
