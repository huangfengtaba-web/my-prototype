# 11 · VSCode 工程化 · 代码推拉 · 部署（Vercel / Cloudflare）· Supabase 接入 —— 逐步操作手册

> 面向第一次上手的人：每一步都给出「在哪点、点什么、敲什么」。跟着从上往下走即可。
> 工程根：`D:\codex\2026-10-28-23-35-39`（下文简写为 `<根>`）

---

## 0. 准备清单（一次性）

| 项 | 去哪弄 | 说明 |
|---|---|---|
| VSCode | https://code.visualstudio.com | 装好后装扩展：**Python**（带 Pylance）、可选中文包 |
| Git | https://git-scm.com（你已有，Git Bash 可用） | `git --version` 验证 |
| Python 3.11 | 已有 miniconda（`D:/software/miniconda/anzhuang/python.exe`） | 项目自带 `.venv`，无需再装 |
| Node.js | 已有（npm 可用） | 前端构建用 |
| GitHub 账号 | https://github.com | 需要一个 **Personal Access Token**（见 §2.1） |
| 代理 | `http://127.0.0.1:10808` 在运行 | GitHub / 部分网站需要 |
| Vercel 账号 | https://vercel.com（用 GitHub 登录） | 前端部署 |
| Cloudflare 账号 | https://dash.cloudflare.com（可选） | 前端备选部署 |
| Railway 账号 | https://railway.app（用 GitHub 登录） | 后端部署 |
| Supabase 账号 | https://supabase.com（用 GitHub 登录） | 数据库 |

---

## 1. VSCode 工程化（每一步的点击）

### 1.1 打开工程（必须开根目录）

1. VSCode → **File → Open Folder…**
2. 选 `D:\codex\2026-10-28-23-35-39` → **选择文件夹**
3. 左侧资源管理器应看到：`frontend/ backend/ docs/ tests/ .vscode/ …`
   ⚠️ 不要打开 `backend/` 子目录——`python -m backend.solver` 必须以仓库根为工作目录。

### 1.2 选解释器（第一次必做）

1. `Ctrl+Shift+P` → 输入 **Python: Select Interpreter** → 回车
2. 选 **`.\.venv\Scripts\python.exe`**（列表里带 `./.venv` 标记的那一项）
3. 验证：新建终端（`Ctrl+` ` `）→ 输入 `python -c "import pulp; print(pulp.__version__)"` → 打印版本号即 OK
   （若提示找不到 `.venv`：先跑任务 `venv:create`，再跑 `install:pip`，见 1.3）

### 1.3 四个一键任务（.vscode/tasks.json 已配好）

1. `Ctrl+Shift+P` → 输入 **Tasks: Run Task** → 回车
2. 依次可用：
   - **venv:create** —— 创建虚拟环境（只在第一次，或删了 .venv 之后）
   - **install:pip** —— 安装/更新后端依赖（拉完代码后建议跑一次）
   - **run:solver** —— 命令行跑六步算法（输出在 `backend/solver/output/`）
   - **run:api** —— 起 FastAPI 后端 `http://127.0.0.1:8000`（终端会一直占着，属正常）
3. 起前端：终端里 `cd frontend; npm install; npm run dev` → 浏览器开 `http://localhost:5173`

### 1.4 F5 调试（.vscode/launch.json 已配好）

按 `F5`（或左侧「运行和调试」→ 顶部下拉选）：
- **Python: litho_solver** —— 跑六步算法，可在 `litho_solver.py` 里打断点看变量
  （推荐断点：step2 求解前看约束数、step3 `l["start"]` 赋值处看开工时间）
- **Python: FastAPI** —— 调试后端；在 `api.py` 的函数里打断点，前端点按钮即触发
- **Python: pytest** —— 先在编辑器打开某个测试文件再按 F5，只跑该文件

调试控制台查 MILP 变量（断在 step2 时）：
```python
[k for k, v in x.items() if v.value() > 0.5]   # 哪些 Lot 分给了哪台机
pulp.value(prob.objective)                     # 目标函数值
```

### 1.5 改完代码的自检铁律

```bash
.venv\Scripts\python.exe -m pytest tests/ -q     # 必须 33 passed（全绿）才能提交
cd frontend && npm run build                      # 前端改动必须构建通过
```

---

## 2. 代码推拉（Git）

### 2.1 第一次配置（只做一次）

1. 生成 Token：GitHub → 右上头像 → **Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)** → 勾 `repo` 权限 → 生成后**立刻复制**（只显示一次）
2. Git 身份（已配好可跳过）：
   ```bash
   git config --global user.name "你的名字"
   git config --global user.email "你的邮箱"
   ```

### 2.2 当前 remote 布局（已配好，`git remote -v` 查看）

```
origin      → github.com/huangfengtaba-web/my-prototype.git   日常推送目标
origin-gtx  → github.com/huangfengtaba-web/gtx-fso-litho.git  旧地址备份
semiconfab  → 上游开源仓库（只用于同步，勿 push）
```

### 2.3 日常推（三步）

```bash
cd /d/codex/2026-10-28-23-35-39
git status                          # ① 看改了什么
git add <具体文件或目录>             # ② 不要盲目 git add . 养成习惯
git commit -m "feat: 一句话说清改动" # ③ 类型前缀：feat/fix/docs/refactor/chore
git -c http.proxy=http://127.0.0.1:10808 -c https.proxy=http://127.0.0.1:10808 push
```
推的时候弹认证：用户名填 GitHub 用户名，**密码填 §2.1 的 Token**。

### 2.4 日常拉（换机器 / 多人协作前先拉）

```bash
git -c http.proxy=http://127.0.0.1:10808 -c https.proxy=http://127.0.0.1:10808 pull origin feat/gtx-fab-fusion
```

### 2.5 验收合并 main

GitHub 上发 PR：`feat/gtx-fab-fusion` → `main`（推送后 GitHub 页面有现成链接）；或本地：
```bash
git checkout main && git merge feat/gtx-fab-fusion
git -c http.proxy=http://127.0.0.1:10808 push origin main
```

### 2.6 常见报错

| 报错 | 处理 |
|---|---|
| `Authentication failed` | 密码栏填 Token，不是 GitHub 密码 |
| `Failed to connect` | 代理没开，或命令没带 `-c http.proxy=…` |
| `Your branch has diverged` | 先 `git pull --rebase` 解决冲突再推 |

---

## 3. 前端部署（Vercel 与 Cloudflare Pages 二选一）

> 前提：代码已推到 GitHub；后端已部署并拿到域名（见 §4），或先用 `http://127.0.0.1:8000` 本地联调。

### 3.1 Vercel（推荐先做这个）

1. https://vercel.com → **Add New → Project**
2. **Import** 你的 `my-prototype` 仓库（授权 GitHub 访问）
3. 配置页：
   - **Root Directory**：点 Edit → 选 `frontend`（关键！否则找不到构建配置）
   - Framework Preset：**Vite**（自动识别）
   - Build Command：`npm run build`；Output Directory：`dist`（自动）
4. **Environment Variables** 加一条：
   - Name：`VITE_API_BASE_URL`
   - Value：`https://<你的后端域名>`（§4 部署完拿到；后端没好可先留空，本地联调）
5. **Deploy** → 等 1~2 分钟 → 拿到 `https://xxx.vercel.app`
6. 验收清单：首页打开 → 侧边栏 17 项逐个点 → 「求解演示」页点「运行求解」出结果 → 无 CORS 报错

### 3.2 Cloudflare Pages（备选）

1. https://dash.cloudflare.com → **Workers & Pages → Create → Pages → Connect to Git**
2. 选仓库 → 构建配置：
   - Framework preset：**Vite**
   - Build command：`npm run build`
   - Build output directory：`frontend/dist`
   - 环境变量：`VITE_API_BASE_URL` 同上
3. **Save and Deploy**
4. 路由重定向已备好：`frontend/public/_redirects` 构建时自动进 dist（与 vercel.json 语义一致）
5. 验收同 §3.1 第 6 步

> 改前端代码后：`git push` 会**自动触发**两家重新部署（不用手动点）。

---

## 4. 后端部署（Railway，必须容器平台）

> 为什么不能放 Vercel/Cloudflare Workers：CBC 求解器是编译好的本地二进制 + 常驻进程 +
> 子进程调用，Serverless 函数模型跑不了。Railway / Render / Fly.io 这类容器平台都可以。

### 4.1 Railway 逐步

1. https://railway.app → **New Project → Deploy from GitHub repo** → 选 `my-prototype`
2. 服务卡片 → **Settings**：
   - **Root Directory**：`/`（留空，仓库根——`backend.` 包路径依赖它）
   - Custom Start Command：`uvicorn backend.app.api:app --host 0.0.0.0 --port $PORT`
3. **Variables** 标签加环境变量：
   - `LITHO_CORS_ORIGINS` = `https://xxx.vercel.app`（前端域名，精确值，不要 `*`）
   - `SUPABASE_DB_URL` = `postgresql://…`（§5.3 拿到后再填，可后补）
   - `LITHO_SOLVER` = `CBC`
4. **Deploy** → 部署完在 Settings → Networking → **Generate Domain** → 拿到 `https://xxx.up.railway.app`
5. 验证：
   ```bash
   curl https://xxx.up.railway.app/api/health
   # {"ok":true,"solver":"CBC","agent_mode":"rule","docgen_enabled":false,...}
   ```
   ⚠️ 部署后如果报 `PulpSolverError`：Settings → Build 里加 Nixpacks 配置装 `coinor-cbc`（backend/nixpacks.toml 已写好注释）。
6. 回到 Vercel/Cloudflare 把 `VITE_API_BASE_URL` 改成这个后端域名 → 重新部署前端 → 前后端联调完成

### 4.2 Render（备选，免费层有 15 分钟冷启动）

New → Web Service → 连仓库 → Root Directory 留空 → Build：`pip install -r backend/requirements.txt` →
Start：`uvicorn backend.app.api:app --host 0.0.0.0 --port $PORT` → 环境变量同上。

### 4.3 免费额度提醒

| 平台 | 免费限制 | 表现 |
|---|---|---|
| Vercel Hobby | 100GB 带宽/月 | 演示足够 |
| Cloudflare Pages | 无限请求 | 演示足够 |
| Railway | $5 额度/月 | 额度尽会停机，注意用量 |
| Render 免费 | 15 分钟无请求休眠 | 首次访问等 ~30s |

---

## 5. Supabase 数据库接入（完整建表 SQL）

> 作用：把每次求解的运行头 / 逐 Lot 明细 / 错误持久化到 Postgres。
> 代码已实现（`backend/app/store.py`）：`.env` 里 `SUPABASE_DB_URL` **不设 = 内存模式（现状不变）**；设了 = 每次求解自动写入，失败只打日志不影响 API。

### 5.1 注册并建项目

1. https://supabase.com → **Sign in with GitHub**
2. **New project**：Name 填 `gtx-fso-litho`；Database Password **自己设一个并保存**（后面要用）；Region 选 Singapore/Japan（离得近）
3. 等待 ~2 分钟初始化完成

### 5.2 建表（完整 SQL，直接粘贴执行）

Supabase 左侧 **SQL Editor** → **New query** → 粘贴以下全部 → **Run**（右下角）→ 显示 `Success. No rows returned` 即成功：

```sql
-- ============================================================
-- GTX FSO Litho · 求解记录持久化（运行头 / 逐 Lot 明细 / 错误）
-- ============================================================

-- ① 运行头：每次六步 MILP 求解一条
create table if not exists solve_runs (
  run_id      text primary key,                 -- 8 位短码（API 返回的 run_id）
  case_name   text,                             -- scenario 名（null = 基线）
  status      text,                             -- done / suboptimal / failed / timeout
  started_at  text,                             -- 求解开始（字符串时间）
  finished_at text,                             -- 求解结束
  milp        jsonb,                            -- {"step2":"Optimal","step3":"Optimal"}
  summary     jsonb,                            -- 完整 run_summary（含六步/甘特/光罩五态）
  created_at  timestamptz default now()
);

-- ② 逐 Lot 明细：每次运行的排程结果行（Scanner Schedule 口径）
create table if not exists solve_lots (
  id         bigserial primary key,
  run_id     text not null references solve_runs(run_id) on delete cascade,
  lot_id     text,
  eqp        text,
  eqp_group  text,
  reticle    text,
  priority   text,                              -- PRI1~PRI4（含属性推导结果）
  temp       text,
  start_time text,
  end_time   text,
  barc_er    text,                              -- BARC 最早放货
  barc_lr    text,                              -- BARC 最晚放货
  post_note  text                               -- ④后处理/校准说明（卡控原因）
);
create index if not exists idx_solve_lots_run  on solve_lots(run_id);
create index if not exists idx_solve_lots_lot  on solve_lots(lot_id);

-- ③ 错误记录：求解失败/超时/非最优时写入（Error Management 口径）
create table if not exists solve_errors (
  id         bigserial primary key,
  run_id     text,
  error_type text,                              -- DATA_ERROR / MODEL_ERROR / UNKNOWN_ERROR
  error_info text,
  detail     text,
  created_at timestamptz default now()
);
create index if not exists idx_solve_errors_run on solve_errors(run_id);
```

（可选）加一条方便查询的视图——「每次运行的急货完工时间」：
```sql
create or replace view v_urgent_completion as
select r.run_id, r.case_name, r.status, l.eqp, l.end_time
from solve_runs r join solve_lots l on l.run_id = r.run_id
where l.lot_id = 'LOT-A01';
```

### 5.3 拿连接串

1. Supabase → **Project Settings → Database → Connection string → URI**
2. 选 **Connection pooler**（端口 6543）那一段（容器部署更稳）
3. 把 `[YOUR-PASSWORD]` 替换成 §5.1 设置的数据库密码，得到形如：
   ```
   postgresql://postgres.abcdefgh:你的密码@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
   ```

### 5.4 项目侧配置

工程根 `.env`（没有就从 `.env.example` 复制）加一行：
```ini
SUPABASE_DB_URL=postgresql://postgres.abcdefgh:你的密码@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```
本地重启后端；Railway/Render 上把同样内容加到 Variables。

### 5.5 验证

```bash
curl -X POST http://127.0.0.1:8000/api/solve/run -H "Content-Type: application/json" -d "{}"
```
然后 Supabase → **Table Editor**：
- `solve_runs` 出现一行，`milp` 字段展开可见 `{"step2":"Optimal",…}`
- `solve_lots` 出现 9~10 行（Lot 明细）
- 故意制造一次错误（把 `.env` 临时改 `LITHO_SOLVER=GUROBI` 重启再求解）→ `solve_errors` 出现记录 → 记得改回来

命令行直查：
```bash
.venv\Scripts\python.exe -c "import psycopg2,os; \
c=psycopg2.connect(os.environ['SUPABASE_DB_URL']); \
cur=c.cursor(); cur.execute('select run_id,status from solve_runs order by created_at desc limit 5'); \
print(cur.fetchall())"
```

### 5.6 排错

| 报错 | 处理 |
|---|---|
| `connection timed out` | 用 **pooler 6543** 端口的串；确认项目没被暂停（免费项目一周不活跃会休眠，面板里 Restore） |
| `password authentication failed` | 密码特殊字符要 URL 编码（`@`→`%40`）；或重置数据库密码 |
| `relation "solve_runs" does not exist` | §5.2 的 SQL 没在该项目执行 |
| 后端日志 `[store] 持久化失败` | 看具体异常；持久化失败不影响 API，修好连接自动恢复 |

---

## 6. Dify 线上工作流接入（接口对接设置，逐步操作）

> 原理：系统**不在本地装 Dify**。你在自己的线上 Dify 建好 3 个应用后，项目通过 `.env` 里的
> App Key 调用它们；Dify 应用里的 HTTP 节点再回调本地后端拿数据。**没配置/不可达时自动
> 本地降级**（`/api/workflow/run` 返回 `mode=local_fallback`，HTTP 恒 200），所以随时可以接。
> 参考文档：`docs/08_DIFY_INTEGRATION.md`（接口契约）；DSL 骨架：`dify/dsl/` 三个文件。

### 6.1 对应关系（先搞清楚谁对谁）

| 项目模板（TEMPLATES id） | dify_key（环境变量后缀） | Dify 应用类型 | DSL 骨架 |
|---|---|---|---|
| `daily-scheduling` | `DIFY_KEY_DAILY_SCHEDULING` | Workflow | `dify/dsl/daily-scheduling.yaml` |
| `scenario-compare` | `DIFY_KEY_SCENARIO_COMPARE` | Workflow | `dify/dsl/scenario-compare.yaml` |
| （智能问答，前端暂未挂） | `DIFY_KEY_QA_CHATFLOW` | Chatflow | `dify/dsl/qa-chatflow.yaml` |

运行链路：前端 `/ai-workflow` 点运行 → `POST /api/workflow/run` → 后端 `run_with_fallback()` →
配置了 Key 且可达 → 调 Dify（`mode=dify`）；否则本地步骤引擎（`mode=local_fallback`）。

### 6.2 ① 线上 Dify 创建 3 个应用（导入 DSL）

1. 登录你的 Dify（SaaS：https://cloud.dify.ai；自托管：你的域名）
2. 首页 **工作室（Studio）** → **创建应用 → 导入 DSL 文件** → 选 `dify/dsl/daily-scheduling.yaml`
3. 同样导入 `scenario-compare.yaml`、`qa-chatflow.yaml`（共 3 个应用）
4. 进入每个应用的**编排**页面：
   - 每个 **LLM 节点**：点开 → 模型下拉 → 选你有额度的模型（骨架默认 gpt-4o-mini，可换 glm-4-flash/qwen-plus）
   - **HTTP 请求节点**：URL 应显示 `{{#env.API_PUBLIC_BASE#}}/api/solve/run` —— 环境变量下一步填
   - `qa-chatflow`：先 **知识库 → 创建知识库** → 上传 `docs/specs/01~07*.md` 与 `docs/03_ALGORITHM_DEMO.md`
     → 回到应用编排页，**知识检索节点** → 绑定刚建的知识库
5. 每个**发布**（右上「发布」按钮）——未发布的应用 API 调不通

### 6.3 ② 配置应用内环境变量（HTTP 节点的回调地址）

每个 Workflow 应用编排页 → **环境变量（ENV）** 面板 → `API_PUBLIC_BASE` → 填第 6.4 步的隧道地址
（先起隧道再回来填，或填好后重启隧道不改值）。

### 6.4 ③ 内网穿透（让线上 Dify 能访问你本机后端）

```powershell
# 安装（一次性）：winget install Cloudflare.cloudflared  或官网下载 exe
cloudflared tunnel --url http://localhost:8000
# 输出里找形如：https://xxx-yyy-zzz.trycloudflare.com  ← 这就是 API_PUBLIC_BASE
```
验证：浏览器开 `https://xxx.trycloudflare.com/api/health` → 返回 JSON 即通。
⚠️ 隧道地址每次重启会变——变了就同步更新 Dify 应用环境变量和 `.env`。

### 6.5 ④ 拿 App Key 并配置项目

1. 每个应用 → 左侧 **访问 API（Access API）** → 右上 **API 密钥** → **创建** → 复制 `app-xxxx`
2. 工程根 `.env` 追加：
```ini
DIFY_BASE=https://api.dify.ai/v1            # 自托管填 https://你的域名/v1
DIFY_KEY_DAILY_SCHEDULING=app-xxxx
DIFY_KEY_SCENARIO_COMPARE=app-yyyy
DIFY_KEY_QA_CHATFLOW=app-zzzz
API_PUBLIC_BASE=https://xxx-yyy.trycloudflare.com
```
3. 重启后端（tasks.json 的 `run:api`，或终端 Ctrl+C 后重跑）

### 6.6 ⑤ 验证（三关）

```bash
# 第一关：配置识别（每个模板 dify_configured 应为 true）
curl http://127.0.0.1:8000/api/workflow/templates

# 第二关：真走 Dify（mode=dify，含 workflow_run_id 与耗时）
curl -X POST http://127.0.0.1:8000/api/workflow/run \
  -H "Content-Type: application/json" -d "{\"template_id\":\"daily_scheduling\"}"

# 第三关：降级保护（清空 .env 的 DIFY_KEY_* 重启再调 → mode=local_fallback，HTTP 仍 200）
```
前端 `/ai-workflow`：右上徽章 **绿色「Dify 线上」**；运行后事件流显示 Dify 返回的
outputs/耗时/节点数；把 Key 清空重启 → 徽章变灰「本地降级」+ 原因 tooltip。

### 6.7 Dify → 项目回调接口清单（HTTP 节点可用）

```
GET  /api/health                     探活
GET  /api/mock/data                  机台/Lot/光罩/配置
GET  /api/cases                      Scenario 用例列表
POST /api/solve/run                  跑六步 MILP        body {"case":"urgent-A01"}
GET  /api/solve/result/{run_id}      取排程结果
POST /api/sim/run                    执行态仿真          body {"case":"...","seed":42}
GET  /api/twin/timeline/{run_id}     3D 时间轴事件流
POST /api/doc/render                 生成文档（本地 Windows）
```

### 6.8 排错

| 现象 | 原因 | 处理 |
|---|---|---|
| 徽章一直「本地降级」 | Key 未配/错、DIFY_BASE 错 | 核对 `.env`；`/api/workflow/templates` 看 `dify_configured` |
| Dify 返回 4xx | 应用未发布 / Key 复制错 | 重新发布、重新生成 Key |
| HTTP 节点超时 | 隧道断了 / blocking 超 100s | 重开 cloudflared；长流程后续可扩 streaming |
| 回调 404 | API_PUBLIC_BASE 填错 | 外网浏览器先自测 `/api/health` |
| Key 安全 | 写进了前端 | `grep -rn "DIFY_KEY" frontend/` 必须无输出（仓库已保持） |

---

## 7. 上线验收清单（全部打勾才算部署完成）

- [ ] Vercel/Cloudflare 前端打开正常，17 项导航逐个点无 404
- [ ] 前端「求解演示/排程结果」能真跑求解（走线上后端）
- [ ] `https://<后端域名>/api/health` 返回 200
- [ ] `.env` 的 `LITHO_CORS_ORIGINS` 是前端精确域名（浏览器 Console 无 CORS 报错）
- [ ] Supabase 三张表有数据
- [ ] （本地 Windows）文档生成页可下载 docx；云端该功能显示停用提示属正常
- [ ] Dify：`/api/workflow/templates` 全部 `dify_configured=true`；运行返回 `mode=dify`；
      清空 Key 后 `mode=local_fallback` 且页面徽章同步；`grep -rn "DIFY_KEY" frontend/` 无输出
