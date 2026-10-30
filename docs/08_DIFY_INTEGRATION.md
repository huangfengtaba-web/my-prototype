# 08 · Dify 线上工作流接入指南（手把手）

> 原则：**Dify 在你自己的线上**（SaaS 或自托管域名），本项目只做「调用它」和「被它回调」，
> 不在本地装 Dify、不拉镜像。未配置时系统自动走本地降级（页面徽章可见），所以随时可以配、可以不配。

## 1. 接入总览（5 步）

```
① 线上 Dify 建 3 个应用（导入 dify/dsl/ 骨架）
② 应用里 HTTP 节点的 Base URL 填 API_PUBLIC_BASE（你的内网穿透地址）
③ cloudflared 起隧道，拿到公网地址
④ 项目 .env 填 DIFY_BASE + 3 个 App Key + API_PUBLIC_BASE → 重启后端
⑤ /ai-workflow 页点运行 → 徽章变「Dify 线上」即接通
```

## 2. 第①步：线上建 3 个应用

| 应用 | 类型 | 导入文件（dify/dsl/） | 对应环境变量 |
|---|---|---|---|
| 日计划排程 | Workflow | `daily-scheduling.yaml` | `DIFY_KEY_DAILY_SCHEDULING` |
| 场景对比 | Workflow | `scenario-compare.yaml` | `DIFY_KEY_SCENARIO_COMPARE` |
| 智能问答 | Chatflow | `qa-chatflow.yaml` | `DIFY_KEY_QA_CHATFLOW` |

操作：Dify 控制台 → 创建应用 → **导入 DSL** → 选上面文件 → 进入编排页：
- 给 LLM 节点选一个你有额度的模型（骨架默认 `gpt-4o-mini`，可换 glm-4-flash / qwen-plus 等）
- 智能问答需先建知识库（上传 `docs/specs/*.md`、`docs/03_ALGORITHM_DEMO.md`），并在知识检索节点绑定

**发布应用**后，在「访问 API」页拿到每个应用的 **App Key**（`app-` 开头）。
⚠️ Key 只填进项目 `.env`（后端读），**绝不写进任何前端代码**（仓库已用 grep 自检兜底）。

## 3. 第②步：HTTP 节点回调本地后端

每个骨架里的 HTTP Request 节点 URL 是 `{{#env.API_PUBLIC_BASE#}}/api/...`。在 Dify 应用里
**环境变量** `API_PUBLIC_BASE` 填你的内网穿透地址（见第③步）。可用的回调接口：

```
GET  /api/health            GET  /api/mock/data        GET  /api/cases
POST /api/solve/run         GET  /api/solve/result/{run_id}
POST /api/sim/run           GET  /api/twin/timeline/{run_id}
POST /api/doc/render
```

## 4. 第③步：内网穿透（线上 Dify 访问不到你的 localhost）

```powershell
# 方案 A（推荐，免费）：cloudflared
cloudflared tunnel --url http://localhost:8000
# 输出形如 https://xxx-yyy.trycloudflare.com

# 方案 B：ngrok http 8000
```

安全提示：隧道用完即关；`.env` 里 `LITHO_CORS_ORIGINS` 保持精确域名，不要 `*`。

## 5. 第④步：项目 .env

```ini
DIFY_BASE=https://api.dify.ai/v1        # 或你的自托管 Dify 域名 + /v1
DIFY_KEY_DAILY_SCHEDULING=app-xxxx
DIFY_KEY_SCENARIO_COMPARE=app-yyyy
DIFY_KEY_QA_CHATFLOW=app-zzzz
API_PUBLIC_BASE=https://xxx-yyy.trycloudflare.com
```

重启后端：`.venv\Scripts\python.exe -m uvicorn backend.app.api:app --reload --port 8000`

## 6. 第⑤步：验证

```bash
# 1) 配置识别
curl http://127.0.0.1:8000/api/workflow/templates
# 每项 dify_configured 应为 true

# 2) 真跑一次（走 Dify）
curl -X POST http://127.0.0.1:8000/api/workflow/run \
  -H "Content-Type: application/json" -d '{"template_id":"daily_scheduling"}'
# → "mode":"dify"，含 workflow_run_id / elapsed / outputs

# 3) 降级验证：清空 Key 重启 → 同接口返回 "mode":"local_fallback"，HTTP 仍 200
```

前端 `/ai-workflow` 页右上角徽章：绿「Dify 线上」/ 灰「本地降级」（含原因 tooltip）。

## 7. 排错

| 现象 | 原因 | 处理 |
|---|---|---|
| 徽章一直「本地降级」 | Key 未配 / DIFY_BASE 错 | 核对 .env；`/api/workflow/templates` 看 dify_configured |
| Dify 返回 HTTP 4xx | App Key 错或应用未发布 | 重新发布应用、重新复制 Key |
| HTTP 节点超时 | 隧道断了 / blocking 超 100s | 重开 cloudflared；长流程用 streaming（后续可扩展） |
| 回调 404 | API_PUBLIC_BASE 填错 | curl {API_PUBLIC_BASE}/api/health 从外网自测 |
| Key 泄露风险 | Key 写进了前端 | `grep -rn "DIFY_KEY" frontend/` 必须无输出 |
