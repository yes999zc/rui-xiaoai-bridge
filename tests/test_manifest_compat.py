"""The shipped manifest must accept the rui release that loads it.

rui's loader refuses a plug whose ``rui_compat`` does not match ``rui.__version__``
(``src/rui/plugins/loader.py``), so a ceiling one release behind silently leaves
every speaker without an adapter on the next minor. This check deliberately does
not import rui: it pins the release the bridge is verified against, so it still
runs where the host package is absent.

Reverse check (old ceiling must fail): copy this manifest to a temporary directory,
set ``rui_compat`` back to ``>=0.6.0 <0.7.0`` and call
``uncovered_manifests(<temp root>, CURRENT_RUI)`` - it must return that file.
"""

from __future__ import annotations

import re
from pathlib import Path

from packaging.specifiers import SpecifierSet
from ruamel.yaml import YAML

#: The rui release this bridge is verified against. Source: house-ear
#: ``src/rui/__init__.py`` at the v0.7.0 release tag (``rui.__version__ == "0.7.0"``);
#: keep this in sync when the image moves to the next rui minor.
CURRENT_RUI = "0.7.0"

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "rui_xiaoai_bridge"

_YAML = YAML(typ="safe")


def _specifier(compat: str) -> SpecifierSet:
    """rui manifests separate comparators with spaces; PEP 440 wants commas."""
    return SpecifierSet(re.sub(r"\s+(?=[<>=!~])", ",", compat.strip()))


def uncovered_manifests(root: Path, version: str) -> list[str]:
    """Every manifest under ``root`` whose ``rui_compat`` does not accept ``version``."""
    missing: list[str] = []
    for path in sorted(root.rglob("plugin.yaml")):
        data = _YAML.load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"{path} is not a YAML mapping"
        compat = data.get("rui_compat")
        assert isinstance(compat, str) and compat, f"{path} has no rui_compat"
        if not _specifier(compat).contains(version):
            missing.append(f"{path}: {compat}")
    return missing


def test_the_repository_ships_a_manifest() -> None:
    assert sorted(PACKAGE.rglob("plugin.yaml")), f"no plugin.yaml under {PACKAGE}"


def test_every_shipped_manifest_covers_the_current_rui() -> None:
    assert uncovered_manifests(PACKAGE, CURRENT_RUI) == []
