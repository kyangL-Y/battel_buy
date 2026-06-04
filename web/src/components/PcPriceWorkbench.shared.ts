export type SectionId =
  | 'summary'
  | 'trend'
  | 'alerts'
  | 'market'
  | 'suppliers'
  | 'purchase'
  | 'quotes'
  | 'plan'
  | 'reports'
  | 'settings'

export type MessageSection = Extract<SectionId, 'summary' | 'alerts' | 'quotes' | 'market' | 'purchase' | 'settings'>

export type ModuleLayout = 'coverage' | 'network' | 'workflow' | 'ledger' | 'insight' | 'ops'

export type ModuleMetric = { label: string; value: string; detail: string; tone: string }

export type ModuleSideItem = { label: string; title: string; detail: string; tone: string }

export type ModuleFlowItem = { step: string; text: string; status?: string }

export type ModuleView = {
  kicker: string
  title: string
  description: string
  action: string
  metrics: ModuleMetric[]
  tableTitle: string
  columns: string[]
  tableRows: string[][]
  sideTitle: string
  sideItems: ModuleSideItem[]
  flowTitle: string
  flow: ModuleFlowItem[]
}

export const WORKBENCH_SECTION_IDS: readonly SectionId[] = [
  'summary',
  'trend',
  'alerts',
  'market',
  'suppliers',
  'purchase',
  'quotes',
  'plan',
  'reports',
  'settings',
]

export const GENERATED_MODULE_SECTIONS: readonly SectionId[] = [
  'market',
  'suppliers',
  'purchase',
  'quotes',
  'plan',
  'reports',
  'settings',
]

const MODULE_LAYOUT_BY_SECTION: Partial<Record<SectionId, ModuleLayout>> = {
  market: 'coverage',
  suppliers: 'network',
  purchase: 'workflow',
  plan: 'workflow',
  quotes: 'ledger',
  reports: 'insight',
  settings: 'ops',
}

const DENSE_SECTIONS = new Set<SectionId>(['quotes', 'settings', 'reports'])
const WORKFLOW_DENSITY_SECTIONS = new Set<SectionId>(['purchase', 'plan'])

export function isWorkbenchSectionId(value: string | null): value is SectionId {
  return Boolean(value && WORKBENCH_SECTION_IDS.includes(value as SectionId))
}

export function readInitialWorkbenchSection(): SectionId | null {
  if (typeof window === 'undefined') return null
  const section = new URLSearchParams(window.location.search).get('section')
  return isWorkbenchSectionId(section) ? section : null
}

export function syncWorkbenchSectionUrl(sectionId: SectionId) {
  if (typeof window === 'undefined') return
  const params = new URLSearchParams(window.location.search)
  params.set('mode', 'workspace')
  params.set('section', sectionId)
  window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`)
}

export function isGeneratedModuleSection(sectionId: SectionId) {
  return GENERATED_MODULE_SECTIONS.includes(sectionId)
}

export function getModuleLayout(sectionId: SectionId): ModuleLayout {
  return MODULE_LAYOUT_BY_SECTION[sectionId] || 'ops'
}

export function getModuleDensityClass(sectionId: SectionId) {
  if (DENSE_SECTIONS.has(sectionId)) return 'is-dense'
  if (WORKFLOW_DENSITY_SECTIONS.has(sectionId)) return 'is-workflow'
  return 'is-balanced'
}
