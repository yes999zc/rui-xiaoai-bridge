# rui-xiaoai-bridge

**把小米 AI 音箱 Pro（LX06）作为 [rui](https://github.com/yes999zc/rui) 的语音卫星接入，但不 fork rui。**

一个 out-of-tree 的 Socket & Plug v1 设备 adapter：`plugin.yaml` + `rui-device/v1`
清单 + 进程内 adapter 包。rui 只通过 manifest 的 `runtime.entrypoint` 认识它，
内核里没有一行小爱专属代码。

> **状态：Phase 1（脚手架 + 可加载）· 2026-10-26**
> 本仓库已是 LX06 adapter 的独立实现，manifest 能被 rui 0.6.0 的 loader 解析，
> adapter 通过官方 `rui plug-test`（rui 0.6.0 main `4f00ef5`：**16 PASS / 0 FAIL /
> 0 WARN / 5 SKIP**；发布 tag `v0.6.0`：15 PASS / 0 FAIL / 1 WARN / 5 SKIP，
> WARN 是 kit 用假 config 时 `probe_layout` 读不到 manifest `audio_defaults`，非 adapter 失败。
> 见 [docs/contract-report-0.6.0.json](docs/contract-report-0.6.0.json)）。
> 但 rui 0.6.x 仍随镜像发布 in-tree 参考实现（`plugs/xiaoai/`），同 id 时它优先；
> **Phase 2 删除 in-tree 之后，本仓库才是生产安装路径**。共存规则见下文。

```
LX06 (open-xiaoai client) ──ws://<rui-host>:4412/?token=***──▶ rui audio plane
                                                              │  in-process:
                                                              │  rui_xiaoai_bridge.adapter:build
                                                              ▼
                                                        ASR / LLM / TTS ──▶ 音箱喇叭
```

## 它是什么 / 不是什么

| 是 | 不是 |
|---|---|
| 独立仓库的 LX06 device adapter（协议、LED、混音、播放收尾） | rui 的 fork，也不复制 rui 内核 |
| `rui-plugin/v0` + `rui-device/v1` 清单，声明 `rui_compat` 与 `audio_defaults` | 设备端固件/client；open-xiaoai client 仍由用户装到音箱上 |
| 进程内 adapter，运行在官方 rui 镜像的音频面里 | 独立常驻服务，不监听除 4412 设备回连以外的端口 |
| 只承诺 `devices/lx06.yaml` 里的 entrypoint | 对外 API；包内其他模块可随 minor 调整 |

**唯一公开契约**：`plugin.yaml`（插件 id `xiaoai-lx06`）、`devices/lx06.yaml`
（设备 id `lx06`、`runtime.entrypoint = rui_xiaoai_bridge.adapter:build`）和
`GET /api/v1/plugs` 暴露的 manifest 字段。

## 兼容窗口

| 项 | 值 | 说明 |
|---|---|---|
| 插件版本 | `0.1.0` | 独立于 rui 版本，semver |
| `rui_compat` | `>=0.6.0 <0.7.0` | 0.6.x 验证窗口；0.7 才允许删 in-tree / 别名 |
| 实测 rui | `0.6.0`（main `4f00ef5` 与 tag `v0.6.0`） | [contract report](docs/contract-report-0.6.0.json) |
| 设备契约 | `rui-device/v1` | inbound ws，8ch/48kHz 采集 + 2ch reference |
| plugin id / device id | `xiaoai-lx06` / `lx06` | 配置里写 `adapter: lx06` |
| 旧拼写 | `adapter: xiaoai` | 仅由 rui 0.6.x 的 `adapter_aliases.py` 提供，**本仓库不定义别名** |

上限设到 `<0.7.0` 是有意的：0.7 之前 rui 侧要保留一个 release 的重叠期，
让 in-tree 删除和本仓库接管可以分两次发布。

## 目录结构

```
plugin.yaml / devices/ 都在包内，和 adapter 同目录 —— 这样
RUI_PLUGINS_DIR 扫描、co-located manifest 查找、data_dir 安装三种路径
看到的是同一份清单。

src/rui_xiaoai_bridge/
├── plugin.yaml            # rui-plugin/v0（id xiaoai-lx06, trust trusted）
├── devices/lx06.yaml      # rui-device/v1（audio_defaults + entrypoint）
├── __init__.py            # 只导出 build / XiaoaiAdapter（入口点）
├── adapter.py             # LX06 websocket adapter（从 rui 0.6.0 迁入）
├── protocol.py            # open-xiaoai 线协议
├── led.py                 # 18 灯环状态机
└── services.py            # mysoftvol 混音
tests/                     # 7 条单测：import / manifest / catalog 语义
docs/contract-report-0.6.0.json
deploy/
├── downstream/Dockerfile  # Phase 1 预览镜像（官方 rui + 本插件）
└── install-plug-manifest.sh
```

## 本地挂载与验证

前提：一个可运行的 rui **0.6.0** checkout 或官方镜像；音箱上已装 open-xiaoai
client。下面以 rui checkout 路径 `$RUI`、本仓库路径 `$BRIDGE` 表示。

### 方式 A：`RUI_PLUGINS_DIR`（推荐做本地验证）

rui 把 `RUI_PLUGINS_DIR` 里的目录当作 **image/builtin** 根来扫描，并从 manifest
的 `runtime.entrypoint` 自动注册 adapter（`source=builtin`）：

```bash
export BRIDGE=~/AI_Workspace/01_Code/projects/rui-xiaoai-bridge
export RUI_PLUGINS_DIR="$BRIDGE/src"
export PYTHONPATH="$BRIDGE/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$RUI" && uv run rui serve --config ~/rui/config/config.yaml
```

`RUI_PLUGINS_DIR` 一旦设置，rui 不再回退到 checkout 的 `plugs/` 目录；所以这条
路径会**隐藏 in-tree 插件**，正好用来验证本仓库单独加载。

### 方式 B：`<data_dir>/plugs/`（user 来源）

```bash
sh deploy/install-plug-manifest.sh ~/rui/data
export PYTHONPATH="$BRIDGE/src${PYTHONPATH:+:$PYTHONPATH}"
export RUI_ADAPTER_PLUGINS='lx06=rui_xiaoai_bridge.adapter:build'
export RUI_DATA_DIR=~/rui/data      # 让 env hook 能找到 user manifest
```

目录出现在 `GET /api/v1/plugs` 里时 `source=user`。**注意**：rui 不会因为
manifest 在 data 目录就执行它，adapter 仍必须由 `RUI_ADAPTER_PLUGINS`（或
`rui.adapters` entry point）点名，且 manifest 必须 `trust: builtin|trusted`。

### 方式 C：下游预览镜像

```bash
docker build -f deploy/downstream/Dockerfile -t rui-xiaoai:0.1.0 .
```

镜像把本插件放到独立的 `/opt/rui-xiaoai-plugins`，并用
`RUI_PLUGINS_DIR=/opt/rui-xiaoai-plugins` 让它在 0.6.0 官方镜像里**确定性地**
压过 in-tree 同 id 插件。Phase 2 删除 in-tree 后，这个额外根会去掉，改回
`/opt/rui-plugins`。

### 验收命令

```bash
# 1) 单测（需要 rui 在 PYTHONPATH/venv 里；没有 rui 时测试会 skip 并说明原因）
python -m pytest -q
# 7 passed

# 2) 官方契约测试（manifest + adapter 面）
python -m rui plug-test src/rui_xiaoai_bridge \
  --adapter rui_xiaoai_bridge.adapter:build
# summary: pass=16 fail=0 warn=0 skip=5 -> PASS

# 3) 目录/API 识别（在 rui checkout 里、把清单装进 data_dir 后）
python - <<'PY'
from fastapi.testclient import TestClient
from rui.config import Config
from rui.web.api.app import create_app
cfg = Config(); cfg.system.data_dir = "/tmp/rui-data"
plug = [p for p in TestClient(create_app(cfg)).get("/api/v1/plugs").json()["plugs"]
        if p["id"] == "xiaoai-lx06"][0]
print(plug["source"], plug["available"], plug["adapter"], plug["devices"])
PY
# user True lx06 ['lx06']
```

Phase 1 的完整证据（命令 + 输出）记录在 rui 仓库
`docs/plan/xiaoai-pro-bridge.md` 的「Phase 1 进度」小节。

## 与 in-tree 插件的共存 / 冲突

rui 0.6.x 的规则（`PlugCatalog` + `device/registry.py`）：

1. **同 plugin id 时 builtin 胜出。** builtin 先入表，user 条目用 `setdefault`
   合并；user 同 id 副本不会被静默丢弃，`GET /api/v1/plugs` 会额外返回一条
   `available=false`、`error=... duplicate plugin id ... the image plug wins`。
2. **builtin adapter 名不可覆盖。** `RUI_ADAPTER_PLUGINS` 注册 `lx06` 时，如果
   in-tree 已注册同名 builtin，会被拒绝（`BuiltinAdapterName`），只留一条 warning。
   所以「只把清单装进 data_dir」在 0.6.0 官方镜像里**不会生效**。
3. **Phase 1 预览镜像用优先级解决**：把本插件放进 `RUI_PLUGINS_DIR` 的独立根，
   env 根先于镜像根扫描，同 id 时本插件先入表、in-tree 变成 duplicate warning。
   这是显式选择，不依赖字母序。
4. **Phase 2 正解**：rui 删除 `plugs/xiaoai/`（并随 0.7 删 `adapter_aliases.py`），
   本仓库清单进入 `/opt/rui-plugins`，冲突从根上消失。

## 发布与版本约定

- **插件版本**（`plugin.yaml: version` / git tag `vX.Y.Z`）与 rui 解耦：
  - patch：adapter 修复，不改 manifest 语义；
  - minor：新增能力/参数（向后兼容）；
  - major：改 plugin id、device id、transport 或 entrypoint 等契约。
- **`rui_compat`**：下界 = 实际跑过 `plug-test` + 真机回归的最低 rui；上界 =
  下一个可能破坏 device contract 的里程碑（当前 0.7.0）。升 rui 之前先发本仓库
  的兼容版本，再由 rui pin 住，**禁止 rui 依赖未发布的 bridge 改动**。
- **每个 rui minor 跑一次契约测试**，产出 `docs/contract-report-<rui>.json`；
  README 徽章/状态只引用这份报告。
- **部署 pin digest，不 pin 浮动 tag**。当前基线与 rui 0.6.0 发布 digest
  （`sha256:abef1f…b241`，linux/amd64 + linux/arm64）一致，写在
  `deploy/downstream/Dockerfile` 与 contract report 的 `upstream_pin`。
- **发布顺序**：bridge 发兼容版本 → 下游镜像 pin/验证 → rui 删 in-tree → 0.7
  再删别名。任何一步失败都回滚到上一个已 pin 的 digest。

## Phase 2 建议（下一步）

1. **真机回归**：用 open-xiaoai client 跑唤醒、播放、barge、音量、灯环，
   把结果补进 `acceptance` 和 report（Phase 1 只验证了 host-free 契约）。
2. **rui 侧清理**：删除 `plugs/xiaoai/`、更新 `tests/test_xiaoai_plug.py` 与
   `pyproject.toml` 的 `pythonpath`；0.7 再删 `adapter_aliases.py`。
3. **发布流水线**：给本仓库加镜像 publish + digest 回写，复用 dot2 的
   `docs/contract-report-*.json` 形状。
4. **配置迁移**：`adapter: xiaoai` → `adapter: lx06`（0.6.x 靠别名过渡）。

## License 与出处

MIT，见 [LICENSE](LICENSE)。`src/rui_xiaoai_bridge/` 下的 adapter/protocol/led/
services 复制自 **rui 0.6.0**（commit `4f00ef5`）的 `plugs/xiaoai/xiaoai_plug/`，
保留了 MIT 版权头与每个文件的 provenance 注释。线协议来自
[open-xiaoai](https://github.com/coderzc/open-xiaoai)（MIT）；本仓库**没有复制**
Apache-2.0 代码，也不分发固件、镜像或密钥。
