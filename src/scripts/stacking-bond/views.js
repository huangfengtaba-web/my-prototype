function viewEQP() {
  const eqps = EQPS.filter(function (e) {
    const q = UI.eqpQ.trim().toLowerCase();
    return !q || e.toLowerCase().indexOf(q) >= 0;
  });

  let s = '';

  /* ---- v5：字段筛选 + 图表区（视图切换已上移至页面 tab 栏右上方）---- */
  s += '<div class="card"><div class="card-h">' +
    '<div class="t">EQP Loading · 机台产能视图</div>' +
    '</div>' + fieldBar() + winBar() + legendBar();

  if (UI.view === "matrix") {
    s += '<div class="scrollx" id="scEqp" style="margin-top:10px">' + eqpMatrix(eqps) + '</div>';
  } else if (UI.view === "cmp") {
    s += cmpPanel();
  } else {
    s += loadChartCard();
  }
  s += '</div>';

  /* ---- v6：矩阵下方先归属图、再机台承接明细表 ---- */
  s += groupOwnerTable();
  s += eqpGroupTable(eqps);

  return s;
}

/* v6：机台分配段（待决策/Free，画在指定机台行上） */
function candSegsHtml(e) {
  if (!UI.showCand) return '';
  let s = '';
  (CANDSEGS[e] || []).forEach(function (x) {
    const left = x.d.a * 26, w = Math.max(26 * 0.6, x.d.span * 26 - 2);
    const cls = x.g.st === "pending" ? "pending" : "free";
    const tip = '<b>' + esc(x.lot.id) + ' · ' + esc(x.g.name) + '</b>（候选）<br>' +
      '<span class="row"><span class="k">状态</span><span>' + esc(ST[x.g.st].n) + ' · 尚未落定</span></span>' +
      '<span class="row"><span class="k">候选机台</span><span>' + esc(x.g.cand.join(" / ")) + '</span></span>' +
      '<span class="row"><span class="k">层 / 天区间</span><span>L' + x.g.lFrom + '–' + x.g.lTo + ' · D' + (x.d.a + 1) + '–' + (x.d.b + 1) + '</span></span>';
    s += '<div class="seg ' + cls + '" style="left:' + left + 'px;width:' + w + 'px;opacity:.85" data-tip="' + esc(tip) + '"></div>';
  });
  return s;
}

/* 段带甘特（机台分组） */
function eqpGantt(eqps) {
  let s = ruler(HEAD_W, "机台 / Lot · Group");
  eqps.forEach(function (e) {
    const list = SEGS[e];
    s += '<div class="grow grp"><div class="gh" style="width:' + HEAD_W + 'px;min-width:' + HEAD_W + 'px">' +
      '<b>' + e + '</b><small>承接 ' + list.length + ' 段 · 合计 ' + f0(MET.tot[e]) + ' pics</small></div>' +
      '<div class="gt" style="width:' + (DAYS * CW) + 'px;background:#F7FAFE">' + candSegsHtml(e) + '</div></div>';
    list.forEach(function (x) {
      const left = x.d.a * CW, w = Math.max(CW * 0.6, x.d.span * CW - 2);
      const tip = segTip(x.lot, x.g, x.d);
      const label = x.d.span * 1 >= 2 ? (x.lot.id.replace("LOT-", "") + " " + x.g.name + " · " + x.g.pics + "p") : "";
      s += '<div class="grow"><div class="gh" style="width:' + HEAD_W + 'px;min-width:' + HEAD_W + 'px;padding-left:20px">' +
        '<b style="font-size:11.2px;font-weight:600">' + esc(x.lot.id) + ' · ' + esc(x.g.name) + '</b>' +
        '<small>L' + x.g.lFrom + '–L' + x.g.lTo + ' · D' + (x.d.a + 1) + '–D' + (x.d.b + 1) + '</small></div>' +
        '<div class="gt" style="width:' + (DAYS * CW) + 'px">' +
        '<div class="seg ' + ST[x.g.st].c + ' edge-l edge-r" style="left:' + left + 'px;width:' + w + 'px" data-tip="' + esc(tip) + '">' +
        esc(label) + '</div></div></div>';
    });
  });
  return s;
}
/* 日负载矩阵 */
function eqpMatrix(eqps) {
  const mx = Math.max.apply(null, EQPS.map(e => Math.max.apply(null, LOAD[e])));
  let s = '<table class="mx"><thead><tr><th class="rh">机台 / 日期</th>';
  for (let t = 0; t < DAYS; t++) s += '<th class="' + (t % 7 === 0 ? "wk" : "") + (inDayRange(t) ? "" : " outd") + '" data-tip="' + esc(dayBoxTip(t)) + '">' + (t + 1) + '</th>';
  s += '</tr></thead><tbody>';
  eqps.forEach(function (e) {
    s += '<tr><td class="rh">' + e + '<br><span style="font-weight:400;font-size:10px;color:#8A94A6">合计 ' + f0(MET.tot[e]) + '</span></td>';
    for (let t = 0; t < DAYS; t++) {
      const v = LOAD[e][t];
      const cl = CANDL[e] ? CANDL[e][t] : 0;
      let cls = "d";
      if (v <= 0) cls = cl > 0 ? "d cand" : "d zero";
      else if (v > mx * 0.75) cls = "d h3";
      else if (v > mx * 0.5) cls = "d h2";
      else if (v > 0) cls = "d h1";
      const bv = LOADB[e][t], dv = LOADD[e][t], ns = NSTART[e][t];
      if (ns > 0) cls += " st";
      const tip = '<b>' + e + ' · D' + (t + 1) + '</b><br>' +
        '<span class="row"><span class="k">当日负载合计</span><span>' + n1(v) + ' pics</span></span>' +
        '<span class="row"><span class="k">其中 已绑定</span><span>' + (bv > 0 ? n1(bv) + ' pics' : '无') + '</span></span>' +
        '<span class="row"><span class="k">其中 本次决策</span><span>' + (dv > 0 ? n1(dv) + ' pics' : '无') + '</span></span>' +
        '<span class="row"><span class="k">待决策 / Free（分配）</span><span>' + (cl > 0 ? n1(cl) + ' pics' : '无') + '</span></span>' +
        '<hr><span class="row"><span class="k">本日新起段</span><span>' + ns + ' 段' + (ns ? '（当日才有新的已绑/决策）' : '（当日无新段，仅持续占用）') + '</span></span>' +
        '<span class="row"><span class="k">全场当日最大</span><span>' + n1(MET.dailyPeak[t]) + ' pics</span></span>';
      s += '<td class="' + cls + (inDayRange(t) ? "" : " outd") + '" data-tip="' + esc(tip) + '">' + (v > 0 ? Math.round(v * 10) / 10 : "·") + '</td>';
    }
    s += '</tr>';
  });
  s += '</tbody></table>';
  return s;
}

/* 机台承接 Group 明细表（c 项：机台 → Lot × Group 反查） */
function eqpGroupTable(eqps) {
  let rows = [];
  eqps.forEach(function (e) {
    SEGS[e].forEach(function (x) {
      rows.push({ eqp: e, lot: x.lot.id, gn: x.g.gn, lFrom: x.g.lFrom, lTo: x.g.lTo,
        dA: x.d.a + 1, dB: x.d.b + 1, span: x.d.span, st: x.g.st, cand: x.g.cand.join("/"), pics: x.g.pics });
    });
  });

  /* v6：Group 编号只有全局一套，序号筛选恒按全局# 匹配 */
  const fsE = gFilterSet();
  if (fsE.on) rows = rows.filter(function (r) { return fsE.want[r.gn]; });
  if (UI.stFilter !== "all") rows = rows.filter(function (r) { return r.st === UI.stFilter; });

  const K = UI.eqpSort.k, D = UI.eqpSort.dir;
  rows.sort(function (a, b) {
    let x = a[K], y = b[K];
    if (typeof x === "string") return x.localeCompare(y) * D;
    return (x - y) * D;
  });

  const COLS = [["eqp", "机台"], ["lot", "Lot"], ["gn", "Group#"], ["lFrom", "起 Layer"], ["lTo", "止 Layer"],
    ["dA", "起 Day"], ["dB", "止 Day"], ["span", "占天"], ["cand", "候选机台"], ["st", "状态"], ["pics", "负载 pics"]];

  let s = '<div class="card"><h3>机台承接 Group 明细</h3>' +
    '<div class="fbar">' +
    '<div class="fi"><label>Group 序号</label><input id="fG" value="' + esc(UI.gFilter) + '" placeholder="如 10-15 或 10,11" style="width:150px"></div>' +
    '<div class="fi"><label>状态</label>' + tip('四态：已绑定(黄)/待决策(橙)/本次决策(蓝)/Free Layer(灰斜纹)；待决策与 Free 已按分配表（mock）落到指定机台') + '<select id="fSt">' +
    '<option value="all"' + (UI.stFilter === "all" ? " selected" : "") + '>全部</option>' +
    '<option value="bound"' + (UI.stFilter === "bound" ? " selected" : "") + '>已绑定</option>' +
    '<option value="pending"' + (UI.stFilter === "pending" ? " selected" : "") + '>待决策</option>' +
    '<option value="free"' + (UI.stFilter === "free" ? " selected" : "") + '>Free Layer</option>' +
    '<option value="dec"' + (UI.stFilter === "dec" ? " selected" : "") + '>本次决策</option></select></div>' +
    '<div class="spacer"></div><span class="cnt">共 ' + rows.length + ' 条</span>' +
    '<button class="btn sm" data-csv="eqpSeg">导出 CSV</button></div>' +
    '<div class="tscroll"><table class="dt"><thead><tr>';
  COLS.forEach(function (c) {
    const ar = (K === c[0]) ? (D > 0 ? " ▲" : " ▼") : " ⇅";
    s += '<th class="sortable" data-sort="' + c[0] + '">' + esc(c[1]) + ar +
      (c[0] === "gn" ? tip('全局 Group 序号：全部段按起始天排序后的唯一编号') : "") +
      '</th>';
  });
  s += '</tr></thead><tbody>';
  rows.forEach(function (r) {
    s += '<tr>' +
      '<td><b>' + esc(r.eqp) + '</b></td>' +
      '<td class="mono">' + esc(r.lot) + '</td>' +
      '<td><b>G' + r.gn + '</b></td>' +
      '<td class="num">' + r.lFrom + '</td><td class="num">' + r.lTo + '</td>' +
      '<td class="num">D' + r.dA + '</td><td class="num">D' + r.dB + '</td>' +
      '<td class="num">' + r.span + '</td>' +
      '<td class="mono">' + esc(r.cand) + '</td>' +
      '<td><span class="pill ' + ST[r.st].pill + '">' + esc(ST[r.st].n) + '</span></td>' +
      '<td class="num">' + r.pics + '</td></tr>';
  });
  s += '</tbody></table></div>';
  if (!rows.length) {
    s += UI.stFilter === "free"
      ? '<div style="padding:20px;text-align:center;color:#5A6478;font-size:12px;line-height:1.8">' +
        '<b>当前筛选下无 Free Layer 承接行。</b><br>可在机台负载图或日负载矩阵中查看分配口径。</div>'
      : '<div style="padding:22px;text-align:center;color:#8A94A6;font-size:12px">无匹配数据</div>';
  }
  s += '</div>';
  return s;
}
/* ---- v4：Group → 机台 归属图（双编号 + 机台悬停汇总）---- */
function groupOwnerTable() {
  const fs = gFilterSet();
  let rows = ALLSEGS;
  if (fs.on) rows = rows.filter(function (x) { return fs.want[x.g[fs.key]]; });
  const eqpStat = {}; EQPS.forEach(function (e) {
    const segs = SEGS[e] || [], lp = {}; let p = 0;
    segs.forEach(function (x) { lp[x.lot.id] = 1; p += x.g.pics; });
    eqpStat[e] = { n: segs.length, p: p, l: Object.keys(lp).length };
  });
  const candTip = function (x) {
    return '<b>' + esc(x.g.lname) + '（全局#' + x.gn + '）· ' + esc(x.lot.id) + '</b><br>' +
      '<span class="row"><span class="k">状态</span><span>' + esc(ST[x.g.st].n) + '（尚未落定）</span></span>' +
      '<span class="row"><span class="k">候选机台</span><span>' + esc(x.g.cand.join(" / ")) + '</span></span>' +
      '<span class="row"><span class="k">层 / 天区间</span><span>L' + x.g.lFrom + '–' + x.g.lTo + ' · D' + (x.d.a + 1) + '–' + (x.d.b + 1) + '</span></span>';
  };
  const fixTip = function (x) {
    return '<b>' + esc(x.g.lname) + '（全局#' + x.gn + '）· ' + esc(x.lot.id) + '</b><br>' +
      '<span class="row"><span class="k">状态</span><span>' + esc(ST[x.g.st].n) + '</span></span>' +
      '<span class="row"><span class="k">承接机台</span><span><b>' + esc(x.g.eqp) + '</b></span></span>' +
      '<span class="row"><span class="k">层 / 天区间</span><span>L' + x.g.lFrom + '–' + x.g.lTo + ' · D' + (x.d.a + 1) + '–' + (x.d.b + 1) + '</span></span>' +
      '<span class="row"><span class="k">负载</span><span>' + x.g.pics + ' pics</span></span>';
  };
  let s = '<div class="card"><h3>Group → 机台 归属图</h3>' +
    '<div class="fbar"><div class="fi"><label>Group 序号</label>' + tip('支持 1-10 / 5,8 / 7；按全局 Group 序号匹配，非法输入自动忽略。') + '<input id="fG" value="' + esc(UI.gFilter) +
    '" placeholder="如 1-10 或 5,8" style="width:150px"></div>' +
    '<div class="spacer"></div><span class="cnt">共 ' + rows.length + ' 行</span>' +
    '<button class="btn sm" data-csv="grpOwner">导出 CSV</button></div>' +
    '<div class="tscroll" style="max-height:540px"><table class="dt"><thead><tr>' +
    '<th>Group#</th><th>Lot</th><th>层区间</th><th>天区间</th><th>状态</th>' +
    EQPS.map(function (e) {
      const t = eqpStat[e];
      return '<th class="eqpTh" data-eqp="' + e + '" data-tip="' + esc(eqpTip(e)) + '">' + tip('机台 ' + e + ' 现有承接：' + t.n + ' 段 · ' + t.p + ' pics · ' + t.l + ' 个 Lot；悬停列头可看逐 Lot 明细') + esc(e) +
        '<span class="th2">' + t.n + '段·' + t.p + ' pics</span></th>';
    }).join("") +
    '<th>负载 pics</th></tr></thead><tbody>';
  rows.forEach(function (x) {
    s += '<tr><td class="mono"><b>G' + x.gn + '</b></td><td class="mono">' + esc(x.lot.id) + '</td>' +
      '<td class="num">L' + x.g.lFrom + '–' + x.g.lTo + '</td>' +
      '<td class="num">D' + (x.d.a + 1) + '–' + (x.d.b + 1) + '</td>' +
      '<td><span class="pill ' + ST[x.g.st].pill + '">' + esc(ST[x.g.st].n) + '</span></td>';
    EQPS.forEach(function (e) {
      if (x.g.eqp === e) {
        const bg = x.g.st === "pending" ? "#F0B95A" : x.g.st === "free" ? "#C9CFD8" : "#2F4368";
        const fg = x.g.st === "free" ? "#5A6478" : "#fff";
        s += '<td data-eqp="' + e + '" style="background:' + bg + ';color:' + fg + ';font-weight:700;cursor:default" data-tip="' + esc(fixTip(x)) + '">' + x.g.pics + '</td>';
      } else s += '<td data-eqp="' + e + '" style="color:#D3D9E3">·</td>';
    });
    s += '<td class="num">' + x.g.pics + '</td></tr>';
  });
  s += '</tbody><tfoot><tr><td colspan="5" style="text-align:right">机台现有承接合计（悬停列头看明细）</td>' +
    EQPS.map(function (e) {
      const t = eqpStat[e];
      return '<td data-eqp="' + e + '" data-tip="' + esc(eqpTip(e)) + '" style="cursor:default">' + t.n + '段·' + t.p + 'p·' + t.l + 'Lot</td>';
    }).join("") + '<td></td></tr></tfoot></table></div>' +
    '<div class="legend" style="margin-top:8px">' +
    '<span class="li"><i style="background:#2F4368"></i>已绑定 / 本次决策（实心）</span>' +
    '<span class="li"><i style="background:#F0B95A"></i>待决策（已按分配表落到机台）</span>' +
    '<span class="li"><i style="background:#C9CFD8"></i>Free Layer（已按分配表落到机台）</span></div></div>';
  return s;
}
/* ---- v3：待决策 / Free Layer 清单 + 候选机台分布 ---- */
function freeList() {
  var rows = [];
  LOTS.forEach(function (l) {
    l.groups.forEach(function (g) {
      if (g.st !== "free" && g.st !== "pending") return;
      var d = segDays(l, g);
      rows.push({ lot: l.id, product: l.product, gn: g.gn, gIdx: g.idx, gname: g.name, lFrom: g.lFrom, lTo: g.lTo,
        dA: d.a + 1, dB: d.b + 1, span: d.span, cand: g.cand.join("/"), nCand: g.cand.length,
        st: g.st, stN: ST[g.st].n, stPill: ST[g.st].pill, pics: g.pics });
    });
  });
  return rows;
}

function freeCandBar(rows) {
  var cnt = {}, pic = {};
  EQPS.forEach(function (e) { cnt[e] = 0; pic[e] = 0; });
  rows.forEach(function (r) {
    r.cand.split("/").forEach(function (e) { if (cnt[e] != null) { cnt[e]++; pic[e] += r.pics / r.nCand; } });
  });
  var mx = 0; EQPS.forEach(function (e) { if (cnt[e] > mx) mx = cnt[e]; });
  var s = '<div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;margin:4px 0 11px">';
  EQPS.forEach(function (e) {
    var w = mx ? (cnt[e] / mx * 100) : 0;
    s += '<div style="border:1px solid var(--line);border-radius:6px;padding:7px 9px;background:#FCFDFF">' +
      '<div style="display:flex;justify-content:space-between;font-size:11.6px;color:var(--ink2)"><b>' + esc(e) +
      '</b><span class="mono">' + cnt[e] + ' 段</span></div>' +
      '<div style="height:6px;background:#EEF1F6;border-radius:4px;margin:6px 0 5px">' +
      '<div style="height:6px;width:' + w.toFixed(1) + '%;background:#7B5CD6;border-radius:4px"></div></div>' +
      '<div style="font-size:10.6px;color:var(--muted)">均分后 ' + n1(pic[e]) + ' pics</div></div>';
  });
  return s + '</div>';
}

function freeLayerTable() {
  var rows = freeList(), fs = gFilterSet();
  if (fs.on) rows = rows.filter(function (r) { return fs.want[fs.key === "idx" ? r.gIdx : r.gn]; });
  var q = (UI.freeQ || "").trim().toLowerCase();
  if (q) rows = rows.filter(function (r) { return r.lot.toLowerCase().indexOf(q) >= 0 || r.product.toLowerCase().indexOf(q) >= 0; });
  var K = UI.freeSort.k, D = UI.freeSort.dir;
  rows.sort(function (a, b) {
    var x = a[K], y = b[K];
    if (typeof x === "string") return x.localeCompare(y) * D;
    return (x - y) * D;
  });
  var tot = rows.reduce(function (a, r) { return a + r.pics; }, 0);
  var COLS = [["lot", "Lot"], ["gn", "Group"], ["lFrom", "起 Layer"], ["lTo", "止 Layer"],
    ["dA", "起 Day"], ["dB", "止 Day"], ["span", "占天"], ["cand", "候选机台"], ["stN", "状态"], ["pics", "负载 pics"]];
  var s = '<div class="card"><h3>待决策 / Free Layer 清单（尚未分配机台）</h3>' +
    '<p class="desc"><b>待决策（橙）= 本轮排程要决定的段</b>；<b>Free Layer（灰斜纹）= 尚未纳入本轮的层</b> —— 两者是不同状态，都还没有落到机台。' +
    '它们不在上方归属图的实心格内。勾选顶部「待决策/Free 段按候选均分计入机台」后，这些 pics 会按候选机台均分并计入机台负载。</p>' +
    '<div class="fbar"><div class="fi"><label>Lot 筛选</label><input id="qFree" value="' + esc(UI.freeQ || "") +
    '" placeholder="如 LOT-A01" style="width:150px"></div>' +
    '<div class="spacer"></div><span class="cnt">共 ' + rows.length + ' 段 / ' + tot + ' pics</span>' +
    '<button class="btn sm" data-csv="freeList">导出 CSV</button></div>' +
    '<div style="font-size:11.4px;color:var(--muted);margin:2px 0 3px"><b>候选机台分布</b>（每个待决策/Free 段点名的机台；条长 = 被点名次数，下方为该机台均分后可得 pics）</div>' +
    freeCandBar(rows) +
    '<div class="tscroll"><table class="dt"><thead><tr>';
  COLS.forEach(function (c) {
    var ar = (K === c[0]) ? (D > 0 ? " ▲" : " ▼") : " ⇅";
    s += '<th class="sortable" data-sort="' + c[0] + '" data-sortset="free">' + esc(c[1]) + ar + '</th>';
  });
  s += '</tr></thead><tbody>';
  rows.forEach(function (r) {
    s += '<tr><td class="mono"><b>' + esc(r.lot) + '</b></td><td><b>' + esc(r.gname) + '</b></td>' +
      '<td class="num">' + r.lFrom + '</td><td class="num">' + r.lTo + '</td>' +
      '<td class="num">D' + r.dA + '</td><td class="num">D' + r.dB + '</td><td class="num">' + r.span + '</td>' +
      '<td class="mono">' + esc(r.cand) + '</td>' +
      '<td><span class="pill ' + r.stPill + '">' + esc(r.stN) + '</span></td>' +
      '<td class="num">' + r.pics + '</td></tr>';
  });
  s += '</tbody></table></div>';
  if (!rows.length) s += '<div style="padding:22px;text-align:center;color:#8A94A6;font-size:12px">无匹配数据</div>';
  s += '</div>';
  return s;
}
/* ============================================================
   5. 页签二：Lot Stacking Bond
   ============================================================ */
function viewLot() {
  const q = UI.lotQ.trim().toLowerCase();
  const pf = UI.pFilter;
  const segHit = function (l, g) {
    return (pf.product === "all" || l.product === pf.product) &&
      (pf.flow === "all" || g.flow === pf.flow) &&
      (pf.stage === "all" || g.stage === pf.stage) &&
      (pf.step === "all" || String(g.step) === pf.step);
  };
  const lots = LOTS.filter(function (l) {
    if (q && l.id.toLowerCase().indexOf(q) < 0 && l.product.toLowerCase().indexOf(q) < 0) return false;
    return l.groups.some(function (g) { return segHit(l, g); });
  });
  const K = UI.lotSort.k, D = UI.lotSort.dir;
  function cnt(l, st) { return l.groups.filter(function (g) { return g.st === st; }).length; }
  function lotVal(l, k) {
    if (k === "dec" || k === "free" || k === "bound") return cnt(l, k);
    if (k === "decSeg") { for (let i = 0; i < l.groups.length; i++) if (l.groups[i].st === "dec") return i + 1; return 0; }
    return l[k];
  }
  lots.sort(function (a, b) {
    const x = lotVal(a, K), y = lotVal(b, K);
    if (typeof x === "string") return x.localeCompare(y) * D;
    return (x - y) * D;
  });

  const eqpSet = {};
  LOTS.forEach(function (l) { l.groups.forEach(function (g) { if (g.eqp) eqpSet[g.eqp] = 1; }); });

  /* v5.1：KPI 已按要求移除 */
  let s = '';

  function pSel(key, label, vals, cmt) {
    return '<div class="fi"><label>' + label + '</label>' + (cmt ? tip(cmt) : "") + '<select data-pf="' + key + '">' +
      '<option value="all"' + (pf[key] === "all" ? " selected" : "") + '>全部</option>' +
      vals.map(function (v) { return '<option value="' + esc(String(v)) + '"' + (pf[key] === String(v) ? " selected" : "") + '>' + esc(v) + '</option>'; }).join("") +
      '</select></div>';
  }
  const stepVals = []; LOTS.forEach(function (l) { l.groups.forEach(function (g) { if (stepVals.indexOf(g.step) < 0) stepVals.push(g.step); }); });
  stepVals.sort(function (a, b) { return a - b; });

  s += '<div class="card"><h3>Lot Stacking Bond · ' + (UI.lotAxis === "grp" ? "按 Group 视图" : "按天数段带视图") + '</h3>' +
    '<div class="fbar">' +
    '<div class="fi"><label>横轴</label>' +
    '<button class="btn sm' + (UI.lotAxis === "day" ? " pri" : "") + '" data-axis="day">按天数</button> ' +
    '<button class="btn sm' + (UI.lotAxis === "grp" ? " pri" : "") + '" data-axis="grp">按 Group</button></div>' +
    '<div class="fi"><label>Lot 筛选</label><input id="qLot" value="' + esc(UI.lotQ) + '" placeholder="如 LOT-A01 / 5002A" style="width:170px"></div>' +
    pSel("product", "Product", PRODS, '产品号筛选；Lot 列表显示含匹配段的 Lot，段带明细表只显示匹配段') +
    pSel("flow", "Flow", FLOWS, '光刻层流程组（演示口径：AA / POLY / METAL / VIA）') +
    pSel("stage", "Stage", ["FE", "ME", "BE"], '工艺阶段：FE前段 / ME中段 / BE后段，与候选机台池的层深对齐（FE→E1E2、ME→E3E4、BE→E5E6）') +
    pSel("step", "Step", stepVals, '4 位光刻步骤号，Lot 内按段递增（演示口径，可被真实数据替换）') +
    dayRangeCtl() +
    '<button class="btn sm primary" data-act="query">查询</button>' +
    '<button class="btn sm" data-act="resetFilter">重置</button>' +
    '<div class="spacer"></div><span class="cnt">共 ' + lots.length + ' 个 Lot</span></div>' +
    legendBar() + winBar() +
    '<div class="scrollx" id="scLot" style="margin-top:10px">' + (UI.lotAxis === "grp" ? lotByGroup(lots) : lotGantt(lots)) + '</div>' +
    '<div class="note">段带宽度 = 该段层数 × 每层 CT（' + CFG.ct + ' 天）。例：某段 4 层 → 横跨 8 天，' +
    '这 8 天的负载值<b>完全相同</b>；段与段之间无空隙的天即为该 Lot 的<b>连续加工期</b>。</div></div>';

  s += lotSegTable(lots);
  return s;
}
/* v6.1：按天数段带视图 —— 行头与天轴之间增加 Product / Flow / Stage / Step 字段列（随天轴滚动，仅首列 Lot 冻结） */
function lotGantt(lots) {
  const FW = 78;
  const heads = ["Product", "Flow", "Stage", "Step"];
  /* 表头：Lot 列 + 4 个字段列 + 天轴 */
  let s = '<div class="ruler"><div class="rh" style="width:' + HEAD_W + 'px;min-width:' + HEAD_W + 'px;height:38px;' +
    'display:flex;align-items:center;padding:0 9px;font-size:11.4px;font-weight:700;color:#5A6B85">Lot / 产品</div>';
  heads.forEach(function (h, i) {
    s += '<div style="width:' + FW + 'px;min-width:' + FW + 'px;height:38px;display:flex;align-items:center;padding:0 7px;' +
      'font-size:11.4px;font-weight:700;color:#5A6B85">' + h + '</div>';
  });
  s += '<div style="display:flex;flex:none">';
  for (let t = 0; t < DAYS; t++) {
    const wk = (t % 7 === 0);
    s += '<div class="rc' + (wk ? " wk" : "") + (inDayRange(t) ? "" : " outd") + '" style="width:' + CW + 'px;height:38px">' + (wk ? "D" + (t + 1) : (t + 1)) + '</div>';
  }
  s += '</div></div>';
  /* 行：Lot 头 + 4 个字段格 + 段带 */
  lots.forEach(function (l) {
    const flows = [], stages = [];
    let stMin = 1e9, stMax = 0;
    l.groups.forEach(function (g) {
      if (flows.indexOf(g.flow) < 0) flows.push(g.flow);
      if (stages.indexOf(g.stage) < 0) stages.push(g.stage);
      if (g.step < stMin) stMin = g.step; if (g.step > stMax) stMax = g.step;
    });
    const vals = [l.product, flows.join("/"), stages.join("/"), stMin + "–" + stMax];
    s += '<div class="grow"><div class="gh" style="width:' + HEAD_W + 'px;min-width:' + HEAD_W + 'px">' +
      '<b>' + esc(l.id) + '</b><small>' + l.layers + ' 层 · ' + l.groups.length + ' 段</small></div>';
    vals.forEach(function (v, i) {
      s += '<div style="flex:none;width:' + FW + 'px;min-width:' + FW + 'px;height:34px;' +
        'display:flex;align-items:center;padding:0 7px;font-size:11px;color:var(--colorTextSecondary);' +
        'border-right:1px solid var(--colorBorderSecondary);overflow:hidden;white-space:nowrap" data-tip="' + esc(heads[i] + ': ' + v) + '">' + esc(v) + '</div>';
    });
    s += '<div class="gt" style="width:' + (DAYS * CW) + 'px">';
    l.groups.forEach(function (g) {
      const d = segDays(l, g);
      const left = d.a * CW, w = Math.max(CW * 0.6, d.span * CW - 2);
      const tip = segTip(l, g, d);
      const lab = w >= 52 ? (g.st === "free" ? "Free" : g.st === "pending" ? "待决策" : g.eqp) + " L" + g.lFrom + "-" + g.lTo : "";
      s += '<div class="seg ' + ST[g.st].c + ' edge-l edge-r" style="left:' + left + 'px;width:' + w + 'px" data-tip="' + esc(tip) + '">' + esc(lab) + '</div>';
    });
    s += '</div></div>';
  });
  return s;
}
/* v6：按 Group 视图（网格矩阵：色块 + 悬浮明细；Group 编号只有全局一套） */
function lotByGroup(lots) {
  const fs = gFilterSet();
  const N = ALLSEGS.length;
  let s = '<div style="padding:14px 4px 4px">';
  /* 列轴标 */
  s += '<div class="gaxis" style="padding-left:146px">';
  for (let i = 1; i <= N; i++) s += '<div class="c' + (fs.on && fs.want[i] ? " on" : "") + '">' + i + '</div>';
  s += '</div>';
  s += '<table class="gmx"><thead><tr><th class="lotcol">Lot / Group#</th>';
  for (let i = 1; i <= N; i++) s += '<th>' + (i % 5 === 0 || i === 1 ? i : "") + '</th>';
  s += '<th style="padding-left:10px;min-width:70px">合计</th></tr></thead><tbody>';
  lots.forEach(function (l) {
    s += '<tr><td class="lotcol"><b>' + esc(l.id) + '</b><br><span style="font-size:11px;color:#8A94A6">' + esc(l.product) + ' · ' + l.groups.length + ' 段</span></td>';
    let tot = 0;
    const colMap = {};
    l.groups.forEach(function (g) { colMap[g.gn] = g; });
    for (let i = 1; i <= N; i++) {
      const g = colMap[i];
      if (!g) { s += '<td class="cell"><div class="gcell none">·</div></td>'; continue; }
      if (fs.on && !fs.want[g.gn]) {
        s += '<td class="cell"><div class="gcell none" style="opacity:.45">G' + g.gn + '</div></td>';
        continue;
      }
      tot += g.pics;
      s += '<td class="cell"><div class="gcell ' + ST[g.st].c + '" data-tip="' + esc(segTip(l, g, segDays(l, g))) + '">G' + g.gn + '</div></td>';
    }
    s += '<td class="num" style="padding-left:10px;font-size:12px;color:#5A6B85">' + tot + ' pics</td></tr>';
  });
  s += '</tbody></table>';
  s += '<div class="legend" style="margin-top:10px"><span class="li"><i style="background:#F2BA02"></i>已绑定</span>' +
    '<span class="li"><i style="background:#F0B95A"></i>待决策</span>' +
    '<span class="li"><i style="background:#4874CB"></i>本次决策</span>' +
    '<span class="li free"><i></i>Free Layer</span>' +
    '<span class="note">列 = 全局 Group#（按起始天排序，全场唯一）</span></div>';
  return s + '</div>';
}
/* v4：Lot 段带明细表（全部段逐行，含待决策/Free 段；双编号 + Product/Flow/Stage/Step 列） */
function lotSegTable(lots) {
  var rows = [], fs = gFilterSet();
  lots.forEach(function (l) {
    l.groups.forEach(function (g) {
      if (fs.on && !fs.want[g.gn]) return;
      if (!segHitP(l, g)) return;
      var d = segDays(l, g);
      rows.push({ lot: l.id, product: l.product, gn: g.gn, flow: g.flow, stage: g.stage, step: g.step,
        lFrom: g.lFrom, lTo: g.lTo,
        dA: d.a + 1, dB: d.b + 1, span: d.span, nLayer: g.lTo - g.lFrom + 1,
        cand: g.cand.join("/"), st: g.st, eqp: g.eqp || "未分配", pics: g.pics });
    });
  });
  var K = UI.lotSegSort.k, D = UI.lotSegSort.dir;
  rows.sort(function (a, b) {
    var x = a[K], y = b[K];
    if (typeof x === "string") return x.localeCompare(y) * D;
    return (x - y) * D;
  });
  var tot = rows.reduce(function (a, r) { return a + r.pics; }, 0);
  var nP = rows.filter(function (r) { return r.st === "pending"; }).length;
  var nF = rows.filter(function (r) { return r.st === "free"; }).length;
  var COLS = [["lot", "Lot"], ["product", "Product"], ["gn", "Group#"], ["flow", "Flow"], ["stage", "Stage"], ["step", "Step"],
    ["lFrom", "起 Layer"], ["lTo", "止 Layer"], ["nLayer", "层数"],
    ["dA", "起 Day"], ["dB", "止 Day"], ["span", "占天"], ["cand", "候选机台"], ["st", "状态"], ["eqp", "承接机台"], ["pics", "负载 pics"]];
  var s = '<div class="card"><h3>Lot 段带明细表（全部段逐行）</h3>' +
    '<div class="fbar">' +
    /* v5.1：筛选补充 Product / Flow / Stage / Step（与视图、页签一共用同一组段级筛选） */
    (function () {
      var pf = UI.pFilter;
      var steps2 = []; LOTS.forEach(function (l) { l.groups.forEach(function (g) { if (steps2.indexOf(g.step) < 0) steps2.push(g.step); }); });
      steps2.sort(function (a, b) { return a - b; });
      var mk = function (key, label, vals) {
        return '<div class="fi"><label>' + label + '</label><select data-pf="' + key + '">' +
          '<option value="all"' + (pf[key] === "all" ? " selected" : "") + '>全部</option>' +
          vals.map(function (v) { return '<option value="' + esc(String(v)) + '"' + (pf[key] === String(v) ? " selected" : "") + '>' + esc(v) + '</option>'; }).join("") +
          '</select></div>';
      };
      return mk("product", "Product", PRODS) + mk("flow", "Flow", FLOWS) + mk("stage", "Stage", ["FE", "ME", "BE"]) + mk("step", "Step", steps2);
    })() +
    '<div class="fi"><label>Group 序号</label><input id="fG" value="' + esc(UI.gFilter) + '" placeholder="如 10-15" style="width:130px"></div>' +
    '<div class="spacer"></div><span class="cnt">共 ' + rows.length + ' 段 / 负载合计 ' + tot + ' pics（待决策 ' + nP + ' 段 · Free ' + nF + ' 段）</span>' +
    '<button class="btn sm" data-csv="lotSeg">导出 CSV</button></div>' +
    '<div class="tscroll"><table class="dt"><thead><tr>';
  COLS.forEach(function (c) {
    var ar = (K === c[0]) ? (D > 0 ? " ▲" : " ▼") : " ⇅";
    s += '<th class="sortable" data-sort="' + c[0] + '" data-sortset="lotseg">' + esc(c[1]) + ar + '</th>';
  });
  s += '</tr></thead><tbody>';
  rows.forEach(function (r) {
    s += '<tr><td class="mono"><b>' + esc(r.lot) + '</b></td><td>' + esc(r.product) + '</td>' +
      '<td><b>G' + r.gn + '</b></td>' +
      '<td class="mono">' + esc(r.flow) + '</td><td class="mono">' + esc(r.stage) + '</td><td class="num">' + r.step + '</td>' +
      '<td class="num">' + r.lFrom + '</td><td class="num">' + r.lTo + '</td><td class="num">' + r.nLayer + '</td>' +
      '<td class="num">D' + r.dA + '</td><td class="num">D' + r.dB + '</td><td class="num">' + r.span + '</td>' +
      '<td class="mono">' + esc(r.cand) + '</td>' +
      '<td><span class="pill ' + ST[r.st].pill + '">' + esc(ST[r.st].n) + '</span></td>' +
      '<td class="mono">' + esc(r.eqp) + '</td><td class="num">' + r.pics + '</td></tr>';
  });
  s += '</tbody></table></div>';
  if (!rows.length) s += '<div style="padding:22px;text-align:center;color:#8A94A6;font-size:12px">无匹配数据</div>';
  s += '</div>';
  return s;
}
function lotTable(lots, cnt) {
  const COLS = [["id", "Lot"], ["product", "Product"], ["startDay", "起始 Day"], ["layers", "总层数"],
    ["groups", "段数"], ["bound", "已绑段"], ["free", "Free 段"], ["dec", "本次决策段"], ["decSeg", "dec 段位置"],
    ["flowSet", "Flow"], ["stageSet", "Stage"], ["stepRange", "Step"], ["pics", "总负载 pics"]];
  const K = UI.lotSort.k, D = UI.lotSort.dir;
  let s = '<div class="card"><h3>Lot 汇总表</h3>' +
    '<p class="desc">点表头可排序。每个 Lot 的段数与分段方式各不相同；<b>「dec 段位置」列显示该 Lot 唯一一个本次决策段的段号与承接机台</b>——它可出现在开头、已绑定段之后或空白段之后，其后仍可有其他段。</p>' +
    '<div class="tscroll"><table class="dt"><thead><tr>';
  COLS.forEach(function (c) {
    const ar = (K === c[0]) ? (D > 0 ? " ▲" : " ▼") : " ⇅";
    s += '<th class="sortable" data-sort="' + c[0] + '">' + esc(c[1]) + ar +
      (c[0] === "decSeg" ? tip('该 Lot 唯一一个「本次决策」段的全局 Group# 与承接机台；可出现在开头、已绑定段之后或空白段之后') : "") +
      '</th>';
  });
  s += '</tr></thead><tbody>';
  lots.forEach(function (l) {
    const di = l.groups.findIndex(function (g) { return g.st === "dec"; });
    const dg = di >= 0 ? l.groups[di] : null;
    const flows = [], stages = [];
    let stMin = 1e9, stMax = 0;
    l.groups.forEach(function (g) {
      if (flows.indexOf(g.flow) < 0) flows.push(g.flow);
      if (stages.indexOf(g.stage) < 0) stages.push(g.stage);
      if (g.step < stMin) stMin = g.step; if (g.step > stMax) stMax = g.step;
    });
    const tot = l.groups.filter(function (g) { return g.st !== "free"; }).reduce(function (a, g) { return a + g.pics; }, 0);
    s += '<tr><td class="mono"><b>' + esc(l.id) + '</b></td><td>' + esc(l.product) + '</td>' +
      '<td class="num">D' + (l.startDay + 1) + '</td><td class="num">' + l.layers + '</td>' +
      '<td class="num">' + l.groups.length + '</td>' +
      '<td class="num">' + cnt(l, "bound") + '</td><td class="num">' + cnt(l, "free") + '</td><td class="num">' + cnt(l, "dec") + '</td>' +
      '<td>' + (dg
        ? '<span class="pill ' + ST[dg.st].pill + '">' + esc(dg.eqp || "—") + ' · ' + esc(dg.lname || dg.name) + '（第' + (di + 1) + '/' + l.groups.length + '段）</span>'
        : '—') + '</td>' +
      '<td class="mono">' + esc(flows.join("/")) + '</td>' +
      '<td class="mono">' + esc(stages.join("/")) + '</td>' +
      '<td class="num">' + stMin + '–' + stMax + '</td>' +
      '<td class="num">' + tot + '</td></tr>';
  });
  s += '</tbody></table></div></div>';
  return s;
}
/* ============================================================
   6. 数据配置（Group 定义可编辑）
   ============================================================ */
function viewCfg() {
  let s = '<div class="card"><h3>数据配置 · Group 定义（可编辑）</h3>' +
    '<p class="desc">因为<b>每个 Lot 的 Group 分段都不一样</b>，本页提供逐段编辑：改「起始层 / 结束层 / 状态 / 机台 / 负载」后点「应用并重算」，' +
    '两个视图与全部统计立即重算。改 CT 会同步改变所有段的天区间（天区间 = 层数 × CT）。</p>' +
    '<div class="params" style="margin-bottom:12px">' +
    '<div class="pf"><label>每层 CT（天）</label><input type="number" id="pCt2" value="' + CFG.ct + '" min="1" max="7"></div>' +
    '<div class="pf"><label>时间轴天数（下限）</label><input type="number" id="pDays2" value="' + CFG.days + '" min="30" max="240"></div>' +
    '<div class="pf"><label>Lot 数量</label><input type="number" id="pLots2" value="' + CFG.nLots + '" min="4" max="60"></div>' +
    '<button class="btn pri" data-act="regen">应用并重算</button>' +
    '<button class="btn" data-act="reset">恢复默认</button>' +
    '<span class="cnt" style="align-self:center">共 ' + MET.nSegAll + ' 段 / ' + LOTS.length + ' 个 Lot</span></div>' +
    '<div class="tscroll" style="max-height:560px"><table class="ed"><thead><tr>' +
    '<th>Lot</th><th>Group</th><th>起始层</th><th>结束层</th><th>候选机台</th><th>状态</th><th>承接机台</th><th>负载 pics</th><th>天区间</th>' +
    '</tr></thead><tbody>';
  LOTS.forEach(function (l, li) {
    l.groups.forEach(function (g, gi) {
      const d = segDays(l, g);
      s += '<tr>' +
        '<td style="white-space:nowrap">' + esc(l.id) + '</td>' +
        '<td><b>' + esc(g.name) + '</b></td>' +
        '<td><input class="n" type="number" data-ed="lFrom" data-li="' + li + '" data-gi="' + gi + '" value="' + g.lFrom + '"></td>' +
        '<td><input class="n" type="number" data-ed="lTo" data-li="' + li + '" data-gi="' + gi + '" value="' + g.lTo + '"></td>' +
        '<td style="white-space:nowrap;font-size:11px">' + esc(g.cand.join("/")) + '</td>' +
        '<td><select data-ed="st" data-li="' + li + '" data-gi="' + gi + '">' +
        '<option value="bound"' + (g.st === "bound" ? " selected" : "") + '>已绑定</option>' +
        '<option value="pending"' + (g.st === "pending" ? " selected" : "") + '>待决策（橙）</option>' +
        '<option value="free"' + (g.st === "free" ? " selected" : "") + '>Free Layer（灰斜纹）</option>' +
        '<option value="dec"' + (g.st === "dec" ? " selected" : "") + '>本次决策</option></select></td>' +
        '<td><select data-ed="eqp" data-li="' + li + '" data-gi="' + gi + '"><option value="">未分配</option>' +
        EQPS.map(function (e) { return '<option value="' + e + '"' + (g.eqp === e ? " selected" : "") + '>' + e + '</option>'; }).join("") +
        '</select></td>' +
        '<td><input class="n" type="number" data-ed="pics" data-li="' + li + '" data-gi="' + gi + '" value="' + g.pics + '"></td>' +
        '<td style="white-space:nowrap;color:#8A94A6;font-size:11px">D' + (d.a + 1) + '–D' + (d.b + 1) + '（' + d.span + '天）</td>' +
        '</tr>';
    });
  });
  s += '</tbody></table></div>' +
    '<div class="alert i"><span class="dot"></span><div><b>天区间是派生的</b>：<span class="mono">dayFrom = 起始日 + 起始层 × CT</span>、' +
    '<span class="mono">dayTo = 起始日 + 结束层 × CT + CT − 1</span>。改层数或 CT 会同时改变段的天区间与横向段带宽度。</div></div></div>';
  return s;
}