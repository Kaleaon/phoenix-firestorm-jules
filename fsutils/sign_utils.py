#!/usr/bin/env python3
"""
sign_utils.py

Helper script for signing workflows in GitHub Actions.
Extracts artifact file collecting, run artifact querying, and signing file preparation.
"""

import argparse
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request

FILENAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
RUN_ID_REGEX = re.compile(r"^\d+$")
REPO_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+$")


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


def validate_filename(filename: str) -> str:
    raw_filename = str(filename).strip()
    if ".." in raw_filename:
        raise ValueError(f"Invalid filename '{filename}'. Path traversal ('..') not allowed.")
    basename = os.path.basename(raw_filename)
    if not basename or not FILENAME_REGEX.match(basename):
        raise ValueError(
            f"Invalid filename '{filename}'. Must be a safe basename without special characters."
        )
    return basename


def validate_repo(repo_str: str) -> str:
    repo_str = str(repo_str).strip()
    if not REPO_REGEX.match(repo_str):
        raise ValueError(f"Invalid repository format '{repo_str}'. Expected 'owner/repo'.")
    return repo_str


def validate_run_id(run_id_str: str) -> str:
    run_id_str = str(run_id_str).strip()
    if not RUN_ID_REGEX.match(run_id_str):
        raise ValueError(f"Invalid run ID '{run_id_str}'. Must be numeric.")
    return run_id_str


def handle_get_setup_files(artifacts_dir: str = "artifacts", output_dir: str = "setup_exe_files") -> None:
    os.makedirs(output_dir, exist_ok=True)
    setup_files = []

    if os.path.exists(artifacts_dir):
        for root, _, files in os.walk(artifacts_dir):
            for file in files:
                if file.endswith("Setup.exe"):
                    safe_name = validate_filename(file)
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join(output_dir, safe_name)
                    shutil.copy2(src_path, dst_path)
                    setup_files.append(safe_name)

    files_json = json.dumps(setup_files)
    export_variable("setup_files", files_json)


def handle_list_run_artifacts(repo: str, run_id: str, token: str, api_url: str = "https://api.github.com") -> None:
    validated_repo = validate_repo(repo)
    validated_run_id = validate_run_id(run_id)

    if not token or not token.strip():
        raise ValueError("GitHub API token must be provided.")

    url = f"{api_url.rstrip('/')}/repos/{validated_repo}/actions/runs/{validated_run_id}/artifacts"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {token.strip()}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "fsutils-sign-utils",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("Available artifacts:")
            print(json.dumps(data, indent=2))
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Failed to query run artifacts ({err.code}): {error_body}") from err


def handle_prepare_file(filename: str, source_dir: str = "setup_exe_files", target_dir: str = "to_sign") -> None:
    safe_filename = validate_filename(filename)
    os.makedirs(target_dir, exist_ok=True)

    src_path = os.path.join(source_dir, safe_filename)
    dst_path = os.path.join(target_dir, safe_filename)

    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Source file '{src_path}' does not exist.")

    shutil.copy2(src_path, dst_path)
    print(f"Copied '{src_path}' to '{dst_path}' successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Signing process helper utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_get = subparsers.add_parser("get_setup_files", help="Find and list setup.exe files.")
    p_get.add_argument("--artifacts-dir", default="artifacts", help="Artifacts directory.")
    p_get.add_argument("--output-dir", default="setup_exe_files", help="Output directory for setup files.")

    p_list = subparsers.add_parser("list_run_artifacts", help="List GitHub Actions run artifacts.")
    p_list.add_argument("--repo", help="Target repo (owner/repo).")
    p_list.add_argument("--run-id", help="GitHub run ID.")
    p_list.add_argument("--token", help="GitHub API token.")

    p_prep = subparsers.add_parser("prepare_file", help="Prepare file for signing.")
    p_prep.add_argument("--filename", help="Filename to prepare for signing.")
    p_prep.add_argument("--source-dir", default="setup_exe_files", help="Source directory.")
    p_prep.add_argument("--target-dir", default="to_sign", help="Target directory.")

    args = parser.parse_args()

    try:
        if args.command == "get_setup_files":
            handle_get_setup_files(args.artifacts_dir, args.output_dir)
        elif args.command == "list_run_artifacts":
            repo = args.repo or os.getenv("GITHUB_REPOSITORY") or ""
            run_id = args.run_id or os.getenv("GITHUB_RUN_ID") or ""
            token = args.token or os.getenv("GITHUB_TOKEN") or ""
            handle_list_run_artifacts(repo, run_id, token)
        elif args.command == "prepare_file":
            filename = args.filename or os.getenv("FILENAME") or os.getenv("MATRIX_FILE") or ""
            handle_prepare_file(filename, args.source_dir, args.target_dir)
    except Exception as exc:
        print(f"Error in sign_utils ({args.command}): {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
