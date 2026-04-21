<template>
  <section class="panel trend-workspace-panel content-shell-panel">
    <div class="panel-header content-panel-header">
      <div>
        <p class="panel-kicker">价格走势</p>
        <h2>单品趋势</h2>
        <p v-if="!isMobileViewport" class="panel-hint">同一商品只跟自己比，默认先看跨市场走势。</p>
      </div>
      <div class="inline-actions">
        <el-radio-group aria-label="趋势模式切换" :model-value="trendMode" @change="emit('update:trend-mode', $event)">
          <el-radio-button value="cross_market">跨市场</el-radio-button>
          <el-radio-button value="single_market">单市场</el-radio-button>
        </el-radio-group>
      </div>
    </div>
    <div v-if="selectedIdentityKey && !isMobileViewport" class="trend-summary-strip trend-summary-strip-compact">
      <div class="summary-card compact-summary-card">
        <span>当前商品</span>
        <strong>{{ currentProductLabel || '-' }}</strong>
        <small>{{ currentProductCoverageLabel }}</small>
      </div>
      <div class="summary-card compact-summary-card">
        <span>比较方式</span>
        <strong>{{ trendMode === 'cross_market' ? '跨市场' : '单市场' }}</strong>
        <small>{{ currentScopeLabel }}</small>
      </div>
      <div class="summary-card compact-summary-card">
        <span>走势记录</span>
        <strong>{{ trendRows.length }}</strong>
        <small>{{ availableSites.length || 0 }} 个市场</small>
      </div>
      <div v-if="productSummary" class="summary-card compact-summary-card">
        <span>最近更新</span>
        <strong>{{ productSummary.latest_captured_at ?? '-' }}</strong>
        <small>{{ productSummary.current_lowest_site ?? '-' }}</small>
      </div>
    </div>
    <div class="trend-toolbar content-toolbar">
      <div class="trend-picker-inline">
        <span>商品</span>
        <el-select
          :model-value="selectedIdentityKey"
          aria-label="选择商品"
          placeholder="选择单品"
          filterable
          @change="emit('select-product', $event)"
        >
          <el-option
            v-for="item in productOptions"
            :key="item.price_identity_key"
            :label="item.price_identity_label"
            :value="item.price_identity_key"
          />
        </el-select>
      </div>
      <div v-if="trendMode === 'single_market'" class="trend-picker-inline site-inline">
        <span>市场</span>
        <el-select
          :model-value="selectedSiteName"
          aria-label="选择市场"
          clearable
          placeholder="选择单个市场"
          @change="emit('update:selected-site-name', $event || '')"
        >
          <el-option v-for="site in availableSites" :key="site" :label="site" :value="site" />
        </el-select>
      </div>
      <div v-if="!isMobileViewport" class="trend-toolbar-count">{{ productOptions.length }} 个商品</div>
    </div>
    <div v-if="isMobileViewport && (currentProductLabel || currentSiteLabel || currentScopeLabel)" class="trend-selection-summary">
      <div v-if="currentProductLabel" class="trend-selection-item">
        <span>当前商品</span>
        <strong>{{ currentProductLabel }}</strong>
        <small>{{ currentProductCoverageLabel }}</small>
      </div>
      <div v-if="currentScopeLabel" class="trend-selection-item">
        <span>{{ trendMode === 'cross_market' ? '比较范围' : '当前市场' }}</span>
        <strong>{{ currentScopeLabel }}</strong>
      </div>
    </div>
    <div v-if="selectedIdentityKey" class="trend-content-shell" :class="{ 'is-loading': loading }">
      <div v-if="currentProductOption && currentProductOption.site_count <= 1" class="trend-single-source-tip">
        当前商品只匹配到 1 个市场，现有数据里通常只会看到 {{ availableSites[0] || '当前来源' }}。
      </div>
      <div v-if="isComparisonMode" class="trend-compare-tip">
        跨市场会补齐断档；每页只展示一组完全重合的价格线。
      </div>
      <div v-if="isMobileViewport" class="trend-mobile-detail-hero">
        <div class="trend-mobile-detail-head">
          <div>
            <p class="panel-kicker">商品详情</p>
            <h3>{{ currentProductLabel || '当前商品' }}</h3>
          </div>
          <span class="trend-mobile-hero-chip">{{ currentScopeLabel }}</span>
        </div>
        <div class="trend-mobile-hero-price">
          <strong>{{ trendAveragePriceLabel }}</strong>
          <small>今日参考价</small>
        </div>
        <div class="trend-mobile-hero-tags">
          <span>最低 {{ numericProductSummary.current_lowest_price_label }}</span>
          <span>最高 {{ numericProductSummary.current_highest_price_label }}</span>
          <span>价差 {{ priceSpanLabel }}</span>
        </div>
      </div>
      <div v-if="isMobileViewport && decisionCards.length" class="trend-mobile-decision-grid">
        <article v-for="item in decisionCards" :key="item.title" class="trend-mobile-decision-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.title }}</strong>
          <small>{{ item.detail }}</small>
        </article>
      </div>
      <div v-if="productSummary && isMobileViewport" class="trend-mobile-overview">
        <div class="trend-mobile-pill">
          <span>最低价</span>
          <strong>{{ productSummary.current_lowest_price ?? '-' }}</strong>
          <small>{{ productSummary.current_lowest_site ?? '-' }}</small>
        </div>
        <div class="trend-mobile-pill">
          <span>均价</span>
          <strong>{{ productSummary.average_price ?? '-' }}</strong>
          <small>{{ productSummary.latest_captured_at ?? '-' }}</small>
        </div>
        <div class="trend-mobile-pill">
          <span>市场数</span>
          <strong>{{ availableSites.length || 0 }}</strong>
          <small>{{ currentOverviewRangeLabel }}</small>
        </div>
      </div>
      <div v-else-if="productSummary" class="trend-summary-strip">
        <div class="summary-card compact-summary-card">
          <span>最低价</span>
          <strong>{{ productSummary.current_lowest_price ?? '-' }}</strong>
          <small>{{ productSummary.current_lowest_site ?? '-' }}</small>
        </div>
        <div class="summary-card compact-summary-card">
          <span>最高价</span>
          <strong>{{ productSummary.current_highest_price ?? '-' }}</strong>
          <small>{{ productSummary.current_highest_site ?? '-' }}</small>
        </div>
        <div class="summary-card compact-summary-card">
          <span>平均价</span>
          <strong>{{ productSummary.average_price ?? '-' }}</strong>
          <small>{{ productSummary.latest_captured_at ?? '-' }}</small>
        </div>
        <div class="summary-card compact-summary-card">
          <span>市场数</span>
          <strong>{{ availableSites.length || 0 }}</strong>
          <small>{{ currentOverviewRangeLabel }}</small>
        </div>
      </div>
      <div class="trend-main-grid">
        <div>
          <div v-if="productSummary && !isMobileViewport" class="trend-insight-strip">
            <span>最低价市场：{{ productSummary.current_lowest_site ?? '-' }}</span>
            <span>最高价市场：{{ productSummary.current_highest_site ?? '-' }}</span>
            <span>最近更新：{{ productSummary.latest_captured_at ?? '-' }}</span>
          </div>
          <div class="trend-chart-shell">
            <button
              v-if="!isMobileViewport && isComparisonMode && comparisonPageCount > 1"
              type="button"
              class="trend-chart-nav trend-chart-nav-left"
              :disabled="comparisonPageIndex <= 0"
              @click="comparisonPageIndex -= 1"
            >
              ◀
            </button>
            <div ref="trendChartRef" class="trend-chart" :style="{ height: chartHeight }"></div>
            <button
              v-if="!isMobileViewport && isComparisonMode && comparisonPageCount > 1"
              type="button"
              class="trend-chart-nav trend-chart-nav-right"
              :disabled="comparisonPageIndex >= comparisonPageCount - 1"
              @click="comparisonPageIndex += 1"
            >
              ▶
            </button>
            <div v-if="!isMobileViewport && isComparisonMode && comparisonPageCount > 1" class="trend-chart-page-indicator">
              {{ comparisonPageIndex + 1 }} / {{ comparisonPageCount }}
            </div>
          </div>
          <div v-if="isMobileViewport && isComparisonMode && comparisonPageCount > 1" class="trend-chart-mobile-nav">
            <div class="trend-chart-mobile-buttons">
              <button
                type="button"
                class="trend-chart-mobile-button"
                aria-label="查看上一组趋势"
                :disabled="comparisonPageIndex <= 0"
                @click="comparisonPageIndex -= 1"
              >
                上一组
              </button>
              <button
                type="button"
                class="trend-chart-mobile-button"
                aria-label="查看下一组趋势"
                :disabled="comparisonPageIndex >= comparisonPageCount - 1"
                @click="comparisonPageIndex += 1"
              >
                下一组
              </button>
            </div>
            <span class="trend-chart-mobile-indicator" data-testid="trend-mobile-page-indicator">
              {{ comparisonPageIndex + 1 }} / {{ comparisonPageCount }}
            </span>
          </div>
          <div v-if="isMobileViewport && marketCompareCards.length" class="trend-mobile-market-board">
            <div class="trend-list-head">
              <strong>市场对比</strong>
              <span>{{ marketCompareCards.length }} 个来源</span>
            </div>
            <div class="trend-mobile-market-list">
              <article v-for="item in marketCompareCards" :key="item.name" class="trend-mobile-market-card">
                <div>
                  <strong>{{ item.name }}</strong>
                  <p>{{ item.meta }}</p>
                </div>
                <div class="trend-mobile-market-value">
                  <strong>{{ item.price }}</strong>
                  <small>{{ item.rank }}</small>
                </div>
              </article>
            </div>
          </div>
        </div>
        <div class="trend-list-shell" :class="{ compact: isMobileViewport }">
          <div class="trend-list-head">
            <strong>最近记录</strong>
            <span>{{ trendListCountLabel }}</span>
          </div>
          <div v-if="recentTrendRows.length" class="trend-list">
            <div v-for="row in recentTrendRows" :key="`${row.trend_series_key || row.site_name}-${row.captured_at}-${row.current_price}`" class="trend-row">
              <div>
                <strong>{{ buildTrendSeriesName(row) }}</strong>
                <p>{{ buildTrendMeta(row) }}</p>
              </div>
              <div class="trend-price">{{ formatPrice(row.current_price) }}</div>
              <div class="trend-time">{{ formatTrendTime(row.captured_at) }}</div>
            </div>
          </div>
          <div v-else class="trend-side-empty">
            <strong>暂无走势记录</strong>
            <p>换一个商品或切换趋势模式再看。</p>
          </div>
        </div>
      </div>
      <SupplierQuotePanel
        :selected-identity-key="selectedIdentityKey"
        :product-label="currentProductLabel"
        :mobile="isMobileViewport"
      />
      <div v-if="isMobileViewport && sourceExplainers.length" class="trend-mobile-source-note">
        <strong>采购说明</strong>
        <p v-for="item in sourceExplainers" :key="item">{{ item }}</p>
      </div>
      <div v-if="loading" class="trend-loading-mask">
        <div class="trend-loading-card">
          <span class="trend-loading-dot"></span>
          <strong>正在切换商品走势</strong>
          <p>优先显示缓存，同时补拉最新记录。</p>
        </div>
      </div>
    </div>
    <div v-else class="table-empty-state trend-empty-state">
      <strong>先选择一个商品，再查看价格趋势</strong>
      <p>上方商品选择器会把同名商品在不同市场的价格放到同一条走势里。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import SupplierQuotePanel from './SupplierQuotePanel.vue'
import type { ProductOptionItem, ProductTrendRow } from '../types'
import { useViewport } from '../composables/useViewport'

const props = defineProps<{
  productOptions: ProductOptionItem[]
  selectedIdentityKey: string
  productSummary: Record<string, any> | null
  trendRows: ProductTrendRow[]
  siteOptions: string[]
  loading: boolean
  trendMode: 'cross_market' | 'single_market'
  selectedSiteName: string
}>()

const emit = defineEmits<{
  (event: 'select-product', value: string): void
  (event: 'update:trend-mode', value: 'cross_market' | 'single_market'): void
  (event: 'update:selected-site-name', value: string): void
  (event: 'refresh-trend'): void
}>()

const trendChartRef = ref<HTMLDivElement | null>(null)
const { isMobileViewport, isNarrowViewport, isShortViewport } = useViewport()
type EChartsCoreModule = typeof import('echarts/core')
let echartsModule: EChartsCoreModule | null = null
let trendChart: import('echarts/core').ECharts | null = null
let resizeObserver: ResizeObserver | null = null
const comparisonPageIndex = ref(0)

const currentProductOption = computed(() => props.productOptions.find((item) => item.price_identity_key === props.selectedIdentityKey) || null)
const availableSites = computed(() => props.siteOptions || [])
const isComparisonMode = computed(() => props.trendMode === 'cross_market')
const shouldCarryForwardPrice = computed(() => isComparisonMode.value)
const currentProductLabel = computed(() => currentProductOption.value?.price_identity_label || '')
const currentProductCoverageLabel = computed(() => {
  const siteCount = Number(currentProductOption.value?.site_count || 0)
  return siteCount ? `已覆盖 ${siteCount} 个市场` : '市场覆盖待确认'
})
const currentSiteLabel = computed(() => String(props.selectedSiteName || '').trim())
const currentScopeLabel = computed(() => (
  props.trendMode === 'cross_market'
    ? `跨市场 · ${availableSites.value.length || 0} 个市场`
    : (currentSiteLabel.value || '待选择单个市场')
))
const currentOverviewRangeLabel = computed(() => (
  props.trendMode === 'cross_market'
    ? '比较范围：跨市场'
    : `当前市场：${currentSiteLabel.value || '待选择'}`
))
const numericProductSummary = computed(() => ({
  current_lowest_price: normalizeNumericValue(props.productSummary?.current_lowest_price),
  current_highest_price: normalizeNumericValue(props.productSummary?.current_highest_price),
  average_price: normalizeNumericValue(props.productSummary?.average_price),
  current_lowest_price_label: formatPrice(normalizeNumericValue(props.productSummary?.current_lowest_price)),
  current_highest_price_label: formatPrice(normalizeNumericValue(props.productSummary?.current_highest_price)),
  average_price_label: formatPrice(normalizeNumericValue(props.productSummary?.average_price)),
}))
const trendAveragePriceLabel = computed(() => numericProductSummary.value.average_price_label || '-')
const priceSpanLabel = computed(() => {
  if (numericProductSummary.value.current_lowest_price == null || numericProductSummary.value.current_highest_price == null) {
    return '-'
  }
  return (numericProductSummary.value.current_highest_price - numericProductSummary.value.current_lowest_price).toFixed(2)
})
const chartCategories = computed(() => buildChartCategories(props.trendRows))
const allChartSeries = computed(() => buildChartSeries(props.trendRows, chartCategories.value, shouldCarryForwardPrice.value))
const comparisonSeriesPages = computed(() => buildSeriesPages(allChartSeries.value, isComparisonMode.value))
const comparisonPageCount = computed(() => comparisonSeriesPages.value.length)
const visibleChartSeries = computed(() => {
  const page = comparisonSeriesPages.value[comparisonPageIndex.value]
  return page && page.length ? page : (comparisonSeriesPages.value[0] || [])
})
const visibleSeriesNameSet = computed(() => new Set(visibleChartSeries.value.map((item) => String(item.name || '').trim()).filter(Boolean)))
const recentTrendRows = computed(() =>
  [...props.trendRows]
    .filter((row) => visibleSeriesNameSet.value.has(buildTrendSeriesName(row)))
    .sort((left, right) => String(right.captured_at || '').localeCompare(String(left.captured_at || '')))
    .slice(0, isMobileViewport.value ? 6 : 18),
)
const marketCompareCards = computed(() => {
  const latestBySeries = new Map<string, ProductTrendRow>()

  recentTrendRows.value.forEach((row) => {
    const seriesName = buildTrendSeriesName(row)
    if (!seriesName) {
      return
    }
    const existingRow = latestBySeries.get(seriesName)
    if (!existingRow || String(row.captured_at || '') > String(existingRow.captured_at || '')) {
      latestBySeries.set(seriesName, row)
    }
  })

  return Array.from(latestBySeries.values())
    .sort((left, right) => Number(left.current_price || 0) - Number(right.current_price || 0))
    .slice(0, 4)
    .map((row, index) => ({
      name: buildTrendSeriesName(row),
      meta: buildTrendMeta(row),
      price: formatPrice(row.current_price),
      rank: index === 0 ? '当前低价' : `第 ${index + 1} 位`,
    }))
})
const decisionCards = computed(() => {
  const cards: Array<{ label: string; title: string; detail: string }> = []
  const siteCount = availableSites.value.length
  const lowPrice = numericProductSummary.value.current_lowest_price
  const avgPrice = numericProductSummary.value.average_price
  const priceSpan = lowPrice != null && numericProductSummary.value.current_highest_price != null
    ? numericProductSummary.value.current_highest_price - lowPrice
    : 0

  if (siteCount <= 1) {
    cards.push({
      label: '建议动作',
      title: '先跟踪单市场',
      detail: '当前只有 1 个稳定来源，更适合先看这一个市场的连续报价。',
    })
  } else if (avgPrice != null && lowPrice != null && avgPrice - lowPrice >= 1) {
    cards.push({
      label: '建议动作',
      title: '建议优先比价采购',
      detail: `当前最低价较均价低 ${(avgPrice - lowPrice).toFixed(2)}，适合先看低价市场。`,
    })
  } else {
    cards.push({
      label: '建议动作',
      title: '建议继续观察走势',
      detail: '当前价位接近均价，先看最近 3 次报价再决定下单节奏。',
    })
  }

  cards.push({
    label: '判断依据',
    title: priceSpan >= 2 ? '跨市场价差较大' : '价格区间相对收敛',
    detail: priceSpan >= 2 ? `当前价差 ${priceSpan.toFixed(2)}，跨市场比价价值更高。` : '更适合结合单市场走势确认是否锁价。',
  })

  return cards
})
const sourceExplainers = computed(() => {
  const notes = [
    '跨市场模式会补齐断档，更适合看整体价格方向。',
    '单市场模式更适合确认具体下单来源和时间点。',
  ]
  if (currentSiteLabel.value) {
    notes.unshift(`当前已锁定 ${currentSiteLabel.value}，可继续观察这个来源的连续报价。`)
  }
  return notes
})
const chartHeight = computed(() => {
  if (!isMobileViewport.value) return isNarrowViewport.value ? '460px' : '520px'
  if (isShortViewport.value) {
    if (comparisonPageCount.value > 1 || visibleChartSeries.value.length >= 4) return '340px'
    if (chartCategories.value.length >= 10) return '316px'
    return '292px'
  }
  if (comparisonPageCount.value > 1 || visibleChartSeries.value.length >= 4) return '404px'
  if (chartCategories.value.length >= 10) return '376px'
  return '348px'
})
const trendListCountLabel = computed(() => (
  isMobileViewport.value
    ? `${recentTrendRows.value.length} / ${props.trendRows.length} 条`
    : `${props.trendRows.length} 条`
))

async function ensureTrendChart() {
  if (!trendChartRef.value) return null
  if (!echartsModule) {
    const [{ use, init }, charts, components, renderers] = await Promise.all([
      import('echarts/core'),
      import('echarts/charts'),
      import('echarts/components'),
      import('echarts/renderers'),
    ])
    use([
      charts.LineChart,
      components.GridComponent,
      components.TooltipComponent,
      components.LegendComponent,
      components.DatasetComponent,
      renderers.CanvasRenderer,
    ])
    echartsModule = { use, init } as EChartsCoreModule
  }
  if (!trendChart) {
    trendChart = echartsModule.init(trendChartRef.value)
  }
  return trendChart
}

function buildChartCategories(rows: ProductTrendRow[]) {
  return Array.from(new Set(rows.map((row) => String(row.captured_at || '').trim()).filter(Boolean))).sort()
}

function buildChartSeries(rows: ProductTrendRow[], categories: string[], carryForwardPrice: boolean) {
  const seriesBySite = new Map<string, Map<string, number>>()
  rows.forEach((row) => {
    const siteName = buildTrendSeriesName(row)
    const capturedAt = String(row.captured_at || '').trim()
    const currentPrice = Number(row.current_price)
    if (!capturedAt || Number.isNaN(currentPrice)) return
    if (!seriesBySite.has(siteName)) {
      seriesBySite.set(siteName, new Map<string, number>())
    }
    seriesBySite.get(siteName)!.set(capturedAt, currentPrice)
  })
  return Array.from(seriesBySite.entries()).map(([name, points]) => {
    let lastKnownPrice: number | null = null
    const data = categories.map((category) => {
      const currentPrice = points.get(category)
      if (currentPrice != null) {
        lastKnownPrice = currentPrice
      }
      if (currentPrice == null && !carryForwardPrice) {
        return null
      }
      if (lastKnownPrice == null) {
        return null
      }
      return {
        value: currentPrice != null ? currentPrice : lastKnownPrice,
        rawPrice: currentPrice != null ? currentPrice : lastKnownPrice,
        isActual: currentPrice != null,
      }
    })
    return {
      name,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      connectNulls: carryForwardPrice,
      showSymbol: false,
      lineStyle: { width: 3 },
      emphasis: { focus: 'series' },
      data,
      latestValue: lastKnownPrice,
    }
  })
}

function buildSeriesPages(seriesItems: Array<Record<string, any>>, comparisonMode: boolean) {
  if (!seriesItems.length) {
    return [[]]
  }
  if (!comparisonMode) {
    return [seriesItems]
  }

  const uniqueSeries: Array<Record<string, any>> = []
  const duplicateBuckets = new Map<string, Array<Record<string, any>>>()

  for (const item of seriesItems) {
    const signature = JSON.stringify(item.data)
    if (!duplicateBuckets.has(signature)) {
      duplicateBuckets.set(signature, [])
    }
    duplicateBuckets.get(signature)!.push(item)
  }

  const duplicateGroups: Array<Array<Record<string, any>>> = []
  for (const items of duplicateBuckets.values()) {
    if (items.length <= 1) {
      uniqueSeries.push(items[0])
      continue
    }
    duplicateGroups.push(items)
  }

  if (!duplicateGroups.length) {
    return [seriesItems]
  }

  const pages = duplicateGroups.map((items) => {
    const page: Array<Record<string, any>> = []
    uniqueSeries.forEach((item) => page.push(item))
    items.forEach((item) => page.push(item))
    return page
  })

  const filteredPages = pages.filter((page) => page.length >= 2)
  if (!filteredPages.length || filteredPages.length === 1) {
    return [seriesItems]
  }
  return filteredPages
}

async function renderTrendChart() {
  if (!trendChartRef.value) return
  await nextTick()
  await new Promise((resolve) => window.requestAnimationFrame(() => resolve(undefined)))
  const chart = await ensureTrendChart()
  if (!chart) return

  if (!props.trendRows.length) {
    chart.clear()
    chart.resize()
    return
  }

  const categories = chartCategories.value
  const comparisonMode = isComparisonMode.value
  const carryForwardPrice = shouldCarryForwardPrice.value
  const series = visibleChartSeries.value
  const isSparseTimeline = categories.length <= 3

  chart.resize()
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const rows = Array.isArray(params) ? params : [params]
        const axisLabel = rows[0]?.axisValueLabel || rows[0]?.axisValue || ''
        const lines = rows
          .filter((item: any) => item?.data)
          .map((item: any) => {
            const data = item.data || {}
            const value = Number(data.value)
            const comparisonText = `${value.toFixed(2)}`
            const actualMarker = data.isActual || !carryForwardPrice ? '' : '（延用上次报价）'
            return `${item.marker}${item.seriesName}：${comparisonText}${actualMarker}`
          })
        return [axisLabel, ...lines].join('<br/>')
      },
    },
    legend: {
      type: 'scroll',
      top: isMobileViewport.value ? 8 : 10,
      left: isMobileViewport.value ? 12 : 18,
      right: isMobileViewport.value ? 12 : 52,
      icon: 'roundRect',
      itemWidth: isMobileViewport.value ? 16 : 22,
      itemHeight: 4,
      itemGap: isMobileViewport.value ? 12 : 18,
      pageIconSize: 10,
      pageButtonGap: 10,
      pageButtonItemGap: 6,
      textStyle: {
        color: '#63738c',
        fontSize: isMobileViewport.value ? 11 : 12,
        fontWeight: 600,
      },
      pageTextStyle: { color: '#63738c' },
      pageIconColor: '#365486',
      pageIconInactiveColor: '#b7c4d8',
      formatter: (name: string) => formatTrendLegendLabel(name),
    },
    grid: {
      left: isSparseTimeline ? (isMobileViewport.value ? '14%' : '12%') : (isMobileViewport.value ? 18 : 24),
      right: isSparseTimeline ? (isMobileViewport.value ? '10%' : '12%') : 18,
      top: isMobileViewport.value ? 84 : 62,
      bottom: isMobileViewport.value ? 56 : 24,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: isSparseTimeline,
      axisLabel: {
        color: '#7c8ca4',
        formatter: (value: string) => formatTrendAxisLabel(value),
        hideOverlap: true,
        rotate: isMobileViewport.value ? 35 : 0,
        fontSize: isMobileViewport.value ? 10 : 12,
        margin: isMobileViewport.value ? 14 : 8,
      },
      axisLine: { lineStyle: { color: '#d7e2f0' } },
      data: categories,
    },
    yAxis: {
      type: 'value',
      name: '价格',
      axisLabel: { color: '#7c8ca4' },
      splitLine: { lineStyle: { color: 'rgba(47,128,237,0.08)' } },
    },
    series,
  }, true)
}

function formatPrice(value?: number | null) {
  return value == null || Number.isNaN(Number(value)) ? '-' : Number(value).toFixed(2)
}

function normalizeNumericValue(value: unknown) {
  if (value == null || value === '') {
    return null
  }
  const normalizedValue = Number(value)
  return Number.isNaN(normalizedValue) ? null : normalizedValue
}

function buildTrendSeriesName(row: ProductTrendRow) {
  if (row.trend_series_name) {
    return String(row.trend_series_name).trim()
  }
  const siteText = String(row.site_name || '').trim()
  const sourceName = siteText.includes('|') ? siteText.split('|')[0].trim() : siteText
  const marketText = String(row.market_name || row.city || row.province || '').trim()
  const regionText = String(row.region_label || row.city || row.province || '').trim()
  if (sourceName && marketText && regionText && marketText !== regionText) {
    return `${sourceName} · ${marketText} · ${regionText}`
  }
  if (sourceName && marketText) {
    return `${sourceName} · ${marketText}`
  }
  return sourceName || marketText || '未知市场'
}

function buildTrendMeta(row: ProductTrendRow) {
  if (row.trend_meta_label) {
    return String(row.trend_meta_label).trim()
  }
  const parts = [row.market_name, row.region_label, row.city, row.province]
    .map((item) => String(item || '').trim())
    .filter(Boolean)
  return parts.length ? Array.from(new Set(parts)).join(' · ') : '未标注市场'
}

function formatTrendAxisLabel(value?: string | null) {
  const text = String(value || '').trim()
  if (!text) return ''
  const dateMatch = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2}))?/)
  if (!dateMatch) return text
  const [, , month, day, hour, minute] = dateMatch
  if (!isMobileViewport.value) {
    return hour && minute ? `${month}-${day} ${hour}:${minute}` : `${month}-${day}`
  }
  return hour && minute ? `${month}-${day}\n${hour}:${minute}` : `${month}-${day}`
}

function formatTrendLegendLabel(name?: string | null) {
  const text = String(name || '').trim()
  if (!text) return ''
  if (!isMobileViewport.value) return text
  const segments = text.split(/[·|]/).map((item) => item.trim()).filter(Boolean)
  const candidate = segments[segments.length - 1] || text
  return candidate.length > 9 ? `${candidate.slice(0, 8)}…` : candidate
}

function formatTrendTime(value?: string | null) {
  const text = String(value || '').trim()
  if (!text) return '-'
  const dateMatch = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2}))?/)
  if (!dateMatch) return text
  const [, , month, day, hour, minute] = dateMatch
  return hour && minute ? `${month}-${day} ${hour}:${minute}` : `${month}-${day}`
}

watch(
  () => [props.trendRows, props.selectedIdentityKey, props.trendMode, props.selectedSiteName, comparisonPageIndex.value],
  async () => {
    await renderTrendChart()
  },
  { deep: true },
)

watch(
  () => [props.trendMode, props.selectedIdentityKey, comparisonPageCount.value],
  () => {
    if (comparisonPageIndex.value >= comparisonPageCount.value) {
      comparisonPageIndex.value = 0
    }
  },
)

onMounted(async () => {
  await renderTrendChart()
  window.addEventListener('resize', renderTrendChart)
  if (typeof ResizeObserver !== 'undefined' && trendChartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      void renderTrendChart()
    })
    resizeObserver.observe(trendChartRef.value)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderTrendChart)
  resizeObserver?.disconnect()
  resizeObserver = null
  trendChart?.dispose()
  trendChart = null
})
</script>

<style scoped>
.trend-single-source-tip {
  margin-bottom: 12px;
  padding: 10px 14px;
  border: 1px solid rgba(227, 160, 8, 0.28);
  border-radius: 12px;
  background: rgba(255, 248, 220, 0.88);
  color: #8a5a00;
  font-size: 13px;
  line-height: 1.5;
}

.trend-compare-tip {
  margin-bottom: 12px;
  padding: 10px 14px;
  border: 1px solid rgba(47, 128, 237, 0.16);
  border-radius: 12px;
  background: rgba(239, 246, 255, 0.94);
  color: #2f80ed;
  font-size: 13px;
  line-height: 1.5;
}

.trend-chart-shell {
  position: relative;
}

.trend-chart-nav {
  position: absolute;
  top: 50%;
  z-index: 3;
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(54, 84, 134, 0.16);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  color: #365486;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
  cursor: pointer;
  transform: translateY(-50%);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    opacity 0.18s ease;
}

.trend-chart-nav:hover:not(:disabled) {
  transform: translateY(-50%) scale(1.04);
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.16);
}

.trend-chart-nav:disabled {
  opacity: 0.38;
  cursor: not-allowed;
  box-shadow: none;
}

.trend-chart-nav-left {
  left: 10px;
}

.trend-chart-nav-right {
  right: 10px;
}

.trend-chart-page-indicator {
  position: absolute;
  right: 16px;
  bottom: 14px;
  z-index: 2;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  color: #365486;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.trend-chart-mobile-nav {
  display: grid;
  gap: 8px;
  margin-top: 10px;
}

.trend-chart-mobile-buttons {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.trend-chart-mobile-button {
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid rgba(54, 84, 134, 0.18);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.94);
  color: #365486;
  font-size: 12px;
  font-weight: 600;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
}

.trend-chart-mobile-button:disabled {
  opacity: 0.44;
}

.trend-chart-mobile-button:focus-visible,
.trend-chart-mobile-button:active {
  outline: none;
  transform: translateY(-1px);
  border-color: rgba(54, 84, 134, 0.28);
  box-shadow: 0 10px 18px rgba(15, 23, 42, 0.1);
}

.trend-chart-mobile-indicator {
  color: #63738c;
  font-size: 11px;
  text-align: right;
}

.trend-mobile-detail-hero,
.trend-mobile-decision-grid,
.trend-mobile-market-board,
.trend-mobile-source-note {
  display: grid;
  gap: 10px;
}

.trend-mobile-detail-hero {
  padding: 14px;
  border-radius: 20px;
  border: 1px solid rgba(96, 165, 250, 0.18);
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.94), rgba(255, 255, 255, 0.96));
}

.trend-mobile-detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.trend-mobile-detail-head h3 {
  margin: 4px 0 0;
  color: #112033;
  font-size: 20px;
  line-height: 1.08;
  letter-spacing: -0.04em;
}

.trend-mobile-hero-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  color: #365486;
  font-size: 10px;
  font-weight: 700;
}

.trend-mobile-hero-price {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.trend-mobile-hero-price strong {
  color: #1e40af;
  font-size: 32px;
  line-height: 1;
  letter-spacing: -0.04em;
}

.trend-mobile-hero-price small,
.trend-mobile-hero-tags span,
.trend-mobile-decision-card span,
.trend-mobile-decision-card small,
.trend-mobile-market-value small,
.trend-mobile-source-note p {
  color: #63738c;
  font-size: 11px;
  line-height: 1.5;
}

.trend-mobile-hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.trend-mobile-hero-tags span,
.trend-mobile-decision-card,
.trend-mobile-market-card,
.trend-mobile-source-note {
  padding: 10px 12px;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(248, 250, 252, 0.9);
}

.trend-mobile-decision-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.trend-mobile-decision-card strong,
.trend-mobile-market-card strong,
.trend-mobile-source-note strong {
  color: #112033;
  font-size: 14px;
  line-height: 1.3;
}

.trend-mobile-market-list {
  display: grid;
  gap: 8px;
}

.trend-mobile-market-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.trend-mobile-market-card p {
  margin: 4px 0 0;
  color: #63738c;
  font-size: 11px;
  line-height: 1.4;
}

.trend-mobile-market-value {
  display: grid;
  justify-items: end;
  gap: 4px;
}

.trend-mobile-market-value strong {
  color: #1e40af;
}

.trend-mobile-source-note p {
  margin: 0;
}

@media (max-width: 720px) {
  .trend-mobile-decision-grid {
    grid-template-columns: 1fr;
  }
}
</style>
