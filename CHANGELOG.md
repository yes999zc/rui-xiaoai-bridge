# Changelog

All notable changes to **rui-xiaoai-bridge** are documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/spec/v2.0.0.html).

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
