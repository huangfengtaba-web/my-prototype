# -*- coding: utf-8 -*-
"""五种产物渲染器（T3-3）。

签名统一：build_xxx(summary: dict, out_dir: str, filename: str) -> str（返回文件绝对路径）。
- docx / pdf / xlsx 走 cli_anything.wps.core export（进程内 import，WPS COM）
- pptx 走 pptengine（Deck + el.*，禁用 CLI impress）
- template 走 KWPS COM Find/Replace 占位符（占位符约定见 docs/07_DOCGEN.md）
"""
import json
import os
import sys
from typing import Any, Dict

from cli_anything.wps.core.export import export

# pptengine 不是 pip 包，位于交付物 harness-anything 内（仅本地 Windows）
_PPT_ENGINE = os.getenv(
    "PPT_ENGINE_PATH",
    r"D:\工作\嘉定GTX\GTX_FSO_交付物\tools\harness-anything\WPS\ppt-engine",
)
_TEMPLATE = os.getenv("DOCGEN_TEMPLATE", "")


def _out_path(out_dir, filename, ext):
    os.makedirs(out_dir, exist_ok=True)
    return os.path.abspath(os.path.join(out_dir, f"{filename}{ext}"))


def _mk_project(summary: Dict[str, Any]) -> Dict[str, Any]:
    """run_summary -> cli_anything writer 项目 JSON（content items）。"""
    sched = summary.get("schedule") or []
    milp = summary.get("milp_status") or {}
    story = summary.get("story_check") or {}
    content = [
        {"type": "heading", "text": "GTX FSO Litho 排程报告", "level": 1},
        {"type": "paragraph",
         "text": f"运行批次 {summary.get('run', {}).get('batch', '-')} · "
                 f"模型 {summary.get('run', {}).get('model', '-')} "
                 f"{summary.get('run', {}).get('version', '-')} · 日期 {summary.get('date', '-')}"
                 f"（run_id 见文件名）"},
        {"type": "heading", "text": "一、MILP 求解状态", "level": 2},
        {"type": "paragraph",
         "text": f"② Reticle 预组批：{milp.get('step2', '-')}；"
                 f"③ Lot 细排程：{milp.get('step3', '-')}。"},
        {"type": "heading", "text": "二、急货故事线自检", "level": 2},
        {"type": "paragraph",
         "text": "；".join(f"{k}：{v}" for k, v in story.items()) or "-"},
        {"type": "heading", "text": "三、Scanner Schedule（Lot 细排程结果）", "level": 2},
    ]
    if sched:
        head = ["LotId", "Eqp", "Reticle", "优先级", "Start", "End"]
        rows = [[r.get("lot", ""), r.get("eqp", "-"), r.get("reticle", ""),
                 r.get("priority", ""), r.get("start", "-"), r.get("end", "-")]
                for r in sched]
        content.append({"type": "table", "rows": len(rows) + 1, "cols": 6,
                        "data": [head] + rows})
    else:
        content.append({"type": "paragraph", "text": "（本 Loop 无排程结果）"})
    content += [
        {"type": "heading", "text": "四、光罩五态（就绪时间）", "level": 2},
        {"type": "paragraph",
         "text": "；".join(f"{rid} 就绪 {m.get('ready') or '-'}"
                          for rid, m in (summary.get("reticles") or {}).items()) or "-"},
    ]
    return {"content": content}


def _export(project, path, preset):
    result = export(project, path, preset=preset, overwrite=True)
    return result["output"]


def build_report_docx(summary, out_dir, filename):
    """排程报告 .docx（WPS Writer COM）。"""
    return _export(_mk_project(summary), _out_path(out_dir, filename, ".docx"), "docx")


def build_report_pdf(summary, out_dir, filename):
    """排程报告 .pdf：先经 harness 出 docx，再用 KWPS COM 转 PDF。

    不走 export(preset='pdf')：harness 里 `app.Visible = False` 在 KWPS 动态派发下
    会抛 AttributeError（WPS 不允许对该属性赋值）。
    """
    docx = build_report_docx(summary, out_dir, filename)
    import win32com.client

    pdf = _out_path(out_dir, filename, ".pdf")
    app = win32com.client.Dispatch("KWPS.Application")
    try:
        app.Visible = False
    except AttributeError:
        pass                        # WPS 动态派发不允许设置 Visible，忽略
    doc = app.Documents.Open(docx)
    try:
        try:
            doc.ExportAsFixedFormat(pdf, 17)       # 17 = wdExportFormatPDF
        except Exception:
            doc.SaveAs(pdf, FileFormat=17)         # 降级：SaveAs PDF
    finally:
        doc.Close(SaveChanges=False)
        app.Quit()
    return pdf


def build_detail_xlsx(summary, out_dir, filename):
    """排程明细 .xlsx：Lot / Eqp / Reticle 三个 sheet（KET COM 直填）。

    不走 harness export(preset='xlsx')：其 save_as 调 SaveAs2，KET 动态派发无此属性。
    """
    sched = [r for r in (summary.get("schedule") or [])]

    def sheet_rows(name, head, rows):
        cells = {}
        for ci, h in enumerate(head):
            cells[f"{chr(65 + ci)}1"] = {"value": h, "type": "string"}
        for ri, row in enumerate(rows, start=2):
            for ci, v in enumerate(row):
                cells[f"{chr(65 + ci)}{ri}"] = {"value": str(v), "type": "string"}
        return {"name": name, "cells": cells}

    sheets = [
        sheet_rows("Lot", ["LotId", "Eqp", "EqpGroup", "Reticle", "Priority", "Temp", "Start", "End"],
                   [[r.get("lot"), r.get("eqp"), r.get("eqp_group"), r.get("reticle"),
                     r.get("priority"), r.get("temp"), r.get("start"), r.get("end")] for r in sched]),
        sheet_rows("Eqp", ["Eqp", "Lot 数", "总加工(min)"],
                   _eqp_rows(sched)),
        sheet_rows("Reticle", ["ReticleId", "状态", "就绪", "备注"],
                   [[rid, m.get("status"), m.get("ready"), m.get("note")]
                    for rid, m in (summary.get("reticles") or {}).items()]),
    ]

    import win32com.client

    app = win32com.client.Dispatch("KET.Application")
    try:
        app.Visible = False
    except AttributeError:
        pass
    wb = app.Workbooks.Add()
    try:
        for i, sh in enumerate(sheets):
            ws = wb.Worksheets.Item(i + 1) if i + 1 <= wb.Worksheets.Count else wb.Worksheets.Add()
            ws.Name = sh["name"][:31]
            for ref, cell in sh["cells"].items():
                try:
                    ws.Range(ref).Value = float(cell["value"])
                except (TypeError, ValueError):
                    ws.Range(ref).Value = str(cell["value"])
        path = _out_path(out_dir, filename, ".xlsx")
        try:
            wb.SaveAs(path, FileFormat=51)          # 51 = xlOpenXMLWorkbook (.xlsx)
        except Exception:
            wb.SaveAs2(path, FileFormat=51)
        return path
    finally:
        wb.Close(SaveChanges=False)
        app.Quit()


def _eqp_rows(sched):
    agg: Dict[str, Dict[str, Any]] = {}
    for r in sched:
        e = r.get("eqp")
        if not e:
            continue
        a = agg.setdefault(e, {"n": 0, "min": 0})
        a["n"] += 1
        s = _hm(r.get("start"))
        t = _hm(r.get("end"))
        if s is not None and t is not None:
            a["min"] += t - s
    return [[e, a["n"], a["min"]] for e, a in sorted(agg.items())]


def _hm(hhmm):
    try:
        h, m = str(hhmm).split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return None


def build_deck_pptx(summary, out_dir, filename):
    """排程汇报 .pptx（pptengine Deck + el.*，WPS 演示 COM）。"""
    if os.path.isdir(_PPT_ENGINE) and _PPT_ENGINE not in sys.path:
        sys.path.insert(0, _PPT_ENGINE)
    from pptengine import Deck, el                      # noqa: E402
    from pptengine.assets import ensure_default_assets  # noqa: E402

    sched = summary.get("schedule") or []
    milp = summary.get("milp_status") or {}
    story = summary.get("story_check") or {}
    run = summary.get("run") or {}

    assets = ensure_default_assets(None)
    # visible 必须为 True：KWPP 动态派发不允许 Visible=False（com_error），
    # 且 connect_wps 的 kill_first 竞态在已杀进程后立即重连会失败——pptengine 默认路径可容忍窗口闪现。
    deck = Deck(assets_dir=str(assets),
                bg=str(assets / "bg_page.png"), visible=True)

    s = deck.add_slide()
    el.header(s, "01", "GTX FSO Litho 排程汇报")
    el.rich(s, 16, 70, 928, 30,
            [(f"{run.get('model', '-')} {run.get('version', '-')} · {run.get('batch', '-')} · "
              f"{summary.get('date', '-')}", el.INK, False)], fs=15)
    el.gray_box(s, 16, 110, 928, 84, [
        [(f"MILP ②预组批 {milp.get('step2', '-')} / ③细排程 {milp.get('step3', '-')}", el.INK, True)],
        [(f"急货 LOT-A01 上机 {story.get('LOT-A01 上机时间', '-')} · "
          f"RT-0101 就绪 {story.get('RT-0101 就绪时间', '-')}", el.INK, False)],
        [(story.get("准备链", ""), el.INK, False)],
    ])

    s = deck.add_slide()
    el.header(s, "02", "Scanner Schedule（Lot 细排程）")
    rows = sched[:9]
    y = 70
    for r in rows:
        el.rich(s, 24, y, 912, 24,
                [(f"{r.get('lot')}  {r.get('eqp') or '-'}  {r.get('reticle')}  "
                  f"{r.get('priority')}  {r.get('start')}~{r.get('end')}", el.INK, False)], fs=13)
        y += 26
    if not rows:
        el.txt(s, 24, y, 912, 24, "（本 Loop 无排程结果）", fs=13)

    s = deck.add_slide()
    el.header(s, "03", "结论与下一步")
    el.gray_box(s, 16, 90, 928, 110, [
        [("急货故事线闭环：IRIS 20min + 搬送 10min + 装载 5min = 35min 就绪链路成立", el.INK, False)],
        [("光罩就绪已耦合进细排程约束（外部 IRIS / StarLight 到期 / 跨机搬送）", el.INK, False)],
        [("执行态仿真（故障/返工/光罩接力）验证计划稳健性，详见仿真验证页", el.INK, False)],
    ])

    path = _out_path(out_dir, filename, ".pptx")
    deck.save(path, pdf=False)
    deck.close()
    return path


def build_from_template(summary, out_dir, filename):
    """套模板正式文档：KWPS COM 打开模板 → Find/Replace 占位符 → SaveAs。

    占位符约定见 docs/07_DOCGEN.md：
    {{RUN_ID}} {{BATCH}} {{DATE}} {{MODEL}} {{TABLE_STEP2}} {{TABLE_STEP3}} {{SUMMARY_TEXT}}
    """
    import win32com.client

    if not _TEMPLATE or not os.path.exists(_TEMPLATE):
        raise RuntimeError(f"模板不存在：DOCGEN_TEMPLATE={_TEMPLATE or '（未配置）'}")

    sched = summary.get("schedule") or []
    milp = summary.get("milp_status") or {}

    def fmt_table(rows):
        lines = ["\t".join(map(str, r)) for r in rows]
        return "\n".join(lines) or "-"

    mapping = {
        "{{RUN_ID}}": os.path.splitext(filename)[0],
        "{{BATCH}}": (summary.get("run") or {}).get("batch", "-"),
        "{{DATE}}": summary.get("date", "-"),
        "{{MODEL}}": f"{(summary.get('run') or {}).get('model', '-')} "
                     f"{(summary.get('run') or {}).get('version', '-')}",
        "{{TABLE_STEP2}}": fmt_table([["阶段", "状态"], ["Reticle 预组批", milp.get("step2", "-")],
                                      ["Lot 细排程", milp.get("step3", "-")]]),
        "{{TABLE_STEP3}}": fmt_table([[r.get("lot"), r.get("eqp"), r.get("start"), r.get("end")]
                                      for r in sched] or [["-", "-", "-", "-"]]),
        "{{SUMMARY_TEXT}}": "；".join(f"{k}：{v}"
                                     for k, v in (summary.get("story_check") or {}).items()) or "-",
    }

    app = win32com.client.Dispatch("KWPS.Application")
    app.Visible = False
    doc = app.Documents.Open(os.path.abspath(_TEMPLATE))
    try:
        for k, v in mapping.items():
            find = doc.Content.Find
            find.Execute(FindText=k, ReplaceWith=str(v), Replace=2)  # 2 = wdReplaceAll
        path = _out_path(out_dir, filename, ".docx")
        doc.SaveAs(path, FileFormat=16)  # 16 = wdFormatDocumentDefault (docx)
        return path
    finally:
        doc.Close(SaveChanges=False)
        app.Quit()
