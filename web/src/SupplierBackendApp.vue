<template>
  <section
    class="app-shell supplier-backend-shell"
    :class="{ mobile: isMobileViewport, 'auth-only': !isAuthenticated }"
    data-testid="supplier-backend-screen"
  >
    <main v-if="!isAuthenticated && !authRestoring" class="supplier-backend-auth-page" data-testid="supplier-auth-shell">
      <div class="market-auth-form supplier-backend-login-card supplier-backend-auth-card" data-testid="supplier-login-form">
        <div v-if="hasProcurementCarryContext" class="supplier-backend-context-strip" data-testid="supplier-carry-context">
          <span>{{ procurementCarrySourceLabel }}</span>
          <strong>{{ selectedProductLabel || '未指定商品' }}</strong>
          <small>{{ procurementCarryHint }}</small>
        </div>
        <div class="supplier-backend-auth-foot">
          <span>用公司账号登录。</span>
        </div>

        <strong>账号登录</strong>
        <input v-model="authForm.username" class="supplier-native-input" data-testid="auth-username-input" autocomplete="username" placeholder="账号" />
        <span class="supplier-native-password-field">
          <input
          v-model="authForm.password"
          data-testid="auth-password-input"
          :type="authPasswordVisible ? 'text' : 'password'"
          autocomplete="current-password"
          placeholder="密码"
          @keyup.enter="submitAuthLogin"
          />
          <button type="button" :aria-label="authPasswordVisible ? '隐藏密码' : '显示密码'" @click="authPasswordVisible = !authPasswordVisible">
            {{ authPasswordVisible ? '隐藏' : '显示' }}
          </button>
        </span>
        <p v-if="authError" class="market-auth-error">{{ authError }}</p>
        <div class="market-auth-actions">
          <button type="button" class="supplier-native-button primary" data-testid="auth-login-button" :disabled="authSubmitting" @click="submitAuthLogin">{{ authSubmitting ? '登录中' : '登录' }}</button>
        </div>
        <div class="supplier-backend-auth-foot">
          <button type="button" @click="showPasswordHelp">忘记密码</button>
        </div>
      </div>
    </main>

    <el-dialog v-if="passwordResetVisible" v-model="passwordResetVisible" title="重置密码" width="min(92vw, 420px)">
      <div class="market-auth-form supplier-backend-reset-form">
        <small>输入账号、旧密码和新密码。</small>
        <el-input v-model="passwordResetForm.username" placeholder="账号" autocomplete="username" />
        <el-input v-model="passwordResetForm.current_password" type="password" show-password placeholder="当前密码" autocomplete="current-password" />
        <el-input v-model="passwordResetForm.new_password" type="password" show-password placeholder="新密码，至少 8 位" autocomplete="new-password" @keyup.enter="submitPasswordReset" />
        <p v-if="passwordResetError" class="market-auth-error">{{ passwordResetError }}</p>
        <div class="market-auth-actions">
          <el-button plain @click="passwordResetVisible = false">取消</el-button>
          <el-button type="primary" :loading="passwordResetSubmitting" @click="submitPasswordReset">确认重置</el-button>
        </div>
      </div>
    </el-dialog>

    <template v-if="isAuthenticated || authRestoring">
    <header class="panel supplier-backend-topbar">
      <div class="supplier-backend-brand">
        <div class="supplier-backend-brand-mark">档</div>
        <div class="supplier-backend-brand-copy">
          <p class="panel-kicker">供应商管理</p>
          <strong>供应商管理</strong>
        </div>
      </div>
      <div class="supplier-backend-topbar-actions">
        <div v-if="currentUser" class="supplier-backend-chip" data-testid="auth-session-status">
          <span>当前账号</span>
          <strong>{{ currentUser.display_name || currentUser.username }}</strong>
          <small>{{ currentAuthScopeLabel }}</small>
        </div>
        <div class="supplier-backend-chip accent">
          <span>账号类型</span>
          <strong>{{ currentAuthRoleLabel }}</strong>
        </div>
        <el-button v-if="isAuthenticated" plain @click="logoutAuthSession">退出登录</el-button>
        <el-button v-if="showBackendContextActions" plain @click="backToProcurementProduct">回采购看同品</el-button>
        <el-button v-if="resolvedBackendSection !== 'quote'" plain @click="setBackendSection('quote')">{{ quoteActionLabel }}</el-button>
        <el-button plain @click="backToMainWorkspace">返回主工作台</el-button>
      </div>
    </header>

    <div class="supplier-backend-frame" :class="{ mobile: isMobileViewport }">
      <aside class="panel supplier-backend-sidebar">
        <div class="supplier-backend-sidebar-head">
          <p class="panel-kicker">控制台</p>
          <h2>导航</h2>
        </div>

        <div class="supplier-backend-sidebar-section">
          <div class="supplier-backend-sidebar-section-head">
            <strong>核心功能</strong>
          </div>
          <div class="supplier-backend-nav-list">
            <button
              v-for="item in backendTabEntries"
              :key="item.key"
              type="button"
              class="supplier-backend-nav-item"
              :class="{ active: resolvedBackendSection === item.key, disabled: item.disabled }"
              :disabled="item.disabled"
              @click="setBackendSection(item.key)"
            >
              <div class="supplier-backend-nav-item-head">
                <strong>{{ item.label }}</strong>
                <span>{{ item.code }}</span>
              </div>
              <em>{{ item.detail }}</em>
            </button>
          </div>
        </div>

        <div v-if="backendSecondaryEntries.length" class="supplier-backend-sidebar-section">
          <div class="supplier-backend-sidebar-section-head">
            <strong>更多</strong>
          </div>
          <div class="supplier-backend-nav-list secondary">
            <button
              v-for="item in backendSecondaryEntries"
              :key="item.key"
              type="button"
              class="supplier-backend-nav-item secondary"
              :class="{ active: resolvedBackendSection === item.key }"
              @click="setBackendSection(item.key)"
            >
              <div class="supplier-backend-nav-item-head">
                <strong>{{ item.label }}</strong>
              </div>
              <em>{{ item.detail }}</em>
            </button>
          </div>
        </div>
      </aside>

      <section class="supplier-backend-stage">
        <header v-if="isAuthenticated && !isCompactWorkspaceSection" class="panel supplier-backend-pagebar" :class="{ compact: isCompactWorkspaceSection }">
          <div class="supplier-backend-pagebar-copy">
            <p class="panel-kicker">{{ isAuthenticated ? '当前页面' : '登录' }}</p>
            <h1>{{ isAuthenticated ? activeBackendTabMeta.title : '登录' }}</h1>
            <div v-if="isAuthenticated" class="supplier-backend-pagebar-meta">
              <span v-for="item in backendWorkspaceTags" :key="item">{{ item }}</span>
            </div>
          </div>
          <div v-if="isAuthenticated" class="supplier-backend-pagebar-side">
            <div class="supplier-backend-pagebar-tags">
              <span>{{ currentAuthRoleLabel }}</span>
              <span>{{ selectedLocationLabel }}</span>
              <span>{{ selectedProductLabel || '未选商品' }}</span>
            </div>
            <div class="supplier-backend-pagebar-actions">
              <el-button type="primary" @click="setBackendSection(primaryBackendActionSection)">{{ primaryBackendActionLabel }}</el-button>
              <el-button plain @click="setBackendSection(secondaryBackendActionSection)">{{ secondaryBackendActionLabel }}</el-button>
            </div>
          </div>
          <div v-else class="supplier-backend-pagebar-login-tip">
            <span>输入账号密码</span>
          </div>
        </header>

        <section
          v-if="isAuthenticated && !isCompactWorkspaceSection"
          class="supplier-backend-overview-grid"
          :class="{ compact: isCompactWorkspaceSection }"
        >
          <article v-for="item in backendOverviewCards" :key="item.label" class="supplier-backend-overview-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </article>
        </section>

        <section
          v-if="isAuthenticated && !isCompactWorkspaceSection"
          class="supplier-backend-command-strip"
          :class="{ compact: isCompactWorkspaceSection }"
        >
          <article v-for="item in backendCommandCards" :key="item.label" class="supplier-backend-command-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </article>
        </section>

        <section class="panel supplier-backend-panel" :class="{ 'auth-screen': !isAuthenticated && !authRestoring }" data-testid="supplier-auth-shell">
          <div v-if="hasProcurementCarryContext" class="supplier-backend-context-strip stage" data-testid="supplier-carry-context">
            <span>{{ procurementCarrySourceLabel }}</span>
            <strong>{{ selectedProductLabel || '未指定商品' }}</strong>
            <small>{{ procurementCarryHint }}</small>
          </div>
          <template v-if="authRestoring">
            <div class="market-auth-copy">
              <p class="panel-kicker">登录</p>
              <h2>正在进入</h2>
            </div>
          </template>

          <template v-else-if="!isAuthenticated">
            <div class="market-auth-form supplier-backend-login-card" data-testid="supplier-login-form">
              <div class="supplier-backend-login-head">
                <div>
                  <strong>账号登录</strong>
                </div>
              </div>
              <input v-model="authForm.username" class="supplier-native-input" data-testid="auth-username-input" autocomplete="username" placeholder="账号" />
              <span class="supplier-native-password-field">
                <input
                v-model="authForm.password"
                data-testid="auth-password-input"
                :type="authPasswordVisible ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="密码"
                @keyup.enter="submitAuthLogin"
                />
                <button type="button" :aria-label="authPasswordVisible ? '隐藏密码' : '显示密码'" @click="authPasswordVisible = !authPasswordVisible">
                  {{ authPasswordVisible ? '隐藏' : '显示' }}
                </button>
              </span>
              <p v-if="authError" class="market-auth-error">{{ authError }}</p>
              <div class="market-auth-actions">
                <button type="button" class="supplier-native-button primary" data-testid="auth-login-button" :disabled="authSubmitting" @click="submitAuthLogin">{{ authSubmitting ? '登录中' : '登录' }}</button>
              </div>
              <div class="supplier-backend-auth-foot">
                <span>没有账号请联系负责人。</span>
                <button type="button" @click="showPasswordHelp">忘记密码</button>
              </div>
            </div>
          </template>

          <template v-else>
            <AccountAdminPanel
              v-if="resolvedBackendSection === 'accounts'"
              :current-user-id="currentUser?.id"
            />
            <SupplierAdminPanel
              v-else
              :product-options="productOptions"
              :selected-identity-key="selectedIdentityKey"
              :selected-product-label="selectedProductLabel"
              :procurement-source-label="procurementSourceLabel"
              :procurement-source-type="initialCarrySource"
              :mobile="isMobileViewport"
              :auth-role="currentAuthRole"
              :auth-supplier-id="currentAuthSupplierId"
              :auth-display-name="currentAuthDisplayName"
              :backend-section="resolvedBackendSection"
              :show-embedded-tabs="false"
              @select-product="handleSelectProduct"
              @navigate-section="setBackendSection"
              @open-procurement-product="backToProcurementProduct"
            />
          </template>
        </section>
      </section>
    </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, reactive, ref, watch } from 'vue'

import {
  clearAuthSession,
  dataSourceState,
  extractApiErrorDetail,
  fetchCurrentUser,
  fetchLocationOptions,
  fetchProductOptions,
  login,
  readAuthSession,
  resetAuthPassword,
  writeAuthSession,
} from './lazyApi'
import { useViewport } from './composables/useViewport'
import { lazyElMessage } from './lazyElementMessage'
import type {
  AuthLoginResponse,
  AuthUserItem,
  ProductOptionItem,
} from './types'

const MAIN_APP_PATH = '/'
const AccountAdminPanel = defineAsyncComponent(() => import('./components/AccountAdminPanel.vue'))
const SupplierAdminPanel = defineAsyncComponent(() => import('./components/SupplierAdminPanel.vue'))
type BackendSection = 'suppliers' | 'accounts' | 'quote' | 'settlement' | 'logs'
const { isMobileViewport } = useViewport()
const searchParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams()
const initialProductIdentityKey = searchParams.get('identity_key') || searchParams.get('product') || searchParams.get('price_identity_key') || ''
const initialProductLabel = searchParams.get('product_label') || searchParams.get('label') || ''
const initialCarrySource = searchParams.get('source') || ''
const initialCarryTitle = searchParams.get('context_title') || ''
const initialAlertRule = searchParams.get('alert_rule') || ''

const authSession = ref<AuthLoginResponse | null>(readAuthSession())
const authSubmitting = ref(false)
const authRestoring = ref(false)
const authError = ref('')
const authForm = reactive({
  username: '',
  password: '',
})
const authPasswordVisible = ref(false)
const passwordResetVisible = ref(false)
const passwordResetSubmitting = ref(false)
const passwordResetError = ref('')
const passwordResetForm = reactive({
  username: '',
  current_password: '',
  new_password: '',
})
const provinces = ref<string[]>([])
const cities = ref<string[]>([])
const productOptions = ref<ProductOptionItem[]>([])
const selectedIdentityKey = ref(initialProductIdentityKey)
const selectedProductFallbackLabel = ref(initialProductLabel)
const backendSection = ref<BackendSection>((searchParams.get('section') as BackendSection) || (initialProductIdentityKey ? 'quote' : 'suppliers'))

const currentUser = computed<AuthUserItem | null>(() => authSession.value?.user ?? null)
const isAuthenticated = computed(() => Boolean(authSession.value?.access_token && currentUser.value))
const currentAuthRole = computed(() => currentUser.value?.role ?? null)
const currentAuthSupplierId = computed(() => currentUser.value?.supplier_id ?? null)
const currentAuthDisplayName = computed(() => currentUser.value?.display_name || currentUser.value?.username || '')
const authRoleHint = computed(() => '管理员管理供应商；供应商填写报价。')
const currentAuthRoleLabel = computed(() => {
  if (!isAuthenticated.value) {
    return '待登录'
  }
  return currentAuthRole.value === 'admin' ? '管理员' : '供应商'
})
const currentAuthScopeLabel = computed(() => {
  if (!isAuthenticated.value) {
    return '还未登录'
  }
  if (currentAuthRole.value === 'admin') {
    return '可管理所有供应商'
  }
  const supplierName = currentUser.value?.supplier_profile?.supplier_name || ''
  return supplierName ? `当前供应商：${supplierName}` : '还没有分配供应商'
})
const selectedProductLabel = computed(() => {
  const current = productOptions.value.find((item) => item.price_identity_key === selectedIdentityKey.value)
  return current?.price_identity_label || selectedProductFallbackLabel.value
})
const selectedLocationLabel = computed(() => cities.value[0] || provinces.value[0] || '全部市场')
const hasProcurementCarryContext = computed(() => initialCarrySource === 'price_alert' || initialCarrySource === 'menu_plan' || Boolean(initialProductLabel || initialCarryTitle))
const procurementCarrySourceLabel = computed(() => {
  if (initialCarrySource === 'price_alert') return '从价格预警带入'
  if (initialCarrySource === 'menu_plan') return '从菜单采购带入'
  return '从采购工作台带入'
})
const procurementCarryHint = computed(() => {
  if (initialCarrySource === 'price_alert') {
    return initialAlertRule ? `登录后进入报价管理处理预警规则：${initialAlertRule}` : '登录后进入报价管理补录/复核该预警商品报价'
  }
  if (initialCarrySource === 'menu_plan') return '登录后进入报价管理补录菜单采购缺失报价'
  return '登录后将保留当前商品上下文'
})
const procurementSourceLabel = computed(() => {
  const sourceName = searchParams.get('source_name') || ''
  const topCategory = searchParams.get('liancai_top_category') || ''
  const subcategory = searchParams.get('liancai_subcategory') || ''
  return [sourceName, topCategory, subcategory].filter(Boolean).join(' / ')
})
const backendTabs: Array<{ key: BackendSection; label: string; detail: string; code: string; adminOnly?: boolean }> = [
  { key: 'suppliers', label: '供应商管理', detail: '档案与账号', code: 'SUP', adminOnly: true },
  { key: 'accounts', label: '账号管理', detail: '用户与权限', code: 'ACC', adminOnly: true },
  { key: 'quote', label: '报价管理', detail: '报价与商品', code: 'QTE' },
  { key: 'settlement', label: '结算台账', detail: '账期与付款', code: 'SET' },
  { key: 'logs', label: '操作日志', detail: '导入导出与留痕', code: 'LOG' },
]
function normalizeBackendSectionForRole(section: BackendSection): BackendSection {
  if (currentAuthRole.value === 'supplier' && section !== 'quote' && section !== 'settlement') {
    return 'quote'
  }
  if (currentAuthRole.value === 'procurement' && section === 'accounts') {
    return 'suppliers'
  }
  return section
}

const resolvedBackendSection = computed<BackendSection>(() => normalizeBackendSectionForRole(backendSection.value))
const backendTabEntries = computed(() =>
  backendTabs
    .filter((item) => {
      if (currentAuthRole.value === 'supplier') {
        return item.key === 'quote' || item.key === 'settlement'
      }
      if (currentAuthRole.value === 'procurement') {
        return item.key === 'suppliers' || item.key === 'quote' || item.key === 'settlement'
      }
      return item.key === 'suppliers' || item.key === 'accounts' || item.key === 'quote' || item.key === 'settlement'
    })
    .map((item) => ({
      ...item,
      label: currentAuthRole.value === 'supplier' && item.key === 'settlement' ? '我的结算' : (currentAuthRole.value === 'supplier' && item.key === 'quote' ? '我的报价' : item.label),
      detail: currentAuthRole.value === 'supplier'
        ? (item.key === 'quote' ? '录价、导入、草稿和历史' : '账期、付款和对账')
        : (
          item.key === 'suppliers' ? '创建供应商、启停和账号绑定'
            : item.key === 'accounts' ? '维护管理员、供应商账号和启停状态'
              : item.key === 'quote' ? '录价、代录和报价历史'
                : item.key === 'settlement' ? '账期、付款和结算明细'
                  : '导入导出和操作留痕'
        ),
      disabled: false,
    })),
)
const backendSecondaryEntries = computed(() => {
  if (currentAuthRole.value === 'supplier') return []
  if (currentAuthRole.value === 'procurement') {
    return [
      {
        key: 'logs' as const,
        label: '操作日志',
        detail: '查看当前团队供应商留痕',
      },
    ]
  }
  return [
    {
      key: 'accounts' as const,
      label: '账号管理',
      detail: '管理账号和权限',
    },
    {
      key: 'logs' as const,
      label: '操作日志',
      detail: '查看留痕和导入导出记录',
    },
  ]
})
const activeBackendTabMeta = computed(() => {
  if (resolvedBackendSection.value === 'quote') {
    return {
      title: '报价管理',
      description: '集中处理商品报价、管理员代录、供应商自助录价和批量导入。',
    }
  }
  if (resolvedBackendSection.value === 'accounts') {
    return {
      title: '账号管理',
      description: '维护管理员和供应商账号、启停状态和密码重置。',
    }
  }
  if (resolvedBackendSection.value === 'settlement') {
    return {
      title: '结算台账',
      description: '集中查看账期、金额、付款状态和结算详情。',
    }
  }
  if (resolvedBackendSection.value === 'logs') {
    return {
      title: '操作日志',
      description: '查看导入、导出、复制、作废和结算动作留痕。',
    }
  }
  return {
    title: '供应商管理',
    description: '维护供应商管理、账号状态以及主营分类和渠道信息。',
  }
})
const isCompactWorkspaceSection = computed(
  () =>
    resolvedBackendSection.value === 'quote'
    || resolvedBackendSection.value === 'suppliers'
    || resolvedBackendSection.value === 'settlement'
    || resolvedBackendSection.value === 'logs',
)
const primaryBackendActionSection = computed<BackendSection>(() => {
  if (!isAuthenticated.value) return 'quote'
  return currentAuthRole.value === 'supplier' ? 'quote' : 'suppliers'
})
const secondaryBackendActionSection = computed<BackendSection>(() => {
  if (!isAuthenticated.value) return 'logs'
  return resolvedBackendSection.value === 'quote' ? 'settlement' : 'quote'
})
const primaryBackendActionLabel = computed(() => {
  if (!isAuthenticated.value) return '默认查看报价管理'
  return currentAuthRole.value === 'supplier' ? '进入报价管理' : '进入供应商管理'
})
const secondaryBackendActionLabel = computed(() =>
  secondaryBackendActionSection.value === 'settlement' ? '查看结算台账' : '切到商品报价',
)
const backendShellCards = computed(() => [
  {
    label: '账号类型',
    value: isAuthenticated.value ? (currentAuthRole.value === 'admin' ? '管理员' : '供应商') : '待登录',
    detail: isAuthenticated.value ? currentAuthRoleLabel.value : '登录后显示可用功能',
  },
  {
    label: '可看内容',
    value: isAuthenticated.value ? (currentAuthRole.value === 'admin' ? '全局供应' : '绑定供应商') : '未验证',
    detail: isAuthenticated.value ? currentAuthScopeLabel.value : '未登录时只能看登录入口',
  },
  {
    label: '当前分区',
    value: isAuthenticated.value ? activeBackendTabMeta.value.title : '账号登录',
    detail: isAuthenticated.value ? activeBackendTabMeta.value.description : '登录后进入',
  },
])
const backendOverviewCards = computed(() => [
  {
    label: '当前页面',
    value: activeBackendTabMeta.value.title,
    detail: activeBackendTabMeta.value.description,
  },
  {
    label: '当前地区',
    value: selectedLocationLabel.value,
    detail: '当前供应上下文默认跟随本地市场筛选',
  },
  {
    label: '当前商品',
    value: selectedProductLabel.value || '未指定商品',
    detail: '报价工作台会优先围绕当前商品查看和代录',
  },
  {
    label: '账号范围',
    value: currentUser.value?.display_name || currentUser.value?.username || '未登录',
    detail: currentAuthScopeLabel.value,
  },
])
const backendWorkspaceTags = computed(() => [
  `地区：${selectedLocationLabel.value}`,
  ...(resolvedBackendSection.value === 'quote' && selectedProductLabel.value ? [`当前商品：${selectedProductLabel.value}`] : []),
])
const showBackendContextActions = computed(() => resolvedBackendSection.value === 'quote' && Boolean(selectedIdentityKey.value))
const quoteActionLabel = computed(() => currentAuthRole.value === 'supplier' ? '进入我的报价' : '进入报价管理')
const loginMetricCards = computed(() => [
  {
    label: '账号登录',
    value: '已接入',
    detail: '用公司账号登录。',
  },
  {
    label: '供应分区',
    value: '4 个',
    detail: '档案、报价管理、结算、日志都能直接使用。',
  },
  {
    label: '当前上下文',
    value: selectedProductLabel.value || '多品类',
    detail: '继续处理当前商品。',
  },
])
const loginSceneCards = computed(() => [
  {
    kicker: '管理员',
    title: '管理员管理供应商',
    detail: '维护资料、录价、看结算。',
  },
  {
    kicker: '供应商',
    title: '供应商填写报价',
    detail: '录价、导入、看记录。',
  },
  {
    kicker: '账号状态',
    title: '停用后不能登录',
    detail: '账号停用即失效。',
  },
])
const loginChecklist = computed(() => [
  {
    step: '01',
    title: '管理员看供应商',
    detail: '供应商、报价、结算。',
  },
  {
    step: '02',
    title: '供应商填报价',
    detail: '录价、导入、看记录。',
  },
  {
    step: '03',
    title: '停用后不能登录',
    detail: '账号停用即失效。',
  },
])
const backendCommandCards = computed(() => [
  {
    label: '推荐动作',
    value: isAuthenticated.value ? (currentAuthRole.value === 'admin' ? '先看供应商再切报价' : '直接进入报价工作台') : '先登录',
    detail: isAuthenticated.value
      ? (currentAuthRole.value === 'admin'
          ? '管理员适合从供应商主列表开始，再切结算和日志。'
          : '进入报价页面。')
      : '登录后进入。',
  },
  {
    label: '当前账号',
    value: isAuthenticated.value ? (currentUser.value?.display_name || currentUser.value?.username || '未登录') : '未登录',
    detail: isAuthenticated.value ? currentAuthScopeLabel.value : '输入公司账号。',
  },
  {
    label: '当前焦点',
    value:
      resolvedBackendSection.value === 'quote'
        ? '报价管理与代录'
        : resolvedBackendSection.value === 'settlement'
          ? '账期与付款'
          : resolvedBackendSection.value === 'logs'
            ? '操作留痕'
            : resolvedBackendSection.value === 'accounts'
              ? '账号与权限'
              : '供应商管理',
    detail: activeBackendTabMeta.value.description,
  },
])

function applyAuthSession(session: AuthLoginResponse | null) {
  authSession.value = session
  authError.value = ''
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
  authRestoring.value = true
  try {
    const me = await fetchCurrentUser()
    applyAuthSession({
      ...authSession.value,
      user: me.user,
    })
  } catch {
    applyAuthSession(null)
  } finally {
    authRestoring.value = false
  }
}

async function submitAuthLogin() {
  authError.value = ''
  if (!authForm.username.trim() || !authForm.password.trim()) {
    authError.value = '请先填写账号和密码'
    return
  }
  authSubmitting.value = true
  try {
    const session = await login({
      username: authForm.username.trim(),
      password: authForm.password,
    })
    applyAuthSession(session)
    authForm.password = ''
    await loadBackendContext()
    lazyElMessage.success(`已登录为${session.user.display_name || session.user.username}`)
  } catch (error) {
    authError.value = extractApiErrorDetail(error) || dataSourceState.lastError || '登录失败，请检查账号和密码'
  } finally {
    authSubmitting.value = false
  }
}

async function logoutAuthSession() {
  applyAuthSession(null)
  authForm.password = ''
  lazyElMessage.success('已退出登录')
}

function showPasswordHelp() {
  passwordResetError.value = ''
  passwordResetForm.username = authForm.username.trim()
  passwordResetForm.current_password = ''
  passwordResetForm.new_password = ''
  passwordResetVisible.value = true
}

async function submitPasswordReset() {
  const username = passwordResetForm.username.trim()
  const currentPassword = passwordResetForm.current_password
  const newPassword = passwordResetForm.new_password
  if (!username || !currentPassword || !newPassword) {
    passwordResetError.value = '请填写账号、当前密码和新密码'
    return
  }
  if (newPassword.length < 8) {
    passwordResetError.value = '新密码至少 8 位'
    return
  }
  passwordResetSubmitting.value = true
  passwordResetError.value = ''
  try {
    const session = await resetAuthPassword({
      username,
      current_password: currentPassword,
      new_password: newPassword,
    })
    applyAuthSession(session)
    authForm.username = username
    authForm.password = ''
    passwordResetVisible.value = false
    lazyElMessage.success('密码已重置')
  } catch (error) {
    passwordResetError.value = extractApiErrorDetail(error) || dataSourceState.lastError || '密码重置失败'
  } finally {
    passwordResetSubmitting.value = false
  }
}

function backToMainWorkspace() {
  if (typeof window !== 'undefined') {
    window.location.assign(`${MAIN_APP_PATH}?mode=workspace&tab=summary`)
  }
}

function backToProcurementProduct() {
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams()
    params.set('mode', 'workspace')
    params.set('tab', 'trend')
    params.set('identity_key', selectedIdentityKey.value)
    params.set('product', selectedIdentityKey.value)
    if (selectedProductLabel.value) {
      params.set('product_label', selectedProductLabel.value)
    }
    const sourceName = searchParams.get('source_name') || ''
    const topCategory = searchParams.get('liancai_top_category') || ''
    const subcategory = searchParams.get('liancai_subcategory') || ''
    if (sourceName) params.set('source_name', sourceName)
    if (topCategory) params.set('liancai_top_category', topCategory)
    if (subcategory) params.set('liancai_subcategory', subcategory)
    window.location.assign(`${MAIN_APP_PATH}?${params.toString()}`)
  }
}

function setBackendSection(section: BackendSection) {
  const nextSection = normalizeBackendSectionForRole(section)
  backendSection.value = nextSection
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search)
    params.set('mode', 'supplier')
    params.set('tab', 'supplier')
    params.set('section', nextSection)
    if (selectedIdentityKey.value) {
      params.set('identity_key', selectedIdentityKey.value)
      params.set('product', selectedIdentityKey.value)
    }
    if (selectedProductLabel.value) {
      params.set('product_label', selectedProductLabel.value)
    }
    window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`)
  }
}

function handleSelectProduct(identityKey: string) {
  selectedIdentityKey.value = identityKey
  const matched = productOptions.value.find((item) => item.price_identity_key === identityKey)
  selectedProductFallbackLabel.value = matched?.price_identity_label || selectedProductFallbackLabel.value
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search)
    params.set('identity_key', identityKey)
    params.set('product', identityKey)
    if (selectedProductLabel.value) {
      params.set('product_label', selectedProductLabel.value)
    }
    window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`)
  }
}

async function loadBackendContext() {
  try {
    const [locationData, productOptionData] = await Promise.all([
      fetchLocationOptions(),
      fetchProductOptions({}),
    ])
    provinces.value = locationData.provinces ?? []
    cities.value = locationData.cities ?? []
    productOptions.value = productOptionData.items ?? []
    if (selectedIdentityKey.value) {
      const matched = productOptions.value.find((item) => item.price_identity_key === selectedIdentityKey.value)
      selectedProductFallbackLabel.value = matched?.price_identity_label || selectedProductFallbackLabel.value || selectedIdentityKey.value
    }
  } catch {
    // Standalone backend can still work without these context hints.
  }
}

onMounted(async () => {
  await restoreAuthSession()
  if (isAuthenticated.value) {
    await loadBackendContext()
  }
})

watch(
  () => currentAuthRole.value,
  (nextRole) => {
    if (nextRole === 'supplier') {
      const nextSection = normalizeBackendSectionForRole(backendSection.value)
      if (nextSection !== backendSection.value) {
        setBackendSection(nextSection)
      }
    }
  },
  { immediate: true },
)
</script>

<style scoped>
.supplier-backend-shell {
  display: grid;
  gap: 14px;
  --backend-radius-xl: 18px;
  --backend-radius-lg: 16px;
  --backend-radius-md: 14px;
  --backend-border: rgba(148, 163, 184, 0.14);
  --backend-border-strong: rgba(148, 163, 184, 0.18);
  --backend-shadow: 0 12px 26px rgba(15, 23, 42, 0.05);
  --backend-surface:
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(243, 247, 252, 0.96));
  --backend-card-surface: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94));
  --backend-soft-surface: rgba(248, 250, 252, 0.9);
  --backend-control-height: 40px;
  --backend-control-radius: 14px;
  --backend-panel-padding: 20px;
}

.supplier-backend-topbar,
.supplier-backend-sidebar,
.supplier-backend-pagebar,
.supplier-backend-panel,
.supplier-backend-stage {
  display: grid;
  gap: 14px;
}

.supplier-backend-topbar {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  padding: 15px 18px;
  border: 1px solid var(--backend-border-strong);
  border-radius: var(--backend-radius-xl);
  background: var(--backend-surface);
  box-shadow: var(--backend-shadow);
}

.supplier-backend-brand {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.supplier-backend-brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: var(--backend-radius-md);
  background: linear-gradient(145deg, rgba(30, 64, 175, 0.96), rgba(37, 99, 235, 0.88));
  color: #eff6ff;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0;
  box-shadow: 0 12px 22px rgba(30, 64, 175, 0.24);
}

.supplier-backend-brand-copy {
  display: grid;
  gap: 4px;
}

.supplier-backend-brand-copy strong,
.supplier-backend-sidebar-head h2,
.supplier-backend-pagebar-copy h1 {
  color: var(--ink-900);
}

.supplier-backend-brand-copy strong {
  font-size: 24px;
  letter-spacing: -0.04em;
}

.supplier-backend-brand-copy span,
.supplier-backend-sidebar-head p,
.supplier-backend-pagebar-copy p:last-child,
.supplier-backend-auth-copy p {
  margin: 0;
  color: var(--ink-700);
  font-size: 13px;
  line-height: 1.6;
}

.supplier-backend-topbar-actions {
  display: flex;
  align-items: stretch;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.supplier-backend-chip {
  display: grid;
  align-content: center;
  gap: 4px;
  min-width: 120px;
  min-height: 50px;
  padding: 8px 12px;
  border: 1px solid var(--backend-border);
  border-radius: var(--backend-radius-md);
  background: rgba(255, 255, 255, 0.8);
}

.supplier-backend-chip span,
.market-auth-helper-card strong,
.market-auth-scope {
  color: var(--ink-500);
  font-size: 10px;
}

.supplier-backend-chip strong {
  color: var(--ink-900);
  font-size: 14px;
}

.supplier-backend-chip.accent {
  border-color: rgba(37, 99, 235, 0.2);
  background: rgba(239, 246, 255, 0.88);
}

.supplier-backend-frame {
  display: grid;
  grid-template-columns: 214px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.supplier-backend-sidebar {
  position: static;
  padding: 16px;
  border: 1px solid var(--backend-border);
  border-radius: var(--backend-radius-xl);
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.96)),
    linear-gradient(145deg, rgba(30, 64, 175, 0.18), transparent);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.22);
}

.supplier-backend-sidebar-head,
.supplier-backend-sidebar-section,
.supplier-backend-sidebar-summary {
  display: grid;
  gap: 10px;
}

.supplier-backend-sidebar-head .panel-kicker,
.supplier-backend-sidebar-section-head strong,
.supplier-backend-sidebar-tip strong,
.supplier-backend-sidebar-tip span,
.supplier-backend-sidebar-card strong,
.supplier-backend-sidebar-card span,
.supplier-backend-sidebar-card small,
.supplier-backend-nav-item strong,
.supplier-backend-nav-item small,
.supplier-backend-nav-item span,
.supplier-backend-nav-item em {
  color: #e2e8f0;
}

.supplier-backend-sidebar-head h2 {
  margin: 2px 0 0;
  font-size: 20px;
  letter-spacing: -0.04em;
}

.supplier-backend-sidebar-head p {
  color: rgba(226, 232, 240, 0.72);
  font-size: 12px;
}

.supplier-backend-sidebar-summary {
  grid-template-columns: 1fr;
}

.supplier-backend-sidebar-card {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: var(--backend-radius-md);
  background: rgba(15, 23, 42, 0.42);
}

.supplier-backend-sidebar-card span,
.supplier-backend-sidebar-tip span {
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.supplier-backend-sidebar-card strong,
.supplier-backend-sidebar-tip strong {
  font-size: 15px;
  line-height: 1.4;
}

.supplier-backend-sidebar-card small,
.supplier-backend-sidebar-tip small {
  color: rgba(226, 232, 240, 0.72);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-backend-sidebar-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.supplier-backend-sidebar-section-head small {
  color: rgba(226, 232, 240, 0.64);
  font-size: 11px;
}

.supplier-backend-auth-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 420px);
  gap: 18px;
  align-items: start;
}

.supplier-backend-auth-copy {
  display: grid;
  gap: 12px;
}

.supplier-backend-auth-metrics,
.supplier-backend-command-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.supplier-backend-auth-scene-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.supplier-backend-auth-metric,
.supplier-backend-auth-scene-card,
.supplier-backend-auth-check-item,
.supplier-backend-command-card {
  display: grid;
  gap: 8px;
  padding: 14px 16px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94));
}

.supplier-backend-auth-metric span,
.supplier-backend-auth-scene-card span,
.supplier-backend-auth-check-item span,
.supplier-backend-command-card span {
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.supplier-backend-auth-metric strong,
.supplier-backend-auth-scene-card strong,
.supplier-backend-auth-check-item strong,
.supplier-backend-command-card strong {
  color: var(--ink-900);
  font-size: 16px;
  line-height: 1.4;
}

.supplier-backend-auth-metric small,
.supplier-backend-auth-scene-card small,
.supplier-backend-auth-check-item small,
.supplier-backend-command-card small {
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-backend-auth-checklist {
  display: grid;
  gap: 10px;
}

.supplier-backend-auth-check-item {
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
}

.supplier-backend-auth-check-item span {
  min-width: 36px;
  min-height: 36px;
  border-radius: 12px;
  background: rgba(239, 246, 255, 0.96);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #1d4ed8;
}

.supplier-backend-login-head {
  display: grid;
  gap: 6px;
}

.supplier-backend-login-head span {
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.supplier-backend-login-head strong {
  color: var(--ink-900);
  font-size: 18px;
}

.supplier-backend-login-head small {
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-backend-login-shortcuts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.supplier-backend-login-shortcut {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 42px;
  padding: 0 12px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.9);
  color: var(--ink-900);
  font: inherit;
  cursor: pointer;
}

.supplier-backend-login-shortcut strong {
  font-size: 13px;
}

.supplier-backend-login-shortcut span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(239, 246, 255, 0.92);
  color: #1d4ed8;
  font-size: 10px;
  font-weight: 700;
}

.supplier-backend-auth-copy h2 {
  margin: 0;
  color: var(--ink-900);
  font-size: 34px;
  letter-spacing: -0.05em;
}

.supplier-backend-stage {
  align-content: start;
}

.supplier-backend-pagebar {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  padding: 16px 18px;
  border: 1px solid var(--backend-border);
  border-radius: var(--backend-radius-xl);
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(246, 249, 253, 0.96));
  box-shadow: var(--backend-shadow);
}

.supplier-backend-pagebar.compact {
  padding: 14px 16px;
}

.supplier-backend-pagebar-copy {
  display: grid;
  gap: 8px;
}

.supplier-backend-breadcrumbs,
.supplier-backend-pagebar-meta,
.supplier-backend-pagebar-tags,
.market-auth-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-backend-breadcrumbs span {
  color: var(--ink-500);
  font-size: 11px;
}

.supplier-backend-pagebar-copy h1 {
  margin: 0;
  font-size: 28px;
  letter-spacing: -0.05em;
}

.supplier-backend-pagebar.compact .supplier-backend-pagebar-copy h1 {
  font-size: 24px;
}

.supplier-backend-pagebar-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(241, 245, 249, 0.96);
  color: var(--ink-600);
  font-size: 12px;
}

.supplier-backend-pagebar-side {
  display: grid;
  gap: 12px;
  justify-items: end;
}

.supplier-backend-pagebar-tags span {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(241, 245, 249, 0.96);
  color: var(--ink-600);
  font-size: 12px;
  white-space: nowrap;
}

.supplier-backend-pagebar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.supplier-backend-overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.supplier-backend-overview-grid.compact {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.supplier-backend-overview-card {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border: 1px solid var(--backend-border);
  border-radius: var(--backend-radius-lg);
  background: var(--backend-card-surface);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.supplier-backend-overview-card span {
  color: var(--ink-500);
  font-size: 11px;
}

.supplier-backend-overview-card strong {
  color: var(--ink-900);
  font-size: 18px;
  line-height: 1.4;
}

.supplier-backend-overview-card small {
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-backend-overview-grid.compact .supplier-backend-overview-card,
.supplier-backend-command-strip.compact .supplier-backend-command-card {
  padding: 12px 14px;
  border-radius: 16px;
}

.supplier-backend-overview-grid.compact .supplier-backend-overview-card strong,
.supplier-backend-command-strip.compact .supplier-backend-command-card strong {
  font-size: 16px;
}

.supplier-backend-command-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.supplier-backend-command-card {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid var(--backend-border);
  border-radius: var(--backend-radius-lg);
  background: var(--backend-card-surface);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.supplier-backend-command-card span {
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.supplier-backend-command-card strong {
  color: var(--ink-900);
  font-size: 18px;
  line-height: 1.4;
}

.supplier-backend-command-card small {
  color: var(--ink-600);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-backend-panel {
  padding: var(--backend-panel-padding);
  border: 1px solid var(--backend-border);
  border-radius: var(--backend-radius-xl);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--backend-shadow);
  align-content: start;
  overflow: visible;
}

.supplier-backend-shell :deep(.el-button) {
  min-height: var(--backend-control-height);
  padding: 0 14px;
  border-radius: 14px;
  font-weight: 600;
}

.supplier-backend-shell :deep(.el-button--small) {
  min-height: 32px;
  padding: 0 12px;
  border-radius: 12px;
  font-size: 12px;
}

.supplier-backend-shell :deep(.el-button--primary) {
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.16);
}

.supplier-backend-shell :deep(.el-input__wrapper),
.supplier-backend-shell :deep(.el-select__wrapper),
.supplier-backend-shell :deep(.el-textarea__inner) {
  min-height: var(--backend-control-height);
  border-radius: var(--backend-control-radius);
  box-shadow: 0 0 0 1px var(--backend-border) inset;
}

.supplier-backend-shell :deep(.el-textarea__inner) {
  padding: 10px 12px;
}

.market-auth-status,
.market-auth-copy,
.market-auth-form,
.market-auth-actions {
  display: grid;
  gap: 10px;
}

.market-auth-status.compact-banner {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.98), rgba(239, 246, 255, 0.74));
}

.market-auth-status.compact-banner h2 {
  margin: 0;
}

.market-auth-form {
  max-width: 420px;
}

.market-auth-error {
  margin: 0;
  color: #b91c1c;
  font-size: 12px;
}

.market-auth-helper-card {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.9);
}

.market-auth-helper-card p,
.market-auth-scope {
  margin: 0;
  color: var(--ink-700);
  font-size: 12px;
  line-height: 1.5;
}

.supplier-backend-login-card {
  max-width: none;
  padding: 20px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94));
}

.supplier-backend-session {
  margin-bottom: 4px;
}

.supplier-backend-session.compact {
  padding: 12px 14px;
}

.supplier-backend-nav-list {
  display: grid;
  gap: 8px;
}

.supplier-backend-nav-item {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.32);
  text-align: left;
  font: inherit;
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    background var(--transition-fast),
    transform var(--transition-fast);
}

.supplier-backend-nav-item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.supplier-backend-nav-item strong {
  font-size: 14px;
}

.supplier-backend-nav-item span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.14);
  font-size: 10px;
  letter-spacing: 0.08em;
}

.supplier-backend-nav-item small,
.supplier-backend-nav-item em {
  font-size: 11px;
  line-height: 1.4;
}

.supplier-backend-nav-item em {
  color: rgba(226, 232, 240, 0.64);
  font-style: normal;
}

.supplier-backend-nav-item.active {
  border-color: rgba(96, 165, 250, 0.32);
  background: linear-gradient(145deg, rgba(30, 64, 175, 0.34), rgba(30, 41, 59, 0.62));
  transform: translateY(-1px);
}

.supplier-backend-nav-item.disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.supplier-backend-sidebar-tip {
  display: grid;
  gap: 6px;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.3);
}

@media (max-width: 1180px) {
  .supplier-backend-frame,
  .supplier-backend-pagebar,
  .supplier-backend-overview-grid,
  .supplier-backend-auth-metrics,
  .supplier-backend-command-strip,
  .supplier-backend-auth-scene-grid {
    grid-template-columns: 1fr;
  }

  .supplier-backend-sidebar {
    position: static;
  }

  .supplier-backend-pagebar-side {
    justify-items: start;
  }

  .supplier-backend-pagebar-actions {
    justify-content: flex-start;
  }
}

.supplier-backend-shell.mobile .supplier-backend-topbar,
.supplier-backend-auth-layout.mobile,
.supplier-backend-frame.mobile {
  grid-template-columns: 1fr;
}

.supplier-backend-shell.mobile .supplier-backend-topbar-actions,
.supplier-backend-shell.mobile .supplier-backend-pagebar-actions {
  justify-content: flex-start;
}

.supplier-backend-shell.mobile .supplier-backend-login-shortcuts {
  grid-template-columns: 1fr;
}

.supplier-backend-shell.mobile .supplier-backend-pagebar {
  padding: 18px;
}

.supplier-backend-shell.mobile .supplier-backend-pagebar-copy h1,
.supplier-backend-shell.mobile .supplier-backend-auth-copy h2,
.supplier-backend-shell.mobile .supplier-backend-brand-copy strong {
  font-size: 26px;
}

.supplier-backend-shell.mobile .supplier-backend-overview-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.supplier-backend-shell.mobile .supplier-backend-sidebar-summary,
.supplier-backend-shell.mobile .supplier-backend-nav-list {
  grid-template-columns: 1fr;
}

@media (max-width: 640px) {
  .supplier-backend-shell.mobile .supplier-backend-overview-grid {
    grid-template-columns: 1fr;
  }

  .supplier-backend-topbar,
  .supplier-backend-sidebar,
  .supplier-backend-panel {
    padding-left: 16px;
    padding-right: 16px;
  }
}

/* Design-draft alignment: supplier backend follows the light dense admin console. */
.supplier-backend-shell {
  gap: 12px;
  padding: 12px;
  background: #f5f7fb;
}

.supplier-backend-topbar,
.supplier-backend-sidebar,
.supplier-backend-pagebar,
.supplier-backend-panel,
.supplier-backend-overview-card,
.supplier-backend-command-card,
.supplier-backend-login-card,
.market-auth-status.compact-banner {
  border-color: #e2e8f0;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.supplier-backend-topbar {
  min-height: 64px;
  padding: 12px 16px;
}

.supplier-backend-brand-mark {
  width: 34px;
  height: 34px;
  border-radius: 8px;
}

.supplier-backend-brand-copy strong,
.supplier-backend-sidebar-head h2,
.supplier-backend-pagebar-copy h1 {
  color: #10203d;
  letter-spacing: 0;
}

.supplier-backend-brand-copy strong {
  font-size: 18px;
}

.supplier-backend-frame {
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 12px;
}

.supplier-backend-sidebar {
  padding: 12px;
}

.supplier-backend-sidebar-head .panel-kicker,
.supplier-backend-sidebar-section-head strong,
.supplier-backend-sidebar-tip strong,
.supplier-backend-sidebar-tip span,
.supplier-backend-sidebar-card strong,
.supplier-backend-sidebar-card span,
.supplier-backend-sidebar-card small,
.supplier-backend-nav-item strong,
.supplier-backend-nav-item small,
.supplier-backend-nav-item span,
.supplier-backend-nav-item em {
  color: #10203d;
}

.supplier-backend-sidebar-head p,
.supplier-backend-sidebar-tip small,
.supplier-backend-nav-item small,
.supplier-backend-nav-item em {
  color: #667085;
}

.supplier-backend-sidebar-card,
.supplier-backend-nav-item,
.supplier-backend-sidebar-tip {
  border-color: #e5edf6;
  border-radius: 8px;
  background: #fff;
  box-shadow: none;
}

.supplier-backend-nav-item.active {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1d4ed8;
}

.supplier-backend-pagebar {
  padding: 16px;
}

.supplier-backend-pagebar-copy h1 {
  font-size: 22px;
}

.supplier-backend-panel {
  padding: 12px;
}

.supplier-backend-panel .supplier-backend-session.compact {
  min-height: 74px;
  padding: 10px 14px;
}

.supplier-backend-panel .supplier-backend-session.compact h2 {
  font-size: 20px;
  line-height: 1.2;
}

.supplier-backend-panel .supplier-backend-session.compact .market-auth-copy {
  gap: 5px;
}

.supplier-backend-panel .supplier-backend-session.compact .market-auth-scope {
  font-size: 11px;
}

/* Product-wide redesign: supplier backend is a ledger-style management desk. */
.supplier-backend-shell {
  align-content: start;
  gap: 14px;
  padding: 18px;
  background:
    linear-gradient(90deg, rgba(124, 58, 237, 0.06) 0 28%, transparent 28%),
    linear-gradient(180deg, #fbfaff 0%, #f0f3f8 100%);
}

.supplier-backend-topbar {
  min-height: 80px;
  border-color: rgba(124, 58, 237, 0.16);
  border-radius: 18px;
  background:
    linear-gradient(90deg, rgba(245, 243, 255, 0.94), #ffffff 44%),
    #ffffff;
  box-shadow: 0 14px 32px rgba(76, 29, 149, 0.08);
}

.supplier-backend-brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: #4c1d95;
  box-shadow: inset 0 -8px 0 rgba(255, 255, 255, 0.12);
}

.supplier-backend-brand-copy strong {
  font-size: 22px;
}

.supplier-backend-frame {
  grid-template-columns: 292px minmax(0, 1fr);
  gap: 16px;
}

.supplier-backend-sidebar {
  position: sticky;
  top: 18px;
  align-content: start;
  padding: 16px;
  border-color: rgba(124, 58, 237, 0.18);
  border-radius: 20px;
  background: #ffffff;
  box-shadow: 0 18px 38px rgba(76, 29, 149, 0.1);
}

.supplier-backend-sidebar::before {
  content: "";
  height: 4px;
  border-radius: 999px;
  background: linear-gradient(90deg, #4c1d95, #7c3aed, #0f9f72);
}

.supplier-backend-sidebar-card,
.supplier-backend-nav-item,
.supplier-backend-sidebar-tip {
  border-color: rgba(124, 58, 237, 0.12);
  border-radius: 14px;
  background: #fbfaff;
}

.supplier-backend-sidebar-card {
  grid-template-columns: minmax(0, 1fr);
}

.supplier-backend-nav-item {
  position: relative;
  min-height: 72px;
  padding-left: 18px;
}

.supplier-backend-nav-item::before {
  content: "";
  position: absolute;
  left: 8px;
  top: 14px;
  bottom: 14px;
  width: 3px;
  border-radius: 999px;
  background: rgba(124, 58, 237, 0.18);
}

.supplier-backend-nav-item.active {
  border-color: rgba(124, 58, 237, 0.32);
  background: #f5f3ff;
  color: #5b21b6;
}

.supplier-backend-nav-item.active::before {
  background: #7c3aed;
}

.supplier-backend-pagebar {
  min-height: 146px;
  align-items: center;
  padding: 20px;
  border-left: 5px solid #7c3aed;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}

.supplier-backend-pagebar-copy h1 {
  font-size: 30px;
  letter-spacing: -0.02em;
}

.supplier-backend-pagebar-meta span,
.supplier-backend-pagebar-tags span {
  border: 1px solid rgba(124, 58, 237, 0.12);
  background: #f5f3ff;
  color: #5b21b6;
}

.supplier-backend-overview-grid {
  grid-template-columns: repeat(4, minmax(150px, 1fr));
}

.supplier-backend-overview-card,
.supplier-backend-command-card {
  min-height: 112px;
  border-color: rgba(124, 58, 237, 0.13);
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 12px 26px rgba(76, 29, 149, 0.06);
}

.supplier-backend-command-card {
  border-top: 4px solid #7c3aed;
}

.supplier-backend-panel {
  padding: 16px;
  border-color: rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}

.supplier-backend-auth-layout {
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, 0.85fr);
}

.supplier-backend-auth-metric,
.supplier-backend-auth-scene-card,
.supplier-backend-auth-check-item,
.supplier-backend-login-card,
.market-auth-helper-card,
.market-auth-status.compact-banner {
  border-color: rgba(124, 58, 237, 0.13);
  border-radius: 14px;
  background: #fbfaff;
}

.supplier-backend-login-card {
  background: #ffffff;
  box-shadow: 0 16px 30px rgba(76, 29, 149, 0.1);
}

.supplier-backend-shell :deep(.el-button--primary) {
  border-color: #6d28d9;
  background: #6d28d9;
}

@media (max-width: 1180px) {
  .supplier-backend-sidebar {
    position: static;
  }
}

/* Align supplier backend with the main PC workbench shell. */
.supplier-backend-shell {
  background:
    radial-gradient(circle at 18% 0, rgba(37, 99, 235, 0.12), transparent 32%),
    linear-gradient(180deg, #f1f5fb 0%, #eaf1f8 100%);
}

.supplier-backend-topbar {
  min-height: 64px;
  border-color: rgba(226, 232, 240, 0.9);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
}

.supplier-backend-brand-mark {
  background: linear-gradient(135deg, #60a5fa, #2563eb);
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.24);
}

.supplier-backend-frame {
  grid-template-columns: 236px minmax(0, 1fr);
}

.supplier-backend-sidebar {
  border-color: rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  background: linear-gradient(180deg, #10233f 0%, #172c4c 58%, #0f1c32 100%);
  box-shadow: 14px 0 34px rgba(15, 23, 42, 0.14);
}

.supplier-backend-sidebar::before {
  background: linear-gradient(90deg, #60a5fa, #2563eb, #f59e0b);
}

.supplier-backend-sidebar-head h2,
.supplier-backend-sidebar-section-head strong,
.supplier-backend-sidebar-tip strong,
.supplier-backend-sidebar-tip span,
.supplier-backend-sidebar-card strong,
.supplier-backend-sidebar-card span,
.supplier-backend-sidebar-card small,
.supplier-backend-nav-item strong,
.supplier-backend-nav-item small,
.supplier-backend-nav-item span,
.supplier-backend-nav-item em {
  color: #e2e8f0;
}

.supplier-backend-sidebar-head p,
.supplier-backend-sidebar-tip small,
.supplier-backend-nav-item small,
.supplier-backend-nav-item em {
  color: rgba(226, 232, 240, 0.74);
}

.supplier-backend-sidebar-card,
.supplier-backend-nav-item,
.supplier-backend-sidebar-tip {
  border-color: rgba(148, 163, 184, 0.22);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
}

.supplier-backend-nav-item::before {
  background: rgba(147, 197, 253, 0.22);
}

.supplier-backend-nav-item.active {
  border-color: rgba(147, 197, 253, 0.38);
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #ffffff;
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.28);
}

.supplier-backend-nav-item.active::before {
  background: #ffffff;
}

.supplier-backend-pagebar {
  min-height: 108px;
  border-left: 0;
  border-color: #e2e8f0;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.06);
}

.supplier-backend-pagebar-copy h1 {
  font-size: 26px;
}

.supplier-backend-pagebar-meta span,
.supplier-backend-pagebar-tags span {
  border-color: #dbeafe;
  background: #eff6ff;
  color: #1d4ed8;
}

.supplier-backend-overview-card,
.supplier-backend-command-card,
.supplier-backend-panel,
.supplier-backend-auth-metric,
.supplier-backend-auth-scene-card,
.supplier-backend-auth-check-item,
.supplier-backend-login-card,
.market-auth-helper-card,
.market-auth-status.compact-banner {
  border-color: #e2e8f0;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.supplier-backend-command-card {
  border-top-color: #2563eb;
}

.supplier-backend-shell :deep(.el-button--primary) {
  border-color: #2563eb;
  background: #2563eb;
}

/* Final sidebar unification: match the main PC workbench rail exactly. */
.supplier-backend-frame {
  grid-template-columns: 192px minmax(0, 1fr);
  gap: 16px;
}

.supplier-backend-sidebar {
  display: grid;
  align-content: start;
  gap: 12px;
  min-height: calc(100vh - 126px);
  padding: 18px 12px;
  border: 0;
  border-right: 1px solid #dfe7f1;
  border-radius: 0;
  background: linear-gradient(180deg, #ffffff 0%, #ffffff 78%, #fbfdff 100%);
  box-shadow: 7px 0 22px rgba(15, 23, 42, 0.035);
}

.supplier-backend-sidebar::before {
  display: none;
}

.supplier-backend-sidebar-head,
.supplier-backend-sidebar-section,
.supplier-backend-sidebar-summary {
  gap: 8px;
}

.supplier-backend-sidebar-head h2 {
  margin: 0;
  color: #111d33;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0;
}

.supplier-backend-sidebar-head p {
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.supplier-backend-sidebar-summary,
.supplier-backend-nav-list {
  gap: 8px;
}

.supplier-backend-sidebar-card,
.supplier-backend-nav-item,
.supplier-backend-sidebar-tip {
  border: 1px solid #dbe4ef;
  border-radius: 8px;
  background: #f8fafc;
  box-shadow: none;
}

.supplier-backend-sidebar-card {
  padding: 8px 10px;
}

.supplier-backend-nav-item {
  min-height: 46px;
  padding: 8px 10px;
}

.supplier-backend-nav-item::before {
  content: none;
}

.supplier-backend-nav-item.active {
  border-color: #dbeafe;
  background: #eaf2ff;
  color: #2563eb;
  box-shadow: inset 3px 0 0 #2563eb;
  transform: none;
}

.supplier-backend-nav-item.active strong,
.supplier-backend-nav-item.active small,
.supplier-backend-nav-item.active em {
  color: #2563eb;
}

.supplier-backend-sidebar-head .panel-kicker,
.supplier-backend-sidebar-section-head strong,
.supplier-backend-sidebar-tip strong,
.supplier-backend-sidebar-tip span,
.supplier-backend-sidebar-card strong,
.supplier-backend-sidebar-card span,
.supplier-backend-sidebar-card small,
.supplier-backend-nav-item strong,
.supplier-backend-nav-item small,
.supplier-backend-nav-item span,
.supplier-backend-nav-item em {
  color: #334155;
}

.supplier-backend-sidebar-card small,
.supplier-backend-sidebar-tip small,
.supplier-backend-nav-item small,
.supplier-backend-nav-item em,
.supplier-backend-sidebar-section-head small {
  color: #64748b;
  font-size: 11px;
}

.supplier-backend-nav-item strong,
.supplier-backend-sidebar-card strong,
.supplier-backend-sidebar-tip strong {
  color: #0f172a;
}

.supplier-backend-nav-item span {
  min-width: 34px;
  min-height: 20px;
  padding: 0 7px;
  background: #eaf2ff;
  color: #2563eb;
}

.supplier-backend-nav-item.active span {
  background: #2563eb;
  color: #ffffff;
}

@media (max-width: 1180px) {
  .supplier-backend-sidebar {
    min-height: auto;
    border-radius: 16px;
  }
}

/* Simple mode: login should be one obvious card. */
.supplier-backend-auth-layout {
  grid-template-columns: minmax(320px, 420px);
  justify-content: start;
}

.supplier-backend-login-card {
  width: min(420px, 100%);
}

/* Workbench match: desktop supplier backend uses the same shell as the PC workbench. */
.supplier-backend-shell:not(.mobile) {
  display: grid;
  grid-template-columns: 190px minmax(0, 1fr);
  grid-template-rows: auto 1fr;
  gap: 0;
  width: 100%;
  min-height: 100vh;
  padding: 0;
  overflow: visible;
  background: #f5f7fb;
  color: #111f36;
  --backend-border: #dfe7f1;
  --backend-border-strong: #dfe7f1;
  --backend-radius-xl: 8px;
  --backend-radius-lg: 8px;
  --backend-radius-md: 8px;
  --backend-control-radius: 7px;
  --backend-shadow: 0 1px 2px rgba(15, 23, 42, 0.025);
  --backend-panel-padding: 18px;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-topbar {
  grid-column: 2;
  grid-row: 1;
  align-items: start;
  min-height: 88px;
  height: auto;
  padding: 12px 24px;
  border: 0;
  border-bottom: 1px solid #e5ebf3;
  border-radius: 0;
  background: #fff;
  box-shadow: none;
  backdrop-filter: none;
  overflow: visible;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-frame {
  display: contents;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-sidebar {
  grid-column: 1;
  grid-row: 1 / 3;
  position: sticky;
  top: 0;
  width: 190px;
  height: auto;
  min-height: 100vh;
  padding: 18px 12px;
  border: 0;
  border-right: 1px solid #dfe6ef;
  border-radius: 0;
  background: #fff;
  box-shadow: none;
  overflow: visible;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-stage {
  grid-column: 2;
  grid-row: 2;
  align-content: start;
  gap: 10px;
  min-width: 0;
  min-height: 0;
  padding: 14px 16px 18px;
  overflow: visible;
  background: #f5f7fb;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-brand-mark {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  background: linear-gradient(135deg, #60a5fa, #2563eb);
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.32);
}

.supplier-backend-shell:not(.mobile) .supplier-backend-brand-copy strong {
  font-size: 20px;
  letter-spacing: 0;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-chip {
  min-height: 38px;
  min-width: 104px;
  max-width: 180px;
  padding: 5px 10px;
  border-color: #dfe6ef;
  border-radius: 8px;
  background: #fff;
  box-shadow: none;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-topbar-actions {
  gap: 8px;
  align-items: flex-start;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-chip strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-brand {
  align-items: center;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-brand-copy {
  gap: 2px;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-chip {
  align-content: start;
  min-height: 52px;
  padding-top: 7px;
  padding-bottom: 7px;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item {
  min-height: 44px;
  padding: 0 12px;
  border-color: transparent;
  border-radius: 8px;
  background: transparent;
  box-shadow: none;
  color: #334155;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item.active {
  border-color: #d7e6ff;
  background: #eaf2ff;
  box-shadow: none;
  color: #2563eb;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item.active strong,
.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item.active small,
.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item.active em {
  color: #2563eb;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-pagebar,
.supplier-backend-shell:not(.mobile) .supplier-backend-panel,
.supplier-backend-shell:not(.mobile) .supplier-backend-overview-card,
.supplier-backend-shell:not(.mobile) .supplier-backend-command-card,
.supplier-backend-shell:not(.mobile) .supplier-backend-login-card,
.supplier-backend-shell:not(.mobile) .market-auth-status.compact-banner {
  border-color: #dfe7f1;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.025);
}

.supplier-backend-shell:not(.mobile) .supplier-backend-panel {
  align-content: start;
  overflow: visible;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-pagebar {
  min-height: auto;
  padding: 16px 18px;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-pagebar-copy h1 {
  font-size: 22px;
  letter-spacing: 0;
}

.supplier-backend-shell:not(.mobile) :deep(.el-button) {
  min-height: 34px;
  border-radius: 7px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02);
}

.supplier-backend-shell:not(.mobile) .supplier-backend-panel.auth-screen {
  align-content: stretch;
  padding: 22px;
  border: 0;
  background: #f5f7fb;
  box-shadow: none;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-panel.auth-screen .supplier-backend-auth-layout {
  grid-template-columns: minmax(0, 1fr) minmax(390px, 430px);
  gap: 18px;
  align-items: start;
  align-content: start;
  width: 100%;
  min-height: auto;
}

.supplier-backend-auth-intro {
  display: grid;
  align-content: start;
  gap: 14px;
  min-height: auto;
  padding: 34px;
  border: 1px solid #dfe7f1;
  border-radius: 8px;
  background:
    linear-gradient(135deg, #f8fbff 0%, #fff 58%, #eef6ff 100%);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.025);
}

.supplier-backend-auth-intro span {
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
}

.supplier-backend-auth-intro strong {
  color: #10203d;
  font-size: 30px;
  line-height: 1.12;
}

.supplier-backend-auth-intro small {
  max-width: 420px;
  color: #607089;
  font-size: 14px;
  line-height: 1.65;
}

.supplier-backend-auth-intro div {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-backend-auth-intro b {
  padding: 7px 10px;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  background: #fff;
  color: #2563eb;
  font-size: 12px;
}

.supplier-backend-auth-intro .supplier-backend-auth-preview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.supplier-backend-auth-preview article {
  display: grid;
  gap: 6px;
  min-height: 118px;
  padding: 14px;
  border: 1px solid #dfe7f1;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
}

.supplier-backend-auth-preview article span {
  color: #2563eb;
  font-size: 11px;
  font-weight: 800;
}

.supplier-backend-auth-preview article strong {
  color: #10203d;
  font-size: 15px;
  line-height: 1.25;
}

.supplier-backend-auth-preview article small {
  color: #607089;
  font-size: 12px;
  line-height: 1.45;
}

.supplier-backend-auth-intro .supplier-backend-auth-note {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: auto;
  padding: 14px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
}

.supplier-backend-auth-note div {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.supplier-backend-auth-note strong {
  color: #1d4ed8;
  font-size: 14px;
}

.supplier-backend-auth-note small {
  color: #3c4d66;
  font-size: 12px;
  line-height: 1.5;
}

.supplier-backend-auth-note button {
  flex: 0 0 auto;
  height: 32px;
  padding: 0 12px;
  border: 1px solid #2563eb;
  border-radius: 7px;
  background: #2563eb;
  color: #fff;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

.supplier-backend-auth-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px;
  padding: 4px;
  border-radius: 8px;
  background: #eef4ff;
}

.supplier-backend-auth-tabs button {
  height: 34px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #607089;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
}

.supplier-backend-auth-tabs button.active {
  background: #fff;
  color: #2563eb;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}

.supplier-backend-panel.auth-screen .supplier-backend-login-card {
  align-content: center;
  gap: 14px;
  align-self: center;
  width: 100%;
  min-height: 340px;
  padding: 24px;
}

.supplier-backend-form-tip {
  color: #607089;
  font-size: 12px;
  line-height: 1.5;
}

.supplier-backend-auth-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.supplier-backend-auth-foot button {
  height: 28px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #2563eb;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

.supplier-backend-shell.auth-only {
  display: block;
  min-height: 100vh;
  padding: 0;
  overflow: auto;
  background: #f5f7fb;
}

.supplier-backend-shell.auth-only .supplier-backend-topbar,
.supplier-backend-shell.auth-only .supplier-backend-sidebar {
  display: none;
}

.supplier-backend-shell.auth-only .supplier-backend-frame {
  display: block;
  width: 100%;
  padding: 0;
}

.supplier-backend-shell.auth-only .supplier-backend-stage {
  display: block;
  padding: 0;
  overflow: visible;
  background: transparent;
}

.supplier-backend-shell.auth-only .supplier-backend-panel {
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}

.supplier-backend-shell.auth-only .supplier-backend-auth-layout {
  display: grid;
  grid-template-columns: 1fr;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.supplier-backend-shell.auth-only:not(.mobile) .supplier-backend-panel.auth-screen .supplier-backend-auth-layout {
  grid-template-columns: minmax(0, 1fr);
  gap: 0;
}

.supplier-backend-shell.auth-only .supplier-backend-auth-intro {
  display: none;
}

.supplier-backend-shell.auth-only .supplier-backend-login-card {
  width: 100%;
  min-height: auto;
  padding: 0;
}

.supplier-backend-auth-page {
  display: grid;
  place-items: center;
  width: 100%;
  min-height: 100vh;
  padding: 32px;
  background: #f5f7fb;
}

.supplier-backend-shell.auth-only .supplier-backend-auth-card {
  width: min(460px, calc(100vw - 48px));
  min-width: 0;
  min-height: 440px;
  margin: 0 auto;
  padding: 36px;
  gap: 18px;
}

.supplier-backend-auth-card > strong {
  color: #10203d;
  font-size: 20px;
  line-height: 1.2;
}

@media (max-width: 1180px) {
  .supplier-backend-auth-page {
    padding: 20px;
  }

  .supplier-backend-shell .supplier-backend-panel.auth-screen .supplier-backend-auth-layout {
    grid-template-columns: 1fr;
    width: 100%;
    min-height: auto;
  }

  .supplier-backend-auth-intro {
    min-height: auto;
    padding: 22px;
  }

  .supplier-backend-auth-intro .supplier-backend-auth-preview {
    grid-template-columns: 1fr;
  }
}

/* shadcn/ui-inspired mobile backend shell: compact chrome, work-first content. */
@media (max-width: 980px) {
  .supplier-backend-shell.mobile {
    display: grid;
    align-content: start;
    gap: 8px;
    min-height: 100vh;
    padding: 8px;
    overflow-x: hidden;
    background: #f8fafc;
    color: #0f172a;
    --backend-border: #e5e7eb;
    --backend-radius-xl: 8px;
    --backend-radius-lg: 8px;
    --backend-control-radius: 8px;
    --backend-shadow: 0 1px 2px rgba(15, 23, 42, 0.035);
    --backend-panel-padding: 10px;
  }

  .supplier-backend-shell.mobile .supplier-backend-topbar,
  .supplier-backend-shell.mobile .supplier-backend-sidebar,
  .supplier-backend-shell.mobile .supplier-backend-pagebar,
  .supplier-backend-shell.mobile .supplier-backend-panel,
  .supplier-backend-shell.mobile .market-auth-status.compact-banner,
  .supplier-backend-shell.mobile .supplier-backend-login-card {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background: #fff;
    box-shadow: var(--backend-shadow);
  }

  .supplier-backend-shell.mobile .supplier-backend-topbar {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
    min-height: 0;
    padding: 10px;
  }

  .supplier-backend-shell.mobile .supplier-backend-brand {
    align-items: center;
    gap: 10px;
  }

  .supplier-backend-shell.mobile .supplier-backend-brand-mark {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: #2563eb;
    box-shadow: none;
    font-size: 20px;
  }

  .supplier-backend-shell.mobile .supplier-backend-brand-copy {
    gap: 1px;
  }

  .supplier-backend-shell.mobile .supplier-backend-brand-copy strong {
    font-size: 20px;
    line-height: 1.16;
    letter-spacing: 0;
  }

  .supplier-backend-shell.mobile .supplier-backend-topbar-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    width: 100%;
  }

  .supplier-backend-shell.mobile .supplier-backend-chip {
    display: none;
  }

  .supplier-backend-shell.mobile .supplier-backend-topbar-actions :deep(.el-button) {
    width: 100%;
    min-height: 34px;
    margin-left: 0;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
  }

  .supplier-backend-shell.mobile .supplier-backend-frame {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
  }

  .supplier-backend-shell.mobile .supplier-backend-sidebar {
    position: static;
    display: grid;
    gap: 8px;
    min-height: 0;
    padding: 10px;
  }

  .supplier-backend-shell.mobile .supplier-backend-sidebar-head,
  .supplier-backend-shell.mobile .supplier-backend-sidebar-section-head,
  .supplier-backend-shell.mobile .supplier-backend-sidebar-summary,
  .supplier-backend-shell.mobile .supplier-backend-sidebar-tip {
    display: none;
  }

  .supplier-backend-shell.mobile .supplier-backend-sidebar-section,
  .supplier-backend-shell.mobile .supplier-backend-nav-list {
    gap: 6px;
  }

  .supplier-backend-shell.mobile .supplier-backend-nav-list {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .supplier-backend-shell.mobile .supplier-backend-nav-item {
    min-height: 44px;
    padding: 7px 6px;
    border-color: #e5e7eb;
    border-radius: 8px;
    background: #fff;
    box-shadow: none;
  }

  .supplier-backend-shell.mobile .supplier-backend-nav-item.active {
    border-color: #bfdbfe;
    background: #eff6ff;
    box-shadow: inset 2px 0 0 #2563eb;
    color: #1d4ed8;
  }

  .supplier-backend-shell.mobile .supplier-backend-nav-item-head {
    display: grid;
    justify-items: start;
    gap: 2px;
  }

  .supplier-backend-shell.mobile .supplier-backend-nav-item strong {
    font-size: 12px;
    line-height: 1.2;
  }

  .supplier-backend-shell.mobile .supplier-backend-nav-item span {
    min-width: 0;
    min-height: 0;
    padding: 0;
    border: 0;
    background: transparent;
    color: #64748b;
    font-size: 10px;
  }

  .supplier-backend-shell.mobile .supplier-backend-nav-item.active span,
  .supplier-backend-shell.mobile .supplier-backend-nav-item.active strong {
    color: #1d4ed8;
  }

  .supplier-backend-shell.mobile .supplier-backend-nav-item em {
    display: none;
  }

  .supplier-backend-shell.mobile .supplier-backend-stage {
    display: grid;
    gap: 8px;
    min-width: 0;
    padding: 0;
    background: transparent;
  }

  .supplier-backend-shell.mobile .supplier-backend-pagebar {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
    min-height: 0;
    padding: 10px;
    border-left: 0;
  }

  .supplier-backend-shell.mobile .supplier-backend-pagebar-copy {
    gap: 3px;
  }

  .supplier-backend-shell.mobile .supplier-backend-pagebar-copy h1 {
    font-size: 20px;
    line-height: 1.18;
    letter-spacing: 0;
  }

  .supplier-backend-shell.mobile .supplier-backend-pagebar-meta,
  .supplier-backend-shell.mobile .supplier-backend-pagebar-tags {
    gap: 6px;
  }

  .supplier-backend-shell.mobile .supplier-backend-pagebar-meta span,
  .supplier-backend-shell.mobile .supplier-backend-pagebar-tags span {
    min-height: 24px;
    padding: 3px 8px;
    border-color: #dbeafe;
    border-radius: 999px;
    background: #eff6ff;
    color: #1d4ed8;
    font-size: 11px;
  }

  .supplier-backend-shell.mobile .supplier-backend-pagebar-side {
    display: none;
  }

  .supplier-backend-shell.mobile .supplier-backend-panel {
    display: grid;
    gap: 8px;
    padding: 10px;
  }

  .supplier-backend-shell.mobile .supplier-backend-session.compact {
    min-height: 0;
    padding: 10px;
    border-radius: 8px;
  }

  .supplier-backend-shell.mobile .supplier-backend-session.compact h2 {
    font-size: 18px;
    line-height: 1.18;
  }

  .supplier-backend-shell.mobile :deep(.supplier-admin-panel) {
    gap: 8px;
  }
}

/* shadcn/ui MIT-style admin skin for the supplier platform shell. */
.supplier-backend-shell:not(.mobile) {
  background: #f8fafc;
  color: #020817;
  --backend-border: #e2e8f0;
  --backend-border-strong: #e2e8f0;
  --backend-radius-xl: 8px;
  --backend-radius-lg: 8px;
  --backend-radius-md: 8px;
  --backend-control-radius: 6px;
  --backend-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.supplier-backend-shell:not(.mobile) .supplier-backend-topbar {
  height: 56px;
  padding: 0 16px;
  border-bottom-color: #e2e8f0;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-sidebar {
  width: 184px;
  padding: 14px 10px;
  border-right-color: #e2e8f0;
}

.supplier-backend-shell:not(.mobile) {
  grid-template-columns: 184px minmax(0, 1fr);
  grid-template-rows: 56px minmax(0, 1fr);
}

.supplier-backend-shell:not(.mobile) .supplier-backend-stage {
  padding: 12px 16px 16px;
  background: #f8fafc;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-brand-mark {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: #020817;
  box-shadow: none;
  font-size: 15px;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-brand-copy strong {
  color: #020817;
  font-size: 18px;
  font-weight: 750;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-brand-copy .panel-kicker,
.supplier-backend-shell:not(.mobile) .supplier-backend-sidebar-head .panel-kicker {
  color: #64748b;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-chip {
  min-height: 34px;
  border-color: #e2e8f0;
  background: #ffffff;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-chip.accent {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-chip span {
  color: #64748b;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-chip strong {
  color: #020817;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item {
  min-height: 38px;
  border-radius: 6px;
  color: #334155;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item.active {
  border-color: #e2e8f0;
  background: #f1f5f9;
  color: #020817;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item.active strong,
.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item.active small,
.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item.active em {
  color: #020817;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item span {
  background: #f1f5f9;
  color: #64748b;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item.active span {
  background: #020817;
  color: #ffffff;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-nav-list.secondary {
  gap: 6px;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item.secondary {
  min-height: 34px;
  padding-top: 5px;
  padding-bottom: 5px;
  border-color: #e2e8f0;
  background: #ffffff;
}

.supplier-backend-shell:not(.mobile) .supplier-backend-nav-item.secondary strong {
  font-size: 13px;
}

.supplier-backend-shell:not(.mobile) :deep(.el-button) {
  min-height: 32px;
  border-color: #e2e8f0;
  border-radius: 6px;
  background: #ffffff;
  color: #020817;
  box-shadow: none;
}

.supplier-backend-shell:not(.mobile) :deep(.el-button--primary) {
  border-color: #020817;
  background: #020817;
  color: #ffffff;
}

.supplier-backend-context-strip {
  display: grid;
  gap: 4px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: 12px;
  background: #eff6ff;
  color: #1e3a8a;
}

.supplier-backend-context-strip.stage {
  margin-bottom: 14px;
}

.supplier-backend-context-strip span {
  font-size: 12px;
  font-weight: 800;
}

.supplier-backend-context-strip strong {
  color: #0f172a;
  font-size: 15px;
}

.supplier-backend-context-strip small {
  color: #475569;
  line-height: 1.45;
}
</style>
