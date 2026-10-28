# CHECKLIST · 验收清单

> **使用规则**
> - 完成一项勾选一项 `[x]`
> - **做不动的标 `[ ]` 并写 ❌ + 阻塞原因，禁止静默跳过**
> - 收工前必须更新本文件与 [`STATUS.md`](STATUS.md)
> - 状态图例：`[x]` 已完成 / `[ ]` 未完成 / `❌` 阻塞

最后更新：2026-10-29 02:30（Zcode 初版完成）

---

## A. 工程骨架

- [x] A1 建立 monorepo 目录结构（`frontend/ backend/ docs/ tests/ vendor/ .vscode/`）
- [x] A2 迁移 9 页原型 HTML 到 `frontend/`
- [x] A3 迁移算法脚本到 `backend/solver/`
- [x] A4 迁移设计文档到 `docs/specs/`
- [x] A5 编写 `backend/requirements.txt`
- [x] A6 编写 `README.md`
- [x] A7 编写 `.gitignore`（须排除 `output/ __pycache__/ .venv/ node_modules/ 01_PPT/ *.pptx *.docx`）
- [x] A8 编写 `.env.example`（`LITHO_CORS_ORIGINS` / `LITHO_SOLVER` / `LITHO_TIME_LIMIT_S` / `VITE_API_BASE_URL`）

---

## B. 后端（P0）

- [x] B1 `backend/app/solver_runner.py`
      - 子进程隔离调用（`sys.executable -m backend.solver run`），防 mock 状态污染（已验证：同 case 连跑两次结果一致）
      - `run_id` 用 uuid4 短码，结果存内存字典 `RUNS`（线程锁保护）
      - 超时保护 120s（`LITHO_TIME_LIMIT_S` 可调）
- [x] B2 `backend/app/api.py` —— 5 个接口
      - [x] `GET  /api/health` 返回 `{"ok": true, "solver": "CBC"}`（已验证 200）
      - [x] `POST /api/solve/run` body `{"case": "<用例名>"}` → `{run_id, status, summary}`（已验证）
      - [x] `GET  /api/solve/result/{run_id}`（不存在时 404，已验证）
      - [x] `GET  /api/mock/data` 返回机台/Lot/光罩/配置（已验证）
      - [x] `GET  /api/cases` 列出 `tests/cases/*.yaml`（已验证）
- [x] B3 CORS 放行 `http://localhost:5173`（生产放 Vercel 域名，`LITHO_CORS_ORIGINS` 覆盖）
- [x] B4 solver 适配器位：环境变量 `LITHO_SOLVER` 预留 Gurobi/COPT 切换点（health/run 结果带出）
- [x] B5 本地验证：`uvicorn backend.app.api:app --reload` 后 `curl /api/health` 返回 200

---

## C. 前端（P0）

- [x] C1 `frontend/package.json`（Vite ^8.3.5 + 原生 JS，**不引入 React/Vue**）
- [x] C2 `frontend/vite.config.js` 多页入口配置
      - `/` → `index.html`
      - `/prototypes/*` → 8 页原样
      - `/scheduling-test` → `src/pages/scheduling-test/index.html`
      - `npm run build` 已跑通，10 页全部产出
- [x] C3 `frontend/src/styles/_design_tokens.css`（从 `docs/_DESIGN_SPEC.md` §3 抽 Token，主色 #1677FF）
- [x] C4 `frontend/src/pages/scheduling-test/`（index.html + style.css + script.js）
      - 用例下拉（调 `/api/cases`）
      - 「运行求解」按钮 → `POST /api/solve/run`
      - 结果渲染：排程列表 + 简易甘特条 + KPI + 历史记录 + CSV 导出
      - 保留 PM 评论气泡机制（`.q[data-cm]`）
- [x] C5 **9 个迁入 HTML 保持内联样式不动**（零回归风险，只给新页面用共享 Token）
- [x] C6 路径校验：所有跨页链接仍为相对路径，9 页互相点击无 404
      - 已修复：`index.html` → 原型页加 `prototypes/` 前缀（含 RFP 矩阵 JS 动态链接）；原型页 → `index.html` 加 `../`；
        `../03_文档/` 重映射到 `../docs/specs/`、`_DESIGN_SPEC.md` → `../docs/_DESIGN_SPEC.md`、`../04_算法demo/README.md` → `../backend/solver/README.md`
      - ❌ 已知限制（非阻塞）：`index.html` 里指向 `../00_素材/*.pptx|docx`、`../01_PPT/` 的附件下载链接仍指向交付物目录，
        这两个目录按 `02_INTEGRATION_GUIDE.md` §8 刻意不入库，上线后这些链接会 404（如需可加占位提示页）
- [x] C7 `frontend/vercel.json`（SPA/多页 rewrite 规则）

---

## D. VSCode 调试环境（P1）

- [x] D1 `.vscode/launch.json` 3 个配置
      - `Python: litho_solver`（module 模式跑 `backend.solver`，断点仍打在 litho_solver.py）
      - `Python: FastAPI`（`uvicorn backend.app.api:app --reload`）
      - `Python: pytest`（当前文件）
- [x] D2 `.vscode/tasks.json` 4 个任务：`venv:create` / `install:pip` / `run:solver` / `run:api`
- [x] D3 `.vscode/settings.json`
      - `python.defaultInterpreterPath` 指向 `.venv`
      - `files.exclude` 排除 `**/__pycache__`、`backend/solver/output`

---

## E. 测试与算法精化（P1）

- [x] E1 `tests/test_litho_solver.py`（9 个用例全过，pytest -q 2.05s）
      - 断言 step2 / step3 状态为 `Optimal`
      - 断言急货 LOT-A01 到站即开工（口径修正：A01 ready=10:00 晚于其他 Lot，"最早开工"应为零无谓延迟，不是全厂最小值）
      - 断言 RT-0101 就绪时间链路 = IRIS 20 + 搬送 10 + 装载 5 = 35min（含延迟场景守恒）
      - 断言 4 个 scenario 全部可跑且 Optimal
      - 测试全部走子进程 CLI（与 API 生产路径一致，规避 mock 状态污染）
- [x] E2 `tests/cases/` 4 个 scenario（YAML）
      - [x] `default.yaml` 基线
      - [x] `urgent-A01.yaml` 急货插单（LOT-A01 priority=1 + SHR tag）
      - [x] `reticle-delay.yaml` RT-0101 光罩延迟到 11:00
      - [x] `temp-conflict.yaml` 温层冲突（相邻 Lot 异温层，验证换温耗时计入）
- [x] E3 `backend/solver/viz/` matplotlib 甘特图渲染（复用 result_litho.html 配色，中文字体用微软雅黑，`LITHO_VIZ_HEADLESS=1` 出 PNG）
      - ⚠️ 算法现状备注（精化档切入点）：step3 只以 Lot 到站时间为下界，光罩就绪时间在 step6 推演、不回写 step3；
        故「光罩延迟」场景下 Lot 开工不变，只有光罩就绪时间顺延。若要 Lot 随光罩顺延，需在 step3 加 `s[l] ≥ reticle_ready[l.reticle]` 约束
- [x] E4 `python -m backend.solver cases` 能列出 4 个用例
- [x] E5 `python -m backend.solver run --case urgent-A01 --json` 能跑通并输出 JSON

---

## F. 文档（P1）

- [x] F1 `README.md` 工程总入口
- [x] F2 `STATUS.md` 接力状态机
- [x] F3 `CHECKLIST.md` 本文件
- [x] F4 `docs/01_GIT_WORKFLOW.md` 拉/推代码
- [x] F5 `docs/02_INTEGRATION_GUIDE.md` 三资产融合映射表
- [x] F6 `docs/03_ALGORITHM_DEMO.md` VSCode 打开与测试
- [x] F7 `docs/04_DEPLOYMENT.md` Vercel + Railway
- [x] F8 `docs/HANDOFF_TO_AGENT.md` 接力手册
- [x] F9 `docs/05_AGENT_HANDOFF_TEMPLATE.md` 接手模板

> **F 档全部完成（2026-10-29 00:15）**。文档体系已可直接交给 Zcode 执行。

---

## G. 版本管理与部署（P2）—— 需用户授权（GitHub / Vercel / Railway 账号），代码侧文件已备齐

- [x] G0（前置）`backend/Procfile` + `backend/runtime.txt` + `backend/nixpacks.toml` 已备齐（docs/04 §3.1）
- [ ] G1 `git init` + 配置 user.name / user.email
- [ ] G2 添加 origin（GitHub 空仓库 `gtx-fso-litho`）
- [ ] G3 `git subtree add` 拉入 SemiconFab（保留 LICENSE）
- [ ] G4 首次 commit + push（按 docs/01_GIT_WORKFLOW.md，代理 http://127.0.0.1:10808）
- [ ] G5 Vercel 连 `frontend/` 部署（Root Directory = frontend，环境变量 VITE_API_BASE_URL）
- [ ] G6 Railway/Render 连 `backend/` 部署（Root Directory = 仓库根，环境变量 LITHO_CORS_ORIGINS）
- [ ] G7 生产环境 CORS 联调验证

---

## 阻塞登记

| 日期 | 事项 | 阻塞原因 | 需要的支持 |
|---|---|---|---|
| （暂无） | | | |
| 备注 | G1~G7 未执行 | 属 P2 且需用户账号授权（GitHub/Vercel/Railway），代码与配置文件已全部备好 | 用户按 docs/01、docs/04 操作或授权 Agent 代办 |
