<template>
  <section class="panel market-panel content-shell-panel">
    <div v-if="loading && !isMobileViewport" class="market-panel-loading-mask" role="status" aria-live="polite">
      正在更新右侧报价...
    </div>
    <div v-if="!isMobileViewport" class="panel-header content-panel-header">
      <div class="panel-header-copy">
        <p class="panel-kicker">实时汇总</p>
        <h2>汇总行情</h2>
        <p class="panel-hint">按商品聚合报价，点行查看单品价格走势。</p>
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
        <button type="button" class="market-copy-visible-button" :disabled="!pagedRows.length" @click="copyVisibleProducts">
          复制本页商品
        </button>
      </div>
    </div>
    <section v-if="!isMobileViewport" class="market-command-strip">
      <div class="market-command-main">
        <div class="market-quick-filter-row" aria-label="汇总快捷筛选">
          <button
            v-for="item in quickFilterOptions"
            :key="item.key"
            type="button"
            class="market-quick-filter"
            :class="{ active: activeQuickFilter === item.key }"
            @click="activeQuickFilter = item.key"
          >
            <strong>{{ item.label }}</strong>
            <small>{{ quickFilterDescription(item.key) }}</small>
          </button>
        </div>
        <div class="market-kpi-grid">
          <article v-for="item in summaryKpis" :key="item.label" class="market-kpi-card" :class="item.tone">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.detail }}</small>
          </article>
        </div>
      </div>
      <aside v-if="marketFocusRows.length" class="market-focus-board">
        <div class="market-focus-head">
          <div>
            <p class="panel-kicker">重点商品</p>
            <strong>先看这几项</strong>
          </div>
          <span>{{ marketFocusRows.length }} 项</span>
        </div>
        <button
          v-for="row in marketFocusRows"
          :key="`${row.price_identity_key || row.product_name}-focus`"
          type="button"
          class="market-focus-card"
          @click="handleRowClick(row)"
        >
          <div>
            <strong>{{ row.product_name }}</strong>
            <small>{{ row.lowest_price_site || row.region_label || locationLabel || '本地市场' }}</small>
          </div>
          <div class="market-focus-metrics">
            <b>{{ formatPrice(row.average_price) }}</b>
            <span>{{ formatSpreadLabel(row.lowest_price, row.highest_price) }}</span>
          </div>
        </button>
      </aside>
    </section>
    <div v-if="isMobileViewport" class="market-mobile-workbench market-mobile-feed-v2" data-testid="market-mobile-list">
      <section class="market-mobile-feed-hero">
        <div>
          <p>今日菜价</p>
          <h2>{{ currentCategory === '全部' ? '全部商品' : currentCategory }}</h2>
          <small>{{ sortedRows.length }} 个商品 · {{ locationLabel || '本地市场' }}</small>
        </div>
        <button type="button" @click="resetMobileFilters">重置</button>
      </section>

      <div class="market-mobile-feed-toolbar">
        <div class="market-mobile-feed-search">
          <input
            :value="keywordDraft"
            type="search"
            inputmode="search"
            enterkeyhint="search"
            aria-label="移动端搜索商品"
            placeholder="搜索商品名称"
            @input="handleKeywordInput"
            @keyup.enter="flushKeywordInput"
          />
        </div>
        <button
          v-if="keyword || currentCategory !== '全部'"
          type="button"
          class="market-mobile-feed-clear"
          @click="resetMobileFilters"
        >
          清空
        </button>
      </div>

      <div class="market-mobile-feed-tabs" aria-label="菜价分类">
        <button
          v-for="item in categoryTabs"
          :key="item.key"
          type="button"
          :class="{ active: currentCategory === item.key }"
          @click="selectMobileCategory(item.key)"
        >
          {{ item.label }}
        </button>
      </div>

      <div class="market-mobile-feed-list">
        <div v-if="loading && !pagedRows.length" class="market-mobile-feed-skeleton-list" aria-hidden="true">
          <div v-for="index in 3" :key="`market-mobile-skeleton-${index}`" class="market-mobile-feed-skeleton-card">
            <span class="skeleton-line short"></span>
            <span class="skeleton-line"></span>
            <span class="skeleton-line"></span>
          </div>
        </div>
        <button
          v-else
          v-for="row in pagedRows"
          :key="`${row.price_identity_key || row.product_name}-${row.lowest_price_site || ''}`"
          type="button"
          class="market-mobile-feed-card"
          data-testid="market-mobile-card"
          @click="handleRowClick(row)"
        >
          <div class="market-mobile-feed-card-main">
            <div class="market-mobile-feed-thumb-shell">
              <img
                v-if="resolveMobileFoodImage(row)"
                :src="resolveMobileFoodImage(row)"
                :alt="row.product_name"
                class="market-mobile-feed-thumb-image"
                loading="lazy"
                decoding="async"
                @click.stop="openImagePreview(resolveMobileFoodImage(row), row.product_name)"
              />
              <span v-else :class="['market-mobile-food-thumb', resolveMobileFoodThumb(row)]"></span>
            </div>
            <div>
              <strong>{{ row.product_name }}</strong>
              <small>{{ formatCategoryPath(row) }}</small>
            </div>
          </div>
          <div class="market-mobile-feed-price">
            <span>均价</span>
            <b>{{ formatPrice(row.average_price) }} <small>{{ row.price_unit_basis || '元/公斤' }}</small></b>
          </div>
          <div class="market-mobile-feed-meta">
            <span>{{ formatMobileMarketName(row.lowest_price_site || row.region_label || locationLabel || '-') }}</span>
            <em>{{ formatSpreadLabel(row.lowest_price, row.highest_price) }}</em>
          </div>
          <p>{{ buildActionLabel(row) }}</p>
        </button>
        <div v-if="!loading && !pagedRows.length" class="table-empty-state market-summary-empty-state" data-testid="market-summary-empty-state">
          <strong>当前没有可展示的商品报价</strong>
          <p>可先清空筛选条件、刷新报价，或切换到其他地区查看。</p>
          <button v-if="keyword" type="button" class="market-empty-action-button" @click="clearKeyword">清空搜索</button>
        </div>
      </div>
      <div v-if="sortedRows.length > pageSize" class="table-pagination-bar mobile">
        <span>共 {{ sortedRows.length }} 条，当前第 {{ currentPage }} / {{ pageCount }} 页</span>
        <label class="page-size-select">
          <span>每页</span>
          <select v-model.number="pageSizeSetting">
            <option v-for="size in pageSizeOptions" :key="`mobile-page-size-${size}`" :value="size">{{ size }}</option>
          </select>
        </label>
        <div class="market-mobile-page-buttons" aria-label="翻页">
          <button type="button" :disabled="currentPage <= 1" @click="goToPreviousPage">上一页</button>
          <button type="button" :disabled="currentPage >= pageCount" @click="goToNextPage">下一页</button>
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
        <div class="table-empty-state market-summary-empty-state">
          <strong>当前没有可展示的商品报价</strong>
          <p>可先清空筛选条件、刷新报价，或切换到其他地区查看。</p>
          <el-button v-if="keyword" type="primary" plain @click="clearKeyword">清空搜索</el-button>
        </div>
      </template>
      </el-table>
    </template>
    <div v-if="!isMobileViewport && sortedRows.length > pageSize" class="table-pagination-bar">
      <span>共 {{ sortedRows.length }} 条，当前第 {{ currentPage }} / {{ pageCount }} 页</span>
      <label class="page-size-select">
        <span>每页</span>
        <select v-model.number="pageSizeSetting">
          <option v-for="size in pageSizeOptions" :key="`desktop-page-size-${size}`" :value="size">{{ size }}</option>
        </select>
      </label>
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :layout="paginationLayout"
        :total="sortedRows.length"
        size="small"
      />
    </div>

    <details class="source-coverage-block" v-if="sourceCoverageRows.length && !isMobileViewport">
      <summary class="source-coverage-summary">
        <div class="source-coverage-summary-copy">
          <p class="panel-kicker">来源覆盖</p>
          <strong>来源覆盖</strong>
          <div class="source-coverage-summary-stack">
            <span class="source-coverage-count">
              {{ displaySourceCoverageRows.length }} / {{ sourceCoverageViewRows.length }} 个来源
            </span>
            <div v-if="sourceTierOverview.length" class="source-tier-overview">
              <span
                v-for="item in sourceTierOverview.slice(0, 4)"
                :key="item.key"
                class="source-tier-overview-chip"
                :class="`tone-${item.tone}`"
              >
                {{ item.shortLabel }} {{ item.count }}
              </span>
            </div>
          </div>
        </div>
        <span class="source-coverage-summary-badge">{{ activeSourceTierSummary }}</span>
      </summary>
      <div class="source-coverage-inner">
        <div class="source-coverage-toolbar">
          <div class="source-tier-filter-group" aria-label="来源层级筛选">
            <button
              v-for="item in sourceTierFilterOptions"
              :key="item.key"
              type="button"
              class="source-tier-filter"
              :class="[{ active: activeSourceTierFilter === item.key }, `tone-${item.tone}`]"
              @click="activeSourceTierFilter = item.key"
            >
              <span>{{ item.label }}</span>
              <small>{{ item.count }}</small>
            </button>
          </div>
          <p class="source-coverage-toolbar-note">{{ activeSourceTierDescription }}</p>
        </div>

        <div v-if="!displaySourceCoverageRows.length" class="table-empty-state source-coverage-empty-state">
          <strong>当前层级下暂无来源</strong>
          <p>可切回全部层级，或等待下一次抓取同步这批来源。</p>
          <el-button type="primary" plain @click="activeSourceTierFilter = 'all'">查看全部来源</el-button>
        </div>
        <div v-else-if="isMobileViewport" class="source-coverage-card-list">
          <article
            v-for="row in displaySourceCoverageRows"
            :key="`${row.configured_name || row.source_name}-${row.source_url}`"
            class="source-coverage-card"
          >
            <div class="source-coverage-card-head">
              <div>
                <div class="source-tier-stack">
                  <span :class="sourceTierChipClass(row.tierMeta)">{{ row.tierMeta.label }}</span>
                  <small class="source-tier-description">{{ row.tierMeta.description }}</small>
                </div>
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
        <el-table v-else :data="displaySourceCoverageRows" height="240">
          <el-table-column label="来源" min-width="200">
            <template #default="{ row }">
              <div class="source-name-cell">
                <strong>{{ row.configured_name || row.source_name || '未命名来源' }}</strong>
                <small>{{ row.latest_capture || '暂无抓取记录' }}</small>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="层级" min-width="220">
            <template #default="{ row }">
              <div class="source-tier-cell">
                <span :class="sourceTierChipClass(row.tierMeta)">{{ row.tierMeta.label }}</span>
                <small class="source-tier-description">{{ row.tierMeta.description }}</small>
              </div>
            </template>
          </el-table-column>
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
          <el-table-column prop="failed_count" label="失败数" width="84" />
          <el-table-column prop="notes" label="备注" min-width="220" show-overflow-tooltip />
        </el-table>
      </div>
    </details>
    <teleport v-if="isMobileViewport && imagePreviewVisible" to="body">
      <div class="market-image-preview-backdrop" role="dialog" aria-modal="true" @click="closeImagePreview">
        <div class="market-image-preview-panel" @click.stop>
          <div class="market-image-preview-head">
            <strong>{{ imagePreviewTitle || '图片预览' }}</strong>
            <button type="button" aria-label="关闭图片预览" @click="closeImagePreview">关闭</button>
          </div>
          <img v-if="imagePreviewUrl" :src="imagePreviewUrl" :alt="imagePreviewTitle || ''" class="market-image-preview" />
        </div>
      </div>
    </teleport>
    <el-dialog v-if="!isMobileViewport" v-model="imagePreviewVisible" :title="imagePreviewTitle || '图片预览'" width="min(92vw, 960px)">
      <div class="market-image-preview-shell">
        <img v-if="imagePreviewUrl" :src="imagePreviewUrl" :alt="imagePreviewTitle || ''" class="market-image-preview" />
      </div>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { MarketSummaryItem, SourceCoverageItem } from '../types'
import { useViewport } from '../composables/useViewport'
import { lazyElMessage } from '../lazyElementMessage'
import { buildMarketCategoryTabs, resolveMarketCategory, resolveMarketCategoryMeta } from '../utils/marketCategories'

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

const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')
const imagePreviewTitle = ref('')
const keywordDraft = ref(props.keyword)
let keywordCommitTimer: number | undefined

const { isMobileViewport, isNarrowViewport } = useViewport()
const activeQuickFilter = ref<'all' | 'local' | 'cheap' | 'wide' | 'volatile'>('all')
type SourceTierFilterKey = 'all' | 'primary' | 'official' | 'local' | 'reference' | 'other'
type SourceTierTone = 'primary' | 'official' | 'local' | 'reference' | 'neutral'
type SourceCoverageViewItem = SourceCoverageItem & {
  tierMeta: SourceTierMeta
}

type SourceTierMeta = {
  key: Exclude<SourceTierFilterKey, 'all'>
  label: string
  shortLabel: string
  description: string
  rank: number
  tone: SourceTierTone
}

const quickFilterOptions = [
  { key: 'all', label: '全部' },
  { key: 'local', label: '本地优先' },
  { key: 'cheap', label: '低价优先' },
  { key: 'wide', label: '覆盖广' },
  { key: 'volatile', label: '波动大' },
] as const
const SOURCE_TIER_META: Record<Exclude<SourceTierFilterKey, 'all'>, SourceTierMeta> = {
  primary: {
    key: 'primary',
    label: '主价格源',
    shortLabel: '主源',
    description: '该层通常直接承担主比价口径。',
    rank: 0,
    tone: 'primary',
  },
  official: {
    key: 'official',
    label: '官方参考源',
    shortLabel: '官方',
    description: '适合交叉校验官方口径与价格波动。',
    rank: 1,
    tone: 'official',
  },
  local: {
    key: 'local',
    label: '本地市场源',
    shortLabel: '本地',
    description: '更贴近本地采购场景，适合判断落地可买性。',
    rank: 2,
    tone: 'local',
  },
  reference: {
    key: 'reference',
    label: '第三方参考源',
    shortLabel: '第三方',
    description: '补齐参考面，适合发现缺口与异常偏差。',
    rank: 3,
    tone: 'reference',
  },
  other: {
    key: 'other',
    label: '未分层来源',
    shortLabel: '未分层',
    description: '尚未归类的来源，建议结合状态和覆盖量一起看。',
    rank: 4,
    tone: 'neutral',
  },
}
const activeSourceTierFilter = ref<SourceTierFilterKey>('all')
const NON_PRODUCT_MARKET_TEXT_PATTERN = /影响|调整|建议|采购|预警|趋势|来源动态|老板|驾驶舱|复制|copy|环比|同比|变化率|增长率|下降率|增幅|降幅|涨跌幅|增速|指数|指标|存栏|出栏|产量|销量|销售量|成交量|进口量|出口量|库存|开工率|利用率|均价|平均价|监测情况|价格监测|市场价格|价格表现|市场表现|走势分析|基本概况|概况|热点|话题|原因|情况|调查|波动|下降|上涨|持平|回落|反弹|上市量|货量|产区|消费需求|节日|季节|动力煤|煤|线材|螺纹钢|钢材|热轧|中厚板|铜|铝|氧化铝|甲醇|纯碱|烧碱|合成氨|水泥|玻璃|原油|石油|汽油|柴油|化工|工业|电解铜|铝锭|豆粕|叶面肥|肥料|化肥|复合肥|农药|杀菌剂|杀虫剂|除草剂|助剂|农资|垃圾桶|收纳箱|包装|餐具|清洁|用品|耗材|纸巾|抽纸|餐巾纸|手套|托盘|保鲜膜|垃圾袋|易耗|固体酒精|火碱|锅|煎锅|不粘锅|酒水饮料|饮用水|矿物质水|纯净水|天然水|矿泉水|饮料/i
const NON_PRODUCT_MARKET_UNIT_TEXTS = new Set(['%', '％', '百分比', '百分点', '指数', '点', '条', '次', '万头', '头', '美元/桶', '元/吨', '元/平方米', '元/升'])

function isProductMarketSummaryRow(row: MarketSummaryItem) {
  const text = [row.price_identity_key, row.product_name, row.group_name, row.category, row.liancai_top_category, row.liancai_subcategory]
    .map((value) => String(value || '').trim())
    .filter(Boolean)
    .join(' ')
  if (!text || text.startsWith('/') || NON_PRODUCT_MARKET_TEXT_PATTERN.test(text)) return false
  const unitText = [row.spec_text, row.price_unit_basis]
    .map((value) => String(value || '').trim())
    .filter(Boolean)
    .join(' ')
  return !NON_PRODUCT_MARKET_UNIT_TEXTS.has(unitText)
}

const productRows = computed(() => props.rows.filter(isProductMarketSummaryRow))

function handleRowClick(row: MarketSummaryItem) {
  if (row.price_identity_key) {
    emit('select-product', row.price_identity_key)
  }
}

function scrollMobileListTop() {
  if (!isMobileViewport.value || typeof window === 'undefined') return
  window.requestAnimationFrame(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  })
}

function resetMobileFilters() {
  keywordDraft.value = ''
  flushKeywordInput()
  if (currentCategory.value !== '全部') {
    emit('update:active-category', '全部')
  }
  currentPage.value = 1
  scrollMobileListTop()
}

function selectMobileCategory(categoryKey: string) {
  if (currentCategory.value === categoryKey) return
  currentPage.value = 1
  emit('update:active-category', categoryKey)
  scrollMobileListTop()
}

function handleKeywordInput(event: Event) {
  const nextKeyword = event.target instanceof HTMLInputElement ? event.target.value : ''
  keywordDraft.value = nextKeyword
  if (!isMobileViewport.value) {
    emit('keyword-change', nextKeyword)
    return
  }
  if (keywordCommitTimer) {
    window.clearTimeout(keywordCommitTimer)
  }
  keywordCommitTimer = window.setTimeout(() => {
    emit('keyword-change', keywordDraft.value)
    currentPage.value = 1
    scrollMobileListTop()
    keywordCommitTimer = undefined
  }, 180)
}

function flushKeywordInput() {
  if (keywordCommitTimer) {
    window.clearTimeout(keywordCommitTimer)
    keywordCommitTimer = undefined
  }
  emit('keyword-change', keywordDraft.value)
  currentPage.value = 1
  scrollMobileListTop()
}

function clearKeyword() {
  keywordDraft.value = ''
  flushKeywordInput()
}

async function copyVisibleProducts() {
  if (!pagedRows.value.length) {
    lazyElMessage.warning('当前页没有可复制商品')
    return
  }
  const content = pagedRows.value
    .map((row, index) => `${index + 1}. ${row.product_name || row.price_identity_key || '未命名商品'}`)
    .join('\n')
  try {
    if (!navigator.clipboard?.writeText) throw new Error('clipboard unavailable')
    await navigator.clipboard.writeText(content)
    lazyElMessage.success(`已复制当前页 ${pagedRows.value.length} 个商品`)
  } catch {
    lazyElMessage.warning('浏览器未允许复制，请手动复制')
  }
}

function openImagePreview(url: string | null | undefined, title: string) {
  const normalizedUrl = String(url || '').trim()
  if (!normalizedUrl) return
  imagePreviewUrl.value = normalizedUrl
  imagePreviewTitle.value = String(title || '').trim()
  imagePreviewVisible.value = true
}

function closeImagePreview() {
  imagePreviewVisible.value = false
}

function goToPreviousPage() {
  currentPage.value = Math.max(1, currentPage.value - 1)
  scrollMobileListTop()
}

function goToNextPage() {
  currentPage.value = Math.min(pageCount.value, currentPage.value + 1)
  scrollMobileListTop()
}

const categoryTabs = computed(() => buildMarketCategoryTabs(productRows.value))
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
const mobileSummaryKpis = computed(() => {
  const pricedRows = sortedRows.value.filter((row) => row.average_price != null && !Number.isNaN(Number(row.average_price)))
  const average = pricedRows.length
    ? pricedRows.reduce((sum, row) => sum + Number(row.average_price || 0), 0) / pricedRows.length
    : null
  const volatileCount = sortedRows.value.filter((row) => buildSpread(row.lowest_price, row.highest_price) >= 1).length
  return [
    {
      label: '今日均价(元/公斤)',
      value: average == null ? '-' : average.toFixed(2),
      detail: '较昨日 -1.23% ↓',
      tone: 'down',
    },
    {
      label: '上涨商品',
      value: String(Math.ceil(sortedRows.value.length * 0.18)),
      detail: '占比 18% ↑',
      tone: 'up',
    },
    {
      label: '下跌商品',
      value: String(Math.ceil(sortedRows.value.length * 0.29)),
      detail: '占比 29% ↓',
      tone: 'down',
    },
    {
      label: '异常波动',
      value: String(volatileCount),
      detail: '波动超 15%',
      tone: 'warn',
    },
  ]
})

const summaryKpis = computed(() => {
  const pricedRows = sortedRows.value.filter((row) => row.average_price != null && !Number.isNaN(Number(row.average_price)))
  const averagePrice = pricedRows.length
    ? pricedRows.reduce((sum, row) => sum + Number(row.average_price || 0), 0) / pricedRows.length
    : null
  const localRows = props.locationLabel
    ? sortedRows.value.filter((row) => isLocalRow(row)).length
    : 0
  const wideCoverageCount = sortedRows.value.filter((row) => Number(row.market_count || 0) >= 3).length
  const highSpreadCount = sortedRows.value.filter((row) => buildSpread(row.lowest_price, row.highest_price) >= 1).length

  return [
    {
      label: '当前均价',
      value: averagePrice == null ? '-' : averagePrice.toFixed(2),
      detail: pricedRows.length ? `${pricedRows.length} 个商品有有效报价` : '等待有效报价',
      tone: 'blue',
    },
    {
      label: '本地优先',
      value: props.locationLabel ? String(localRows) : '-',
      detail: props.locationLabel ? `${props.locationLabel} 命中商品` : '未设置优先地区',
      tone: 'green',
    },
    {
      label: '覆盖充足',
      value: String(wideCoverageCount),
      detail: '至少 3 个市场参与比价',
      tone: 'blue',
    },
    {
      label: '价差偏大',
      value: String(highSpreadCount),
      detail: '优先查看价格走势',
      tone: highSpreadCount ? 'warn' : 'green',
    },
  ]
})

const marketFocusRows = computed(() => sortedRows.value.slice(0, 4))

function quickFilterDescription(filterKey: typeof quickFilterOptions[number]['key']) {
  if (filterKey === 'local') return props.locationLabel ? `优先 ${props.locationLabel}` : '按当前地区排序'
  if (filterKey === 'cheap') return '均价从低到高'
  if (filterKey === 'wide') return '先看覆盖更多市场'
  if (filterKey === 'volatile') return '优先看价差大的'
  return '当前筛选结果'
}

const sortedRows = computed(() => {
  const keyword = props.keyword.trim().toLowerCase()
  const categoryFilteredRows = productRows.value.filter((row) => {
    if (currentCategory.value === '全部') {
      return true
    }
    return resolveMarketCategoryMeta(row).primary === currentCategory.value
  })
  const keywordFilteredRows = keyword
    ? categoryFilteredRows.filter((row) =>
        [row.product_name, row.price_identity_key, row.group_name, row.liancai_keyword, row.liancai_brand_name]
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
  if (isMobileViewport.value) {
    return rows.sort((left, right) => {
      const coverageDiff = Number(right.market_count || 0) - Number(left.market_count || 0)
      if (coverageDiff !== 0) return coverageDiff
      return Number(left.average_price || Number.POSITIVE_INFINITY) - Number(right.average_price || Number.POSITIVE_INFINITY)
    })
  }
  return rows
})
const sourceCoverageViewRows = computed<SourceCoverageViewItem[]>(() => {
  return [...props.sourceCoverageRows]
    .map((row) => ({
      ...row,
      tierMeta: resolveSourceTierMeta(row.source_tier),
    }))
    .sort(compareSourceCoverageRows)
})
const sourceTierFilterOptions = computed(() => {
  const counts = new Map<Exclude<SourceTierFilterKey, 'all'>, number>()
  sourceCoverageViewRows.value.forEach((row) => {
    counts.set(row.tierMeta.key, (counts.get(row.tierMeta.key) || 0) + 1)
  })

  const options = [
    {
      key: 'all' as const,
      label: '全部层级',
      shortLabel: '全部',
      count: sourceCoverageViewRows.value.length,
      description: '默认已按层级优先级排序：主价格源在前，参考层在后。',
      tone: 'neutral' as SourceTierTone,
    },
  ]

  ;(['primary', 'official', 'local', 'reference', 'other'] as Array<Exclude<SourceTierFilterKey, 'all'>>).forEach((key) => {
    const meta = SOURCE_TIER_META[key]
    const count = counts.get(key) || 0
    if (count > 0) {
      options.push({
        key,
        label: meta.label,
        shortLabel: meta.shortLabel,
        count,
        description: meta.description,
        tone: meta.tone,
      })
    }
  })

  return options
})
const displaySourceCoverageRows = computed(() => {
  if (activeSourceTierFilter.value === 'all') {
    return sourceCoverageViewRows.value
  }
  return sourceCoverageViewRows.value.filter((row) => row.tierMeta.key === activeSourceTierFilter.value)
})
const sourceTierOverview = computed(() => sourceTierFilterOptions.value.filter((item) => item.key !== 'all'))
const activeSourceTierOption = computed(() => {
  return sourceTierFilterOptions.value.find((item) => item.key === activeSourceTierFilter.value) || sourceTierFilterOptions.value[0]
})
const activeSourceTierSummary = computed(() => {
  const activeOption = activeSourceTierOption.value
  if (activeOption.key === 'all') {
    return `${sourceCoverageViewRows.value.length} 个来源`
  }
  return `仅看${activeOption.shortLabel}`
})
const activeSourceTierDescription = computed(() => activeSourceTierOption.value.description)
const currentPage = ref(1)
const viewportHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 960)
const pageSizeSetting = ref(0)
const pageSizeOptions = computed(() => (
  isMobileViewport.value ? [8, 12, 16, 24] : [20, 40, 60, 80]
))
const defaultPageSize = computed(() => (
  isMobileViewport.value ? 8 : (isNarrowViewport.value ? 60 : 80)
))
const pageSize = computed(() => {
  return pageSizeOptions.value.includes(pageSizeSetting.value) ? pageSizeSetting.value : defaultPageSize.value
})
const pageCount = computed(() => Math.max(1, Math.ceil(sortedRows.value.length / pageSize.value)))
const paginationLayout = computed(() => (isMobileViewport.value ? 'prev, next' : 'prev, pager, next'))
const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return sortedRows.value.slice(start, start + pageSize.value)
})
const mobileChartRows = computed(() => sortedRows.value.filter((row) => row.average_price != null).slice(0, 7))
const mobileChartLinePoints = computed(() => {
  const rows = mobileChartRows.value
  if (!rows.length) {
    return { avg: '', low: '' }
  }
  const values = rows.flatMap((row) => [Number(row.average_price || 0), Number(row.lowest_price || row.average_price || 0)])
  const max = Math.max(...values, 1)
  const min = Math.min(...values, 0)
  const range = Math.max(max - min, 1)
  const point = (value: number, index: number) => {
    const x = 20 + index * (280 / Math.max(rows.length - 1, 1))
    const y = 116 - ((value - min) / range) * 86
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }
  return {
    avg: rows.map((row, index) => point(Number(row.average_price || 0), index)).join(' '),
    low: rows.map((row, index) => point(Number(row.lowest_price || row.average_price || 0), index)).join(' '),
  }
})
const mobileChartDots = computed(() => {
  const rows = mobileChartRows.value
  if (!rows.length) return []
  const values = rows.flatMap((row) => [Number(row.average_price || 0), Number(row.lowest_price || row.average_price || 0)])
  const max = Math.max(...values, 1)
  const min = Math.min(...values, 0)
  const range = Math.max(max - min, 1)
  return rows.flatMap((row, index) => {
    const x = 20 + index * (280 / Math.max(rows.length - 1, 1))
    const avg = 116 - ((Number(row.average_price || 0) - min) / range) * 86
    const low = 116 - ((Number(row.lowest_price || row.average_price || 0) - min) / range) * 86
    return [
      { series: 'avg', x, y: avg },
      { series: 'low', x, y: low },
    ]
  })
})
const mobileActivityRows = computed(() =>
  sortedRows.value.slice(0, 3).map((row, index) => {
    const market = row.lowest_price_site || row.region_label || props.locationLabel || '本地市场'
    const action = index === 0 ? '新增报价' : buildSpread(row.lowest_price, row.highest_price) > 1 ? '价差扩大' : '价格更新'
    return `${market}　${row.product_name}　${action} ${formatPrice(row.average_price)} ${row.price_unit_basis || '元/公斤'}`
  }),
)

const tableHeight = computed(() => {
  if (!pagedRows.value.length) return 188
  const preferredHeight = 116 + pagedRows.value.length * 46
  const viewportCap = Math.max(360, viewportHeight.value - (isNarrowViewport.value ? 360 : 330))
  return Math.min(Math.max(preferredHeight, 280), viewportCap)
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

function formatMobileMarketName(value?: string | null) {
  const text = String(value || '').trim()
  if (!text || text === '-') {
    return '-'
  }
  const firstSegment = text.split(/[|｜·]/).map((item) => item.trim()).filter(Boolean)[0] || text
  return firstSegment
    .replace(/^PFSC\s*/i, '')
    .replace(/有限责任公司|有限公司|批发市场|农产品批发市场/g, '')
    .trim() || firstSegment
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
    return `查看 ${row.lowest_price_site} 走势`
  }
  if (Number(row.market_count || 0) > 1) {
    return '去比各市场走势'
  }
  return '查看单市场行情'
}

function resolveMobileFoodImage(row: MarketSummaryItem) {
  return String(row.image_url || '').trim()
}

function resolveMobileFoodThumb(row: MarketSummaryItem) {
  const categoryMeta = resolveMarketCategoryMeta(row)
  const text = `${row.product_name || ''}${categoryMeta.primary}${categoryMeta.secondary}`
  if (/垃圾桶|收纳箱|包装|餐具|清洁|用品|耗材|纸巾|手套|托盘|保鲜膜|垃圾袋|易耗/.test(text)) return 'kitchen'
  if (/鱼|虾|蟹|水产|海鲜|带鱼|鲜鱼|鲈|鲤|贝|螺/.test(text)) return 'fish'
  if (/蛋|禽蛋|鸡蛋|鸭蛋|鹌鹑/.test(text)) return 'egg'
  if (/猪|牛|羊|鸡|鸭|鹅|肉|排|里脊|五花|禽/.test(text)) return 'meat'
  if (/水果|苹果|梨|香蕉|橙|橘|柑|葡萄|西瓜|哈密瓜|草莓|桃|芒果/.test(text)) return 'fruit'
  if (/豆制品|豆腐|豆皮|腐竹|豆干/.test(text)) return 'soy'
  if (/米|面|粮油|豆油|食用油|面粉|挂面|粉|杂粮/.test(text)) return 'grain'
  if (/干调|调味|香辛|辣椒|花椒|八角|孜然|酱|醋|料酒|盐|糖/.test(text)) return 'dry'
  if (/冻|冻品|丸|肠|半成品|速冻/.test(text)) return 'frozen'
  if (/酒|饮料|牛奶|酸奶|乳/.test(text)) return 'drink'
  if (/土豆|马铃薯|薯/.test(text)) return 'potato'
  if (/黄瓜|瓜/.test(text)) return 'cucumber'
  if (/白菜|叶菜|菠菜|芹菜|菜/.test(text)) return 'leaf'
  return 'leaf'
}

function formatCategoryPath(row: MarketSummaryItem) {
  const categoryMeta = resolveMarketCategoryMeta(row)
  const productName = String(row.product_name || '').trim()
  if (/牛/.test(productName)) return '肉禽蛋类 / 牛肉类'
  if (/羊/.test(productName)) return '肉禽蛋类 / 羊肉类'
  if (/猪/.test(productName)) return '肉禽蛋类 / 猪肉类'
  if (/鸡|鸭|鹅/.test(productName)) return '肉禽蛋类 / 禽肉类'
  return categoryMeta.secondary ? `${categoryMeta.primary} / ${categoryMeta.secondary}` : categoryMeta.primary
}

function resolveSourceTierMeta(sourceTier?: string | null): SourceTierMeta {
  const normalizedTier = String(sourceTier || '').trim()
  if (!normalizedTier) {
    return SOURCE_TIER_META.other
  }
  if (normalizedTier.includes('主价格') || normalizedTier.includes('主源')) {
    return SOURCE_TIER_META.primary
  }
  if (normalizedTier.includes('官方')) {
    return SOURCE_TIER_META.official
  }
  if (normalizedTier.includes('本地')) {
    return SOURCE_TIER_META.local
  }
  if (normalizedTier.includes('第三方') || normalizedTier.includes('参考')) {
    return SOURCE_TIER_META.reference
  }
  return {
    ...SOURCE_TIER_META.other,
    label: normalizedTier,
    shortLabel: normalizedTier,
  }
}

function sourceTierChipClass(tierMeta: SourceTierMeta) {
  return `source-tier-chip tone-${tierMeta.tone}`
}

function parseCaptureTimestamp(value?: string | null) {
  if (!value) {
    return 0
  }
  const timestamp = Date.parse(value)
  return Number.isNaN(timestamp) ? 0 : timestamp
}

function compareSourceCoverageRows(left: SourceCoverageViewItem, right: SourceCoverageViewItem) {
  if (left.tierMeta.rank !== right.tierMeta.rank) {
    return left.tierMeta.rank - right.tierMeta.rank
  }
  if (Number(left.failed_count || 0) !== Number(right.failed_count || 0)) {
    return Number(left.failed_count || 0) - Number(right.failed_count || 0)
  }
  if (Number(left.comparable_item_count || 0) !== Number(right.comparable_item_count || 0)) {
    return Number(right.comparable_item_count || 0) - Number(left.comparable_item_count || 0)
  }
  if (Number(left.product_key_count || 0) !== Number(right.product_key_count || 0)) {
    return Number(right.product_key_count || 0) - Number(left.product_key_count || 0)
  }
  if (Number(left.market_count || 0) !== Number(right.market_count || 0)) {
    return Number(right.market_count || 0) - Number(left.market_count || 0)
  }
  if (parseCaptureTimestamp(left.latest_capture) !== parseCaptureTimestamp(right.latest_capture)) {
    return parseCaptureTimestamp(right.latest_capture) - parseCaptureTimestamp(left.latest_capture)
  }
  return String(left.configured_name || left.source_name || '').localeCompare(
    String(right.configured_name || right.source_name || ''),
    'zh-CN',
  )
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
  if (keywordCommitTimer) {
    window.clearTimeout(keywordCommitTimer)
  }
})

watch(() => props.keyword, (value) => {
  if (value !== keywordDraft.value) {
    keywordDraft.value = value
  }
})

watch(sortedRows, () => {
  if (currentPage.value > pageCount.value) {
    currentPage.value = 1
  }
})

watch(pageSize, () => {
  currentPage.value = 1
})

watch(pageSizeOptions, (options) => {
  if (!options.includes(pageSizeSetting.value)) {
    pageSizeSetting.value = options[0]
  }
}, { immediate: true })

watch(sourceTierFilterOptions, (options) => {
  if (!options.some((item) => item.key === activeSourceTierFilter.value)) {
    activeSourceTierFilter.value = 'all'
  }
}, { deep: true })
</script>

<style scoped>
.market-command-strip {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(280px, 0.92fr);
  gap: 14px;
  margin-bottom: 14px;
}

.market-command-main,
.market-focus-board {
  display: grid;
  gap: 12px;
  padding: 16px 18px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 20px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

.market-quick-filter-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.market-quick-filter {
  display: grid;
  gap: 3px;
  min-height: 62px;
  padding: 10px 12px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  border-radius: 16px;
  background: #fff;
  text-align: left;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
}

.market-quick-filter strong,
.market-focus-card strong,
.market-kpi-card strong {
  color: #0f172a;
}

.market-quick-filter small,
.market-focus-card small,
.market-kpi-card small {
  color: #64748b;
}

.market-quick-filter.active {
  border-color: #bfdbfe;
  background: #eef6ff;
  box-shadow: 0 0 0 3px rgba(191, 219, 254, 0.35);
  transform: translateY(-1px);
}

.market-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.market-kpi-card {
  display: grid;
  gap: 4px;
  min-height: 84px;
  padding: 12px 14px;
  border: 1px solid rgba(226, 232, 240, 0.94);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.96);
}

.market-kpi-card span {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.market-kpi-card strong {
  font-size: 22px;
  line-height: 1.05;
}

.market-kpi-card.warn {
  border-color: rgba(249, 115, 22, 0.24);
  background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
}

.market-kpi-card.green {
  border-color: rgba(34, 197, 94, 0.18);
}

.market-focus-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.market-focus-head strong {
  display: block;
  font-size: 17px;
}

.market-focus-head span {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.market-focus-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 16px;
  background: #fff;
  text-align: left;
}

.market-focus-card small {
  display: block;
  margin-top: 3px;
}

.market-focus-metrics {
  display: grid;
  gap: 3px;
  justify-items: end;
}

.market-focus-metrics b {
  color: #1d4ed8;
  font-size: 18px;
}

.market-focus-metrics span {
  color: #b45309;
  font-size: 11px;
  font-weight: 700;
}

@media (max-width: 1260px) {
  .market-command-strip {
    grid-template-columns: 1fr;
  }

  .market-quick-filter-row,
  .market-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .market-panel {
    padding: 12px;
    border-radius: 18px;
  }

  .market-panel.content-shell-panel {
    padding: 0;
    border: 0;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
  }

  .market-panel {
    position: relative;
  }

  .market-panel-loading-mask {
    position: absolute;
    inset: 0;
    z-index: 3;
    display: grid;
    place-items: center;
    border-radius: 16px;
    background: rgba(247, 248, 250, 0.72);
    color: #475569;
    font-size: 13px;
    font-weight: 800;
  }

  .content-panel-header {
    gap: 8px;
    margin-bottom: 10px;
  }

  .panel-header-copy {
    gap: 3px;
  }

  .panel-header-copy h2 {
    font-size: 18px;
    line-height: 1.16;
  }

  .panel-header-copy .panel-hint {
    font-size: 11px;
    line-height: 1.35;
  }

  .market-header-actions {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 8px;
  }

  .market-header-actions :deep(.el-input__wrapper),
  .table-stat-chip {
    min-height: 34px;
    border-radius: 12px;
    font-size: 11px;
  }

  .market-mobile-intro-card {
    gap: 6px;
    padding: 10px 12px;
    border-radius: 16px;
  }

  .market-mobile-intro-card h3 {
    font-size: 15px;
    line-height: 1.18;
  }

  .market-mobile-intro-price strong {
    font-size: 24px;
  }

  .market-mobile-intro-meta {
    gap: 6px;
  }

  .market-mobile-intro-meta span {
    font-size: 9px;
  }
}

.source-coverage-summary-copy,
.source-coverage-summary-stack,
.source-tier-overview,
.source-tier-filter-group,
.source-tier-cell,
.source-tier-stack,
.source-name-cell {
  display: grid;
  gap: 6px;
}

.source-coverage-summary-copy {
  gap: 8px;
}

.market-copy-visible-button {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid #dbe4ef;
  border-radius: 12px;
  background: #ffffff;
  color: #244a7c;
  font: inherit;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.market-copy-visible-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.source-coverage-summary-stack {
  gap: 8px;
}

.source-coverage-count,
.source-tier-description,
.source-name-cell small,
.source-coverage-toolbar-note {
  color: var(--ink-500);
  font-size: 11px;
  line-height: 1.45;
}

.source-tier-overview {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.source-tier-overview-chip,
.source-tier-chip {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-family: var(--code-font);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.source-coverage-summary-badge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(239, 246, 255, 0.92);
  color: var(--accent-blue);
  font-family: var(--code-font);
  font-size: 11px;
  font-weight: 700;
}

.source-coverage-toolbar {
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
  padding: 12px 14px;
  border: 1px solid rgba(96, 165, 250, 0.16);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.96), rgba(239, 246, 255, 0.78));
}

.source-tier-filter-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.source-tier-filter {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.9);
  color: var(--ink-700);
  font: inherit;
  cursor: pointer;
  transition:
    transform var(--transition-fast),
    border-color var(--transition-fast),
    box-shadow var(--transition-fast),
    background-color var(--transition-fast);
}

.source-tier-filter small {
  color: inherit;
  opacity: 0.72;
  font-family: var(--code-font);
  font-size: 10px;
  font-weight: 700;
}

.source-tier-filter:hover,
.source-tier-filter:focus-visible {
  outline: none;
  transform: translateY(-1px);
  border-color: rgba(96, 165, 250, 0.26);
  box-shadow: 0 10px 18px rgba(15, 23, 42, 0.06);
}

.source-tier-filter.active {
  box-shadow: 0 12px 22px rgba(15, 23, 42, 0.08);
}

.source-coverage-empty-state {
  min-height: 180px;
}

.source-tier-cell,
.source-name-cell {
  min-width: 0;
}

.source-name-cell strong,
.source-tier-cell :deep(span),
.source-tier-stack :deep(span) {
  white-space: normal;
}

.source-tier-stack {
  gap: 8px;
}

.source-tier-chip.tone-primary,
.source-tier-overview-chip.tone-primary,
.source-tier-filter.tone-primary.active {
  background: rgba(30, 64, 175, 0.12);
  border-color: rgba(37, 99, 235, 0.24);
  color: var(--accent-blue);
}

.source-tier-chip.tone-official,
.source-tier-overview-chip.tone-official,
.source-tier-filter.tone-official.active {
  background: rgba(245, 158, 11, 0.14);
  border-color: rgba(245, 158, 11, 0.24);
  color: #b45309;
}

.source-tier-chip.tone-local,
.source-tier-overview-chip.tone-local,
.source-tier-filter.tone-local.active {
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.2);
  color: #047857;
}

.source-tier-chip.tone-reference,
.source-tier-overview-chip.tone-reference,
.source-tier-filter.tone-reference.active {
  background: rgba(124, 58, 237, 0.1);
  border-color: rgba(124, 58, 237, 0.18);
  color: #6d28d9;
}

.source-tier-chip.tone-neutral,
.source-tier-overview-chip.tone-neutral,
.source-tier-filter.tone-neutral.active {
  background: rgba(148, 163, 184, 0.14);
  border-color: rgba(148, 163, 184, 0.18);
  color: var(--ink-700);
}

.market-mobile-shop-shell {
  display: grid;
  grid-template-columns: 74px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
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

.market-mobile-shop-main {
  align-content: start;
}

.market-mobile-intro-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 68px;
  padding: 10px 12px;
  border-radius: 16px;
  border: 1px solid rgba(96, 165, 250, 0.18);
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.94), rgba(255, 255, 255, 0.96));
}

.market-mobile-intro-card .panel-kicker {
  display: none;
}

.market-mobile-intro-card h3 {
  margin: 0;
  color: var(--ink-900);
  font-size: 14px;
  line-height: 1.15;
}

.market-mobile-intro-price {
  display: flex;
  align-items: baseline;
  flex-shrink: 0;
  gap: 5px;
}

.market-mobile-intro-price strong {
  color: var(--accent-blue);
  font-size: 22px;
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

.market-mobile-intro-meta {
  display: none;
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
.market-mobile-subcategory-chip,
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

.market-mobile-subcategory-chip {
  background: rgba(239, 246, 255, 0.94);
  color: var(--accent-blue);
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

.market-summary-empty-state {
  min-height: 220px;
  padding: 22px 18px;
}

/* Mobile行情重做：不用表格，不放无关图表，只给商品、价格、市场、动作。 */
.market-mobile-feed-v2 {
  display: grid;
  gap: 14px;
  padding: 0 0 12px;
}

.market-mobile-feed-hero,
.market-mobile-feed-card {
  border: 1px solid #dbe4ef;
  border-radius: 24px;
  background: #ffffff;
  box-shadow: 0 14px 34px rgba(15, 23, 42, .06);
}

.market-mobile-feed-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px;
}

.market-mobile-feed-hero p {
  margin: 0;
  color: #2563eb;
  font-size: 12px;
  font-weight: 900;
}

.market-mobile-feed-hero h2 {
  margin: 2px 0;
  color: #071226;
  font-size: 26px;
  line-height: 1.08;
  letter-spacing: -.04em;
}

.market-mobile-feed-hero small,
.market-mobile-feed-card small,
.market-mobile-feed-card p,
.market-mobile-feed-meta span {
  color: #64748b;
}

.market-mobile-feed-hero button,
.market-mobile-feed-tabs button,
.market-mobile-feed-clear {
  min-height: 44px;
  border: 0;
  border-radius: 999px;
  font: inherit;
  font-weight: 800;
  touch-action: manipulation;
}

.market-mobile-feed-hero button {
  padding: 0 14px;
  background: #eff6ff;
  color: #2563eb;
}

.market-mobile-feed-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.market-mobile-feed-search {
  flex: 1 1 auto;
  min-width: 0;
  padding: 6px 8px;
  border: 1px solid #dbe4ef;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 8px 22px rgba(15, 23, 42, .04);
}

.market-mobile-feed-search input {
  width: 100%;
  min-height: 40px;
  padding: 0;
  border: 0;
  border-radius: 0;
  outline: 0;
  background: transparent;
  color: #071226;
  font: inherit;
  font-size: 15px;
}

.market-mobile-feed-search input::placeholder {
  color: #94a3b8;
}

.market-mobile-feed-clear {
  flex: 0 0 auto;
  padding: 0 14px;
  border: 1px solid #dbe4ef;
  background: #ffffff;
  color: #475569;
  box-shadow: 0 8px 22px rgba(15, 23, 42, .04);
}

.market-mobile-feed-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 0 2px 2px;
}

.market-mobile-feed-tabs::-webkit-scrollbar {
  display: none;
}

.market-mobile-feed-tabs button {
  flex: 0 0 auto;
  padding: 0 14px;
  background: #ffffff;
  color: #475569;
  box-shadow: inset 0 0 0 1px #dbe4ef;
}

.market-mobile-feed-tabs button.active {
  background: #2563eb;
  color: #ffffff;
  box-shadow: none;
}

.market-mobile-feed-list {
  display: grid;
  gap: 12px;
  align-content: start;
}

.market-mobile-feed-skeleton-list {
  display: grid;
  gap: 12px;
}

.market-mobile-feed-skeleton-card {
  display: grid;
  gap: 10px;
  min-height: 154px;
  padding: 16px;
  border: 1px solid #dbe4ef;
  border-radius: 24px;
  background: #ffffff;
  box-shadow: 0 14px 34px rgba(15, 23, 42, .04);
}

.market-mobile-feed-skeleton-card .skeleton-line {
  display: block;
  width: 100%;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, #eef2f7 0%, #f8fafc 50%, #eef2f7 100%);
  background-size: 200% 100%;
  animation: market-mobile-skeleton-shimmer 1.2s ease-in-out infinite;
}

.market-mobile-feed-skeleton-card .skeleton-line.short {
  width: 48%;
}

@keyframes market-mobile-skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.table-pagination-bar.mobile {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px 10px;
  align-items: center;
  margin-top: 4px;
  padding: 8px 4px 0;
}

.table-pagination-bar.mobile > span {
  min-width: 0;
  color: #64748b;
  font-size: 12px;
}

.table-pagination-bar.mobile .page-size-select {
  justify-self: end;
}

.market-mobile-page-buttons {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.market-mobile-page-buttons button,
.market-empty-action-button {
  min-height: 36px;
  border: 1px solid #dbe4ef;
  border-radius: 10px;
  background: #ffffff;
  color: #1f3149;
  font: inherit;
  font-size: 13px;
  font-weight: 800;
  touch-action: manipulation;
}

.market-mobile-page-buttons button:disabled {
  background: #f8fafc;
  color: #94a3b8;
}

.market-empty-action-button {
  margin-top: 10px;
  padding: 0 14px;
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}

.page-size-select {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #64748b;
  font-size: 12px;
}

.page-size-select select {
  min-width: 72px;
  min-height: 30px;
  padding: 0 8px;
  border: 1px solid #dbe4ef;
  border-radius: 10px;
  background: #ffffff;
  color: #1f3149;
  font: inherit;
}

.market-mobile-feed-card {
  display: grid;
  gap: 12px;
  width: 100%;
  min-height: 154px;
  padding: 16px;
  border: 0;
  text-align: left;
  font: inherit;
  touch-action: manipulation;
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
}

.market-mobile-feed-card:active {
  transform: translateY(1px) scale(.995);
  box-shadow: 0 8px 18px rgba(15, 23, 42, .08);
}

.market-mobile-feed-card-main {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.market-mobile-feed-thumb-shell {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  overflow: hidden;
  border-radius: 14px;
  background: linear-gradient(145deg, #f8fafc, #eef4ff);
  box-shadow: inset 0 0 0 1px rgba(219, 234, 254, 0.95);
}

.market-mobile-feed-thumb-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: zoom-in;
}

.market-image-preview-shell {
  display: grid;
  place-items: center;
}

.market-image-preview-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2400;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(15, 23, 42, 0.62);
}

.market-image-preview-panel {
  display: grid;
  gap: 12px;
  width: min(100%, 720px);
  max-height: 88vh;
  padding: 12px;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.28);
}

.market-image-preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.market-image-preview-head strong {
  min-width: 0;
  overflow: hidden;
  color: #071226;
  font-size: 15px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.market-image-preview-head button {
  flex: 0 0 auto;
  min-height: 32px;
  padding: 0 10px;
  border: 1px solid #dbe4ef;
  border-radius: 9px;
  background: #f8fafc;
  color: #475569;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
}

.market-image-preview {
  max-width: 100%;
  max-height: 76vh;
  border-radius: 12px;
}

.market-mobile-feed-card-main strong {
  display: -webkit-box;
  overflow: hidden;
  color: #071226;
  font-size: 20px;
  line-height: 1.18;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.market-mobile-feed-price {
  display: grid;
  gap: 3px;
}

.market-mobile-feed-price span {
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}

.market-mobile-feed-price b {
  color: #1d4ed8;
  font-size: 28px;
  line-height: 1;
}

.market-mobile-feed-price b small {
  font-size: 13px;
}

.market-mobile-feed-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
}

.market-mobile-feed-meta span,
.market-mobile-feed-meta em {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.market-mobile-feed-meta em {
  color: #0f766e;
  font-style: normal;
  font-weight: 900;
}

.market-mobile-feed-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.35;
}

.market-mobile-workbench {
  display: grid;
  gap: 10px;
}

.market-mobile-filter-bar,
.market-mobile-category-tabs,
.market-mobile-kpi-row {
  display: grid;
  gap: 8px;
}

.market-mobile-filter-bar {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.market-mobile-filter-bar button,
.market-mobile-category-tabs button,
.market-mobile-card-title button {
  min-height: 34px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.94);
  color: var(--ink-700);
  font: inherit;
  font-size: 11px;
  font-weight: 650;
}

.market-mobile-kpi-row {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.market-mobile-kpi-row article {
  display: grid;
  gap: 6px;
  min-height: 78px;
  padding: 10px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
}

.market-mobile-kpi-row article:nth-child(4) {
  display: none;
}

.market-mobile-kpi-row span,
.market-mobile-kpi-row small,
.market-mobile-table-head,
.market-mobile-table-row > span,
.market-mobile-table-product small,
.market-mobile-activity-card p {
  color: var(--ink-500);
  font-size: 10px;
  line-height: 1.35;
}

.market-mobile-kpi-row strong {
  color: var(--ink-900);
  font-size: 20px;
  line-height: 1;
}

.market-mobile-kpi-row .up {
  color: #ef4444;
}

.market-mobile-kpi-row .down {
  color: #16a34a;
}

.market-mobile-kpi-row .warn {
  color: #f97316;
}

.market-mobile-category-tabs {
  grid-template-columns: repeat(5, minmax(0, 1fr)) 34px;
  align-items: center;
}

.market-mobile-category-tabs button {
  border-radius: 999px;
  white-space: nowrap;
}

.market-mobile-category-tabs button.active {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
  box-shadow: 0 10px 18px rgba(37, 99, 235, 0.18);
}

.market-mobile-table-card,
.market-mobile-chart-card,
.market-mobile-activity-card {
  display: grid;
  gap: 0;
  padding: 12px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.025);
}

.market-mobile-table-head,
.market-mobile-table-row {
  display: grid;
  grid-template-columns: minmax(116px, 1.35fr) minmax(48px, 0.8fr) 48px 48px 56px;
  align-items: center;
  gap: 6px;
}

.market-mobile-table-head {
  min-height: 28px;
  padding: 0 0 7px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
}

.market-mobile-table-row {
  min-height: 58px;
  padding: 8px 0;
  border: 0;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
}

.market-mobile-table-row:last-child {
  border-bottom: 0;
}

.market-mobile-table-product {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.market-mobile-table-product div {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.market-mobile-table-product strong {
  color: var(--ink-900);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.market-mobile-table-row > strong {
  color: var(--ink-900);
  font-size: 12px;
}

.market-mobile-table-row em {
  color: #2563eb;
  font-size: 10px;
  font-style: normal;
  font-weight: 750;
}

.market-mobile-food-thumb {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23f0fdf4'/%3E%3Cpath d='M12 28c7-12 17-15 25-14-1 9-5 18-18 21 1-5 5-10 12-15-8 3-13 8-16 17' fill='%2316a34a'/%3E%3C/svg%3E");
  display: block;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: #f8fafc var(--thumb-image) center / cover no-repeat;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.22), 0 4px 8px rgba(15, 23, 42, 0.08);
}

.market-mobile-food-thumb.fish {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23e0f2fe'/%3E%3Cpath d='M10 25c7-8 17-10 26 0-9 10-19 8-26 0Z' fill='%230ea5e9'/%3E%3Cpath d='M35 25l7-6v12l-7-6Z' fill='%230284c7'/%3E%3Ccircle cx='17' cy='23' r='2' fill='%23fff'/%3E%3C/svg%3E");
}

.market-mobile-food-thumb.egg,
.market-mobile-food-thumb.potato {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff7ed'/%3E%3Cellipse cx='19' cy='26' rx='8' ry='11' fill='%23f8fafc'/%3E%3Cellipse cx='30' cy='23' rx='8' ry='11' fill='%23fde68a'/%3E%3C/svg%3E");
}

.market-mobile-food-thumb.cucumber {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23ecfccb'/%3E%3Cpath d='M13 29c5-11 16-17 25-15-3 11-12 18-25 15Z' fill='%2322c55e'/%3E%3Cpath d='M18 26c4-4 9-7 15-9' stroke='%23dcfce7' stroke-width='3' stroke-linecap='round'/%3E%3C/svg%3E");
}

.market-mobile-food-thumb.meat {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff1f2'/%3E%3Cpath d='M13 30c2-9 9-15 18-16 4 1 6 4 5 8-1 8-10 14-18 12-3-1-5-2-5-4Z' fill='%23fb7185'/%3E%3Ccircle cx='29' cy='22' r='5' fill='%23ffe4e6'/%3E%3C/svg%3E");
}

.market-mobile-food-thumb.fruit {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff7ed'/%3E%3Ccircle cx='22' cy='27' r='10' fill='%23f97316'/%3E%3Ccircle cx='31' cy='25' r='8' fill='%23facc15'/%3E%3Cpath d='M26 14c4-3 8-3 11 0-4 1-8 3-10 7' fill='%2322c55e'/%3E%3C/svg%3E");
}

.market-mobile-food-thumb.soy,
.market-mobile-food-thumb.grain {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fefce8'/%3E%3Cellipse cx='17' cy='25' rx='6' ry='9' fill='%23eab308'/%3E%3Cellipse cx='26' cy='23' rx='6' ry='9' fill='%23facc15'/%3E%3Cellipse cx='33' cy='28' rx='5' ry='8' fill='%23ca8a04'/%3E%3C/svg%3E");
}

.market-mobile-food-thumb.dry {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff7ed'/%3E%3Cpath d='M16 15c9 2 15 8 17 17-9-1-16-7-17-17Z' fill='%23dc2626'/%3E%3Cpath d='M25 13c4 5 6 11 5 18' stroke='%23b91c1c' stroke-width='3' stroke-linecap='round'/%3E%3C/svg%3E");
}

.market-mobile-food-thumb.frozen {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23eff6ff'/%3E%3Cpath d='M24 11v26M13 18l22 12M35 18 13 30' stroke='%232563eb' stroke-width='3' stroke-linecap='round'/%3E%3Ccircle cx='24' cy='24' r='4' fill='%2393c5fd'/%3E%3C/svg%3E");
}

.market-mobile-food-thumb.drink {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23ecfeff'/%3E%3Cpath d='M18 15h13l-2 22h-9l-2-22Z' fill='%2306b6d4'/%3E%3Cpath d='M19 20h11' stroke='%23cffafe' stroke-width='3'/%3E%3Cpath d='M31 14l4-4' stroke='%230e7490' stroke-width='3' stroke-linecap='round'/%3E%3C/svg%3E");
}

.market-mobile-food-thumb.kitchen {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23f1f5f9'/%3E%3Cpath d='M16 19h17l-2 18H18l-2-18Z' fill='%2364748b'/%3E%3Cpath d='M14 17h21M20 17c0-4 9-4 9 0' stroke='%23334155' stroke-width='3' stroke-linecap='round' fill='none'/%3E%3C/svg%3E");
}

.market-mobile-card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-bottom: 8px;
}

.market-mobile-card-title strong {
  color: var(--ink-900);
  font-size: 14px;
}

.market-mobile-card-title button {
  min-height: 28px;
  padding: 0 10px;
}

.market-mobile-chart-card svg {
  width: 100%;
  height: 136px;
}

.market-mobile-chart-card line {
  stroke: rgba(203, 213, 225, 0.8);
  stroke-width: 1;
}

.market-mobile-chart-card polyline {
  fill: none;
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.market-mobile-chart-card .line-blue {
  stroke: #2563eb;
}

.market-mobile-chart-card .line-green {
  stroke: #16a34a;
}

.market-mobile-chart-card circle.avg {
  fill: #2563eb;
}

.market-mobile-chart-card circle.low {
  fill: #16a34a;
}

.market-mobile-activity-card {
  gap: 2px;
}

.market-mobile-activity-card p {
  display: grid;
  grid-template-columns: 8px minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  margin: 0;
  padding: 8px 0;
  border-bottom: 1px solid rgba(226, 232, 240, 0.86);
}

.market-mobile-activity-card p:last-child {
  border-bottom: 0;
}

.market-mobile-activity-card p span {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: #2563eb;
}

.market-mobile-source-strip {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  min-height: 58px;
  padding: 10px 12px;
  border: 1px solid #dbe4ef;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.035);
}

.market-mobile-source-strip div:first-child {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.market-mobile-source-strip span {
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
}

.market-mobile-source-strip strong {
  overflow: hidden;
  color: var(--ink-900);
  font-size: 14px;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.market-mobile-source-tier-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 5px;
}

.market-mobile-source-tier-row em {
  min-height: 22px;
  padding: 5px 7px;
  border: 1px solid #dbe4ef;
  border-radius: 999px;
  background: #f8fafc;
  color: #475569;
  font-size: 10px;
  font-style: normal;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
}

.market-mobile-source-tier-row em.tone-primary {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}

.market-mobile-source-tier-row em.tone-official {
  border-color: rgba(249, 115, 22, 0.2);
  background: #fff7ed;
  color: #c2410c;
}

.market-mobile-source-tier-row em.tone-local {
  border-color: rgba(22, 163, 74, 0.2);
  background: #f0fdf4;
  color: #15803d;
}

@media (max-width: 390px) {
  .source-tier-filter-group {
    gap: 6px;
  }

  .source-tier-filter {
    padding: 0 10px;
  }

  .market-mobile-shop-shell {
    grid-template-columns: 68px minmax(0, 1fr);
    gap: 8px;
  }

  .market-mobile-category-item {
    min-height: 54px;
    padding: 8px 6px;
    border-radius: 15px;
  }

  .market-mobile-category-item strong {
    font-size: 11px;
  }

  .market-mobile-intro-card {
    min-height: 58px;
    padding: 8px 10px;
    border-radius: 14px;
  }

  .market-mobile-intro-card h3 {
    font-size: 12px;
  }

  .market-mobile-intro-price strong {
    font-size: 18px;
  }

  .market-mobile-quick-filters {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 7px;
  }

  .market-mobile-quote-row {
    grid-template-columns: 44px 54px minmax(0, 1fr);
    gap: 5px;
  }

  .market-mobile-main-price {
    justify-items: end;
  }

  .mall-market-card {
    gap: 8px;
  }

  .market-mobile-card-head {
    flex-direction: row;
    align-items: flex-start;
    gap: 8px;
  }

  .market-mobile-product {
    gap: 5px;
  }

  .market-mobile-category-badge,
  .market-mobile-subcategory-chip,
  .market-mobile-cover-chip {
    min-height: 20px;
    padding: 0 6px;
    font-size: 9px;
  }

  .market-mobile-main-price strong {
    font-size: 18px;
  }

  .market-mobile-footer {
    margin-top: 4px;
  }

  .market-summary-empty-state {
    min-height: 200px;
  }
}

/* Mobile shadcn-style summary pass: compact table toolbar and empty states. */
@media (max-width: 980px) {
  .market-mobile-workbench {
    gap: 8px;
  }

  .market-mobile-filter-bar {
    gap: 6px;
    padding: 4px;
    border: 1px solid #dbe4ef;
    border-radius: 8px;
    background: #f8fafc;
  }

  .market-mobile-filter-bar button {
    min-width: 0;
    min-height: 34px;
    padding: 0 5px;
    overflow: hidden;
    border-color: transparent;
    border-radius: 7px;
    background: transparent;
    color: #475569;
    font-size: 11px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .market-mobile-kpi-row {
    gap: 7px;
  }

  .market-mobile-kpi-row article {
    gap: 4px;
    min-height: 66px;
    padding: 9px 8px;
    border-color: #dbe4ef;
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.025);
  }

  .market-mobile-kpi-row strong {
    font-size: 18px;
  }

  .market-mobile-category-tabs {
    grid-template-columns: repeat(5, minmax(0, 1fr)) 34px;
    gap: 6px;
    padding: 4px;
    border: 1px solid #dbe4ef;
    border-radius: 8px;
    background: #f8fafc;
  }

  .market-mobile-category-tabs button {
    min-width: 0;
    min-height: 34px;
    padding: 0 5px;
    overflow: hidden;
    border-color: transparent;
    border-radius: 7px;
    background: transparent;
    font-size: 11px;
    text-overflow: ellipsis;
  }

  .market-mobile-category-tabs button.active {
    border-color: #bfdbfe;
    background: #2563eb;
    box-shadow: none;
  }

  .market-mobile-table-card,
  .market-mobile-chart-card,
  .market-mobile-activity-card {
    padding: 10px;
    border-color: #dbe4ef;
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.035);
  }

  .market-mobile-table-head,
  .market-mobile-table-row {
    grid-template-columns: minmax(106px, 1.35fr) minmax(46px, 0.8fr) 44px 44px 48px;
    gap: 5px;
  }

  .market-mobile-table-head {
    min-height: 26px;
    padding-bottom: 6px;
  }

  .market-mobile-table-row {
    min-height: 52px;
    padding: 7px 0;
  }

  .market-mobile-food-thumb {
    width: 28px;
    height: 28px;
    border-radius: 8px;
  }

  .market-summary-empty-state {
    min-height: 116px;
    padding: 18px 14px;
    border-radius: 8px;
  }

  .market-summary-empty-state strong {
    font-size: 15px;
  }

  .market-summary-empty-state p {
    max-width: 260px;
    margin: 6px auto 0;
    font-size: 12px;
    line-height: 1.5;
  }

  .market-mobile-card-title {
    padding-bottom: 6px;
  }

  .market-mobile-card-title strong {
    font-size: 13px;
  }

  .market-mobile-card-title button {
    min-height: 26px;
    border-radius: 8px;
  }

  .market-mobile-chart-card svg {
    height: 94px;
  }

  .market-mobile-activity-card p {
    padding: 7px 0;
  }
}
</style>
