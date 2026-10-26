"""The package is importable without side effects and exposes only the plug entrypoint.

These tests need rui on the path: the adapter imports rui's device/config contracts
because it runs in-process in the rui audio plane. rui is the *host* in production
(the official image supplies it), so the suite skips with a readable reason instead of
failing on a machine that only has this repository.
"""
from __future__ import annotations

from pathlib import Path

import pytest

rui = pytest.importorskip("rui", reason="rui is the in-process host; install it to run the adapter tests")

import rui_xiaoai_bridge  # noqa: E402
from rui_xiaoai_bridge import adapter  # noqa: E402

PLUG = Path(__file__).resolve().parents[1] / "src" / "rui_xiaoai_bridge"


def test_package_imports_and_exports_the_documented_surface() -> None:
    assert rui_xiaoai_bridge.__all__ == [
        "DEFAULT_ADAPTER",
        "DEFAULT_LISTEN_PORT",
        "XiaoaiAdapter",
        "build",
    ]
    # Only `adapter:build` is declared in devices/lx06.yaml; the rest is internal.
    assert rui_xiaoai_bridge.build is adapter.build
    assert callable(rui_xiaoai_bridge.build)
    assert rui_xiaoai_bridge.DEFAULT_ADAPTER == "lx06"
    assert rui_xiaoai_bridge.DEFAULT_LISTEN_PORT == 4412


def test_build_needs_a_device_spec() -> None:
    # The contract kit passes a SimpleNamespace; a bare call must fail loudly rather
    # than construct a speaker with invented identity.
    with pytest.raises(TypeError):
        adapter.build()
