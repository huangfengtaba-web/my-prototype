/* ============================================================
   9. boot
   ============================================================ */
/* v4：评论模式（?标记 + 气泡，仅在 body.cmt-on 时显示；委托绑定，重渲染后仍生效） */
function tip(t) { return '<span class="q" data-cm="' + esc(t) + '">?</span>'; }
document.addEventListener("click", function (ev) {
  const q = ev.target.closest(".q");
  if (!q) return;
  ev.stopImmediatePropagation();
  document.querySelectorAll(".bubble").forEach(function (b) { b.remove(); });
  const b = document.createElement("div");
  b.className = "bubble";
  b.innerHTML = '<div class="bt">字段说明</div><div class="bd">' + esc(q.getAttribute("data-cm")) + '</div>';
  document.body.appendChild(b);
  const r = q.getBoundingClientRect();
  b.style.left = Math.max(8, Math.min(window.innerWidth - 330, r.left)) + "px";
  b.style.top = Math.min(window.innerHeight - 170, r.bottom + 8) + "px";
  setTimeout(function () {
    const h = function () { b.remove(); document.removeEventListener("click", h); };
    document.addEventListener("click", h);
  }, 0);
}, true);
const cmtBtn = $("#cmtBtn");
if (cmtBtn) cmtBtn.onclick = function () {
  document.body.classList.toggle("cmt-on");
  cmtBtn.classList.toggle("pri", document.body.classList.contains("cmt-on"));
};

/* v5：顶栏时钟 */
(function clock() {
  const el = $("#clock"); if (!el) return;
  const d = new Date(), p = function (n) { return String(n).padStart(2, "0"); };
  el.textContent = d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) + " " + p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());
  setTimeout(clock, 1000);
})();

/* v5：数据配置弹窗（顶栏按钮触发，替代原第三个页签） */
function openCfg() {
  $("#modalRoot").innerHTML =
    '<div class="overlay"><div class="modal"><div class="modal-h"><div class="t">数据配置 · Group 定义（可编辑）</div>' +
    '<div class="x" data-act="closeCfg">✕</div></div>' +
    '<div class="modal-b">' + viewCfg() + '</div>' +
    '<div class="modal-f"><button class="btn" data-act="closeCfg">关闭</button></div></div></div>';
}
const cfgBtn = $("#cfgBtn");
if (cfgBtn) cfgBtn.onclick = openCfg;
document.addEventListener("click", function (ev) {
  const x = ev.target.closest('[data-act="closeCfg"]');
  if (x) { $("#modalRoot").innerHTML = ""; return; }
  if (ev.target.classList && ev.target.classList.contains("overlay")) { $("#modalRoot").innerHTML = ""; }
});

rebuild();
render();

/* 供无头测试用 */
if (typeof module !== "undefined" && module.exports) {
  module.exports = { CFG: CFG, UI: UI, LOTS: LOTS, DAYS: DAYS, LOAD: LOAD, SEGS: SEGS, MET: MET,
    EQPS: EQPS, ST: ST, segDays: segDays, stats: stats, viewEQP: viewEQP, viewLot: viewLot, viewCfg: viewCfg,
    exportCSV: exportCSV, TABS: TABS,
    maxGn: maxGn, gFilterSet: gFilterSet, freeList: freeList,
    eqpGroupMatrix: function () { return eqpGroupMatrix(EQPS); },
    lotGroupTable: function () { return lotGroupTable(LOTS); },
    freeLayerTable: freeLayerTable, freeCandBar: function () { return freeCandBar(freeList()); },
    lotSegTable: function () { return lotSegTable(LOTS); },
    ALLSEGS: function () { return ALLSEGS; }, CANDL: function () { return CANDL; },
    groupOwnerTable: groupOwnerTable, lotByGroup: function () { return lotByGroup(LOTS); },
    loadChartCard: loadChartCard, viewDetail: function (e) { return viewDetail(e); },
    recalcByFilter: recalcByFilter, viewTabs: viewTabs, fieldBar: fieldBar, winDays: winDays,
    resetFilters: resetFilters, dayLo: dayLo, dayHi: dayHi, hasDayRange: hasDayRange, dayRangeCtl: dayRangeCtl,
    dayToDate: dayToDate, dateToDay: dateToDay };
}