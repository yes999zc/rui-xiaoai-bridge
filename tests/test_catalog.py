"""Catalog semantics for an out-of-tree install, using rui's real resolver.

Two paths matter and they behave differently on purpose:

* **user plug** - ``<data_dir>/plugs/<dir>/plugin.yaml`` is discovered by
  ``discover_plugins`` and appears in ``PlugCatalog`` with ``source="user"``. This is
  the path the wizard and ``GET /api/v1/plugs`` read.
* **image/builtin plug** - a root listed in ``RUI_PLUGINS_DIR`` (or
  ``/opt/rui-plugins``) is scanned as builtin. If both carry the same plugin id, the
  builtin entry wins and the user copy is reported as a duplicate; that is the
  coexistence rule 0.6.x applies while the in-tree reference plug still ships.

The tests copy only the manifest files: the catalog never imports the adapter.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

rui = pytest.importorskip("rui", reason="rui's plug catalog/resolver is the contract under test")

from rui.plugins import PlugCatalog, RuntimeMode, TrustLevel, discover_plugins  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
PLUG = REPO / "src" / "rui_xiaoai_bridge"


def _available(plugin) -> bool:
    """The `available` rule both /api/v1/plugs and /api/v2/plugins apply.

    Kept local instead of importing a web-layer helper: the oldest rui in the
    declared `rui_compat` window must be able to run this suite, and the console v2
    module is newer than the 0.6.0 release tag. The real endpoint is exercised by the
    Phase 1 acceptance run recorded in the rui plan document.
    """
    if plugin.trust not in (TrustLevel.BUILTIN, TrustLevel.TRUSTED):
        return False
    return all(
        device.runtime is None or device.runtime.mode is not RuntimeMode.SIDECAR
        for device in plugin.devices
    )


def _install_user_manifest(data_dir: Path) -> Path:
    target = data_dir / "plugs" / "xiaoai-lx06"
    (target / "devices").mkdir(parents=True)
    shutil.copy2(PLUG / "plugin.yaml", target / "plugin.yaml")
    shutil.copy2(PLUG / "devices" / "lx06.yaml", target / "devices" / "lx06.yaml")
    return target


def test_user_install_is_source_user_and_available(tmp_path, monkeypatch) -> None:
    # Isolate from the checkout's plugs/ fallback so this really exercises "user".
    builtin_root = tmp_path / "empty-builtin"
    builtin_root.mkdir()
    monkeypatch.setenv("RUI_PLUGINS_DIR", str(builtin_root))
    _install_user_manifest(tmp_path / "data")

    catalog = PlugCatalog(tmp_path / "data")
    entry = catalog.get("xiaoai-lx06")

    assert entry is not None
    assert entry.source == "user"
    assert entry.plugin.trust.value == "trusted"
    # This is exactly what /api/v1/plugs and /api/v2/plugins use for `available`.
    assert _available(entry.plugin) is True
    assert entry.plugin.devices[0].id == "lx06"
    assert catalog.resolve(adapter="lx06").source == "user"


def test_builtin_wins_on_duplicate_plugin_id(tmp_path, monkeypatch) -> None:
    # src/ is a valid RUI_PLUGINS_DIR root: src/rui_xiaoai_bridge/plugin.yaml.
    monkeypatch.setenv("RUI_PLUGINS_DIR", str(REPO / "src"))
    user_dir = _install_user_manifest(tmp_path / "data")

    catalog = PlugCatalog(tmp_path / "data")
    entry = catalog.get("xiaoai-lx06")

    assert entry is not None
    assert entry.source == "builtin", "the image/builtin plug must win on a shared id"
    # The user copy is still discovered - the wizard reports it as a failed duplicate
    # instead of silently dropping it; the catalog itself only keeps the winner.
    scan = discover_plugins(tmp_path / "data")
    assert [plugin.id for plugin in scan.plugins] == ["xiaoai-lx06"]
    assert scan.plugins[0].source_dir == user_dir.resolve()
    assert scan.errors == []
