/* V2.0：时间筛选（起止日期）—— 与「时间窗口」共存，取交集 */
const DAY1 = "2026-09-01";          // 日历锚点：D1 = 2026-09-01（演示口径，可换成真实排产首日）
const MS_DAY = 86400000;
function _utc(s) { return Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10)); }
function _pad(n) { return (n < 10 ? "0" : "") + n; }
function dayToDate(d) { const x = new Date(_utc(DAY1) + (d - 1) * MS_DAY); return x.getUTCFullYear() + "-" + _pad(x.getUTCMonth() + 1) + "-" + _pad(x.getUTCDate()); }
function dateToDay(s) { if (!s || s.length < 10) return 0; return Math.round((_utc(s.slice(0, 10)) - _utc(DAY1)) / MS_DAY) + 1; }
function dayHi() { const v = parseInt(UI.dayTo, 10); return (!v || v > DAYS) ? DAYS : Math.max(1, v); }
function dayLo() { const v = parseInt(UI.dayFrom, 10) || 1; return Math.max(1, Math.min(v, dayHi())); }
function hasDayRange() { return dayLo() > 1 || dayHi() < DAYS; }
function inDayRange(t) { return (t + 1) >= dayLo() && (t + 1) <= dayHi(); }
function dayRangeCtl() {
  const lo = dayLo(), hi = dayHi();
  return '<div class="fi"><label>时间</label>' +
    tip('时间筛选：按日期收窄统计口径（D1 = ' + DAY1 + '，共 ' + DAYS + ' 天）。影响负载对比 / 机台负载图 / 机台详情 / 承接明细的逐日聚合；日负载矩阵与段带中区间外的天列淡化。') +
    '<input class="inp" type="date" id="dayFrom" value="' + dayToDate(lo) + '" min="' + dayToDate(1) + '" max="' + dayToDate(DAYS) + '" style="width:150px" title="起始日期">' +
    '<span style="color:var(--colorTextTertiary);font-size:12px">–</span>' +
    '<input class="inp" type="date" id="dayTo" value="' + dayToDate(hi) + '" min="' + dayToDate(1) + '" max="' + dayToDate(DAYS) + '" style="width:150px" title="结束日期"></div>';
}
function resetFilters() {
  UI.eqpQ = ""; UI.lotQ = ""; UI.gFilter = ""; UI.freeQ = "";
  UI.stFilter = "all";
  UI.pFilter = { product: "all", flow: "all", stage: "all", step: "all" };
  UI.dayFrom = 1; UI.dayTo = 0; UI.win = "all";
}
function winDays() {
  let a = UI.win === "all" ? 0 : (parseInt(UI.win, 10) - 1) * 30;
  let b = UI.win === "all" ? DAYS - 1 : Math.min(DAYS - 1, a + 29);
  /* V2.0：再与自定义起止天求交集；交集为空时回落到起止天区间本身 */
  const lo = dayLo() - 1, hi = dayHi() - 1;
  const ra = Math.max(a, lo), rb = Math.min(b, hi);
  if (ra > rb) { a = lo; b = hi; } else { a = ra; b = rb; }
  const days = []; for (let t = a; t <= b; t++) days.push(t);
  return days;
}
/* v4：段级 PFSS 匹配（Product/Flow/Stage/Step，供段带明细与视图共用） */
function segHitP(l, g) {
  const pf = UI.pFilter;
  return (pf.product === "all" || l.product === pf.product) &&
    (pf.flow === "all" || g.flow === pf.flow) &&
    (pf.stage === "all" || g.stage === pf.stage) &&
    (pf.step === "all" || String(g.step) === pf.step);
}