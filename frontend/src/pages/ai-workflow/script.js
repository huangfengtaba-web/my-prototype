// AI 工作流页 v2：真实执行链路
// - 本地降级：POST /api/workflow/run 返回完整 record（mode=local_fallback，steps 含真实秒级耗时）
// - Dify 线上：返回 mode=dify + workflow_run_id/elapsed/total_steps/outputs
import { API_BASE, $, mountShell, statusTag } from '../_shared/shell.js'

mountShell('ai-workflow')

const state = { templates: [], current: null }

function setBadge(mode, reason) {
  const el = $('#modeBadge')
  if (mode === 'dify') {
    el.textContent = 'Dify 线上'
    el.className = 'mode-badge dify'
  } else {
    el.textContent = '本地降级'
    el.className = 'mode-badge local_fallback'
    if (reason) el.title = reason
  }
}

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
      <div class="t-name">${t.name}
        <span class="dify-tag ${t.dify_configured ? 'on' : 'off'}">
          ${t.dify_configured ? 'Dify 已配置' : 'Dify 未配置'}</span></div>
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
  $('#guideBtn').addEventListener('click', () => $('#guide').classList.toggle('show'))
}

async function runWorkflow() {
  const t = state.templates.find((x) => x.id === state.current)
  const params = {}
  if (state.current === 'daily-scheduling' && $('#caseSel').value) params.case = $('#caseSel').value
  if (state.current === 'daily-scheduling') params.seed = Number($('#seed').value) || 42
  $('#runBtn').disabled = true
  $('#runState').textContent = '执行中…（本地模式：真实求解+仿真，约 3~5s）'
  $('#runState').className = 'run-state'
  try {
    const res = await fetch(`${API_BASE}/api/workflow/run`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template_id: state.current, params }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status} ${(await res.json()).detail || ''}`)
    const wf = await res.json()
    setBadge(wf.mode, wf.fallback_reason)
    render(wf)
    $('#runState').textContent = `结束：${wf.status || wf.mode}`
    $('#runState').className = 'run-state ' + (wf.status === 'failed' ? 'err' : 'ok')
  } catch (err) {
    $('#runState').textContent = `失败：${err.message}`
    $('#runState').className = 'run-state err'
  } finally {
    $('#runBtn').disabled = false
  }
}

// 本地模式：真实步骤时间线（名称/状态/秒级耗时/输出）
// Dify 模式：workflow_run_id / elapsed / total_steps / outputs 元数据
function render(wf) {
  $('#wfMeta').textContent = wf.mode === 'dify'
    ? `${wf.template_id || ''} · mode=dify · run=${wf.workflow_run_id || '-'} · ${wf.elapsed || '-'}s · 节点 ${wf.total_steps ?? '-'}`
    : `${wf.template_name || ''} · wf_id=${wf.wf_id} · mode=local_fallback`

  if (wf.mode === 'dify') {
    $('#steps').innerHTML = `
      <div class="step done"><div class="s-dot"></div><div>
        <div class="s-name">Dify 工作流执行完成 <span class="tag success">${wf.status || 'finished'}</span> · ${wf.elapsed || '-'}s</div>
        <div class="s-out">${JSON.stringify(wf.outputs || {}, null, 1)}</div></div></div>`
    $('#report').textContent = JSON.stringify(wf.outputs || {}, null, 1)
    $('#reportCard').style.display = ''
    return
  }

  $('#steps').innerHTML = (wf.steps || []).map((s) => `
    <div class="step ${s.status}">
      <div class="s-dot"></div>
      <div>
        <div class="s-name">${s.name}
          ${statusTag(s.status)} ${s.seconds != null ? `· ${s.seconds}s` : ''} ${s.started_at || ''}</div>
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