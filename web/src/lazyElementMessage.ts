type ElementMessageLevel = 'success' | 'warning' | 'error' | 'info'

type ElementMessageApi = Record<ElementMessageLevel, (message: string) => void>

let elementMessageApiPromise: Promise<ElementMessageApi> | null = null

function loadElementMessageApi() {
  if (!elementMessageApiPromise) {
    elementMessageApiPromise = Promise.all([
      import('element-plus/es/components/message/index.mjs'),
      import('element-plus/es/components/message/style/css'),
    ]).then(([messageModule]) => messageModule.ElMessage)
  }

  return elementMessageApiPromise
}

function showElementMessage(level: ElementMessageLevel, message: string) {
  void loadElementMessageApi().then((elementMessageApi) => {
    elementMessageApi[level](message)
  })
}

export const lazyElMessage: ElementMessageApi = {
  success(message) {
    showElementMessage('success', message)
  },
  warning(message) {
    showElementMessage('warning', message)
  },
  error(message) {
    showElementMessage('error', message)
  },
  info(message) {
    showElementMessage('info', message)
  },
}
