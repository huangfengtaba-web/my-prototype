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
│   ├── src/styles/_design_tokens.css    共享 Design Token
│   └── src/pages/scheduling-test/       ★ 新增：接 /api/solve 的实时演示页
│
├── backend/
│   ├── requirements.txt
│   ├── app/api.py            FastAPI 入口（4 个接口）
│   ├── app/solver_runner.py  封装 litho_solver（进程隔离调用）
│   └── solver/               ← A 的 04_算法demo/ 迁入
│       ├── litho_solver.py   六步 MILP 主程序
│       ├── mock_data.py      mock 数据
│       ├── cli.py  __main__.py   命令行工具
│       └── viz/              甘特图渲染（算法精化档）
│
├── tests/                    pytest + cases/ scenario 用例
├── vendor/semiconfab-fork/   git subtree 拉入，保留 LICENSE
├── .vscode/                  launch.json / tasks.json / settings.json
└── docs/
    ├── HANDOFF_TO_AGENT.md       ★ 接力手册
    ├── 01_GIT_WORKFLOW.md        拉代码 / 推代码
    ├── 02_INTEGRATION_GUIDE.md   ★ 三资产融合映射表
    ├── 03_ALGORITHM_DEMO.md      ★ VSCode 打开与测试
    ├── 04_DEPLOYMENT.md          Vercel + Railway
    ├── 05_AGENT_HANDOFF_TEMPLATE.md
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

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/health` | 探活，返回求解器状态 |
| POST | `/api/solve/run` | body `{"case": "用例名"}`，返回 `run_id` + 六步结果 JSON |
| GET | `/api/solve/result/{run_id}` | 按 run_id 取结果 |
| GET | `/api/mock/data` | 返回 mock_data 快照（机台/Lot/光罩/配置） |
| GET | `/api/cases` | 列出所有 scenario 用例 |

**求解器默认 CBC**（PuLP 自带，零配置）。`litho_solver.py` 内保留 solver 适配器位，换 Gurobi/COPT 只改一处。

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

> 生成时间：2026-10-29 · 生成方：WorkBuddy

**已完成**
- 目录骨架建立（`frontend/` `backend/` `docs/` `tests/` `vendor/` `.vscode/`）
- 资产 A 迁移：`frontend/index.html` + `frontend/prototypes/` 8 页 + `backend/solver/` 2 个 py + `docs/specs/` 8 份文档
- `backend/requirements.txt`、`backend/solver/{__init__,__main__,cli}.py` 已就位

**未完成**
- `backend/app/api.py`、`backend/app/solver_runner.py`（目录已建，文件待写）
- `frontend/package.json`、`vite.config.js`、`vercel.json`
- `.vscode/` 三件套
- `tests/` 用例与 pytest
- 全部 MD 文档（本文件除外）
- git 初始化与首次推送

详细分项见 [`CHECKLIST.md`](CHECKLIST.md)。
