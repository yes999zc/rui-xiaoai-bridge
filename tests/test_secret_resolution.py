"""The console-written secret reaches this adapter's transport token."""
from __future__ import annotations

from pathlib import Path

import pytest
from rui import secrets
from rui.config.schema import CaptureConfig, DeviceConfig, VoiceConfig

from rui_xiaoai_bridge.adapter import XiaoaiAdapter

TOKEN_ENV = "RUI_TEST_SECRET_TOKEN"
TOKEN = "console-token"


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(secrets, "_name", "")
    secrets.configure(tmp_path)
    monkeypatch.delenv(TOKEN_ENV, raising=False)
    secrets.put(TOKEN_ENV, TOKEN)
    return tmp_path


def test_console_secret_reaches_the_adapter(store: Path) -> None:
    dev = DeviceConfig(id="living", host="192.0.2.10", token_env=TOKEN_ENV)
    adapter = XiaoaiAdapter(dev, CaptureConfig(), VoiceConfig())
    assert adapter.token == TOKEN
