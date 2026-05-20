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
            <p class="panel-kicker">供应商前端</p>
            <h1>供应商报价门户</h1>
          </div>
        </div>
        <p>登录后直接处理今天待报价的商品、草稿和历史，不需要先判断该进哪个后台。</p>
        <div class="supplier-portal-auth-actions">
          <el-button plain @click="backToMainWorkspace">返回采购工作台</el-button>
        </div>
      </div>
      <div class="supplier-portal-login-card supplier-portal-auth-card" data-testid="supplier-login-form">
        <div class="supplier-portal-auth-tabs">
          <button type="button" :class="{ active: authMode === 'login' }" @click="setAuthMode('login')">登录</button>
          <button type="button" :class="{ active: authMode === 'register' }" @click="setAuthMode('register')">注册</button>
        </div>

        <template v-if="authMode === 'login'">
          <strong>账号登录</strong>
          <el-input v-model="authForm.username" data-testid="auth-username-input" placeholder="账号" />
          <el-input
            v-model="authForm.password"
            data-testid="auth-password-input"
            type="password"
            show-password
            placeholder="密码"
            @keyup.enter="submitAuthLogin"
          />
          <p v-if="authError" class="supplier-portal-error">{{ authError }}</p>
          <el-button type="primary" data-testid="auth-login-button" :loading="authSubmitting" @click="submitAuthLogin">
            登录门户
          </el-button>
          <div class="supplier-portal-auth-foot">
            <button type="button" @click="setAuthMode('register')">申请账号</button>
            <button type="button" @click="showPasswordHelp">忘记密码</button>
          </div>
        </template>

        <template v-else-if="registrationSubmitted">
          <strong>申请已提交，等待审核</strong>
          <small class="supplier-portal-form-tip">管理员审核并开通账号后才能登录；当前不会立即生成可用密码。</small>
          <div class="supplier-portal-workbench-strip">
            <article class="supplier-portal-workbench-card">
              <span>申请账号</span>
              <strong>{{ lastRegistrationUsername || '已提交' }}</strong>
              <small>请等待管理员审核，审核通过后再回到登录页。</small>
            </article>
          </div>
          <div class="supplier-portal-auth-foot">
            <button type="button" @click="setAuthMode('login')">返回登录</button>
            <button type="button" @click="resetRegistrationForm">继续提交新申请</button>
          </div>
        </template>

        <template v-else>
          <strong>注册申请</strong>
          <el-input v-model="registerForm.supplierName" data-testid="supplier-register-name" placeholder="供应商名称" />
          <el-input v-model="registerForm.contactName" data-testid="supplier-register-contact" placeholder="联系人" />
          <el-input v-model="registerForm.contactPhone" data-testid="supplier-register-phone" placeholder="手机号" />
          <el-input v-model="registerForm.username" data-testid="supplier-register-username" placeholder="登录账号" />
          <p v-if="authError" class="supplier-portal-error">{{ authError }}</p>
          <el-button type="primary" data-testid="supplier-register-submit" :loading="authSubmitting" @click="submitRegisterRequest">提交申请</el-button>
          <div class="supplier-portal-auth-foot">
            <button type="button" @click="setAuthMode('login')">已有账号，去登录</button>
          </div>
        </template>
      </div>
    </main>

    <template v-else>
    <header class="panel supplier-portal-topbar">
      <div class="supplier-portal-brand">
        <div class="supplier-portal-brand-mark">报</div>
        <div class="supplier-portal-brand-copy">
          <p class="panel-kicker">供应商前端</p>
          <h1>供应商报价门户</h1>
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
          <div class="supplier-portal-login-layout" :class="{ mobile: isMobileViewport }">
            <div class="supplier-portal-auth-intro">
              <span>SUPPLIER PORTAL</span>
              <strong>供应商报价入口</strong>
              <small>供应商只需要处理报价、草稿和历史；档案、结算和账号管理由管理员在后台完成。</small>
              <div>
                <b>实时报价</b>
                <b>批量导入</b>
                <b>记录留痕</b>
              </div>
              <div class="supplier-portal-auth-preview">
                <article>
                  <span>01</span>
                  <strong>登录账号</strong>
                  <small>进入自己的报价范围</small>
                </article>
                <article>
                  <span>02</span>
                  <strong>选择商品</strong>
                  <small>按当前商品录价</small>
                </article>
                <article>
                  <span>03</span>
                  <strong>提交报价</strong>
                  <small>保存记录并留痕</small>
                </article>
              </div>
              <div class="supplier-portal-auth-note">
                <div>
                  <strong>还没有账号？</strong>
                  <small>提交申请后，管理员开通即可登录。</small>
                </div>
                <button type="button" @click="setAuthMode('register')">申请账号</button>
              </div>
            </div>

            <div class="supplier-portal-login-card" data-testid="supplier-login-form">
              <div class="supplier-portal-auth-tabs">
                <button type="button" :class="{ active: authMode === 'login' }" @click="setAuthMode('login')">登录</button>
                <button type="button" :class="{ active: authMode === 'register' }" @click="setAuthMode('register')">注册</button>
              </div>

              <template v-if="authMode === 'login'">
                <strong>账号登录</strong>
                <el-input v-model="authForm.username" data-testid="auth-username-input" placeholder="账号" />
                <el-input
                  v-model="authForm.password"
                  data-testid="auth-password-input"
                  type="password"
                  show-password
                  placeholder="密码"
                  @keyup.enter="submitAuthLogin"
                />
                <p v-if="authError" class="supplier-portal-error">{{ authError }}</p>
                <el-button type="primary" data-testid="auth-login-button" :loading="authSubmitting" @click="submitAuthLogin">
                  登录
                </el-button>
                <div class="supplier-portal-auth-foot">
                  <button type="button" @click="setAuthMode('register')">申请账号</button>
                  <button type="button" @click="showPasswordHelp">忘记密码</button>
                </div>
              </template>

              <template v-else-if="registrationSubmitted">
                <strong>申请已提交，等待审核</strong>
                <small class="supplier-portal-form-tip">管理员审核并开通账号后才能登录；当前不会立即生成可用密码。</small>
                <div class="supplier-portal-workbench-strip">
                  <article class="supplier-portal-workbench-card">
                    <span>申请账号</span>
                    <strong>{{ lastRegistrationUsername || '已提交' }}</strong>
                    <small>请等待管理员审核，审核通过后再回到登录页。</small>
                  </article>
                </div>
                <div class="supplier-portal-auth-foot">
                  <button type="button" @click="setAuthMode('login')">返回登录</button>
                  <button type="button" @click="resetRegistrationForm">继续提交新申请</button>
                </div>
              </template>

              <template v-else>
                <strong>注册申请</strong>
                <small class="supplier-portal-form-tip">提交资料后由管理员开通账号。</small>
                <el-input v-model="registerForm.supplierName" data-testid="supplier-register-name" placeholder="供应商名称" />
                <el-input v-model="registerForm.contactName" data-testid="supplier-register-contact" placeholder="联系人" />
                <el-input v-model="registerForm.contactPhone" data-testid="supplier-register-phone" placeholder="手机号" />
                <el-input v-model="registerForm.username" data-testid="supplier-register-username" placeholder="登录账号" />
                <p v-if="authError" class="supplier-portal-error">{{ authError }}</p>
                <el-button type="primary" data-testid="supplier-register-submit" :loading="authSubmitting" @click="submitRegisterRequest">提交申请</el-button>
                <div class="supplier-portal-auth-foot">
                  <button type="button" @click="setAuthMode('login')">已有账号，去登录</button>
                </div>
              </template>
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
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'

import {
  clearAuthSession,
  createSupplierRegistrationRequest,
  extractApiErrorDetail,
  fetchCurrentUser,
  fetchLocationOptions,
  fetchProductOptions,
  login,
  readAuthSession,
  writeAuthSession,
} from './api'
import SupplierAdminPanel from './components/SupplierAdminPanel.vue'
import { useViewport } from './composables/useViewport'
import type { AuthLoginResponse, AuthUserItem, ProductOptionItem } from './types'
import './supplier-portal.css'

const MAIN_APP_PATH = '/'
const SUPPLIER_BACKEND_PATH = '/supplier-backend'
const { isMobileViewport } = useViewport()

const authSession = ref<AuthLoginResponse | null>(readAuthSession())
const authSubmitting = ref(false)
const authRestoring = ref(false)
const portalContextLoading = ref(false)
const authError = ref('')
const authMode = ref<'login' | 'register'>('login')
const authForm = reactive({ username: '', password: '' })
const registrationSubmitted = ref(false)
const lastRegistrationUsername = ref('')
const registerForm = reactive({
  supplierName: '',
  contactName: '',
  contactPhone: '',
  username: '',
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
  if (!isAuthenticated.value) return '当前范围：待登录'
  if (currentAuthRole.value === 'admin') return '当前范围：管理员账号；门户仅处理录价，供应商资料与结算请回管理台维护'
  return currentUser.value?.supplier_profile?.supplier_name
    ? `当前范围：${currentUser.value.supplier_profile.supplier_name}`
    : '当前范围：仅限已绑定供应商'
})
const portalLiveCards = computed(() => [
  {
    label: '账号范围',
    title: isAuthenticated.value ? (currentUser.value?.display_name || currentUser.value?.username || '已登录') : '待登录',
    detail: isAuthenticated.value ? currentAuthScopeLabel.value : '登录后按真实账号限制可维护的供应商范围。',
  },
  {
    label: '商品目录',
    title: portalContextLoading.value ? '商品同步中' : `${productOptions.value.length} 个可选商品`,
    detail: selectedProductLabel.value
      ? `当前商品：${selectedProductLabel.value}`
      : (portalContextLoading.value ? '正在读取后端商品目录。' : '后端暂未返回可选商品。'),
  },
  {
    label: '写入链路',
    title: 'API 提交',
    detail: '报价、批量导入和作废动作都会写入后端供应商报价记录。',
  },
])
const portalWorkbenchCards = computed(() => [
  {
    label: '门户范围',
    value: currentAuthRole.value === 'admin' ? '管理员账号' : (currentUser.value?.supplier_profile?.supplier_name || '待绑定'),
    detail: currentAuthRole.value === 'admin' ? '门户只保留录价动作，资料和结算回管理台处理' : currentAuthScopeLabel.value,
  },
  {
    label: '可选商品',
    value: `${productOptions.value.length} 个`,
    detail: selectedProductLabel.value
      ? `当前录价商品：${selectedProductLabel.value}`
      : (portalContextLoading.value ? '商品目录同步中' : '请先确认后端商品目录接口返回'),
  },
  {
    label: '数据链路',
    value: '后端同步',
    detail: '报价提交后通过 API 写入供应商报价记录',
  },
])
const portalScopeCards = computed(() => {
  if (currentAuthRole.value === 'admin') {
    return [
      {
        key: 'scope' as const,
        label: '身份范围',
        value: '管理员账号',
        detail: '门户可临时录价，供应商资料和结算仍在管理台处理',
        tone: 'primary',
      },
      {
        key: 'history' as const,
        label: '数据边界',
        value: '全局可见',
        detail: '历史记录按当前选中供应商收拢',
        tone: 'neutral',
      },
      {
        key: 'scope' as const,
        label: '下一步',
        value: '继续录价',
        detail: '管理员在此确认商品和最新报价，资料维护再回管理台处理',
        tone: 'neutral',
      },
    ]
  }

  const supplierName = currentUser.value?.supplier_profile?.supplier_name || ''
  return [
    {
      key: 'scope' as const,
      label: '身份范围',
      value: supplierName || '待绑定供应商',
      detail: supplierName ? '仅维护当前供应商报价' : '管理员绑定档案后才能录价',
      tone: supplierName ? 'primary' : 'warning',
    },
    {
      key: 'history' as const,
      label: '数据边界',
      value: supplierName ? '本供应商' : '未开通',
      detail: supplierName ? '历史、草稿和提交都按当前供应商隔离' : '暂无可查看的报价范围',
      tone: 'neutral',
    },
    {
      key: supplierName ? 'quote' as const : 'backend' as const,
      label: '下一步',
      value: supplierName ? '继续录价' : '申请绑定',
      detail: supplierName ? '回到报价表单填写当前商品' : '请联系管理员完成绑定后再录价',
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
    detail: currentAuthRole.value === 'admin' ? '门户内先看最近记录' : '查看自己的历史报价',
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
const portalStickySecondaryLabel = computed(() => '去后台')
function applyAuthSession(session: AuthLoginResponse | null) {
  authSession.value = session
  if (session) {
    writeAuthSession(session)
  } else {
    clearAuthSession()
  }
}

function setAuthMode(mode: 'login' | 'register') {
  authMode.value = mode
  authError.value = ''
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

function runPortalQuoteQueueAction(action: 'pending' | 'drafts' | 'history') {
  if (action === 'history') {
    portalMobileTask.value = 'history'
    void scrollToQuoteDesk()
    return
  }
  portalMobileTask.value = 'quote'
  if (action === 'drafts' && !quoteDraftSummary.count) {
    ElMessage.info('当前还没有本机草稿，填写报价后可先保存草稿')
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
      ElMessage.success('已登录供应商门户')
    }
  } catch (error) {
    authError.value = extractApiErrorDetail(error) || '登录失败，请检查账号或密码'
  } finally {
    authSubmitting.value = false
  }
}

function submitRegisterRequest() {
  authError.value = ''
  registrationSubmitted.value = false
  const supplierName = registerForm.supplierName.trim()
  const contactName = registerForm.contactName.trim()
  const contactPhone = registerForm.contactPhone.trim()
  const username = registerForm.username.trim()
  if (!supplierName || !contactPhone || !username) {
    authError.value = '请填写供应商名称、手机号和登录账号'
    return
  }
  authSubmitting.value = true
  createSupplierRegistrationRequest({
    company_name: supplierName,
    contact_name: contactName || undefined,
    contact_phone: contactPhone,
    username,
  }).then(() => {
    ElMessage.success('注册申请已提交，请等待管理员审核开通')
    registrationSubmitted.value = false
    authMode.value = 'login'
    lastRegistrationUsername.value = username
    authForm.username = username
    registerForm.supplierName = ''
    registerForm.contactName = ''
    registerForm.contactPhone = ''
    registerForm.username = ''
  }).catch((error) => {
    authError.value = extractApiErrorDetail(error) || '注册申请提交失败'
  }).finally(() => {
    authSubmitting.value = false
  })
}

function resetRegistrationForm() {
  registrationSubmitted.value = false
  authError.value = ''
  authMode.value = 'register'
}

function showPasswordHelp() {
  ElMessage.info('请联系管理员重置密码')
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
  await Promise.all([restoreAuthSession(), loadPortalContext()])
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
