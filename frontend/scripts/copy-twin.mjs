import { cpSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

const src = resolve(process.cwd(), '../vendor/semiconfab-gtx')
const dst = resolve(process.cwd(), 'dist/vendor-twin')
if (!existsSync(src)) {
  console.warn('[copy-twin] 源不存在，跳过:', src)
  process.exit(0)
}
cpSync(src, dst, { recursive: true })
console.log('[copy-twin] done ->', dst)
