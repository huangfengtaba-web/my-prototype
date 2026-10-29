# -*- coding: utf-8 -*-
"""文档生成接口（T3-4）：POST /api/doc/render → 轮询 status → 下载 file。"""
import json
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import renderers, wps_worker

router = APIRouter(prefix="/api/doc", tags=["docgen"])

_MAP = {"docx": renderers.build_report_docx, "pdf": renderers.build_report_pdf,
        "xlsx": renderers.build_detail_xlsx, "pptx": renderers.build_deck_pptx,
        "template": renderers.build_from_template}


class RenderRequest(BaseModel):
    kind: str = "docx"
    filename: str = "排程报告"
    run_id: str | None = None


def _out_dir() -> str:
    d = os.getenv("DOCGEN_OUT_DIR", "./output/doc")
    os.makedirs(d, exist_ok=True)
    return d


def _summary(run_id: str | None) -> dict:
    p = os.path.join("backend", "solver", "output", "run_summary.json")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


@router.post("/render")
def render(req: RenderRequest):
    if req.kind not in _MAP:
        raise HTTPException(400, detail=f"kind 只允许 {list(_MAP)}")
    if os.getenv("DOCGEN_ENABLED", "1") != "1":
        raise HTTPException(503, detail="DOCGEN_ENABLED=0，当前环境不生成文档")
    fn = _MAP[req.kind]
    args = (_summary(req.run_id), _out_dir(), req.filename)
    jid = wps_worker.submit(lambda: fn(*args), kind=req.kind, args=args)
    return {"job_id": jid, "status": "pending"}


@router.get("/status/{job_id}")
def job_status(job_id: str):
    st = wps_worker.status(job_id)
    if not st:
        raise HTTPException(404, detail="job 不存在")
    return st


@router.get("/file/{job_id}")
def job_file(job_id: str):
    st = wps_worker.status(job_id)
    if not st or st["status"] != "done":
        raise HTTPException(404, detail="文件未就绪")
    if not os.path.exists(st["path"]):
        raise HTTPException(404, detail="产出文件丢失")
    return FileResponse(st["path"], filename=os.path.basename(st["path"]))
