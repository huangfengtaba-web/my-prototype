# 04 · 部署指南（Vercel 前端 + Render 后端）

> 前置：MVP 档已本地跑通（见 [`03_ALGORITHM_DEMO.md`](03_ALGORITHM_DEMO.md) 第 5 节验收四项）。
> 需要用户授权 Vercel / Render 账号。Railway 2026-11 起新用户注册受限，已降为备选。

---

## 1. 架构

```
浏览器
  │
  ├──→ Vercel（静态）     frontend/dist/      9 页原型 + 求解演示页
  │
  └──→ Render（容器）     backend/            FastAPI + PuLP/CBC
         │
         └─ subprocess: python -m backend.solver run
```

**为什么不能全放 Vercel**：Vercel 的 Serverless 跑不了 CBC 求解器的二进制依赖，
且冷启动 + 子进程调用不可靠。后端必须常驻容器。

---

## 2. 前端部署（Vercel）

### 2.1 配置文件

`frontend/vercel.json`：

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    { "source": "/prototypes/:path", "destination": "/prototypes/:path" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### 2.2 部署步骤

1. 登录 <https://vercel.com> → Add New → Project
2. Import `huangfengtaba-web/gtx-fso-litho`
3. **Root Directory 设为 `frontend`**（关键，否则找不到 package.json）
4. Framework Preset：`Vite`
5. Build Command：`npm run build`，Output：`dist`
6. Environment Variables：
   - `VITE_API_BASE_URL` = `https://你的后端域名.railway.app`
7. Deploy

### 2.3 前端代码要注意

API 地址不能硬编码，从环境变量读：

```js
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
```

这样本地开发走 localhost，生产走 Render。

---

## 3. 后端部署（Render —— 主推；Railway 因注册限制降为备选）

> **逐步点击级操作见 [`docs/11_VSCODE_DEPLOY_SUPABASE.md` §4](11_VSCODE_DEPLOY_SUPABASE.md)**
> （含 Blueprint 一键部署 / 手动创建 / Docker 兜底三种方式、环境变量表、报错排查、免费层限制）。
> 本节只保留要点与差异。

### 3.1 为什么是 Render

- **免信用卡**、GitHub 登录即用（Railway 2026-11 起新用户注册受限）
- 免费层 750 实例小时/月；15 分钟无请求休眠（演示前 curl 一次 `/api/health` 唤醒）
- 仓库根已提供 **`render.yaml`**（Blueprint）：构建/启动命令、健康检查、环境变量全版本化

### 3.2 Render 逐步（Blueprint 方式，2 分钟）

1. https://dashboard.render.com → **New + → Blueprint** → 连接 `my-prototype` 仓库（分支 `feat/gtx-fab-fusion`）
2. Render 解析 `render.yaml` → 弹出环境变量表单（`sync: false` 的项）：
   - `LITHO_CORS_ORIGINS` = `https://你的前端域名.vercel.app`（精确域名，不要 `*`）
   - `SUPABASE_DB_URL` = §5.3 的连接串（可后补）
   - `DIFY_BASE` / `DIFY_KEY_*` / `API_PUBLIC_BASE`（可后补）
3. **Apply** → 构建约 5~10 分钟 → 域名 `https://gtx-fso-litho-api.onrender.com`

### 3.3 验证

```bash
curl https://gtx-fso-litho-api.onrender.com/api/health
# {"ok":true,"solver":"CBC","agent_mode":"rule",...}

curl -X POST https://gtx-fso-litho-api.onrender.com/api/solve/run      -H "Content-Type: application/json" -d '{}'
# 首次调用含冷启动，等 30~60 秒属正常
```

### 3.4 Railway（备选）

若你已有可用 Railway 账号：Start Command `uvicorn backend.app.api:app --host 0.0.0.0 --port $PORT`、
Root Directory=仓库根、`nixpacks.toml` 已备。新用户注册受限，详见 docs/11 §4.5 平台对比。

---

## 4. CORS 配置

`backend/app/api.py`：

```python
import os
from fastapi.middleware.cors import CORSMiddleware

origins = os.getenv("LITHO_CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_methods=["*"], allow_headers=["*"])
```

本地默认放行 5173；生产用环境变量覆盖。**不要用 `allow_origins=["*"]` 上线。**

---

## 5. 环境变量清单

| 变量 | 位置 | 默认值 | 说明 |
|---|---|---|---|
| `VITE_API_BASE_URL` | Vercel | `http://127.0.0.1:8000` | 前端调后端地址 |
| `LITHO_CORS_ORIGINS` | Render/Railway | `http://localhost:5173` | 逗号分隔白名单 |
| `LITHO_SOLVER` | Render/Railway | `CBC` | 预留 Gurobi/COPT 切换 |
| `LITHO_TIME_LIMIT_S` | Render/Railway | `60` | 单次求解超时 |

`.env.example` 需包含以上四项（无值或默认值）。

---

## 6. 免费层限制与降级

| 平台 | 限制 | 表现 | 降级方案 |
|---|---|---|---|
| Vercel Hobby | 每月 100 GB 带宽、构建次数 | 超限后站点暂停 | 换 Cloudflare Pages（静态站免费无限） |
| Railway 免费 | $5 额度 / 月，约 500 小时 | 额度耗尽停机 | 换 Render 免费层（**但有冷启动 30s**） |
| Render 免费 | 15 分钟无请求休眠 | 首次请求等 30s+ | 前端加「唤醒中」提示，或定时 ping |

**推荐组合**：Vercel（前端）+ Render（后端）。Render 冷启动虽慢，但免费层长期可用，
且对「演示场景」来说，点一次等 30s 可接受。

**彻底规避冷启动**：把求解结果**预生成**为静态 JSON，前端直接读。
代价是失去「现场改参数实时求解」的能力 —— 演示时按需要权衡。

---

## 7. 部署后验证清单

- [ ] 前端首页能打开（9 页全在）
- [ ] 9 页之间点击跳转无 404
- [ ] `/scheduling-test` 页点「运行求解」能拿到结果（**核心验收点**）
- [ ] 浏览器 Console 无 CORS 报错
- [ ] 后端 `/api/health` 返回 200
- [ ] 求解耗时 < 10s（含冷启动）
- [ ] 移动端/小屏不崩（可选）

---

## 8. 回滚

```bash
# Vercel：Deployments 页 → 选上一个成功版本 → Promote to Production
# Railway：Deployments → 选历史版本 → Redeploy
# 本地：git revert <commit> && git push
```

若后端挂了但前端还在，前端会一直转圈 —— 在 `/scheduling-test` 页加超时提示（8s 无响应提示「后端可能在冷启动」）。
