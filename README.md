<div align="center">

# rui-xiaoai-bridge

**把小米 AI 音箱 Pro（LX06）作为 [rui](https://github.com/yes999zc/rui) 的语音卫星接入，不 fork 核心。**
一个 out-of-tree 的 Socket & Plug v1 设备插件：`plugin.yaml` + `rui-device/v1` 清单 + 进程内 adapter 包。

[![License: MIT](https://img.shields.io/github/license/yes999zc/rui-xiaoai-bridge?style=flat-square)](LICENSE)
[![rui](https://img.shields.io/badge/rui-%3E%3D0.6.0%20%3C0.8.0-2f6f6a)](https://github.com/yes999zc/rui)
[![plugin](https://img.shields.io/badge/plugin-0.2.2-b4744a)](src/rui_xiaoai_bridge/plugin.yaml)

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

- **纯 out-of-tree**：0.7.6 起核心不再内置设备实现，**本仓库是唯一来源**；插件目录挂到 `/opt/rui-plugins` 即可，没有内置回退、没有 adapter 别名（旧配置 `adapter: xiaoai` 只在读入时迁移为 `lx06` 并告警，0.8.0 删除）。
- **契约优先**：设备清单遵循 `rui-device/v1`；`rui_compat` 明确声明支持的 rui 版本窗口。
- **入站设备模型**：设备把音频推到已注册的监听端口（`listen_port`），插件在音频平面内完成上下行与事件处理。
- **可观测**：`rui plug-test` 跑契约自测；设备状态与重连进 rui 的日志与轨迹。

## 三行启动

```bash
git clone --branch v0.2.2 https://github.com/yes999zc/rui-xiaoai-bridge.git && cd rui-xiaoai-bridge
mkdir -p /vol1/rui/plugins && cp -r src/rui_xiaoai_bridge /vol1/rui/plugins/   # 宿主插件目录
IMG=ghcr.io/yes999zc/rui@sha256:1f074bb3af1ef4854ef040b12c9146ed8a6ef2b1c4a5f6cc7858ac6ccac3ecaa
docker run --rm -v /vol1/rui/plugins:/opt/rui-plugins:ro -e PYTHONPATH=/opt/rui-plugins \
  --entrypoint rui "$IMG" plug-test /opt/rui-plugins/rui_xiaoai_bridge \
  --adapter rui_xiaoai_bridge.adapter:build   # 契约自测
```

生产用 Compose：核心镜像 + `-v ./plugins:/opt/rui-plugins:ro` + `PYTHONPATH=/opt/rui-plugins` + `RUI_ADAPTER_PLUGINS=lx06=rui_xiaoai_bridge.adapter:build`，**不需要造下游镜像**。重启后在控制台「设备」页添加 LX06，或直接在 `config.yaml` 的 `devices[]` 里加一条。

## 让 AI 帮你装

把下面这段贴给任意 AI 助手：

```text
目标：用 Docker 跑起 rui 0.7.8 + 本插件 0.2.2（adapter id = lx06），核心镜像 + 外置插件目录，不造下游镜像。
前置：docker compose version 通过；8080 空闲；5 GB 磁盘。
1) git clone --branch main https://github.com/yes999zc/rui.git && cd rui/examples/two-speakers   # main 才有本示例；镜像 pin 到 0.7.8 的 amd64 摘要
2) git clone --branch v0.2.2 https://github.com/yes999zc/rui-xiaoai-bridge.git && git clone --branch v1.3.1 https://github.com/yes999zc/rui-dot2-bridge.git
3) mkdir -p plugins && cp -r rui-xiaoai-bridge/src/rui_xiaoai_bridge plugins/   # 需要两台都接时，把另一个桥的 src 也 cp 进来
4) 写 ./config/config.yaml（web.auth_token + devices[]，含 lx06 的 host/listen_port）
5) TLS（同 compose 里 dot2 的 tls_port 开启时必需；只接 lx06 可跳过）：原 controller 证书放 ./secrets/，没有就运行 `bash ../../scripts/make_dev_tls.sh`。自签只保证平面能起，真机信任取决于设备 CA
6) export RUI_DEVICE_TOKEN=<设备令牌>; docker compose up -d
7) 验收：/health 的 planes 里 lx06 为 running、devices 正确、device_errors=0（外置 catalog 插件不进 registered）
失败看：docker compose logs --tail=80 rui 的 config error / adapter / TLS；回滚：down 后换回上一版 image tag；TLS 失败先移走 ./secrets/ 排查
不需要自己编译 ffmpeg（镜像已内置）
```

## 兼容性与前置条件

- `rui` **>=0.6.0 <0.8.0**（本版面向 **0.7.8** 验证）；本版通过 **9 条插件契约测试 + 4 条重连复位测试**，LX06 真机指标为 **2026-10-24 历史实测**。Python **3.11+**。
- 安装：核心镜像 + 外置插件目录（`/vol1/rui/plugins/rui_xiaoai_bridge`），挂载 `/opt/rui-plugins` 并设 `PYTHONPATH` + `RUI_ADAPTER_PLUGINS`；**不需要造下游镜像**。
- **设备前置条件**（第三方设备，与厂商**无官方关联**）：
  - 小米 AI 音箱 Pro（LX06），固件需已具备设备本地接口，并与 rui 主机在同一局域网；
  - 设备令牌（`RUI_DEVICE_TOKEN` 或插件配置里的 `token_env`）由你提供；
  - 监听端口（默认 `4412`）需在 rui 主机上可达；
  - 本项目只提供软件侧桥接层；设备固件与网络准备由你按设备既有能力完成。
- 唤醒与打断依赖 rui 服务端 KWS（中文），设备侧不做唤醒判定。

| rui 核心 | 本插件 | 说明 |
|---|---|---|
| **0.7.8**（当前） | **0.2.2** | 推荐；核心 + 外置插件目录 |
| 0.7.4（历史） | 0.2.2 | 外置插件同样可用 |

## 支持矩阵

> 数字来自历史真机实测（2026-10），**未测项一律标「未测」**；引用时请连同日期一起引用。

| 能力 | 状态 |
|---|---|
| 唤醒（服务端中文 KWS） | 19/20（历史实测） |
| 播放中打断 | 停播延迟 205.2 ms（历史实测；**stop-push 判据**，非声学端到端；三轮 24.2/64.5/205.2，max n=3） |
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
| `plug-test` 失败 | rui 版本或插件目录不对 | 在 rui 容器内跑 `rui plug-test <插件目录> --adapter rui_xiaoai_bridge.adapter:build`，按失败项逐个修 |

## 已知限制

- 未声明 `wake_words_residual` 的第三方清单不做 vendor 短语兜底。
- 两音箱默认只起第一台设备的平面，需 `multi_device: {enabled: true, max_planes: 2}`。
- 自签证书只保证平面能起，真机信任取决于设备 CA。


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

- **Pure out-of-tree**: since 0.7.6 the core ships no device implementation; **this repository is the only source**. Mount the plug directory at `/opt/rui-plugins`; there is no in-tree fallback and no adapter alias (a legacy `adapter: xiaoai` is migrated to `lx06` on load, removed in 0.8.0).
- **Contract first**: the device manifest follows `rui-device/v1` and declares the supported rui window in `rui_compat`.
- **Inbound device model**: the device pushes audio to a registered listen port; the plug handles uplink/downlink and events inside the audio plane.
- **Observability**: `rui plug-test` runs the contract suite; device state and reconnects land in rui logs and traces.

## Three-line quickstart

```bash
git clone --branch v0.2.2 https://github.com/yes999zc/rui-xiaoai-bridge.git && cd rui-xiaoai-bridge
mkdir -p /vol1/rui/plugins && cp -r src/rui_xiaoai_bridge /vol1/rui/plugins/   # host plug dir
IMG=ghcr.io/yes999zc/rui@sha256:1f074bb3af1ef4854ef040b12c9146ed8a6ef2b1c4a5f6cc7858ac6ccac3ecaa
docker run --rm -v /vol1/rui/plugins:/opt/rui-plugins:ro -e PYTHONPATH=/opt/rui-plugins \
  --entrypoint rui "$IMG" plug-test /opt/rui-plugins/rui_xiaoai_bridge \
  --adapter rui_xiaoai_bridge.adapter:build   # contract self-test
```

In production use Compose: core image + `-v ./plugins:/opt/rui-plugins:ro` + `PYTHONPATH=/opt/rui-plugins` + `RUI_ADAPTER_PLUGINS=lx06=rui_xiaoai_bridge.adapter:build`; **no downstream image is needed**. Restart, then add the LX06 on the Devices page or append an entry to `devices[]`.

## Let an AI install it

Paste this:

```text
Goal: run rui 0.7.8 + this plug 0.2.2 (adapter id = lx06) with Docker, using the core image plus an external plug directory (no downstream image).
Preflight: docker compose version; port 8080 free; 5 GB disk.
1) git clone --branch main https://github.com/yes999zc/rui.git && cd rui/examples/two-speakers   # main 才有本示例；镜像 pin 到 0.7.8 的 amd64 摘要
2) git clone --branch v0.2.2 https://github.com/yes999zc/rui-xiaoai-bridge.git && git clone --branch v1.3.1 https://github.com/yes999zc/rui-dot2-bridge.git
3) mkdir -p plugins && cp -r rui-xiaoai-bridge/src/rui_xiaoai_bridge plugins/   # 需要两台都接时，把另一个桥的 src 也 cp 进来
4) write ./config/config.yaml (web.auth_token + devices[] with host/listen_port for lx06)
5) TLS (required only when dot2's tls_port is on in the same compose; skip for lx06-only): put the original controller cert into ./secrets/, or run `bash ../../scripts/make_dev_tls.sh`. Self-signed only proves the plane starts; the device's trusted CA decides acceptance
6) export RUI_DEVICE_TOKEN=<device token>; docker compose up -d
7) verify: /health.planes shows lx06 running, devices correct, device_errors=0 (external catalog plugs do not appear in registered)
On failure: docker compose logs --tail=80 rui (config error / adapter / TLS); rollback: down and switch the image tag back; for TLS failures move ./secrets/ away first
No ffmpeg build needed (the image ships it)
```

## Compatibility and prerequisites

- `rui` **>=0.6.0 <0.8.0** (this release is validated against **0.7.8**); this release passes **9 plugin contract tests + 4 reconnect-reset tests**, and the LX06 device numbers are **historical (2026-10-24)**. Python **3.11+**.
- Install: core image + external plug directory (`/vol1/rui/plugins/rui_xiaoai_bridge`), mounted at `/opt/rui-plugins` with `PYTHONPATH` + `RUI_ADAPTER_PLUGINS`; **no downstream image is needed**.
- **Device prerequisites** (third-party hardware, **not affiliated with any vendor**):
  - Xiaomi AI Speaker Pro (LX06) with firmware that already exposes the device's local interface, on the same LAN as the rui host;
  - a device token (`RUI_DEVICE_TOKEN`, or the `token_env` value in the plug config) that you provide;
  - the listen port (default `4412`) reachable on the rui host;
  - this project only provides the software bridge; preparing firmware and network is up to you, using the device's existing capabilities.
- Wake and barge-in rely on rui's server-side KWS (Chinese); the device makes no wake decision.

| rui core | This plug | Notes |
|---|---|---|
| **0.7.8** (current) | **0.2.2** | Recommended; core image + external plug directory |
| 0.7.4 (historical) | 0.2.2 | The external plug works the same way |

## Support matrix

> Historical real-device measurements (Oct 2026); anything untested is marked **untested** — quote the date when quoting the numbers.

| Capability | Status |
|---|---|
| Wake (server-side Chinese KWS) | 19/20 (historical) |
| Barge-in during playback | 205.2 ms stop latency (historical; **stop-push criterion**, not acoustical end-to-end; three runs 24.2/64.5/205.2, max n=3) |
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
| `plug-test` fails | Wrong rui version or plug path | Run `rui plug-test <plugin-dir> --adapter rui_xiaoai_bridge.adapter:build` inside the container |

## Known limitations

- A third-party manifest without `wake_words_residual` gets no vendor-phrase backstop.
- Two speakers start one plane by default unless `multi_device: {enabled: true, max_planes: 2}` is set.
- A self-signed certificate only starts the plane; real-device trust depends on its CA.


- LX06 numbers are historical (19/20 wake, 205.2 ms barge-in) with **no** 0.7.2 re-measurement.
- Voice-command success rate, volume, LED and concurrency are **untested**.
- Firmware differences can change uplink audio and AEC behaviour; this project does not touch the device.
- The plug runs in-process inside the audio plane (`trust=trusted` is self-asserted metadata, not a sandbox).

## Credits

The `rui-device/v1` contract and `plug-test` come from [rui](https://github.com/yes999zc/rui); the manifest follows the example plug in that contract.

## License

[MIT](LICENSE).
