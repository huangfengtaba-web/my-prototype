import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'
import { createReadStream, existsSync, statSync } from 'node:fs'
import { extname, resolve as pathResolve } from 'node:path'

// 多页入口：9 页原型原样保留（内联样式不动），新增智能应用页。
// 约束见 docs/02_INTEGRATION_GUIDE.md §3 —— 迁入 HTML 零改造，跨页仍为相对路径。
const r = (p) => fileURLToPath(new URL(p, import.meta.url))
const TWIN_DIR = pathResolve(r('.'), '../vendor/semiconfab-gtx')

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
}

// devserver 下复刻 vercel.json 的路由语义（干净 URL + /twin 静态目录 + gtx 数据文件）
function gtxDevUrls() {
  return {
    name: 'gtx-dev-urls',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = (req.url || '').split('?')[0]
        const serveFile = (fp) => {
          res.setHeader('Content-Type', MIME[extname(fp)] || 'application/octet-stream')
          createReadStream(fp).pipe(res)
        }
        if (url === '/twin' || url.startsWith('/twin/')) {
          const rel = url === '/twin' ? 'twin.html' : decodeURIComponent(url.slice('/twin/'.length))
          const fp = pathResolve(TWIN_DIR, rel)
          if (fp.startsWith(TWIN_DIR) && existsSync(fp) && statSync(fp).isFile()) return serveFile(fp)
        }
        // twin.html 的相对资源（无斜杠 URL 下解析到根）：/js/* 也来自孪生目录
        if (url.startsWith('/js/')) {
          const fp = pathResolve(TWIN_DIR, decodeURIComponent(url.slice(1)))
          if (fp.startsWith(TWIN_DIR) && existsSync(fp) && statSync(fp).isFile()) return serveFile(fp)
        }
        for (const f of ['gtx-catalog.json', 'gtx-layout-map.json']) {
          if (url === `/${f}`) return serveFile(pathResolve(TWIN_DIR, f))
        }
        const cleanMap = {
          '/simulation': '/src/pages/simulation/index.html',
          '/ai-agent': '/src/pages/ai-agent/index.html',
          '/ai-workflow': '/src/pages/ai-workflow/index.html',
          '/scheduling-test': '/src/pages/scheduling-test/index.html',
          '/reports': '/src/pages/reports/index.html',
          '/twin-control': '/src/pages/twin-control/index.html',
          '/litho-schedule': '/src/pages/litho-schedule/index.html',
          '/reticle-schedule': '/src/pages/reticle-schedule/index.html',
          '/logs': '/src/pages/logs/index.html'
        }
        if (cleanMap[url]) req.url = cleanMap[url]
        next()
      })
    }
  }
}

export default defineConfig({
  root: r('.'),
  plugins: [gtxDevUrls()],
  server: {
    port: 5173,
    strictPort: true,
    // 同时监听 IPv4 / IPv6：否则 Windows 上默认只绑 [::1]，
    // 导致 http://127.0.0.1:5173 打不开（只有 localhost 能用）。
    host: true
  },
  build: {
    rollupOptions: {
      input: {
        index:         r('index.html'),
        protoIndex:    r('prototypes/index.html'),
        dataZone:      r('prototypes/data_zone.html'),
        configZone:    r('prototypes/config_zone.html'),
        modelZone:     r('prototypes/model_zone.html'),
        resultLitho:   r('prototypes/result_litho.html'),
        resultReticle: r('prototypes/result_reticle.html'),
        logZone:       r('prototypes/log_zone.html'),
        stacking:      r('prototypes/stacking_bond_ui_v6.html'),
        equipTemp:     r('prototypes/equip_temp_layer_config.html'),
        schedTest:     r('src/pages/scheduling-test/index.html'),
        simPage:       r('src/pages/simulation/index.html'),
        workflowPage:  r('src/pages/ai-workflow/index.html'),
        agentPage:     r('src/pages/ai-agent/index.html'),
        twinControl:   r('src/pages/twin-control/index.html'),
        reportsPage:   r('src/pages/reports/index.html'),
        lithoSched:    r('src/pages/litho-schedule/index.html'),
        reticleSched:  r('src/pages/reticle-schedule/index.html'),
        logsPage:      r('src/pages/logs/index.html')
      }
    }
  }
})
