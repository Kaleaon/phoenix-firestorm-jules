"""
test_parse_workflow_inputs.py

Unit test suite for fsutils/parse_workflow_inputs.py validating input parsing,
string sanitization, and shell injection prevention.
"""

import json
import os
import pytest
import sys

# Add repository root to python path to import fsutils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fsutils.parse_workflow_inputs import (
    validate_version,
    validate_build_number,
    validate_release_type,
    validate_channel,
    validate_project,
    validate_sha,
    validate_dry_run,
    export_variable,
    handle_deploy,
    handle_tag,
    handle_run_number,
)


def test_validate_version_valid():
    assert validate_version("7.1.10") == "7.1.10"
    assert validate_version("0.0.1") == "0.0.1"
    assert validate_version("10.200.3000") == "10.200.3000"


@pytest.mark.parametrize(
    "invalid_version",
    [
        "7.1",
        "7.1.10.1",
        "7.1.10-beta",
        "7.1.10; rm -rf /",
        "7.1.10\n",
        "7.1.10$(id)",
        "`whoami`",
        "7.1.10 | cat",
    ],
)
def test_validate_version_invalid(invalid_version):
    with pytest.raises(ValueError):
        validate_version(invalid_version)


def test_validate_build_number_valid():
    assert validate_build_number("799999") == "799999"
    assert validate_build_number("0") == "0"
    assert validate_build_number(12345) == "12345"


@pytest.mark.parametrize(
    "invalid_build",
    [
        "799999a",
        "-5",
        "799999; calc",
        "799999\n",
        "$(whoami)",
        "12.3",
    ],
)
def test_validate_build_number_invalid(invalid_build):
    with pytest.raises(ValueError):
        validate_build_number(invalid_build)


def test_validate_release_type_valid():
    assert validate_release_type("Release") == "Release"
    assert validate_release_type("Beta") == "Beta"
    assert validate_release_type("Alpha") == "Alpha"
    assert validate_release_type("Nightly") == "Nightly"
    assert validate_release_type("Manual") == "Manual"
    assert validate_release_type("Custom-Release_1") == "Custom-Release_1"


@pytest.mark.parametrize(
    "invalid_release_type",
    [
        "Release; rm -rf /",
        "Beta && touch hacked",
        "Alpha$(whoami)",
        "Nightly\n",
        "Manual|ls",
        "Release' OR '1'='1",
    ],
)
def test_validate_release_type_invalid(invalid_release_type):
    with pytest.raises(ValueError):
        validate_release_type(invalid_release_type)


def test_validate_channel_valid():
    assert validate_channel("Test") == "Test"
    assert validate_channel("Develop") == "Develop"
    assert validate_channel("Project") == "Project"
    assert validate_channel("Release") == "Release"


@pytest.mark.parametrize(
    "invalid_channel",
    [
        "Develop; reboot",
        "Test$(id)",
        "Release\n",
        "Project/../../etc",
    ],
)
def test_validate_channel_invalid(invalid_channel):
    with pytest.raises(ValueError):
        validate_channel(invalid_channel)


def test_validate_project_valid():
    assert validate_project("hippo") == "hippo"
    assert validate_project("my-project_v2") == "my-project_v2"


@pytest.mark.parametrize(
    "invalid_project",
    [
        "hippo; calc",
        "project$(whoami)",
        "proj/path",
        "proj name",
    ],
)
def test_validate_project_invalid(invalid_project):
    with pytest.raises(ValueError):
        validate_project(invalid_project)


def test_validate_sha_valid():
    sha = "1234567890abcdef1234567890abcdef12345678"
    assert validate_sha(sha) == sha
    assert validate_sha("1234567") == "1234567"


@pytest.mark.parametrize(
    "invalid_sha",
    [
        "123456",  # too short
        "1234567890abcdef1234567890abcdef123456789",  # too long (41)
        "1234567890abcdef1234567890abcdef1234567g",  # non-hex char 'g'
        "12345678; rm -rf /",
    ],
)
def test_validate_sha_invalid(invalid_sha):
    with pytest.raises(ValueError):
        validate_sha(invalid_sha)


def test_validate_dry_run_valid():
    assert validate_dry_run("true") == "true"
    assert validate_dry_run("TRUE") == "true"
    assert validate_dry_run("false") == "false"
    assert validate_dry_run("1") == "true"
    assert validate_dry_run("0") == "false"


def test_validate_dry_run_invalid():
    with pytest.raises(ValueError):
        validate_dry_run("maybe")
    with pytest.raises(ValueError):
        validate_dry_run("true; echo bad")


def test_export_variable(tmp_path, monkeypatch):
    env_file = tmp_path / "env.txt"
    output_file = tmp_path / "output.txt"

    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    export_variable("TEST_KEY", "TEST_VAL")

    assert env_file.read_text(encoding="utf-8") == "TEST_KEY=TEST_VAL\n"
    assert output_file.read_text(encoding="utf-8") == "TEST_KEY=TEST_VAL\n"


def test_handle_deploy_release(tmp_path, monkeypatch):
    env_file = tmp_path / "env.txt"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("VIEWER_RELEASE_TYPE", "Release")
    monkeypatch.setenv("RELEASE_WEBHOOK_URL", "https://hooks.discord.com/release")

    handle_deploy()

    content = env_file.read_text(encoding="utf-8")
    assert "FS_RELEASE_FOLDER=release\n" in content
    assert "FS_BUILD_WEBHOOK_URL=https://hooks.discord.com/release\n" in content


def test_handle_deploy_beta(tmp_path, monkeypatch):
    env_file = tmp_path / "env.txt"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("VIEWER_RELEASE_TYPE", "Beta")
    monkeypatch.setenv("BETA_WEBHOOK_URL", "https://hooks.discord.com/beta")

    handle_deploy()

    content = env_file.read_text(encoding="utf-8")
    assert "FS_RELEASE_FOLDER=preview\n" in content
    assert "FS_BUILD_WEBHOOK_URL=https://hooks.discord.com/beta\n" in content


def test_handle_deploy_nightly_schedule(tmp_path, monkeypatch):
    env_file = tmp_path / "env.txt"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("EVENT_NAME", "schedule")
    monkeypatch.setenv("NIGHTLY_WEBHOOK_URL", "https://hooks.discord.com/nightly")

    handle_deploy()

    content = env_file.read_text(encoding="utf-8")
    assert "FS_RELEASE_FOLDER=nightly\n" in content
    assert "FS_BUILD_WEBHOOK_URL=https://hooks.discord.com/nightly\n" in content


def test_handle_deploy_injection_attempt(monkeypatch):
    monkeypatch.setenv("VIEWER_RELEASE_TYPE", "Release; rm -rf /")
    with pytest.raises(ValueError):
        handle_deploy()


def test_handle_tag_channel_mode(tmp_path, monkeypatch):
    env_file = tmp_path / "env.txt"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("INPUT_CHANNEL", "Release")
    monkeypatch.setenv("INPUT_PROJECT", "hippo")
    monkeypatch.setenv("GITHUB_SHA", "1234567890abcdef1234567890abcdef12345678")

    handle_tag()

    content = env_file.read_text(encoding="utf-8")
    assert "VIEWER_CHANNEL=Second_Life_Release\n" in content
    assert "TAG_ID=12345678-hippo\n" in content
    assert "tag_name=Second_Life_Release#12345678-hippo\n" in content


def test_handle_tag_channel_mode_injection_attempt(monkeypatch):
    monkeypatch.setenv("INPUT_CHANNEL", "Release")
    monkeypatch.setenv("INPUT_PROJECT", "hippo; touch hacked")
    monkeypatch.setenv("GITHUB_SHA", "1234567890abcdef1234567890abcdef12345678")

    with pytest.raises(ValueError):
        handle_tag()


def test_handle_tag_fs_build_mode(tmp_path, monkeypatch):
    build_info = {
        "release_type": "Alpha",
        "viewer_version": "7.1.10",
        "viewer_build": "100000",
    }
    json_path = tmp_path / "build_info.json"
    json_path.write_text(json.dumps(build_info), encoding="utf-8")

    env_file = tmp_path / "env.txt"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("BUILD_INFO_FILE", str(json_path))
    monkeypatch.setenv("EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("INPUT_RELEASE_TYPE", "Beta")
    monkeypatch.setenv("INPUT_VIEWER_VERSION", "7.1.11")
    monkeypatch.setenv("INPUT_VIEWER_BUILD", "200000")
    monkeypatch.setenv("INPUT_DRY_RUN", "false")

    handle_tag()

    content = env_file.read_text(encoding="utf-8")
    assert "release_type=Beta\n" in content
    assert "viewer_version=7.1.11\n" in content
    assert "viewer_build=200000\n" in content
    assert "dry_run=false\n" in content
    assert "tag_name=Firestorm_Beta_7.1.11.200000\n" in content


def test_handle_tag_fs_build_mode_injection_attempt(tmp_path, monkeypatch):
    build_info = {
        "release_type": "Alpha",
        "viewer_version": "7.1.10",
        "viewer_build": "100000",
    }
    json_path = tmp_path / "build_info.json"
    json_path.write_text(json.dumps(build_info), encoding="utf-8")

    monkeypatch.setenv("BUILD_INFO_FILE", str(json_path))
    monkeypatch.setenv("EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("INPUT_VIEWER_VERSION", "7.1.10; rm -rf /")

    with pytest.raises(ValueError):
        handle_tag()


def test_handle_deploy_alpha_and_manual(tmp_path, monkeypatch):
    env_file = tmp_path / "env.txt"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("VIEWER_RELEASE_TYPE", "Alpha")
    monkeypatch.setenv("BETA_WEBHOOK_URL", "https://hooks.discord.com/beta")
    monkeypatch.setenv("VIEWER_VERSION", "7.1.10")
    monkeypatch.setenv("VIEWER_BUILD", "123456")
    monkeypatch.setenv("BUILD_RUN_NUMBER", "99")

    handle_deploy()

    content = env_file.read_text(encoding="utf-8")
    assert "FS_RELEASE_FOLDER=test\n" in content
    assert "FS_BUILD_WEBHOOK_URL=https://hooks.discord.com/beta\n" in content
    assert "FS_VIEWER_VERSION=7.1.10\n" in content
    assert "FS_VIEWER_BUILD=123456\n" in content
    assert "BUILD_RUN_NUMBER=99\n" in content

    # Test Manual
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("VIEWER_RELEASE_TYPE", "Manual")
    monkeypatch.setenv("MANUAL_WEBHOOK_URL", "https://hooks.discord.com/manual")
    handle_deploy()
    content = env_file.read_text(encoding="utf-8")
    assert "FS_RELEASE_FOLDER=test\n" in content
    assert "FS_BUILD_WEBHOOK_URL=https://hooks.discord.com/manual\n" in content


def test_handle_deploy_unsupported_type(monkeypatch):
    monkeypatch.setenv("VIEWER_RELEASE_TYPE", "Unsupported")
    with pytest.raises(ValueError, match="Unsupported release type"):
        handle_deploy()


def test_handle_tag_channel_mode_no_project(tmp_path, monkeypatch):
    env_file = tmp_path / "env.txt"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("INPUT_CHANNEL", "Develop")
    monkeypatch.setenv("GITHUB_SHA", "1234567890abcdef1234567890abcdef12345678")

    handle_tag()

    content = env_file.read_text(encoding="utf-8")
    assert "VIEWER_CHANNEL=Second_Life_Develop\n" in content
    assert "Second_Life_Develop#12345678-" in content


def test_handle_run_number_workflow_run(tmp_path, monkeypatch):
    output_file = tmp_path / "output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("EVENT_NAME", "workflow_run")
    monkeypatch.setenv("WORKFLOW_RUN_NUMBER", "112233")

    handle_run_number()

    content = output_file.read_text(encoding="utf-8")
    assert "build_run_number=112233\n" in content


def test_main_cli_deploy(tmp_path, monkeypatch, capsys):
    env_file = tmp_path / "env.txt"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("VIEWER_RELEASE_TYPE", "Release")
    monkeypatch.setattr("sys.argv", ["parse_workflow_inputs.py", "deploy"])

    from fsutils.parse_workflow_inputs import main
    main()

    captured = capsys.readouterr()
    assert "FS_RELEASE_FOLDER=release" in captured.out


def test_main_cli_tag_and_run_number(tmp_path, monkeypatch, capsys):
    env_file = tmp_path / "env.txt"
    output_file = tmp_path / "output.txt"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    # Test main tag
    monkeypatch.setenv("INPUT_CHANNEL", "Test")
    monkeypatch.setenv("GITHUB_SHA", "abcdef1234567890abcdef1234567890abcdef12")
    monkeypatch.setattr("sys.argv", ["parse_workflow_inputs.py", "tag"])

    from fsutils.parse_workflow_inputs import main
    main()

    content = env_file.read_text(encoding="utf-8")
    assert "VIEWER_CHANNEL=Second_Life_Test\n" in content

    # Test main run_number
    monkeypatch.setenv("EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("INPUT_BUILD_RUN_NUMBER", "54321")
    monkeypatch.setattr("sys.argv", ["parse_workflow_inputs.py", "run_number"])

    main()

    content_out = output_file.read_text(encoding="utf-8")
    assert "build_run_number=54321\n" in content_out


def test_main_cli_error_exit(monkeypatch, capsys):
    monkeypatch.setenv("VIEWER_RELEASE_TYPE", "Release; bad")
    monkeypatch.setattr("sys.argv", ["parse_workflow_inputs.py", "deploy"])

    from fsutils.parse_workflow_inputs import main
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error validating workflow inputs" in captured.err

