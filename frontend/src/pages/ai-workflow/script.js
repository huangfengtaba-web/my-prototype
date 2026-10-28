// AI 工作流页逻辑：选模板 → POST /api/workflow/run → 轮询 status → 时间线 + 报告
import { API_BASE, $, mountShell, statusTag } from '../_shared/shell.js'

mountShell('ai-workflow')

const state = { templates: [], current: null, timer: null, wfId: null }

async function init() {
  try {
    const [tplRes, caseRes] = await Promise.all([
      fetch(`${API_BASE}/api/workflow/templates`),
      fetch(`${API_BASE}/api/cases`),
    ])
    state.templates = (await tplRes.json()).templates || []
    const cases = (await caseRes.json()).cases || []
    $('#caseSel').innerHTML = '<option value="">基线</option>' +
      cases.map((c) => `<option value="${c}">${c}</option>`).join('')
  } catch {
    $('#tplGrid').innerHTML = '<div class="empty">后端不可达：先跑 uvicorn backend.app.api:app</div>'
    return
  }
  $('#tplGrid').innerHTML = state.templates.map((t, i) => `
    <div class="tpl ${i === 0 ? 'on' : ''}" data-id="${t.id}">
      <div class="t-name">${t.name}</div>
      <div class="t-desc">${t.desc}</div>
      <div class="t-params">参数：${JSON.stringify(t.params)}</div>
    </div>`).join('')
  state.current = state.templates[0]?.id
  document.querySelectorAll('.tpl').forEach((el) =>
    el.addEventListener('click', () => {
      document.querySelectorAll('.tpl').forEach((x) => x.classList.remove('on'))
      el.classList.add('on')
      state.current = el.dataset.id
    }))
  $('#runBtn').addEventListener('click', runWorkflow)
}

async function runWorkflow() {
  const t = state.templates.find((x) => x.id === state.current)
  const params = {}
  if (state.current === 'daily-scheduling' && $('#caseSel').value) params.case = $('#caseSel').value
  if (state.current === 'daily-scheduling') params.seed = Number($('#seed').value) || 42
  $('#runBtn').disabled = true
  $('#runState').textContent = '启动中…'
  $('#runState').className = 'run-state'
  clearInterval(state.timer)
  try {
    const res = await fetch(`${API_BASE}/api/workflow/run`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template: state.current, params }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const wf = await res.json()
    state.wfId = wf.wf_id
    $('#runState').textContent = `运行中 wf_id=${wf.wf_id}`
    poll()                                            // 立即刷一次
    state.timer = setInterval(poll, 1200)
  } catch (err) {
    $('#runState').textContent = `启动失败：${err.message}`
    $('#runState').className = 'run-state err'
    $('#runBtn').disabled = false
  }
}

async function poll() {
  try {
    const res = await fetch(`${API_BASE}/api/workflow/status/${state.wfId}`)
    const wf = await res.json()
    render(wf)
    if (wf.status === 'done' || wf.status === 'failed') {
      clearInterval(state.timer)
      $('#runBtn').disabled = false
      $('#runState').textContent = `结束：${wf.status}${wf.error ? '（' + wf.error + '）' : ''}`
      $('#runState').className = 'run-state ' + (wf.status === 'done' ? 'ok' : 'err')
    }
  } catch { /* 轮询失败下次再试 */ }
}

function render(wf) {
  $('#wfMeta').textContent = `${wf.template_name} · wf_id=${wf.wf_id} · 状态 ${wf.status}`
  $('#steps').innerHTML = (wf.steps || []).map((s) => `
    <div class="step ${s.status}">
      <div class="s-rail"><div class="s-dot"></div></div>
      <div class="s-main">
        <div class="s-name">${s.name}
          ${statusTag(s.status)} ${s.seconds != null ? `· ${s.seconds}s` : ''} ${s.started_at}</div>
        ${s.output ? `<div class="s-out">${JSON.stringify(s.output, null, 1)}</div>` : ''}
        ${s.error ? `<div class="s-out s-err">${s.error}</div>` : ''}
      </div>
    </div>`).join('') || '<div class="empty">等待步骤启动…</div>'

  const reportStep = (wf.steps || []).find((s) => s.id === 'report' && s.status === 'done')
  if (reportStep?.output?.markdown) {
    $('#report').textContent = reportStep.output.markdown
    $('#reportCard').style.display = ''
  } else if (wf.status === 'done') {
    $('#reportCard').style.display = ''
    $('#report').textContent = '（本模板无报告步骤）'
  }
}

init()
