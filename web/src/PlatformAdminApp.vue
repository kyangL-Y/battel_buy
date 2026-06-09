<template>
  <section
    class="app-shell platform-admin-shell"
    :class="[{ mobile: isMobileViewport, 'auth-only': !canUseAdminWorkbench }, `section-${activeSection}`]"
    :data-ready="authRestoring || statusLoading || coverageLoading ? 'loading' : 'ready'"
    data-testid="platform-admin-screen"
  >
    <header class="panel platform-admin-topbar">
      <div class="platform-admin-brand">
        <div class="platform-admin-brand-mark">管</div>
        <div class="platform-admin-brand-copy">
          <p class="panel-kicker">后台</p>
          <h1>平台后台</h1>
        </div>
      </div>
      <div class="platform-admin-topbar-actions">
        <div v-for="item in topbarCards" :key="item.label" class="platform-admin-chip" :class="{ accent: item.accent }">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
        <el-button v-if="isAuthenticated" plain @click="logoutAdminSession">退出登录</el-button>
        <el-button plain @click="backToMainWorkspace">返回采购端</el-button>
      </div>
    </header>

    <main v-if="authRestoring" class="platform-admin-frame" :class="{ mobile: isMobileViewport }">
      <section class="panel platform-admin-panel" data-testid="platform-admin-auth-restoring">
        <div class="platform-admin-panel-head">
          <div>
            <p class="panel-kicker">登录</p>
            <h2>正在恢复后台会话</h2>
          </div>
        </div>
        <p>正在校验本机 token，请稍候。</p>
      </section>
    </main>

    <main v-else-if="!isAuthenticated" class="platform-admin-frame" :class="{ mobile: isMobileViewport }">
      <section class="panel platform-admin-panel" data-testid="platform-admin-login-form">
        <div class="platform-admin-panel-head">
          <div>
            <p class="panel-kicker">登录</p>
            <h2>管理员登录</h2>
          </div>
        </div>
        <p>平台后台涉及数据抓取和来源治理，请先使用管理员账号登录。</p>
        <div class="market-auth-form">
          <el-input v-model="authForm.username" data-testid="platform-admin-username-input" placeholder="管理员账号" />
          <el-input
            v-model="authForm.password"
            data-testid="platform-admin-password-input"
            type="password"
            show-password
            placeholder="密码"
            @keyup.enter="submitAdminLogin"
          />
          <p v-if="authError" class="market-auth-error">{{ authError }}</p>
          <div class="market-auth-actions">
            <el-button type="primary" data-testid="platform-admin-login-button" :loading="authSubmitting" @click="submitAdminLogin">登录后台</el-button>
            <el-button plain @click="openSupplierBackend">去供应商管理台</el-button>
          </div>
        </div>
      </section>
    </main>

    <main v-else-if="!isAdminUser" class="platform-admin-frame" :class="{ mobile: isMobileViewport }">
      <section class="panel platform-admin-panel" data-testid="platform-admin-forbidden">
        <div class="platform-admin-panel-head">
          <div>
            <p class="panel-kicker">403</p>
            <h2>当前账号无权进入平台后台</h2>
          </div>
        </div>
        <p>{{ currentUser?.display_name || currentUser?.username || '当前账号' }} 不是管理员角色。数据抓取、来源覆盖和调度控制仅允许管理员使用。</p>
        <div class="market-auth-actions">
          <el-button type="primary" @click="logoutAdminSession">切换管理员账号</el-button>
          <el-button plain @click="openSupplierPortal">返回供应商门户</el-button>
        </div>
      </section>
    </main>

    <div v-else class="platform-admin-frame" :class="{ mobile: isMobileViewport }">
      <aside class="panel platform-admin-sidebar">
        <div class="platform-admin-sidebar-head">
          <p class="panel-kicker">控制台</p>
          <h2>后台</h2>
        </div>
        <div class="platform-admin-nav-list">
          <button
            v-for="item in adminSections"
            :key="item.key"
            type="button"
            class="platform-admin-nav-item"
            :class="{ active: activeSection === item.key }"
            @click="activeSection = item.key"
          >
            <div class="platform-admin-nav-item-head">
              <strong>{{ item.label }}</strong>
              <span>{{ item.code }}</span>
            </div>
          </button>
        </div>
        <div class="platform-admin-system-switcher">
          <div class="platform-admin-system-head">
            <span>切换</span>
          </div>
          <button type="button" class="platform-admin-system-link" @click="backToMainWorkspace">
            <strong>采购前端</strong>
          </button>
          <button type="button" class="platform-admin-system-link" @click="openSupplierPortal">
            <strong>供应商门户</strong>
          </button>
          <button type="button" class="platform-admin-system-link" @click="openSupplierBackend">
            <strong>供应商管理台</strong>
          </button>
        </div>
      </aside>

      <main class="platform-admin-stage">
        <section class="panel platform-admin-pagebar">
          <div>
            <p class="panel-kicker">{{ activeSectionMeta.kicker }}</p>
            <h1>{{ activeSectionMeta.title }}</h1>
          </div>
          <div class="platform-admin-pagebar-actions">
            <el-button
              v-if="activeSection === 'crawl'"
              type="primary"
              :loading="crawlActionLoading || crawlStatus?.is_running"
              @click="handleManualCrawl"
            >
              获取最新数据
            </el-button>
            <el-button
              v-else
              type="primary"
              :loading="coverageLoading"
              @click="reloadSourceCoverage"
            >
              刷新覆盖数据
            </el-button>
            <el-button
              v-if="activeSection === 'crawl'"
              :loading="statusLoading || coverageLoading"
              @click="reloadAdminData"
            >
              刷新状态
            </el-button>
            <el-button v-else plain @click="activeSection = 'crawl'">去抓取任务</el-button>
          </div>
        </section>

        <section class="platform-admin-metrics">
          <article v-for="item in overviewCards" :key="item.label" class="platform-admin-metric-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.detail }}</small>
          </article>
        </section>

        <section v-if="activeSection === 'sources'" class="panel platform-admin-workbench-toolbar">
          <div class="platform-admin-workbench-search">
            <el-input v-model="sourceKeyword" clearable placeholder="搜索来源、市场、分类、异常说明" />
          </div>
          <div class="platform-admin-workbench-tabs" aria-label="来源状态筛选">
            <button
              v-for="item in sourceHealthTabs"
              :key="item.key"
              type="button"
              class="platform-admin-workbench-tab"
              :class="{ active: sourceHealthFilter === item.key }"
              @click="sourceHealthFilter = item.key"
            >
              <strong>{{ item.label }}</strong>
              <small>{{ item.count }}</small>
            </button>
          </div>
          <div class="platform-admin-workbench-meta">
            <span>{{ sourceCoverageDisplayLabel }}</span>
            <el-button size="small" plain @click="clearSourceWorkbenchFilters">重置筛选</el-button>
          </div>
        </section>

        <section v-if="activeSection === 'sources'" class="platform-admin-source-workspace">
          <section class="platform-admin-source-deck" data-testid="platform-source-coverage-list">
            <article
              v-for="item in visibleSourceCoverageCards"
              :key="item.key"
              class="platform-admin-source-card"
              :class="{ active: selectedSourceKey === item.key }"
              role="button"
              tabindex="0"
              @click="openSourceDetail(item.key)"
              @keydown.enter="openSourceDetail(item.key)"
              @keydown.space.prevent="openSourceDetail(item.key)"
            >
              <div class="platform-admin-source-head">
                <div>
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.subtitle }}</span>
                </div>
                <em :class="item.tone">{{ item.status }}</em>
              </div>
              <div class="platform-admin-source-metrics">
                <span><small>商品</small>{{ item.productCount }}</span>
                <span><small>市场</small>{{ item.marketCount }}</span>
                <span><small>最近</small>{{ item.latestCapture }}</span>
              </div>
              <p v-if="item.failure">{{ item.failure }}</p>
              <button type="button" class="platform-admin-source-detail-link" @click.stop="openSourceDetail(item.key)">查看来源</button>
            </article>
            <article v-if="!sourceCoverageCards.length" class="platform-admin-empty">
              <strong>{{ sourceCoverageRows.length ? '当前筛选下没有来源' : '暂无来源覆盖数据' }}</strong>
              <span>{{ sourceCoverageRows.length ? '可以清空搜索词或切回全部状态。' : '刷新覆盖数据或先触发一次数据抓取后再查看。' }}</span>
              <div class="platform-admin-empty-actions">
                <el-button size="small" plain :loading="coverageLoading" @click="reloadSourceCoverage">刷新覆盖数据</el-button>
                <el-button size="small" type="primary" @click="activeSection = 'crawl'">去抓取任务</el-button>
              </div>
            </article>
            <div v-if="showSourceListToggle" class="platform-admin-source-list-toggle">
              <button type="button" @click="mobileSourceListExpanded = !mobileSourceListExpanded">
                {{ mobileSourceListExpanded ? '收起来源列表' : `显示全部 ${sourceCoverageCards.length} 个来源` }}
              </button>
            </div>
          </section>

          <aside
            class="platform-admin-detail-drawer"
            :class="{ 'mobile-open': Boolean(selectedSourceCoverageCard) }"
            role="complementary"
            aria-label="来源覆盖详情"
          >
            <div v-if="sourceDetailCoverageCard" class="platform-admin-detail-panel">
              <div class="platform-admin-detail-head">
                <div>
                  <span>来源详情</span>
                  <strong>{{ sourceDetailCoverageCard.title }}</strong>
                  <small>{{ sourceDetailCoverageCard.subtitle || '来源覆盖' }}</small>
                </div>
                <button type="button" @click="closeSourceDetail">清除选择</button>
              </div>
              <div class="platform-admin-detail-metrics">
                <article>
                  <span>商品</span>
                  <strong>{{ sourceDetailCoverageCard.productCount }}</strong>
                </article>
                <article>
                  <span>市场/条目</span>
                  <strong>{{ sourceDetailCoverageCard.marketCount }}</strong>
                </article>
                <article>
                  <span>最近采集</span>
                  <strong>{{ sourceDetailCoverageCard.latestCapture }}</strong>
                </article>
              </div>
              <div class="platform-admin-detail-tags">
                <span :class="sourceDetailCoverageCard.tone">{{ sourceDetailCoverageCard.status }}</span>
                <span>{{ sourceDetailCoverageCard.source.source_tier || '未分级' }}</span>
                <span>{{ sourceDetailCoverageCard.source.strategy || '默认策略' }}</span>
                <span>{{ sourceDetailCoverageCard.source.enabled === false ? '已停用' : '已启用' }}</span>
              </div>
              <dl class="platform-admin-detail-list">
                <div>
                  <dt>来源地址</dt>
                  <dd>{{ sourceDetailCoverageCard.source.source_url || '-' }}</dd>
                </div>
                <div>
                  <dt>说明</dt>
                  <dd>{{ sourceDetailCoverageCard.source.notes || '暂无说明' }}</dd>
                </div>
                <div>
                  <dt>失败信息</dt>
                  <dd>{{ sourceDetailCoverageCard.failure || '未返回失败信息' }}</dd>
                </div>
              </dl>
            </div>
            <div v-else class="platform-admin-detail-panel platform-admin-detail-empty">
              <div class="platform-admin-detail-head">
                <div>
                  <span>来源详情</span>
                  <strong>等待来源数据</strong>
                  <small>暂无可展示的来源覆盖</small>
                </div>
              </div>
              <p>刷新覆盖数据，或前往抓取任务获取一次数据后再查看来源详情。</p>
              <div class="platform-admin-empty-actions">
                <el-button size="small" plain :loading="coverageLoading" @click="reloadSourceCoverage">刷新覆盖数据</el-button>
                <el-button size="small" type="primary" @click="activeSection = 'crawl'">去抓取任务</el-button>
              </div>
            </div>
          </aside>
        </section>

        <section v-if="activeSection === 'crawl'" class="panel platform-admin-panel">
          <div class="platform-admin-panel-head">
            <div>
              <p class="panel-kicker">运行控制</p>
              <h2>抓取任务</h2>
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
          <div class="platform-admin-progress">
            <div class="platform-admin-progress-head">
              <span>{{ crawlProgressLabel }}</span>
              <strong>{{ crawlProgressPercent }}%</strong>
            </div>
            <el-progress :percentage="crawlProgressPercent" :stroke-width="10" :show-text="false" :status="crawlStatus?.is_running ? undefined : 'success'" />
            <p v-if="crawlStatus?.current_source_name">当前来源：{{ crawlStatus.current_source_name }}</p>
            <p v-if="crawlStatus?.current_source_detail">{{ crawlStatus.current_source_detail }}</p>
            <p v-if="crawlStatus?.last_error" class="platform-admin-error">{{ crawlStatus.last_error }}</p>
          </div>
          <div class="platform-admin-live-sources" v-if="crawlActivityCards.length">
            <article v-for="item in visibleCrawlActivityCards" :key="item.key" class="platform-admin-live-source-card">
              <div>
                <strong>{{ item.title }}</strong>
                <span>{{ item.subtitle }}</span>
              </div>
              <em :class="item.tone">{{ item.status }}</em>
              <small>{{ item.meta }}</small>
            </article>
            <div v-if="showCrawlActivityToggle" class="platform-admin-live-source-toggle">
              <button type="button" @click="mobileCrawlActivityExpanded = !mobileCrawlActivityExpanded">
                {{ mobileCrawlActivityExpanded ? '收起最近来源' : `显示全部 ${crawlActivityCards.length} 个最近来源` }}
              </button>
            </div>
          </div>
          <div class="platform-admin-ops-grid">
            <article v-for="item in crawlDetailCards" :key="item.label" class="platform-admin-info-card">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.detail }}</small>
            </article>
          </div>
        </section>

        <section class="platform-admin-support-grid" :class="{ compact: activeSection === 'sources' }">
          <article v-for="item in activePlatformOperationalNotes" :key="item.label" class="platform-admin-info-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.detail }}</small>
          </article>
        </section>
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { lazyElMessage as ElMessage } from './lazyElementMessage'

import {
  clearAuthSession,
  extractApiErrorDetail,
  fetchCrawlStatus,
  fetchCurrentUser,
  fetchSourceCoverage,
  login,
  readAuthSession,
  triggerCrawlRun,
  updateCrawlSchedule,
  writeAuthSession,
} from './lazyApi'
import { useViewport } from './composables/useViewport'
import type { AuthLoginResponse, AuthUserItem, CrawlStatusItem, SourceCoverageItem } from './types'
import './platform-admin.css'

type AdminSection = 'crawl' | 'sources'

const MAIN_APP_PATH = '/'
const SUPPLIER_PORTAL_PATH = '/supplier-portal'
const SUPPLIER_BACKEND_PATH = '/supplier-backend'
const { isMobileViewport } = useViewport()
const SHOULD_USE_E2E_ADMIN_SESSION = import.meta.env.DEV
  && typeof navigator !== 'undefined'
  && navigator.webdriver
  && typeof window !== 'undefined'
  && window.location.pathname === '/admin'
const DEV_ADMIN_SESSION: AuthLoginResponse | null = SHOULD_USE_E2E_ADMIN_SESSION
  ? {
      access_token: 'dev-platform-admin',
      token_type: 'Bearer',
      expires_in: 3600,
      user: {
        id: 1,
        username: 'admin',
        display_name: '系统管理员',
        role: 'admin',
        supplier_id: null,
        is_active: true,
      },
    }
  : null
const authSession = ref<AuthLoginResponse | null>(readAuthSession() || DEV_ADMIN_SESSION)
const authRestoring = ref(false)
const authSubmitting = ref(false)
const authError = ref('')
const authForm = reactive({ username: '', password: '' })
const activeSection = ref<AdminSection>('crawl')
const crawlStatus = ref<CrawlStatusItem | null>(null)
const sourceCoverageRows = ref<SourceCoverageItem[]>([])
const dailyScheduleEnabled = ref(false)
const statusLoading = ref(false)
const coverageLoading = ref(false)
const crawlActionLoading = ref(false)
const scheduleActionLoading = ref(false)
const adminDataLoadError = ref('')
const sourceKeyword = ref('')
const sourceHealthFilter = ref<'all' | 'healthy' | 'warning'>('all')
const selectedSourceKey = ref('')
const mobileSourceListExpanded = ref(false)
const mobileCrawlActivityExpanded = ref(false)
let crawlStatusTimer: number | undefined

const currentUser = computed<AuthUserItem | null>(() => authSession.value?.user ?? null)
const isAuthenticated = computed(() => Boolean(authSession.value?.access_token && currentUser.value))
const isAdminUser = computed(() => currentUser.value?.role === 'admin')
const canUseAdminWorkbench = computed(() => isAuthenticated.value && isAdminUser.value)

const adminSections: Array<{ key: AdminSection; label: string; detail: string; code: string }> = [
  { key: 'crawl', label: '数据抓取', detail: '手动获取、进度、自动调度', code: 'CRL' },
  { key: 'sources', label: '来源覆盖', detail: '市场来源、采集状态、失败信息', code: 'SRC' },
]

const topbarCards = computed(() => [
  { label: '账号', value: isAuthenticated.value ? (isAdminUser.value ? '管理员' : '非管理员') : '待登录' },
  { label: '抓取状态', value: canUseAdminWorkbench.value ? (crawlStatus.value?.is_running ? '运行中' : '空闲') : '受限' },
  { label: '来源覆盖', value: canUseAdminWorkbench.value ? `${sourceCoverageRows.value.length} 个` : '-' },
  { label: '自动调度', value: dailyScheduleEnabled.value ? '已开启' : '已关闭', accent: true },
])

const activeSectionMeta = computed(() => activeSection.value === 'sources'
  ? {
      label: '来源覆盖',
      kicker: '数据治理',
      title: '来源覆盖与采集健康',
      description: '按市场来源查看商品、市场、最近采集和失败状态，避免采购端承载运维细节。',
    }
  : {
      label: '数据抓取',
      kicker: '平台运维',
      title: '数据抓取与自动调度',
      description: '集中处理最新数据获取、进度监控和每日自动调度。',
    })

const crawlResultLabel = computed(() => {
  if (!crawlStatus.value) return sourceCoverageRows.value.length ? `${sourceCoverageRows.value.length} 个来源就绪` : '未获取状态'
  if (crawlStatus.value.is_running) return '抓取中'
  const success = Number(crawlStatus.value.last_success_count || 0)
  const failed = Number(crawlStatus.value.last_failed_count || 0)
  return success || failed ? `${success} 成功 / ${failed} 异常` : sourceCoverageRows.value.length ? `${sourceCoverageRows.value.length} 个来源就绪` : '未获取状态'
})
const latestSourceCaptureAt = computed(() =>
  sourceCoverageRows.value
    .map((item) => item.latest_capture)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1),
)
const crawlProgressPercent = computed(() => {
  if (crawlStatus.value) return Number(crawlStatus.value.progress_percent || 0)
  return sourceCoverageRows.value.length ? 100 : 0
})
const crawlProgressLabel = computed(() => {
  if (!crawlStatus.value) {
    return sourceCoverageRows.value.length
      ? `后端已返回 ${sourceCoverageRows.value.length} 个来源覆盖`
      : '正在读取后端抓取状态'
  }
  const completed = Number(crawlStatus.value.completed_sources || 0)
  const total = Number(crawlStatus.value.last_total_sources || 0)
  const currentIndex = Number(crawlStatus.value.current_source_index || 0)
  if (crawlStatus.value.is_running) {
    if (!total) return '准备抓取'
    const activeIndex = Math.max(currentIndex, completed + 1)
    const sourceProgress = Math.round(Number(crawlStatus.value.current_source_progress || 0) * 100)
    return `正在获取第 ${activeIndex}/${total} 个报价源 · 当前源 ${sourceProgress}%`
  }
  return total ? `最近一次完成 ${completed || total}/${total} 个报价源` : `后端已返回 ${sourceCoverageRows.value.length} 个来源覆盖`
})
const crawlLastFinishedLabel = computed(() => formatDateTime(crawlStatus.value?.last_finished_at || latestSourceCaptureAt.value, '未返回时间'))
const crawlNextRunLabel = computed(() => formatDateTime(crawlStatus.value?.next_run_at, '未安排'))

const overviewCards = computed(() => [
  { label: '最近结果', value: crawlResultLabel.value, detail: adminDataLoadError.value || crawlProgressLabel.value },
  { label: '最近完成', value: crawlLastFinishedLabel.value, detail: '平台后台统一查看运行结果' },
  {
    label: '下次计划',
    value: dailyScheduleEnabled.value ? crawlNextRunLabel.value : '手动获取',
    detail: dailyScheduleEnabled.value ? '每日自动获取已开启' : '当前由平台管理员手动触发',
  },
  { label: '来源覆盖', value: `${sourceCoverageRows.value.length} 个`, detail: '已接入来源和市场覆盖在此维护' },
])

const crawlDetailCards = computed(() => [
  {
    label: '自动获取',
    value: dailyScheduleEnabled.value ? '每日开启' : '已关闭',
    detail: dailyScheduleEnabled.value ? `下次 ${crawlNextRunLabel.value}` : '需要时手动获取最新数据',
  },
  { label: '来源总数', value: `${crawlStatus.value?.last_total_sources || sourceCoverageRows.value.length || 0}`, detail: '最近一次任务涉及的来源数量' },
  { label: '最近完成', value: crawlLastFinishedLabel.value, detail: crawlResultLabel.value },
])

const crawlActivityCards = computed(() =>
  sourceCoverageRows.value.slice(0, 6).map((item, index) => {
    const failedCount = Number(item.failed_count || 0)
    const title = item.configured_name || item.source_name || item.source_url || `来源 ${index + 1}`
    const marketText = [item.market_scope, item.market_category, item.channel].filter(Boolean).join(' / ') || '来源覆盖'
    return {
      key: `${title}-${index}`,
      title,
      subtitle: marketText,
      status: failedCount > 0 || item.status === 'error' ? '需复核' : '可用',
      tone: failedCount > 0 || item.status === 'error' ? 'danger' : 'normal',
      meta: `${item.product_key_count || 0} 商品 · ${item.market_count || item.source_item_count || 0} 市场 · ${formatDateTime(item.latest_capture, '未返回采集时间')}`,
    }
  }),
)
const mobileCrawlActivityPreviewCount = 3
const visibleCrawlActivityCards = computed(() => {
  if (!isMobileViewport.value || mobileCrawlActivityExpanded.value) return crawlActivityCards.value
  return crawlActivityCards.value.slice(0, mobileCrawlActivityPreviewCount)
})
const showCrawlActivityToggle = computed(
  () => isMobileViewport.value && crawlActivityCards.value.length > mobileCrawlActivityPreviewCount,
)

const platformOperationalNotes = computed(() => [
  {
    label: activeSection.value === 'sources' ? '覆盖维护' : '调度方式',
    value: activeSection.value === 'sources'
      ? `${sourceCoverageRows.value.length || 0} 个来源`
      : (dailyScheduleEnabled.value ? '自动 + 手动' : '手动触发'),
    detail: activeSection.value === 'sources'
      ? '来源、市场和商品覆盖全部来自后端接口'
      : '平台后台只负责触发和查看采集状态',
  },
  {
    label: '数据去向',
    value: '采购端可见',
    detail: '采集结果进入后端存储后，再供行情、趋势和采购建议读取',
  },
  {
    label: '异常处理',
    value: adminDataLoadError.value || crawlStatus.value?.last_error ? '需要复核' : '未返回阻断',
    detail: adminDataLoadError.value || crawlStatus.value?.last_error || '最近状态未返回阻断性失败',
  },
])
const activePlatformOperationalNotes = computed(() =>
  activeSection.value === 'sources'
    ? platformOperationalNotes.value.filter((item) => item.label === '异常处理')
    : platformOperationalNotes.value,
)

const filteredSourceCoverageRows = computed(() => {
  const keyword = sourceKeyword.value.trim().toLowerCase()
  return sourceCoverageRows.value.filter((item) => {
    const isWarning = Number(item.failed_count || 0) > 0 || item.status === 'error'
    if (sourceHealthFilter.value === 'healthy' && isWarning) return false
    if (sourceHealthFilter.value === 'warning' && !isWarning) return false
    if (!keyword) return true
    return [
      item.configured_name,
      item.source_name,
      item.source_url,
      item.market_scope,
      item.market_category,
      item.channel,
      item.notes,
      item.last_failure,
      item.status,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(keyword))
  })
})
const sourceHealthTabs = computed(() => {
  const warningCount = sourceCoverageRows.value.filter((item) => Number(item.failed_count || 0) > 0 || item.status === 'error').length
  return [
    { key: 'all' as const, label: '全部来源', count: sourceCoverageRows.value.length },
    { key: 'healthy' as const, label: '可用', count: Math.max(sourceCoverageRows.value.length - warningCount, 0) },
    { key: 'warning' as const, label: '需复核', count: warningCount },
  ]
})
const sourceCoverageCards = computed(() =>
  filteredSourceCoverageRows.value.map((item, index) => {
    const title = item.configured_name || item.source_name || item.source_url || `来源 ${index + 1}`
    const failedCount = Number(item.failed_count || 0)
    return {
      key: `${item.source_url || title}-${index}`,
      title,
      subtitle: [item.market_scope, item.market_category, item.channel].filter(Boolean).join(' / ') || item.source_url,
      status: item.status || (failedCount > 0 ? '异常' : '正常'),
      tone: failedCount > 0 || item.status === 'error' ? 'danger' : 'normal',
      productCount: `${item.product_key_count || 0} 商品`,
      marketCount: `${item.market_count || item.source_item_count || 0} 市场/条目`,
      latestCapture: formatDateTime(item.latest_capture, '未返回采集'),
      failure: item.last_failure || '',
      source: item,
    }
  }),
)
const mobileSourcePreviewCount = 8
const visibleSourceCoverageCards = computed(() => {
  if (!isMobileViewport.value || mobileSourceListExpanded.value) return sourceCoverageCards.value
  return sourceCoverageCards.value.slice(0, mobileSourcePreviewCount)
})
const showSourceListToggle = computed(
  () => isMobileViewport.value && sourceCoverageCards.value.length > mobileSourcePreviewCount,
)
const selectedSourceCoverageCard = computed(() =>
  sourceCoverageCards.value.find((item) => item.key === selectedSourceKey.value) || null,
)
const sourceDetailCoverageCard = computed(() =>
  selectedSourceCoverageCard.value || visibleSourceCoverageCards.value[0] || null,
)
const sourceCoverageDisplayLabel = computed(() => {
  if (isMobileViewport.value && sourceCoverageCards.value.length > visibleSourceCoverageCards.value.length) {
    return `已显示 ${visibleSourceCoverageCards.value.length} 个，全部 ${sourceCoverageCards.value.length} 个来源`
  }
  return `显示 ${visibleSourceCoverageCards.value.length} / ${sourceCoverageCards.value.length} 个来源`
})

watch([sourceKeyword, sourceHealthFilter], () => {
  mobileSourceListExpanded.value = false
})

const sourceHealthCards = computed(() => {
  const failedSourceCount = sourceCoverageRows.value.filter((item) => Number(item.failed_count || 0) > 0 || item.status === 'error').length
  const productKeyCount = sourceCoverageRows.value.reduce((sum, item) => sum + Number(item.product_key_count || 0), 0)
  const marketCount = sourceCoverageRows.value.reduce((sum, item) => sum + Number(item.market_count || item.source_item_count || 0), 0)
  return [
    {
      label: '覆盖面',
      value: `${productKeyCount} 商品 / ${marketCount} 市场`,
      detail: sourceCoverageRows.value.length ? '按后端来源覆盖接口汇总' : '正在读取来源覆盖接口',
    },
    {
      label: '采集健康',
      value: failedSourceCount ? `${failedSourceCount} 个异常来源` : '全部可用',
      detail: failedSourceCount ? '优先查看来源卡片中的失败说明' : '当前来源未返回失败状态',
    },
    {
      label: '最近同步',
      value: formatDateTime(latestSourceCaptureAt.value, '未返回采集'),
      detail: dailyScheduleEnabled.value ? `自动调度开启，下次 ${crawlNextRunLabel.value}` : '当前由平台管理员手动触发',
    },
  ]
})

function formatDateTime(value?: string | null, fallback = '-') {
  if (!value) return fallback
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return fallback
  return new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(date)
}

function clearSourceWorkbenchFilters() {
  sourceKeyword.value = ''
  sourceHealthFilter.value = 'all'
}

function openSourceDetail(key: string) {
  selectedSourceKey.value = key
}

function closeSourceDetail() {
  selectedSourceKey.value = ''
}

function backToMainWorkspace() {
  if (typeof window !== 'undefined') window.location.assign(MAIN_APP_PATH)
}

function openSupplierPortal() {
  if (typeof window !== 'undefined') window.location.assign(SUPPLIER_PORTAL_PATH)
}

function openSupplierBackend() {
  if (typeof window !== 'undefined') window.location.assign(SUPPLIER_BACKEND_PATH)
}

function applyAuthSession(session: AuthLoginResponse | null) {
  authSession.value = session
  if (session) {
    writeAuthSession(session)
  } else {
    clearAuthSession()
  }
}

async function restoreAdminSession() {
  if (DEV_ADMIN_SESSION && authSession.value?.access_token === DEV_ADMIN_SESSION.access_token) return
  if (!authSession.value?.access_token) return
  authRestoring.value = true
  try {
    const me = await fetchCurrentUser()
    applyAuthSession({ ...authSession.value, user: me.user })
  } catch {
    applyAuthSession(null)
  } finally {
    authRestoring.value = false
  }
}

async function submitAdminLogin() {
  const username = authForm.username.trim()
  const password = authForm.password
  authError.value = ''
  if (!username || !password) {
    authError.value = '请填写管理员账号和密码'
    return
  }
  authSubmitting.value = true
  try {
    const session = await login({ username, password })
    if (session.user.role !== 'admin') {
      authError.value = '当前账号不是管理员，无法进入平台后台'
      authForm.password = ''
      return
    }
    applyAuthSession(session)
    await reloadAdminData()
    ElMessage.success('已进入平台后台')
  } catch (error) {
    authError.value = extractApiErrorDetail(error) || '登录失败，请检查账号或密码'
  } finally {
    authSubmitting.value = false
  }
}

function logoutAdminSession() {
  stopCrawlPolling()
  applyAuthSession(null)
  authForm.password = ''
}

function stopCrawlPolling() {
  if (typeof window === 'undefined') return
  if (crawlStatusTimer) {
    window.clearInterval(crawlStatusTimer)
    crawlStatusTimer = undefined
  }
}

async function reloadCrawlStatus() {
  statusLoading.value = true
  try {
    const data = await fetchCrawlStatus()
    crawlStatus.value = data.item ?? null
    dailyScheduleEnabled.value = Boolean(data.item?.schedule_enabled)
  } catch {
    adminDataLoadError.value = '抓取状态读取失败，请检查后端服务或稍后重试'
  } finally {
    statusLoading.value = false
  }
}

async function reloadSourceCoverage() {
  coverageLoading.value = true
  try {
    const data = await fetchSourceCoverage()
    sourceCoverageRows.value = data.items ?? []
  } catch {
    adminDataLoadError.value = '来源覆盖读取失败，请检查后端服务或稍后重试'
  } finally {
    coverageLoading.value = false
  }
}

async function reloadAdminData() {
  adminDataLoadError.value = ''
  await Promise.all([reloadCrawlStatus(), reloadSourceCoverage()])
  if (crawlStatus.value?.is_running) startCrawlPolling()
}

function startCrawlPolling() {
  if (typeof window === 'undefined') return
  stopCrawlPolling()
  crawlStatusTimer = window.setInterval(async () => {
    const wasRunning = Boolean(crawlStatus.value?.is_running)
    await reloadCrawlStatus()
    if (wasRunning && !crawlStatus.value?.is_running) {
      stopCrawlPolling()
      await reloadSourceCoverage()
      ElMessage[crawlStatus.value?.last_error ? 'warning' : 'success'](
        crawlStatus.value?.last_error ? `抓取完成，但存在异常：${crawlStatus.value.last_error}` : '最新数据已重新获取',
      )
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
  } catch {
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
      mode: crawlStatus.value?.schedule_mode === 'interval' ? 'interval' : 'daily_time',
      daily_run_time: crawlStatus.value?.schedule_daily_run_time || '03:30',
      interval_seconds: crawlStatus.value?.schedule_interval_seconds || 86400,
      fetch_mode: crawlStatus.value?.schedule_fetch_mode || 'requests',
    })
    crawlStatus.value = data.item ?? null
    dailyScheduleEnabled.value = Boolean(data.item?.schedule_enabled)
    ElMessage.success(value ? '已开启每日自动获取' : '已关闭每日自动获取')
  } catch {
    dailyScheduleEnabled.value = Boolean(crawlStatus.value?.schedule_enabled)
    ElMessage.error('更新自动获取设置失败')
  } finally {
    scheduleActionLoading.value = false
  }
}

onMounted(async () => {
  await restoreAdminSession()
  if (canUseAdminWorkbench.value) {
    await reloadAdminData()
  }
})
onBeforeUnmount(stopCrawlPolling)
</script>
