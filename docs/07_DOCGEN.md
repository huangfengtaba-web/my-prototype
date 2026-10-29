# 07 · WPS 文档生成（docgen）

> 实现代码：`backend/app/docgen/`（worker / renderers / api）。仅本地 Windows 可用；
> 云端部署必须设 `DOCGEN_ENABLED=0`（接口返回 503，前端 reports 页显示降级提示）。

## 1. 架构与硬约束

```
POST /api/doc/render ──► wps_worker（单线程队列，pythoncom.CoInitialize）
                            │  进程内 import cli_anything.wps.core.export
                            │  60s 超时 → taskkill wps.exe 重试 1 次
                            ▼  仍失败 → headless 降级（docx→python-docx / pptx→python-pptx）
                         output/doc/<filename>.{docx,pdf,xlsx,pptx}
GET /api/doc/status/{job_id}   轮询（pending/running 内部态/done/failed）
GET /api/doc/file/{job_id}     下载（FileResponse）
```

- **禁 subprocess 逐条调 CLI**：每条起一次 COM 会卡死；渲染器全部进程内 import。
- WPS COM 三个 ProgID：`KWPS.Application`（文字）/ `KET.Application`（表格）/ `KWPP.Application`（演示）。
- 已踩坑记录（renderers.py 内有注释）：
  - KWPS/KET/KWPP 动态派发**不允许设 `Visible=False`**（AttributeError/com_error）——
    pptengine 必须 `visible=True`；PDF 转换自开 COM 并 try/except Visible。
  - harness 的 `save_as` 用 `SaveAs2`，KET 无此属性 → xlsx 渲染器自实现（`SaveAs FileFormat=51`）。
  - **文件名必须合法**：中文经 GBK 控制台传参会变 `????`，WPS 弹不可见错误对话框表现为挂起
    （超时 60s ×2 后走降级）。浏览器 fetch 发 UTF-8 无此问题；命令行测试请用 UTF-8 客户端。
- pptengine 不是 pip 包：`PPT_ENGINE_PATH` 指向交付物
  `tools/harness-anything/WPS/ppt-engine/`，renderers 动态 sys.path。

## 2. 五种产物

| kind | 渲染器 | 产出 | 引擎 |
|---|---|---|---|
| `docx` | `build_report_docx` | 排程报告 | cli_anything.wps writer（heading/paragraph/table content items） |
| `pdf` | `build_report_pdf` | 排程报告 PDF | 先出 docx → KWPS `ExportAsFixedFormat`（降级 SaveAs 17） |
| `xlsx` | `build_detail_xlsx` | 三 sheet 明细 | KET COM 直填（Lot / Eqp / Reticle） |
| `pptx` | `build_deck_pptx` | 汇报幻灯片 | **pptengine**（Deck + el.*，禁用 CLI impress） |
| `template` | `build_from_template` | 套模板正式文档 | KWPS `Content.Find.Execute` 替换占位符 → SaveAs |

数据源：`backend/solver/output/run_summary.json`（最近一次求解）。

## 3. 套模板占位符约定（模板里写这些，生成时整词替换）

```
{{RUN_ID}}        ← 渲染时传入的 filename（去扩展名）
{{BATCH}}         ← run.batch，如 RUN-20261024-01
{{DATE}}          ← summary.date
{{MODEL}}         ← 模型名 + 版本
{{TABLE_STEP2}}   ← 整表替换（文本对齐表：阶段/状态）
{{TABLE_STEP3}}   ← 整表替换（Lot 排程明细）
{{SUMMARY_TEXT}}  ← 急货故事线自检一句话汇总
```

配置模板：`.env` 设 `DOCGEN_TEMPLATE=D:/path/模板.docx`，再 `POST /api/doc/render {"kind":"template", ...}`。

## 4. 快速验证

```bash
# 直跑渲染器（四种产物，全 >0 字节）
.venv/Scripts/python.exe -c "import json;from backend.app.docgen import renderers; \
  s=json.load(open('backend/solver/output/run_summary.json',encoding='utf-8')); \
  print(renderers.build_report_docx(s,'output/doc','verify'))"

# 走接口（UTF-8 客户端！Git Bash 控制台直接 curl -d 中文会变 ????）
python -c "import json,urllib.request; \
  req=urllib.request.Request('http://127.0.0.1:8000/api/doc/render', \
  data=json.dumps({'kind':'docx','filename':'排程报告'}).encode(), \
  headers={'Content-Type':'application/json'},method='POST'); \
  print(urllib.request.urlopen(req).read())"
```

前端入口：`/reports` 页（三按钮 + 轮询 + 下载链接 + DOCGEN_ENABLED=0 降级提示）。
