/* ============================================================
   7. CSV
   ============================================================ */
function toCSV(head, rows) {
  const esc2 = function (v) {
    const s = String(v == null ? "" : v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  return "\ufeff" + head.map(esc2).join(",") + "\n" + rows.map(function (r) { return r.map(esc2).join(","); }).join("\n");
}
function dl(name, text) {
  const blob = new Blob([text], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = name;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
}
function exportCSV(mode) {
  let head, rows, name;
  if (mode === "eqpMatrix") {
    head = ["机台"]; for (let t = 1; t <= DAYS; t++) head.push("D" + t);
    rows = EQPS.map(function (e) { return [e].concat(LOAD[e].map(function (v) { return Math.round(v * 10) / 10; })); });
    name = "EQP日负载矩阵";
  } else if (mode === "eqpSeg") {
    head = ["机台", "Lot", "Group#", "Flow", "Stage", "Step", "起始Layer", "结束Layer", "起始Day", "结束Day", "占天数", "候选机台", "状态", "负载pics"];
    rows = [];
    EQPS.forEach(function (e) { SEGS[e].forEach(function (x) {
      rows.push([e, x.lot.id, x.g.gn, x.g.flow, x.g.stage, x.g.step, x.g.lFrom, x.g.lTo, x.d.a + 1, x.d.b + 1, x.d.span, x.g.cand.join("/"), ST[x.g.st].n, x.g.pics]);
    }); });
    name = "机台承接Group明细";
  } else if (mode === "lotSeg") {
    head = ["Lot", "Product", "总层数", "每层CT", "起始Day", "Group#", "Flow", "Stage", "Step", "起始Layer", "结束Layer", "起始Day", "结束Day", "占天数", "候选机台", "状态", "承接机台", "负载pics"];
    rows = [];
    LOTS.forEach(function (l) { l.groups.forEach(function (g) {
      const d = segDays(l, g);
      rows.push([l.id, l.product, l.layers, l.ct, l.startDay + 1, g.gn, g.flow, g.stage, g.step, g.lFrom, g.lTo, d.a + 1, d.b + 1, d.span,
        g.cand.join("/"), ST[g.st].n, g.eqp || "未分配", g.pics]);
    }); });
    name = "Lot段带明细";
  } else if (mode === "eqpGrp") {
    var GN = maxGn();
    head = ["机台"]; for (var gi = 1; gi <= GN; gi++) head.push("G" + gi);
    head.push("合计pics", "合计段数");
    rows = EQPS.map(function (e) {
      var r = [e], tp = 0, tc = 0;
      for (var gj = 1; gj <= GN; gj++) {
        var p = 0, c = 0;
        SEGS[e].forEach(function (x) { if (x.g.idx === gj) { p += x.g.pics; c++; } });
        r.push(Math.round(p * 10) / 10); tp += p; tc += c;
      }
      r.push(Math.round(tp * 10) / 10, tc);
      return r;
    });
    name = "机台xGroup热力图";
  } else if (mode === "lotGrp") {
    var GN2 = maxGn();
    head = ["Lot", "产品"]; for (var gk = 1; gk <= GN2; gk++) head.push("G" + gk + "机台", "G" + gk + "状态", "G" + gk + "pics");
    rows = LOTS.map(function (l) {
      var r = [l.id, l.product];
      for (var gl = 1; gl <= GN2; gl++) {
        var g2 = null; l.groups.forEach(function (x) { if (x.idx === gl) g2 = x; });
        r.push(g2 ? (g2.eqp || "Free") : "", g2 ? ST[g2.st].n : "", g2 ? g2.pics : "");
      }
      return r;
    });
    name = "LotxGroup分段";
  } else if (mode === "freeList") {
    head = ["Lot", "产品", "Group", "起始Layer", "结束Layer", "起始Day", "结束Day", "占天数", "候选机台", "状态", "负载pics"];
    rows = freeList().map(function (r) {
      return [r.lot, r.product, r.gname, r.lFrom, r.lTo, r.dA, r.dB, r.span, r.cand, r.stN, r.pics];
    });
    name = "待决策FreeLayer清单";
  } else if (mode === "grpOwner") {
    head = ["Group#", "Lot", "Product", "Flow", "Stage", "Step", "起始Layer", "结束Layer", "起始Day", "结束Day", "占天数", "状态", "承接机台", "候选机台", "负载pics"];
    rows = ALLSEGS.map(function (x) {
      return [x.g.gn, x.lot.id, x.lot.product, x.g.flow, x.g.stage, x.g.step, x.g.lFrom, x.g.lTo, x.d.a + 1, x.d.b + 1, x.d.span,
        ST[x.g.st].n, x.g.eqp || "未分配", x.g.cand.join("/"), x.g.pics];
    });
    name = "Group机台归属";
  } else if (mode === "detail") {
    const e = UI.detailEqp || "E1";
    const days = winDays(), rws = eqpDailyStates(e, days);
    head = ["日期", "已绑定", "本次决策", "待决策", "Free Layer", "当日合计", "新起段", "当日全场最大"];
    rows = rws.map(function (r) {
      return ["D" + (r.t + 1), n1(r.b), n1(r.d), n1(r.p), n1(r.f), n1(r.tot), r.ns, n1(r.peak)];
    });
    name = e + "逐日负载明细";
  } else {
    head = ["Lot", "Product", "起始Day", "总层数", "段数", "已绑段", "Free段", "本次决策段", "dec段位置", "dec段机台", "Flow", "Stage", "Step范围", "总负载pics"];
    rows = LOTS.map(function (l) {
      const di = l.groups.findIndex(function (g) { return g.st === "dec"; });
      const dg = di >= 0 ? l.groups[di] : null;
      const flows = [], stages = []; let stMin = 1e9, stMax = 0;
      l.groups.forEach(function (g) {
        if (flows.indexOf(g.flow) < 0) flows.push(g.flow);
        if (stages.indexOf(g.stage) < 0) stages.push(g.stage);
        if (g.step < stMin) stMin = g.step; if (g.step > stMax) stMax = g.step;
      });
      const tot = l.groups.filter(function (g) { return g.st !== "free"; }).reduce(function (a, g) { return a + g.pics; }, 0);
      return [l.id, l.product, l.startDay + 1, l.layers, l.groups.length,
        l.groups.filter(function (g) { return g.st === "bound"; }).length,
        l.groups.filter(function (g) { return g.st === "free"; }).length,
        l.groups.filter(function (g) { return g.st === "dec"; }).length,
        dg ? ("第" + (di + 1) + "/" + l.groups.length + "段 " + (dg.lname || dg.name)) : "—",
        dg ? (dg.eqp || "未分配") : "—",
        flows.join("/"), stages.join("/"), stMin + "-" + stMax, tot];
    });
    name = "Lot汇总";
  }
  dl(name + "_" + DAYS + "天.csv", toCSV(head, rows));
}