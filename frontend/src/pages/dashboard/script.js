// 系统总览（真后端）：状态 pills + 真实数据 KPI + 最近求解批次
import { API_BASE, $, mountShell, statusTag } from '../_shared/shell.js'

mountShell('dashboard')

async function init() {
  tickClocks()
  await Promise.all([loadStatus(), loadKpis(), loadRuns()])
}

function tickClocks() {
  const tick = () => { const el = $('#clock'); if (el) el.textContent = new Date().toLocaleString('zh-CN', { hour12: false }) }
  tick(); setInterval(tick, 1000)
}

function pill(label, cls) {
  return `<span class="status-pill ${cls || ''}"><span class="dot"></span>${label}</span>`
}

async function loadStatus() {
  const row = $('#statusRow')
  try {
    const [health, tpl] = await Promise.all([
      fetch(`${API_BASE}/api/health`).then((r) => r.json()),
      fetch(`${API_BASE}/api/workflow/templates`).then((r) => r.json()).catch(() => null),
    ])
    const difyOn = (tpl?.templates || []).some((t) => t.dify_configured)
    row.innerHTML =
      pill(`后端运行中 · v${health.version || '?'}`, 'ok') +
      pill(`求解器 ${health.solver || 'CBC'}`, 'ok') +
      pill(`Agent：${health.agent_mode === 'llm' ? 'LLM 自主决策' : '规则模式'}`,
        health.agent_mode === 'llm' ? 'ok' : 'warn') +
      pill(`Dify 线上工作流：${difyOn ? '已配置' : '未配置（本地降级）'}`, difyOn ? 'ok' : 'warn') +
      pill(`文档生成：${health.docgen_enabled ? '启用（WPS COM）' : '停用'}`,
        health.docgen_enabled ? 'ok' : 'warn')
  } catch (e) {
    row.innerHTML = pill('后端不可达：uvicorn backend.app.api:app', 'err')
  }
}

async function loadKpis() {
  try {
    const d = await (await fetch(`${API_BASE}/api/mock/data`)).json()
    const eqps = Object.keys(d.machines || {})
    const lots = d.lots || []
    const rets = Object.keys(d.reticles || {})
    const over = lots.filter((l) => l.qtms_over)
    $('#kEqp').textContent = eqps.length
    $('#kEqp').title = eqps.join(' · ')
    $('#kLot').textContent = lots.length
    $('#kRet').textContent = rets.length
    const el = $('#kQtms')
    el.textContent = over.length
    el.className = 'k-v ' + (over.length ? 'err' : 'ok')
  } catch { /* 后端未起：保持 — */ }
}

async function loadRuns() {
  try {
    const { runs } = await (await fetch(`${API_BASE}/api/solve/list`)).json()
    $('#runTbl tbody').innerHTML = (runs || []).slice(0, 10).map((r) => `<tr>
      <td><b>${r.run_id}</b></td><td>${r.case || '基线'}</td>
      <td>${r.milp ? `${r.milp.step2} / ${r.milp.step3}` : '—'}</td>
      <td>${r.lots ?? '-'}</td><td>${r.started_at || ''}</td>
      <td>${statusTag(r.status)}</td>
      <td><a href="/litho-schedule">查看 ›</a></td></tr>`).join('')
      || '<tr><td colspan="7" style="color:var(--colorTextQuaternary)">暂无运行，去「求解演示」跑一次</td></tr>'
  } catch { /* ignore */ }
}

init()
