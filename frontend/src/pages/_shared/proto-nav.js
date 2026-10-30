// 原型页系统导航胶囊：在 9 页 mock 原型上提供返回真实系统的入口（不改动原型自身布局与样式）。
// 用法：原型页 </body> 前加 <script src="/src/pages/_shared/proto-nav.js" defer></script>
(function () {
  if (window.__gtxProtoNav) return
  window.__gtxProtoNav = true

  const LINKS = [
    ['/', '系统总览'],
    ['/litho-schedule', 'Litho 排程（真数据）'],
    ['/reticle-schedule', 'Reticle 排程（真数据）'],
    ['/twin-control', '数字孪生回放'],
    ['/simulation', '仿真验证'],
    ['/scheduling-test', '求解演示'],
    ['/ai-agent', 'AI 助手'],
    ['/ai-workflow', 'AI 工作流'],
    ['/reports', '报告生成'],
    ['/prototypes/index.html', '原型总览'],
  ]

  const css = document.createElement('style')
  css.textContent = `
  #gtxProtoNav{position:fixed;left:12px;bottom:12px;z-index:99999;font-family:'Segoe UI',system-ui,sans-serif}
  #gtxProtoNav .pn-btn{display:inline-flex;align-items:center;gap:6px;background:#1677FF;color:#fff;
    border:none;border-radius:999px;padding:7px 14px;font-size:12px;cursor:pointer;
    box-shadow:0 4px 12px rgba(0,0,0,.25)}
  #gtxProtoNav .pn-menu{display:none;position:absolute;bottom:40px;left:0;background:#fff;
    border:1px solid #d9d9d9;border-radius:8px;box-shadow:0 6px 16px rgba(0,0,0,.12);
    padding:6px;min-width:180px}
  #gtxProtoNav.open .pn-menu{display:block}
  #gtxProtoNav .pn-menu a{display:block;padding:7px 10px;border-radius:6px;color:rgba(0,0,0,.88);
    text-decoration:none;font-size:13px}
  #gtxProtoNav .pn-menu a:hover{background:#E6F4FF;color:#1677FF}
  #gtxProtoNav .pn-menu .pn-h{font-size:11px;color:rgba(0,0,0,.45);padding:4px 10px 2px}`
  document.head.appendChild(css)

  const root = document.createElement('div')
  root.id = 'gtxProtoNav'
  root.innerHTML = `
    <div class="pn-menu">
      <div class="pn-h">GTX FSO 系统导航（真后端）</div>
      ${LINKS.map(([h, t]) => `<a href="${h}">${t}</a>`).join('')}
    </div>
    <button class="pn-btn">🧭 系统导航</button>`
  document.body.appendChild(root)
  root.querySelector('.pn-btn').addEventListener('click', () => root.classList.toggle('open'))
  document.addEventListener('click', (e) => {
    if (!root.contains(e.target)) root.classList.remove('open')
  })
})()
