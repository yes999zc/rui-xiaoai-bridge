<div align="center">

# rui-xiaoai-bridge

**把小米 AI 音箱 Pro（LX06）作为 [rui](https://github.com/yes999zc/rui) 的语音卫星接入，不 fork 核心。**
一个 out-of-tree 的 Socket & Plug v1 设备插件：`plugin.yaml` + `rui-device/v1` 清单 + 进程内 adapter 包。

[![License: MIT](https://img.shields.io/github/license/yes999zc/rui-xiaoai-bridge?style=flat-square)](LICENSE)
[![rui](https://img.shields.io/badge/rui-%3E%3D0.6.0%20%3C0.8.0-2f6f6a)](https://github.com/yes999zc/rui)
[![plugin](https://img.shields.io/badge/plugin-0.2.1-b4744a)](src/rui_xiaoai_bridge/plugin.yaml)

</div>

---

# 中文

## 15 秒了解

LX06 自带麦克风阵列与硬件 AEC；唤醒、对话、播放由你的 rui 服务决定。rui 只通过 manifest 认识这个插件——**内核里没有一行小爱专属代码**，卸载插件就等于不支持这类设备。

```text
rui 起一个音频平面 → 插件按 rui-device/v1 提供上下行 → 说「你好小瑞」→ rui 决定这一轮 → 插件播报/报灯
```

## 架构

![architecture](docs/assets/architecture.png)

源文件：[`docs/assets/architecture.mmd`](docs/assets/architecture.mmd)；导出物 [`architecture.svg`](docs/assets/architecture.svg) / [`architecture.png`](docs/assets/architecture.png)。桥仓无界面，hero 即这张架构图。

| 层 | 在这个仓库里的东西 | 说明 |
|---|---|---|
| **rui 核心（不改）** | 会话/回合、供应商、唤醒仲裁、音频门限 | 用官方镜像，不补丁、不 fork |
| **本仓库（插件）** | `adapter`（`build()` 入口）、`plugin.yaml`（契约窗口）、`devices/lx06.yaml` | `rui_compat: >=0.6.0 <0.8.0`；越界时 loader 会拒载。桥仓无界面，hero 即这张架构图 |
| **设备** | LX06：入站音频上行、喇叭、LED、按键 | 设备侧 AEC 归设备 |

## 特性

- **纯 out-of-tree**：核心通过 manifest 的 `runtime.entrypoint` 加载，插件放在 `RUI_PLUGINS_DIR` 或 `<data_dir>/plugs/xiaoai-lx06` 即可；核心只有 0.6→0.7 的临时 adapter 别名，没有设备实现。
- **契约优先**：设备清单遵循 `rui-device/v1`；`rui_compat` 明确声明支持的 rui 版本窗口。
- **入站设备模型**：设备把音频推到已注册的监听端口（`listen_port`），插件在音频平面内完成上下行与事件处理。
- **可观测**：`rui plug-test` 跑契约自测；设备状态与重连进 rui 的日志与轨迹。

## 三行启动

```bash
git clone --branch v0.2.1 https://github.com/yes999zc/rui-xiaoai-bridge.git && cd rui-xiaoai-bridge
bash deploy/install-plug-manifest.sh          # 把 plugin.yaml + adapter 安装到 rui 的插件目录
PYTHONPATH=src python -m pytest -q            # 契约测试（9 项）
rui plug-test <插件目录>   # 契约自测（directory 必填，--adapter 指定入口）
```

安装后重启 rui，在控制台「设备」页添加 LX06，填入设备地址与令牌；也可以直接在 `config.yaml` 的 `devices[]` 里加一条。

## 兼容性与前置条件

- `rui` **>=0.6.0 <0.8.0**；本版通过 **9 项插件契约测试**，LX06 真机指标为 **2026-10-24 历史实测**（0.7.2 未复测）。Python **3.11+**。
- **设备前置条件**（第三方设备，与厂商**无官方关联**）：
  - 小米 AI 音箱 Pro（LX06），固件需已具备设备本地接口，并与 rui 主机在同一局域网；
  - 设备令牌（`RUI_DEVICE_TOKEN` 或插件配置里的 `token_env`）由你提供；
  - 监听端口（默认 `4412`）需在 rui 主机上可达；
  - 本项目只提供软件侧桥接层；设备固件与网络准备由你按设备既有能力完成。
- 唤醒与打断依赖 rui 服务端 KWS（中文），设备侧不做唤醒判定。

## 支持矩阵

> 数字来自历史真机实测（2026-10），**未测项一律标「未测」**；引用时请连同日期一起引用。

| 能力 | 状态 |
|---|---|
| 唤醒（服务端中文 KWS） | 19/20（历史实测） |
| 播放中打断 | 停播延迟 205.2 ms（历史实测） |
| 语音指令 | 未测（回归项，未单独统计） |
| 音量控制 | 未测 |
| 指示灯 | 未测 |
| 多设备并发 | 未测 |

## 故障排查

| 现象 | 原因 | 处置 |
|---|---|---|
| 插件未被加载 | manifest 不在插件目录，或 `rui_compat` 越界 | 看 rui 启动日志里的 manifest 报错；确认 rui 版本在窗口内 |
| 设备一直离线 | 端口不可达 / 令牌不匹配 | 确认 `listen_port` 可达；`token_env` 指向的环境变量有值 |
| 能唤醒但不回话 | 音频上行或播放下行不通 | 看音频平面的 `[seg]` 与播放日志；确认设备侧 AEC 正常 |
| 与另一台音箱抢答 | 两台都在同一房间且先后被唤醒 | 分到不同房间；跨房间的播放与回合仲裁互不影响（runner 仍单会话） |
| `plug-test` 失败 | rui 版本或插件目录不对 | 在 rui 容器内跑 `rui plug-test`，按失败项逐个修 |

## 已知限制

- LX06 的关键指标只有历史实测（唤醒 19/20、打断 205.2 ms），**没有** 0.7.2 的复测数据。
- 语音指令成功率、音量、指示灯、多设备并发均**未测**。
- 设备固件差异可能影响上行音频与 AEC 行为；本项目不做设备侧干预。
- 插件在音频平面内以 in-process 方式运行（`trust=trusted` 为自声明元数据，不是沙箱）。

## 致谢

`rui-device/v1` 契约与 `plug-test` 来自 [rui](https://github.com/yes999zc/rui)；设备清单写法参考该契约的示例插件。

## License

[MIT](LICENSE)。

---

# English

## In 15 seconds

The LX06 brings its own microphone array and hardware AEC; wakes, dialogue and playback are decided by your rui server. rui recognises this plug only through its manifest — **the core contains no vendor-specific code**, and removing the plug means the device is simply unsupported.

```text
rui starts an audio plane → the plug provides uplink/downlink per rui-device/v1 → "Hey Rui" → rui decides the turn → the plug speaks / lights
```

## Architecture

![architecture](docs/assets/architecture.png)

Source: [`docs/assets/architecture.mmd`](docs/assets/architecture.mmd); exports [`architecture.svg`](docs/assets/architecture.svg) / [`architecture.png`](docs/assets/architecture.png). A bridge has no UI, so this diagram is the hero.

| Layer | What lives here | Notes |
|---|---|---|
| **rui core (unchanged)** | Sessions/turns, providers, wake arbitration, audio gate | Official image, no patches, no fork |
| **This repo (plug)** | `adapter` (`build()` entry), `plugin.yaml` (contract window), `devices/lx06.yaml` | `rui_compat: >=0.6.0 <0.8.0`; the loader refuses out-of-range versions |
| **Device** | LX06: inbound audio uplink, speaker, LED, keys | Device-side AEC stays on the device |

## Features

- **Pure out-of-tree**: the core loads it via the manifest's `runtime.entrypoint`; drop it under `RUI_PLUGINS_DIR` or `<data_dir>/plugs/xiaoai-lx06`. The core carries only a temporary 0.6→0.7 adapter alias, no device implementation.
- **Contract first**: the device manifest follows `rui-device/v1` and declares the supported rui window in `rui_compat`.
- **Inbound device model**: the device pushes audio to a registered listen port; the plug handles uplink/downlink and events inside the audio plane.
- **Observability**: `rui plug-test` runs the contract suite; device state and reconnects land in rui logs and traces.

## Three-line quickstart

```bash
git clone --branch v0.2.1 https://github.com/yes999zc/rui-xiaoai-bridge.git && cd rui-xiaoai-bridge
bash deploy/install-plug-manifest.sh          # installs plugin.yaml + adapter into rui's plug dir
PYTHONPATH=src python -m pytest -q            # contract tests (9)
rui plug-test <plugin-dir>   # contract self-test (directory required; --adapter selects the entry)
```

Restart rui, then add the LX06 on the console's Devices page (address + token), or append an entry to `devices[]` in `config.yaml`.

## Compatibility and prerequisites

- `rui` **>=0.6.0 <0.8.0**; this release passes the **9 plugin contract tests**, and the LX06 device numbers are **historical (2026-10-24)** — not re-measured on 0.7.2. Python **3.11+**.
- **Device prerequisites** (third-party hardware, **not affiliated with any vendor**):
  - Xiaomi AI Speaker Pro (LX06) with firmware that already exposes the device's local interface, on the same LAN as the rui host;
  - a device token (`RUI_DEVICE_TOKEN`, or the `token_env` value in the plug config) that you provide;
  - the listen port (default `4412`) reachable on the rui host;
  - this project only provides the software bridge; preparing firmware and network is up to you, using the device's existing capabilities.
- Wake and barge-in rely on rui's server-side KWS (Chinese); the device makes no wake decision.

## Support matrix

> Historical real-device measurements (Oct 2026); anything untested is marked **untested** — quote the date when quoting the numbers.

| Capability | Status |
|---|---|
| Wake (server-side Chinese KWS) | 19/20 (historical) |
| Barge-in during playback | 205.2 ms stop latency (historical) |
| Voice commands | untested |
| Volume control | untested |
| LED | untested |
| Concurrent multi-device | untested |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Plug never loads | Manifest missing from the plug dir, or `rui_compat` out of range | Read the manifest error in rui's startup log; confirm the rui version |
| Device stays offline | Port unreachable, or token mismatch | Check the listen port and that `token_env` points at a value |
| Wakes but never answers | Uplink or playback downlink is broken | Inspect `[seg]` and playback lines in the audio plane logs; verify device AEC |
| Two speakers talk over each other | Both in the same room and woken in sequence | Put them in different rooms; cross-room playback and turn arbitration are isolated (the runner is still single-session) |
| `plug-test` fails | Wrong rui version or plug path | Run `rui plug-test` inside the rui container and fix the failing items |

## Known limitations

- LX06 numbers are historical (19/20 wake, 205.2 ms barge-in) with **no** 0.7.2 re-measurement.
- Voice-command success rate, volume, LED and concurrency are **untested**.
- Firmware differences can change uplink audio and AEC behaviour; this project does not touch the device.
- The plug runs in-process inside the audio plane (`trust=trusted` is self-asserted metadata, not a sandbox).

## Credits

The `rui-device/v1` contract and `plug-test` come from [rui](https://github.com/yes999zc/rui); the manifest follows the example plug in that contract.

## License

[MIT](LICENSE).
