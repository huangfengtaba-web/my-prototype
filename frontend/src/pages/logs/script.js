// 系统日志页（真数据）：GET /api/logs → Scheduling Log + Error Management
import { API_BASE, $, mountShell, statusTag } from '../_shared/shell.js'

mountShell('logs')

async function init() {
  try {
    const { schedulings, errors } = await (await fetch(`${API_BASE}/api/logs`)).json()
    $('#logTbl tbody').innerHTML = (schedulings || []).map((s) => {
      const cls = s.status === 'done' ? 'success'
        : s.status === 'suboptimal' ? 'warning' : 'error'
      return `<tr><td>${s.model}</td><td>${s.version}</td><td><b>${s.run_id}</b></td>
        <td>${s.case || '基线'}</td>
        <td><span class="tag ${cls}">${s.status}</span></td><td>${s.start || ''}</td>
        <td>${s.status !== 'done' ? '<a href="#errTbl">View Error</a>' : ''}</td></tr>`
    }).join('') || '<tr><td colspan="7" style="color:var(--colorTextQuaternary)">暂无运行，去「求解演示」跑一次</td></tr>'

    $('#errTbl tbody').innerHTML = (errors || []).map((e) => `<tr>
      <td><b>${e.run_id}</b></td>
      <td><span class="tag error">${e.error_type}</span></td>
      <td>${e.error_info}</td><td>${e.detail || '-'}</td><td>${e.time || ''}</td></tr>`).join('')
    $('#errEmpty').style.display = (errors || []).length ? 'none' : ''
  } catch {
    $('#logTbl tbody').innerHTML =
      '<tr><td colspan="7" style="color:var(--colorError)">后端不可达：uvicorn backend.app.api:app</td></tr>'
  }
}

init()
