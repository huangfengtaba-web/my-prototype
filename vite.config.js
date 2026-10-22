import { defineConfig } from 'vite'
import { resolve } from 'path'
import { cpSync } from 'fs'

/**
 * 原型页面使用「经典脚本（非 module）+ 全局函数 + 内联 onclick」的组织方式，
 * Vite 不会打包 <script src> 非 module 脚本，因此构建时把 src/scripts 原样复制到 dist/scripts，
 * 保证 `vite preview` / 静态部署时脚本可用，同时保留原型交互行为不变。
 */
function copyClassicScripts() {
  return {
    name: 'copy-classic-scripts',
    apply: 'build',
    closeBundle() {
      cpSync(
        resolve(process.cwd(), 'src/scripts'),
        resolve(process.cwd(), 'dist/scripts'),
        { recursive: true }
      )
    }
  }
}

export default defineConfig({
  // 指定根目录为 src
  root: 'src',
  // 静态资源目录（如果有 favicon.ico 等）
  publicDir: resolve(process.cwd(), 'public'),
  server: {
    open: '/' // 启动时自动打开浏览器
  },
  plugins: [copyClassicScripts()],
  build: {
    // 打包输出到根目录的 dist 文件夹
    outDir: resolve(process.cwd(), 'dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        // 原型入口
        main: resolve(process.cwd(), 'src/index.html'),
        // 设备温层配置
        'temp-layer-config': resolve(process.cwd(), 'src/pages/temp-layer-config/index.html'),
        // Stacking Bond 产能分配
        'stacking-bond': resolve(process.cwd(), 'src/pages/stacking-bond/index.html')
      }
    }
  }
})
