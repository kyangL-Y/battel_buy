import { dataSourceState, formatApiErrorMessage } from './apiSession'

type RequestStateOptions = {
  affectGlobalState?: boolean
}

function isAxiosError(error: unknown) {
  return typeof error === 'object' && error !== null && 'isAxiosError' in error
}

export async function requestWithState<T>(request: () => Promise<T>, options: RequestStateOptions = {}) {
  const { affectGlobalState = true } = options
  try {
    const responsePayload = await request()
    if (affectGlobalState) {
      dataSourceState.mode = 'live'
      dataSourceState.lastError = ''
    }
    return responsePayload
  } catch (error) {
    if (affectGlobalState && isAxiosError(error)) {
      dataSourceState.mode = 'error'
      dataSourceState.lastError = formatApiErrorMessage(error)
    }
    throw error
  }
}
