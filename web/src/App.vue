<template>
  <section v-if="isMobileViewport && viewMode === 'landing'" class="app-shell market-mobile-home" data-testid="sales-landing-view">
    <section class="panel market-mobile-home-hero">
      <div class="market-mobile-home-topline">
        <div>
          <p class="market-mobile-kicker">本地食材行情</p>
          <h1>本地市场采购小程序</h1>
        </div>
        <span class="market-mobile-city-pill">{{ selectedLocationLabel }}</span>
      </div>
      <p class="market-mobile-hero-copy">
        参考莲菜商城这类本地食材采购小程序，把本地市场、明确分类和单品行情承接压缩到手机一屏内。
      </p>
      <div class="market-mobile-search-row">
        <el-input
          v-model="filters.keyword"
          type="search"
          inputmode="search"
          enterkeyhint="search"
          aria-label="搜索食材关键词"
          placeholder="搜索菜品、干调或市场"
          clearable
        />
        <el-button type="primary" data-testid="enter-workspace-button" @click="enterWorkspace('summary')">进入行情</el-button>
      </div>
      <div class="market-mobile-stat-grid">
        <article v-for="item in homeHeroStats" :key="item.label" class="market-mobile-stat-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <small>{{ item.detail }}</small>
        </article>
      </div>
    </section>

    <section class="market-mobile-section">
      <div class="market-mobile-section-head">
        <div>
          <p class="market-mobile-kicker">常采分类</p>
          <h2>按采购类别进入</h2>
        </div>
        <span>{{ mobileQuickCategories.length - 1 }} 类</span>
      </div>
      <div class="market-mobile-chip-strip">
        <button
          v-for="item in mobileQuickCategories"
          :key="item.key"
          type="button"
          class="market-mobile-chip"
          @click="openCategoryMarket(item.key)"
        >
          <strong>{{ item.label }}</strong>
          <small>{{ item.count }} 款</small>
        </button>
      </div>
    </section>

    <section class="panel market-mobile-lead-card">
      <div class="market-mobile-section-head">
        <div>
          <p class="market-mobile-kicker">今日建议</p>
          <h2>{{ mobileLeadAction?.title || '先看本地低价与热门食材' }}</h2>
        </div>
        <span class="market-mobile-accent-pill">{{ mobileLeadAction?.badge || '本地优先' }}</span>
      </div>
      <p class="market-mobile-lead-copy">
        {{ mobileLeadAction?.summary || '优先进入本地行情列表，先按分类查看低价和价差，再进入单品详情确认走势。' }}
      </p>
      <div class="market-mobile-lead-actions">
        <el-button type="primary" @click="enterWorkspace('summary')">查看本地行情</el-button>
        <el-button plain @click="enterWorkspace('trend')">进入单品详情</el-button>
      </div>
    </section>

    <section class="market-mobile-section">
      <div class="market-mobile-section-head">
        <div>
          <p class="market-mobile-kicker">本地市场</p>
          <h2>报价来源</h2>
        </div>
        <span>{{ mobileSourceMarketCards.length }} 个市场</span>
      </div>
      <div class="market-mobile-source-grid">
        <article v-for="item in mobileSourceMarketCards" :key="item.title" class="market-mobile-source-card">
          <div class="market-mobile-source-head">
            <strong>{{ item.title }}</strong>
            <span>{{ item.status }}</span>
          </div>
          <p>{{ item.detail }}</p>
          <small>{{ item.meta }}</small>
        </article>
      </div>
    </section>

    <section class="market-mobile-section">
      <div class="market-mobile-section-head">
        <div>
          <p class="market-mobile-kicker">热门行情</p>
          <h2>直接看单品</h2>
        </div>
      </div>
      <div class="market-mobile-product-feed">
        <button
          v-for="item in mobileSpotlightRows"
          :key="item.identityKey"
          type="button"
          class="market-mobile-product-card"
          @click="openProductDetail(item.identityKey)"
        >
          <div class="market-mobile-product-top">
            <span>{{ item.category }}</span>
            <small>{{ item.market }}</small>
          </div>
          <strong>{{ item.title }}</strong>
          <div class="market-mobile-product-price">
            <b>{{ item.price }}</b>
            <small>{{ item.unit }}</small>
          </div>
          <div class="market-mobile-product-meta">
            <span>最低价 {{ item.lowest }}</span>
            <span>{{ item.spread }}</span>
          </div>
        </button>
      </div>
    </section>
  </section>

  <div v-else-if="isMobileViewport" class="app-shell market-mobile-shell">
    <header class="panel market-mobile-shell-head">
      <button type="button" class="market-mobile-back-button" @click="goToLanding()">首页</button>
      <div class="market-mobile-shell-copy">
        <p class="market-mobile-kicker">本地行情工作区</p>
        <h1>{{ mobileTabMeta.title }}</h1>
        <p>{{ mobileTabMeta.description }}</p>
      </div>
      <span class="market-mobile-city-pill">{{ selectedLocationLabel }}</span>
    </header>

    <div class="market-mobile-tab-strip">
      <button
        type="button"
        class="market-mobile-tab-button"
        :class="{ active: mobileActiveTab === 'summary' }"
        @click="enterWorkspace('summary')"
      >
        行情列表
      </button>
      <button
        type="button"
        class="market-mobile-tab-button"
        :class="{ active: mobileActiveTab === 'trend' }"
        @click="enterWorkspace('trend')"
      >
        单品详情
      </button>
      <button
        type="button"
        class="market-mobile-tab-button"
        :class="{ active: mobileActiveTab === 'supplier' }"
        @click="enterWorkspace('supplier')"
      >
        供应商后台
      </button>
    </div>

    <div class="market-mobile-context-row">
      <div class="market-mobile-context-pill">
        <span>当前地区</span>
        <strong>{{ selectedLocationLabel }}</strong>
      </div>
      <div class="market-mobile-context-pill">
        <span>当前分类</span>
        <strong>{{ activeMarketCategory }}</strong>
      </div>
      <div class="market-mobile-context-pill" v-if="selectedProductLabel">
        <span>当前商品</span>
        <strong>{{ selectedProductLabel }}</strong>
      </div>
    </div>

    <section v-if="showBlockingError" class="active-strip compact source-warning-strip">
      <div>
        <h2>真实接口当前不可用</h2>
        <p class="active-strip-copy">请先确认 API 已启动，再刷新页面查看真实抓取结果。</p>
      </div>
      <div class="source-warning-text">{{ pageError || dataSourceState.lastError || '接口暂不可用' }}</div>
    </section>

    <main class="market-mobile-shell-content">
      <MarketSummaryPanel
        v-if="mobileActiveTab === 'summary'"
        :rows="marketRows"
        :source-coverage-rows="sourceCoverageRows"
        :keyword="filters.keyword"
        :location-label="selectedLocationLabel"
        :loading="summaryLoading"
        :active-category="activeMarketCategory"
        @keyword-change="filters.keyword = $event"
        @select-product="handleSelectProduct"
        @update:active-category="activeMarketCategory = $event"
      />

      <ProductTrendPanel
        v-else-if="mobileActiveTab === 'trend'"
        :product-options="productOptions"
        :selected-identity-key="selectedIdentityKey"
        :product-summary="productSummary"
        :trend-rows="trendRows"
        :site-options="trendSiteOptions"
        :loading="trendLoading"
        :trend-mode="trendMode"
        :selected-site-name="selectedSiteName"
        @select-product="handleSelectProduct"
        @update:trend-mode="trendMode = $event"
        @update:selected-site-name="selectedSiteName = $event"
        @refresh-trend="reloadTrend"
      />

      <SupplierAdminPanel
        v-else
        :product-options="productOptions"
        :selected-identity-key="selectedIdentityKey"
        :selected-product-label="selectedProductLabel"
        :mobile="true"
        @select-product="handleSelectProduct"
      />
    </main>

    <nav class="market-mobile-bottom-nav">
      <button type="button" class="market-mobile-bottom-item" @click="goToLanding()">
        <span>首页</span>
        <strong>频道</strong>
      </button>
      <button
        type="button"
        class="market-mobile-bottom-item"
        :class="{ active: mobileActiveTab === 'summary' }"
        @click="enterWorkspace('summary')"
      >
        <span>列表</span>
        <strong>行情</strong>
      </button>
      <button
        type="button"
        class="market-mobile-bottom-item"
        :class="{ active: mobileActiveTab === 'trend' }"
        @click="enterWorkspace('trend')"
      >
        <span>详情</span>
        <strong>单品</strong>
      </button>
      <button
        type="button"
        class="market-mobile-bottom-item"
        :class="{ active: mobileActiveTab === 'supplier' }"
        @click="enterWorkspace('supplier')"
      >
        <span>后台</span>
        <strong>供应商</strong>
      </button>
    </nav>
  </div>

  <section v-else-if="viewMode === 'landing'" class="app-shell sales-home-shell" data-testid="sales-landing-view">
    <section class="panel sales-home-hero">
      <div class="sales-home-copy">
        <p class="panel-kicker">{{ demoHero.eyebrow }}</p>
        <h1 class="sales-home-title">{{ demoHero.title }}</h1>
        <p class="sales-home-subcopy">{{ demoHero.description }}</p>
        <div class="sales-home-actions">
          <el-button type="primary" data-testid="enter-workspace-button" @click="enterWorkspace()">
            {{ demoHero.primaryCta }}
          </el-button>
          <el-button @click="enterWorkspace('summary')">查看真实行情</el-button>
        </div>
      </div>
      <div class="sales-home-command">
        <div class="sales-home-command-head">
          <div>
            <p class="panel-kicker">今天先判断什么</p>
            <h2>老板先看结论，再看明细</h2>
          </div>
          <span>{{ filters.city || filters.province || '全国市场' }}</span>
        </div>
        <div class="sales-home-command-grid">
          <article v-for="item in homeHeroStats" :key="item.label" class="sales-home-command-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.detail }}</small>
          </article>
        </div>
      </div>
    </section>

    <section class="sales-home-layout">
      <section class="panel sales-decision-panel sales-priority-panel">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">现在该看</p>
            <h2>今日优先事项</h2>
          </div>
          <span class="workspace-mode-pill">{{ homePriorityItems.length }} 项重点</span>
        </div>
        <div class="decision-list">
          <article
            v-for="item in homePriorityItems"
            :key="`${item.title}-${item.badge}`"
            class="decision-item"
            :class="[`tone-${item.tone}`]"
          >
            <div class="decision-item-head">
              <strong>{{ item.title }}</strong>
              <span>{{ item.badge }}</span>
            </div>
            <p>{{ item.summary }}</p>
            <small>{{ item.meta }}</small>
          </article>
        </div>
      </section>

      <section class="panel sales-decision-panel sales-reason-panel">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">为什么重要</p>
            <h2>今天影响经营的原因</h2>
          </div>
        </div>
        <div class="decision-metric-grid">
          <article v-for="item in bossSummary.kpis.slice(0, 4)" :key="item.label" class="decision-metric-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.detail || bossSummary.riskNote }}</small>
          </article>
        </div>
        <p class="decision-panel-note">{{ bossSummary.noteSummary }}</p>
        <div class="reason-highlight-list">
          <article v-for="item in bossSummary.focusItems.slice(0, 3)" :key="item.title" class="reason-highlight-item">
            <strong>{{ item.title }}</strong>
            <p>{{ item.summary }}</p>
            <small>{{ item.owner }}</small>
          </article>
        </div>
      </section>

      <section class="panel sales-decision-panel sales-action-panel">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">下一步</p>
            <h2>建议动作</h2>
          </div>
        </div>
        <div class="action-list">
          <article v-for="item in homeActionItems" :key="`${item.title}-${item.owner}`" class="action-item">
            <div class="decision-item-head">
              <strong>{{ item.title }}</strong>
              <span>{{ item.owner }}</span>
            </div>
            <p>{{ item.detail }}</p>
            <small>{{ item.meta }}</small>
          </article>
        </div>
      </section>

      <section class="panel sales-decision-panel sales-entry-panel">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">关键入口</p>
            <h2>直接进入工作区</h2>
          </div>
        </div>
        <div class="entry-grid">
          <button
            v-for="item in homeEntryCards"
            :key="item.key"
            type="button"
            class="entry-card"
            @click="enterWorkspace(item.key)"
          >
            <span>{{ item.kicker }}</span>
            <strong>{{ item.title }}</strong>
            <small>{{ item.detail }}</small>
          </button>
        </div>
      </section>

      <section class="panel sales-decision-panel sales-market-panel">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">真实快照</p>
            <h2>市场速览</h2>
          </div>
          <el-button text @click="enterWorkspace('summary')">进入汇总行情</el-button>
        </div>
        <div class="data-health-grid">
          <article v-for="item in homeDataHealth" :key="item.label" class="data-health-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.detail }}</small>
          </article>
        </div>
        <div class="market-watch-grid">
          <article v-for="item in homeMarketWatch" :key="item.title" class="market-watch-card">
            <div class="decision-item-head">
              <strong>{{ item.title }}</strong>
              <span>{{ item.coverage }}</span>
            </div>
            <div class="market-watch-metrics">
              <div>
                <span>最低</span>
                <strong>{{ item.lowest }}</strong>
              </div>
              <div>
                <span>最高</span>
                <strong>{{ item.highest }}</strong>
              </div>
            </div>
            <small>{{ item.meta }}</small>
          </article>
        </div>
      </section>
    </section>
  </section>

  <div v-else class="app-shell dashboard-shell">
    <aside class="control-rail">
      <section class="rail-card brand-card">
        <div class="brand-lockup">
          <div v-if="!isMobileViewport" class="brand-mark">BT</div>
          <div class="brand-stack">
            <p class="eyebrow">BATTEL 工作台</p>
            <h1 class="page-title">市场价格工作台</h1>
            <p class="header-copy">真实多市场报价、趋势和采购判断。</p>
          </div>
        </div>
        <div v-if="!isMobileViewport" class="brand-notes">
          <span>主表优先</span>
          <span>真实报价</span>
          <span>多市场</span>
        </div>
      </section>

      <section class="rail-card rail-nav-card">
        <div class="rail-section-head">
          <div>
            <p class="rail-section-kicker">工作区</p>
            <h2>工作区</h2>
          </div>
        </div>
        <div class="rail-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            type="button"
            class="rail-tab"
            :data-tab="tab.key"
            :class="{ active: activeTab === tab.key }"
            :aria-label="`切换到${tab.label}`"
            :aria-pressed="activeTab === tab.key"
            @click="activateTab(tab.key)"
          >
            <span v-if="!isMobileViewport" class="rail-tab-icon">{{ tab.code }}</span>
            <span class="rail-tab-copy">
              <strong>{{ tab.label }}</strong>
              <small v-if="!isMobileViewport">{{ tabHints[tab.key] }}</small>
            </span>
          </button>
        </div>
      </section>

      <section class="rail-card filter-card">
        <div class="rail-section-head">
          <div>
            <p class="rail-section-kicker">筛选</p>
            <h2>筛选条件</h2>
          </div>
          <div class="rail-action-group">
            <el-button
              type="primary"
              :loading="crawlActionLoading || crawlStatus?.is_running"
              @click="handleManualCrawl"
            >
              获取最新数据
            </el-button>
            <el-button @click="reloadAll">刷新</el-button>
          </div>
        </div>
        <div class="rail-filter-stack">
          <el-select v-model="filters.province" aria-label="省份筛选" clearable filterable placeholder="省份筛选">
            <el-option v-for="item in provinces" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select
            :key="filters.province || 'all-cities'"
            v-model="filters.city"
            aria-label="城市筛选"
            clearable
            filterable
            :loading="locationLoading"
            :placeholder="filters.province ? '选择该省城市' : '城市优先'"
            @visible-change="handleCityDropdownVisible"
          >
            <el-option v-for="item in filteredCities" :key="item" :label="item" :value="item" />
          </el-select>
          <el-input
            v-model="filters.keyword"
            type="search"
            inputmode="search"
            enterkeyhint="search"
            aria-label="搜索商品关键词"
            placeholder="搜索商品关键词"
            clearable
          />
        </div>
        <div v-if="!isMobileViewport" class="rail-context-inline">
          <div class="rail-inline-pill">
            <span>地区</span>
            <strong>{{ filters.city || filters.province || '全部市场' }}</strong>
          </div>
          <div class="rail-inline-pill">
            <span>商品</span>
            <strong>{{ selectedProductLabel || '未选择' }}</strong>
          </div>
          <div class="rail-inline-pill">
            <span>主表</span>
            <strong>{{ marketRows.length }} 条</strong>
          </div>
        </div>
        <div class="crawl-ops-card">
          <div class="crawl-ops-head">
            <div>
              <p class="rail-section-kicker">抓取</p>
              <h3>数据获取</h3>
            </div>
            <el-switch
              v-model="dailyScheduleEnabled"
              :loading="scheduleActionLoading"
              inline-prompt
              active-text="开"
              inactive-text="关"
              @change="handleScheduleToggle"
            />
          </div>
          <div class="crawl-progress-wrap">
            <div class="crawl-progress-head">
              <span>{{ crawlProgressLabel }}</span>
              <strong>{{ crawlProgressPercent }}%</strong>
            </div>
            <el-progress
              :percentage="crawlProgressPercent"
              :stroke-width="10"
              :show-text="false"
              :status="crawlStatus?.is_running ? undefined : 'success'"
            />
            <p v-if="crawlStatus?.is_running && crawlStatus?.current_source_name" class="crawl-progress-note">
              正在获取：{{ crawlStatus.current_source_name }}
            </p>
            <p v-if="crawlStatus?.is_running && crawlStatus?.current_source_detail" class="crawl-progress-note secondary">
              {{ crawlStatus.current_source_detail }}
            </p>
          </div>
          <div v-if="isMobileViewport" class="crawl-compact-inline">
            <div class="crawl-mini-stat">
              <span>自动获取</span>
              <strong>{{ dailyScheduleEnabled ? '每日开启' : '已关闭' }}</strong>
            </div>
            <div class="crawl-mini-stat">
              <span>最近结果</span>
              <strong>{{ crawlResultLabel }}</strong>
            </div>
          </div>
          <div v-else class="crawl-ops-grid">
            <div class="crawl-mini-stat">
              <span>自动获取</span>
              <strong>{{ dailyScheduleEnabled ? '每日开启' : '已关闭' }}</strong>
            </div>
            <div class="crawl-mini-stat">
              <span>上次完成</span>
              <strong>{{ crawlLastFinishedLabel }}</strong>
            </div>
            <div class="crawl-mini-stat">
              <span>下次计划</span>
              <strong>{{ crawlNextRunLabel }}</strong>
            </div>
            <div class="crawl-mini-stat">
              <span>最近结果</span>
              <strong>{{ crawlResultLabel }}</strong>
            </div>
          </div>
          <p v-if="crawlStatus?.last_error" class="crawl-error-text">{{ crawlStatus.last_error }}</p>
        </div>
      </section>
    </aside>

    <main class="workspace-shell">
      <section v-if="!isMobileViewport" class="workspace-topbar">
        <div class="workspace-topbar-copy">
          <div class="workspace-heading-row">
            <p class="workspace-kicker">{{ activeTabMeta.kicker }}</p>
          </div>
          <h2>{{ activeTabMeta.title }}</h2>
          <p class="workspace-subcopy">{{ activeTabMeta.description }}</p>
        </div>
        <div class="workspace-topbar-chips">
          <div class="workspace-mini-chip">
            <span>地区</span>
            <strong>{{ filters.city || filters.province || '全部市场' }}</strong>
          </div>
          <div class="workspace-mini-chip">
            <span>{{ activeTabMeta.metricLabel }}</span>
            <strong>{{ activeTabMeta.metricValue }}</strong>
          </div>
          <div v-if="selectedProductLabel" class="workspace-mini-chip accent-chip">
            <span>当前商品</span>
            <strong>{{ selectedProductLabel }}</strong>
          </div>
          <el-button plain @click="goToLanding">返回销售首页</el-button>
        </div>
      </section>

      <section v-if="showBlockingError" class="active-strip compact source-warning-strip">
        <div>
          <h2>真实接口当前不可用</h2>
          <p class="active-strip-copy">请先确认 API 已启动，再刷新页面查看真实抓取结果。</p>
        </div>
        <div class="source-warning-text">{{ pageError || dataSourceState.lastError || '接口暂不可用' }}</div>
      </section>

      <main class="content-area">
        <MarketSummaryPanel
          v-if="activeTab === 'summary'"
          :rows="marketRows"
          :source-coverage-rows="sourceCoverageRows"
          :keyword="filters.keyword"
          :location-label="selectedLocationLabel"
          :loading="summaryLoading"
          @keyword-change="filters.keyword = $event"
          @select-product="handleSelectProduct"
        />

        <section v-if="activeTab !== 'summary'" class="detail-workspace">
          <section v-if="activeTab === 'signals'" class="signals-workspace" data-testid="signals-workspace">
            <BossCockpitSummary
              :risk-label="bossSummary.riskLabel"
              :risk-tone="bossSummary.riskTone"
              :risk-note="bossSummary.riskNote"
              :kpis="bossSummary.kpis"
              :focus-items="bossSummary.focusItems"
              :note-summary="bossSummary.noteSummary"
              :decision-points="bossSummary.decisionPoints"
            />
            <BusinessSignalOverview
              :window-label="signalPanel.windowLabel"
              :review-label="signalPanel.reviewLabel"
              :signals="signalPanel.signals"
              :alerts="signalPanel.alerts"
            />
          </section>

          <ProductTrendPanel
            v-if="activeTab === 'trend'"
            :product-options="productOptions"
            :selected-identity-key="selectedIdentityKey"
            :product-summary="productSummary"
            :trend-rows="trendRows"
            :site-options="trendSiteOptions"
            :loading="trendLoading"
            :trend-mode="trendMode"
            :selected-site-name="selectedSiteName"
            @select-product="handleSelectProduct"
            @update:trend-mode="trendMode = $event"
            @update:selected-site-name="selectedSiteName = $event"
            @refresh-trend="reloadTrend"
          />

          <MenuPlanPanel
            v-if="activeTab === 'menu'"
            v-model:menu-text="menuForm.menuText"
            v-model:tables="menuForm.tables"
            v-model:diners="menuForm.diners"
            v-model:preferred-location="menuForm.preferredLocation"
            :location-candidates="menuLocationCandidates"
            :ingredient-rows="ingredientRows"
            :plan-rows="planRows"
            :parsed-menu-count="parsedMenuCount"
            :matched-plan-count="matchedPlanCount"
            :pending-plan-count="pendingPlanCount"
            :total-cost-label="menuTotalCostLabel"
            :loading="menuPlanLoading"
            @submit="submitMenuPlan"
            @import-lines="appendMenuLines"
          />

          <SupplierAdminPanel
            v-if="activeTab === 'supplier'"
            :product-options="productOptions"
            :selected-identity-key="selectedIdentityKey"
            :selected-product-label="selectedProductLabel"
            :mobile="false"
            @select-product="handleSelectProduct"
          />
        </section>
      </main>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import {
  dataSourceState,
  fetchCrawlStatus,
  fetchLocationOptions,
  fetchMarketSummary,
  fetchProcurementRecommendation,
  fetchProductOptions,
  fetchProductSummary,
  fetchProductTrend,
  fetchSalesDemoContent,
  fetchSignalsOverview,
  fetchSourceCoverage,
  generateMenuPlan,
  triggerCrawlRun,
  updateCrawlSchedule,
} from './api'
import type {
  CrawlStatusItem,
  MarketSummaryItem,
  MenuPlanRow,
  ProcurementRecommendationItem,
  ProductOptionItem,
  ProductTrendRow,
  SalesDemoContentResponse,
  SignalOverviewResponse,
  SourceCoverageItem,
} from './types'
import { useViewport } from './composables/useViewport'
import { buildMarketCategoryTabs, resolveMarketCategory } from './utils/marketCategories'

const BossCockpitSummary = defineAsyncComponent(() => import('./components/BossCockpitSummary.vue'))
const BusinessSignalOverview = defineAsyncComponent(() => import('./components/BusinessSignalOverview.vue'))
const MarketSummaryPanel = defineAsyncComponent(() => import('./components/MarketSummaryPanel.vue'))
const ProductTrendPanel = defineAsyncComponent(() => import('./components/ProductTrendPanel.vue'))
const MenuPlanPanel = defineAsyncComponent(() => import('./components/MenuPlanPanel.vue'))
const SupplierAdminPanel = defineAsyncComponent(() => import('./components/SupplierAdminPanel.vue'))
const { isMobileViewport } = useViewport()
const searchParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams()
const initialTab = searchParams.get('tab')
const initialMode = searchParams.get('mode')

const tabs = [
  { key: 'signals', label: '老板驾驶舱', code: 'SIG' },
  { key: 'summary', label: '汇总行情', code: 'SUM' },
  { key: 'trend', label: '单品趋势', code: 'TRD' },
  { key: 'menu', label: '菜单采购', code: 'BUY' },
  { key: 'supplier', label: '供应商后台', code: 'SUP' },
] as const
const tabHints = {
  signals: '销售演示页',
  summary: '查看汇总报价',
  trend: '查看价格走势',
  menu: '生成采购建议',
  supplier: '维护供应商与录价',
} as const
const defaultTab = tabs.some((item) => item.key === initialTab) ? (initialTab as (typeof tabs)[number]['key']) : 'signals'
const viewMode = ref<'landing' | 'workspace'>(initialMode === 'workspace' || Boolean(initialTab) ? 'workspace' : 'landing')
const activeTab = ref<(typeof tabs)[number]['key']>(defaultTab)
const provinces = ref<string[]>([])
const cities = ref<string[]>([])
const provinceCityMap = ref<Record<string, string[]>>({})
const marketRows = ref<MarketSummaryItem[]>([])
const sourceCoverageRows = ref<SourceCoverageItem[]>([])
const productOptions = ref<ProductOptionItem[]>([])
const selectedIdentityKey = ref('')
const selectedSiteName = ref('')
const selectedProductFallbackLabel = ref('')
const productSummary = ref<Record<string, any> | null>(null)
const trendRows = ref<ProductTrendRow[]>([])
const trendSiteOptions = ref<string[]>([])
const trendLoading = ref(false)
const trendMode = ref<'cross_market' | 'single_market'>('cross_market')
const ingredientRows = ref<Record<string, any>[]>([])
const planRows = ref<MenuPlanRow[]>([])
const procurementRecommendations = ref<ProcurementRecommendationItem[]>([])
const menuPlanLoading = ref(false)
const crawlStatus = ref<CrawlStatusItem | null>(null)
const signalOverview = ref<SignalOverviewResponse | null>(null)
const demoContent = ref<SalesDemoContentResponse | null>(null)
const pageError = ref('')
const summaryLoading = ref(false)
const locationLoading = ref(false)
const coverageLoading = ref(false)
const productOptionsLoading = ref(false)
const crawlActionLoading = ref(false)
const scheduleActionLoading = ref(false)
const dailyScheduleEnabled = ref(false)
const productOptionsContextKey = ref('')
let crawlStatusTimer: number | undefined
let productOptionsPromise: Promise<void> | null = null
let trendRequestSequence = 0
let trendPrefetchContextKey = ''
const trendPrefetchPromises = new Map<string, Promise<void>>()
const activeMarketCategory = ref('全部')
const filters = reactive({
  province: '',
  city: '',
  keyword: '',
})
const menuForm = reactive({
  menuText: '',
  tables: 10,
  diners: 100,
  preferredLocation: '',
})

const parsedMenuCount = computed(() => menuForm.menuText.split('\n').map((item) => item.trim()).filter(Boolean).length)
const matchedPlanCount = computed(() => planRows.value.filter((item) => item.price_status === '已匹配报价').length)
const pendingPlanCount = computed(() => planRows.value.filter((item) => item.price_status !== '已匹配报价').length)
const menuTotalCostLabel = computed(() => {
  const total = planRows.value.reduce((sum, item) => sum + (Number(item.estimated_cost) || 0), 0)
  return total > 0 ? `${total.toFixed(2)} 元` : '-'
})
const filteredCities = computed(() => {
  if (!filters.province) {
    return cities.value
  }
  if (!Object.keys(provinceCityMap.value).length) {
    return []
  }
  const provinceCities = provinceCityMap.value[filters.province] || []
  return provinceCities
})
const menuLocationCandidates = computed(() => {
  const options = ['当前位置']
  for (const item of filteredCities.value) {
    if (item && !options.includes(item)) {
      options.push(item)
    }
  }
  for (const item of provinces.value) {
    if (item && !options.includes(item)) {
      options.push(item)
    }
  }
  return options
})
const lowestPriceSignal = computed(() => {
  const rowsWithLowestPrice = marketRows.value.filter((item) => item.lowest_price != null && !Number.isNaN(Number(item.lowest_price)))
  if (!rowsWithLowestPrice.length) {
    return '暂无信号'
  }
  const bestRow = rowsWithLowestPrice.reduce((currentBest, row) => {
    if (!currentBest) {
      return row
    }
    return Number(row.lowest_price) < Number(currentBest.lowest_price) ? row : currentBest
  }, rowsWithLowestPrice[0])
  return `${bestRow.product_name} · ${Number(bestRow.lowest_price).toFixed(2)}`
})
const crawlResultLabel = computed(() => {
  if (!crawlStatus.value) return '暂无'
  if (crawlStatus.value.is_running) return '抓取中'
  const success = Number(crawlStatus.value.last_success_count || 0)
  const failed = Number(crawlStatus.value.last_failed_count || 0)
  if (!success && !failed) return '暂无'
  return `${success} 成功 / ${failed} 异常`
})
const crawlProgressPercent = computed(() => {
  if (!crawlStatus.value) return 0
  const reported = Number(crawlStatus.value.progress_percent || 0)
  return reported
})
const crawlProgressLabel = computed(() => {
  if (!crawlStatus.value) return '等待获取'
  const completed = Number(crawlStatus.value.completed_sources || 0)
  const total = Number(crawlStatus.value.last_total_sources || 0)
  const currentIndex = Number(crawlStatus.value.current_source_index || 0)
  if (crawlStatus.value.is_running) {
    if (total) {
      const activeIndex = Math.max(currentIndex, completed + 1)
      const sourceProgress = Math.round(Number(crawlStatus.value.current_source_progress || 0) * 100)
      return `正在获取第 ${activeIndex}/${total} 个报价源 · 当前源 ${sourceProgress}%`
    }
    return '准备抓取'
  }
  if (total) {
    return `最近一次完成 ${completed || total}/${total} 个报价源`
  }
  return '等待获取'
})
const crawlLastFinishedLabel = computed(() => formatBeijingDateTime(crawlStatus.value?.last_finished_at, '暂无', true))
const crawlNextRunLabel = computed(() => formatBeijingDateTime(crawlStatus.value?.next_run_at, '未安排', true))
const selectedProductLabel = computed(() => {
  const current = productOptions.value.find((item) => item.price_identity_key === selectedIdentityKey.value)
  return current?.price_identity_label ?? selectedProductFallbackLabel.value
})
const selectedLocationLabel = computed(() => filters.city || filters.province || '河南本地市场')
const mobileActiveTab = computed(() => {
  if (activeTab.value === 'trend') return 'trend'
  if (activeTab.value === 'supplier') return 'supplier'
  return 'summary'
})
const mobileTabMeta = computed(() => {
  if (mobileActiveTab.value === 'trend') {
    return {
      title: '单品详情',
      description: '先看当前价格区间，再判断跨市场还是单市场跟踪。',
    }
  }
  if (mobileActiveTab.value === 'supplier') {
    return {
      title: '供应商后台',
      description: '维护本地供应商，录入报价并同步到前台对比。',
    }
  }
  return {
    title: '本地行情列表',
    description: '按分类、地区和关键词查看本地食材行情。',
  }
})
const hasLiveSummary = computed(() => marketRows.value.length > 0)
const showBlockingError = computed(() => dataSourceState.mode === 'error' && !hasLiveSummary.value)
const activeTabMeta = computed(() => {
  if (activeTab.value === 'signals') {
    return {
      kicker: '老板驾驶舱',
      title: '经营信号与销售演示',
      description: '先讲今天该关注什么，再进入明细行情和采购动作。',
      metricLabel: '高优先信号',
      metricValue: `${signalOverview.value?.top_opportunities?.length || 0} 条`,
    }
  }
  if (activeTab.value === 'trend') {
    return {
      kicker: '价格走势',
      title: '单品趋势',
        description: '看同一商品在不同市场的价格变化。',
      metricLabel: '走势记录',
      metricValue: `${trendRows.value.length} 条`,
    }
  }
  if (activeTab.value === 'menu') {
    return {
      kicker: '菜单采购',
      title: '菜单采购',
        description: '拆菜单、比报价、生成采购建议。',
      metricLabel: '采购建议',
      metricValue: `${planRows.value.length} 条`,
    }
  }
  if (activeTab.value === 'supplier') {
    return {
      kicker: '供应商后台',
      title: '供应商与录价管理',
      description: '集中维护本地供应商资料、分类和人工录价入口。',
      metricLabel: '已选商品',
      metricValue: selectedProductLabel.value || '未选择',
    }
  }
  return {
    kicker: '汇总行情',
    title: '汇总行情',
    description: '按商品快速比较不同市场报价。',
    metricLabel: '汇总商品',
    metricValue: `${marketRows.value.length} 条`,
  }
})

const demoHero = computed(() => ({
  eyebrow: demoContent.value?.hero?.eyebrow || 'BATTEL SALE READY',
  title: demoContent.value?.hero?.title || '把价格工作台升级成可直接报价的经营决策产品。',
  description: demoContent.value?.hero?.description || '先让客户看懂今天的机会和风险，再让他看见报价与交付路径。',
  primaryCta: demoContent.value?.hero?.primary_cta || '进入老板驾驶舱',
}))

const bossSummary = computed(() => {
  const metrics = signalOverview.value?.overview_metrics || []
  const opportunities = signalOverview.value?.top_opportunities || []
  const risks = signalOverview.value?.top_risks || []
  const highRiskCount = risks.filter((item) => item.risk_score >= 70).length
  return {
    riskLabel: highRiskCount > 0 ? '可控偏紧' : '总体可控',
    riskTone: highRiskCount > 0 ? 'watch' : 'stable',
    riskNote: signalOverview.value?.headline || '当前建议先讲机会，再补风险说明',
    kpis: metrics.slice(0, 4).map((item, index) => ({
      label: item.label,
      value: item.value,
      detail: item.detail || '',
      emphasis: index === 0,
    })),
    focusItems: [...opportunities.slice(0, 2), ...risks.slice(0, 1)].map((item) => ({
      title: item.product_name,
      summary: item.reason_summary,
      owner: item.recommended_action,
    })),
    noteSummary: signalOverview.value?.headline || '当前先用老板视角解释价格变化，再带客户进入趋势明细。',
    decisionPoints: [
      {
        title: '今日动作',
        value: opportunities[0]?.recommended_action || '持续观察',
        detail: opportunities[0]?.product_name || '暂无重点商品',
      },
      {
        title: '风险重点',
        value: `${highRiskCount} 项`,
        detail: risks[0]?.product_name || '暂无高风险商品',
      },
      {
        title: '成交承接',
        value: '老板驾驶舱',
        detail: '先讲机会和风险，再进入趋势与采购动作',
      },
    ],
  }
})

const signalPanel = computed(() => ({
  windowLabel: signalOverview.value?.generated_at || '近 7 天',
  reviewLabel: '老板摘要 + 采购建议',
  signals: [...(signalOverview.value?.top_opportunities || []), ...(signalOverview.value?.top_risks || [])]
    .slice(0, 6)
    .map((item) => ({
      title: item.product_name,
      value: `${Math.round(item.timing_score)}/${Math.round(item.risk_score)}`,
      changeLabel: item.recommended_action,
      detail: item.reason_summary,
      trend: item.trend_label === '上涨' ? 'up' : item.trend_label === '下降' ? 'down' : 'flat',
      severity: item.signal_level === 'high' ? 'risk' : item.signal_level === 'medium' ? 'watch' : 'good',
    })),
  alerts: [
    ...(signalOverview.value?.recommended_actions || []).slice(0, 2).map((item) => ({
      title: item.title,
      detail: item.description,
      owner: item.action,
    })),
    ...procurementRecommendations.value.slice(0, 2).map((item) => ({
      title: item.ingredient_name || '采购建议',
      detail: item.reason_summary,
      owner: item.recommended_action,
    })),
  ].slice(0, 4),
}))

const homeHeroStats = computed(() => [
  {
    label: '老板结论',
    value: bossSummary.value.riskLabel,
    detail: bossSummary.value.riskNote,
  },
  {
    label: '当前最低价',
    value: lowestPriceSignal.value,
    detail: hasLiveSummary.value ? `${marketRows.value.length} 个商品已汇总` : '等待真实报价',
  },
  {
    label: '数据状态',
    value: crawlResultLabel.value,
    detail: crawlProgressLabel.value,
  },
])

const homePriorityItems = computed(() => {
  const opportunities = (signalOverview.value?.top_opportunities || []).slice(0, 2).map((item) => ({
    title: item.product_name,
    badge: item.recommended_action,
    summary: item.reason_summary,
    meta: item.recommended_market || item.recommended_site || '机会信号',
    tone: 'good',
  }))
  const risks = (signalOverview.value?.top_risks || []).slice(0, 1).map((item) => ({
    title: item.product_name,
    badge: '风险关注',
    summary: item.reason_summary,
    meta: item.recommended_market || item.recommended_site || '风险信号',
    tone: 'warn',
  }))
  const items = [...opportunities, ...risks]
  if (items.length) {
    return items
  }
  return [
    {
      title: '等待数据同步',
      badge: '先获取数据',
      summary: '当前还没有形成可执行的优先级，请先拉取最新市场报价。',
      meta: '进入工作区后可手动获取',
      tone: 'default',
    },
  ]
})

const homeActionItems = computed(() => {
  const signalActions = (signalOverview.value?.recommended_actions || []).slice(0, 2).map((item) => ({
    title: item.title,
    detail: item.description,
    owner: item.action,
    meta: item.confidence != null ? `置信度 ${Math.round(item.confidence)}%` : '建议纳入今日动作',
  }))
  const procurementActions = procurementRecommendations.value.slice(0, 2).map((item) => ({
    title: item.ingredient_name || '采购建议',
    detail: item.reason_summary,
    owner: item.recommended_action,
    meta: item.recommended_market || item.recommended_site || '采购判断',
  }))
  const items = [...signalActions, ...procurementActions]
  if (items.length) {
    return items
  }
  return [
    {
      title: '进入老板驾驶舱',
      detail: '先查看今日经营信号，再决定是否进入趋势和采购明细。',
      owner: '默认路径',
      meta: '首屏保留关键入口',
    },
  ]
})

const homeEntryCards = computed(() => [
  {
    key: 'signals',
    kicker: '经营信号',
    title: '老板驾驶舱',
    detail: `${signalOverview.value?.top_opportunities?.length || 0} 条机会，先看结论与动作`,
  },
  {
    key: 'summary',
    kicker: '真实报价',
    title: '汇总行情',
    detail: `${marketRows.value.length} 个商品主表，适合快速比价`,
  },
  {
    key: 'trend',
    kicker: '价格变化',
    title: '单品趋势',
    detail: selectedProductLabel.value || `${productOptions.value.length} 个商品可查看走势`,
  },
  {
    key: 'menu',
    kicker: '采购执行',
    title: '菜单采购',
    detail: `${procurementRecommendations.value.length || planRows.value.length} 条采购建议可复核`,
  },
])

const homeMarketWatch = computed(() => {
  const rows = marketRows.value.slice(0, 3).map((item) => ({
    title: item.product_name,
    coverage: `${item.site_count || 0} 个来源`,
    lowest: formatPriceMetric(item.lowest_price, item.price_unit_basis),
    highest: formatPriceMetric(item.highest_price, item.price_unit_basis),
    meta: item.lowest_price_site || item.region_label || '已接入真实报价',
  }))
  if (rows.length) {
    return rows
  }
  return [
    {
      title: '等待报价接入',
      coverage: '暂无来源',
      lowest: '-',
      highest: '-',
      meta: '获取最新数据后，这里会显示首批真实市场快照。',
    },
  ]
})

const homeDataHealth = computed(() => [
  {
    label: '已接入来源',
    value: `${sourceCoverageRows.value.length} 个`,
    detail: hasLiveSummary.value ? '来源覆盖已加载' : '等待主表同步',
  },
  {
    label: '最近完成',
    value: crawlLastFinishedLabel.value,
    detail: crawlResultLabel.value,
  },
  {
    label: '下次计划',
    value: dailyScheduleEnabled.value ? crawlNextRunLabel.value : '手动获取',
    detail: dailyScheduleEnabled.value ? '自动抓取已开启' : '当前按需刷新',
  },
])
const mobileQuickCategories = computed(() => buildMarketCategoryTabs(marketRows.value).slice(0, 6))
const mobileLeadAction = computed(() => homePriorityItems.value[0] || null)
const mobileSourceMarketCards = computed(() => {
  const rows = sourceCoverageRows.value.slice(0, 3).map((item) => ({
    title: item.configured_name || item.source_name || '未命名市场',
    status: item.status || '待同步',
    detail: item.market_scope || item.market_category || item.channel || '本地市场来源',
    meta: item.latest_capture || '暂无最近抓取',
  }))
  if (rows.length) {
    return rows
  }
  return [
    {
      title: '等待来源同步',
      status: '待同步',
      detail: '获取本地市场报价后，这里会展示已接入市场。',
      meta: '建议先进入行情页查看主表',
    },
  ]
})
const mobileSpotlightRows = computed(() => {
  const rows = marketRows.value.slice(0, 4).map((item) => ({
    identityKey: item.price_identity_key || item.product_name,
    title: item.product_name,
    category: resolveMarketCategory(item.product_name),
    market: item.lowest_price_site || item.region_label || '本地市场',
    price: formatMetricValue(item.average_price),
    unit: item.price_unit_basis || '元/公斤',
    lowest: formatMetricValue(item.lowest_price),
    spread: formatMetricSpread(item.lowest_price, item.highest_price),
  }))
  if (rows.length) {
    return rows
  }
  return [
    {
      identityKey: 'placeholder',
      title: '等待行情接入',
      category: '精选',
      market: '本地市场',
      price: '-',
      unit: '元/公斤',
      lowest: '-',
      spread: '价差待同步',
    },
  ]
})

const SUMMARY_CACHE_KEY = 'battel.market-summary.cache.v2'
const PRODUCT_OPTIONS_CACHE_KEY = 'battel.product-options.cache.v2'
const PRODUCT_SUMMARY_CACHE_KEY = 'battel.product-summary.cache.v2'
const PRODUCT_TREND_CACHE_KEY = 'battel.product-trend.cache.v2'
const BEIJING_DATE_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: 'numeric',
  day: 'numeric',
})
const BEIJING_DATETIME_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: 'numeric',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
})

function buildFilterParams() {
  return {
    province: filters.province || undefined,
    city: filters.city || undefined,
  }
}

function formatMetricValue(value?: number | string | null) {
  if (value == null || value === '') {
    return '-'
  }
  const normalizedValue = Number(value)
  return Number.isNaN(normalizedValue) ? String(value) : normalizedValue.toFixed(2)
}

function formatMetricSpread(lowest?: number | string | null, highest?: number | string | null) {
  const lowValue = Number(lowest)
  const highValue = Number(highest)
  if (Number.isNaN(lowValue) || Number.isNaN(highValue)) {
    return '价差待同步'
  }
  return `价差 ${Math.max(highValue - lowValue, 0).toFixed(2)}`
}

function formatBeijingDateTime(value?: string | null, fallback = '暂无', compact = false) {
  if (!value) return fallback
  const text = String(value).trim()
  if (!text) return fallback

  const parsedDate = new Date(text.replace(' ', 'T'))
  if (Number.isNaN(parsedDate.getTime())) {
    return text
  }

  const hasTime = /[T\s]\d{1,2}:\d{2}/.test(text)
  const parts = (hasTime ? BEIJING_DATETIME_FORMATTER : BEIJING_DATE_FORMATTER).formatToParts(parsedDate)
  const year = parts.find((item) => item.type === 'year')?.value ?? ''
  const month = parts.find((item) => item.type === 'month')?.value ?? ''
  const day = parts.find((item) => item.type === 'day')?.value ?? ''
  if (!hasTime) {
    return compact ? `${year}/${month}/${day}` : `${year}年${month}月${day}日`
  }
  const hour = parts.find((item) => item.type === 'hour')?.value ?? ''
  const minute = parts.find((item) => item.type === 'minute')?.value ?? ''
  const second = parts.find((item) => item.type === 'second')?.value ?? ''
  return compact ? `${year}/${month}/${day} ${hour}:${minute}` : `${year}年${month}月${day}日 ${hour}:${minute}:${second}`
}

function formatPriceMetric(value?: number | null, unit?: string | null) {
  const numeric = Number(value)
  if (value == null || Number.isNaN(numeric)) {
    return '-'
  }
  return unit ? `${numeric.toFixed(2)} ${unit}` : numeric.toFixed(2)
}

function buildContextKey(params: { province?: string; city?: string }) {
  return JSON.stringify({
    province: params.province || '',
    city: params.city || '',
  })
}

function buildTrendRequestKey(identityKey: string, mode: string, siteKey?: string) {
  return JSON.stringify({
    identityKey,
    mode,
    siteKey: siteKey || '',
  })
}

function extractTrendSiteOptions(rows: ProductTrendRow[]) {
  return Array.from(
    new Set(
      rows
        .map((row) => row.trend_series_key || row.trend_series_name || row.site_name)
        .filter(Boolean),
    ),
  ) as string[]
}

function getPrefetchSnapshotQueue(identityKey: string) {
  const existing = trendPrefetchPromises.get(identityKey)
  if (existing) {
    return existing
  }
  const promise = prefetchTrendSnapshot(identityKey).finally(() => {
    trendPrefetchPromises.delete(identityKey)
  })
  trendPrefetchPromises.set(identityKey, promise)
  return promise
}

function readLocalCache<T>(storageKey: string, cacheKey: string): T | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(storageKey)
    if (!raw) return null
    const payload = JSON.parse(raw) as Record<string, T>
    return payload[cacheKey] ?? null
  } catch {
    return null
  }
}

function writeLocalCache<T>(storageKey: string, cacheKey: string, value: T) {
  if (typeof window === 'undefined') return
  try {
    const raw = window.localStorage.getItem(storageKey)
    const payload = raw ? (JSON.parse(raw) as Record<string, T>) : {}
    payload[cacheKey] = value
    window.localStorage.setItem(storageKey, JSON.stringify(payload))
  } catch {
    // Ignore cache write failures.
  }
}

function readSummaryCache(params: { province?: string; city?: string }) {
  const cacheKey = buildContextKey(params)
  const cached = readLocalCache<MarketSummaryItem[]>(SUMMARY_CACHE_KEY, cacheKey)
  return Array.isArray(cached) ? cached : null
}

function writeSummaryCache(params: { province?: string; city?: string }, rows: MarketSummaryItem[]) {
  writeLocalCache(SUMMARY_CACHE_KEY, buildContextKey(params), rows)
}

function appendMenuLines(lines: string[]) {
  const normalized = lines.map((item) => item.trim()).filter(Boolean)
  if (!normalized.length) return
  const existing = menuForm.menuText.split('\n').map((item) => item.trim()).filter(Boolean)
  menuForm.menuText = [...existing, ...normalized].join('\n')
  ElMessage.success(`已导入 ${normalized.length} 条菜单项`)
}

function normalizeLocationList(values: unknown): string[] {
  if (!Array.isArray(values)) {
    return []
  }
  return Array.from(
    new Set(
      values
        .map((item) => String(item ?? '').trim())
        .filter(Boolean),
    ),
  ).sort((left, right) => left.localeCompare(right, 'zh-CN'))
}

function normalizeProvinceCityMap(input: unknown): Record<string, string[]> {
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    return {}
  }
  const normalizedEntries = Object.entries(input as Record<string, unknown>)
    .map(([province, value]) => [String(province ?? '').trim(), normalizeLocationList(value)] as const)
    .filter(([province]) => Boolean(province))
  return Object.fromEntries(normalizedEntries)
}

function pickPreferredProductOption(options: ProductOptionItem[]) {
  if (!options.length) {
    return null
  }
  const multiMarketOption = options.find((item) => Number(item.site_count || 0) > 1)
  return multiMarketOption || options[0]
}

function handleSelectProduct(identityKey: string) {
  const selectedRow = marketRows.value.find((item) => item.price_identity_key === identityKey)
  selectedProductFallbackLabel.value = selectedRow?.product_name || selectedProductFallbackLabel.value
  if (selectedIdentityKey.value !== identityKey) {
    selectedSiteName.value = ''
  }
  selectedIdentityKey.value = identityKey
  void prefetchNearbyTrendSnapshots(identityKey)
  if (activeTab.value !== 'trend') {
    void activateTab('trend')
  }
}

function goToLanding() {
  viewMode.value = 'landing'
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search)
    params.delete('mode')
    params.delete('tab')
    const nextQuery = params.toString()
    window.history.replaceState({}, '', `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ''}`)
  }
}

function openCategoryMarket(categoryKey: string) {
  activeMarketCategory.value = categoryKey
  enterWorkspace('summary')
}

function openProductDetail(identityKey: string) {
  if (!identityKey || identityKey === 'placeholder') {
    enterWorkspace('summary')
    return
  }
  viewMode.value = 'workspace'
  handleSelectProduct(identityKey)
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search)
    params.set('mode', 'workspace')
    params.set('tab', 'trend')
    window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`)
  }
}

function enterWorkspace(targetTab: (typeof tabs)[number]['key'] = isMobileViewport.value ? 'summary' : 'signals') {
  viewMode.value = 'workspace'
  void activateTab(targetTab)
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search)
    params.set('mode', 'workspace')
    params.set('tab', targetTab)
    window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`)
  }
}

async function activateTab(tabKey: (typeof tabs)[number]['key']) {
  const wasTrendTab = activeTab.value === 'trend'
  activeTab.value = tabKey
  if (tabKey !== 'trend') return
  await ensureProductOptionsLoaded()
  const firstOption = pickPreferredProductOption(productOptions.value)
  const identityKey = selectedIdentityKey.value || firstOption?.price_identity_key || ''
  if (!identityKey) return
  if (!selectedIdentityKey.value) {
    selectedIdentityKey.value = identityKey
    selectedProductFallbackLabel.value = firstOption?.price_identity_label || selectedProductFallbackLabel.value
  }
  if (wasTrendTab && selectedIdentityKey.value === identityKey) {
    return
  }
  await reloadTrend(identityKey)
}

async function reloadSummary() {
  summaryLoading.value = true
  try {
    pageError.value = ''
    const params = buildFilterParams()
    const cachedRows = readSummaryCache(params)
    if (cachedRows?.length) {
      marketRows.value = cachedRows
    }

    const summary = await fetchMarketSummary(params)
    marketRows.value = summary.items ?? []
    writeSummaryCache(params, marketRows.value)
  } catch (error) {
    pageError.value = dataSourceState.lastError || '报价接口暂不可用'
  } finally {
    summaryLoading.value = false
  }
}

async function reloadLocations(force = false) {
  if (
    locationLoading.value ||
    (!force && provinces.value.length > 0 && cities.value.length > 0 && Object.keys(provinceCityMap.value).length > 0)
  ) {
    return
  }
  locationLoading.value = true
  try {
    const locationData = await fetchLocationOptions()
    provinces.value = normalizeLocationList(locationData.provinces)
    cities.value = normalizeLocationList(locationData.cities)
    provinceCityMap.value = normalizeProvinceCityMap(locationData.province_city_map)
  } catch (error) {
    pageError.value = dataSourceState.lastError || '地区选项暂不可用'
  } finally {
    locationLoading.value = false
  }
}

async function handleCityDropdownVisible(visible: boolean) {
  if (!visible) {
    return
  }
  if (!filters.province) {
    if (!cities.value.length) {
      await reloadLocations(true)
    }
    return
  }
  const provinceCities = provinceCityMap.value[filters.province] || []
  if (!provinceCities.length) {
    await reloadLocations(true)
  }
}

async function reloadSourceCoverage() {
  if (coverageLoading.value) return
  coverageLoading.value = true
  try {
    const sourceCoverageData = await fetchSourceCoverage()
    sourceCoverageRows.value = sourceCoverageData.items ?? []
  } catch (error) {
    if (!sourceCoverageRows.value.length) {
      pageError.value = dataSourceState.lastError || '来源覆盖接口暂不可用'
    }
  } finally {
    coverageLoading.value = false
  }
}

function stopCrawlPolling() {
  if (typeof window === 'undefined') return
  if (crawlStatusTimer) {
    window.clearInterval(crawlStatusTimer)
    crawlStatusTimer = undefined
  }
}

async function reloadCrawlStatus() {
  try {
    const data = await fetchCrawlStatus()
    crawlStatus.value = data.item ?? null
    dailyScheduleEnabled.value = Boolean(data.item?.schedule_enabled)
  } catch (error) {
    // Keep previous crawl status if the endpoint is temporarily unavailable.
  }
}

function startCrawlPolling() {
  if (typeof window === 'undefined') return
  stopCrawlPolling()
  crawlStatusTimer = window.setInterval(async () => {
    const wasRunning = Boolean(crawlStatus.value?.is_running)
    await reloadCrawlStatus()
    const isRunning = Boolean(crawlStatus.value?.is_running)
    if (wasRunning && !isRunning) {
      stopCrawlPolling()
      await reloadAll()
      await ensureProductOptionsLoaded(true)
      if (activeTab.value === 'trend') {
        await reloadTrend()
      }
      if (crawlStatus.value?.last_error) {
        ElMessage.warning(`抓取完成，但存在异常：${crawlStatus.value.last_error}`)
      } else {
        ElMessage.success('最新数据已重新获取')
      }
    }
  }, 3000)
}

async function handleManualCrawl() {
  crawlActionLoading.value = true
  try {
    const data = await triggerCrawlRun()
    crawlStatus.value = data.item ?? null
    if (data.accepted) {
      ElMessage.success('已开始抓取最新数据')
      startCrawlPolling()
    } else {
      ElMessage.warning('当前已有抓取任务在执行')
    }
  } catch (error) {
    ElMessage.error('启动抓取失败，请确认后端服务正常')
  } finally {
    crawlActionLoading.value = false
  }
}

async function handleScheduleToggle(value: boolean) {
  scheduleActionLoading.value = true
  try {
    const data = await updateCrawlSchedule({
      enabled: value,
      interval_seconds: 86400,
      fetch_mode: crawlStatus.value?.schedule_fetch_mode || 'requests',
    })
    crawlStatus.value = data.item ?? null
    dailyScheduleEnabled.value = Boolean(data.item?.schedule_enabled)
    ElMessage.success(value ? '已开启每日自动获取' : '已关闭每日自动获取')
  } catch (error) {
    dailyScheduleEnabled.value = Boolean(crawlStatus.value?.schedule_enabled)
    ElMessage.error('更新自动获取设置失败')
  } finally {
    scheduleActionLoading.value = false
  }
}

async function ensureProductOptionsLoaded(force = false) {
  const params = buildFilterParams()
  const contextKey = buildContextKey(params)
  if (!force) {
    const cachedOptions = readLocalCache<ProductOptionItem[]>(PRODUCT_OPTIONS_CACHE_KEY, contextKey)
    if (cachedOptions?.length && (!productOptions.value.length || productOptionsContextKey.value !== contextKey)) {
      productOptions.value = cachedOptions
      productOptionsContextKey.value = contextKey
      if (!selectedIdentityKey.value) {
        selectedIdentityKey.value = cachedOptions[0].price_identity_key
        selectedProductFallbackLabel.value = cachedOptions[0].price_identity_label
      }
    }
    if (productOptionsContextKey.value === contextKey && productOptions.value.length) {
      void prefetchTopTrendSnapshots(contextKey)
      return
    }
  }
  if (productOptionsPromise && productOptionsLoading.value) {
    await productOptionsPromise
    void prefetchTopTrendSnapshots(contextKey)
    return
  }
  productOptionsPromise = (async () => {
    productOptionsLoading.value = true
    try {
      const optionsData = await fetchProductOptions(params)
      productOptions.value = optionsData.items ?? []
      productOptionsContextKey.value = contextKey
      writeLocalCache(PRODUCT_OPTIONS_CACHE_KEY, contextKey, productOptions.value)
      if (!selectedIdentityKey.value && productOptions.value.length) {
        const preferredOption = pickPreferredProductOption(productOptions.value)
        selectedIdentityKey.value = preferredOption?.price_identity_key || ''
        selectedProductFallbackLabel.value = preferredOption?.price_identity_label || ''
      }
    } catch (error) {
      if (!productOptions.value.length) {
        productOptions.value = []
        productOptionsContextKey.value = ''
      }
      pageError.value = dataSourceState.lastError || '商品列表接口暂不可用'
    } finally {
      productOptionsLoading.value = false
      productOptionsPromise = null
    }
  })()
  await productOptionsPromise
  void prefetchTopTrendSnapshots(contextKey)
}

async function reloadAll() {
  await reloadSummary()
  void reloadSalesAssets()
  void reloadSourceCoverage()
  void reloadCrawlStatus()
}

async function reloadSalesAssets() {
  try {
    const params = {
      ...buildFilterParams(),
      focus: filters.keyword || undefined,
    }
    const [overview, salesDemo] = await Promise.all([
      fetchSignalsOverview(params),
      fetchSalesDemoContent('sales'),
    ])
    signalOverview.value = overview
    demoContent.value = salesDemo
  } catch (error) {
    if (!signalOverview.value) {
      signalOverview.value = null
    }
  }
}

async function reloadTrend(identityKeyOverride?: string) {
  const identityKey = identityKeyOverride || selectedIdentityKey.value
  if (!identityKey) {
    productSummary.value = null
    trendRows.value = []
    trendSiteOptions.value = []
    selectedSiteName.value = ''
    trendLoading.value = false
    return
  }
  const requestId = ++trendRequestSequence
  trendLoading.value = true

  const summaryCacheKey = identityKey
  const summaryCached = readLocalCache<Record<string, any>>(PRODUCT_SUMMARY_CACHE_KEY, summaryCacheKey)
  if (summaryCached) {
    productSummary.value = summaryCached
  } else {
    productSummary.value = null
  }

  const currentSiteKey = selectedSiteName.value || undefined
  const currentTrendCacheKey = buildTrendRequestKey(identityKey, trendMode.value, currentSiteKey)
  const crossMarketTrendCacheKey = buildTrendRequestKey(identityKey, 'cross_market')
  const cachedTrendRows = readLocalCache<ProductTrendRow[]>(PRODUCT_TREND_CACHE_KEY, currentTrendCacheKey)
  const cachedCrossMarketRows = readLocalCache<ProductTrendRow[]>(PRODUCT_TREND_CACHE_KEY, crossMarketTrendCacheKey)
  const usedCachedTrend = Boolean(cachedTrendRows?.length)
  if (cachedTrendRows?.length) {
    trendRows.value = cachedTrendRows
  }
  if (cachedCrossMarketRows?.length) {
    trendSiteOptions.value = extractTrendSiteOptions(cachedCrossMarketRows)
  } else if (trendMode.value === 'cross_market' && cachedTrendRows?.length) {
    trendSiteOptions.value = extractTrendSiteOptions(cachedTrendRows)
  } else {
    trendSiteOptions.value = []
  }

  try {
    const filterParams = buildFilterParams()
    const summaryRequest = fetchProductSummary(identityKey, filterParams)

    const loadCrossMarketRows = async () => {
      if (cachedCrossMarketRows?.length) {
        return cachedCrossMarketRows
      }
      const response = await fetchProductTrend(identityKey, { mode: 'cross_market', ...filterParams })
      const rows = response.items ?? []
      writeLocalCache(PRODUCT_TREND_CACHE_KEY, crossMarketTrendCacheKey, rows)
      return rows
    }

    let trend: { items?: ProductTrendRow[] }
    if (trendMode.value === 'single_market') {
      const crossMarketRows = await loadCrossMarketRows()
      trendSiteOptions.value = extractTrendSiteOptions(crossMarketRows)
      const siteName = selectedSiteName.value || trendSiteOptions.value[0] || ''
      if (siteName && selectedSiteName.value !== siteName) {
        selectedSiteName.value = siteName
      }
      trend = siteName
        ? await fetchProductTrend(identityKey, {
            mode: 'single_market',
            series_key: siteName,
            ...filterParams,
          })
        : { items: [] }
    } else {
      trend = await fetchProductTrend(identityKey, {
        mode: 'cross_market',
        ...filterParams,
      })
      const crossMarketRows = trend.items ?? []
      trendSiteOptions.value = extractTrendSiteOptions(crossMarketRows)
      writeLocalCache(PRODUCT_TREND_CACHE_KEY, crossMarketTrendCacheKey, crossMarketRows)
    }

    const summary = await summaryRequest
    if (requestId !== trendRequestSequence || identityKey !== selectedIdentityKey.value) {
      return
    }
    productSummary.value = summary.item ?? null
    if (productSummary.value) {
      writeLocalCache(PRODUCT_SUMMARY_CACHE_KEY, summaryCacheKey, productSummary.value)
    }
    trendRows.value = trend.items ?? []
    writeLocalCache(
      PRODUCT_TREND_CACHE_KEY,
      buildTrendRequestKey(identityKey, trendMode.value, selectedSiteName.value),
      trendRows.value,
    )
    void prefetchNearbyTrendSnapshots(identityKey)
  } catch (error) {
    if (requestId !== trendRequestSequence || identityKey !== selectedIdentityKey.value) {
      return
    }
    pageError.value = dataSourceState.lastError || '趋势接口暂不可用'
    if (!usedCachedTrend) {
      trendRows.value = []
    }
  } finally {
    if (requestId === trendRequestSequence && identityKey === selectedIdentityKey.value) {
      trendLoading.value = false
    }
  }
}

async function prefetchTrendSnapshot(identityKey: string) {
  if (!identityKey) return
  const summaryCacheKey = identityKey
  const trendCacheKey = buildTrendRequestKey(identityKey, 'cross_market')
  const cachedSummary = readLocalCache<Record<string, any>>(PRODUCT_SUMMARY_CACHE_KEY, summaryCacheKey)
  const cachedTrend = readLocalCache<ProductTrendRow[]>(PRODUCT_TREND_CACHE_KEY, trendCacheKey)
  if (cachedSummary && cachedTrend?.length) {
    return
  }
  try {
    const [summary, trend] = await Promise.all([
      cachedSummary ? Promise.resolve({ item: cachedSummary }) : fetchProductSummary(identityKey, buildFilterParams()),
      cachedTrend?.length ? Promise.resolve({ items: cachedTrend }) : fetchProductTrend(identityKey, { mode: 'cross_market', ...buildFilterParams() }),
    ])
    if (summary.item) {
      writeLocalCache(PRODUCT_SUMMARY_CACHE_KEY, summaryCacheKey, summary.item)
    }
    if (trend.items?.length) {
      writeLocalCache(PRODUCT_TREND_CACHE_KEY, trendCacheKey, trend.items)
    }
  } catch {
    // Ignore prefetch failures and keep interactive fetch as fallback.
  }
}

async function prefetchTopTrendSnapshots(contextKey: string) {
  if (!productOptions.value.length) return
  trendPrefetchContextKey = contextKey
  const keys = productOptions.value
    .slice(0, 12)
    .map((item) => item.price_identity_key)
    .filter(Boolean)
  await runPrefetchQueue(keys, contextKey)
}

async function prefetchNearbyTrendSnapshots(identityKey: string) {
  if (!identityKey || !productOptions.value.length) return
  const contextKey = buildContextKey(buildFilterParams())
  const currentIndex = productOptions.value.findIndex((item) => item.price_identity_key === identityKey)
  if (currentIndex < 0) return
  const keys = productOptions.value
    .slice(Math.max(0, currentIndex - 3), currentIndex + 4)
    .map((item) => item.price_identity_key)
    .filter(Boolean)
  await runPrefetchQueue(keys, contextKey)
}

async function runPrefetchQueue(identityKeys: string[], contextKey: string) {
  const uniqueKeys = Array.from(new Set(identityKeys.filter(Boolean)))
  if (!uniqueKeys.length) return
  trendPrefetchContextKey = contextKey
  const concurrency = Math.min(3, uniqueKeys.length)
  let cursor = 0
  await Promise.all(
    Array.from({ length: concurrency }, async () => {
      while (cursor < uniqueKeys.length) {
        if (trendPrefetchContextKey !== contextKey) {
          return
        }
        const key = uniqueKeys[cursor]
        cursor += 1
        await getPrefetchSnapshotQueue(key)
      }
    }),
  )
}

async function submitMenuPlan() {
  menuPlanLoading.value = true
  try {
    const payload = {
      menu_text: menuForm.menuText,
      diners: menuForm.diners,
      tables: menuForm.tables,
      preferred_province: filters.province || undefined,
      preferred_city: filters.city || undefined,
      preferred_location: menuForm.preferredLocation || undefined,
    }
    const [data, recommendation] = await Promise.all([
      generateMenuPlan(payload),
      fetchProcurementRecommendation(payload),
    ])
    ingredientRows.value = data.ingredient_items ?? []
    planRows.value = data.procurement_plan ?? []
    procurementRecommendations.value = recommendation.items ?? []
    ElMessage.success('采购方案已生成')
  } catch (error) {
    ElMessage.error('采购方案生成失败，请确认 API 已启动')
  } finally {
    menuPlanLoading.value = false
  }
}

watch([() => filters.province, () => filters.city], async () => {
  activeMarketCategory.value = '全部'
  productOptions.value = []
  productOptionsContextKey.value = ''
  selectedIdentityKey.value = ''
  selectedSiteName.value = ''
  selectedProductFallbackLabel.value = ''
  trendLoading.value = false
  trendPrefetchContextKey = ''
  await reloadAll()
})

watch(() => filters.province, async (province) => {
  if (province && !(provinceCityMap.value[province] || []).length) {
    await reloadLocations(true)
  }
  const availableCities = province ? (provinceCityMap.value[province] || []) : cities.value
  if (filters.city && !availableCities.includes(filters.city)) {
    filters.city = ''
  }

  const locationCandidates = new Set<string>(['当前位置', ...availableCities, ...provinces.value])
  if (menuForm.preferredLocation && !locationCandidates.has(menuForm.preferredLocation)) {
    menuForm.preferredLocation = ''
  }
})

watch([selectedIdentityKey, trendMode, selectedSiteName], async ([identityKey, mode, site], [prevIdentityKey, prevMode, prevSite]) => {
  if (activeTab.value !== 'trend') return
  if (!identityKey) return
  if (identityKey === prevIdentityKey && mode === prevMode && site === prevSite) return
  await reloadTrend()
})

onMounted(async () => {
  void reloadLocations()
  await reloadAll()
  void ensureProductOptionsLoaded().then(() => {
    const identityKey = selectedIdentityKey.value || pickPreferredProductOption(productOptions.value)?.price_identity_key || ''
    if (identityKey && activeTab.value !== 'trend') {
      void prefetchTrendSnapshot(identityKey)
    }
  })
  if (activeTab.value === 'trend') {
    await activateTab('trend')
  }
  if (crawlStatus.value?.is_running) {
    startCrawlPolling()
  }
})

onBeforeUnmount(() => {
  stopCrawlPolling()
})
</script>

<style scoped>
.market-mobile-home,
.market-mobile-shell {
  display: grid;
  gap: 14px;
  padding-bottom: calc(88px + env(safe-area-inset-bottom));
}

.market-mobile-home-hero,
.market-mobile-shell-head,
.market-mobile-lead-card {
  display: grid;
  gap: 14px;
}

.market-mobile-home-topline,
.market-mobile-section-head,
.market-mobile-source-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.market-mobile-kicker {
  margin: 0;
  color: var(--accent-blue-bright);
  font-family: var(--code-font);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.market-mobile-home h1,
.market-mobile-shell h1,
.market-mobile-section-head h2 {
  margin: 4px 0 0;
  color: var(--ink-900);
  letter-spacing: -0.04em;
}

.market-mobile-home h1,
.market-mobile-shell h1 {
  font-size: 24px;
  line-height: 1.05;
}

.market-mobile-section-head h2 {
  font-size: 18px;
  line-height: 1.12;
}

.market-mobile-city-pill,
.market-mobile-accent-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(239, 246, 255, 0.92);
  color: var(--accent-blue);
  font-family: var(--code-font);
  font-size: 10px;
  font-weight: 700;
}

.market-mobile-hero-copy,
.market-mobile-shell-copy p,
.market-mobile-lead-copy,
.market-mobile-source-card p {
  margin: 0;
  color: var(--ink-700);
  font-size: 13px;
  line-height: 1.6;
}

.market-mobile-search-row,
.market-mobile-lead-actions,
.market-mobile-context-row {
  display: grid;
  gap: 10px;
}

.market-mobile-stat-grid,
.market-mobile-source-grid,
.market-mobile-product-feed {
  display: grid;
  gap: 10px;
}

.market-mobile-stat-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.market-mobile-stat-card,
.market-mobile-source-card,
.market-mobile-product-card,
.market-mobile-context-pill {
  display: grid;
  gap: 5px;
  min-width: 0;
  padding: 12px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(248, 250, 252, 0.86);
}

.market-mobile-stat-card span,
.market-mobile-source-card span,
.market-mobile-context-pill span,
.market-mobile-product-top span,
.market-mobile-product-meta span {
  color: var(--ink-500);
  font-size: 10px;
}

.market-mobile-stat-card strong,
.market-mobile-source-card strong,
.market-mobile-context-pill strong,
.market-mobile-product-card strong {
  color: var(--ink-900);
  font-size: 14px;
  line-height: 1.3;
}

.market-mobile-chip-strip,
.market-mobile-tab-strip {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.market-mobile-chip,
.market-mobile-tab-button,
.market-mobile-bottom-item,
.market-mobile-back-button,
.market-mobile-product-card {
  font: inherit;
  cursor: pointer;
}

.market-mobile-chip,
.market-mobile-tab-button,
.market-mobile-back-button {
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(255, 255, 255, 0.92);
}

.market-mobile-chip {
  display: grid;
  flex: 0 0 auto;
  gap: 4px;
  min-width: 88px;
  padding: 10px 12px;
  border-radius: 16px;
  text-align: left;
}

.market-mobile-chip strong,
.market-mobile-tab-button {
  color: var(--ink-900);
  font-size: 13px;
  font-weight: 700;
}

.market-mobile-chip small {
  color: var(--ink-500);
  font-size: 10px;
}

.market-mobile-tab-button {
  min-height: 42px;
  padding: 0 16px;
  border-radius: 999px;
}

.market-mobile-tab-button.active,
.market-mobile-bottom-item.active,
.market-mobile-back-button {
  color: #eff6ff;
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.96), rgba(37, 99, 235, 0.92));
  border-color: transparent;
  box-shadow: 0 14px 24px rgba(30, 64, 175, 0.18);
}

.market-mobile-source-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.market-mobile-source-card small,
.market-mobile-shell-copy p,
.market-mobile-context-pill strong {
  white-space: normal;
}

.market-mobile-product-card {
  border: none;
  text-align: left;
  transition:
    transform var(--transition-fast),
    box-shadow var(--transition-fast);
}

.market-mobile-product-card:focus-visible,
.market-mobile-product-card:active {
  outline: none;
  transform: translateY(-1px);
  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.12);
}

.market-mobile-product-top,
.market-mobile-product-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.market-mobile-product-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.market-mobile-product-price b {
  color: var(--accent-blue);
  font-size: 22px;
  line-height: 1;
}

.market-mobile-product-price small,
.market-mobile-product-top small {
  color: var(--ink-500);
  font-size: 11px;
}

.market-mobile-shell-content {
  min-width: 0;
}

.market-mobile-bottom-nav {
  position: fixed;
  left: 12px;
  right: 12px;
  bottom: max(12px, env(safe-area-inset-bottom));
  z-index: 8;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  padding: 10px;
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(18px);
  box-shadow: 0 20px 38px rgba(15, 23, 42, 0.12);
}

.market-mobile-bottom-item {
  display: grid;
  gap: 2px;
  min-height: 52px;
  padding: 8px 10px;
  border: none;
  border-radius: 16px;
  background: transparent;
  color: var(--ink-900);
  text-align: center;
}

.market-mobile-bottom-item span {
  font-size: 10px;
  color: var(--ink-500);
}

.market-mobile-bottom-item strong {
  font-size: 13px;
}

@media (max-width: 430px) {
  .market-mobile-stat-grid,
  .market-mobile-source-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 360px) {
  .market-mobile-source-grid {
    grid-template-columns: 1fr;
  }
}
</style>
