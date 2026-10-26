"""The shipped manifest is the load contract: rui's own loader must accept it.

The assertions pin the fields the out-of-tree split depends on: the plugin id, the
0.7.x compatibility window, the inbound device id, the entrypoint that points at
*this* package, and the hardware audio defaults the in-tree copy used to bake into
the core.
"""
from __future__ import annotations

from pathlib import Path

import pytest

rui = pytest.importorskip("rui", reason="rui's plugin loader is the contract under test")

from rui.device.contract import Capability, Transport  # noqa: E402
from rui.plugins import DeviceClass, RuntimeMode, TrustLevel, WakeSource, load_plugin  # noqa: E402

PLUG = Path(__file__).resolve().parents[1] / "src" / "rui_xiaoai_bridge"


def test_manifest_loads_through_rui_loader() -> None:
    plugin = load_plugin(PLUG)

    assert plugin.id == "xiaoai-lx06"
    assert plugin.version == "0.2.1"
    assert plugin.trust is TrustLevel.TRUSTED
    assert plugin.rui_compat == ">=0.6.0 <0.8.0"
    assert plugin.license == "MIT"
    assert plugin.source_dir == PLUG.resolve()
    assert len(plugin.devices) == 1


def test_device_contract_is_the_inbound_lx06_shape() -> None:
    device = load_plugin(PLUG).devices[0]

    assert device.id == "lx06"
    assert device.schema == "rui-device/v1"
    assert device.device_class is DeviceClass.A
    assert device.transport is Transport.INBOUND
    assert device.protocol.kind == "ws"
    assert device.protocol.version == "1"
    # LX06 stays on RUI KWS: an omitted wake block means source=rui, no device_wake.
    assert device.wake is None
    assert device.wake_source is WakeSource.RUI
    assert Capability.MIC_ARRAY in device.capabilities
    assert Capability.REFERENCE in device.capabilities


def test_audio_defaults_and_entrypoint_are_preserved() -> None:
    device = load_plugin(PLUG).devices[0]
    capture = device.audio_defaults.capture

    assert (capture.rate, capture.channels, capture.mic_channels, capture.ref_channels) == (
        48000,
        8,
        6,
        2,
    )
    assert (capture.bits, capture.mic_shift, capture.ref_shift) == (32, 12, 16)
    assert device.audio_defaults.ack_echo_ignore_ms == 1200

    runtime = device.runtime
    assert runtime is not None
    assert runtime.mode is RuntimeMode.IN_PROCESS
    # The entrypoint names this repository's package; the in-tree name must not leak.
    assert runtime.entrypoint == "rui_xiaoai_bridge.adapter:build"
    assert runtime.listen_port == 4412
    assert runtime.token_env == "RUI_DEVICE_TOKEN"
