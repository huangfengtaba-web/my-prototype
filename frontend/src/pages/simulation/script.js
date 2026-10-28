// 仿真验证页逻辑：POST /api/sim/run → KPI + 计划/实际双轨甘特 + Lot 明细
import { API_BASE, $, mountShell, toMin, fmtMin } from '../_shared/shell.js'

mountShell('simulation')

async function init() {
  try {
    const res = await fetch(`${API_BASE}/api/cases`)
    const { cases } = await res.json()
    $('#caseSel').innerHTML = '<option value="">基线</option>' +
      (cases || []).map((c) => `<option value="${c}">${c}</option>`).join('')
  } catch {
    $('#runState').textContent = '后端不可达：先跑 uvicorn backend.app.api:app'
    $('#runState').className = 'run-state err'
  }
  $('#runBtn').addEventListener('click', runSim)
}

async function runSim() {
  const btn = $('#runBtn')
  btn.disabled = true
  $('#runState').textContent = '求解 + 仿真中…'
  $('#runState').className = 'run-state'
  try {
    const res = await fetch(`${API_BASE}/api/sim/run`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        case: $('#caseSel').value || null,
        seed: Number($('#seed').value) || 42,
        breakdown: $('#breakdown').checked,
      }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status} ${(await res.json()).detail || ''}`)
    const data = await res.json()
    render(data.sim)
    $('#runState').textContent = `完成 · solve_run_id=${data.solve_run_id}`
    $('#runState').className = 'run-state ok'
  } catch (err) {
    $('#runState').textContent = `失败：${err.message}`
    $('#runState').className = 'run-state err'
  } finally {
    btn.disabled = false
  }
}

function render(sim) {
  const k = sim.kpis
  $('#kOnTime').textContent = `${(k.on_time_rate * 100).toFixed(0)}%`
  $('#kOnTime').className = 'k-v ' + (k.on_time_rate >= 0.8 ? 'ok' : k.on_time_rate >= 0.5 ? 'warn' : 'err')
  $('#kSpan').textContent = `${k.makespan_actual}`
  $('#kDelta').textContent = `${k.makespan_delta_min > 0 ? '+' : ''}${k.makespan_delta_min}min`
  $('#kDelta').className = 'k-v ' + (k.makespan_delta_min <= 15 ? 'ok' : 'err')
  $('#kAvg').textContent = `${k.avg_delay_min}min`
  $('#kDist').textContent = `${k.breakdowns} / ${k.rework_count} / ${k.qtime_violations}`

  renderGantt(sim.lots)
  $('#tbl tbody').innerHTML = sim.lots.map((r) => `<tr>
    <td><b>${r.lot}</b></td><td>${r.eqp}</td><td>${r.reticle}</td>
    <td>${r.planned_start}</td><td>${r.planned_end}</td>
    <td>${r.actual_start}</td><td>${r.actual_end}</td>
    <td><span class="tag ${r.on_time ? 'success' : 'error'}">${r.delay_min}</span></td>
    <td>${r.qtime_breach ? '<span class="tag error">违约</span>' : '<span class="tag success">OK</span>'}</td>
    <td>${r.note}</td></tr>`).join('')
}

// 每机台一行，行内两条子轨道：上=计划（描边） 下=实际（实色，延误标红）
function renderGantt(lots) {
  const pts = lots.flatMap((r) => [r.planned_start_m, r.planned_end_m, r.actual_start_m, r.actual_end_m])
  const t0 = Math.min(...pts), t1 = Math.max(...pts), span = Math.max(t1 - t0, 1)
  const byEqp = {}
  for (const r of lots) (byEqp[r.eqp] ||= []).push(r)

  let html = `<div class="gantt"><div class="g-ruler">`
  for (let m = Math.ceil(t0 / 60) * 60; m <= t1; m += 60)
    html += `<span style="left:${((m - t0) / span) * 100}%">${fmtMin(m)}</span>`
  html += `</div>`
  for (const eqp of Object.keys(byEqp).sort()) {
    html += `<div class="g-row"><div class="g-name">${eqp}</div><div class="g-track">
      <div class="g-sub plan"></div><div class="g-sub act"></div></div></div>`
  }
  html += `</div>`
  $('#gantt').innerHTML = html

  const rows = document.querySelectorAll('#gantt .g-row')
  for (const eqp of Object.keys(byEqp)) {
    const row = [...rows].find((r) => r.querySelector('.g-name').textContent === eqp)
    const planSub = row.querySelector('.g-sub.plan'), actSub = row.querySelector('.g-sub.act')
    for (const r of byEqp[eqp]) {
      const seg = (sub, cls, s, e, label) => {
        const left = ((s - t0) / span) * 100, width = Math.max(((e - s) / span) * 100, 1)
        sub.insertAdjacentHTML('beforeend',
          `<div class="g-seg ${cls}" style="left:${left}%;width:${width}%" title="${label}">${label}</div>`)
      }
      seg(planSub, 'plan', r.planned_start_m, r.planned_end_m,
        `${r.lot} 计划 ${r.planned_start}~${r.planned_end}`)
      seg(actSub, r.on_time ? 'act' : 'act late', r.actual_start_m, r.actual_end_m,
        `${r.lot} 实际 ${r.actual_start}~${r.actual_end}（延误 ${r.delay_min}min）${r.note}`)
    }
  }
  $('#ganttEmpty').style.display = 'none'
}

init()
