<template>
  <section class="panel supplier-admin-panel content-shell-panel" :class="[{ mobile, embedded: isEmbeddedBackendMode, 'procurement-mode': isProcurementSupplierManagement }, embeddedLayoutClass]" data-testid="supplier-admin-panel">
    <div v-if="!isEmbeddedBackendMode" class="panel-header content-panel-header">
      <div>
        <p class="panel-kicker">供应平台</p>
        <h2>{{ panelHeaderTitle }}</h2>
        <p class="panel-hint">
          {{ panelHeaderHint }}
        </p>
      </div>
      <div class="inline-actions compact-actions">
        <el-button plain :loading="loading" @click="reloadAll">刷新供应数据</el-button>
      </div>
    </div>

    <div v-if="!isEmbeddedBackendMode" class="supplier-session-banner" data-testid="supplier-session-banner">
      <div class="supplier-session-banner-copy">
        <span>当前账号</span>
        <strong>{{ sessionDisplayName }}</strong>
        <small>{{ sessionScopeLabel }}</small>
      </div>
      <span class="supplier-session-banner-role">{{ sessionRoleLabel }}</span>
    </div>

    <div v-if="mobile && !resolvedBackendSection" class="supplier-mobile-focus-card">
      <div class="supplier-mobile-focus-copy">
        <span>当前任务</span>
        <strong>{{ mobileSupplierTaskTitle }}</strong>
        <small>{{ mobileSupplierTaskDescription }}</small>
      </div>
      <div class="supplier-mobile-focus-meta">
        <span>{{ selectedSupplier?.supplier_name || '先选供应商' }}</span>
        <span>{{ selectedProductLabelResolved || '再选商品' }}</span>
      </div>
    </div>

    <div v-if="mobile && !resolvedBackendSection" class="supplier-mobile-task-strip">
      <button
        v-for="item in mobileSupplierTaskTabs"
        :key="item.key"
        type="button"
        class="supplier-mobile-task-button"
        :class="{ active: mobileSupplierTask === item.key }"
        @click="mobileSupplierTask = item.key"
      >
        <strong>{{ item.label }}</strong>
        <small>{{ item.detail }}</small>
      </button>
    </div>

    <div v-if="mobile && !resolvedBackendSection && recentSupplierItems.length" class="supplier-mobile-recent-strip">
      <button
        v-for="item in recentSupplierItems"
        :key="item.id"
        type="button"
        class="supplier-mobile-recent-chip"
        :class="{ active: selectedSupplierId === item.id }"
        @click="selectSupplier(item.id)"
      >
        <strong>{{ item.supplier_name }}</strong>
        <small>{{ item.market_category || item.channel || '本地供应商' }}</small>
      </button>
    </div>

    <div v-if="mobile && !resolvedBackendSection && !suppliers.length && !isSupplierSession" class="supplier-mobile-guide-card">
      <div class="supplier-mobile-guide-copy">
        <span>首次使用</span>
        <strong>先把本地供应商链路跑起来</strong>
        <small>{{ isProcurementSupplierManagement ? '推荐先创建供应商并分配账号，再从报价历史、结算和日志里处理供应商数据。' : '推荐先创建供应商，再录第一条报价，最后回到历史和结算做复核。' }}</small>
      </div>
      <div class="supplier-mobile-guide-actions">
        <button type="button" class="supplier-mobile-guide-button primary" @click="resetSupplierForm">新建首个供应商</button>
        <button v-if="!isProcurementSupplierManagement" type="button" class="supplier-mobile-guide-button" @click="mobileSupplierTask = 'quote'">打开录价页</button>
      </div>
      <div class="supplier-mobile-guide-list">
        <article class="supplier-mobile-guide-step">
          <span>01</span>
          <strong>创建供应商</strong>
          <small>补齐分类、联系人和渠道</small>
        </article>
        <article class="supplier-mobile-guide-step">
          <span>02</span>
          <strong>{{ isProcurementSupplierManagement ? '授权' : '录价' }}</strong>
          <small>{{ isProcurementSupplierManagement ? '给供应商分配账号和状态' : '给今日商品录一条有效报价' }}</small>
        </article>
        <article class="supplier-mobile-guide-step">
          <span>03</span>
          <strong>对账</strong>
          <small>月底再看历史与结算单</small>
        </article>
      </div>
    </div>

    <div
      v-if="showSupplierBindingEmptyState"
      class="supplier-session-empty-card"
      data-testid="supplier-binding-empty-state"
    >
      <div class="supplier-session-empty-copy">
        <span>账号范围异常</span>
        <strong>{{ supplierBindingEmptyTitle }}</strong>
        <p>{{ supplierBindingEmptyDescription }}</p>
      </div>
      <div class="supplier-session-empty-actions">
        <el-button plain :loading="loading" @click="reloadAll">重新加载</el-button>
      </div>
    </div>

    <template v-else>
    <div v-if="!isEmbeddedBackendMode" class="supplier-admin-metrics" data-testid="supplier-admin-top-metrics">
      <article class="supplier-admin-metric">
        <span>启用供应商</span>
        <strong>{{ activeSupplierCount }}</strong>
        <small>本地市场持续录价</small>
      </article>
      <article class="supplier-admin-metric">
        <span>已覆盖分类</span>
        <strong>{{ categoryCount }}</strong>
        <small>干调、蔬菜等分类可独立管理</small>
      </article>
      <article class="supplier-admin-metric">
        <span>最近录价</span>
        <strong>{{ latestQuotedAtLabel }}</strong>
        <small>{{ recentQuoteRows[0]?.supplier_name || '平台最近一次录价时间' }}</small>
      </article>
      <article class="supplier-admin-metric">
        <span>累计报价</span>
        <strong>{{ totalQuoteCount }}</strong>
        <small>供应平台已沉淀的报价记录</small>
      </article>
    </div>

    <div v-if="!shouldCollapseEmbeddedWorkspaceChrome" class="supplier-workbench-header" :class="{ compact: isEmbeddedBackendMode }">
      <div class="supplier-workbench-copy">
        <span>{{ supplierWorkbenchKicker }}</span>
        <strong>{{ supplierWorkbenchTitle }}</strong>
      </div>
      <div class="supplier-workbench-side">
        <div class="supplier-workbench-chips">
          <span v-for="item in supplierWorkbenchBadges" :key="item" class="supplier-workbench-chip">{{ item }}</span>
        </div>
        <div class="supplier-workbench-actions">
          <el-button size="small" plain :loading="loading" @click="reloadAll">同步数据</el-button>
          <el-button
            v-if="showWorkbenchPrimaryAction"
            size="small"
            type="primary"
            @click="runWorkbenchPrimaryAction"
          >
            {{ workbenchPrimaryActionLabel }}
          </el-button>
        </div>
      </div>
    </div>

    <div v-if="isEmbeddedBackendMode" class="supplier-command-center" data-testid="supplier-command-center">
      <div class="supplier-command-copy">
        <span>{{ supplierWorkbenchKicker }}</span>
        <strong>{{ supplierWorkbenchTitle }}</strong>
      </div>
      <div class="supplier-command-metrics">
        <article v-for="item in supplierCommandMetrics" :key="item.label" class="supplier-command-metric">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </div>
      <div class="supplier-command-actions" aria-label="供应平台快捷动作">
        <template v-if="isSupplierWorkspace">
          <el-button v-if="isAdminSession" size="small" type="primary" @click="openSupplierCreateFromCommand">新建供应商</el-button>
          <el-button size="small" plain @click="openQuoteFromCommand">去录报价</el-button>
        </template>
        <template v-else-if="isQuoteWorkspace">
          <el-button v-if="selectedProductKey" size="small" plain @click="$emit('open-procurement-product')">回采购同品</el-button>
          <el-button size="small" type="primary" @click="openQuoteImportFromCommand">批量导入</el-button>
          <el-button v-if="latestActiveQuoteRecordId" size="small" plain @click="copyLatestQuoteFromCommand">复制最新价</el-button>
        </template>
        <template v-else-if="isSettlementWorkspace">
          <el-button v-if="isAdminSession" size="small" type="primary" @click="openSettlementFromCommand">新建结算</el-button>
          <el-button v-if="isAdminSession" size="small" plain @click="navigateSupplierCommandSection('logs')">查看日志</el-button>
        </template>
        <template v-else-if="isLogsWorkspace">
          <el-button size="small" plain :loading="loading" @click="reloadAll">同步日志</el-button>
          <el-button size="small" plain :disabled="!hasQuoteActionAdvancedFilters" @click="resetQuoteActionFilters">清空筛选</el-button>
        </template>
      </div>
    </div>

    <div v-if="!shouldCollapseEmbeddedWorkspaceChrome && !isProcurementSupplierManagement" class="supplier-admin-toolbar" :class="{ compact: isEmbeddedBackendMode }">
      <div class="supplier-admin-toolbar-main">
        <el-input v-model="keyword" placeholder="搜索供应商、联系人、分类" clearable />
      </div>
      <div class="supplier-admin-toolbar-filters">
        <el-select v-model="categoryFilter" clearable filterable placeholder="按分类筛选">
          <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="状态">
          <el-option label="全部状态" value="all" />
          <el-option label="仅启用" value="active" />
          <el-option label="仅停用" value="inactive" />
        </el-select>
      </div>
    </div>

    <div v-if="mobile && !resolvedBackendSection" class="supplier-mobile-action-bar">
      <button
        type="button"
        class="supplier-mobile-action-button primary"
        :disabled="mobilePrimaryActionDisabled"
        @click="runMobilePrimaryAction"
      >
        {{ mobilePrimaryActionLabel }}
      </button>
      <button
        type="button"
        class="supplier-mobile-action-button"
        :disabled="mobileSecondaryActionDisabled"
        @click="runMobileSecondaryAction"
      >
        {{ mobileSecondaryActionLabel }}
      </button>
    </div>

    <div
      v-if="isProcurementSupplierManagement && isAdminSession"
      class="supplier-procurement-view-switch"
      aria-label="采购端供应商管理视图切换"
    >
      <button
        type="button"
        :class="{ active: procurementAdminView === 'suppliers' }"
        @click="procurementAdminView = 'suppliers'"
      >
        <strong>供应商管理</strong>
        <small>维护正式供应商、账号与报价链路</small>
      </button>
    </div>

    <div v-if="isSupplierSession && isSettlementWorkspace" class="supplier-my-settlement-page">
      <div class="supplier-my-settlement-shell">
        <div class="supplier-my-settlement-hero">
          <div class="supplier-my-settlement-hero-copy">
            <span>我的结算</span>
            <strong>{{ selectedSupplier?.supplier_name || '当前供应商' }}</strong>
            <small>这里只看我的账期、应收和付款进度。</small>
          </div>
          <div class="supplier-my-settlement-hero-actions">
            <el-button size="small" plain :loading="settlementLoading" @click="loadSupplierSettlements">刷新</el-button>
            <el-button size="small" plain :disabled="!settlementRows.length" @click="exportSettlementRows('xlsx')">导出 Excel</el-button>
            <el-button size="small" plain :disabled="!settlementRows.length" @click="exportSettlementRows('csv')">导出 CSV</el-button>
          </div>
        </div>

        <div class="supplier-my-settlement-kpis">
          <article v-for="item in mySettlementKpis" :key="item.label" :class="item.tone">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.detail }}</small>
          </article>
        </div>

        <div class="supplier-my-settlement-filters">
          <el-select v-model="settlementStatusFilter" size="small" class="supplier-history-filter-select">
            <el-option label="全部结算" value="all" />
            <el-option label="待付款" value="pending" />
            <el-option label="部分付款" value="partial" />
            <el-option label="已结清" value="paid" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
          <el-input v-model="settlementKeyword" clearable size="small" placeholder="搜标题、备注、创建人" />
          <el-date-picker
            v-model="settlementDateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            unlink-panels
            range-separator="至"
            start-placeholder="账期开始"
            end-placeholder="账期结束"
          />
        </div>

        <div v-if="settlementRows.length" class="supplier-my-settlement-layout">
          <section class="supplier-my-settlement-list">
            <button
              v-for="(item, index) in settlementRows"
              :key="item.id"
              type="button"
              class="supplier-my-settlement-row"
              :class="{ active: focusedSettlementId === item.id }"
              @click="focusedSettlementId = item.id"
            >
              <div class="supplier-my-settlement-row-topline">
                <span class="supplier-my-settlement-row-index">#{{ String(index + 1).padStart(2, '0') }}</span>
                <span class="supplier-my-settlement-row-progress">{{ getSettlementProgressLabel(item) }}</span>
              </div>
              <div class="supplier-my-settlement-row-head">
                <div class="supplier-my-settlement-row-title">
                  <strong>{{ item.settlement_title }}</strong>
                  <small>{{ item.record_count }} 条报价</small>
                </div>
                <span :class="['supplier-status-chip', getSettlementStatusClass(item.status)]">
                  {{ getSettlementStatusLabel(item.status) }}
                </span>
              </div>
              <div class="supplier-my-settlement-row-meta">
                <span>账期 {{ formatSettlementPeriod(item) }}</span>
                <span>应付 {{ formatTime(item.payment_due_date) }}</span>
              </div>
              <div class="supplier-my-settlement-row-metrics">
                <article>
                  <span>总额</span>
                  <strong>{{ formatPrice(item.total_amount) }}</strong>
                </article>
                <article>
                  <span>已付</span>
                  <strong>{{ formatPrice(item.paid_amount) }}</strong>
                </article>
                <article>
                  <span>未付</span>
                  <strong>{{ formatPrice(item.pending_amount) }}</strong>
                </article>
              </div>
              <div class="supplier-my-settlement-row-note">
                <p>{{ item.remarks || '暂无备注' }}</p>
              </div>
              <div class="supplier-my-settlement-row-progressbar" aria-hidden="true">
                <span :style="{ width: `${getSettlementProgressPercent(item)}%` }"></span>
              </div>
              <div class="supplier-my-settlement-row-footer">
                <span>{{ getSettlementFollowUpLabel(item) }}</span>
                <span>{{ item.created_by || '平台创建' }}</span>
              </div>
            </button>
          </section>

          <aside class="supplier-my-settlement-detail">
            <template v-if="focusedSettlement">
              <div class="supplier-my-settlement-detail-head">
                <div class="supplier-my-settlement-detail-heading">
                  <span>当前结算单</span>
                  <strong>{{ focusedSettlement.settlement_title }}</strong>
                  <small>{{ getSettlementStatusLabel(focusedSettlement.status) }} · {{ focusedSettlement.record_count }} 条报价</small>
                </div>
                <div class="supplier-my-settlement-detail-head-side">
                  <div class="supplier-my-settlement-detail-progress-pill">
                    <span>付款进度</span>
                    <strong>{{ getSettlementProgressLabel(focusedSettlement) }}</strong>
                  </div>
                  <el-button size="small" text @click="openSettlementDetail(focusedSettlement)">查看详情</el-button>
                </div>
              </div>
              <div class="supplier-my-settlement-detail-summary">
                <div class="total">
                  <span>未付金额</span>
                  <strong>{{ formatPrice(focusedSettlement.pending_amount) }}</strong>
                  <small>{{ focusedSettlement.payment_due_date ? `应付 ${formatTime(focusedSettlement.payment_due_date)}` : '未设置应付日期' }}</small>
                </div>
                <div>
                  <span>结算总额</span>
                  <strong>{{ formatPrice(focusedSettlement.total_amount) }}</strong>
                </div>
                <div>
                  <span>已付金额</span>
                  <strong>{{ formatPrice(focusedSettlement.paid_amount) }}</strong>
                </div>
              </div>
              <div class="supplier-my-settlement-detail-progress">
                <div class="supplier-my-settlement-detail-progress-copy">
                  <span>本单付款进度</span>
                  <strong>{{ getSettlementFollowUpLabel(focusedSettlement) }}</strong>
                  <small>{{ getSettlementFollowUpDescription(focusedSettlement) }}</small>
                </div>
                <div class="supplier-my-settlement-detail-progress-track" aria-hidden="true">
                  <span :style="{ width: `${getSettlementProgressPercent(focusedSettlement)}%` }"></span>
                </div>
                <div class="supplier-my-settlement-detail-progress-legend">
                  <article>
                    <span>已付</span>
                    <strong>{{ formatPrice(focusedSettlement.paid_amount) }}</strong>
                  </article>
                  <article>
                    <span>剩余</span>
                    <strong>{{ formatPrice(focusedSettlement.pending_amount) }}</strong>
                  </article>
                  <article>
                    <span>记录</span>
                    <strong>{{ focusedSettlement.record_count }} 条</strong>
                  </article>
                </div>
              </div>
              <div class="supplier-my-settlement-detail-grid">
                <article>
                  <span>账期</span>
                  <strong>{{ formatSettlementPeriod(focusedSettlement) }}</strong>
                </article>
                <article>
                  <span>应付日期</span>
                  <strong>{{ formatTime(focusedSettlement.payment_due_date) }}</strong>
                </article>
                <article>
                  <span>付款日期</span>
                  <strong>{{ formatTime(focusedSettlement.payment_date) }}</strong>
                </article>
                <article>
                  <span>创建人</span>
                  <strong>{{ focusedSettlement.created_by || '平台' }}</strong>
                </article>
              </div>
              <div class="supplier-my-settlement-detail-note">
                <span>备注</span>
                <p>{{ focusedSettlement.remarks || '当前结算单没有备注说明。' }}</p>
              </div>
              <div class="supplier-my-settlement-detail-tip">
                <span>结算提示</span>
                <strong>{{ getSettlementStatusLabel(focusedSettlement.status) }}</strong>
                <p>{{ getSettlementFollowUpDescription(focusedSettlement) }}</p>
              </div>
            </template>
          </aside>
        </div>

        <div v-if="settlementTotal" class="supplier-history-pagination">
          <el-button size="small" text :disabled="settlementOffset === 0" @click="changeSettlementPage('prev')">上一页</el-button>
          <span>{{ settlementPageLabel }} · 共 {{ Math.max(Math.ceil(settlementTotal / settlementPageSize), 1) }} 页</span>
          <el-button size="small" text :disabled="!settlementHasMore" @click="changeSettlementPage('next')">下一页</el-button>
        </div>

        <div v-else class="supplier-card-empty compact-empty supplier-my-settlement-empty">
          <strong>还没有结算单</strong>
          <p>管理员创建或生成结算单后，这里会按状态和账期展示你的付款进度。</p>
        </div>
      </div>
    </div>

    <div v-else class="supplier-admin-layout" :class="embeddedLayoutClass">
      <section
        v-if="showSupplierListColumn"
        v-show="isAdminSession && showMobileSupplierTask('suppliers')"
        class="supplier-admin-column supplier-list-column"
        :class="{ 'is-empty': !filteredSuppliers.length }"
      >
        <div class="supplier-list-section-head" :class="{ compact: isSupplierWorkspace }">
          <div class="supplier-column-head">
            <strong>{{ isProcurementSupplierManagement ? '供应商管理' : '供应商列表' }}</strong>
            <span>{{ filteredSuppliers.length }} 家</span>
          </div>
        <div v-if="showSupplierListWorkspaceToolbar" class="supplier-list-workspace-stats">
            <article v-for="item in supplierWorkspaceQuickStats" :key="item.label" class="supplier-list-summary-card compact">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.detail }}</small>
            </article>
          </div>
          <div v-else-if="showSupplierListSummary" class="supplier-list-summary-grid">
            <article v-for="item in supplierListStats" :key="item.label" class="supplier-list-summary-card">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.detail }}</small>
            </article>
          </div>
        </div>
        <div v-if="showSupplierListWorkspaceToolbar" class="supplier-list-workspace-toolbar">
          <div class="supplier-list-workspace-search">
            <el-input
              v-model="keyword"
              :placeholder="isSupplierWorkspace ? '搜索供应商、联系人、账号' : '搜索供应商、联系人、分类'"
              clearable
            />
          </div>
          <el-select v-model="categoryFilter" clearable filterable placeholder="按分类筛选">
            <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="statusFilter" placeholder="状态">
            <el-option label="全部状态" value="all" />
            <el-option label="仅启用" value="active" />
            <el-option label="仅停用" value="inactive" />
          </el-select>
          <div class="supplier-list-workspace-actions">
            <el-button size="small" plain :loading="loading" @click="reloadAll">同步</el-button>
              <el-button v-if="isSettlementWorkspace || isLogsWorkspace" size="small" type="primary" @click="$emit('navigate-section', 'suppliers')">切到档案</el-button>
              <el-button v-else size="small" type="primary" @click="resetSupplierForm">新建供应商</el-button>
          </div>
        </div>
        <div class="supplier-list-toolbar">
          <div class="supplier-list-filter-pills">
            <button type="button" class="supplier-filter-pill" :class="{ active: statusFilter === 'all' }" @click="statusFilter = 'all'">全部</button>
            <button type="button" class="supplier-filter-pill" :class="{ active: statusFilter === 'active' }" @click="statusFilter = 'active'">启用中</button>
            <button type="button" class="supplier-filter-pill" :class="{ active: statusFilter === 'inactive' }" @click="statusFilter = 'inactive'">已停用</button>
          </div>
          <div class="supplier-list-toolbar-meta">
            <span>{{ selectedSupplier ? `当前选中：${selectedSupplier.supplier_name}` : '未选供应商' }}</span>
            <el-button v-if="selectedSupplier" size="small" text @click="clearSelectedSupplierDetail">取消选中</el-button>
          </div>
        </div>
        <div class="supplier-card-list">
          <div v-if="!isQuoteWorkspace" class="supplier-datagrid-head supplier-list-grid supplier-datagrid-head-sticky">
            <span>供应商</span>
            <span>分类与渠道</span>
            <span>账号</span>
            <span>最近录价</span>
          </div>
          <button
            v-for="item in filteredSuppliers"
            :key="item.id"
            type="button"
            class="supplier-card"
            :class="{ active: selectedSupplierId === item.id }"
            @click="selectSupplier(item.id)"
          >
            <div class="supplier-card-head">
              <strong>{{ item.supplier_name }}</strong>
              <span :class="['supplier-status-chip', item.is_active ? 'is-active' : 'is-inactive']">
                {{ item.is_active ? '启用' : '停用' }}
              </span>
            </div>
            <div class="supplier-card-meta">
              <span>{{ item.market_category || '待分类' }}</span>
              <span>{{ item.channel || '待标渠道' }}</span>
              <span>{{ item.quote_count || 0 }} 条报价</span>
            </div>
            <div class="supplier-card-submeta">
              <span>{{ formatSupplierAccountLabel(item) }}</span>
              <span>{{ item.account_is_active === false ? '账号停用' : '账号可用' }}</span>
            </div>
            <p>{{ item.contact_name || '联系人待补充' }}</p>
            <div class="supplier-card-foot">
              <small>{{ formatTime(item.latest_quoted_at) }}</small>
              <small>{{ item.market_scope || '本地市场' }}</small>
            </div>
          </button>
          <div v-if="!filteredSuppliers.length" class="supplier-card-empty">
            <strong>还没有供应商</strong>
            <p>{{ supplierListEmptyDescription }}</p>
            <div class="supplier-empty-actions">
              <el-button size="small" type="primary" @click="resetSupplierForm">新建供应商</el-button>
              <el-button v-if="!isProcurementSupplierManagement" size="small" plain @click="$emit('navigate-section', 'quote')">进入录价区</el-button>
            </div>
          </div>
        </div>
      </section>

      <section v-if="showWorkbenchColumn" class="supplier-admin-column supplier-form-column">
        <div v-if="!mobile && isAdminSession && shouldShowEmbeddedTabs && !isSupplierWorkspace && !isQuoteWorkspace && !isProcurementSupplierManagement" class="supplier-pane-tabs workbench-tabs">
          <button
            v-for="item in desktopSupplierWorkbenchTabs"
            :key="item.key"
            type="button"
            class="supplier-pane-tab"
            :class="{ active: desktopSupplierWorkbenchTab === item.key }"
            @click="desktopSupplierWorkbenchTab = item.key"
          >
            <strong>{{ item.label }}</strong>
            <small>{{ item.detail }}</small>
          </button>
        </div>
        <div
          v-if="selectedSupplier && isAdminSession && showMobileSupplierTask('suppliers') && !isQuoteWorkspace"
          class="supplier-master-detail-banner"
          :class="{ compact: isSupplierWorkspace }"
        >
          <div class="supplier-master-detail-copy">
            <span>当前选中供应商</span>
            <strong>{{ selectedSupplier.supplier_name }}</strong>
            <small>{{ selectedSupplier.market_category || '待分类' }} · {{ selectedSupplier.channel || '待标渠道' }} · {{ selectedSupplier.market_scope || '本地市场' }}</small>
          </div>
          <div class="supplier-master-detail-tags">
            <span class="supplier-workbench-chip">{{ formatSupplierAccountLabel(selectedSupplier) }}</span>
            <span class="supplier-workbench-chip">{{ selectedSupplier.account_is_active === false ? '账号停用' : '账号可用' }}</span>
            <span class="supplier-workbench-chip">{{ selectedSupplier.quote_count || 0 }} 条报价</span>
            <span class="supplier-workbench-chip">{{ formatTime(selectedSupplier.latest_quoted_at) }}</span>
          </div>
          <div class="supplier-master-detail-actions">
            <el-button v-if="!isProcurementSupplierManagement" size="small" plain @click="openQuoteHistoryPanel">查看报价记录</el-button>
            <el-button v-if="!isProcurementSupplierManagement" size="small" type="primary" @click="focusSelectedSupplierQuoteWorkbench">进入录价区</el-button>
          </div>
        </div>
        <div
          v-if="!isQuoteWorkspace"
          v-show="isAdminSession && (!mobile || showMobileSupplierTask('suppliers'))"
          class="supplier-column-head"
          :class="{ compact: isSupplierWorkspace }"
        >
          <strong>{{ isSupplierWorkspace ? (selectedSupplier ? '档案与账号' : '新建供应商') : (selectedSupplier ? '编辑供应商' : '新增供应商') }}</strong>
          <span>{{ selectedSupplier ? `ID ${selectedSupplier.id}` : '新建' }}</span>
        </div>
        <div
          v-if="isProcurementSupplierManagement && !selectedSupplier && isAdminSession"
          class="supplier-form-card supplier-workbench-empty-card"
        >
          <div class="supplier-workbench-empty-copy">
            <span>下一步</span>
            <strong>先从左侧选择一个供应商</strong>
            <p>选中后这里会直接显示供应商资料、账号状态和可编辑信息；如果还没有供应商，可以先创建一条供应商记录。</p>
          </div>
          <div class="supplier-workbench-empty-actions">
            <el-button type="primary" @click="resetSupplierForm">新建供应商</el-button>
          </div>
        </div>
        <div
          v-if="showSupplierWorkbenchPanel('supplier')"
          v-show="isAdminSession && showMobileSupplierTask('suppliers')"
          class="supplier-form-card"
        >
          <div class="supplier-form-grid">
            <label class="supplier-form-field">
              <span>供应商名称</span>
              <el-input v-model="supplierForm.supplier_name" placeholder="例如：莲菜档口A" />
            </label>
            <label class="supplier-form-field">
              <span>联系人</span>
              <el-input v-model="supplierForm.contact_name" placeholder="例如：老王" />
            </label>
            <label class="supplier-form-field">
              <span>联系电话</span>
              <el-input v-model="supplierForm.contact_phone" placeholder="例如：13800000000" />
            </label>
            <label class="supplier-form-field">
              <span>市场范围</span>
              <el-input v-model="supplierForm.market_scope" placeholder="本地市场 / 周边市场" />
            </label>
            <label class="supplier-form-field">
              <span>主营分类</span>
              <el-select v-model="supplierForm.market_category" clearable filterable placeholder="选择分类">
                <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </label>
            <label class="supplier-form-field">
              <span>默认渠道</span>
              <el-select v-model="supplierForm.channel" clearable filterable placeholder="选择渠道">
                <el-option v-for="item in channelOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </label>
          </div>
          <label class="supplier-form-field supplier-form-field-full">
            <span>备注</span>
            <el-input v-model="supplierForm.notes" type="textarea" :rows="mobile ? 3 : 2" placeholder="例如：只做干调、下午统一发车、支持月结" />
          </label>
          <div class="supplier-account-card">
            <div class="supplier-column-head compact">
              <strong>供应商账号</strong>
              <span data-testid="supplier-account-summary">{{ supplierAccountSummaryLabel }}</span>
            </div>
            <div class="supplier-form-grid">
              <label class="supplier-form-field">
                <span>登录账号</span>
                <el-input v-model="supplierAccountForm.account_username" placeholder="例如：lencai-a" />
              </label>
              <label class="supplier-form-field">
                <span>显示名称</span>
                <el-input v-model="supplierAccountForm.account_display_name" placeholder="例如：莲菜档口A" />
              </label>
              <label class="supplier-form-field">
                <span>{{ selectedSupplier?.account_username ? '重置密码' : '初始密码' }}</span>
                <el-input v-model="supplierAccountForm.account_password" type="password" show-password placeholder="新建账号必须填写；编辑时留空保持原密码" />
              </label>
              <label class="supplier-form-field" data-testid="supplier-account-active-field">
                <span>账号状态</span>
                <el-switch v-model="supplierAccountForm.account_is_active" inline-prompt active-text="启" inactive-text="停" />
              </label>
            </div>
          </div>
          <div class="supplier-form-actions">
            <label class="supplier-status-toggle">
              <span>供应商状态</span>
              <el-switch v-model="supplierForm.is_active" inline-prompt active-text="启" inactive-text="停" />
            </label>
            <div class="supplier-form-action-buttons">
              <el-button plain @click="resetSupplierForm">新建空白</el-button>
              <el-button type="primary" data-testid="supplier-save-button" :loading="supplierSaving" @click="saveSupplier">
                {{ selectedSupplier ? '保存修改' : '创建供应商' }}
              </el-button>
            </div>
          </div>
        </div>

        <div
          v-if="!isProcurementSupplierManagement"
          v-show="showMobileSupplierTask('quote') && showSupplierWorkbenchPanel('quote')"
          class="supplier-form-card"
          :class="{ 'quote-readiness-gated': showMobileQuoteReadinessGate }"
        >
        <div class="supplier-column-head compact">
          <strong>给当前商品录价</strong>
          <div class="supplier-import-actions">
            <span>{{ selectedProductLabelResolved || '未选商品' }}</span>
            <input ref="quoteImportInputRef" class="hidden-file-input" type="file" accept=".xlsx,.xls,.csv" @change="handleQuoteImportFileChange" />
            <el-button v-if="lastQuoteImportFailureRows.length" size="small" plain @click="downloadLastQuoteImportFailures">下载失败行</el-button>
            <el-button size="small" plain data-testid="quote-import-template" @click="downloadQuoteImportTemplate">下载导入模板</el-button>
            <el-button size="small" plain data-testid="quote-import-trigger" :loading="quoteImporting" @click="openQuoteImportDialog">
              {{ isAdminSession ? '批量导入报价' : '批量导入我的报价' }}
            </el-button>
          </div>
        </div>
          <div v-if="isQuoteWorkspace && !selectedProductKey" class="supplier-quote-selection-alert" data-testid="quote-product-required-alert">
            <strong>请先选择商品</strong>
            <span>未从 URL 或商品下拉明确选择商品前，不能提交报价，避免误录到错误商品。</span>
          </div>
          <div v-if="showProcurementCarryTask" class="supplier-procurement-carry-task" data-testid="supplier-procurement-carry-task">
            <div>
              <span>{{ procurementCarryTaskKicker }}</span>
              <strong>{{ procurementCarryTaskTitle }}</strong>
              <p>{{ procurementCarryTaskDescription }}</p>
            </div>
            <div class="supplier-procurement-carry-actions">
              <span>{{ selectedSupplier?.supplier_name || '先选供应商' }}</span>
              <el-button size="small" type="primary" :disabled="quoteSubmitDisabled && !selectedProductKey" @click="focusQuotePriceInput">填写报价</el-button>
            </div>
          </div>
          <div v-if="showQuoteReadinessCard" class="supplier-quote-readiness-card">
            <div class="supplier-quote-readiness-copy">
              <span>录价前检查</span>
              <strong>{{ quoteReadinessTitle }}</strong>
              <p>{{ quoteReadinessDescription }}</p>
            </div>
            <div class="supplier-quote-readiness-list">
              <article
                v-for="item in quoteReadinessItems"
                :key="item.label"
                class="supplier-quote-readiness-item"
                :class="{ ready: item.ready }"
              >
                <span>{{ item.ready ? '已就绪' : '待处理' }}</span>
                <strong>{{ item.label }}</strong>
                <small>{{ item.detail }}</small>
              </article>
            </div>
          <div class="supplier-quote-readiness-actions">
              <el-button
                v-if="isAdminSession && !selectedSupplier"
                size="small"
                type="primary"
                @click="$emit('navigate-section', 'suppliers')"
              >
                去供应平台创建供应商
              </el-button>
              <el-button v-if="!selectedProductKey" size="small" plain @click="$emit('navigate-section', 'quote')">
                先同步商品目录
              </el-button>
              <el-button v-if="selectedSupplier && !selectedSupplier.is_active" size="small" plain @click="$emit('navigate-section', 'suppliers')">
                去供应平台启用
              </el-button>
            </div>
          </div>
          <div v-if="showMobileQuoteReadinessGate" class="supplier-quote-gate-note">
            <strong>录价表单已收起</strong>
            <span>先处理上方待办，完成后再填写报价、单位和备注。</span>
          </div>
          <div v-if="currentQuoteDraft" class="supplier-quote-draft-card">
            <div class="supplier-quote-draft-copy">
              <span>本地草稿</span>
              <strong>{{ currentQuoteDraft.price_identity_label || '未命名商品' }}</strong>
              <small>{{ currentQuoteDraft.supplier_name }} · {{ formatTime(currentQuoteDraft.updated_at) }}</small>
            </div>
            <div class="supplier-quote-draft-meta">
              <span>{{ currentQuoteDraft.quote_price == null ? '未填报价' : formatPrice(currentQuoteDraft.quote_price) }}</span>
              <span>{{ currentQuoteDraft.quote_unit || '默认单位' }}</span>
              <span>{{ currentQuoteDraft.inventory_status || '库存未填' }}</span>
            </div>
            <div class="supplier-quote-draft-actions">
              <el-button size="small" plain @click="restoreQuoteDraft">恢复草稿</el-button>
              <el-button size="small" text @click="clearCurrentQuoteDraft()">删除</el-button>
            </div>
          </div>
          <div v-if="shouldShowQuoteEntryFields && canSwitchQuoteSupplier && isQuoteWorkspace" class="supplier-quote-supplier-switcher">
            <label class="supplier-form-field">
              <span>切换供应商</span>
              <el-select :model-value="selectedSupplierId" filterable placeholder="切换供应商" @change="selectSupplier">
                <el-option
                  v-for="item in filteredSuppliers"
                  :key="item.id"
                  :label="item.supplier_name"
                  :value="item.id"
                />
              </el-select>
            </label>
            <div v-if="selectedSupplier" class="supplier-quote-supplier-meta">
              <span class="supplier-workbench-chip">{{ selectedSupplier.market_category || '待分类' }}</span>
              <span class="supplier-workbench-chip">{{ selectedSupplier.channel || '待标渠道' }}</span>
              <span class="supplier-workbench-chip">{{ selectedSupplier.quote_count || 0 }} 条报价</span>
              <span class="supplier-workbench-chip">{{ formatTime(selectedSupplier.latest_quoted_at) }}</span>
            </div>
          </div>
          <div v-if="shouldShowQuoteEntryFields && productCompareSummary" class="supplier-compare-summary">
            <article class="supplier-compare-card">
              <span>公开最低价</span>
              <strong>{{ formatPrice(productCompareSummary.market_lowest_price) }}</strong>
              <small>{{ productCompareSummary.product_name || selectedProductLabelResolved }}</small>
            </article>
            <article class="supplier-compare-card">
              <span>供应商最低价</span>
              <strong>{{ formatPrice(productCompareSummary.lowest_quote) }}</strong>
              <small>{{ productCompareSummary.lowest_quote_supplier || '待录入' }}</small>
            </article>
            <article class="supplier-compare-card">
              <span>当前供应商</span>
              <strong>{{ formatPrice(selectedSupplierCurrentQuote?.quote_price) }}</strong>
              <small>{{ selectedSupplierComparisonLabel }}</small>
            </article>
          </div>
          <div v-if="shouldShowQuoteEntryFields" class="supplier-form-grid">
            <label class="supplier-form-field supplier-form-field-full">
              <span>先选择本次报价商品</span>
              <el-select :model-value="selectedProductKey" filterable placeholder="先选择本次报价商品" @change="handleProductChange">
                <el-option
                  v-for="item in productOptions"
                  :key="item.price_identity_key"
                  :label="item.price_identity_label"
                  :value="item.price_identity_key"
                />
              </el-select>
            </label>
            <label class="supplier-form-field">
              <span>报价</span>
              <el-input-number ref="quotePriceInputRef" v-model="quoteForm.quote_price" :min="0" :precision="2" :step="0.1" controls-position="right" />
            </label>
            <label class="supplier-form-field">
              <span>单位</span>
              <el-input v-model="quoteForm.quote_unit" placeholder="斤 / 箱 / 件" />
            </label>
            <label class="supplier-form-field">
              <span>箱价</span>
              <el-input-number v-model="quoteForm.box_price" :min="0" :precision="2" :step="0.5" controls-position="right" />
            </label>
            <label class="supplier-form-field">
              <span>含税价</span>
              <el-input-number v-model="quoteForm.tax_price" :min="0" :precision="2" :step="0.5" controls-position="right" />
            </label>
            <label class="supplier-form-field">
              <span>库存状态</span>
              <el-input v-model="quoteForm.inventory_status" placeholder="现货 / 预定 / 缺货" />
            </label>
            <label class="supplier-form-field supplier-form-field-full">
              <span>操作人</span>
              <el-input v-model="operatorName" placeholder="例如：刘洋 / 老王 / 采购部小李" />
            </label>
          </div>
          <label v-if="shouldShowQuoteEntryFields" class="supplier-form-field supplier-form-field-full">
            <span>报价备注</span>
            <el-input v-model="quoteForm.remarks" type="textarea" :rows="mobile ? 3 : 2" placeholder="例如：今天早市价，整箱可送" />
          </label>
          <div v-if="shouldShowQuoteEntryFields" class="supplier-form-actions">
            <div class="supplier-inline-tip">
              <strong>{{ selectedSupplier?.supplier_name || '请先选择或创建供应商' }}</strong>
              <span>{{ selectedProductLabelResolved || selectedProductKey || '请选择商品' }}</span>
            </div>
            <div class="supplier-form-action-buttons">
              <el-button plain :disabled="quoteDraftSaveDisabled" @click="saveQuoteDraft">保存草稿</el-button>
              <el-button type="primary" :loading="quoteSaving" :disabled="quoteSubmitDisabled" @click="saveQuote">提交报价</el-button>
            </div>
          </div>
        </div>
      </section>

      <section v-if="!isProcurementSupplierManagement || isSettlementWorkspace || isLogsWorkspace" v-show="showInsightColumn" class="supplier-admin-column supplier-quotes-column">
        <div v-if="!mobile && shouldShowEmbeddedTabs && !isSupplierWorkspace && !isSettlementWorkspace && !isLogsWorkspace" class="supplier-pane-tabs">
          <button
            v-for="item in desktopSupplierInsightTabs"
            :key="item.key"
            type="button"
            class="supplier-pane-tab"
            :class="{ active: desktopSupplierInsightTab === item.key }"
            @click="desktopSupplierInsightTab = item.key"
          >
            <strong>{{ item.label }}</strong>
            <small>{{ item.detail }}</small>
          </button>
        </div>

        <div
          v-if="showSupplierInsightPanel('overview')"
          v-show="isAdminSession && showMobileSupplierTask('suppliers')"
          class="supplier-form-card"
        >
          <div class="supplier-column-head compact">
            <strong>分类概览</strong>
            <span>{{ categorySummaryItems.length }} 个分类</span>
          </div>
          <div v-if="categorySummaryItems.length" class="supplier-category-list">
            <article
              v-for="item in categorySummaryItems"
              :key="item.market_category"
              class="supplier-category-row"
            >
              <div class="supplier-category-head">
                <strong>{{ item.market_category }}</strong>
                <span>{{ item.quote_count }} 条报价</span>
              </div>
              <div class="supplier-category-meta">
                <span>{{ item.active_supplier_count }}/{{ item.supplier_count }} 家启用</span>
                <span>最近 {{ formatTime(item.latest_quoted_at) }}</span>
              </div>
            </article>
          </div>
          <div v-else class="supplier-card-empty compact-empty">
            <strong>还没有分类统计</strong>
            <p>{{ categoryEmptyDescription }}</p>
          </div>
        </div>

        <div v-if="showSupplierInsightPanel('history')" v-show="showMobileSupplierTask('history')" class="supplier-mobile-task-shell">
          <div class="supplier-column-head">
            <strong>{{ supplierHistoryPanelTitle }}</strong>
            <div class="supplier-history-filters">
              <span>{{ selectedSupplier ? selectedSupplier.supplier_name : '未选择供应商' }}</span>
              <el-select v-model="quoteStatusFilter" size="small" class="supplier-history-filter-select">
                <el-option label="全部历史" value="all" />
                <el-option label="有效报价" value="active" />
                <el-option label="已作废" value="invalidated" />
              </el-select>
            </div>
          </div>
          <div class="supplier-history-context-strip">
            <span class="supplier-workbench-chip">{{ selectedSupplier?.supplier_name || '未选供应商' }}</span>
            <span class="supplier-workbench-chip">{{ selectedProductLabelResolved || '全部商品' }}</span>
            <span class="supplier-workbench-chip">{{ quoteStatusFilter === 'all' ? '全部状态' : quoteStatusFilter === 'active' ? '仅有效报价' : '仅作废报价' }}</span>
            <span class="supplier-workbench-chip">{{ quoteCurrentProductOnly ? '锁定当前商品' : '跨商品查看' }}</span>
          </div>
          <div class="supplier-history-viewbar">
            <div class="supplier-history-viewtabs" aria-label="报价历史视图">
              <button
                v-for="item in quoteHistoryViewTabs"
                :key="item.key"
                type="button"
                class="supplier-history-viewtab"
                :class="{ active: item.active }"
                @click="applyQuoteHistoryView(item.key)"
              >
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </button>
            </div>
            <div class="supplier-history-viewmeta">
              <span>{{ selectedQuoteRows.length ? `已选 ${selectedQuoteRows.length} 条` : `${historyQuoteRows.length} 条可见` }}</span>
              <el-button size="small" text :disabled="!selectedQuoteRows.length" @click="clearSelectedQuotes">清空选择</el-button>
            </div>
          </div>
          <div v-if="historyQuoteTotal" class="supplier-history-command-strip">
            <article>
              <span>当前筛选</span>
              <strong>{{ historyQuoteTotal }} 条</strong>
              <small>{{ historyActiveQuoteCount }} 有效 / {{ historyInvalidatedQuoteCount }} 作废</small>
            </article>
            <article>
              <span>已选报价</span>
              <strong>{{ selectedQuoteRows.length }} 条</strong>
              <small>{{ formatPrice(selectedQuoteTotalAmount) }}</small>
            </article>
            <article>
              <span>最近报价</span>
              <strong>{{ formatTime(historyQuoteRows[0]?.quoted_at) }}</strong>
              <small>{{ historyQuoteRows[0]?.supplier_name || selectedSupplier?.supplier_name || '当前供应商' }}</small>
            </article>
          </div>
          <div class="supplier-history-toolbar">
            <el-input v-model="quoteKeyword" clearable size="small" placeholder="筛商品、规格、备注、作废原因" />
            <el-date-picker
              v-model="quoteDateRange"
              type="daterange"
              unlink-panels
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              size="small"
            />
            <div class="supplier-history-date-shortcuts">
              <el-button size="small" text @click="setQuoteDateRangeShortcut(0)">今天</el-button>
              <el-button size="small" text @click="setQuoteDateRangeShortcut(7)">近7天</el-button>
              <el-button size="small" text @click="setQuoteDateRangeShortcut(30)">近30天</el-button>
              <el-button size="small" text @click="clearQuoteDateRange">清空日期</el-button>
            </div>
            <el-switch v-model="quoteCurrentProductOnly" inline-prompt active-text="当前商品" inactive-text="全部商品" />
            <el-select v-model="quoteHistorySort" size="small" class="supplier-history-filter-select">
              <el-option label="最新优先" value="latest" />
              <el-option label="价格从高到低" value="price_desc" />
              <el-option label="价格从低到高" value="price_asc" />
              <el-option label="状态优先" value="status" />
            </el-select>
            <el-button v-if="hasQuoteHistoryAdvancedFilters" size="small" text @click="resetQuoteHistoryFilters">清空全部筛选</el-button>
          </div>
          <div v-if="historyQuoteTotal" class="supplier-history-summary">
            <span>{{ selectedSupplier ? '筛选总数' : '最近记录' }} {{ historyQuoteTotal }} 条</span>
            <span>本页有效 {{ historyActiveQuoteCount }} 条</span>
            <span>本页作废 {{ historyInvalidatedQuoteCount }} 条</span>
            <span>当前页 {{ historyQuoteRows.length }} 条</span>
          </div>
          <div v-if="quoteHistoryFilterTags.length" class="supplier-history-filter-tags">
            <span v-for="tag in quoteHistoryFilterTags" :key="tag" class="supplier-action-log-chip">
              {{ tag }}
            </span>
          </div>
          <div
            v-if="historyQuoteRows.length"
            class="supplier-history-batch-bar"
            :class="{ 'is-active': selectedQuoteRows.length > 0 }"
          >
            <div class="supplier-history-batch-meta">
              <span>{{ quoteHistorySelectionSummary }}</span>
              <el-button size="small" text @click="selectAllFilteredQuotes">全选当前筛选</el-button>
              <el-button size="small" text @click="selectFilteredQuotesByStatus('active')">只选有效</el-button>
              <el-button size="small" text @click="selectFilteredQuotesByStatus('invalidated')">只选作废</el-button>
              <el-button size="small" text @click="clearSelectedQuotes">清空选择</el-button>
            </div>
            <div class="supplier-history-batch-actions">
              <el-button size="small" plain @click="exportFilteredQuotes('xlsx')">导出当前 Excel</el-button>
              <el-button size="small" plain @click="exportFilteredQuotes('csv')">导出当前 CSV</el-button>
              <el-button size="small" plain :disabled="!selectedQuoteRows.length" @click="exportSelectedQuotes('xlsx')">导出已选 Excel</el-button>
              <el-button size="small" plain :disabled="!selectedQuoteRows.length" @click="exportSelectedQuotes('csv')">导出已选 CSV</el-button>
              <el-button
                size="small"
                plain
                :disabled="!selectedQuoteRows.length"
                :loading="batchActionLoading === 'copy'"
                @click="copySelectedQuotesAsNew"
              >
                批量复制为新报价
              </el-button>
              <el-button
                size="small"
                type="danger"
                plain
                v-if="isAdminSession"
                :disabled="!selectedActiveQuoteRows.length"
                :loading="batchActionLoading === 'invalidate'"
                @click="invalidateSelectedQuotes"
              >
                批量作废
              </el-button>
            </div>
          </div>
        </div>
        <div
          v-if="showSupplierInsightPanel('settlement')"
          v-show="showMobileSupplierTask('settlement') && showSupplierInsightPanel('settlement')"
          class="supplier-form-card supplier-settlement-card"
          :class="{ 'compact-workspace': isSettlementWorkspace }"
        >
          <div class="supplier-column-head compact supplier-settlement-head" :class="{ 'compact-workspace': isSettlementWorkspace }">
            <div class="supplier-settlement-head-copy">
              <strong>结算台账明细</strong>
              <span>{{ selectedSupplier ? `${settlementTotal} 单` : '先选供应商范围' }}</span>
            </div>
            <div class="supplier-settlement-head-actions" :class="{ 'compact-workspace': isSettlementWorkspace }">
              <div class="supplier-settlement-action-grid">
                <el-button size="small" plain :loading="settlementLoading" @click="loadSupplierSettlements">刷新</el-button>
                <el-button v-if="isAdminSession" size="small" plain @click="openSettlementCreateForm">新建结算单</el-button>
                <el-button size="small" plain :disabled="!settlementRows.length" @click="exportSettlementRows('xlsx')">导出 Excel</el-button>
                <el-button size="small" plain :disabled="!settlementRows.length" @click="exportSettlementRows('csv')">导出 CSV</el-button>
              </div>
              <el-button
                v-if="isAdminSession"
                size="small"
                type="primary"
                class="supplier-settlement-build-button"
                :disabled="!selectedActiveQuoteRows.length"
                :loading="settlementSaving === 'build'"
                @click="buildSettlementFromSelectedQuotes"
              >
                用已选报价生成结算单
              </el-button>
              <el-button
                v-if="isAdminSession && !selectedActiveQuoteRows.length"
                size="small"
                plain
                data-testid="settlement-go-quote-history"
                @click="goQuoteHistoryForSettlement"
              >
                去报价历史勾选报价
              </el-button>
            </div>
          </div>
          <div class="supplier-settlement-filters" :class="{ compact: isSettlementWorkspace }">
            <el-select v-model="settlementStatusFilter" size="small" class="supplier-history-filter-select">
              <el-option label="全部结算" value="all" />
              <el-option label="待付款" value="pending" />
              <el-option label="部分付款" value="partial" />
              <el-option label="已结清" value="paid" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
            <el-input v-model="settlementKeyword" clearable size="small" placeholder="搜标题、备注、创建人" />
            <el-date-picker
              v-model="settlementDateRange"
              type="daterange"
              value-format="YYYY-MM-DD"
              unlink-panels
              range-separator="至"
              start-placeholder="账期开始"
              end-placeholder="账期结束"
            />
          </div>
          <div class="supplier-settlement-summary" :class="{ compact: isSettlementWorkspace }">
            <span class="supplier-settlement-summary-chip">本页总额 {{ formatPrice(settlementPageTotalAmount) }}</span>
            <span class="supplier-settlement-summary-chip">已付 {{ formatPrice(settlementPagePaidAmount) }}</span>
            <span class="supplier-settlement-summary-chip">未付 {{ formatPrice(settlementPagePendingAmount) }}</span>
            <span class="supplier-settlement-summary-chip">已选报价 {{ selectedQuoteRows.length }} 条 / {{ formatPrice(selectedQuoteTotalAmount) }}</span>
          </div>
          <div v-if="isAdminSession && !selectedActiveQuoteRows.length" class="supplier-settlement-next-step" data-testid="settlement-selected-quotes-guide">
            需先到报价管理/历史报价勾选有效报价，再生成结算单。
          </div>
          <div v-if="!isSettlementWorkspace" class="supplier-admin-metrics supplier-settlement-stat-grid">
            <div class="supplier-admin-metric supplier-settlement-stat-card">
              <span>本页待付款</span>
              <strong>{{ settlementPagePendingCount }}</strong>
              <small>仍需继续付款跟进</small>
            </div>
            <div class="supplier-admin-metric supplier-settlement-stat-card">
              <span>本页部分付款</span>
              <strong>{{ settlementPagePartialCount }}</strong>
              <small>已付款但未结清</small>
            </div>
            <div class="supplier-admin-metric supplier-settlement-stat-card">
              <span>本页已结清</span>
              <strong>{{ settlementPagePaidCount }}</strong>
              <small>本页已完成对账</small>
            </div>
            <div class="supplier-admin-metric supplier-settlement-stat-card">
              <span>本页结算总额</span>
              <strong>{{ formatPrice(settlementPageTotalAmount) }}</strong>
              <small>当前页所有结算单汇总</small>
            </div>
            <div class="supplier-admin-metric supplier-settlement-stat-card">
              <span>本页未付金额</span>
              <strong>{{ formatPrice(settlementPagePendingAmount) }}</strong>
              <small>当前页剩余待付金额</small>
            </div>
          </div>
          <div v-if="isAdminSession && settlementFormVisible" class="supplier-settlement-form">
            <label class="supplier-form-field supplier-form-field-full">
              <span>结算单标题</span>
              <el-input v-model="settlementForm.settlement_title" placeholder="例如：4月干调月结单" />
            </label>
            <label class="supplier-form-field">
              <span>周期开始</span>
              <el-date-picker v-model="settlementForm.period_start" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" />
            </label>
            <label class="supplier-form-field">
              <span>周期结束</span>
              <el-date-picker v-model="settlementForm.period_end" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" />
            </label>
            <label class="supplier-form-field">
              <span>总金额</span>
              <el-input-number v-model="settlementForm.total_amount" :min="0" :precision="2" :step="1" controls-position="right" />
            </label>
            <label class="supplier-form-field">
              <span>已付金额</span>
              <el-input-number v-model="settlementForm.paid_amount" :min="0" :precision="2" :step="1" controls-position="right" />
            </label>
            <label class="supplier-form-field">
              <span>应付日期</span>
              <el-date-picker v-model="settlementForm.payment_due_date" type="date" value-format="YYYY-MM-DD" placeholder="应付日期" />
            </label>
            <label class="supplier-form-field">
              <span>付款日期</span>
              <el-date-picker v-model="settlementForm.payment_date" type="date" value-format="YYYY-MM-DD" placeholder="付款日期" />
            </label>
            <label class="supplier-form-field supplier-form-field-full">
              <span>备注</span>
              <el-input v-model="settlementForm.remarks" type="textarea" :rows="mobile ? 3 : 2" placeholder="例如：从4月已选报价生成，月底统一付款" />
            </label>
            <div class="supplier-form-actions supplier-form-field-full">
              <span class="supplier-inline-tip">手工结算单可直接录入金额；已选报价生成会由后端自动汇总报价金额。</span>
              <div class="supplier-form-action-buttons">
                <el-button plain @click="settlementFormVisible = false">收起</el-button>
                <el-button type="primary" :loading="settlementSaving === 'create'" @click="createManualSettlement">保存结算单</el-button>
              </div>
            </div>
          </div>
          <div v-if="!selectedSupplier && isSettlementWorkspace" class="supplier-card-empty compact-empty">
            <strong>先确定结算对象</strong>
            <p>结算台账按供应商归集。选择供应商后，会直接显示账期、应付金额、付款状态和下一步处理动作。</p>
            <div class="supplier-empty-actions">
              <el-button size="small" type="primary" @click="selectFirstSupplierForWorkspace">选择第一家供应商</el-button>
              <el-button size="small" plain @click="$emit('navigate-section', 'suppliers')">回档案选择</el-button>
            </div>
          </div>
          <div v-if="selectedSupplier && settlementRows.length" class="supplier-my-settlement-layout supplier-admin-settlement-layout">
            <section class="supplier-my-settlement-list supplier-admin-settlement-list">
              <button
                v-for="(item, index) in settlementRows"
                :key="item.id"
                type="button"
                class="supplier-my-settlement-row supplier-admin-settlement-row"
                :class="{ active: focusedSettlementId === item.id }"
                @click="focusedSettlementId = item.id"
              >
                <div class="supplier-my-settlement-row-topline">
                  <span class="supplier-my-settlement-row-index">#{{ String(index + 1).padStart(2, '0') }}</span>
                  <span class="supplier-my-settlement-row-progress">{{ getSettlementProgressLabel(item) }}</span>
                </div>
                <div class="supplier-my-settlement-row-head">
                  <div class="supplier-my-settlement-row-title">
                    <strong>{{ item.settlement_title }}</strong>
                    <small>{{ item.record_count }} 条报价</small>
                  </div>
                  <span :class="['supplier-status-chip', getSettlementStatusClass(item.status)]">
                    {{ getSettlementStatusLabel(item.status) }}
                  </span>
                </div>
                <div class="supplier-my-settlement-row-meta">
                  <span>账期 {{ formatSettlementPeriod(item) }}</span>
                  <span>应付 {{ formatTime(item.payment_due_date) }}</span>
                </div>
                <div class="supplier-my-settlement-row-metrics">
                  <article>
                    <span>总额</span>
                    <strong>{{ formatPrice(item.total_amount) }}</strong>
                  </article>
                  <article>
                    <span>已付</span>
                    <strong>{{ formatPrice(item.paid_amount) }}</strong>
                  </article>
                  <article>
                    <span>未付</span>
                    <strong>{{ formatPrice(item.pending_amount) }}</strong>
                  </article>
                </div>
                <div class="supplier-my-settlement-row-note">
                  <p>{{ item.remarks || '暂无备注' }}</p>
                </div>
                <div class="supplier-my-settlement-row-progressbar" aria-hidden="true">
                  <span :style="{ width: `${getSettlementProgressPercent(item)}%` }"></span>
                </div>
                <div class="supplier-my-settlement-row-footer">
                  <span>{{ getSettlementFollowUpLabel(item) }}</span>
                  <span>{{ item.created_by || '平台创建' }}</span>
                </div>
              </button>
            </section>

            <aside class="supplier-my-settlement-detail supplier-admin-settlement-detail">
              <template v-if="focusedSettlement">
                <div class="supplier-my-settlement-detail-head">
                  <div class="supplier-my-settlement-detail-heading">
                    <span>当前结算单</span>
                    <strong>{{ focusedSettlement.settlement_title }}</strong>
                    <small>{{ getSettlementStatusLabel(focusedSettlement.status) }} · {{ focusedSettlement.record_count }} 条报价</small>
                  </div>
                  <div class="supplier-my-settlement-detail-head-side">
                    <div class="supplier-my-settlement-detail-progress-pill">
                      <span>付款进度</span>
                      <strong>{{ getSettlementProgressLabel(focusedSettlement) }}</strong>
                    </div>
                    <el-button size="small" text @click="openSettlementDetail(focusedSettlement)">查看详情</el-button>
                  </div>
                </div>

                <div class="supplier-my-settlement-detail-summary">
                  <div class="total">
                    <span>未付金额</span>
                    <strong>{{ formatPrice(focusedSettlement.pending_amount) }}</strong>
                    <small>{{ focusedSettlement.payment_due_date ? `应付 ${formatTime(focusedSettlement.payment_due_date)}` : '未设置应付日期' }}</small>
                  </div>
                  <div>
                    <span>结算总额</span>
                    <strong>{{ formatPrice(focusedSettlement.total_amount) }}</strong>
                  </div>
                  <div>
                    <span>已付金额</span>
                    <strong>{{ formatPrice(focusedSettlement.paid_amount) }}</strong>
                  </div>
                </div>

                <div class="supplier-my-settlement-detail-progress">
                  <div class="supplier-my-settlement-detail-progress-copy">
                    <span>本单付款进度</span>
                    <strong>{{ getSettlementFollowUpLabel(focusedSettlement) }}</strong>
                    <small>{{ getSettlementFollowUpDescription(focusedSettlement) }}</small>
                  </div>
                  <div class="supplier-my-settlement-detail-progress-track" aria-hidden="true">
                    <span :style="{ width: `${getSettlementProgressPercent(focusedSettlement)}%` }"></span>
                  </div>
                  <div class="supplier-my-settlement-detail-progress-legend">
                    <article>
                      <span>已付</span>
                      <strong>{{ formatPrice(focusedSettlement.paid_amount) }}</strong>
                    </article>
                    <article>
                      <span>剩余</span>
                      <strong>{{ formatPrice(focusedSettlement.pending_amount) }}</strong>
                    </article>
                    <article>
                      <span>记录</span>
                      <strong>{{ focusedSettlement.record_count }} 条</strong>
                    </article>
                  </div>
                </div>

                <div class="supplier-my-settlement-detail-grid">
                  <article>
                    <span>账期</span>
                    <strong>{{ formatSettlementPeriod(focusedSettlement) }}</strong>
                  </article>
                  <article>
                    <span>应付日期</span>
                    <strong>{{ formatTime(focusedSettlement.payment_due_date) }}</strong>
                  </article>
                  <article>
                    <span>付款日期</span>
                    <strong>{{ formatTime(focusedSettlement.payment_date) }}</strong>
                  </article>
                  <article>
                    <span>创建人</span>
                    <strong>{{ focusedSettlement.created_by || '平台' }}</strong>
                  </article>
                </div>

                <div class="supplier-admin-settlement-edit-panel">
                  <label class="supplier-form-field">
                    <span>已付金额</span>
                    <el-input-number v-model="focusedSettlement.paid_amount" size="small" :min="0" :precision="2" :step="1" controls-position="right" :disabled="!isAdminSession" />
                  </label>
                  <label class="supplier-form-field">
                    <span>付款日期</span>
                    <el-date-picker v-model="focusedSettlement.payment_date" size="small" type="date" value-format="YYYY-MM-DD" placeholder="付款日期" :disabled="!isAdminSession" />
                  </label>
                  <div class="supplier-admin-settlement-edit-actions">
                    <el-button v-if="isAdminSession && focusedSettlement.status !== 'paid' && focusedSettlement.status !== 'cancelled'" size="small" text type="danger" :loading="settlementSaving === focusedSettlement.id" @click="cancelSettlement(focusedSettlement)">
                      作废
                    </el-button>
                    <el-button v-if="isAdminSession" size="small" plain :disabled="focusedSettlement.status === 'cancelled'" :loading="settlementSaving === focusedSettlement.id" @click="updateSettlementPayment(focusedSettlement)">
                      保存付款
                    </el-button>
                  </div>
                </div>

                <div class="supplier-my-settlement-detail-note">
                  <span>备注</span>
                  <p>{{ focusedSettlement.remarks || '当前结算单没有备注说明。' }}</p>
                </div>

                <div class="supplier-my-settlement-detail-tip">
                  <span>结算提示</span>
                  <strong>{{ getSettlementStatusLabel(focusedSettlement.status) }}</strong>
                  <p>{{ getSettlementFollowUpDescription(focusedSettlement) }}</p>
                </div>
              </template>
            </aside>
          </div>
          <div v-if="selectedSupplier && settlementTotal" class="supplier-history-pagination">
            <el-button size="small" text :disabled="settlementOffset === 0" @click="changeSettlementPage('prev')">上一页</el-button>
            <span>{{ settlementPageLabel }} · 共 {{ Math.max(Math.ceil(settlementTotal / settlementPageSize), 1) }} 页</span>
            <el-button size="small" text :disabled="!settlementHasMore" @click="changeSettlementPage('next')">下一页</el-button>
          </div>
          <div v-else-if="selectedSupplier" class="supplier-card-empty compact-empty">
            <strong>{{ selectedSupplier ? '还没有结算单' : '请先选择供应商' }}</strong>
            <p>{{ selectedSupplier ? '可以手工创建，也可以先勾选历史报价后生成结算单。' : '选择供应商后会显示结算台账。' }}</p>
            <div class="supplier-empty-actions">
              <el-button
                v-if="isAdminSession && selectedSupplier"
                size="small"
                type="primary"
                @click="openSettlementCreateForm"
              >
                手工新建结算单
              </el-button>
              <el-button
                v-else
                size="small"
                plain
                @click="mobileSupplierTask = 'suppliers'"
              >
                去选供应商
              </el-button>
            </div>
          </div>
        </div>
        <div v-if="showSupplierInsightPanel('history')" v-show="showMobileSupplierTask('history') && lastBatchOperationRows.length" class="supplier-last-batch-card">
          <div class="supplier-column-head compact">
            <strong>{{ lastBatchOperationTitle || '最近一批操作结果' }}</strong>
            <span>{{ lastBatchOperationSummary }}</span>
          </div>
          <div class="supplier-last-batch-actions">
            <span>{{ lastBatchOperationRows.length }} 条结果可导出</span>
            <el-button size="small" plain @click="downloadLastBatchOperationResults('xlsx')">导出 Excel</el-button>
            <el-button size="small" plain @click="downloadLastBatchOperationResults('csv')">导出 CSV</el-button>
            <el-button size="small" text @click="clearLastBatchOperationResult">清空结果</el-button>
          </div>
          <div class="supplier-last-batch-preview-list">
            <article
              v-for="(row, index) in lastBatchOperationPreviewRows"
              :key="`batch-preview-${index}`"
              class="supplier-last-batch-preview-row"
            >
              <strong>{{ row.商品 || row.对比键 || `结果 ${index + 1}` }}</strong>
              <div class="supplier-last-batch-preview-meta">
                <span :class="['supplier-action-log-chip', row.状态 === '成功' ? 'is-success' : row.状态 === '跳过' ? 'is-warning' : 'is-danger']">
                  {{ row.状态 || '结果' }}
                </span>
                <span v-if="row.来源记录">来源 {{ row.来源记录 }}</span>
                <span v-if="row.新记录">新记录 {{ row.新记录 }}</span>
              </div>
              <small>{{ row.说明 || '—' }}</small>
            </article>
          </div>
        </div>
          <div
            v-if="showSupplierInsightPanel('history')"
            v-show="showMobileSupplierTask('history') && historyQuoteRows.length"
            class="supplier-quote-list supplier-history-grid-shell"
          >
            <div class="supplier-datagrid-head quote-history-grid supplier-datagrid-head-sticky">
              <button type="button" class="supplier-history-select-head" @click="toggleVisibleQuoteSelection(!allVisibleQuotesSelected)">
                <el-checkbox
                  :model-value="allVisibleQuotesSelected"
                  :indeterminate="someVisibleQuotesSelected && !allVisibleQuotesSelected"
                  @change="toggleVisibleQuoteSelection"
                />
                商品与供应商
              </button>
              <span>价格与库存</span>
              <span>时间与备注</span>
              <span>操作</span>
          </div>
          <article
            v-for="item in historyQuoteRows"
            :key="item.record_id || `${item.supplier_id}-${item.quoted_at}-${item.price_identity_key}`"
            class="supplier-quote-row"
            :class="{ 'is-latest-active': latestActiveQuoteRecordId != null && item.record_id === latestActiveQuoteRecordId, 'is-selected': isQuoteSelected(item) }"
          >
            <div class="supplier-quote-main">
              <div class="supplier-quote-primary">
                <div class="supplier-quote-row-head">
                  <div class="supplier-quote-title-wrap">
                    <el-checkbox
                      v-if="item.record_id"
                      :model-value="isQuoteSelected(item)"
                      @change="(checked) => handleQuoteSelection(item, checked)"
                    />
                    <strong>{{ item.product_name || item.price_identity_label || item.price_identity_key }}</strong>
                  </div>
                  <span :class="['supplier-status-chip', item.status === 'invalidated' ? 'is-inactive' : 'is-active']">
                    {{ getQuoteStatusLabel(item) }}
                  </span>
                </div>
                <div class="supplier-quote-row-meta">
                  <span>{{ item.market_category || item.category || '待分类' }}</span>
                  <span>{{ item.supplier_name || selectedSupplier?.supplier_name || '未标供应商' }}</span>
                  <span>{{ item.quote_unit || '未标单位' }}</span>
                </div>
              </div>
              <div class="supplier-quote-price-panel">
                <strong>{{ formatPrice(item.quote_price) }}</strong>
                <span>{{ item.inventory_status || '库存待确认' }}</span>
                <small v-if="item.box_price != null">箱价 {{ formatPrice(item.box_price) }}</small>
                <small v-if="item.tax_price != null">含税 {{ formatPrice(item.tax_price) }}</small>
              </div>
              <div class="supplier-quote-context">
                <div class="supplier-quote-row-foot">
                  <small>{{ formatTime(item.quoted_at) }}</small>
                  <small v-if="latestActiveQuoteRecordId != null && item.record_id === latestActiveQuoteRecordId" class="supplier-latest-badge">
                    最新有效报价
                  </small>
                </div>
                <p class="supplier-quote-note">{{ item.invalidated_reason || item.remarks || '无备注' }}</p>
              </div>
              <div class="supplier-quote-actions supplier-quote-actions-column">
                <el-button size="small" plain @click="copyQuoteAsNew(item)">复制</el-button>
                <el-button
                  v-if="isAdminSession"
                  size="small"
                  type="danger"
                  plain
                  :loading="quoteActionLoadingId === item.record_id"
                  @click="invalidateQuote(item)"
                >
                  {{ item.status === 'invalidated' ? '修改作废原因' : '作废' }}
                </el-button>
              </div>
            </div>
          </article>
        </div>
        <div v-if="showSupplierInsightPanel('history')" v-show="showMobileSupplierTask('history') && selectedSupplier && quoteTotal" class="supplier-history-pagination">
          <el-button size="small" text :disabled="quotePageOffset === 0" @click="changeQuotePage('prev')">上一页</el-button>
          <span>{{ quotePageLabel }} · 共 {{ Math.max(Math.ceil(quoteTotal / quotePageSize), 1) }} 页</span>
          <el-button size="small" text :disabled="!quoteHasMore" @click="changeQuotePage('next')">下一页</el-button>
        </div>
        <div
          v-if="showSupplierInsightPanel('history')"
          v-show="showMobileSupplierTask('history') && historyQuoteTotal && historyQuoteRows.length <= 3"
          class="supplier-quote-assist-grid"
        >
          <article v-for="item in quoteAssistCards" :key="item.label" class="supplier-quote-assist-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.detail }}</small>
          </article>
        </div>
        <div v-if="showSupplierInsightPanel('history')" v-show="showMobileSupplierTask('history') && !historyQuoteTotal" class="supplier-card-empty">
          <strong>{{ selectedSupplier ? ((selectedSupplier.quote_count || 0) > 0 ? '当前筛选条件下没有报价' : '这家供应商还没有录价') : '暂无全局最近报价' }}</strong>
          <p>{{ selectedSupplier ? ((selectedSupplier.quote_count || 0) > 0 ? '可以调整状态、关键词、日期或“当前商品”筛选条件。' : supplierQuoteEmptyDescription) : '可以先选择供应商后查看更完整的历史。' }}</p>
          <div class="supplier-empty-actions">
            <el-button
              v-if="selectedSupplier && !isProcurementSupplierManagement"
              size="small"
              type="primary"
              @click="mobileSupplierTask = 'quote'"
            >
              去录第一条报价
            </el-button>
            <el-button
              v-else
              size="small"
              plain
              @click="openSupplierPickerFromHistory"
            >
              去选供应商
            </el-button>
          </div>
        </div>

        <div
          v-if="showSupplierInsightPanel('logs')"
          v-show="isAdminSession && showMobileSupplierTask('history')"
          class="supplier-form-card supplier-logs-card"
          :class="{ 'compact-workspace': isLogsWorkspace }"
        >
          <div class="supplier-column-head compact supplier-logs-head" :class="{ 'compact-workspace': isLogsWorkspace }">
            <strong>操作日志明细</strong>
            <div class="supplier-action-log-filters" :class="{ 'compact-workspace': isLogsWorkspace }">
              <span>{{ selectedSupplier ? `${quoteActionTotal} 条` : '先选供应商范围' }}</span>
              <span v-if="selectedSupplier">{{ selectedSupplier.supplier_name }}</span>
              <el-button size="small" plain :loading="loading" @click="reloadAll">同步数据</el-button>
            </div>
          </div>
          <div v-if="!selectedSupplier && isLogsWorkspace" class="supplier-card-empty compact-empty">
            <strong>先确定日志范围</strong>
            <p>操作日志按供应商归集。选择供应商后，会显示导入、导出、复制、作废和结算动作的时间线。</p>
            <div class="supplier-empty-actions">
              <el-button size="small" type="primary" @click="selectFirstSupplierForWorkspace">选择第一家供应商</el-button>
              <el-button size="small" plain @click="$emit('navigate-section', 'suppliers')">回档案选择</el-button>
            </div>
          </div>
          <template v-else>
          <div class="supplier-action-log-summary" :class="{ 'compact-workspace': isLogsWorkspace }">
            <article>
              <span>留痕动作</span>
              <strong>{{ quoteActionTotal || filteredQuoteActionLogs.length }}</strong>
              <small>{{ selectedSupplier ? `${selectedSupplier.supplier_name} 当前范围` : '全局供应商范围' }}</small>
            </article>
            <article>
              <span>筛选状态</span>
              <strong>{{ hasQuoteActionAdvancedFilters ? '已筛选' : '全部动作' }}</strong>
              <small>{{ hasQuoteActionAdvancedFilters ? quoteActionFilterTags.join(' / ') : '导入、导出、复制、作废统一查询' }}</small>
            </article>
            <article>
              <span>最近动作</span>
              <strong>{{ filteredQuoteActionLogs[0] ? getQuoteActionLabel(filteredQuoteActionLogs[0]) : '暂无动作' }}</strong>
              <small>{{ filteredQuoteActionLogs[0] ? formatTime(filteredQuoteActionLogs[0].created_at) : '产生操作后会自动按时间倒序显示' }}</small>
            </article>
          </div>
          <div class="supplier-action-log-filter-grid" :class="{ 'compact-workspace': isLogsWorkspace }">
            <el-select v-model="quoteActionTypeFilter" size="small" class="supplier-history-filter-select">
              <el-option label="全部动作" value="all" />
              <el-option label="复制为新报价" value="copy_as_new" />
              <el-option label="作废报价" value="invalidate" />
              <el-option label="修改作废原因" value="update_invalidation_reason" />
              <el-option label="批量导入报价" value="import_quotes" />
              <el-option label="导出历史报价" value="export_quotes" />
              <el-option label="导出结算台账" value="export_settlements" />
              <el-option label="创建结算单" value="create_settlement" />
              <el-option label="更新结算单" value="update_settlement" />
              <el-option label="作废结算单" value="cancel_settlement" />
              <el-option label="报价生成结算单" value="build_settlement_from_quotes" />
            </el-select>
            <el-input v-model="quoteActionOperatorFilter" clearable size="small" placeholder="按操作人筛选" />
            <el-input v-model="quoteActionKeywordFilter" clearable size="small" placeholder="按商品 / 原因 / 备注筛选" />
            <el-date-picker
              v-model="quoteActionDateRange"
              type="daterange"
              unlink-panels
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              size="small"
            />
          </div>
          <div v-if="quoteActionFilterTags.length" class="supplier-action-log-tags">
            <span
              v-for="tag in quoteActionFilterTags"
              :key="tag"
              class="supplier-action-log-chip"
            >
              {{ tag }}
            </span>
            <el-button size="small" text @click="resetQuoteActionFilters">清空筛选</el-button>
          </div>
          <div class="supplier-history-date-shortcuts supplier-action-log-shortcuts">
            <el-button size="small" text @click="setQuoteActionDateRangeShortcut(0)">今天</el-button>
            <el-button size="small" text @click="setQuoteActionDateRangeShortcut(7)">近7天</el-button>
            <el-button size="small" text @click="setQuoteActionDateRangeShortcut(30)">近30天</el-button>
            <el-button size="small" text @click="clearQuoteActionDateRange">清空日期</el-button>
          </div>
          <div v-if="filteredQuoteActionLogs.length" class="supplier-action-log-list">
            <article v-for="item in filteredQuoteActionLogs" :key="item.id" class="supplier-action-log-row">
              <div class="supplier-quote-row-head">
                <strong>{{ getQuoteActionLabel(item) }}</strong>
                <span>{{ formatTime(item.created_at) }}</span>
              </div>
              <div class="supplier-quote-row-meta">
                <span>{{ item.product_name || item.price_identity_label || item.price_identity_key || '供应商历史报价' }}</span>
                <span>{{ item.operator_name || '供应平台' }}</span>
              </div>
              <div class="supplier-quote-row-foot">
                <small>{{ item.action_reason || getQuoteActionDescription(item) }}</small>
                <small v-if="item.target_product_name || item.target_price_identity_label">
                  新报价：{{ item.target_product_name || item.target_price_identity_label }}
                </small>
              </div>
              <div v-if="getQuoteActionPayloadTags(item).length" class="supplier-action-log-tags">
                <span
                  v-for="tag in getQuoteActionPayloadTags(item)"
                  :key="`${item.id}-${tag}`"
                  class="supplier-action-log-chip"
                >
                  {{ tag }}
                </span>
              </div>
              <div v-if="shouldShowQuoteActionPayloadDetails(item)" class="supplier-action-log-actions">
                <el-button size="small" text @click="openQuoteActionDetail(item)">
                  查看详情
                </el-button>
              </div>
            </article>
          </div>
          <div v-if="quoteActionTotal" class="supplier-history-pagination">
            <el-button size="small" text :disabled="quoteActionOffset === 0" @click="changeQuoteActionPage('prev')">上一页</el-button>
            <span>{{ quoteActionPageLabel }} · 共 {{ Math.max(Math.ceil(quoteActionTotal / quoteActionPageSize), 1) }} 页</span>
            <el-button size="small" text :disabled="!quoteActionHasMore" @click="changeQuoteActionPage('next')">下一页</el-button>
          </div>
          <div v-else class="supplier-card-empty compact-empty">
            <strong>{{ hasQuoteActionAdvancedFilters ? '当前筛选条件下没有日志' : '还没有操作日志' }}</strong>
            <p>{{ hasQuoteActionAdvancedFilters ? '可以放宽动作、操作人、关键词或日期条件后再试。' : '导出、作废、修改作废原因和历史复制完成后，这里会按时间倒序保留最近动作。' }}</p>
          </div>
          </template>
        </div>

        <div v-if="showSupplierInsightPanel('overview')" v-show="showMobileSupplierTask('suppliers')" class="supplier-form-card">
          <div class="supplier-column-head compact">
            <strong>平台最新录价</strong>
            <div class="supplier-overview-head-actions">
              <span>{{ recentQuoteRows.length }} 条</span>
              <el-button size="small" text @click="openQuoteHistoryPanel">查看历史报价</el-button>
            </div>
          </div>
          <div v-if="recentQuoteRows.length" class="supplier-overview-quote-list">
            <button
              v-for="item in recentQuoteRows"
              :key="`${item.supplier_id}-${item.quoted_at}-${item.price_identity_key}-overview`"
              type="button"
              class="supplier-overview-quote-row"
              @click="focusRecentQuote(item)"
            >
              <div class="supplier-quote-row-head">
                <strong>{{ item.supplier_name }}</strong>
                <div class="supplier-quote-head-side">
                  <span>{{ formatPrice(item.quote_price) }}</span>
                  <span :class="['supplier-status-chip', item.status === 'invalidated' ? 'is-inactive' : 'is-active']">
                    {{ getQuoteStatusLabel(item) }}
                  </span>
                </div>
              </div>
              <div class="supplier-quote-row-meta">
                <span>{{ item.product_name || item.price_identity_label || item.price_identity_key }}</span>
                <span>{{ item.market_category || item.category || '待分类' }}</span>
              </div>
              <div class="supplier-quote-row-foot">
                <small>{{ formatTime(item.quoted_at) }}</small>
                <small>{{ item.quote_unit || '未标单位' }}</small>
              </div>
            </button>
          </div>
          <div v-else class="supplier-card-empty compact-empty">
            <strong>还没有平台录价</strong>
            <p>{{ recentQuoteEmptyDescription }}</p>
            <div class="supplier-empty-actions">
              <el-button v-if="!isProcurementSupplierManagement" size="small" plain @click="mobileSupplierTask = 'quote'">去录第一条报价</el-button>
            </div>
          </div>
        </div>
      </section>
    </div>
    </template>

    <el-dialog
      v-model="quoteImportPreviewVisible"
      title="批量导入报价预览"
      width="min(960px, calc(100vw - 24px))"
      destroy-on-close
    >
      <div class="quote-import-preview-shell">
        <div class="quote-import-preview-summary">
          <span>文件：{{ quoteImportPreviewFileName || '未选择文件' }}</span>
          <span>总行数：{{ quoteImportPreviewRows.length }}</span>
          <span>可导入：{{ readyQuoteImportPreviewCount }}</span>
          <span>待处理：{{ invalidQuoteImportPreviewCount }}</span>
          <span>将新增：{{ appendQuoteImportPreviewCount }}</span>
          <span>将跳过：{{ skipQuoteImportPreviewCount }}</span>
          <span>将覆盖：{{ overrideQuoteImportPreviewCount }}</span>
          <span>波动异常：{{ abnormalQuoteImportPreviewCount }}</span>
        </div>
        <div class="quote-import-config-grid">
          <label class="quote-import-mode-field">
            <span>导入模式</span>
            <el-select v-model="quoteImportMode" size="small" class="quote-import-mode-select">
              <el-option
                v-for="option in QUOTE_IMPORT_MODE_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <small>{{ getQuoteImportModeDescription(quoteImportMode) }}</small>
          </label>
          <label class="quote-import-mode-field">
            <span>重复判定字段</span>
            <el-select
              v-model="quoteImportDuplicateMatchFields"
              size="small"
              multiple
              clearable
              collapse-tags
              collapse-tags-tooltip
              filterable
              class="quote-import-duplicate-select"
              placeholder="留空则使用系统默认规则"
            >
              <el-option
                v-for="option in QUOTE_IMPORT_DUPLICATE_FIELD_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <small>{{ quoteImportDuplicateFieldSummary }}</small>
          </label>
          <label class="quote-import-mode-field">
            <span>异常波动阈值</span>
            <el-input-number
              v-model="quoteImportAbnormalThresholdPercent"
              size="small"
              :min="0"
              :step="5"
              controls-position="right"
            />
            <small>例如填 20 表示相对当前有效价波动超过 20% 时高亮提示；留空则不提示。</small>
          </label>
        </div>
        <div class="quote-import-preview-rule-tags">
          <span
            v-for="tag in quoteImportRuleTags"
            :key="tag"
            class="supplier-action-log-chip"
          >
            {{ tag }}
          </span>
        </div>
        <div v-if="quoteImportPreviewRows.length" class="quote-import-preview-filters">
          <button
            type="button"
            class="quote-import-preview-filter-chip"
            :class="{ active: quoteImportPreviewFilter === 'all' }"
            @click="quoteImportPreviewFilter = 'all'"
          >
            全部 {{ quoteImportPreviewRows.length }}
          </button>
          <button
            type="button"
            class="quote-import-preview-filter-chip"
            :class="{ active: quoteImportPreviewFilter === 'append' }"
            @click="quoteImportPreviewFilter = 'append'"
          >
            将新增 {{ appendQuoteImportPreviewCount }}
          </button>
          <button
            type="button"
            class="quote-import-preview-filter-chip"
            :class="{ active: quoteImportPreviewFilter === 'skip_duplicate' }"
            @click="quoteImportPreviewFilter = 'skip_duplicate'"
          >
            将跳过 {{ skipQuoteImportPreviewCount }}
          </button>
          <button
            type="button"
            class="quote-import-preview-filter-chip"
            :class="{ active: quoteImportPreviewFilter === 'override_latest' }"
            @click="quoteImportPreviewFilter = 'override_latest'"
          >
            将覆盖 {{ overrideQuoteImportPreviewCount }}
          </button>
          <button
            type="button"
            class="quote-import-preview-filter-chip"
            :class="{ active: quoteImportPreviewFilter === 'abnormal' }"
            @click="quoteImportPreviewFilter = 'abnormal'"
          >
            波动异常 {{ abnormalQuoteImportPreviewCount }}
          </button>
          <button
            type="button"
            class="quote-import-preview-filter-chip"
            :class="{ active: quoteImportPreviewFilter === 'invalid' }"
            @click="quoteImportPreviewFilter = 'invalid'"
          >
            待修正 {{ invalidQuoteImportPreviewCount }}
          </button>
        </div>
        <div v-if="quoteImportPreviewRows.length" class="quote-import-preview-table">
          <div v-if="mobile" class="quote-import-preview-card-list">
            <article
              v-for="row in filteredQuoteImportPreviewRows"
              :key="`preview-${row.row_number}`"
              class="quote-import-preview-card"
            >
              <div class="quote-import-preview-card-head">
                <strong>第 {{ row.row_number }} 行 · {{ row.product_name || row.matched_product_label || row.price_identity_key || '未识别商品' }}</strong>
                <span :class="['quote-import-status-chip', row.status === 'ready' ? 'is-ready' : 'is-error']">
                  {{ row.status === 'ready' ? '可导入' : '待修正' }}
                </span>
              </div>
              <div class="quote-import-preview-card-meta">
                <span>对比键：{{ row.price_identity_key || '—' }}</span>
                <span>报价：{{ row.quote_price || '—' }} {{ row.quote_unit || '' }}</span>
                <span>匹配商品：{{ row.matched_product_label || '未匹配' }}</span>
              </div>
              <div class="quote-import-preview-card-section">
                <strong :class="['quote-import-preview-decision', getQuoteImportPreviewDecisionClass(row)]">
                  {{ getQuoteImportPreviewDecisionLabel(row) }}
                </strong>
                <small>{{ getQuoteImportPreviewDecisionReason(row) }}</small>
              </div>
              <div class="quote-import-preview-card-section">
                <strong>当前有效报价：{{ getQuoteImportPreviewExistingLabel(row) }}</strong>
                <small>{{ getQuoteImportPreviewExistingMeta(row) }}</small>
              </div>
              <div v-if="row.abnormal_change_ratio != null" class="quote-import-preview-card-section is-abnormal">
                <strong>异常波动：{{ formatPercent(row.abnormal_change_ratio) }}</strong>
                <small>{{ row.abnormal_change_hint }}</small>
              </div>
            </article>
          </div>
          <el-table v-else :data="filteredQuoteImportPreviewRows" size="small" max-height="420">
            <el-table-column prop="row_number" label="行号" width="72" />
            <el-table-column prop="price_identity_key" label="对比键" min-width="132" show-overflow-tooltip />
            <el-table-column prop="product_name" label="商品" min-width="180" show-overflow-tooltip />
            <el-table-column prop="quote_price" label="报价" width="108" />
            <el-table-column label="匹配结果" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="quote-import-preview-cell">
                  <strong>{{ row.matched_product_label || '未匹配' }}</strong>
                  <small>{{ row.reason || (row.status === 'ready' ? '可直接导入' : '需先修正') }}</small>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="导入诊断" min-width="240" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="quote-import-preview-cell">
                  <strong :class="['quote-import-preview-decision', getQuoteImportPreviewDecisionClass(row)]">
                    {{ getQuoteImportPreviewDecisionLabel(row) }}
                  </strong>
                  <small>{{ getQuoteImportPreviewDecisionReason(row) }}</small>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="当前有效报价" min-width="220" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="quote-import-preview-cell">
                  <strong>{{ getQuoteImportPreviewExistingLabel(row) }}</strong>
                  <small>{{ getQuoteImportPreviewExistingMeta(row) }}</small>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <span :class="['quote-import-status-chip', row.status === 'ready' ? 'is-ready' : 'is-error']">
                  {{ row.status === 'ready' ? '可导入' : '待修正' }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <div class="quote-import-preview-footer">
          <el-button plain @click="closeQuoteImportPreview">取消</el-button>
          <el-button
            v-if="invalidQuoteImportPreviewCount"
            plain
            @click="downloadQuoteImportPreviewFailures"
          >
            下载待修正行
          </el-button>
          <el-button
            type="primary"
            :loading="quoteImporting"
            :disabled="!readyQuoteImportPreviewCount"
            @click="confirmQuoteImport"
          >
            确认导入 {{ readyQuoteImportPreviewCount }} 条
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="quoteActionDetailVisible"
      :title="activeQuoteActionDetail ? `${getQuoteActionLabel(activeQuoteActionDetail)}详情` : '操作详情'"
      width="min(860px, calc(100vw - 24px))"
      destroy-on-close
    >
      <div v-if="activeQuoteActionDetail" class="supplier-action-detail-shell">
        <div class="supplier-action-detail-meta">
          <span>{{ formatTime(activeQuoteActionDetail.created_at) }}</span>
          <span>{{ activeQuoteActionDetail.operator_name || '供应平台' }}</span>
          <span>{{ getQuoteActionDescription(activeQuoteActionDetail) }}</span>
        </div>
        <div v-if="activeQuoteActionDetailTags.length" class="supplier-action-log-tags">
          <span
            v-for="tag in activeQuoteActionDetailTags"
            :key="`dialog-${activeQuoteActionDetail.id}-${tag}`"
            class="supplier-action-log-chip"
          >
            {{ tag }}
          </span>
        </div>
        <div v-if="activeQuoteActionDetail.action_reason" class="supplier-action-log-failure-list">
          <strong>操作说明</strong>
          <p>{{ activeQuoteActionDetail.action_reason }}</p>
        </div>
        <div v-if="activeQuoteActionDetailEntries.length" class="supplier-action-log-detail-grid">
          <div
            v-for="entry in activeQuoteActionDetailEntries"
            :key="`${activeQuoteActionDetail.id}-${entry.label}`"
            class="supplier-action-log-detail-item"
          >
            <span>{{ entry.label }}</span>
            <strong>{{ entry.value }}</strong>
          </div>
        </div>
        <div v-if="activeQuoteActionSuccessRecordIds.length" class="supplier-action-log-failure-list">
          <strong>成功记录 ID</strong>
          <p>{{ activeQuoteActionSuccessRecordIds.join('、') }}</p>
        </div>
        <div v-if="activeQuoteActionFailureExamples.length" class="supplier-action-log-failure-list">
          <strong>失败示例</strong>
          <p
            v-for="(example, index) in activeQuoteActionFailureExamples"
            :key="`${activeQuoteActionDetail.id}-example-${index}`"
          >
            {{ example }}
          </p>
        </div>
        <div v-if="activeQuoteActionRows.length" class="supplier-action-log-failure-list">
          <strong>{{ isImportQuoteAction(activeQuoteActionDetail) ? '返回行明细' : '记录快照' }}</strong>
          <p
            v-for="(row, index) in activeQuoteActionRows"
            :key="`${activeQuoteActionDetail.id}-row-${index}`"
          >
            {{ formatQuoteActionPayloadRowSummary(row, index) }}
            <template v-if="formatQuoteActionPayloadRowDetail(row)">
              · {{ formatQuoteActionPayloadRowDetail(row) }}
            </template>
          </p>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="settlementDetailVisible"
      :title="activeSettlementDetail?.item ? `${activeSettlementDetail.item.settlement_title}详情` : '结算单详情'"
      width="min(880px, calc(100vw - 24px))"
      destroy-on-close
    >
      <div v-if="activeSettlementDetail?.item" class="supplier-action-detail-shell">
        <div class="supplier-settlement-summary">
          <span>总额 {{ formatPrice(activeSettlementDetail.item.total_amount) }}</span>
          <span>已付 {{ formatPrice(activeSettlementDetail.item.paid_amount) }}</span>
          <span>未付 {{ formatPrice(activeSettlementDetail.item.pending_amount) }}</span>
          <span>{{ getSettlementStatusLabel(activeSettlementDetail.item.status) }}</span>
        </div>
        <div class="supplier-action-log-detail-grid">
          <div class="supplier-action-log-detail-item">
            <span>账期</span>
            <strong>{{ formatSettlementPeriod(activeSettlementDetail.item) }}</strong>
          </div>
          <div class="supplier-action-log-detail-item">
            <span>应付日期</span>
            <strong>{{ formatTime(activeSettlementDetail.item.payment_due_date) }}</strong>
          </div>
          <div class="supplier-action-log-detail-item">
            <span>付款日期</span>
            <strong>{{ formatTime(activeSettlementDetail.item.payment_date) }}</strong>
          </div>
          <div class="supplier-action-log-detail-item">
            <span>创建人</span>
            <strong>{{ activeSettlementDetail.item.created_by || '供应平台' }}</strong>
          </div>
        </div>
        <div v-if="activeSettlementDetail.item.remarks" class="supplier-action-log-failure-list">
          <strong>备注</strong>
          <p>{{ activeSettlementDetail.item.remarks }}</p>
        </div>
        <div class="supplier-action-log-failure-list">
          <strong>关联报价记录</strong>
          <p v-if="!activeSettlementDetail.quote_items.length">未找到关联报价明细</p>
          <p
            v-for="quote in activeSettlementDetail.quote_items"
            :key="`settlement-quote-${quote.record_id}`"
          >
            {{ quote.product_name || quote.price_identity_label || quote.price_identity_key }}
            · {{ formatPrice(quote.quote_price) }}
            · {{ quote.quote_unit || '未标单位' }}
            · {{ formatTime(quote.quoted_at) }}
          </p>
        </div>
      </div>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { ElCheckbox } from 'element-plus/es/components/checkbox/index.mjs'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { ElMessageBox } from 'element-plus/es/components/message-box/index.mjs'
import {
  buildSupplierSettlementsFromQuotes,
  cancelSupplierSettlement,
  createSupplierSettlement,
  createSupplier,
  createSupplierQuoteAction,
  fetchProductSupplierQuotes,
  fetchSupplierSettlementDetail,
  fetchSupplierOverview,
  fetchSupplierQuoteActions,
  fetchSupplierQuotesBySupplier,
  fetchSupplierSettlementsBySupplier,
  fetchSuppliers,
  importSupplierQuotes,
  invalidateSupplierQuote,
  previewImportSupplierQuotes,
  submitSupplierQuote,
  updateSupplier,
  updateSupplierSettlement,
} from '../api'
import type {
  ProductOptionItem,
  AuthUserRole,
  SupplierCategorySummaryItem,
  SupplierItem,
  SupplierOverviewResponse,
  SupplierQuoteActionItem,
  SupplierQuoteCompareResponse,
  SupplierQuoteCreatePayload,
  SupplierQuoteDuplicateField,
  SupplierQuoteImportItemPayload,
  SupplierQuoteImportMode,
  SupplierQuoteImportPayload,
  SupplierQuoteImportPreviewItem,
  SupplierQuoteImportResultItem,
  SupplierQuoteItem,
  SupplierSettlementDetailResponse,
  SupplierSettlementItem,
  SupplierSettlementStatus,
} from '../types'

const props = defineProps<{
  productOptions: ProductOptionItem[]
  selectedIdentityKey: string
  selectedProductLabel: string
  procurementSourceLabel?: string
  procurementSourceType?: string
  mobile: boolean
  authRole?: AuthUserRole | null
  authSupplierId?: number | null
  authDisplayName?: string | null
  backendSection?: 'suppliers' | 'quote' | 'settlement' | 'logs' | null
  procurementMode?: boolean
  showEmbeddedTabs?: boolean
  mobileTask?: MobileSupplierTask | null
}>()
const mobile = computed(() => props.mobile)
const procurementAdminView = ref<'suppliers'>('suppliers')

const emit = defineEmits<{
  (event: 'select-product', value: string): void
  (event: 'navigate-section', value: 'suppliers' | 'quote' | 'settlement' | 'logs'): void
  (event: 'open-procurement-product'): void
  (event: 'quote-draft-summary', value: { count: number; hasCurrent: boolean; latestLabel: string; latestUpdatedAt: string }): void
}>()

type QuoteActionTypeFilter = 'all' | 'copy_as_new' | 'invalidate' | 'update_invalidation_reason' | 'import_quotes' | 'export_quotes' | 'export_settlements' | 'create_settlement' | 'update_settlement' | 'cancel_settlement' | 'build_settlement_from_quotes'
type QuoteImportPreviewFilter = 'all' | 'append' | 'skip_duplicate' | 'override_latest' | 'invalid' | 'abnormal'
const ACCOUNT_USERNAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.@-]{2,63}$/
const MIN_ACCOUNT_PASSWORD_LENGTH = 8
type QuoteImportHeaderKey =
  | 'price_identity_key'
  | 'product_name'
  | 'quote_price'
  | 'quote_unit'
  | 'box_price'
  | 'tax_price'
  | 'inventory_status'
  | 'remarks'
  | 'quoted_at'
  | 'channel'
  | 'market_category'
  | 'market_scope'

type ImportedSupplierQuoteDraft = Partial<Record<QuoteImportHeaderKey, string>> & {
  row_number: number
}

type MatchedImportedProduct = {
  price_identity_key: string
  price_identity_label: string
  product_name: string
}

type QuoteImportPreviewRow = {
  row_number: number
  price_identity_key: string
  product_name: string
  quote_price: string
  quote_unit: string
  matched_product_label: string
  status: 'ready' | 'error'
  reason: string
  draft: ImportedSupplierQuoteDraft
  payload?: SupplierQuoteCreatePayload
  preview_status?: 'append' | 'skip_duplicate' | 'override_latest' | 'invalid'
  preview_reason?: string
  existing_record_id?: number | null
  existing_quote_price?: number | null
  existing_quote_unit?: string | null
  existing_quoted_at?: string | null
  existing_remarks?: string | null
  duplicate_match_fields?: SupplierQuoteDuplicateField[]
  abnormal_change_ratio?: number | null
  abnormal_change_hint?: string | null
}

type QuoteActionPayload = Record<string, unknown>
type QuoteActionDetailEntry = { label: string; value: string }
type BatchOperationKind = 'import' | 'copy' | 'invalidate'
type BatchOperationExportRow = Record<string, string | number | null | undefined>
type SupplierQuoteDraft = {
  supplier_id: number
  supplier_name: string
  price_identity_key: string
  price_identity_label: string
  quote_price?: number
  quote_unit: string
  box_price?: number
  tax_price?: number
  inventory_status: string
  remarks: string
  operator_name: string
  updated_at: string
}
type MobileSupplierTask = 'suppliers' | 'quote' | 'history' | 'settlement'
type MobilePrimaryAction = 'create_supplier' | 'save_quote' | 'open_quote' | 'open_suppliers' | 'open_settlement_create' | 'open_history' | 'build_settlement'
type DesktopSupplierInsightTab = 'overview' | 'history' | 'settlement' | 'logs'
type DesktopSupplierWorkbenchTab = 'supplier' | 'quote'
type QuoteHistoryView = 'all' | 'active' | 'invalidated' | 'current_product'

const TEXT_ENCODINGS = ['utf-8', 'gb18030']
const LAST_SUPPLIER_ID_STORAGE_KEY = 'battel:supplier-admin-last-supplier-id'
const RECENT_SUPPLIER_IDS_STORAGE_KEY = 'battel:supplier-admin-recent-supplier-ids'
const QUOTE_DRAFTS_STORAGE_KEY = 'battel:supplier-admin-quote-drafts'
const QUOTE_IMPORT_MODE_OPTIONS: Array<{ value: SupplierQuoteImportMode; label: string; description: string }> = [
  { value: 'append', label: '追加导入', description: '保留历史报价，每一行都按新的报价记录导入。' },
  { value: 'skip_duplicate', label: '跳过重复', description: '遇到重复报价时跳过该行，避免重复写入。' },
  { value: 'override_latest', label: '覆盖最新', description: '若存在重复报价，则覆盖当前最新有效报价。' },
]
const QUOTE_IMPORT_DUPLICATE_FIELD_OPTIONS: Array<{ value: SupplierQuoteDuplicateField; label: string }> = [
  { value: 'quote_price', label: '报价' },
  { value: 'quote_unit', label: '单位' },
  { value: 'box_price', label: '箱价' },
  { value: 'tax_price', label: '含税价' },
  { value: 'inventory_status', label: '库存状态' },
  { value: 'remarks', label: '备注' },
  { value: 'channel', label: '渠道' },
  { value: 'market_category', label: '分类' },
  { value: 'market_scope', label: '市场范围' },
]
const QUOTE_IMPORT_DEFAULT_HEADERS: QuoteImportHeaderKey[] = [
  'price_identity_key',
  'product_name',
  'quote_price',
  'quote_unit',
  'box_price',
  'tax_price',
  'inventory_status',
  'remarks',
  'quoted_at',
  'channel',
  'market_category',
]
const QUOTE_IMPORT_HEADER_ALIASES: Record<QuoteImportHeaderKey, string[]> = {
  price_identity_key: ['对比键', '对比key', 'price_identity_key', 'identity_key', '商品对比键', '商品编码'],
  product_name: ['商品', '商品名称', '品名', '产品', 'product_name', 'price_identity_label'],
  quote_price: ['报价', '价格', '单价', 'quote_price', 'price'],
  quote_unit: ['单位', 'quote_unit', '报价单位'],
  box_price: ['箱价', '件价', 'box_price'],
  tax_price: ['含税价', '税后价', 'tax_price'],
  inventory_status: ['库存状态', '库存', '供货状态', 'inventory_status'],
  remarks: ['备注', '说明', 'remarks', 'note'],
  quoted_at: ['报价时间', '报价日期', 'quoted_at', '日期', '时间'],
  channel: ['渠道', 'channel'],
  market_category: ['分类', '品类', 'market_category'],
  market_scope: ['市场范围', 'market_scope'],
}
const QUOTE_IMPORT_HEADER_LOOKUP = new Map<string, QuoteImportHeaderKey>(
  Object.entries(QUOTE_IMPORT_HEADER_ALIASES).flatMap(([field, aliases]) =>
    aliases.map((alias) => [normalizeImportHeader(alias), field as QuoteImportHeaderKey] as const),
  ),
)

const loading = ref(false)
const supplierSaving = ref(false)
const quoteSaving = ref(false)
const quoteImporting = ref(false)
const quoteImportPreviewVisible = ref(false)
const quoteImportPreviewFileName = ref('')
const quoteImportMode = ref<SupplierQuoteImportMode>('append')
const quoteImportPreviewFilter = ref<QuoteImportPreviewFilter>('all')
const quoteImportDuplicateMatchFields = ref<SupplierQuoteDuplicateField[]>([])
const quoteImportAbnormalThresholdPercent = ref<number | null>(20)
const quoteActionLoadingId = ref<number | null>(null)
const quoteActionDetailVisible = ref(false)
const settlementDetailVisible = ref(false)
const settlementLoading = ref(false)
const settlementSaving = ref<'create' | 'build' | number | null>(null)
const settlementFormVisible = ref(false)
const keyword = ref('')
const categoryFilter = ref('')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')
const quoteStatusFilter = ref<'all' | 'active' | 'invalidated'>('all')
const quoteActionTypeFilter = ref<QuoteActionTypeFilter>('all')
const quoteActionOperatorFilter = ref('')
const quoteActionKeywordFilter = ref('')
const quoteActionDateRange = ref<string[]>([])
const settlementStatusFilter = ref<'all' | SupplierSettlementStatus>('all')
const settlementKeyword = ref('')
const settlementDateRange = ref<string[]>([])
const quoteKeyword = ref('')
const quoteDateRange = ref<string[]>([])
const quoteCurrentProductOnly = ref(false)
const quoteHistorySort = ref<'latest' | 'price_desc' | 'price_asc' | 'status'>('latest')
const selectedQuoteIds = ref<number[]>([])
const batchActionLoading = ref<'copy' | 'invalidate' | null>(null)
const operatorName = ref('')
const quoteImportInputRef = ref<HTMLInputElement | null>(null)
const quoteImportPreviewRows = ref<QuoteImportPreviewRow[]>([])
const lastQuoteImportFailureRows = ref<QuoteImportPreviewRow[]>([])
const quotePageSize = ref(20)
const quotePageOffset = ref(0)
const quoteTotal = ref(0)
const quoteHasMore = ref(false)
const quoteActionPageSize = ref(12)
const quoteActionOffset = ref(0)
const quoteActionTotal = ref(0)
const quoteActionHasMore = ref(false)
const settlementPageSize = ref(8)
const settlementOffset = ref(0)
const settlementTotal = ref(0)
const settlementHasMore = ref(false)
const suppliers = ref<SupplierItem[]>([])
const overview = ref<SupplierOverviewResponse | null>(null)
const productCompare = ref<SupplierQuoteCompareResponse | null>(null)
const selectedSupplierId = ref<number | null>(null)
const selectedSupplierQuoteRows = ref<SupplierQuoteItem[]>([])
const quoteActionLogs = ref<SupplierQuoteActionItem[]>([])
const settlementRows = ref<SupplierSettlementItem[]>([])
const activeQuoteActionDetail = ref<SupplierQuoteActionItem | null>(null)
const activeSettlementDetail = ref<SupplierSettlementDetailResponse | null>(null)
const lastBatchOperationKind = ref<BatchOperationKind | null>(null)
const lastBatchOperationTitle = ref('')
const lastBatchOperationSummary = ref('')
const lastBatchOperationRows = ref<BatchOperationExportRow[]>([])
const currentQuoteDraft = ref<SupplierQuoteDraft | null>(null)
const mobileSupplierTask = ref<MobileSupplierTask>('suppliers')
const desktopSupplierInsightTab = ref<DesktopSupplierInsightTab>('overview')
const desktopSupplierWorkbenchTab = ref<DesktopSupplierWorkbenchTab>('supplier')
const recentSupplierIds = ref<number[]>(readRecentSupplierIds())
const supplierAccountOriginalUsername = ref('')
const quotePriceInputRef = ref<{ focus?: () => void } | null>(null)

const supplierForm = reactive({
  supplier_name: '',
  contact_name: '',
  contact_phone: '',
  market_scope: '本地市场',
  market_category: '',
  channel: '微信小程序',
  notes: '',
  is_active: true,
})

const supplierAccountForm = reactive({
  account_username: '',
  account_password: '',
  account_display_name: '',
  account_is_active: true,
})

const quoteForm = reactive({
  source_record_id: undefined as number | undefined,
  quote_price: undefined as number | undefined,
  quote_unit: '斤',
  box_price: undefined as number | undefined,
  tax_price: undefined as number | undefined,
  inventory_status: '现货',
  remarks: '',
})

const settlementForm = reactive({
  settlement_title: '',
  period_start: '',
  period_end: '',
  total_amount: undefined as number | undefined,
  paid_amount: 0,
  payment_due_date: '',
  payment_date: '',
  remarks: '',
})

const selectedSupplier = computed(() => suppliers.value.find((item) => item.id === selectedSupplierId.value) || null)
const isAdminSession = computed(() => props.authRole === 'admin')
const isSupplierSession = computed(() => props.authRole === 'supplier')
const isProcurementSession = computed(() => props.authRole === 'procurement')
const hasBackendAuthSession = computed(() => isAdminSession.value || isSupplierSession.value || isProcurementSession.value)
const canSwitchQuoteSupplier = computed(() => isAdminSession.value || isProcurementSession.value)
const resolvedBackendSection = computed(() => props.backendSection ?? null)
const isProcurementAdminMode = computed(() => Boolean(props.procurementMode) && isAdminSession.value)
const isProcurementSupplierManagement = computed(
  () => isProcurementAdminMode.value && !resolvedBackendSection.value,
)
const isSupplierWorkspace = computed(() => resolvedBackendSection.value === 'suppliers')
const isSettlementWorkspace = computed(() => resolvedBackendSection.value === 'settlement')
const isLogsWorkspace = computed(() => resolvedBackendSection.value === 'logs')
const isQuoteWorkspace = computed(() => resolvedBackendSection.value === 'quote')
const isEmbeddedBackendMode = computed(() => Boolean(resolvedBackendSection.value))
const shouldCollapseEmbeddedWorkspaceChrome = computed(
  () => isEmbeddedBackendMode.value && (isQuoteWorkspace.value || isSupplierWorkspace.value || isSettlementWorkspace.value || isLogsWorkspace.value),
)
const effectiveMobileSupplierTask = computed<MobileSupplierTask>(() => {
  if (props.mobileTask) return props.mobileTask
  if (resolvedBackendSection.value === 'quote') return 'quote'
  if (resolvedBackendSection.value === 'suppliers') return 'suppliers'
  if (resolvedBackendSection.value === 'settlement') return 'settlement'
  if (resolvedBackendSection.value === 'logs') return 'history'
  return mobileSupplierTask.value
})
const showSupplierListColumn = computed(() => {
  if (props.mobile) {
    return resolvedBackendSection.value !== 'quote' && resolvedBackendSection.value !== 'settlement' && resolvedBackendSection.value !== 'logs'
  }
  // In admin settlement/log workspaces, the supplier list is the only way to switch scope.
  // Keep it visible instead of collapsing the whole layout to an empty shell.
  if (isAdminSession.value && (resolvedBackendSection.value === 'settlement' || resolvedBackendSection.value === 'logs')) {
    return true
  }
  if (resolvedBackendSection.value === 'quote' || resolvedBackendSection.value === 'settlement' || resolvedBackendSection.value === 'logs') {
    return false
  }
  return true
})
const showWorkbenchColumn = computed(() => {
  if (props.mobile) {
    return isProcurementSupplierManagement.value ? showAnyMobileSupplierTask(['suppliers']) : showAnyMobileSupplierTask(['suppliers', 'quote'])
  }
  if (!isEmbeddedBackendMode.value) {
    return true
  }
  // Settlement and logs use the insight column as the primary content area, so the empty workbench column is collapsed.
  return resolvedBackendSection.value === 'suppliers' || resolvedBackendSection.value === 'quote'
})
const showInsightColumn = computed(() => {
  if (isProcurementAdminMode.value && (isSettlementWorkspace.value || isLogsWorkspace.value || !resolvedBackendSection.value)) {
    return resolvedBackendSection.value === 'settlement' || resolvedBackendSection.value === 'logs'
  }
  if (isSupplierWorkspace.value) {
    return false
  }
  if (props.mobile) {
    return showAnyMobileSupplierTask(['suppliers', 'history', 'settlement'])
  }
  return true
})
const shouldShowEmbeddedTabs = computed(() => props.showEmbeddedTabs !== false)
const showSupplierListSummary = computed(
  () => !isProcurementSupplierManagement.value && !isQuoteWorkspace.value && !isSupplierWorkspace.value && !isSettlementWorkspace.value && !isLogsWorkspace.value,
)
const showSupplierListWorkspaceToolbar = computed(() => isProcurementSupplierManagement.value || isSupplierWorkspace.value || isSettlementWorkspace.value || isLogsWorkspace.value)
const embeddedLayoutClass = computed(() => {
  if (isProcurementAdminMode.value && !isQuoteWorkspace.value) {
    if (resolvedBackendSection.value === 'settlement' || resolvedBackendSection.value === 'logs') {
      return 'layout-two-column'
    }
    return resolvedBackendSection.value === 'suppliers' ? 'layout-two-column' : 'layout-procurement-management'
  }
  if (resolvedBackendSection.value === 'settlement' || resolvedBackendSection.value === 'logs') {
    // Admin settlement/log pages keep the supplier scope list visible; use two columns so content does not stack below it.
    return isAdminSession.value ? 'layout-two-column' : 'layout-content-only'
  }
  if (resolvedBackendSection.value === 'quote') {
    return 'layout-quote-focus'
  }
  if (resolvedBackendSection.value === 'suppliers') {
    return 'layout-two-column'
  }
  return 'layout-default'
})
const currentSupplierScopeId = computed(() => props.authSupplierId ?? null)
const sessionDisplayName = computed(() => props.authDisplayName?.trim() || '未登录账号')
const sessionRoleLabel = computed(() => (isAdminSession.value ? '管理员权限' : '供应商账号'))
const sessionScopeLabel = computed(() => {
  if (isAdminSession.value) {
    return '当前范围：全局供应商与报价数据'
  }
  return selectedSupplier.value?.supplier_name
    ? `当前范围：${selectedSupplier.value.supplier_name}`
    : '当前范围：仅限已绑定供应商数据'
})
const panelHeaderTitle = computed(() => (
  isProcurementSupplierManagement.value ? '供应商管理' : '供应商与录价管理'
))
const panelHeaderHint = computed(() => {
  if (isProcurementSupplierManagement.value) {
    return '采购端只管理供应商、账号状态、报价记录、结算和日志；供应商自己维护报价。'
  }
  return isAdminSession.value
    ? '维护本地供应商资料，直接录入报价，前台按商品做公开价对比。'
    : '当前为供应商账号，仅可查看并维护自己的报价数据。'
})
const selectedProductKey = computed(() => props.selectedIdentityKey || '')
const selectedProductOption = computed(
  () => props.productOptions.find((item) => item.price_identity_key === selectedProductKey.value) || null,
)
const supplierAccountSummaryLabel = computed(() => {
  if (!selectedSupplier.value?.account_username) {
    return '未配置'
  }
  return `${formatSupplierAccountLabel(selectedSupplier.value)} · ${supplierAccountForm.account_is_active ? '账号已启用' : '账号已停用'}`
})
const supplierWorkspaceQuickStats = computed(() => [
  isLogsWorkspace.value
    ? {
        label: '筛选供应商',
        value: String(filteredSuppliers.value.length),
        detail: '先选供应商，再查操作留痕',
      }
    : isSettlementWorkspace.value
    ? {
        label: '筛选供应商',
        value: String(filteredSuppliers.value.length),
        detail: '先选供应商，再进入结算处理',
      }
    : {
        label: '启用供应商',
        value: String(activeSupplierCount.value),
        detail: '直接从列表进入档案维护',
      },
  isLogsWorkspace.value
    ? {
        label: '动作日志',
        value: String(quoteActionTotal.value || filteredQuoteActionLogs.value.length),
        detail: hasQuoteActionAdvancedFilters.value ? `${quoteActionFilterTags.value.length} 个高级筛选` : '当前无高级筛选',
      }
    : isSettlementWorkspace.value
    ? {
        label: '本页未付',
        value: formatPrice(settlementPagePendingAmount.value),
        detail: selectedSupplier.value ? `${selectedSupplier.value.supplier_name} 当前页待付金额` : '选中供应商后查看待付金额',
      }
    : {
        label: '已覆盖分类',
        value: String(categoryCount.value),
        detail: '分类与渠道在首列同步筛选',
      },
  isLogsWorkspace.value
    ? {
        label: '最近动作',
        value: filteredQuoteActionLogs.value[0] ? getQuoteActionLabel(filteredQuoteActionLogs.value[0]) : '等待新动作',
        detail: filteredQuoteActionLogs.value[0]?.operator_name || '选中供应商后查看最新留痕',
      }
    : isSettlementWorkspace.value
    ? {
        label: '结算单',
        value: String(settlementTotal.value || settlementRows.value.length),
        detail: selectedSupplier.value ? '当前供应商结算单数量' : '先选供应商后查看账期明细',
      }
    : {
        label: '最近录价',
        value: latestQuotedAtLabel.value,
        detail: recentQuoteRows.value[0]?.supplier_name || '等待新的报价动作',
      },
])
const supplierWorkbenchKicker = computed(() => {
  if (isProcurementSupplierManagement.value) return '采购端'
  if (isSupplierSession.value) return '我的报价'
  if (resolvedBackendSection.value === 'settlement') return '结算'
  if (resolvedBackendSection.value === 'logs') return '日志'
  if (resolvedBackendSection.value === 'quote') return '报价'
  return '档案'
})
const supplierWorkbenchTitle = computed(() => {
  if (isProcurementSupplierManagement.value) return '供应商管理台'
  if (isSupplierSession.value && resolvedBackendSection.value === 'settlement') return '我的结算'
  if (isSupplierSession.value) return '我的报价工作台'
  if (resolvedBackendSection.value === 'settlement') return '供应商结算台账'
  if (resolvedBackendSection.value === 'logs') return '最近操作日志'
  if (resolvedBackendSection.value === 'quote') return '报价工作台'
  return '供应商管理'
})
const selectedProductLabelResolved = computed(
  () => selectedProductOption.value?.price_identity_label || props.selectedProductLabel || selectedProductKey.value || '',
)
const supplierHistoryPanelTitle = computed(() => {
  if (isProcurementSupplierManagement.value) return '供应商概览'
  return isSupplierWorkspace.value ? '近期报价与动作' : '最近报价记录'
})
const recentQuoteRows = computed(() => overview.value?.recent_quotes ?? [])
const categoryOptions = computed(() => {
  const base = ['蔬菜类', '干调类', '水产类', '冻品类', '肉禽蛋类', '粮油米面类']
  const dynamic = suppliers.value.map((item) => String(item.market_category || '').trim()).filter(Boolean)
  return Array.from(new Set([...base, ...dynamic]))
})
const channelOptions = computed(() => {
  const base = ['微信小程序', 'Excel', '门店直报', '电话报价']
  const dynamic = suppliers.value.map((item) => String(item.channel || '').trim()).filter(Boolean)
  return Array.from(new Set([...base, ...dynamic]))
})
const filteredSuppliers = computed(() => {
  const search = keyword.value.trim().toLowerCase()
  return suppliers.value.filter((item) => {
    if (statusFilter.value === 'active' && !item.is_active) return false
    if (statusFilter.value === 'inactive' && item.is_active) return false
    if (categoryFilter.value && item.market_category !== categoryFilter.value) return false
    if (!search) return true
    return [
      item.supplier_name,
      item.contact_name,
      item.contact_phone,
      item.market_category,
      item.channel,
      item.account_display_name,
      item.account_username,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(search))
  })
})
const supplierListStats = computed(() => [
  {
    label: '筛选结果',
    value: `${filteredSuppliers.value.length} 家`,
    detail: keyword.value.trim() ? '结果会跟随搜索和分类筛选变化' : '当前列表按供应平台默认视图展示',
  },
  {
    label: '启用供应商',
    value: `${activeSupplierCount.value} 家`,
    detail: '可继续录价并进入结算流程',
  },
  {
    label: '最近录价',
    value: latestQuotedAtLabel.value,
    detail: recentQuoteRows.value[0]?.supplier_name || '最近一次平台录价时间',
  },
])
const filteredSelectedSupplierQuoteRows = computed(() => {
  return sortQuoteHistoryRows(selectedSupplierQuoteRows.value)
})
const filteredGlobalRecentQuoteRows = computed(() => {
  return sortQuoteHistoryRows(recentQuoteRows.value.filter((item) => {
    if (quoteStatusFilter.value !== 'all' && getNormalizedQuoteStatus(item) !== quoteStatusFilter.value) {
      return false
    }
    if (quoteCurrentProductOnly.value && selectedProductKey.value && item.price_identity_key !== selectedProductKey.value) {
      return false
    }
    const keyword = quoteKeyword.value.trim().toLowerCase()
    if (keyword) {
      const haystack = [
        item.product_name,
        item.price_identity_label,
        item.price_identity_key,
        item.supplier_name,
        item.market_category,
        item.category,
        item.remarks,
        item.invalidated_reason,
      ].map((value) => String(value || '').toLowerCase()).join(' ')
      if (!haystack.includes(keyword)) {
        return false
      }
    }
    if (quoteDateRange.value.length === 2) {
      const quotedDate = String(item.quoted_at || '').slice(0, 10)
      if (!quotedDate || quotedDate < quoteDateRange.value[0] || quotedDate > quoteDateRange.value[1]) {
        return false
      }
    }
    return true
  }))
})
const historyQuoteRows = computed(() => selectedSupplier.value ? filteredSelectedSupplierQuoteRows.value : filteredGlobalRecentQuoteRows.value)
const historyQuoteTotal = computed(() => selectedSupplier.value ? quoteTotal.value : historyQuoteRows.value.length)
const hasQuoteHistoryAdvancedFilters = computed(() => {
  return Boolean(
    quoteStatusFilter.value !== 'all'
      || quoteKeyword.value.trim()
      || quoteDateRange.value.length
      || quoteCurrentProductOnly.value,
  )
})
const quoteHistoryFilterTags = computed(() => {
  const tags: string[] = []
  if (quoteStatusFilter.value === 'active') {
    tags.push('状态：仅有效')
  } else if (quoteStatusFilter.value === 'invalidated') {
    tags.push('状态：仅作废')
  }
  if (quoteKeyword.value.trim()) {
    tags.push(`关键词：${quoteKeyword.value.trim()}`)
  }
  if (quoteDateRange.value.length === 2) {
    tags.push(`日期：${quoteDateRange.value[0]} 至 ${quoteDateRange.value[1]}`)
  }
  if (quoteCurrentProductOnly.value) {
    tags.push(`范围：当前商品 ${selectedProductLabelResolved.value || selectedProductKey.value || ''}`.trim())
  }
  if (quoteHistorySort.value === 'price_desc') {
    tags.push('排序：价格从高到低')
  } else if (quoteHistorySort.value === 'price_asc') {
    tags.push('排序：价格从低到高')
  } else if (quoteHistorySort.value === 'status') {
    tags.push('排序：状态优先')
  }
  return tags
})
const activeQuoteCount = computed(
  () => selectedSupplierQuoteRows.value.filter((item) => getNormalizedQuoteStatus(item) === 'active').length,
)
const invalidatedQuoteCount = computed(
  () => selectedSupplierQuoteRows.value.filter((item) => getNormalizedQuoteStatus(item) === 'invalidated').length,
)
const historyActiveQuoteCount = computed(
  () => historyQuoteRows.value.filter((item) => getNormalizedQuoteStatus(item) === 'active').length,
)
const historyInvalidatedQuoteCount = computed(
  () => historyQuoteRows.value.filter((item) => getNormalizedQuoteStatus(item) === 'invalidated').length,
)
const selectedQuoteRows = computed(() => {
  const selectedIdSet = new Set(selectedQuoteIds.value)
  return historyQuoteRows.value.filter((item) => {
    const recordId = getQuoteRecordId(item)
    return recordId != null && selectedIdSet.has(recordId)
  })
})
const selectedActiveQuoteRows = computed(
  () => selectedQuoteRows.value.filter((item) => (String(item.status || 'active').trim() || 'active') !== 'invalidated'),
)
const selectedQuoteTotalAmount = computed(
  () => selectedQuoteRows.value.reduce((sum, item) => sum + Number(item.quote_price || 0), 0),
)
const quoteHistorySelectionSummary = computed(() => {
  if (!selectedQuoteRows.value.length) {
    return '当前未选择记录'
  }
  return `已选 ${selectedQuoteRows.value.length} 条 · 合计 ${formatPrice(selectedQuoteTotalAmount.value)}`
})
const visibleQuoteRecordIds = computed(() =>
  historyQuoteRows.value
    .map((item) => getQuoteRecordId(item))
    .filter((item): item is number => item != null),
)
const visibleSelectedQuoteCount = computed(() => {
  const selectedIdSet = new Set(selectedQuoteIds.value)
  return visibleQuoteRecordIds.value.filter((item) => selectedIdSet.has(item)).length
})
const allVisibleQuotesSelected = computed(
  () => Boolean(visibleQuoteRecordIds.value.length) && visibleSelectedQuoteCount.value === visibleQuoteRecordIds.value.length,
)
const someVisibleQuotesSelected = computed(() => visibleSelectedQuoteCount.value > 0)
const quoteHistoryViewTabs = computed<Array<{ key: QuoteHistoryView; label: string; value: string; active: boolean }>>(() => [
  {
    key: 'all',
    label: '全部报价',
    value: `${historyQuoteTotal.value} 条`,
    active: quoteStatusFilter.value === 'all' && !quoteCurrentProductOnly.value,
  },
  {
    key: 'active',
    label: '有效',
    value: `${historyActiveQuoteCount.value} 条`,
    active: quoteStatusFilter.value === 'active' && !quoteCurrentProductOnly.value,
  },
  {
    key: 'invalidated',
    label: '作废',
    value: `${historyInvalidatedQuoteCount.value} 条`,
    active: quoteStatusFilter.value === 'invalidated' && !quoteCurrentProductOnly.value,
  },
  {
    key: 'current_product',
    label: '当前商品',
    value: selectedProductLabelResolved.value || '未选',
    active: quoteCurrentProductOnly.value,
  },
])
const quoteAssistCards = computed(() => [
  {
    label: '当前报价范围',
    value: selectedSupplier.value?.supplier_name || (isAdminSession.value ? '全局最近' : '未选供应商'),
    detail: selectedProductLabelResolved.value
      ? `围绕 ${selectedProductLabelResolved.value} 查看和补录报价`
      : (selectedSupplier.value ? '选择商品后会同步报价历史' : '未选供应商时先展示平台最近报价'),
  },
  {
    label: '本页状态',
    value: `${historyActiveQuoteCount.value} 有效 / ${historyInvalidatedQuoteCount.value} 作废`,
    detail: hasQuoteHistoryAdvancedFilters.value ? quoteHistoryFilterTags.value.join(' / ') : '当前使用默认历史视图',
  },
  {
    label: '下一步动作',
    value: selectedQuoteRows.value.length ? `${selectedQuoteRows.value.length} 条已选` : '继续补齐',
    detail: selectedQuoteRows.value.length
      ? '可导出已选记录，或生成结算单继续对账'
      : '可复制最新报价为新记录，或通过导入模板批量补录',
  },
])
const filteredQuoteActionLogs = computed(() => {
  return quoteActionLogs.value
})
const latestActiveQuoteRecordId = computed(() => {
  const latestActiveRow = selectedSupplierQuoteRows.value.find(
    (item) => (String(item.status || 'active').trim() || 'active') === 'active' && getQuoteRecordId(item) != null,
  )
  return latestActiveRow ? getQuoteRecordId(latestActiveRow) : null
})
const categorySummaryItems = computed<SupplierCategorySummaryItem[]>(() => overview.value?.category_items ?? [])
const productCompareSummary = computed(() => productCompare.value?.summary ?? null)
const selectedSupplierCurrentQuote = computed(
  () => productCompare.value?.items.find((item) => item.supplier_id === selectedSupplierId.value) ?? null,
)
const recentSupplierItems = computed(() => {
  const idSet = new Set(suppliers.value.map((item) => item.id))
  return recentSupplierIds.value
    .filter((id) => idSet.has(id))
    .map((id) => suppliers.value.find((item) => item.id === id) || null)
    .filter((item): item is SupplierItem => Boolean(item))
    .slice(0, 4)
})
const activeSupplierCount = computed(
  () => overview.value?.summary.active_supplier_count ?? suppliers.value.filter((item) => item.is_active).length,
)
const categoryCount = computed(
  () => overview.value?.summary.category_count ?? new Set(suppliers.value.map((item) => item.market_category).filter(Boolean)).size,
)
const latestQuotedAtLabel = computed(
  () => formatTime(overview.value?.summary.latest_quoted_at || selectedSupplier.value?.latest_quoted_at),
)
const totalQuoteCount = computed(
  () => overview.value?.summary.total_quote_count ?? suppliers.value.reduce((sum, item) => sum + Number(item.quote_count || 0), 0),
)
const supplierCommandMetrics = computed(() => [
  ...(isSupplierWorkspace.value
    ? [
        {
          label: '启用供应商',
          value: String(activeSupplierCount.value),
          detail: `${filteredSuppliers.value.length} 家匹配当前筛选`,
        },
        {
          label: '已覆盖分类',
          value: String(categoryCount.value),
          detail: '按主营分类和默认渠道维护',
        },
        {
          label: '最近录价',
          value: latestQuotedAtLabel.value,
          detail: '选中供应商后可继续录价',
        },
      ]
    : []),
  ...(isQuoteWorkspace.value
    ? [
        {
          label: '当前商品',
          value: selectedProductLabelResolved.value || selectedProductKey.value || '未选',
          detail: props.procurementSourceLabel || '选择商品后再录价',
        },
        {
          label: '有效报价',
          value: `${historyActiveQuoteCount.value} 条`,
          detail: selectedSupplier.value?.supplier_name || '当前供应商未选',
        },
        {
          label: '已选记录',
          value: `${selectedQuoteRows.value.length} 条`,
          detail: selectedQuoteRows.value.length ? '可导出或生成结算' : '可从历史中勾选',
        },
      ]
    : []),
  ...(isSettlementWorkspace.value
    ? [
        {
          label: '结算单',
          value: `${settlementTotal.value || settlementRows.value.length} 单`,
          detail: selectedSupplier.value?.supplier_name || '先选择供应商范围',
        },
        {
          label: '待付款',
          value: formatPrice(settlementPagePendingAmount.value),
          detail: `${settlementPagePendingCount.value} 单仍需处理`,
        },
        {
          label: '已付金额',
          value: formatPrice(settlementPagePaidAmount.value),
          detail: '当前页结算汇总',
        },
      ]
    : []),
  ...(isLogsWorkspace.value
    ? [
        {
          label: '动作日志',
          value: `${quoteActionTotal.value || filteredQuoteActionLogs.value.length} 条`,
          detail: selectedSupplier.value?.supplier_name || '全局供应商范围',
        },
        {
          label: '筛选状态',
          value: hasQuoteActionAdvancedFilters.value ? '已筛选' : '全部动作',
          detail: hasQuoteActionAdvancedFilters.value ? quoteActionFilterTags.value.join(' / ') : '导入、作废、结算留痕',
        },
        {
          label: '最近动作',
          value: filteredQuoteActionLogs.value[0] ? getQuoteActionLabel(filteredQuoteActionLogs.value[0]) : '暂无动作',
          detail: filteredQuoteActionLogs.value[0] ? formatTime(filteredQuoteActionLogs.value[0].created_at) : '完成操作后自动留痕',
        },
      ]
    : []),
])
const quoteSubmitDisabled = computed(
  () => !selectedSupplier.value || !selectedSupplier.value.is_active || !selectedProductKey.value,
)
const showProcurementCarryTask = computed(
  () => isQuoteWorkspace.value && (props.procurementSourceType === 'menu_plan' || props.procurementSourceType === 'price_alert' || Boolean(props.procurementSourceLabel)),
)
const procurementCarryTaskKicker = computed(() => {
  if (props.procurementSourceType === 'menu_plan') return '菜单采购待补价'
  if (props.procurementSourceType === 'price_alert') return '价格预警待复核'
  return '采购工作台带入'
})
const procurementCarryTaskTitle = computed(() => selectedProductLabelResolved.value || selectedProductKey.value || '待选择商品')
const procurementCarryTaskDescription = computed(() => {
  const sourceLabel = props.procurementSourceLabel ? `来源：${props.procurementSourceLabel}。` : ''
  if (props.procurementSourceType === 'menu_plan') return `${sourceLabel}请选择绑定供应商，补一条真实报价后采购计划就能复核。`
  if (props.procurementSourceType === 'price_alert') return `${sourceLabel}请复核当前供应商报价，避免预警只停留在公开行情。`
  return `${sourceLabel}当前商品已从采购工作台带入，可直接补录供应商报价。`
})
const hasQuoteDraftContent = computed(() => (
  quoteForm.quote_price != null
  || quoteForm.box_price != null
  || quoteForm.tax_price != null
  || quoteForm.remarks.trim().length > 0
  || quoteForm.quote_unit.trim() !== '斤'
  || quoteForm.inventory_status.trim() !== '现货'
))
const quoteDraftSaveDisabled = computed(() => !selectedSupplier.value || !selectedProductKey.value || !hasQuoteDraftContent.value)
const quoteReadinessItems = computed(() => [
  {
    label: '商品目录',
    ready: Boolean(selectedProductKey.value),
    detail: selectedProductLabelResolved.value || (props.productOptions.length ? '先在商品下拉里选择本次报价商品' : '当前还没有可选商品，请先同步目录'),
  },
  {
    label: '供应商管理',
    ready: Boolean(selectedSupplier.value),
    detail: selectedSupplier.value?.supplier_name || (isAdminSession.value ? '先创建供应商或切换到已有供应商' : '当前账号还未绑定供应商'),
  },
  {
    label: '账号状态',
    ready: Boolean(selectedSupplier.value?.is_active),
    detail: selectedSupplier.value
      ? (selectedSupplier.value.is_active ? '供应商启用中，可以提交报价' : '供应商已停用，需先启用后再报价')
      : '选中供应商后会自动检查是否可报价',
  },
])
const showQuoteReadinessCard = computed(() => isQuoteWorkspace.value && quoteReadinessItems.value.some((item) => !item.ready))
const showMobileQuoteReadinessGate = computed(
  () => props.mobile && isEmbeddedBackendMode.value && isQuoteWorkspace.value && showQuoteReadinessCard.value,
)
const shouldShowQuoteEntryFields = computed(() => !showMobileQuoteReadinessGate.value)
const quoteReadinessTitle = computed(() => {
  const pendingCount = quoteReadinessItems.value.filter((item) => !item.ready).length
  return pendingCount ? `${pendingCount} 项未就绪` : '可以提交报价'
})
const quoteReadinessDescription = computed(() => {
  if (!selectedProductKey.value && !selectedSupplier.value) {
    return '先完成商品目录和供应商管理，后面只需要填写价格、单位和备注。'
  }
  if (!selectedProductKey.value) {
    return '当前缺少报价商品，商品目录同步后即可选择。'
  }
  if (!selectedSupplier.value) {
    return '当前缺少供应商，创建后这张表单会直接沿用该供应商。'
  }
  return '当前供应商不可报价，请先检查启用状态。'
})
const resolvedOperatorName = computed(
  () => props.authDisplayName?.trim() || operatorName.value.trim() || selectedSupplier.value?.contact_name || '供应平台',
)
const quotePageLabel = computed(() => {
  if (!quoteTotal.value) return '第 0 页'
  return `第 ${Math.floor(quotePageOffset.value / quotePageSize.value) + 1} 页`
})
const quoteActionPageLabel = computed(() => {
  if (!quoteActionTotal.value) return '第 0 页'
  return `第 ${Math.floor(quoteActionOffset.value / quoteActionPageSize.value) + 1} 页`
})
const settlementPageLabel = computed(() => {
  if (!settlementTotal.value) return '第 0 页'
  return `第 ${Math.floor(settlementOffset.value / settlementPageSize.value) + 1} 页`
})
const settlementPageTotalAmount = computed(
  () => settlementRows.value.reduce((sum, item) => sum + Number(item.total_amount || 0), 0),
)
const settlementPagePaidAmount = computed(
  () => settlementRows.value.reduce((sum, item) => sum + Number(item.paid_amount || 0), 0),
)
const settlementPagePendingAmount = computed(
  () => settlementRows.value.reduce((sum, item) => sum + Number(item.pending_amount || 0), 0),
)
const settlementPagePendingCount = computed(
  () => settlementRows.value.filter((item) => String(item.status || 'pending').trim() === 'pending').length,
)
const settlementPagePartialCount = computed(
  () => settlementRows.value.filter((item) => String(item.status || 'pending').trim() === 'partial').length,
)
const settlementPagePaidCount = computed(
  () => settlementRows.value.filter((item) => String(item.status || 'pending').trim() === 'paid').length,
)
const focusedSettlementId = ref<number | null>(null)
const focusedSettlement = computed(
  () => settlementRows.value.find((item) => item.id === focusedSettlementId.value) || settlementRows.value[0] || null,
)
const nextPendingSettlement = computed(
  () => settlementRows.value.find((item) => ['pending', 'partial'].includes(String(item.status || '').trim())) || null,
)
const mySettlementKpis = computed(() => [
  {
    label: '待付款',
    value: String(settlementPagePendingCount.value),
    detail: '需要继续跟进',
    tone: 'warn',
  },
  {
    label: '未付金额',
    value: formatPrice(settlementPagePendingAmount.value),
    detail: selectedSupplier.value ? `${selectedSupplier.value.supplier_name} 当前页` : '当前页结算汇总',
    tone: 'danger',
  },
  {
    label: '已结清',
    value: String(settlementPagePaidCount.value),
    detail: '已完成付款',
    tone: 'green',
  },
  {
    label: '最近应付',
    value: formatTime(nextPendingSettlement.value?.payment_due_date),
    detail: nextPendingSettlement.value?.settlement_title || '当前没有待付款单',
    tone: 'blue',
  },
])
const supplierWorkbenchBadges = computed(() => {
  if (isProcurementSupplierManagement.value) {
    return [
      `${filteredSuppliers.value.length} 家供应商`,
      `${activeSupplierCount.value} 家启用`,
      `${historyQuoteTotal.value} 条报价记录`,
      selectedSupplier.value?.supplier_name || '未选供应商',
    ]
  }
  if (resolvedBackendSection.value === 'settlement') {
    return [
      `${settlementTotal.value} 张结算单`,
      `${settlementPagePendingCount.value} 张待付款`,
      `未付 ${formatPrice(settlementPagePendingAmount.value)}`,
      selectedSupplier.value?.supplier_name || '未选供应商',
    ]
  }
  if (resolvedBackendSection.value === 'logs') {
    return [
      `${quoteActionTotal.value} 条动作日志`,
      hasQuoteActionAdvancedFilters.value ? `${quoteActionFilterTags.value.length} 个高级筛选` : '当前无高级筛选',
      lastBatchOperationRows.value.length ? `${lastBatchOperationRows.value.length} 条最近批次结果` : '暂无批量结果',
      selectedSupplier.value?.supplier_name || '未选供应商',
    ]
  }
  if (resolvedBackendSection.value === 'quote') {
    return [
      selectedProductLabelResolved.value || '未选商品',
      `${activeQuoteCount.value} 条有效报价`,
      `${selectedQuoteRows.value.length} 条已选记录`,
      selectedSupplier.value?.supplier_name || '未选供应商',
    ]
  }
  return [
    `${filteredSuppliers.value.length} 家筛选结果`,
    `${activeSupplierCount.value} 家启用供应商`,
    `${categoryCount.value} 个主营分类`,
    `${totalQuoteCount.value} 条累计报价`,
  ]
})
const workbenchPrimaryActionLabel = computed(() => {
  if (resolvedBackendSection.value === 'quote') {
    return isAdminSession.value ? '批量导入报价' : '批量导入我的报价'
  }
  if (resolvedBackendSection.value === 'settlement') {
    return isAdminSession.value ? '新建结算单' : ''
  }
  if (resolvedBackendSection.value === 'logs') {
    return ''
  }
  return isAdminSession.value ? '新建供应商' : ''
})
const showWorkbenchPrimaryAction = computed(() => Boolean(workbenchPrimaryActionLabel.value))
const selectedSupplierComparisonLabel = computed(() => {
  if (selectedSupplier.value && !selectedSupplier.value.is_active) {
    return '供应商已停用，当前不可继续录价'
  }
  return selectedSupplierCurrentQuote.value?.comparison_label || '录价后会自动和公开最低价做对比'
})
const mobileSupplierTaskTabs = computed(() => [
  ...(isAdminSession.value ? [{
    key: 'suppliers' as MobileSupplierTask,
    label: '档案',
    detail: `${filteredSuppliers.value.length} 家供应商`,
  }] : []),
  ...(isProcurementSupplierManagement.value
    ? []
    : [
        {
          key: 'quote' as MobileSupplierTask,
          label: '录价',
          detail: selectedProductLabelResolved.value || '选择商品',
        },
        {
          key: 'history' as MobileSupplierTask,
          label: '历史',
          detail: `${historyQuoteTotal.value} 条报价`,
        },
        {
          key: 'settlement' as MobileSupplierTask,
          label: '结算',
          detail: `${settlementTotal.value || settlementRows.value.length} 单`,
        },
      ]),
])
const desktopSupplierInsightTabs = computed(() => {
  const items: Array<{ key: DesktopSupplierInsightTab; label: string; detail: string }> = [
    { key: 'overview', label: '概览', detail: `${categorySummaryItems.value.length} 类 / ${recentQuoteRows.value.length} 条速览` },
    { key: 'history', label: '历史', detail: `${historyQuoteTotal.value} 条报价` },
    { key: 'settlement', label: '结算', detail: `${settlementTotal.value || settlementRows.value.length} 单账期` },
  ]
  if (isAdminSession.value) {
    items.push({ key: 'logs', label: '日志', detail: `${quoteActionTotal.value || filteredQuoteActionLogs.value.length} 条动作` })
  }
  return items
})
const desktopSupplierWorkbenchTabs = computed(() => [
  {
    key: 'supplier' as DesktopSupplierWorkbenchTab,
    label: '档案',
    detail: selectedSupplier.value ? `编辑 ${selectedSupplier.value.supplier_name}` : '维护供应商资料与账号',
  },
  ...(isProcurementSupplierManagement.value
    ? []
    : [{
        key: 'quote' as DesktopSupplierWorkbenchTab,
        label: '录价',
        detail: selectedProductLabelResolved.value || '按当前商品录报价',
      }]),
])
const mobileSupplierTaskTitle = computed(() => {
  const activeTask = mobileSupplierTaskTabs.value.find((item) => item.key === mobileSupplierTask.value)
  return activeTask?.label || (isSupplierSession.value ? '录价' : '档案')
})
const showSupplierBindingEmptyState = computed(() => isSupplierSession.value && !selectedSupplier.value)
const supplierBindingEmptyTitle = computed(() => (
  currentSupplierScopeId.value ? '绑定的供应商暂未同步到供应平台列表' : '当前账号还没有绑定供应商'
))
const supplierBindingEmptyDescription = computed(() => (
  currentSupplierScopeId.value
    ? '请联系管理员确认该供应商仍处于启用状态，并同步到当前列表；同步完成后你就能继续录价。'
    : '请联系管理员先把当前账号绑定到对应供应商，绑定完成后重新登录即可继续录价。'
))
const supplierQuoteEmptyDescription = computed(() => (
  isProcurementSupplierManagement.value
    ? '等待供应商账号提交第一条报价；一旦有数据，这里会按供应商和商品自动沉淀。'
    : '先在中间表单里选择商品并录入报价，录完后这里会自动出现历史记录。'
))
const supplierListEmptyDescription = computed(() => (
  isProcurementSupplierManagement.value
    ? '先新建供应商并分配账号，供应端提交报价后这里会汇总覆盖情况和待办。'
    : (props.mobile ? '先新建供应商，或进入供应平台完成创建后再回来录价。' : '先在右侧新建一个供应商，创建完成后再开始录价。')
))
const categoryEmptyDescription = computed(() => (
  isProcurementSupplierManagement.value
    ? '供应商提交报价后，这里会按主营分类汇总覆盖供应商和报价数量。'
    : '先创建供应商并录入报价，这里会自动汇总干调类、蔬菜类等分类。'
))
const recentQuoteEmptyDescription = computed(() => (
  isProcurementSupplierManagement.value
    ? '供应商提交报价后，这里会按时间倒序展示，便于采购复核。'
    : '录价后这里会按时间倒序展示，便于快速回看最近更新。'
))
const mobileSupplierTaskDescription = computed(() => {
  if (showSupplierBindingEmptyState.value) {
    return currentSupplierScopeId.value
      ? '当前账号已带有供应商标识，但该供应商暂未在供应平台列表中加载出来。'
      : '当前账号还没有绑定供应商，因此暂时无法录价和查看历史。'
  }
  if (mobileSupplierTask.value === 'suppliers') {
    if (isProcurementSupplierManagement.value) {
      return selectedSupplier.value ? '维护供应商资料、账号、报价记录和结算关系。' : '先选一个供应商，后面报价记录和结算都会跟着走。'
    }
    return selectedSupplier.value ? '维护供应商资料，切回录价会沿用当前选中供应商。' : '先选一个供应商，后面录价和结算都会跟着走。'
  }
  if (mobileSupplierTask.value === 'quote') {
    return selectedSupplier.value ? '直接给当前商品录价，系统会同步显示和公开低价的差异。' : '先回到档案页选择供应商，再进入录价。'
  }
  if (mobileSupplierTask.value === 'history') {
    return isAdminSession.value ? '集中处理复制新报价、作废、批量导出和操作日志。' : '回看自己的历史报价，快速复制为新报价。'
  }
  return isAdminSession.value ? '对账、付款、作废结算单都放在这一页，便于月底集中处理。' : '查看自己的结算结果和金额进度。'
})
const mobilePrimaryAction = computed<MobilePrimaryAction>(() => {
  if (mobileSupplierTask.value === 'suppliers') {
    return selectedSupplier.value ? 'open_quote' : 'create_supplier'
  }
  if (mobileSupplierTask.value === 'quote') {
    return selectedSupplier.value ? 'save_quote' : 'open_suppliers'
  }
  if (mobileSupplierTask.value === 'history') {
    return selectedSupplier.value ? 'open_quote' : 'open_suppliers'
  }
  if (!selectedSupplier.value) {
    return 'open_suppliers'
  }
  if (isSupplierSession.value) {
    return 'open_quote'
  }
  if (selectedActiveQuoteRows.value.length) {
    return 'build_settlement'
  }
  return 'open_settlement_create'
})
const mobilePrimaryActionLabel = computed(() => {
  if (mobilePrimaryAction.value === 'create_supplier') return '新建供应商'
  if (mobilePrimaryAction.value === 'save_quote') return '提交当前报价'
  if (mobilePrimaryAction.value === 'open_quote') return '去录新报价'
  if (mobilePrimaryAction.value === 'open_settlement_create') return '新建结算单'
  if (mobilePrimaryAction.value === 'build_settlement') return '已选报价生成结算单'
  return '去选供应商'
})
const mobilePrimaryActionDisabled = computed(() => {
  if (mobilePrimaryAction.value === 'save_quote') {
    return quoteSubmitDisabled.value || quoteSaving.value
  }
  if (mobilePrimaryAction.value === 'build_settlement') {
    return !selectedActiveQuoteRows.value.length || settlementSaving.value === 'build'
  }
  return false
})
const mobileSecondaryActionLabel = computed(() => {
  if (mobileSupplierTask.value === 'suppliers') return '查看历史'
  if (mobileSupplierTask.value === 'quote') return selectedSupplier.value ? '查看历史' : '新建供应商'
  if (mobileSupplierTask.value === 'history') return '查看结算'
  return '回到档案'
})
const mobileSecondaryActionDisabled = computed(() => {
  return false
})
const readyQuoteImportPreviewCount = computed(
  () => quoteImportPreviewRows.value.filter((item) => item.status === 'ready').length,
)
const invalidQuoteImportPreviewCount = computed(
  () => quoteImportPreviewRows.value.filter((item) => item.status === 'error').length,
)
const appendQuoteImportPreviewCount = computed(
  () => quoteImportPreviewRows.value.filter((item) => item.status === 'ready' && item.preview_status === 'append').length,
)
const skipQuoteImportPreviewCount = computed(
  () => quoteImportPreviewRows.value.filter((item) => item.status === 'ready' && item.preview_status === 'skip_duplicate').length,
)
const overrideQuoteImportPreviewCount = computed(
  () => quoteImportPreviewRows.value.filter((item) => item.status === 'ready' && item.preview_status === 'override_latest').length,
)
const abnormalQuoteImportPreviewCount = computed(
  () => quoteImportPreviewRows.value.filter((item) => item.status === 'ready' && item.abnormal_change_ratio != null).length,
)
const quoteImportDuplicateFieldSummary = computed(() => {
  if (!quoteImportDuplicateMatchFields.value.length) {
    return '未选择时将回退到系统默认判重规则。'
  }
  return `当前按 ${quoteImportDuplicateMatchFields.value.length} 个字段联合判重。`
})
const filteredQuoteImportPreviewRows = computed(() => {
  return quoteImportPreviewRows.value.filter((item) => {
    if (quoteImportPreviewFilter.value === 'all') return true
    if (quoteImportPreviewFilter.value === 'invalid') return item.status === 'error'
    if (quoteImportPreviewFilter.value === 'abnormal') {
      return item.status === 'ready' && item.abnormal_change_ratio != null
    }
    return item.status === 'ready' && item.preview_status === quoteImportPreviewFilter.value
  })
})
const hasQuoteActionAdvancedFilters = computed(() => {
  return Boolean(
    quoteActionTypeFilter.value !== 'all'
      || quoteActionOperatorFilter.value.trim()
      || quoteActionKeywordFilter.value.trim()
      || quoteActionDateRange.value.length,
  )
})
const quoteActionFilterTags = computed(() => {
  const tags: string[] = []
  if (quoteActionTypeFilter.value !== 'all') {
    tags.push(`动作：${quoteActionTypeFilter.value}`)
  }
  if (quoteActionOperatorFilter.value.trim()) {
    tags.push(`操作人：${quoteActionOperatorFilter.value.trim()}`)
  }
  if (quoteActionKeywordFilter.value.trim()) {
    tags.push(`关键词：${quoteActionKeywordFilter.value.trim()}`)
  }
  if (quoteActionDateRange.value.length === 2) {
    tags.push(`日期：${quoteActionDateRange.value[0]} 至 ${quoteActionDateRange.value[1]}`)
  }
  return tags
})
const quoteImportRuleTags = computed(() => {
  const tags: string[] = []
  if (quoteImportDuplicateMatchFields.value.length) {
    const labels = QUOTE_IMPORT_DUPLICATE_FIELD_OPTIONS
      .filter((item) => quoteImportDuplicateMatchFields.value.includes(item.value))
      .map((item) => item.label)
    tags.push(`判重字段：${labels.join(' / ')}`)
  } else {
    tags.push('判重字段：系统默认')
  }
  if (quoteImportAbnormalThresholdPercent.value != null) {
    tags.push(`异常阈值：${Number(quoteImportAbnormalThresholdPercent.value)}%`)
  } else {
    tags.push('异常阈值：关闭')
  }
  return tags
})
const lastBatchOperationPreviewRows = computed(() => lastBatchOperationRows.value.slice(0, 6))
const activeQuoteActionDetailEntries = computed<QuoteActionDetailEntry[]>(() => {
  return activeQuoteActionDetail.value ? getQuoteActionDetailEntries(activeQuoteActionDetail.value) : []
})
const activeQuoteActionFailureExamples = computed(() => {
  return activeQuoteActionDetail.value ? getImportQuoteActionFailedExamples(activeQuoteActionDetail.value) : []
})
const activeQuoteActionSuccessRecordIds = computed(() => {
  return activeQuoteActionDetail.value ? getQuoteActionSuccessRecordIdList(activeQuoteActionDetail.value) : []
})
const activeQuoteActionRows = computed(() => {
  return activeQuoteActionDetail.value ? getQuoteActionPayloadRows(activeQuoteActionDetail.value) : []
})
const activeQuoteActionDetailTags = computed(() => {
  return activeQuoteActionDetail.value ? getQuoteActionPayloadTags(activeQuoteActionDetail.value) : []
})

function getQuoteImportModeLabel(mode?: SupplierQuoteImportMode | string | null) {
  const matched = QUOTE_IMPORT_MODE_OPTIONS.find((item) => item.value === mode)
  return matched?.label || '追加导入'
}

function getQuoteImportModeDescription(mode?: SupplierQuoteImportMode | string | null) {
  const matched = QUOTE_IMPORT_MODE_OPTIONS.find((item) => item.value === mode)
  return matched?.description || QUOTE_IMPORT_MODE_OPTIONS[0].description
}

function formatPercent(value?: number | null) {
  return value == null || Number.isNaN(Number(value)) ? '—' : `${(Number(value) * 100).toFixed(2)}%`
}

function buildQuoteImportRulePayload() {
  return {
    duplicate_match_fields: quoteImportDuplicateMatchFields.value.length
      ? [...quoteImportDuplicateMatchFields.value]
      : undefined,
    abnormal_change_ratio_threshold: quoteImportAbnormalThresholdPercent.value == null
      ? undefined
      : Number(quoteImportAbnormalThresholdPercent.value) / 100,
  }
}

function getQuoteImportPreviewDecisionLabel(row: QuoteImportPreviewRow) {
  if (row.status !== 'ready') {
    return '待修正'
  }
  if (row.abnormal_change_ratio != null) {
    return '波动异常'
  }
  if (row.preview_status === 'skip_duplicate') {
    return '将跳过'
  }
  if (row.preview_status === 'override_latest') {
    return '将覆盖'
  }
  return '将新增'
}

function getQuoteImportPreviewDecisionReason(row: QuoteImportPreviewRow) {
  if (row.status !== 'ready') {
    return row.reason || '需先修正后再导入'
  }
  const parts = [row.preview_reason || '将作为新报价写入']
  if (row.abnormal_change_hint) {
    parts.push(row.abnormal_change_hint)
  }
  if (row.existing_quote_price != null) {
    parts.push(`当前有效价 ${row.existing_quote_price}${row.existing_quote_unit || ''}`)
  }
  if (row.existing_quoted_at) {
    parts.push(`录于 ${formatTime(row.existing_quoted_at)}`)
  }
  return parts.filter(Boolean).join('，')
}

function getQuoteImportPreviewDecisionClass(row: QuoteImportPreviewRow) {
  if (row.status !== 'ready') {
    return 'is-invalid'
  }
  if (row.abnormal_change_ratio != null) {
    return 'is-abnormal'
  }
  if (row.preview_status === 'skip_duplicate') {
    return 'is-skip'
  }
  if (row.preview_status === 'override_latest') {
    return 'is-override'
  }
  return 'is-append'
}

function getQuoteImportPreviewExistingLabel(row: QuoteImportPreviewRow) {
  if (row.existing_quote_price == null) {
    return '暂无有效报价'
  }
  return `${row.existing_quote_price}${row.existing_quote_unit || ''}`
}

function getQuoteImportPreviewExistingMeta(row: QuoteImportPreviewRow) {
  const parts = []
  if (row.existing_record_id != null) {
    parts.push(`记录 #${row.existing_record_id}`)
  }
  if (row.existing_quoted_at) {
    parts.push(`录于 ${formatTime(row.existing_quoted_at)}`)
  }
  if (row.existing_remarks) {
    parts.push(row.existing_remarks)
  }
  if (!parts.length && row.existing_quote_price == null) {
    parts.push('导入后将成为首条有效报价')
  }
  return parts.join('，')
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function tryParseJson(value: string) {
  try {
    return JSON.parse(value) as unknown
  } catch {
    return null
  }
}

function formatPrice(value?: number | null) {
  return value == null || Number.isNaN(Number(value)) ? '-' : `${Number(value).toFixed(2)} 元`
}

function formatTime(value?: string | null) {
  const text = String(value || '').trim()
  if (!text) return '暂无'
  const matched = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2}))?/)
  if (!matched) return text
  const [, , month, day, hour, minute] = matched
  return hour && minute ? `${month}-${day} ${hour}:${minute}` : `${month}-${day}`
}

function formatSupplierAccountLabel(item?: SupplierItem | null) {
  if (!item?.account_username) {
    return '未配置账号'
  }
  const displayName = String(item.account_display_name || '').trim()
  if (isSeedAccountUsername(item.account_username) && /演示|demo|test/i.test(displayName)) {
    return '账号已配置'
  }
  return displayName || '账号已配置'
}

function isSeedAccountUsername(value?: string | null) {
  return /^demo[-_]/i.test(String(value || '').trim())
}

function getSupplierAccountFormUsername(item?: SupplierItem | null) {
  const username = String(item?.account_username || '').trim()
  if (!username) return ''
  return isSeedAccountUsername(username) ? formatSupplierAccountLabel(item) : username
}

function normalizeSupplierAccountUsernameForSave() {
  const current = supplierAccountForm.account_username.trim()
  const original = supplierAccountOriginalUsername.value.trim()
  if (!original) return current || undefined
  if (current === original || (isSeedAccountUsername(original) && current === getSupplierAccountFormUsername(selectedSupplier.value))) {
    return original
  }
  return current || undefined
}

function validateSupplierAccountFormBeforeSave() {
  const username = normalizeSupplierAccountUsernameForSave() || ''
  const password = supplierAccountForm.account_password.trim()
  const hasExistingAccount = Boolean(selectedSupplier.value?.account_username)
  if (!username && password) {
    ElMessage.warning('请先填写登录账号，再设置账号密码')
    return false
  }
  if (username && !ACCOUNT_USERNAME_PATTERN.test(username)) {
    ElMessage.warning('登录账号需为 3-64 位，只能包含字母、数字、下划线、中划线、点或 @')
    return false
  }
  if (username && !hasExistingAccount && !password) {
    ElMessage.warning('新建供应商账号必须填写初始密码')
    return false
  }
  if (password && password.length < MIN_ACCOUNT_PASSWORD_LENGTH) {
    ElMessage.warning(`账号密码至少 ${MIN_ACCOUNT_PASSWORD_LENGTH} 位`)
    return false
  }
  return true
}

function toDateTimestamp(value?: string | null, boundary: 'start' | 'end' | 'exact' = 'exact') {
  const text = String(value || '').trim()
  if (!text) return null
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
    const suffix = boundary === 'start' ? 'T00:00:00' : boundary === 'end' ? 'T23:59:59' : 'T00:00:00'
    const parsed = new Date(`${text}${suffix}`)
    return Number.isNaN(parsed.getTime()) ? null : parsed.getTime()
  }
  const parsed = new Date(text)
  return Number.isNaN(parsed.getTime()) ? null : parsed.getTime()
}

function formatDateOnly(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function slugifyExportValue(value?: string | null) {
  const normalized = String(value || '').trim()
  return normalized ? normalized.replace(/[\\/:*?"<>|]+/g, '-').replace(/\s+/g, '-') : 'supplier-quotes'
}

function normalizeImportHeader(value?: string | null) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[\s_-]+/g, '')
    .replace(/[()（）【】\[\]:：]/g, '')
}

function normalizeComparableText(value?: string | null) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '')
}

function getFileExtension(filename: string) {
  const parts = filename.toLowerCase().split('.')
  return parts.length > 1 ? parts.pop() || '' : ''
}

function decodeTextBuffer(buffer: ArrayBuffer) {
  for (const encoding of TEXT_ENCODINGS) {
    try {
      return new TextDecoder(encoding).decode(buffer)
    } catch {
      // Fall through to the next encoding.
    }
  }
  return new TextDecoder().decode(buffer)
}

function parseCsvLine(line: string) {
  const cells: string[] = []
  let current = ''
  let inQuotes = false

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index]
    const nextChar = line[index + 1]

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        current += '"'
        index += 1
      } else {
        inQuotes = !inQuotes
      }
      continue
    }

    if (char === ',' && !inQuotes) {
      cells.push(current)
      current = ''
      continue
    }

    current += char
  }

  cells.push(current)
  return cells.map((item) => item.replace(/^\ufeff/, '').trim())
}

function extractProductBaseName(label?: string | null) {
  const text = String(label || '').trim()
  if (!text) return ''
  const withoutParen = text.replace(/（.*?）|\(.*?\)/g, ' ')
  const firstSegment = withoutParen.split(/[|｜/]/)[0] || withoutParen
  return firstSegment.replace(/\s+/g, ' ').trim()
}

function normalizeOptionalText(value?: string | null) {
  const text = String(value || '').replace(/\u0000/g, '').trim()
  return text || undefined
}

function parseImportedNumber(value?: string | null) {
  const normalized = String(value || '')
    .trim()
    .replace(/[,，]/g, '')
  if (!normalized) return undefined
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : undefined
}

function normalizeImportedQuotedAt(value?: string | null) {
  const text = String(value || '').trim()
  if (!text) return undefined
  return toDateTimestamp(text) == null ? undefined : text
}

/**
 * Parse spreadsheet-like input into canonical quote import drafts.
 *
 * Args:
 *   rows: Raw tabular rows from xlsx/csv parsing.
 *
 * Returns:
 *   A normalized list of import drafts keyed by the supported template fields.
 */
function parseQuoteImportRows(rows: unknown[][]) {
  const normalizedRows = rows
    .filter((row) => Array.isArray(row))
    .map((row) => row.map((cell) => String(cell ?? '').replace(/\u0000/g, '').trim()))
    .filter((row) => row.some(Boolean))

  if (!normalizedRows.length) {
    return [] as ImportedSupplierQuoteDraft[]
  }

  const firstRow = normalizedRows[0]
  const mappedHeaders = firstRow.map((cell) => QUOTE_IMPORT_HEADER_LOOKUP.get(normalizeImportHeader(cell)) || null)
  const recognizedHeaderCount = mappedHeaders.filter(Boolean).length
  const fieldOrder = recognizedHeaderCount > 0
    ? mappedHeaders
    : firstRow.map((_, index) => QUOTE_IMPORT_DEFAULT_HEADERS[index] || null)
  const dataRows = recognizedHeaderCount > 0 ? normalizedRows.slice(1) : normalizedRows
  const baseRowNumber = recognizedHeaderCount > 0 ? 2 : 1

  return dataRows
    .map((row, rowIndex) => {
      const draft: ImportedSupplierQuoteDraft = {
        row_number: rowIndex + baseRowNumber,
      }

      fieldOrder.forEach((field, columnIndex) => {
        if (!field) return
        const value = normalizeOptionalText(row[columnIndex])
        if (value != null) {
          draft[field] = value
        }
      })

      return draft
    })
    .filter((draft) => {
      return Boolean(
        draft.price_identity_key ||
        draft.product_name ||
        draft.quote_price ||
        draft.quote_unit ||
        draft.remarks,
      )
    })
}

async function parseQuoteCsvFile(file: File) {
  const buffer = await file.arrayBuffer()
  const content = decodeTextBuffer(buffer)
  return content
    .split(/\r?\n/)
    .filter((line) => line.trim())
    .map((line) => parseCsvLine(line))
}

async function parseQuoteSpreadsheetFile(file: File) {
  const xlsx = await import('xlsx')
  const buffer = await file.arrayBuffer()
  const workbook = xlsx.read(buffer, { type: 'array' })
  const firstSheetName = workbook.SheetNames[0]
  if (!firstSheetName) {
    return [] as unknown[][]
  }
  const firstSheet = workbook.Sheets[firstSheetName]
  return xlsx.utils.sheet_to_json(firstSheet, {
    header: 1,
    raw: false,
    defval: '',
  }) as unknown[][]
}

async function parseQuoteImportFile(file: File) {
  const extension = getFileExtension(file.name)
  if (extension === 'csv') {
    return parseQuoteCsvFile(file)
  }
  if (extension === 'xlsx' || extension === 'xls') {
    return parseQuoteSpreadsheetFile(file)
  }
  throw new Error('暂不支持该导入格式')
}

function matchImportedProduct(draft: ImportedSupplierQuoteDraft) {
  const keyCandidate = normalizeComparableText(draft.price_identity_key)
  if (keyCandidate) {
    const exactKey = props.productOptions.find(
      (item) => normalizeComparableText(item.price_identity_key) === keyCandidate,
    )
    if (exactKey) {
      return {
        price_identity_key: exactKey.price_identity_key,
        price_identity_label: exactKey.price_identity_label,
        product_name: extractProductBaseName(exactKey.price_identity_label) || exactKey.price_identity_label,
      } as MatchedImportedProduct
    }
  }

  const nameCandidate = normalizeComparableText(draft.product_name)
  if (!nameCandidate) {
    return null
  }

  const exactLabel = props.productOptions.find(
    (item) => normalizeComparableText(item.price_identity_label) === nameCandidate,
  )
  if (exactLabel) {
    return {
      price_identity_key: exactLabel.price_identity_key,
      price_identity_label: exactLabel.price_identity_label,
      product_name: extractProductBaseName(exactLabel.price_identity_label) || exactLabel.price_identity_label,
    } as MatchedImportedProduct
  }

  const baseNameCandidate = normalizeComparableText(extractProductBaseName(draft.product_name))
  const fuzzyMatches = props.productOptions.filter(
    (item) => normalizeComparableText(extractProductBaseName(item.price_identity_label)) === baseNameCandidate,
  )
  if (fuzzyMatches.length === 1) {
    const onlyMatch = fuzzyMatches[0]
    return {
      price_identity_key: onlyMatch.price_identity_key,
      price_identity_label: onlyMatch.price_identity_label,
      product_name: extractProductBaseName(onlyMatch.price_identity_label) || onlyMatch.price_identity_label,
    } as MatchedImportedProduct
  }

  return null
}

function getQuoteStatusLabel(item: SupplierQuoteItem) {
  return item.status === 'invalidated' ? '已作废' : '有效报价'
}

function getNormalizedQuoteStatus(item: SupplierQuoteItem) {
  return String(item.status || 'active').trim() || 'active'
}

function sortQuoteHistoryRows(rows: SupplierQuoteItem[]) {
  const nextRows = [...rows]
  if (quoteHistorySort.value === 'price_desc') {
    return nextRows.sort((left, right) => Number(right.quote_price || 0) - Number(left.quote_price || 0))
  }
  if (quoteHistorySort.value === 'price_asc') {
    return nextRows.sort((left, right) => Number(left.quote_price || 0) - Number(right.quote_price || 0))
  }
  if (quoteHistorySort.value === 'status') {
    const statusRank = (item: SupplierQuoteItem) => {
      const normalized = getNormalizedQuoteStatus(item)
      if (normalized === 'active') return 0
      if (normalized === 'invalidated') return 2
      return 1
    }
    return nextRows.sort((left, right) => {
      const statusDelta = statusRank(left) - statusRank(right)
      if (statusDelta !== 0) return statusDelta
      return String(right.quoted_at || '').localeCompare(String(left.quoted_at || ''))
    })
  }
  return nextRows.sort((left, right) => String(right.quoted_at || '').localeCompare(String(left.quoted_at || '')))
}

function getQuoteActionLabel(item: SupplierQuoteActionItem) {
  const actionType = String(item.action_type || '').trim()
  if (actionType === 'copy_as_new') return '复制为新报价'
  if (actionType === 'invalidate') return '作废报价'
  if (actionType === 'update_invalidation_reason') return '修改作废原因'
  if (actionType === 'import_quotes') return '批量导入报价'
  if (actionType === 'export_quotes') return '导出历史报价'
  if (actionType === 'export_settlements') return '导出结算台账'
  if (actionType === 'create_settlement') return '创建结算单'
  if (actionType === 'update_settlement') return '更新结算单'
  if (actionType === 'cancel_settlement') return '作废结算单'
  if (actionType === 'build_settlement_from_quotes') return '报价生成结算单'
  return '历史操作'
}

function getQuoteActionDescription(item: SupplierQuoteActionItem) {
  const actionType = String(item.action_type || '').trim()
  if (actionType === 'copy_as_new') return '已从历史报价复制出新的报价记录'
  if (actionType === 'invalidate') return '已将该历史报价标记为作废'
  if (actionType === 'update_invalidation_reason') return '已更新该历史报价的作废原因'
  if (actionType === 'import_quotes') return '已批量导入供应商报价'
  if (actionType === 'export_quotes') return '已导出当前筛选下的历史报价'
  if (actionType === 'export_settlements') return '已导出当前筛选下的结算台账'
  if (actionType === 'create_settlement') return '已创建供应商结算单'
  if (actionType === 'update_settlement') return '已更新结算单付款进度'
  if (actionType === 'cancel_settlement') return '已作废供应商结算单'
  if (actionType === 'build_settlement_from_quotes') return '已从已选历史报价生成结算单'
  return '已执行供应平台操作'
}

function getSettlementStatusLabel(status?: SupplierSettlementStatus | string | null) {
  const normalizedStatus = String(status || 'pending').trim()
  if (normalizedStatus === 'partial') return '部分付款'
  if (normalizedStatus === 'paid') return '已结清'
  if (normalizedStatus === 'cancelled') return '已取消'
  return '待付款'
}

function getSettlementStatusClass(status?: SupplierSettlementStatus | string | null) {
  const normalizedStatus = String(status || 'pending').trim()
  if (normalizedStatus === 'paid') return 'is-active'
  if (normalizedStatus === 'cancelled') return 'is-inactive'
  if (normalizedStatus === 'partial') return 'is-warning'
  return 'is-pending'
}

function formatSettlementPeriod(item: SupplierSettlementItem) {
  const startText = formatTime(item.period_start)
  const endText = formatTime(item.period_end)
  if (startText === '暂无' && endText === '暂无') {
    return '未设置'
  }
  if (startText === endText || endText === '暂无') {
    return startText
  }
  if (startText === '暂无') {
    return endText
  }
  return `${startText} 至 ${endText}`
}

function getSettlementProgressPercent(item: SupplierSettlementItem) {
  const totalAmount = Number(item.total_amount || 0)
  const paidAmount = Number(item.paid_amount || 0)
  if (totalAmount <= 0) return 0
  return Math.max(0, Math.min(100, Math.round((paidAmount / totalAmount) * 100)))
}

function getSettlementProgressLabel(item: SupplierSettlementItem) {
  return `${getSettlementProgressPercent(item)}% 已付`
}

function getSettlementFollowUpLabel(item: SupplierSettlementItem) {
  const normalizedStatus = String(item.status || 'pending').trim()
  if (normalizedStatus === 'paid') return '已完成付款'
  if (normalizedStatus === 'cancelled') return '当前结算单已取消'
  if (normalizedStatus === 'partial') return `剩余 ${formatPrice(item.pending_amount)} 待付`
  return item.payment_due_date ? `请在 ${formatTime(item.payment_due_date)} 前完成付款` : '等待管理员确认付款时间'
}

function getSettlementFollowUpDescription(item: SupplierSettlementItem) {
  const normalizedStatus = String(item.status || 'pending').trim()
  if (normalizedStatus === 'paid') {
    return '该结算单已经结清，建议留意后续新账期和新的结算通知。'
  }
  if (normalizedStatus === 'cancelled') {
    return '该结算单已被取消，如需继续处理，请联系管理员重新生成结算单。'
  }
  if (normalizedStatus === 'partial') {
    return `本单仍有 ${formatPrice(item.pending_amount)} 未付，建议按照账期继续跟进剩余款项。`
  }
  return item.payment_due_date
    ? `当前仍处于待付款状态，应付日期为 ${formatTime(item.payment_due_date)}，请尽快安排付款。`
    : '当前还没有明确的付款日期，建议先和管理员确认账期与付款计划。'
}

function getQuoteActionPayload(item: SupplierQuoteActionItem): QuoteActionPayload {
  const payload = item.action_payload
  if (typeof payload === 'string') {
    const parsed = tryParseJson(payload.trim())
    return isRecord(parsed) ? parsed : {}
  }
  return isRecord(payload) ? payload : {}
}

function getQuoteActionPayloadString(item: SupplierQuoteActionItem, key: string) {
  const value = getQuoteActionPayload(item)[key]
  return typeof value === 'string' ? value.trim() : ''
}

function getQuoteActionPayloadNumber(item: SupplierQuoteActionItem, key: string) {
  const value = getQuoteActionPayload(item)[key]
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function getQuoteActionPayloadBoolean(item: SupplierQuoteActionItem, key: string) {
  const value = getQuoteActionPayload(item)[key]
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (normalized === 'true' || normalized === '1') return true
    if (normalized === 'false' || normalized === '0') return false
  }
  return typeof value === 'boolean' ? value : null
}

function getQuoteActionPayloadArray(item: SupplierQuoteActionItem, key: string) {
  const value = getQuoteActionPayload(item)[key]
  if (Array.isArray(value)) return value
  if (typeof value === 'string') {
    const text = value.trim()
    if (!text) return []
    const parsed = tryParseJson(text)
    if (Array.isArray(parsed)) return parsed
    if (text.includes(',')) {
      return text.split(',').map((entry) => entry.trim()).filter(Boolean)
    }
  }
  return []
}

function getQuoteActionPayloadStringArray(item: SupplierQuoteActionItem, key: string) {
  const value = getQuoteActionPayloadArray(item, key)
  return value
    .map((entry) => String(entry || '').trim())
    .filter(Boolean)
    .slice(0, 5)
}

function getQuoteActionPayloadCount(item: SupplierQuoteActionItem, ...keys: string[]) {
  for (const key of keys) {
    const numericValue = getQuoteActionPayloadNumber(item, key)
    if (numericValue != null) {
      return numericValue
    }
    const listValue = getQuoteActionPayloadArray(item, key)
    if (listValue.length) {
      return listValue.length
    }
  }
  return null
}

function formatQuoteActionCount(value: number | null) {
  return value == null ? '—' : `${value} 条`
}

function isImportQuoteAction(item: SupplierQuoteActionItem) {
  return String(item.action_type || '').trim() === 'import_quotes'
}

function isExportQuoteAction(item: SupplierQuoteActionItem) {
  return String(item.action_type || '').trim() === 'export_quotes'
}

function isExportSettlementAction(item: SupplierQuoteActionItem) {
  return String(item.action_type || '').trim() === 'export_settlements'
}

function getImportQuoteActionFileName(item: SupplierQuoteActionItem) {
  return getQuoteActionPayloadString(item, 'file_name') || '未记录'
}

function getImportQuoteActionRowCount(item: SupplierQuoteActionItem) {
  return getQuoteActionPayloadCount(item, 'total_count', 'rows')
}

function getImportQuoteActionSuccessCount(item: SupplierQuoteActionItem) {
  return getQuoteActionPayloadNumber(item, 'success_count')
}

function getImportQuoteActionSkippedCount(item: SupplierQuoteActionItem) {
  return getQuoteActionPayloadNumber(item, 'skipped_count')
}

function getImportQuoteActionFailureCount(item: SupplierQuoteActionItem) {
  return getQuoteActionPayloadCount(item, 'failed_count', 'failure_examples')
}

function getImportQuoteActionModeLabel(item: SupplierQuoteActionItem) {
  const importMode = getQuoteActionPayloadString(item, 'import_mode')
  return importMode ? getQuoteImportModeLabel(importMode) : ''
}

function formatQuoteActionPayloadValue(value: unknown) {
  if (value == null) return ''
  if (typeof value === 'string') return value.trim()
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : ''
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (Array.isArray(value)) {
    return value
      .map((entry) => formatQuoteActionPayloadValue(entry))
      .filter(Boolean)
      .join('、')
  }
  if (isRecord(value)) {
    return Object.entries(value)
      .slice(0, 5)
      .map(([key, entry]) => `${key}: ${formatQuoteActionPayloadValue(entry)}`)
      .filter((entry) => !entry.endsWith(': '))
      .join('；')
  }
  return String(value)
}

function formatQuoteActionExample(example: unknown, index: number) {
  if (typeof example === 'string') {
    return example.trim()
  }
  if (isRecord(example)) {
    const rowNumber = formatQuoteActionPayloadValue(example.row_number ?? example.row ?? example.index)
    const product = formatQuoteActionPayloadValue(
      example.product_name ?? example.price_identity_label ?? example.price_identity_key,
    )
    const reason = formatQuoteActionPayloadValue(example.failure_reason ?? example.reason ?? example.message)
    const status = formatQuoteActionPayloadRowStatus(example)
    return [
      rowNumber ? `第 ${rowNumber} 行` : `示例 ${index + 1}`,
      product,
      reason || status,
    ].filter(Boolean).join(' · ')
  }
  return formatQuoteActionPayloadValue(example) || `示例 ${index + 1}`
}

function getImportQuoteActionFailedExamples(item: SupplierQuoteActionItem) {
  return getQuoteActionPayloadArray(item, 'failure_examples')
    .map((entry, index) => formatQuoteActionExample(entry, index))
    .filter(Boolean)
    .slice(0, 8)
}

function getQuoteActionSuccessRecordIdList(item: SupplierQuoteActionItem) {
  return getQuoteActionPayloadArray(item, 'success_record_ids')
    .map((entry) => String(entry || '').trim())
    .filter(Boolean)
    .slice(0, 20)
}

function getQuoteActionScopeText(item: SupplierQuoteActionItem) {
  const scope = getQuoteActionPayloadString(item, 'scope')
  if (scope === 'filtered') return '当前筛选'
  if (scope === 'selected') return '已选记录'
  return ''
}

function getQuoteActionScopeLabel(item: SupplierQuoteActionItem) {
  const scope = getQuoteActionScopeText(item)
  return scope ? `范围：${scope}` : ''
}

function getQuoteActionStatusFilterText(item: SupplierQuoteActionItem) {
  const statusFilter = getQuoteActionPayloadString(item, 'status_filter')
  if (statusFilter === 'active') return '仅有效'
  if (statusFilter === 'invalidated') return '仅作废'
  if (statusFilter === 'pending') return '待付款'
  if (statusFilter === 'partial') return '部分付款'
  if (statusFilter === 'paid') return '已结清'
  if (statusFilter === 'cancelled') return '已取消'
  if (statusFilter === 'all') return '全部'
  return ''
}

function getQuoteActionStatusFilterLabel(item: SupplierQuoteActionItem) {
  const statusFilter = getQuoteActionStatusFilterText(item)
  return statusFilter ? `状态：${statusFilter}` : ''
}

function getQuoteActionDateRangeText(item: SupplierQuoteActionItem) {
  const startDate = getQuoteActionPayloadString(item, 'start_quoted_at')
    || getQuoteActionPayloadString(item, 'start_created_at')
    || getQuoteActionPayloadString(item, 'start_period_start')
  const endDate = getQuoteActionPayloadString(item, 'end_quoted_at')
    || getQuoteActionPayloadString(item, 'end_created_at')
    || getQuoteActionPayloadString(item, 'end_period_end')
  if (startDate && endDate) return `${startDate} 至 ${endDate}`
  if (startDate) return `${startDate} 起`
  if (endDate) return `截至 ${endDate}`
  return ''
}

function getQuoteActionDateRangeLabel(item: SupplierQuoteActionItem) {
  const dateRange = getQuoteActionDateRangeText(item)
  return dateRange ? `时间：${dateRange}` : ''
}

function getQuoteActionFormatLabel(item: SupplierQuoteActionItem) {
  const format = getQuoteActionPayloadString(item, 'format')
  return format ? `格式：${format.toUpperCase()}` : ''
}

function getQuoteActionRowCountLabel(item: SupplierQuoteActionItem) {
  const rowCount = getQuoteActionPayloadCount(item, 'row_count', 'total_count', 'rows')
  return rowCount == null ? '' : `导出：${rowCount} 条`
}

function getQuoteActionCurrentProductOnlyText(item: SupplierQuoteActionItem) {
  const currentProductOnly = getQuoteActionPayloadBoolean(item, 'current_product_only')
  if (currentProductOnly == null) return ''
  return currentProductOnly ? '仅当前商品' : '全部商品'
}

function getQuoteActionCurrentProductOnlyLabel(item: SupplierQuoteActionItem) {
  const currentProductOnly = getQuoteActionCurrentProductOnlyText(item)
  return currentProductOnly ? `商品：${currentProductOnly}` : ''
}

function getImportQuoteActionSummaryTags(item: SupplierQuoteActionItem) {
  const tags = [
    getImportQuoteActionFileName(item) !== '未记录' ? `文件：${getImportQuoteActionFileName(item)}` : '',
    getImportQuoteActionModeLabel(item) ? `模式：${getImportQuoteActionModeLabel(item)}` : '',
    getImportQuoteActionRowCount(item) == null ? '' : `总行：${getImportQuoteActionRowCount(item)}`,
    getImportQuoteActionSuccessCount(item) == null ? '' : `成功：${getImportQuoteActionSuccessCount(item)}`,
    getImportQuoteActionSkippedCount(item) == null ? '' : `跳过：${getImportQuoteActionSkippedCount(item)}`,
    getImportQuoteActionFailureCount(item) == null ? '' : `失败：${getImportQuoteActionFailureCount(item)}`,
  ]
  return tags.filter(Boolean)
}

function getQuoteActionPayloadTags(item: SupplierQuoteActionItem) {
  if (isImportQuoteAction(item)) {
    return getImportQuoteActionSummaryTags(item)
  }

  if (isExportQuoteAction(item) || isExportSettlementAction(item)) {
    return [
      getQuoteActionScopeLabel(item),
      getQuoteActionFormatLabel(item),
      getQuoteActionRowCountLabel(item),
      getQuoteActionStatusFilterLabel(item),
      getQuoteActionDateRangeLabel(item),
      getQuoteActionCurrentProductOnlyLabel(item),
    ].filter(Boolean)
  }

  return [
    getQuoteActionPayloadString(item, 'settlement_title') ? `结算单：${getQuoteActionPayloadString(item, 'settlement_title')}` : '',
    getQuoteActionPayloadNumber(item, 'record_count') != null ? `报价条数：${getQuoteActionPayloadNumber(item, 'record_count')}` : '',
    getQuoteActionPayloadNumber(item, 'total_amount') != null ? `总额：${getQuoteActionPayloadNumber(item, 'total_amount')}` : '',
    getQuoteActionPayloadString(item, 'status') ? `状态：${getSettlementStatusLabel(getQuoteActionPayloadString(item, 'status'))}` : '',
  ].filter(Boolean)
}

function getQuoteActionPayloadRowStatus(row: Record<string, unknown>) {
  if (row.skipped === true || String(row.status || '').trim() === 'skipped') {
    return '已跳过'
  }
  const status = String(row.status || '').trim()
  if (status === 'success') return '成功'
  if (status === 'failed') return '失败'
  if (status) return status
  if (row.failure_reason || row.reason || row.message) return '失败'
  if (row.record_id != null) return '已入库'
  return ''
}

function getQuoteActionPayloadRows(item: SupplierQuoteActionItem) {
  return getQuoteActionPayloadArray(item, 'rows').slice(0, 20)
}

function formatQuoteActionPayloadRowSummary(row: unknown, index: number) {
  if (!isRecord(row)) {
    return formatQuoteActionPayloadValue(row) || `第 ${index + 1} 条`
  }

  const rowNumber = formatQuoteActionPayloadValue(row.row_number ?? row.row ?? row.index)
  const product = formatQuoteActionPayloadValue(
    row.product_name ?? row.price_identity_label ?? row.price_identity_key ?? row.target_product_name,
  )
  const price = formatQuoteActionPayloadValue(row.quote_price ?? row.target_quote_price)
  const status = getQuoteActionPayloadRowStatus(row)

  return [
    rowNumber ? `第 ${rowNumber} 行` : `第 ${index + 1} 条`,
    product,
    price ? `报价 ${price}` : '',
    status,
  ].filter(Boolean).join(' · ')
}

function formatQuoteActionPayloadRowDetail(row: unknown) {
  if (!isRecord(row)) {
    return ''
  }

  return [
    formatQuoteActionPayloadValue(row.failure_reason ?? row.reason ?? row.message),
    formatQuoteActionPayloadValue(row.remarks),
    formatQuoteActionPayloadValue(row.import_mode ? `模式 ${getQuoteImportModeLabel(String(row.import_mode))}` : ''),
    formatQuoteActionPayloadValue(row.quoted_at),
  ].filter(Boolean).join('；')
}

function getQuoteActionDetailEntries(item: SupplierQuoteActionItem) {
  if (isImportQuoteAction(item)) {
    return [
      { label: '文件名', value: getImportQuoteActionFileName(item) },
      { label: '导入模式', value: getImportQuoteActionModeLabel(item) },
      { label: '总行数', value: formatQuoteActionCount(getImportQuoteActionRowCount(item)) },
      { label: '成功数', value: formatQuoteActionCount(getImportQuoteActionSuccessCount(item)) },
      { label: '跳过数', value: formatQuoteActionCount(getImportQuoteActionSkippedCount(item)) },
      { label: '失败数', value: formatQuoteActionCount(getImportQuoteActionFailureCount(item)) },
    ].filter((entry) => entry.value && entry.value !== '—')
  }

  if (isExportQuoteAction(item)) {
    return [
      { label: '导出格式', value: getQuoteActionFormatLabel(item).replace('格式：', '') },
      { label: '导出范围', value: getQuoteActionScopeText(item) },
      { label: '状态筛选', value: getQuoteActionStatusFilterText(item) },
      { label: '商品范围', value: getQuoteActionCurrentProductOnlyText(item) },
      { label: '导出条数', value: formatQuoteActionCount(getQuoteActionPayloadCount(item, 'row_count', 'total_count', 'rows')) },
      { label: '文件名', value: getQuoteActionPayloadString(item, 'file_name') },
    ].filter((entry) => entry.value && entry.value !== '—')
  }

  if (isExportSettlementAction(item)) {
    return [
      { label: '导出格式', value: getQuoteActionFormatLabel(item).replace('格式：', '') },
      { label: '导出范围', value: getQuoteActionScopeText(item) },
      { label: '结算状态', value: getQuoteActionStatusFilterText(item) },
      { label: '账期范围', value: getQuoteActionDateRangeText(item) },
      { label: '导出条数', value: formatQuoteActionCount(getQuoteActionPayloadCount(item, 'row_count', 'total_count', 'rows')) },
      { label: '文件名', value: getQuoteActionPayloadString(item, 'file_name') },
    ].filter((entry) => entry.value && entry.value !== '—')
  }

  if (String(item.action_type || '').trim() === 'copy_as_new') {
    return [
      { label: '来源记录', value: item.record_id ? `#${item.record_id}` : '' },
      { label: '来源商品', value: item.product_name || item.price_identity_label || item.price_identity_key || '' },
      { label: '来源报价', value: item.quote_price != null ? `${item.quote_price}${item.quote_unit || ''}` : '' },
      { label: '来源时间', value: item.quoted_at ? formatTime(item.quoted_at) : '' },
      { label: '新记录', value: item.target_record_id ? `#${item.target_record_id}` : '' },
      { label: '新报价商品', value: item.target_product_name || item.target_price_identity_label || '' },
      { label: '新报价', value: item.target_quote_price != null ? `${item.target_quote_price}${item.quote_unit || ''}` : '' },
      { label: '新报价时间', value: item.target_quoted_at ? formatTime(item.target_quoted_at) : '' },
    ].filter((entry) => entry.value)
  }

  if (String(item.action_type || '').trim() === 'invalidate' || String(item.action_type || '').trim() === 'update_invalidation_reason') {
    return [
      { label: '记录 ID', value: item.record_id ? `#${item.record_id}` : '' },
      { label: '商品', value: item.product_name || item.price_identity_label || item.price_identity_key || '' },
      { label: '报价', value: item.quote_price != null ? `${item.quote_price}${item.quote_unit || ''}` : '' },
      { label: '报价时间', value: item.quoted_at ? formatTime(item.quoted_at) : '' },
      { label: '原状态', value: getQuoteActionPayloadString(item, 'previous_status') || '' },
      { label: '原作废原因', value: getQuoteActionPayloadString(item, 'previous_invalidated_reason') || '' },
      { label: '当前作废原因', value: getQuoteActionPayloadString(item, 'next_invalidated_reason') || item.action_reason || '' },
    ].filter((entry) => entry.value)
  }

  if (['create_settlement', 'update_settlement', 'cancel_settlement', 'build_settlement_from_quotes'].includes(String(item.action_type || '').trim())) {
    return [
      { label: '结算单 ID', value: getQuoteActionPayloadNumber(item, 'settlement_id') != null ? `#${getQuoteActionPayloadNumber(item, 'settlement_id')}` : '' },
      { label: '结算单标题', value: getQuoteActionPayloadString(item, 'settlement_title') || '' },
      { label: '报价条数', value: formatQuoteActionCount(getQuoteActionPayloadNumber(item, 'record_count')) },
      { label: '总金额', value: getQuoteActionPayloadNumber(item, 'total_amount') != null ? formatPrice(getQuoteActionPayloadNumber(item, 'total_amount')) : '' },
      { label: '原已付金额', value: getQuoteActionPayloadNumber(item, 'previous_paid_amount') != null ? formatPrice(getQuoteActionPayloadNumber(item, 'previous_paid_amount')) : '' },
      { label: '当前已付金额', value: getQuoteActionPayloadNumber(item, 'next_paid_amount') != null ? formatPrice(getQuoteActionPayloadNumber(item, 'next_paid_amount')) : (getQuoteActionPayloadNumber(item, 'paid_amount') != null ? formatPrice(getQuoteActionPayloadNumber(item, 'paid_amount')) : '') },
      { label: '原状态', value: getQuoteActionPayloadString(item, 'previous_status') ? getSettlementStatusLabel(getQuoteActionPayloadString(item, 'previous_status')) : '' },
      { label: '当前状态', value: getQuoteActionPayloadString(item, 'next_status') ? getSettlementStatusLabel(getQuoteActionPayloadString(item, 'next_status')) : (getQuoteActionPayloadString(item, 'status') ? getSettlementStatusLabel(getQuoteActionPayloadString(item, 'status')) : '') },
      { label: '作废原因', value: getQuoteActionPayloadString(item, 'cancel_reason') || '' },
      { label: '应付日期', value: getQuoteActionPayloadString(item, 'payment_due_date') || '' },
      { label: '付款日期', value: getQuoteActionPayloadString(item, 'payment_date') || '' },
    ].filter((entry) => entry.value && entry.value !== '—')
  }

  return Object.entries(getQuoteActionPayload(item))
    .filter(([key, value]) => key !== 'rows' && key !== 'failure_examples' && key !== 'success_record_ids' && value != null)
    .slice(0, 8)
    .map(([key, value]) => ({ label: key, value: formatQuoteActionPayloadValue(value) }))
    .filter((entry) => entry.value)
}

function shouldShowQuoteActionPayloadDetails(item: SupplierQuoteActionItem) {
  return Boolean(
    getQuoteActionDetailEntries(item).length
      || getImportQuoteActionFailedExamples(item).length
      || getQuoteActionSuccessRecordIdList(item).length
      || getQuoteActionPayloadRows(item).length,
  )
}

function openQuoteActionDetail(item: SupplierQuoteActionItem) {
  activeQuoteActionDetail.value = item
  quoteActionDetailVisible.value = true
}

function applyQuoteImportPreviewDiagnostics(
  rows: QuoteImportPreviewRow[],
  previewItems: SupplierQuoteImportPreviewItem[],
) {
  const previewItemMap = new Map(previewItems.map((item) => [item.row_number, item] as const))
  return rows.map((row) => {
    const previewItem = previewItemMap.get(row.row_number)
    if (!previewItem) return row
    return {
      ...row,
      preview_status: previewItem.preview_status,
      preview_reason: previewItem.preview_reason || '',
      existing_record_id: previewItem.existing_record_id ?? null,
      existing_quote_price: previewItem.existing_quote_price ?? null,
      existing_quote_unit: previewItem.existing_quote_unit ?? null,
      existing_quoted_at: previewItem.existing_quoted_at ?? null,
      existing_remarks: previewItem.existing_remarks ?? null,
      duplicate_match_fields: previewItem.duplicate_match_fields ?? [],
      abnormal_change_ratio: previewItem.abnormal_change_ratio ?? null,
      abnormal_change_hint: previewItem.abnormal_change_hint ?? null,
    } satisfies QuoteImportPreviewRow
  })
}

async function enrichQuoteImportPreviewRows(rows: QuoteImportPreviewRow[]) {
  if (!selectedSupplier.value) {
    return rows
  }
  const readyRows = rows.filter((item) => item.status === 'ready')
  if (!readyRows.length) {
    return rows
  }
  try {
    const response = await previewImportSupplierQuotes({
      supplier_id: selectedSupplier.value.id,
      import_mode: quoteImportMode.value,
      ...buildQuoteImportRulePayload(),
      items: readyRows.map((item) => buildQuoteImportRequestItem(item)),
    })
    return applyQuoteImportPreviewDiagnostics(rows, response.items)
  } catch {
    return rows
  }
}

function getQuoteRecordId(item: SupplierQuoteItem) {
  return item.record_id == null ? null : Number(item.record_id)
}

function buildHistoryRemark(item: SupplierQuoteItem) {
  const historyLabel = item.product_name || item.price_identity_label || item.price_identity_key || '历史报价'
  const historyTime = formatTime(item.quoted_at)
  const historyRemarkPrefix = `复制自历史报价：${historyLabel}${historyTime !== '暂无' ? `（${historyTime}）` : ''}`
  const originalRemark = String(item.remarks || '').trim()
  return originalRemark && !originalRemark.startsWith(historyRemarkPrefix)
    ? `${historyRemarkPrefix}；${originalRemark}`
    : historyRemarkPrefix
}

function isQuoteSelected(item: SupplierQuoteItem) {
  const recordId = getQuoteRecordId(item)
  return recordId != null && selectedQuoteIds.value.includes(recordId)
}

function handleQuoteSelection(item: SupplierQuoteItem, checked: string | number | boolean) {
  const recordId = getQuoteRecordId(item)
  if (recordId == null) return
  const next = new Set(selectedQuoteIds.value)
  if (checked) {
    next.add(recordId)
  } else {
    next.delete(recordId)
  }
  selectedQuoteIds.value = Array.from(next)
}

function selectAllFilteredQuotes() {
  const next = new Set(selectedQuoteIds.value)
  historyQuoteRows.value.forEach((item) => {
    const recordId = getQuoteRecordId(item)
    if (recordId != null) {
      next.add(recordId)
    }
  })
  selectedQuoteIds.value = Array.from(next)
}

function toggleVisibleQuoteSelection(checked: string | number | boolean) {
  if (checked) {
    selectAllFilteredQuotes()
    return
  }
  const visibleIdSet = new Set(visibleQuoteRecordIds.value)
  selectedQuoteIds.value = selectedQuoteIds.value.filter((item) => !visibleIdSet.has(item))
}

function selectFilteredQuotesByStatus(targetStatus: 'active' | 'invalidated') {
  selectedQuoteIds.value = historyQuoteRows.value
    .filter((item) => getNormalizedQuoteStatus(item) === targetStatus)
    .map((item) => getQuoteRecordId(item))
    .filter((item): item is number => item != null)
}

function clearSelectedQuotes() {
  selectedQuoteIds.value = []
}

function applyQuoteHistoryView(view: QuoteHistoryView) {
  if (view === 'current_product') {
    quoteCurrentProductOnly.value = !quoteCurrentProductOnly.value
    return
  }
  quoteCurrentProductOnly.value = false
  quoteStatusFilter.value = view === 'all' ? 'all' : view
}

function setQuoteDateRangeShortcut(days: number) {
  const endDate = new Date()
  const startDate = new Date()
  startDate.setDate(endDate.getDate() - days)
  quoteDateRange.value = [formatDateOnly(startDate), formatDateOnly(endDate)]
}

function clearQuoteDateRange() {
  quoteDateRange.value = []
}

function resetQuoteHistoryFilters() {
  quoteStatusFilter.value = 'all'
  quoteKeyword.value = ''
  quoteCurrentProductOnly.value = false
  clearQuoteDateRange()
}

function setQuoteActionDateRangeShortcut(days: number) {
  const endDate = new Date()
  const startDate = new Date()
  startDate.setDate(endDate.getDate() - days)
  quoteActionDateRange.value = [formatDateOnly(startDate), formatDateOnly(endDate)]
}

function clearQuoteActionDateRange() {
  quoteActionDateRange.value = []
}

function resetQuoteActionFilters() {
  quoteActionTypeFilter.value = 'all'
  quoteActionOperatorFilter.value = ''
  quoteActionKeywordFilter.value = ''
  clearQuoteActionDateRange()
}

function readLastSelectedSupplierId() {
  if (typeof window === 'undefined') return null
  try {
    const raw = String(window.localStorage.getItem(LAST_SUPPLIER_ID_STORAGE_KEY) || '').trim()
    if (!raw) {
      return null
    }
    const id = Number(raw)
    return Number.isFinite(id) ? id : null
  } catch {
    return null
  }
}

function writeLastSelectedSupplierId(value: number | null) {
  if (typeof window === 'undefined') return
  try {
    if (value == null) {
      window.localStorage.removeItem(LAST_SUPPLIER_ID_STORAGE_KEY)
      return
    }
    window.localStorage.setItem(LAST_SUPPLIER_ID_STORAGE_KEY, String(value))
  } catch {
    // Ignore local cache write failures.
  }
}

function readRecentSupplierIds() {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(RECENT_SUPPLIER_IDS_STORAGE_KEY)
    if (!raw) {
      return []
    }
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      return []
    }
    return parsed
      .map((item) => Number(item))
      .filter((item) => Number.isFinite(item) && item > 0)
      .slice(0, 6)
  } catch {
    return []
  }
}

function writeRecentSupplierIds(nextIds: number[]) {
  recentSupplierIds.value = nextIds.slice(0, 6)
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(RECENT_SUPPLIER_IDS_STORAGE_KEY, JSON.stringify(recentSupplierIds.value))
  } catch {
    // Ignore local cache write failures.
  }
}

function rememberSupplierSelection(id: number | null) {
  writeLastSelectedSupplierId(id)
  if (id == null) {
    return
  }
  writeRecentSupplierIds([id, ...recentSupplierIds.value.filter((item) => item !== id)])
}

function readQuoteDrafts() {
  if (typeof window === 'undefined') return {} as Record<string, SupplierQuoteDraft>
  try {
    const parsed = JSON.parse(window.localStorage.getItem(QUOTE_DRAFTS_STORAGE_KEY) || '{}')
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return {} as Record<string, SupplierQuoteDraft>
    }
    return parsed as Record<string, SupplierQuoteDraft>
  } catch {
    return {} as Record<string, SupplierQuoteDraft>
  }
}

function writeQuoteDrafts(nextDrafts: Record<string, SupplierQuoteDraft>) {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(QUOTE_DRAFTS_STORAGE_KEY, JSON.stringify(nextDrafts))
  } catch {
    // Ignore local cache write failures.
  }
}

function currentQuoteDraftKey() {
  if (!selectedSupplier.value || !selectedProductKey.value) return ''
  return `${selectedSupplier.value.id}::${selectedProductKey.value}`
}

function loadCurrentQuoteDraft() {
  const key = currentQuoteDraftKey()
  currentQuoteDraft.value = key ? readQuoteDrafts()[key] || null : null
  emitQuoteDraftSummary()
}

function emitQuoteDraftSummary() {
  const drafts = Object.values(readQuoteDrafts())
  const supplierId = selectedSupplier.value?.id
  const scopedDrafts = supplierId
    ? drafts.filter((item) => item.supplier_id === supplierId)
    : drafts
  const latestDraft = scopedDrafts
    .slice()
    .sort((first, second) => new Date(second.updated_at).getTime() - new Date(first.updated_at).getTime())[0]
  emit('quote-draft-summary', {
    count: scopedDrafts.length,
    hasCurrent: Boolean(currentQuoteDraft.value),
    latestLabel: latestDraft?.price_identity_label || '',
    latestUpdatedAt: latestDraft?.updated_at || '',
  })
}

function readSavedOperatorName() {
  if (typeof window === 'undefined') return ''
  try {
    return String(window.localStorage.getItem('battel:supplier-admin-operator') || '').trim()
  } catch {
    return ''
  }
}

function writeSavedOperatorName(value: string) {
  if (typeof window === 'undefined') return
  try {
    const normalizedValue = value.trim()
    if (!normalizedValue) {
      window.localStorage.removeItem('battel:supplier-admin-operator')
      return
    }
    window.localStorage.setItem('battel:supplier-admin-operator', normalizedValue)
  } catch {
    // Ignore local cache write failures.
  }
}

function buildSupplierQuoteQueryOptions(offset = quotePageOffset.value, limit = quotePageSize.value) {
  const [startDate, endDate] = quoteDateRange.value
  return {
    limit,
    offset,
    status: quoteStatusFilter.value === 'all' ? undefined : quoteStatusFilter.value,
    keyword: quoteKeyword.value.trim() || undefined,
    start_quoted_at: startDate || undefined,
    end_quoted_at: endDate || undefined,
    price_identity_key: quoteCurrentProductOnly.value ? selectedProductKey.value || undefined : undefined,
  }
}

function buildSupplierQuoteActionQueryOptions(offset = quoteActionOffset.value, limit = quoteActionPageSize.value) {
  const [startDate, endDate] = quoteActionDateRange.value
  return {
    limit,
    offset,
    action_type: quoteActionTypeFilter.value === 'all' ? undefined : quoteActionTypeFilter.value,
    operator_name: quoteActionOperatorFilter.value.trim() || undefined,
    keyword: quoteActionKeywordFilter.value.trim() || undefined,
    start_created_at: startDate || undefined,
    end_created_at: endDate || undefined,
  }
}

function buildSupplierSettlementQueryOptions(offset = settlementOffset.value, limit = settlementPageSize.value) {
  const [startDate, endDate] = settlementDateRange.value
  return {
    limit,
    offset,
    status: settlementStatusFilter.value === 'all' ? undefined : settlementStatusFilter.value,
    keyword: settlementKeyword.value.trim() || undefined,
    start_period_start: startDate || undefined,
    end_period_end: endDate || undefined,
  }
}

function buildDefaultSettlementTitle() {
  const supplierName = selectedSupplier.value?.supplier_name || '供应商'
  const today = formatDateOnly(new Date())
  return `${supplierName} ${today} 结算单`
}

function summarizeBatchOperationRows(rows: BatchOperationExportRow[]) {
  const successCount = rows.filter((item) => item.状态 === '成功').length
  const failedCount = rows.filter((item) => item.状态 === '失败').length
  const skippedCount = rows.filter((item) => item.状态 === '跳过').length
  const summaryParts = [`共 ${rows.length} 条`]
  if (successCount) summaryParts.push(`成功 ${successCount} 条`)
  if (skippedCount) summaryParts.push(`跳过 ${skippedCount} 条`)
  if (failedCount) summaryParts.push(`失败 ${failedCount} 条`)
  return summaryParts.join('，')
}

function setLastBatchOperationResult(
  kind: BatchOperationKind,
  title: string,
  rows: BatchOperationExportRow[],
) {
  lastBatchOperationKind.value = kind
  lastBatchOperationTitle.value = title
  lastBatchOperationRows.value = rows
  lastBatchOperationSummary.value = summarizeBatchOperationRows(rows)
}

function clearLastBatchOperationResult() {
  lastBatchOperationKind.value = null
  lastBatchOperationTitle.value = ''
  lastBatchOperationSummary.value = ''
  lastBatchOperationRows.value = []
}

async function downloadLastBatchOperationResults(format: 'xlsx' | 'csv') {
  if (!lastBatchOperationRows.value.length) {
    ElMessage.warning('当前没有可导出的批量操作结果')
    return
  }

  const exportPrefix = slugifyExportValue(selectedSupplier.value?.supplier_name || 'supplier-batch')
  const fileSuffix = `${exportPrefix}-${lastBatchOperationKind.value || 'batch'}-${formatDateOnly(new Date())}`

  try {
    if (format === 'xlsx') {
      const xlsx = await import('xlsx')
      const worksheet = xlsx.utils.json_to_sheet(lastBatchOperationRows.value)
      const workbook = xlsx.utils.book_new()
      xlsx.utils.book_append_sheet(workbook, worksheet, '批量操作结果')
      xlsx.writeFile(workbook, `${fileSuffix}.xlsx`)
    } else {
      const headers = Object.keys(lastBatchOperationRows.value[0] || {})
      const lines = [
        headers.join(','),
        ...lastBatchOperationRows.value.map((row) =>
          headers
            .map((header) => `"${String(row[header] ?? '').replaceAll('"', '""')}"`)
            .join(','),
        ),
      ]
      const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `${fileSuffix}.csv`
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)
      URL.revokeObjectURL(url)
    }
    ElMessage.success(`已导出${lastBatchOperationTitle.value || '最近一批操作结果'}`)
  } catch {
    ElMessage.error('批量操作结果导出失败，请稍后重试')
  }
}

function buildQuotePayloadFromHistory(item: SupplierQuoteItem): SupplierQuoteCreatePayload | null {
  if (!item.supplier_id || !item.price_identity_key || item.quote_price == null) {
    return null
  }
  return {
    source_record_id: getQuoteRecordId(item) || undefined,
    supplier_id: item.supplier_id,
    supplier_name: item.supplier_name,
    contact_name: item.contact_name || selectedSupplier.value?.contact_name || undefined,
    contact_phone: item.contact_phone || selectedSupplier.value?.contact_phone || undefined,
    market_scope: item.market_scope || selectedSupplier.value?.market_scope || '本地市场',
    market_category: item.market_category || item.category || selectedSupplier.value?.market_category || undefined,
    channel: item.channel || selectedSupplier.value?.channel || undefined,
    price_identity_key: item.price_identity_key,
    price_identity_label: item.price_identity_label || undefined,
    product_name: item.product_name || undefined,
    category: item.category || undefined,
    spec_text: item.spec_text || undefined,
    quote_price: Number(item.quote_price),
    quote_unit: item.quote_unit || undefined,
    box_price: item.box_price == null ? undefined : Number(item.box_price),
    tax_price: item.tax_price == null ? undefined : Number(item.tax_price),
    inventory_status: item.inventory_status || undefined,
    remarks: buildHistoryRemark(item),
    quoted_by: resolvedOperatorName.value || item.quoted_by || item.contact_name || selectedSupplier.value?.contact_name || undefined,
  }
}

function fillQuoteFormFromHistory(item: SupplierQuoteItem) {
  quoteForm.source_record_id = getQuoteRecordId(item) || undefined
  if (item.price_identity_key) {
    emit('select-product', item.price_identity_key)
  }
  quoteForm.quote_price = item.quote_price == null ? undefined : Number(item.quote_price)
  quoteForm.quote_unit = item.quote_unit || '斤'
  quoteForm.box_price = item.box_price == null ? undefined : Number(item.box_price)
  quoteForm.tax_price = item.tax_price == null ? undefined : Number(item.tax_price)
  quoteForm.inventory_status = item.inventory_status || '现货'
  quoteForm.remarks = item.remarks || ''
}

function resetSupplierForm() {
  selectedSupplierId.value = isSupplierSession.value ? currentSupplierScopeId.value : null
  if (props.mobile) {
    mobileSupplierTask.value = isQuoteWorkspace.value || isSupplierSession.value ? 'quote' : 'suppliers'
  }
  if (isAdminSession.value && !props.mobile) {
    desktopSupplierWorkbenchTab.value = 'supplier'
  }
  supplierForm.supplier_name = ''
  supplierForm.contact_name = ''
  supplierForm.contact_phone = ''
  supplierForm.market_scope = '本地市场'
  supplierForm.market_category = ''
  supplierForm.channel = '微信小程序'
  supplierForm.notes = ''
  supplierForm.is_active = true
  supplierAccountOriginalUsername.value = ''
  supplierAccountForm.account_username = ''
  supplierAccountForm.account_password = ''
  supplierAccountForm.account_display_name = ''
  supplierAccountForm.account_is_active = true
  selectedSupplierQuoteRows.value = []
}

function resetQuoteForm() {
  quoteForm.source_record_id = undefined
  quoteForm.quote_price = undefined
  quoteForm.quote_unit = '斤'
  quoteForm.box_price = undefined
  quoteForm.tax_price = undefined
  quoteForm.inventory_status = '现货'
  quoteForm.remarks = ''
}

function saveQuoteDraft() {
  if (!selectedSupplier.value) {
    ElMessage.warning('请先选择或创建供应商')
    return
  }
  if (!selectedProductKey.value) {
    ElMessage.warning('请先选择商品')
    return
  }
  if (!hasQuoteDraftContent.value) {
    ElMessage.warning('当前没有可保存的草稿内容')
    return
  }

  const key = currentQuoteDraftKey()
  if (!key) return
  const nextDrafts = readQuoteDrafts()
  nextDrafts[key] = {
    supplier_id: selectedSupplier.value.id,
    supplier_name: selectedSupplier.value.supplier_name,
    price_identity_key: selectedProductKey.value,
    price_identity_label: selectedProductLabelResolved.value || selectedProductKey.value,
    quote_price: quoteForm.quote_price == null ? undefined : Number(quoteForm.quote_price),
    quote_unit: quoteForm.quote_unit || '斤',
    box_price: quoteForm.box_price == null ? undefined : Number(quoteForm.box_price),
    tax_price: quoteForm.tax_price == null ? undefined : Number(quoteForm.tax_price),
    inventory_status: quoteForm.inventory_status || '现货',
    remarks: quoteForm.remarks.trim(),
    operator_name: resolvedOperatorName.value,
    updated_at: new Date().toISOString(),
  }
  writeQuoteDrafts(nextDrafts)
  loadCurrentQuoteDraft()
  ElMessage.success('草稿已保存到本机')
}

function restoreQuoteDraft() {
  if (!currentQuoteDraft.value) {
    ElMessage.warning('当前没有可恢复的草稿')
    return
  }
  quoteForm.quote_price = currentQuoteDraft.value.quote_price
  quoteForm.quote_unit = currentQuoteDraft.value.quote_unit || '斤'
  quoteForm.box_price = currentQuoteDraft.value.box_price
  quoteForm.tax_price = currentQuoteDraft.value.tax_price
  quoteForm.inventory_status = currentQuoteDraft.value.inventory_status || '现货'
  quoteForm.remarks = currentQuoteDraft.value.remarks || ''
  operatorName.value = currentQuoteDraft.value.operator_name || operatorName.value
  ElMessage.success('已恢复本地草稿')
}

function clearCurrentQuoteDraft(silent = false) {
  const key = currentQuoteDraftKey()
  if (!key) {
    currentQuoteDraft.value = null
    return
  }
  const nextDrafts = readQuoteDrafts()
  if (!nextDrafts[key]) {
    currentQuoteDraft.value = null
    return
  }
  delete nextDrafts[key]
  writeQuoteDrafts(nextDrafts)
  currentQuoteDraft.value = null
  emitQuoteDraftSummary()
  if (!silent) {
    ElMessage.success('草稿已删除')
  }
}

function resetSettlementForm() {
  settlementForm.settlement_title = ''
  settlementForm.period_start = ''
  settlementForm.period_end = ''
  settlementForm.total_amount = undefined
  settlementForm.paid_amount = 0
  settlementForm.payment_due_date = ''
  settlementForm.payment_date = ''
  settlementForm.remarks = ''
}

function runWorkbenchPrimaryAction() {
  if (resolvedBackendSection.value === 'quote') {
    openQuoteImportDialog()
    return
  }
  if (resolvedBackendSection.value === 'settlement') {
    if (isAdminSession.value) {
      openSettlementCreateForm()
    }
    return
  }
  if (resolvedBackendSection.value === 'logs') {
    return
  }
  if (isAdminSession.value) {
    resetSupplierForm()
  }
}

function openSettlementCreateForm() {
  if (!selectedSupplier.value) {
    ElMessage.warning('请先选择供应商')
    return
  }
  resetSettlementForm()
  settlementForm.settlement_title = buildDefaultSettlementTitle()
  settlementFormVisible.value = true
}

async function createManualSettlement() {
  if (!selectedSupplierId.value) {
    ElMessage.warning('请先选择供应商')
    return
  }
  if (!settlementForm.settlement_title.trim()) {
    ElMessage.warning('请填写结算单标题')
    return
  }
  settlementSaving.value = 'create'
  try {
    await createSupplierSettlement(selectedSupplierId.value, {
      settlement_title: settlementForm.settlement_title.trim(),
      period_start: settlementForm.period_start || undefined,
      period_end: settlementForm.period_end || undefined,
      total_amount: settlementForm.total_amount ?? 0,
      paid_amount: settlementForm.paid_amount ?? 0,
      payment_due_date: settlementForm.payment_due_date || undefined,
      payment_date: settlementForm.payment_date || undefined,
      remarks: settlementForm.remarks.trim() || undefined,
      created_by: resolvedOperatorName.value,
    })
    settlementFormVisible.value = false
    resetSettlementForm()
    await Promise.all([loadSupplierSettlements(), loadSupplierQuoteActions()])
    ElMessage.success('结算单已创建')
  } catch {
    ElMessage.error('结算单创建失败，请稍后重试')
  } finally {
    settlementSaving.value = null
  }
}

async function buildSettlementFromSelectedQuotes() {
  if (!selectedSupplierId.value) {
    ElMessage.warning('请先选择供应商')
    return
  }
  if (!selectedActiveQuoteRows.value.length) {
    ElMessage.warning('请先勾选有效历史报价')
    return
  }

  const defaultTitle = buildDefaultSettlementTitle()
  try {
    const { value } = await ElMessageBox.prompt(
      `将基于已选的 ${selectedActiveQuoteRows.value.length} 条有效历史报价生成一张结算单。`,
      '报价生成结算单',
      {
        confirmButtonText: '生成结算单',
        cancelButtonText: '取消',
        inputValue: defaultTitle,
        inputPlaceholder: '请输入结算单标题',
        inputValidator: (inputValue) => String(inputValue || '').trim() ? true : '请填写结算单标题',
      },
    )

    settlementSaving.value = 'build'
    await buildSupplierSettlementsFromQuotes(selectedSupplierId.value, {
      settlement_title: String(value || '').trim(),
      quote_record_ids: selectedActiveQuoteRows.value
        .map((item) => item.record_id)
        .filter((item): item is number => item != null),
      payment_due_date: settlementForm.payment_due_date || undefined,
      remarks: `由已选有效历史报价生成，合计 ${selectedActiveQuoteRows.value.length} 条`,
      created_by: resolvedOperatorName.value,
    })
    await Promise.all([loadSupplierSettlements(), loadSupplierQuoteActions()])
    ElMessage.success('已从已选报价生成结算单')
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    ElMessage.error('生成结算单失败，请稍后重试')
  } finally {
    settlementSaving.value = null
  }
}

async function updateSettlementPayment(item: SupplierSettlementItem) {
  settlementSaving.value = item.id
  try {
    await updateSupplierSettlement(item.id, {
      paid_amount: Number(item.paid_amount || 0),
      payment_date: item.payment_date || undefined,
      remarks: item.remarks || undefined,
      operator_name: resolvedOperatorName.value,
    })
    await Promise.all([loadSupplierSettlements(), loadSupplierQuoteActions()])
    ElMessage.success('结算单付款进度已更新')
  } catch {
    ElMessage.error('结算单更新失败，请稍后重试')
  } finally {
    settlementSaving.value = null
  }
}

async function openSettlementDetail(item: SupplierSettlementItem) {
  try {
    activeSettlementDetail.value = await fetchSupplierSettlementDetail(item.id)
    settlementDetailVisible.value = true
  } catch {
    ElMessage.error('结算单详情加载失败，请稍后重试')
  }
}

async function cancelSettlement(item: SupplierSettlementItem) {
  settlementSaving.value = item.id
  try {
    const { value } = await ElMessageBox.prompt(
      `确认作废结算单「${item.settlement_title}」吗？作废后会保留在台账与日志中。`,
      '作废结算单',
      {
        confirmButtonText: '确认作废',
        cancelButtonText: '取消',
        inputPlaceholder: '可选填写作废原因',
        inputValue: '',
      },
    )
    await cancelSupplierSettlement(item.id, {
      operator_name: resolvedOperatorName.value,
      cancel_reason: String(value || '').trim() || undefined,
    })
    await Promise.all([loadSupplierSettlements(), loadSupplierQuoteActions()])
    ElMessage.success('结算单已作废')
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    ElMessage.error('结算单作废失败，请稍后重试')
  } finally {
    settlementSaving.value = null
  }
}

function buildSettlementExportRows(rows: SupplierSettlementItem[]) {
  return rows.map((item) => ({
    结算单标题: item.settlement_title,
    供应商: item.supplier_name,
    账期: formatSettlementPeriod(item),
    报价条数: item.record_count,
    总金额: item.total_amount,
    已付金额: item.paid_amount,
    未付金额: item.pending_amount,
    付款状态: getSettlementStatusLabel(item.status),
    应付日期: item.payment_due_date || '',
    付款日期: item.payment_date || '',
    创建人: item.created_by || '',
    备注: item.remarks || '',
  }))
}

async function logSettlementExport(format: 'xlsx' | 'csv', rowCount: number, fileName: string) {
  if (!selectedSupplierId.value) return
  const [startDate, endDate] = settlementDateRange.value
  try {
    await createSupplierQuoteAction(selectedSupplierId.value, {
      action_type: 'export_settlements',
      action_reason: `导出当前筛选的${rowCount}条结算台账`,
      operator_name: resolvedOperatorName.value,
      action_payload: {
        format,
        scope: 'filtered',
        row_count: rowCount,
        file_name: fileName,
        status_filter: settlementStatusFilter.value,
        keyword: settlementKeyword.value.trim() || undefined,
        start_period_start: startDate || undefined,
        end_period_end: endDate || undefined,
      },
    })
    await loadSupplierQuoteActions()
  } catch {
    // Export should not fail because logging is unavailable.
  }
}

async function exportSettlementRows(format: 'xlsx' | 'csv') {
  if (!settlementRows.value.length) {
    ElMessage.warning('当前没有可导出的结算台账')
    return
  }
  const exportRows = buildSettlementExportRows(settlementRows.value)
  const exportPrefix = slugifyExportValue(selectedSupplier.value?.supplier_name || 'supplier-settlements')
  const fileSuffix = `${exportPrefix}-settlements-${formatDateOnly(new Date())}`
  const fileName = `${fileSuffix}.${format}`

  try {
    if (format === 'xlsx') {
      const xlsx = await import('xlsx')
      const worksheet = xlsx.utils.json_to_sheet(exportRows)
      const workbook = xlsx.utils.book_new()
      xlsx.utils.book_append_sheet(workbook, worksheet, '结算台账')
      xlsx.writeFile(workbook, fileName)
    } else {
      const headers = Object.keys(exportRows[0] || {})
      const lines = [
        headers.join(','),
        ...exportRows.map((row) =>
          headers
            .map((header) => `"${String(row[header as keyof typeof row] ?? '').replaceAll('"', '""')}"`)
            .join(','),
        ),
      ]
      const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = fileName
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)
      URL.revokeObjectURL(url)
    }
    await logSettlementExport(format, exportRows.length, fileName)
    ElMessage.success(`已导出当前筛选的${exportRows.length}条结算台账`)
  } catch {
    ElMessage.error('结算台账导出失败，请稍后重试')
  }
}

async function loadSuppliers() {
  if (!hasBackendAuthSession.value) {
    suppliers.value = []
    selectedSupplierId.value = null
    return
  }
  const response = await fetchSuppliers(false)
  suppliers.value = response.items ?? []
  writeRecentSupplierIds(recentSupplierIds.value.filter((id) => suppliers.value.some((item) => item.id === id)))
  if (isSupplierSession.value && currentSupplierScopeId.value) {
    selectedSupplierId.value = currentSupplierScopeId.value
    return
  }
  const hasSelected = suppliers.value.some((item) => item.id === selectedSupplierId.value)
  if (!hasSelected) {
    const rememberedId = readLastSelectedSupplierId()
    const preferredId = rememberedId != null && suppliers.value.some((item) => item.id === rememberedId)
      ? rememberedId
      : recentSupplierIds.value.find((id) => suppliers.value.some((item) => item.id === id)) ?? null
    selectedSupplierId.value = preferredId ?? suppliers.value[0]?.id ?? null
  }
}

async function loadOverview() {
  if (!hasBackendAuthSession.value) {
    overview.value = null
    return
  }
  overview.value = await fetchSupplierOverview(12)
}

async function loadSupplierQuotes() {
  if (!hasBackendAuthSession.value) {
    selectedSupplierQuoteRows.value = []
    quoteTotal.value = 0
    quoteHasMore.value = false
    return
  }
  if (!selectedSupplierId.value) {
    selectedSupplierQuoteRows.value = []
    quoteTotal.value = 0
    quoteHasMore.value = false
    return
  }
  const response = await fetchSupplierQuotesBySupplier(selectedSupplierId.value, buildSupplierQuoteQueryOptions())
  selectedSupplierQuoteRows.value = response.items ?? []
  quoteTotal.value = Number(response.total || 0)
  quoteHasMore.value = Boolean(response.has_more)
}

async function loadSupplierQuoteActions() {
  if (!hasBackendAuthSession.value) {
    quoteActionLogs.value = []
    quoteActionTotal.value = 0
    quoteActionHasMore.value = false
    return
  }
  if (isSupplierSession.value) {
    quoteActionLogs.value = []
    quoteActionTotal.value = 0
    quoteActionHasMore.value = false
    return
  }
  if (!selectedSupplierId.value) {
    quoteActionLogs.value = []
    quoteActionTotal.value = 0
    quoteActionHasMore.value = false
    return
  }
  const response = await fetchSupplierQuoteActions(selectedSupplierId.value, buildSupplierQuoteActionQueryOptions())
  quoteActionLogs.value = response.items ?? []
  quoteActionTotal.value = Number(response.total || 0)
  quoteActionHasMore.value = Boolean(response.has_more)
}

async function loadSupplierSettlements() {
  if (!hasBackendAuthSession.value) {
    settlementRows.value = []
    settlementTotal.value = 0
    settlementHasMore.value = false
    return
  }
  if (!selectedSupplierId.value) {
    settlementRows.value = []
    settlementTotal.value = 0
    settlementHasMore.value = false
    return
  }
  settlementLoading.value = true
  try {
    const response = await fetchSupplierSettlementsBySupplier(selectedSupplierId.value, buildSupplierSettlementQueryOptions())
    settlementRows.value = response.items ?? []
    settlementTotal.value = Number(response.total || 0)
    settlementHasMore.value = Boolean(response.has_more)
  } finally {
    settlementLoading.value = false
  }
}

async function changeQuotePage(direction: 'prev' | 'next') {
  if (direction === 'prev') {
    quotePageOffset.value = Math.max(quotePageOffset.value - quotePageSize.value, 0)
  } else if (quoteHasMore.value) {
    quotePageOffset.value += quotePageSize.value
  }
  clearSelectedQuotes()
  await loadSupplierQuotes()
}

async function changeQuoteActionPage(direction: 'prev' | 'next') {
  if (direction === 'prev') {
    quoteActionOffset.value = Math.max(quoteActionOffset.value - quoteActionPageSize.value, 0)
  } else if (quoteActionHasMore.value) {
    quoteActionOffset.value += quoteActionPageSize.value
  }
  await loadSupplierQuoteActions()
}

async function changeSettlementPage(direction: 'prev' | 'next') {
  if (direction === 'prev') {
    settlementOffset.value = Math.max(settlementOffset.value - settlementPageSize.value, 0)
  } else if (settlementHasMore.value) {
    settlementOffset.value += settlementPageSize.value
  }
  await loadSupplierSettlements()
}

async function resetQuotePaginationAndReload() {
  quotePageOffset.value = 0
  clearSelectedQuotes()
  await loadSupplierQuotes()
}

async function resetQuoteActionPaginationAndReload() {
  quoteActionOffset.value = 0
  await loadSupplierQuoteActions()
}

async function resetSettlementPaginationAndReload() {
  settlementOffset.value = 0
  await loadSupplierSettlements()
}

async function loadProductCompare() {
  if (!hasBackendAuthSession.value) {
    productCompare.value = null
    return
  }
  if (!selectedProductKey.value) {
    productCompare.value = null
    return
  }
  productCompare.value = await fetchProductSupplierQuotes(selectedProductKey.value)
}

function fillSupplierForm(item: SupplierItem | null) {
  if (!item) {
    resetSupplierForm()
    return
  }
  supplierForm.supplier_name = item.supplier_name || ''
  supplierForm.contact_name = item.contact_name || ''
  supplierForm.contact_phone = item.contact_phone || ''
  supplierForm.market_scope = item.market_scope || '本地市场'
  supplierForm.market_category = item.market_category || ''
  supplierForm.channel = item.channel || '微信小程序'
  supplierForm.notes = item.notes || ''
  supplierForm.is_active = Boolean(item.is_active)
  supplierAccountOriginalUsername.value = item.account_username || ''
  supplierAccountForm.account_username = getSupplierAccountFormUsername(item)
  supplierAccountForm.account_password = ''
  supplierAccountForm.account_display_name = item.account_display_name || item.contact_name || item.supplier_name || ''
  supplierAccountForm.account_is_active = item.account_is_active == null ? true : Boolean(item.account_is_active)
}

async function reloadAll() {
  if (!hasBackendAuthSession.value) {
    return
  }
  loading.value = true
  try {
    await Promise.all([loadSuppliers(), loadOverview(), loadProductCompare()])
    fillSupplierForm(selectedSupplier.value)
    loadCurrentQuoteDraft()
    await Promise.all([loadSupplierQuotes(), loadSupplierQuoteActions(), loadSupplierSettlements()])
  } catch (error) {
    const status = Number((error as { response?: { status?: number } }).response?.status || 0)
    if (status === 401 || status === 403) {
      ElMessage.warning('当前账号未登录或登录已失效，请先重新登录')
      return
    }
    ElMessage.error('本次同步未成功，已保留当前可用内容；请稍后重试，或联系管理员检查后端服务')
  } finally {
    loading.value = false
  }
}

function ensureCommandSupplierSelection() {
  if (selectedSupplier.value) {
    return true
  }
  if (!filteredSuppliers.value.length) {
    return false
  }
  const preferred = filteredSuppliers.value.find((item) => item.is_active) || filteredSuppliers.value[0]
  if (preferred) {
    selectSupplier(preferred.id)
    return true
  }
  return false
}

function focusQuotePriceInput() {
  nextTick(() => {
    quotePriceInputRef.value?.focus?.()
  })
}

function openSupplierCreateFromCommand() {
  mobileSupplierTask.value = 'suppliers'
  desktopSupplierWorkbenchTab.value = 'supplier'
  emit('navigate-section', 'suppliers')
  resetSupplierForm()
}

function selectFirstSupplierForWorkspace() {
  const preferredSupplier = filteredSuppliers.value[0] || suppliers.value[0]
  if (!preferredSupplier) {
    ElMessage.warning('当前还没有供应商，请先创建供应商')
    emit('navigate-section', 'suppliers')
    resetSupplierForm()
    return
  }
  selectSupplier(preferredSupplier.id)
}

function openQuoteFromCommand(): boolean {
  if (!ensureCommandSupplierSelection() && isAdminSession.value) {
    ElMessage.warning('请先新建供应商')
    emit('navigate-section', 'suppliers')
    resetSupplierForm()
    return false
  }
  mobileSupplierTask.value = 'quote'
  desktopSupplierWorkbenchTab.value = 'quote'
  emit('navigate-section', 'quote')
  focusQuotePriceInput()
  return true
}

function openQuoteImportFromCommand() {
  if (!openQuoteFromCommand()) return
  openQuoteImportDialog()
}

function openSettlementFromCommand() {
  if (!ensureCommandSupplierSelection()) {
    ElMessage.warning('请先选择供应商')
    emit('navigate-section', 'suppliers')
    return
  }
  mobileSupplierTask.value = 'settlement'
  desktopSupplierInsightTab.value = 'settlement'
  emit('navigate-section', 'settlement')
  openSettlementCreateForm()
}

function goQuoteHistoryForSettlement() {
  if (!ensureCommandSupplierSelection()) {
    ElMessage.warning('请先选择供应商')
    emit('navigate-section', 'suppliers')
    return
  }
  mobileSupplierTask.value = 'history'
  desktopSupplierWorkbenchTab.value = 'quote'
  desktopSupplierInsightTab.value = 'history'
  quoteStatusFilter.value = 'active'
  emit('navigate-section', 'quote')
}

function navigateSupplierCommandSection(section: 'suppliers' | 'quote' | 'settlement' | 'logs') {
  if (section === 'quote') {
    openQuoteFromCommand()
    return
  }
  if (section === 'settlement') {
    ensureCommandSupplierSelection()
    mobileSupplierTask.value = 'settlement'
    desktopSupplierInsightTab.value = 'settlement'
  }
  if (section === 'logs') {
    ensureCommandSupplierSelection()
    desktopSupplierInsightTab.value = 'logs'
  }
  if (section === 'suppliers') {
    mobileSupplierTask.value = 'suppliers'
    desktopSupplierWorkbenchTab.value = selectedSupplier.value ? 'supplier' : desktopSupplierWorkbenchTab.value
  }
  emit('navigate-section', section)
}

function copyLatestQuoteFromCommand() {
  const latest = selectedSupplierQuoteRows.value.find((item) => getQuoteRecordId(item) === latestActiveQuoteRecordId.value)
  if (!latest) {
    ElMessage.warning('当前供应商没有可复制的有效报价')
    return
  }
  copyQuoteAsNew(latest)
  emit('navigate-section', 'quote')
  mobileSupplierTask.value = 'quote'
  desktopSupplierWorkbenchTab.value = 'quote'
  focusQuotePriceInput()
}

function selectSupplier(id: number) {
  if (isSupplierSession.value) return
  selectedSupplierId.value = id
  if (props.mobile) {
    mobileSupplierTask.value = 'quote'
  } else {
    desktopSupplierWorkbenchTab.value = isProcurementSupplierManagement.value || isSupplierWorkspace.value ? 'supplier' : 'quote'
    if (isProcurementSupplierManagement.value) {
      desktopSupplierInsightTab.value = 'overview'
    }
  }
}

async function runMobilePrimaryAction() {
  if (mobilePrimaryActionDisabled.value) return
  if (mobilePrimaryAction.value === 'create_supplier') {
    resetSupplierForm()
    return
  }
  if (mobilePrimaryAction.value === 'save_quote') {
    await saveQuote()
    return
  }
  if (mobilePrimaryAction.value === 'open_quote') {
    mobileSupplierTask.value = 'quote'
    return
  }
  if (mobilePrimaryAction.value === 'open_settlement_create') {
    openSettlementCreateForm()
    return
  }
  if (mobilePrimaryAction.value === 'build_settlement') {
    await buildSettlementFromSelectedQuotes()
    return
  }
  mobileSupplierTask.value = isSupplierSession.value ? 'quote' : 'suppliers'
}

function runMobileSecondaryAction() {
  if (mobileSecondaryActionDisabled.value) return
  if (mobileSupplierTask.value === 'suppliers') {
    mobileSupplierTask.value = 'history'
    return
  }
  if (mobileSupplierTask.value === 'quote') {
    if (selectedSupplier.value) {
      mobileSupplierTask.value = 'history'
      return
    }
    resetSupplierForm()
    return
  }
  if (mobileSupplierTask.value === 'history') {
    mobileSupplierTask.value = 'settlement'
    return
  }
  mobileSupplierTask.value = isSupplierSession.value ? 'quote' : 'suppliers'
}

function showMobileSupplierTask(task: MobileSupplierTask) {
  return !props.mobile || effectiveMobileSupplierTask.value === task
}

function showAnyMobileSupplierTask(tasks: MobileSupplierTask[]) {
  return !props.mobile || tasks.includes(effectiveMobileSupplierTask.value)
}

function showSupplierInsightPanel(panel: DesktopSupplierInsightTab) {
  if (resolvedBackendSection.value === 'suppliers') return false
  if (resolvedBackendSection.value === 'quote') return panel === 'history'
  if (resolvedBackendSection.value === 'settlement') return panel === 'settlement'
  if (resolvedBackendSection.value === 'logs') return panel === 'logs'
  return props.mobile || desktopSupplierInsightTab.value === panel
}

function showSupplierWorkbenchPanel(panel: DesktopSupplierWorkbenchTab) {
  if (isProcurementSupplierManagement.value) return panel === 'supplier'
  if (resolvedBackendSection.value === 'suppliers') return panel === 'supplier'
  if (resolvedBackendSection.value === 'quote') return panel === 'quote'
  if (resolvedBackendSection.value === 'settlement' || resolvedBackendSection.value === 'logs') return false
  if (props.mobile || !isAdminSession.value) {
    return true
  }
  return desktopSupplierWorkbenchTab.value === panel
}

async function saveSupplier() {
  if (!isAdminSession.value) {
    ElMessage.warning('当前账号只能录入自己的报价，不能维护供应商管理')
    return
  }
  if (!supplierForm.supplier_name.trim()) {
    ElMessage.warning('请填写供应商名称')
    return
  }
  if (!validateSupplierAccountFormBeforeSave()) {
    return
  }
  supplierSaving.value = true
  try {
    const payload = {
      supplier_name: supplierForm.supplier_name.trim(),
      contact_name: supplierForm.contact_name.trim() || undefined,
      contact_phone: supplierForm.contact_phone.trim() || undefined,
      market_scope: supplierForm.market_scope.trim() || undefined,
      market_category: supplierForm.market_category.trim() || undefined,
      channel: supplierForm.channel.trim() || undefined,
      notes: supplierForm.notes.trim() || undefined,
      is_active: supplierForm.is_active,
      account_username: normalizeSupplierAccountUsernameForSave(),
      account_password: supplierAccountForm.account_password.trim() || undefined,
      account_display_name: supplierAccountForm.account_display_name.trim() || undefined,
      account_is_active: supplierAccountForm.account_is_active,
    }

    if (!selectedSupplierId.value) {
      const created = await createSupplier(payload)
      selectedSupplierId.value = created.id
      ElMessage.success('供应商已创建')
    } else {
      await updateSupplier(selectedSupplierId.value, payload)
      ElMessage.success('供应商资料已更新')
    }
    await reloadAll()
  } catch {
    ElMessage.error('供应商保存失败，请稍后重试')
  } finally {
    supplierSaving.value = false
  }
}

async function saveQuote() {
  if (!selectedSupplier.value) {
    ElMessage.warning('请先选择或创建供应商')
    return
  }
  if (!selectedProductKey.value) {
    ElMessage.warning('请先选择商品')
    return
  }
  if (!selectedSupplier.value.is_active) {
    ElMessage.warning('该供应商已停用，请先启用后再录价')
    return
  }
  if (quoteForm.quote_price == null || Number(quoteForm.quote_price) <= 0) {
    ElMessage.warning('请填写有效报价')
    return
  }

  const payload: SupplierQuoteCreatePayload = {
    price_identity_key: selectedProductKey.value,
    source_record_id: quoteForm.source_record_id,
    supplier_id: selectedSupplier.value.id,
    supplier_name: selectedSupplier.value.supplier_name,
    contact_name: selectedSupplier.value.contact_name || undefined,
    market_scope: selectedSupplier.value.market_scope || '本地市场',
    market_category: selectedSupplier.value.market_category || undefined,
    channel: selectedSupplier.value.channel || undefined,
    product_name: selectedProductLabelResolved.value || undefined,
    price_identity_label: selectedProductLabelResolved.value || undefined,
    quote_price: Number(quoteForm.quote_price),
    quote_unit: quoteForm.quote_unit || undefined,
    box_price: quoteForm.box_price == null ? undefined : Number(quoteForm.box_price),
    tax_price: quoteForm.tax_price == null ? undefined : Number(quoteForm.tax_price),
    inventory_status: quoteForm.inventory_status || undefined,
    remarks: quoteForm.remarks || undefined,
    quoted_by: resolvedOperatorName.value || undefined,
  }

  quoteSaving.value = true
  try {
    await submitSupplierQuote(payload)
    clearCurrentQuoteDraft(true)
    ElMessage.success('报价已录入并同步到前台对比')
    resetQuoteForm()
    await reloadAll()
  } catch {
    ElMessage.error('报价提交失败，请稍后重试')
  } finally {
    quoteSaving.value = false
  }
}

function openQuoteImportDialog() {
  if (!selectedSupplier.value) {
    ElMessage.warning('请先选择供应商')
    return
  }
  if (!selectedSupplier.value.is_active) {
    ElMessage.warning('该供应商已停用，请先启用后再导入')
    return
  }
  if (!props.productOptions.length) {
    ElMessage.warning('当前没有可匹配的商品对比键，请先同步商品')
    return
  }
  if (quoteImporting.value) {
    return
  }
  if (quoteImportInputRef.value) {
    quoteImportInputRef.value.value = ''
    quoteImportInputRef.value.click()
  }
}

async function downloadQuoteImportTemplate() {
  if (!selectedSupplier.value) {
    ElMessage.warning('请先选择供应商')
    return
  }

  try {
    const xlsx = await import('xlsx')
    const sampleProduct = selectedProductOption.value
    const today = new Date()
    const worksheet = xlsx.utils.json_to_sheet([
      {
        对比键: sampleProduct?.price_identity_key || '',
        商品: sampleProduct?.price_identity_label || '',
        报价: '',
        单位: quoteForm.quote_unit || '斤',
        箱价: '',
        含税价: '',
        库存状态: quoteForm.inventory_status || '现货',
        备注: '',
        报价时间: `${formatDateOnly(today)} 06:00`,
        渠道: selectedSupplier.value.channel || '微信小程序',
        分类: selectedSupplier.value.market_category || '',
        市场范围: selectedSupplier.value.market_scope || '本地市场',
      },
    ])
    const workbook = xlsx.utils.book_new()
    xlsx.utils.book_append_sheet(workbook, worksheet, '报价导入模板')
    xlsx.writeFile(
      workbook,
      `${slugifyExportValue(selectedSupplier.value.supplier_name)}-报价导入模板-${formatDateOnly(today)}.xlsx`,
    )
  } catch {
    ElMessage.error('导入模板生成失败，请稍后重试')
  }
}

function buildImportedQuotePayload(
  supplier: SupplierItem,
  draft: ImportedSupplierQuoteDraft,
  matchedProduct: MatchedImportedProduct,
): SupplierQuoteCreatePayload | null {
  const quotePrice = parseImportedNumber(draft.quote_price)
  if (quotePrice == null || quotePrice <= 0) {
    return null
  }

  return {
    supplier_id: supplier.id,
    supplier_name: supplier.supplier_name,
    contact_name: supplier.contact_name || undefined,
    contact_phone: supplier.contact_phone || undefined,
    market_scope: normalizeOptionalText(draft.market_scope) || supplier.market_scope || '本地市场',
    market_category: normalizeOptionalText(draft.market_category) || supplier.market_category || undefined,
    channel: normalizeOptionalText(draft.channel) || supplier.channel || undefined,
    price_identity_key: matchedProduct.price_identity_key,
    price_identity_label: matchedProduct.price_identity_label,
    product_name: matchedProduct.product_name,
    quote_price: quotePrice,
    quote_unit: normalizeOptionalText(draft.quote_unit) || quoteForm.quote_unit || '斤',
    box_price: parseImportedNumber(draft.box_price),
    tax_price: parseImportedNumber(draft.tax_price),
    inventory_status: normalizeOptionalText(draft.inventory_status) || quoteForm.inventory_status || undefined,
    remarks: normalizeOptionalText(draft.remarks),
    quoted_at: normalizeImportedQuotedAt(draft.quoted_at),
    quoted_by: resolvedOperatorName.value || undefined,
  }
}

function buildQuoteImportPreviewRows(drafts: ImportedSupplierQuoteDraft[]) {
  return drafts.map((draft) => {
    const matchedProduct = matchImportedProduct(draft)
    const baseRow: QuoteImportPreviewRow = {
      row_number: draft.row_number,
      price_identity_key: draft.price_identity_key || '',
      product_name: draft.product_name || '',
      quote_price: draft.quote_price || '',
      quote_unit: draft.quote_unit || quoteForm.quote_unit || '斤',
      matched_product_label: matchedProduct?.price_identity_label || '',
      status: 'error',
      reason: '',
      draft,
    }

    if (!matchedProduct) {
      return {
        ...baseRow,
        status: 'error',
        reason: '未匹配到商品或对比键',
      } satisfies QuoteImportPreviewRow
    }

    if (!selectedSupplier.value) {
      return {
        ...baseRow,
        matched_product_label: matchedProduct.price_identity_label,
        status: 'error',
        reason: '未选择供应商',
      } satisfies QuoteImportPreviewRow
    }

    const payload = buildImportedQuotePayload(selectedSupplier.value, draft, matchedProduct)
    if (!payload) {
      return {
        ...baseRow,
        matched_product_label: matchedProduct.price_identity_label,
        status: 'error',
        reason: '报价为空或格式不正确',
      } satisfies QuoteImportPreviewRow
    }

    return {
      ...baseRow,
      matched_product_label: matchedProduct.price_identity_label,
      status: 'ready',
      reason: '',
      payload,
    } satisfies QuoteImportPreviewRow
  })
}

async function exportQuoteImportFailureRows(rows: QuoteImportPreviewRow[], sourceFileName: string) {
  if (!rows.length) {
    ElMessage.warning('当前没有可导出的失败行')
    return
  }

  try {
    const xlsx = await import('xlsx')
    const worksheet = xlsx.utils.json_to_sheet(
      rows.map((item) => ({
        行号: item.row_number,
        对比键: item.draft.price_identity_key || '',
        商品: item.draft.product_name || '',
        报价: item.draft.quote_price || '',
        单位: item.draft.quote_unit || '',
        箱价: item.draft.box_price || '',
        含税价: item.draft.tax_price || '',
        库存状态: item.draft.inventory_status || '',
        备注: item.draft.remarks || '',
        报价时间: item.draft.quoted_at || '',
        渠道: item.draft.channel || '',
        分类: item.draft.market_category || '',
        失败原因: item.reason || '导入失败',
      })),
    )
    const workbook = xlsx.utils.book_new()
    xlsx.utils.book_append_sheet(workbook, worksheet, '待修正报价行')
    const fileBaseName = slugifyExportValue(sourceFileName.replace(/\.[^.]+$/, ''))
    xlsx.writeFile(workbook, `${fileBaseName}-待修正报价行-${formatDateOnly(new Date())}.xlsx`)
  } catch {
    ElMessage.error('失败行导出失败，请稍后重试')
  }
}

function buildQuoteImportRequestItem(row: QuoteImportPreviewRow): SupplierQuoteImportItemPayload {
  if (row.status === 'ready' && row.payload) {
    return {
      row_number: row.row_number,
      price_identity_key: row.payload.price_identity_key,
      price_identity_label: row.payload.price_identity_label,
      product_name: row.payload.product_name,
      category: row.payload.category,
      spec_text: row.payload.spec_text,
      market_scope: row.payload.market_scope,
      market_category: row.payload.market_category,
      channel: row.payload.channel,
      quote_price: row.payload.quote_price,
      quote_unit: row.payload.quote_unit,
      box_price: row.payload.box_price,
      tax_price: row.payload.tax_price,
      inventory_status: row.payload.inventory_status,
      remarks: row.payload.remarks,
      quoted_at: row.payload.quoted_at,
      quoted_by: row.payload.quoted_by,
    }
  }

  return {
    row_number: row.row_number,
    price_identity_key: row.draft.price_identity_key,
    price_identity_label: row.matched_product_label || undefined,
    product_name: row.draft.product_name,
    market_scope: row.draft.market_scope,
    market_category: row.draft.market_category,
    channel: row.draft.channel,
    quote_price: parseImportedNumber(row.draft.quote_price),
    quote_unit: row.draft.quote_unit,
    box_price: parseImportedNumber(row.draft.box_price),
    tax_price: parseImportedNumber(row.draft.tax_price),
    inventory_status: row.draft.inventory_status,
    remarks: row.draft.remarks,
    quoted_at: normalizeImportedQuotedAt(row.draft.quoted_at),
    quoted_by: resolvedOperatorName.value || undefined,
  }
}

function buildFailurePreviewRowsFromImportResult(
  sourceRows: QuoteImportPreviewRow[],
  resultItems: SupplierQuoteImportResultItem[],
) {
  const previewRowMap = new Map(sourceRows.map((item) => [item.row_number, item] as const))
  return resultItems
    .filter((item) => item.status === 'failed')
    .map((item) => {
      const sourceRow = previewRowMap.get(item.row_number)
      return {
        ...(sourceRow || {
          row_number: item.row_number,
          price_identity_key: item.price_identity_key || '',
          product_name: item.product_name || '',
          quote_price: '',
          quote_unit: '',
          matched_product_label: item.price_identity_label || '',
          status: 'error' as const,
          reason: item.failure_reason || '导入失败',
          draft: { row_number: item.row_number },
        }),
        matched_product_label: item.price_identity_label || sourceRow?.matched_product_label || '',
        status: 'error' as const,
        reason: item.failure_reason || sourceRow?.reason || '导入失败',
      } satisfies QuoteImportPreviewRow
    })
}

function buildImportBatchOperationRows(
  sourceRows: QuoteImportPreviewRow[],
  resultItems: SupplierQuoteImportResultItem[],
) {
  const previewRowMap = new Map(sourceRows.map((item) => [item.row_number, item] as const))
  return resultItems.map((item) => {
    const sourceRow = previewRowMap.get(item.row_number)
    const statusLabel = item.status === 'success' ? '成功' : item.status === 'skipped' ? '跳过' : '失败'
    return {
      行号: item.row_number,
      状态: statusLabel,
      商品: item.product_name || sourceRow?.product_name || sourceRow?.matched_product_label || '',
      对比键: item.price_identity_key || sourceRow?.price_identity_key || '',
      报价: sourceRow?.quote_price || '',
      导入模式: getQuoteImportModeLabel(quoteImportMode.value),
      说明: item.failure_reason || item.abnormal_change_hint || sourceRow?.preview_reason || '',
      诊断: sourceRow ? getQuoteImportPreviewDecisionLabel(sourceRow) : '',
      当前有效报价: sourceRow ? getQuoteImportPreviewExistingLabel(sourceRow) : '',
      当前有效报价说明: sourceRow ? getQuoteImportPreviewExistingMeta(sourceRow) : '',
      异常波动: item.abnormal_change_ratio != null ? formatPercent(item.abnormal_change_ratio) : '',
      记录ID: item.record_id != null ? `#${item.record_id}` : '',
    } satisfies BatchOperationExportRow
  })
}

/**
 * Submit parsed rows through the backend batch import API so validation,
 * persistence and action logging stay consistent with the server response.
 *
 * Args:
 *   fileName: Uploaded source filename.
  *   previewRows: Parsed and previewed import rows.
 */
async function importQuoteRows(fileName: string, previewRows: QuoteImportPreviewRow[]) {
  if (!selectedSupplier.value) {
    ElMessage.warning('请先选择供应商')
    return
  }

  const payload: SupplierQuoteImportPayload = {
    supplier_id: selectedSupplier.value.id,
    operator_name: resolvedOperatorName.value,
    file_name: fileName,
    import_mode: quoteImportMode.value,
    ...buildQuoteImportRulePayload(),
    items: previewRows.map((item) => buildQuoteImportRequestItem(item)),
  }
  const response = await importSupplierQuotes(payload)
  await reloadAll()
  const failureRows = buildFailurePreviewRowsFromImportResult(previewRows, response.items)
  setLastBatchOperationResult(
    'import',
    '最近一批导入结果',
    buildImportBatchOperationRows(previewRows, response.items),
  )
  lastQuoteImportFailureRows.value = failureRows
  const successCount = Number(response.success_count || 0)
  const failedCount = Number(response.failed_count || 0)
  const skippedCount = Number(response.skipped_count || 0)

  if (!successCount) {
    if (skippedCount && !failedCount) {
      ElMessage.warning(`没有新增报价，${skippedCount} 条在“${getQuoteImportModeLabel(quoteImportMode.value)}”模式下被跳过`)
      return
    }
    const firstFailure = response.items.find((item) => item.status === 'failed')
    ElMessage.error(`导入失败，${firstFailure?.failure_reason || '没有可用的报价数据'}`)
    return
  }

  if (failedCount) {
    await ElMessageBox.alert(
      failureRows
        .slice(0, 10)
        .map((item) => `第 ${item.row_number} 行：${item.reason || '导入失败'}`)
        .join('<br/>'),
      '部分报价导入失败',
      {
        confirmButtonText: '知道了',
        dangerouslyUseHTMLString: true,
      },
    )
    const summary = [`已导入 ${successCount} 条`]
    if (skippedCount) {
      summary.push(`跳过 ${skippedCount} 条`)
    }
    summary.push(`失败 ${failedCount} 条`)
    ElMessage.warning(summary.join('，'))
    return
  }

  if (skippedCount) {
    ElMessage.success(`已导入 ${successCount} 条，另有 ${skippedCount} 条被跳过`)
    return
  }

  ElMessage.success(`已批量导入 ${successCount} 条报价`)
}

function closeQuoteImportPreview() {
  quoteImportPreviewVisible.value = false
}

async function downloadQuoteImportPreviewFailures() {
  await exportQuoteImportFailureRows(quoteImportPreviewRows.value.filter((item) => item.status === 'error'), quoteImportPreviewFileName.value || 'quote-import')
}

async function confirmQuoteImport() {
  if (!quoteImportPreviewRows.value.length) {
    ElMessage.warning('没有可导入的报价预览数据')
    return
  }

  quoteImporting.value = true
  try {
    await importQuoteRows(
      quoteImportPreviewFileName.value || 'quote-import',
      quoteImportPreviewRows.value,
    )
    quoteImportPreviewVisible.value = false
  } finally {
    quoteImporting.value = false
  }
}

async function downloadLastQuoteImportFailures() {
  await exportQuoteImportFailureRows(lastQuoteImportFailureRows.value, quoteImportPreviewFileName.value || 'quote-import')
}

async function handleQuoteImportFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  try {
    if (!selectedSupplier.value) {
      ElMessage.warning('请先选择供应商')
      return
    }
    if (!selectedSupplier.value.is_active) {
      ElMessage.warning('该供应商已停用，请先启用后再导入')
      return
    }

    const rawRows = await parseQuoteImportFile(file)
    const drafts = parseQuoteImportRows(rawRows)
    if (!drafts.length) {
      ElMessage.warning('文件中没有识别到可导入的报价行')
      return
    }
    quoteImportPreviewFileName.value = file.name
    const previewRows = buildQuoteImportPreviewRows(drafts)
    quoteImportPreviewRows.value = await enrichQuoteImportPreviewRows(previewRows)
    quoteImportPreviewVisible.value = true
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '报价导入失败，请稍后重试')
  } finally {
    input.value = ''
  }
}

function copyQuoteAsNew(item: SupplierQuoteItem) {
  fillQuoteFormFromHistory(item)
  quoteForm.remarks = buildHistoryRemark(item)
  ElMessage.success('历史报价已回填到录价表单，请确认后重新提交')
}

async function copySelectedQuotesAsNew() {
  if (!selectedQuoteRows.value.length) {
    ElMessage.warning('请先选择要复制的历史报价')
    return
  }

  try {
    await ElMessageBox.confirm(
      `将选中的 ${selectedQuoteRows.value.length} 条历史报价直接复制成新的报价记录，原记录会保留不变。是否继续？`,
      '批量复制为新报价',
      {
        confirmButtonText: '开始复制',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    batchActionLoading.value = 'copy'
    let successCount = 0
    let skippedCount = 0
    let failedCount = 0
    const resultRows: BatchOperationExportRow[] = []
    for (const item of selectedQuoteRows.value) {
      const payload = buildQuotePayloadFromHistory(item)
      if (!payload) {
        skippedCount += 1
        resultRows.push({
          状态: '跳过',
          商品: item.product_name || item.price_identity_label || item.price_identity_key,
          对比键: item.price_identity_key,
          来源记录: item.record_id != null ? `#${item.record_id}` : '',
          新记录: '',
          说明: '字段不完整，无法复制为新报价',
        })
        continue
      }
      try {
        const response = await submitSupplierQuote(payload)
        successCount += 1
        resultRows.push({
          状态: '成功',
          商品: payload.product_name || payload.price_identity_label || payload.price_identity_key,
          对比键: payload.price_identity_key,
          来源记录: item.record_id != null ? `#${item.record_id}` : '',
          新记录: response.item.record_id != null ? `#${response.item.record_id}` : '',
          说明: '已复制为新报价',
        })
      } catch {
        failedCount += 1
        resultRows.push({
          状态: '失败',
          商品: payload.product_name || payload.price_identity_label || payload.price_identity_key,
          对比键: payload.price_identity_key,
          来源记录: item.record_id != null ? `#${item.record_id}` : '',
          新记录: '',
          说明: '请求失败，请稍后重试',
        })
      }
    }
    if (resultRows.length) {
      setLastBatchOperationResult('copy', '最近一批复制结果', resultRows)
    }
    clearSelectedQuotes()
    if (successCount) {
      await reloadAll()
    }
    if (successCount && (skippedCount || failedCount)) {
      ElMessage.warning(`已复制 ${successCount} 条，跳过 ${skippedCount} 条，失败 ${failedCount} 条`)
      return
    }
    if (successCount) {
      ElMessage.success(`已批量复制 ${successCount} 条新报价`)
      return
    }
    if (failedCount) {
      ElMessage.error(`复制失败 ${failedCount} 条，请稍后重试`)
      return
    }
    ElMessage.warning('没有可复制的有效报价记录')
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    ElMessage.error('批量复制失败，请稍后重试')
  } finally {
    batchActionLoading.value = null
  }
}

async function logQuoteExport(
  format: 'xlsx' | 'csv',
  rowCount: number,
  scope: 'filtered' | 'selected',
  scopeLabel: string,
) {
  if (!selectedSupplierId.value) return
  try {
    await createSupplierQuoteAction(selectedSupplierId.value, {
      action_type: 'export_quotes',
      action_reason: `导出${scopeLabel}${rowCount}条历史报价`,
      operator_name: resolvedOperatorName.value,
      action_payload: {
        format,
        scope,
        row_count: rowCount,
        status_filter: quoteStatusFilter.value,
        current_product_only: quoteCurrentProductOnly.value,
      },
    })
    await loadSupplierQuoteActions()
  } catch {
    // Export should not fail because logging is unavailable.
  }
}

async function fetchAllFilteredSupplierQuoteRows() {
  if (!selectedSupplierId.value) {
    return [] as SupplierQuoteItem[]
  }

  const rows: SupplierQuoteItem[] = []
  let offset = 0
  let hasMore = true

  while (hasMore) {
    const response = await fetchSupplierQuotesBySupplier(
      selectedSupplierId.value,
      buildSupplierQuoteQueryOptions(offset, 100),
    )
    rows.push(...(response.items ?? []))
    hasMore = Boolean(response.has_more)
    offset += Number(response.limit || 100)
  }

  return rows
}

function buildQuoteExportRows(rows: SupplierQuoteItem[]) {
  return rows.map((item) => ({
    商品名称: item.product_name || item.price_identity_label || item.price_identity_key,
    对比键: item.price_identity_key,
    分类: item.market_category || item.category || '',
    规格: item.spec_text || '',
    报价: item.quote_price ?? '',
    单位: item.quote_unit || '',
    箱价: item.box_price ?? '',
    含税价: item.tax_price ?? '',
    库存状态: item.inventory_status || '',
    报价状态: getQuoteStatusLabel(item),
    作废原因: item.invalidated_reason || '',
    渠道: item.channel || '',
    备注: item.remarks || '',
    报价人: item.quoted_by || '',
    报价时间: item.quoted_at || '',
  }))
}

async function exportQuoteRows(
  format: 'xlsx' | 'csv',
  rows: SupplierQuoteItem[],
  scope: 'filtered' | 'selected',
  scopeLabel: string,
) {
  const exportRows = buildQuoteExportRows(rows)
  const exportPrefix = slugifyExportValue(selectedSupplier.value?.supplier_name)
  const fileSuffix = `${exportPrefix}-history-${scope}-${formatDateOnly(new Date())}`

  try {
    if (format === 'xlsx') {
      const xlsx = await import('xlsx')
      const worksheet = xlsx.utils.json_to_sheet(exportRows)
      const workbook = xlsx.utils.book_new()
      xlsx.utils.book_append_sheet(workbook, worksheet, '历史报价')
      xlsx.writeFile(workbook, `${fileSuffix}.xlsx`)
    } else {
      const headers = Object.keys(exportRows[0] || {})
      const lines = [
        headers.join(','),
        ...exportRows.map((row) =>
          headers
            .map((header) => `"${String(row[header as keyof typeof row] ?? '').replaceAll('"', '""')}"`)
            .join(','),
        ),
      ]
      const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `${fileSuffix}.csv`
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)
      URL.revokeObjectURL(url)
    }
    await logQuoteExport(format, exportRows.length, scope, scopeLabel)
    ElMessage.success(`已导出${scopeLabel}${exportRows.length}条历史报价`)
  } catch {
    ElMessage.error('导出失败，请稍后重试')
  }
}

async function exportFilteredQuotes(format: 'xlsx' | 'csv') {
  if (!historyQuoteTotal.value) {
    ElMessage.warning('当前筛选结果为空，无法导出')
    return
  }
  const exportRows = selectedSupplier.value ? await fetchAllFilteredSupplierQuoteRows() : historyQuoteRows.value
  if (!exportRows.length) {
    ElMessage.warning('当前筛选结果为空，无法导出')
    return
  }
  await exportQuoteRows(format, exportRows, 'filtered', '当前筛选的')
}

async function exportSelectedQuotes(format: 'xlsx' | 'csv') {
  if (!selectedQuoteRows.value.length) {
    ElMessage.warning('请先选择要导出的历史报价')
    return
  }
  await exportQuoteRows(format, selectedQuoteRows.value, 'selected', '已选的')
}

async function invalidateQuote(item: SupplierQuoteItem) {
  if (!item.record_id) {
    ElMessage.warning('这条报价缺少记录 ID，暂时无法作废')
    return
  }

  const isAlreadyInvalidated = item.status === 'invalidated'
  const title = isAlreadyInvalidated ? '修改作废原因' : '填写作废原因'
  const confirmButtonText = isAlreadyInvalidated ? '保存原因' : '确认作废'

  try {
    const { value } = await ElMessageBox.prompt(
      isAlreadyInvalidated ? '可补充或修改这条历史报价的作废原因。' : '作废后该报价会保留在历史中，但不再参与有效报价对比。',
      title,
      {
        confirmButtonText,
        cancelButtonText: '取消',
        inputValue: item.invalidated_reason || '',
        inputPlaceholder: '例如：录错价格 / 规格填错 / 重复录入',
        inputValidator: (value) => {
          if (String(value || '').trim()) {
            return true
          }
          return '请填写作废原因'
        },
      },
    )

    quoteActionLoadingId.value = item.record_id
    await invalidateSupplierQuote(item.record_id, {
      reason: String(value || '').trim() || undefined,
      operator_name: resolvedOperatorName.value,
    })
    ElMessage.success(isAlreadyInvalidated ? '作废原因已更新' : '报价已作废，后续比价将自动排除这条记录')
    await reloadAll()
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    ElMessage.error('作废失败，请稍后重试')
  } finally {
    quoteActionLoadingId.value = null
  }
}

async function invalidateSelectedQuotes() {
  if (!selectedActiveQuoteRows.value.length) {
    ElMessage.warning('请选择至少一条有效报价再执行批量作废')
    return
  }

  try {
    const batchCount = selectedActiveQuoteRows.value.length
    const { value } = await ElMessageBox.prompt(
      `将批量作废 ${batchCount} 条历史报价，作废后不会参与有效比价。`,
      '批量作废报价',
      {
        confirmButtonText: '确认作废',
        cancelButtonText: '取消',
        inputPlaceholder: '例如：重复录入 / 录错价格 / 临时报错',
        inputValidator: (inputValue) => {
          if (String(inputValue || '').trim()) {
            return true
          }
          return '请填写作废原因'
        },
      },
    )

    batchActionLoading.value = 'invalidate'
    const reason = String(value || '').trim()
    let successCount = 0
    let failedCount = 0
    const resultRows: BatchOperationExportRow[] = []
    for (const item of selectedActiveQuoteRows.value) {
      if (!item.record_id) {
        resultRows.push({
          状态: '跳过',
          商品: item.product_name || item.price_identity_label || item.price_identity_key,
          对比键: item.price_identity_key,
          来源记录: '',
          新记录: '',
          说明: '缺少记录 ID，无法作废',
        })
        continue
      }
      try {
        const response = await invalidateSupplierQuote(item.record_id, { reason, operator_name: resolvedOperatorName.value })
        successCount += 1
        resultRows.push({
          状态: '成功',
          商品: item.product_name || item.price_identity_label || item.price_identity_key,
          对比键: item.price_identity_key,
          来源记录: `#${item.record_id}`,
          新记录: response.item.record_id != null ? `#${response.item.record_id}` : '',
          说明: reason,
        })
      } catch {
        failedCount += 1
        resultRows.push({
          状态: '失败',
          商品: item.product_name || item.price_identity_label || item.price_identity_key,
          对比键: item.price_identity_key,
          来源记录: `#${item.record_id}`,
          新记录: '',
          说明: '作废失败，请稍后重试',
        })
      }
    }
    if (resultRows.length) {
      setLastBatchOperationResult('invalidate', '最近一批作废结果', resultRows)
    }
    clearSelectedQuotes()
    if (successCount) {
      await reloadAll()
    }
    if (successCount === batchCount && !failedCount) {
      ElMessage.success(`已批量作废 ${batchCount} 条报价`)
      return
    }
    if (successCount || failedCount) {
      ElMessage.warning(`已作废 ${successCount} 条，失败 ${failedCount} 条`)
      return
    }
    ElMessage.warning('没有成功作废的报价记录')
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    ElMessage.error('批量作废失败，请稍后重试')
  } finally {
    batchActionLoading.value = null
  }
}

function handleProductChange(value: string) {
  if (!value) return
  emit('select-product', value)
}

function openQuoteHistoryPanel() {
  if (props.mobile) {
    mobileSupplierTask.value = 'history'
  }
  desktopSupplierInsightTab.value = 'history'
}

function openSupplierPickerFromHistory() {
  if (isEmbeddedBackendMode.value) {
    emit('navigate-section', 'suppliers')
    return
  }
  mobileSupplierTask.value = 'suppliers'
}

function focusSelectedSupplierQuoteWorkbench() {
  if (props.mobile) {
    mobileSupplierTask.value = 'quote'
  }
  desktopSupplierWorkbenchTab.value = 'quote'
  if (resolvedBackendSection.value === 'suppliers') {
    emit('navigate-section', 'quote')
  }
}

function clearSelectedSupplierDetail() {
  if (!isAdminSession.value) return
  selectedSupplierId.value = null
}

function focusRecentQuote(item: SupplierQuoteItem) {
  if (item.supplier_id) {
    selectedSupplierId.value = item.supplier_id
  }
  if (item.price_identity_key) {
    emit('select-product', item.price_identity_key)
  }
}

watch(selectedSupplierId, async () => {
  rememberSupplierSelection(selectedSupplierId.value)
  fillSupplierForm(selectedSupplier.value)
  quotePageOffset.value = 0
  quoteActionOffset.value = 0
  settlementOffset.value = 0
  clearSelectedQuotes()
  settlementFormVisible.value = false
  settlementDetailVisible.value = false
  activeSettlementDetail.value = null
  resetSettlementForm()
  lastBatchOperationKind.value = null
  lastBatchOperationTitle.value = ''
  lastBatchOperationSummary.value = ''
  lastBatchOperationRows.value = []
  loadCurrentQuoteDraft()
  await Promise.all([loadSupplierQuotes(), loadSupplierQuoteActions(), loadSupplierSettlements()])
})

watch(
  () => selectedProductKey.value,
  async () => {
    if (!hasBackendAuthSession.value) {
      productCompare.value = null
      loadCurrentQuoteDraft()
      return
    }
    await loadProductCompare()
    loadCurrentQuoteDraft()
    if (selectedSupplierId.value && quoteCurrentProductOnly.value) {
      await resetQuotePaginationAndReload()
    }
  },
)

watch(
  [quoteStatusFilter, quoteKeyword, quoteCurrentProductOnly, () => quoteDateRange.value.join('|')],
  async () => {
    if (!selectedSupplierId.value) return
    await resetQuotePaginationAndReload()
  },
)

watch(
  [quoteActionTypeFilter, quoteActionOperatorFilter, quoteActionKeywordFilter, () => quoteActionDateRange.value.join('|')],
  async () => {
    if (!selectedSupplierId.value) return
    await resetQuoteActionPaginationAndReload()
  },
)

watch(
  [settlementStatusFilter, settlementKeyword, () => settlementDateRange.value.join('|')],
  async () => {
    if (!selectedSupplierId.value) return
    await resetSettlementPaginationAndReload()
  },
)

watch(
  [quoteImportMode, () => quoteImportDuplicateMatchFields.value.join('|'), quoteImportAbnormalThresholdPercent],
  async () => {
    if (!quoteImportPreviewVisible.value || !quoteImportPreviewRows.value.length) return
    quoteImportPreviewRows.value = await enrichQuoteImportPreviewRows(quoteImportPreviewRows.value)
  },
)

watch(operatorName, (value) => {
  writeSavedOperatorName(value)
})

watch(historyQuoteRows, () => {
  const allowedIds = new Set(
    historyQuoteRows.value
      .map((item) => getQuoteRecordId(item))
      .filter((item): item is number => item != null),
  )
  selectedQuoteIds.value = selectedQuoteIds.value.filter((item) => allowedIds.has(item))
})

watch(settlementRows, (rows) => {
  if (!rows.length) {
    focusedSettlementId.value = null
    return
  }
  if (!rows.some((item) => item.id === focusedSettlementId.value)) {
    focusedSettlementId.value = rows[0].id
  }
})

onMounted(() => {
  operatorName.value = props.authDisplayName?.trim() || readSavedOperatorName()
  if (isSupplierSession.value) {
    mobileSupplierTask.value = 'quote'
    selectedSupplierId.value = currentSupplierScopeId.value
    desktopSupplierInsightTab.value = 'history'
    desktopSupplierWorkbenchTab.value = 'quote'
  }
})

watch(
  () => isAdminSession.value,
  (nextIsAdmin) => {
    if (nextIsAdmin) {
      desktopSupplierInsightTab.value = desktopSupplierInsightTab.value === 'logs' ? 'overview' : desktopSupplierInsightTab.value
      desktopSupplierWorkbenchTab.value = isProcurementSupplierManagement.value || !selectedSupplier.value ? 'supplier' : 'quote'
      return
    }
    if (desktopSupplierInsightTab.value === 'logs' || desktopSupplierInsightTab.value === 'overview') {
      desktopSupplierInsightTab.value = 'history'
    }
    desktopSupplierWorkbenchTab.value = 'quote'
  },
  { immediate: true },
)

watch(
  () => selectedSupplierId.value,
  (nextSupplierId) => {
    if (props.mobile || !isAdminSession.value) return
    desktopSupplierWorkbenchTab.value = isProcurementSupplierManagement.value || !nextSupplierId ? 'supplier' : 'quote'
    if ((isProcurementSupplierManagement.value || isSupplierWorkspace.value) && nextSupplierId) {
      desktopSupplierWorkbenchTab.value = 'supplier'
      desktopSupplierInsightTab.value = 'overview'
    }
  },
)

watch(
  () => resolvedBackendSection.value,
  (nextSection) => {
    if (props.mobile) {
      if (nextSection === 'quote') {
        mobileSupplierTask.value = 'quote'
        return
      }
      if (nextSection === 'suppliers') {
        mobileSupplierTask.value = 'suppliers'
        return
      }
      if (nextSection === 'settlement') {
        mobileSupplierTask.value = 'settlement'
        return
      }
      if (nextSection === 'logs') {
        mobileSupplierTask.value = 'history'
      }
      return
    }
    if (nextSection === 'suppliers') {
      desktopSupplierWorkbenchTab.value = 'supplier'
      desktopSupplierInsightTab.value = 'overview'
      return
    }
    if (nextSection === 'settlement') {
      desktopSupplierInsightTab.value = 'settlement'
      return
    }
    if (nextSection === 'logs') {
      desktopSupplierInsightTab.value = 'logs'
      return
    }
    if (nextSection === 'quote') {
      desktopSupplierInsightTab.value = 'history'
      desktopSupplierWorkbenchTab.value = 'quote'
    }
  },
  { immediate: true },
)

void reloadAll()
</script>

<style scoped>
.supplier-admin-panel {
  --admin-radius-xl: 18px;
  --admin-radius-lg: 16px;
  --admin-radius-md: 14px;
  --admin-border: rgba(148, 163, 184, 0.14);
  --admin-border-strong: rgba(148, 163, 184, 0.18);
  --admin-shadow: 0 10px 22px rgba(15, 23, 42, 0.045);
  --admin-card-surface: rgba(255, 255, 255, 0.96);
  --admin-soft-surface: linear-gradient(145deg, rgba(248, 250, 252, 0.94), rgba(255, 255, 255, 0.98));
  --admin-control-height: 40px;
  --admin-control-radius: 14px;
}

.supplier-admin-panel,
.supplier-admin-layout,
.supplier-admin-metrics,
.supplier-admin-toolbar,
.supplier-mobile-focus-card,
.supplier-mobile-focus-copy,
.supplier-card-list,
.supplier-category-list,
.supplier-compare-summary,
.supplier-form-grid,
.supplier-action-log-list,
.supplier-overview-quote-list,
.supplier-quote-list,
.supplier-settlement-list {
  display: grid;
  gap: 12px;
}

.supplier-mobile-focus-card {
  grid-template-columns: minmax(0, 1fr);
  padding: 14px;
  border: 1px solid rgba(96, 165, 250, 0.18);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.96), rgba(255, 255, 255, 0.98));
}

.supplier-mobile-guide-card,
.supplier-mobile-guide-copy,
.supplier-mobile-guide-list {
  display: grid;
  gap: 10px;
}

.supplier-mobile-guide-card {
  padding: 14px;
  border: 1px solid rgba(14, 116, 144, 0.12);
  border-radius: 18px;
  background: linear-gradient(160deg, rgba(248, 250, 252, 0.98), rgba(236, 253, 245, 0.88));
}

.supplier-mobile-guide-copy span,
.supplier-mobile-guide-step span {
  color: var(--accent-blue);
  font-size: 11px;
  font-weight: 700;
}

.supplier-mobile-guide-copy strong,
.supplier-mobile-guide-step strong {
  color: var(--ink-900);
}

.supplier-mobile-guide-copy small,
.supplier-mobile-guide-step small {
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.45;
}

.supplier-mobile-guide-actions,
.supplier-empty-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-mobile-guide-button {
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  color: var(--ink-900);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.supplier-mobile-guide-button.primary {
  border-color: transparent;
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.96), rgba(37, 99, 235, 0.92));
  color: #eff6ff;
}

.supplier-mobile-guide-list {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.supplier-mobile-guide-step {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
}

.supplier-mobile-focus-copy {
  gap: 6px;
}

.supplier-mobile-focus-copy span,
.supplier-mobile-focus-copy small,
.supplier-mobile-focus-meta span {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-mobile-focus-copy strong {
  color: var(--ink-900);
  font-size: 18px;
  line-height: 1.2;
}

.supplier-mobile-focus-meta,
.supplier-mobile-task-strip {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-mobile-recent-strip,
.supplier-mobile-action-bar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-mobile-focus-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
}

.supplier-mobile-task-button {
  display: grid;
  gap: 4px;
  flex: 1 1 132px;
  min-width: 0;
  padding: 12px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.94);
  color: var(--ink-900);
  text-align: left;
  font: inherit;
  cursor: pointer;
  transition:
    transform var(--transition-fast),
    box-shadow var(--transition-fast),
    border-color var(--transition-fast);
}

.supplier-mobile-task-button strong {
  font-size: 14px;
}

.supplier-mobile-task-button small {
  color: var(--ink-500);
  font-size: 11px;
  line-height: 1.4;
}

.supplier-mobile-task-button.active {
  border-color: rgba(37, 99, 235, 0.24);
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.94), rgba(255, 255, 255, 0.98));
  box-shadow: 0 12px 22px rgba(15, 23, 42, 0.08);
}

.supplier-mobile-recent-chip,
.supplier-mobile-action-button {
  font: inherit;
  cursor: pointer;
}

.supplier-mobile-recent-chip {
  display: grid;
  gap: 4px;
  flex: 0 0 auto;
  min-width: 116px;
  padding: 10px 12px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.94);
  text-align: left;
}

.supplier-mobile-recent-chip strong {
  color: var(--ink-900);
  font-size: 13px;
}

.supplier-mobile-recent-chip small {
  color: var(--ink-500);
  font-size: 10px;
}

.supplier-mobile-recent-chip.active {
  border-color: rgba(37, 99, 235, 0.24);
  background: rgba(239, 246, 255, 0.96);
}

.supplier-mobile-action-button {
  flex: 1 1 140px;
  min-height: 42px;
  padding: 0 14px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  color: var(--ink-900);
  font-weight: 700;
}

.supplier-mobile-action-button.primary {
  border-color: transparent;
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.96), rgba(37, 99, 235, 0.92));
  color: #eff6ff;
}

.supplier-mobile-action-button:disabled {
  cursor: not-allowed;
  opacity: 0.56;
}

.supplier-mobile-task-shell {
  display: grid;
  gap: 12px;
}

.supplier-admin-metrics {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.supplier-admin-panel.embedded {
  gap: 10px;
  padding: 0;
  border: none;
  background: transparent;
  box-shadow: none;
}

.supplier-admin-metric,
.supplier-card,
.supplier-form-card,
.supplier-category-row,
.supplier-compare-card,
.supplier-action-log-row,
.supplier-overview-quote-row,
.supplier-quote-row,
.supplier-card-empty {
  border: 1px solid var(--admin-border-strong);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-card-surface);
  box-shadow: var(--admin-shadow);
}

.supplier-admin-metric,
.supplier-form-card,
.supplier-category-row,
.supplier-compare-card,
.supplier-action-log-row,
.supplier-overview-quote-row,
.supplier-quote-row,
.supplier-card-empty {
  padding: 14px;
}

.supplier-admin-metric span,
.supplier-admin-metric small,
.supplier-card-meta span,
.supplier-card p,
.supplier-card small,
.supplier-quote-row-meta span,
.supplier-quote-row-foot small {
  color: var(--ink-500);
}

.supplier-admin-metric strong {
  display: block;
  margin: 6px 0;
  color: var(--ink-900);
  font-size: 22px;
}

.supplier-workbench-header,
.supplier-workbench-copy,
.supplier-workbench-side,
.supplier-workbench-chips,
.supplier-workbench-actions,
.supplier-command-center,
.supplier-command-copy,
.supplier-command-metrics,
.supplier-overview-head-actions,
.supplier-admin-toolbar-main,
.supplier-admin-toolbar-filters,
.supplier-list-section-head,
.supplier-list-summary-grid,
.supplier-list-summary-card,
.supplier-card-submeta,
.supplier-card-foot {
  display: grid;
  gap: 10px;
}

.supplier-workbench-header {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  padding: 14px 16px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-xl);
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 34%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(244, 247, 251, 0.96));
  box-shadow: var(--admin-shadow);
}

.supplier-workbench-header.compact {
  padding: 12px 14px;
}

.supplier-command-center {
  grid-template-columns: minmax(160px, 0.52fr) minmax(0, 1.42fr) 320px;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.035);
}

.supplier-command-copy {
  align-content: center;
  gap: 3px;
  padding: 0 2px;
}

.supplier-command-copy span {
  color: #2563eb;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.supplier-command-copy strong {
  color: #0f172a;
  font-size: 16px;
  line-height: 1.35;
}

.supplier-command-metrics {
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 6px;
}

.supplier-command-metric {
  display: grid;
  gap: 2px;
  min-height: 46px;
  padding: 7px 8px;
  border: 1px solid #e5edf6;
  border-radius: 8px;
  background: #ffffff;
}

.supplier-command-metric span {
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
}

.supplier-command-metric strong {
  color: #0f172a;
  font-size: 15px;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.supplier-command-nav,
.supplier-command-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.supplier-command-nav {
  align-content: start;
  flex-wrap: nowrap;
  justify-content: flex-end;
}

.supplier-command-actions {
  grid-column: 1 / -1;
  justify-content: flex-end;
  min-height: 34px;
  padding-top: 5px;
  border-top: 1px solid #edf2f7;
}

.supplier-command-nav-item {
  display: grid;
  gap: 2px;
  min-width: 72px;
  min-height: 38px;
  padding: 5px 8px;
  border: 1px solid #dbe4ef;
  border-radius: 8px;
  background: #ffffff;
  color: #334155;
  text-align: left;
}

.supplier-command-nav-item.active {
  border-color: #bfdbfe;
  background: #eef6ff;
  box-shadow: inset 3px 0 0 #2563eb;
}

.supplier-command-nav-item.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.supplier-command-nav-item span {
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
}

.supplier-command-nav-item strong {
  color: #0f172a;
  font-size: 12px;
}

@media (max-width: 1180px) {
  .supplier-command-center {
    grid-template-columns: 1fr;
  }

  .supplier-command-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .supplier-command-actions {
    justify-content: flex-start;
  }
}

.supplier-workbench-copy span {
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.supplier-workbench-copy strong {
  color: var(--ink-900);
  font-size: 18px;
  line-height: 1.35;
}

.supplier-workbench-copy small {
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.6;
}

.supplier-workbench-side {
  justify-items: end;
}

.supplier-workbench-chips,
.supplier-workbench-actions,
.supplier-master-detail-tags,
.supplier-master-detail-actions,
.supplier-list-filter-pills,
.supplier-list-toolbar-meta,
.supplier-overview-head-actions,
.supplier-admin-toolbar-filters,
.supplier-card-submeta,
.supplier-card-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-workbench-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(241, 245, 249, 0.96);
  color: var(--ink-600);
  font-size: 12px;
  white-space: nowrap;
}

.supplier-list-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.88);
}

.supplier-filter-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 0 12px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  color: var(--ink-600);
  font: inherit;
  cursor: pointer;
}

.supplier-filter-pill.active {
  border-color: rgba(37, 99, 235, 0.24);
  background: rgba(239, 246, 255, 0.96);
  color: #1d4ed8;
}

.supplier-list-toolbar-meta span {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-admin-toolbar {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-soft-surface);
  box-shadow: var(--admin-shadow);
}

.supplier-admin-toolbar.compact {
  grid-template-columns: minmax(0, 1fr) auto;
  margin-bottom: 2px;
}

.supplier-admin-toolbar-main {
  min-width: 0;
}

.supplier-admin-toolbar-main :deep(.el-input),
.supplier-admin-toolbar-filters :deep(.el-select) {
  width: 100%;
}

.supplier-admin-panel :deep(.el-button) {
  min-height: var(--admin-control-height);
  padding: 0 14px;
  border-radius: var(--admin-control-radius);
  font-weight: 600;
}

.supplier-admin-panel :deep(.el-button--small) {
  min-height: 32px;
  padding: 0 12px;
  border-radius: 12px;
  font-size: 12px;
}

.supplier-admin-panel :deep(.el-button--primary) {
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.16);
}

.supplier-admin-panel :deep(.el-input__wrapper),
.supplier-admin-panel :deep(.el-select__wrapper),
.supplier-admin-panel :deep(.el-textarea__inner) {
  min-height: var(--admin-control-height);
  border-radius: var(--admin-control-radius);
  box-shadow: 0 0 0 1px var(--admin-border) inset;
}

.supplier-admin-panel :deep(.el-textarea__inner) {
  padding: 10px 12px;
}

.supplier-admin-panel :deep(.el-input-number) {
  width: 100%;
}

.supplier-admin-panel :deep(.el-input-number .el-input__wrapper) {
  padding-left: 12px;
  padding-right: 34px;
}

.supplier-admin-layout {
  grid-template-columns: minmax(220px, 0.72fr) minmax(360px, 1.16fr) minmax(420px, 1.42fr);
  align-items: start;
}

.supplier-admin-layout.layout-two-column {
  grid-template-columns: minmax(208px, 0.54fr) minmax(0, 1.78fr);
}

.supplier-admin-layout.layout-quote-focus {
  grid-template-columns: minmax(300px, 340px) minmax(0, 1fr);
  gap: 12px;
}

.supplier-admin-layout.layout-suppliers-focus {
  grid-template-columns: minmax(220px, 0.68fr) minmax(420px, 1.24fr) minmax(320px, 0.92fr);
}

.supplier-admin-layout.layout-procurement-management {
  grid-template-columns: minmax(280px, 0.78fr) minmax(390px, 0.92fr) minmax(520px, 1.34fr);
  gap: 12px;
}

.supplier-admin-column {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.supplier-pane-tabs {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.supplier-pane-tabs.workbench-tabs {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.supplier-form-column > .supplier-column-head {
  margin-top: -2px;
}

.supplier-admin-panel.embedded .supplier-form-column > .supplier-column-head,
.supplier-admin-panel.embedded .supplier-column-head {
  margin-top: 0;
}

.supplier-admin-panel.embedded .supplier-form-card,
.supplier-admin-panel.embedded .supplier-category-row,
.supplier-admin-panel.embedded .supplier-compare-card,
.supplier-admin-panel.embedded .supplier-action-log-row,
.supplier-admin-panel.embedded .supplier-overview-quote-row,
.supplier-admin-panel.embedded .supplier-quote-row,
.supplier-admin-panel.embedded .supplier-card-empty,
.supplier-admin-panel.embedded .supplier-card,
.supplier-admin-panel.embedded .supplier-admin-toolbar,
.supplier-admin-panel.embedded .supplier-settlement-row,
.supplier-admin-panel.embedded .supplier-last-batch-card,
.supplier-admin-panel.embedded .supplier-last-batch-preview-row {
  border-color: rgba(148, 163, 184, 0.14);
  background: rgba(255, 255, 255, 0.98);
  box-shadow: none;
}

.supplier-admin-panel.embedded .supplier-admin-toolbar,
.supplier-admin-panel.embedded .supplier-card-empty,
.supplier-admin-panel.embedded .supplier-form-card,
.supplier-admin-panel.embedded .supplier-last-batch-card {
  border-radius: 10px;
}

.supplier-admin-panel.embedded {
  gap: 8px;
  background: transparent;
  overflow: visible;
}

.supplier-admin-panel.embedded .supplier-workbench-header,
.supplier-admin-panel.embedded .supplier-admin-toolbar,
.supplier-admin-panel.embedded .supplier-form-card,
.supplier-admin-panel.embedded .supplier-card,
.supplier-admin-panel.embedded .supplier-card-empty,
.supplier-admin-panel.embedded .supplier-category-row,
.supplier-admin-panel.embedded .supplier-compare-card,
.supplier-admin-panel.embedded .supplier-action-log-row,
.supplier-admin-panel.embedded .supplier-overview-quote-row,
.supplier-admin-panel.embedded .supplier-quote-row,
.supplier-admin-panel.embedded .supplier-settlement-row,
.supplier-admin-panel.embedded .supplier-last-batch-card,
.supplier-admin-panel.embedded .supplier-last-batch-preview-row,
.supplier-admin-panel.embedded .supplier-datagrid-head {
  border-color: #e2e8f0;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.supplier-admin-panel.embedded .supplier-workbench-header {
  padding: 12px 14px;
}

.supplier-admin-panel.embedded .supplier-workbench-copy strong {
  color: #10203d;
  font-size: 17px;
  letter-spacing: 0;
}

.supplier-admin-panel.embedded .supplier-workbench-chip,
.supplier-admin-panel.embedded .supplier-filter-pill {
  border: 1px solid #e2e8f0;
  background: #f8fafc;
}

.supplier-admin-panel.embedded .supplier-quote-list,
.supplier-admin-panel.embedded .supplier-overview-quote-list {
  max-height: none;
}

.supplier-admin-panel.layout-suppliers-focus {
  gap: 10px;
}

.supplier-admin-panel.layout-procurement-management {
  gap: 12px;
}

.supplier-admin-panel.layout-procurement-management .supplier-workbench-header {
  border-color: rgba(37, 99, 235, 0.12);
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.98), rgba(255, 255, 255, 0.98));
}

.supplier-admin-panel.layout-procurement-management .supplier-admin-layout {
  grid-template-columns: minmax(280px, 0.78fr) minmax(390px, 0.92fr) minmax(520px, 1.34fr);
  gap: 12px;
}

.supplier-admin-panel.layout-procurement-management .supplier-list-section-head,
.supplier-admin-panel.layout-procurement-management .supplier-list-workspace-toolbar,
.supplier-admin-panel.layout-procurement-management .supplier-list-toolbar,
.supplier-admin-panel.layout-procurement-management .supplier-master-detail-banner,
.supplier-admin-panel.layout-procurement-management .supplier-form-card {
  padding: 12px 14px;
}

.supplier-admin-panel.layout-procurement-management .supplier-list-workspace-stats {
  gap: 8px;
}

.supplier-admin-panel.layout-procurement-management .supplier-list-workspace-stats,
.supplier-admin-panel.layout-procurement-management .supplier-list-summary-grid {
  grid-template-columns: 1fr;
}

.supplier-admin-panel.layout-procurement-management .supplier-list-workspace-toolbar {
  grid-template-columns: 1fr;
  align-items: stretch;
}

.supplier-admin-panel.layout-procurement-management .supplier-list-workspace-actions,
.supplier-admin-panel.layout-procurement-management .supplier-list-toolbar-meta {
  justify-content: flex-start;
}

.supplier-admin-panel.layout-procurement-management .supplier-list-toolbar {
  grid-template-columns: 1fr;
  gap: 8px;
}

.supplier-admin-panel.layout-procurement-management .supplier-list-column .supplier-datagrid-head {
  display: none;
}

.supplier-admin-panel.layout-procurement-management .supplier-card-list {
  max-height: 780px;
  overflow: auto;
  padding-right: 2px;
}

.supplier-admin-panel.layout-procurement-management .supplier-card {
  grid-template-columns: 1fr;
  align-items: start;
  gap: 8px;
  padding: 12px 14px;
}

.supplier-admin-panel.layout-procurement-management .supplier-card-meta,
.supplier-admin-panel.layout-procurement-management .supplier-card-submeta,
.supplier-admin-panel.layout-procurement-management .supplier-card-foot {
  justify-content: flex-start;
  gap: 6px;
}

.supplier-admin-panel.layout-procurement-management .supplier-form-column {
  align-content: start;
}

.supplier-admin-panel.layout-procurement-management .supplier-quotes-column {
  min-width: 0;
}

.supplier-admin-panel.layout-procurement-management .supplier-history-grid-shell {
  min-height: 420px;
}

.supplier-admin-panel.layout-procurement-management .supplier-history-toolbar {
  grid-template-columns: minmax(180px, 1fr) minmax(220px, 0.9fr);
}

.supplier-admin-panel.layout-procurement-management .supplier-history-batch-bar {
  border-color: rgba(37, 99, 235, 0.16);
  background: rgba(248, 250, 252, 0.96);
}

.supplier-admin-panel.layout-procurement-management .supplier-history-batch-bar.is-active {
  border-color: rgba(245, 158, 11, 0.28);
  background: rgba(255, 251, 235, 0.9);
}

.supplier-procurement-view-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.supplier-procurement-view-switch button {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid var(--admin-border-strong);
  border-radius: var(--admin-control-radius);
  background: rgba(248, 250, 252, 0.9);
  color: var(--ink-900);
  text-align: left;
  font: inherit;
  cursor: pointer;
}

.supplier-procurement-view-switch button.active {
  border-color: rgba(37, 99, 235, 0.24);
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.94), rgba(255, 255, 255, 0.98));
  box-shadow: 0 12px 22px rgba(15, 23, 42, 0.08);
}

.supplier-procurement-view-switch strong {
  color: var(--ink-900);
  font-size: 13px;
}

.supplier-procurement-view-switch small {
  color: var(--ink-500);
  font-size: 11px;
  line-height: 1.45;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-admin-layout {
  gap: 10px;
  grid-template-columns: minmax(230px, 0.58fr) minmax(420px, 1fr) minmax(300px, 0.76fr);
}

.supplier-admin-panel.layout-suppliers-focus .supplier-list-section-head,
.supplier-admin-panel.layout-suppliers-focus .supplier-list-workspace-toolbar,
.supplier-admin-panel.layout-suppliers-focus .supplier-list-toolbar,
.supplier-admin-panel.layout-suppliers-focus .supplier-master-detail-banner,
.supplier-admin-panel.layout-suppliers-focus .supplier-form-card {
  padding: 10px 12px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-list-workspace-stats {
  gap: 8px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-list-summary-card.compact {
  min-height: 72px;
  padding: 10px 12px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-card-list {
  max-height: 780px;
  overflow: auto;
  padding-right: 2px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-card {
  grid-template-columns: 1fr;
  gap: 6px;
  padding: 10px 12px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-card-head {
  flex-direction: row;
  align-items: center;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-card-meta,
.supplier-admin-panel.layout-suppliers-focus .supplier-card-submeta,
.supplier-admin-panel.layout-suppliers-focus .supplier-card-foot {
  justify-content: flex-start;
  gap: 6px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-card p {
  color: var(--ink-600);
  font-size: 12px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-form-grid {
  gap: 10px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-account-card {
  gap: 10px;
  padding: 10px 12px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-form-actions {
  padding-top: 2px;
}

.supplier-datagrid-head {
  display: grid;
  align-items: center;
  min-height: 38px;
  padding: 0 16px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 16px;
  background: rgba(241, 245, 249, 0.82);
}

.supplier-datagrid-head-sticky {
  position: sticky;
  top: 0;
  z-index: 3;
  box-shadow: 0 10px 18px rgba(15, 23, 42, 0.04);
}

.supplier-quote-list .supplier-datagrid-head,
.supplier-datagrid-head span {
  color: var(--ink-500);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.quote-history-grid {
  grid-template-columns: minmax(220px, 1.5fr) minmax(140px, 0.9fr) minmax(180px, 1fr) auto;
}

.supplier-list-grid {
  grid-template-columns: minmax(120px, 1fr) minmax(120px, 0.9fr) minmax(120px, 0.9fr) minmax(110px, 0.8fr);
}

.settlement-grid {
  grid-template-columns: minmax(220px, 1.2fr) minmax(160px, 0.9fr) minmax(220px, 1fr) minmax(280px, 1.15fr);
}

.supplier-pane-tab {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 12px 14px;
  border: 1px solid var(--admin-border-strong);
  border-radius: var(--admin-control-radius);
  background: rgba(248, 250, 252, 0.9);
  color: var(--ink-900);
  text-align: left;
  font: inherit;
  cursor: pointer;
  transition:
    transform var(--transition-fast),
    border-color var(--transition-fast),
    box-shadow var(--transition-fast),
    background var(--transition-fast);
}

.supplier-pane-tab strong {
  color: var(--ink-900);
  font-size: 13px;
}

.supplier-pane-tab small {
  color: var(--ink-500);
  font-size: 11px;
  line-height: 1.4;
}

.supplier-pane-tab.active {
  border-color: rgba(37, 99, 235, 0.24);
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.94), rgba(255, 255, 255, 0.98));
  box-shadow: 0 12px 22px rgba(15, 23, 42, 0.08);
}

.supplier-column-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.supplier-list-summary-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.supplier-list-workspace-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.supplier-list-summary-card {
  padding: 12px 14px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-md);
  background: rgba(248, 250, 252, 0.88);
}

.supplier-list-summary-card.compact {
  gap: 4px;
  padding: 10px 12px;
}

.supplier-list-summary-card span,
.supplier-card-submeta span,
.supplier-card-foot small {
  color: var(--ink-500);
  font-size: 11px;
}

.supplier-list-summary-card strong {
  color: var(--ink-900);
  font-size: 18px;
}

.supplier-list-summary-card small {
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-list-workspace-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(150px, 0.55fr) minmax(140px, 0.45fr) auto;
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-soft-surface);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.03);
}

.supplier-list-workspace-search {
  min-width: 0;
}

.supplier-list-workspace-toolbar :deep(.el-input),
.supplier-list-workspace-toolbar :deep(.el-select) {
  width: 100%;
}

.supplier-list-workspace-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-card-list {
  max-height: 720px;
  overflow: auto;
  padding-right: 4px;
}

.supplier-admin-panel.layout-quote-focus .supplier-list-toolbar {
  grid-template-columns: 1fr;
}

.supplier-admin-panel.layout-quote-focus .supplier-list-toolbar-meta {
  justify-content: space-between;
}

.supplier-admin-panel.layout-quote-focus .supplier-list-column .supplier-datagrid-head,
.supplier-admin-panel.layout-suppliers-focus .supplier-list-column .supplier-datagrid-head {
  display: none;
}

.supplier-admin-panel.layout-quote-focus .supplier-list-workspace-stats,
.supplier-admin-panel.layout-suppliers-focus .supplier-list-workspace-stats,
.supplier-admin-panel.layout-two-column .supplier-list-workspace-stats,
.supplier-admin-panel.layout-quote-focus .supplier-list-summary-grid,
.supplier-admin-panel.layout-suppliers-focus .supplier-list-summary-grid,
.supplier-admin-panel.layout-two-column .supplier-list-summary-grid {
  grid-template-columns: 1fr;
}

.supplier-admin-panel.layout-quote-focus .supplier-list-workspace-toolbar,
.supplier-admin-panel.layout-suppliers-focus .supplier-list-workspace-toolbar,
.supplier-admin-panel.layout-two-column .supplier-list-workspace-toolbar {
  grid-template-columns: 1fr;
  align-items: stretch;
}

.supplier-admin-panel.layout-quote-focus .supplier-list-workspace-actions,
.supplier-admin-panel.layout-suppliers-focus .supplier-list-workspace-actions,
.supplier-admin-panel.layout-two-column .supplier-list-workspace-actions {
  justify-content: flex-start;
}

.supplier-admin-panel.layout-quote-focus .supplier-card-list {
  max-height: 760px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-list-toolbar {
  grid-template-columns: 1fr;
  gap: 8px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-list-toolbar-meta {
  justify-content: space-between;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-card-list {
  max-height: 760px;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-card {
  grid-template-columns: 1fr;
  align-items: start;
  gap: 8px;
  padding: 12px 14px;
}

.supplier-admin-panel.layout-quote-focus .supplier-card {
  grid-template-columns: 1fr;
  align-items: start;
  gap: 8px;
  padding: 12px;
}

.supplier-quote-supplier-switcher {
  display: grid;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.88);
}

.supplier-procurement-carry-task {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid rgba(14, 165, 233, 0.24);
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.96), rgba(240, 253, 250, 0.94));
  box-shadow: 0 14px 34px rgba(14, 116, 144, 0.08);
}

.supplier-procurement-carry-task span,
.supplier-procurement-carry-task p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.supplier-procurement-carry-task strong {
  display: block;
  margin: 3px 0;
  color: #0f172a;
  font-size: 17px;
}

.supplier-procurement-carry-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.supplier-quote-readiness-card {
  display: grid;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid rgba(245, 158, 11, 0.22);
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(255, 251, 235, 0.94), rgba(255, 255, 255, 0.98));
}

.supplier-quote-selection-alert {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid rgba(220, 38, 38, 0.18);
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(254, 242, 242, 0.96), rgba(255, 255, 255, 0.98));
  color: #991b1b;
}

.supplier-quote-selection-alert span {
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-quote-readiness-copy {
  display: grid;
  gap: 4px;
}

.supplier-quote-readiness-copy span,
.supplier-quote-readiness-copy p,
.supplier-quote-readiness-item small {
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-quote-readiness-copy strong {
  color: var(--ink-900);
  font-size: 16px;
}

.supplier-quote-readiness-copy p {
  margin: 0;
}

.supplier-quote-readiness-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.supplier-quote-readiness-item {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 10px;
  border: 1px solid rgba(245, 158, 11, 0.16);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
}

.supplier-quote-readiness-item.ready {
  border-color: rgba(16, 185, 129, 0.18);
  background: rgba(240, 253, 244, 0.86);
}

.supplier-quote-readiness-item span {
  color: #b45309;
  font-size: 10px;
  font-weight: 800;
}

.supplier-quote-readiness-item.ready span {
  color: #047857;
}

.supplier-quote-readiness-item strong {
  color: var(--ink-900);
  font-size: 13px;
}

.supplier-quote-readiness-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-quote-gate-note {
  display: grid;
  gap: 3px;
  padding: 10px 12px;
  border: 1px dashed rgba(148, 163, 184, 0.4);
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.92);
}

.supplier-quote-gate-note strong {
  color: var(--ink-900);
  font-size: 13px;
}

.supplier-quote-gate-note span {
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.45;
}

.supplier-quote-draft-card {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) auto auto;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: 14px;
  background: rgba(239, 246, 255, 0.78);
}

.supplier-quote-draft-copy {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.supplier-quote-draft-copy span,
.supplier-quote-draft-copy small,
.supplier-quote-draft-meta span {
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.45;
}

.supplier-quote-draft-copy strong {
  overflow: hidden;
  color: var(--ink-900);
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.supplier-quote-draft-meta,
.supplier-quote-draft-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.supplier-quote-draft-meta span {
  display: inline-flex;
  min-height: 26px;
  align-items: center;
  padding: 0 9px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.74);
}

.supplier-quote-supplier-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-admin-panel.layout-quote-focus .supplier-card-meta,
.supplier-admin-panel.layout-quote-focus .supplier-card-submeta,
.supplier-admin-panel.layout-quote-focus .supplier-card-foot {
  justify-content: flex-start;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-card-meta,
.supplier-admin-panel.layout-suppliers-focus .supplier-card-submeta,
.supplier-admin-panel.layout-suppliers-focus .supplier-card-foot {
  justify-content: flex-start;
}

.supplier-admin-panel.layout-suppliers-focus .supplier-form-column {
  align-content: start;
}

.supplier-admin-panel.layout-quote-focus .supplier-form-column {
  align-content: start;
}

.supplier-admin-panel.layout-quote-focus .supplier-quotes-column {
  min-width: 0;
}

.supplier-master-detail-banner {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.94), rgba(255, 255, 255, 0.98));
}

.supplier-master-detail-banner.compact {
  gap: 8px;
  padding: 12px 14px;
  border-radius: 18px;
}

.supplier-master-detail-copy {
  display: grid;
  gap: 6px;
}

.supplier-master-detail-copy span,
.supplier-master-detail-copy small {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-master-detail-copy strong {
  color: var(--ink-900);
  font-size: 18px;
  line-height: 1.35;
}

.supplier-history-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-history-context-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 12px 14px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.88), rgba(255, 255, 255, 0.98));
}

.quote-import-preview-shell,
.quote-import-preview-cell {
  display: grid;
  gap: 8px;
}

.quote-import-config-grid,
.quote-import-preview-filters,
.quote-import-preview-card-list,
.quote-import-preview-rule-tags,
.supplier-action-log-filter-grid,
.supplier-last-batch-preview-list {
  display: grid;
  gap: 10px;
}

.quote-import-preview-summary,
.quote-import-preview-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.quote-import-mode-field,
.supplier-action-detail-shell {
  display: grid;
  gap: 8px;
}

.quote-import-config-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.quote-import-preview-summary span {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(226, 232, 240, 0.72);
  color: var(--ink-600);
  font-size: 12px;
}

.quote-import-mode-field > span,
.quote-import-mode-field small,
.supplier-action-detail-meta span {
  color: var(--ink-500);
  font-size: 12px;
}

.quote-import-mode-select {
  max-width: 240px;
}

.quote-import-duplicate-select {
  width: 100%;
}

.quote-import-preview-filters {
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
}

.quote-import-preview-rule-tags {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.quote-import-preview-filter-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.96);
  color: var(--ink-600);
  font: inherit;
  cursor: pointer;
}

.quote-import-preview-filter-chip.active {
  border-color: rgba(37, 99, 235, 0.24);
  background: rgba(239, 246, 255, 0.96);
  color: #1d4ed8;
}

.quote-import-status-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.quote-import-status-chip.is-ready {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
}

.quote-import-status-chip.is-error {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.quote-import-preview-cell strong {
  color: var(--ink-900);
  font-size: 13px;
}

.quote-import-preview-decision.is-append {
  color: #0f766e;
}

.quote-import-preview-decision.is-skip {
  color: #92400e;
}

.quote-import-preview-decision.is-override {
  color: #1d4ed8;
}

.quote-import-preview-decision.is-abnormal,
.quote-import-preview-decision.is-invalid {
  color: #b91c1c;
}

.quote-import-preview-cell small {
  color: var(--ink-500);
  font-size: 12px;
}

.quote-import-preview-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.92);
}

.quote-import-preview-card-head,
.quote-import-preview-card-meta,
.quote-import-preview-card-section,
.supplier-last-batch-actions,
.supplier-last-batch-preview-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.quote-import-preview-card-head {
  align-items: flex-start;
  justify-content: space-between;
}

.quote-import-preview-card-meta,
.quote-import-preview-card-section {
  flex-direction: column;
}

.quote-import-preview-card-meta span,
.quote-import-preview-card-section small {
  color: var(--ink-500);
  font-size: 12px;
}

.quote-import-preview-card-section.is-abnormal {
  padding: 10px;
  border-radius: 14px;
  background: rgba(254, 226, 226, 0.64);
}

.supplier-action-log-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-action-log-filters.compact-workspace {
  justify-content: flex-end;
}

.supplier-action-log-filter-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.supplier-action-log-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.supplier-action-log-summary article {
  display: grid;
  gap: 5px;
  min-height: 82px;
  padding: 12px 14px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.92));
}

.supplier-action-log-summary span,
.supplier-action-log-summary small {
  color: var(--ink-500);
  font-size: 12px;
  line-height: 1.45;
}

.supplier-action-log-summary strong {
  color: var(--ink-900);
  font-size: 16px;
  line-height: 1.3;
}

.supplier-action-log-filter-grid.compact-workspace {
  padding: 12px 14px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.92), rgba(255, 255, 255, 0.98));
}

.supplier-import-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.hidden-file-input {
  display: none;
}

.supplier-history-toolbar,
.supplier-history-summary,
.supplier-history-command-strip,
.supplier-history-batch-bar,
.supplier-history-pagination,
.supplier-history-batch-meta,
.supplier-history-batch-actions,
.supplier-history-viewbar,
.supplier-history-viewmeta,
.supplier-action-log-actions,
.supplier-action-detail-meta,
.supplier-quote-title-wrap,
.supplier-history-date-shortcuts,
.supplier-action-log-tags,
.supplier-last-batch-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-history-viewbar {
  justify-content: space-between;
  gap: 10px;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
}

.supplier-history-viewtabs {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
  flex: 1;
  min-width: min(620px, 100%);
}

.supplier-history-viewtab {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
  min-height: 34px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #334155;
  text-align: left;
  font: inherit;
  cursor: pointer;
}

.supplier-history-viewtab.active {
  border-color: #bfdbfe;
  background: #ffffff;
  color: #1d4ed8;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.supplier-history-viewtab span {
  overflow: hidden;
  font-size: 12px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.supplier-history-viewtab strong {
  overflow: hidden;
  color: inherit;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.supplier-history-viewmeta {
  flex: 0 0 auto;
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-history-grid-shell {
  gap: 0;
  padding: 0;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #ffffff;
}

.supplier-history-grid-shell .supplier-datagrid-head {
  border: 0;
  border-bottom: 1px solid #e2e8f0;
  border-radius: 10px 10px 0 0;
  background: #f8fafc;
  box-shadow: none;
}

.supplier-history-select-head {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  font: inherit;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  cursor: pointer;
}

.supplier-history-filter-select {
  min-width: 120px;
}

.supplier-history-toolbar :deep(.el-input) {
  flex: 1;
  min-width: 180px;
}

.supplier-action-log-filter-grid :deep(.el-input),
.supplier-action-log-filter-grid :deep(.el-select),
.supplier-action-log-filter-grid :deep(.el-date-editor) {
  width: 100%;
}

.supplier-history-toolbar :deep(.el-date-editor) {
  min-width: 240px;
}

.supplier-history-date-shortcuts {
  flex-wrap: nowrap;
}

.supplier-history-summary span {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(226, 232, 240, 0.72);
  color: var(--ink-600);
  font-size: 12px;
}

.supplier-history-command-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.supplier-history-command-strip article {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.96), rgba(255, 255, 255, 0.98));
}

.supplier-history-command-strip span,
.supplier-history-command-strip small {
  color: var(--ink-500);
  font-size: 11px;
  line-height: 1.35;
}

.supplier-history-command-strip strong {
  overflow: hidden;
  color: var(--ink-900);
  font-size: 16px;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.supplier-history-filter-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-history-batch-bar {
  justify-content: space-between;
}

.supplier-history-batch-bar.is-active {
  padding: 12px 14px;
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.92), rgba(255, 255, 255, 0.98));
}

.supplier-quote-assist-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.supplier-quote-assist-card {
  display: grid;
  gap: 6px;
  min-height: 92px;
  padding: 13px 14px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.94), rgba(255, 255, 255, 0.98));
}

.supplier-quote-assist-card span,
.supplier-quote-assist-card small {
  color: var(--ink-500);
  font-size: 12px;
  line-height: 1.45;
}

.supplier-quote-assist-card strong {
  color: var(--ink-900);
  font-size: 16px;
  line-height: 1.3;
}

.supplier-last-batch-card {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 249, 0.94));
}

.supplier-last-batch-preview-row {
  display: grid;
  gap: 6px;
  padding: 12px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.9);
}

.supplier-last-batch-preview-row small,
.supplier-last-batch-preview-meta span:not(.supplier-action-log-chip) {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-action-log-chip.is-success {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
}

.supplier-action-log-chip.is-warning {
  background: rgba(245, 158, 11, 0.16);
  color: #92400e;
}

.supplier-action-log-chip.is-danger {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.supplier-quote-title-wrap {
  flex: 1;
  min-width: 0;
}

.supplier-quote-row.is-latest-active {
  border-color: rgba(16, 185, 129, 0.28);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
}

.supplier-quote-row.is-selected {
  border-color: rgba(37, 99, 235, 0.28);
  background: #f8fbff;
  box-shadow: inset 3px 0 0 #2563eb;
}

.supplier-latest-badge {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.14);
  color: #047857;
  font-size: 11px;
  font-weight: 700;
}

.supplier-column-head strong {
  color: var(--ink-900);
  font-size: 17px;
}

.supplier-column-head span {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  text-align: left;
  font: inherit;
  cursor: pointer;
  grid-template-columns: minmax(120px, 1fr) minmax(120px, 0.9fr) minmax(120px, 0.9fr) minmax(110px, 0.8fr);
  align-items: center;
}

.supplier-card.active {
  border-color: rgba(37, 99, 235, 0.24);
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.94), rgba(255, 255, 255, 0.98));
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
}

.supplier-card-head,
.supplier-form-actions,
.supplier-quote-row-head,
.supplier-quote-row-foot,
.supplier-card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-quote-head-side,
.supplier-quote-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-card-head strong,
.supplier-quote-row-head strong {
  color: var(--ink-900);
  font-size: 15px;
}

.supplier-card-head {
  flex-direction: column;
  align-items: flex-start;
}

.supplier-card p {
  margin: 0;
}

.supplier-category-row,
.supplier-compare-card,
.supplier-overview-quote-row,
.supplier-action-log-row {
  display: grid;
  gap: 8px;
}

.supplier-action-log-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  max-width: 100%;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(226, 232, 240, 0.8);
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.35;
}

.supplier-action-log-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.supplier-action-log-detail-item,
.supplier-action-log-failure-list {
  display: grid;
  gap: 4px;
}

.supplier-action-log-detail-item span,
.supplier-action-log-failure-list p {
  color: var(--ink-500);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-action-log-detail-item strong,
.supplier-action-log-failure-list strong {
  color: var(--ink-900);
  font-size: 13px;
  word-break: break-word;
}

.supplier-category-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.supplier-category-head strong,
.supplier-compare-card strong {
  color: var(--ink-900);
}

.supplier-category-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-category-meta span,
.supplier-category-head span,
.supplier-compare-card span,
.supplier-compare-card small {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-compare-summary {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.supplier-status-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.supplier-status-chip.is-active {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
}

.supplier-status-chip.is-inactive {
  background: rgba(148, 163, 184, 0.18);
  color: #475569;
}

.supplier-status-chip.is-warning {
  background: rgba(245, 158, 11, 0.16);
  color: #b45309;
}

.supplier-status-chip.is-pending {
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
}

.supplier-form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.supplier-account-card {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-soft-surface);
}

.supplier-form-field {
  display: grid;
  gap: 6px;
}

.supplier-form-field span,
.supplier-inline-tip span {
  color: var(--ink-500);
  font-size: 11px;
}

.supplier-form-field-full {
  grid-column: 1 / -1;
}

.supplier-form-action-buttons {
  display: flex;
  gap: 8px;
}

.supplier-status-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  color: var(--ink-600);
  font-size: 12px;
  font-weight: 700;
}

.supplier-status-toggle span {
  white-space: nowrap;
}

.supplier-inline-tip {
  display: grid;
  gap: 4px;
}

.supplier-inline-tip strong,
.supplier-quote-row-head span {
  color: var(--ink-900);
  font-size: 14px;
}

.supplier-quote-list {
  max-height: 860px;
  overflow: auto;
  display: grid;
  gap: 10px;
  padding-right: 4px;
}

.supplier-admin-panel.layout-quote-focus .supplier-quote-list {
  max-height: calc(100vh - 432px);
  min-height: 330px;
}

.supplier-overview-quote-list {
  max-height: 360px;
  overflow: auto;
}

.supplier-quote-row {
  display: grid;
  gap: 8px;
  border-right: 0;
  border-left: 0;
  border-radius: 0;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast),
    transform var(--transition-fast);
}

.supplier-quote-row:hover {
  border-color: rgba(37, 99, 235, 0.18);
  box-shadow: none;
  transform: none;
}

.supplier-quote-main,
.supplier-settlement-main {
  display: grid;
  gap: 12px;
}

.supplier-quote-main {
  grid-template-columns: minmax(220px, 1.3fr) minmax(136px, 0.72fr) minmax(220px, 1.08fr) auto;
  align-items: center;
  min-width: 760px;
}

.supplier-admin-panel.layout-quote-focus .quote-history-grid {
  grid-template-columns: minmax(260px, 1.2fr) minmax(160px, 0.62fr) minmax(300px, 1.18fr) minmax(128px, 0.42fr);
}

.supplier-admin-panel.layout-quote-focus .supplier-quote-main {
  grid-template-columns: minmax(260px, 1.2fr) minmax(160px, 0.62fr) minmax(300px, 1.18fr) minmax(128px, 0.42fr);
  min-width: 760px;
}

.supplier-settlement-main {
  grid-template-columns: minmax(220px, 1.02fr) minmax(180px, 0.82fr) minmax(220px, 0.96fr) minmax(320px, 1.24fr);
  align-items: center;
  min-width: 0;
}

.supplier-quote-primary,
.supplier-settlement-title,
.supplier-settlement-period,
.supplier-quote-price-panel,
.supplier-quote-context {
  display: grid;
  gap: 6px;
}

.supplier-quote-primary {
  position: sticky;
  left: 0;
  z-index: 1;
  padding-right: 12px;
  background: linear-gradient(90deg, rgba(248, 250, 252, 0.98) 0%, rgba(248, 250, 252, 0.98) 86%, rgba(248, 250, 252, 0) 100%);
}

.supplier-quote-price-panel {
  justify-items: start;
}

.supplier-quote-price-panel strong,
.supplier-settlement-title strong {
  color: var(--ink-900);
  font-size: 18px;
  line-height: 1.35;
}

.supplier-quote-price-panel span,
.supplier-quote-price-panel small,
.supplier-settlement-title small,
.supplier-settlement-period small,
.supplier-quote-note {
  color: var(--ink-500);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-quote-note {
  margin: 0;
}

.supplier-quote-actions-column {
  justify-content: flex-end;
}

.supplier-admin-panel.layout-two-column .settlement-grid,
.supplier-admin-panel.layout-two-column .supplier-settlement-main {
  grid-template-columns: minmax(180px, 0.86fr) minmax(180px, 0.82fr) minmax(180px, 0.86fr) minmax(240px, 1fr);
}

.supplier-admin-panel.layout-two-column .supplier-settlement-head {
  display: grid;
  grid-template-columns: 1fr;
  align-items: stretch;
}

.supplier-admin-panel.layout-two-column .supplier-settlement-head-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: stretch;
  width: 100%;
}

.supplier-admin-panel.layout-two-column .supplier-settlement-build-button {
  min-height: 36px;
}

.supplier-admin-panel.layout-two-column .supplier-settlement-filters.compact {
  grid-template-columns: minmax(132px, 0.42fr) minmax(0, 1fr);
}

.supplier-admin-panel.layout-two-column .supplier-settlement-filters.compact :deep(.el-date-editor) {
  grid-column: 1 / -1;
  width: 100%;
}

.supplier-admin-panel.layout-two-column .supplier-settlement-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.supplier-admin-panel.layout-two-column .supplier-list-toolbar {
  grid-template-columns: 1fr;
  gap: 8px;
}

.supplier-admin-panel.layout-two-column .supplier-list-toolbar-meta {
  justify-content: space-between;
}

.supplier-admin-panel.layout-two-column .supplier-datagrid-head {
  display: none;
}

.supplier-admin-panel.layout-two-column .supplier-card-list {
  max-height: 980px;
}

.supplier-admin-panel.layout-two-column .supplier-card {
  grid-template-columns: 1fr;
  align-items: start;
  gap: 8px;
  padding: 12px 14px;
}

.supplier-admin-panel.layout-two-column .supplier-card-meta,
.supplier-admin-panel.layout-two-column .supplier-card-submeta,
.supplier-admin-panel.layout-two-column .supplier-card-foot {
  justify-content: flex-start;
}

.supplier-workbench-empty-card {
  display: grid;
  gap: 14px;
  align-content: start;
  min-height: 220px;
}

.supplier-workbench-empty-copy {
  display: grid;
  gap: 8px;
}

.supplier-workbench-empty-copy span {
  color: var(--ink-500);
  font-size: 12px;
  font-weight: 700;
}

.supplier-workbench-empty-copy strong {
  color: var(--ink-900);
  font-size: 20px;
  line-height: 1.25;
}

.supplier-workbench-empty-copy p {
  margin: 0;
  color: var(--ink-600);
  line-height: 1.6;
}

.supplier-workbench-empty-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.supplier-settlement-card,
.supplier-settlement-form,
.supplier-settlement-row {
  display: grid;
  gap: 10px;
}

.supplier-settlement-card.compact-workspace {
  gap: 12px;
}

.supplier-logs-card.compact-workspace {
  gap: 12px;
}

.supplier-settlement-head-actions,
.supplier-settlement-filters,
.supplier-settlement-summary,
.supplier-settlement-metrics,
.supplier-settlement-edit-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-settlement-head {
  align-items: flex-start;
}

.supplier-settlement-head.compact-workspace {
  align-items: start;
}

.supplier-logs-head.compact-workspace {
  align-items: center;
}

.supplier-settlement-head-copy {
  display: grid;
  gap: 4px;
}

.supplier-settlement-head-actions.compact-workspace {
  justify-content: flex-end;
}

.supplier-settlement-head-copy span {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-settlement-action-grid {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  width: 100%;
}

.supplier-settlement-action-grid :deep(.el-button) {
  margin-left: 0;
  width: 100%;
}

.supplier-settlement-build-button {
  width: 100%;
}

.supplier-settlement-summary {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.supplier-settlement-filters.compact {
  display: grid;
  grid-template-columns: minmax(132px, 0.48fr) minmax(0, 1fr) minmax(240px, 1.08fr);
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.92), rgba(255, 255, 255, 0.98));
}

.supplier-settlement-edit-row {
  min-width: 0;
}

.supplier-settlement-edit-row :deep(.el-input-number),
.supplier-settlement-edit-row :deep(.el-date-editor) {
  width: 100%;
}

.supplier-admin-panel.layout-two-column .supplier-settlement-edit-row {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: minmax(108px, 0.9fr) minmax(122px, 1fr) repeat(3, max-content);
  align-items: center;
}

.supplier-admin-panel.layout-two-column .supplier-settlement-edit-row :deep(.el-button) {
  padding-left: 8px;
  padding-right: 8px;
}

.supplier-settlement-summary.compact {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.supplier-settlement-next-step {
  padding: 10px 12px;
  border: 1px dashed rgba(37, 99, 235, 0.24);
  border-radius: 12px;
  background: rgba(239, 246, 255, 0.72);
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-settlement-summary-chip {
  display: flex;
  align-items: center;
  min-height: 36px;
  padding: 0 12px;
  border-radius: 12px;
  background: rgba(241, 245, 249, 0.92);
  color: var(--ink-600);
  font-size: 12px;
}

.supplier-settlement-summary span,
.supplier-settlement-metrics span {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-settlement-row {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.78);
}

.supplier-settlement-stat-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.supplier-settlement-stat-card {
  min-height: 116px;
}

.supplier-settlement-stat-card strong {
  font-size: 20px;
}

.supplier-admin-settlement-layout {
  grid-template-columns: minmax(0, 1.06fr) minmax(420px, 0.94fr);
}

.supplier-admin-settlement-list {
  align-content: start;
}

.supplier-admin-settlement-detail {
  top: 0;
}

.supplier-admin-settlement-edit-panel {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 13px 14px;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.96);
}

.supplier-admin-settlement-edit-panel .supplier-form-field {
  min-width: 0;
}

.supplier-admin-settlement-edit-panel .supplier-form-field > span {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-admin-settlement-edit-panel :deep(.el-input-number),
.supplier-admin-settlement-edit-panel :deep(.el-date-editor) {
  width: 100%;
}

.supplier-admin-settlement-edit-actions {
  display: flex;
  align-items: end;
  justify-content: flex-end;
  gap: 8px;
  grid-column: 1 / -1;
  flex-wrap: wrap;
}

.supplier-my-settlement-page {
  width: 100%;
  min-width: 0;
}

.supplier-my-settlement-shell {
  display: grid;
  gap: 14px;
  width: 100%;
  min-width: 0;
}

.supplier-my-settlement-hero,
.supplier-my-settlement-kpis article,
.supplier-my-settlement-filters,
.supplier-my-settlement-row,
.supplier-my-settlement-detail {
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.035);
}

.supplier-my-settlement-hero {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.96), rgba(255, 255, 255, 0.98));
}

.supplier-my-settlement-hero-copy {
  display: grid;
  gap: 4px;
}

.supplier-my-settlement-hero-copy span,
.supplier-my-settlement-detail-head span,
.supplier-my-settlement-detail-note span {
  color: var(--ink-500);
  font-size: 12px;
  font-weight: 700;
}

.supplier-my-settlement-hero-copy strong {
  color: var(--ink-900);
  font-size: 20px;
}

.supplier-my-settlement-hero-copy small,
.supplier-my-settlement-detail-head small,
.supplier-my-settlement-detail-note p {
  color: var(--ink-500);
  font-size: 11px;
  line-height: 1.45;
}

.supplier-my-settlement-hero-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-my-settlement-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
}

.supplier-my-settlement-kpis article {
  display: grid;
  gap: 5px;
  padding: 12px 14px;
}

.supplier-my-settlement-kpis article span {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-my-settlement-kpis article strong {
  color: var(--ink-900);
  font-size: 20px;
  line-height: 1;
}

.supplier-my-settlement-kpis article small {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-my-settlement-kpis article.warn strong { color: #f97316; }
.supplier-my-settlement-kpis article.danger strong { color: #ef4444; }
.supplier-my-settlement-kpis article.green strong { color: #16a34a; }
.supplier-my-settlement-kpis article.blue strong { color: #2563eb; }

.supplier-my-settlement-filters {
  display: grid;
  grid-template-columns: minmax(132px, 0.38fr) minmax(0, 1fr) minmax(260px, 0.95fr);
  gap: 10px;
  padding: 10px 12px;
  width: 100%;
}

.supplier-my-settlement-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(390px, 0.92fr);
  gap: 14px;
  align-items: start;
  width: 100%;
}

.supplier-my-settlement-list {
  display: grid;
  gap: 10px;
  min-width: 0;
  align-content: start;
}

.supplier-my-settlement-row {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), transform var(--transition-fast);
}

.supplier-my-settlement-row:hover {
  transform: translateY(-1px);
  border-color: rgba(59, 130, 246, 0.18);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.06);
}

.supplier-my-settlement-row.active {
  border-color: rgba(37, 99, 235, 0.24);
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.94), rgba(255, 255, 255, 0.98));
  box-shadow: 0 12px 22px rgba(15, 23, 42, 0.08);
}

.supplier-my-settlement-row::before {
  content: "";
  position: absolute;
  left: 0;
  top: 14px;
  bottom: 14px;
  width: 3px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.22);
}

.supplier-my-settlement-row.active::before {
  background: #2563eb;
}

.supplier-my-settlement-row-topline,
.supplier-my-settlement-row-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.supplier-my-settlement-row-index,
.supplier-my-settlement-row-progress {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border-radius: 999px;
  background: rgba(248, 250, 252, 0.96);
  color: var(--ink-600);
  font-size: 11px;
  font-weight: 700;
}

.supplier-my-settlement-row-progress {
  background: rgba(239, 246, 255, 0.96);
  color: #1d4ed8;
}

.supplier-my-settlement-row-head,
.supplier-my-settlement-row-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.supplier-my-settlement-row-title {
  display: grid;
  gap: 2px;
}

.supplier-my-settlement-row-title small {
  color: var(--ink-500);
  font-size: 11px;
}

.supplier-my-settlement-row-head strong,
.supplier-my-settlement-detail-head strong {
  color: var(--ink-900);
  font-size: 15px;
}

.supplier-my-settlement-row-meta span,
.supplier-my-settlement-row p {
  color: var(--ink-500);
  font-size: 11px;
}

.supplier-my-settlement-row-metrics,
.supplier-my-settlement-detail-grid,
.supplier-my-settlement-detail-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.supplier-my-settlement-row-metrics article,
.supplier-my-settlement-detail-grid article,
.supplier-my-settlement-detail-summary div {
  display: grid;
  gap: 4px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(248, 250, 252, 0.96);
}

.supplier-my-settlement-row-metrics span,
.supplier-my-settlement-detail-grid span,
.supplier-my-settlement-detail-summary span {
  color: var(--ink-500);
  font-size: 11px;
}

.supplier-my-settlement-row-metrics strong,
.supplier-my-settlement-detail-grid strong,
.supplier-my-settlement-detail-summary strong {
  color: var(--ink-900);
  font-size: 16px;
}

.supplier-my-settlement-row-note {
  padding-top: 2px;
  border-top: 1px dashed rgba(148, 163, 184, 0.18);
}

.supplier-my-settlement-row-note p {
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.supplier-my-settlement-row-progressbar {
  width: 100%;
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(226, 232, 240, 0.9);
}

.supplier-my-settlement-row-progressbar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #2563eb, #60a5fa);
}

.supplier-my-settlement-row-footer {
  color: var(--ink-500);
  font-size: 11px;
}

.supplier-my-settlement-detail {
  display: grid;
  gap: 12px;
  padding: 16px;
  min-width: 0;
  position: sticky;
  top: 12px;
}

.supplier-my-settlement-detail-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
}

.supplier-my-settlement-detail-heading {
  display: grid;
  gap: 4px;
}

.supplier-my-settlement-detail-head-side {
  display: grid;
  justify-items: end;
  gap: 8px;
}

.supplier-my-settlement-detail-progress-pill {
  display: grid;
  gap: 4px;
  min-width: 132px;
  padding: 10px 12px;
  border: 1px solid rgba(37, 99, 235, 0.12);
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.96), rgba(255, 255, 255, 0.98));
}

.supplier-my-settlement-detail-progress-pill strong {
  color: #1d4ed8;
  font-size: 18px;
  line-height: 1;
}

.supplier-my-settlement-detail-summary {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) repeat(2, minmax(120px, 1fr));
  gap: 10px;
}

.supplier-my-settlement-detail-summary div {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.96);
}

.supplier-my-settlement-detail-summary div.total {
  border: 1px solid rgba(239, 68, 68, 0.12);
  background: linear-gradient(145deg, rgba(254, 242, 242, 0.96), rgba(255, 255, 255, 0.98));
}

.supplier-my-settlement-detail-summary span {
  color: var(--ink-500);
  font-size: 11px;
}

.supplier-my-settlement-detail-summary strong {
  color: var(--ink-900);
  font-size: 24px;
  line-height: 1;
}

.supplier-my-settlement-detail-summary div.total strong {
  color: #dc2626;
}

.supplier-my-settlement-detail-summary small {
  color: var(--ink-500);
  font-size: 11px;
  line-height: 1.4;
}

.supplier-my-settlement-detail-progress,
.supplier-my-settlement-detail-note,
.supplier-my-settlement-detail-tip {
  display: grid;
  gap: 10px;
  padding: 13px 14px;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.96);
}

.supplier-my-settlement-detail-progress-copy,
.supplier-my-settlement-detail-tip {
  display: grid;
  gap: 4px;
}

.supplier-my-settlement-detail-progress-copy strong,
.supplier-my-settlement-detail-tip strong {
  color: var(--ink-900);
  font-size: 15px;
}

.supplier-my-settlement-detail-progress-copy small,
.supplier-my-settlement-detail-tip p {
  margin: 0;
  color: var(--ink-500);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-my-settlement-detail-progress-track {
  width: 100%;
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(226, 232, 240, 0.96);
}

.supplier-my-settlement-detail-progress-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #1d4ed8, #60a5fa);
}

.supplier-my-settlement-detail-progress-legend {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.supplier-my-settlement-detail-progress-legend article {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
}

.supplier-my-settlement-detail-progress-legend span {
  color: var(--ink-500);
  font-size: 11px;
}

.supplier-my-settlement-detail-progress-legend strong {
  color: var(--ink-900);
  font-size: 16px;
}

.supplier-my-settlement-detail-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.supplier-my-settlement-empty {
  min-height: 180px;
}

@media (max-width: 1180px) {
  .supplier-admin-settlement-layout,
  .supplier-my-settlement-kpis,
  .supplier-my-settlement-layout,
  .supplier-my-settlement-row-metrics,
  .supplier-my-settlement-detail-summary,
  .supplier-my-settlement-detail-grid,
  .supplier-my-settlement-detail-amounts,
  .supplier-my-settlement-filters,
  .supplier-admin-settlement-edit-panel {
    grid-template-columns: 1fr;
  }

  .supplier-my-settlement-hero {
    grid-template-columns: 1fr;
  }

  .supplier-my-settlement-detail {
    position: static;
    top: auto;
  }

  .supplier-my-settlement-detail-head-side {
    justify-items: start;
  }
}

.supplier-quote-row-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-card-empty {
  text-align: center;
}

.supplier-overview-quote-row {
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.supplier-session-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.84);
}

.supplier-session-banner-copy {
  display: grid;
  gap: 4px;
}

.supplier-session-banner-copy span,
.supplier-session-banner-copy small {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-session-banner-copy strong {
  color: var(--ink-900);
  font-size: 15px;
}

.supplier-session-banner-role {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(239, 246, 255, 0.92);
  color: var(--accent-blue);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.supplier-session-empty-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 18px;
  border: 1px solid rgba(245, 158, 11, 0.22);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(255, 251, 235, 0.96), rgba(255, 255, 255, 0.98));
}

.supplier-session-empty-copy {
  display: grid;
  gap: 6px;
}

.supplier-session-empty-copy span,
.supplier-session-empty-copy p {
  color: var(--ink-600);
  font-size: 12px;
}

.supplier-session-empty-copy strong {
  color: var(--ink-900);
  font-size: 16px;
}

.supplier-session-empty-copy p {
  margin: 0;
  line-height: 1.6;
}

.supplier-session-empty-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.compact-empty {
  padding: 14px;
}

.supplier-card-empty strong {
  display: block;
  margin-bottom: 6px;
  color: var(--ink-900);
}

.mobile .supplier-workbench-header,
.mobile .supplier-admin-toolbar,
.mobile .supplier-admin-layout {
  grid-template-columns: 1fr;
}

.mobile .supplier-datagrid-head,
.mobile .supplier-list-grid,
.mobile .quote-history-grid,
.mobile .settlement-grid,
.mobile .supplier-quote-main,
.mobile .supplier-settlement-main {
  grid-template-columns: 1fr;
}

.mobile .supplier-datagrid-head {
  padding: 10px 14px;
}

.mobile .supplier-workbench-side {
  justify-items: stretch;
}

.mobile .supplier-workbench-actions,
.mobile .supplier-master-detail-actions,
.mobile .supplier-admin-toolbar-filters {
  align-items: stretch;
  flex-direction: column;
}

.mobile .supplier-list-toolbar {
  grid-template-columns: 1fr;
}

.mobile .supplier-list-workspace-toolbar {
  grid-template-columns: 1fr;
}

.mobile .supplier-list-workspace-actions {
  justify-content: stretch;
  flex-direction: column;
  align-items: stretch;
}

.mobile .supplier-list-summary-grid {
  grid-template-columns: 1fr;
}

.mobile .supplier-list-workspace-stats {
  grid-template-columns: 1fr;
}

.mobile .supplier-session-banner {
  align-items: flex-start;
  flex-direction: column;
}

.mobile .supplier-session-empty-card,
.mobile .supplier-session-empty-actions {
  align-items: flex-start;
  flex-direction: column;
}

.mobile .supplier-admin-metrics {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.mobile .supplier-compare-summary {
  grid-template-columns: 1fr;
}

@media (max-width: 1180px) {
  .supplier-admin-metrics,
  .supplier-admin-toolbar,
  .supplier-admin-layout {
    grid-template-columns: 1fr;
  }

  .supplier-compare-summary {
    grid-template-columns: 1fr;
  }

  .supplier-pane-tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.mobile .supplier-form-grid {
  grid-template-columns: 1fr;
}

.mobile .supplier-admin-metric {
  min-height: 94px;
  padding: 14px;
}

.mobile .supplier-admin-metric strong {
  margin: 4px 0;
  font-size: 20px;
}

.mobile .supplier-admin-metric small {
  font-size: 11px;
  line-height: 1.45;
}

.mobile .supplier-mobile-guide-actions,
.mobile .supplier-empty-actions {
  align-items: flex-start;
  flex-direction: column;
}

.mobile .supplier-mobile-guide-button,
.mobile .supplier-empty-actions :deep(.el-button) {
  width: 100%;
}

.mobile .supplier-mobile-guide-list {
  grid-template-columns: 1fr;
}

.mobile .supplier-mobile-task-strip {
  overflow-x: auto;
  flex-wrap: nowrap;
  padding-bottom: 2px;
}

.mobile .supplier-mobile-recent-strip {
  overflow-x: auto;
  flex-wrap: nowrap;
  padding-bottom: 2px;
}

.mobile .supplier-mobile-task-button {
  flex: 0 0 144px;
}

.mobile .supplier-mobile-recent-chip {
  flex: 0 0 136px;
}

.mobile .supplier-mobile-action-bar {
  align-items: stretch;
}

.mobile .supplier-form-actions {
  align-items: flex-start;
  flex-direction: column;
}

.mobile .supplier-history-filters {
  width: 100%;
  justify-content: space-between;
}

.mobile .supplier-action-log-filters {
  width: 100%;
  align-items: flex-start;
  flex-direction: column;
}

.mobile .supplier-import-actions {
  width: 100%;
  justify-content: flex-start;
}

.mobile .quote-import-config-grid,
.mobile .quote-import-preview-filters,
.mobile .supplier-action-log-filter-grid {
  grid-template-columns: 1fr;
}

.mobile .supplier-action-log-filter-grid.compact-workspace {
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
}

.mobile .supplier-action-log-summary {
  grid-template-columns: 1fr;
}

.mobile .quote-import-preview-summary,
.mobile .quote-import-preview-footer {
  align-items: flex-start;
  flex-direction: column;
}

.mobile .supplier-history-toolbar,
.mobile .supplier-history-summary,
.mobile .supplier-history-filter-tags,
.mobile .supplier-history-context-strip,
.mobile .supplier-history-command-strip,
.mobile .supplier-history-batch-bar,
.mobile .supplier-history-pagination,
.mobile .supplier-history-batch-meta,
.mobile .supplier-history-batch-actions,
.mobile .supplier-settlement-head-actions,
.mobile .supplier-settlement-filters,
.mobile .supplier-settlement-summary,
.mobile .supplier-settlement-metrics,
.mobile .supplier-settlement-edit-row,
.mobile .supplier-action-log-actions,
.mobile .supplier-action-detail-meta,
.mobile .supplier-history-date-shortcuts,
.mobile .supplier-action-log-tags,
.mobile .supplier-last-batch-actions {
  align-items: flex-start;
  flex-direction: column;
}

.mobile .supplier-history-command-strip {
  grid-template-columns: 1fr;
}

.mobile .supplier-history-filters {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  width: 100%;
  gap: 6px;
}

.mobile .supplier-mobile-task-shell > .supplier-column-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: stretch;
  gap: 8px;
}

.mobile .supplier-mobile-task-shell > .supplier-column-head > strong {
  font-size: 18px;
  line-height: 1.2;
}

.mobile .supplier-history-filters > span {
  overflow: hidden;
  color: var(--ink-500);
  font-size: 12px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile .supplier-history-context-strip {
  flex-direction: row;
  align-items: center;
  gap: 6px;
  padding: 8px;
  border-radius: 12px;
}

.mobile .supplier-history-context-strip .supplier-workbench-chip {
  min-height: 28px;
  padding: 0 9px;
  font-size: 11px;
}

.mobile .supplier-history-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: stretch;
  gap: 8px;
}

.mobile .supplier-history-filter-select,
.mobile .supplier-history-toolbar :deep(.el-input),
.mobile .supplier-history-toolbar :deep(.el-select),
.mobile .supplier-history-toolbar :deep(.el-date-editor) {
  width: 100%;
  min-width: 0;
}

.mobile .supplier-history-date-shortcuts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: stretch;
  gap: 6px;
}

.mobile .supplier-history-date-shortcuts :deep(.el-button) {
  width: 100%;
  min-height: 32px;
  margin-left: 0;
  padding: 0 6px;
}

.mobile .supplier-quote-actions-column {
  justify-content: flex-start;
}

.mobile .supplier-quote-primary {
  position: static;
  padding-right: 0;
  background: none;
}

.mobile .supplier-quote-supplier-meta {
  flex-direction: column;
  align-items: flex-start;
}

.mobile .supplier-quote-readiness-list {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}

.mobile .supplier-quote-readiness-item {
  padding: 8px 7px;
}

.mobile .supplier-quote-readiness-item strong {
  font-size: 12px;
}

.mobile .supplier-quote-readiness-item small {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.mobile .supplier-quote-readiness-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.mobile .supplier-quote-readiness-actions :deep(.el-button) {
  width: 100%;
  margin-left: 0;
}

.mobile .supplier-quote-draft-card {
  grid-template-columns: 1fr;
  align-items: stretch;
}

.mobile .supplier-quote-draft-meta,
.mobile .supplier-quote-draft-actions {
  justify-content: flex-start;
}

.mobile .supplier-quote-draft-actions :deep(.el-button) {
  margin-left: 0;
}

.mobile .supplier-settlement-head {
  gap: 14px;
}

.mobile .supplier-settlement-head-copy strong {
  font-size: 22px;
  line-height: 1.18;
}

.mobile .supplier-settlement-head-actions {
  width: 100%;
}

.mobile .supplier-settlement-filters.compact {
  grid-template-columns: 1fr;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
}

.mobile .supplier-settlement-summary.compact {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.mobile .supplier-settlement-action-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.mobile .supplier-settlement-build-button {
  margin-top: 2px;
}

.mobile .supplier-settlement-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: stretch;
}

.mobile .supplier-settlement-summary-chip {
  min-height: 40px;
  padding: 8px 10px;
  line-height: 1.4;
}

.mobile .supplier-settlement-stat-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.mobile .supplier-settlement-stat-card {
  min-height: 96px;
  padding: 12px;
}

.mobile .supplier-settlement-stat-card strong {
  font-size: 18px;
  margin: 4px 0;
}

.mobile .supplier-settlement-stat-card small {
  font-size: 11px;
}

.mobile .supplier-settlement-filters :deep(.el-date-editor),
.mobile .supplier-settlement-filters :deep(.el-select),
.mobile .supplier-settlement-filters :deep(.el-input) {
  width: 100%;
}

.mobile .supplier-action-log-detail-grid {
  grid-template-columns: 1fr;
}

.mobile.layout-quote-focus.embedded {
  gap: 8px;
}

.mobile.layout-quote-focus.embedded .supplier-form-card {
  gap: 9px;
  padding: 10px;
  border-color: #e5e7eb;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.035);
}

.mobile.layout-quote-focus.embedded .supplier-form-card > .supplier-column-head.compact {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.mobile.layout-quote-focus.embedded .supplier-form-card > .supplier-column-head.compact > strong {
  font-size: 18px;
  line-height: 1.16;
  letter-spacing: 0;
}

.mobile.layout-quote-focus.embedded .supplier-import-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  width: 100%;
}

.mobile.layout-quote-focus.embedded .supplier-import-actions > span {
  grid-column: 1 / -1;
  overflow: hidden;
  color: #64748b;
  font-size: 12px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile.layout-quote-focus.embedded .supplier-import-actions :deep(.el-button) {
  width: 100%;
  min-height: 34px;
  margin-left: 0;
  border-radius: 8px;
  font-size: 12px;
}

.mobile.layout-quote-focus.embedded .supplier-quote-readiness-card {
  gap: 8px;
  padding: 10px;
  border-color: #fde68a;
  border-radius: 8px;
  background: #fff;
}

.mobile.layout-quote-focus.embedded .supplier-quote-readiness-copy {
  gap: 3px;
}

.mobile.layout-quote-focus.embedded .supplier-quote-readiness-copy span {
  color: #92400e;
  font-size: 11px;
  font-weight: 700;
}

.mobile.layout-quote-focus.embedded .supplier-quote-readiness-copy strong {
  font-size: 18px;
  line-height: 1.2;
}

.mobile.layout-quote-focus.embedded .supplier-quote-readiness-copy p {
  font-size: 13px;
  line-height: 1.45;
}

.mobile.layout-quote-focus.embedded .supplier-quote-readiness-list {
  gap: 6px;
}

.mobile.layout-quote-focus.embedded .supplier-quote-readiness-item {
  gap: 3px;
  padding: 8px 7px;
  border-color: #fde68a;
  border-radius: 8px;
  background: #fffdf7;
}

.mobile.layout-quote-focus.embedded .supplier-quote-readiness-item strong {
  font-size: 12px;
  line-height: 1.25;
}

.mobile.layout-quote-focus.embedded .supplier-quote-readiness-item small {
  font-size: 11px;
  line-height: 1.35;
}

.mobile.layout-suppliers-focus.embedded .supplier-admin-layout {
  grid-template-columns: minmax(0, 1fr);
}

.mobile.layout-suppliers-focus.embedded .supplier-card-list {
  max-height: none;
  overflow: visible;
  padding-right: 0;
}

.mobile.layout-suppliers-focus.embedded .supplier-form-column {
  order: 2;
}

.mobile.layout-suppliers-focus.embedded .supplier-list-column {
  order: 1;
}

.mobile.layout-suppliers-focus.embedded .supplier-list-column.is-empty .supplier-list-workspace-stats,
.mobile.layout-suppliers-focus.embedded .supplier-list-column.is-empty .supplier-list-workspace-toolbar,
.mobile.layout-suppliers-focus.embedded .supplier-list-column.is-empty .supplier-list-toolbar {
  display: none;
}

.mobile.layout-suppliers-focus.embedded .supplier-list-column.is-empty .supplier-card-list {
  display: grid;
  gap: 0;
}

.mobile.layout-suppliers-focus.embedded .supplier-list-column.is-empty .supplier-card-empty {
  padding: 14px;
}

.mobile.layout-suppliers-focus.embedded .supplier-form-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: stretch;
  gap: 10px;
}

.mobile.layout-suppliers-focus.embedded .supplier-status-toggle {
  justify-content: space-between;
  width: 100%;
  min-height: 38px;
  padding: 0 2px;
}

.mobile.layout-suppliers-focus.embedded .supplier-form-action-buttons {
  display: grid;
  grid-template-columns: minmax(0, 0.72fr) minmax(0, 1fr);
}

.mobile.layout-suppliers-focus.embedded .supplier-form-action-buttons :deep(.el-button) {
  width: 100%;
  margin-left: 0;
}

@media (max-width: 360px) {
  .mobile .supplier-admin-metrics {
    grid-template-columns: 1fr;
  }
}

/* shadcn/ui MIT-style admin skin for supplier workspace surfaces. */
.supplier-admin-panel.embedded {
  color: #020817;
  --admin-border: #e2e8f0;
  --admin-border-strong: #e2e8f0;
  --admin-radius-xl: 8px;
  --admin-radius-lg: 8px;
  --admin-radius-md: 8px;
  --admin-control-radius: 6px;
  --admin-control-height: 32px;
  --admin-soft-surface: #f8fafc;
  --admin-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  --ink-900: #020817;
  --ink-700: #334155;
  --ink-600: #475569;
  --ink-500: #64748b;
  --accent-blue: #020817;
}

.supplier-admin-panel.embedded .supplier-command-center,
.supplier-admin-panel.embedded .supplier-form-card,
.supplier-admin-panel.embedded .supplier-card,
.supplier-admin-panel.embedded .supplier-card-empty,
.supplier-admin-panel.embedded .supplier-quote-row,
.supplier-admin-panel.embedded .supplier-history-grid-shell,
.supplier-admin-panel.embedded .supplier-settlement-row,
.supplier-admin-panel.embedded .supplier-last-batch-card,
.supplier-admin-panel.embedded .supplier-action-log-row {
  border-color: #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.supplier-admin-panel.embedded .supplier-command-center {
  padding: 8px;
}

.supplier-admin-panel.embedded .supplier-command-copy span,
.supplier-admin-panel.embedded .supplier-workbench-copy span {
  color: #64748b;
  letter-spacing: 0;
  text-transform: none;
}

.supplier-admin-panel.embedded .supplier-command-copy strong,
.supplier-admin-panel.embedded .supplier-column-head strong,
.supplier-admin-panel.embedded .supplier-quote-row-head strong {
  color: #020817;
  font-weight: 750;
}

.supplier-admin-panel.embedded .supplier-command-metric,
.supplier-admin-panel.embedded .supplier-command-nav-item,
.supplier-admin-panel.embedded .supplier-list-summary-card,
.supplier-admin-panel.embedded .supplier-compare-card,
.supplier-admin-panel.embedded .supplier-history-command-strip article,
.supplier-admin-panel.embedded .supplier-quote-assist-card,
.supplier-admin-panel.embedded .supplier-settlement-stat-card {
  border-color: #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: none;
}

.supplier-admin-panel.embedded .supplier-command-nav-item.active,
.supplier-admin-panel.embedded .supplier-history-viewtab.active,
.supplier-admin-panel.embedded .supplier-filter-pill.active {
  border-color: #cbd5e1;
  background: #f1f5f9;
  color: #020817;
  box-shadow: none;
}

.supplier-admin-panel.embedded .supplier-command-nav-item.active {
  box-shadow: inset 2px 0 0 #020817;
}

.supplier-admin-panel.embedded .supplier-history-viewbar,
.supplier-admin-panel.embedded .supplier-history-toolbar,
.supplier-admin-panel.embedded .supplier-history-batch-bar,
.supplier-admin-panel.embedded .supplier-history-context-strip,
.supplier-admin-panel.embedded .supplier-list-toolbar,
.supplier-admin-panel.embedded .supplier-list-workspace-toolbar {
  border-color: #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  box-shadow: none;
}

.supplier-admin-panel.embedded .supplier-history-batch-bar.is-active {
  border-color: #cbd5e1;
  background: #f1f5f9;
}

.supplier-admin-panel.embedded .supplier-history-grid-shell {
  overflow: hidden auto;
}

.supplier-admin-panel.embedded .supplier-history-grid-shell .supplier-datagrid-head {
  border-bottom-color: #e2e8f0;
  background: #f8fafc;
}

.supplier-admin-panel.embedded .supplier-quote-row {
  border-top: 0;
  box-shadow: none;
}

.supplier-admin-panel.embedded .supplier-quote-row + .supplier-quote-row {
  border-top: 1px solid #e2e8f0;
}

.supplier-admin-panel.embedded .supplier-quote-row.is-selected {
  border-color: #cbd5e1;
  background: #f8fafc;
  box-shadow: inset 3px 0 0 #020817;
}

.supplier-admin-panel.embedded .supplier-quote-row.is-latest-active {
  border-color: #bbf7d0;
  box-shadow: inset 3px 0 0 #22c55e;
}

.supplier-admin-panel.embedded .supplier-workbench-chip,
.supplier-admin-panel.embedded .supplier-action-log-chip,
.supplier-admin-panel.embedded .supplier-history-summary span,
.supplier-admin-panel.embedded .supplier-settlement-summary-chip {
  min-height: 24px;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  background: #ffffff;
  color: #475569;
}

.supplier-admin-panel.embedded .supplier-status-chip {
  min-height: 22px;
  border-radius: 999px;
}

.supplier-admin-panel.embedded :deep(.el-button) {
  min-height: 32px;
  border-color: #e2e8f0;
  border-radius: 6px;
  background: #ffffff;
  color: #020817;
  box-shadow: none;
}

.supplier-admin-panel.embedded :deep(.el-button--primary) {
  border-color: #020817;
  background: #020817;
  color: #ffffff;
}

.supplier-admin-panel.embedded :deep(.el-button--danger.is-plain) {
  border-color: #fecaca;
  background: #fff1f2;
  color: #be123c;
}

.supplier-admin-panel.embedded :deep(.el-input__wrapper),
.supplier-admin-panel.embedded :deep(.el-select__wrapper),
.supplier-admin-panel.embedded :deep(.el-textarea__inner),
.supplier-admin-panel.embedded :deep(.el-input-number .el-input__wrapper) {
  min-height: 32px;
  border-radius: 6px;
  background: #ffffff;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.supplier-admin-panel.embedded :deep(.el-input__wrapper.is-focus),
.supplier-admin-panel.embedded :deep(.el-select__wrapper.is-focused),
.supplier-admin-panel.embedded :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px #020817 inset;
}

.supplier-admin-panel.embedded :deep(.el-checkbox__input.is-checked .el-checkbox__inner),
.supplier-admin-panel.embedded :deep(.el-checkbox__input.is-indeterminate .el-checkbox__inner) {
  border-color: #020817;
  background: #020817;
}

.supplier-admin-panel.layout-quote-focus.embedded {
  gap: 8px;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-admin-layout {
  align-items: stretch;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-form-column {
  position: sticky;
  top: 0;
  align-self: start;
  max-height: calc(100vh - 92px);
  overflow: auto;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-form-card {
  padding: 12px;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-form-card > .supplier-column-head.compact {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 8px;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-form-card > .supplier-column-head.compact > strong {
  font-size: 16px;
  line-height: 1.2;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-import-actions {
  display: grid;
  grid-template-columns: 1fr;
  justify-items: stretch;
  width: 100%;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-import-actions > span {
  overflow: hidden;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-import-actions :deep(.el-button) {
  width: 100%;
  margin-left: 0;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-compare-summary {
  grid-template-columns: 1fr;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-compare-card {
  min-height: 64px;
  padding: 10px;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-form-grid {
  grid-template-columns: 1fr;
  gap: 9px;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-form-actions {
  align-items: stretch;
  flex-direction: column;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-form-action-buttons {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1fr);
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-form-action-buttons :deep(.el-button) {
  width: 100%;
  margin-left: 0;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-quotes-column {
  min-width: 0;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-history-context-strip,
.supplier-admin-panel.layout-quote-focus.embedded .supplier-history-command-strip,
.supplier-admin-panel.layout-quote-focus.embedded .supplier-history-summary,
.supplier-admin-panel.layout-quote-focus.embedded .supplier-history-filter-tags {
  display: none;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-history-viewbar {
  position: sticky;
  top: 0;
  z-index: 5;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-history-toolbar {
  display: grid;
  grid-template-columns: minmax(190px, 1fr) minmax(260px, 0.92fr) auto minmax(132px, 0.42fr);
  gap: 8px;
  align-items: center;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-history-date-shortcuts {
  display: none;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-history-batch-bar {
  min-height: 40px;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-history-batch-meta {
  flex: 1 1 260px;
}

.supplier-admin-panel.layout-quote-focus.embedded .supplier-history-batch-actions {
  justify-content: flex-end;
  flex: 1 1 420px;
}

@media (min-width: 821px) {
  .supplier-admin-panel.layout-two-column.embedded .supplier-admin-layout {
    grid-template-columns: minmax(260px, 340px) minmax(520px, 1fr);
    align-items: start;
  }

  .supplier-admin-panel.layout-two-column.embedded .supplier-list-column,
  .supplier-admin-panel.layout-two-column.embedded .supplier-form-column {
    min-width: 0;
  }

  .supplier-admin-panel.layout-quote-focus.embedded .supplier-admin-layout {
    grid-template-columns: minmax(260px, 340px) minmax(520px, 1fr);
    align-items: start;
  }

  .supplier-admin-panel.layout-content-only.embedded .supplier-admin-layout {
    grid-template-columns: minmax(0, 1fr);
    align-items: stretch;
    align-content: start;
    min-height: 0;
  }

  .supplier-admin-panel.layout-content-only.embedded .supplier-quotes-column {
    display: grid;
    align-content: start;
    min-width: 0;
    min-height: 0;
    height: auto;
    overflow: visible;
  }

  .supplier-admin-panel.layout-content-only.embedded .supplier-settlement-card,
  .supplier-admin-panel.layout-content-only.embedded .supplier-logs-card {
    align-self: start;
    min-height: 320px;
    height: auto;
    overflow: visible;
  }
}
</style>
