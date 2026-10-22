/* ============================================================
   3. 片段渲染
   ============================================================ */
function kpi(k, v, s, unit) {
  return '<div class="kpi"><div class="k">' + esc(k) + '</div><div class="v">' + v +
    (unit ? '<small>' + esc(unit) + '</small>' : '') + '</div>' + (s ? '<div class="s">' + esc(s) + '</div>' : '') + '</div>';
}

/* v5：视图切换分段控件 */
function viewTabs(items, cur, act) {
  let s = '<div class="viewtabs">';
  items.forEach(function (it) {
    s += '<button class="' + (cur === it[0] ? "on" : "") + '" data-' + act + '="' + it[0] + '">' + esc(it[1]) + '</button>';
  });
  return s + '</div>';
}

/* v5：字段筛选栏（Product / Flow / Stage / Step + 状态 + 机台） */
function fieldBar() {
  const steps = []; LOTS.forEach(function (l) { l.groups.forEach(function (g) { if (steps.indexOf(g.step) < 0) steps.push(g.step); }); });
  steps.sort(function (a, b) { return a - b; });
  const pf = UI.pFilter;
  const sel = function (key, label, vals, cmt) {
    return '<div class="fi"><label>' + esc(label) + '</label>' + tip(cmt) +
      '<select class="inp" data-pf="' + key + '">' +
      '<option value="all"' + (pf[key] === "all" ? " selected" : "") + '>全部</option>' +
      vals.map(function (v) { return '<option value="' + esc(String(v)) + '"' + (pf[key] === String(v) ? " selected" : "") + '>' + esc(v) + '</option>'; }).join("") +
      '</select></div>';
  };
  return '<div class="toolbar">' +
    '<div class="fi"><label>机台</label><input class="inp" id="qEqp" value="' + esc(UI.eqpQ) + '" placeholder="如 E3" style="width:100px"></div>' +
    sel("product", "Product", PRODS, '产品号筛选；影响本页所有图表与下方表格') +
    sel("flow", "Flow", FLOWS, '光刻层流程组 AA / POLY / METAL / VIA') +
    sel("stage", "Stage", ["FE", "ME", "BE"], '工艺阶段 FE前段 / ME中段 / BE后段，与候选机台池层深对齐') +
    sel("step", "Step", steps, '4 位光刻步骤号，Lot 内按段递增') +
    '<div class="fi"><label>状态</label><select class="inp" data-stf="1">' +
      '<option value="all"' + (UI.stFilter === "all" ? " selected" : "") + '>全部</option>' +
      '<option value="bound"' + (UI.stFilter === "bound" ? " selected" : "") + '>已绑定</option>' +
      '<option value="dec"' + (UI.stFilter === "dec" ? " selected" : "") + '>本次决策</option>' +
      '<option value="pending"' + (UI.stFilter === "pending" ? " selected" : "") + '>待决策</option>' +
      '<option value="free"' + (UI.stFilter === "free" ? " selected" : "") + '>Free Layer</option>' +
    '</select></div>' +
    dayRangeCtl() +
    '<button class="btn sm primary" data-act="query">查询</button>' +
    '<button class="btn sm" data-act="resetFilter">重置</button>' +
    '</div>';
}
function legendBar() {
  return '<div class="legend" style="margin:9px 0 2px">' +
    '<span class="li"><i style="background:#F2BA02"></i>已绑定（黄）</span>' +
    '<span class="li pending"><i></i>待决策（橙 · 已按分配表落机台）</span>' +
    '<span class="li"><i style="background:#4874CB"></i>本次决策（蓝）</span>' +
    '<span class="li free"><i></i>Free Layer（灰斜纹 · 已按分配表落机台）</span></div>';
}

function winBar() {
  const wins = [["all", "全部 1–" + DAYS], ["1", "1–30"], ["2", "31–60"], ["3", "61–90"], ["4", "91–120"]];
  let s = '<div class="winbar"><span class="lab">时间窗口</span>';
  wins.forEach(function (w) {
    s += '<button data-win="' + w[0] + '" class="' + (UI.win === w[0] ? "on" : "") + '">' + esc(w[1]) + '</button>';
  });
  return s + '</div>';   // v6：视图切换已上移至页面 tab 栏右上方，此处仅保留时间窗口
}

/* 日期刻度 */
function ruler(headW, headLabel) {
  let s = '<div class="ruler"><div class="rh" style="width:' + headW + 'px;min-width:' + headW + 'px;height:38px;' +
    'display:flex;align-items:center;padding:0 9px;font-size:11.4px;font-weight:700;color:#5A6B85">' +
    esc(headLabel) + '</div>';
  s += '<div style="display:flex;flex:none">';
  for (let t = 0; t < DAYS; t++) {
    const wk = (t % 7 === 0);
    s += '<div class="rc' + (wk ? " wk" : "") + '" style="width:' + CW + 'px;height:38px">' +
      (wk ? "D" + (t + 1) : (t + 1)) + '</div>';
  }
  s += '</div></div>';
  return s;
}

/* 段 tooltip */
function segTip(lot, g, d) {
  return '<b>' + esc(lot.id) + ' · G' + g.gn + '</b><br>' +
    '<span class="row"><span class="k">产品 / 层数</span><span>' + esc(lot.product) + ' · ' + lot.layers + ' 层</span></span>' +
    '<span class="row"><span class="k">Layer 区间</span><span>L' + g.lFrom + ' – L' + g.lTo + '（' + (g.lTo - g.lFrom + 1) + ' 层）</span></span>' +
    '<span class="row"><span class="k">占用天区间</span><span>D' + (d.a + 1) + ' – D' + (d.b + 1) + '（' + d.span + ' 天）</span></span>' +
    '<hr>' +
    '<span class="row"><span class="k">候选机台</span><span>' + esc(g.cand.join(" / ")) + '</span></span>' +
    '<span class="row"><span class="k">决策状态</span><span>' + esc(ST[g.st].n) + '</span></span>' +
    '<span class="row"><span class="k">承接机台</span><span>' + (g.eqp ? esc(g.eqp) : "未分配") + '</span></span>' +
    '<span class="row"><span class="k">负载</span><span>' + g.pics + ' pics</span></span>';
}

/* v6：Group 序号筛选解析（全局 Group# 口径） */
function gFilterSet() {
  var gf = UI.gFilter.trim(), want = {}, on = true, any = false;
  if (!gf) return { want: want, on: false };
  gf.split(/[,，\s]+/).forEach(function (p) {
    if (!p) return; any = true;
    var mm = p.match(/^(\d+)\s*[-~]\s*(\d+)$/);
    if (mm) { for (var i = +mm[1]; i <= +mm[2]; i++) want[i] = 1; }
    else if (/^\d+$/.test(p)) want[+p] = 1;
    else on = false;
  });
  if (!any) on = false;
  return { want: want, on: on, key: "gn" };   // v6：Group 编号只有全局一套
}

function maxGn() { var m = 1; LOTS.forEach(function (l) { if (l.groups.length > m) m = l.groups.length; }); return m; }

/* ---- v4：机台现有承接汇总 tooltip（归属图列头 / 整列悬停同步显示）---- */
function eqpTip(e) {
  const segs = SEGS[e] || [];
  let pics = 0, nb = 0, nd = 0;
  const lots = [];
  segs.forEach(function (x) {
    pics += x.g.pics; if (x.g.st === "dec") nd++; else nb++;
    let f = null; for (let i = 0; i < lots.length; i++) if (lots[i].id === x.lot.id) { f = lots[i]; break; }
    if (f) { f.n++; f.p += x.g.pics; } else lots.push({ id: x.lot.id, n: 1, p: x.g.pics });
  });
  let days = 0; (LOAD[e] || []).forEach(function (v) { if (v > 0) days++; });
  const csegs = CANDSEGS[e] || [];
  let candP = 0; csegs.forEach(function (x) { candP += x.g.pics / x.g.cand.length; });
  return '<b>' + esc(e) + ' 现有承接汇总</b><br>' +
    '<span class="row"><span class="k">承接段数</span><span><b>' + segs.length + '</b> 段（已绑定 ' + nb + ' · 本次决策 ' + nd + '）</span></span>' +
    '<span class="row"><span class="k">段级负载合计</span><span><b>' + pics + '</b> pics（每段只计 1 次）</span></span>' +
    '<span class="row"><span class="k">日累计负载</span><span>' + (MET ? MET.tot[e] : 0) + ' pics·天（占用 ' + days + ' 天，跨日重复计）</span></span>' +
    '<span class="row"><span class="k">涉及 Lot</span><span><b>' + lots.length + '</b> 个</span></span>' +
    lots.map(function (o) { return '<span class="row"><span class="k">' + esc(o.id) + '</span><span>' + o.n + ' 段 · ' + o.p + ' pics</span></span>'; }).join("") +
    '<span class="row"><span class="k">待决策/Free（分配）</span><span>' + csegs.length + ' 段 · 分配负载合计 ' + Math.round(candP) + ' pics</span></span>';
}