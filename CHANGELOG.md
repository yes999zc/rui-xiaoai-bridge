# Changelog

All notable changes to **rui-xiaoai-bridge** are documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2026-10-26

### Fixed

- **连接替换后播放器不复位**（rui#25 / xiaoai#1）：设备重连时旧 socket 被替换，但
  `_playing` / `consumed` / `sink_generation` 仍停留在旧代际，新连接的首个 `play()` 跳过
  `start_play`——表现为重连后整首歌静音、或被误判为「已播完」。现在替换连接时统一
  `_reset_media_state()`；挂起的旧 `play()` 也不会复活旧代际，旧 socket 的 `consumed`
  事件不再推进新队列。
- 镜像 house-ear 的修复（house `4468521`、本仓 `8f3ac46`）；`rui_compat` 维持
  `">=0.6.0 <0.8.0"`，版本 0.2.1 → **0.2.2**。

### Verified

- 新增四条 fake 连接测试：① mid-play 替换后新连接首个 `play()` 必发 `start_play`；
  ② 旧 handler 的 `finally` 不会清掉新连接状态；③ 卡在 `start_play` 的旧 `play()`
  在替换后不会复活旧代际；④ 旧连接替换后发来的 `consumed` 不推进新玩家。
- `PYTHONPATH=src pytest -q` → 13 passed；`ruff check src tests` 绿。

## [0.2.1] - 2026-10-26

### Changed

- Plugin 版本 0.2.0 → **0.2.1**；`rui_compat` 维持 `">=0.6.0 <0.8.0"`。
- 仓库**公开**：公开前完成全历史扫描（token / 私钥 / 内网 IP / 个人绝对路径 / MAC 均为 0），
  公开后启用 secret scanning 与 push protection。README 重写为中英双语，设备准备写成
  「前置条件」而不是任何设备侧操作步骤。

### Verified

- 9 项插件契约测试通过（`rui plug-test`，见 README）。
- 其余能力（语音指令成功率、音量、指示灯、多设备并发）**未测**。

### Historical measurements (2026-10-24, not re-tested)

- 唤醒 19/20；播放中打断停播延迟 205.2 ms（**stop-push 判据**；当日三轮 24.2/64.5/205.2，max n=3）。
- 来自 2026-10-24 的真机轮次，0.7.2 / 0.7.3 未复测；引用时必须带日期与分母。

## [0.2.0] - 2026-10-25

### Changed

- 与 rui 0.7.0 对齐：`rui_compat` 抬到 `">=0.6.0 <0.8.0"`；插件作为 out-of-tree 设备接入，
  核心不含设备专用代码。

## [0.1.0] - 2026-10-24

### Added

- 首个可用版本：`rui-device/v1` 设备清单 + 进程内 adapter（LX06，入站音频）。
