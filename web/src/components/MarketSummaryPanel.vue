<template>
  <section
    v-loading="loading"
    element-loading-text="正在更新右侧报价..."
    element-loading-background="rgba(247, 248, 250, 0.72)"
    class="panel market-panel content-shell-panel"
  >
    <div class="panel-header content-panel-header">
      <div class="panel-header-copy">
        <p class="panel-kicker">实时汇总</p>
        <h2>汇总行情</h2>
        <p class="panel-hint">按商品聚合报价，点行直接进入单品趋势。</p>
      </div>
      <div class="inline-actions compact-actions market-header-actions">
        <el-input
          :model-value="keyword"
          type="search"
          inputmode="search"
          enterkeyhint="search"
          aria-label="表内搜索商品"
          placeholder="表内搜索商品"
          clearable
          @update:model-value="emit('keyword-change', $event || '')"
        />
        <div class="table-stat-chip">{{ sortedRows.length }} 条</div>
      </div>
    </div>
    <div v-if="isMobileViewport" class="market-mobile-shop-shell">
      <aside class="market-mobile-category-rail">
        <button
          v-for="item in categoryTabs"
          :key="item.key"
          type="button"
          class="market-mobile-category-item"
          :class="{ active: currentCategory === item.key }"
          @click="emit('update:active-category', item.key)"
        >
          <strong>{{ item.label }}</strong>
          <small>{{ item.count }}</small>
        </button>
      </aside>
      <div class="market-mobile-shop-main">
        <div v-if="topSummary && sortedRows.length" class="market-mobile-intro-card">
          <p class="panel-kicker">本地行情速览</p>
          <h3>{{ currentCategory === '全部' ? '全部食材' : currentCategory }} · {{ locationLabel || '本地市场' }}</h3>
          <div class="market-mobile-intro-price">
            <strong>{{ formatPrice(topSummary.average_price) }}</strong>
            <small>{{ topSummary.price_unit_basis || '元/公斤' }}</small>
          </div>
          <div class="market-mobile-intro-meta">
            <span>{{ topSummary.product_name }}</span>
            <span>最低价 {{ topSummary.lowest_price_site || '-' }}</span>
            <span>{{ topSummary.market_count || 0 }} 个市场可比</span>
          </div>
        </div>

        <div class="market-mobile-quick-filters">
          <button
            v-for="item in quickFilterOptions"
            :key="item.key"
            type="button"
            class="market-mobile-filter-chip"
            :class="{ active: activeQuickFilter === item.key }"
            @click="activeQuickFilter = item.key"
          >
            {{ item.label }}
          </button>
        </div>

        <div class="market-mobile-list" data-testid="market-mobile-list">
          <button
            v-for="row in pagedRows"
            :key="`${row.price_identity_key || row.product_name}-${row.lowest_price_site || ''}`"
            type="button"
            class="market-mobile-card mall-market-card"
            data-testid="market-mobile-card"
            @click="handleRowClick(row)"
          >
            <div class="market-mobile-card-head">
              <div class="market-mobile-product">
                <div class="market-mobile-product-top">
                  <span class="market-mobile-category-badge">{{ resolveMarketCategory(row.product_name) }}</span>
                  <span class="market-mobile-cover-chip">{{ row.market_count || 0 }} 个市场</span>
                </div>
                <strong>{{ row.product_name }}</strong>
                <div class="product-cell-meta">
                  <span>{{ row.region_label || locationLabel || '本地市场' }}</span>
                  <span>{{ row.price_unit_basis || '元/公斤' }}</span>
                </div>
              </div>
              <div class="market-mobile-main-price">
                <span>今日参考价</span>
                <strong>{{ formatPrice(row.average_price) }}</strong>
              </div>
            </div>
            <div class="market-mobile-quote-stack">
              <div class="market-mobile-quote-row">
                <span>最低价</span>
                <strong>{{ formatPrice(row.lowest_price) }}</strong>
                <small>{{ row.lowest_price_site || '-' }}</small>
              </div>
              <div class="market-mobile-quote-row">
                <span>最高价</span>
                <strong>{{ formatPrice(row.highest_price) }}</strong>
                <small>{{ row.highest_price_site || '-' }}</small>
              </div>
            </div>
            <div class="market-mobile-footer">
              <span class="spread-value">{{ formatSpreadLabel(row.lowest_price, row.highest_price) }}</span>
              <span class="market-mobile-action">{{ buildActionLabel(row) }}</span>
            </div>
          </button>
          <div v-if="!pagedRows.length" class="table-empty-state">
            <strong>当前没有可展示的商品报价</strong>
            <p>可先清空筛选条件、刷新报价，或切换到其他地区查看。</p>
            <el-button v-if="keyword" type="primary" plain @click="emit('keyword-change', '')">清空搜索</el-button>
          </div>
        </div>
      </div>
    </div>
    <template v-else>
      <div class="market-snapshot" v-if="topSummary && sortedRows.length">
        <div class="snapshot-pill emphasis-pill">
          <span>最低均价</span>
          <strong>{{ topSummary.product_name }}</strong>
          <small>{{ formatPrice(topSummary.average_price) }} / {{ topSummary.price_unit_basis || '元/公斤' }}</small>
        </div>
        <div class="snapshot-pill">
          <span>最低价市场</span>
          <strong>{{ topSummary.lowest_price_site || '-' }}</strong>
          <small>{{ formatPrice(topSummary.lowest_price) }}</small>
        </div>
        <div class="snapshot-pill">
          <span>最高价市场</span>
          <strong>{{ topSummary.highest_price_site || '-' }}</strong>
          <small>{{ formatPrice(topSummary.highest_price) }}</small>
        </div>
        <div class="snapshot-pill">
          <span>覆盖商品</span>
          <strong>{{ sortedRows.length }}</strong>
          <small>{{ topSummary.market_count || 0 }} 个市场参与比较</small>
        </div>
      </div>
      <el-table :data="pagedRows" :height="tableHeight" @row-click="handleRowClick">
      <el-table-column label="商品" min-width="220" fixed="left">
        <template #default="{ row }">
          <div class="product-cell">
            <strong>{{ row.product_name }}</strong>
            <div class="product-cell-meta">
              <span>{{ row.region_label || '未标注地区' }}</span>
              <span>{{ row.price_unit_basis || '元/公斤' }}</span>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="market_count" label="覆盖" width="74" />
      <el-table-column label="最低价（元/公斤）" width="132" sortable>
        <template #default="{ row }">
          <span class="price-chip low">{{ formatPrice(row.lowest_price) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="lowest_price_site" label="最低价市场" min-width="150" show-overflow-tooltip />
      <el-table-column label="最高价（元/公斤）" width="132" sortable>
        <template #default="{ row }">
          <span class="price-chip high">{{ formatPrice(row.highest_price) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="highest_price_site" label="最高价市场" min-width="150" show-overflow-tooltip />
      <el-table-column label="均价（元/公斤）" width="132" sortable>
        <template #default="{ row }">
          <span class="price-chip avg">{{ formatPrice(row.average_price) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="价差" width="92">
        <template #default="{ row }">
          <span class="spread-value">{{ formatSpread(row.lowest_price, row.highest_price) }}</span>
        </template>
      </el-table-column>
      <template #empty>
        <div class="table-empty-state">
          <strong>当前没有可展示的商品报价</strong>
          <p>可先清空筛选条件、刷新报价，或切换到其他地区查看。</p>
          <el-button v-if="keyword" type="primary" plain @click="emit('keyword-change', '')">清空搜索</el-button>
        </div>
      </template>
      </el-table>
    </template>
    <div v-if="sortedRows.length > pageSize" class="table-pagination-bar">
      <span>共 {{ sortedRows.length }} 条，当前第 {{ currentPage }} / {{ pageCount }} 页</span>
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :layout="paginationLayout"
        :total="sortedRows.length"
        size="small"
      />
    </div>

    <details class="source-coverage-block" v-if="sourceCoverageRows.length">
      <summary class="source-coverage-summary">
        <div>
          <p class="panel-kicker">来源覆盖</p>
          <strong>来源覆盖</strong>
        </div>
        <span>{{ sourceCoverageRows.length }} 个来源</span>
      </summary>
      <div class="source-coverage-inner">
        <div v-if="isMobileViewport" class="source-coverage-card-list">
          <article
            v-for="row in sourceCoverageRows"
            :key="`${row.configured_name || row.source_name}-${row.source_url}`"
            class="source-coverage-card"
          >
            <div class="source-coverage-card-head">
              <div>
                <strong>{{ row.configured_name || row.source_name || '未命名来源' }}</strong>
                <p>{{ row.latest_capture || '暂无抓取记录' }}</p>
                <div class="source-meta-list" v-if="row.market_scope || row.market_category || row.channel">
                  <span v-if="row.market_scope" class="source-meta-chip">{{ row.market_scope }}</span>
                  <span v-if="row.market_category" class="source-meta-chip">{{ row.market_category }}</span>
                  <span v-if="row.channel" class="source-meta-chip">{{ row.channel }}</span>
                </div>
              </div>
              <span :class="coverageStatusClass(row.status)">{{ row.status || '-' }}</span>
            </div>
            <p v-if="row.notes" class="source-coverage-note">{{ row.notes }}</p>
            <div class="source-coverage-card-grid">
              <div class="source-coverage-stat">
                <span>入库键数</span>
                <strong>{{ row.product_key_count || 0 }}</strong>
              </div>
              <div class="source-coverage-stat">
                <span>可比商品</span>
                <strong>{{ row.comparable_item_count || 0 }}</strong>
              </div>
              <div class="source-coverage-stat">
                <span>站内去重</span>
                <strong>{{ row.source_item_count || 0 }}</strong>
              </div>
              <div class="source-coverage-stat">
                <span>失败数</span>
                <strong>{{ row.failed_count || 0 }}</strong>
              </div>
            </div>
          </article>
        </div>
        <el-table v-else :data="sourceCoverageRows" height="240">
          <el-table-column prop="configured_name" label="来源" min-width="160" />
          <el-table-column label="属性" min-width="220">
            <template #default="{ row }">
              <div class="source-meta-list">
                <span v-if="row.market_scope" class="source-meta-chip">{{ row.market_scope }}</span>
                <span v-if="row.market_category" class="source-meta-chip">{{ row.market_category }}</span>
                <span v-if="row.channel" class="source-meta-chip">{{ row.channel }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <span :class="coverageStatusClass(row.status)">{{ row.status || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="product_key_count" label="入库键数" width="96" />
          <el-table-column prop="source_item_count" label="站内去重" width="96" />
          <el-table-column prop="comparable_item_count" label="可比商品" width="96" />
          <el-table-column prop="market_count" label="市场数" width="84" />
          <el-table-column prop="latest_capture" label="最近抓取" min-width="160" show-overflow-tooltip />
          <el-table-column prop="failed_count" label="失败数" width="84" />
          <el-table-column prop="notes" label="备注" min-width="220" show-overflow-tooltip />
        </el-table>
      </div>
    </details>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { MarketSummaryItem, SourceCoverageItem } from '../types'
import { useViewport } from '../composables/useViewport'
import { buildMarketCategoryTabs, resolveMarketCategory } from '../utils/marketCategories'

const props = defineProps<{
  rows: MarketSummaryItem[]
  sourceCoverageRows: SourceCoverageItem[]
  keyword: string
  activeCategory?: string
  locationLabel?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  (event: 'keyword-change', value: string): void
  (event: 'select-product', identityKey: string): void
  (event: 'update:active-category', value: string): void
}>()

const { isMobileViewport, isNarrowViewport } = useViewport()
const activeQuickFilter = ref<'all' | 'local' | 'cheap' | 'wide' | 'volatile'>('all')
const quickFilterOptions = [
  { key: 'all', label: '全部' },
  { key: 'local', label: '本地优先' },
  { key: 'cheap', label: '低价优先' },
  { key: 'wide', label: '覆盖广' },
  { key: 'volatile', label: '波动大' },
] as const

function handleRowClick(row: MarketSummaryItem) {
  if (row.price_identity_key) {
    emit('select-product', row.price_identity_key)
  }
}

const categoryTabs = computed(() => buildMarketCategoryTabs(props.rows))
const currentCategory = computed(() => {
  if (!props.activeCategory) {
    return '全部'
  }
  return categoryTabs.value.some((item) => item.key === props.activeCategory) ? props.activeCategory : '全部'
})
const topSummary = computed(() => {
  if (!sortedRows.value.length) return null
  const rowsWithPrice = sortedRows.value.filter((row) => row.average_price != null && !Number.isNaN(Number(row.average_price)))
  if (!rowsWithPrice.length) {
    return sortedRows.value[0]
  }
  return [...rowsWithPrice].sort((left, right) => Number(left.average_price) - Number(right.average_price))[0]
})

const sortedRows = computed(() => {
  const keyword = props.keyword.trim().toLowerCase()
  const categoryFilteredRows = props.rows.filter((row) => {
    if (currentCategory.value === '全部') {
      return true
    }
    return resolveMarketCategory(row.product_name) === currentCategory.value
  })
  const keywordFilteredRows = keyword
    ? categoryFilteredRows.filter((row) =>
        [row.product_name, row.region_label, row.lowest_price_site, row.highest_price_site, resolveMarketCategory(row.product_name)]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(keyword)),
      )
    : categoryFilteredRows

  const rows = [...keywordFilteredRows]
  if (activeQuickFilter.value === 'cheap') {
    return rows.sort((left, right) => Number(left.average_price || Number.POSITIVE_INFINITY) - Number(right.average_price || Number.POSITIVE_INFINITY))
  }
  if (activeQuickFilter.value === 'wide') {
    return rows.sort((left, right) => Number(right.market_count || 0) - Number(left.market_count || 0))
  }
  if (activeQuickFilter.value === 'volatile') {
    return rows.sort((left, right) => buildSpread(right.lowest_price, right.highest_price) - buildSpread(left.lowest_price, left.highest_price))
  }
  if (activeQuickFilter.value === 'local' && props.locationLabel) {
    return rows.sort((left, right) => Number(isLocalRow(right)) - Number(isLocalRow(left)))
  }
  return rows
})
const currentPage = ref(1)
const viewportHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 960)
const pageSize = computed(() => {
  if (isMobileViewport.value) return 8
  return isNarrowViewport.value ? 60 : 80
})
const pageCount = computed(() => Math.max(1, Math.ceil(sortedRows.value.length / pageSize.value)))
const paginationLayout = computed(() => (isMobileViewport.value ? 'prev, next' : 'prev, pager, next'))
const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return sortedRows.value.slice(start, start + pageSize.value)
})

const tableHeight = computed(() => {
  const minimumHeight = isNarrowViewport.value ? 460 : 520
  const targetHeight = Math.max(minimumHeight, viewportHeight.value - (isNarrowViewport.value ? 266 : 246))
  if (!pagedRows.value.length) return targetHeight
  if (pagedRows.value.length <= 8) return Math.max(targetHeight, 580)
  if (pagedRows.value.length <= 18) return Math.max(targetHeight, 680)
  return Math.max(targetHeight, 760)
})

function formatPrice(value?: number | null) {
  return value == null || Number.isNaN(Number(value)) ? '-' : `${Number(value).toFixed(2)}`
}

function formatSpread(lowest?: number | null, highest?: number | null) {
  if (lowest == null || highest == null) return '-'
  return (Number(highest) - Number(lowest)).toFixed(2)
}

function buildSpread(lowest?: number | null, highest?: number | null) {
  if (lowest == null || highest == null) {
    return 0
  }
  return Math.max(Number(highest) - Number(lowest), 0)
}

function formatSpreadLabel(lowest?: number | null, highest?: number | null) {
  if (lowest == null || highest == null) {
    return '价差待同步'
  }
  return `价差 ${formatSpread(lowest, highest)}`
}

function isLocalRow(row: MarketSummaryItem) {
  const locationLabel = String(props.locationLabel || '').trim()
  if (!locationLabel) {
    return false
  }
  return String(row.region_label || '').includes(locationLabel)
}

function buildActionLabel(row: MarketSummaryItem) {
  if (row.lowest_price_site) {
    return `看 ${row.lowest_price_site} 走势`
  }
  if (Number(row.market_count || 0) > 1) {
    return '去比各市场走势'
  }
  return '查看单市场行情'
}

function coverageStatusClass(status?: string | null) {
  if (status === '已入库') return 'coverage-chip ok'
  if (status === '重复偏多') return 'coverage-chip warn'
  if (status === '抓取异常') return 'coverage-chip error'
  return 'coverage-chip'
}

function syncViewportHeight() {
  viewportHeight.value = window.innerHeight
}

onMounted(() => {
  window.addEventListener('resize', syncViewportHeight)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncViewportHeight)
})

watch(sortedRows, () => {
  if (currentPage.value > pageCount.value) {
    currentPage.value = 1
  }
}, { deep: true })

watch(pageSize, () => {
  currentPage.value = 1
})
</script>

<style scoped>
.market-mobile-shop-shell {
  display: grid;
  grid-template-columns: 74px minmax(0, 1fr);
  gap: 12px;
}

.market-mobile-category-rail {
  display: grid;
  gap: 8px;
  align-content: start;
}

.market-mobile-category-item,
.market-mobile-filter-chip {
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(248, 250, 252, 0.94);
  color: var(--ink-900);
  font: inherit;
  cursor: pointer;
}

.market-mobile-category-item {
  display: grid;
  gap: 2px;
  min-height: 62px;
  padding: 10px 8px;
  border-radius: 18px;
  text-align: center;
}

.market-mobile-category-item strong {
  font-size: 12px;
  line-height: 1.25;
}

.market-mobile-category-item small {
  color: var(--ink-500);
  font-size: 10px;
}

.market-mobile-category-item.active,
.market-mobile-filter-chip.active {
  border-color: rgba(37, 99, 235, 0.24);
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.08), rgba(255, 255, 255, 0.96));
  box-shadow: 0 12px 20px rgba(15, 23, 42, 0.08);
}

.market-mobile-shop-main,
.market-mobile-quick-filters,
.market-mobile-quote-stack {
  display: grid;
  gap: 10px;
}

.market-mobile-intro-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 22px;
  border: 1px solid rgba(96, 165, 250, 0.18);
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.94), rgba(255, 255, 255, 0.96));
}

.market-mobile-intro-card h3 {
  margin: 0;
  color: var(--ink-900);
  font-size: 18px;
  line-height: 1.15;
}

.market-mobile-intro-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.market-mobile-intro-price strong {
  color: var(--accent-blue);
  font-size: 28px;
  line-height: 1;
}

.market-mobile-intro-price small,
.market-mobile-intro-meta span,
.market-mobile-main-price span,
.market-mobile-cover-chip,
.market-mobile-quote-row span,
.market-mobile-quote-row small {
  color: var(--ink-500);
  font-size: 10px;
}

.market-mobile-intro-meta,
.market-mobile-product-top {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.market-mobile-quick-filters {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.market-mobile-filter-chip {
  min-height: 38px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}

.mall-market-card {
  gap: 12px;
}

.market-mobile-main-price {
  display: grid;
  justify-items: end;
  gap: 4px;
}

.market-mobile-main-price strong {
  color: var(--accent-blue);
  font-size: 22px;
  line-height: 1;
}

.market-mobile-category-badge,
.market-mobile-cover-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
}

.market-mobile-category-badge {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
  font-size: 10px;
  font-weight: 700;
}

.market-mobile-cover-chip {
  background: rgba(239, 246, 255, 0.94);
}

.market-mobile-quote-row {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr) minmax(0, 1.3fr);
  align-items: baseline;
  gap: 8px;
}

.market-mobile-quote-row strong {
  color: var(--ink-900);
  font-size: 14px;
  line-height: 1.2;
}

.market-mobile-action {
  color: var(--accent-blue);
  font-size: 12px;
  font-weight: 700;
}

@media (max-width: 390px) {
  .market-mobile-shop-shell {
    grid-template-columns: 68px minmax(0, 1fr);
    gap: 10px;
  }

  .market-mobile-quick-filters {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .market-mobile-quote-row {
    grid-template-columns: 1fr;
  }

  .market-mobile-main-price {
    justify-items: start;
  }
}
</style>
