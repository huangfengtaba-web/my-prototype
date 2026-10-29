// 报告生成页：POST /api/doc/render → 轮询 /api/doc/status/{job} → /api/doc/file/{job} 下载
import { API_BASE, $, mountShell, statusTag } from '../_shared/shell.js'

mountShell('reports')

function row(kind) {
  return document.querySelector(`[data-row="${kind}"]`)
}

function notice(msg) {
  const el = $('#notice')
  if (!msg) return el.classList.remove('show')
  el.textContent = msg
  el.classList.add('show')
}

async function generate(kind, name) {
  notice('')
  row(kind).innerHTML = '<span class="tag processing">提交中…</span>'
  try {
    const res = await fetch(`${API_BASE}/api/doc/render`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kind, filename: name }),
    })
    if (res.status === 503) {
      const d = (await res.json()).detail || ''
      row(kind).innerHTML = '<span class="tag default">未启用</span>'
      return notice(`当前环境未启用文档生成（${d}）。本地把 .env 的 DOCGEN_ENABLED 设 1 并重启后端。`)
    }
    if (!res.ok) throw new Error(`HTTP ${res.status} ${(await res.json()).detail || ''}`)
    const { job_id: job } = await res.json()
    poll(job, kind)
  } catch (err) {
    row(kind).innerHTML = `<span class="tag error">失败</span> ${err.message}`
  }
}

function poll(job, kind, tries = 0) {
  row(kind).innerHTML = `<span class="tag processing">生成中…</span> job=${job.slice(0, 8)}`
  if (tries > 60) return row(kind).innerHTML = '<span class="tag error">超时</span>'
  setTimeout(async () => {
    try {
      const st = await (await fetch(`${API_BASE}/api/doc/status/${job}`)).json()
      if (st.status === 'done') {
        row(kind).innerHTML =
          `<span class="tag success">完成</span> <a href="${API_BASE}/api/doc/file/${job}">下载 ⬇</a>`
        return
      }
      if (st.status === 'failed') {
        return row(kind).innerHTML =
          `<span class="tag error">失败</span> <span title="${st.err || ''}">${(st.err || '').slice(0, 60)}</span>`
      }
      poll(job, kind, tries + 1)
    } catch (err) {
      row(kind).innerHTML = `<span class="tag error">状态查询失败</span> ${err.message}`
    }
  }, 1500)
}

document.querySelectorAll('[data-kind]').forEach((btn) =>
  btn.addEventListener('click', () => generate(btn.dataset.kind, btn.dataset.name)))
