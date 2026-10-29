// src/pages/ 共享壳层：侧栏导航 + 表头时钟 + 评论模式 + tooltip
// 用法（页面 index.html 里）：
//   <div class="app"><aside class="sider" id="sider"></aside><div class="main">…（header/content 自定义）</div></div>
//   import { mountShell } from '../_shared/shell.js'
//   mountShell('scheduling-test')   // 传当前页 key 高亮
const NAV = [
  ['系统导航', [
    ['/', '系统总览', 'index'],
    ['/prototypes/data_zone.html', '数据接入', ''],
    ['/prototypes/config_zone.html', '数据配置', ''],
    ['/prototypes/model_zone.html', '模型管理', ''],
    ['/prototypes/result_litho.html', 'Litho 排程', ''],
    ['/prototypes/result_reticle.html', 'Reticle 排程', ''],
    ['/prototypes/log_zone.html', '系统日志', ''],
  ]],
  ['智能应用（真后端）', [
    ['/simulation', '仿真验证', 'simulation'],
    ['/twin', '数字孪生', 'twin'],
    ['/scheduling-test', '求解演示', 'scheduling-test'],
    ['/ai-agent', 'AI 助手', 'ai-agent'],
    ['/ai-workflow', 'AI 工作流', 'ai-workflow'],
    ['/reports', '报告生成', 'reports'],
  ]],
]

export function mountShell(active) {
  const sider = document.getElementById('sider')
  sider.innerHTML = `
    <div class="logo"><b>Pxsemi FSO</b><span>智能生产中心 · 光刻排程</span></div>
    <nav>${NAV.map(([g, links]) => `
      <div class="nav-g">${g}</div>
      ${links.map(([href, label, key]) =>
        `<a href="${href}" class="${key === active ? 'on' : ''}">${label}</a>`).join('')}
    `).join('')}</nav>`

  const clock = document.getElementById('clock')
  if (clock) {
    const tick = () => clock.textContent = new Date().toLocaleString('zh-CN', { hour12: false })
    tick(); setInterval(tick, 1000)
  }
  const cmBtn = document.getElementById('cmBtn')
  if (cmBtn) cmBtn.addEventListener('click', () => document.body.classList.toggle('cm'))

  const tt = document.getElementById('tt')
  if (tt) {
    document.addEventListener('mouseover', (e) => {
      const q = e.target.closest('.q[data-cm]')
      if (!q) return tt.style.display = 'none'
      const r = q.getBoundingClientRect()
      tt.textContent = q.dataset.cm
      tt.style.display = 'block'
      tt.style.left = Math.min(r.left, innerWidth - 340) + 'px'
      tt.style.top = (r.bottom + 6) + 'px'
    })
  }
}

export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
export const $ = (s) => document.querySelector(s)

export function statusTag(st) {
  const map = { done: 'success', failed: 'error', timeout: 'error', running: 'processing',
    pending: 'default', suboptimal: 'warning' }
  return `<span class="tag ${map[st] || 'default'}">${st}</span>`
}

export function toMin(hm) {
  if (!hm) return null
  const [h, m] = String(hm).split(':').map(Number)
  return Number.isFinite(h) && Number.isFinite(m) ? h * 60 + m : null
}

export function fmtMin(m) {
  return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(Math.round(m % 60)).padStart(2, '0')}`
}
