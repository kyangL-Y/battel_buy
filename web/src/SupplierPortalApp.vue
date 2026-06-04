<template>
  <section
    class="app-shell supplier-portal-shell"
    :class="{ mobile: isMobileViewport, 'auth-only': !isAuthenticated }"
    :data-ready="authRestoring || portalContextLoading ? 'loading' : 'ready'"
    data-testid="supplier-portal-screen"
  >
    <main v-if="!isAuthenticated && !authRestoring" class="supplier-portal-auth-page" data-testid="supplier-auth-shell">
      <div class="supplier-portal-auth-hero">
        <div class="supplier-portal-brand">
          <div class="supplier-portal-brand-mark">报</div>
          <div class="supplier-portal-brand-copy">
            <p class="panel-kicker">供应商报价</p>
            <h1>供应商报价登录</h1>
          </div>
        </div>
        <div class="supplier-portal-auth-actions">
          <button type="button" class="supplier-native-button ghost" @click="backToMainWorkspace">返回采购工作台</button>
        </div>
      </div>
      <div class="supplier-portal-login-card supplier-portal-auth-card" data-testid="supplier-login-form">
        <div class="supplier-portal-auth-note">
          <div>
            <strong>账号由采购分配</strong>
            <small>没有账号请联系采购。</small>
          </div>
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
        <p v-if="authError" class="supplier-portal-error">{{ authError }}</p>
        <button type="button" class="supplier-native-button primary" data-testid="auth-login-button" :disabled="authSubmitting" @click="submitAuthLogin">{{ authSubmitting ? '登录中' : '登录' }}</button>
        <div class="supplier-portal-auth-foot">
          <button type="button" @click="showPasswordHelp">忘记密码</button>
        </div>
      </div>
    </main>

    <el-dialog v-if="passwordResetVisible" v-model="passwordResetVisible" title="重置密码" width="min(92vw, 420px)">
      <div class="supplier-portal-reset-form">
        <small>输入账号、当前密码和新密码，验证通过后直接更新密码并登录。</small>
        <el-input v-model="passwordResetForm.username" placeholder="账号" autocomplete="username" />
        <el-input v-model="passwordResetForm.current_password" type="password" show-password placeholder="当前密码" autocomplete="current-password" />
        <el-input v-model="passwordResetForm.new_password" type="password" show-password placeholder="新密码，至少 8 位" autocomplete="new-password" @keyup.enter="submitPasswordReset" />
        <p v-if="passwordResetError" class="supplier-portal-error">{{ passwordResetError }}</p>
        <div class="supplier-portal-auth-foot">
          <el-button plain @click="passwordResetVisible = false">取消</el-button>
          <el-button type="primary" :loading="passwordResetSubmitting" @click="submitPasswordReset">确认重置</el-button>
        </div>
      </div>
    </el-dialog>

    <template v-if="isAuthenticated || authRestoring">
    <header class="panel supplier-portal-topbar">
      <div class="supplier-portal-brand">
        <div class="supplier-portal-brand-mark">报</div>
        <div class="supplier-portal-brand-copy">
          <p class="panel-kicker">供应商报价</p>
          <h1>供应商报价登录</h1>
        </div>
      </div>
      <div class="supplier-portal-topbar-actions">
        <div class="supplier-portal-chip">
          <span>当前任务商品</span>
          <strong>{{ selectedProductLabel || (portalContextLoading ? '商品同步中' : '未指定商品') }}</strong>
        </div>
        <div class="supplier-portal-chip accent">
          <span>账号状态</span>
          <strong>{{ isAuthenticated ? '已登录' : (authRestoring ? '恢复中' : '待登录') }}</strong>
        </div>
        <el-button plain @click="backToMainWorkspace">返回采购工作台</el-button>
      </div>
    </header>

    <main class="supplier-portal-frame">
      <section class="panel supplier-portal-hero">
        <div>
          <p class="panel-kicker">{{ isAuthenticated ? '报价' : '登录' }}</p>
          <h2>{{ isAuthenticated ? '我的报价' : '登录报价' }}</h2>
        </div>
        <div class="supplier-portal-steps">
          <article v-for="item in portalLiveCards" :key="item.title" class="supplier-portal-step">
            <span>{{ item.label }}</span>
            <strong>{{ item.title }}</strong>
          </article>
        </div>
      </section>

      <section class="panel supplier-portal-panel" :class="{ 'auth-screen': !isAuthenticated && !authRestoring }" data-testid="supplier-auth-shell">
        <template v-if="authRestoring">
          <div class="supplier-portal-auth-copy">
            <p class="panel-kicker">登录</p>
            <h2>正在进入</h2>
          </div>
        </template>

        <template v-else-if="!isAuthenticated">
          <div class="supplier-portal-login-card" data-testid="supplier-login-form">
            <div class="supplier-portal-auth-note">
              <div>
                <strong>账号由采购分配</strong>
                <small>没有账号请联系采购。</small>
              </div>
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
            <p v-if="authError" class="supplier-portal-error">{{ authError }}</p>
            <button type="button" class="supplier-native-button primary" data-testid="auth-login-button" :disabled="authSubmitting" @click="submitAuthLogin">{{ authSubmitting ? '登录中' : '登录' }}</button>
            <div class="supplier-portal-auth-foot">
              <button type="button" @click="showPasswordHelp">忘记密码</button>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="supplier-portal-session" data-testid="auth-session-status">
            <div>
              <p class="panel-kicker">当前账号</p>
              <h2>{{ currentUser?.display_name || currentUser?.username }}</h2>
              <small>{{ currentAuthScopeLabel }}</small>
            </div>
            <div class="supplier-portal-session-actions">
              <el-button type="primary" @click="openSupplierBackend()">进入供应商管理台</el-button>
              <el-button plain @click="logoutAuthSession">退出登录</el-button>
            </div>
          </div>
          <div class="supplier-portal-workbench-strip">
            <article v-for="item in portalWorkbenchCards" :key="item.label" class="supplier-portal-workbench-card">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.detail }}</small>
            </article>
          </div>
          <section class="supplier-portal-scope-strip" aria-label="供应商范围">
            <button
              v-for="item in portalScopeCards"
              :key="item.key"
              type="button"
              class="supplier-portal-scope-card"
              :class="item.tone"
              @click="runPortalScopeAction(item.key)"
            >
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.detail }}</small>
            </button>
          </section>
          <section class="supplier-portal-quote-queue" aria-label="报价状态队列">
            <button
              v-for="item in portalQuoteQueueCards"
              :key="item.key"
              type="button"
              class="supplier-portal-quote-queue-card"
              :class="item.tone"
              @click="runPortalQuoteQueueAction(item.key)"
            >
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.detail }}</small>
            </button>
          </section>
          <div class="supplier-portal-operations">
            <section class="supplier-portal-todo-board" aria-label="供应商今日待办">
              <article v-for="item in portalTodoCards" :key="item.label" class="supplier-portal-todo-card" :class="item.tone">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
                <small>{{ item.detail }}</small>
              </article>
            </section>

            <section class="supplier-portal-action-deck" aria-label="供应商快捷操作">
              <button
                v-for="item in portalQuickActions"
                :key="item.key"
                type="button"
                class="supplier-portal-action-card"
                :class="{ primary: item.primary }"
                @click="runPortalAction(item.key)"
              >
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </button>
            </section>

            <section ref="productStripRef" class="supplier-portal-product-strip" aria-label="商品快捷切换">
              <button
                v-for="item in portalProductShortlist"
                :key="item.price_identity_key"
                type="button"
                class="supplier-portal-product-chip"
                :class="{ active: selectedIdentityKey === item.price_identity_key }"
                @click="selectPortalProduct(item)"
              >
                <strong>{{ item.price_identity_label }}</strong>
                <small>{{ item.site_count || 0 }} 个来源</small>
              </button>
              <div v-if="!portalProductShortlist.length" class="supplier-portal-product-empty">
                <strong>商品目录同步中</strong>
                <small>后端返回商品后会显示快捷切换。</small>
              </div>
            </section>
          </div>

          <div ref="quoteDeskRef" class="supplier-portal-quote-desk">
            <SupplierAdminPanel
              :product-options="productOptions"
              :selected-identity-key="selectedIdentityKey"
              :selected-product-label="selectedProductLabel"
              :mobile="isMobileViewport"
              :auth-role="currentAuthRole"
              :auth-supplier-id="currentAuthSupplierId"
              :auth-display-name="currentAuthDisplayName"
              backend-section="quote"
              :mobile-task="portalMobileTask"
              :show-embedded-tabs="false"
              @select-product="handleSelectProduct"
              @navigate-section="handleSupplierPanelNavigate"
              @quote-draft-summary="handleQuoteDraftSummary"
            />
          </div>

          <div v-if="isMobileViewport" class="supplier-portal-sticky-actions" role="region" aria-label="供应商快捷操作栏">
            <button type="button" class="primary" @click="runPortalStickyPrimaryAction">{{ portalStickyPrimaryLabel }}</button>
            <button type="button" @click="runPortalStickySecondaryAction">{{ portalStickySecondaryLabel }}</button>
          </div>
        </template>
      </section>
    </main>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onMounted, reactive, ref } from 'vue'

import {
  clearAuthSession,
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
import type { AuthLoginResponse, AuthUserItem, ProductOptionItem } from './types'
import './supplier-portal.css'

const SupplierAdminPanel = defineAsyncComponent(() => import('./components/SupplierAdminPanel.vue'))

const MAIN_APP_PATH = '/'
const SUPPLIER_BACKEND_PATH = '/supplier-backend'
const { isMobileViewport } = useViewport()

const authSession = ref<AuthLoginResponse | null>(readAuthSession())
const authSubmitting = ref(false)
const authRestoring = ref(false)
const portalContextLoading = ref(false)
const authError = ref('')
const authForm = reactive({ username: '', password: '' })
const authPasswordVisible = ref(false)
const passwordResetVisible = ref(false)
const passwordResetSubmitting = ref(false)
const passwordResetError = ref('')
const passwordResetForm = reactive({
  username: '',
  current_password: '',
  new_password: '',
})
const productOptions = ref<ProductOptionItem[]>([])
const selectedIdentityKey = ref('')
const selectedProductFallbackLabel = ref('')
const quoteDeskRef = ref<HTMLElement | null>(null)
const productStripRef = ref<HTMLElement | null>(null)
const quoteDraftSummary = reactive({
  count: 0,
  hasCurrent: false,
  latestLabel: '',
  latestUpdatedAt: '',
})
const portalMobileTask = ref<'quote' | 'history'>('quote')

const initialSearchParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams()
const queryIdentityKey = initialSearchParams.get('identity_key') || initialSearchParams.get('identityKey') || initialSearchParams.get('product') || ''
const queryProductLabel = initialSearchParams.get('product_label') || initialSearchParams.get('label') || ''
const SUPPLIER_CONTEXT_QUERY_KEYS = [
  'source',
  'source_name',
  'liancai_top_category',
  'liancai_subcategory',
  'alert_rule',
  'context_title',
]

const currentUser = computed<AuthUserItem | null>(() => authSession.value?.user ?? null)
const isAuthenticated = computed(() => Boolean(authSession.value?.access_token && currentUser.value))
const currentAuthRole = computed(() => currentUser.value?.role ?? null)
const currentAuthSupplierId = computed(() => currentUser.value?.supplier_id ?? null)
const currentAuthDisplayName = computed(() => currentUser.value?.display_name || currentUser.value?.username || '')
const selectedProductLabel = computed(() =>
  productOptions.value.find((item) => item.price_identity_key === selectedIdentityKey.value)?.price_identity_label
  || selectedProductFallbackLabel.value,
)
const currentAuthScopeLabel = computed(() => {
  if (!isAuthenticated.value) return '还未登录'
  if (currentAuthRole.value === 'admin') return '管理员账号：可帮供应商录价'
  return currentUser.value?.supplier_profile?.supplier_name
    ? `当前供应商：${currentUser.value.supplier_profile.supplier_name}`
    : '还没有分配供应商'
})
const portalLiveCards = computed(() => [
  {
    label: '当前账号',
    title: isAuthenticated.value ? (currentUser.value?.display_name || currentUser.value?.username || '已登录') : '待登录',
    detail: isAuthenticated.value ? currentAuthScopeLabel.value : '登录后显示你的商品。',
  },
  {
    label: '商品目录',
    title: portalContextLoading.value ? '商品同步中' : `${productOptions.value.length} 个可选商品`,
    detail: selectedProductLabel.value
      ? `当前商品：${selectedProductLabel.value}`
      : (portalContextLoading.value ? '正在读取后端商品目录。' : '后端暂未返回可选商品。'),
  },
  {
    label: '报价保存',
    title: '提交后保存',
    detail: '提交后保存记录。',
  },
])
const portalWorkbenchCards = computed(() => [
  {
    label: '当前账号',
    value: currentAuthRole.value === 'admin' ? '管理员账号' : (currentUser.value?.supplier_profile?.supplier_name || '待绑定'),
    detail: currentAuthRole.value === 'admin' ? '管理员可帮供应商录价' : currentAuthScopeLabel.value,
  },
  {
    label: '可选商品',
    value: `${productOptions.value.length} 个`,
    detail: selectedProductLabel.value
      ? `当前录价商品：${selectedProductLabel.value}`
      : (portalContextLoading.value ? '商品目录同步中' : '暂时没有可选商品'),
  },
  {
    label: '保存状态',
    value: '提交后保存',
    detail: '提交后保存记录',
  },
])
const portalScopeCards = computed(() => {
  if (currentAuthRole.value === 'admin') {
    return [
      {
        key: 'scope' as const,
        label: '当前账号',
        value: '管理员账号',
        detail: '可帮供应商临时录价',
        tone: 'primary',
      },
      {
        key: 'history' as const,
        label: '可看内容',
        value: '全局可见',
        detail: '历史记录按当前选中供应商显示',
        tone: 'neutral',
      },
      {
        key: 'scope' as const,
        label: '下一步',
        value: '继续录价',
        detail: '确认商品和最新报价后继续录价',
        tone: 'neutral',
      },
    ]
  }

  const supplierName = currentUser.value?.supplier_profile?.supplier_name || ''
  return [
    {
      key: 'scope' as const,
      label: '当前账号',
      value: supplierName || '待绑定供应商',
      detail: supplierName ? '仅维护当前供应商报价' : '管理员绑定档案后才能录价',
      tone: supplierName ? 'primary' : 'warning',
    },
    {
      key: 'history' as const,
      label: '可看内容',
      value: supplierName ? '本供应商' : '未开通',
      detail: supplierName ? '只显示本供应商记录' : '暂无报价',
      tone: 'neutral',
    },
    {
      key: supplierName ? 'quote' as const : 'backend' as const,
      label: '下一步',
      value: supplierName ? '继续录价' : '等待绑定',
      detail: supplierName ? '继续填写报价' : '请联系管理员',
      tone: 'neutral',
    },
  ]
})
const portalQuoteQueueCards = computed(() => [
  {
    key: 'pending' as const,
    label: '待处理',
    value: selectedProductLabel.value ? '当前商品' : `${productOptions.value.length} 个商品`,
    detail: selectedProductLabel.value || (portalContextLoading.value ? '目录同步中' : '先从商品队列选择报价对象'),
    tone: 'primary',
  },
  {
    key: 'drafts' as const,
    label: '草稿',
    value: quoteDraftSummary.count ? `${quoteDraftSummary.count} 条` : '无草稿',
    detail: quoteDraftSummary.hasCurrent
      ? '当前商品有本机草稿'
      : (quoteDraftSummary.latestLabel ? `最近：${quoteDraftSummary.latestLabel}` : '可先保存草稿再提交'),
    tone: quoteDraftSummary.count ? 'warning' : 'neutral',
  },
  {
    key: 'history' as const,
    label: '已提交',
    value: '报价记录',
    detail: currentAuthRole.value === 'admin' ? '先看最近记录' : '查看自己的历史报价',
    tone: 'neutral',
  },
])
const portalProductShortlist = computed(() => productOptions.value.slice(0, 8))
const portalTodoCards = computed(() => [
  {
    label: '今日待办',
    value: selectedProductLabel.value ? '补录当前商品' : '先选商品',
    detail: selectedProductLabel.value || '商品目录返回后选择报价商品',
    tone: 'primary',
  },
  {
    label: '报价范围',
    value: currentAuthRole.value === 'admin' ? '全局可见' : (currentUser.value?.supplier_profile?.supplier_name || '绑定供应商'),
    detail: currentAuthScopeLabel.value,
    tone: 'neutral',
  },
  {
    label: '目录状态',
    value: portalContextLoading.value ? '同步中' : `${productOptions.value.length} 个商品`,
    detail: selectedIdentityKey.value ? '可直接进入录价区' : '等待商品目录',
    tone: productOptions.value.length ? 'success' : 'warning',
  },
])
const portalQuickActions = computed(() => [
  { key: 'quote' as const, label: '快捷操作', value: portalMobileTask.value === 'history' ? '返回录价' : '继续录价', primary: true },
  { key: 'products' as const, label: '商品', value: '切换商品' },
  { key: 'refresh' as const, label: '同步', value: portalContextLoading.value ? '同步中' : '刷新目录' },
  { key: 'history' as const, label: '记录', value: '查看历史' },
])
const portalStickyPrimaryLabel = computed(() => {
  if (portalMobileTask.value === 'history') return '返回录价'
  if (quoteDraftSummary.hasCurrent) return '恢复草稿'
  return productOptions.value.length ? '继续录价' : '刷新目录'
})
const portalStickySecondaryLabel = computed(() => '去管理页')
function applyAuthSession(session: AuthLoginResponse | null) {
  authSession.value = session
  if (session) {
    writeAuthSession(session)
  } else {
    clearAuthSession()
  }
}

function backToMainWorkspace() {
  if (typeof window === 'undefined') return
  const params = new URLSearchParams()
  const identityKey = selectedIdentityKey.value || initialSearchParams.get('identity_key') || initialSearchParams.get('identityKey') || initialSearchParams.get('product') || ''
  const productLabel = selectedProductLabel.value || initialSearchParams.get('product_label') || initialSearchParams.get('label') || ''
  params.set('mode', 'workspace')
  params.set('tab', identityKey ? 'trend' : 'summary')
  if (identityKey) {
    params.set('section', 'trend')
    params.set('identity_key', identityKey)
    params.set('product', identityKey)
  }
  if (productLabel) {
    params.set('product_label', productLabel)
  }
  window.location.assign(`${MAIN_APP_PATH}?${params.toString()}`)
}

function openSupplierBackend(section?: 'suppliers' | 'quote' | 'settlement' | 'logs') {
  if (typeof window === 'undefined') return
  const params = new URLSearchParams()
  params.set('mode', initialSearchParams.get('mode') || 'supplier')
  params.set('tab', initialSearchParams.get('tab') || 'supplier')
  params.set('section', section || initialSearchParams.get('section') || portalMobileTask.value || 'quote')

  SUPPLIER_CONTEXT_QUERY_KEYS.forEach((key) => {
    const value = initialSearchParams.get(key)
    if (value) params.set(key, value)
  })

  const identityKey = selectedIdentityKey.value || queryIdentityKey
  const productLabel = selectedProductLabel.value || queryProductLabel
  if (identityKey) {
    params.set('identity_key', identityKey)
    params.set('product', identityKey)
  }
  if (productLabel) {
    params.set('product_label', productLabel)
  }
  window.location.assign(`${SUPPLIER_BACKEND_PATH}?${params.toString()}`)
}

function handleSupplierPanelNavigate(section: 'suppliers' | 'quote' | 'settlement' | 'logs') {
  if (section === 'quote') {
    void loadPortalContext(true)
    return
  }
  openSupplierBackend(section)
}

function handleQuoteDraftSummary(summary: { count: number; hasCurrent: boolean; latestLabel: string; latestUpdatedAt: string }) {
  quoteDraftSummary.count = summary.count
  quoteDraftSummary.hasCurrent = summary.hasCurrent
  quoteDraftSummary.latestLabel = summary.latestLabel
  quoteDraftSummary.latestUpdatedAt = summary.latestUpdatedAt
}

function handleSelectProduct(identityKey: string) {
  selectedIdentityKey.value = identityKey
  const matched = productOptions.value.find((item) => item.price_identity_key === identityKey)
  selectedProductFallbackLabel.value = matched?.price_identity_label || selectedProductFallbackLabel.value
}

function selectPortalProduct(item: ProductOptionItem) {
  selectedIdentityKey.value = item.price_identity_key
  selectedProductFallbackLabel.value = item.price_identity_label
  portalMobileTask.value = 'quote'
  scrollToQuoteDesk()
}

async function scrollToQuoteDesk() {
  await nextTick()
  quoteDeskRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function scrollToProductStrip() {
  await nextTick()
  productStripRef.value?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}

function runPortalStickyPrimaryAction() {
  if (portalMobileTask.value === 'history') {
    portalMobileTask.value = 'quote'
    void scrollToQuoteDesk()
    return
  }
  if (!productOptions.value.length) {
    void loadPortalContext(true)
    return
  }
  portalMobileTask.value = 'quote'
  void scrollToQuoteDesk()
}

function runPortalStickySecondaryAction() {
  openSupplierBackend()
}

async function runPortalQuoteQueueAction(action: 'pending' | 'drafts' | 'history') {
  if (action === 'history') {
    portalMobileTask.value = 'history'
    void scrollToQuoteDesk()
    return
  }
  portalMobileTask.value = 'quote'
  if (action === 'drafts' && !quoteDraftSummary.count) {
    lazyElMessage.info('当前还没有本机草稿，填写报价后可先保存草稿')
  }
  void scrollToQuoteDesk()
}

function runPortalScopeAction(action: 'scope' | 'history' | 'backend' | 'quote') {
  if (action === 'history') {
    portalMobileTask.value = 'history'
    void scrollToQuoteDesk()
    return
  }
  portalMobileTask.value = 'quote'
  void scrollToQuoteDesk()
}

function runPortalAction(action: 'quote' | 'products' | 'refresh' | 'history' | 'backend') {
  if (action === 'quote') {
    portalMobileTask.value = 'quote'
    scrollToQuoteDesk()
    return
  }
  if (action === 'products') {
    scrollToProductStrip()
    return
  }
  if (action === 'refresh') {
    void loadPortalContext(true)
    return
  }
  if (action === 'history') {
    portalMobileTask.value = 'history'
    void scrollToQuoteDesk()
    return
  }
  openSupplierBackend()
}

async function restoreAuthSession() {
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

async function submitAuthLogin() {
  const username = authForm.username.trim()
  const password = authForm.password
  if (!username || !password) {
    authError.value = '请填写账号和密码'
    return
  }
  authSubmitting.value = true
  authError.value = ''
  try {
    authForm.username = username
    const session = await login({ username, password })
    applyAuthSession(session)
    await loadPortalContext(true)
    if (!isMobileViewport.value) {
      lazyElMessage.success('已登录供应商报价页')
    }
  } catch (error) {
    authError.value = extractApiErrorDetail(error) || '登录失败，请检查账号或密码'
  } finally {
    authSubmitting.value = false
  }
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
    await loadPortalContext(true)
    lazyElMessage.success('密码已重置')
  } catch (error) {
    passwordResetError.value = extractApiErrorDetail(error) || '密码重置失败'
  } finally {
    passwordResetSubmitting.value = false
  }
}

function logoutAuthSession() {
  applyAuthSession(null)
}

async function loadPortalContext(force = false) {
  if (portalContextLoading.value && !force) return
  portalContextLoading.value = true
  try {
    const [locationResult, productOptionResult] = await Promise.allSettled([
      fetchLocationOptions(),
      fetchProductOptions({}),
    ])
    if (locationResult.status === 'rejected') {
      // Location options are only context hints for this portal; product selection must stay usable.
    }
    if (productOptionResult.status !== 'fulfilled') {
      throw productOptionResult.reason
    }
    productOptions.value = productOptionResult.value.items ?? []
    if (queryIdentityKey) {
      const matchedQueryProduct = productOptions.value.find((item) => item.price_identity_key === queryIdentityKey || item.price_identity_label === queryProductLabel)
      selectedIdentityKey.value = matchedQueryProduct?.price_identity_key || queryIdentityKey
      selectedProductFallbackLabel.value = matchedQueryProduct?.price_identity_label || queryProductLabel || queryIdentityKey
      return
    }
    if (!selectedIdentityKey.value && productOptions.value.length) {
      selectedIdentityKey.value = productOptions.value[0].price_identity_key
      selectedProductFallbackLabel.value = productOptions.value[0].price_identity_label
    }
  } catch {
    // Portal remains usable after login even if context hints are temporarily unavailable.
  } finally {
    portalContextLoading.value = false
  }
}

onMounted(async () => {
  await restoreAuthSession()
  if (isAuthenticated.value) {
    await loadPortalContext()
  }
})
</script>

<style scoped>
@media (min-width: 981px) {
  :global(.supplier-portal-shell.auth-only:not(.mobile)) {
    padding: 32px;
  }

  :global(.supplier-portal-auth-page) {
    grid-template-columns: minmax(0, 1fr) minmax(360px, 420px);
    align-items: stretch;
    width: min(960px, calc(100vw - 64px));
  }

  :global(.supplier-portal-auth-hero) {
    align-content: space-between;
    min-height: 430px;
  }
}

@media (max-width: 980px) {
  :global(.supplier-portal-shell.mobile button),
  :global(.supplier-portal-shell.mobile .el-button),
  :global(.supplier-portal-shell.mobile .el-input__wrapper),
  :global(.supplier-portal-shell.mobile .el-select__wrapper),
  :global(.supplier-portal-shell.mobile .el-textarea__inner),
  :global(.supplier-portal-shell.mobile .el-input-number),
  :global(.supplier-portal-shell.mobile .el-input-number__decrease),
  :global(.supplier-portal-shell.mobile .el-input-number__increase) {
    min-height: 44px !important;
  }

  :global(.supplier-portal-shell.mobile .el-input-number .el-input__inner) {
    min-height: 44px;
    line-height: 44px;
  }

  :global(.supplier-portal-shell.mobile .supplier-portal-scope-card),
  :global(.supplier-portal-shell.mobile .supplier-portal-quote-queue-card),
  :global(.supplier-portal-shell.mobile .supplier-portal-action-card),
  :global(.supplier-portal-shell.mobile .supplier-portal-product-chip),
  :global(.supplier-portal-shell.mobile .supplier-portal-todo-card),
  :global(.supplier-portal-shell.mobile .supplier-portal-sticky-actions button),
  :global(.supplier-portal-shell.mobile .supplier-portal-auth-tabs button),
  :global(.supplier-portal-shell.mobile .supplier-portal-auth-foot button),
  :global(.supplier-portal-shell.mobile .supplier-portal-auth-note button) {
    min-height: 44px !important;
  }

  :global(.supplier-portal-shell.mobile .supplier-portal-auth-foot button),
  :global(.supplier-portal-shell.mobile .supplier-portal-auth-note button) {
    padding: 0 10px;
  }
}
</style>
