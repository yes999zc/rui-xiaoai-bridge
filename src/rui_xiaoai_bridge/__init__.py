"""rui-xiaoai-bridge: the LX06 (Xiaomi AI Speaker Pro) adapter as an out-of-tree plug.

This repository is a *device adapter*, not a rui fork. It ships:

* ``plugin.yaml`` - the ``rui-plugin/v0`` catalogue entry (id ``xiaoai-lx06``);
* ``devices/lx06.yaml`` - the ``rui-device/v1`` manifest, including the 8 ch /
  48 kHz ``audio_defaults`` and the inbound websocket entrypoint;
* this package - the adapter, wire protocol, LED ring and mixer helpers that the
  in-process rui audio plane runs after importing ``runtime.entrypoint``.

Only the entrypoint named by ``devices/lx06.yaml`` (``rui_xiaoai_bridge.adapter:build``)
is public API. Everything else is an implementation detail of this adapter and may
move between minor releases without a rui contract change.

The package is imported by rui's in-process audio plane, so rui is a *host*
dependency supplied by the running image, not an install dependency of this
repository (the PyPI ``rui`` project is unrelated - see README).
"""
from __future__ import annotations

from .adapter import DEFAULT_ADAPTER, DEFAULT_LISTEN_PORT, XiaoaiAdapter, build

__all__ = ["DEFAULT_ADAPTER", "DEFAULT_LISTEN_PORT", "XiaoaiAdapter", "build"]
