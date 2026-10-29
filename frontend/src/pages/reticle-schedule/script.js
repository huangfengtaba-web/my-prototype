// Reticle 排程结果页（真数据）：run_summary → 每枚光罩的 Stocker/Transport/装载/Process 分段甘特
import { API_BASE, $, mountShell, seqGantt, toMin } from '../_shared/shell.js'

mountShell('reticle-schedule')

const C = { process: '#2D6CDF', inspection: '#F5921B', starlight: '#8B5CF6',
  stocker: '#9CA3AF', transport: '#10B981' }

async function init() {
  try {
    await refreshRuns()
  } catch {
    $('#runSel').innerHTML = '<option value="">后端不可达</option>'
  }
  $('#runSel').addEventListener('change', () => renderRun($('#runSel').value))
}

async function refreshRuns(preferId) {
  const { runs } = await (await fetch(`${API_BASE}/api/solve/list`)).json()
  if (!runs.length) {
    $('#runSel').innerHTML = '<option value="">（暂无运行，去求解演示页跑一次）</option>'
    return
  }
  $('#runSel').innerHTML = runs.map((r) =>
    `<option value="${r.run_id}">${r.run_id} · ${r.case || '基线'} · ${r.started_at || ''}</option>`).join('')
  $('#runSel').value = (preferId && runs.some((r) => r.run_id === preferId))
    ? preferId : runs[0].run_id
  renderRun($('#runSel').value)
}

async function renderRun(runId) {
  if (!runId) return
  const rec = await (await fetch(`${API_BASE}/api/solve/result/${runId}`)).json()
  const s = rec.summary || {}
  const sched = (s.schedule || []).filter((r) => r.eqp && r.start && r.end)
  $('#runMeta').textContent = `run_id=${rec.run_id} · case=${rec.case || '基线'}`

  // 每枚光罩的关联 Lot（按开工排序）
  const byRet = {}
  for (const r of sched) (byRet[r.reticle] ||= []).push(r)
  const retMeta = s.reticles || {}

  const rows = []
  for (const [ret, lots] of Object.entries(byRet).sort()) {
    lots.sort((a, b) => toMin(a.start) - toMin(b.start))
    const segs = []
    const firstStart = toMin(lots[0].start)
    const winStart = Math.max(toMin(Object.values(byRet).flat()[0].start) - 300, 0)
    segs.push({ s: winStart, e: Math.max(firstStart - 300, winStart),
      label: 'Stocker', color: C.stocker, tip: `${ret} 储位（就绪 ${retMeta[ret]?.ready || '-'}）` })
    for (const l of lots) {
      const st = toMin(l.start), en = toMin(l.end)
      segs.push({ s: Math.max(st - 300, 0), e: Math.max(st - 60, 0),
        label: '搬送', color: C.transport, tip: `${ret} → ${l.eqp}（OHT 搬送，供 ${l.lot}）` })
      segs.push({ s: Math.max(st - 60, 0), e: st,
        label: '装载', color: C.inspection, tip: `${ret} 在 ${l.eqp} 装载/检测（供 ${l.lot}）` })
      segs.push({ s: st, e: en, label: l.lot, color: C.process,
        tip: `${ret} Process @${l.eqp}（${l.lot}）${l.start}~${l.end}` })
    }
    rows.push({ name: ret, segs })
  }
  // 无需求的的光罩也给一行 Stocker 态
  for (const [ret, m] of Object.entries(retMeta)) {
    if (!byRet[ret]) rows.push({ name: ret, segs: [
      { s: 480, e: 780, label: `Stocker（${m.status}）`, color: C.stocker,
        tip: `${ret} 本 Loop 无需求 · ${m.note || ''}` }] })
  }
  $('#gantt').innerHTML = rows.length ? seqGantt(rows) : '<div class="empty">无数据</div>'

  $('#tbl tbody').innerHTML = Object.entries(retMeta).map(([ret, m]) => {
    const lots = (byRet[ret] || []).map((l) => `${l.lot}@${l.eqp} ${l.start}~${l.end}`).join('；') || '—'
    return `<tr><td><b>${ret}</b></td><td>${m.status || '-'}</td><td>${m.ready || '-'}</td>
      <td>${lots}</td><td>${m.note || '-'}</td></tr>`
  }).join('')
}

init()
