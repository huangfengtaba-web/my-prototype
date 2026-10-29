# CHECKLIST · 验收清单

> **使用规则**
> - 完成一项勾选一项 `[x]`
> - **做不动的标 `[ ]` 并写 ❌ + 阻塞原因，禁止静默跳过**
> - 收工前必须更新本文件与 [`STATUS.md`](STATUS.md)
> - 状态图例：`[x]` 已完成 / `[ ]` 未完成 / `❌` 阻塞

最后更新：2026-10-29 05:30（Zcode 第三轮：真融合改造完成，工单 22 条 + 验收表 15 项全绿）

---

## I. 真融合改造（2026-10-29 第三轮，按 ZCODE_TASKS.md 执行，验收汇总表 15/15 全绿）

- [x] I1 P0 修致命坑：vercel.json 兜底 rewrite 删除（无扩展名目的地+cleanUrls，grep=0）；
      index.html KPI 硬编码改真实数据（失败显示 —/后端未连接，绝不回落假数字）；入口卡 8→12；.env.example 补 7 变量
- [x] I2 P1 3D 孪生时间轴回放：vendor/semiconfab-gtx 副本（fork 一字节未动）；
      mimacMid 冻结（gtx-layout-map.json，值=真实 TG01_LITHO_01..06）；gtx-catalog.json 精选 6 台 L1 光刻机
      （默认目录只有 4 台 L1，draft 无信号灯 → 用 ?catalog= 参数加载，6/6 resolved 实测通过）；
      window.gtxTwinApi v1.0（契约逐字实现，IAB 实测 timeSec 推进 + eqp 状态机）；/api/twin/timeline
      （41 事件升序）；twin-control 控制页（加载排程→机台亮灭→进度条拖动→Lot 面板实时更新，IAB 实测通过）
- [x] I3 P3 WPS 文档生成：wps_worker 单线程队列 COM（60s 超时→taskkill 重试→python-docx/pptx 降级）；
      五种渲染器（docx/pdf/xlsx/pptx/template）；绕过 harness 三坑（Visible 不可设/SaveAs2 缺失/KWPP kill 竞态）；
      4 产物真实生成（12.4K/83.7K/12.1K/77K）；/api/doc 3 接口 render→status→file 全通；docs/07_DOCGEN.md
- [x] I4 P2 Dify 线上接入：dify_client（httpx，未配 Key 不抛异常）；dify/dsl 3 个导入骨架
      （无 Key 字样、含 API_PUBLIC_BASE）；workflow.py 降级为本地 fallback + run_with_fallback 统一入口
      （未配 Key 实测 mode=local_fallback 且 steps 全 done）；/api/workflow/* 加 mode/dify_configured；
      ai-workflow 页 v2（模式徽章 + dify_configured 标签 + 真实节点级事件流）；frontend 无 DIFY_KEY 字样
- [x] I5 P4 reports 页 + 全站导航 13 项（shell.js 根路径）；T4-3 验收 14 路径（含 /twin-control）全 200
- [x] I6 收尾：STATUS/CHECKLIST/ZCODE_TASKS 回写；pytest 23/23；npm run build 通过
- [x] I7 T5-2：remote origin 改指 my-prototype（旧 gtx-fso-litho 留 origin-gtx），分支 feat/gtx-fab-fusion 推送
- 已知限制：`reticle_move` 事件未驱动 OHT（缺弧长参数，gtxMoveOht 已暴露待接）；
  WPS COM 在 uvicorn 进程内偶发挂起（命令行中文参数所致；worker 超时+降级兜底，UTF-8 调用 5s 出件）

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

## H. 全量工程化 + AI 能力（2026-10-29 第二轮，用户要求：全量复杂项目 + 工作流 + Agent）

- [x] H1 算法补足
      - step3 新增「光罩就绪耦合约束」`s[l] ≥ reticle_ready_lb`（外部 IRIS 链路/StarLight 到期/跨机搬送三口径），
        MakeSpan 11:10 → 12:34（RT-0204 11:18 到期正确卡控），基线自检不受影响
      - `_pick_solver()` 求解器适配器：`LITHO_SOLVER=CBC/GUROBI/COPT`，未安装自动回退 CBC
      - 测试口径同步：reticle-delay 断言升级为「Lot 随光罩顺延」
- [x] H2 仿真模块（SemiconFab 叙事移植）
      - `backend/sim/fab_sim.py`：轻量自研 DES（零依赖，事件按计划开工全局推进），
        三类扰动：机台故障（MTBF900/MTTR30）、光罩接力（10+5min）、良率返工（5%×2）
      - 同种子完全可复现；无扰动时准时率 ≥0.8；KPI：准时率/MakeSpan 偏差/延误/QTime 违约
      - `backend/app/sim_runner.py`（求解→仿真串联）+ `POST /api/sim/run`
- [x] H3 工作流引擎 `backend/app/workflow.py`
      - 模板 `daily-scheduling`（校验→求解→仿真→报告）与 `scenario-compare`（3 场景对比→报告），
        均端到端跑通；步骤函数签名 `step(ctx, params)`，ctx 黑板传值
      - 后台线程异步执行 + 同步入口（测试/Agent 用）；步骤级状态/耗时/输出
      - 4 个接口：templates / run / status/{id} / list
- [x] H4 排程 Agent `backend/app/agent/`
      - 7 个工具（list_cases/run_solve/get_result/get_mock_data/run_sim/run_workflow/list_workflows）
      - 双模式：LLM（OpenAI 兼容 function calling，`LLM_API_BASE/KEY/MODEL` 配置即启用）
        + 规则模式兜底（关键词路由，7 类意图全对，无 Key 演示永不冷场）
      - 会话记忆（内存 20 条）+ 2 个接口（status/chat）
- [x] H5 前端 3 个新页（共享 shell：`src/pages/_shared/`）
      - `simulation/`：计划 vs 实际双轨甘特 + 扰动 KPI + Lot 延误明细
      - `ai-workflow/`：模板卡片 + 轮询时间线（步骤状态灯）+ Markdown 报告渲染
      - `ai-agent/`：对话式助手（工具调用 chip、快捷提问、LLM/规则模式徽章）
      - vite 入口扩至 13 页，`npm run build` 通过；scheduling-test 导航补齐 4 页互链
- [x] H6 测试扩展：23/23 全绿（原 9 + 仿真 4 + 工作流 3 + Agent 7）
- [x] H7 文档：`docs/06_AI_CAPABILITIES.md`（三层架构/接口/LLM 接入/扩展指南）+ README 目录/接口契约更新 + `.env.example` 增 LLM 三项
- [x] H8 本地验证记录：uvicorn 全 14 接口冒烟通过；agent 经 HTTP（UTF-8）路由正确触发 run_solve/run_workflow/run_sim

---

## G. 版本管理与部署（P2）—— 本地部分已完成，仅剩需要用户账号/凭据的远端操作

- [x] G0（前置）`backend/Procfile` + `backend/runtime.txt` + `backend/nixpacks.toml` 已备齐（docs/04 §3.1）
- [x] G1 `git init`（main 分支；身份沿用全局配置 aichifeizailuo / huangjwshan@163.com，首次提交 a166aed）
- [x] G2 `git remote add origin https://github.com/huangfengtaba-web/gtx-fso-litho.git` 已配置（⚠️ GitHub 侧空仓库尚需用户创建，push 时才用到）
- [x] G3 `git subtree add` 拉入 SemiconFab（保留 LICENSE）✅ 2026-10-29
      - `vendor/semiconfab-fork/` 12MB，LICENSE = PolyForm Noncommercial 1.0.0 已验证存在
      - 拉入前须先删掉空壳目录 `vendor/semiconfab-fork/`（否则 subtree 报 "prefix already exists"）
      - 同步上游：`git subtree pull --prefix=vendor/semiconfab-fork semiconfab main --squash`
      - 转商用时删除整个 vendor/ 即可（docs/01 §4）
- [ ] G4 首次 commit ✅（本地已有 2 个 commit）+ **push ❌**（gh CLI 未装、无凭据；需用户按 docs/01 §1 建 GitHub 空仓库后 `git push -u origin main`，走代理 http://127.0.0.1:10808）
- [ ] G5 Vercel 连 `frontend/` 部署（Root Directory = frontend，环境变量 VITE_API_BASE_URL）
- [ ] G6 Railway/Render 连 `backend/` 部署（Root Directory = 仓库根，环境变量 LITHO_CORS_ORIGINS）
- [ ] G7 生产环境 CORS 联调验证

---

## 阻塞登记

| 日期 | 事项 | 阻塞原因 | 需要的支持 |
|---|---|---|---|
| （暂无） | | | |
| 备注 | G4 的 push / G5~G7 未执行 | gh CLI 未安装、无 GitHub/Vercel/Railway 凭据；本地 git（init/commit/subtree/remote）已全部完成 | 用户按 docs/01 §1 建 `gtx-fso-litho` 空仓库后 `git push -u origin main`，再按 docs/04 部署 |
