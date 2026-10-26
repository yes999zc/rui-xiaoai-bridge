"""Expose this repository's plug to the core registry during tests.

The core no longer ships the adapter; a test that starts an AudioPlaneSupervisor
must point RUI_PLUGINS_DIR at a root containing <plug>/plugin.yaml. src/ holds
rui_xiaoai_bridge/plugin.yaml, so it is the root (PYTHONPATH=src is already set).
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"


@pytest.fixture(autouse=True)
def _plug_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUI_PLUGINS_DIR", str(SRC))
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(
        [str(SRC), os.environ.get("PYTHONPATH", "")]).rstrip(os.pathsep))
