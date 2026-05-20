<template>

  <section v-if="isLegacyMobileLandingEnabled && isMobileViewport && viewMode === 'landing'" class="app-shell market-mobile-home mobile-redesign-home" data-testid="sales-landing-view">
    <header class="mobile-redesign-hero-card">
      <div class="mobile-redesign-topbar">
        <div class="mobile-redesign-brand">
          <span>食</span>
          <div>
            <strong>食采云</strong>
            <small>本地餐饮采购</small>
          </div>
        </div>
        <div class="mobile-redesign-top-actions">
          <button type="button" class="mobile-redesign-location" @click="enterWorkspace('summary')">
            <i></i>
            {{ selectedLocationLabel }}
          </button>
          <button type="button" class="mobile-redesign-alert-dot" aria-label="查看预警消息" @click="enterWorkspace('alerts')">
            <b>{{ mobileAlertBadge }}</b>
          </button>
        </div>
      </div>

      <div class="mobile-redesign-hero-copy">
        <p>本地采购工作台</p>
        <h1>先看预警，再找低价，最后下采购单</h1>
        <small>{{ latestSyncLabel === '等待同步' ? '真实行情同步后会更新今日商品和预警。' : `最近同步 ${latestSyncLabel}` }}</small>
      </div>

      <div class="mobile-redesign-search">
        <el-input
          v-model="filters.keyword"
          type="search"
          inputmode="search"
          enterkeyhint="search"
          aria-label="搜索食材关键词"
          placeholder="搜商品、市场、供应商"
          clearable
          @keyup.enter="enterWorkspace('summary')"
        />
        <button type="button" data-testid="enter-workspace-button" @click="enterWorkspace('summary')">查价</button>
      </div>

      <div class="mobile-redesign-stat-strip" aria-label="今日关键动作">
        <button type="button" class="danger" @click="enterWorkspace('alerts')">
          <span>预警</span>
          <strong>{{ mobileAlertBadge }}</strong>
        </button>
        <button type="button" class="primary" @click="enterWorkspace('summary')">
          <span>低价</span>
          <strong>{{ mobileSpotlightRows.length }}</strong>
        </button>
        <button type="button" class="success" @click="enterWorkspace('menu')">
          <span>采购</span>
          <strong>{{ parsedMenuCount || procurementRecommendations.length || planRows.length }}</strong>
        </button>
      </div>
    </header>

    <main class="mobile-redesign-main">
      <section class="mobile-redesign-section mobile-redesign-priority-grid">
        <div class="mobile-redesign-workbench-head">
          <p>工作台</p>
          <h2>市场价格工作台</h2>
        </div>
        <button type="button" class="mobile-redesign-priority-card is-main" @click="mobileAlertBadge ? enterWorkspace('alerts') : enterWorkspace('menu')">
          <p>{{ mobileAlertBadge ? '先处理' : '继续采购' }}</p>
          <strong>{{ mobileAlertBadge ? `${mobileAlertBadge} 条价格预警待处理` : '把菜单直接变成采购建议' }}</strong>
          <small>{{ mobileAlertBadge ? '先确认影响今日采购成本的商品，再去看低价和生成方案。' : (matchedPlanCount ? `${matchedPlanCount} 项已匹配报价，可以直接继续采购。` : '录菜单后自动拆食材、匹配行情和供应商报价。') }}</small>
        </button>
      </section>

      <section class="mobile-redesign-section mobile-redesign-products" data-testid="mobile-spotlight-feed-section">
        <div class="mobile-redesign-section-head">
          <div>
            <p>今日低价</p>
            <h2>重点商品行情</h2>
          </div>
          <div class="mobile-redesign-head-actions">
            <button type="button" class="mobile-trend-shortcut market-mobile-bottom-item" @click="enterWorkspace('trend')">单品</button>
            <button type="button" @click="enterWorkspace('summary')">全部</button>
          </div>
        </div>
        <div class="mobile-redesign-product-rail" data-testid="mobile-spotlight-feed">
          <button
            v-for="item in mobileSpotlightRows.slice(0, 3)"
            :key="item.identityKey"
            type="button"
            class="mobile-redesign-product-card"
            @click="openProductDetail(item.identityKey)"
          >
            <div class="mobile-redesign-product-copy">
              <strong>{{ item.title }}</strong>
              <span>{{ item.category }}</span>
            </div>
            <footer>
              <b>{{ item.price }} <small>{{ item.unit }}</small></b>
              <em>{{ item.spread }}</em>
            </footer>
          </button>
          <div v-if="!mobileSpotlightRows.length" class="mobile-redesign-empty-card">
            <strong>等待真实行情同步</strong>
            <small>同步后这里会优先展示低价和价差明显的商品。</small>
          </div>
        </div>
      </section>

      <section class="mobile-redesign-section mobile-redesign-sources">
        <div class="mobile-redesign-section-head">
          <div>
            <p>常采分类</p>
            <h2>按分类快速进入</h2>
          </div>
          <button type="button" @click="showMobileHomeMore = !showMobileHomeMore">
            {{ showMobileHomeMore ? '收起' : '更多' }}
          </button>
        </div>
        <div class="mobile-redesign-source-grid" data-testid="mobile-source-groups">
          <button
            v-for="item in displayedMobileCategoryTableRows.slice(0, showMobileHomeMore ? 6 : 4)"
            :key="item.key"
            type="button"
            @click="openCategoryMarket(item.category)"
          >
            <span>{{ item.category }}</span>
            <strong>{{ item.subcategory }}</strong>
            <small>{{ item.count }} 款可比价</small>
          </button>
          <div v-if="!mobileCategoryTableRows.length" class="mobile-redesign-empty-card compact">
            <strong>暂无商品分类</strong>
            <small>{{ selectedCategorySourceLabel }} 当前没有可展示分类。</small>
          </div>
        </div>
      </section>

      <section class="mobile-redesign-section mobile-redesign-alert-preview">
        <div class="mobile-redesign-section-head">
          <div>
            <p>最新预警</p>
            <h2>需要马上看的商品</h2>
          </div>
          <button type="button" @click="enterWorkspace('alerts')">处理</button>
        </div>
        <div class="mobile-redesign-alert-list">
          <button
            v-for="item in mobileAlertRows.slice(0, 3)"
            :key="`${item.name}-${item.market}`"
            type="button"
            @click="enterWorkspace('alerts')"
          >
            <strong>{{ item.name }}</strong>
            <span>{{ item.market }} · {{ item.current }}</span>
            <small>{{ item.rule }}</small>
          </button>
          <div v-if="!mobileAlertRows.length" class="mobile-redesign-empty-card compact">
            <strong>暂无触发预警</strong>
            <small>超过阈值后会直接进入待处理。</small>
          </div>
        </div>
      </section>

      <section class="mobile-redesign-section mobile-redesign-entry-section">
        <div class="mobile-redesign-section-head">
          <div>
            <p>协同入口</p>
            <h2>采购与供应一起处理</h2>
          </div>
        </div>
        <div class="mobile-redesign-entry-grid">
          <button type="button" data-testid="mobile-buyer-entry-button" @click="enterWorkspace()">
            <span>采购工作台</span>
            <strong>继续采购</strong>
            <small>行情、预警、菜单采购</small>
          </button>
          <button type="button" data-testid="mobile-supplier-nav-button" @click="openSupplierPortal(false)">
            <span>供应商报价</span>
            <strong>去录价</strong>
            <small>录价、草稿、历史</small>
          </button>
        </div>
      </section>
    </main>

    <nav class="market-mobile-bottom-nav mobile-redesign-nav">
      <button type="button" class="market-mobile-bottom-item active" aria-label="首页" @click="goToLanding()">
        <span class="market-mobile-nav-icon home"></span>
        <strong>首页</strong>
      </button>
      <button type="button" class="market-mobile-bottom-item" aria-label="行情" @click="enterWorkspace('summary')">
        <span class="market-mobile-nav-icon market"></span>
        <strong>行情</strong>
      </button>
      <button type="button" class="market-mobile-bottom-item" aria-label="价格预警" @click="enterWorkspace('alerts')">
        <span class="market-mobile-nav-icon alert"></span>
        <strong>预警</strong>
      </button>
      <button type="button" class="market-mobile-bottom-item" aria-label="采购" @click="enterWorkspace('menu')">
        <span class="market-mobile-nav-icon buy"></span>
        <strong>采购</strong>
      </button>
    </nav>
  </section>



  <div v-else-if="isMobileViewport" class="app-shell market-mobile-shell">

    <header class="market-mobile-shell-head">

      <button type="button" class="market-mobile-back-button market-mobile-back-icon" aria-label="返回首页" @click="goToLanding()">‹</button>

      <div class="market-mobile-shell-copy">

        <h1>{{ mobileTabMeta.title }}</h1>

      </div>

      <button type="button" class="mobile-trend-shortcut market-mobile-bottom-item" aria-label="单品" @click="enterWorkspace('trend')">单品</button>

      <button type="button" class="market-mobile-message-button" aria-label="查看预警消息" @click="enterWorkspace('alerts')">

        <span></span>

        <b>{{ mobileAlertBadge }}</b>

      </button>

    </header>



    <section v-if="showBlockingError" class="active-strip compact source-warning-strip">

      <div>

        <h2>真实接口连接失败</h2>

        <p class="active-strip-copy">请先确认 API 已启动，再刷新页面查看真实抓取结果。</p>

      </div>

      <div class="source-warning-text">{{ pageError || dataSourceState.lastError || '接口连接失败' }}</div>

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

        @refresh-products="refreshTrendProducts"

        @open-tab="enterWorkspace"

      />



      <section v-else-if="mobileActiveTab === 'alerts'" class="market-mobile-alert-page">
        <header class="market-mobile-alert-hero">
          <div>
            <p class="market-mobile-kicker">价格预警</p>
            <h2>先处理异常</h2>
            <span>{{ mobileAlertHeroText }}</span>
          </div>
          <strong>{{ mobileAlertBadge }}</strong>
        </header>

        <div class="market-mobile-alert-pills" aria-label="预警概览">
          <article v-for="item in mobileAlertSummaryPills" :key="item.label" :class="item.tone">
            <strong>{{ item.value }}</strong>
            <span>{{ item.label }}</span>
          </article>
        </div>

        <section class="market-mobile-alert-card market-mobile-alert-feed-card">
          <div class="market-mobile-section-head">
            <div>
              <p class="market-mobile-kicker">待办列表</p>
              <h2>今天要看的商品</h2>
            </div>
            <span>{{ mobileAlertRows.length }} 条</span>
          </div>

          <div class="market-mobile-alert-list">
            <article v-for="item in mobileAlertRows" :key="`${item.name}-${item.market}`" :class="['market-mobile-alert-row', item.tone]">
              <div class="market-mobile-alert-row-main">
                <div class="market-mobile-alert-thumb-shell">
                  <img
                    v-if="item.imageUrl"
                    :src="item.imageUrl"
                    :alt="item.name"
                    class="market-mobile-alert-thumb-image"
                    loading="lazy"
                    decoding="async"
                    @click.stop="openImagePreview(item.imageUrl, item.name)"
                  />
                  <span v-else :class="['market-mobile-thumb', item.thumb]"></span>
                </div>
                <div>
                  <strong>{{ item.name }}</strong>
                  <small>{{ item.market }} · {{ item.current }}</small>
                </div>
                <em>{{ item.state }}</em>
              </div>
              <p>{{ item.rule }}</p>
              <footer>
                <button type="button" @click="openMobileAlertTrend(item)">看趋势</button>
                <button type="button" @click="openMobileAlertSupplier(item)">找报价</button>
                <button type="button" class="primary" @click="acknowledgeMobileAlert(item)">标记处理</button>
                <time>{{ item.time }}</time>
              </footer>
            </article>

            <div v-if="!mobileAlertRows.length" class="market-mobile-alert-empty">
              <strong>暂无触发预警</strong>
              <p>当前商品与市场继续监控，超过阈值后会出现在这里。</p>
            </div>
          </div>
        </section>

        <section class="market-mobile-alert-card market-mobile-alert-rule-card" :class="{ collapsed: !showMobileAlertRuleForm }">
          <div class="market-mobile-section-head">
            <div>
              <p class="market-mobile-kicker">规则</p>
              <h2>设置价格线</h2>
            </div>
            <button
              type="button"
              class="market-mobile-rule-toggle"
              @click="showMobileAlertRuleForm = !showMobileAlertRuleForm"
            >
              {{ showMobileAlertRuleForm ? '收起' : '新建规则' }}
            </button>
          </div>

          <p v-if="!showMobileAlertRuleForm" class="market-mobile-rule-summary">
            先处理上面的异常；需要盯某个商品最高/最低价时，再新建规则。
          </p>

          <div v-else class="market-mobile-rule-form">
            <label>
              <span>商品</span>
              <select v-model="mobileAlertRuleDraft.identityKey">
                <option value="">请选择商品</option>
                <option v-for="item in mobileAlertProductOptions" :key="item.value" :value="item.value">
                  {{ item.label }}
                </option>
              </select>
            </label>
            <label>
              <span>来源</span>
              <select v-model="mobileAlertRuleDraft.sourceName">
                <option value="">全部来源</option>
                <option v-for="item in mobileAlertSourceOptions" :key="item" :value="item">
                  {{ item }}
                </option>
              </select>
            </label>
            <label><span>市场</span><strong>{{ selectedLocationLabel }}</strong></label>
            <label><span>最高价</span><input v-model.number="mobileAlertRuleDraft.maxPrice" type="number" min="0" step="0.01" placeholder="例如 12.50" /></label>
            <label><span>最低价</span><input v-model.number="mobileAlertRuleDraft.minPrice" type="number" min="0" step="0.01" placeholder="例如 8.80" /></label>
            <label><span>阈值</span><strong>{{ mobileAlertThresholdLabel }}</strong></label>
            <button type="button" @click="saveMobileAlertRule">保存规则</button>
          </div>
        </section>

      </section>

      <section v-else class="market-mobile-menu-page">

        <div class="market-mobile-menu-intro">

          <p class="market-mobile-kicker">采购表单</p>

          <h2>录菜单，直接出采购建议</h2>

          <span>{{ parsedMenuCount }} 个菜品 · {{ matchedPlanCount }} 项已匹配 · {{ pendingPlanCount }} 项待确认</span>

        </div>

        <MenuPlanPanel

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
          @view-market="handleMenuPlanViewMarket"
          @fill-supplier-price="handleMenuPlanFillSupplierPrice"
          @confirm-row="handleMenuPlanConfirmRow"
          @fill-missing-quotes="handleMenuPlanFillMissingQuotes"

        />

      </section>

    </main>



    <nav class="market-mobile-bottom-nav">

      <button type="button" class="market-mobile-bottom-item" @click="goToLanding()">

        <span class="market-mobile-nav-icon home"></span>

        <strong>首页</strong>

      </button>

      <button

        type="button"

        class="market-mobile-bottom-item"

        :class="{ active: mobileActiveTab === 'summary' }"

        aria-label="行情"

        @click="enterWorkspace('summary')"

      >

        <span class="market-mobile-nav-icon market"></span>

        <strong>行情</strong>

      </button>

      <button

        type="button"

        class="market-mobile-bottom-item"

        :class="{ active: mobileActiveTab === 'alerts' }"

        aria-label="价格预警"

        @click="enterWorkspace('alerts')"

      >

        <span class="market-mobile-nav-icon alert"></span>

        <strong>预警</strong>

      </button>

      <button

        type="button"

        class="market-mobile-bottom-item"

        :class="{ active: mobileActiveTab === 'menu' }"

        aria-label="采购"

        @click="enterWorkspace('menu')"

      >

        <span class="market-mobile-nav-icon buy"></span>

        <strong>采购</strong>

      </button>

    </nav>

  </div>



  <section v-else-if="viewMode === 'landing'" class="app-shell platform-choice-shell" data-testid="sales-landing-view">
    <nav class="platform-choice-nav" aria-label="首页导航">
      <button type="button" class="platform-choice-wordmark" @click="enterWorkspace()">
        <span>食</span>
        <strong>食采云</strong>
      </button>
      <div class="platform-choice-nav-links" aria-label="能力导航">
        <button type="button" @click="enterWorkspace('summary')">行情洞察</button>
        <button type="button" @click="enterWorkspace('suppliers')">供应商协同</button>
        <button type="button" @click="enterWorkspace('plan')">采购计划</button>
      </div>
      <div class="platform-choice-nav-actions">
        <button type="button" class="platform-choice-pill ghost" @click="openSupplierPortal(false)">供应商入口</button>
        <button type="button" class="platform-choice-pill solid" @click="enterWorkspace()">客户进入</button>
      </div>
    </nav>

    <section class="platform-choice-hero-banner" data-testid="platform-choice-hero">
      <div class="platform-choice-hero-banner-copy">
        <div class="platform-choice-update-badge" data-testid="homepage-local-change-badge">
          <span>采购平台</span>
          <strong>行情、报价、计划在一个工作台里闭环</strong>
        </div>
        <h1>让餐饮采购<br><em>更简单。</em></h1>
        <p>把市场行情、供应商报价、菜单采购和结算协同放进同一张决策桌。少看复杂数据，多做正确决策。</p>
        <div class="platform-choice-hero-tags" aria-label="平台能力">
          <span>实时行情</span>
          <span>报价比价</span>
          <span>采购建议</span>
          <span>供应商门户</span>
        </div>
        <div class="platform-choice-hero-banner-actions" aria-label="主要入口">
          <button type="button" class="platform-choice-pill solid large" data-testid="enter-workspace-button" @click="enterWorkspace()">
            进入采购平台
          </button>
          <button type="button" class="platform-choice-pill ghost large" data-testid="supplier-choice-button" @click="openSupplierPortal(false)">
            我是供应商
          </button>
        </div>
      </div>
      <aside class="platform-choice-hero-rail" aria-label="今日采购简报">
        <div class="platform-choice-rail-header">
          <span>今日采购简报</span>
          <strong>可执行</strong>
        </div>
        <div class="platform-choice-signal-list">
          <article>
            <span class="signal-dot green"></span>
            <div>
              <strong>低价窗口</strong>
              <small>自动聚合多个市场，优先标出可下单品类。</small>
            </div>
          </article>
          <article>
            <span class="signal-dot amber"></span>
            <div>
              <strong>异常波动</strong>
              <small>高波动商品提前预警，避免临采被动。</small>
            </div>
          </article>
          <article>
            <span class="signal-dot blue"></span>
            <div>
              <strong>供应商报价</strong>
              <small>报价、作废、结算台账留痕可追溯。</small>
            </div>
          </article>
        </div>
        <div class="platform-choice-rail-metrics">
          <div>
            <small>决策链路</small>
            <strong>4步</strong>
            <span>看行情 → 选好价 → 出计划 → 留台账</span>
          </div>
          <div>
            <small>推荐动作</small>
            <strong>实时</strong>
            <span>按市场、分类、商品自动刷新</span>
          </div>
        </div>
      </aside>
    </section>

    <section class="platform-choice-feature-strip" aria-label="核心价值">
      <article class="platform-choice-inline-route">
        <div class="platform-choice-inline-route-copy">
          <span>Market Signal</span>
          <strong>看得懂行情</strong>
          <p>用清楚的价格趋势和市场对比，帮助客户快速判断今天该不该采购。</p>
          <ul>
            <li>市场汇总</li>
            <li>趋势追踪</li>
          </ul>
        </div>
        <div class="platform-choice-inline-route-meta">
          <small>01</small>
          <em>进入行情 ›</em>
        </div>
      </article>
      <article class="platform-choice-inline-route">
        <div class="platform-choice-inline-route-copy">
          <span>Supplier Quote</span>
          <strong>选得到好价</strong>
          <p>把供应商报价集中展示，减少反复询价，让采购选择更直接。</p>
          <ul>
            <li>报价比对</li>
            <li>历史留痕</li>
          </ul>
        </div>
        <div class="platform-choice-inline-route-meta">
          <small>02</small>
          <em>管理报价 ›</em>
        </div>
      </article>
      <article class="platform-choice-inline-route">
        <div class="platform-choice-inline-route-copy">
          <span>Procurement Flow</span>
          <strong>协同更省心</strong>
          <p>采购方和供应商在同一平台完成沟通、报价和后续跟进。</p>
          <ul>
            <li>菜单采购</li>
            <li>结算台账</li>
          </ul>
        </div>
        <div class="platform-choice-inline-route-meta">
          <small>03</small>
          <em>开始协同 ›</em>
        </div>
      </article>
    </section>
  </section>

  <PcPriceWorkbench
    v-else-if="!isMobileViewport"
    :active-tab="activeTab"
    :location-label="selectedLocationLabel"
    :rows="activeSupplierSummaryRow && activeTab === 'summary' ? [activeSupplierSummaryRow, ...marketRows] : marketRows"
    :summary-loading="summaryLoading"
    :summary-status-text="summaryStatusText"
    :source-coverage-rows="sourceCoverageRows"
    :crawl-status="crawlStatus"
    :summary-liancai-filter="summaryLiancaiFilter"
    :liancai-category-summary-items="liancaiCategorySummaryItems"
    :liancai-facet-options="liancaiFacetOptions"
    :product-options="productOptions"

    :selected-identity-key="selectedIdentityKey"

    :product-summary="productSummary"

    :trend-rows="trendRows"

    :product-supplier-quotes="productSupplierQuotes"

    :trend-loading="trendLoading"

    :refreshing="workbenchRefreshing"

    :signal-overview="signalOverview"
    :supplier-overview="supplierOverview"
    :procurement-recommendations="procurementRecommendations"
    :plan-rows="planRows"
    :menu-text="menuForm.menuText"
    :menu-tables="menuForm.tables"
    :menu-diners="menuForm.diners"
    :menu-preferred-location="menuForm.preferredLocation"
    :menu-location-candidates="menuLocationCandidates"
    :ingredient-rows="ingredientRows"
    :parsed-menu-count="parsedMenuCount"
    :matched-plan-count="matchedPlanCount"
    :pending-plan-count="pendingPlanCount"
    :menu-total-cost-label="menuTotalCostLabel"
    :menu-loading="menuPlanLoading"
    :global-alert-rules="globalAlertRules"
    :settings-change-logs="settingsChangeLogs"
    :auth-role="authSession?.user.role || null"
    :auth-supplier-id="authSession?.user.supplier_id || null"
    :auth-display-name="authSession?.user.display_name || authSession?.user.username || null"
    @select-tab="enterWorkspace"
    @select-product="handleWorkbenchSelectProduct"
    @update-summary-liancai-filter="handleWorkbenchSummaryLiancaiFilter"
    @ensure-trend="ensureWorkbenchTrend"
    @update:menu-text="menuForm.menuText = $event"
    @update:menu-tables="menuForm.tables = $event"
    @update:menu-diners="menuForm.diners = $event"
    @update:menu-preferred-location="menuForm.preferredLocation = $event"
    @submit-menu="submitMenuPlan"
    @menu-view-market="handleMenuPlanViewMarket"
    @menu-fill-supplier-price="handleMenuPlanFillSupplierPrice"
    @menu-confirm-row="handleMenuPlanConfirmRow"
    @menu-fill-missing-quotes="handleMenuPlanFillMissingQuotes"
    @refresh="reloadAll"
    @open-supplier-backend="openSupplierBackend"
    @run-crawl="handleWorkbenchRunCrawl"
    @run-source-crawl="handleWorkbenchRunSourceCrawl"
    @update-crawl-schedule="handleWorkbenchUpdateCrawlSchedule"
    @update-source-config="handleWorkbenchUpdateSourceConfig"
    @update-source-strategy="handleWorkbenchUpdateSourceStrategy"
    @update-global-alert-rules="handleWorkbenchUpdateGlobalAlertRules"
  />

  <el-dialog v-model="imagePreviewVisible" :title="imagePreviewTitle || '图片预览'" width="min(92vw, 960px)">
    <div class="market-image-preview-shell">
      <img v-if="imagePreviewUrl" :src="imagePreviewUrl" :alt="imagePreviewTitle || ''" class="market-image-preview" />
    </div>
  </el-dialog>



</template>



<script setup lang="ts">

import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'

import {

  buildSnapshotProductSummary,
  clearAuthSession,
  dataSourceState,
  extractApiErrorDetail,
  fetchCurrentUser,
  fetchCrawlStatus,
  fetchLiancaiFacets,
  fetchLocationOptions,
  fetchLiancaiCategorySummary,
  fetchMarketSummary,

  fetchProcurementRecommendation,

  fetchGlobalAlertRules,
  fetchProductOptions,

  fetchProductSupplierQuotes,

  fetchProductSummary,

  fetchProductTrend,

  fetchSalesDecisionContent,

  fetchSignalsOverview,

  fetchSourceCoverage,

  fetchSupplierOverview,
  generateMenuPlan,
  readAuthSession,
  triggerCrawlRun,
  updateCrawlSchedule,
  updateGlobalAlertRules,
  updateSourceCoverage,
  updateSourceStrategy,
  writeAuthSession,
} from './api'
import type {
  AuthLoginResponse,
  CrawlStatusItem,
  LiancaiFacetResponse,
  LiancaiCategorySummaryItem,
  MarketSummaryItem,

  MenuPlanRow,

  ProcurementRecommendationItem,
  GlobalAlertRuleItem,
  SettingsChangeLogItem,

  ProductOptionItem,

  ProductTrendRow,

  SupplierQuoteCompareItem,

  SalesDemoContentResponse,

  SignalOverviewResponse,

  SourceCoverageItem,

  SupplierOverviewResponse,

} from './types'

import { useViewport } from './composables/useViewport'

import { buildMarketCategoryTabs, resolveMarketCategory } from './utils/marketCategories'
import {
  buildProductAlertHit,
  pickAlertRuleProductLabel,
  readProductAlertRules,
  upsertProductAlertRule,
  writeProductAlertRules,
} from './utils/alertRules'

const MarketSummaryPanel = defineAsyncComponent(() => import('./components/MarketSummaryPanel.vue'))
const MenuPlanPanel = defineAsyncComponent(() => import('./components/MenuPlanPanel.vue'))
const PcPriceWorkbench = defineAsyncComponent(() => import('./components/PcPriceWorkbench.vue'))
const ProductTrendPanel = defineAsyncComponent(() => import('./components/ProductTrendPanel.vue'))


const { isMobileViewport } = useViewport()
const isLegacyMobileLandingEnabled = true
const searchParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams()
const initialPathname = typeof window !== 'undefined' ? window.location.pathname : '/'

const initialTab = searchParams.get('tab')

const initialMode = searchParams.get('mode')

const MAIN_APP_PATH = '/'
const SUPPLIER_PLATFORM_PATH = '/supplier-backend'
const SUPPLIER_PORTAL_PATH = '/supplier-portal'
const MARKET_SUMMARY_INITIAL_LIMIT = 200
const MARKET_SUMMARY_BACKGROUND_LIMIT = 1000

const tabs = [
  { key: 'signals', label: '老板驾驶舱', code: 'SIG' },
  { key: 'summary', label: '汇总行情', code: 'SUM' },
  { key: 'trend', label: '单品趋势', code: 'TRD' },
  { key: 'alerts', label: '价格预警', code: 'ALT' },
  { key: 'menu', label: '菜单采购', code: 'BUY' },
] as const
const shouldRedirectToStandaloneSupplier = initialPathname !== SUPPLIER_PLATFORM_PATH && (initialMode === 'supplier' || initialTab === 'supplier')
const defaultTab = tabs.some((item) => item.key === initialTab)

  ? (initialTab as (typeof tabs)[number]['key'])

  : 'summary'

const viewMode = ref<'landing' | 'workspace'>(

  initialMode === 'workspace' || Boolean(initialTab)

    ? 'workspace'

    : 'landing',

)

const activeTab = ref<(typeof tabs)[number]['key']>(defaultTab)
const trendDeepLinkTarget = initialTab === 'trend' ? searchParams.get('product') || searchParams.get('identity_key') || searchParams.get('identityKey') || '' : ''
const trendDeepLinkLabel = initialTab === 'trend' ? searchParams.get('product_label') || searchParams.get('label') || '' : ''
const trendTestTargetLabels = ['三黄鸡 | 公斤', '一级豆油 | 公斤']
const provinces = ref<string[]>([])
const cities = ref<string[]>([])
const provinceCityMap = ref<Record<string, string[]>>({})
const marketRows = ref<MarketSummaryItem[]>([])
const liancaiCategorySummaryItems = ref<LiancaiCategorySummaryItem[]>([])
const liancaiFacetOptions = ref<LiancaiFacetResponse>({ keywords: [], brands: [] })
const sourceCoverageRows = ref<SourceCoverageItem[]>([])
const productOptions = ref<ProductOptionItem[]>([])
const selectedIdentityKey = ref('')
const selectedSiteName = ref('')
const selectedProductFallbackLabel = ref('')
const mobileAlertRuleDraft = ref({
  identityKey: '',
  productLabel: '',
  sourceName: '',
  sourceLabel: '',
  minPrice: 0,
  maxPrice: 0,
})
const showMobileAlertRuleForm = ref(false)
const mobileProductAlertRules = ref(readProductAlertRules())
if (mobileProductAlertRules.value[0]) {
  mobileAlertRuleDraft.value = {
    identityKey: mobileProductAlertRules.value[0].identityKey,
    productLabel: mobileProductAlertRules.value[0].productLabel,
    sourceName: mobileProductAlertRules.value[0].sourceName,
    sourceLabel: mobileProductAlertRules.value[0].sourceLabel,
    minPrice: mobileProductAlertRules.value[0].minPrice,
    maxPrice: mobileProductAlertRules.value[0].maxPrice,
  }
}
const productSummary = ref<Record<string, any> | null>(null)
const trendRows = ref<ProductTrendRow[]>([])
const productSupplierQuotes = ref<SupplierQuoteCompareItem[]>([])
const trendSiteOptions = ref<string[]>([])
const trendLoading = ref(false)
const trendMode = ref<'cross_market' | 'single_market'>('cross_market')
const ingredientRows = ref<Record<string, any>[]>([])

const planRows = ref<MenuPlanRow[]>([])

const procurementRecommendations = ref<ProcurementRecommendationItem[]>([])

const menuPlanLoading = ref(false)

const crawlStatus = ref<CrawlStatusItem | null>(null)

const signalOverview = ref<SignalOverviewResponse | null>(null)
const globalAlertRules = ref<GlobalAlertRuleItem[]>([])
const settingsChangeLogs = ref<SettingsChangeLogItem[]>(readSettingsChangeLogs())

const supplierOverview = ref<SupplierOverviewResponse | null>(null)

const demoContent = ref<SalesDemoContentResponse | null>(null)
const pageError = ref('')
const summaryLoading = ref(false)
const summaryBackfillLoading = ref(false)
const locationLoading = ref(false)
const coverageLoading = ref(false)

const liancaiCategorySummaryLoading = ref(false)

const productOptionsLoading = ref(false)
const workbenchRefreshing = ref(false)
const productOptionsContextKey = ref('')
const authSession = ref<AuthLoginResponse | null>(readAuthSession())
const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')
const imagePreviewTitle = ref('')
const showMobileHomeMore = ref(false)

const selectedProductTouched = ref(false)

let crawlStatusTimer: number | undefined
let productOptionsPromise: Promise<void> | null = null
let trendRequestSequence = 0
let summaryRequestSequence = 0
let suppressNextTrendWatch = false
let trendPrefetchContextKey = ''
const trendPrefetchPromises = new Map<string, Promise<void>>()
const SETTINGS_CHANGE_LOG_STORAGE_KEY = 'battel.settings-change-log.v1'

const activeMarketCategory = ref('全部')

const selectedCategorySourceName = ref('')

const filters = reactive({
  province: '',
  city: '',
  keyword: '',
  summarySourceName: '',
  liancaiTopCategory: '',
  liancaiSubcategory: '',
  liancaiKeyword: '',
  liancaiBrand: '',
})
const summaryLiancaiFilter = computed(() => ({
  source_name: filters.summarySourceName,
  liancai_top_category: filters.liancaiTopCategory,
  liancai_subcategory: filters.liancaiSubcategory,
  liancai_keyword: filters.liancaiKeyword,
  liancai_brand: filters.liancaiBrand,
}))

function resetSummaryFilters() {
  filters.summarySourceName = ''
  filters.liancaiTopCategory = ''
  filters.liancaiSubcategory = ''
  filters.liancaiKeyword = ''
  filters.liancaiBrand = ''
  selectedCategorySourceName.value = ''
  activeMarketCategory.value = '全部'
}
const menuForm = reactive({
  menuText: '',

  tables: 10,

  diners: 100,

  preferredLocation: '',

})

const parsedMenuCount = computed(() => menuForm.menuText.split('\n').map((item) => item.trim()).filter(Boolean).length)

const isMenuPlanRowConfirmed = (item: MenuPlanRow) => String(item.price_status || '').includes('已确认') || String(item.remarks || '').includes('采购已确认')

const matchedPlanCount = computed(() => planRows.value.filter((item) => item.price_status === '已匹配报价' || isMenuPlanRowConfirmed(item)).length)

const pendingPlanCount = computed(() => planRows.value.filter((item) => item.price_status !== '已匹配报价' && !isMenuPlanRowConfirmed(item)).length)

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

const selectedProductLabel = computed(() => {
  const current = productOptions.value.find((item) => item.price_identity_key === selectedIdentityKey.value)
  return current?.price_identity_label ?? selectedProductFallbackLabel.value
})
const mobileAlertProductOptions = computed(() => productOptions.value
  .map((item) => ({
    value: item.price_identity_key,
    label: item.price_identity_label,
  }))
  .filter((item) => item.value && item.label))
const mobileAlertSourceOptions = computed(() => {
  const options = new Set<string>()
  for (const row of trendRows.value) {
    const label = String(row.source_name || row.site_name || '').trim()
    if (label) options.add(label)
  }
  const fallback = String(productSummary.value?.current_lowest_site || '').trim()
  if (fallback) options.add(fallback)
  return Array.from(options)
})
const selectedLocationLabel = computed(() => filters.city || filters.province || '河南本地市场')
const latestSyncLabel = computed(() => {
  const latestSourceCapture = sourceCoverageRows.value
    .map((item) => item.latest_capture)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1)
  return formatBeijingDateTime(crawlStatus.value?.last_finished_at || latestSourceCapture, '等待同步', true)
})
const failedSourceCount = computed(() => sourceCoverageRows.value.filter((item) => (
  Number(item.failed_count || 0) > 0 || item.status === 'error' || item.last_failure
)).length)
const mobileActiveTab = computed(() => {
  if (activeTab.value === 'trend') return 'trend'
  if (activeTab.value === 'alerts') return 'alerts'

  if (activeTab.value === 'menu') return 'menu'

  return 'summary'
})

function syncMobileAlertDraftFromSelection() {
  const identityKey = mobileAlertRuleDraft.value.identityKey || selectedIdentityKey.value
  const productLabel = pickAlertRuleProductLabel(
    identityKey,
    productOptions.value,
    selectedProductLabel.value || mobileAlertRuleDraft.value.productLabel,
  )
  mobileAlertRuleDraft.value = {
    ...mobileAlertRuleDraft.value,
    identityKey,
    productLabel,
  }
}

function saveMobileAlertRule() {
  syncMobileAlertDraftFromSelection()
  if (!mobileAlertRuleDraft.value.identityKey || !mobileAlertRuleDraft.value.productLabel) return
  const normalizedSourceName = String(mobileAlertRuleDraft.value.sourceName || '').trim()
  const nextRules = upsertProductAlertRule(mobileProductAlertRules.value, {
    identityKey: mobileAlertRuleDraft.value.identityKey,
    productLabel: mobileAlertRuleDraft.value.productLabel,
    sourceName: normalizedSourceName,
    sourceLabel: normalizedSourceName,
    minPrice: mobileAlertRuleDraft.value.minPrice,
    maxPrice: mobileAlertRuleDraft.value.maxPrice,
    enabled: true,
  })
  mobileProductAlertRules.value = nextRules
  writeProductAlertRules(nextRules)
  ElMessage.success('价格预警规则已保存')
}

type MobileAlertActionRow = {
  identityKey?: string
  name: string
  market?: string
}

function resolveMobileAlertIdentityKey(item: MobileAlertActionRow) {
  if (item.identityKey) return item.identityKey
  const matchedOption = productOptions.value.find((option) => option.price_identity_label === item.name)
  if (matchedOption?.price_identity_key) return matchedOption.price_identity_key
  const matchedMarketRow = marketRows.value.find((row) => row.product_name === item.name)
  return matchedMarketRow?.price_identity_key || item.name
}

function openMobileAlertTrend(item: MobileAlertActionRow) {
  const identityKey = resolveMobileAlertIdentityKey(item)
  if (identityKey) handleSelectProduct(identityKey)
  enterWorkspace('trend')
}

function openMobileAlertSupplier(item: MobileAlertActionRow) {
  const identityKey = resolveMobileAlertIdentityKey(item)
  if (identityKey) handleSelectProduct(identityKey)
  ElMessage.success(`已带上 ${item.name}，去采购页找供应商报价`)
  enterWorkspace('menu')
}

function acknowledgeMobileAlert(item: MobileAlertActionRow) {
  ElMessage.success(`${item.name} 已标记处理`)
}
const mobileTabMeta = computed(() => {

  if (mobileActiveTab.value === 'trend') {

    return {

      title: '单品趋势',

      description: '先看当前价格区间，再判断跨市场还是单市场跟踪。',

    }

  }

  if (mobileActiveTab.value === 'alerts') {

    return {

      title: '价格预警',

      description: '处理异常波动，并给常采商品设置触发阈值。',

    }

  }

  if (mobileActiveTab.value === 'menu') {

    return {

      title: '采购表单',

      description: '把菜单、桌数和地区转成可执行的采购建议。',

    }

  }

  return {

    title: '汇总行情',

    description: '按分类、地区和关键词查看本地食材行情。',

  }

})

const hasLiveSummary = computed(() => marketRows.value.length > 0)
const summaryStatusText = computed(() => {
  const loaded = marketRows.value.length
  if (summaryLoading.value) {
    return loaded > 0 ? `首批已加载 ${loaded} 条，仍在整理中` : '行情加载中'
  }
  if (summaryBackfillLoading.value) {
    return `已加载 ${loaded} 条，后台继续补齐中`
  }
  return loaded > 0 ? `共 ${loaded} 条真实报价` : '暂无报价'
})
const showBlockingError = computed(() => dataSourceState.mode === 'error' && !hasLiveSummary.value)

const demoHero = computed(() => ({
  eyebrow: demoContent.value?.hero?.eyebrow || 'REAL MARKET SIGNALS',

  title: demoContent.value?.hero?.title || '真实行情经营信号',

  description: demoContent.value?.hero?.description || '先看真实价格、风险和机会，再进入报价与采购承接。',

  primaryCta: demoContent.value?.hero?.primary_cta || '进入老板驾驶舱',
}))


const marketAveragePriceLabel = computed(() => {

  const values = marketRows.value

    .map((item) => Number(item.average_price))

    .filter((value) => !Number.isNaN(value) && value > 0)

  if (!values.length) return '暂无'

  const average = values.reduce((sum, value) => sum + value, 0) / values.length

  return average.toFixed(2)

})



const homeHeroStats = computed(() => [

  {

    label: '待处理预警',

    value: `${mobileAlertBadge.value || 0}`,

    detail: mobileAlertBadge.value ? '建议先看异常价格' : '当前没有紧急项',

  },

  {

    label: '低价机会',

    value: `${signalOverview.value?.top_opportunities?.length || mobileSpotlightRows.value.length || 0}`,

    detail: lowestPriceSignal.value,

  },

  {

    label: '最近同步',

    value: latestSyncLabel.value,

    detail: crawlResultLabel.value,

  },

])

const mobileDecisionMetrics = computed(() => [
  { label: '待处理', value: String(mobileAlertBadge.value || 0) },
  { label: '机会', value: String(signalOverview.value?.top_opportunities?.length || 0) },
  { label: '来源', value: String(sourceCoverageRows.value.length || 0) },
])

const mobileTrustCards = computed(() => [
  {
    label: '最近同步',
    value: latestSyncLabel.value,
    detail: summaryStatusText.value,
  },
  {
    label: '来源覆盖',
    value: `${sourceCoverageRows.value.length || 0} 个`,
    detail: '系统持续监控这些市场和平台',
  },
  {
    label: '异常来源',
    value: String(failedSourceCount.value),
    detail: failedSourceCount.value ? '建议先复核同步状态' : '当前没有失败来源',
  },
])



const homePriorityItems = computed(() => {

  const opportunities = (signalOverview.value?.top_opportunities || []).slice(0, 2).map((item) => ({

    title: item.product_name,

    badge: formatRecommendedAction(item.recommended_action),

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

const landingTodayCards = computed(() => [
  {
    label: '今日异常',
    value: mobileAlertBadge.value ? `${mobileAlertBadge.value} 条待处理` : '当前无紧急异常',
  },
  {
    label: '今日机会',
    value: signalOverview.value?.top_opportunities?.length
      ? `${signalOverview.value.top_opportunities.length} 条值得先看`
      : '等待系统识别机会',
  },
  {
    label: '待办动作',
    value: procurementRecommendations.value.length || planRows.value.length
      ? `${procurementRecommendations.value.length || planRows.value.length} 条可执行`
      : '先同步后再生成动作',
  },
])

const landingPriorityCards = computed(() => homePriorityItems.value.map((item, index) => ({
  kicker: index === 0 ? '今日机会' : item.tone === 'warn' ? '今日异常' : '待办动作',
  title: item.title,
  detail: item.summary,
  meta: item.meta,
  action: item.tone === 'warn' ? '去处理' : item.tone === 'good' ? '去看机会' : '去查看',
  code: item.tone === 'warn' ? 'ALERT' : item.tone === 'good' ? 'OPP' : 'TODO',
  tone: item.tone === 'warn' ? 'suite-backend' : 'suite-buyer',
  target: item.tone === 'warn' ? 'alerts' : item.tone === 'good' ? 'signals' : 'summary',
})))

const landingTrustCards = computed(() => [
  {
    label: '最新同步',
    value: latestSyncLabel.value,
    detail: '最近一次可用行情时间',
  },
  {
    label: '来源覆盖',
    value: `${sourceCoverageRows.value.length || 0} 个`,
    detail: failedSourceCount.value ? `${failedSourceCount.value} 个来源待复核` : '当前覆盖状态稳定',
  },
  {
    label: '建议依据',
    value: signalOverview.value?.headline || '真实行情 + 供应报价',
    detail: '异常、机会和建议均来自现有接口返回',
  },
])



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



type HomeSuiteKey = 'buyer' | 'supplier'


const homeSuiteCards = computed<Array<{

  key: HomeSuiteKey

  kicker: string

  code: string

  title: string

  detail: string

  features: string[]

  action: string

  tone: string

}>>(() => [

  {
    key: 'buyer',
    kicker: '采购平台',
    code: 'BUYER',
    title: '我是采购',
    detail: '查看市场行情、单品趋势、价格预警和采购建议。',
    features: ['行情总览', '价格预警', '采购建议'],
    action: '进入采购平台',
    tone: 'suite-buyer',
  },
  {
    key: 'supplier',
    kicker: '供应平台',
    code: 'SUPPLIER',
    title: '我是供应',
    detail: '维护供应商管理、商品报价、批量导入、历史和结算。',
    features: ['供应商管理', '报价录入', '结算对账'],
    action: '进入供应平台',
    tone: 'suite-backend',
  },
])


const mobileQuickCategories = computed(() => {
  if (liancaiCategorySummaryItems.value.length) {

    const grouped = new Map<string, number>()
    liancaiCategorySummaryItems.value.forEach((item) => {
      const key = String(item.liancai_top_category || '').trim() || '全部'
      if (key === '未映射' || key === '未归类') return
      grouped.set(key, (grouped.get(key) || 0) + Number(item.product_count || 0))
    })
    const rows = Array.from(grouped.entries())

      .map(([label, count]) => ({ key: label, label, count }))

      .sort((left, right) => right.count - left.count)

    return [{ key: '全部', label: '全部', count: marketRows.value.length || rows.reduce((sum, item) => sum + item.count, 0) }, ...rows]

  }

  return buildMarketCategoryTabs(marketRows.value)

})

const MOBILE_HOME_QUICK_CATEGORY_LIMIT = 8

const mobileQuickCategoryRows = computed(() =>
  mobileQuickCategories.value.filter((item) => item.key !== '全部'),
)

const displayedMobileQuickCategoryRows = computed(() =>
  mobileQuickCategoryRows.value.slice(0, MOBILE_HOME_QUICK_CATEGORY_LIMIT),
)

const displayedMobileQuickCategories = computed(() => {
  const allCategory = mobileQuickCategories.value.find((item) => item.key === '全部')
  return allCategory ? [allCategory, ...displayedMobileQuickCategoryRows.value] : displayedMobileQuickCategoryRows.value
})

const mobileQuickCategoryCount = computed(() => mobileQuickCategoryRows.value.length)

const displayedMobileQuickCategoryCount = computed(() => displayedMobileQuickCategoryRows.value.length)

const hiddenMobileQuickCategoryCount = computed(() =>
  Math.max(0, mobileQuickCategoryCount.value - displayedMobileQuickCategoryCount.value),
)

const mobileQuickSubcategories = computed(() => {

  if (!liancaiCategorySummaryItems.value.length) {

    return []

  }

  return liancaiCategorySummaryItems.value
    .filter((item) => item.liancai_subcategory && item.liancai_subcategory !== '全部' && item.liancai_subcategory !== '未映射' && item.liancai_subcategory !== '未归类')
    .map((item) => ({

      key: item.liancai_subcategory,

      label: item.liancai_subcategory,

      count: item.product_count,

      parent: item.liancai_top_category,

    }))

})

const mobileCategoryTableRows = computed(() => {

  if (liancaiCategorySummaryItems.value.length) {

    return liancaiCategorySummaryItems.value

      .map((item, index) => ({

        category: String(item.liancai_top_category || '未映射'),

        subcategory: String(item.liancai_subcategory || '未映射'),

        count: Number(item.product_count || 0),

        key: `${String(item.liancai_top_category || '未映射')}-${String(item.liancai_subcategory || '未映射')}-${index}`,

      }))

  }

  return mobileQuickCategories.value

    .filter((item) => item.key !== '全部')

    .map((item, index) => ({

      category: item.label,

      subcategory: '全部',

      count: item.count,

      key: `${item.label}-全部-${index}`,

    }))

})

const MOBILE_HOME_CATEGORY_PREVIEW_LIMIT = 6

const displayedMobileCategoryTableRows = computed(() =>
  mobileCategoryTableRows.value.slice(0, MOBILE_HOME_CATEGORY_PREVIEW_LIMIT),
)

const hiddenMobileCategoryCount = computed(() =>
  Math.max(0, mobileCategoryTableRows.value.length - displayedMobileCategoryTableRows.value.length),
)

const totalCategorySourceCount = computed(() => mobileCategoryTableRows.value.reduce((sum, item) => sum + item.count, 0))
function normalizeLiancaiSourceLabel(value?: string | null) {
  const label = String(value || '').trim()
  if (!label) return ''
  return label.includes('莲菜网') ? '莲菜网' : label
}

function formatMobileAlertMarketLabel(value?: string | null) {
  const rawLabel = String(value || '').trim()
  if (!rawLabel) return selectedLocationLabel.value
  const [firstPart] = rawLabel.split(/[|｜/]/).map((part) => part.trim()).filter(Boolean)
  const normalized = normalizeLiancaiSourceLabel(firstPart || rawLabel)
  return normalized.length > 14 ? `${normalized.slice(0, 14)}…` : normalized
}
const categorySourceOptions = computed(() => {
  const optionMap = new Map<string, { label: string; value: string; count: number }>()
  ;['莲菜网', 'PFSC', 'Chinaprice', '万邦国际'].forEach((value) => {
    optionMap.set(value, { label: value, value, count: 0 })
  })
  sourceCoverageRows.value.forEach((item) => {
    const value = normalizeLiancaiSourceLabel(item.source_name || item.configured_name)
    if (!value) return
    const next = optionMap.get(value) || {
      label: value,
      value,
      count: 0,
    }
    next.count += Number(item.source_item_count || item.comparable_item_count || item.product_key_count || item.price_record_count || 0)
    optionMap.set(value, next)
  })
  return Array.from(optionMap.values())
})

const displayedCategorySourceOptions = computed(() => categorySourceOptions.value.slice(0, 6))

const selectedCategorySourceLabel = computed(() => {

  if (!selectedCategorySourceName.value) return '全部来源'

  return categorySourceOptions.value.find((item) => item.value === selectedCategorySourceName.value)?.label || selectedCategorySourceName.value

})

const categorySourceTotalCount = computed(() => mobileQuickCategories.value.reduce((sum, item) => item.key === '全部' ? sum : sum + item.count, 0))

const mobileLeadAction = computed(() => homePriorityItems.value[0] || null)

const mobileLocalShortcuts = computed(() => {

  const primaryCategory = mobileQuickCategories.value.find((item) => item.key !== '全部') || mobileQuickCategories.value[0]

  const primarySubcategory = mobileQuickSubcategories.value[0]

  const primaryMarket = mobileSourceMarketCards.value[0]

  return [

    {

      key: 'category' as const,

      label: '常看分类',

      title: primarySubcategory?.label || primaryCategory?.label || '全部分类',

      detail: primarySubcategory

        ? `${primarySubcategory.parent} · ${primarySubcategory.count} 款可直接比价`

        : primaryCategory

          ? `${primaryCategory.count} 款可直接比价`

          : '先进入行情页同步本地分类',

    },

    {

      key: 'market' as const,

      label: '本地市场',

      title: primaryMarket?.title || selectedLocationLabel.value,

      detail: primaryMarket?.detail || '先看今天已接入的本地市场来源',

    },

    {

      key: 'product' as const,

      label: '热门单品',

      title: primaryMobileSpotlight.value.title,

      detail: primaryMobileSpotlight.value.detail,

    },

  ]

})

const mobileRecentEntries = computed(() => {

  const lastTabLabel = tabs.find((item) => item.key === mobileRecentState.value.workspaceTab)?.label || '汇总行情'

  const categoryTitle = mobileRecentState.value.categoryLabel || mobileQuickCategories.value.find((item) => item.key !== '全部')?.label || '全部分类'

  const productTitle = mobileRecentState.value.productTitle || primaryMobileSpotlight.value.title

  return [

    {

      key: 'workspace' as const,

      label: '最近工作区',

      title: lastTabLabel,

      detail: `${selectedLocationLabel.value} · 接着回到上次入口`,

    },

    {

      key: 'category' as const,

      label: '最近分类',

      title: categoryTitle,

      detail: '继续查看上次常看的本地分类',

    },

    {

      key: 'product' as const,

      label: '最近单品',

      title: productTitle,

      detail: mobileRecentState.value.productIdentityKey ? '继续看走势和价差' : primaryMobileSpotlight.value.detail,

    },

  ]

})

const mobileSourceMarketCards = computed(() => {

  const rows = sourceCoverageRows.value.slice(0, 3).map((item) => ({

    title: item.configured_name || item.source_name || '未命名市场',

    status: item.status || '待同步',

    detail: item.source_tier || item.market_scope || item.market_category || item.channel || '本地市场来源',

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

const preferredMobileMarketRows = computed(() => {

  const scoredRows = marketRows.value

    .map((item, index) => ({

      item,

      index,

      score: scoreMobileFoodRow(item),

    }))

    .filter((row) => row.score > 0)

    .sort((left, right) => right.score - left.score || left.index - right.index)

    .map((row) => row.item)

  return scoredRows.length ? scoredRows : marketRows.value

})

const mobileSpotlightRows = computed(() => {

  const rows = preferredMobileMarketRows.value.slice(0, 4).map((item) => ({

    identityKey: item.price_identity_key || item.product_name,

    title: item.product_name,

    category: resolveMarketCategory(item),

    market: item.lowest_price_site || item.region_label || '本地市场',

    thumb: resolveMobileThumbClass(item.product_name, resolveMarketCategory(item)),

    price: formatMetricValue(item.average_price),

    unit: item.price_unit_basis || '元/公斤',

    lowest: formatMetricValue(item.lowest_price),

    spread: formatMetricSpread(item.lowest_price, item.highest_price),

    changeLabel: buildMobileChangeLabel(item),

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

      thumb: 'leaf',

      price: '-',

      unit: '元/公斤',

      lowest: '-',

      spread: '价差待同步',

      changeLabel: '同步中',

    },

  ]

})

const mobileAlertRows = computed(() => {
  const configuredRows = mobileProductAlertRules.value
    .map((rule, index) => {
      const hit = buildProductAlertHit(
        rule,
        marketRows.value,
        rule.identityKey === selectedIdentityKey.value ? trendRows.value : [],
      )
      if (!hit) return null
      return {
        identityKey: rule.identityKey,
        name: hit.productLabel,
        market: formatMobileAlertMarketLabel(hit.market),
        current: `${formatMetricValue(hit.currentPrice)} 元`,
        rule: hit.rule,
        state: hit.triggered ? '待处理' : '观察中',
        time: formatMobileAlertTime(index),
        tone: hit.tone,
        thumb: resolveMobileThumbClass(hit.productLabel, ''),
        imageUrl: resolveMobileAlertImageUrl(rule.identityKey, hit.productLabel),
      }
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item))
  if (configuredRows.length) return configuredRows
  const marketAlertRows = preferredMobileMarketRows.value
    .map((item, index) => {

      const lowValue = Number(item.lowest_price)

      const highValue = Number(item.highest_price)

      const spreadRatio = lowValue > 0 && !Number.isNaN(highValue) ? (highValue - lowValue) / lowValue : 0

      return {

        identityKey: item.price_identity_key || item.product_name,

        name: item.product_name,

        market: formatMobileAlertMarketLabel(item.lowest_price_site || item.region_label || selectedLocationLabel.value),

        current: `${formatMetricValue(item.average_price)} ${item.price_unit_basis || '元/公斤'}`,

        rule: spreadRatio >= 0.12 ? `价差 ${(spreadRatio * 100).toFixed(1)}%，超过预警阈值` : '价格接近常规阈值，建议继续观察',

        state: spreadRatio >= 0.12 ? '待处理' : index % 2 ? '已确认' : '观察中',

        time: formatMobileAlertTime(index),

        tone: spreadRatio >= 0.18 ? 'up' : spreadRatio >= 0.08 ? 'warn' : 'down',

        thumb: resolveMobileThumbClass(item.product_name, resolveMarketCategory(item)),

        imageUrl: resolveMobileAlertImageUrl(item.price_identity_key || item.product_name, item.product_name),

      }

    })

    .filter((item) => item.name)

    .slice(0, 4)

  if (marketAlertRows.length) return marketAlertRows

  const riskRows = (signalOverview.value?.top_risks || []).slice(0, 4).map((item, index) => ({

    identityKey: item.product_name,

    name: item.product_name,

    market: formatMobileAlertMarketLabel(item.recommended_market || item.recommended_site || selectedLocationLabel.value),

    current: item.trend_label || '价格波动',

    rule: item.reason_summary || formatRecommendedAction(item.recommended_action, '触发真实行情风险信号'),

    state: index % 3 === 1 ? '已确认' : index % 3 === 2 ? '观察中' : '待处理',

    time: formatMobileAlertTime(index),

    tone: item.trend_label === '下降' ? 'down' : item.trend_label === '上涨' ? 'up' : 'warn',

    thumb: resolveMobileThumbClass(item.product_name, ''),

    imageUrl: resolveMobileAlertImageUrl(item.product_name, item.product_name),

  }))

  if (riskRows.length) return riskRows

  return []

})

const mobileAlertBadge = computed(() => {

  const explicitCount = Number(signalOverview.value?.alert_count || 0)

  return explicitCount || mobileAlertRows.value.filter((item) => item.state === '待处理').length || mobileAlertRows.value.length

})

const mobileAlertKpis = computed(() => {

  const pending = mobileAlertRows.value.filter((item) => item.state === '待处理').length

  const up = mobileAlertRows.value.filter((item) => item.tone === 'up').length

  const down = mobileAlertRows.value.filter((item) => item.tone === 'down').length

  const warn = mobileAlertRows.value.filter((item) => item.tone === 'warn').length

  return [

    { label: '待处理', value: String(pending || mobileAlertBadge.value), detail: '个商品', tone: 'pending' },

    { label: '上涨预警', value: String(up), detail: '个商品', tone: 'up' },

    { label: '下跌预警', value: String(down), detail: '个商品', tone: 'down' },

    { label: '波动预警', value: String(warn), detail: '个商品', tone: 'warn' },

  ]

})

const mobileAlertHeroText = computed(() => {
  const pending = mobileAlertRows.value.filter((item) => item.state === '待处理').length
  if (pending > 0) return `先处理 ${pending} 个待处理商品，再决定是否下单。`
  if (mobileAlertRows.value.length > 0) return '暂无急单，先观察波动明显的商品。'
  return '还没有触发异常，系统会继续盯价格线。'
})

const mobileAlertSummaryPills = computed(() => {
  const pending = mobileAlertRows.value.filter((item) => item.state === '待处理').length
  const up = mobileAlertRows.value.filter((item) => item.tone === 'up').length
  const down = mobileAlertRows.value.filter((item) => item.tone === 'down').length
  return [
    { label: '待处理', value: String(pending || mobileAlertBadge.value), tone: 'pending' },
    { label: '上涨', value: String(up), tone: 'up' },
    { label: '下跌', value: String(down), tone: 'down' },
  ]
})

const mobileAlertThresholdLabel = computed(() => {
  const lower = Number(mobileAlertRuleDraft.value.minPrice || 0)
  const upper = Number(mobileAlertRuleDraft.value.maxPrice || 0)
  if (lower > 0 && upper > 0) return `${lower.toFixed(2)} - ${upper.toFixed(2)}`
  if (upper > 0) return `>= ${upper.toFixed(2)}`
  if (lower > 0) return `<= ${lower.toFixed(2)}`
  return '未设置'
})
const primaryMobileSpotlight = computed(() => {

  const firstRow = mobileSpotlightRows.value[0]

  if (firstRow) {

    return {

      identityKey: firstRow.identityKey,

      title: firstRow.title,

      detail: `${firstRow.market} · ${firstRow.spread}`,

    }

  }

  return {

    identityKey: 'placeholder',

    title: '选择一个热门食材',

    detail: '先看跨市场走势，再决定今天是否锁价。',

  }

})



const SUMMARY_CACHE_KEY = 'battel.market-summary.cache.v4'
const PRODUCT_OPTIONS_CACHE_KEY = 'battel.product-options.cache.v3'
const PRODUCT_SUMMARY_CACHE_KEY = 'battel.product-summary.cache.v3'
const PRODUCT_TREND_CACHE_KEY = 'battel.product-trend.cache.v3'
const MOBILE_RECENT_STATE_KEY = 'battel.mobile-recent.v1'

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
    source_name: filters.summarySourceName || undefined,
    liancai_top_category: filters.liancaiTopCategory || undefined,
    liancai_subcategory: filters.liancaiSubcategory || undefined,
    liancai_keyword: filters.liancaiKeyword || undefined,
    liancai_brand: filters.liancaiBrand || undefined,
  }
}


function formatMetricValue(value?: number | string | null) {

  if (value == null || value === '') {

    return '-'

  }

  const normalizedValue = Number(value)

  return Number.isNaN(normalizedValue) ? String(value) : normalizedValue.toFixed(2)

}

function formatRecommendedAction(value?: string | null, fallback = '先复核价格来源') {
  const raw = String(value || '').trim()
  if (!raw) return fallback
  const normalized = raw.toLowerCase()
  const actionMap: Record<string, string> = {
    switch_market: '切换低价市场',
    quote_supplier: '联系供应商报价',
    request_supplier_quote: '联系供应商报价',
    contact_supplier: '联系供应商确认',
    watch: '先观察',
    monitor: '继续观察',
    buy_now: '尽快采购',
    purchase_now: '尽快采购',
    adjust_plan: '调整采购计划',
    review_source: '复核价格来源',
  }
  return actionMap[normalized] || raw.replace(/_/g, ' ')
}



function formatMetricSpread(lowest?: number | string | null, highest?: number | string | null) {

  const lowValue = Number(lowest)

  const highValue = Number(highest)

  if (Number.isNaN(lowValue) || Number.isNaN(highValue)) {

    return '价差待同步'

  }

  return `价差 ${Math.max(highValue - lowValue, 0).toFixed(2)}`

}



function buildMobileChangeLabel(item: MarketSummaryItem) {

  const lowValue = Number(item.lowest_price)

  const highValue = Number(item.highest_price)

  if (Number.isNaN(lowValue) || Number.isNaN(highValue) || lowValue <= 0) {

    return '同步中'

  }

  const spreadRatio = (highValue - lowValue) / lowValue

  if (spreadRatio >= 0.18) return '波动大'

  if (spreadRatio >= 0.08) return '需关注'

  return '较稳定'

}



function resolveMobileThumbClass(name?: string | null, category?: string | null) {
  const text = `${name || ''}${category || ''}`
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



function scoreMobileFoodRow(item: MarketSummaryItem) {

  const category = resolveMarketCategory(item)

  const text = [

    item.product_name,

    item.liancai_top_category,

    item.liancai_subcategory,

    category,

  ].join(' ')

  const normalizedText = text.replace(/\s+/g, '')

  if (/垃圾桶|收纳箱|包装|餐具|清洁|用品|耗材|纸巾|手套|托盘|保鲜膜|垃圾袋/.test(normalizedText)) {

    return 0

  }

  let score = 0

  if (/蔬菜|叶菜|根茎|瓜果|菌菇|豆制品|水产|鲜冻水产|禽蛋|肉禽|猪肉|牛羊肉|水果/.test(normalizedText)) score += 80

  if (/白菜|西兰花|菠菜|黄瓜|土豆|番茄|鸡蛋|鲜鱼|带鱼|虾|牛肉|猪肉|鸡肉|豆腐|蘑菇/.test(normalizedText)) score += 60

  if (Number(item.average_price) > 0) score += 8

  if (Number(item.site_count || item.market_count || 0) > 1) score += 6

  if ((item.product_name || '').length <= 14) score += 4

  return score

}



function formatMobileAlertTime(index: number) {

  const baseHour = 9

  const minute = Math.max(0, 12 - index * 17)

  return `${String(baseHour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`

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



function buildContextKey(params: { province?: string; city?: string; source_name?: string; liancai_top_category?: string; liancai_subcategory?: string; liancai_keyword?: string; liancai_brand?: string }) {
  return JSON.stringify({
    province: params.province ?? '',
    city: params.city ?? '',
    source_name: params.source_name ?? '',
    liancai_top_category: params.liancai_top_category ?? '',
    liancai_subcategory: params.liancai_subcategory ?? '',
    liancai_keyword: params.liancai_keyword ?? '',
    liancai_brand: params.liancai_brand ?? '',
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


function normalizeIdentityCacheKey(value: string) {
  return String(value || '')
    .trim()
    .replace(/[\s*·•/]+/g, '')
}

function resolveCanonicalIdentityKey(identityKey: string) {
  const raw = String(identityKey || '').trim()
  if (!raw) return ''
  const normalized = normalizeIdentityCacheKey(raw)
  const optionMatch = productOptions.value.find((item) => normalizeIdentityCacheKey(item.price_identity_key) === normalized)
  return optionMatch?.price_identity_key || raw
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

if (typeof window !== 'undefined') {
  try {
    window.localStorage.removeItem(PRODUCT_SUMMARY_CACHE_KEY)
    window.localStorage.removeItem(PRODUCT_TREND_CACHE_KEY)
  } catch {
    // Ignore local cache cleanup failures.
  }
}



type MobileRecentState = {

  workspaceTab?: 'summary' | 'trend'

  categoryKey?: string

  categoryLabel?: string

  productIdentityKey?: string

  productTitle?: string

}



const mobileRecentState = ref<MobileRecentState>(readMobileRecentState())



function readMobileRecentState(): MobileRecentState {

  if (typeof window === 'undefined') {

    return {}

  }

  try {

    const raw = window.localStorage.getItem(MOBILE_RECENT_STATE_KEY)

    if (!raw) {

      return {}

    }

    const parsed = JSON.parse(raw)

    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {

      return {}

    }

    return parsed as MobileRecentState

  } catch {

    return {}

  }

}



function writeMobileRecentState(partial: Partial<MobileRecentState>) {

  mobileRecentState.value = {

    ...mobileRecentState.value,

    ...partial,

  }

  if (typeof window === 'undefined') return

  try {

    window.localStorage.setItem(MOBILE_RECENT_STATE_KEY, JSON.stringify(mobileRecentState.value))

  } catch {

    // Ignore storage failures and keep the in-memory recent state.

  }

}



function readSummaryCache(params: { province?: string; city?: string; source_name?: string; liancai_top_category?: string; liancai_subcategory?: string; liancai_keyword?: string; liancai_brand?: string }) {
  const cacheKey = buildContextKey(params)
  const cached = readLocalCache<MarketSummaryItem[]>(SUMMARY_CACHE_KEY, cacheKey)
  if (!Array.isArray(cached)) return null
  const filtered = filterProductMarketSummaryRows(cached)
  return filtered.length || !cached.length ? filtered : cached
}

function writeSummaryCache(params: { province?: string; city?: string; source_name?: string; liancai_top_category?: string; liancai_subcategory?: string; liancai_keyword?: string; liancai_brand?: string }, rows: MarketSummaryItem[]) {
  const filtered = filterProductMarketSummaryRows(rows)
  writeLocalCache(SUMMARY_CACHE_KEY, buildContextKey(params), filtered.length || !rows.length ? filtered : rows)
}

const NON_PRODUCT_MARKET_TEXT_PATTERN = /影响|调整|建议|采购|预警|趋势|来源动态|老板|驾驶舱|复制|copy|环比|同比|变化率|增长率|下降率|增幅|降幅|涨跌幅|增速|指数|指标|存栏|出栏|产量|销量|销售量|成交量|进口量|出口量|库存|开工率|利用率|均价|平均价|监测情况|价格监测|市场价格|价格表现|市场表现|走势分析|基本概况|概况|热点|话题|原因|情况|调查|波动|下降|上涨|持平|回落|反弹|上市量|货量|产区|包装成本|消费需求|节日|季节|动力煤|煤|线材|螺纹钢|钢材|热轧|中厚板|铜|铝|氧化铝|甲醇|纯碱|烧碱|合成氨|水泥|玻璃|原油|石油|汽油|柴油|化工|工业|电解铜|铝锭|豆粕|叶面肥|肥料|化肥|复合肥|农药|杀菌剂|杀虫剂|除草剂|助剂|农资|垃圾桶|收纳箱|包装|餐具|清洁|用品|耗材|纸巾|抽纸|餐巾纸|手套|托盘|保鲜膜|垃圾袋|易耗|固体酒精|火碱|锅|煎锅|不粘锅|酒水饮料|饮用水|矿物质水|纯净水|天然水|矿泉水|饮料/i
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

function filterProductMarketSummaryRows(rows: MarketSummaryItem[]) {
  return (rows || []).filter(isProductMarketSummaryRow)
}

function simplifySummaryProductName(value?: string | null) {
  return String(value || '')
    .replace(/\s+/g, '')
    .replace(/[|｜].*$/, '')
    .replace(/净菜\d+斤/g, '')
    .replace(/\d+斤/g, '')
    .replace(/原包|整包|毛菜|本地|精品|普通|一级|二级|三级|红皮|黄皮|黄心|黑皮|吊瓜|地瓜|圆片|片|条|丝|丁|段/g, '')
    .trim()
    .toLowerCase()
}

function fillSummaryRowImageUrls(rows: MarketSummaryItem[], options: ProductOptionItem[]) {
  if (!rows.length || !options.length) return rows
  const imageByIdentity = new Map<string, string>()
  const imageByName = new Map<string, string>()
  const optionImages = options
    .map((option) => ({
      label: simplifySummaryProductName(option.price_identity_label),
      imageUrl: String(option.image_url || '').trim(),
    }))
    .filter((item) => item.label && item.imageUrl)
  for (const option of options) {
    const imageUrl = String(option.image_url || '').trim()
    if (!imageUrl) continue
    const identityKey = String(option.price_identity_key || '').trim()
    const label = simplifySummaryProductName(option.price_identity_label)
    if (identityKey && !imageByIdentity.has(identityKey)) {
      imageByIdentity.set(identityKey, imageUrl)
    }
    if (label && !imageByName.has(label)) {
      imageByName.set(label, imageUrl)
    }
  }
  return rows.map((row) => {
    if (String(row.image_url || '').trim()) return row
    const identityKey = String(row.price_identity_key || '').trim()
    const productName = simplifySummaryProductName(row.product_name)
    const fuzzyMatch = productName
      ? optionImages.find((item) => item.label.includes(productName) || productName.includes(item.label))
      : null
    const fallbackImage =
      (identityKey && imageByIdentity.get(identityKey))
      || imageByName.get(productName)
      || fuzzyMatch?.imageUrl
      || ''
    return fallbackImage ? { ...row, image_url: fallbackImage } : row
  })
}

function resolveMobileAlertImageUrl(identityKey?: string, productName?: string) {
  const normalizedIdentityKey = String(identityKey || '').trim()
  if (normalizedIdentityKey) {
    const matchedSummaryRow = marketRows.value.find((row) => String(row.price_identity_key || '').trim() === normalizedIdentityKey)
    if (String(matchedSummaryRow?.image_url || '').trim()) return String(matchedSummaryRow?.image_url || '').trim()
    const matchedProductOption = productOptions.value.find((item) => String(item.price_identity_key || '').trim() === normalizedIdentityKey)
    if (String(matchedProductOption?.image_url || '').trim()) return String(matchedProductOption?.image_url || '').trim()
  }
  const normalizedProductName = simplifySummaryProductName(productName)
  if (!normalizedProductName) return ''
  const matchedSummaryName = marketRows.value.find((row) => simplifySummaryProductName(row.product_name) === normalizedProductName)
  if (String(matchedSummaryName?.image_url || '').trim()) return String(matchedSummaryName?.image_url || '').trim()
  const matchedOptionByName = productOptions.value.find((item) => {
    const optionName = simplifySummaryProductName(item.price_identity_label)
    return optionName === normalizedProductName || optionName.includes(normalizedProductName) || normalizedProductName.includes(optionName)
  })
  return String(matchedOptionByName?.image_url || '').trim()
}

function openImagePreview(url?: string | null, title = '') {
  const normalizedUrl = String(url || '').trim()
  if (!normalizedUrl) return
  imagePreviewUrl.value = normalizedUrl
  imagePreviewTitle.value = String(title || '').trim()
  imagePreviewVisible.value = true
}

function filterSummaryRowsByLiancaiCategory(
  rows: MarketSummaryItem[],
  params: { source_name?: string; liancai_top_category?: string; liancai_subcategory?: string; liancai_keyword?: string; liancai_brand?: string },
) {
  const sourceName = String(params.source_name || '').trim()
  const topCategory = String(params.liancai_top_category || '').trim()
  const subcategory = String(params.liancai_subcategory || '').trim()
  const keyword = String(params.liancai_keyword || '').trim()
  const brand = String(params.liancai_brand || '').trim()
  const topAliases: Record<string, string[]> = {
    干调类: ['干调类', '调味品', '调味料', '调味品酱料类', '干货调料', '干货类', '香辛料'],
    调味品: ['调味品', '干调类', '调味料', '调味品酱料类', '干货调料', '香辛料'],
    米面粮油: ['米面粮油', '粮油米面', '粮油类', '主食类'],
    蔬菜类: ['蔬菜类', '蔬菜', '净菜类'],
    肉禽蛋类: ['肉禽蛋类', '鲜猪肉', '鲜禽类', '禽蛋类', '牛羊肉'],
    水产类: ['水产类', '鲜活水产', '水产', '海鲜水产'],
  }
  const matchesCategory = (actual: string, expected: string) => {
    if (!expected) return true
    if (actual === expected) return true
    const aliases = topAliases[expected] || []
    return aliases.some((alias) => actual === alias || actual.includes(alias) || alias.includes(actual))
  }
  return rows.filter((row) => {
    const rowTopCategory = String(row.liancai_top_category || '').trim()
    const rowSubcategory = String(row.liancai_subcategory || '').trim()
    const rowKeyword = String(row.liancai_keyword || '').trim()
    const rowBrand = String(row.liancai_brand_name || '').trim()
    if (sourceName) {
      const sourceText = [row.source_names, row.source_display_names, row.lowest_price_site, row.highest_price_site]
        .map((value) => String(value || '').trim())
        .filter(Boolean)
        .join(' ')
      if (!sourceText.includes(sourceName) && !(sourceName.includes('莲菜网') && sourceText.includes('莲菜网'))) return false
    }
    if (topCategory && !matchesCategory(rowTopCategory, topCategory)) return false
    if (subcategory && rowSubcategory !== subcategory) return false
    if (keyword && rowKeyword !== keyword && !String(row.product_name || '').includes(keyword)) return false
    if (brand && rowBrand !== brand && !String(row.product_name || '').includes(brand)) return false
    return true
  })
}

function hasLiancaiSummaryFilter(params: { source_name?: string; liancai_top_category?: string; liancai_subcategory?: string; liancai_keyword?: string; liancai_brand?: string }) {
  return Boolean(
    String(params.source_name || '').trim()
    || String(params.liancai_top_category || '').trim()
    || String(params.liancai_subcategory || '').trim()
    || String(params.liancai_keyword || '').trim()
    || String(params.liancai_brand || '').trim(),
  )
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



function normalizeSelectableProductOption(item: ProductOptionItem): ProductOptionItem | null {
  const key = String(item?.price_identity_key || '').trim()
  const label = String(item?.price_identity_label || '').trim()
  const siteCount = Number(item?.site_count || 0)
  const priceObservationCount = item?.price_observation_count == null ? null : Number(item.price_observation_count)
  if (!key || !label) return null
  if (key.startsWith('/') || label.startsWith('/')) return null
  if (!Number.isFinite(siteCount) || siteCount <= 0) return null
  if (priceObservationCount != null && (!Number.isFinite(priceObservationCount) || priceObservationCount <= 0)) return null
  const sourceInfo = [item.source_name, item.source_category, item.liancai_top_category, item.liancai_subcategory]
    .filter(Boolean)
    .join(' ')
  if (NON_PRODUCT_MARKET_TEXT_PATTERN.test(`${key} ${label} ${sourceInfo}`)) return null
  const normalizedSourceName = item.source_name ? String(item.source_name).trim() : ''
  return {
    ...item,
    price_identity_key: key,
    price_identity_label: label,
    site_count: siteCount,
    price_observation_count: priceObservationCount,
    source_name: normalizedSourceName || null,
    source_category: item.source_category ? String(item.source_category).trim() : null,
    liancai_top_category: item.liancai_top_category ? String(item.liancai_top_category).trim() : null,
    liancai_subcategory: item.liancai_subcategory ? String(item.liancai_subcategory).trim() : null,
    liancai_keyword: item.liancai_keyword ? String(item.liancai_keyword).trim() : null,
    liancai_brand_name: item.liancai_brand_name ? String(item.liancai_brand_name).trim() : null,
    image_url: normalizedSourceName === '莲菜网' && item.image_url ? String(item.image_url).trim() : null,
  }
}

function filterSelectableProductOptions(options: ProductOptionItem[]) {
  const optionByKey = new Map<string, ProductOptionItem>()
  ;(options || []).forEach((item) => {
    const normalized = normalizeSelectableProductOption(item)
    if (normalized && !optionByKey.has(normalized.price_identity_key)) {
      optionByKey.set(normalized.price_identity_key, normalized)
    }
  })
  return Array.from(optionByKey.values())
}

function pickPreferredProductOption(options: ProductOptionItem[]) {
  if (!options.length) {
    return null
  }
  if (activeTab.value === 'trend') {
    const explicitTarget = trendDeepLinkLabel || trendDeepLinkTarget
    if (explicitTarget) {
      const explicitOption = options.find(
        (item) => item.price_identity_label === explicitTarget || item.price_identity_key === explicitTarget,
      )
      if (explicitOption) {
        return explicitOption
      }
    }
  }
  const firstOption = options[0]
  if (activeTab.value === 'trend') {
    // 趋势页允许调用方通过预置 product-options 缓存顺序指定首选商品；
    // 不再在首屏自动跳到覆盖市场更多的默认商品，避免覆盖回归测试/深链预热目标。
    return firstOption
  }
  if (Number(firstOption.site_count || 0) > 1) {
    return firstOption
  }
  return options.find((item) => Number(item.site_count || 0) > 1) || firstOption
}

function pickPreferredSummaryTrendRow() {
  return (
    marketRows.value.find((item) => item.price_identity_key && item.average_price != null) ||
    marketRows.value.find((item) => item.price_identity_key) ||
    null
  )
}

function resolveInitialTrendTarget() {
  const preferredOption = pickPreferredProductOption(productOptions.value)
  const fallbackRow = pickPreferredSummaryTrendRow()
  const identityKey = selectedIdentityKey.value || preferredOption?.price_identity_key || fallbackRow?.price_identity_key || ''
  const label =
    preferredOption?.price_identity_key === identityKey
      ? preferredOption.price_identity_label
      : fallbackRow?.price_identity_key === identityKey
        ? fallbackRow.product_name
        : selectedProductFallbackLabel.value

  return { identityKey, label }
}

function setTrendSelection(identityKey: string, label?: string | null) {
  suppressNextTrendWatch = true
  selectedIdentityKey.value = resolveCanonicalIdentityKey(identityKey)
  if (label !== undefined) {
    selectedProductFallbackLabel.value = label || selectedProductFallbackLabel.value
  }
}

function handleSelectProduct(identityKey: string) {
  selectedProductTouched.value = true
  const selectedRow = marketRows.value.find((item) => item.price_identity_key === identityKey)
  selectedProductFallbackLabel.value = selectedRow?.product_name || selectedProductFallbackLabel.value
  const isSwitchingProduct = selectedIdentityKey.value !== identityKey
  if (isSwitchingProduct) {
    productSummary.value = buildSnapshotProductSummary(resolveCanonicalIdentityKey(identityKey), marketRows.value)
    trendRows.value = []
    trendSiteOptions.value = []
    selectedSiteName.value = ''
    trendLoading.value = activeTab.value === 'trend'
  }
  const matchedProduct =
    productOptions.value.find((item) => item.price_identity_key === identityKey)?.price_identity_label ||
    selectedRow?.product_name ||
    selectedProductFallbackLabel.value
  writeMobileRecentState({
    productIdentityKey: identityKey,
    productTitle: matchedProduct,
  })
  selectedIdentityKey.value = resolveCanonicalIdentityKey(identityKey)
  syncWorkspaceTrendUrl(identityKey, matchedProduct)
  if (activeTab.value !== 'trend') {
    void activateTab('trend')
  }
}

function syncWorkspaceTrendUrl(identityKey: string, productLabel = '') {
  if (typeof window === 'undefined') return
  const params = new URLSearchParams(window.location.search)
  params.set('mode', 'workspace')
  params.set('tab', 'trend')
  params.set('identity_key', identityKey)
  // 切换到新版 identity_key 深链后必须清理旧版 product/label；
  // 否则刷新时初始化逻辑会优先读取旧 product，回到上一个商品。
  params.delete('product')
  params.delete('label')
  if (productLabel) {
    params.set('product_label', productLabel)
  } else {
    params.delete('product_label')
  }
  window.history.replaceState({}, '', `${MAIN_APP_PATH}?${params.toString()}`)
}

function handleWorkbenchSelectProduct(identityKey: string) {
  if (!identityKey) return
  selectedProductTouched.value = true
  const selectedRow = marketRows.value.find((item) => item.price_identity_key === identityKey)
  selectedProductFallbackLabel.value = selectedRow?.product_name || selectedProductFallbackLabel.value
  const isSwitchingProduct = selectedIdentityKey.value !== identityKey
  if (isSwitchingProduct) {
    productSummary.value = buildSnapshotProductSummary(resolveCanonicalIdentityKey(identityKey), marketRows.value)
    trendRows.value = []
    trendSiteOptions.value = []
    selectedSiteName.value = ''
  }
  const matchedProduct =
    productOptions.value.find((item) => item.price_identity_key === identityKey)?.price_identity_label ||
    selectedRow?.product_name ||
    selectedProductFallbackLabel.value
  writeMobileRecentState({
    workspaceTab: 'trend',
    productIdentityKey: identityKey,
    productTitle: matchedProduct,
  })
  selectedIdentityKey.value = resolveCanonicalIdentityKey(identityKey)
  syncWorkspaceTrendUrl(identityKey, matchedProduct)
}

async function handleWorkbenchSummaryLiancaiFilter(payload: { source_name?: string; liancai_top_category?: string; liancai_subcategory?: string; liancai_keyword?: string; liancai_brand?: string }) {
  const nextSourceName = String((payload as any).source_name || '').trim()
  const nextTopCategory = String(payload.liancai_top_category || '').trim()
  const nextSubcategory = String(payload.liancai_subcategory || '').trim()
  const nextKeyword = String(payload.liancai_keyword || '').trim()
  const nextBrand = String(payload.liancai_brand || '').trim()
  if (
    filters.summarySourceName === nextSourceName
    && filters.liancaiTopCategory === nextTopCategory
    && filters.liancaiSubcategory === nextSubcategory
    && filters.liancaiKeyword === nextKeyword
    && filters.liancaiBrand === nextBrand
  ) return

  filters.summarySourceName = nextSourceName
  filters.liancaiTopCategory = nextTopCategory
  filters.liancaiSubcategory = nextSubcategory
  filters.liancaiKeyword = nextKeyword
  filters.liancaiBrand = nextBrand
  productOptions.value = []
  productOptionsContextKey.value = ''
  selectedIdentityKey.value = ''
  selectedSiteName.value = ''
  selectedProductFallbackLabel.value = ''
  productSummary.value = null
  trendRows.value = []
  trendSiteOptions.value = []

  void reloadLiancaiFacets()
  await reloadSummary()
  window.setTimeout(() => {
    void ensureProductOptionsLoaded(true)
    void reloadLiancaiCategorySummary()
  }, 300)
}

function goToLanding() {
  viewMode.value = 'landing'
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search)

    params.delete('mode')

    params.delete('tab')

    params.delete('identity_key')

    params.delete('identityKey')

    params.delete('product')

    params.delete('product_label')

    params.delete('label')

    const nextQuery = params.toString()

    window.history.replaceState({}, '', `${MAIN_APP_PATH}${nextQuery ? `?${nextQuery}` : ''}`)

  }

}



function openSupplierPortal(useCurrentProduct = viewMode.value === 'workspace') {
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search)
    const identityKey = useCurrentProduct ? selectedIdentityKey.value : ''
    const productLabel = useCurrentProduct ? (selectedProductLabel.value || selectedProductFallbackLabel.value || '') : ''
    params.set('mode', 'supplier-portal')
    if (identityKey) {
      params.set('identity_key', identityKey)
      params.set('product', identityKey)
    } else {
      params.delete('identity_key')
      params.delete('identityKey')
      params.delete('product')
    }
    if (productLabel) {
      params.set('product_label', productLabel)
    } else {
      params.delete('product_label')
      params.delete('label')
    }
    window.location.assign(SUPPLIER_PORTAL_PATH + '?' + params.toString())
  }
}

function openSupplierBackend(
  useCurrentProduct = viewMode.value === 'workspace',
  context: { source?: string; productLabel?: string; identityKey?: string; section?: string } = {},
) {
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search)
    const identityKey = context.identityKey || (useCurrentProduct ? selectedIdentityKey.value : '')
    const productLabel = context.productLabel || (useCurrentProduct ? (selectedProductLabel.value || selectedProductFallbackLabel.value || '') : '')
    params.set('mode', 'supplier')
    params.set('tab', 'supplier')
    if (context.source) {
      params.set('source', context.source)
    }
    if (context.section) {
      params.set('section', context.section)
    }
    if (identityKey) {
      params.set('section', context.section || 'quote')
      params.set('identity_key', identityKey)
      params.set('product', identityKey)
    } else if (!context.section) {
      params.delete('section')
      params.delete('identity_key')
      params.delete('identityKey')
      params.delete('product')
    } else {
      params.delete('identity_key')
      params.delete('identityKey')
      params.delete('product')
    }
    if (productLabel) {
      params.set('product_label', productLabel)
    } else {
      params.delete('product_label')
      params.delete('label')
    }
    if (filters.summarySourceName) {
      params.set('source_name', filters.summarySourceName)
    }
    if (filters.liancaiTopCategory) {
      params.set('liancai_top_category', filters.liancaiTopCategory)
    }
    if (filters.liancaiSubcategory) {
      params.set('liancai_subcategory', filters.liancaiSubcategory)
    }
    window.location.assign(`${SUPPLIER_PLATFORM_PATH}?${params.toString()}`)
  }
}

function openHomeSuiteEntry(key: HomeSuiteKey) {
  if (key === 'supplier') {
    openSupplierBackend(false)
    return
  }
  enterWorkspace()
}

function openLandingPriorityEntry(target: 'alerts' | 'signals' | 'summary') {
  if (target === 'alerts') {
    enterWorkspace('alerts')
    return
  }
  if (target === 'signals') {
    enterWorkspace('signals')
    return
  }
  enterWorkspace('summary')
}


function openCategoryMarket(categoryKey: string) {

  activeMarketCategory.value = categoryKey

  const category = mobileQuickCategories.value.find((item) => item.key === categoryKey)

  writeMobileRecentState({

    categoryKey,

    categoryLabel: category?.label || categoryKey,

  })

  enterWorkspace('summary')

}



function openProductDetail(identityKey: string) {

  if (!identityKey || identityKey === 'placeholder') {

    enterWorkspace('summary')

    return

  }

  const matchedProduct =

    productOptions.value.find((item) => item.price_identity_key === identityKey)?.price_identity_label ||

    marketRows.value.find((item) => item.price_identity_key === identityKey)?.product_name ||

    primaryMobileSpotlight.value.title

  viewMode.value = 'workspace'

  writeMobileRecentState({

    workspaceTab: 'trend',

    productIdentityKey: identityKey,

    productTitle: matchedProduct,

  })

  handleSelectProduct(identityKey)

  syncWorkspaceTrendUrl(identityKey, matchedProduct)

}



async function openPrimaryMobileSpotlight() {

  const spotlightKey = primaryMobileSpotlight.value.identityKey

  if (spotlightKey && spotlightKey !== 'placeholder') {

    openProductDetail(spotlightKey)

    return

  }

  await ensureProductOptionsLoaded()

  const preferredOption = pickPreferredProductOption(productOptions.value)

  if (preferredOption?.price_identity_key) {

    openProductDetail(preferredOption.price_identity_key)

    return

  }

  enterWorkspace('trend')

}



function openMobileLocalShortcut(shortcutKey: 'category' | 'market' | 'product') {

  if (shortcutKey === 'category') {

    const category = mobileQuickCategories.value.find((item) => item.key !== '全部') || mobileQuickCategories.value[0]

    openCategoryMarket(category?.key || '全部')

    return

  }

  if (shortcutKey === 'product') {

    openPrimaryMobileSpotlight()

    return

  }

  enterWorkspace('summary')

}



function openMobileRecentEntry(entryKey: 'workspace' | 'category' | 'product') {

  if (entryKey === 'category') {

    openCategoryMarket(mobileRecentState.value.categoryKey || '全部')

    return

  }

  if (entryKey === 'product') {

    openProductDetail(mobileRecentState.value.productIdentityKey || primaryMobileSpotlight.value.identityKey)

    return

  }

  enterWorkspace(mobileRecentState.value.workspaceTab || 'summary')

}



function applyAuthSession(session: AuthLoginResponse | null) {

  authSession.value = session

  if (session) {

    writeAuthSession(session)

  } else {

    clearAuthSession()

  }

}



async function restoreAuthSession() {

  if (!authSession.value?.access_token) {

    return

  }

  try {

    const me = await fetchCurrentUser()

    applyAuthSession({

      ...authSession.value,

      user: me.user,

    })

  } catch {

    applyAuthSession(null)

  }

}



function enterWorkspace(targetTab: (typeof tabs)[number]['key'] = 'summary') {
  if (targetTab === 'summary' && activeTab.value !== 'summary') {
    resetSummaryFilters()
  }
  viewMode.value = 'workspace'
  const urlTab = typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('tab') : ''
  const launchedDirectlyToTrend = targetTab === 'trend' && activeTab.value !== 'trend' && urlTab === 'trend' && !selectedProductTouched.value
  if (launchedDirectlyToTrend) {
    selectedIdentityKey.value = ''
    selectedSiteName.value = ''
    selectedProductFallbackLabel.value = ''
    productSummary.value = null
    trendRows.value = []
  }
  if (targetTab === 'summary' || targetTab === 'trend') {
    writeMobileRecentState({ workspaceTab: targetTab })
  }
  void activateTab(targetTab)
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search)
    params.set('mode', 'workspace')
    params.set('tab', targetTab)
    if (targetTab !== 'trend') {
      params.delete('identity_key')
      params.delete('identityKey')
      params.delete('product')
      params.delete('product_label')
      params.delete('label')
    }
    window.history.replaceState({}, '', `${MAIN_APP_PATH}?${params.toString()}`)
  }
}


async function activateTab(tabKey: (typeof tabs)[number]['key']) {
  const wasTrendTab = activeTab.value === 'trend'
  activeTab.value = tabKey
  if (tabKey !== 'trend') return
  if (!selectedIdentityKey.value) {
    trendLoading.value = true
  }
  const initialTarget = resolveInitialTrendTarget()
  if (initialTarget.identityKey) {
    if (!selectedIdentityKey.value) {
      setTrendSelection(initialTarget.identityKey, initialTarget.label)
    }
    syncWorkspaceTrendUrl(initialTarget.identityKey, initialTarget.label)
    if (wasTrendTab && selectedIdentityKey.value === initialTarget.identityKey && trendRows.value.length) {
      trendLoading.value = false
      return
    }
    await reloadTrend(initialTarget.identityKey)
    void ensureProductOptionsLoaded()
    return
  }

  if (!marketRows.value.length) {
    await reloadSummary()
  }
  let loadedTarget = resolveInitialTrendTarget()
  if (!loadedTarget.identityKey) {
    await ensureProductOptionsLoaded()
    loadedTarget = resolveInitialTrendTarget()
  }
  if (!loadedTarget.identityKey) {
    trendLoading.value = false
    return
  }
  if (!selectedIdentityKey.value) {
    setTrendSelection(loadedTarget.identityKey, loadedTarget.label)
  }
  syncWorkspaceTrendUrl(loadedTarget.identityKey, loadedTarget.label)
  if (wasTrendTab && selectedIdentityKey.value === loadedTarget.identityKey && trendRows.value.length) {
    trendLoading.value = false
    return
  }
  await reloadTrend(loadedTarget.identityKey)
}

async function ensureWorkbenchTrend() {
  const initialTarget = resolveInitialTrendTarget()
  if (!initialTarget.identityKey && !productOptionsLoading.value) {
    void ensureProductOptionsLoaded()
  }
  if (!initialTarget.identityKey && !marketRows.value.length) {
    await reloadSummary()
  }
  const target = initialTarget.identityKey ? initialTarget : resolveInitialTrendTarget()
  const identityKey = target.identityKey
  if (!identityKey) return
  if (!selectedIdentityKey.value) {
    setTrendSelection(identityKey, target.label)
  }
  if (!trendRows.value.length || productSummary.value?.price_identity_key !== identityKey) {
    await reloadTrend(identityKey)
  }
  const loadedRows = trendRows.value
  // 用户或测试显式选择了商品时，不再自动跳到“趋势更丰富”的其它商品。
  if (trendMode.value === 'cross_market' && loadedRows.length < 2 && !selectedProductTouched.value) {
    await ensureProductOptionsLoaded()
    const trendReadyOption = await findTrendReadyProductOption(identityKey)
    if (trendReadyOption && trendReadyOption.price_identity_key !== selectedIdentityKey.value) {
      setTrendSelection(trendReadyOption.price_identity_key, trendReadyOption.price_identity_label)
      await reloadTrend(trendReadyOption.price_identity_key)
    }
  }
}



async function reloadSummary() {
  const requestId = ++summaryRequestSequence
  summaryLoading.value = true
  summaryBackfillLoading.value = false
  try {
    pageError.value = ''
    if (selectedIdentityKey.value) {
      const canonicalIdentityKey = resolveCanonicalIdentityKey(selectedIdentityKey.value)
      fetchProductSupplierQuotes(canonicalIdentityKey)
        .then((response) => {
          if (canonicalIdentityKey === resolveCanonicalIdentityKey(selectedIdentityKey.value)) {
            productSupplierQuotes.value = response.items ?? []
          }
        })
        .catch(() => {
          if (canonicalIdentityKey === resolveCanonicalIdentityKey(selectedIdentityKey.value)) {
            productSupplierQuotes.value = []
          }
        })
    }
    const params = buildFilterParams()
    // Start the lightweight product catalog request before the heavier summary request.
    // This keeps the first screen usable even if /api/market/summary is slow or stalls.
    void ensureProductOptionsLoaded(true)
    const cachedRows = readSummaryCache(params)
    if (cachedRows?.length) {

      marketRows.value = fillSummaryRowImageUrls(cachedRows, productOptions.value)

    }



    let firstSummary: Awaited<ReturnType<typeof fetchMarketSummary>>
    try {
      firstSummary = await fetchMarketSummary({
        ...params,
        limit: MARKET_SUMMARY_INITIAL_LIMIT,
        offset: 0,
      })
    } catch (error) {
      if (!hasLiancaiSummaryFilter(params)) throw error
      firstSummary = { items: [], total: 0, limit: MARKET_SUMMARY_INITIAL_LIMIT, offset: 0, has_more: false }
    }
    if (requestId !== summaryRequestSequence) return

    if (hasLiancaiSummaryFilter(params) && !(firstSummary.items ?? []).length) {
      const fallbackParams = {
        province: params.province,
        city: params.city,
        source_name: params.source_name,
      }
      const fallbackSummary = await fetchMarketSummary({
        ...fallbackParams,
        limit: 0,
        offset: 0,
      })
      if (requestId !== summaryRequestSequence) return
      const fallbackRows = filterSummaryRowsByLiancaiCategory(fallbackSummary.items ?? [], params)
      firstSummary = {
        items: fallbackRows,
        total: fallbackRows.length,
        limit: 0,
        offset: 0,
        has_more: false,
      }
    }

    const firstItems = firstSummary.items ?? []
    let loadedRows = filterProductMarketSummaryRows(firstItems)
    if (!loadedRows.length && firstItems.length) {
      loadedRows = firstItems
    }
    if (selectedIdentityKey.value) {
      try {
        const canonicalIdentityKey = resolveCanonicalIdentityKey(selectedIdentityKey.value)
        const trend = await fetchProductTrend(canonicalIdentityKey, { mode: 'cross_market', ...params })
        const supplierRow = buildSupplierSummaryRowFromTrendRows(
          trend.items ?? [],
          canonicalIdentityKey,
          selectedProductFallbackLabel.value,
        )
        if (supplierRow) {
          loadedRows = [
            supplierRow,
            ...loadedRows.filter((row) => !(String(row.source_names || row.lowest_price_site || '').includes('供应平台'))),
          ]
        }
      } catch {
        // Keep summary usable even if supplier trend backfill fails.
      }
    }
    loadedRows = fillSummaryRowImageUrls(loadedRows, productOptions.value)
    marketRows.value = loadedRows
    if (selectedIdentityKey.value) {
      void syncSupplierSummaryRow(selectedIdentityKey.value)
    }
    summaryLoading.value = false

    let hasMore = Boolean(firstSummary.has_more)
    let nextOffset = Number(firstSummary.next_offset || 0) || Number(firstSummary.offset || 0) + Number(hasMore ? firstSummary.limit || firstItems.length : firstItems.length)
    writeSummaryCache(params, marketRows.value)
    summaryBackfillLoading.value = hasMore
    void loadRemainingSummaryPages(requestId, params, loadedRows, nextOffset, hasMore)
  } catch (error) {
    if (requestId === summaryRequestSequence) {
      pageError.value = dataSourceState.lastError || '报价接口读取失败，请检查 API 服务'
      summaryBackfillLoading.value = false
    }
  } finally {
    if (requestId === summaryRequestSequence) {
      summaryLoading.value = false
    }
  }
}

async function loadRemainingSummaryPages(
  requestId: number,
  params: ReturnType<typeof buildFilterParams>,
  initialRows: MarketSummaryItem[],
  nextOffset: number,
  hasMore: boolean,
) {
  if (!hasMore) return
  let loadedRows = [...initialRows]
  await new Promise((resolve) => window.setTimeout(resolve, 120))
  try {
    while (hasMore) {
      const page = await fetchMarketSummary({
        ...params,
        limit: MARKET_SUMMARY_BACKGROUND_LIMIT,
        offset: nextOffset,
      })
      if (requestId !== summaryRequestSequence) return
      const pageItems = page.items ?? []
      let pageRows = filterProductMarketSummaryRows(pageItems)
      if (!pageRows.length && pageItems.length) {
        pageRows = pageItems
      }
      loadedRows = fillSummaryRowImageUrls([...loadedRows, ...pageRows], productOptions.value)
      marketRows.value = loadedRows.length ? loadedRows : marketRows.value
      hasMore = Boolean(page.has_more) && pageItems.length > 0
      nextOffset = Number(page.next_offset || 0) || Number(page.offset || nextOffset) + Number(hasMore ? page.limit || pageItems.length : pageItems.length)
    }
    writeSummaryCache(params, marketRows.value)
  } catch {
    // 首屏数据已可用，后台补齐失败时不打断用户查看行情列表。
  } finally {
    if (requestId === summaryRequestSequence) {
      summaryBackfillLoading.value = false
    }
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

    pageError.value = dataSourceState.lastError || '地区选项读取失败，请检查 API 服务'

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

      pageError.value = dataSourceState.lastError || '来源覆盖接口读取失败，请检查 API 服务'

    }

  } finally {

    coverageLoading.value = false

  }

}



async function reloadLiancaiCategorySummary() {
  if (liancaiCategorySummaryLoading.value) return
  liancaiCategorySummaryLoading.value = true
  try {
    const data = await fetchLiancaiCategorySummary({

      source_name: selectedCategorySourceName.value || undefined,

    })

    liancaiCategorySummaryItems.value = data.items ?? []

  } catch {

    if (!liancaiCategorySummaryItems.value.length) {

      liancaiCategorySummaryItems.value = []

    }

  } finally {
    liancaiCategorySummaryLoading.value = false
  }
}

async function reloadLiancaiFacets() {
  const top = String(filters.liancaiTopCategory || '').trim()
  const sub = String(filters.liancaiSubcategory || '').trim()
  if (!top || !sub) {
    liancaiFacetOptions.value = { keywords: [], brands: [] }
    return
  }
  try {
    liancaiFacetOptions.value = await fetchLiancaiFacets({
      liancai_top_category: top,
      liancai_subcategory: sub,
    })
  } catch {
    liancaiFacetOptions.value = { keywords: [], brands: [] }
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
  } catch (error) {
    // Keep previous crawl status if the endpoint is temporarily unavailable.

  }

}



async function applyExplicitTrendTarget() {
  if (activeTab.value !== 'trend') return false
  const explicitTarget = trendDeepLinkLabel || trendDeepLinkTarget
  if (!explicitTarget) return false
  const explicitOption = productOptions.value.find(
    (item) => item.price_identity_label === explicitTarget || item.price_identity_key === explicitTarget,
  )
  if (!explicitOption) return false
  if (selectedIdentityKey.value !== explicitOption.price_identity_key) {
    setTrendSelection(explicitOption.price_identity_key, explicitOption.price_identity_label)
    selectedSiteName.value = ''
  }
  await reloadTrend(explicitOption.price_identity_key)
  return true
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
        await applyExplicitTrendTarget()
      }

      if (crawlStatus.value?.last_error) {

        ElMessage.warning(`抓取完成，但存在异常：${crawlStatus.value.last_error}`)

      } else {

        ElMessage.success('最新数据已重新获取')

      }

    }

  }, 3000)
}

async function handleWorkbenchRunCrawl() {
  if (crawlStatus.value?.is_running) {
    ElMessage.warning('当前已有同步任务在执行')
    return
  }
  try {
    const data = await triggerCrawlRun()
    crawlStatus.value = data.item ?? null
    if (data.accepted) {
      ElMessage.success('已开始同步数据源')
      startCrawlPolling()
    } else {
      ElMessage.warning('当前已有同步任务在执行')
    }
  } catch {
    ElMessage.error('启动数据源同步失败，请检查 API 服务')
  }
}

function readSettingsChangeLogs(): SettingsChangeLogItem[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(SETTINGS_CHANGE_LOG_STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function appendSettingsChangeLog(action_type: SettingsChangeLogItem['action_type'], target_name: string, summary: string) {
  const actor_name = authSession.value?.user.display_name || authSession.value?.user.username || '当前用户'
  const nextItem: SettingsChangeLogItem = {
    id: `${action_type}-${Date.now()}`,
    changed_at: new Date().toISOString(),
    actor_name,
    action_type,
    target_name,
    summary,
  }
  settingsChangeLogs.value = [nextItem, ...settingsChangeLogs.value].slice(0, 12)
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(SETTINGS_CHANGE_LOG_STORAGE_KEY, JSON.stringify(settingsChangeLogs.value))
  }
}

async function handleWorkbenchRunSourceCrawl(payload: { source_url?: string; source_name?: string }) {
  if (crawlStatus.value?.is_running) {
    ElMessage.warning('当前已有同步任务在执行')
    return
  }
  try {
    const data = await triggerCrawlRun({
      source_url: payload.source_url,
      source_name: payload.source_name,
    })
    crawlStatus.value = data.item ?? null
    if (data.accepted) {
      ElMessage.success(payload.source_name ? `已开始试跑 ${payload.source_name}` : '已开始试跑当前来源')
      startCrawlPolling()
    } else {
      ElMessage.warning('当前已有同步任务在执行')
    }
  } catch {
    ElMessage.error('试跑当前来源失败，请检查 API 服务')
  }
}

async function handleWorkbenchUpdateCrawlSchedule(payload: {
  enabled: boolean
  interval_seconds: number
  fetch_mode?: 'requests' | 'playwright'
}) {
  try {
    const data = await updateCrawlSchedule(payload)
    crawlStatus.value = data.item ?? null
    appendSettingsChangeLog('schedule', '系统同步设置', `${payload.enabled ? '开启' : '关闭'}自动同步，频率 ${payload.interval_seconds} 秒，模式 ${payload.fetch_mode || 'requests'}`)
    ElMessage.success(payload.enabled ? '已开启每日自动同步' : '已关闭每日自动同步')
  } catch {
    ElMessage.error('更新系统同步设置失败')
  }
}

async function handleWorkbenchUpdateSourceConfig(payload: {
  source_url: string
  enabled: boolean
  configured_name?: string
  market_scope?: string
  market_category?: string
  notes?: string
}) {
  try {
    const data = await updateSourceCoverage(payload)
    const nextItem = data.item ?? null
    if (nextItem?.source_url) {
      const nextUrl = String(nextItem.source_url)
      const nextRows = [...sourceCoverageRows.value]
      const existingIndex = nextRows.findIndex((item) => String(item.source_url || '') === nextUrl)
      if (existingIndex >= 0) {
        nextRows.splice(existingIndex, 1, nextItem)
      } else {
        nextRows.unshift(nextItem)
      }
      sourceCoverageRows.value = nextRows
    } else {
      await reloadSourceCoverage()
    }
    appendSettingsChangeLog('source_config', payload.configured_name || payload.source_url || '来源配置', `${payload.enabled ? '启用' : '停用'}，范围 ${payload.market_scope || '未填写'}，分类 ${payload.market_category || '未填写'}`)
    ElMessage.success(payload.enabled ? '来源配置已启用' : '来源配置已停用')
  } catch {
    ElMessage.error('保存来源配置失败')
  }
}

async function handleWorkbenchUpdateSourceStrategy(payload: {
  source_name: string
  preferred_fetch_mode?: 'requests' | 'playwright' | 'api'
  strategy?: string
  timeout_seconds?: number
  retry_count?: number
  request_delay_seconds?: number
  blocked_status_codes?: number[]
  verify_ssl?: boolean
  api_strategy?: string
}) {
  try {
    await updateSourceStrategy(payload)
    await reloadSourceCoverage()
    appendSettingsChangeLog('source_strategy', payload.source_name, `模式 ${payload.preferred_fetch_mode || 'requests'}，策略 ${payload.strategy || '未填写'}，超时 ${payload.timeout_seconds || 0} 秒`)
    ElMessage.success('抓取策略已保存')
  } catch {
    ElMessage.error('保存抓取策略失败')
  }
}

async function handleWorkbenchUpdateGlobalAlertRules(items: GlobalAlertRuleItem[]) {
  try {
    const data = await updateGlobalAlertRules(items)
    globalAlertRules.value = data.items ?? items
    appendSettingsChangeLog('global_alert', '全局预警规则', `已保存 ${items.length} 条规则`)
    ElMessage.success('全局预警规则已保存')
  } catch {
    ElMessage.error('保存全局预警规则失败')
  }
}

function marketSummaryRowsFromProductOptions(options: ProductOptionItem[]): MarketSummaryItem[] {
  return filterSelectableProductOptions(options).map((item) => ({
    price_identity_key: item.price_identity_key,
    product_name: item.price_identity_label,
    group_name: item.price_identity_label,
    category: item.source_category || item.liancai_top_category || item.liancai_subcategory || item.source_name || '',
    liancai_top_category: item.liancai_top_category || item.source_category || '',
    liancai_subcategory: item.liancai_subcategory || '',
    liancai_keyword: item.liancai_keyword || null,
    liancai_brand_name: item.liancai_brand_name || null,
    region_label: item.source_name || selectedLocationLabel.value || '',
    lowest_price_site: item.source_name || '',
    highest_price_site: item.source_name || '',
    average_price: null,
    lowest_price: null,
    highest_price: null,
    market_count: item.price_observation_count || item.site_count || 1,
    site_count: item.site_count || 1,
    latest_captured_at: item.latest_captured_at || null,
    price_unit_basis: '',
    image_url: item.image_url || null,
  })) as MarketSummaryItem[]
}

function buildSupplierSummaryRowFromTrendRows(
  rows: ProductTrendRow[],
  identityKey: string,
  fallbackLabel: string,
): MarketSummaryItem | null {
  const supplierRows = (rows || []).filter((item) => String(item.source_name || '').includes('供应平台') && item.current_price != null)
  if (!supplierRows.length) return null
  const lowest = [...supplierRows].sort((left, right) => Number(left.current_price) - Number(right.current_price))[0]
  const productLabel = lowest.price_identity_label || fallbackLabel || identityKey
  return {
    product_name: productLabel,
    price_identity_key: identityKey,
    group_name: productLabel,
    category: lowest.liancai_top_category || lowest.category || '供应商报价',
    liancai_top_category: lowest.liancai_top_category || lowest.category || '供应商报价',
    liancai_subcategory: lowest.liancai_subcategory || lowest.category || '供应商报价',
    average_price: Number(lowest.current_price),
    lowest_price: Number(lowest.current_price),
    highest_price: Number(lowest.current_price),
    market_count: supplierRows.length,
    site_count: supplierRows.length,
    lowest_price_site: '供应平台',
    highest_price_site: '供应平台',
    source_names: '供应平台',
    source_display_names: supplierRows.map((item) => item.site_name).filter(Boolean).join('、') || '供应平台',
    latest_captured_at: lowest.captured_at || null,
    price_unit_basis: lowest.spec_text || '公斤',
  }
}

const activeSupplierSummaryRow = computed<MarketSummaryItem | null>(() => {
  if (!selectedIdentityKey.value) return null
  const supplierTrendRows = trendRows.value.filter((item) => String(item.source_name || '').includes('供应平台') && item.current_price != null)
  if (supplierTrendRows.length) {
    const lowestTrend = [...supplierTrendRows].sort((left, right) => Number(left.current_price) - Number(right.current_price))[0]
    const productLabel = lowestTrend.price_identity_label || selectedProductFallbackLabel.value || selectedIdentityKey.value
    return {
      product_name: productLabel,
      price_identity_key: selectedIdentityKey.value,
      group_name: productLabel,
      category: lowestTrend.liancai_top_category || lowestTrend.category || '供应商报价',
      liancai_top_category: lowestTrend.liancai_top_category || lowestTrend.category || '供应商报价',
      liancai_subcategory: lowestTrend.liancai_subcategory || lowestTrend.category || '供应商报价',
      average_price: Number(lowestTrend.current_price),
      lowest_price: Number(lowestTrend.current_price),
      highest_price: Number(lowestTrend.current_price),
      market_count: supplierTrendRows.length,
      site_count: supplierTrendRows.length,
      lowest_price_site: '供应平台',
      highest_price_site: '供应平台',
      source_names: '供应平台',
      source_display_names: supplierTrendRows.map((item) => item.site_name).filter(Boolean).join('、') || '供应平台',
      latest_captured_at: lowestTrend.captured_at || null,
      price_unit_basis: lowestTrend.spec_text || '公斤',
    }
  }
  if (!productSupplierQuotes.value.length) return null
  const activeQuotes = productSupplierQuotes.value.filter((item) => item.quote_price != null)
  if (!activeQuotes.length) return null
  const lowestQuote = [...activeQuotes].sort((left, right) => Number(left.quote_price) - Number(right.quote_price))[0]
  const productLabel = lowestQuote.price_identity_label || selectedProductFallbackLabel.value || selectedIdentityKey.value
  return {
    product_name: productLabel,
    price_identity_key: selectedIdentityKey.value,
    group_name: productLabel,
    category: lowestQuote.market_category || lowestQuote.category || '供应商报价',
    liancai_top_category: lowestQuote.market_category || lowestQuote.category || '供应商报价',
    liancai_subcategory: lowestQuote.market_category || lowestQuote.category || '供应商报价',
    average_price: Number(lowestQuote.quote_price),
    lowest_price: Number(lowestQuote.quote_price),
    highest_price: Number(lowestQuote.quote_price),
    market_count: activeQuotes.length,
    site_count: activeQuotes.length,
    lowest_price_site: '供应平台',
    highest_price_site: '供应平台',
    source_names: '供应平台',
    source_display_names: activeQuotes.map((item) => item.supplier_name).filter(Boolean).join('、') || '供应平台',
    latest_captured_at: lowestQuote.quoted_at || null,
    price_unit_basis: lowestQuote.quote_unit || '公斤',
  }
})


async function syncSupplierSummaryRow(identityKey: string) {
  const canonicalIdentityKey = resolveCanonicalIdentityKey(identityKey)
  if (!canonicalIdentityKey) return
  try {
    const trend = await fetchProductTrend(canonicalIdentityKey, { mode: 'cross_market', ...buildFilterParams() })
    const supplierRow = buildSupplierSummaryRowFromTrendRows(
      trend.items ?? [],
      canonicalIdentityKey,
      selectedProductFallbackLabel.value,
    )
    marketRows.value = marketRows.value.filter((row) => !String(row.source_names || row.lowest_price_site || '').includes('供应平台'))
    if (supplierRow) {
      marketRows.value = [supplierRow, ...marketRows.value]
    }
  } catch {
    // Ignore supplier summary sync failure and keep market rows visible.
  }
}

async function ensureProductOptionsLoaded(force = false) {
  const params = buildFilterParams()
  const contextKey = buildContextKey(params)
  const cachedOptions = readLocalCache<ProductOptionItem[]>(PRODUCT_OPTIONS_CACHE_KEY, contextKey)
  if (cachedOptions?.length) {
    const selectableCachedOptions = filterSelectableProductOptions(cachedOptions)
    const cachedHasSelection = selectedIdentityKey.value
      ? selectableCachedOptions.some((item) => item.price_identity_key === selectedIdentityKey.value)
      : true
    if (selectableCachedOptions.length && (!force || cachedHasSelection)) {
      productOptions.value = selectableCachedOptions
      if (!marketRows.value.length && selectableCachedOptions.length) {
        marketRows.value = marketSummaryRowsFromProductOptions(selectableCachedOptions)
      } else if (marketRows.value.length) {
        marketRows.value = fillSummaryRowImageUrls(marketRows.value, selectableCachedOptions)
      }
      productOptionsContextKey.value = contextKey
      if (trendDeepLinkTarget) {
        const matchedDeepLink = selectableCachedOptions.find((item) => item.price_identity_key === trendDeepLinkTarget || item.price_identity_label === trendDeepLinkTarget)
        if (matchedDeepLink) {
          selectedIdentityKey.value = matchedDeepLink.price_identity_key
          selectedProductFallbackLabel.value = matchedDeepLink.price_identity_label || trendDeepLinkLabel || selectedProductFallbackLabel.value
        }
      } else if (trendDeepLinkLabel) {
        const matchedLabel = selectableCachedOptions.find((item) => item.price_identity_label === trendDeepLinkLabel)
        if (matchedLabel) {
          selectedIdentityKey.value = matchedLabel.price_identity_key
          selectedProductFallbackLabel.value = matchedLabel.price_identity_label || selectedProductFallbackLabel.value
        }
      }
      if (!selectedIdentityKey.value) {
        const preferredOption = pickPreferredProductOption(selectableCachedOptions)
        selectedIdentityKey.value = preferredOption?.price_identity_key || ''
        selectedProductFallbackLabel.value = preferredOption?.price_identity_label || ''
      }
      void prefetchTopTrendSnapshots(contextKey)
      return
    }
  }
  if (!force && productOptionsContextKey.value === contextKey && productOptions.value.length) {
    void prefetchTopTrendSnapshots(contextKey)
    return
  }
  if (productOptionsPromise && productOptionsLoading.value) {
    await productOptionsPromise

    void prefetchTopTrendSnapshots(contextKey)

    return

  }

  productOptionsPromise = (async () => {

    productOptionsLoading.value = true

    try {

      const optionsData = await fetchProductOptions({ ...params, limit: 1000 })
      const incomingOptions = filterSelectableProductOptions(optionsData.items ?? [])
      const preservedSelectedOption = selectedIdentityKey.value
        ? filterSelectableProductOptions(productOptions.value).find((item) => item.price_identity_key === selectedIdentityKey.value)
        : null
      const nextProductOptions = preservedSelectedOption
        ? [preservedSelectedOption, ...incomingOptions.filter((item) => item.price_identity_key !== preservedSelectedOption.price_identity_key)]
        : incomingOptions
      productOptions.value = filterSelectableProductOptions(nextProductOptions)
      if (!marketRows.value.length && productOptions.value.length) {
        marketRows.value = marketSummaryRowsFromProductOptions(productOptions.value)
      } else if (marketRows.value.length) {
        marketRows.value = fillSummaryRowImageUrls(marketRows.value, productOptions.value)
      }
      productOptionsContextKey.value = contextKey
      writeLocalCache(PRODUCT_OPTIONS_CACHE_KEY, contextKey, productOptions.value)
      if (!selectedIdentityKey.value && productOptions.value.length) {
        const preferredOption = pickPreferredProductOption(productOptions.value)
        selectedIdentityKey.value = preferredOption?.price_identity_key || ''
        selectedProductFallbackLabel.value = preferredOption?.price_identity_label || ''
      } else if (selectedIdentityKey.value && !productOptions.value.some((item) => item.price_identity_key === selectedIdentityKey.value)) {
        const preferredOption = pickPreferredProductOption(productOptions.value)
        selectedIdentityKey.value = preferredOption?.price_identity_key || ''
        selectedProductFallbackLabel.value = preferredOption?.price_identity_label || ''
        selectedSiteName.value = ''
      }
    } catch (error) {

      if (!productOptions.value.length) {

        productOptions.value = []

        productOptionsContextKey.value = ''

      }

      pageError.value = dataSourceState.lastError || '商品列表接口读取失败，请检查 API 服务'

    } finally {

      productOptionsLoading.value = false

      productOptionsPromise = null

    }

  })()

  await productOptionsPromise

  void prefetchTopTrendSnapshots(contextKey)

}



async function reloadAll() {
  if (workbenchRefreshing.value) return
  workbenchRefreshing.value = true
  try {
    await reloadSummary()
    void Promise.allSettled([
      ensureProductOptionsLoaded(true),
      reloadSalesAssets(),
      reloadSupplierOverview(),
      reloadSourceCoverage(),
      reloadLiancaiCategorySummary(),
      reloadCrawlStatus(),
      reloadGlobalAlertRules(),
    ]).then(async () => {
      if (!marketRows.value.length) {
        await reloadSummary()
      }
      if (selectedIdentityKey.value) {
        await reloadTrend(selectedIdentityKey.value)
      }
    })
    if (!marketRows.value.length) {
      void reloadSummary()
    }
  } finally {
    workbenchRefreshing.value = false
  }
}


async function refreshTrendProducts() {

  trendLoading.value = true

  try {

    await ensureProductOptionsLoaded(true)

    const preferredOption = pickPreferredProductOption(productOptions.value)

    const identityKey = selectedIdentityKey.value || preferredOption?.price_identity_key || ''

    if (!identityKey) {

      return

    }

    if (!selectedIdentityKey.value) {

      selectedIdentityKey.value = identityKey

      selectedProductFallbackLabel.value = preferredOption?.price_identity_label || ''

    }

    await reloadTrend(identityKey)

  } finally {

    if (!selectedIdentityKey.value) {

      trendLoading.value = false

    }

  }

}



async function reloadSupplierOverview() {
  if (!authSession.value?.access_token) {
    supplierOverview.value = null
    return
  }
  try {
    supplierOverview.value = await fetchSupplierOverview(10)
  } catch {
    if (!supplierOverview.value) {

      supplierOverview.value = null

    }

  }

}

async function reloadGlobalAlertRules() {
  try {
    const data = await fetchGlobalAlertRules()
    globalAlertRules.value = data.items ?? []
  } catch {
    if (!globalAlertRules.value.length) {
      globalAlertRules.value = []
    }
  }
}



async function reloadSalesAssets() {

  try {

    const params = {

      ...buildFilterParams(),

      focus: filters.keyword || undefined,

    }

    const [overview, salesDemo] = await Promise.all([

      fetchSignalsOverview(params),

      fetchSalesDecisionContent('sales'),

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

  const identityKey = resolveCanonicalIdentityKey(identityKeyOverride || selectedIdentityKey.value)

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



  const summaryCacheKey = normalizeIdentityCacheKey(identityKey)

  const summaryCached = readLocalCache<Record<string, any>>(PRODUCT_SUMMARY_CACHE_KEY, summaryCacheKey)

  if (summaryCached) {
    productSummary.value = {
      ...summaryCached,
      price_identity_key: summaryCached.price_identity_key || identityKey,
    }
  } else {
    productSummary.value = null
  }


  const currentSiteKey = selectedSiteName.value || undefined

  const currentTrendCacheKey = buildTrendRequestKey(normalizeIdentityCacheKey(identityKey), trendMode.value, currentSiteKey)

  const crossMarketTrendCacheKey = buildTrendRequestKey(normalizeIdentityCacheKey(identityKey), 'cross_market')

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

    fetchProductSupplierQuotes(identityKey)
      .then((response) => {
        if (identityKey === resolveCanonicalIdentityKey(selectedIdentityKey.value)) {
          productSupplierQuotes.value = response.items ?? []
        }
      })
      .catch(() => {
        if (identityKey === resolveCanonicalIdentityKey(selectedIdentityKey.value)) {
          productSupplierQuotes.value = []
        }
      })

    const summaryRequest = fetchProductSummary(identityKey, filterParams)
      .then((summary) => {
        if (requestId !== trendRequestSequence || identityKey !== selectedIdentityKey.value) {
          return
        }
        const nextSummary = summary.item
          ? {
              ...summary.item,
              price_identity_key: summary.item.price_identity_key || identityKey,
            }
          : null
        productSummary.value = nextSummary
        if (nextSummary) {
          writeLocalCache(PRODUCT_SUMMARY_CACHE_KEY, summaryCacheKey, nextSummary)
        }
      })
      .catch(() => {
        if (requestId === trendRequestSequence && identityKey === selectedIdentityKey.value && !summaryCached) {
          productSummary.value = null
        }
      })

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



    if (requestId !== trendRequestSequence || identityKey !== resolveCanonicalIdentityKey(selectedIdentityKey.value)) {
      return
    }
    trendRows.value = trend.items ?? []
    writeLocalCache(
      PRODUCT_TREND_CACHE_KEY,
      buildTrendRequestKey(normalizeIdentityCacheKey(identityKey), trendMode.value, selectedSiteName.value),
      trendRows.value,
    )
    void summaryRequest
  } catch (error) {

    if (requestId !== trendRequestSequence || identityKey !== resolveCanonicalIdentityKey(selectedIdentityKey.value)) {

      return

    }

    pageError.value = dataSourceState.lastError || '趋势接口读取失败，请检查 API 服务'

    if (!usedCachedTrend) {

      trendRows.value = []

    }

  } finally {

    if (requestId === trendRequestSequence && identityKey === resolveCanonicalIdentityKey(selectedIdentityKey.value)) {

      trendLoading.value = false

    }

  }

}



async function prefetchTrendSnapshot(identityKey: string) {

  if (!identityKey) return

  const summaryCacheKey = normalizeIdentityCacheKey(identityKey)

  const trendCacheKey = buildTrendRequestKey(normalizeIdentityCacheKey(identityKey), 'cross_market')

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



async function findTrendReadyProductOption(currentIdentityKey: string) {

  const contextParams = buildFilterParams()

  const trendSeedKeywords = ['三黄鸡', '鸡', '肉', '鱼', '虾', '菜', '蛋', '豆油', '大米', '土豆']

  const getTrendCandidateScore = (item: ProductOptionItem) => {

    const label = `${item.price_identity_label || ''} ${item.price_identity_key || ''}`

    const cachedTrend = readLocalCache<ProductTrendRow[]>(

      PRODUCT_TREND_CACHE_KEY,

      buildTrendRequestKey(item.price_identity_key, 'cross_market'),

    )

    if (cachedTrend?.length) return 0

    if (item.price_identity_key === currentIdentityKey) return 1

    if (label.includes('三黄鸡')) return 2

    if (trendSeedKeywords.some((keyword) => label.includes(keyword)) && Number(item.site_count || 0) > 1) return 3

    if (trendSeedKeywords.some((keyword) => label.includes(keyword))) return 4

    if (Number(item.site_count || 0) > 1) return 5

    return 6

  }

  const candidates = [

    ...productOptions.value.filter((item) => item.price_identity_key === currentIdentityKey),

    ...productOptions.value.filter((item) => Number(item.site_count || 0) > 1 && item.price_identity_key !== currentIdentityKey),

    ...productOptions.value.filter((item) => item.price_identity_key !== currentIdentityKey),

  ]

  const uniqueCandidates = Array.from(

    new Map(candidates.map((item) => [item.price_identity_key, item])).values(),

  )

    .sort((left, right) => {

      const scoreDiff = getTrendCandidateScore(left) - getTrendCandidateScore(right)

      if (scoreDiff) return scoreDiff

      return Number(right.site_count || 0) - Number(left.site_count || 0)

    })

    .slice(0, 60)



  for (const option of uniqueCandidates) {

    const identityKey = option.price_identity_key

    if (!identityKey) continue

    const trendCacheKey = buildTrendRequestKey(normalizeIdentityCacheKey(identityKey), 'cross_market')

    const cachedTrend = readLocalCache<ProductTrendRow[]>(PRODUCT_TREND_CACHE_KEY, trendCacheKey)

    if (cachedTrend?.length) {

      return option

    }

    try {

      const trend = await fetchProductTrend(identityKey, { mode: 'cross_market', ...contextParams })

      const rows = trend.items ?? []

      if (rows.length) {

        writeLocalCache(PRODUCT_TREND_CACHE_KEY, trendCacheKey, rows)

        return option

      }

    } catch {

      // Continue scanning other real products; the active product can still fall back to its current行情快照.

    }

  }

  return null

}



async function prefetchTopTrendSnapshots(contextKey: string) {
  if (!productOptions.value.length) return
  if (activeTab.value !== 'trend' || selectedIdentityKey.value) return
  trendPrefetchContextKey = contextKey
  const keys = productOptions.value
    .slice(0, 3)
    .map((item) => item.price_identity_key)

    .filter(Boolean)

  await runPrefetchQueue(keys, contextKey)

}



async function prefetchNearbyTrendSnapshots(identityKey: string) {
  if (!identityKey || !productOptions.value.length) return
  if (trendLoading.value) return
  const contextKey = buildContextKey(buildFilterParams())
  const currentIndex = productOptions.value.findIndex((item) => item.price_identity_key === identityKey)
  if (currentIndex < 0) return
  const keys = productOptions.value
    .slice(Math.max(0, currentIndex - 1), currentIndex + 2)
    .map((item) => item.price_identity_key)
    .filter((item) => item !== identityKey)
    .filter(Boolean)
  await runPrefetchQueue(keys, contextKey)
}


async function runPrefetchQueue(identityKeys: string[], contextKey: string) {

  const uniqueKeys = Array.from(new Set(identityKeys.filter(Boolean)))

  if (!uniqueKeys.length) return

  trendPrefetchContextKey = contextKey

  const concurrency = 1
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



function getMenuPlanRowLabel(row?: MenuPlanRow | null) {
  return String(row?.ingredient_name || row?.product_label || row?.menu_name || '').trim()
}

function normalizeMenuProductText(value?: string | null) {
  return String(value || '')
    .replace(/\s*\|\s*.*/, '')
    .replace(/[（）()\[\]【】]/g, '')
    .trim()
    .toLowerCase()
}

function resolveMenuPlanIdentityKey(row?: MenuPlanRow | null) {
  const explicitKey = String(row?.price_identity_key || row?.identity_key || row?.product_identity_key || '').trim()
  if (explicitKey) return resolveCanonicalIdentityKey(explicitKey)
  const label = normalizeMenuProductText(getMenuPlanRowLabel(row))
  if (!label) return ''
  const matchedOption = productOptions.value.find((item) => {
    const optionLabel = normalizeMenuProductText(item.price_identity_label)
    const optionKey = normalizeMenuProductText(item.price_identity_key)
    return optionLabel === label || optionLabel.includes(label) || label.includes(optionLabel) || optionKey.includes(label)
  })
  return matchedOption?.price_identity_key || ''
}

function handleMenuPlanViewMarket(row: MenuPlanRow) {
  const label = getMenuPlanRowLabel(row)
  if (label) {
    filters.keyword = label
    selectedProductFallbackLabel.value = label
  }
  enterWorkspace('summary')
  ElMessage.success(label ? `已带入“${label}”查看行情` : '已切到汇总行情')
}

function handleMenuPlanFillSupplierPrice(row: MenuPlanRow) {
  const productLabel = getMenuPlanRowLabel(row)
  const identityKey = resolveMenuPlanIdentityKey(row)
  openSupplierBackend(false, {
    section: 'quote',
    source: 'menu_plan',
    productLabel,
    identityKey,
  })
}

function handleMenuPlanFillMissingQuotes() {
  const pendingPlanRow = planRows.value.find((item) => item.price_status !== '已匹配报价' && !isMenuPlanRowConfirmed(item)) || planRows.value[0]
  const firstIngredient = ingredientRows.value.find((item) => String(item.ingredient_name || '').trim())
  const productLabel = String(getMenuPlanRowLabel(pendingPlanRow) || firstIngredient?.ingredient_name || menuForm.menuText.split(/\r?\n/).find((line) => line.trim()) || '').trim()
  const identityKey = resolveMenuPlanIdentityKey(pendingPlanRow)
  openSupplierBackend(false, {
    section: 'quote',
    source: 'menu_plan',
    productLabel,
    identityKey,
  })
}

function handleMenuPlanConfirmRow(row: MenuPlanRow) {
  const rowKey = `${row.menu_name || ''}::${row.ingredient_name || ''}::${row.recommended_market || ''}`
  planRows.value = planRows.value.map((item) => {
    const itemKey = `${item.menu_name || ''}::${item.ingredient_name || ''}::${item.recommended_market || ''}`
    if (itemKey !== rowKey) return item
    return {
      ...item,
      price_status: item.price_status === '已匹配报价' ? '已匹配报价（已确认）' : '已确认',
      remarks: item.remarks ? `${item.remarks}；采购已确认` : '采购已确认',
    }
  })
  ElMessage.success(`${getMenuPlanRowLabel(row) || '该食材'}已标记确认`)
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

    const data = await generateMenuPlan(payload)
    let recommendation: Awaited<ReturnType<typeof fetchProcurementRecommendation>> | null = null
    try {
      recommendation = await fetchProcurementRecommendation(payload)
    } catch (recommendError) {
      ElMessage.warning(`采购建议暂未生成：${extractApiErrorDetail(recommendError) || '建议接口暂不可用'}`)
    }
    ingredientRows.value = data.ingredient_items ?? []
    planRows.value = data.procurement_plan ?? []
    procurementRecommendations.value = recommendation?.items ?? []
    ElMessage.success('采购方案已生成')
  } catch (error) {
    ElMessage.error(`采购方案生成失败：${extractApiErrorDetail(error) || '请确认 API 已启动'}`)
  } finally {
    menuPlanLoading.value = false

  }

}



watch([() => filters.province, () => filters.city], async () => {

  activeMarketCategory.value = '全部'

  productOptions.value = []

  productOptionsContextKey.value = ''

  selectedIdentityKey.value = ''

  selectedProductTouched.value = false

  selectedSiteName.value = ''

  selectedProductFallbackLabel.value = ''

  trendLoading.value = false

  trendPrefetchContextKey = ''

  await reloadAll()

})



watch(() => selectedCategorySourceName.value, () => {

  activeMarketCategory.value = '全部'

  void reloadLiancaiCategorySummary()

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
  if (suppressNextTrendWatch && identityKey !== prevIdentityKey) {
    suppressNextTrendWatch = false
    return
  }
  suppressNextTrendWatch = false
  await reloadTrend()
})

watch(selectedIdentityKey, async (identityKey, prevIdentityKey) => {
  if (activeTab.value !== 'summary') return
  if (!identityKey || identityKey === prevIdentityKey) return
  await syncSupplierSummaryRow(identityKey)
})


onMounted(async () => {
  if (shouldRedirectToStandaloneSupplier) {
    openSupplierBackend()
    return
  }
  const isMobileLanding = isMobileViewport.value && viewMode.value === 'landing'
  void restoreAuthSession()
  if (activeTab.value === 'trend') {
    if (trendDeepLinkLabel || trendDeepLinkTarget) {
      await ensureProductOptionsLoaded()
      await applyExplicitTrendTarget()
    } else {
      void ensureProductOptionsLoaded()
    }
    await activateTab('trend')
    await Promise.all([
      marketRows.value.length ? Promise.resolve() : reloadSummary(),
      reloadLocations(),
      reloadSalesAssets(),
      reloadSupplierOverview(),
      reloadSourceCoverage(),
      reloadLiancaiCategorySummary(),
      reloadCrawlStatus(),
    ])
  } else {
    await reloadSummary()
    void Promise.allSettled([
      ensureProductOptionsLoaded(),
      reloadLocations(),
      ...(isMobileLanding ? [] : [reloadSalesAssets()]),
      reloadSupplierOverview(),
      reloadSourceCoverage(),
      reloadLiancaiCategorySummary(),
      reloadCrawlStatus(),
    ]).then(() => {
      if (isMobileLanding) return
      const identityKey = selectedIdentityKey.value || pickPreferredProductOption(productOptions.value)?.price_identity_key || ''
      if (identityKey && activeTab.value !== 'trend') {
        void prefetchTrendSnapshot(identityKey)
      }
    })
  }
  if (crawlStatus.value?.is_running) {
    startCrawlPolling()
  }
  syncMobileAlertDraftFromSelection()
})


onBeforeUnmount(() => {

  stopCrawlPolling()

})

</script>



<style scoped>

.backend-entry-panel,

.backend-entry-copy,

.backend-entry-actions {

  display: grid;

  gap: 10px;

}



.backend-entry-panel.desktop {

  padding: 20px;

}



.backend-entry-copy h2 {

  margin: 0;

  color: var(--ink-900);

  letter-spacing: -0.03em;

}



.backend-entry-copy p:last-child {

  margin: 0;

  color: var(--ink-700);

  font-size: 14px;

  line-height: 1.6;

}



.backend-entry-meta {

  display: grid;

  grid-template-columns: repeat(3, minmax(0, 1fr));

  gap: 10px;

}



.backend-entry-pill {

  display: grid;

  gap: 4px;

  min-width: 0;

  padding: 12px 14px;

  border: 1px solid rgba(148, 163, 184, 0.18);

  border-radius: 16px;

  background: rgba(248, 250, 252, 0.84);

}



.backend-entry-pill span {

  color: var(--ink-500);

  font-size: 10px;

}



.backend-entry-pill strong {

  color: var(--ink-900);

  font-size: 14px;

  line-height: 1.45;

}



.backend-entry-actions {

  grid-template-columns: repeat(2, minmax(0, max-content));

  align-items: center;

}



.market-mobile-home,
.market-mobile-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  width: 100%;

  max-width: 100vw;

  box-sizing: border-box;

  overflow-x: hidden;

}



.market-mobile-home {

  gap: 10px;

  align-content: start;

  padding: 10px 10px 0;

  padding-bottom: calc(132px + env(safe-area-inset-bottom));

  background: #f1f5f9;

}



.market-mobile-section.compact-section {

  gap: 10px;

}



.market-mobile-shell {

  gap: 8px;

  align-content: start;

  padding: 10px 10px 0;

  padding-bottom: calc(132px + env(safe-area-inset-bottom));

}



.market-mobile-home-hero,

.market-mobile-lead-card {

  display: grid;

  gap: 10px;

}



.market-mobile-home-hero {

  padding: 10px 10px 12px;

  border: 1px solid rgba(203, 213, 225, 0.84);

  border-radius: 16px;

  background: #fff;

  box-shadow: none;

}



.market-mobile-workbench-section {

  position: relative;

  order: 1;

  overflow: hidden;

  border: 1px solid rgba(203, 213, 225, 0.76);

  background: #fff;

}



.market-mobile-workbench-section::before {

  content: "";

  position: absolute;

  top: 28px;

  left: 0;

  width: 3px;

  height: 64px;

  border-radius: 999px;

  background: #2563eb;

}



.market-mobile-workbench-head {

  position: relative;

  z-index: 1;

  display: grid;

  grid-template-columns: minmax(0, 1fr) auto;

  align-items: start;

  gap: 12px;

}



.market-mobile-workbench-title {

  display: grid;

  grid-template-columns: 34px minmax(0, 1fr);

  align-items: center;

  gap: 9px;

  min-width: 0;

}



.market-mobile-workbench-title > div {

  display: grid;

  gap: 4px;

  min-width: 0;

}



.market-mobile-title-icon {

  display: grid;

  place-items: center;

  width: 34px;

  height: 34px;

  border: 1px solid rgba(37, 99, 235, 0.16);

  border-radius: 12px;

  background: #eff6ff;

  color: #2563eb;

  font-size: 15px;

  font-weight: 900;

  box-shadow: none;

}



.market-mobile-workbench-title h2 {

  margin: 0;

  color: var(--ink-900);

  font-size: 18px;

  line-height: 1.18;

}



.market-mobile-workbench-title small {

  display: inline-flex;

  align-items: center;

  width: fit-content;

  min-height: 24px;

  padding: 0 9px;

  border-radius: 999px;

  background: rgba(255, 255, 255, 0.74);

  color: var(--ink-600);

  font-size: 10px;

  font-weight: 800;

}



.market-mobile-workbench-badge {

  display: grid;

  justify-items: center;

  gap: 2px;

  min-width: 54px;

  padding: 6px 8px;

  border: 1px solid rgba(239, 68, 68, 0.18);

  border-radius: 12px;

  background: #fff7ed;

  box-shadow: none;

}



.market-mobile-workbench-badge span {

  color: var(--ink-500);

  font-size: 10px;

  font-weight: 800;

  white-space: nowrap;

}



.market-mobile-workbench-badge strong {

  color: #ef4444;

  font-size: 17px;

  line-height: 1;

}



.market-mobile-workbench-metrics {

  position: relative;

  z-index: 1;

  display: grid;

  grid-template-columns: repeat(3, minmax(0, 1fr));

  gap: 6px;

  padding: 6px;

  border: 1px solid rgba(226, 232, 240, 0.9);

  border-radius: 14px;

  background: #f8fafc;

}



.market-mobile-workbench-metrics span {

  display: inline-flex;

  align-items: baseline;

  justify-content: center;

  gap: 4px;

  min-width: 0;

  min-height: 32px;

  padding: 0 5px;

  border: none;

  border-radius: 10px;

  background: #fff;

  color: var(--ink-500);

  font-size: 10px;

  font-weight: 800;

}



.market-mobile-workbench-metrics strong {

  color: var(--ink-900);

  font-size: 14px;

  letter-spacing: -0.03em;

}



.market-mobile-product-section {

  order: 2;

}



.market-mobile-advice-section {

  order: 3;

}



.market-mobile-category-section {

  order: 4;

}



.market-mobile-shortcut-section {

  order: 5;

}



.market-mobile-source-section {

  order: 6;

}



.market-mobile-system-section {

  order: 7;

}



.market-mobile-bottom-nav {

  order: 8;

}



.market-mobile-appbar {

  display: grid;

  grid-template-columns: minmax(0, 1fr) minmax(82px, 116px) 34px;

  align-items: center;

  gap: 10px;

}



.market-mobile-brand,

.market-mobile-location-button,

.market-mobile-message-button {

  display: inline-flex;

  align-items: center;

}



.market-mobile-brand {

  gap: 8px;

  min-width: 0;

  color: var(--ink-900);

  font-size: 15px;

  font-weight: 800;

}



.market-mobile-brand > div {

  display: grid;

  gap: 2px;

  min-width: 0;

}



.market-mobile-brand small {

  color: var(--ink-500);

  font-size: 10px;

  font-weight: 700;

  line-height: 1;

}



.market-mobile-brand-mark {

  display: grid;

  place-items: center;

  width: 28px;

  height: 28px;

  border-radius: 10px;

  background: linear-gradient(135deg, #2563eb, #1d4ed8);

  color: #fff;

  font-size: 15px;

  box-shadow: 0 10px 18px rgba(37, 99, 235, 0.2);

}



.market-mobile-location-button,

.market-mobile-message-button {

  min-height: 34px;

  border: 1px solid rgba(148, 163, 184, 0.16);

  background: rgba(255, 255, 255, 0.92);

  font: inherit;

  cursor: pointer;

}



.market-mobile-location-button {

  gap: 6px;

  min-width: 0;

  max-width: 116px;

  padding: 0 10px;

  border-radius: 999px;

  color: var(--ink-700);

  font-size: 11px;

  font-weight: 700;

  overflow: hidden;

  text-overflow: ellipsis;

  white-space: nowrap;

}



.market-mobile-location-dot {

  width: 8px;

  height: 8px;

  border-radius: 999px;

  background: #2563eb;

  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);

}



.market-mobile-message-button {

  position: relative;

  justify-content: center;

  width: 34px;

  border-radius: 12px;

}



.market-mobile-message-button span {

  width: 15px;

  height: 13px;

  border: 1.8px solid #1f2d44;

  border-radius: 6px;

}



.market-mobile-message-button b {

  position: absolute;

  top: -6px;

  right: -5px;

  display: grid;

  place-items: center;

  min-width: 18px;

  height: 18px;

  padding: 0 4px;

  border-radius: 999px;

  background: #ef4444;

  color: #fff;

  font-size: 10px;

  line-height: 1;

}



.market-mobile-home-hero,

.market-mobile-lead-card,

.market-mobile-home .panel {

  border-radius: 20px;

  padding: 14px;

}



.market-mobile-home-hero {

  border: 1px solid rgba(203, 213, 225, 0.84);

  background: #fff;

  box-shadow: none;

}



.market-mobile-shell-head {

  display: grid;

  grid-template-columns: 38px minmax(0, 1fr) 38px;

  align-items: center;

  gap: 8px;

  min-height: 42px;

  padding: 0 0 4px;

  border: 0;

  border-radius: 0;

  background: transparent;

  box-shadow: none;

}



.market-mobile-home-topline,

.market-mobile-source-head {

  display: flex;

  align-items: flex-start;

  justify-content: space-between;

  gap: 12px;

}



.market-mobile-section-head {

  display: grid;

  position: relative;

  grid-template-columns: minmax(0, 1fr) auto;

  align-items: center;

  gap: 10px;

  min-height: 44px;

  padding: 7px 10px 7px 12px;

  border: 1px solid rgba(226, 232, 240, 0.78);

  border-radius: 14px;

  background: #fff;

}



.market-mobile-section-head::before {

  content: "";

  position: absolute;

  top: 12px;

  left: 0;

  width: 3px;

  height: 32px;

  border-radius: 999px;

  background: var(--head-accent, #2563eb);

}



.market-mobile-head-icon {

  display: none;

}



.market-mobile-section-head > div {

  display: grid;

  gap: 2px;

  min-width: 0;

}



.market-mobile-section-head.price-head { --head-accent: #2563eb; }

.market-mobile-section-head.advice-head { --head-accent: #f97316; }

.market-mobile-section-head.category-head { --head-accent: #16a34a; }

.market-mobile-section-head.shortcut-head { --head-accent: #2563eb; }

.market-mobile-section-head.source-head { --head-accent: #0891b2; }

.market-mobile-section-head.system-head { --head-accent: #475569; }



.market-mobile-section-head.price-head,

.market-mobile-section-head.advice-head,

.market-mobile-section-head.category-head,

.market-mobile-section-head.shortcut-head,

.market-mobile-section-head.source-head,

.market-mobile-section-head.system-head {

  background: #fff;

}



.market-mobile-section-head > span:not(.market-mobile-head-icon),

.market-mobile-section-head .market-mobile-inline-link {

  flex: 0 0 auto;

  min-height: 26px;

  padding: 0 9px;

  border: 1px solid color-mix(in srgb, var(--head-accent, #2563eb) 22%, #e2e8f0);

  border-radius: 999px;

  background: rgba(255, 255, 255, 0.76);

  color: var(--head-accent, #2563eb);

  font-size: 10px;

  font-weight: 800;

  white-space: nowrap;

}



.market-mobile-kicker {

  margin: 0;

  color: color-mix(in srgb, var(--head-accent, var(--accent-blue-bright)) 86%, #0f172a);

  font-size: 10px;

  font-weight: 800;

  letter-spacing: 0.08em;

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

  font-size: 17px;

  line-height: 1.14;

}



.market-mobile-shell h1 {

  font-size: 17px;

  line-height: 1.14;

}



.market-mobile-section-head h2 {

  margin-top: 1px;

  overflow: hidden;

  font-size: 15px;

  line-height: 1.16;

  letter-spacing: -0.03em;

  text-overflow: ellipsis;

  white-space: nowrap;

}



.market-mobile-city-pill,

.market-mobile-accent-pill {

  display: inline-flex;

  align-items: center;

  justify-content: center;

  min-height: 30px;

  padding: 0 10px;

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

  font-size: 12px;

  line-height: 1.5;

}



.market-mobile-shell-copy {

  display: grid;

  gap: 2px;

  min-width: 0;

  text-align: center;

}



.market-mobile-shell-copy p {

  display: none;

  font-size: 11px;

  line-height: 1.35;

}



.market-mobile-search-row,

.market-mobile-lead-actions {

  display: grid;

  gap: 10px;

}



.market-mobile-search-row :deep(.el-input__wrapper) {

  min-height: 38px;

  border-radius: 12px;

  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.16) inset;

}



.market-mobile-context-row {

  display: grid;

  grid-template-columns: repeat(3, minmax(0, 1fr));

  gap: 8px;

  padding: 0 2px 2px;

}



.market-mobile-stat-grid,

.market-mobile-task-grid,

.market-mobile-source-grid,

.market-mobile-product-feed {

  display: grid;

  gap: 8px;

}



.market-mobile-stat-grid {

  display: grid;

  grid-template-columns: repeat(3, minmax(0, 1fr));

}



.market-mobile-task-grid {

  display: grid;

  grid-template-columns: repeat(3, minmax(0, 1fr));

  gap: 9px;

}



.market-mobile-stat-card,

.market-mobile-task-card,

.market-mobile-system-card,

.market-mobile-shortcut-card,

.market-mobile-recent-card,

.market-mobile-source-card,

.market-mobile-product-card,

.market-mobile-context-pill {

  display: grid;

  gap: 4px;

  min-width: 0;

  padding: 9px;

  border-radius: 16px;

  border: 1px solid rgba(148, 163, 184, 0.16);

  background: rgba(248, 250, 252, 0.86);

}



.market-mobile-stat-card,

.market-mobile-task-card {

  width: auto;

  max-width: 100%;

  min-width: 0;

  box-sizing: border-box;

}



.market-mobile-stat-card strong,

.market-mobile-stat-card small,

.market-mobile-task-card strong,

.market-mobile-task-card small {

  min-width: 0;

  overflow: hidden;

  text-overflow: ellipsis;

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

.market-mobile-task-card strong,

.market-mobile-system-card strong,

.market-mobile-source-card strong,

.market-mobile-context-pill strong,

.market-mobile-product-card strong {

  color: var(--ink-900);

  font-size: 12px;

  line-height: 1.3;

}



.market-mobile-task-card strong {

  text-align: center;

}



.market-mobile-chip-strip,

.market-mobile-system-strip,

.market-mobile-tab-strip {

  display: flex;

  gap: 8px;

  overflow-x: auto;

  padding-bottom: 2px;

}



.market-mobile-system-strip {

  padding: 8px;

  border: 1px solid rgba(148, 163, 184, 0.14);

  border-radius: 18px;

  background: rgba(241, 245, 249, 0.72);

}



.market-mobile-chip,

.market-mobile-tab-button,

.market-mobile-bottom-item,

.market-mobile-external-entry,

.market-mobile-back-button,

.market-mobile-task-card,

.market-mobile-system-card,

.market-mobile-shortcut-card,

.market-mobile-recent-card,

.market-mobile-product-card {

  font: inherit;

  cursor: pointer;

}



.market-mobile-task-card,

.market-mobile-system-card,

.market-mobile-shortcut-card,

.market-mobile-recent-card {

  text-align: left;

  transition:

    transform var(--transition-fast),

    box-shadow var(--transition-fast),

    border-color var(--transition-fast);

}



.market-mobile-task-card.primary {

  border-color: rgba(37, 99, 235, 0.22);

  background: #eff6ff;

}



.market-mobile-task-card {

  position: relative;

  display: grid;

  align-content: center;

  min-height: 54px;

  padding: 10px;

  border-color: rgba(203, 213, 225, 0.78);

  border-radius: 14px;

  background: #fff;

  box-shadow: none;

  overflow: hidden;

}



.market-mobile-task-card.warning {

  border-color: rgba(239, 68, 68, 0.22);

  background: #fff7ed;

}



.market-mobile-task-card > b {

  position: absolute;

  right: 9px;

  bottom: 9px;

  display: grid;

  place-items: center;

  min-width: 18px;

  height: 18px;

  padding: 0 4px;

  border-radius: 999px;

  background: #ef4444;

  color: #fff;

  font-size: 10px;

}



.market-mobile-task-icon {

  display: none;

}



.market-mobile-task-icon.trend {

  background: rgba(37, 99, 235, 0.1);

}



.market-mobile-task-icon.alert {

  background: rgba(254, 226, 226, 0.9);

  color: #ef4444;

}



.market-mobile-system-card {

  flex: 0 0 136px;

  min-height: 66px;

  padding: 9px 10px;

  border-radius: 14px;

  background: rgba(255, 255, 255, 0.72);

}



.market-mobile-system-card.primary {

  border-color: rgba(37, 99, 235, 0.16);

  background: rgba(255, 255, 255, 0.92);

}



.market-mobile-system-card span {

  color: var(--ink-500);

  font-size: 10px;

}



.market-mobile-task-card small,

.market-mobile-system-card small {

  color: var(--ink-600);

  font-size: 10px;

  line-height: 1.45;

  overflow-wrap: anywhere;

}



.market-mobile-subsection {

  display: grid;

  gap: 8px;

}



.market-mobile-subhead {

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 10px;

  min-height: 30px;

  padding: 0 2px;

}



.market-mobile-subhead strong {

  position: relative;

  padding-left: 12px;

  color: var(--ink-900);

  font-size: 13px;

}



.market-mobile-subhead strong::before {

  content: "";

  position: absolute;

  left: 0;

  top: 50%;

  width: 6px;

  height: 6px;

  border-radius: 999px;

  background: #2563eb;

  transform: translateY(-50%);

}



.market-mobile-subhead small {

  padding: 4px 8px;

  border-radius: 999px;

  background: #f1f5f9;

  color: var(--ink-500);

  font-size: 10px;

  font-weight: 800;

}



.market-mobile-shortcut-strip,

.market-mobile-recent-strip-row {

  display: flex;

  gap: 10px;

  overflow-x: auto;

  padding-bottom: 2px;

}



.market-mobile-shortcut-card {

  background: rgba(255, 255, 255, 0.94);

}



.market-mobile-shortcut-card.compact,

.market-mobile-recent-card.compact {

  flex: 0 0 150px;

  min-height: 78px;

  padding: 10px;

  border-radius: 15px;

  background: linear-gradient(180deg, #fff, #f8fafc);

  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.035);

}



.market-mobile-shortcut-card span {

  color: var(--accent-blue);

  font-size: 10px;

  font-weight: 700;

}



.market-mobile-shortcut-card small {

  color: var(--ink-600);

  font-size: 11px;

  line-height: 1.45;

}



.market-mobile-recent-card {

  background: rgba(248, 250, 252, 0.9);

}



.market-mobile-recent-card span {

  color: var(--ink-500);

  font-size: 10px;

}



.market-mobile-recent-card small {

  color: var(--ink-600);

  font-size: 11px;

  line-height: 1.45;

}



.market-mobile-task-card:focus-visible,

.market-mobile-system-card:focus-visible,

.market-mobile-shortcut-card:focus-visible,

.market-mobile-recent-card:focus-visible,

.market-mobile-task-card:active {

  outline: none;

  transform: translateY(-1px);

  border-color: rgba(37, 99, 235, 0.24);

  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.08);

}



.market-mobile-system-card:active {

  outline: none;

  transform: translateY(-1px);

  border-color: rgba(22, 163, 74, 0.24);

  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.08);

}



.market-mobile-shortcut-card:active {

  outline: none;

  transform: translateY(-1px);

  border-color: rgba(37, 99, 235, 0.24);

  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.08);

}



.market-mobile-recent-card:active {

  outline: none;

  transform: translateY(-1px);

  border-color: rgba(37, 99, 235, 0.24);

  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.08);

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

  flex: 0 0 auto;

  min-width: 82px;

  min-height: 38px;

  padding: 0 14px;

  border-radius: 999px;

  font-size: 12px;

  white-space: nowrap;

  touch-action: manipulation;

}



.market-mobile-back-button {

  align-self: start;

  min-height: 30px;

  padding: 0 10px;

  border-radius: 10px;

  font-size: 11px;

  font-weight: 700;

  white-space: nowrap;

}



.market-mobile-tab-button.active,

.market-mobile-bottom-item.active {

  color: #eff6ff;

  background: linear-gradient(135deg, rgba(30, 64, 175, 0.96), rgba(37, 99, 235, 0.92));

  border-color: transparent;

  box-shadow: 0 14px 24px rgba(30, 64, 175, 0.18);

}



.market-mobile-back-button {

  color: var(--ink-700);

  background: rgba(255, 255, 255, 0.86);

  box-shadow: none;

}



.market-mobile-back-icon {

  align-self: center;

  justify-self: start;

  width: 34px;

  height: 34px;

  min-height: 34px;

  padding: 0;

  border: 0;

  background: transparent;

  color: #0f172a;

  font-size: 28px;

  font-weight: 400;

  line-height: 1;

}



.market-mobile-source-grid {

  grid-template-columns: repeat(2, minmax(0, 1fr));

}



.market-mobile-source-section {

  gap: 10px;

}



.market-mobile-source-section.pc-like,

.market-mobile-product-section.pc-like {

  border: 1px solid rgba(203, 213, 225, 0.72);

  background: rgba(255, 255, 255, 0.98);

}



.market-mobile-pc-filter {

  display: flex;

  gap: 8px;

  overflow-x: auto;

  padding: 2px 0 4px;

}



.market-mobile-pc-filter button,

.market-mobile-pc-table-row {

  border: 1px solid rgba(203, 213, 225, 0.8);

  background: #fff;

  font: inherit;

  cursor: pointer;

  touch-action: manipulation;

}



.market-mobile-pc-filter button {

  flex: 0 0 auto;

  display: inline-flex;

  align-items: center;

  gap: 8px;

  min-height: 34px;

  padding: 0 11px;

  border-radius: 10px;

  color: var(--ink-700);

  font-size: 11px;

  font-weight: 700;

  white-space: nowrap;

}



.market-mobile-pc-filter button small {

  min-width: 18px;

  padding: 2px 5px;

  border-radius: 999px;

  background: rgba(241, 245, 249, 0.94);

  color: var(--ink-500);

  font-size: 10px;

  text-align: center;

}



.market-mobile-pc-filter button.active {

  border-color: rgba(37, 99, 235, 0.7);

  background: #eff6ff;

  color: #1d4ed8;

}



.market-mobile-pc-filter button.active small {

  background: #2563eb;

  color: #fff;

}



.market-mobile-pc-table,

.market-mobile-summary-table {

  display: grid;

  overflow: hidden;

  border: 1px solid rgba(226, 232, 240, 0.94);

  border-radius: 14px;

  background: #fff;

}



.market-mobile-pc-table-head,

.market-mobile-pc-table-row,

.market-mobile-summary-table-head,

.market-mobile-summary-table-row {

  display: grid;

  grid-template-columns: minmax(70px, 1.1fr) minmax(76px, 1.1fr) 56px 44px;

  align-items: center;

  gap: 8px;

  min-width: 0;

  padding: 9px 10px;

}



.market-mobile-pc-table-head,

.market-mobile-summary-table-head {

  background: #f8fafc;

  color: var(--ink-500);

  font-size: 10px;

  font-weight: 800;

}



.market-mobile-pc-table-row,

.market-mobile-summary-table-row {

  width: 100%;

  border-width: 1px 0 0;

  border-color: rgba(226, 232, 240, 0.94);

  border-radius: 0;

  color: var(--ink-700);

  text-align: left;

}



.market-mobile-pc-table-row:focus-visible,

.market-mobile-pc-table-row:active,

.market-mobile-summary-table-row:focus-visible,

.market-mobile-summary-table-row:active {

  outline: none;

  background: #eff6ff;

}



.market-mobile-pc-table-row strong,

.market-mobile-pc-table-row span,

.market-mobile-summary-table-row strong,

.market-mobile-summary-table-row span {

  min-width: 0;

  overflow: hidden;

  text-overflow: ellipsis;

  white-space: nowrap;

}



.market-mobile-pc-table-row strong,

.market-mobile-summary-table-row strong {

  color: var(--ink-900);

  font-size: 12px;

}



.market-mobile-pc-table-row span,

.market-mobile-summary-table-row span {

  color: var(--ink-600);

  font-size: 11px;

}



.market-mobile-pc-table-row b,

.market-mobile-summary-table-row b {

  color: #1d4ed8;

  font-size: 12px;

}



.market-mobile-pc-table-row em,

.market-mobile-summary-table-row em {

  color: #2563eb;

  font-size: 11px;

  font-style: normal;

  font-weight: 800;

}



.market-mobile-pc-empty {

  display: grid;

  gap: 4px;

  padding: 16px 12px;

  text-align: center;

}



.market-mobile-pc-empty strong {

  color: var(--ink-800);

  font-size: 13px;

}



.market-mobile-pc-empty span {

  color: var(--ink-500);

  font-size: 11px;

}



.market-mobile-source-section .market-mobile-source-card {

  gap: 6px;

  padding: 11px 12px;

  border-radius: 16px;

  background: rgba(255, 255, 255, 0.9);

}



.market-mobile-source-section .market-mobile-source-card p {

  font-size: 12px;

  line-height: 1.45;

}



.market-mobile-source-card small,

.market-mobile-shell-copy p,

.market-mobile-context-pill strong {

  white-space: normal;

}



.market-mobile-context-pill {

  min-width: 0;

  padding: 10px 12px;

}



.market-mobile-product-card {

  grid-template-columns: 1fr;

  gap: 10px;

  padding: 12px;

  border-color: rgba(203, 213, 225, 0.84);

  background: rgba(255, 255, 255, 0.96);

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

.market-mobile-product-meta,

.market-mobile-product-middle {

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 8px;

}



.market-mobile-product-top {

  display: grid;

  grid-template-columns: auto minmax(0, 1fr) auto;

}



.market-mobile-product-top div {

  display: grid;

  gap: 3px;

  min-width: 0;

}



.market-mobile-product-top em {

  color: #16a34a;

  font-size: 11px;

  font-style: normal;

  font-weight: 700;

}



.market-mobile-product-price {

  display: flex;

  align-items: baseline;

  gap: 8px;

}



.market-mobile-product-middle b {

  color: #12213c;

  font-size: 20px;

  line-height: 1;

}



.market-mobile-product-middle button {

  min-height: 30px;

  padding: 0 12px;

  border: 1px solid rgba(37, 99, 235, 0.34);

  border-radius: 8px;

  background: rgba(239, 246, 255, 0.86);

  color: #2563eb;

  font-size: 11px;

  font-weight: 700;

}



.market-mobile-thumb {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23f0fdf4'/%3E%3Cpath d='M12 28c7-12 17-15 25-14-1 9-5 18-18 21 1-5 5-10 12-15-8 3-13 8-16 17' fill='%2316a34a'/%3E%3C/svg%3E");
  position: relative;
  display: block;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  overflow: hidden;
  background: #f8fafc var(--thumb-image) center / cover no-repeat;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.6), 0 5px 10px rgba(15, 23, 42, 0.08);
}

.market-mobile-thumb.leaf {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23f0fdf4'/%3E%3Cpath d='M12 28c7-12 17-15 25-14-1 9-5 18-18 21 1-5 5-10 12-15-8 3-13 8-16 17' fill='%2316a34a'/%3E%3C/svg%3E");
}

.market-mobile-thumb.fish {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23e0f2fe'/%3E%3Cpath d='M10 25c7-8 17-10 26 0-9 10-19 8-26 0Z' fill='%230ea5e9'/%3E%3Cpath d='M35 25l7-6v12l-7-6Z' fill='%230284c7'/%3E%3Ccircle cx='17' cy='23' r='2' fill='%23fff'/%3E%3C/svg%3E");
}

.market-mobile-thumb.egg,
.market-mobile-thumb.potato {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff7ed'/%3E%3Cellipse cx='19' cy='26' rx='8' ry='11' fill='%23f8fafc'/%3E%3Cellipse cx='30' cy='23' rx='8' ry='11' fill='%23fde68a'/%3E%3C/svg%3E");
}

.market-mobile-thumb.cucumber {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23ecfccb'/%3E%3Cpath d='M13 29c5-11 16-17 25-15-3 11-12 18-25 15Z' fill='%2322c55e'/%3E%3Cpath d='M18 26c4-4 9-7 15-9' stroke='%23dcfce7' stroke-width='3' stroke-linecap='round'/%3E%3C/svg%3E");
}

.market-mobile-thumb.meat {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff1f2'/%3E%3Cpath d='M13 30c2-9 9-15 18-16 4 1 6 4 5 8-1 8-10 14-18 12-3-1-5-2-5-4Z' fill='%23fb7185'/%3E%3Ccircle cx='29' cy='22' r='5' fill='%23ffe4e6'/%3E%3C/svg%3E");
}

.market-mobile-thumb.fruit {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff7ed'/%3E%3Ccircle cx='22' cy='27' r='10' fill='%23f97316'/%3E%3Ccircle cx='31' cy='25' r='8' fill='%23facc15'/%3E%3Cpath d='M26 14c4-3 8-3 11 0-4 1-8 3-10 7' fill='%2322c55e'/%3E%3C/svg%3E");
}

.market-mobile-thumb.soy,
.market-mobile-thumb.grain {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fefce8'/%3E%3Cellipse cx='17' cy='25' rx='6' ry='9' fill='%23eab308'/%3E%3Cellipse cx='26' cy='23' rx='6' ry='9' fill='%23facc15'/%3E%3Cellipse cx='33' cy='28' rx='5' ry='8' fill='%23ca8a04'/%3E%3C/svg%3E");
}

.market-mobile-thumb.dry {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff7ed'/%3E%3Cpath d='M16 15c9 2 15 8 17 17-9-1-16-7-17-17Z' fill='%23dc2626'/%3E%3Cpath d='M25 13c4 5 6 11 5 18' stroke='%23b91c1c' stroke-width='3' stroke-linecap='round'/%3E%3C/svg%3E");
}

.market-mobile-thumb.frozen {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23eff6ff'/%3E%3Cpath d='M24 11v26M13 18l22 12M35 18 13 30' stroke='%232563eb' stroke-width='3' stroke-linecap='round'/%3E%3Ccircle cx='24' cy='24' r='4' fill='%2393c5fd'/%3E%3C/svg%3E");
}

.market-mobile-thumb.drink {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23ecfeff'/%3E%3Cpath d='M18 15h13l-2 22h-9l-2-22Z' fill='%2306b6d4'/%3E%3Cpath d='M19 20h11' stroke='%23cffafe' stroke-width='3'/%3E%3Cpath d='M31 14l4-4' stroke='%230e7490' stroke-width='3' stroke-linecap='round'/%3E%3C/svg%3E");
}

.market-mobile-thumb.kitchen {
  --thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23f1f5f9'/%3E%3Cpath d='M16 19h17l-2 18H18l-2-18Z' fill='%2364748b'/%3E%3Cpath d='M14 17h21M20 17c0-4 9-4 9 0' stroke='%23334155' stroke-width='3' stroke-linecap='round' fill='none'/%3E%3C/svg%3E");
}


.market-mobile-inline-link {

  display: inline-flex;

  align-items: center;

  justify-content: center;

  font: inherit;

  cursor: pointer;

}



.market-mobile-advice-card {

  position: relative;

  display: grid;

  gap: 6px;

  padding: 12px 14px 12px 32px;

  border: 1px solid rgba(148, 163, 184, 0.16);

  border-radius: 14px;

  background: rgba(255, 255, 255, 0.95);

}



.market-mobile-advice-card span {

  position: absolute;

  left: 14px;

  top: 17px;

  width: 8px;

  height: 8px;

  border-radius: 999px;

  background: #16a34a;

}



.market-mobile-advice-card strong {

  color: var(--ink-900);

  font-size: 13px;

}



.market-mobile-advice-card p {

  margin: 0;

  color: var(--ink-600);

  font-size: 11px;

  line-height: 1.45;

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

  position: relative;

  z-index: 1;

  display: grid;

  gap: 10px;

  margin-top: 8px;

  min-width: 0;

  padding-bottom: calc(188px + env(safe-area-inset-bottom));

}



.market-mobile-shell .backend-entry-panel {

  padding: 14px;

}



.market-mobile-bottom-nav {

  position: fixed;

  left: 0;

  right: 0;

  bottom: 0;

  z-index: 100;

  display: grid;

  grid-template-columns: repeat(4, minmax(0, 1fr));

  gap: 6px;

  padding: 6px 10px calc(6px + env(safe-area-inset-bottom, 0px));

  border-top: 1px solid rgba(226, 232, 240, 0.96);

  background: rgba(255, 255, 255, 0.98);

  backdrop-filter: blur(14px);

  box-shadow: 0 -6px 18px rgba(15, 23, 42, 0.06);

}



.market-mobile-bottom-item {

  position: relative;

  z-index: 1;

  touch-action: manipulation;

}



.market-mobile-alert-page {
  display: grid;
  gap: 12px;
  padding: 0 0 calc(72px + env(safe-area-inset-bottom));
}

.market-mobile-alert-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  min-height: 96px;
  padding: 16px;
  border: 1px solid rgba(203, 213, 225, 0.72);
  border-radius: 22px;
  background:
    radial-gradient(circle at 90% 0%, rgba(96, 165, 250, 0.16), transparent 34%),
    linear-gradient(135deg, #f6f9ff 0%, #ffffff 56%, #f8fafc 100%);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}

.market-mobile-alert-hero div {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.market-mobile-alert-hero h2 {
  margin: 0;
  color: #0f172a;
  font-size: 20px;
  line-height: 1.12;
  letter-spacing: -0.04em;
}

.market-mobile-alert-hero span {
  color: #475569;
  font-size: 12px;
  line-height: 1.45;
}

.market-mobile-alert-hero > strong {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 62px;
  height: 62px;
  border-radius: 20px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  font-size: 28px;
  line-height: 1;
  box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
}

.market-mobile-alert-hero > strong::after {
  content: "待处理";
  margin-top: 3px;
  color: rgba(255, 255, 255, 0.82);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0;
}

.market-mobile-alert-pills {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.market-mobile-alert-pills article {
  min-width: 0;
  padding: 10px 11px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
}

.market-mobile-alert-pills strong,
.market-mobile-alert-pills span {
  display: block;
}

.market-mobile-alert-pills strong {
  color: #0f172a;
  font-size: 18px;
  line-height: 1;
}

.market-mobile-alert-pills span {
  margin-top: 5px;
  color: #64748b;
  font-size: 10px;
  font-weight: 700;
}

.market-mobile-alert-pills .up strong { color: #dc2626; }
.market-mobile-alert-pills .down strong { color: #16a34a; }

.market-mobile-alert-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

.market-mobile-alert-list {
  display: grid;
  gap: 10px;
}

.market-mobile-alert-row {
  position: relative;
  display: grid;
  gap: 8px;
  min-width: 0;
  padding: 12px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
}

.market-mobile-alert-row::before {
  content: "";
  position: absolute;
  inset: 12px auto 12px 0;
  width: 4px;
  border-radius: 999px;
  background: #f97316;
}

.market-mobile-alert-row.up::before { background: #ef4444; }
.market-mobile-alert-row.down::before { background: #16a34a; }

.market-mobile-alert-row-main {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.market-mobile-alert-thumb-shell {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  overflow: hidden;
  border-radius: 15px;
  background: linear-gradient(145deg, #f8fafc, #eef4ff);
  box-shadow: inset 0 0 0 1px rgba(219, 234, 254, 0.95);
}

.market-mobile-alert-thumb-image {
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

.market-image-preview {
  max-width: 100%;
  max-height: 76vh;
  border-radius: 12px;
}

.market-mobile-alert-row .market-mobile-thumb {
  width: 32px;
  height: 32px;
  border-radius: 10px;
}

.market-mobile-alert-row-main div {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.market-mobile-alert-row strong {
  overflow: hidden;
  color: #0f172a;
  font-size: 15px;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.market-mobile-alert-row small,
.market-mobile-alert-row p,
.market-mobile-alert-row time {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.35;
}

.market-mobile-alert-row small,
.market-mobile-alert-row p {
  display: -webkit-box;
  overflow: hidden;
  white-space: normal;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.market-mobile-alert-row p {
  padding-left: 2px;
  color: #334155;
  font-weight: 700;
}

.market-mobile-alert-row em {
  justify-self: end;
  max-width: 72px;
  padding: 6px 9px;
  border-radius: 999px;
  background: #fff7ed;
  color: #f97316;
  font-size: 11px;
  font-style: normal;
  font-weight: 900;
  line-height: 1;
  white-space: nowrap;
}

.market-mobile-alert-row.down em {
  background: #ecfdf5;
  color: #16a34a;
}

.market-mobile-alert-row.up em {
  background: #fef2f2;
  color: #dc2626;
}

.market-mobile-alert-row footer {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  align-items: center;
}

.market-mobile-alert-row button {
  min-width: 0;
  min-height: 44px;
  padding: 0 8px;
  border: 1px solid #dbe4ef;
  border-radius: 12px;
  background: #fff;
  color: #1e40af;
  font: inherit;
  font-size: 12px;
  font-weight: 900;
  touch-action: manipulation;
}

.market-mobile-alert-row button.primary {
  border-color: transparent;
  background: #2563eb;
  color: #fff;
}

.market-mobile-alert-row time {
  grid-column: 1 / -1;
  justify-self: end;
  color: #94a3b8;
  font-size: 11px;
}

.market-mobile-alert-empty {
  display: grid;
  gap: 5px;
  min-height: 76px;
  padding: 14px;
  border: 1px dashed rgba(96, 165, 250, 0.35);
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.92), rgba(255, 255, 255, 0.98));
}

.market-mobile-alert-empty strong {
  color: #0f172a;
  font-size: 14px;
  line-height: 1.25;
}

.market-mobile-alert-empty p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.market-mobile-alert-rule-card.collapsed {
  gap: 8px;
  box-shadow: none;
}

.market-mobile-rule-toggle {
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: 999px;
  background: #eff6ff;
  color: #2563eb;
  font: inherit;
  font-size: 12px;
  font-weight: 900;
  touch-action: manipulation;
}

.market-mobile-rule-summary {
  margin: 0;
  padding: 12px 14px;
  border: 1px dashed rgba(96, 165, 250, 0.28);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.9), rgba(255, 255, 255, 0.96));
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.market-mobile-rule-form {
  display: grid;
  gap: 8px;
  max-height: min(58vh, 430px);
  overflow-y: auto;
  padding-bottom: 6px;
  overscroll-behavior: contain;
}

.market-mobile-rule-form label {
  display: grid;
  grid-template-columns: 60px minmax(0, 1fr);
  align-items: center;
  min-height: 44px;
  padding: 0 12px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 14px;
  background: #fbfdff;
}

.market-mobile-rule-form span {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.market-mobile-rule-form strong {
  overflow: hidden;
  color: #0f172a;
  font-size: 13px;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.market-mobile-rule-form select,
.market-mobile-rule-form input {
  width: 100%;
  min-width: 0;
  border: none;
  background: transparent;
  color: #0f172a;
  font: inherit;
  font-size: 13px;
  line-height: 1.25;
  outline: none;
}

.market-mobile-rule-form button {
  position: sticky;
  bottom: 0;
  min-height: 48px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  font: inherit;
  font-size: 14px;
  font-weight: 900;
}

.market-mobile-bottom-item {

  display: grid;

  justify-items: center;

  align-content: center;

  gap: 3px;

  min-height: 48px;

  padding: 5px 6px;

  border: none;

  border-radius: 12px;

  background: transparent;

  color: var(--ink-900);

  text-align: center;

}



.market-mobile-bottom-item strong {

  color: inherit;

  font-size: 11px;

  line-height: 1.15;

}



.market-mobile-nav-icon {

  position: relative;

  display: block;

  width: 18px;

  height: 18px;

  color: #64748b;

}



.market-mobile-nav-icon::before,

.market-mobile-nav-icon::after {

  content: "";

  position: absolute;

  box-sizing: border-box;

}



.market-mobile-nav-icon.home::before {

  left: 2px;

  top: 7px;

  width: 14px;

  height: 10px;

  border: 1.8px solid currentColor;

  border-radius: 3px;

}



.market-mobile-nav-icon.home::after {

  left: 4px;

  top: 2px;

  width: 10px;

  height: 10px;

  border-left: 1.8px solid currentColor;

  border-top: 1.8px solid currentColor;

  transform: rotate(45deg);

}



.market-mobile-nav-icon.market::before {

  inset: 2px;

  border: 1.8px solid currentColor;

  border-radius: 4px;

}



.market-mobile-nav-icon.market::after {

  left: 5px;

  top: 5px;

  width: 2px;

  height: 8px;

  background: currentColor;

  box-shadow: 4px -2px 0 currentColor, 8px 2px 0 currentColor;

}



.market-mobile-nav-icon.trend::before {

  left: 2px;

  right: 2px;

  top: 8px;

  height: 2px;

  border-radius: 999px;

  background: currentColor;

  transform: rotate(-18deg);

}



.market-mobile-nav-icon.trend::after {

  left: 3px;

  top: 4px;

  width: 4px;

  height: 4px;

  border-radius: 999px;

  background: currentColor;

  box-shadow: 6px 5px 0 currentColor, 12px 1px 0 currentColor;

}



.market-mobile-nav-icon.alert::before {

  left: 4px;

  top: 2px;

  width: 10px;

  height: 12px;

  border: 1.8px solid currentColor;

  border-radius: 8px 8px 5px 5px;

}



.market-mobile-nav-icon.alert::after {

  left: 7px;

  bottom: 1px;

  width: 4px;

  height: 2px;

  border-radius: 999px;

  background: currentColor;

}



.market-mobile-nav-icon.supplier::before {

  left: 2px;

  top: 6px;

  width: 14px;

  height: 10px;

  border: 1.8px solid currentColor;

  border-radius: 4px;

}



.market-mobile-nav-icon.supplier::after {

  left: 5px;

  top: 3px;

  width: 8px;

  height: 5px;

  border: 1.8px solid currentColor;

  border-bottom: 0;

  border-radius: 4px 4px 0 0;

}



.market-mobile-bottom-item.active .market-mobile-nav-icon {

  color: #eff6ff;

}



@media (max-width: 430px) {

  .backend-entry-meta {

    grid-template-columns: 1fr;

  }



  .backend-entry-actions {

    grid-template-columns: 1fr;

  }



  .market-mobile-home-topline {

    display: grid;

    grid-template-columns: 1fr;

    gap: 8px;

  }



  .market-mobile-home-topline .market-mobile-city-pill {

    grid-column: auto;

    justify-self: start;

    max-width: 100%;

  }



  .market-mobile-home .market-mobile-section-head > span {

    display: none;

  }



  .market-mobile-task-grid {

    grid-template-columns: repeat(3, minmax(0, 1fr));

  }



  .market-mobile-task-card {

    min-height: 108px;

    padding: 10px;

  }



  .market-mobile-task-card strong {

    font-size: 12px;

  }



  .market-mobile-task-card small {

    font-size: 11px;

  }



  .market-mobile-shortcut-grid,

  .market-mobile-recent-grid {

    grid-template-columns: repeat(2, minmax(0, 1fr));

  }



  .market-mobile-source-grid {

    grid-template-columns: 1fr;

  }



  .market-mobile-shell-head {

    grid-template-columns: 38px minmax(0, 1fr) 38px;

  }



  .market-mobile-city-pill {

    grid-column: 2;

    justify-self: end;

    min-height: 28px;

    padding: 0 10px;

    font-size: 9px;

  }

}



/* Mobile home shadcn-style final pass: data first, compact segmented controls. */

.market-mobile-home {

  gap: 8px;

  padding: 8px 10px calc(126px + env(safe-area-inset-bottom));

  background: #f8fafc;

  --mobile-home-radius: 8px;

  --mobile-home-border: #dbe4ef;

  --mobile-home-shadow: 0 1px 2px rgba(15, 23, 42, 0.035);

}



.market-mobile-home .market-mobile-home-hero,

.market-mobile-home .market-mobile-section {

  border: 1px solid var(--mobile-home-border);

  border-radius: var(--mobile-home-radius);

  background: #ffffff;

  box-shadow: var(--mobile-home-shadow);

}



.market-mobile-home .market-mobile-home-hero {

  gap: 8px;

  padding: 10px;

}



.market-mobile-home .market-mobile-appbar {

  grid-template-columns: minmax(0, 1fr) auto 34px;

  gap: 8px;

}



.market-mobile-home .market-mobile-brand-mark {

  width: 30px;

  height: 30px;

  border-radius: 8px;

  box-shadow: none;

}



.market-mobile-home .market-mobile-brand strong {

  color: #0f172a;

  font-size: 15px;

  line-height: 1.1;

}



.market-mobile-home .market-mobile-location-button,

.market-mobile-home .market-mobile-message-button {

  min-height: 34px;

  border-color: var(--mobile-home-border);

  border-radius: 8px;

  background: #ffffff;

  box-shadow: none;

}



.market-mobile-home .market-mobile-location-button {

  max-width: 122px;

  padding: 0 9px;

  font-size: 11px;

}



.market-mobile-home .market-mobile-pc-filter.main {

  display: none;

}



.market-mobile-home .market-mobile-chip-strip {

  display: flex;

  gap: 8px;

  overflow-x: auto;

  padding: 2px 1px 6px;

  scrollbar-width: none;

}



.market-mobile-home .market-mobile-chip-strip::-webkit-scrollbar {

  display: none;

}



.market-mobile-home .market-mobile-chip {

  flex: 0 0 auto;

  min-height: 34px;

  padding: 0 12px;

  border: 1px solid var(--mobile-home-border);

  border-radius: 999px;

  background: #ffffff;

  color: #475569;

  font-size: 11px;

  font-weight: 600;

  white-space: nowrap;

}



.market-mobile-home .market-mobile-chip.active {

  border-color: #bfdbfe;

  background: #eff6ff;

  color: #2563eb;

}



.market-mobile-home .market-mobile-section-note {

  color: #64748b;

  font-size: 11px;

  line-height: 1.55;

}



.market-mobile-home .market-mobile-product-feed {

  display: grid;

  gap: 10px;

}



.market-mobile-home .market-mobile-product-card {

  padding: 14px;

  border: 1px solid var(--mobile-home-border);

  border-radius: 14px;

  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);

  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);

}



.market-mobile-home .market-mobile-product-top {

  display: flex;

  align-items: flex-start;

  justify-content: space-between;

  gap: 10px;

}



.market-mobile-home .market-mobile-product-top strong {

  color: #0f172a;

  font-size: 15px;

  line-height: 1.35;

}



.market-mobile-home .market-mobile-product-top span,
.market-mobile-home .market-mobile-product-meta span,
.market-mobile-home .market-mobile-product-bottom em,
.market-mobile-home .market-mobile-product-bottom small {

  color: #64748b;

  font-size: 11px;

}



.market-mobile-home .market-mobile-product-meta,
.market-mobile-home .market-mobile-product-bottom {

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 8px;

}



.market-mobile-home .market-mobile-product-bottom b {

  color: #1d4ed8;

  font-size: 18px;

  line-height: 1.2;

}



.market-mobile-home .market-mobile-source-grid {

  display: grid;

  grid-template-columns: repeat(2, minmax(0, 1fr));

  gap: 10px;

}



.market-mobile-home .market-mobile-source-card {

  display: grid;

  gap: 6px;

  min-height: 108px;

  padding: 14px 12px;

  border: 1px solid var(--mobile-home-border);

  border-radius: 14px;

  background: #ffffff;

  text-align: left;

}



.market-mobile-home .market-mobile-source-card span {

  color: #2563eb;

  font-size: 11px;

  font-weight: 700;

}



.market-mobile-home .market-mobile-source-card strong {

  color: #0f172a;

  font-size: 14px;

  line-height: 1.35;

}



.market-mobile-home .market-mobile-source-card p {

  color: #64748b;

  font-size: 11px;

  line-height: 1.5;

}



.market-mobile-home .market-mobile-search-row :deep(.el-input__wrapper) {

  min-height: 36px;

  border-radius: 8px;

}



.market-mobile-home .market-mobile-stat-grid {

  grid-template-columns: repeat(3, minmax(0, 1fr));

  gap: 7px;

}



.market-mobile-home .market-mobile-stat-card {

  gap: 3px;

  min-height: 70px;

  padding: 9px 8px;

  border-color: var(--mobile-home-border);

  border-radius: 8px;

  background: #ffffff;

  box-shadow: none;

}



.market-mobile-home .market-mobile-stat-card span,

.market-mobile-home .market-mobile-stat-card small {

  font-size: 10px;

  line-height: 1.25;

}



.market-mobile-home .market-mobile-stat-card strong {

  font-size: 13px;

  line-height: 1.25;

}



.market-mobile-home .market-mobile-workbench-section {

  order: 1;

  padding: 10px;

}

.market-mobile-home .market-mobile-workbench-metrics,
.market-mobile-home .market-mobile-trust-strip {
  display: none;
}

.market-mobile-home .market-mobile-workbench-section {
  gap: 10px;
}



.market-mobile-home .market-mobile-product-section {

  order: 2;

}



.market-mobile-home .market-mobile-advice-section {

  order: 3;

}



.market-mobile-home .market-mobile-category-section {

  order: 6;

}



.market-mobile-home .market-mobile-shortcut-section {

  order: 7;

  margin-top: 82px;

}



.market-mobile-home .market-mobile-source-section {

  order: 4;

}

.market-mobile-home .market-mobile-source-section.compact {
  gap: 8px;
}

.market-mobile-home .market-mobile-source-section.compact .market-mobile-source-card {
  min-height: 92px;
  padding: 12px;
}

.market-mobile-home .market-mobile-more-section {

  order: 5;

}



.market-mobile-home .market-mobile-system-section {

  order: 8;

}



.market-mobile-home .market-mobile-workbench-section::before {

  display: none;

}



.market-mobile-home .market-mobile-workbench-head {

  grid-template-columns: minmax(0, 1fr) auto;

  align-items: center;

  gap: 8px;

}



.market-mobile-home .market-mobile-workbench-title {

  grid-template-columns: 30px minmax(0, 1fr);

  gap: 8px;

}



.market-mobile-home .market-mobile-title-icon {

  width: 30px;

  height: 30px;

  border-radius: 8px;

}



.market-mobile-home .market-mobile-workbench-title h2 {

  font-size: 17px;

}



.market-mobile-home .market-mobile-workbench-title small {

  min-height: 0;

  padding: 0;

  border-radius: 0;

  background: transparent;

  color: #475569;

  font-size: 10px;

}



.market-mobile-home .market-mobile-workbench-badge {

  min-width: 50px;

  padding: 5px 7px;

  border-radius: 8px;

}



.market-mobile-home .market-mobile-workbench-metrics {

  gap: 6px;

  padding: 0;

  border: 0;

  border-radius: 0;

  background: transparent;

}



.market-mobile-home .market-mobile-workbench-metrics span {

  min-height: 30px;

  border: 1px solid var(--mobile-home-border);

  border-radius: 8px;

  background: #f8fafc;

}



.market-mobile-home .market-mobile-task-grid {

  gap: 6px;

}



.market-mobile-home .market-mobile-task-card {

  min-height: 42px;

  padding: 8px 6px;

  border-color: var(--mobile-home-border);

  border-radius: 8px;

  background: #ffffff;

}



.market-mobile-home .market-mobile-task-card.primary {

  border-color: #bfdbfe;

  background: #eff6ff;

}



.market-mobile-home .market-mobile-task-card.warning {

  border-color: #fed7aa;

  background: #fff7ed;

}



.market-mobile-home .market-mobile-task-card strong {

  font-size: 12px;

  letter-spacing: 0;

}



.market-mobile-home .market-mobile-section-head {

  min-height: 42px;

  padding: 8px 10px;

  border-color: var(--mobile-home-border);

  border-radius: 8px;

  background: #ffffff;

}



.market-mobile-home .market-mobile-section-head::before {

  top: 11px;

  height: 20px;

}



.market-mobile-home .market-mobile-section-head h2 {

  font-size: 15px;

  letter-spacing: 0;

}



.market-mobile-home .market-mobile-section-head .market-mobile-inline-link,

.market-mobile-home .market-mobile-section-head > span:not(.market-mobile-head-icon) {

  min-height: 26px;

  border-radius: 8px;

  background: #ffffff;

}



.market-mobile-home .market-mobile-summary-table,

.market-mobile-home .market-mobile-pc-table {

  border-color: var(--mobile-home-border);

  border-radius: 8px;

}



.market-mobile-home .market-mobile-summary-table-head,

.market-mobile-home .market-mobile-summary-table-row,

.market-mobile-home .market-mobile-pc-table-head,

.market-mobile-home .market-mobile-pc-table-row {

  grid-template-columns: minmax(76px, 1.15fr) minmax(70px, 1fr) 52px 42px;

  gap: 6px;

  padding: 8px 9px;

}



.market-mobile-home .market-mobile-advice-card {

  padding: 11px 12px 11px 28px;

  border-color: var(--mobile-home-border);

  border-radius: 8px;

  background: #ffffff;

}



.market-mobile-home .market-mobile-chip-strip,

.market-mobile-home .market-mobile-shortcut-strip,

.market-mobile-home .market-mobile-recent-strip-row,

.market-mobile-home .market-mobile-system-strip {

  scrollbar-width: none;

}



.market-mobile-home .market-mobile-chip-strip::-webkit-scrollbar,

.market-mobile-home .market-mobile-shortcut-strip::-webkit-scrollbar,

.market-mobile-home .market-mobile-recent-strip-row::-webkit-scrollbar,

.market-mobile-home .market-mobile-system-strip::-webkit-scrollbar {

  display: none;

}



.market-mobile-home .market-mobile-chip,

.market-mobile-home .market-mobile-shortcut-card.compact,

.market-mobile-home .market-mobile-recent-card.compact,

.market-mobile-home .market-mobile-system-card {

  border-color: var(--mobile-home-border);

  border-radius: 8px;

  background: #ffffff;

  box-shadow: none;

}



.market-mobile-home .market-mobile-shortcut-strip,

.market-mobile-home .market-mobile-recent-strip-row {

  display: grid;

  grid-template-columns: repeat(2, minmax(0, 1fr));

  gap: 8px;

  overflow: visible;

  padding-bottom: 0;

}



.market-mobile-home .market-mobile-shortcut-card.compact,

.market-mobile-home .market-mobile-recent-card.compact {

  flex: initial;

  width: 100%;

  min-height: 76px;

}



.market-mobile-home .market-mobile-system-strip {

  display: grid;

  grid-template-columns: repeat(3, minmax(0, 1fr));

  gap: 6px;

  overflow: visible;

  padding: 6px;

  border-color: var(--mobile-home-border);

  border-radius: 8px;

  background: #f8fafc;

}



.market-mobile-home .market-mobile-system-card {

  flex: initial;

  min-width: 0;

  min-height: 62px;

  padding: 8px;

}



.market-mobile-home .market-mobile-bottom-nav {

  left: 10px;

  right: 10px;

  bottom: max(8px, env(safe-area-inset-bottom));

  padding: 5px;

  border-color: var(--mobile-home-border);

  border-radius: 14px;

  background: rgba(255, 255, 255, 0.96);

  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.1);

}



.market-mobile-home .market-mobile-bottom-item {

  min-height: 42px;

  border-radius: 10px;

}



.market-mobile-home .market-mobile-bottom-item strong {

  font-size: 10px;

}



.market-mobile-home .market-mobile-nav-icon {

  width: 16px;

  height: 16px;

}



.market-mobile-home .market-mobile-bottom-item.active {

  background: #2563eb;

  color: #ffffff;

  box-shadow: none;

}



@media (max-width: 360px) {

  .market-mobile-shell {

    padding-bottom: calc(138px + env(safe-area-inset-bottom));

  }



  .market-mobile-task-grid,

  .market-mobile-shortcut-grid,

  .market-mobile-recent-grid,

  .market-mobile-source-grid {

    grid-template-columns: repeat(2, minmax(0, 1fr));

  }



  .market-mobile-context-pill {

    padding: 9px 8px;

  }

}

.market-mobile-trust-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.market-mobile-trust-card {
  display: grid;
  gap: 3px;
  min-height: 66px;
  padding: 9px 8px;
  border: 1px solid rgba(219, 228, 239, 0.95);
  border-radius: 10px;
  background: #f8fafc;
}

.market-mobile-trust-card span,
.market-mobile-trust-card small,
.market-mobile-advice-card small,
.market-mobile-more-note {
  color: var(--ink-500);
  font-size: 10px;
  line-height: 1.35;
}

.market-mobile-trust-card strong {
  color: var(--ink-900);
  font-size: 12px;
  line-height: 1.2;
}

.market-mobile-more-section {
  gap: 8px;
}

.market-mobile-more-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.market-mobile-more-head h2 {
  margin: 0;
  color: var(--ink-900);
  font-size: 14px;
  line-height: 1.3;
}

.market-mobile-more-button {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid #dbe4ef;
  border-radius: 999px;
  background: #ffffff;
  color: #1d4ed8;
  font: inherit;
  font-size: 12px;
  font-weight: 700;
}




/* Mobile price-alert guard: bottom nav clearance and two-line source truncation. */
.market-mobile-shell-content:has(.market-mobile-alert-page) {
  padding-bottom: calc(188px + env(safe-area-inset-bottom, 0px));
}

.market-mobile-alert-page {
  padding-bottom: calc(76px + env(safe-area-inset-bottom, 0px));
}

.market-mobile-alert-row div {
  min-width: 0;
}

.market-mobile-alert-row small,
.market-mobile-alert-row p,
.market-mobile-source-card strong,
.market-mobile-source-card p,
.market-mobile-home .market-mobile-source-card strong,
.market-mobile-home .market-mobile-source-card p {
  display: -webkit-box;
  overflow: hidden;
  white-space: normal;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.market-mobile-bottom-nav {
  max-height: calc(74px + env(safe-area-inset-bottom, 0px));
}

/* Mobile touch/safe-area guard: fixed bottom nav should not steal final content,
   and header actions keep a thumb-friendly hit target. */
.market-mobile-shell-content {
  padding-bottom: calc(244px + env(safe-area-inset-bottom, 0px));
}

.market-mobile-home {
  padding-bottom: calc(214px + env(safe-area-inset-bottom, 0px));
}

.market-mobile-back-button,
.market-mobile-back-icon,
.market-mobile-message-button {
  min-width: 44px !important;
  width: 44px !important;
  min-height: 44px !important;
}

.market-mobile-rule-toggle {
  min-height: 44px !important;
  padding-inline: 16px !important;
}

.market-mobile-appbar,
.market-mobile-home .market-mobile-appbar {
  grid-template-columns: minmax(0, 1fr) auto 44px;
}

/* Mobile Experience v2: rebuild the phone flow as a procurement-first app. */
.mobile-redesign-home {
  display: grid;
  gap: 10px;
  min-height: 100dvh;
  padding: 10px 10px calc(112px + env(safe-area-inset-bottom, 0px));
  background:
    radial-gradient(circle at 18% 0%, rgba(37, 99, 235, .08), transparent 26%),
    linear-gradient(180deg, #f4f7fb 0%, #f8fafc 36%, #ffffff 100%);
  color: #0f172a;
}

.mobile-redesign-hero-card,
.mobile-redesign-section {
  border: 1px solid #dbe4ef;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 8px 22px rgba(15, 23, 42, .05);
}

.mobile-redesign-hero-card {
  display: grid;
  gap: 14px;
  padding: 14px;
}

.mobile-redesign-topbar,
.mobile-redesign-section-head,
.mobile-redesign-search,
.mobile-redesign-product-card footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.mobile-redesign-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.mobile-redesign-top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-redesign-brand > span {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  font-size: 19px;
  font-weight: 900;
  box-shadow: 0 8px 18px rgba(37, 99, 235, .18);
}

.mobile-redesign-brand strong,
.mobile-redesign-hero-copy h1,
.mobile-redesign-section-head h2,
.mobile-redesign-priority-card strong,
.mobile-redesign-product-card strong,
.mobile-redesign-entry-grid strong {
  color: #071226;
}

.mobile-redesign-brand strong {
  display: block;
  font-size: 16px;
  line-height: 1.1;
}

.mobile-redesign-brand small,
.mobile-redesign-hero-copy small,
.mobile-redesign-priority-card small,
.mobile-redesign-product-card span,
.mobile-redesign-product-card span,
.mobile-redesign-alert-list span,
.mobile-redesign-alert-list small,
.mobile-redesign-source-grid small,
.mobile-redesign-entry-grid small {
  color: #64748b;
}

.mobile-redesign-location,
.mobile-redesign-alert-dot,
.mobile-redesign-search button,
.mobile-redesign-section-head button {
  min-height: 40px;
  border: 1px solid #dbe4ef;
  border-radius: 12px;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
}

.mobile-redesign-location {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  max-width: 128px;
  padding: 0 12px;
  background: #ffffff;
  color: #334155;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-redesign-location i {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #2563eb;
  box-shadow: 0 0 0 5px rgba(37, 99, 235, .12);
}

.mobile-redesign-alert-dot {
  position: relative;
  display: grid;
  place-items: center;
  width: 40px;
  flex: 0 0 40px;
  background: #ffffff;
  color: #e11d48;
}

.mobile-redesign-alert-dot::before {
  content: "";
  width: 17px;
  height: 15px;
  border: 2px solid currentColor;
  border-radius: 8px;
}

.mobile-redesign-alert-dot b {
  position: absolute;
  top: -5px;
  right: -4px;
  display: grid;
  place-items: center;
  min-width: 22px;
  height: 22px;
  padding: 0 5px;
  border: 2px solid #fff;
  border-radius: 999px;
  background: #ef4444;
  color: #fff;
  font-size: 12px;
}

.mobile-redesign-search {
  padding: 6px;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e2e8f0;
}

.mobile-redesign-search :deep(.el-input__wrapper) {
  min-height: 40px;
  border: 0;
  box-shadow: none !important;
  background: transparent;
}

.mobile-redesign-search button {
  padding: 0 18px;
  min-width: 76px;
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
  white-space: nowrap;
}

.mobile-redesign-hero-copy {
  display: grid;
  gap: 4px;
}

.mobile-redesign-hero-copy p,
.mobile-redesign-section-head p {
  margin: 0;
  color: #2563eb;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .04em;
}

.mobile-redesign-hero-copy h1 {
  margin: 0;
  max-width: 320px;
  font-size: clamp(21px, 5.8vw, 25px);
  line-height: 1.16;
  letter-spacing: -.03em;
  font-weight: 800;
}

.mobile-redesign-stat-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.mobile-redesign-stat-strip button,
.mobile-redesign-priority-card,
.mobile-redesign-product-card,
.mobile-redesign-alert-list button,
.mobile-redesign-source-grid button,
.mobile-redesign-entry-grid button {
  border: 0;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.mobile-redesign-stat-strip button {
  display: grid;
  gap: 6px;
  min-height: 68px;
  padding: 10px;
  border: 1px solid #dbe4ef;
  border-radius: 14px;
  background: #ffffff;
}

.mobile-redesign-stat-strip button span {
  color: #475569;
  font-size: 10px;
  font-weight: 800;
}

.mobile-redesign-stat-strip button strong {
  color: #0f172a;
  font-size: 20px;
  line-height: 1;
}

.mobile-redesign-stat-strip .danger {
  border-color: #fecaca;
  background: linear-gradient(180deg, #fff7f7, #ffffff);
}

.mobile-redesign-stat-strip .primary {
  border-color: #bfdbfe;
  background: linear-gradient(180deg, #f5f9ff, #ffffff);
}

.mobile-redesign-stat-strip .success {
  border-color: #bbf7d0;
  background: linear-gradient(180deg, #f2fbf6, #ffffff);
}

.mobile-redesign-main {
  display: grid;
  gap: 10px;
}

.mobile-redesign-section {
  display: grid;
  gap: 12px;
  padding: 12px;
}

.mobile-redesign-section-head h2 {
  margin: 2px 0 0;
  font-size: 17px;
  line-height: 1.2;
  letter-spacing: -.02em;
}

.mobile-redesign-section-head button {
  padding: 0 14px;
  background: #ffffff;
  color: #2563eb;
}

.mobile-redesign-head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-redesign-priority-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}

.mobile-redesign-workbench-head {
  display: grid;
  gap: 4px;
  margin-bottom: 10px;
  padding: 0 4px;
}

.mobile-redesign-workbench-head p {
  margin: 0;
  color: #2563eb;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .04em;
}

.mobile-redesign-workbench-head h2 {
  margin: 0;
  color: #071226;
  font-size: 18px;
  line-height: 1.18;
  letter-spacing: -.02em;
}

.mobile-redesign-priority-card {
  display: grid;
  gap: 10px;
  min-height: 96px;
  padding: 14px;
  border: 1px solid #dbe4ef;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.035);
}

.mobile-redesign-priority-card p {
  margin: 0;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .04em;
  text-transform: uppercase;
}

.mobile-redesign-priority-card strong {
  font-size: 15px;
  line-height: 1.28;
  letter-spacing: -.03em;
}

.mobile-redesign-priority-card small {
  font-size: 12px;
  line-height: 1.4;
}

.mobile-redesign-priority-card.is-alert {
  border-color: #fed7aa;
  background: linear-gradient(180deg, #fff8f3, #ffffff);
}

.mobile-redesign-priority-card.is-alert p {
  color: #c2410c;
}

.mobile-redesign-priority-card.is-menu {
  border-color: #bfdbfe;
  background: linear-gradient(180deg, #f5f9ff, #ffffff);
}

.mobile-redesign-priority-card.is-menu p {
  color: #1d4ed8;
}

.mobile-redesign-priority-card.is-main {
  min-height: 104px;
  border-color: #bfdbfe;
  background: linear-gradient(180deg, #f7fbff, #ffffff 70%);
}

.mobile-redesign-priority-card.is-main p {
  color: #1d4ed8;
}

.mobile-trend-shortcut.market-mobile-bottom-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  width: auto;
  min-height: 44px;
  padding: 0 14px;
  border: 0;
  border-radius: 999px;
  background: #f8fafc;
  color: #475569;
  box-shadow: inset 0 0 0 1px #dbe4ef;
  font-size: 13px;
  font-weight: 900;
}

.market-mobile-shell-head {
  grid-template-columns: 44px minmax(0, 1fr) auto 44px;
  gap: 8px;
}

.market-mobile-shell-head .mobile-trend-shortcut.market-mobile-bottom-item {
  min-width: 52px;
  min-height: 44px;
  padding-inline: 12px;
}

.mobile-redesign-alert-list strong {
  display: block;
  overflow: hidden;
  font-size: 15px;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-redesign-alert-list small {
  display: -webkit-box;
  overflow: hidden;
  margin-top: 3px;
  font-size: 12px;
  line-height: 1.35;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.mobile-redesign-product-rail {
  display: grid;
  gap: 12px;
  margin: 0;
  padding: 0;
  overflow: visible;
}

.mobile-redesign-product-rail::-webkit-scrollbar,
.mobile-redesign-sources::-webkit-scrollbar {
  display: none;
}

.mobile-redesign-product-card {
  display: grid;
  gap: 10px;
  min-height: 98px;
  padding: 12px;
  border: 1px solid #dbe4ef;
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.035);
}

.mobile-redesign-product-copy {
  display: grid;
  gap: 4px;
}

.mobile-redesign-product-card strong {
  display: -webkit-box;
  overflow: hidden;
  font-size: 14px;
  line-height: 1.24;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.mobile-redesign-product-copy span {
  font-size: 12px;
  font-weight: 800;
}

.mobile-redesign-product-card b {
  color: #1d4ed8;
  font-size: 17px;
  line-height: 1;
}

.mobile-redesign-product-card small {
  font-size: 11px;
}

.mobile-redesign-product-card em {
  color: #0f766e;
  font-size: 12px;
  font-style: normal;
  font-weight: 800;
}

.mobile-redesign-alert-list,
.mobile-redesign-source-grid,
.mobile-redesign-entry-grid {
  display: grid;
  gap: 10px;
}

.mobile-redesign-alert-list button {
  display: grid;
  gap: 4px;
  min-height: 82px;
  padding: 12px;
  border: 1px solid #fed7aa;
  border-radius: 16px;
  background: linear-gradient(180deg, #fff8f2, #ffffff);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}

.mobile-redesign-source-grid,
.mobile-redesign-entry-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.mobile-redesign-source-grid button,
.mobile-redesign-entry-grid button {
  display: grid;
  gap: 6px;
  min-height: 88px;
  padding: 12px;
  border: 1px solid #dbe4ef;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}

.mobile-redesign-source-grid span,
.mobile-redesign-entry-grid span {
  color: #2563eb;
  font-size: 12px;
  font-weight: 900;
}

.mobile-redesign-source-grid strong,
.mobile-redesign-entry-grid strong {
  display: -webkit-box;
  overflow: hidden;
  font-size: 15px;
  line-height: 1.24;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.mobile-redesign-empty-card {
  display: grid;
  gap: 6px;
  min-height: 112px;
  padding: 16px;
  border: 1px dashed #cbd5e1;
  border-radius: 16px;
  background: #f8fafc;
}

.mobile-redesign-empty-card.compact {
  min-height: 84px;
  grid-column: 1 / -1;
}

.mobile-redesign-nav {
  left: 0;
  right: 0;
  bottom: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  min-height: 62px;
  padding: 6px 10px calc(6px + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid rgba(226, 232, 240, .96);
  border-left: 0;
  border-right: 0;
  border-bottom: 0;
  border-radius: 0;
  background: rgba(255, 255, 255, .98);
  box-shadow: 0 -6px 18px rgba(15, 23, 42, .06);
  backdrop-filter: blur(14px);
}

.mobile-redesign-nav .market-mobile-bottom-item {
  min-height: 44px;
  border-radius: 10px;
}

.mobile-redesign-nav .market-mobile-bottom-item.active {
  background: #2563eb;
  color: #ffffff;
  box-shadow: none;
}

@media (max-width: 374px) {
  .mobile-redesign-home {
    padding-inline: 10px;
  }

  .mobile-redesign-topbar {
    gap: 8px;
  }

  .mobile-redesign-location {
    max-width: 104px;
  }

  .mobile-redesign-priority-grid,
  .mobile-redesign-stat-strip {
    gap: 8px;
  }

  .mobile-redesign-priority-grid {
    grid-template-columns: 1fr;
  }
}

</style>

