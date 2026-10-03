#!/usr/bin/env python3
"""
parse_workflow_inputs.py

Helper script for parsing, validating, and defaulting GitHub Action workflow inputs safely
to eliminate shell injection risks in release workflows.
"""

import argparse
import datetime
import json
import os
import re
import sys
from typing import Set

# Regex constants for strict input validation
VERSION_REGEX = re.compile(r"^\d+\.\d+\.\d+$")
BUILD_NUMBER_REGEX = re.compile(r"^\d+$")
IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")
SHA_REGEX = re.compile(r"^[a-fA-F0-9]{7,40}$")

ALLOWED_RELEASE_TYPES: Set[str] = {
    "Release",
    "Beta",
    "Alpha",
    "Nightly",
    "Manual",
    "Profiling",
    "Test",
    "undefined",
}

ALLOWED_CHANNELS: Set[str] = {
    "Test",
    "Develop",
    "Project",
    "Release",
}


def validate_version(version_str: str) -> str:
    """Validate version string format (e.g. '7.1.10')."""
    version_str = str(version_str)
    if version_str != version_str.strip() or not VERSION_REGEX.match(version_str):
        raise ValueError(
            f"Invalid viewer version '{version_str}'. Must match pattern '\\d+\\.\\d+\\.\\d+'."
        )
    return version_str


def validate_build_number(build_str: str) -> str:
    """Validate build number or run number format (e.g. '799999')."""
    build_str = str(build_str)
    if build_str != build_str.strip() or not BUILD_NUMBER_REGEX.match(build_str):
        raise ValueError(
            f"Invalid build/run number '{build_str}'. Must be a numeric string."
        )
    return build_str


def validate_release_type(release_type_str: str) -> str:
    """Validate release type string against allowed values or alphanumeric identifier."""
    release_type_str = str(release_type_str)
    if release_type_str != release_type_str.strip() or (
        release_type_str not in ALLOWED_RELEASE_TYPES
        and not IDENTIFIER_REGEX.match(release_type_str)
    ):
        raise ValueError(
            f"Invalid release type '{release_type_str}'. Must be alphanumeric with hyphens/underscores."
        )
    return release_type_str


def validate_channel(channel_str: str) -> str:
    """Validate channel string against allowed values."""
    channel_str = str(channel_str)
    if channel_str != channel_str.strip() or (
        channel_str not in ALLOWED_CHANNELS
        and not IDENTIFIER_REGEX.match(channel_str)
    ):
        raise ValueError(
            f"Invalid channel '{channel_str}'. Must be alphanumeric with hyphens/underscores."
        )
    return channel_str


def validate_project(project_str: str) -> str:
    """Validate project identifier string."""
    project_str = str(project_str)
    if project_str != project_str.strip() or not IDENTIFIER_REGEX.match(project_str):
        raise ValueError(
            f"Invalid project name '{project_str}'. Must match pattern '^[a-zA-Z0-9_\\-]+$'."
        )
    return project_str


def validate_sha(sha_str: str) -> str:
    """Validate git SHA string."""
    sha_str = str(sha_str)
    if sha_str != sha_str.strip() or not SHA_REGEX.match(sha_str):
        raise ValueError(
            f"Invalid git SHA '{sha_str}'. Must be 7 to 40 hex characters."
        )
    return sha_str


def validate_dry_run(dry_run_str: str) -> str:
    """Validate and normalize dry_run string representation."""
    dry_run_str_raw = str(dry_run_str)
    if dry_run_str_raw != dry_run_str_raw.strip():
        raise ValueError(
            f"Invalid dry_run setting '{dry_run_str}'. Leading or trailing whitespace not allowed."
        )
    dry_run_str_lower = dry_run_str_raw.lower()
    if dry_run_str_lower in ("true", "1", "yes"):
        return "true"
    if dry_run_str_lower in ("false", "0", "no"):
        return "false"
    raise ValueError(
        f"Invalid dry_run setting '{dry_run_str}'. Must be boolean true/false."
    )


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


def handle_deploy() -> None:
    """Handle deployment environment resolution and validation."""
    viewer_release_type = (
        os.getenv("VIEWER_RELEASE_TYPE")
        or os.getenv("INPUT_VIEWER_RELEASE_TYPE")
        or os.getenv("RELEASE_TYPE")
        or "Release"
    )
    event_name = os.getenv("EVENT_NAME", "").strip()

    validated_release_type = validate_release_type(viewer_release_type)

    # Optional version / build validations if provided
    viewer_version = os.getenv("VIEWER_VERSION")
    if viewer_version and viewer_version != "undefined":
        export_variable("FS_VIEWER_VERSION", validate_version(viewer_version))

    viewer_build = os.getenv("VIEWER_BUILD")
    if viewer_build and viewer_build != "undefined":
        export_variable(
            "FS_VIEWER_BUILD", validate_build_number(viewer_build)
        )

    build_run_number = os.getenv("BUILD_RUN_NUMBER")
    if build_run_number:
        export_variable(
            "BUILD_RUN_NUMBER", validate_build_number(build_run_number)
        )

    # Resolve deploy folder and webhook URL based on release type & event
    release_webhook_url = os.getenv("RELEASE_WEBHOOK_URL", "")
    beta_webhook_url = os.getenv("BETA_WEBHOOK_URL", "")
    nightly_webhook_url = os.getenv("NIGHTLY_WEBHOOK_URL", "")
    manual_webhook_url = os.getenv("MANUAL_WEBHOOK_URL", "")

    if validated_release_type == "Nightly" or event_name == "schedule":
        release_folder = "nightly"
        webhook_url = nightly_webhook_url
    elif validated_release_type == "Release":
        release_folder = "release"
        webhook_url = release_webhook_url
    elif validated_release_type == "Beta":
        release_folder = "preview"
        webhook_url = beta_webhook_url
    elif validated_release_type == "Alpha":
        release_folder = "test"
        webhook_url = beta_webhook_url
    elif validated_release_type == "Manual":
        release_folder = "test"
        webhook_url = manual_webhook_url
    else:
        raise ValueError(
            f"Unsupported release type for deployment: '{validated_release_type}'"
        )

    export_variable("FS_RELEASE_FOLDER", release_folder)
    export_variable("FS_BUILD_WEBHOOK_URL", webhook_url)


def handle_tag() -> None:
    """Handle release tag generation and validation."""
    # Check if channel-based release tagging (tag-release.yaml)
    input_channel = os.getenv("INPUT_CHANNEL") or os.getenv("CHANNEL")
    input_project = os.getenv("INPUT_PROJECT") or os.getenv("PROJECT")
    github_sha = os.getenv("GITHUB_SHA")

    # Check if building Firestorm tag (tag-fs-build.yml) vs channel tag
    build_info_file = os.getenv("BUILD_INFO_FILE", "build_info/build_info.json")

    is_channel_tag = (
        input_channel is not None
        or (github_sha is not None and not os.path.exists(build_info_file))
    )

    if is_channel_tag:
        channel = input_channel if input_channel else "Develop"
        validated_channel = validate_channel(channel)
        viewer_channel = f"Second_Life_{validated_channel}"

        nightly_date = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d"
        )

        short_sha = validate_sha(github_sha)[:8] if github_sha else "00000000"

        if input_project and input_project.strip() and input_project != "${NIGHTLY_DATE}":
            project_suffix = validate_project(input_project)
        else:
            project_suffix = nightly_date

        tag_id = f"{short_sha}-{project_suffix}"
        tag_name = f"{viewer_channel}#{tag_id}"

        export_variable("VIEWER_CHANNEL", viewer_channel)
        export_variable("NIGHTLY_DATE", nightly_date)
        export_variable("TAG_ID", tag_id)
        export_variable("tag_name", tag_name)
        export_variable("TAG_NAME", tag_name)

    else:
        # Firestorm build tag logic
        release_type = "undefined"
        viewer_version = "undefined"
        viewer_build = "undefined"
        dry_run = "false"

        if os.path.exists(build_info_file):
            with open(build_info_file, "r", encoding="utf-8") as f:
                build_info = json.load(f)
                release_type = build_info.get("release_type", "undefined")
                viewer_version = build_info.get("viewer_version", "undefined")
                viewer_build = build_info.get("viewer_build", "undefined")

        event_name = os.getenv("EVENT_NAME", "")
        if event_name == "workflow_dispatch":
            override_release_type = os.getenv("INPUT_RELEASE_TYPE") or os.getenv("RELEASE_TYPE")
            if override_release_type and override_release_type != "undefined":
                release_type = override_release_type

            override_version = os.getenv("INPUT_VIEWER_VERSION") or os.getenv("VIEWER_VERSION")
            if override_version and override_version != "undefined":
                viewer_version = override_version

            override_build = os.getenv("INPUT_VIEWER_BUILD") or os.getenv("VIEWER_BUILD")
            if override_build and override_build != "undefined":
                viewer_build = override_build

            override_dry_run = os.getenv("INPUT_DRY_RUN") or os.getenv("DRY_RUN")
            if override_dry_run:
                dry_run = override_dry_run

        validated_release_type = validate_release_type(release_type)
        validated_version = validate_version(viewer_version)
        validated_build = validate_build_number(viewer_build)
        validated_dry_run = validate_dry_run(dry_run)

        tag_name = f"Firestorm_{validated_release_type}_{validated_version}.{validated_build}"

        export_variable("release_type", validated_release_type)
        export_variable("viewer_version", validated_version)
        export_variable("viewer_build", validated_build)
        export_variable("dry_run", validated_dry_run)
        export_variable("tag_name", tag_name)

        export_variable("RELEASE_TYPE", validated_release_type)
        export_variable("VIEWER_VERSION", validated_version)
        export_variable("VIEWER_BUILD", validated_build)
        export_variable("DRY_RUN", validated_dry_run)
        export_variable("TAG_NAME", tag_name)


def handle_run_number() -> None:
    """Handle build run number resolution and validation."""
    event_name = os.getenv("EVENT_NAME", "")
    workflow_run_number = os.getenv("WORKFLOW_RUN_NUMBER", "").strip()
    input_build_run_number = (
        os.getenv("INPUT_BUILD_RUN_NUMBER")
        or os.getenv("BUILD_RUN_NUMBER")
        or ""
    ).strip()

    if event_name == "workflow_run" and workflow_run_number:
        run_number = workflow_run_number
    else:
        run_number = input_build_run_number

    validated_run_number = validate_build_number(run_number)
    export_variable("build_run_number", validated_run_number)
    export_variable("BUILD_RUN_NUMBER", validated_run_number)


def main() -> None:
    """Main entrypoint for workflow input parser."""
    parser = argparse.ArgumentParser(
        description="Parse and validate workflow dispatch inputs for release workflows."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    subparsers.add_parser(
        "deploy", help="Parse and validate deployment parameters."
    )
    subparsers.add_parser(
        "tag", help="Construct and validate release tag strings."
    )
    subparsers.add_parser(
        "run_number", help="Extract and validate workflow run numbers."
    )

    args = parser.parse_args()

    try:
        if args.mode == "deploy":
            handle_deploy()
        elif args.mode == "tag":
            handle_tag()
        elif args.mode == "run_number":
            handle_run_number()
    except Exception as exc:
        print(f"Error validating workflow inputs: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
