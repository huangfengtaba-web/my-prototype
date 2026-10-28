import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'

// 多页入口：9 页原型原样保留（内联样式不动），新增 /scheduling-test 求解演示页。
// 约束见 docs/02_INTEGRATION_GUIDE.md §3 —— 迁入 HTML 零改造，跨页仍为相对路径。
const r = (p) => fileURLToPath(new URL(p, import.meta.url))

export default defineConfig({
  root: r('.'),
  server: { port: 5173 },
  build: {
    rollupOptions: {
      input: {
        index:         r('index.html'),
        dataZone:      r('prototypes/data_zone.html'),
        configZone:    r('prototypes/config_zone.html'),
        modelZone:     r('prototypes/model_zone.html'),
        resultLitho:   r('prototypes/result_litho.html'),
        resultReticle: r('prototypes/result_reticle.html'),
        logZone:       r('prototypes/log_zone.html'),
        stacking:      r('prototypes/stacking_bond_ui_v6.html'),
        equipTemp:     r('prototypes/equip_temp_layer_config.html'),
        schedTest:     r('src/pages/scheduling-test/index.html')
      }
    }
  }
})
