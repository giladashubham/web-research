from __future__ import annotations

import os

from webresearch.env import load_environment


def test_load_environment_reads_dotenv_from_current_working_directory(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("WEBRESEARCH_TEST_DOTENV", raising=False)
    (tmp_path / ".env").write_text("WEBRESEARCH_TEST_DOTENV=from-file\n")
    load_environment.cache_clear()

    load_environment()

    assert os.environ["WEBRESEARCH_TEST_DOTENV"] == "from-file"


def test_load_environment_does_not_override_existing_shell_env(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("WEBRESEARCH_TEST_DOTENV", "from-shell")
    (tmp_path / ".env").write_text("WEBRESEARCH_TEST_DOTENV=from-file\n")
    load_environment.cache_clear()

    load_environment()

    assert os.environ["WEBRESEARCH_TEST_DOTENV"] == "from-shell"
