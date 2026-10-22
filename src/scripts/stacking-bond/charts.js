/* v5：机台详情（独立标签页）—— 逐日四态堆叠柱形对比 */
function viewDetail(e) {
  const days = winDays();
  const rows = eqpDailyStates(e, days);
  const t = eqpStateTotals(e, days);
  const bw = 16, step = 28;
  const W = Math.max(760, days.length * step + 68), H = 320, PL = 52, PR = 16, PT = 20, PB = 44;
  const plotH = H - PT - PB;
  const mx = Math.max.apply(null, rows.map(function (r) { return r.tot; })) || 1;
  const Y = function (v) { return PT + plotH - (v / mx) * plotH; };
  let g = '<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '" style="display:block">';
  for (let k = 0; k <= 4; k++) {
    const v = mx * k / 4, y = Y(v);
    g += '<line x1="' + PL + '" y1="' + y + '" x2="' + (W - PR) + '" y2="' + y + '" stroke="#F0F0F0"/>';
    g += '<text x="' + (PL - 6) + '" y="' + (y + 3) + '" fill="#8A94A6" font-size="10" text-anchor="end">' + Math.round(v) + '</text>';
  }
  /* 四态自下而上堆叠：已绑定 / 本次决策 / 待决策 / Free */
  const series = [["b", "已绑定", "#F2BA02"], ["d", "本次决策", "#4874CB"], ["p", "待决策", "#F0B95A"], ["f", "Free", "#C9CFD8"]];
  days.forEach(function (tt, i) {
    const r = rows.filter(function (x) { return x.t === tt; })[0];
    const gx = PL + 8 + i * step;
    let tipTxt = '<b>' + e + ' · D' + (tt + 1) + '</b>';
    let acc = 0;
    series.forEach(function (se) {
      const v = r ? r[se[0]] : 0;
      tipTxt += '<span class="row"><span class="k">' + se[1] + '</span><span>' + n1(v) + ' pics</span></span>';
      if (v > 0) {
        g += '<rect x="' + gx + '" y="' + Y(acc + v) + '" width="' + bw + '" height="' + Math.max(1, (v / mx) * plotH) + '" fill="' + se[2] + '" rx="1"/>';
      }
      acc += v;
    });
    g += '<text x="' + (gx + bw / 2) + '" y="' + (H - 24) + '" fill="#8A94A6" font-size="9.5" text-anchor="middle">D' + (tt + 1) + '</text>';
    g += '<rect x="' + (gx - 4) + '" y="' + PT + '" width="' + (bw + 8) + '" height="' + plotH + '" fill="transparent" pointer-events="all" data-tip="' + esc(tipTxt) + '"/>';
  });
  g += '</svg>';
  /* v6：详情页 KPI 已按要求移除 */
  let s = '';
  s += '<div class="card"><div class="card-h"><div class="t">' + e + ' · 逐日四态负载堆叠对比</div>' +
    '<div class="sub">X 轴 = 天（D1…），每根柱自下而上堆叠 = 已绑定 / 本次决策 / 待决策 / Free Layer</div>' +
    '<div class="right"><button class="btn sm" data-act="closeDetail">← 返回 EQP Loading</button></div></div>' +
    '<div class="legend"><span class="li"><i style="background:#F2BA02"></i>已绑定</span>' +
    '<span class="li"><i style="background:#4874CB"></i>本次决策</span>' +
    '<span class="li"><i style="background:#F0B95A"></i>待决策</span>' +
    '<span class="li"><i style="background:#C9CFD8"></i>Free Layer</span></div>' +
    '<div class="scrollx" id="scDetail" style="padding:8px 10px">' + g + '</div></div>';
  s += '<div class="card"><div class="card-h"><div class="t">' + e + ' · 逐日明细表</div>' +
    '<div class="sub">仅列出窗口内有负载的日期</div>' +
    '<div class="right"><button class="btn sm" data-csv="detail">导出 CSV</button></div></div>' +
    '<div class="tscroll" style="max-height:520px"><table class="dt"><thead><tr>' +
    '<th>日期</th><th>已绑定</th><th>本次决策</th><th>待决策</th><th>Free Layer</th><th>当日合计</th><th>新起段</th><th>当日全场最大</th></tr></thead><tbody>';
  rows.forEach(function (r) {
    s += '<tr><td class="mono"><b>D' + (r.t + 1) + '</b></td>' +
      '<td class="num">' + n1(r.b) + '</td><td class="num">' + n1(r.d) + '</td>' +
      '<td class="num">' + n1(r.p) + '</td><td class="num">' + n1(r.f) + '</td>' +
      '<td class="num"><b>' + n1(r.tot) + '</b></td><td class="num">' + r.ns + '</td>' +
      '<td class="num">' + n1(r.peak) + '</td></tr>';
  });
  s += '</tbody></table></div></div>';
  return s;
}
/* v6：机台负载图（按天分组柱状图，一屏天数可调，点击柱进入详情标签页） */
function drawLoadChart() {
  const days = winDays();
  const rows = EQPS.map(function (e) {
    const t = eqpStateTotals(e, days);
    return { e: e, b: t.b, d: t.d, p: t.p, f: t.f, tot: t.tot, segs: (SEGS[e] || []).length };
  });
  /* v6：按天分组柱状图 —— X=窗口内每天，每天 6 台机台各一根柱；一屏可见天数由滑块调节；点击柱进入该机台详情 */
  const vis = Math.max(1, Math.min(30, UI.loadZoom || 30));
  const unit = Math.max(24, Math.round(760 / vis));      // 一屏可见 vis 天 → 列宽随缩放
  const bw = Math.max(2.4, unit * 0.11), gap = Math.max(0.8, unit * 0.03), padL = Math.max(4, unit * 0.18);
  const gw = bw * 6 + gap * 5 + padL * 2;
  const W = 52 + days.length * gw + 16, H = 300, PL = 52, PR = 16, PT = 20, PB = 40;
  const plotH = H - PT - PB;
  let mx = 0;
  days.forEach(function (t) { EQPS.forEach(function (e) { if (LOAD[e][t] > mx) mx = LOAD[e][t]; }); });
  mx = Math.ceil(mx * 1.1 / 10) * 10 || 10;
  const Y = function (v) { return PT + plotH - (v / mx) * plotH; };
  let g = '<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '" style="display:block">';
  for (let k = 0; k <= 4; k++) {
    const v = mx * k / 4, y = Y(v);
    g += '<line x1="' + PL + '" y1="' + y + '" x2="' + (W - PR) + '" y2="' + y + '" stroke="#F0F0F0"/>';
    g += '<text x="' + (PL - 6) + '" y="' + (y + 3) + '" fill="#8A94A6" font-size="10" text-anchor="end">' + Math.round(v) + '</text>';
  }
  days.forEach(function (t, i) {
    const gx = PL + i * gw + padL;
    /* 先画当天整列 hover 带（空白处悬停看全部机台明细），柱子后画、在上层可点击 */
    let dayTip = '<b>D' + (t + 1) + ' 各机台当日负载</b>';
    EQPS.forEach(function (e) {
      dayTip += '<span class="row"><span class="k">' + e + '</span><span>' + n1(LOAD[e][t]) + ' pics</span></span>';
    });
    dayTip += '<hr><span class="k">点击柱子进入该机台详情 →</span>';
    g += '<rect x="' + (PL + i * gw) + '" y="' + PT + '" width="' + gw + '" height="' + plotH + '" fill="transparent" data-tip="' + esc(dayTip) + '"/>';
    EQPS.forEach(function (e, j) {
      const v = LOAD[e][t];
      const tipTxt = '<b>' + e + ' · D' + (t + 1) + '</b><br>' +
        '<span class="row"><span class="k">当日负载</span><span>' + n1(v) + ' pics</span></span>' +
        '<span class="row"><span class="k">已绑定 / 决策</span><span>' + n1(LOADB[e][t]) + ' / ' + n1(LOADD[e][t]) + '</span></span>' +
        '<span class="row"><span class="k">待决 / Free（分配）</span><span>' + n1(LOADP[e][t]) + ' / ' + n1(LOADF[e][t]) + '</span></span>' +
        '<hr><span class="k">点击进入机台详情 →</span>';
      if (v > 0) {
        g += '<rect x="' + (gx + j * (bw + gap)) + '" y="' + Y(v) + '" width="' + bw + '" height="' + (PT + plotH - Y(v)) + '" fill="' + (CMP_COLORS[e] || "#333") + '" rx="1"/>';
      }
      /* 点击热区（含 v=0 时也可点入详情） */
      g += '<rect x="' + (gx + j * (bw + gap) - 1) + '" y="' + PT + '" width="' + (bw + 2) + '" height="' + plotH + '" fill="transparent" data-eqp="' + e + '" style="cursor:pointer" data-tip="' + esc(tipTxt) + '"/>';
    });
    if (gw >= 26 || i % 2 === 0) g += '<text x="' + (gx + bw * 3 + gap * 2.5) + '" y="' + (H - 22) + '" fill="#8A94A6" font-size="9.5" text-anchor="middle">D' + (t + 1) + '</text>';
  });
  g += '</svg>';
  return g;
}
function loadChartCard() {
  const days = winDays();
  const rows = EQPS.map(function (e) {
    const t = eqpStateTotals(e, days);
    return { e: e, b: t.b, d: t.d, p: t.p, f: t.f, tot: t.tot, segs: (SEGS[e] || []).length };
  });
  let g = drawLoadChart();
  let s = '<div class="toolbar"><label class="note">一屏可见天数</label>' +
    '<input type="range" min="1" max="30" value="' + (UI.loadZoom || 30) + '" data-act="loadZoom" style="width:220px">' +
    '<b id="loadZoomLbl" style="font-size:13px">' + (UI.loadZoom || 30) + '</b><span class="note">天</span>' +
    '<div class="sp"></div><span class="note">机台负载对比：X 轴 = 筛选窗口内每天，每天 6 根柱 = 6 台机台当日负载；<b>点击柱子进入该机台详情</b>。</span></div>';
  s += '<div class="scrollx" id="scLoadCht" style="padding:8px 10px">' + g + '</div>';
  s += '<div class="legend">' +
    EQPS.map(function (e) { return '<span class="li"><i style="background:' + (CMP_COLORS[e] || "#333") + '"></i>' + e + '</span>'; }).join("") +
    '</div>';
  s += '<div class="tscroll" style="margin-top:14px;max-height:none"><table class="dt"><thead><tr>' +
    '<th>机台</th><th>已绑定</th><th>本次决策</th><th>待决策</th><th>Free Layer</th>' +
    '<th>合计（pics）</th><th>承接段数</th><th>日均（pics·天）</th><th>峰值（pics）</th><th>操作</th></tr></thead><tbody>';
  rows.forEach(function (r) {
    s += '<tr><td><b>' + r.e + '</b></td><td class="num">' + n1(r.b) + '</td><td class="num">' + n1(r.d) + '</td>' +
      '<td class="num">' + n1(r.p) + '</td><td class="num">' + n1(r.f) + '</td>' +
      '<td class="num"><b>' + n1(r.tot) + '</b></td><td class="num">' + r.segs + '</td>' +
      '<td class="num">' + n1(r.tot / (days.length || 1)) + '</td><td class="num">' + n1(MET.per[r.e].mx) + '</td>' +
      '<td><button class="btn sm" data-eqp="' + r.e + '">查看逐日明细</button></td></tr>';
  });
  s += '</tbody></table></div>';
  return s;
}
/* v4：日负载矩阵「日期列头」箱型图 + 数据对比折线图（仅新增，不改现有功能） */
function dayBoxTip(t) {
  const vals = EQPS.map(function (e) { return LOAD[e][t]; });
  const mn = Math.min.apply(null, vals), mx = Math.max.apply(null, vals);
  const srt = EQPS.map(function (e, i) { return { e: e, v: vals[i] }; }).sort(function (a, b) { return a.v - b.v; });
  const q = function (p) { const id = (srt.length - 1) * p, lo = Math.floor(id), hi = Math.ceil(id); return lo === hi ? srt[lo].v : srt[lo].v + (srt[hi].v - srt[lo].v) * (id - lo); };
  const q1 = q(0.25), med = q(0.5), q3 = q(0.75);
  const mean = vals.reduce(function (a, b) { return a + b; }, 0) / vals.length;
  const eqOf = function (v) { return srt.filter(function (o) { return Math.abs(o.v - v) < 1e-9; }).map(function (o) { return o.e; }); };
  const fmtEq = function (arr) { return arr.join(",") + (arr.length > 1 ? " (" + arr.length + " 台)" : ""); };
  return '<b>D' + (t + 1) + ' 各机台负载分布</b>' +
    dayBoxSvg(t, mn, q1, med, q3, mx, srt) +
    '<span class="row"><span class="k">min / max</span><span>' + n1(mn) + ' / ' + n1(mx) + ' pics</span></span>' +
    '<span class="row"><span class="k">中位 / 均值</span><span>' + n1(med) + ' / ' + n1(mean) + ' pics</span></span>' +
    '<span class="row"><span class="k">最高 / 最低</span><span>' + fmtEq(eqOf(mx)) + ' / ' + fmtEq(eqOf(mn)) + '</span></span>';
}
function dayBoxSvg(t, mn, q1, med, q3, mx, srt) {
  const W = 224, H = 100, L = 10, R = W - 10, PW = R - L;
  const amax = Math.max(mx * 1.12, 1);
  const X = function (v) { return L + (v / amax) * PW; };
  let s = '<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '" style="display:block;margin:4px 0">';
  s += '<line x1="' + L + '" y1="62" x2="' + R + '" y2="62" stroke="rgba(255,255,255,.35)" stroke-width="1"/>';
  s += '<line x1="' + X(mn) + '" y1="30" x2="' + X(mx) + '" y2="30" stroke="rgba(255,255,255,.6)" stroke-width="1"/>';
  s += '<line x1="' + X(mn) + '" y1="24" x2="' + X(mn) + '" y2="36" stroke="rgba(255,255,255,.6)" stroke-width="1"/>';
  s += '<line x1="' + X(mx) + '" y1="24" x2="' + X(mx) + '" y2="36" stroke="rgba(255,255,255,.6)" stroke-width="1"/>';
  s += '<rect x="' + X(q1) + '" y="21" width="' + (X(q3) - X(q1)) + '" height="18" fill="rgba(255,217,122,.22)" stroke="#FFD97A" stroke-width="1"/>';
  s += '<line x1="' + X(med) + '" y1="21" x2="' + X(med) + '" y2="39" stroke="#FFD97A" stroke-width="2"/>';
  /* v4.2：按负载值分组，同值机台合并为逗号标签，避免重叠遮挡 */
  const groups = [];
  srt.forEach(function (o) {
    const g = groups[groups.length - 1];
    if (g && Math.abs(g.v - o.v) < 1e-9) g.eqps.push(o.e);
    else groups.push({ v: o.v, eqps: [o.e] });
  });
  const same = Math.abs(mx - mn) < 1e-9;
  const labels = [];
  groups.forEach(function (g) {
    const px = X(g.v);
    const isMax = Math.abs(g.v - mx) < 1e-9;
    let txt = g.eqps.join(",");
    if (!same && isMax && g.eqps.length > 1) txt += " (最高)";
    const r = 3.4 + Math.min(2.4, (g.eqps.length - 1) * 0.9);
    s += '<circle cx="' + px + '" cy="64" r="' + r.toFixed(1) + '" fill="' + (CMP_COLORS[g.eqps[0]] || "#fff") + '"/>';
    labels.push({ px: px, txt: txt });
  });
  /* 两行交错错开：默认第 1 行，与上一标签会碰撞时切到第 2 行 */
  const rowRight = [-1e9, -1e9];
  labels.forEach(function (lb) {
    const w = lb.txt.length * 4.7 + (lb.txt.indexOf("(") >= 0 ? 8 : 0);
    const left = lb.px - w / 2;
    let row = 0;
    if (left - rowRight[0] < 3) row = 1;
    const anchor = lb.px < 30 ? "start" : (lb.px > W - 30 ? "end" : "middle");
    const y = row === 0 ? 80 : 90;
    s += '<text x="' + lb.px + '" y="' + y + '" fill="#cdd8ea" font-size="8" text-anchor="' + anchor + '">' + lb.txt + '</text>';
    rowRight[row] = lb.px + w / 2;
  });
  s += '</svg>';
  return s;
}
function poly(days, fv, X, Y, color, w, dashed) {
  let d = "";
  days.forEach(function (t, i) { d += (i === 0 ? "M" : "L") + X(i) + " " + Y(fv(t)) + " "; });
  return '<path d="' + d.trim() + '" fill="none" stroke="' + color + '" stroke-width="' + w + '"' + (dashed ? ' stroke-dasharray="4 3"' : "") + '/>';
}
function cmpPanel() {
  const wlab = UI.win === "all" ? "全部 D1–" + DAYS : ({ "1": "D1–30", "2": "D31–60", "3": "D61–90", "4": "D91–120" })[UI.win];
  let s = '<div class="card"><h3>各机台负载对比 · 窗口：' + esc(wlab) + '</h3>' +
    '<p class="desc">X 轴=窗口内天数，Y 轴=每日 Stacking Bond 负载 pics；每条线=一台机台（E1~E6），红色=全场当日峰值 dailyPeak，灰色虚线=当日各机台均值。下方滑块调整一屏可见天数，超出则横向滚动。</p>' +
    '<div style="display:flex;align-items:center;gap:12px;margin:4px 0 8px">' +
    '<label class="lab" style="margin:0">一屏可见天数</label>' +
    '<input type="range" min="1" max="30" value="' + UI.cmpZoom + '" data-act="cmpZoom" style="width:220px">' +
    '<b id="cmpZoomLbl" style="color:#2F4368">' + UI.cmpZoom + '</b>' +
    '<span class="note" style="margin:0">天</span></div>' +
    '<div class="scrollx" id="scCmp" style="border:1px solid var(--line);border-radius:8px;padding:6px 8px;background:#fff">' +
    drawCmpChart() + '</div>' +
    '<div class="note" style="margin-top:6px">提示：缩放滑块滑动时仅重绘此图，不刷新上方矩阵。</div></div>';
  return s;
}
function drawCmpChart() {
  const a = UI.win === "all" ? 0 : (parseInt(UI.win, 10) - 1) * 30;
  const b = UI.win === "all" ? DAYS - 1 : a + 29;
  const days = []; for (let t = a; t <= b && t < DAYS; t++) days.push(t);
  const nd = days.length;
  const vis = Math.max(1, Math.min(30, UI.cmpZoom));
  const VPW = 760;
  const ppd = Math.max(10, Math.min(760, Math.round(VPW / vis)));
  const W = nd * ppd, H = 320, PL = 46, PR = 14, PT = 16, PB = 28;
  const plotW = W - PL - PR, plotH = H - PT - PB;
  let maxY = 0;
  days.forEach(function (t) { EQPS.forEach(function (e) { if (LOAD[e][t] > maxY) maxY = LOAD[e][t]; }); if (MET.dailyPeak[t] > maxY) maxY = MET.dailyPeak[t]; });
  maxY = Math.ceil(maxY * 1.08 / 10) * 10 || 10;
  const Y = function (v) { return PT + plotH - (v / maxY) * plotH; };
  const X = function (i) { return PL + (nd === 1 ? plotW / 2 : i * ppd); };
  let s = '<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '" style="display:block">';
  for (let k = 0; k <= 5; k++) {
    const v = maxY * k / 5, y = Y(v);
    s += '<line x1="' + PL + '" y1="' + y + '" x2="' + (W - PR) + '" y2="' + y + '" stroke="#EDF1F8" stroke-width="1"/>';
    s += '<text x="' + (PL - 6) + '" y="' + (y + 3) + '" fill="#8A94A6" font-size="10" text-anchor="end">' + Math.round(v) + '</text>';
  }
  const step = ppd >= 18 ? 1 : (ppd >= 9 ? 5 : 10);
  days.forEach(function (t, i) {
    if (i % step === 0 || i === nd - 1) s += '<text x="' + X(i) + '" y="' + (H - 8) + '" fill="#8A94A6" font-size="10" text-anchor="middle">D' + (t + 1) + '</text>';
  });
  const meanOf = function (t) { let s2 = 0; EQPS.forEach(function (e) { s2 += LOAD[e][t]; }); return s2 / EQPS.length; };
  s += poly(days, function (t) { return MET.dailyPeak[t]; }, X, Y, "#E5484D", 2, false);
  s += poly(days, meanOf, X, Y, "#8A94A6", 1.5, true);
  EQPS.forEach(function (e) { s += poly(days, function (t) { return LOAD[e][t]; }, X, Y, CMP_COLORS[e] || "#333", 1.6, false); });
  /* v4.1：按天 hover 带 + 明细 tooltip（鼠标移入该天列即展示各机台负载明细） */
  days.forEach(function (t, i) {
    let tip = '<div style="font-weight:600;margin-bottom:4px">第 ' + (t + 1) + ' 天 · D' + (t + 1) + '</div>'
      + '<div class="row"><span class="k">机台</span><span>负载 / 已绑 / 决策</span></div>';
    EQPS.forEach(function (e) {
      tip += '<div class="row"><span><b style="color:' + (CMP_COLORS[e] || '#fff') + '">' + e + '</b></span>'
        + '<span>' + n1(LOAD[e][t]) + ' / ' + n1(LOADB[e][t]) + ' / ' + n1(LOADD[e][t]) + '</span></div>';
    });
    tip += '<hr>'
      + '<div class="row"><span class="k">全场当日峰值</span><span>' + n1(MET.dailyPeak[t]) + ' pics</span></div>'
      + '<div class="row"><span class="k">当日机台均值</span><span>' + n1(meanOf(t)) + ' pics</span></div>';
    const x0 = X(i) - ppd / 2;
    s += '<rect x="' + x0 + '" y="' + PT + '" width="' + ppd + '" height="' + plotH + '" fill="transparent" pointer-events="all" data-tip="' + esc(tip) + '"/>';
  });
  let lx = PL;
  EQPS.forEach(function (e) {
    s += '<rect x="' + lx + '" y="6" width="10" height="3" fill="' + (CMP_COLORS[e] || "#333") + '"/>';
    s += '<text x="' + (lx + 14) + '" y="10" fill="#5A6B85" font-size="10">' + e + '</text>';
    lx += 44;
  });
  s += '<rect x="' + lx + '" y="6" width="10" height="3" fill="#E5484D"/>';
  s += '<text x="' + (lx + 14) + '" y="10" fill="#5A6B85" font-size="10">峰值</text>';
  lx += 44;
  s += '<line x1="' + lx + '" y1="7" x2="' + (lx + 12) + '" y2="7" stroke="#8A94A6" stroke-width="1.5" stroke-dasharray="3 2"/>';
  s += '<text x="' + (lx + 16) + '" y="10" fill="#5A6B85" font-size="10">均值</text>';
  s += '</svg>';
  return s;
}