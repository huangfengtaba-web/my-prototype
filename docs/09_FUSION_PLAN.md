# 嘉定 GTX · 真融合改造计划（Zcode 严格执行版）

> 工程根：`D:\codex\2026-10-28-23-35-39`
> 计划生成：2026-10-29 22:30｜修订：2026-10-29 22:40（Dify 改线上搭建）
> 执行方：Zcode｜验收方：WorkBuddy + 用户
> **每条任务都有可命令验证的验收标准，不达标即视为未完成。**

---

## 0. 为什么上一版没做成「整合」—— 三个真实原因

| # | 问题 | 证据 |
|---|---|---|
| 1 | 计划文档把 SemiconFab 定位成「参考」而非「必须嵌入」 | `docs/02_INTEGRATION_GUIDE.md` §1.3 映射写的是 `SimPy 仿真模块 → 参考` |
| 2 | CHECKLIST 明文许可跳过 | `CHECKLIST.md` §8 写着 `❌ 不移植 SemiconFab 的 SimPy 仿真` |
| 3 | 按「最小可演示」拆成了拼接而非融合 | 前端用 A、骨架用 B、C 只作叙事参考 |

**结果**：Zcode 把 SemiconFab 的「叙事」抄成了一个新页面（`frontend/src/pages/simulation/`），原站 26 个页面成了死代码。

**本计划的核心纠正**：SemiconFab 的 3D 孪生引擎是**必须接入的运行时**，不是参考资料。

---

## 1. 目标与总验收（三个必须能现场演示的场景）

### 场景 A：排程 → 3D 回放（核心诉求）

打开 `http://localhost:5173/twin`，点「加载排程」，3D 洁净室里：
- 6 台光刻机（IMM01~IMM06）按时间轴依次亮起/熄灭（SEMI E10 Busy/Idle）
- OHT 小车沿 AMHS 单轨移动，把光罩从 Stocker 送到对应机台
- 时间轴可拖动、可暂停、可 1x/2x/4x 变速
- 侧面板显示当前时刻的 Lot 在机台加工状态

### 场景 B：Dify 线上工作流（用户线上搭建）

打开 `/ai-workflow` 页：
- 选「日计划排程」→ 运行 → 页面显示 Dify 返回的**节点级执行链路**（node_started / node_finished 事件流）
- 环境变量未配 / Dify 不可达时，自动降级并提示「Dify 未连接，已切换本地模式」

> **重要**：本项目**不在本地安装/构建 Dify**。用户在自己线上的 Dify 里搭好工作流，
> 把 `DIFY_BASE` + 3 个 App Key 填进 `.env`，项目即可调用。

### 场景 C：WPS 文档生成

在 `/reports` 页点「生成排程报告」：
- 服务端真实调 WPS COM，产出 `排程报告.docx` + `.pdf`
- 产出 `排程明细.xlsx`（Lot/Eqp/Reticle 三个 sheet）
- 产出 `排程汇报.pptx`（用 pptengine，非 CLI impress）
- 前端能下载

---

## 2. 现状诊断（必须先修的坑）

| # | 问题 | 位置 | 严重度 |
|---|---|---|---|
| D1 | `vercel.json` 兜底 rewrite `/(.*) → /index.html` 会把 `/simulation`、`/ai-workflow`、`/ai-agent`、`/twin` **全部改成总览页** | `frontend/vercel.json` | **致命** |
| D2 | 总览页 KPI 硬编码 `8台/120批/156枚/3处`，与后端真实 `6机台/10 Lot/5光罩` 直接矛盾 | `frontend/index.html` L172/177/182/187 | **高** |
| D3 | 总览页 9 张入口卡**无一**通往 4 个智能页 | `frontend/index.html` | **高** |
| D4 | `workflow.py` 是 `TEMPLATES` 字典 + for 循环 + 线程，**与 Dify 零关系** | `backend/app/workflow.py` L130-216 | **高** |
| D5 | `agent` 默认 7 条正则，`agent_mode: "rule"` | `backend/app/agent/` | 中（保留作保底，不能宣称是 AI） |
| D6 | `git remote origin` 指向 `gtx-fso-litho`，但决定推 `my-prototype` | `git remote -v` | 中 |
| D7 | `frontend/vite.config.js` 有未提交改动（`host: true`） | git status | 低 |
| D8 | twin.html 的 `mimacMid` 按渲染顺序自增生成（L14229/14306），**不冻结就与 IMM01~06 对不上** | `vendor/.../twin.html` | **高** |

---

## 3. 已确认的技术锚点（直接用，不要重新探索）

### 3.1 twin.html（24,779 行，无 IIFE 顶层脚本，Three.js r128 纯程序化几何）

| 锚点 | 行号 | 用途 |
|---|---|---|
| `mimacMid` 生成 | 14229 / 14306 | 设备 ID 映射，**必须先冻结** |
| `applyResearchStateAtTime(timeSec)` | 14661 | **已有时间轴函数**，含二分查表，直接复用 |
| `ohtVehicles` 数组 | 15355 / 15379 / 15657 | OHT 小车，已挂 `window.ohtVehicles` |
| `manualSetEquipmentState(eqId, newState)` | 22502 | **已有设备状态函数**，直接调用 |

**结论**：注入通道现成，无需重构。只需 4 处增量插入约 270 行，暴露统一 API。

### 3.2 现有后端接口（12 个，契约不许改）

```
GET  /api/health          GET  /api/mock/data       GET  /api/cases
POST /api/solve/run       GET  /api/solve/result/{run_id}
POST /api/sim/run
GET  /api/workflow/templates   POST /api/workflow/run
GET  /api/workflow/status/{wf_id}   GET /api/workflow/list
GET  /api/agent/status    POST /api/agent/chat
```

### 3.3 排程输出结构（`run_summary.json`）

```json
{
  "milp_status": {"step2":"Optimal","step3":"Optimal"},
  "schedule": [
    {"lot":"LOT-A01","eqp":"IMM03","eqp_group":"...","reticle":"RT-0101",
     "priority":"PRI1","temp":"...","start":"10:00","end":"10:25",
     "barc_er":"09:45","barc_lr":"...","post_note":"-"}
  ],
  "reticles": {"RT-0101": {"status":"...","note":"...","ready":"09:45"}},
  "story_check": {...}
}
```

### 3.4 WPS CLI 事实

- 包名 `cli-anything-wps`，Click CLI，**无 HTTP 模式**，全靠 WPS COM（pywin32）
- 本机 COM 已注册：`KWPS.Application` / `KET.Application` / `KWPP.Application`
- 必须**进程内 import core + 单 worker 串行**（COM 非线程安全），不要 subprocess 逐条调
- PPT 用 `pptengine`（`tools/harness-anything/WPS/ppt-engine/`），CLI 的 impress 只能写标题+正文
- 项目 venv 缺 `win32com`、`pptx`

### 3.5 Dify 事实（线上版，不本地部署）

- API 根：线上 `https://api.dify.ai/v1`（或用户自托管域名 + `/v1`）
- 鉴权：`Authorization: Bearer app-xxx`，**每个工作流一个独立 App Key**
- 端点：`POST /v1/workflows/run`（`blocking` / `streaming` SSE），`GET /v1/parameters`
- 限制：**blocking 模式 Cloudflare 100s 超时**；代码节点禁出站网络、禁文件系统、禁系统命令
- 工作流可导出为 DSL YAML（不含 Key），可进 git 作版本基线
- **Key 只能放后端**，前端内嵌等同泄露

---

## 4. 分阶段实施（严格按序，每阶段独立验收）

### P0 · 修复致命坑（先做，否则后面白干）

**P0-1 修 vercel.json**

`frontend/vercel.json` → 显式声明所有多页路由，**删掉兜底 rewrite**：

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "cleanUrls": true,
  "rewrites": [
    { "source": "/twin", "destination": "/vendor-twin/twin.html" },
    { "source": "/twin/:path*", "destination": "/vendor-twin/:path*" },
    { "source": "/prototypes/:path*", "destination": "/prototypes/:path*" },
    { "source": "/simulation", "destination": "/src/pages/simulation/index.html" },
    { "source": "/ai-agent", "destination": "/src/pages/ai-agent/index.html" },
    { "source": "/ai-workflow", "destination": "/src/pages/ai-workflow/index.html" },
    { "source": "/scheduling-test", "destination": "/src/pages/scheduling-test/index.html" },
    { "source": "/reports", "destination": "/src/pages/reports/index.html" }
  ]
}
```

**验收**：`npm run build` 后 `dist/vendor-twin/twin.html` 存在；`curl /simulation` 返回 200 且 `grep -c "仿真验证" > 0`（证明确实是仿真页不是总览页）。

**P0-2 修总览页 KPI 与入口卡**

`frontend/index.html`：
- L172/177/182/187 的 `8 / 120 / 156 / 3` → 从 `GET /api/mock/data` 读真实值（机台数 / Lot 数 / 光罩数 / 异常数），失败显示 `—` 而非假数字
- 9 张入口卡补 4 张：仿真验证 `/simulation`、AI 助手 `/ai-agent`、AI 工作流 `/ai-workflow`、数字孪生 `/twin`

**验收**：页面加载后 KPI 显示 `6 / 10 / 5 / N`；Network 面板可见 `/api/mock/data`；4 个新卡片可点通。

**P0-3 建 `.env.example`**

```ini
# ===== 后端 =====
LITHO_CORS_ORIGINS=http://localhost:5173
LITHO_SOLVER=CBC

# ===== Dify 线上（用户自己填，不填则自动降级本地模式）=====
DIFY_BASE=https://api.dify.ai/v1
DIFY_KEY_DAILY_SCHEDULING=
DIFY_KEY_SCENARIO_COMPARE=
DIFY_KEY_QA_CHATFLOW=

# 供线上 Dify 的 HTTP 节点回调本地后端（内网穿透地址）
API_PUBLIC_BASE=

# ===== WPS 文档生成 =====
DOCGEN_ENABLED=1
DOCGEN_OUT_DIR=./output/doc
```

**验收**：`.env.example` 存在且字段齐全；`.gitignore` 已包含 `.env`（已有）。

---

### P1 · 深度联动：3D 孪生时间轴回放（核心诉求）

#### P1-1 冻结设备 layout，稳定 mimacMid 映射

`vendor/semiconfab-fork/` → **复制**为 `vendor/semiconfab-gtx/`（原目录不改，便于同步上游）

在 `vendor/semiconfab-gtx/twin.html`：
- L14229 / L14306 的 `mimacMid` 生成改为**从冻结的 layout JSON 读取**，不按渲染顺序自增
- 新增 `vendor/semiconfab-gtx/gtx-layout-map.json`：
  ```json
  {"IMM01":"LIT_01","IMM02":"LIT_02","IMM03":"LIT_03",
   "IMM04":"LIT_04","IMM05":"LIT_05","IMM06":"LIT_06"}
  ```
- 初始化时校验：映射表每个 GTX 机台必须能在场景里找到，否则 `console.error` 并降级为「仅驱动 Lot 面板」

**验收**：控制台输出 `[gtxTwin] layout map OK: 6/6 eqp resolved`。

#### P1-2 暴露 window.gtxTwinApi（约 270 行，4 个插入点）

| 插入点 | 内容 |
|---|---|
| L14306 之后 | `const GTX_LAYOUT_MAP = {...}` 与 `resolveEqpId(gtxEqpId)` |
| L14661 之后 | `function gtxSeekTo(timeSec)` —— 复用 `applyResearchStateAtTime` 的二分查表，再叠加排程事件 |
| L15379 之后 | `function gtxMoveOht(vehicleId, fromPos, toPos, durationSec)` —— 驱动 `ohtVehicles[i].s` |
| L22502 之后 | `window.gtxTwinApi = {...}` |

API 契约（**冻结，签名不许改**）：

```js
window.gtxTwinApi = {
  version: '1.0',
  loadSchedule: (timeline) => {},   // timeline 见 P1-3 契约
  play: () => {},
  pause: () => {},
  seek: (timeSec) => {},
  setTime: (timeSec) => {},
  setSpeed: (x) => {},              // 0.5 / 1 / 2 / 4
  getState: () => ({ timeSec, eqp: {...}, oht: [...] })
}
```

**验收**：控制台 `gtxTwinApi.loadSchedule({...})` 后 `play()`，`getState().eqp` 随时间变化。

#### P1-3 后端新增时间轴接口

新增 `backend/app/twin_timeline.py`：

```python
def build_timeline(run_summary: dict) -> dict:
    """把 run_summary.json 转成孪生可消费的时间轴事件流。"""
```

输出契约（**冻结**）：

```json
{
  "run_id": "abc123",
  "baseDate": "2025-10-23",
  "t0": "09:00",
  "t1": "11:10",
  "events": [
    {"t": 600, "type": "eqp_state", "target": "IMM01", "state": "Busy", "lot": "LOT-A01"},
    {"t": 625, "type": "eqp_state", "target": "IMM01", "state": "Idle"},
    {"t": 540, "type": "reticle_move", "target": "RT-0101",
     "from": "STOCKER-01", "to": "IMM01", "vehicle": "OHT-03"},
    {"t": 555, "type": "reticle_state", "target": "RT-0101", "state": "装载"}
  ]
}
```

- `t` 单位**秒，相对 t0**
- `type` 只允许 `eqp_state` / `reticle_move` / `reticle_state`
- 事件按 `t` 升序

`backend/app/api.py` 新增：
```python
@app.get("/api/twin/timeline/{run_id}")
```

**验收**：`curl /api/twin/timeline/<run_id>` 返回上述结构，`events` 数量 > 0 且按 t 升序。

#### P1-4 前端挂载 twin 页 + 时间轴控制条

- `vendor/semiconfab-gtx/` 纳入 Vite 静态资源（build 时 copy 到 `dist/vendor-twin/`）
- 新增 `frontend/src/pages/twin-control/`：**不改 twin.html 的 UI**，用独立控制面板，通过同源 `window.gtxTwinApi` 驱动
- 控制条：`▶/⏸`、进度条（可拖动）、速度 `0.5x/1x/2x/4x`、当前时刻、Lot 状态面板

**验收**：`/twin` → 点「加载排程」→ IMM 机台按时间轴亮灭 + OHT 移动 + 进度条拖动可跳转。

---

### P2 · Dify 线上工作流接入（**不装 Docker，不做本地构建**）

> 用户在自己线上的 Dify 搭工作流，项目只做「调它」和「被它调」两件事。

#### P2-1 项目侧只做配置与客户端

新增 `backend/app/ai/dify_client.py`：

```python
import os, httpx

DIFY_BASE = os.getenv("DIFY_BASE", "").rstrip("/")
KEYS = {
    "daily_scheduling": os.getenv("DIFY_KEY_DAILY_SCHEDULING", ""),
    "scenario_compare": os.getenv("DIFY_KEY_SCENARIO_COMPARE", ""),
    "qa_chatflow":      os.getenv("DIFY_KEY_QA_CHATFLOW", ""),
}

def is_available(wf_key: str) -> bool:
    """KEY 未配 或 /v1/parameters 探测失败 → False"""

def run_workflow(wf_key: str, inputs: dict, user: str = "gtx-demo",
                 stream: bool = False, timeout: int = 90):
    """POST {DIFY_BASE}/workflows/run，返回统一结构：
       {"mode":"dify","workflow_run_id":...,"status":...,"outputs":{...},"elapsed":...}
       异常时抛 DifyUnavailable，由上层降级"""
```

**约束**：
- Key **只能放后端**，禁止任何前端代码读 `DIFY_KEY_*`
- blocking 模式加 `timeout=90`（Cloudflare 100s 上限留余量）
- 长流程一律走 `streaming`，后端用 SSE 透传给前端

**不做的事**：不建 `docker/dify/`、不写 docker-compose、不下载 Dify 镜像。

#### P2-2 六类可用 Dify 承载的能力（职责划分）

| # | 能力 | Dify 类型 | 节点链 | 调用的项目接口 |
|---|---|---|---|---|
| 1 | **日计划排程编排** | Workflow | 开始 → HTTP(`/api/solve/run`) → LLM 解释 → 结束 | POST `/api/solve/run` |
| 2 | **场景对比**（基线 vs 急货） | Workflow | 开始 → 并行 HTTP ×2 → LLM 差异分析 → 结束 | POST `/api/solve/run` ×2 |
| 3 | **排程异常诊断** | Workflow | 开始 → HTTP(`/api/solve/result/{id}`) → LLM 归因 → 结束 | GET `/api/solve/result/{run_id}` |
| 4 | **智能问答** | Chatflow | 开始 → 知识库检索 → LLM → 结束 | 无（纯 RAG）或调 `/api/mock/data` |
| 5 | **光罩五态推演解读** | Workflow | 开始 → HTTP(`/api/solve/result`) → LLM 生成说明 | GET `/api/solve/result/{run_id}` |
| 6 | **报表生成编排** | Workflow | 开始 → HTTP(`/api/doc/render`) → 输出下载链接 | POST `/api/doc/render` |

**不能用 Dify 承载的（必须留 Python）**：

| 能力 | 原因 |
|---|---|
| MILP 求解本体（PuLP + CBC） | Dify 代码节点禁出站网络、禁系统命令，无 CBC 二进制 |
| WPS COM 文档生成 | 需 Windows 桌面会话 + COM，容器内必失败 |
| 3D 孪生时间轴高频推送 | 毫秒级驱动，Dify 的 HTTP 往返不适合 |
| 数据落库 / 批量作业 | 需长事务与幂等，不适合工作流引擎 |

#### P2-3 双向接口契约（交接清单）

**A. 项目 → Dify（项目调线上 Dify）**

```
POST {DIFY_BASE}/workflows/run
Authorization: Bearer {对应 App Key}
Content-Type: application/json

{
  "inputs": { "case": "urgent-A01", "run_id": "abc123" },
  "response_mode": "blocking",     // 或 "streaming"
  "user": "gtx-demo-001"
}
```

三个 App Key 与工作流一一对应：

| 环境变量 | 对应 Dify 工作流 | 用途 |
|---|---|---|
| `DIFY_KEY_DAILY_SCHEDULING` | 日计划排程 | 能力 1 |
| `DIFY_KEY_SCENARIO_COMPARE` | 场景对比 | 能力 2 |
| `DIFY_KEY_QA_CHATFLOW` | 智能问答 | 能力 4 |

**B. Dify → 项目（线上 Dify 的 HTTP 节点回调本地后端）**

Dify 里的 HTTP Request 节点，Base URL 填 `{{API_PUBLIC_BASE}}`：

| 方法 | 路径 | 用途 | 请求体 |
|---|---|---|---|
| GET | `/api/health` | 探活 | — |
| GET | `/api/mock/data` | 拿机台/Lot/光罩/配置 | — |
| GET | `/api/cases` | 用例列表（给下拉） | — |
| POST | `/api/solve/run` | 跑六步 MILP | `{"case":"urgent-A01"}` |
| GET | `/api/solve/result/{run_id}` | 取排程结果 | — |
| POST | `/api/sim/run` | 跑执行态仿真 | `{"run_id":"...","seed":42}` |
| GET | `/api/twin/timeline/{run_id}` | 拿 3D 时间轴 | — |
| POST | `/api/doc/render` | 生成文档 | `{"kind":"docx","filename":"排程报告"}` |

#### P2-4 线上 Dify 如何回调本地后端（关键）

线上 Dify 访问不到 `localhost:8000`，必须给一个公网可达地址：

```powershell
# 方案 A：cloudflared（推荐，免费稳定）
cloudflared tunnel --url http://localhost:8000
# 输出形如 https://xxx-yyy-zzz.trycloudflare.com

# 方案 B：ngrok
ngrok http 8000
```

把得到的公网地址填进 `.env` 的 `API_PUBLIC_BASE`，再填到 Dify HTTP 节点的 Base URL。

**安全提示**：公网隧道暴露后端时，`.env` 里设 `LITHO_CORS_ORIGINS` 精确域名，不要用 `*`。

**验收**：`curl {API_PUBLIC_BASE}/api/health` 从外网返回 200。

#### P2-5 DSL 骨架留档（给用户线上导入用）

`dify/dsl/` 只作为**导入模板**（含节点结构，不含 Key）：

| 文件 | 工作流 | 节点链 |
|---|---|---|
| `daily-scheduling.yaml` | 日计划排程 | 开始 → HTTP → LLM → 结束 |
| `scenario-compare.yaml` | 场景对比 | 开始 → 并行 HTTP ×2 → LLM → 结束 |
| `qa-chatflow.yaml` | 智能问答 | 开始 → 知识库 → LLM → 结束 |

**用途**：用户在线上 Dify 里 `导入 DSL`，再把 HTTP 节点的 Base URL 改成自己的 `API_PUBLIC_BASE`，填好模型即可用。

#### P2-6 后端接口改造（优先 Dify，失败降级）

改造 `backend/app/workflow.py`：
- `run_workflow_sync` 保留为 **fallback**
- `TEMPLATES` 降级为「模板元数据」（id/name/desc + 对应 Dify app 名）
- `/api/workflow/run` 逻辑：
  ```
  1. dify_client.is_available(wf_key) → 可用则走 Dify
  2. 返回 {"mode":"dify", "workflow_run_id":..., "outputs":...}
  3. 不可用/超时/报错 → 走本地 run_workflow_sync
  4. 返回 {"mode":"local_fallback", ...}，HTTP 仍 200
  ```
- `/api/workflow/templates` 返回值增加 `dify_configured: true/false` 字段

**验收**：
1. `.env` 配好 Key + 线上 Dify 可达 → `/api/workflow/run` 返回 `"mode":"dify"` 且有 `workflow_run_id`
2. 把 Key 清空 → 同一接口返回 `"mode":"local_fallback"`，200 不报错
3. 前端顶部有模式徽章

#### P2-7 前端 ai-workflow 页改为真执行链路

`frontend/src/pages/ai-workflow/script.js`：
- 从 `/api/workflow/templates` 拉模板元数据（含 `dify_configured`）
- 运行后展示**节点级执行流**（node_started / node_finished / 耗时），而非静态流程图
- 顶部 `mode` 徽章：`Dify 线上` / `本地降级`

**验收**：两种模式下都有真实事件流，不是硬编码动画。

---

### P3 · WPS CLI 文档生成（用户诉求 2）

#### P3-1 依赖与环境

```powershell
pip install -e "D:/工作/嘉定GTX/GTX_FSO_交付物/tools/harness-anything"
pip install pywin32 click
```

`backend/requirements.txt` 追加：
```
pywin32>=306 ; sys_platform == "win32"
python-pptx>=0.6.23
```

#### P3-2 单 worker COM 服务

新增 `backend/app/docgen/wps_worker.py`：
- 单线程 + 队列 + `pythoncom.CoInitialize()`，**天然串行**，避免 WPS 单实例冲突
- 进程内 `from cli_anything.wps.core import export`，**不要 subprocess 逐条调**（每条起一次 COM，15 元素报告 ≈ 15 次起停）
- 超时 60s；失败 `taskkill /F /IM wps.exe` 重试 1 次；再失败降级 `python-docx`
- `DOCGEN_ENABLED`（默认 `1`），云端设 `0` 返回 503

新增 `backend/app/docgen/renderers.py`：

| 产物 | 实现 |
|---|---|
| 排程报告 docx | `cli_anything.wps.core` project schema → `export.export(..., preset="docx")` |
| 排程报告 pdf | 同上 `preset="pdf"` |
| 排程明细 xlsx | `calc` 域，3 sheet：Lot / Eqp / Reticle |
| 排程汇报 pptx | **pptengine**（`Deck` + `el.*`），不走 CLI impress |
| 套模板正式文档 | `Documents.Open(模板.docx)` → `Content.Find.Execute` 替换占位符 → `SaveAs` |

**套模板占位符约定**（写进 `docs/07_DOCGEN.md`）：

```
{{RUN_ID}} {{BATCH}} {{DATE}} {{MODEL}}
{{TABLE_STEP2}}   ← 整表替换
{{TABLE_STEP3}}
{{SUMMARY_TEXT}}
```

#### P3-3 接口

```python
POST /api/doc/render    # {kind, filename, run_id?} → 200 FileResponse 或 202 {job_id}
GET  /api/doc/file/{job_id}
GET  /api/doc/status/{job_id}
```

**验收**（必须真跑）：
1. `curl -X POST /api/doc/render -d '{"kind":"docx","filename":"排程报告"}'` → 200，`output/doc/` 下出现 `.docx`
2. 打开 docx，内容含真实 Lot 数据（不是占位符）
3. pdf 生成成功且页数 > 0
4. xlsx 三个 sheet 都在
5. pptx 用 WPS 打开无错版

---

### P4 · reports 页 + 全站导航

新增 `frontend/src/pages/reports/`：
- 三个按钮：生成报告(docx) / 生成明细(xlsx) / 生成汇报(pptx)
- 生成中状态、下载链接、失败降级提示

`frontend/src/pages/_shared/` 侧边栏补 5 项：

```
系统总览         /
数据接入         /prototypes/data_zone.html
数据配置         /prototypes/config_zone.html
模型管理         /prototypes/model_zone.html
Litho 排程       /prototypes/result_litho.html
Reticle 排程     /prototypes/result_reticle.html
系统日志         /prototypes/log_zone.html
─────────────
仿真验证         /simulation
数字孪生         /twin
求解演示         /scheduling-test
AI 助手          /ai-agent
AI 工作流        /ai-workflow
报告生成         /reports
```

**验收**：侧边栏 13 项全可点，无 404。

---

## 5. VSCode 构建与推送（用户诉求 5）

### 5.1 首次构建

**后端**
```powershell
cd D:\codex\2026-10-28-23-35-39
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
pip install -e "D:\工作\嘉定GTX\GTX_FSO_交付物\tools\harness-anything"
pip install pywin32

# 配环境变量（复制模板后填 Key）
Copy-Item .env.example .env
# 编辑 .env：填 DIFY_BASE / DIFY_KEY_* / API_PUBLIC_BASE（不填也能跑，走本地降级）
```

**前端**
```powershell
cd D:\codex\2026-10-28-23-35-39\frontend
npm install
npm run build      # 产物在 frontend\dist\
npm run dev        # 开发：http://localhost:5173
```

**两个服务一起起**（VSCode 开 2 个终端）
```powershell
# 终端1 后端
.venv\Scripts\python.exe -m uvicorn backend.app.api:app --reload --port 8000
# 终端2 前端
cd frontend; npm run dev
```

> **不需要装 Dify**。Dify 在你线上，只需把地址和 Key 写进 `.env`。

**如果要让线上 Dify 回调本地后端**（可选，仅端到端联调时需要）
```powershell
cloudflared tunnel --url http://localhost:8000
# 把输出的 https://xxx.trycloudflare.com 填进 .env 的 API_PUBLIC_BASE
```

### 5.2 推送到 my-prototype 新分支

**当前状态**：`origin` 指向 `gtx-fso-litho`，需改成 `my-prototype`。

```powershell
cd D:\codex\2026-10-28-23-35-39

# 1) 改 remote（旧地址留作 backup）
git remote rename origin origin-gtx
git remote add origin https://github.com/huangfengtaba-web/my-prototype.git

# 2) 确认工作区
git status

# 3) 提交
git add -A
git commit -m "feat: 真融合 SemiconFab 3D 孪生 + Dify 线上工作流 + WPS 文档生成

- P0 修复 vercel.json 吞页 / 总览页 KPI 硬编码 / 入口卡缺失
- P1 twin.html 暴露 window.gtxTwinApi，六步排程时间轴驱动 3D 回放
- P2 接入线上 Dify 工作流（配置驱动 + 优雅降级，不做本地部署）
- P3 WPS COM 单 worker 文档生成（docx/pdf/xlsx/pptx/套模板）
- P4 补 reports 页与 13 项全站导航"

# 4) 开新分支推送（不污染 main）
git branch -M feat/gtx-fab-fusion
git push -u origin feat/gtx-fab-fusion
```

**验收**：
- GitHub `my-prototype` 出现 `feat/gtx-fab-fusion` 分支
- `main` **未被动过**，你原 Vercel 站点不受影响
- 分支里能看到 `vendor/semiconfab-gtx/`、`dify/dsl/`、`backend/app/docgen/`、`.env.example`

### 5.3 日常推送

```powershell
git add -A
git commit -m "fix: xxx"
git push
```

---

## 6. 给 Zcode 的强制指令（复制粘贴用）

```
你在改造 D:\codex\2026-10-28-23-35-39 这个工程。严格执行
C:\Users\huangjunwen\.workbuddy\plans\electric-nebula-curie-2WRIzaVz.md，
按 P0 → P1 → P3 → P2 → P4 顺序做，每个阶段做完必须跑验收命令。

【禁止事项 —— 违反即返工】
1. 禁止把 SemiconFab 当"参考"。twin.html 是必须接入的运行时。
2. 禁止新建"仿制"页面替代 twin.html。必须直接改造 vendor/semiconfab-gtx/twin.html。
3. 禁止改 vendor/semiconfab-fork/（原目录保留，用于同步上游）。
4. 禁止改动现有 12 个 /api/* 接口的契约（只能新增，不能改签名）。
5. 【重要】Dify 不做本地部署：禁止创建 docker/dify/、禁止写 docker-compose、
   禁止下载 Dify 镜像。Dify 由用户线上搭建，项目只做配置 + 客户端调用。
6. 禁止把 DIFY_KEY_* 暴露到前端任何代码里（只能后端读环境变量）。
7. 禁止在 Dify 代码节点里跑 CBC 求解或调 WPS COM（沙箱禁网络与系统命令）。
8. 禁止用 subprocess 逐条调 cli-anything-wps（每条起一次 COM，会卡死）。
9. 禁止在 index.html 保留任何硬编码数字（8/120/156/3 必须改真实数据）。
10. 禁止保留 vercel.json 的 /(.*) → /index.html 兜底 rewrite。
11. 禁止把 workflow.py 说成是 Dify（它只是本地 fallback）。
12. 禁止改 docs/specs/ 与 docs/_DESIGN_SPEC.md（设计基线只读）。

【技术锚点 —— 直接用，不要重新探索】
- twin.html 24,779 行，Three.js r128，无 IIFE
- applyResearchStateAtTime(timeSec) 在 L14661（已有，直接复用）
- ohtVehicles 在 L15355/15379/15657，已挂 window.ohtVehicles
- manualSetEquipmentState(eqId, newState) 在 L22502（已有，直接调用）
- mimacMid 生成在 L14229/14306（必须冻结，否则与 IMM01~06 对不上）
- 时间轴契约：{"t": 秒(相对t0), "type": "eqp_state|reticle_move|reticle_state", ...}，按 t 升序
- gtxTwinApi 契约见计划 §P1-2，签名不许改
- Dify API：POST {DIFY_BASE}/workflows/run，Bearer {AppKey}，
  body {"inputs":{...},"response_mode":"blocking","user":"gtx-demo-001"}
- 三个 App Key 分别对应：日计划排程 / 场景对比 / 智能问答
- Dify 回调本地后端的 8 个接口见计划 §P2-3 表 B
- WPS: 进程内 import core + 单 worker + pythoncom.CoInitialize()
- PPT 用 pptengine，不用 CLI impress

【每阶段验收（不通过不许进下一阶段）】
P0: curl /simulation 返回 200 且 grep -c "仿真验证" > 0；KPI 显示 6/10/5；
    .env.example 存在
P1: 控制台有 [gtxTwin] layout map OK: 6/6 eqp resolved；
    gtxTwinApi.play() 后 getState().eqp 随时间变化；
    curl /api/twin/timeline/<run_id> 事件按 t 升序
P2: 配 Key 时 /api/workflow/run 返回 mode=dify；
    清空 Key 时返回 mode=local_fallback 且 200；
    全仓 grep -r "DIFY_KEY" frontend/ 结果必须为空
P3: 真实生成 docx 并打开确认含 Lot 数据；pdf 页数>0；xlsx 3 sheet
P4: 侧边栏 13 项全可点，无 404

【收工必做】
更新 STATUS.md 四项（当前阶段/已完成/未完成/下一步）与 CHECKLIST.md 勾选。
做不动的项标 ❌ + 阻塞原因，禁止静默跳过。
```

---

## 7. 风险与回退

| 风险 | 影响 | 回退 |
|---|---|---|
| 线上 Dify 调不到本地后端 | HTTP 节点超时 | `cloudflared tunnel` 内网穿透，填 `API_PUBLIC_BASE` |
| Dify blocking 100s 超时 | 长工作流被截断 | 一律 streaming（SSE）或异步 job + 轮询 |
| Dify Key 泄露 | 被刷额度 | Key 只存后端环境变量；`.env` 已 gitignore；前端只显示 `dify_configured` 布尔值 |
| Dify 不可达 | 工作流页报错 | 自动 `local_fallback`，200 不报错，前端显示降级徽章 |
| WPS COM 无桌面会话/被占用 | 文档生成 500 | 单 worker + 60s 超时 + taskkill 重试；再失败降级 python-docx |
| WPS COM **只能本地 Windows** | 云端不可能生成文档 | `DOCGEN_ENABLED=0` 返回 503，文档生成做成本地子服务 |
| twin.html 改造破坏原站功能 | 孪生页白屏 | 改的是 `vendor/semiconfab-gtx/` 副本，原 `vendor/semiconfab-fork/` 未动，可对照 |
| layout map 映射错 | 机台亮错 | 初始化 6/6 校验，失败降级为「仅驱动 Lot 面板」 |
| 公网隧道暴露后端 | 安全风险 | 设置 `LITHO_CORS_ORIGINS` 精确域名；隧道用完即关 |
| 推 my-prototype 影响线上 | 现有 Vercel 站点坏 | 推**新分支** `feat/gtx-fab-fusion`，main 不动 |

---

## 8. 关键文件清单

| 动作 | 文件 |
|---|---|
| 改 | `frontend/vercel.json` |
| 改 | `frontend/index.html`（L172/177/182/187 + 入口卡） |
| 改 | `frontend/vite.config.js`（加 twin 静态资源 + reports 入口） |
| 改 | `frontend/src/pages/_shared/`（导航补 5 项） |
| 改 | `frontend/src/pages/ai-workflow/script.js`（真执行链路 + 模式徽章） |
| 改 | `backend/app/api.py`（加 4 个新接口） |
| 改 | `backend/app/workflow.py`（降级为 fallback） |
| 改 | `backend/requirements.txt` |
| 新建 | `.env.example` |
| 新建 | `vendor/semiconfab-gtx/`（从 fork 复制 + 改造） |
| 新建 | `vendor/semiconfab-gtx/gtx-layout-map.json` |
| 新建 | `backend/app/twin_timeline.py` |
| 新建 | `backend/app/ai/dify_client.py` |
| 新建 | `backend/app/docgen/{wps_worker.py,renderers.py,api.py}` |
| 新建 | `frontend/src/pages/twin-control/` |
| 新建 | `frontend/src/pages/reports/` |
| 新建 | `dify/dsl/{daily-scheduling,scenario-compare,qa-chatflow}.yaml`（**仅用于线上导入，不部署**） |
| 新建 | `docs/07_DOCGEN.md`、`docs/08_DIFY_INTEGRATION.md`（双向接口 + 线上配置步骤） |
| 只读 | `docs/specs/`、`docs/_DESIGN_SPEC.md`、`vendor/semiconfab-fork/` |

---

## 9. 执行顺序与工作量

| 阶段 | 内容 | 依赖 | 预估 |
|---|---|---|---|
| P0 | 修 3 个致命坑 + 建 .env.example | 无 | 小 |
| P1 | 3D 孪生时间轴回放 | P0 | **大**（核心） |
| P3 | WPS 文档生成 | 无 | 中 |
| P2 | Dify 线上工作流接入（配置驱动，无部署） | P0 + 用户线上 Dify 就绪 | 小~中 |
| P4 | reports 页 + 全站导航 | P1/P2/P3 | 小 |

**推荐顺序 P0 → P1 → P3 → P2 → P4**
P2 现在变小了（不装 Docker），可以更早做，但它依赖你线上 Dify 是否已就绪，所以放在 P3 之后更稳。
