/* ============================================================
   8. 渲染与事件
   ============================================================ */
const TABS = ["eqp", "lot"];

function render() {
  let s = '<div class="tabs">' +
    '<div class="tab ' + (UI.tab === "eqp" ? "on" : "") + '" data-tab="eqp">EQP Loading</div>' +
    '<div class="tab ' + (UI.tab === "lot" ? "on" : "") + '" data-tab="lot">Lot Stacking Bond</div>';
  if (UI.detailEqp) {
    s += '<div class="tab ' + (UI.tab === "detail" ? "on" : "") + '" data-tab="detail">' + UI.detailEqp + ' 负载明细<span class="x" data-act="closeDetail">×</span></div>';
  }
  /* v5：视图切换由右上方 tab 完成（仅 EQP Loading 页签显示，段带甘特已移除） */
  if (UI.tab === "eqp") {
    s += '<div style="margin-left:auto">' +
      viewTabs([["matrix", "日负载矩阵"], ["cmp", "负载对比"], ["load", "机台负载图"]], UI.view, "eqpview") +
      '</div>';
  }
  s += '</div>';
  $("#content").innerHTML = s +
    (UI.tab === "detail" && UI.detailEqp ? viewDetail(UI.detailEqp)
      : UI.tab === "lot" ? viewLot() : viewEQP());
  applyWin();
}

/* 窗口滚动定位 */
function applyWin() {
  const el = $("#scEqp") || $("#scLot") || $("#scDetail") || $("#scCmp");
  if (!el) return;
  /* V2.0：自定义起止天优先定位到起始天 */
  if (hasDayRange()) { el.scrollLeft = (dayLo() - 1) * CW; return; }
  if (UI.win === "all") { el.scrollLeft = 0; return; }
  el.scrollLeft = (parseInt(UI.win, 10) - 1) * 30 * CW;
}

document.addEventListener("click", function (ev) {
  const t = ev.target;

  /* v5：详情页 × 关闭需先于 data-tab 命中（× 位于详情 tab 内部） */
  const xd = t.closest('[data-act="closeDetail"]');
  if (xd) { UI.detailEqp = null; UI.tab = "eqp"; render(); return; }

  const tb = t.closest("[data-tab]");
  if (tb) { UI.tab = tb.getAttribute("data-tab"); render(); return; }

  /* v5：机台负载图点击 → 打开机台详情标签页 */
  const eq = t.closest("[data-eqp]");
  if (eq) { UI.detailEqp = eq.getAttribute("data-eqp"); UI.tab = "detail"; render(); return; }

  /* v5：EQP Loading 页签内视图切换 */
  const vb = t.closest("[data-eqpview]");
  if (vb) { UI.view = vb.getAttribute("data-eqpview"); render(); return; }

  const wb = t.closest("[data-win]");
  if (wb) { UI.win = wb.getAttribute("data-win"); UI.dayFrom = 1; UI.dayTo = 0; render(); return; }

  const vb2 = t.closest("[data-view]");
  if (vb2) { UI.view = vb2.getAttribute("data-view"); render(); return; }

  const ax = t.closest("[data-axis]");
  if (ax) { UI.lotAxis = ax.getAttribute("data-axis"); render(); return; }

  const st = t.closest("[data-sort]");
  if (st) {
    const k = st.getAttribute("data-sort");
    const set = st.getAttribute("data-sortset");
    const cur = set === "free" ? UI.freeSort : set === "lotseg" ? UI.lotSegSort : (UI.tab === "lot") ? UI.lotSort : UI.eqpSort;
    if (cur.k === k) cur.dir = -cur.dir; else { cur.k = k; cur.dir = 1; }
    render(); return;
  }

  const cs = t.closest("[data-csv]");
  if (cs) { exportCSV(cs.getAttribute("data-csv")); return; }

  const ac = t.closest("[data-act]");
  if (ac) {
    const a = ac.getAttribute("data-act");
    if (a === "regen") { readParams(); rebuild(); render(); }
    if (a === "reset") { CFG.ct = 2; CFG.days = 120; CFG.nLots = 16; CFG.seed = 20261015; CFG.incFree = false; rebuild(); render(); }
    if (a === "numMode") { UI.numMode = ac.getAttribute("data-m") === "global" ? "global" : "lot"; render(); }
    if (a === "cmpToggle") { UI.view = UI.view === "cmp" ? "matrix" : "cmp"; render(); }
    if (a === "closeDetail") { UI.tab = "eqp"; UI.detailEqp = null; render(); }
    if (a === "query") { recalcByFilter(); render(); }
    if (a === "resetFilter") { resetFilters(); recalcByFilter(); render(); }
    return;
  }
});
document.addEventListener("input", function (ev) {
  const el = ev.target, id = el.id;
  if (id === "qEqp") { UI.eqpQ = el.value; render(); keepFocus("qEqp"); return; }
  if (id === "qLot") { UI.lotQ = el.value; render(); keepFocus("qLot"); return; }
  if (id === "fG")   { UI.gFilter = el.value; render(); keepFocus("fG"); return; }
  if (id === "qFree") { UI.freeQ = el.value; render(); keepFocus("qFree"); return; }
  if (el.getAttribute("data-act") === "cmpZoom") {
    UI.cmpZoom = Math.max(1, Math.min(30, parseInt(el.value, 10) || 30));
    const c = $("#scCmp"); if (c) { c.innerHTML = drawCmpChart(); const lb = $("#cmpZoomLbl"); if (lb) lb.textContent = UI.cmpZoom; }
    return;
  }
  if (el.getAttribute("data-act") === "loadZoom") {
    UI.loadZoom = Math.max(1, Math.min(30, parseInt(el.value, 10) || 30));
    const c = $("#scLoadCht"); if (c) { c.innerHTML = drawLoadChart(); const lb = $("#loadZoomLbl"); if (lb) lb.textContent = UI.loadZoom; }
    return;
  }
  const ed = el.getAttribute("data-ed");
  if (ed) {
    const li = +el.getAttribute("data-li"), gi = +el.getAttribute("data-gi");
    const g = LOTS[li] && LOTS[li].groups[gi]; if (!g) return;
    if (ed === "lFrom" || ed === "lTo" || ed === "pics") g[ed] = Math.max(0, parseInt(el.value, 10) || 0);
    else g[ed] = el.value;
    if (g.lTo < g.lFrom) g.lTo = g.lFrom;
    rebuild(); render();
  }
});

document.addEventListener("change", function (ev) {
  const el = ev.target;
  /* V2.0：时间筛选（起止日期）—— 选完即生效 */
  if (el.id === "dayFrom" || el.id === "dayTo") {
    const d = dateToDay(el.value);
    if (el.id === "dayFrom") UI.dayFrom = d ? Math.max(1, Math.min(DAYS, d)) : 1;
    else UI.dayTo = d ? Math.max(1, Math.min(DAYS, d)) : 0;
    render(); return;
  }
  const pfKey = el.getAttribute && el.getAttribute("data-pf");
  if (pfKey) { UI.pFilter[pfKey] = el.value; recalcByFilter(); render(); return; }
  if (el.getAttribute && el.getAttribute("data-stf")) { UI.stFilter = el.value; recalcByFilter(); render(); return; }
  if (el.id === "fSt") { UI.stFilter = el.value; recalcByFilter(); render(); return; }
  if (el.id === "cFree") { CFG.incFree = !!el.checked; recalcByFilter(); render(); return; }
  const ed = el.getAttribute("data-ed");
  if (ed) {
    const li = +el.getAttribute("data-li"), gi = +el.getAttribute("data-gi");
    const g = LOTS[li] && LOTS[li].groups[gi]; if (!g) return;
    g[ed] = el.value; rebuild(); render();
  }
});

function keepFocus(id) {
  const el = $("#" + id);
  if (el) { el.focus(); try { el.setSelectionRange(el.value.length, el.value.length); } catch (e) {} }
}

/* tooltip */
document.addEventListener("mouseover", function (ev) {
  const el = ev.target.closest("[data-tip]");
  const tt = $("#tt");
  if (!el) { tt.style.display = "none"; return; }
  tt.innerHTML = el.getAttribute("data-tip");
  tt.style.display = "block";
  const r = el.getBoundingClientRect();
  let x = r.left, y = r.bottom + 8;
  if (x + 340 > window.innerWidth) x = Math.max(8, window.innerWidth - 348);
  if (y + 200 > window.innerHeight) y = Math.max(8, r.top - 200);
  tt.style.left = x + "px"; tt.style.top = y + "px";
});
document.addEventListener("mouseout", function () { const tt = $("#tt"); if (tt) tt.style.display = "none"; });

function readParams() {
  const g = function (id) { const e = $("#" + id); return e ? e.value : null; };
  const v = function (id, dft, lo, hi) {
    const x = parseInt(g(id), 10);
    return isNaN(x) ? dft : Math.max(lo, Math.min(hi, x));
  };
  CFG.ct = v("pCt", v("pCt2", CFG.ct, 1, 7), 1, 7);
  CFG.days = v("pDays", v("pDays2", CFG.days, 30, 240), 30, 240);
  CFG.nLots = v("pLots", v("pLots2", CFG.nLots, 4, 60), 4, 60);
  /* CT 变更同步到每个 Lot */
  LOTS.forEach(function (l) { l.ct = CFG.ct; });
}