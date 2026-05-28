<template>
  <section class="menu-workspace">
    <div class="panel menu-command-panel content-shell-panel">
      <div class="panel-header content-panel-header">
        <div>
          <p class="panel-kicker">菜单录入</p>
          <h2>菜单采购</h2>
          <p class="panel-hint">
            {{ isMobileViewport ? '先录菜单，再生成采购建议。' : '录菜单、补食材、直接出采购建议（按总人数口径）。' }}
          </p>
        </div>
        <div v-if="!isMobileViewport" class="content-panel-meta">
          <span class="workspace-mode-pill">采购执行</span>
        </div>
      </div>
      <section v-if="isMobileViewport" class="menu-mobile-hero">
        <div class="menu-mobile-hero-copy">
          <p>主流程</p>
          <h3>先录菜单，再看食材和报价</h3>
          <span>{{ mobileHeroSummary }}</span>
        </div>
        <div class="menu-mobile-hero-stats">
          <article>
            <strong>{{ parsedMenuCount }}</strong>
            <span>菜品</span>
          </article>
          <article>
            <strong>{{ matchedPlanCount }}</strong>
            <span>已匹配</span>
          </article>
          <article :class="{ warning: pendingPlanCount > 0 }">
            <strong>{{ pendingPlanCount }}</strong>
            <span>待确认</span>
          </article>
        </div>
        <div v-if="showMobileHeroSummary" class="menu-mobile-hero-summary">
          <article class="emphasis">
            <span>总成本</span>
            <strong>{{ totalCostLabel }}</strong>
          </article>
          <article v-if="pendingPlanCount > 0" class="warning">
            <span>待补动作</span>
            <strong>{{ pendingPlanCount }} 项</strong>
          </article>
        </div>
        <button
          v-if="pendingRows.length > 0"
          type="button"
          class="menu-pending-copy-button"
          @click="copyPendingRows"
        >
          复制待确认食材
        </button>
      </section>
      <div class="menu-grid">
        <div class="menu-form">
          <el-input
            :model-value="menuText"
            type="textarea"
            aria-label="菜单文本输入"
            :rows="isMobileViewport ? 2 : 6"
            :autosize="false"
            :placeholder="isMobileViewport ? '每行一个菜名，例如：\n蒜蓉西兰花' : '每行一个菜名，例如：\n蒜蓉西兰花\n清蒸鲈鱼\n红烧排骨'"
            @update:model-value="emit('update:menu-text', $event)"
          />
          <div class="menu-actions">
            <div class="menu-action-field">
              <span class="menu-action-label">桌数</span>
              <el-input-number aria-label="桌数" :model-value="tables" :min="1" @update:model-value="emit('update:tables', Number($event) || 1)" />
            </div>
            <div class="menu-action-field">
              <span class="menu-action-label">总人数</span>
              <el-input-number aria-label="总人数" :model-value="diners" :min="1" @update:model-value="emit('update:diners', Number($event) || 1)" />
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
          <p class="menu-action-helper">{{ guestSizingHint }}</p>
          <div class="menu-submit-bar">
            <el-button aria-label="生成采购方案" type="primary" :loading="loading" :disabled="!hasMenuInput" @click="emit('submit')">生成采购方案</el-button>
            <p v-if="!hasMenuInput" class="menu-input-required" role="status" aria-live="polite">请先输入至少 1 个菜名</p>
            <p v-if="loading" :class="['menu-ai-status', { warning: isPlanTakingLong }]" role="status" aria-live="polite" data-testid="menu-ai-status">
              {{ isPlanTakingLong ? '匹配超过 9 秒，可能是接口较慢；可继续等待，或在下方重新尝试。' : 'AI 正在联网拆分食材，并匹配今日行情报价' }}
            </p>
          </div>
        </div>
        <aside
          v-if="!isMobileViewport"
          class="menu-guidance-card compact-guidance-card"
          :class="{ 'is-parse-ready': ingredientParseRows.length > 0 }"
          :data-testid="ingredientParseRows.length ? 'menu-ai-parse-panel' : undefined"
        >
          <template v-if="ingredientParseRows.length">
            <div class="menu-ai-parse-head">
              <div>
                <p class="panel-kicker">AI 解析</p>
                <h2>食材拆分结果</h2>
              </div>
              <span>{{ ingredientRows.length }} 项食材</span>
            </div>
            <div class="menu-ai-parse-list desktop">
              <article v-for="row in ingredientParseRows" :key="row.menuName" class="menu-ai-parse-card">
                <strong>{{ row.menuName }}</strong>
                <div>
                  <span v-for="item in row.ingredients" :key="`${row.menuName}-${item}`">{{ item }}</span>
                </div>
                <small>{{ row.summary }}</small>
              </article>
            </div>
          </template>
          <template v-else>
            <div class="guidance-head">
              <span class="guidance-tag">采购流程</span>
              <strong>三步完成采购判断</strong>
            </div>
            <ul class="menu-guidance-list">
              <li>先录菜单，再由 AI 或规则补足主要食材。</li>
              <li>优先地区只影响推荐顺序，不改原始报价。</li>
              <li>缺报价只保留轻提示，完整字段放表格里查看。</li>
            </ul>
          </template>
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
        <button type="button" class="menu-pending-copy-button desktop" @click="copyPendingRows">复制待确认食材</button>
      </div>
    </div>
    <section v-if="isMobileViewport && ingredientParseRows.length" class="menu-ai-parse-panel" data-testid="menu-ai-parse-panel">
      <div class="menu-ai-parse-head">
        <div>
          <p class="panel-kicker">第 1 步</p>
          <h2>食材拆分结果</h2>
        </div>
        <span>{{ ingredientRows.length }} 项食材</span>
      </div>
      <div class="menu-ai-parse-list">
        <article v-for="row in ingredientParseRows" :key="row.menuName" class="menu-ai-parse-card">
          <strong>{{ row.menuName }}</strong>
          <div>
            <span v-for="item in row.ingredients" :key="`${row.menuName}-${item}`">{{ item }}</span>
          </div>
          <small>{{ row.summary }}</small>
        </article>
      </div>
    </section>

    <div class="menu-analysis-grid">
      <div class="panel nested-panel content-shell-panel">
        <div class="panel-header content-panel-header">
          <div>
            <p class="panel-kicker">{{ isMobileViewport ? '第 2 步' : '采购建议' }}</p>
            <h2>{{ isMobileViewport ? '再决定去哪买' : '采购建议' }}</h2>
            <p class="panel-hint">{{ isMobileViewport ? '只看食材、成本、推荐市场和下一步动作。' : '默认只看食材、推荐、报价和状态；长说明收进单元格次级信息。' }}</p>
          </div>
          <span>{{ filteredPlanRows.length }} / {{ planRows.length }} 条</span>
        </div>
        <div v-if="planRows.length" class="menu-plan-filter-row" aria-label="采购建议筛选">
          <button
            v-for="item in planFilterOptions"
            :key="item.key"
            type="button"
            class="menu-plan-filter"
            :class="{ active: activePlanQueueFilter === item.key }"
            @click="activePlanQueueFilter = item.key"
          >
            <strong>{{ item.label }}</strong>
            <small>{{ item.count }}</small>
          </button>
        </div>
        <el-skeleton :loading="showPlanSkeleton" animated :rows="6">
          <div v-if="isMobileViewport" class="menu-mobile-card-list" data-testid="menu-plan-mobile-list">
            <article
              v-for="row in filteredPlanRows"
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
              <div v-if="row.price_status !== '已匹配报价' || !isRowConfirmed(row)" class="menu-mobile-next-step">
                <span>下一步</span>
                <strong>{{ isRowConfirmed(row) ? '已确认采购' : row.price_status === '已匹配报价' ? '直接确认采购' : '先补供应商报价' }}</strong>
              </div>
              <div class="menu-mobile-data-row">
                <span>推荐</span>
                <strong>{{ row.recommended_market || '-' }}</strong>
                <small>{{ row.recommended_site || '未标注报价源' }}</small>
              </div>
              <div v-if="row.source_tier || row.backup_source_tier" class="menu-mobile-tag-row">
                <span v-if="row.source_tier" class="source-tier-chip primary">推荐 {{ row.source_tier }}</span>
                <span v-if="row.backup_source_tier" class="source-tier-chip secondary">备选 {{ row.backup_source_tier }}</span>
              </div>
              <div v-if="row.backup_market || row.backup_site" class="menu-mobile-data-row secondary">
                <span>备选</span>
                <strong>{{ row.backup_market || row.backup_site || '-' }}</strong>
                <small>{{ row.backup_site || '无备选来源' }}</small>
              </div>
              <p class="menu-mobile-card-note">{{ row.distance_label || row.source_priority_label || '按价格和地区综合排序' }}</p>
              <p v-if="row.remarks && (row.distance_label || row.source_priority_label) && row.remarks !== row.distance_label && row.remarks !== row.source_priority_label" class="menu-mobile-card-note secondary">
                {{ row.remarks }}
              </p>
              <div class="menu-plan-row-actions mobile" data-testid="menu-plan-row-actions">
                <el-button size="small" plain @click="emit('view-market', row)">看行情</el-button>
                <el-button size="small" type="warning" plain @click="emit('fill-supplier-price', row)">补供应商价</el-button>
                <el-button size="small" type="success" plain :disabled="isRowConfirmed(row)" @click="emit('confirm-row', row)">{{ isRowConfirmed(row) ? '已确认' : '标记确认' }}</el-button>
              </div>
            </article>
            <div v-if="!filteredPlanRows.length" class="table-empty-state menu-mobile-empty-state">
              <strong>{{ planEmptyTitle }}</strong>
              <p>{{ planEmptyDetail }}</p>
              <el-button type="primary" size="small" :loading="loading && !isPlanTakingLong" :disabled="planEmptyActionDisabled" @click="handlePlanEmptyAction">{{ planEmptyActionLabel }}</el-button>
            </div>
          </div>
          <el-table v-else :data="filteredPlanRows" :height="planTableHeight" size="small">
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
                  <div v-if="row.source_tier || row.backup_source_tier" class="plan-source-tags">
                    <span v-if="row.source_tier" class="source-tier-chip primary">{{ row.source_tier }}</span>
                    <span v-if="row.backup_source_tier" class="source-tier-chip secondary">备选 {{ row.backup_source_tier }}</span>
                  </div>
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
                  <span :class="['status-chip', isRowConfirmed(row) || row.price_status === '已匹配报价' ? 'ok' : 'pending']">{{ row.price_status || '-' }}</span>
                  <small>{{ row.distance_label || row.source_priority_label || '按价格和地区综合排序' }}</small>
                  <small>{{ row.remarks || '无额外说明' }}</small>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="252" fixed="right">
              <template #default="{ row }">
                <div class="menu-plan-row-actions" data-testid="menu-plan-row-actions">
                  <el-button size="small" plain @click="emit('view-market', row)">看行情</el-button>
                  <el-button size="small" type="warning" plain @click="emit('fill-supplier-price', row)">补供应商价</el-button>
                  <el-button size="small" type="success" plain :disabled="isRowConfirmed(row)" @click="emit('confirm-row', row)">{{ isRowConfirmed(row) ? '已确认' : '标记确认' }}</el-button>
                </div>
              </template>
            </el-table-column>
            <template #empty>
              <div class="menu-desktop-empty-state">
                <strong>{{ planEmptyTitle }}</strong>
                <p>{{ planEmptyDetail }}</p>
                <el-button type="primary" size="small" :loading="loading && !isPlanTakingLong" :disabled="planEmptyActionDisabled" @click="handlePlanEmptyAction">{{ planEmptyActionLabel }}</el-button>
              </div>
            </template>
          </el-table>
        </el-skeleton>
      </div>
      <div v-if="showIngredientPanel" class="panel nested-panel content-shell-panel">
        <div class="panel-header content-panel-header">
          <div>
            <p class="panel-kicker">{{ isMobileViewport ? '第 3 步' : '食材拆分' }}</p>
            <h2>{{ isMobileViewport ? '最后补齐食材数量' : '食材拆分' }}</h2>
            <p class="panel-hint">{{ isMobileViewport ? '生成后直接核对菜品、食材和数量。' : '保留校对所需的菜品、食材和数量，不再放过多辅助字段。' }}</p>
          </div>
          <span>{{ ingredientRows.length }} 条</span>
        </div>
        <el-skeleton :loading="showIngredientSkeleton" animated :rows="5">
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
            <div v-if="!ingredientRows.length" class="table-empty-state menu-mobile-empty-state">
              <strong>还没有食材拆分</strong>
              <p>生成采购方案后，这里会按手机端卡片展示菜品与食材数量。</p>
            </div>
          </div>
          <el-table v-else :data="ingredientRows" :height="ingredientTableHeight" size="small">
            <el-table-column prop="menu_name" label="菜品" min-width="144" show-overflow-tooltip />
            <el-table-column prop="ingredient_name" label="食材" min-width="132" show-overflow-tooltip />
            <el-table-column label="数量" width="112">
              <template #default="{ row }">
                <span class="plan-inline-number">{{ formatQuantity(row.estimated_quantity, row.quantity_unit) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="remarks" label="备注" min-width="180" show-overflow-tooltip />
            <template #empty>
              <div class="menu-desktop-empty-state compact">
                <strong>等待食材拆分</strong>
                <p>采购方案生成后再展示菜品、食材和数量校对表。</p>
              </div>
            </template>
          </el-table>
        </el-skeleton>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
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
  (event: 'view-market', row: MenuPlanRow): void
  (event: 'fill-supplier-price', row: MenuPlanRow): void
  (event: 'confirm-row', row: MenuPlanRow): void
  (event: 'fill-missing-quotes'): void
}>()

const { isMobileViewport } = useViewport()
const isPlanTakingLong = ref(false)
const activePlanQueueFilter = ref<'all' | 'pending' | 'matched' | 'confirmed'>('all')
let planLoadingTimer: ReturnType<typeof setTimeout> | undefined

watch(
  () => props.loading,
  (loading) => {
    if (planLoadingTimer) {
      clearTimeout(planLoadingTimer)
      planLoadingTimer = undefined
    }
    isPlanTakingLong.value = false
    if (loading) {
      planLoadingTimer = setTimeout(() => {
        isPlanTakingLong.value = true
      }, 9000)
    }
  },
  { immediate: true },
)

const hasMenuInput = computed(() => props.menuText.split(/\r?\n/).some((line) => line.trim()))
const guestSizingHint = computed(() => {
  const totalTables = Math.max(1, Number(props.tables) || 1)
  const totalDiners = Math.max(1, Number(props.diners) || 1)
  const dinersPerTable = (totalDiners / totalTables).toFixed(1)
  return `按${totalTables}桌共${totalDiners}人测算（约 ${dinersPerTable} 人/桌）`
})
const mobileHeroSummary = computed(() => {
  if (!hasMenuInput.value) return '输入菜单后，系统会先拆食材，再匹配今日报价。'
  if (props.loading && !isPlanTakingLong.value) return '正在拆分食材并匹配报价，稍后会直接给出采购建议。'
  if (props.planRows.length) return `${props.matchedPlanCount} 项已可直接采购，${props.pendingPlanCount} 项还要人工确认。`
  if (props.ingredientRows.length) return '食材已经拆出，优先处理还没有报价的项目。'
  return '先录菜单，再生成采购建议。'
})
const showMobileHeroSummary = computed(() => (
  props.planRows.length > 0
  || props.ingredientRows.length > 0
  || props.loading
  || props.pendingPlanCount > 0
))
const filteredPlanRows = computed(() => {
  if (activePlanQueueFilter.value === 'pending') {
    return props.planRows.filter((item) => item.price_status !== '已匹配报价' && !isRowConfirmed(item))
  }
  if (activePlanQueueFilter.value === 'matched') {
    return props.planRows.filter((item) => item.price_status === '已匹配报价' && !isRowConfirmed(item))
  }
  if (activePlanQueueFilter.value === 'confirmed') {
    return props.planRows.filter((item) => isRowConfirmed(item))
  }
  return props.planRows
})
const planFilterOptions = computed(() => ([
  { key: 'all' as const, label: '全部', count: props.planRows.length },
  { key: 'pending' as const, label: '待确认', count: props.planRows.filter((item) => item.price_status !== '已匹配报价' && !isRowConfirmed(item)).length },
  { key: 'matched' as const, label: '可直采', count: props.planRows.filter((item) => item.price_status === '已匹配报价' && !isRowConfirmed(item)).length },
  { key: 'confirmed' as const, label: '已确认', count: props.planRows.filter((item) => isRowConfirmed(item)).length },
]))
const hasPlanFilterResult = computed(() => filteredPlanRows.value.length > 0)
const planEmptyTitle = computed(() => {
  if (props.planRows.length > 0 && !hasPlanFilterResult.value) return '当前筛选下没有记录'
  if (isPlanTakingLong.value) return '匹配时间较长'
  if (!hasMenuInput.value) return '先录菜单，再生成采购建议'
  if (props.ingredientRows.length > 0) return '已拆出食材但暂无报价匹配'
  return '暂未生成采购建议'
})
const planEmptyDetail = computed(() => {
  if (props.planRows.length > 0 && !hasPlanFilterResult.value) return '切换上方队列筛选，查看待确认、可直采或已确认记录。'
  if (isPlanTakingLong.value) return '接口仍在处理或网络较慢，可稍后重试；如果已拆出食材，会先展示拆分结果供你复核。'
  if (!hasMenuInput.value) return '请先输入至少 1 个菜名，再生成采购方案。'
  if (props.ingredientRows.length > 0) return '已完成食材拆分，但当前报价库未匹配到可用报价；可补录供应商报价后重新匹配。'
  return '当前没有返回采购建议，请检查菜名是否清晰，或重新生成采购方案。'
})
const hasMissingQuoteEmptyState = computed(() => hasMenuInput.value && props.ingredientRows.length > 0 && !props.planRows.length)
const planEmptyActionLabel = computed(() => {
  if (props.planRows.length > 0 && !hasPlanFilterResult.value) return '查看全部'
  return isPlanTakingLong.value ? '重新尝试' : hasMissingQuoteEmptyState.value ? '去补录供应商报价' : '重新生成方案'
})
const planEmptyActionDisabled = computed(() => !hasMenuInput.value && !hasMissingQuoteEmptyState.value && !isPlanTakingLong.value && !(props.planRows.length > 0 && !hasPlanFilterResult.value))

function handlePlanEmptyAction() {
  if (props.planRows.length > 0 && !hasPlanFilterResult.value) {
    activePlanQueueFilter.value = 'all'
    return
  }
  if (hasMissingQuoteEmptyState.value) {
    emit('fill-missing-quotes')
    return
  }
  emit('submit')
}

async function copyPendingRows() {
  if (!pendingRows.value.length) {
    ElMessage.warning('当前没有待确认食材')
    return
  }
  const content = pendingRows.value
    .map((item, index) => {
      const ingredient = item.ingredient_name || item.menu_name || '未命名食材'
      const quantity = formatQuantity(item.estimated_quantity, item.quantity_unit)
      const market = item.recommended_market || item.recommended_site || '待定市场'
      return `${index + 1}. ${ingredient} | ${quantity} | ${market}`
    })
    .join('\n')
  try {
    if (!navigator.clipboard?.writeText) throw new Error('clipboard unavailable')
    await navigator.clipboard.writeText(content)
    ElMessage.success(`已复制 ${pendingRows.value.length} 条待确认食材`)
  } catch {
    ElMessage.warning('浏览器未允许复制，请手动复制')
  }
}

function isRowConfirmed(row: MenuPlanRow) {
  return String(row.price_status || '').includes('已确认') || String(row.remarks || '').includes('采购已确认')
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

function calculatePanelTableHeight(rowCount: number, rowHeight: number) {
  if (!rowCount) return 160
  return Math.min(Math.max(118 + rowCount * rowHeight, 220), 420)
}

const pendingRows = computed(() => props.planRows.filter((item) => item.price_status !== '已匹配报价' && !isRowConfirmed(item)))
const pendingPreviewRows = computed(() => pendingRows.value.slice(0, 4))
const pendingOverflowCount = computed(() => Math.max(0, pendingRows.value.length - pendingPreviewRows.value.length))
const ingredientParseRows = computed(() => {
  const grouped = new Map<string, { menuName: string; ingredients: string[]; remarks: string[] }>()
  for (const item of props.ingredientRows) {
    const menuName = String(item.menu_name || '未命名菜品')
    const ingredientName = String(item.ingredient_name || '').trim()
    const quantity = formatQuantity(Number(item.estimated_quantity), String(item.quantity_unit || ''))
    const label = ingredientName ? `${ingredientName}${quantity !== '-' ? ` ${quantity}` : ''}` : quantity
    const remarks = String(item.remarks || '').trim()
    const existing = grouped.get(menuName) || { menuName, ingredients: [], remarks: [] }
    if (label && !existing.ingredients.includes(label)) {
      existing.ingredients.push(label)
    }
    if (remarks && !existing.remarks.includes(remarks)) {
      existing.remarks.push(remarks)
    }
    grouped.set(menuName, existing)
  }
  return Array.from(grouped.values()).map((row) => ({
    ...row,
    summary: row.remarks[0] || `已拆分 ${row.ingredients.length} 项主要食材`,
  }))
})
const showIngredientPanel = computed(() => (
  isMobileViewport.value
    ? props.ingredientRows.length > 0
    : true
))
const showPlanSkeleton = computed(() => props.loading && !isPlanTakingLong.value && !props.planRows.length)
const showIngredientSkeleton = computed(() => props.loading && !isPlanTakingLong.value && !props.ingredientRows.length)
const planTableHeight = computed(() => calculatePanelTableHeight(filteredPlanRows.value.length, 48))
const ingredientTableHeight = computed(() => calculatePanelTableHeight(props.ingredientRows.length, 46))
</script>

<style scoped>
.menu-plan-filter-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.menu-plan-filter {
  display: grid;
  gap: 2px;
  padding: 10px 12px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  border-radius: 14px;
  background: #fff;
  text-align: left;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
}

.menu-plan-filter.active {
  border-color: #bfdbfe;
  background: #eef6ff;
  box-shadow: 0 0 0 3px rgba(191, 219, 254, 0.28);
  transform: translateY(-1px);
}

.menu-plan-filter strong {
  color: #0f172a;
  font-size: 13px;
}

.menu-plan-filter small {
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
}

.menu-mobile-tag-row,
.plan-source-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.menu-mobile-hero {
  display: grid;
  gap: 10px;
  margin-bottom: 14px;
  padding: 15px;
  border: 1px solid rgba(203, 213, 225, 0.72);
  border-radius: 22px;
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 34%),
    linear-gradient(160deg, #f8fbff 0%, #ffffff 52%, #f8fafc 100%);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}

.menu-mobile-hero-copy {
  display: grid;
  gap: 5px;
}

.menu-mobile-hero-copy p,
.menu-mobile-next-step span {
  margin: 0;
  color: #b45309;
  font-size: 11px;
  font-weight: 800;
  line-height: 1.2;
}

.menu-mobile-hero-copy h3 {
  margin: 0;
  color: #0f172a;
  font-size: 21px;
  line-height: 1.12;
  letter-spacing: -0.04em;
}

.menu-mobile-hero-copy span {
  color: #475569;
  font-size: 12px;
  line-height: 1.45;
}

.menu-mobile-hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.menu-mobile-hero-stats article {
  display: grid;
  gap: 4px;
  padding: 9px 10px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.94);
}

.menu-mobile-hero-stats article.warning {
  border-color: rgba(249, 115, 22, 0.2);
  background: #fff7ed;
}

.menu-mobile-hero-stats strong {
  color: #0f172a;
  font-size: 18px;
  line-height: 1;
}

.menu-mobile-hero-stats span {
  color: #64748b;
  font-size: 10px;
  font-weight: 700;
}

.menu-mobile-hero-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.menu-mobile-hero-summary article {
  display: grid;
  gap: 4px;
  padding: 10px 11px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 14px;
  background: #ffffff;
}

.menu-mobile-hero-summary article.emphasis {
  background: #eff6ff;
  border-color: rgba(37, 99, 235, 0.18);
}

.menu-mobile-hero-summary article.warning {
  background: #fff7ed;
  border-color: rgba(249, 115, 22, 0.18);
}

.menu-mobile-hero-summary span {
  color: #64748b;
  font-size: 10px;
  font-weight: 700;
}

.menu-mobile-hero-summary strong {
  color: #0f172a;
  font-size: 16px;
  line-height: 1.2;
}

.menu-pending-copy-button {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(37, 99, 235, 0.22);
  border-radius: 999px;
  background: #ffffff;
  color: #1d4ed8;
  font: inherit;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.menu-pending-copy-button.desktop {
  align-self: start;
}

.menu-plan-row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.menu-plan-row-actions.mobile {
  margin-top: 4px;
}

.menu-action-helper {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.35;
}

.menu-ai-status {
  margin: 8px 0 0;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.35;
}

.menu-ai-status.warning {
  color: #c2410c;
}

.menu-input-required {
  margin: 8px 0 0;
  color: #b45309;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.35;
}

.menu-mobile-next-step {
  display: grid;
  gap: 3px;
  padding: 10px 12px;
  border: 1px dashed rgba(249, 115, 22, 0.26);
  border-radius: 14px;
  background: #fff7ed;
}

.menu-mobile-next-step strong {
  color: #9a3412;
  font-size: 13px;
  line-height: 1.3;
}

@media (max-width: 720px) {
  .menu-plan-filter-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .menu-workspace {
    display: grid;
    gap: 14px;
  }

  .menu-command-panel.content-shell-panel,
  .menu-analysis-grid > .panel {
    border-radius: 22px;
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
  }

  .menu-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .menu-form {
    display: grid;
    gap: 12px;
  }

  .menu-form :deep(.el-textarea__inner) {
    min-height: 112px !important;
    padding: 14px 15px;
    border-radius: 18px;
    font-size: 14px;
    line-height: 1.45;
  }

  .menu-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    padding: 10px;
    border-radius: 18px;
  }

  .menu-location-field {
    grid-column: 1 / -1;
  }

  .menu-action-field {
    display: grid;
    gap: 8px;
    padding: 8px 10px 10px;
    border-radius: 14px;
  }

  .menu-action-label {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.02em;
  }

  .menu-action-field :deep(.el-input-number) {
    min-height: 44px;
  }

  .menu-action-field :deep(.el-input-number__decrease),
  .menu-action-field :deep(.el-input-number__increase),
  .menu-action-field :deep(.el-input-number .el-input__wrapper) {
    min-height: 44px;
  }

  .menu-action-field :deep(.el-input-number .el-input__inner) {
    min-height: 44px;
    line-height: 44px;
  }

  .menu-action-field :deep(.el-input__wrapper),
  .menu-action-field :deep(.el-select__wrapper) {
    min-height: 44px;
    border-radius: 14px;
  }

  .menu-submit-bar {
    display: grid;
    gap: 8px;
  }

  .menu-submit-bar :deep(.el-button) {
    width: 100%;
    min-height: 48px;
    border-radius: 14px;
    font-size: 15px;
    font-weight: 800;
  }

  .menu-ai-parse-panel {
    gap: 12px;
    padding: 14px;
    border-radius: 18px;
  }

  .menu-ai-parse-head h2 {
    font-size: 18px;
  }

  .menu-ai-parse-list {
    gap: 10px;
  }

  .menu-ai-parse-card {
    gap: 8px;
    padding: 11px;
    border-radius: 14px;
  }

  .menu-ai-parse-card strong {
    font-size: 14px;
  }

  .menu-mobile-card-list {
    display: grid;
    gap: 12px;
  }

  .menu-mobile-card {
    display: grid;
    gap: 12px;
    padding: 13px;
    border: 1px solid rgba(226, 232, 240, 0.95);
    border-radius: 18px;
    background: linear-gradient(180deg, #ffffff, #f8fafc);
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
  }

  .menu-mobile-card-head {
    align-items: start;
  }

  .menu-mobile-card .plan-ingredient-cell {
    display: grid;
    gap: 4px;
    min-width: 0;
  }

  .menu-mobile-card .plan-ingredient-cell strong {
    color: #0f172a;
    font-size: 15px;
    line-height: 1.25;
  }

  .menu-mobile-card .plan-ingredient-cell small,
  .menu-mobile-card-note,
  .menu-mobile-data-row small {
    color: #64748b;
    font-size: 12px;
    line-height: 1.45;
  }

  .menu-mobile-card .status-chip {
    min-height: 28px;
    padding-inline: 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 800;
  }

  .menu-mobile-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .menu-mobile-metric {
    display: grid;
    gap: 4px;
    min-width: 0;
    padding: 9px;
    border-radius: 14px;
    background: #ffffff;
    border: 1px solid rgba(226, 232, 240, 0.95);
  }

  .menu-mobile-metric.emphasis {
    background: #eff6ff;
    border-color: rgba(37, 99, 235, 0.18);
  }

  .menu-mobile-metric span {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
  }

  .menu-mobile-metric strong {
    color: #0f172a;
    font-size: 14px;
    line-height: 1.2;
  }

  .menu-mobile-metric small {
    color: #94a3b8;
    font-size: 10px;
    line-height: 1.35;
  }

  .menu-mobile-data-row {
    display: grid;
    gap: 4px;
    padding: 9px 11px;
    border-radius: 14px;
    background: #ffffff;
    border: 1px solid rgba(226, 232, 240, 0.95);
  }

  .menu-mobile-data-row.secondary {
    background: #f8fafc;
  }

  .menu-mobile-data-row > span {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
  }

  .menu-mobile-data-row strong {
    color: #0f172a;
    font-size: 14px;
    line-height: 1.35;
  }

  .menu-mobile-card-note {
    margin: 0;
  }

  .menu-mobile-card-note.secondary {
    margin-top: -6px;
  }

  .menu-plan-row-actions.mobile {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    margin-top: 0;
  }

  .menu-plan-row-actions.mobile :deep(.el-button) {
    width: 100%;
    min-height: 44px;
    margin-left: 0;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 800;
  }

  .ingredient-mobile-card .price-chip.avg {
    min-height: 28px;
    padding-inline: 10px;
    border-radius: 999px;
  }

  .menu-mobile-empty-state {
    min-height: 118px;
    padding: 18px 16px;
    border-radius: 18px;
  }

  .menu-mobile-empty-state p {
    max-width: none;
  }
}

.menu-ai-parse-panel {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.96), rgba(255, 255, 255, 0.98));
}

.menu-ai-parse-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.menu-ai-parse-head h2 {
  margin: 0;
  color: var(--ink-900);
  font-size: 16px;
  line-height: 1.25;
}

.menu-ai-parse-head span,
.menu-ai-parse-card small {
  color: var(--ink-500);
  font-size: 11px;
  line-height: 1.4;
}

.menu-ai-parse-list {
  display: grid;
  gap: 8px;
}

.menu-guidance-card.is-parse-ready {
  align-content: start;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.96), rgba(255, 255, 255, 0.98));
  border-color: rgba(37, 99, 235, 0.18);
}

.menu-guidance-card.is-parse-ready .menu-ai-parse-head {
  padding-bottom: 2px;
}

.menu-ai-parse-list.desktop {
  max-height: 286px;
  overflow: auto;
  padding-right: 2px;
}

.menu-ai-parse-card {
  display: grid;
  gap: 7px;
  padding: 10px;
  border: 1px solid rgba(219, 234, 254, 0.9);
  border-radius: 10px;
  background: #ffffff;
}

.menu-ai-parse-card strong {
  color: var(--ink-900);
  font-size: 13px;
  line-height: 1.25;
}

.menu-ai-parse-card div {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.menu-ai-parse-card div span {
  min-height: 24px;
  padding: 5px 8px;
  border-radius: 999px;
  background: rgba(219, 234, 254, 0.72);
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.menu-mobile-tag-row {
  margin-top: -2px;
}

.plan-source-tags {
  margin-top: 4px;
}

.source-tier-chip {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
}

.source-tier-chip.primary {
  border: 1px solid rgba(37, 99, 235, 0.2);
  background: rgba(219, 234, 254, 0.72);
  color: #1d4ed8;
}

.source-tier-chip.secondary {
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(241, 245, 249, 0.92);
  color: #475569;
}

.menu-mobile-empty-state {
  min-height: 92px;
  padding: 13px 14px;
  align-content: center;
}

.menu-mobile-empty-state strong {
  font-size: 13px;
  line-height: 1.25;
}

.menu-mobile-empty-state p {
  max-width: 260px;
  font-size: 11px;
  line-height: 1.45;
}

.menu-desktop-empty-state {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 7px;
  min-height: 112px;
  padding: 14px;
  text-align: center;
}

.menu-desktop-empty-state.compact {
  min-height: 96px;
}

.menu-desktop-empty-state strong {
  color: var(--ink-900);
  font-size: 13px;
  line-height: 1.25;
}

.menu-desktop-empty-state p {
  max-width: 320px;
  margin: 0;
  color: var(--ink-500);
  font-size: 11px;
  line-height: 1.45;
}
</style>
