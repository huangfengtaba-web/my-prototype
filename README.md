# GTX FSO Litho · 仿真 + 排程融合工程

> **给执行方（Zcode / 任意 Agent）的第一读**
> 本仓库融合三个资产，目标是产出一个**可本地演示、可公网部署、可被任意 Agent 接力**的光刻排程系统。
> 开工前请先读 [`STATUS.md`](STATUS.md) 与 [`CHECKLIST.md`](CHECKLIST.md)，30 秒恢复上下文。

---

## 1. 项目定位

把「半导体 Fab 数字孪生的仿真叙事」与「嘉定 GTX 光刻区（Litho）六步排程算法」合成一个演示系统：

- **仿真侧**：产线状态、设备编目、物料流转的可视化叙事（源自 SemiconFab）
- **排程侧**：真正能跑出 Optimal 解的 MILP 算法链（源自 GTX 交付物 `litho_solver.py`）

一句话：**不是又一个静态原型，是前端能点「运行求解」、后端真跑 CBC 求解器、结果回填页面的可运行系统。**

---

## 2. 三个资产来源

| 代号 | 资产 | 位置 | 提供什么 |
|---|---|---|---|
| **A** | GTX 本地交付物 | `D:\工作\嘉定GTX\GTX_FSO_交付物` | 9 页离线 HTML 原型 + 六步 MILP 算法 + 8 份设计文档 |
| **B** | my-prototype | `github.com/huangfengtaba-web/my-prototype` | Vite 8 + 原生 JS 工程骨架（2 页，已部署 Vercel） |
| **C** | SemiconFab | `github.com/jinjiefan2020/SemiconFab` | Fab 级数字孪生纯静态站（SimPy 仿真 + 设备编目） |

### License 声明（重要）

- **C（SemiconFab）为 PolyForm Noncommercial 许可，禁止商用。**
  本项目定位为**对甲方/客户的非商用演示**，因此以 `git subtree` 拉入 `vendor/semiconfab-fork/` 并**保留其原始 LICENSE 文件**。
- **若后续转为商用交付**：删除整个 `vendor/` 目录即可，前端路由与后端不受任何影响（见 [风险表](#7-风险与回退)）。
- A、B 为自有资产，可自由使用。

---

## 3. 目录结构

```
gtx-fso-litho/
├── README.md                 本文件
├── STATUS.md                 ★ 接力状态机（阶段/已完成/未完成/阻塞）
├── CHECKLIST.md              ★ 验收清单（未完成标 ❌ + 理由）
├── .gitignore
├── .env.example
│
├── frontend/                 Vite 多页前端（沿用 B 的技术栈）
│   ├── package.json  vite.config.js  vercel.json
│   ├── index.html            总览页（A 的 index.html 迁入）
│   ├── prototypes/           其余 8 页（原样迁入，保留内联样式与 PM 评论气泡）
│   └── src/
│       ├── styles/_design_tokens.css    共享 Design Token
│       └── pages/                       ★ 真后端驱动的智能应用页（共享 shell）
│           ├── _shared/                 shell.js/shell.css（侧栏/表头/气泡）
│           ├── scheduling-test/         求解演示（六步 MILP）
│           ├── simulation/              仿真验证（计划 vs 实际）
│           ├── ai-workflow/             AI 工作流（模板/时间线/报告）
│           └── ai-agent/                AI 助手（对话 + 工具调用）
│
├── backend/
│   ├── requirements.txt  Procfile  runtime.txt  nixpacks.toml
│   ├── app/
│   │   ├── api.py            FastAPI 入口（14 个接口）
│   │   ├── solver_runner.py  求解封装（子进程隔离 + RUNS 注册表）
│   │   ├── sim_runner.py     仿真封装（求解→仿真串联）
│   │   ├── workflow.py       ★ 工作流引擎（模板/步骤/线程执行）
│   │   └── agent/            ★ 排程 Agent（tools/llm/agent，双模式）
│   ├── sim/fab_sim.py        执行态离散事件仿真（故障/返工/光罩接力）
│   └── solver/               ← A 的 04_算法demo/ 迁入
│       ├── litho_solver.py   六步 MILP 主程序（含光罩就绪耦合约束）
│       ├── mock_data.py      mock 数据
│       ├── cli.py  __main__.py   命令行工具
│       └── viz/              甘特图渲染
│
├── tests/                    pytest（23 用例）+ cases/ 4 个 scenario
├── vendor/semiconfab-fork/   git subtree 拉入，保留 LICENSE（PolyForm 非商用）
├── .vscode/                  launch.json / tasks.json / settings.json
└── docs/
    ├── HANDOFF_TO_AGENT.md       ★ 接力手册
    ├── 01_GIT_WORKFLOW.md        拉代码 / 推代码
    ├── 02_INTEGRATION_GUIDE.md   ★ 三资产融合映射表
    ├── 03_ALGORITHM_DEMO.md      ★ VSCode 打开与测试
    ├── 04_DEPLOYMENT.md          Vercel + Railway
    ├── 05_AGENT_HANDOFF_TEMPLATE.md
    ├── 06_AI_CAPABILITIES.md     ★ AI 能力架构（工作流 + Agent）
    └── specs/                ← A 的 03_文档/ 8 份设计文档
```

**为什么不用 SemiconFab 自带的 Cloudflare Pages 部署**：它是纯静态站，无后端能力，**跑不了 PuLP/CBC 求解器**。
它的价值在页面结构与仿真叙事，因此拉进 `vendor/` 后由 Vite 接管路由，而不是直接托管。

---

## 4. 快速开始（本地跑通）

### 后端

```bash
cd D:\codex\2026-10-28-23-35-39

# 1) 建虚拟环境
python -m venv .venv
.venv\Scripts\activate          # PowerShell/Git Bash 用：source .venv/Scripts/activate

# 2) 装依赖
pip install -r backend/requirements.txt

# 3) 直接跑算法（不启服务也能验证）
python -m backend.solver run

# 4) 起 API 服务
uvicorn backend.app.api:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

---

## 5. 文档导航

| 我要做什么 | 读哪份 |
|---|---|
| 接手这个项目，不知道从哪开始 | [`STATUS.md`](STATUS.md) → [`CHECKLIST.md`](CHECKLIST.md) |
| 拉取 / 推送代码、建仓库、分支策略 | [`docs/01_GIT_WORKFLOW.md`](docs/01_GIT_WORKFLOW.md) |
| 三个资产怎么合并、文件搬到哪 | [`docs/02_INTEGRATION_GUIDE.md`](docs/02_INTEGRATION_GUIDE.md) |
| 算法 demo 怎么打开、怎么调参、怎么断点 | [`docs/03_ALGORITHM_DEMO.md`](docs/03_ALGORITHM_DEMO.md) |
| 部署到 Vercel / Railway | [`docs/04_DEPLOYMENT.md`](docs/04_DEPLOYMENT.md) |
| 我要把活交给另一个 Agent | [`docs/HANDOFF_TO_AGENT.md`](docs/HANDOFF_TO_AGENT.md) |
| 写一份新的交接状态 | [`docs/05_AGENT_HANDOFF_TEMPLATE.md`](docs/05_AGENT_HANDOFF_TEMPLATE.md) |

---

## 6. 前后端接口契约

| 分组 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 基础 | GET | `/api/health` | 探活（求解器 + Agent 模式 + 版本） |
| 基础 | GET | `/api/mock/data` | 返回 mock_data 快照（机台/Lot/光罩/配置） |
| 基础 | GET | `/api/cases` | 列出所有 scenario 用例 |
| 求解 | POST | `/api/solve/run` | body `{"case": "用例名"}`，返回 `run_id` + 六步结果 JSON |
| 求解 | GET | `/api/solve/result/{run_id}` | 按 run_id 取结果 |
| 仿真 | POST | `/api/sim/run` | 求解 + 执行态仿真（`seed`/`breakdown` 可调，同种子可复现） |
| 工作流 | GET | `/api/workflow/templates` | 工作流模板清单 |
| 工作流 | POST | `/api/workflow/run` | 异步启动（`{"template": "...", "params": {...}}`） |
| 工作流 | GET | `/api/workflow/status/{wf_id}` | 轮询执行状态与步骤时间线 |
| 工作流 | GET | `/api/workflow/list` | 最近运行记录 |
| Agent | GET | `/api/agent/status` | Agent 模式（llm/rule）与工具清单 |
| Agent | POST | `/api/agent/chat` | 对话（可触发任意工具，`session_id` 多轮） |

**求解器默认 CBC**（PuLP 自带，零配置），`LITHO_SOLVER` 环境变量可切 Gurobi/COPT（未安装自动回退 CBC）。
AI 能力详见 [`docs/06_AI_CAPABILITIES.md`](docs/06_AI_CAPABILITIES.md)。

---

## 7. 风险与回退

| 风险 | 回退方案 |
|---|---|
| 后期转商用 → SemiconFab 违规 | 删 `vendor/` 整目录，前端路由不受影响 |
| CBC 大规模求解慢 | solver 适配器改一行切 Gurobi/COPT |
| Vercel 跨域失败 | 先本地 `vite dev` + `uvicorn` 验证，再上云 |
| Railway 冷启动超时 | 换 Render 常驻，或前端预生成静态 JSON |
| 多次调用结果互相污染 | `solver_runner` 用**子进程隔离**（见接口文档说明） |
| `build_ppt.py` 硬编码 `D:/工作/...` 路径 | 不入版本库，`.gitignore` 排除 `01_PPT/` |

---

## 8. 当前状态快照

> 更新时间：2026-10-29 · 生成方：WorkBuddy（骨架）→ Zcode（全量工程化 + AI 能力）

**已完成（本地全链路验证通过，pytest 23/23）**
- 排程主线：9 页原型 + 六步 MILP（含光罩就绪耦合约束）+ FastAPI + 求解演示页
- 仿真腿：执行态 DES（故障/返工/光罩接力，种子可复现）+ 仿真验证页
- AI 能力：工作流引擎（2 模板）+ 排程 Agent（LLM/规则双模式，7 工具）+ 2 个新页面
- 工程配套：.vscode 三件套、pytest 23 用例、4 个 scenario、部署配置文件、9+1 份文档
- git 仓库初始化 + SemiconFab subtree 拉入（vendor/，PolyForm LICENSE 保留）

**未完成（需用户账号/凭据）**
- `git push`（GitHub 空仓库 gtx-fso-litho 待建）与 Vercel/Railway 部署（G4~G7）

详细分项见 [`CHECKLIST.md`](CHECKLIST.md)。
