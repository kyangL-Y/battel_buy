type XlsxModule = typeof import('xlsx')

let xlsxModulePromise: Promise<XlsxModule> | null = null

export function loadXlsxModule() {
  if (!xlsxModulePromise) {
    xlsxModulePromise = import('xlsx')
  }
  return xlsxModulePromise
}
