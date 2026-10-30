# 11 · VSCode 工程化 · 代码推拉 · 部署（Vercel / Cloudflare）· Supabase 接入

## 1. VSCode 日常工程化（本项目已配好）

| 动作 | 操作 |
|---|---|
| 打开工程 | File → Open Folder → `D:\codex\2026-10-28-23-35-39`（必须开根目录，`python -m backend.solver` 依赖它） |
| 解释器 | Ctrl+Shift+P → Python: Select Interpreter → `./.venv/Scripts/python.exe` |
| 一键任务 | Ctrl+Shift+P → Tasks: Run Task → `venv:create` / `install:pip` / `run:solver` / `run:api` |
| 调试 | F5 → `Python: litho_solver`（六步算法）/ `Python: FastAPI`（:8000）/ `Python: pytest`（当前文件） |
| 前端 | 终端 `cd frontend && npm run dev`（:5173）；调试 JS 用浏览器 F12 |
| 测试 | 终端 `.venv\Scripts\python.exe -m pytest tests/ -q`（必须全绿再提交） |

## 2. 代码推拉（当前 remote 布局）

```
origin      → github.com/huangfengtaba-web/my-prototype.git   （日常推送，分支 feat/gtx-fab-fusion）
origin-gtx  → github.com/huangfengtaba-web/gtx-fso-litho.git  （旧地址备份）
semiconfab  → 上游 SemiconFab（只用于 subtree 同步，勿直接 push）
```

```bash
# 日常推（在 feat/gtx-fab-fusion 分支）
git status && git add <具体文件> && git commit -m "feat: xxx"
git -c http.proxy=http://127.0.0.1:10808 -c https.proxy=http://127.0.0.1:10808 push

# 拉取（多人协作 / 换机器）
git -c http.proxy=http://127.0.0.1:10808 pull origin feat/gtx-fab-fusion

# 验收后合 main（GitHub PR 或本地）
git checkout main && git merge feat/gtx-fab-fusion && git push origin main
```

## 3. 部署拓扑（谁放哪里，为什么）

| 组件 | 平台 | 原因 |
|---|---|---|
| 前端（静态 dist） | **Vercel** 或 **Cloudflare Pages**（二选一，都能放） | 纯静态，两家免费额度都够 |
| 后端（FastAPI+CBC） | **Railway / Render / Fly.io**（容器平台） | ❌ Vercel/CF Workers 跑不了 CBC 常驻进程；后端必须常驻容器 |
| 数据库 | **Supabase**（Postgres） | 免费额度、自带面板；放运行记录/Lot 快照/错误日志 |
| WPS 文档生成 | 只能本地 Windows（DOCGEN_ENABLED=0 关闭） | COM 依赖桌面会话 |

### 3.1 前端 → Vercel（已配好 vercel.json）

Root Directory=frontend，Framework=Vite，环境变量 `VITE_API_BASE_URL=https://<后端域名>`。

### 3.2 前端 → Cloudflare Pages（备选）

Workers & Pages → Create → 连 Git 仓库 → 构建命令 `npm run build`、输出目录 `frontend/dist`、
Root Directory 留空（在根加 Package Path=frontend 亦可）。路由重定向已备好 `frontend/public/_redirects`
（构建时自动进 dist，语义与 vercel.json 一致）。环境变量同上。

### 3.3 后端 → Railway（推荐）/ Render

- Railway：New Project → Deploy from Git → 选仓库；**Root Directory = 仓库根**；
  Start Command：`uvicorn backend.app.api:app --host 0.0.0.0 --port $PORT`；
  Variables：`LITHO_CORS_ORIGINS=https://<前端域名>`、`SUPABASE_DB_URL=<第4步的连接串>`。
- Render：同类；免费层有 15 分钟冷启动，演示可接受（docs/04 §6）。
- `backend/nixpacks.toml` / `runtime.txt` / `Procfile` 已备齐。

## 4. Supabase（Postgres）接入

### 4.1 建表（Supabase SQL Editor 执行一次）

```sql
create table if not exists solve_runs (
  run_id      text primary key,
  case_name   text,
  status      text,
  started_at  text,
  finished_at text,
  milp        jsonb,
  summary     jsonb,
  created_at  timestamptz default now()
);
create table if not exists solve_errors (
  run_id     text,
  error_type text,
  error_info text,
  detail     text,
  created_at timestamptz default now()
);
```

### 4.2 项目侧连接（已实现，环境变量开关）

- 连接串：Supabase → Project Settings → Database → Connection string (URI)，
  **用连接池端口 6543**（serverless/容器友好）：`postgresql://postgres.<ref>:<pwd>@aws-0-<region>.pooler.supabase.com:6543/postgres`
- `.env`：`SUPABASE_DB_URL=postgresql://...`
- 代码：`backend/app/store.py` —— `SUPABASE_DB_URL` 未设置时**内存模式**（现状不变）；
  设置后每次求解完成自动 `persist_run()`（写 solve_runs；失败写 solve_errors），失败不影响 API（try/except）。
- 依赖：`pip install psycopg2-binary`（requirements 已含）。

### 4.3 验证

```bash
curl -X POST http://127.0.0.1:8000/api/solve/run -H "Content-Type: application/json" -d '{}'
# Supabase → Table Editor → solve_runs 应出现一行
```

## 5. 常见坑速查

| 坑 | 处理 |
|---|---|
| push 403 | 密码栏填 PAT（GitHub → Developer settings → Tokens classic，勾 repo） |
| 推送超时 | 确认代理 10808 在跑；命令带 `-c http.proxy=...` |
| Vercel 页面 404 | vercel.json rewrites 已配齐；确认用的是最新分支 |
| 后端 CORS 报错 | `LITHO_CORS_ORIGINS` 填前端精确域名（逗号分隔），不要 * |
| Supabase 连接失败 | 用 pooler 6543 端口；密码含特殊字符做 URL 编码 |
