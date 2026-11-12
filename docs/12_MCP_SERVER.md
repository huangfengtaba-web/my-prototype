# MCP Server · 接入指南

> 把 GTX FSO Litho 的排程能力暴露为**标准 MCP 工具**，任何 MCP 客户端（Claude Desktop / Cursor / Cline / Inspector）都能直接调用。

---

## 1. 它解决什么问题

改造前：能力只能在自家网页（`/ai-agent`）里用。
改造后：在 **Claude Desktop 里说一句「帮我跑一下急货场景」**，就能驱动你的排程系统跑 MILP 并返回结果。

```
Claude Desktop / Cursor
        ↓  MCP (JSON-RPC over stdio)
backend/mcp_server
        ↓  调用
backend/app/registry  ← 与 /api/capabilities 同源
        ↓
six-step MILP / DES 仿真 / 工作流
```

---

## 2. 安装

```bash
cd D:\codex\2026-10-28-23-35-39
.venv/Scripts/python.exe -m pip install -r backend/requirements-mcp.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> `mcp` **不进主 `requirements.txt`** —— Render 免费层只有 512MB，MCP 进程常驻约 70~100MB，只在本地/内网跑。

## 3. 验证

```bash
# 自检（不起服务，不联网）
.venv/Scripts/python.exe -m backend.mcp_server --selftest

# 期望输出
# [selftest] server=gtx-fso-litho  mcp_tools=7
# [selftest] list_cases -> 10 个用例: apc-block, bullet-wait, ...
# [selftest] PASS
```

---

## 4. 接入 Claude Desktop

配置文件：`%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gtx-fso-litho": {
      "command": "D:\\codex\\2026-10-28-23-35-39\\.venv\\Scripts\\python.exe",
      "args": ["-m", "backend.mcp_server", "--transport", "stdio"],
      "cwd": "D:\\codex\\2026-10-28-23-35-39",
      "env": { "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1" }
    }
  }
}
```

改完**完全退出 Claude Desktop** 再重开（托盘也要退），然后在输入框右下角能看到工具图标。

## 5. 接入 Cursor

复制仓库根的 `mcp.json.example` 到 `.cursor/mcp.json`（内容相同），重启 Cursor。

---

## 6. 工具清单（7 个）

| 工具 | 必填参数 | 说明 | risk |
|---|---|---|---|
| `list_cases` | — | 列出全部 scenario 用例 | read |
| `get_mock_data` | — | 机台 / Lot / 光罩概览 | read |
| `run_solve` | — | 六步 MILP 求解（可选 `case` / `fix`） | compute |
| `get_result` | `run_id` | 查历史求解详情 | read |
| `run_sim` | — | 求解 + 执行态仿真（`case` / `seed` / `breakdown`） | compute |
| `run_workflow` | — | 跑完整工作流（`template_id` / `case`） | compute |
| `list_workflows` | — | 工作流模板与最近运行 | read |

**schema 与 `/api/capabilities` 逐字段同源**（`tests/test_mcp_schema.py` 断言），不存在两套描述。

---

## 7. 在 Claude 里的用法示例

```
你：跑一下急货场景，看看 LOT-A01 什么时候能上机
Claude：（调用 run_solve {"case": "urgent-A01"}）
        → 求解完成，run_id a1b2c3d4，MILP Optimal/Optimal，LOT-A01 10:00 上机 IMM04

你：带设备故障仿真一遍，种子 7
Claude：（调用 run_sim {"case": "urgent-A01", "seed": 7, "breakdown": true}）
        → 准时率 94%，实际 MakeSpan 13:05（计划 12:35，偏差 30min），故障 2 次
```

---

## 8. HTTP 传输（可选）

```bash
.venv/Scripts/python.exe -m backend.mcp_server --transport http --port 8765
curl -X POST http://127.0.0.1:8765/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

> 若 `streamable_http_manager` 与新版本 SDK 不兼容，`--transport http` 会明确报错退出，**不影响 stdio 主路径**。

---

## 9. 两个必须知道的实现细节

### ① stdout 保护
MCP stdio 把 **stdout 当 JSON-RPC 通道**。项目中 `store.py`、`solver_runner.py` 都有 `print()`，一旦写到 stdout 会让客户端解析失败、直接断连。

`__main__.py` 在**任何 backend 导入之前**执行：

```python
builtins.print = _safe_print          # 全部转到 stderr
contextlib.redirect_stdout(sys.stderr)
```

所以看到 MCP 日志在 stderr 是正常的。

### ② 为什么不用 FastMCP 装饰器

`@mcp.tool` 靠函数签名推断 JSON Schema，而我们的 handler 是 `Callable[..., dict]`（由注册表统一持有），签名推断会得到空 schema。

因此用官方**低层 `Server` API**，把注册表里的 `input_schema` 原样交给协议层 —— 这是确定性路径。

---

## 10. 加新工具的步骤

1. 在 `backend/app/registry/skills/` 下新建或修改技能文件，`register(Skill(...))`
2. 跑 `.venv/Scripts/python.exe -m pytest tests/test_registry.py tests/test_mcp_schema.py -q`
3. 重启 MCP 客户端 —— **无需改 MCP 代码**，工具自动出现

三端（MCP / OpenAI function calling / 前端能力面板）自动同步。
