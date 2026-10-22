function segMatch(l, g) {
  return segHitP(l, g) && (UI.stFilter === "all" || g.st === UI.stFilter);
}

/* v5：按当前筛选重算负载矩阵（筛选即时生效，各图表口径一致） */
function recalcByFilter() {
  const L = {}, LB = {}, LD = {}, LP = {}, LF = {}, NS = {}, S = {}, CS = {}, CL = {};
  EQPS.forEach(function (e) {
    L[e] = new Array(DAYS).fill(0); LB[e] = new Array(DAYS).fill(0); LD[e] = new Array(DAYS).fill(0);
    LP[e] = new Array(DAYS).fill(0); LF[e] = new Array(DAYS).fill(0); NS[e] = new Array(DAYS).fill(0);
    S[e] = []; CS[e] = []; CL[e] = new Array(DAYS).fill(0);
  });
  let freePics = 0, pendPics = 0;
  ALLSEGS.forEach(function (x) {
    const l = x.lot, g = x.g, d = x.d, hit = segMatch(l, g);
    if (g.st === "free" || g.st === "pending") {
      if (g.st === "free") { if (hit) freePics += g.pics; }
      else { if (hit) pendPics += g.pics; }
      if (!hit) return;
      /* v6：待决策 / Free 按分配表（mock）全额计入指定机台，不再候选均分 */
      const e = g.eqp; if (!e || !L[e]) return;
      for (let t = d.a; t <= d.b && t < DAYS; t++) {
        if (g.st === "free") LF[e][t] += g.pics; else LP[e][t] += g.pics;
        L[e][t] += g.pics; CL[e][t] += g.pics;
      }
      CS[e].push(x);
      return;
    }
    const e = g.eqp; if (!e || !L[e]) return;
    if (!hit) return;
    for (let t = d.a; t <= d.b && t < DAYS; t++) {
      L[e][t] += g.pics;
      if (g.st === "bound") LB[e][t] += g.pics; else if (g.st === "dec") LD[e][t] += g.pics;
    }
    if (d.a < DAYS) NS[e][d.a]++;
    S[e].push({ lot: l, g: g, d: d });
  });
  EQPS.forEach(function (e) { S[e].sort(function (x, y) { return x.d.a - y.d.a || x.g.idx - y.g.idx; }); });
  const tot = {}; EQPS.forEach(function (e) { tot[e] = L[e].reduce(function (a, b) { return a + b; }, 0); });
  const tv = EQPS.map(function (e) { return tot[e]; });
  const between = stats(tv);
  const per = {}; EQPS.forEach(function (e) { per[e] = stats(L[e]); });
  const dailyPeak = []; for (let t = 0; t < DAYS; t++) dailyPeak.push(Math.max.apply(null, EQPS.map(function (e) { return L[e][t]; })));
  const globalPeak = dailyPeak.length ? Math.max.apply(null, dailyPeak) : 0;
  LOAD = L; LOADB = LB; LOADD = LD; LOADP = LP; LOADF = LF; NSTART = NS;
  SEGS = S; CANDSEGS = CS; CANDL = CL;
  MET = Object.assign({}, MET, { tot: tot, between: between, per: per, dailyPeak: dailyPeak,
    globalPeak: globalPeak, freePics: freePics, pendPics: pendPics });
}

/* v6：机台四态逐日明细（已绑定 / 本次决策 / 待决策 / Free，分配口径） */
function eqpDailyStates(e, days) {
  const rows = [];
  days.forEach(function (t) {
    const b = LOADB[e][t], d = LOADD[e][t], p = LOADP[e][t], f = LOADF[e][t];
    const tot = b + d + p + f;
    if (tot <= 0) return;
    rows.push({ t: t, b: b, d: d, p: p, f: f, tot: tot, ns: NSTART[e][t], peak: MET.dailyPeak[t] });
  });
  return rows;
}
function eqpStateTotals(e, days) {
  let b = 0, d = 0, p = 0, f = 0;
  days.forEach(function (t) { b += LOADB[e][t]; d += LOADD[e][t]; p += LOADP[e][t]; f += LOADF[e][t]; });
  return { b: b, d: d, p: p, f: f, tot: b + d + p + f };
}