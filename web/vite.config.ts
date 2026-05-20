import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

function normalizeModuleId(id: string) {
  return id.replace(/\\/g, '/')
}

function getNodeModulePackageName(id: string) {
  const normalizedId = normalizeModuleId(id)
  const nodeModulesPath = normalizedId.split('/node_modules/')[1]
  if (!nodeModulesPath) {
    return null
  }

  const segments = nodeModulesPath.split('/')
  if (segments[0]?.startsWith('@')) {
    return `${segments[0]}/${segments[1]}`
  }

  return segments[0] || null
}

function toVendorChunkName(packageName: string) {
  return `vendor-${packageName.replace('@', '').replace('/', '-')}`
}

const uiSharedPackages = new Set([
  '@ctrl/tinycolor',
  '@popperjs/core',
  '@vueuse/core',
  '@vueuse/shared',
  'lodash-es',
  'lodash-unified',
  'normalize-wheel-es',
  'tslib',
])

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const devApiTarget = env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [vue()],
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            const normalizedId = normalizeModuleId(id)
            if (!normalizedId.includes('/node_modules/')) {
              return
            }

            const packageName = getNodeModulePackageName(normalizedId)
            if (!packageName) {
              return
            }

            if (packageName === 'vue' || packageName.startsWith('@vue/')) {
              return 'vendor-vue'
            }
            if (packageName === 'echarts' || packageName === 'zrender') {
              return
            }
            if (packageName === 'element-plus' || packageName.startsWith('@element-plus/')) {
              return 'vendor-element-plus'
            }
            if (uiSharedPackages.has(packageName)) {
              return 'vendor-ui-shared'
            }
            return toVendorChunkName(packageName)
          },
        },
      },
    },
    server: {
      port: 4273,
      proxy: {
        '/api': {
          target: devApiTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
