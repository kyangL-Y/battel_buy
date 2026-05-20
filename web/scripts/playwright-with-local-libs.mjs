import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const webRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(webRoot, '..')
const linuxLibDir = path.join(
  repoRoot,
  'web',
  '.tmp',
  'pw-libs',
  'root',
  'usr',
  'lib',
  'x86_64-linux-gnu',
)

const env = { ...process.env }

if (process.platform !== 'win32') {
  if (fs.existsSync(linuxLibDir)) {
    env.LD_LIBRARY_PATH = env.LD_LIBRARY_PATH
      ? `${linuxLibDir}:${env.LD_LIBRARY_PATH}`
      : linuxLibDir
  } else {
    console.error(
      [
        `未找到本地 Playwright 依赖库目录：${linuxLibDir}`,
        '如果 Chromium 报缺少 libnspr4/libnss3，可先执行：',
        '  mkdir -p web/.tmp/pw-libs && cd web/.tmp/pw-libs',
        '  apt-get download libnspr4 libnss3',
        '  for d in *.deb; do dpkg-deb -x "$d" root; done',
        '或使用系统方式安装：',
        '  sudo npx playwright install-deps chromium',
      ].join('\n'),
    )
  }
}

const child = spawn('npx', ['playwright', ...process.argv.slice(2)], {
  cwd: webRoot,
  env,
  stdio: 'inherit',
  shell: process.platform === 'win32',
})

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal)
    return
  }
  process.exit(code ?? 1)
})

child.on('error', (error) => {
  console.error(error)
  process.exit(1)
})
