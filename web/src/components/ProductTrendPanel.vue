<template>
  <section class="panel trend-workspace-panel content-shell-panel" :data-ready="loading ? 'loading' : 'ready'">
    <div v-if="productMismatch" class="trend-stale-data-banner" role="status">
      <strong>正在切换商品数据</strong>
      <span>已选择 {{ fallbackProductLabel }}，正在同步对应的走势与报价。</span>
    </div>
    <div v-if="!isMobileViewport" class="panel-header content-panel-header">
      <div>
        <p class="panel-kicker">价格走势</p>
        <h2>单品趋势</h2>
        <p class="panel-hint">同一商品按自身历史和来源报价对比，默认展示跨市场走势。</p>
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
        <strong>{{ displayTrendRows.length }}</strong>
        <small>{{ trendTierSummaryLabel }}</small>
      </div>
      <div v-if="productSummary" class="summary-card compact-summary-card">
        <span>最近更新</span>
        <strong>{{ productSummary.latest_captured_at ?? '-' }}</strong>
        <small>{{ latestTrendSourceSummary }}</small>
      </div>
    </div>
    <div v-if="isMobileViewport && (currentProductLabel || selectedIdentityKey)" class="trend-mobile-current-product">
      <span>当前商品</span>
      <strong>{{ currentProductLabel || selectedIdentityKey }}</strong>
      <small>{{ currentProductCoverageLabel }}</small>
    </div>
    <div class="trend-toolbar content-toolbar">
      <div class="trend-picker-inline">
        <span>商品</span>
        <el-select
          v-if="!isMobileViewport"
          class="trend-product-select"
          :model-value="selectedIdentityKey"
          aria-label="选择商品"
          placeholder="选择商品"
          popper-class="trend-product-select-popper"
          :fit-input-width="false"
          filterable
          :filter-method="handleProductFilter"
          @visible-change="handleProductSelectVisibleChange"
          @change="emit('select-product', $event)"
        >
          <el-option
            v-for="item in visibleProductOptions"
            :key="item.price_identity_key"
            :label="item.price_identity_label"
            :value="item.price_identity_key"
          >
            <span class="trend-product-option" :title="item.price_identity_label">
              <img
                v-if="isSourceProductImageAllowed(item.source_name) && item.image_url && !brokenTrendImageUrls.has(item.image_url)"
                :src="item.image_url"
                alt=""
                loading="lazy"
                @error="handleTrendImageError(item.image_url)"
                @click.stop="openImagePreview(item.image_url, item.price_identity_label)"
              />
              <span>
                <strong>{{ item.price_identity_label }}</strong>
                <small>{{ item.source_name || '来源' }} · {{ item.source_category || '未分类' }}</small>
              </span>
            </span>
          </el-option>
        </el-select>
        <select
          v-else
          class="trend-native-select trend-product-native-select"
          :value="selectedIdentityKey"
          aria-label="选择商品"
          @focus="handleProductSelectVisibleChange(true)"
          @change="handleNativeProductChange"
        >
          <option value="" disabled>选择商品</option>
          <option
            v-for="item in visibleProductOptions"
            :key="item.price_identity_key"
            :value="item.price_identity_key"
          >
            {{ item.price_identity_label }}
          </option>
        </select>
      </div>
      <div v-if="trendMode === 'single_market'" class="trend-picker-inline site-inline">
        <span>市场</span>
        <el-select
          v-if="!isMobileViewport"
          :model-value="selectedSiteName"
          aria-label="选择市场"
          clearable
          placeholder="选择单个市场"
          @change="emit('update:selected-site-name', $event || '')"
        >
          <el-option v-for="site in availableSites" :key="site" :label="site" :value="site" />
        </el-select>
        <select
          v-else
          class="trend-native-select"
          :value="selectedSiteName"
          aria-label="选择市场"
          @change="handleNativeSiteChange"
        >
          <option value="">全部市场</option>
          <option v-for="site in availableSites" :key="site" :value="site">{{ site }}</option>
        </select>
      </div>
      <div v-if="!isMobileViewport" class="trend-toolbar-count">
        {{ visibleProductOptions.length }} / {{ productOptions.length }} 个商品
      </div>
    </div>
    <div
      v-if="isMobileViewport"
      class="trend-mobile-mode-switch"
      role="group"
      aria-label="趋势模式切换"
      data-testid="trend-mode-switch"
    >
      <button
        type="button"
        :class="{ active: trendMode === 'cross_market' }"
        @click="emit('update:trend-mode', 'cross_market')"
      >
        跨市场
      </button>
      <button
        type="button"
        :class="{ active: trendMode === 'single_market' }"
        @click="emit('update:trend-mode', 'single_market')"
      >
        单市场
      </button>
    </div>
    <div v-if="selectedIdentityKey || currentProductOption" class="trend-content-shell" :class="{ 'is-loading': loading }">
      <div v-if="currentProductOption && currentProductOption.site_count <= 1 && !isMobileViewport" class="trend-single-source-tip">
        当前商品只匹配到 1 个市场，现有数据里通常只会看到 {{ availableSites[0] || '当前来源' }}。
      </div>
      <div v-if="isComparisonMode && displayTrendRows.length && !isMobileViewport" class="trend-compare-tip">
        跨市场会补齐断档；每页只展示一组完全重合的价格线。
      </div>
      <div v-if="isMobileViewport && displayTrendRows.length" class="trend-mobile-detail-hero">
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
          <span>{{ trendTierSummaryLabel }}</span>
        </div>
      </div>
      <div v-if="isMobileViewport && !displayTrendRows.length" class="trend-empty-workbench trend-empty-workbench-mobile">
        <div class="trend-empty-workbench-copy">
          <p class="panel-kicker">价格明细</p>
          <strong>{{ emptyTrendTitle }}</strong>
          <span v-if="emptyTrendModeHint">{{ emptyTrendModeHint }}</span>
          <span>{{ emptyTrendDescription }}</span>
        </div>
        <div v-if="recommendedTrendOptions.length" class="trend-empty-product-list primary">
          <span>可查看的商品</span>
          <button
            v-for="item in recommendedTrendOptions"
            :key="item.price_identity_key"
            type="button"
            class="trend-empty-product-button primary"
            @click="selectRecommendedTrendProduct(item.price_identity_key)"
          >
            <img
              v-if="isSourceProductImageAllowed(item.source_name) && item.image_url && !brokenTrendImageUrls.has(item.image_url)"
              :src="item.image_url"
              alt=""
              loading="lazy"
              @error="handleTrendImageError(item.image_url)"
              @click.stop="openImagePreview(item.image_url, item.price_identity_label)"
            />
            <span>
              <strong>{{ item.price_identity_label }}</strong>
              <small>{{ item.source_name || '来源' }} · {{ item.source_category || '未分类' }}</small>
            </span>
          </button>
        </div>
        <div class="trend-empty-action-row">
          <button
            v-if="trendMode === 'cross_market' && availableSites.length"
            type="button"
            class="trend-empty-action primary"
            @click="emit('update:trend-mode', 'single_market')"
          >
            查看当前市场
          </button>
          <button
            v-else-if="recommendedTrendOptions.length"
            type="button"
            class="trend-empty-action primary"
            @click="selectRecommendedTrendProduct(recommendedTrendOptions[0].price_identity_key)"
          >
            选择商品
          </button>
          <button type="button" class="trend-empty-action" @click="emit('refresh-trend')">刷新价格</button>
        </div>
      </div>
      <div v-if="!isMobileViewport && displayTrendRows.length && decisionCards.length" class="trend-mobile-decision-grid">
        <article v-for="item in decisionCards" :key="item.title" class="trend-mobile-decision-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.title }}</strong>
          <small>{{ item.detail }}</small>
        </article>
      </div>
      <div v-if="productSummary && isMobileViewport && displayTrendRows.length" class="trend-mobile-overview">
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
          <span>来源层级</span>
          <strong>{{ visibleTierMetas.length || 0 }}</strong>
          <small>{{ trendTierSummaryLabel }}</small>
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
          <span>来源层级</span>
          <strong>{{ visibleTierMetas.length || 0 }}</strong>
          <small>{{ trendTierSummaryLabel }}</small>
        </div>
      </div>
      <div class="trend-main-grid">
        <div>
          <div v-if="productSummary && !isMobileViewport" class="trend-insight-strip">
            <span>最低价市场：{{ productSummary.current_lowest_site ?? '-' }}</span>
            <span>最高价市场：{{ productSummary.current_highest_site ?? '-' }}</span>
            <span>最近更新：{{ productSummary.latest_captured_at ?? '-' }}</span>
            <span>来源层级：{{ trendTierSummaryLabel }}</span>
          </div>
          <div v-if="displayTrendRows.length" class="trend-chart-shell">
            <div v-if="isMobileViewport" class="trend-mobile-chart-title">
              <strong>价格趋势（元/公斤）</strong>
              <span>{{ trendMode === 'cross_market' ? '7 日趋势' : currentSiteLabel || '单市场' }}</span>
            </div>
            <button
              v-if="!isMobileViewport && isComparisonMode && comparisonPageCount > 1"
              type="button"
              class="trend-chart-nav trend-chart-nav-left"
              :disabled="comparisonPageIndex <= 0"
              @click="comparisonPageIndex -= 1"
            >
              ◀
            </button>
            <svg
              v-if="isMobileViewport"
              class="trend-mobile-svg-chart"
              viewBox="0 0 320 156"
              role="img"
              aria-label="商品价格变化"
            >
              <line v-for="y in [24, 56, 88, 120]" :key="`trend-grid-${y}`" x1="14" :y1="y" x2="306" :y2="y" />
              <polyline
                v-for="line in mobileTrendSvgLines"
                :key="line.name"
                :points="line.points"
                :class="line.tone"
              />
              <circle
                v-for="point in mobileTrendSvgDots"
                :key="`${point.name}-${point.x}-${point.y}`"
                :class="point.tone"
                :cx="point.x"
                :cy="point.y"
                r="3"
              />
            </svg>
            <div v-else ref="trendChartRef" class="trend-chart" :style="{ height: chartHeight }"></div>
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
          <div v-if="displayTrendRows.length && !isMobileViewport" class="trend-hover-inspector">
            <div class="trend-hover-summary">
              <p class="panel-kicker">悬停查看</p>
              <strong>{{ hoveredTrendSnapshot?.axisLabel || '最近趋势点' }}</strong>
              <small>{{ hoveredTrendSnapshot?.summary || '把鼠标移到折线上，查看该时间点的具体来源和价格。' }}</small>
            </div>
            <div class="trend-hover-grid">
              <article v-for="item in hoveredTrendItems" :key="`${item.name}-${item.price}`" class="trend-hover-card">
                <span>{{ item.name }}</span>
                <strong>{{ item.price }}</strong>
                <small>{{ item.actual ? '真实报价点' : '沿用上次报价' }}</small>
              </article>
            </div>
          </div>
          <div v-else-if="!isMobileViewport" class="trend-empty-workbench">
            <div class="trend-empty-workbench-copy">
              <p class="panel-kicker">走势数据</p>
              <strong>{{ emptyTrendTitle }}</strong>
              <span v-if="emptyTrendModeHint">{{ emptyTrendModeHint }}</span>
              <span>{{ emptyTrendDescription }}</span>
            </div>
            <div class="trend-empty-action-row">
              <button
                v-if="trendMode === 'cross_market' && availableSites.length"
                type="button"
                class="trend-empty-action primary"
                @click="emit('update:trend-mode', 'single_market')"
              >
                查看单市场/行情快照
              </button>
              <button
                v-else-if="recommendedTrendOptions.length"
                type="button"
                class="trend-empty-action primary"
                @click="selectRecommendedTrendProduct(recommendedTrendOptions[0].price_identity_key)"
              >
                选择有走势商品
              </button>
              <button type="button" class="trend-empty-action" @click="emit('refresh-trend')">重新同步走势</button>
            </div>
            <div v-if="recommendedTrendOptions.length" class="trend-empty-product-list">
              <span>可选有走势商品</span>
              <button
                v-for="item in recommendedTrendOptions"
                :key="item.price_identity_key"
                type="button"
                class="trend-empty-product-button"
                @click="selectRecommendedTrendProduct(item.price_identity_key)"
              >
                <strong>{{ item.price_identity_label }}</strong>
                <small>{{ item.site_count || 0 }} 个市场</small>
              </button>
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
                  <div class="trend-row-source-bar">
                    <span :class="sourceTierChipClass(item.tierMeta)">{{ item.tierMeta.shortLabel }}</span>
                    <small>{{ item.sourceLabel }}</small>
                  </div>
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
        <div v-if="!(isMobileViewport && !recentTrendRows.length)" class="trend-list-shell" :class="{ compact: isMobileViewport }">
          <div class="trend-list-head">
            <strong>最近记录</strong>
            <span>{{ trendListCountLabel }}</span>
          </div>
          <div v-if="recentTrendRows.length" class="trend-list">
            <div v-for="row in recentTrendRows" :key="`${row.trend_series_key || row.site_name}-${row.captured_at}-${row.current_price}`" class="trend-row">
              <div>
                <div class="trend-row-source-bar">
                  <span :class="sourceTierChipClass(resolveTrendSourceTierMeta(row.source_tier))">
                    {{ resolveTrendSourceTierMeta(row.source_tier).shortLabel }}
                  </span>
                  <small>{{ buildTrendSourceSummary(row) }}</small>
                </div>
                <strong>{{ buildTrendSeriesName(row) }}</strong>
                <p>{{ buildTrendMeta(row) }}</p>
              </div>
              <div class="trend-price">{{ formatPrice(row.current_price) }}</div>
              <div class="trend-time">{{ formatTrendTime(row.captured_at) }}</div>
            </div>
          </div>
          <div v-else class="trend-side-empty">
            <strong>走势记录待补齐</strong>
            <p>{{ sideEmptyTrendDescription }}</p>
          </div>
        </div>
      </div>
      <section v-if="!loading" class="trend-supplier-collapsible">
        <button type="button" class="trend-supplier-toggle" @click="showSupplierQuotePanel = !showSupplierQuotePanel">
          <span>
            <strong>查看/补录供应商报价</strong>
            <small>补齐本地报价，辅助走势待补齐时决策</small>
          </span>
          <em>{{ showSupplierQuotePanel ? '收起' : '查看/补录' }}</em>
        </button>
        <SupplierQuotePanel
          v-if="showSupplierQuotePanel"
          :selected-identity-key="selectedIdentityKey"
          :product-label="currentProductLabel"
          :mobile="isMobileViewport"
        />
      </section>
      <div v-if="isMobileViewport && sourceExplainers.length && displayTrendRows.length" class="trend-mobile-source-note">
        <strong>采购说明</strong>
        <p v-for="item in sourceExplainers" :key="item">{{ item }}</p>
      </div>
      <div v-if="loading" class="trend-loading-mask">
        <div class="trend-loading-card">
          <span class="trend-loading-dot"></span>
          <strong>正在切换商品</strong>
          <p>正在加载最新价格。</p>
        </div>
      </div>
    </div>
    <div v-else-if="loading" class="table-empty-state trend-empty-state trend-main-empty-state trend-pending-state">
      <strong>正在准备价格明细</strong>
      <p>正在加载可查看的商品，请稍候。</p>
    </div>
    <div v-else class="table-empty-state trend-empty-state trend-main-empty-state">
      <div class="trend-main-empty-copy">
        <strong>先选择一个商品</strong>
        <p>选择后查看这个商品的价格变化。</p>
      </div>
      <div v-if="isMobileViewport && productOptions.length" class="trend-empty-product-list trend-empty-product-list-mobile">
        <span>可直接查看的商品</span>
        <button
          v-for="item in productOptions.slice(0, 3)"
          :key="item.price_identity_key"
          type="button"
          class="trend-empty-product-button"
          @click="selectRecommendedTrendProduct(item.price_identity_key)"
        >
          <img
            v-if="isSourceProductImageAllowed(item.source_name) && item.image_url && !brokenTrendImageUrls.has(item.image_url)"
            :src="item.image_url"
            alt=""
            loading="lazy"
            @error="handleTrendImageError(item.image_url)"
            @click.stop="openImagePreview(item.image_url, item.price_identity_label)"
          />
          <span>
            <strong>{{ item.price_identity_label }}</strong>
            <small>{{ item.source_name || '来源' }} · {{ item.source_category || '未分类' }}</small>
          </span>
        </button>
      </div>
      <div v-else-if="isMobileViewport" class="trend-empty-action-row trend-empty-refresh-row">
        <button type="button" class="trend-empty-action primary" @click="emit('refresh-products')">刷新商品列表</button>
        <button type="button" class="trend-empty-action" @click="emit('refresh-trend')">刷新价格</button>
      </div>
      <div v-else class="trend-empty-action-row">
        <button type="button" class="trend-empty-action primary" @click="emit('refresh-products')">刷新商品列表</button>
        <button type="button" class="trend-empty-action" @click="emit('open-tab', 'summary')">去查菜价</button>
        <button type="button" class="trend-empty-action" @click="emit('open-tab', 'menu')">去采购计划</button>
      </div>
      <div v-if="isMobileViewport" class="trend-empty-next-actions">
        <span>可选操作</span>
        <button type="button" @click="emit('open-tab', 'summary')">
          <strong>查看菜价</strong>
          <small>从商品列表进入明细</small>
        </button>
        <button type="button" @click="emit('open-tab', 'menu')">
          <strong>去采购计划</strong>
          <small>按菜单生成采购建议</small>
        </button>
      </div>
    </div>
    <teleport v-if="isMobileViewport && imagePreviewVisible" to="body">
      <div class="trend-image-preview-backdrop" role="dialog" aria-modal="true" @click="closeImagePreview">
        <div class="trend-image-preview-panel" @click.stop>
          <div class="trend-image-preview-head">
            <strong>{{ imagePreviewTitle || '图片预览' }}</strong>
            <button type="button" aria-label="关闭图片预览" @click="closeImagePreview">关闭</button>
          </div>
          <img v-if="imagePreviewUrl" :src="imagePreviewUrl" :alt="imagePreviewTitle || ''" class="trend-image-preview" />
        </div>
      </div>
    </teleport>
    <el-dialog v-if="!isMobileViewport" v-model="imagePreviewVisible" :title="imagePreviewTitle || '图片预览'" width="min(92vw, 960px)">
      <div class="trend-image-preview-shell">
        <img v-if="imagePreviewUrl" :src="imagePreviewUrl" :alt="imagePreviewTitle || ''" class="trend-image-preview" />
      </div>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import type { ProductOptionItem, ProductTrendRow } from '../types'
import { useViewport } from '../composables/useViewport'

const SupplierQuotePanel = defineAsyncComponent({
  loader: () => import('./SupplierQuotePanel.vue'),
  delay: 0,
  suspensible: false,
})

const props = defineProps<{
  productOptions: ProductOptionItem[]
  searchProductOptions?: ProductOptionItem[]
  productSearchLoading?: boolean
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
  (event: 'search-product-options', value: string): void
  (event: 'update:trend-mode', value: 'cross_market' | 'single_market'): void
  (event: 'update:selected-site-name', value: string): void
  (event: 'refresh-trend'): void
  (event: 'refresh-products'): void
  (event: 'open-tab', value: 'summary' | 'menu'): void
}>()

const trendChartRef = ref<HTMLDivElement | null>(null)
const { isMobileViewport, isNarrowViewport, isShortViewport } = useViewport()
type EChartsCoreModule = typeof import('echarts/core')
let echartsModule: EChartsCoreModule | null = null
let trendChart: import('echarts/core').ECharts | null = null
let resizeObserver: ResizeObserver | null = null
const comparisonPageIndex = ref(0)
const showSupplierQuotePanel = ref(false)
const productSearchQuery = ref('')
const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')
const imagePreviewTitle = ref('')
const brokenTrendImageUrls = reactive(new Set<string>())
const hoveredTrendSnapshot = ref<null | {
  axisLabel: string
  summary: string
  items: Array<{ name: string; price: string; actual: boolean }>
}>(null)
const PRODUCT_SELECT_DEFAULT_LIMIT = 80
const PRODUCT_SELECT_SEARCH_LIMIT = 120
type SourceTierTone = 'primary' | 'official' | 'local' | 'reference' | 'neutral'
type SourceTierKey = 'primary' | 'official' | 'local' | 'reference' | 'other'
type SourceTierMeta = {
  key: SourceTierKey
  label: string
  shortLabel: string
  tone: SourceTierTone
  rank: number
}

const SOURCE_TIER_META: Record<SourceTierKey, SourceTierMeta> = {
  primary: { key: 'primary', label: '主价格源', shortLabel: '主源', tone: 'primary', rank: 0 },
  official: { key: 'official', label: '官方参考源', shortLabel: '官方', tone: 'official', rank: 1 },
  local: { key: 'local', label: '本地市场源', shortLabel: '本地', tone: 'local', rank: 2 },
  reference: { key: 'reference', label: '第三方参考源', shortLabel: '第三方', tone: 'reference', rank: 3 },
  other: { key: 'other', label: '未分层来源', shortLabel: '未分层', tone: 'neutral', rank: 4 },
}

const currentProductOption = computed(() =>
  props.productOptions.find((item) => item.price_identity_key === props.selectedIdentityKey) ||
  (props.selectedIdentityKey ? ({
    price_identity_key: props.selectedIdentityKey,
    price_identity_label: String(props.productSummary?.product_name || props.selectedIdentityKey),
    site_count: Number(props.productSummary?.site_count || 0),
  } as ProductOptionItem) : null),
)
const baseProductOptions = computed(() => (
  isMobileViewport.value
    ? (normalizeProductSearchText(productSearchQuery.value)
        ? (props.searchProductOptions || [])
        : props.productOptions.slice(0, PRODUCT_SELECT_DEFAULT_LIMIT))
    : props.productOptions
))
const visibleProductOptions = computed(() => {
  const query = normalizeProductSearchText(productSearchQuery.value)
  const selectedKey = String(props.selectedIdentityKey || '').trim()
  const selectedCandidate = selectedKey
    ? ([...baseProductOptions.value, ...props.productOptions].find((item) => item.price_identity_key === selectedKey) || null)
    : null
  const selectedMatchesQuery = selectedCandidate && query
    ? normalizeProductSearchText(
        `${selectedCandidate.price_identity_label} ${selectedCandidate.price_identity_key} ${selectedCandidate.source_name || ''} ${selectedCandidate.source_category || ''} ${selectedCandidate.liancai_subcategory || ''}`,
      ).includes(query)
    : true
  const selected = !query || selectedMatchesQuery ? selectedCandidate : null
  const matched = baseProductOptions.value
    .filter((item) => {
      if (isMobileViewport.value) return true
      if (!query) return true
      return normalizeProductSearchText(
        `${item.price_identity_label} ${item.price_identity_key} ${item.source_name || ''} ${item.source_category || ''} ${item.liancai_subcategory || ''}`,
      ).includes(query)
    })
    .sort((left, right) => Number(right.site_count || 0) - Number(left.site_count || 0))
    .slice(0, query ? PRODUCT_SELECT_SEARCH_LIMIT : PRODUCT_SELECT_DEFAULT_LIMIT)
  const rows = selected ? [selected, ...matched.filter((item) => item.price_identity_key !== selected.price_identity_key)] : matched
  return rows
})
const availableSites = computed(() => props.siteOptions || [])
const isComparisonMode = computed(() => props.trendMode === 'cross_market')
const shouldCarryForwardPrice = computed(() => isComparisonMode.value)
const currentProductLabel = computed(() => currentProductOption.value?.price_identity_label || '')
const summaryIdentityKey = computed(() => String(props.productSummary?.price_identity_key || '').trim())
const productMismatch = computed(() => Boolean(props.selectedIdentityKey && summaryIdentityKey.value && summaryIdentityKey.value !== props.selectedIdentityKey))
const fallbackProductLabel = computed(() => currentProductLabel.value || String(props.selectedIdentityKey || '当前商品'))
const currentProductCoverageLabel = computed(() => {
  const siteCount = Number(currentProductOption.value?.site_count || 0)
  return siteCount ? `已覆盖 ${siteCount} 个市场` : '市场覆盖待确认'
})
const currentSiteLabel = computed(() => String(props.selectedSiteName || '').trim())
const currentScopeLabel = computed(() => (
  props.trendMode === 'cross_market'
    ? `跨市场 · ${availableSites.value.length || fallbackTrendRows.value.length || 0} 个市场`
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
const fallbackTrendRows = computed<ProductTrendRow[]>(() => {
  if (props.trendRows.length || !props.productSummary) return []
  const capturedAt = String(props.productSummary.latest_captured_at || new Date().toISOString())
  const productName = currentProductLabel.value || String(props.productSummary.product_name || '当前商品')
  const rows: ProductTrendRow[] = []
  const lowestPrice = numericProductSummary.value.current_lowest_price
  const averagePrice = numericProductSummary.value.average_price
  const highestPrice = numericProductSummary.value.current_highest_price
  if (lowestPrice != null) {
    rows.push({
      site_name: String(props.productSummary.current_lowest_site || '最低价来源'),
      source_name: String(props.productSummary.current_lowest_site || '行情主表'),
      source_tier: '本地市场源',
      market_name: String(props.productSummary.current_lowest_site || '本地市场'),
      region_label: String(props.productSummary.current_lowest_site || '本地市场'),
      current_price: lowestPrice,
      captured_at: capturedAt,
      product_name: productName,
      trend_series_name: String(props.productSummary.current_lowest_site || '最低价来源'),
      trend_meta_label: '商品 summary 当前最低价',
    })
  }
  if (averagePrice != null && averagePrice !== lowestPrice) {
    rows.push({
      site_name: '今日均价',
      source_name: '行情主表',
      source_tier: '第三方参考源',
      market_name: '今日均价',
      region_label: '本地市场',
      current_price: averagePrice,
      captured_at: capturedAt,
      product_name: productName,
      trend_series_name: '今日均价',
      trend_meta_label: '商品 summary 平均价',
    })
  }
  if (highestPrice != null && highestPrice !== averagePrice && highestPrice !== lowestPrice) {
    rows.push({
      site_name: String(props.productSummary.current_highest_site || '最高价来源'),
      source_name: String(props.productSummary.current_highest_site || '行情主表'),
      source_tier: '第三方参考源',
      market_name: String(props.productSummary.current_highest_site || '本地市场'),
      region_label: String(props.productSummary.current_highest_site || '本地市场'),
      current_price: highestPrice,
      captured_at: capturedAt,
      product_name: productName,
      trend_series_name: String(props.productSummary.current_highest_site || '最高价来源'),
      trend_meta_label: '商品 summary 当前最高价',
    })
  }
  return rows
})
const displayTrendRows = computed(() => props.trendRows.length ? props.trendRows : fallbackTrendRows.value)
const chartCategories = computed(() => buildChartCategories(displayTrendRows.value))
const allChartSeries = computed(() => buildChartSeries(displayTrendRows.value, chartCategories.value, shouldCarryForwardPrice.value))
const comparisonSeriesPages = computed(() => buildSeriesPages(allChartSeries.value, isComparisonMode.value))
const comparisonPageCount = computed(() => comparisonSeriesPages.value.length)
const visibleChartSeries = computed(() => {
  const page = comparisonSeriesPages.value[comparisonPageIndex.value]
  return page && page.length ? page : (comparisonSeriesPages.value[0] || [])
})
const mobileTrendSvgLines = computed(() => buildMobileTrendSvgLines())
const mobileTrendSvgDots = computed(() =>
  mobileTrendSvgLines.value.flatMap((line) =>
    line.dots.map((point) => ({
      ...point,
      name: line.name,
      tone: line.tone,
    })),
  ),
)
const visibleSeriesNameSet = computed(() => new Set(visibleChartSeries.value.map((item) => String(item.name || '').trim()).filter(Boolean)))
const recentTrendRows = computed(() =>
  [...displayTrendRows.value]
    .filter((row) => visibleSeriesNameSet.value.has(buildTrendSeriesName(row)))
    .sort((left, right) => String(right.captured_at || '').localeCompare(String(left.captured_at || '')))
    .slice(0, isMobileViewport.value ? 2 : 18),
)
const visibleTierMetas = computed(() => {
  const metaByKey = new Map<SourceTierKey, SourceTierMeta>()
  recentTrendRows.value.forEach((row) => {
    const meta = resolveTrendSourceTierMeta(row.source_tier)
    if (!metaByKey.has(meta.key)) {
      metaByKey.set(meta.key, meta)
    }
  })
  return Array.from(metaByKey.values()).sort((left, right) => left.rank - right.rank)
})
const trendTierSummaryLabel = computed(() => {
  if (!visibleTierMetas.value.length) {
    return currentOverviewRangeLabel.value
  }
  if (visibleTierMetas.value.length === 1) {
    return `${visibleTierMetas.value[0].label}优先`
  }
  return `${visibleTierMetas.value[0].shortLabel}优先 · ${visibleTierMetas.value.length} 个层级`
})
const latestTrendRow = computed(() => recentTrendRows.value[0] || null)
const latestTrendSourceSummary = computed(() => {
  if (!latestTrendRow.value) {
    return props.productSummary?.current_lowest_site ?? '-'
  }
  return buildTrendSourceSummary(latestTrendRow.value)
})
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
      sourceLabel: buildTrendSourceSummary(row),
      tierMeta: resolveTrendSourceTierMeta(row.source_tier),
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
      detail: '当前只有 1 个稳定来源，更适合查看该市场的连续报价。',
    })
  } else if (avgPrice != null && lowPrice != null && avgPrice - lowPrice >= 1) {
    cards.push({
      label: '建议动作',
      title: '建议优先比价采购',
      detail: `当前最低价较均价低 ${(avgPrice - lowPrice).toFixed(2)}，适合查看低价市场。`,
    })
  } else {
    cards.push({
      label: '建议动作',
      title: '建议继续观察走势',
      detail: '当前价位接近均价，建议结合最近 3 次报价判断下单节奏。',
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
const hoveredTrendItems = computed(() => (hoveredTrendSnapshot.value?.items || []).slice(0, 4))
const chartHeight = computed(() => {
  if (!isMobileViewport.value) {
    if (comparisonPageCount.value > 1 || visibleChartSeries.value.length >= 4) return isNarrowViewport.value ? '340px' : '380px'
    return isNarrowViewport.value ? '320px' : '360px'
  }
  if (isShortViewport.value) {
    if (comparisonPageCount.value > 1 || visibleChartSeries.value.length >= 4) return '216px'
    if (chartCategories.value.length >= 10) return '204px'
    return '190px'
  }
  if (comparisonPageCount.value > 1 || visibleChartSeries.value.length >= 4) return '236px'
  if (chartCategories.value.length >= 10) return '220px'
  return '204px'
})
const trendListCountLabel = computed(() => (
  isMobileViewport.value
    ? `${recentTrendRows.value.length} / ${displayTrendRows.value.length} 条`
    : `${displayTrendRows.value.length} 条`
))
const recommendedTrendOptions = computed(() =>
  props.productOptions
    .filter((item) => item.price_identity_key !== props.selectedIdentityKey && Number(item.site_count || 0) > 0)
    .sort((left, right) => Number(right.site_count || 0) - Number(left.site_count || 0))
    .slice(0, isMobileViewport.value ? 3 : 5),
)
const hasProductMarketSnapshot = computed(() => {
  if (displayTrendRows.value.length) return false
  const summary = props.productSummary
  if (!summary) return false
  return [
    summary.latest_captured_at,
    summary.current_lowest_site,
    summary.current_highest_site,
    summary.site_count,
    summary.current_price,
    summary.current_lowest_price,
    summary.current_highest_price,
    summary.average_price,
    summary.price_span,
  ].some((value) => normalizeNumericValue(value) != null || String(value || '').trim().length > 0)
})
const emptyTrendTitle = computed(() => (
  props.trendMode === 'cross_market'
    ? '价格记录还不完整'
    : '价格记录待补齐'
))
const emptyTrendModeHint = computed(() => {
  if (hasProductMarketSnapshot.value && availableSites.value.length) {
    return '当前商品已有市场价格，可先查看当前市场。'
  }
  if (recommendedTrendOptions.value.length) {
    return '可选择下方商品，或刷新价格。'
  }
  return props.trendMode === 'cross_market'
    ? '多市场价格还在整理中。'
    : ''
})
const emptyTrendDescription = computed(() => {
  if (!currentProductLabel.value) {
    return '先选择一个商品，再查看价格。'
  }
  if (hasProductMarketSnapshot.value) {
    if (availableSites.value.length > 0) {
      return `${currentProductLabel.value} 已有当前市场价格，可先查看当前市场。`
    }
    return `${currentProductLabel.value} 已有价格记录，可选择商品或刷新价格。`
  }
  if (availableSites.value.length > 0) {
    return `${currentProductLabel.value} 已有关联市场，可查看当前市场或刷新价格。`
  }
  return `${currentProductLabel.value} 的价格记录还在整理中，可选择下方商品或刷新价格。`
})
const sideEmptyTrendDescription = computed(() => {
  if (hasProductMarketSnapshot.value) {
    return '当前价格仍可参考，也可以刷新价格。'
  }
  if (recommendedTrendOptions.value.length) {
    return '可切换下方商品或刷新价格。'
  }
  return '当前价格记录还在整理中，可刷新价格。'
})

function selectRecommendedTrendProduct(identityKey: string) {
  if (!identityKey) return
  emit('select-product', identityKey)
}

function openImagePreview(url: string | null | undefined, title: string) {
  const normalizedUrl = String(url || '').trim()
  if (!normalizedUrl) return
  imagePreviewUrl.value = normalizedUrl
  imagePreviewTitle.value = String(title || '').trim()
  imagePreviewVisible.value = true
}

function handleTrendImageError(url: string | null | undefined) {
  const normalizedUrl = String(url || '').trim()
  if (!normalizedUrl) return
  brokenTrendImageUrls.add(normalizedUrl)
}

function isLiancaiProductImageSource(sourceName: string) {
  return sourceName === '莲菜网'
}

function isMeicaiProductImageSource(sourceName: string) {
  return sourceName === '美菜网'
}

function isSourceProductImageAllowed(sourceName: string | null | undefined) {
  const normalizedSourceName = String(sourceName || '').trim()
  return isLiancaiProductImageSource(normalizedSourceName) || isMeicaiProductImageSource(normalizedSourceName)
}

function closeImagePreview() {
  imagePreviewVisible.value = false
}

function normalizeProductSearchText(value: string) {
  return String(value || '').replace(/\s+/g, '').toLowerCase()
}

function handleProductFilter(query: string) {
  productSearchQuery.value = query
  if (isMobileViewport.value) {
    emit('search-product-options', query)
  }
}

function handleProductRemoteSearch(query: string) {
  productSearchQuery.value = query
  emit('search-product-options', query)
}

function readNativeSelectValue(event: Event) {
  return event.target instanceof HTMLSelectElement ? event.target.value : ''
}

function handleNativeProductChange(event: Event) {
  const identityKey = readNativeSelectValue(event)
  if (!identityKey) return
  productSearchQuery.value = ''
  emit('select-product', identityKey)
}

function handleNativeSiteChange(event: Event) {
  emit('update:selected-site-name', readNativeSelectValue(event))
}

function handleProductSelectVisibleChange(visible: boolean) {
  if (visible && isMobileViewport.value) {
    emit('search-product-options', productSearchQuery.value)
  }
  if (!visible) {
    productSearchQuery.value = ''
  }
}

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

function buildMobileTrendSvgLines() {
  const seriesItems = visibleChartSeries.value.slice(0, 2)
  const numericSeries = seriesItems.map((seriesItem, index) => {
    const values = Array.isArray(seriesItem.data)
      ? seriesItem.data
        .map((item: any) => Number(item?.value ?? item))
        .filter((value: number) => !Number.isNaN(value))
      : []
    return {
      name: String(seriesItem.name || `series-${index}`),
      tone: index === 0 ? 'line-blue' : 'line-green',
      values,
    }
  }).filter((item) => item.values.length)

  const allValues = numericSeries.flatMap((item) => item.values)
  if (!allValues.length) {
    return []
  }
  const minValue = Math.min(...allValues)
  const maxValue = Math.max(...allValues)
  const range = Math.max(maxValue - minValue, 1)

  return numericSeries.map((seriesItem) => {
    const count = Math.max(seriesItem.values.length - 1, 1)
    const dots = seriesItem.values.map((value, index) => {
      const x = 18 + (index / count) * 284
      const y = 126 - ((value - minValue) / range) * 96
      return {
        x: Number(x.toFixed(2)),
        y: Number(y.toFixed(2)),
      }
    })
    return {
      ...seriesItem,
      points: dots.map((point) => `${point.x},${point.y}`).join(' '),
      dots,
    }
  })
}

function syncHoveredTrendSnapshot(axisIndex: number) {
  const axisLabel = chartCategories.value[axisIndex]
  if (axisLabel == null) {
    hoveredTrendSnapshot.value = null
    return
  }

  const items = visibleChartSeries.value
    .map((seriesItem) => {
      const point = Array.isArray(seriesItem.data) ? seriesItem.data[axisIndex] : null
      if (!point || point.value == null) return null
      return {
        name: String(seriesItem.name || '未命名来源'),
        price: formatPrice(Number(point.value)),
        actual: Boolean(point.isActual),
      }
    })
    .filter(Boolean) as Array<{ name: string; price: string; actual: boolean }>

  hoveredTrendSnapshot.value = {
    axisLabel: formatTrendAxisLabel(axisLabel),
    summary: items.length ? `当前共有 ${items.length} 条走势可读，优先看真实报价点。` : '当前时间点暂无可读走势。',
    items,
  }
}

async function renderTrendChart() {
  if (!trendChartRef.value) return
  await nextTick()
  await new Promise((resolve) => window.requestAnimationFrame(() => resolve(undefined)))
  const chart = await ensureTrendChart()
  if (!chart) return

  if (!displayTrendRows.value.length) {
    chart.clear()
    chart.resize()
    hoveredTrendSnapshot.value = null
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
      top: isMobileViewport.value ? 0 : 10,
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
      top: isMobileViewport.value ? 42 : 62,
      bottom: isMobileViewport.value ? 28 : 24,
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
        margin: isMobileViewport.value ? 10 : 8,
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

  chart.off('updateAxisPointer')
  chart.off('globalout')
  chart.on('updateAxisPointer', (event: any) => {
    const axisInfo = Array.isArray(event?.axesInfo) ? event.axesInfo[0] : null
    if (!axisInfo) return
    const axisIndex = typeof axisInfo.value === 'number'
      ? axisInfo.value
      : categories.indexOf(String(axisInfo.value || '').trim())
    if (axisIndex >= 0) {
      syncHoveredTrendSnapshot(axisIndex)
    }
  })
  chart.on('globalout', () => {
    syncHoveredTrendSnapshot(categories.length - 1)
  })
  syncHoveredTrendSnapshot(categories.length - 1)
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

function buildTrendSourceName(row: ProductTrendRow) {
  const explicitSourceName = String(row.source_name || '').trim()
  if (explicitSourceName) {
    return explicitSourceName
  }
  const siteText = String(row.site_name || '').trim()
  if (siteText.includes('|')) {
    return siteText.split('|')[0].trim()
  }
  return siteText
}

function buildTrendSourceSummary(row: ProductTrendRow) {
  const sourceName = buildTrendSourceName(row)
  const tierLabel = resolveTrendSourceTierMeta(row.source_tier).label
  const parts = [sourceName, tierLabel].filter(Boolean)
  return parts.length ? Array.from(new Set(parts)).join(' · ') : '来源待补充'
}

function resolveTrendSourceTierMeta(sourceTier?: string | null): SourceTierMeta {
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
  return `trend-source-tier-chip tone-${tierMeta.tone}`
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
  () => props.selectedIdentityKey,
  () => {
    showSupplierQuotePanel.value = false
  },
)

watch(
  () => [displayTrendRows.value, props.selectedIdentityKey, props.trendMode, props.selectedSiteName, comparisonPageIndex.value],
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

.trend-hover-inspector {
  display: grid;
  grid-template-columns: minmax(220px, 0.78fr) minmax(0, 1.22fr);
  gap: 12px;
  margin-top: 12px;
  padding: 14px 16px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.trend-hover-summary {
  display: grid;
  gap: 5px;
}

.trend-hover-summary strong {
  color: #112033;
  font-size: 18px;
  line-height: 1.2;
}

.trend-hover-summary small,
.trend-hover-card small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.trend-hover-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.trend-hover-card {
  display: grid;
  gap: 3px;
  min-height: 74px;
  padding: 12px 14px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.96);
}

.trend-hover-card span {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.trend-hover-card strong {
  color: #1d4ed8;
  font-size: 20px;
  line-height: 1.05;
}

.trend-mobile-mode-switch {
  display: none;
}

.trend-mobile-current-product {
  display: none;
}

.trend-mobile-chart-title {
  display: none;
}

.trend-mobile-svg-chart {
  display: none;
}

:global(.trend-product-select-popper) {
  width: min(520px, calc(100vw - 32px));
  max-width: calc(100vw - 32px);
}

:global(.trend-product-select-popper .el-select-dropdown__item) {
  height: auto;
  min-height: 34px;
  padding: 7px 12px;
  line-height: 1.35;
  white-space: normal;
}

:global(.trend-product-select-popper .trend-product-option) {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  min-width: 0;
  white-space: normal;
  overflow-wrap: anywhere;
}

:global(.trend-product-select-popper .trend-product-option img) {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  object-fit: cover;
  background: #f1f5f9;
  cursor: zoom-in;
}

.trend-empty-product-button img {
  cursor: zoom-in;
}

.trend-image-preview-shell {
  display: grid;
  place-items: center;
}

.trend-image-preview-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2400;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(15, 23, 42, 0.62);
}

.trend-image-preview-panel {
  display: grid;
  gap: 12px;
  width: min(100%, 720px);
  max-height: 88vh;
  padding: 12px;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.28);
}

.trend-image-preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.trend-image-preview-head strong {
  min-width: 0;
  overflow: hidden;
  color: #071226;
  font-size: 15px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trend-image-preview-head button {
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

.trend-image-preview {
  max-width: 100%;
  max-height: 76vh;
  border-radius: 12px;
}

:global(.trend-product-select-popper .trend-product-option span) {
  display: grid;
  gap: 2px;
  min-width: 0;
}

:global(.trend-product-select-popper .trend-product-option strong) {
  color: #112033;
  font-size: 13px;
  line-height: 1.25;
}

:global(.trend-product-select-popper .trend-product-option small) {
  color: #64748b;
  font-size: 11px;
  line-height: 1.2;
}

.trend-empty-workbench {
  display: grid;
  gap: 14px;
  min-height: 260px;
  padding: 18px;
  border: 1px solid rgba(96, 165, 250, 0.18);
  border-radius: 20px;
  background:
    linear-gradient(145deg, rgba(239, 246, 255, 0.9), rgba(255, 255, 255, 0.98)),
    linear-gradient(135deg, rgba(37, 99, 235, 0.05), transparent);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
  align-content: start;
}

.trend-empty-workbench-copy {
  display: grid;
  gap: 6px;
}

.trend-empty-workbench-copy strong {
  color: #112033;
  font-size: 18px;
  line-height: 1.25;
}

.trend-empty-workbench-copy span,
.trend-empty-product-list > span,
.trend-empty-product-button small {
  color: #63738c;
  font-size: 12px;
  line-height: 1.5;
}

.trend-empty-action-row,
.trend-empty-product-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.trend-empty-product-list {
  display: grid;
}

.trend-empty-action,
.trend-empty-product-button {
  min-height: 36px;
  border: 1px solid rgba(54, 84, 134, 0.16);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.94);
  color: #365486;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.trend-empty-action {
  padding: 0 14px;
}

.trend-empty-action.primary {
  border-color: rgba(37, 99, 235, 0.24);
  background: #2563eb;
  color: #fff;
}

.trend-empty-product-button {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 9px 11px;
  text-align: left;
}

.trend-empty-product-button img {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  object-fit: cover;
  background: #f1f5f9;
}

.trend-empty-product-button span {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.trend-empty-product-button strong {
  overflow: hidden;
  color: #112033;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  border-radius: 16px;
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
.trend-mobile-source-note p,
.trend-row-source-bar small {
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

.trend-row-source-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.trend-source-tier-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-family: var(--code-font);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.trend-source-tier-chip.tone-primary {
  background: rgba(30, 64, 175, 0.12);
  border: 1px solid rgba(37, 99, 235, 0.22);
  color: #1d4ed8;
}

.trend-source-tier-chip.tone-official {
  background: rgba(245, 158, 11, 0.14);
  border: 1px solid rgba(245, 158, 11, 0.22);
  color: #b45309;
}

.trend-source-tier-chip.tone-local {
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: #047857;
}

.trend-source-tier-chip.tone-reference {
  background: rgba(124, 58, 237, 0.1);
  border: 1px solid rgba(124, 58, 237, 0.18);
  color: #6d28d9;
}

.trend-source-tier-chip.tone-neutral {
  background: rgba(148, 163, 184, 0.14);
  border: 1px solid rgba(148, 163, 184, 0.18);
  color: #475569;
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

.trend-main-empty-state {
  min-height: 240px;
  padding: 22px 18px;
}

@media (max-width: 720px) {
  .trend-workspace-panel.content-shell-panel {
    display: grid;
    grid-template-columns: minmax(0, 0.94fr) minmax(0, 1.06fr);
    align-items: center;
    gap: 10px 8px;
    padding: 0;
    border: 0;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
  }

  .trend-workspace-panel.content-shell-panel :deep(.el-loading-mask) {
    border-radius: 16px;
  }

  .panel-header.content-panel-header,
  .trend-selection-summary,
  .trend-single-source-tip,
  .trend-compare-tip,
  .trend-mobile-decision-grid {
    display: none;
  }

.trend-workspace-panel {
  position: relative;
}

.trend-stale-data-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: 14px;
  background: rgba(239, 246, 255, 0.86);
  color: #1e3a8a;
  font-size: 13px;
}

.trend-stale-data-banner strong {
  white-space: nowrap;
}

.trend-stale-data-banner span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trend-toolbar {
    display: grid;
    gap: 0;
    grid-column: 1;
    margin-bottom: 0;
    padding: 12px;
    border-radius: 16px;
  }

  .trend-picker-inline {
    display: grid;
    gap: 0;
  }

  .trend-picker-inline > span {
    display: none;
  }

  .trend-picker-inline :deep(.el-select__wrapper) {
    min-height: 34px;
    border-radius: 999px;
    box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.18) inset;
  }

  .trend-native-select {
    width: 100%;
    min-width: 0;
    min-height: 38px;
    padding: 0 32px 0 12px;
    border: 1px solid rgba(203, 213, 225, 0.82);
    border-radius: 12px;
    outline: 0;
    background: #ffffff;
    color: #0f172a;
    font: inherit;
    font-size: 12px;
    font-weight: 800;
  }

  .trend-product-native-select {
    text-overflow: ellipsis;
  }

  .trend-toolbar-count {
    display: none;
  }

  .trend-mobile-current-product {
    display: grid;
    gap: 4px;
    padding: 10px 12px;
    border: 1px solid rgba(203, 213, 225, 0.72);
    border-radius: 14px;
    background: #fff;
  }

  .trend-mobile-current-product span,
  .trend-mobile-current-product small {
    color: #64748b;
    font-size: 11px;
  }

  .trend-mobile-current-product strong {
    min-width: 0;
    color: #0f172a;
    font-size: 15px;
    line-height: 1.35;
    overflow-wrap: anywhere;
  }

  .trend-mobile-mode-switch {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    grid-column: 2;
    align-self: center;
    margin-bottom: 0;
  }

  .trend-content-shell,
  .trend-empty-workbench {
    grid-column: 1 / -1;
    align-self: stretch;
  }

  .trend-main-empty-state,
  .trend-pending-state {
    grid-column: 1 / -1;
  }

  .trend-mobile-mode-switch button {
    min-height: 42px;
    border: 1px solid rgba(203, 213, 225, 0.82);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.98);
    color: #475569;
    font: inherit;
    font-size: 12px;
    font-weight: 800;
    touch-action: manipulation;
    transition: background .16s ease, color .16s ease, transform .16s ease;
  }

  .trend-mobile-mode-switch button:active,
  .trend-empty-action:active,
  .trend-empty-product-button:active,
  .trend-chart-mobile-buttons button:active {
    transform: translateY(1px) scale(.99);
  }

  .trend-mobile-mode-switch button.active {
    border-color: transparent;
    background: rgba(37, 99, 235, 0.12);
    color: #2563eb;
    box-shadow: none;
  }

  .trend-mobile-detail-hero {
    padding: 14px 14px 12px;
    border: 1px solid rgba(203, 213, 225, 0.72);
    border-radius: 18px;
    background:
      radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 34%),
      linear-gradient(160deg, #f8fbff 0%, #ffffff 52%, #f8fafc 100%);
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
  }

  .trend-mobile-detail-head h3 {
    font-size: 20px;
    line-height: 1.16;
  }

  .trend-mobile-hero-chip {
    min-height: 32px;
    padding: 0 12px;
    border-radius: 999px;
    border: 1px solid rgba(203, 213, 225, 0.82);
    background: rgba(255, 255, 255, 0.92);
    color: #475569;
    font-size: 11px;
    font-weight: 800;
    display: inline-flex;
    align-items: center;
  }

  .trend-mobile-hero-price strong {
    font-size: 28px;
  }

  .trend-mobile-overview {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .trend-mobile-pill {
    display: grid;
    gap: 4px;
    padding: 10px 11px;
    border: 1px solid rgba(226, 232, 240, 0.92);
    border-radius: 14px;
    background: #ffffff;
  }

  .trend-mobile-pill span {
    color: #64748b;
    font-size: 10px;
    font-weight: 700;
  }

  .trend-mobile-pill strong {
    color: #0f172a;
    font-size: 15px;
    line-height: 1.2;
  }

  .trend-mobile-pill small {
    color: #64748b;
    font-size: 11px;
    line-height: 1.35;
  }

  .trend-mobile-chart-title {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 8px;
  }

  .trend-mobile-chart-title strong {
    color: #112033;
    font-size: 15px;
    line-height: 1.2;
  }

  .trend-mobile-chart-title span {
    color: #63738c;
    font-size: 11px;
  }

  .trend-mobile-svg-chart {
    display: block;
    width: 100%;
    height: 164px;
    border: 1px solid rgba(226, 232, 240, 0.92);
    border-radius: 15px;
    background: rgba(255, 255, 255, 0.9);
  }

  .trend-mobile-svg-chart line {
    stroke: rgba(203, 213, 225, 0.84);
    stroke-width: 1;
  }

  .trend-mobile-svg-chart polyline {
    fill: none;
    stroke-width: 2.6;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .trend-mobile-svg-chart .line-blue {
    stroke: #2563eb;
  }

  .trend-mobile-svg-chart .line-green {
    stroke: #16a34a;
  }

  .trend-mobile-svg-chart circle.line-blue {
    fill: #2563eb;
  }

  .trend-mobile-svg-chart circle.line-green {
    fill: #16a34a;
  }

  .trend-chart-shell,
  .trend-mobile-market-board {
    padding: 12px;
    border: 1px solid rgba(226, 232, 240, 0.95);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.98);
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
  }

  .trend-empty-workbench {
    min-height: 0;
    padding: 14px;
    border-radius: 18px;
    border-color: rgba(203, 213, 225, 0.72);
    background:
      linear-gradient(145deg, rgba(248, 251, 255, 0.94), rgba(255, 255, 255, 0.98)),
      linear-gradient(135deg, rgba(37, 99, 235, 0.04), transparent);
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
  }

  .trend-empty-product-list-mobile .trend-empty-product-button {
    min-height: 44px;
    border-radius: 12px;
    padding: 8px 10px;
  }

  .trend-empty-refresh-row .trend-empty-action {
    min-height: 44px;
    touch-action: manipulation;
  }

  .trend-empty-next-actions button {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 2px;
    min-height: 52px;
    padding: 9px 11px;
    border: 1px solid rgba(203, 213, 225, 0.82);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.96);
    color: #112033;
    font: inherit;
    text-align: left;
    cursor: pointer;
  }

  .trend-empty-next-actions button:active,
  .trend-empty-next-actions button:focus-visible {
    outline: none;
    border-color: rgba(37, 99, 235, 0.24);
    background: #eff6ff;
  }

  .trend-chart-mobile-nav {
    gap: 8px;
    margin-top: 8px;
  }

  .trend-chart-mobile-buttons button {
    min-height: 42px;
    border: 1px solid rgba(203, 213, 225, 0.82);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.98);
    color: #2563eb;
    font: inherit;
    font-size: 12px;
    font-weight: 800;
    touch-action: manipulation;
  }

  .trend-chart-mobile-buttons button:disabled {
    color: #94a3b8;
  }

  .trend-mobile-market-card {
    padding: 10px 12px;
    border-radius: 14px;
    border: 1px solid rgba(226, 232, 240, 0.92);
    background: #ffffff;
  }

  .trend-main-grid {
    gap: 10px;
  }

  .trend-mobile-decision-grid {
    grid-template-columns: 1fr;
  }

  .trend-main-empty-state {
    min-height: 0;
    padding: 14px;
    border-radius: 16px;
  }

  .trend-empty-workbench-copy strong {
    font-size: 16px;
  }

  .trend-main-empty-copy {
    display: grid;
    gap: 6px;
  }

  .trend-main-empty-state {
    min-height: 148px;
  }

  .trend-empty-product-list-mobile {
    display: grid;
    gap: 8px;
    margin-top: 2px;
  }

  .trend-empty-product-list-mobile > span {
    color: #63738c;
    font-size: 11px;
  }

  .trend-empty-next-actions {
    display: grid;
    gap: 8px;
    margin-top: 4px;
  }

  .trend-empty-next-actions > span {
    color: #63738c;
    font-size: 11px;
    font-weight: 700;
  }

  .trend-empty-next-actions strong {
    font-size: 13px;
    line-height: 1.25;
  }

  .trend-empty-next-actions small {
    color: #63738c;
    font-size: 11px;
    line-height: 1.35;
  }

  .trend-list-shell.compact {
    margin-top: 6px;
  }

  .trend-list-head strong {
    font-size: 14px;
  }

  .trend-row {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 8px;
    padding: 10px 0;
  }

  .trend-row .trend-time {
    display: none;
  }

  .trend-row strong {
    font-size: 13px;
  }

  .trend-price {
    font-size: 14px;
  }

}
</style>
