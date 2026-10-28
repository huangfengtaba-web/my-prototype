# STATUS · 项目接力状态机

> **任何 Agent 接手本项目，第一件事就是读这个文件。**
> 读完再读 [`CHECKLIST.md`](CHECKLIST.md)。两份加起来 30 秒恢复完整上下文。

---

## 当前阶段

```
阶段：全量工程化档 · 排程+仿真+AI 能力全部完成（pytest 23/23，13 页构建通过）
进度：███████████  95%（仅剩 push + 部署，需用户账号）
阻塞：GitHub/Vercel/Railway 凭据（用户侧）
下一步：git push → Vercel/Railway 部署 → 线上验收（或直接进入功能迭代）
```

| 项 | 值 |
|---|---|
| 当前阶段 | **全量工程化档完成**（A~F、H 档全勾，G 档剩远端操作） |
| 本阶段负责人 | Zcode（初版+AI 能力，2026-10-29）→ 下一 Agent（部署/迭代） |
| 最近更新 | 2026-10-29 04:10 |
| 阻塞项 | push 需用户建 GitHub 仓库；部署需 Vercel/Railway 账号 |

---

## 系统能力全景（本阶段达成）

| 能力 | 实现 | 页面 | 验证 |
|---|---|---|---|
| 六步 MILP 排程 | `backend/solver/`（PuLP+CBC，**含光罩就绪耦合约束**，`LITHO_SOLVER` 可切 Gurobi/COPT） | 求解演示 scheduling-test | 4 scenario 全 Optimal |
| 执行态仿真 | `backend/sim/fab_sim.py`（自研 DES：故障/返工/光罩接力，**同种子可复现**） | 仿真验证 simulation | 同种子 KPI 一致；无扰动准时率≥0.8 |
| 工作流引擎 | `backend/app/workflow.py`（2 模板：日计划链路 / 多场景对比，线程异步+步骤时间线） | AI 工作流 ai-workflow | 两模板端到端 done |
| 排程 Agent | `backend/app/agent/`（7 工具，LLM function calling / 规则模式双轨） | AI 助手 ai-agent | 7 类意图路由全对 |
| 原型叙事 | 9 页离线 HTML（内联样式 + PM 评论气泡，**只读基线**） | prototypes/ | 互链无 404 |

---

## 已完成 ✅（按轮次）

### 第一轮（MVP 档，02:30）
| # | 事项 | 产物 |
|---|---|---|
| 1 | 目录骨架 + 9 页原型 + 算法迁移 + CLI | `frontend/` `backend/solver/` `docs/specs/` |
| 2 | FastAPI 5 接口 + 子进程隔离求解 | `backend/app/{api,solver_runner}.py` |
| 3 | Vite 前端 + 求解演示页 + Design Token | `frontend/package.json` `vite.config.js` 等 |
| 4 | VSCode 三件套 + pytest 9 用例 + 4 scenario + viz | `.vscode/` `tests/` |
| 5 | git init + SemiconFab subtree（LICENSE 保留） | 仓库 4 commit + `vendor/semiconfab-fork/` |
| 6 | MD 文档体系 9 份 | `docs/01`~`05` `HANDOFF_TO_AGENT.md` |

### 第二轮（全量工程化 + AI 能力，04:10）
| # | 事项 | 产物 |
|---|---|---|
| 7 | **算法补足**：step3 光罩就绪耦合约束（MakeSpan 11:10→12:34）+ 求解器适配器 | `litho_solver.py` |
| 8 | **仿真模块**：自研 DES + 求解仿真串联 + `/api/sim/run` | `backend/sim/` `sim_runner.py` |
| 9 | **工作流引擎**：2 模板 + 步骤时间线 + 4 接口 | `backend/app/workflow.py` |
| 10 | **排程 Agent**：7 工具 + LLM/规则双模式 + 会话 + 2 接口 | `backend/app/agent/` |
| 11 | **前端 3 新页**（共享 shell）+ vite 13 页入口 | `src/pages/{simulation,ai-workflow,ai-agent}/` |
| 12 | 测试扩至 **23 用例全绿**；uvicorn 14 接口冒烟全过 | `tests/test_{sim,workflow,agent}.py` |
| 13 | AI 能力文档 + README/`.env.example` 更新 | `docs/06_AI_CAPABILITIES.md` |

---

## 未完成 ❌（按优先级排序）

| 优先级 | 事项 | 应产出 | 依赖 |
|---|---|---|---|
| **P2** | push 到 GitHub | `git push -u origin main`（docs/01 §1、§6） | 用户先建空仓库 `huangfengtaba-web/gtx-fso-litho`；走代理 10808 |
| **P2** | 部署上线 | Vercel（frontend/）+ Railway/Render（仓库根） | 用户授权，配置文件已备齐（docs/04） |
| P1（迭代档） | RUNS/WORKFLOWS/SESSIONS 持久化 | 三个内存注册表落 SQLite/JSON（重启不丢） | 按需 |
| P1（迭代档） | 仿真参数页上可调 | MTBF/MTTR/返工率从 DEFAULT_PARAMS 暴露到 /api/sim/run body | 小改动 |
| P1（迭代档） | 大规模数据 | mock_data 换宽表真实数据（docs/specs/06_宽表数据对接） | 客户数据 |

---

## 关键文件路径（接力必记）

| 用途 | 路径 |
|---|---|
| 工程根 | `D:\codex\2026-10-28-23-35-39` |
| 算法主程序 | `backend\solver\litho_solver.py`（六步 MILP + 光罩就绪耦合） |
| mock 数据 / 用例 | `backend\solver\mock_data.py` / `tests\cases\*.yaml`（4 个） |
| API 入口（14 接口） | `backend\app\api.py` |
| 求解 / 仿真运行器 | `backend\app\solver_runner.py` / `backend\app\sim_runner.py` |
| **工作流引擎** | `backend\app\workflow.py`（TEMPLATES 扩展点） |
| **Agent** | `backend\app\agent\{tools,llm,agent}.py`（TOOLS 扩展点） |
| 仿真 DES | `backend\sim\fab_sim.py`（DEFAULT_PARAMS 调扰动） |
| 前端智能页 | `frontend\src\pages\`（4 页 + `_shared/shell.js`） |
| Design Token | `docs\_DESIGN_SPEC.md` §3 + `frontend\src\styles\_design_tokens.css` |
| AI 能力文档 | `docs\06_AI_CAPABILITIES.md`（接口/LLM 接入/扩展指南） |
| 原始交付物（只读） | `D:\工作\嘉定GTX\GTX_FSO_交付物` |

---

## 环境事实（已验证，不用再查）

- Python 3.11；**项目解释器 `.venv/Scripts/python.exe` 已建好**（pulp/fastapi/uvicorn/pytest/PyYAML/matplotlib 已装）
- Git Bash 无 `python` 命令，用 `./.venv/Scripts/python.exe`
- CBC 随 PuLP 自带，4 scenario 全 Optimal；**pytest 23/23（约 5s）**
- npm 需代理 `--proxy http://127.0.0.1:10808`；pip 走清华源；node_modules 已装
- 本地跑通：uvicorn :8000 + `cd frontend && npm run dev` :5173，
  四个智能页：`/src/pages/{scheduling-test,simulation,ai-workflow,ai-agent}/index.html`
- Agent 当前**规则模式**（未配 LLM Key）；配 `LLM_API_BASE/LLM_API_KEY/LLM_MODEL` 即切 LLM 自主决策
- ⚠️ Windows 控制台 curl 发中文会 GBK 乱码 → Agent 关键词匹配失效；测试/演示请用 UTF-8 客户端（页面本身没问题）
- vendor/semiconfab-fork/（PolyForm 非商用，转商用删 vendor/）
- 原型 HTML 内联样式与 PM 气泡勿动；`docs/specs/` 与 `_DESIGN_SPEC.md` 只读

---

## 算法口径（精化/迭代必读）

1. **光罩就绪已耦合进 step3**（`reticle_ready_lb`：外部 IRIS 链路 35min / StarLight 到期 / 跨机搬送 15min）。
   光罩延迟场景下 Lot 开工**会**顺延——`test_reticle_delay_couples_to_lots` 按 this 口径断言。
2. **"急货最早开工"口径**：LOT-A01 ready=10:00 晚于其他 Lot，验收是「到站即开工（零无谓延迟）」。
3. 仿真 KPI 中 `makespan_delta_min` 允许小幅为负（加工时长正态波动可提前完工）。
4. 改算法必跑：`pytest tests/ -q`（23 用例），任一红即回归。

---

## 下一步动作（按序执行）

1. **push（需用户账号）**：建 GitHub 空仓库 `gtx-fso-litho` → `git push -u origin main`
2. **部署**：按 `docs/04_DEPLOYMENT.md`（Vercel Root=frontend；Railway Root=仓库根）
3. （迭代档，可选）RUNS 持久化 / 仿真参数暴露 / 真实宽表数据接入
4. AI 能力扩展见 `docs/06_AI_CAPABILITIES.md` §2.3（工作流）与 §3.5（工具）

---

## 接力规则（写给下一个 Agent）

1. **开工前**：读 `STATUS.md` + `CHECKLIST.md`
2. **每完成一项**：更新 `CHECKLIST.md` 勾选，并回写本文件「已完成」表
3. **遇到做不动的**：不要静默跳过，CHECKLIST 标 ❌ + 阻塞原因
4. **收工前**：更新本文件「当前阶段 / 已完成 / 未完成 / 下一步动作」四项
5. **禁止**：改 `docs/specs/` 与 `_DESIGN_SPEC.md`；拆 9 页原型内联样式；删 PM 气泡
6. **回归底线**：`pytest tests/ -q` 必须 23 passed；step2/step3 必须 Optimal；`npm run build` 必须过
