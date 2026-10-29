// Litho 排程结果页（真数据）：批次选择 → run_summary → KPI/甘特/明细/六步时间线
import { API_BASE, $, mountShell, seqGantt, statusTag, toMin, fmtMin } from '../_shared/shell.js'

mountShell('litho-schedule')

async function init() {
  try {
    const cases = (await (await fetch(`${API_BASE}/api/cases`)).json()).cases || []
    $('#caseSel').innerHTML = '<option value="">Scenario: 基线</option>' +
      cases.map((c) => `<option value="${c}">Scenario: ${c}</option>`).join('')
    await refreshRuns()
  } catch {
    $('#runSel').innerHTML = '<option value="">后端不可达</option>'
  }
  $('#runSel').addEventListener('change', () => renderRun($('#runSel').value))
  $('#resolveBtn').addEventListener('click', resolveNow)
  $('#csvBtn').addEventListener('click', exportCSV)
}

async function refreshRuns(preferId) {
  const { runs } = await (await fetch(`${API_BASE}/api/solve/list`)).json()
  if (!runs.length) {
    $('#runSel').innerHTML = '<option value="">（暂无运行，先点「重新求解」）</option>'
    return
  }
  $('#runSel').innerHTML = runs.map((r) =>
    `<option value="${r.run_id}">${r.run_id} · ${r.case || '基线'} · ${r.started_at || ''} · ${r.status}</option>`).join('')
  $('#runSel').value = (preferId && runs.some((r) => r.run_id === preferId))
    ? preferId : runs[0].run_id
  renderRun($('#runSel').value)
}

async function resolveNow() {
  const btn = $('#resolveBtn')
  btn.disabled = true
  $('#runMeta').textContent = '求解中…（六步 MILP 约 3~5s）'
  try {
    const res = await fetch(`${API_BASE}/api/solve/run`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case: $('#caseSel').value || null }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const { run_id: runId } = await res.json()
    await refreshRuns(runId)
  } catch (e) {
    $('#runMeta').textContent = `失败：${e.message}`
  } finally {
    btn.disabled = false
  }
}

async function renderRun(runId) {
  if (!runId) return
  const rec = await (await fetch(`${API_BASE}/api/solve/result/${runId}`)).json()
  const s = rec.summary || {}
  const milp = s.milp_status || {}
  const sched = s.schedule || []

  $('#runMeta').textContent =
    `run_id=${rec.run_id} · case=${rec.case || '基线'} · ${rec.started_at || ''}`
  $('#kMilp').textContent = `${milp.step2 || '-'} / ${milp.step3 || '-'}`
  $('#kMilp').className = 'k-v ' + (milp.step2 === 'Optimal' && milp.step3 === 'Optimal' ? 'ok' : 'err')
  const ends = sched.map((r) => toMin(r.end)).filter((v) => v != null)
  $('#kSpan').textContent = ends.length ? fmtMin(Math.max(...ends)) : '—'
  $('#kLots').textContent = sched.filter((r) => r.start).length
  const a01 = sched.find((r) => r.lot === 'LOT-A01')
  $('#kUrgent').textContent = a01?.start || '—'

  // 六步执行时间线
  $('#stepsLine').innerHTML = (s.steps || []).map((st) => `
    <span class="stepchip"><b>${st.name}</b>${st.detail || ''}
      <span class="st">${statusTag(st.status === '完成' ? 'done' : st.status)} ${st.seconds}s</span></span>`).join('')

  // 机台甘特（急货 PRI1 标红）
  const byEqp = {}
  for (const r of sched) {
    if (!r.eqp || !r.start) continue
    ;(byEqp[r.eqp] ||= []).push(r)
  }
  const rows = Object.keys(byEqp).sort().map((eqp) => ({
    name: eqp,
    segs: byEqp[eqp].map((r) => ({
      s: toMin(r.start), e: toMin(r.end),
      label: r.lot,
      color: r.priority === 'PRI1' ? 'var(--colorError)' : 'var(--colorPrimary)',
      tip: `${r.lot} · ${r.reticle} · ${r.priority} · ${r.start}~${r.end}`,
    })),
  }))
  $('#gantt').innerHTML = rows.length ? seqGantt(rows) : '<div class="empty">无排程</div>'

  // 明细表
  $('#tbl tbody').innerHTML = sched.map((r) => `<tr>
    <td><b>${r.lot}</b></td><td>${r.eqp || '—'}</td><td>${r.eqp_group || '—'}</td>
    <td>${r.reticle}</td>
    <td><span class="tag ${r.priority === 'PRI1' ? 'error' : 'default'}">${r.priority}</span></td>
    <td>${r.temp}</td><td>${r.start || '—'}</td><td>${r.end || '—'}</td>
    <td>${r.barc_er || '—'}</td><td>${r.barc_lr || '—'}</td><td>${r.post_note || '-'}</td>
  </tr>`).join('')
}

function exportCSV() {
  const rows = [['LotId', 'Eqp', 'EqpGroup', 'Reticle', 'Priority', 'Temp', 'Start', 'End', 'BarcER', 'BarcLR', 'Note']]
  document.querySelectorAll('#tbl tbody tr').forEach((tr) =>
    rows.push([...tr.children].map((td) => td.textContent.trim())))
  const csv = '\ufeff' + rows.map((r) => r.map((v) => `"${v}"`).join(',')).join('\n')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
  a.download = 'litho-schedule.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

init()
