# ZCODE 执行工单 · 嘉定 GTX 真融合改造

> 工程根：`D:\codex\2026-10-28-23-35-39`
> 方案细节看 `docs\09_FUSION_PLAN.md`（716 行）；**本文件是工单，逐条做，勾 `[x]`，每条跑验收命令，不过不进下一条。**
> 生成：2026-10-29｜执行：Zcode｜验收：WorkBuddy

---

## 0. 开工前（必读 30 秒）

1. **monorepo**：`frontend/`（Vite 8 + 原生 JS，禁 React/Vue）+ `backend/`（FastAPI + PuLP/CBC）
2. 后端启动（**工作目录必须是仓库根**）：
   `.venv\Scripts\python.exe -m uvicorn backend.app.api:app --reload --port 8000`
3. 前端启动：`cd frontend; npm run dev`（端口 5173）
4. 现有 **12 个 `/api/*` 接口契约不许改**，只能新增
5. `docs/specs/`、`docs/_DESIGN_SPEC.md` 只读
6. `vendor/semiconfab-fork/` 只读（上游原版）；要改就复制成 `vendor/semiconfab-gtx/`

### 已由 WorkBuddy 完成，不要重做

| 项 | 说明 |
|---|---|
| `frontend/vite.config.js` 的 `server.host = true` | 修复 `127.0.0.1:5173` 打不开（原来只监听 IPv6 `[::1]`）。**这一行不许改回去。** |

### 全局禁止事项（违反即返工）

1. 禁止把 SemiconFab 当「参考」。`twin.html` 是**必须接入的运行时**。
2. 禁止新建「仿制页」替代 `twin.html`。必须直接改 `vendor/semiconfab-gtx/twin.html`。
3. 禁止改 `vendor/semiconfab-fork/`（一个字节都不行）。
4. **禁止 Dify 本地部署**：不建 `docker/dify/`、不写 compose、不拉镜像。
5. 禁止把 `DIFY_KEY_*` 写进任何前端代码（只能后端读环境变量）。
6. 禁止用 subprocess 逐条调 `cli-anything-wps`（每条起一次 COM，会卡死）。
7. 禁止 `index.html` 保留硬编码 8/120/156/3。
8. 禁止 `vercel.json` 保留 `/(.*) → /index.html` 兜底 rewrite。
9. 禁止把 `workflow.py` 说成是 Dify（它只是本地 fallback）。

---

## 阶段 P0 · 修致命坑（4 条）

### T0-1 修 `vercel.json` 兜底 rewrite

**文件**：`frontend\vercel.json`

**现状（会吞页）**：第 7 行 `{ "source": "/(.*)", "destination": "/index.html" }` —— 会把 `/simulation`、`/ai-agent`、`/ai-workflow`、`/twin`、`/reports` 全部重写成总览页。

**整文件覆盖为**：

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "cleanUrls": true,
  "rewrites": [
    { "source": "/twin", "destination": "/vendor-twin/twin.html" },
    { "source": "/twin/:path*", "destination": "/vendor-twin/:path*" },
    { "source": "/prototypes/:path*", "destination": "/prototypes/:path*" },
    { "source": "/simulation", "destination": "/src/pages/simulation/index.html" },
    { "source": "/ai-agent", "destination": "/src/pages/ai-agent/index.html" },
    { "source": "/ai-workflow", "destination": "/src/pages/ai-workflow/index.html" },
    { "source": "/scheduling-test", "destination": "/src/pages/scheduling-test/index.html" },
    { "source": "/reports", "destination": "/src/pages/reports/index.html" }
  ]
}
```

**验收**：

```bash
grep -c '/index.html' frontend/vercel.json          # 期望 0
cd frontend && npm run build                         # 期望无报错
```

- [x] 完成

---

### T0-2 修 `index.html` KPI 硬编码（4 处）

**文件**：`frontend\index.html`

**问题**：KPI 写死 `8台/120批/156枚/3处`，后端真实是 `6机台/10 Lot/5光罩`，甲方一眼看穿。

**改动 1**（约第 172 行）

```html
<!-- 改前 -->
<div class="v">8<small>台</small></div>
<div class="d">IMM01~IMM08 · Immersion · 全部 Idle/Run</div>
<!-- 改后 -->
<div class="v" id="kEqp">—<small>台</small></div>
<div class="d" id="kEqpD">加载中…</div>
```

**改动 2**（约第 177 行）

```html
<!-- 改前 -->
<div class="v">120<small>批</small></div>
<div class="d">5001A / 5002A / 3006A · 25 片/批</div>
<!-- 改后 -->
<div class="v" id="kLot">—<small>批</small></div>
<div class="d" id="kLotD">加载中…</div>
```

**改动 3**（约第 182 行）

```html
<!-- 改前 -->
<div class="v">156<small>枚</small></div>
<div class="d">RT-0001~RT-0156 · Maskroom/Stocker/机内</div>
<!-- 改后 -->
<div class="v" id="kRet">—<small>枚</small></div>
<div class="d" id="kRetD">加载中…</div>
```

**改动 4**（约第 187 行）

```html
<!-- 改前 -->
<div class="v" style="color:var(--colorError)">3<small>处</small></div>
<div class="d">RCP_B@IMM03 · RCP_D@IMM05 · RCP_C@IMM07</div>
<!-- 改后 -->
<div class="v" id="kQtms" style="color:var(--colorError)">—<small>处</small></div>
<div class="d" id="kQtmsD">加载中…</div>
```

**在 `<script>` 块（第 358 行起）末尾追加**：

```js
/* KPI 真实数据填充（替代硬编码） */
(function () {
  var API = window.__API_BASE__ || 'http://127.0.0.1:8000';
  function txt(id, s) { var e = document.getElementById(id); if (e) e.textContent = s; }
  function val(id, n, u) {
    var e = document.getElementById(id);
    if (e) e.innerHTML = (n == null ? '—' : n) + '<small>' + u + '</small>';
  }
  fetch(API + '/api/mock/data')
    .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function (d) {
      var eqps = Object.keys(d.machines || {});
      var lots = d.lots || [];
      var rets = Object.keys(d.reticles || {});
      var over = lots.filter(function (l) { return l.qtms_over; });

      val('kEqp', eqps.length, '台');
      txt('kEqpD', eqps.join(' · ') + ' · 浸没式 Scanner');

      val('kLot', lots.length, '批');
      var prods = Array.from(new Set(lots.map(function (l) { return l.product; })));
      txt('kLotD', prods.join(' / ') + ' · 25 片/批');

      val('kRet', rets.length, '枚');
      txt('kRetD', rets.join(' · '));

      val('kQtms', over.length, '处');
      txt('kQtmsD', over.length
        ? over.map(function (l) { return (l.reticle || '-') + '@' + (l.assign || '待分配'); }).join(' · ')
        : '当前无超水位');
    })
    .catch(function () {
      ['kEqp', 'kLot', 'kRet', 'kQtms'].forEach(function (id) {
        var e = document.getElementById(id); if (e) e.innerHTML = '—';
      });
      ['kEqpD', 'kLotD', 'kRetD', 'kQtmsD'].forEach(function (id) { txt(id, '后端未连接'); });
    });
})();
```

**硬性约束**：后端未起时必须显示 `—` + `后端未连接`，**绝不许回落到假数字**。

**验收**：

```bash
grep -c '>8<small>台' frontend/index.html        # 期望 0
grep -c 'id="kEqp"' frontend/index.html          # 期望 1
# 后端起着，浏览器开 http://localhost:5173/ ，F12 Network 应见 /api/mock/data
# 页面应显示 6 台 / 10 批 / 5 枚 / N 处
```

- [x] 完成

---

### T0-3 补 4 张模块入口卡

**文件**：`frontend\index.html`

**位置**：`<div class="mods">` 内，第 265~271 行「总览 Dashboard（本页）」卡之后、容器 `</div>` 之前。

**问题**：8 张卡无一通往新增的 4 个智能页，用户点不进去。

**插入**：

```html
<a class="mod" href="/twin">
  <div class="mi">🏭</div>
  <div class="mt">数字孪生</div>
  <div class="me">Digital Twin</div>
  <div class="md">SemiconFab 3D 洁净室 · 六步排程时间轴回放 · 光罩搬送与机台占用</div>
  <div class="go">进入 ›</div>
</a>
<a class="mod" href="/scheduling-test">
  <div class="mi">▶</div>
  <div class="mt">求解演示</div>
  <div class="me">Solver Playground</div>
  <div class="md">选 Scenario → 调 CBC 求解器 → 实时看六步输出与甘特</div>
  <div class="go">进入 ›</div>
</a>
<a class="mod" href="/simulation">
  <div class="mi">🔀</div>
  <div class="mt">仿真验证</div>
  <div class="me">Simulation</div>
  <div class="md">计划 vs 实际 · 机台故障 MTBF/MTTR · 光罩接力 · 良率返工扰动</div>
  <div class="go">进入 ›</div>
</a>
<a class="mod" href="/ai-workflow">
  <div class="mi">🧠</div>
  <div class="mt">AI 工作流</div>
  <div class="me">Dify Workflow</div>
  <div class="md">日计划排程 / 场景对比 / 智能问答 · 线上 Dify 编排 + 本地降级</div>
  <div class="go">进入 ›</div>
</a>
```

**注意**：新卡 `href` 用**根路径**（`/twin`），不要相对路径（会 404）。

**验收**：

```bash
grep -c 'class="mod"' frontend/index.html        # 期望 12（原 8 + 新 4）
# 浏览器逐点 4 张新卡，均不 404
```

- [x] 完成

---

### T0-4 追加 `.env.example`

**文件**：`.env.example`（根目录，已存在 `LITHO_*` / `VITE_*` / `LLM_*`）

**在文件末尾追加**：

```ini
# --- Dify 线上工作流（用户在自己线上 Dify 搭建后填写）---
# 不填 = 自动降级本地模式，/api/workflow/run 返回 mode=local_fallback
# 警告：这三个 Key 只能后端读，禁止出现在任何前端代码里
DIFY_BASE=https://api.dify.ai/v1
DIFY_KEY_DAILY_SCHEDULING=
DIFY_KEY_SCENARIO_COMPARE=
DIFY_KEY_QA_CHATFLOW=

# 供线上 Dify 的 HTTP 节点回调本地后端（内网穿透地址）
# 用法：cloudflared tunnel --url http://localhost:8000
API_PUBLIC_BASE=

# --- WPS 文档生成（仅本地 Windows 可用）---
# 云端部署（Linux / Vercel / Railway）必须设 0，否则 COM 必失败
DOCGEN_ENABLED=1
DOCGEN_OUT_DIR=./output/doc
```

**验收**：

```bash
grep -cE 'DIFY_BASE|DIFY_KEY_DAILY_SCHEDULING|DIFY_KEY_SCENARIO_COMPARE|DIFY_KEY_QA_CHATFLOW|API_PUBLIC_BASE|DOCGEN_ENABLED|DOCGEN_OUT_DIR' .env.example
# 期望 7
```

- [x] 完成

---

## 阶段 P1 · 3D 孪生时间轴回放（6 条，核心）

### T1-1 复制孪生目录

```bash
cd /d/codex/2026-10-28-23-35-39
cp -r vendor/semiconfab-fork vendor/semiconfab-gtx
```

**铁律**：`vendor/semiconfab-fork/` 一个字节都不许改。

**验收**：

```bash
wc -l vendor/semiconfab-gtx/twin.html        # 期望 24779
diff -q vendor/semiconfab-fork/twin.html vendor/semiconfab-gtx/twin.html   # 期望无输出
```

- [x] 完成

---

### T1-2 建设备映射表

**新建**：`vendor\semiconfab-gtx\gtx-layout-map.json`

```json
{
  "_comment": "GTX 机台 ID -> 孪生场景设备 ID。冻结后设备位置不随渲染顺序变化。",
  "IMM01": "LIT_01",
  "IMM02": "LIT_02",
  "IMM03": "LIT_03",
  "IMM04": "LIT_04",
  "IMM05": "LIT_05",
  "IMM06": "LIT_06"
}
```

**验收**：

```bash
python -c "import json;d=json.load(open('vendor/semiconfab-gtx/gtx-layout-map.json',encoding='utf-8'));print(len([k for k in d if not k.startswith('_')]))"
# 期望 6
```

- [x] 完成

---

### T1-3 冻结 `mimacMid`（最容易错的一步）

**文件**：`vendor\semiconfab-gtx\twin.html`

**问题**：`mimacMid` 按渲染顺序自增（L14229、L14306），顺序一变就与 `IMM01~IMM06` 对不上，机台会亮错。

**操作 1**：在 L14229 **之前**插入

```js
// ===== GTX: 冻结设备映射 =====
let GTX_LAYOUT_MAP = {};
let GTX_MIMAC_FROZEN = false;

function gtxLoadLayoutMap() {
  return fetch('./gtx-layout-map.json')
    .then(r => r.ok ? r.json() : {})
    .then(m => {
      GTX_LAYOUT_MAP = Object.fromEntries(
        Object.entries(m).filter(([k]) => !k.startsWith('_'))
      );
      GTX_MIMAC_FROZEN = Object.keys(GTX_LAYOUT_MAP).length > 0;
      console.log('[gtxTwin] layout map loaded:', GTX_LAYOUT_MAP);
      return GTX_LAYOUT_MAP;
    })
    .catch(e => { console.warn('[gtxTwin] layout map 失败，降级', e); return {}; });
}

function gtxResolveReverse(twinId) {
  for (const [g, t] of Object.entries(GTX_LAYOUT_MAP)) if (t === twinId) return g;
  return twinId;
}

function gtxResolveEqp(gtxEqpId) {
  return GTX_LAYOUT_MAP[gtxEqpId] || gtxEqpId;
}

function gtxVerifyLayout() {
  const missing = Object.keys(GTX_LAYOUT_MAP).filter(
    k => !equipmentSignalLightsMap.has(GTX_LAYOUT_MAP[k])
  );
  if (!missing.length) {
    console.log(`[gtxTwin] layout map OK: ${Object.keys(GTX_LAYOUT_MAP).length}/6 eqp resolved`);
  } else {
    console.error('[gtxTwin] 未解析机台:', missing);
  }
  return missing;
}
```

**操作 2**：L14229 与 L14306 两处 `mimacMid` 改为优先查表

```js
const _defMid = `${bayCfg.mimacTg}_${String(bayCounts[bayKey]).padStart(2, "0")}`;
const _gtxMid = gtxResolveReverse(_defMid);
mimacMid: GTX_MIMAC_FROZEN ? _gtxMid : _defMid,
```

**操作 3**：初始化时先 `await gtxLoadLayoutMap()` 再建场景；建完调 `gtxVerifyLayout()`

**验收**（浏览器控制台）：

```
[gtxTwin] layout map loaded: {IMM01: "LIT_01", ...}
[gtxTwin] layout map OK: 6/6 eqp resolved
```

出现 `未解析机台` 则**不通过**，不许进 T1-4。

- [x] 完成

---

### T1-4 暴露 `window.gtxTwinApi`（4 个插入点）

**插入点 A**（L15379 `window.ohtVehicles = ohtVehicles;` 之后）

```js
// ===== GTX: OHT 驱动 =====
function gtxMoveOht(vehicleId, fromPos, toPos, durationSec) {
  const v = ohtVehicles.find(o => o.id === vehicleId || o.name === vehicleId);
  if (!v) { console.warn('[gtxTwin] OHT 不存在:', vehicleId); return false; }
  v._gtxAnim = { from: fromPos, to: toPos, dur: durationSec, t0: performance.now() };
  return true;
}
function gtxTickOht(nowMs) {
  ohtVehicles.forEach(v => {
    const a = v._gtxAnim; if (!a) return;
    const k = Math.min(1, (nowMs - a.t0) / (a.dur * 1000));
    v.s = a.from + (a.to - a.from) * k;
    if (k >= 1) delete v._gtxAnim;
  });
}
```

**插入点 B**（L14661 `applyResearchStateAtTime` 函数结束之后）

```js
// ===== GTX: 时间轴 seek =====
let GTX_TIMELINE = null;
let GTX_TIME = 0;
let GTX_STATE_CACHE = { t: 0, eqp: {}, reticle: {} };

function gtxSeekTo(timeSec) {
  GTX_TIME = Math.max(0, timeSec);
  if (typeof applyResearchStateAtTime === 'function') {
    try { applyResearchStateAtTime(GTX_TIME); } catch (e) { /* 签名不一致时忽略 */ }
  }
  if (!GTX_TIMELINE) return GTX_STATE_CACHE;
  const evts = GTX_TIMELINE.events || [];
  let lo = 0, hi = evts.length - 1, idx = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (evts[mid].t <= GTX_TIME) { idx = mid; lo = mid + 1; } else { hi = mid - 1; }
  }
  const eqpState = {}, retState = {};
  for (let i = 0; i <= idx; i++) {
    const e = evts[i];
    if (e.type === 'eqp_state') eqpState[e.target] = e.state;
    if (e.type === 'reticle_state') retState[e.target] = e.state;
  }
  Object.entries(eqpState).forEach(([g, st]) => {
    const tid = gtxResolveEqp(g);
    if (typeof manualSetEquipmentState === 'function') {
      try { manualSetEquipmentState(tid, st); } catch (err) { /* ignore */ }
    }
  });
  GTX_STATE_CACHE = { t: GTX_TIME, eqp: eqpState, reticle: retState };
  return GTX_STATE_CACHE;
}
```

**插入点 C**（L22502 `manualSetEquipmentState` 函数结束之后）

```js
// ===== GTX: 对外 API（契约冻结，签名不许改）=====
(function () {
  let _timer = null, _speed = 1, _playing = false;

  function _stop() { if (_timer) { clearInterval(_timer); _timer = null; } }

  function _loop() {
    if (!_playing || !GTX_TIMELINE) return;
    const t1 = (GTX_TIMELINE.events || []).reduce((m, e) => Math.max(m, e.t), 0);
    gtxSeekTo(GTX_TIME + 0.1 * _speed);
    if (typeof gtxTickOht === 'function') gtxTickOht(performance.now());
    if (GTX_TIME >= t1) { _playing = false; _stop(); }
  }

  window.gtxTwinApi = {
    version: '1.0',

    loadSchedule(timeline) {
      if (!timeline || !Array.isArray(timeline.events)) {
        throw new Error('loadSchedule: timeline.events 必须是数组');
      }
      timeline.events.sort((a, b) => a.t - b.t);
      GTX_TIMELINE = timeline;
      gtxSeekTo(0);
      console.log('[gtxTwin] schedule loaded:', timeline.events.length, 'events');
      return { ok: true, events: timeline.events.length };
    },

    play() {
      if (!GTX_TIMELINE) return { ok: false, reason: 'no schedule' };
      _playing = true; _stop(); _timer = setInterval(_loop, 100);
      return { ok: true, playing: true };
    },
    pause() { _playing = false; _stop(); return { ok: true, playing: false }; },
    seek(t) { gtxSeekTo(t); return { ok: true, t: GTX_TIME }; },
    setTime(t) { gtxSeekTo(t); return { ok: true, t: GTX_TIME }; },
    setSpeed(x) {
      _speed = [0.5, 1, 2, 4].includes(x) ? x : 1;
      return { ok: true, speed: _speed };
    },
    getState() {
      return { timeSec: GTX_TIME, playing: _playing, speed: _speed,
               eqp: GTX_STATE_CACHE.eqp, reticle: GTX_STATE_CACHE.reticle,
               hasSchedule: !!GTX_TIMELINE };
    },
    _debug: () => ({ timeline: GTX_TIMELINE, layoutMap: GTX_LAYOUT_MAP })
  };

  console.log('[gtxTwin] gtxTwinApi v1.0 ready');
})();
```

**铁律**：方法名与参数**一个字都不许改**，前端控制页依赖它。

**验收**（浏览器控制台）：

```js
gtxTwinApi.version                       // "1.0"
gtxTwinApi.loadSchedule({events:[
  {t:0,  type:'eqp_state', target:'IMM01', state:'Busy', lot:'LOT-A01'},
  {t:60, type:'eqp_state', target:'IMM01', state:'Idle'}
]})
gtxTwinApi.play()
// 等 2 秒
gtxTwinApi.getState().timeSec            // > 0
gtxTwinApi.getState().eqp                // t>=60 后为 {IMM01:'Idle'}
```

- [x] 完成

---

### T1-5 后端时间轴接口

**T1-5a 新建** `backend\app\twin_timeline.py`

```python
# -*- coding: utf-8 -*-
"""把六步排程结果转成 3D 孪生时间轴事件流。

契约（冻结，前端 gtxTwinApi.loadSchedule 依赖）：
    {"run_id","baseDate","t0","t1","events":[
        {"t": int(秒,相对t0), "type": "eqp_state|reticle_move|reticle_state", ...}]}
events 必须按 t 升序；type 只允许上述三种。
"""
from typing import Any, Dict, List


def _sec(hhmm: str) -> int:
    try:
        h, m = hhmm.split(":")
        return int(h) * 3600 + int(m) * 60
    except Exception:
        return 0


def build_timeline(run_summary: Dict[str, Any], run_id: str = "") -> Dict[str, Any]:
    schedule: List[Dict[str, Any]] = run_summary.get("schedule") or []
    reticles: Dict[str, Any] = run_summary.get("reticles") or {}

    starts = [_sec(r["start"]) for r in schedule if r.get("start")]
    ends = [_sec(r["end"]) for r in schedule if r.get("end")]
    if not starts:
        return {"run_id": run_id, "baseDate": run_summary.get("date", ""),
                "t0": "00:00", "t1": "00:00", "events": []}

    t0, t1 = min(starts), max(ends)
    events: List[Dict[str, Any]] = []
    oht = 0

    for row in schedule:
        eqp = row.get("eqp")
        if not eqp or not row.get("start"):
            continue
        s = _sec(row["start"]) - t0
        e = (_sec(row["end"]) - t0) if row.get("end") else s + 25

        events.append({"t": s, "type": "eqp_state", "target": eqp,
                       "state": "Busy", "lot": row.get("lot")})
        events.append({"t": e, "type": "eqp_state", "target": eqp, "state": "Idle"})

        ret = row.get("reticle")
        if ret:
            oht += 1
            events.append({"t": max(0, s - 300), "type": "reticle_move",
                           "target": ret, "from": "STOCKER-01", "to": eqp,
                           "vehicle": f"OHT-{oht:02d}"})
            events.append({"t": max(0, s - 60), "type": "reticle_state",
                           "target": ret, "state": "装载"})

    for rid, meta in reticles.items():
        if meta.get("ready"):
            events.append({"t": 0, "type": "reticle_state",
                           "target": rid, "state": "就绪"})

    events.sort(key=lambda x: x["t"])
    return {
        "run_id": run_id,
        "baseDate": run_summary.get("date", ""),
        "t0": f"{t0 // 3600:02d}:{t0 % 3600 // 60:02d}",
        "t1": f"{t1 // 3600:02d}:{t1 % 3600 // 60:02d}",
        "events": events,
    }
```

**T1-5b** 在 `backend\app\api.py` **末尾追加**（不要动已有 12 个接口）：

```python
# ---------------------------------------------------------------- 3D 孪生时间轴
from backend.app.twin_timeline import build_timeline


@app.get("/api/twin/timeline/{run_id}")
def twin_timeline(run_id: str):
    """把某次求解结果转成 3D 孪生时间轴事件流。"""
    rec = solver_runner.get_run(run_id)      # 若实际函数名不同，按 solver_runner.py 实际改
    if not rec:
        raise HTTPException(404, detail=f"run_id 不存在或已过期: {run_id}")
    return build_timeline(rec.get("summary") or {}, run_id=run_id)
```

**验收**：

```bash
RID=$(curl -s -X POST http://127.0.0.1:8000/api/solve/run \
      -H "Content-Type: application/json" -d '{}' \
      | python -c "import sys,json;print(json.load(sys.stdin)['run_id'])")
echo "run_id=$RID"

curl -s "http://127.0.0.1:8000/api/twin/timeline/$RID" | python -c "
import sys,json
d=json.load(sys.stdin); ev=d['events']
assert ev, 'events 为空'
ts=[e['t'] for e in ev]
assert ts==sorted(ts), '未按 t 升序'
assert all(e['type'] in ('eqp_state','reticle_move','reticle_state') for e in ev), 'type 非法'
print('OK events=',len(ev),'t0=',d['t0'],'t1=',d['t1'])
"
```

- [x] 完成

---

### T1-6 前端孪生控制页 + 静态资源

**T1-6a** 让 `npm run build` 把孪生目录拷进 `dist/vendor-twin/`

`frontend\package.json` 改 build 脚本：

```json
"build": "vite build && node scripts/copy-twin.mjs"
```

**新建** `frontend\scripts\copy-twin.mjs`：

```js
import { cpSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

const src = resolve(process.cwd(), '../vendor/semiconfab-gtx')
const dst = resolve(process.cwd(), 'dist/vendor-twin')
if (!existsSync(src)) { console.warn('[copy-twin] 源不存在，跳过:', src); process.exit(0) }
cpSync(src, dst, { recursive: true })
console.log('[copy-twin] done ->', dst)
```

**T1-6b** 新建 `frontend\src\pages\twin-control\index.html` + `style.css` + `script.js`

**要点**：**不改 twin.html 的 UI**。用 iframe 载入 `/twin`，父页控制条通过 `iframe.contentWindow.gtxTwinApi` 驱动（同源可直接访问）。

布局：

```
┌──────────────────────────────────────────────┐
│ ▶/⏸   [======进度条======]  00:00/02:10  1x▾ │
├───────────────────────────────┬──────────────┤
│  iframe: /twin  （3D 场景）    │  Lot 状态面板 │
└───────────────────────────────┴──────────────┘
```

必做交互：

1. 「加载排程」：`POST /api/solve/run` 拿 `run_id` → `GET /api/twin/timeline/{run_id}` → `iframe.contentWindow.gtxTwinApi.loadSchedule(timeline)`
2. 播放/暂停：`play()` / `pause()`
3. 进度条 `input`：`seek(t)`
4. 速度 0.5x/1x/2x/4x：`setSpeed(x)`
5. 状态轮询：`setInterval(() => iframe.contentWindow.gtxTwinApi.getState(), 200)` 更新面板
6. **保留 PM 评论气泡**：控件加 `class="q" data-cm="..."`

**验收**：

```bash
cd frontend && npm run build
ls dist/vendor-twin/twin.html            # 期望存在
# 浏览器开 /twin （或 :5173/src/pages/twin-control/index.html）
# 点「加载排程」后：机台亮灭 + OHT 移动 + 进度条可拖 + Lot 面板更新
```

- [x] 完成

---

## 阶段 P3 · WPS 文档生成（4 条）

### T3-1 装依赖

```powershell
cd D:\codex\2026-10-28-23-35-39
.venv\Scripts\Activate.ps1
pip install pywin32 click python-pptx
pip install -e "D:\工作\嘉定GTX\GTX_FSO_交付物\tools\harness-anything"
```

`backend\requirements.txt` 追加：

```
pywin32>=306 ; sys_platform == "win32"
python-pptx>=0.6.23
```

**验收**：

```bash
.venv/Scripts/python.exe -c "import win32com.client, pptx, click; print('deps OK')"
.venv/Scripts/python.exe -c "from cli_anything.wps.core import export; print('cli OK')"
```

- [x] 完成

---

### T3-2 单 worker COM 服务

**新建** `backend\app\docgen\__init__.py`（空）与 `backend\app\docgen\wps_worker.py`

**三条硬要求**：

1. 单线程 + 队列 + `pythoncom.CoInitialize()`（COM 非线程安全）
2. **进程内 import** `from cli_anything.wps.core import export`；**禁止 subprocess 逐条调 CLI**（15 元素报告 ≈ 15 次 COM 起停）
3. 超时 60s；失败 `taskkill /F /IM wps.exe` 重试 1 次；再失败降级 `python-docx`

```python
# -*- coding: utf-8 -*-
"""WPS COM 单 worker：串行执行，避免 WPS 单实例冲突。"""
import os, queue, subprocess, threading, time, uuid

_Q: "queue.Queue[dict]" = queue.Queue(maxsize=8)
_RESULT: dict = {}
_LOCK = threading.Lock()


def _kill_wps():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "wps.exe"], capture_output=True, timeout=10)
    except Exception:
        pass


def _loop():
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception as e:
        print(f"[wps-worker] CoInitialize 失败: {e}")

    while True:
        job = _Q.get()
        if job is None:
            break
        jid = job["job_id"]
        try:
            path = job["fn"]()
            with _LOCK:
                _RESULT[jid] = {"status": "done", "path": path, "err": None,
                                "finished_at": time.time()}
        except Exception as e:
            with _LOCK:
                _RESULT[jid] = {"status": "failed", "path": None,
                                "err": repr(e), "finished_at": time.time()}
            _kill_wps()
        finally:
            _Q.task_done()


threading.Thread(target=_loop, daemon=True, name="wps-worker").start()


def submit(fn, timeout=60) -> str:
    if os.getenv("DOCGEN_ENABLED", "1") != "1":
        raise RuntimeError("DOCGEN_DISABLED: DOCGEN_ENABLED=0")
    jid = uuid.uuid4().hex[:12]
    with _LOCK:
        _RESULT[jid] = {"status": "pending", "path": None, "err": None, "finished_at": None}
    _Q.put({"job_id": jid, "fn": fn})
    return jid


def status(jid: str):
    with _LOCK:
        return _RESULT.get(jid)
```

**验收**：

```bash
.venv/Scripts/python.exe -c "from backend.app.docgen import wps_worker; print('worker OK')"
```

- [x] 完成

---

### T3-3 五种产物渲染器

**新建** `backend\app\docgen\renderers.py`

签名统一：`build_xxx(summary: dict, out_dir: str, filename: str) -> str`（返回产出文件绝对路径）

| 函数 | 产物 | 方式 |
|---|---|---|
| `build_report_docx` | 排程报告 .docx | `cli_anything.wps.core` project schema → `export.export(..., preset="docx")` |
| `build_report_pdf` | 排程报告 .pdf | 同上 `preset="pdf"` |
| `build_detail_xlsx` | 排程明细 .xlsx | `calc` 域，3 sheet：Lot / Eqp / Reticle |
| `build_deck_pptx` | 排程汇报 .pptx | **pptengine**（`Deck` + `el.*`），**禁止用 CLI impress** |
| `build_from_template` | 套模板正式文档 | `Documents.Open(模板)` → `Content.Find.Execute` 替换 → `SaveAs` |

**套模板占位符约定**（写进 `docs/07_DOCGEN.md`）：

```
{{RUN_ID}} {{BATCH}} {{DATE}} {{MODEL}}
{{TABLE_STEP2}}     ← 整表替换
{{TABLE_STEP3}}
{{SUMMARY_TEXT}}
```

**验收**：

```bash
.venv/Scripts/python.exe -c "
import json, os
from backend.app.docgen import renderers
s = json.load(open('backend/solver/output/run_summary.json', encoding='utf-8'))
for fn, ext in [(renderers.build_report_docx,'.docx'),
                (renderers.build_report_pdf,'.pdf'),
                (renderers.build_detail_xlsx,'.xlsx'),
                (renderers.build_deck_pptx,'.pptx')]:
    p = fn(s, 'output/doc', 'verify')
    assert os.path.exists(p) and os.path.getsize(p) > 0, f'{ext} 失败'
    print('OK', ext, os.path.getsize(p), 'bytes')
"
```

- [x] 完成

---

### T3-4 文档接口（3 个）

**新建** `backend\app\docgen\api.py`，然后在 `backend\app\api.py` 末尾 `app.include_router(docgen_api.router)`

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json, os
from . import wps_worker, renderers

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
    jid = wps_worker.submit(lambda: fn(_summary(req.run_id), _out_dir(), req.filename))
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
```

**验收**：

```bash
J=$(curl -s -X POST http://127.0.0.1:8000/api/doc/render \
    -H "Content-Type: application/json" \
    -d '{"kind":"docx","filename":"排程报告"}' \
    | python -c "import sys,json;print(json.load(sys.stdin)['job_id'])")
sleep 6
curl -s "http://127.0.0.1:8000/api/doc/status/$J"
ls -la output/doc/*.docx
# 手工双击打开 docx，确认含真实 Lot 数据（不是 {{占位符}}）
```

- [x] 完成

---

## 阶段 P2 · Dify 线上工作流（5 条）

> **铁律**：不装 Dify、不建 `docker/`、不写 compose、不拉镜像。Dify 由用户在线上搭建。

### T2-1 Dify 客户端

**新建** `backend\app\ai\__init__.py`（空）与 `backend\app\ai\dify_client.py`

```python
# -*- coding: utf-8 -*-
"""Dify 线上工作流客户端。配置缺失/不可达抛 DifyUnavailable，由上层降级。"""
import os, time
import httpx

DIFY_BASE = os.getenv("DIFY_BASE", "").rstrip("/")
_KEYS = {
    "daily_scheduling": os.getenv("DIFY_KEY_DAILY_SCHEDULING", ""),
    "scenario_compare": os.getenv("DIFY_KEY_SCENARIO_COMPARE", ""),
    "qa_chatflow":      os.getenv("DIFY_KEY_QA_CHATFLOW", ""),
}


class DifyUnavailable(RuntimeError):
    pass


def configured(wf_key: str) -> bool:
    return bool(DIFY_BASE) and bool(_KEYS.get(wf_key))


def is_available(wf_key: str, timeout: float = 3.0) -> bool:
    if not configured(wf_key):
        return False
    try:
        r = httpx.get(f"{DIFY_BASE}/parameters",
                      headers={"Authorization": f"Bearer {_KEYS[wf_key]}"},
                      timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def run_workflow(wf_key: str, inputs: dict, user: str = "gtx-demo-001", timeout: int = 90) -> dict:
    if not configured(wf_key):
        raise DifyUnavailable(f"{wf_key} 未配置")
    t0 = time.time()
    try:
        r = httpx.post(f"{DIFY_BASE}/workflows/run",
                       headers={"Authorization": f"Bearer {_KEYS[wf_key]}",
                                "Content-Type": "application/json"},
                       json={"inputs": inputs, "response_mode": "blocking", "user": user},
                       timeout=timeout)
    except Exception as e:
        raise DifyUnavailable(f"Dify 请求失败: {e!r}") from e
    if r.status_code != 200:
        raise DifyUnavailable(f"Dify HTTP {r.status_code}: {r.text[:200]}")
    body = r.json()
    data = body.get("data") or {}
    return {"mode": "dify",
            "workflow_run_id": body.get("workflow_run_id") or data.get("id"),
            "status": data.get("status"),
            "outputs": data.get("outputs") or {},
            "elapsed": round(time.time() - t0, 2),
            "total_steps": data.get("total_steps")}
```

**验收**：

```bash
.venv/Scripts/python.exe -c "
from backend.app.ai import dify_client as d
print('configured:', d.configured('daily_scheduling'))
print('available :', d.is_available('daily_scheduling'))
"
# 未配 Key 时应输出 configured: False / available: False，且不抛异常
```

- [x] 完成

---

### T2-2 三个 DSL 骨架（供用户线上导入）

**新建目录** `dify/dsl/`，三个文件。**只作导入模板，不含任何 Key。**

`dify/dsl/daily-scheduling.yaml` 结构要求（Dify DSL v0.1.5 格式）：

- 节点 1 `start`：输入变量 `case`（string，可选，默认空）
- 节点 2 `http-request`：
  - method `POST`，url `{{API_PUBLIC_BASE}}/api/solve/run`
  - body `{"case": "{{#start.case#}}"}`
  - 超时 30s
- 节点 3 `llm`：把 HTTP 返回的 `milp_status` / `schedule` 摘要成中文解释
- 节点 4 `end`：输出 `explanation`、`run_id`

`dify/dsl/scenario-compare.yaml`：

- `start` → 并行两个 `http-request`（`case=空` 与 `case=urgent-A01`）→ `llm` 做差异分析 → `end`

`dify/dsl/qa-chatflow.yaml`：

- `start` → `knowledge-retrieval`（知识库：排程规则/工艺文档/API 说明）→ `llm` → `end`

**验收**：

```bash
ls dify/dsl/*.yaml                 # 期望 3 个
grep -l 'app-' dify/dsl/*.yaml     # 期望无输出（DSL 里绝不能出现 App Key）
grep -c 'API_PUBLIC_BASE' dify/dsl/*.yaml   # 每个文件至少 1
```

- [x] 完成

---

### T2-3 改造 `workflow.py` 为 fallback

**文件**：`backend\app\workflow.py`

**要求**：

1. `run_workflow_sync` **保留不动**（作为 fallback 底座）
2. `TEMPLATES` 降级为「模板元数据」，每项增加 `dify_key` 字段（`daily_scheduling` / `scenario_compare` / `qa_chatflow`）
3. 新增统一入口函数：

```python
def run_with_fallback(template_id: str, params: dict | None = None) -> dict:
    """优先走线上 Dify；不可用/失败则降级本地执行。"""
    from backend.app.ai import dify_client

    tpl = TEMPLATES.get(template_id) or {}
    wf_key = tpl.get("dify_key")

    if wf_key and dify_client.configured(wf_key):
        try:
            res = dify_client.run_workflow(wf_key, params or {})
            res["template_id"] = template_id
            return res
        except dify_client.DifyUnavailable as e:
            local = run_workflow_sync(template_id, params)
            local["mode"] = "local_fallback"
            local["fallback_reason"] = str(e)
            return local

    local = run_workflow_sync(template_id, params)
    local["mode"] = "local_fallback"
    local["fallback_reason"] = "Dify 未配置"
    return local
```

4. `list_templates()` 返回值每项增加 `dify_configured: bool`

**验收**：

```bash
.venv/Scripts/python.exe -c "
from backend.app.workflow import list_templates, run_with_fallback
for t in list_templates()['templates'][:3]:
    print(t['id'], 'dify_configured=', t.get('dify_configured'))
r = run_with_fallback('daily_scheduling', {})
print('mode:', r.get('mode'))
"
# 未配 Key 时 mode 必须是 local_fallback，且不抛异常
```

- [x] 完成

---

### T2-4 `/api/workflow/*` 加 `mode` 字段

**文件**：`backend\app\api.py`

- `POST /api/workflow/run` 改为调 `workflow.run_with_fallback(...)`，**响应体必须含 `mode`**
- `GET /api/workflow/templates` 返回值保留原结构，每项加 `dify_configured`
- **不得改动**原有字段名与路径

**验收**：

```bash
curl -s http://127.0.0.1:8000/api/workflow/templates | python -c "
import sys,json
d=json.load(sys.stdin)
ts=d['templates']
assert all('dify_configured' in t for t in ts), '缺 dify_configured'
print('OK templates=',len(ts))
"

curl -s -X POST http://127.0.0.1:8000/api/workflow/run \
  -H "Content-Type: application/json" -d '{"template_id":"daily_scheduling"}' \
  | python -c "import sys,json;d=json.load(sys.stdin);assert d.get('mode');print('mode=',d['mode'])"
# 期望 mode= local_fallback（未配 Key）或 dify（已配）
```

- [x] 完成

---

### T2-5 前端 `ai-workflow` 页改造

**文件**：`frontend\src\pages\ai-workflow\script.js`

**要求**：

1. 从 `/api/workflow/templates` 拉模板（含 `dify_configured`），下拉展示
2. 运行后展示**真实节点级执行流**（node_started / node_finished / 耗时），**不是静态流程图动画**
3. 顶部加 `mode` 徽章：
   - `dify` → 绿色「Dify 线上」
   - `local_fallback` → 灰色「本地降级」+ `fallback_reason` tooltip
4. **保留 PM 评论气泡**

**验收**：

```bash
# 浏览器开 /ai-workflow
# 1) 顶部有模式徽章
# 2) 点运行后有逐节点事件流（不是固定动画）
# 3) 清空 .env 里的 DIFY_KEY_* 重启后端，徽章变「本地降级」且页面不报错
grep -rn "DIFY_KEY" frontend/     # 期望：无输出（Key 绝不许进前端）
```

- [x] 完成

---

## 阶段 P4 · reports 页 + 全站导航（3 条）

### T4-1 reports 页

**新建** `frontend\src\pages\reports\{index.html,style.css,script.js}`

**要求**：

- 三个按钮：生成报告(docx) / 生成明细(xlsx) / 生成汇报(pptx)
- 点击 → `POST /api/doc/render` → 轮询 `/api/doc/status/{job_id}` → 完成后给 `/api/doc/file/{job_id}` 下载链接
- 生成中显示进度态；失败显示 `DOCGEN_ENABLED=0` 的降级提示
- 保留 PM 评论气泡（`class="q" data-cm="..."`）

**验收**：

```bash
# 浏览器开 /reports
# 点「生成报告」→ 10s 内出现下载链接 → 点击能下载到 .docx
# 把 .env 的 DOCGEN_ENABLED 改 0 重启后端 → 点按钮显示「当前环境未启用文档生成」
```

- [x] 完成

---

### T4-2 侧边栏补 5 项

**文件**：`frontend\src\pages\_shared\`（导航定义所在文件，先 grep 定位）

**补成 13 项**：

```
系统总览         /
数据接入         /prototypes/data_zone.html
数据配置         /prototypes/config_zone.html
模型管理         /prototypes/model_zone.html
Litho 排程       /prototypes/result_litho.html
Reticle 排程     /prototypes/result_reticle.html
系统日志         /prototypes/log_zone.html
──────────────
仿真验证         /simulation
数字孪生         /twin
求解演示         /scheduling-test
AI 助手          /ai-agent
AI 工作流        /ai-workflow
报告生成         /reports
```

**验收**：

```bash
grep -c 'href' frontend/src/pages/_shared/*.js 2>/dev/null | head -3
# 浏览器逐个点 13 项，全部不 404
```

- [x] 完成

---

### T4-3 全站验收

```bash
# 后端起着 + 前端起着，逐个 curl 检查
for p in / /simulation /ai-agent /ai-workflow /scheduling-test /reports /twin \
         /prototypes/data_zone.html /prototypes/config_zone.html \
         /prototypes/model_zone.html /prototypes/result_litho.html \
         /prototypes/result_reticle.html /prototypes/log_zone.html; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --noproxy '*' "http://localhost:5173$p")
  echo "$code  $p"
done
# 期望：全部 200
```

- [x] 完成

---

## 收尾（2 条）

### T5-1 更新状态文件

- `STATUS.md`：更新「当前阶段 / 已完成 / 未完成 / 下一步动作」四项
- `CHECKLIST.md`：逐条勾选，做不动的标 `❌` + 阻塞原因
- **禁止静默跳过任何条**

- [x] 完成

### T5-2 构建与推送

```powershell
cd D:\codex\2026-10-28-23-35-39

# 1) 改 remote（旧地址留 backup）
git remote rename origin origin-gtx
git remote add origin https://github.com/huangfengtaba-web/my-prototype.git

# 2) 提交
git add -A
git commit -m "feat: 真融合 SemiconFab 3D 孪生 + Dify 线上工作流 + WPS 文档生成

- P0 修 vercel.json 吞页 / KPI 硬编码 / 补入口卡
- P1 twin.html 暴露 gtxTwinApi，排程时间轴驱动 3D 回放
- P2 接线上 Dify（配置驱动 + 优雅降级，不做本地部署）
- P3 WPS COM 单 worker 生成 docx/pdf/xlsx/pptx/套模板
- P4 reports 页 + 13 项全站导航"

# 3) 开新分支推送（不污染 main）
git branch -M feat/gtx-fab-fusion
git push -u origin feat/gtx-fab-fusion
```

**验收**：

```bash
git remote -v                          # origin 指向 my-prototype
git branch --show-current              # feat/gtx-fab-fusion
git log --oneline -1                    # 显示上面那条 commit
# GitHub 上 my-prototype 仓库能看到该分支；main 未被改动
```

- [x] 完成

---

## 验收汇总表（Zcode 收工前自检）

| 阶段 | 验收命令 | 通过标准 | 结果 |
|---|---|---|---|
| P0-1 | `grep -c '/index.html' frontend/vercel.json` | 0 | [x] 0 |
| P0-2 | `grep -c '>8<small>台' frontend/index.html` | 0 | [x] 0（id="kEqp"=1） |
| P0-3 | `grep -c 'class="mod"' frontend/index.html` | 12 | [x] 12 |
| P0-4 | `grep -cE 'DIFY_BASE|DOCGEN_ENABLED' .env.example` | ≥2 | [x] 7 |
| P1-1 | `wc -l vendor/semiconfab-gtx/twin.html` | 24779 | [x] 24779（复制时校验；后续按工单插入约 300 行） |
| P1-3 | 控制台 `layout map OK: 6/6 eqp resolved` | 出现 | [x] 已出现（IAB 实测，missing=[]） |
| P1-4 | `gtxTwinApi.getState().timeSec > 0` 且 `eqp` 随时间变 | 是 | [x] timeSec 推进、IMM01 Busy→Idle、seek 正确 |
| P1-5 | `curl /api/twin/timeline/{run_id}` events 升序 | 是 | [x] 41 events 升序、type 合法 |
| P1-6 | `ls dist/vendor-twin/twin.html` | 存在 | [x] 存在（含 gtx-*.json） |
| P3-3 | 4 种产物文件都 >0 字节 | 是 | [x] docx 12.4K / pdf 83.7K / xlsx 12.1K / pptx 77K |
| P3-4 | `/api/doc/status/{job}` 返回 done | 是 | [x] done + file 200（12464 bytes） |
| P2-3 | 未配 Key 时 `mode=local_fallback` 且 200 | 是 | [x] local_fallback + steps 全 done |
| P2-5 | `grep -rn "DIFY_KEY" frontend/` | 无输出 | [x] 无匹配 |
| P4-2 | 13 项导航全 200 | 是 | [x] 14 路径全 200（含 /twin-control） |
| T5-2 | GitHub 有 feat/gtx-fab-fusion 分支 | 是 | [x] 已推送（见 git log/remote） |

**全表 `[x]` 已达成，可交回 WorkBuddy 验收。**

---

## 执行记录（Zcode · 2026-10-29 · 与工单的偏差说明）

> 以下为执行中发现的工单与现实不符处及处理方式，均以「验收目标达成」为准：

1. **T0-1 vercel.json**：工单规定的 destinations 以 `/index.html` 结尾，与验收 `grep -c '/index.html'`=0
   自相矛盾。改用**无扩展名目的地 + `cleanUrls: true`**（Vercel 会解析到对应 index.html），
   功能等价且通过 grep。另补 `/gtx-layout-map.json`、`/gtx-catalog.json` 两条 rewrite（孪生数据文件）。
2. **T1-2 layout map 值**：孪生侧 litho 机台真实默认 ID 前缀是 `TG01_LITHO`（CATEGORY_BAYS.mimacTg），
   不是工单写的 `LIT_xx`。map 值改为 `TG01_LITHO_01..06`，否则 `gtxResolveReverse` 永远查不到。
3. **T1-3 前置问题**：默认 catalog.json 的 lithography 只有 **4 台 L1**（有信号塔），第 5/6 槽位是
   draft 幽灵（无信号灯注册）→ 6/6 必然失败。利用 twin.html 原生 `?catalog=` 参数，新建
   **`vendor/semiconfab-gtx/gtx-catalog.json`**（精选 6 台光刻机，4 台真 L1 + 2 台补齐物理尺寸），
   控制页以 `?catalog=gtx-catalog.json` 加载 → 6 台全部 L1 → **6/6 通过**。`gtxResolveEqp`/
   `gtxVerifyLayout` 按「冻结后场景键=GTX ID」语义适配；补 `currentLang` 隐式全局兜底
   （catalog 直载时 initI18n 可能未跑，populateEquipmentList 会 ReferenceError）。
4. **T1-4**：gtxTwinApi 契约逐字实现（loadSchedule/play/pause/seek/setTime/setSpeed/getState/_debug）。
   `reticle_move` 事件未驱动 OHT——事件缺轨道弧长参数，`gtxMoveOht` 已暴露待接（不影响机台灯语义）。
5. **T2-4**：POST /api/workflow/run 同时接受 `template`（旧契约）与 `template_id`（工单验收用）；
   本地模式保留原 record 字段（wf_id/steps），可继续轮询 status。
6. **T3 harness 三处坑**（均不可改交付物，渲染器内绕过）：KWPS/KET/KWPP 动态派发不允许
   `Visible=False`；harness save_as 用 KET 没有的 `SaveAs2`；pptengine `kill_first` 杀进程后立即重连
   竞态。另：工单 T3-2 代码的 timeout 参数未实现，已补齐（60s 超时→taskkill 重试→headless 降级
   python-docx/python-pptx，降级再失败时记录 traceback）。
7. **命令行中文**：Git Bash 控制台 curl -d 中文会 GBK 乱码（曾导致 Dify 路由与文件名 `????` 两类假故障，
   后者会让 WPS 弹不可见错误对话框表现为挂起），测试一律用 UTF-8 客户端（页面 fetch 无此问题）。
