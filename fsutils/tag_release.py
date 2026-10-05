#!/usr/bin/env python3
"""
tag_release.py

Creates GitHub release tags using the GitHub REST API cleanly and safely,
replacing inline JavaScript actions and workflow expression expansions.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+$")
SHA_REGEX = re.compile(r"^[a-fA-F0-9]{7,40}$")
TAG_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.\#\/]+$")


def validate_repo(repo_str: str) -> str:
    repo_str = repo_str.strip()
    if not REPO_REGEX.match(repo_str):
        raise ValueError(f"Invalid repository format '{repo_str}'. Expected 'owner/repo'.")
    return repo_str


def validate_sha(sha_str: str) -> str:
    sha_str = sha_str.strip()
    if not SHA_REGEX.match(sha_str):
        raise ValueError(f"Invalid commit SHA '{sha_str}'. Must be 7-40 hex characters.")
    return sha_str


def validate_tag_name(tag_name: str) -> str:
    tag_name = tag_name.strip()
    if not tag_name or not TAG_NAME_REGEX.match(tag_name):
        raise ValueError(f"Invalid tag name '{tag_name}'. Must contain only alphanumeric, '-', '_', '.', '#', '/'.")
    return tag_name


def create_git_ref(
    repo: str,
    tag_name: str,
    sha: str,
    token: str,
    api_url: str = "https://api.github.com",
) -> dict:
    repo = validate_repo(repo)
    tag_name = validate_tag_name(tag_name)
    sha = validate_sha(sha)

    if not token or not token.strip():
        raise ValueError("GitHub API token must be provided.")

    ref_str = f"refs/tags/{tag_name}" if not tag_name.startswith("refs/") else tag_name
    url = f"{api_url.rstrip('/')}/repos/{repo}/git/refs"
    payload = json.dumps({"ref": ref_str, "sha": sha}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"token {token.strip()}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "fsutils-tag-release",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"Successfully created git ref '{ref_str}' for SHA '{sha}' in '{repo}'.")
            return data
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed ({err.code}): {error_body}") from err


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Git tag reference via GitHub REST API.")
    parser.add_argument("--repo", help="Target repository in owner/repo format.")
    parser.add_argument("--tag-name", help="Tag name (e.g. Second_Life_Test#sha-project).")
    parser.add_argument("--sha", help="Commit SHA to tag.")
    parser.add_argument("--token", help="GitHub authentication token.")

    args = parser.parse_args()

    repo = args.repo or os.getenv("GITHUB_REPOSITORY") or ""
    channel = os.getenv("VIEWER_CHANNEL") or ""
    tag_id = os.getenv("TAG_ID") or ""
    tag_name = args.tag_name or os.getenv("TAG_NAME") or (f"{channel}#{tag_id}" if channel and tag_id else "")
    sha = args.sha or os.getenv("COMMIT_SHA") or os.getenv("GITHUB_SHA") or ""
    token = args.token or os.getenv("GITHUB_TOKEN") or os.getenv("LL_TAG_RELEASE_TOKEN") or ""

    try:
        create_git_ref(repo=repo, tag_name=tag_name, sha=sha, token=token)
    except Exception as exc:
        print(f"Error creating tag reference: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
