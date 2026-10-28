# STATUS · 项目接力状态机

> **任何 Agent 接手本项目，第一件事就是读这个文件。**
> 读完再读 [`CHECKLIST.md`](CHECKLIST.md)。两份加起来 30 秒恢复完整上下文。

---

## 当前阶段

```
阶段：MVP 档 · 本地全链路已跑通（CLI + pytest 9/9 + API 5 接口 + Vite 构建 10 页）
进度：█████████░░░  85%
阻塞：无（G 档 git/部署需用户授权账号）
下一步：G 档 —— git init + subtree 拉 SemiconFab + push + Vercel/Railway 部署（照 docs/01、docs/04 执行）
```

| 项 | 值 |
|---|---|
| 当前阶段 | **MVP 档收尾**（A~F 档全部完成，仅剩 G 档版本管理与部署） |
| 本阶段负责人 | Zcode（初版，2026-10-29 完成）→ 下一 Agent（G 档 + 优化） |
| 最近更新 | 2026-10-29 02:30 |
| 阻塞项 | 无 |

---

## 已完成 ✅

| # | 事项 | 产物路径 |
|---|---|---|
| 1 | 目录骨架建立 | `frontend/` `backend/` `docs/` `tests/` `vendor/` `.vscode/` |
| 2 | 9 页原型迁移 | `frontend/index.html`、`frontend/prototypes/*.html`（8 个） |
| 3 | 算法脚本迁移 | `backend/solver/litho_solver.py`、`mock_data.py` |
| 4 | 求解器 CLI | `backend/solver/cli.py`、`__main__.py`、`__init__.py` |
| 5 | **FastAPI 后端** | `backend/app/api.py`（5 接口）、`backend/app/solver_runner.py`（子进程隔离） |
| 6 | **Vite 前端配置** | `frontend/package.json`、`vite.config.js`（10 入口）、`vercel.json` |
| 7 | **求解演示页** | `frontend/src/pages/scheduling-test/`（三件套）+ `src/styles/_design_tokens.css` |
| 8 | **VSCode 三件套** | `.vscode/launch.json`（3 配置）、`tasks.json`（4 任务）、`settings.json` |
| 9 | **测试体系** | `tests/test_litho_solver.py`（9 用例全过）、`tests/cases/*.yaml`（4 scenario） |
| 10 | **算法精化档入口** | `backend/solver/viz/`（matplotlib 甘特，中文字体已配） |
| 11 | **部署配置文件** | `backend/Procfile`、`runtime.txt`、`nixpacks.toml`、`.env.example`、`.gitignore` |
| 12 | MD 文档体系（9 份） | `STATUS.md` `CHECKLIST.md` `docs/01`~`05` `HANDOFF_TO_AGENT.md` |

### 本地验证记录（2026-10-29，全部实跑通过）

- `python -m backend.solver cases` → 列出 4 个用例
- 4 个 scenario 全部 `Optimal`；基线 LOT-A01 上机 10:00、RT-0101 就绪 09:45（链路 35min 守恒）
- `pytest tests/ -q` → **9 passed**（约 2s，全部走子进程 CLI）
- `uvicorn backend.app.api:app` → 5 接口全通；同 case 连跑两次结果一致（进程隔离有效）
- `npm run build`（frontend/）→ 10 页全部产出，构建 163ms
- 跨页链接校验：9 页互点无 404（修复了 index↔prototypes 互链与 RFP 矩阵 JS 动态链接）

---

## 未完成 ❌（按优先级排序）

| 优先级 | 事项 | 应产出 | 依赖 |
|---|---|---|---|
| **P2** | git 初始化与首推 | G1~G4（docs/01_GIT_WORKFLOW.md） | 用户 GitHub 账号 + 代理 10808 |
| **P2** | 部署上线 | G5~G7：Vercel（frontend/）+ Railway/Render（仓库根） | 用户授权，配置文件已备齐 |
| P1（优化档） | 光罩就绪回写 step3 | step3 加 `s[l] ≥ reticle_ready` 约束，让 Lot 随光罩延迟顺延 | 算法精化档，见下「算法现状」 |
| P1（优化档） | SimPy 仿真移植 | `frontend/src/pages/simulation/`（从 vendor/semiconfab-fork 移植） | G3 subtree 先拉入 vendor/ |
| P1（优化档） | RUNS 持久化 | 求解历史目前存内存，重启即失；可落 SQLite/JSON | 按需 |

---

## 关键文件路径（接力必记）

| 用途 | 路径 |
|---|---|
| 工程根 | `D:\codex\2026-10-28-23-35-39` |
| 算法主程序 | `backend\solver\litho_solver.py`（六步 MILP，PuLP+CBC） |
| mock 数据 | `backend\solver\mock_data.py` |
| 求解器 CLI | `backend\solver\cli.py`（`python -m backend.solver run --case X`） |
| **API 入口** | `backend\app\api.py`（5 接口） |
| **子进程隔离运行器** | `backend\app\solver_runner.py`（RUNS 内存字典） |
| **求解演示页** | `frontend\src\pages\scheduling-test\`（script.js 里 `API_BASE` 读 `VITE_API_BASE_URL`） |
| scenario 用例 | `tests\cases\*.yaml`（4 个） |
| Design Token | `docs\_DESIGN_SPEC.md` §3 + `frontend\src\styles\_design_tokens.css` |
| 设计书权威字段源 | `D:\工作\嘉定GTX\GTX_FSO_交付物\00_素材\GTX FSO项目设计说明书-Litho-V0.1-1023.docx` |
| 原始交付物（只读，勿改） | `D:\工作\嘉定GTX\GTX_FSO_交付物` |

---

## 环境事实（已验证，不用再查）

- Python：**3.11**，miniconda 路径 `D:/software/miniconda/anzhuang/python.exe`；**项目解释器 `.venv/Scripts/python.exe` 已建好**（依赖已装全）
- Git Bash 里没有 `python` 命令，用 `./.venv/Scripts/python.exe` 或 miniconda 绝对路径
- 求解器：CBC 随 PuLP 自带，零配置，4 个 scenario 全部 **Optimal**
- npm 需代理：`npm install --proxy http://127.0.0.1:10808 --https-proxy http://127.0.0.1:10808`；pip 走清华源即可
- node_modules 已装（frontend/），`npm run dev` 起在 5173
- 原型 HTML：CSS/JS **全内联**，**含 PM 评论气泡**（勿删）；新页面才用共享 Token
- 交付物目录**不是** git 仓库

---

## 算法现状（精化档 Agent 必读）

1. **step3 约束只看 Lot 到站时间**（`s[l] ≥ l.ready`），光罩就绪时间在 step6 才推演、**不回写 step3**。
   所以 `reticle-delay` 场景下 Lot 开工不变、只有光罩就绪顺延 —— 这是当前算法的真实行为，测试按此口径断言。
2. **"急货最早开工"的正确口径**：LOT-A01 ready=10:00 晚于其他 Lot 的 09:00，所以验收是「到站即开工（零无谓延迟）」，不是全厂最小开工时间。
3. 若要让 Lot 随光罩延迟顺延（更真实的耦合）：在 step3 加约束 `s[l] ≥ reticle_ready[l["reticle"]]`，
   reticle_ready 由 step2/step6 的 IRIS 链路推算。改完必跑 `pytest tests/` 并同步改 `test_reticle_delay_postpones_ready` 口径。
4. `run_summary.json` 的 `schedule` / `reticles` 结构化字段已在 `main()` 末尾一并写盘（本次修的缺陷：原先写盘早于字段构造）。

---

## 下一步动作（按序执行）

1. **G 档（需用户账号）**：按 `docs/01_GIT_WORKFLOW.md` 执行 G1~G4（git init → subtree 拉 SemiconFab → push）
2. **部署**：按 `docs/04_DEPLOYMENT.md` 执行 G5~G7（Vercel Root=frontend；Railway Root=仓库根）
3. **联调验收**：线上 `/scheduling-test` 点「运行求解」拿到结果（docs/04 §7 清单）
4. （可选优化档）step3 光罩就绪约束、SimPy 仿真移植、RUNS 持久化

---

## 接力规则（写给下一个 Agent）

1. **开工前**：读 `STATUS.md` + `CHECKLIST.md`
2. **每完成一项**：更新 `CHECKLIST.md` 勾选，并回写本文件的「已完成」表
3. **遇到做不动的**：**不要静默跳过**，在 `CHECKLIST.md` 标 ❌ 并写清阻塞原因
4. **收工前**：必须更新本文件的「当前阶段 / 已完成 / 未完成 / 下一步动作」四项
5. **禁止**：改动 `docs/specs/` 与 `docs/_DESIGN_SPEC.md`（设计基线，只读）
6. **禁止**：拆 9 页原型 HTML 的内联样式；删 PM 评论气泡（`.q[data-cm]`）
7. **回归底线**：`pytest tests/ -q` 必须 9 passed；step2/step3 必须 Optimal
