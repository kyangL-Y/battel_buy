<template>
  <section class="menu-workspace">
    <div class="panel menu-command-panel content-shell-panel">
      <div class="panel-header content-panel-header">
        <div>
          <p class="panel-kicker">菜单录入</p>
          <h2>菜单采购</h2>
          <p class="panel-hint">
            {{ isMobileViewport ? '先录菜单，再生成采购建议。' : '录菜单、补食材、直接出采购建议。导入说明保留一行，首屏尽量只看关键字段。' }}
          </p>
        </div>
        <div v-if="!isMobileViewport" class="content-panel-meta">
          <span class="workspace-mode-pill">采购执行</span>
        </div>
      </div>
      <div class="menu-grid">
        <div class="menu-form">
          <el-input
            :model-value="menuText"
            type="textarea"
            aria-label="菜单文本输入"
            :rows="isMobileViewport ? 4 : 6"
            :autosize="isMobileViewport ? { minRows: 4, maxRows: 8 } : false"
            placeholder="每行一个菜名，例如：&#10;蒜蓉西兰花&#10;清蒸鲈鱼&#10;红烧排骨"
            @update:model-value="emit('update:menu-text', $event)"
          />
          <div class="menu-import-row">
            <input ref="fileInputRef" class="hidden-file-input" type="file" accept=".txt,.csv,.xlsx,.xls,.docx,.pdf" @change="handleFileChange" />
            <el-button aria-label="导入菜单文件" @click="openFileDialog">导入菜单文件</el-button>
            <span v-if="!isMobileViewport" class="panel-hint menu-import-hint">支持 TXT / CSV / Excel / Word / PDF，默认读取首列或首段文本。</span>
          </div>
          <div class="menu-actions">
            <div class="menu-action-field">
              <span class="menu-action-label">桌数</span>
              <el-input-number aria-label="桌数" :model-value="tables" :min="1" @update:model-value="emit('update:tables', Number($event) || 1)" />
            </div>
            <div class="menu-action-field">
              <span class="menu-action-label">人数</span>
              <el-input-number aria-label="人数" :model-value="diners" :min="1" @update:model-value="emit('update:diners', Number($event) || 1)" />
            </div>
            <div class="menu-action-field menu-location-field">
              <span class="menu-action-label">优先地区</span>
              <el-select
                :model-value="preferredLocation"
                aria-label="优先地区"
                clearable
                filterable
                placeholder="当前位置 / 城市 / 省份"
                @update:model-value="emit('update:preferred-location', String($event || ''))"
              >
                <el-option
                  v-for="item in locationCandidates"
                  :key="item"
                  :label="item"
                  :value="item"
                />
              </el-select>
            </div>
          </div>
          <div class="menu-submit-bar">
            <el-button aria-label="生成采购方案" type="primary" :loading="loading" @click="emit('submit')">生成采购方案</el-button>
          </div>
        </div>
        <aside v-if="!isMobileViewport" class="menu-guidance-card compact-guidance-card">
          <div class="guidance-head">
            <span class="guidance-tag">采购流程</span>
            <strong>三步完成采购判断</strong>
          </div>
          <ul class="menu-guidance-list">
            <li>先录菜单，再由 AI 或规则补足主要食材。</li>
            <li>优先地区只影响推荐顺序，不改原始报价。</li>
            <li>缺报价只保留轻提示，完整字段放表格里查看。</li>
          </ul>
        </aside>
      </div>
    </div>

    <div v-if="!isMobileViewport" class="menu-summary-strip content-overview-strip">
      <div class="summary-card menu-kpi">
        <span>菜品行数</span>
        <strong>{{ parsedMenuCount }}</strong>
        <small>当前输入</small>
      </div>
      <div class="summary-card menu-kpi">
        <span>已匹配报价</span>
        <strong>{{ matchedPlanCount }}</strong>
        <small>可直接采购</small>
      </div>
      <div class="summary-card menu-kpi" :class="{ 'menu-kpi-pending': pendingPlanCount > 0 }">
        <span>待确认</span>
        <strong>{{ pendingPlanCount }}</strong>
        <small>需要人工确认</small>
      </div>
      <div class="summary-card menu-kpi menu-kpi-emphasis">
        <span>总成本</span>
        <strong>{{ totalCostLabel }}</strong>
        <small>已匹配估算</small>
      </div>

      <div v-if="pendingPreviewRows.length" class="menu-pending-brief">
        <div class="menu-pending-head">
          <span>待确认食材</span>
          <strong>{{ pendingPlanCount }} 项</strong>
        </div>
        <div class="menu-alert-tags compact-alert-tags">
          <em v-for="row in pendingPreviewRows" :key="`${row.ingredient_name}-${row.menu_name}`">{{ row.ingredient_name || row.menu_name }}</em>
          <em v-if="pendingOverflowCount > 0" class="overflow-tag">+{{ pendingOverflowCount }}</em>
        </div>
      </div>
    </div>
    <div v-else class="menu-mobile-overview">
      <div class="menu-mobile-overview-pill">
        <span>菜品</span>
        <strong>{{ parsedMenuCount }}</strong>
      </div>
      <div class="menu-mobile-overview-pill">
        <span>已匹配</span>
        <strong>{{ matchedPlanCount }}</strong>
      </div>
      <div class="menu-mobile-overview-pill" :class="{ warning: pendingPlanCount > 0 }">
        <span>待确认</span>
        <strong>{{ pendingPlanCount }}</strong>
      </div>
      <div class="menu-mobile-overview-pill emphasis">
        <span>总成本</span>
        <strong>{{ totalCostLabel }}</strong>
      </div>
    </div>

    <div class="menu-analysis-grid">
      <div class="panel nested-panel content-shell-panel">
        <div class="panel-header content-panel-header">
          <div>
            <p class="panel-kicker">采购建议</p>
            <h2>采购建议</h2>
            <p class="panel-hint">默认只看食材、推荐、报价和状态；长说明收进单元格次级信息。</p>
          </div>
          <span>{{ planRows.length }} 条</span>
        </div>
        <el-skeleton :loading="loading" animated :rows="6">
          <div v-if="isMobileViewport" class="menu-mobile-card-list" data-testid="menu-plan-mobile-list">
            <article
              v-for="row in planRows"
              :key="`${row.ingredient_name}-${row.menu_name}-${row.recommended_market}`"
              class="menu-mobile-card"
              data-testid="menu-plan-mobile-card"
            >
              <div class="menu-mobile-card-head">
                <div class="plan-ingredient-cell">
                  <strong>{{ row.ingredient_name || '-' }}</strong>
                  <small>{{ row.menu_name || '-' }}</small>
                </div>
                <span :class="['status-chip', row.price_status === '已匹配报价' ? 'ok' : 'pending']">{{ row.price_status || '-' }}</span>
              </div>
              <div class="menu-mobile-metrics">
                <div class="menu-mobile-metric emphasis">
                  <span>成本</span>
                  <strong class="menu-mobile-price">{{ formatPrice(row.estimated_cost) }}</strong>
                  <small>本次估算</small>
                </div>
                <div class="menu-mobile-metric">
                  <span>报价</span>
                  <strong>{{ formatPrice(row.reference_price) }}</strong>
                  <small>{{ row.price_unit_basis === '元/公斤' ? '统一公斤口径' : (row.price_unit_basis || '口径待确认') }}</small>
                </div>
                <div class="menu-mobile-metric">
                  <span>数量</span>
                  <strong>{{ formatQuantity(row.estimated_quantity, row.quantity_unit) }}</strong>
                  <small>{{ row.quantity_unit || '数量' }}</small>
                </div>
              </div>
              <div class="menu-mobile-data-row">
                <span>推荐</span>
                <strong>{{ row.recommended_market || '-' }}</strong>
                <small>{{ row.recommended_site || '未标注报价源' }}</small>
              </div>
              <div v-if="row.backup_market || row.backup_site" class="menu-mobile-data-row secondary">
                <span>备选</span>
                <strong>{{ row.backup_market || row.backup_site || '-' }}</strong>
                <small>{{ row.backup_site || '无备选来源' }}</small>
              </div>
              <p class="menu-mobile-card-note">{{ row.distance_label || row.source_priority_label || row.remarks || '按价格和地区综合排序' }}</p>
              <p v-if="row.remarks && row.remarks !== row.distance_label && row.remarks !== row.source_priority_label" class="menu-mobile-card-note secondary">
                {{ row.remarks }}
              </p>
            </article>
            <div v-if="!planRows.length" class="table-empty-state">
              <strong>还没有采购建议</strong>
              <p>先录入菜单并生成采购方案，手机端会直接展示精简卡片。</p>
            </div>
          </div>
          <el-table v-else :data="planRows" height="410" size="small">
            <el-table-column label="食材 / 菜品" min-width="172" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="plan-ingredient-cell">
                  <strong>{{ row.ingredient_name || '-' }}</strong>
                  <small>{{ row.menu_name || '-' }}</small>
                  <small class="plan-inline-number">{{ formatQuantity(row.estimated_quantity, row.quantity_unit) }}</small>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="推荐 / 备选" min-width="176" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="plan-ingredient-cell">
                  <strong>{{ row.recommended_market || '-' }}</strong>
                  <small>{{ row.recommended_site || '未标注报价源' }}</small>
                  <small>{{ row.backup_market || row.backup_site || '无备选市场' }}</small>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="报价 / 成本" min-width="148">
              <template #default="{ row }">
                <div class="plan-ingredient-cell">
                  <strong>{{ formatPrice(row.reference_price) }}</strong>
                  <small>{{ row.price_unit_basis === '元/公斤' ? '统一公斤口径' : (row.price_unit_basis || '口径待确认') }}</small>
                  <small class="plan-inline-number">成本 {{ formatPrice(row.estimated_cost) }}</small>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态 / 说明" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="plan-status-cell">
                  <span :class="['status-chip', row.price_status === '已匹配报价' ? 'ok' : 'pending']">{{ row.price_status || '-' }}</span>
                  <small>{{ row.distance_label || row.source_priority_label || '按价格和地区综合排序' }}</small>
                  <small>{{ row.remarks || '无额外说明' }}</small>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-skeleton>
      </div>
      <div class="panel nested-panel content-shell-panel">
        <div class="panel-header content-panel-header">
          <div>
            <p class="panel-kicker">食材拆分</p>
            <h2>食材拆分</h2>
            <p class="panel-hint">保留校对所需的菜品、食材和数量，不再放过多辅助字段。</p>
          </div>
          <span>{{ ingredientRows.length }} 条</span>
        </div>
        <el-skeleton :loading="loading" animated :rows="5">
          <div v-if="isMobileViewport" class="menu-mobile-card-list ingredient-mobile-list" data-testid="ingredient-mobile-list">
            <article
              v-for="row in ingredientRows"
              :key="`${row.menu_name}-${row.ingredient_name}-${row.estimated_quantity}`"
              class="menu-mobile-card ingredient-mobile-card"
              data-testid="ingredient-mobile-card"
            >
              <div class="menu-mobile-card-head">
                <div class="plan-ingredient-cell">
                  <strong>{{ row.ingredient_name || '-' }}</strong>
                  <small>{{ row.menu_name || '-' }}</small>
                </div>
                <span class="price-chip avg">{{ formatQuantity(row.estimated_quantity, row.quantity_unit) }}</span>
              </div>
              <p class="menu-mobile-card-note">{{ row.remarks || '无额外备注' }}</p>
            </article>
            <div v-if="!ingredientRows.length" class="table-empty-state">
              <strong>还没有食材拆分</strong>
              <p>生成采购方案后，这里会按手机端卡片展示菜品与食材数量。</p>
            </div>
          </div>
          <el-table v-else :data="ingredientRows" height="410" size="small">
            <el-table-column prop="menu_name" label="菜品" min-width="144" show-overflow-tooltip />
            <el-table-column prop="ingredient_name" label="食材" min-width="132" show-overflow-tooltip />
            <el-table-column label="数量" width="112">
              <template #default="{ row }">
                <span class="plan-inline-number">{{ formatQuantity(row.estimated_quantity, row.quantity_unit) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="remarks" label="备注" min-width="180" show-overflow-tooltip />
          </el-table>
        </el-skeleton>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import type { MenuPlanRow } from '../types'
import { useViewport } from '../composables/useViewport'

const props = defineProps<{
  menuText: string
  tables: number
  diners: number
  preferredLocation: string
  locationCandidates: string[]
  ingredientRows: Record<string, any>[]
  planRows: MenuPlanRow[]
  parsedMenuCount: number
  matchedPlanCount: number
  pendingPlanCount: number
  totalCostLabel: string
  loading: boolean
}>()

const emit = defineEmits<{
  (event: 'update:menu-text', value: string): void
  (event: 'update:tables', value: number): void
  (event: 'update:diners', value: number): void
  (event: 'update:preferred-location', value: string): void
  (event: 'submit'): void
  (event: 'import-lines', value: string[]): void
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const { isMobileViewport } = useViewport()
const MENU_NAME_HEADER_PATTERNS = [/菜名/i, /菜单/i, /菜品/i, /品名/i, /^名称$/i]
const TEXT_ENCODINGS = ['utf-8', 'gb18030']

function openFileDialog() {
  fileInputRef.value?.click()
}

function formatPrice(value: number | null | undefined) {
  if (value == null || Number.isNaN(Number(value))) {
    return '-'
  }
  return Number(value).toFixed(2)
}

function formatQuantity(value: number | null | undefined, unit?: string | null) {
  if (value == null || Number.isNaN(Number(value))) {
    return unit ? `- ${unit}` : '-'
  }
  return `${Number(value).toFixed(2)} ${unit || ''}`.trim()
}

function getFileExtension(filename: string) {
  const parts = filename.toLowerCase().split('.')
  return parts.length > 1 ? parts.pop() || '' : ''
}

function normalizeImportedLines(lines: string[]) {
  return Array.from(
    new Set(
      lines
        .map((item) => item.replace(/\u0000/g, '').trim())
        .filter(Boolean),
    ),
  )
}

function decodeTextBuffer(buffer: ArrayBuffer) {
  for (const encoding of TEXT_ENCODINGS) {
    try {
      return new TextDecoder(encoding).decode(buffer)
    } catch {
      // Try next encoding.
    }
  }
  return new TextDecoder().decode(buffer)
}

function parseImportedText(content: string, filename: string): string[] {
  const lowerName = filename.toLowerCase()
  if (lowerName.endsWith('.csv')) {
    return normalizeImportedLines(
      content
      .split(/\r?\n/)
      .map((line) => line.split(',')[0]?.replace(/^"|"$/g, '').trim())
      .filter(Boolean) as string[],
    )
  }
  return normalizeImportedLines(content.split(/\r?\n/).map((item) => item.trim()).filter(Boolean))
}

function findMenuColumnIndex(rows: string[][]) {
  const headerRows = rows.slice(0, 3)
  for (const row of headerRows) {
    for (const [index, cell] of row.entries()) {
      if (MENU_NAME_HEADER_PATTERNS.some((pattern) => pattern.test(cell))) {
        return index
      }
    }
  }
  return -1
}

function parseTabularRows(rows: unknown[][]) {
  const normalizedRows = rows
    .filter((row) => Array.isArray(row))
    .map((row) => row.map((cell) => String(cell ?? '').trim()))
    .filter((row) => row.some(Boolean))
  if (!normalizedRows.length) {
    return []
  }

  const menuColumnIndex = findMenuColumnIndex(normalizedRows)
  if (menuColumnIndex >= 0) {
    return normalizeImportedLines(
      normalizedRows
        .slice(1)
        .map((row) => row[menuColumnIndex] || '')
        .filter(Boolean),
    )
  }

  return normalizeImportedLines(
    normalizedRows
      .map((row) => row.find(Boolean) || '')
      .filter(Boolean),
  )
}

async function parseSpreadsheetFile(file: File) {
  const xlsx = await import('xlsx')
  const buffer = await file.arrayBuffer()
  const workbook = xlsx.read(buffer, { type: 'array' })
  const firstSheetName = workbook.SheetNames[0]
  if (!firstSheetName) {
    return []
  }
  const firstSheet = workbook.Sheets[firstSheetName]
  const rows = xlsx.utils.sheet_to_json(firstSheet, {
    header: 1,
    raw: false,
    defval: '',
  }) as unknown[][]
  return parseTabularRows(rows)
}

async function parseDocxFile(file: File) {
  const mammoth = await import('mammoth')
  const buffer = await file.arrayBuffer()
  const result = await mammoth.extractRawText({ arrayBuffer: buffer })
  return normalizeImportedLines(
    result.value
      .split(/\r?\n/)
      .flatMap((line) => line.split(/\t+/))
      .map((item) => item.trim())
      .filter(Boolean),
  )
}

async function parsePdfFile(file: File) {
  const pdfjs = await import('pdfjs-dist/build/pdf.min.mjs')
  pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerUrl
  const buffer = await file.arrayBuffer()
  const document = await pdfjs.getDocument({ data: new Uint8Array(buffer) }).promise
  const lines: string[] = []

  for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
    const page = await document.getPage(pageNumber)
    const textContent = await page.getTextContent()
    let currentLine = ''
    for (const item of textContent.items as Array<{ str?: string; hasEOL?: boolean }>) {
      const text = String(item.str || '').trim()
      if (text) {
        currentLine = currentLine ? `${currentLine} ${text}` : text
      }
      if (item.hasEOL && currentLine) {
        lines.push(currentLine)
        currentLine = ''
      }
    }
    if (currentLine) {
      lines.push(currentLine)
    }
  }

  return normalizeImportedLines(lines)
}

async function parseImportedFile(file: File) {
  const extension = getFileExtension(file.name)
  if (extension === 'txt' || extension === 'csv') {
    const buffer = await file.arrayBuffer()
    return parseImportedText(decodeTextBuffer(buffer), file.name)
  }
  if (extension === 'xlsx' || extension === 'xls') {
    return parseSpreadsheetFile(file)
  }
  if (extension === 'docx') {
    return parseDocxFile(file)
  }
  if (extension === 'pdf') {
    return parsePdfFile(file)
  }
  throw new Error('暂不支持该文件格式')
}

async function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const lines = await parseImportedFile(file)
    if (!lines.length) {
      ElMessage.warning('文件里没有识别到菜单项，PDF 需为可复制文本内容')
      return
    }
    emit('import-lines', lines)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '菜单文件读取失败')
  } finally {
    input.value = ''
  }
}

const pendingRows = computed(() => props.planRows.filter((item) => item.price_status !== '已匹配报价'))
const pendingPreviewRows = computed(() => pendingRows.value.slice(0, 4))
const pendingOverflowCount = computed(() => Math.max(0, pendingRows.value.length - pendingPreviewRows.value.length))
</script>
