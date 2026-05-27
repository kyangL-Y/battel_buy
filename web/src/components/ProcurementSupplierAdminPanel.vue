<template>
  <section class="panel procurement-supplier-admin" data-testid="procurement-supplier-admin-panel">
    <div class="procurement-head">
      <div>
        <p class="panel-kicker">采购端</p>
        <h2>供应商管理</h2>
        <p>这里只维护正式供应商、账号状态和注册审核，不承载报价导入、历史、结算等供应平台工作区。</p>
      </div>
      <div class="procurement-head-actions">
        <el-button plain :loading="loading" @click="loadAll">刷新数据</el-button>
      </div>
    </div>

    <div class="procurement-stats">
      <article>
        <span>启用供应商</span>
        <strong>{{ activeSupplierCount }}</strong>
        <small>可继续承接采购协同</small>
      </article>
      <article>
        <span>覆盖分类</span>
        <strong>{{ categoryCount }}</strong>
        <small>按主营分类管理</small>
      </article>
      <article>
        <span>最近录价</span>
        <strong>{{ latestQuotedAtLabel }}</strong>
        <small>{{ overview?.recent_quotes?.[0]?.supplier_name || '暂无记录' }}</small>
      </article>
      <article>
        <span>累计报价</span>
        <strong>{{ totalQuoteCount }}</strong>
        <small>只作为采购参考计数</small>
      </article>
    </div>

    <div v-if="!effectiveAuthRole" class="procurement-auth-gate" data-testid="procurement-supplier-login-gate">
      <div>
        <p class="panel-kicker">需要采购端登录</p>
        <strong>登录状态已失效，请重新登录后进入供应商管理</strong>
        <span>请重新使用采购管理员账号登录。</span>
      </div>
      <div class="procurement-auth-form">
        <el-input v-model="authForm.username" data-testid="procurement-auth-username" placeholder="采购端账号" />
        <el-input
          v-model="authForm.password"
          data-testid="procurement-auth-password"
          type="password"
          show-password
          placeholder="密码"
          @keyup.enter="submitProcurementLogin"
        />
        <p v-if="authError" class="procurement-auth-error">{{ authError }}</p>
        <el-button type="primary" :loading="authSubmitting" data-testid="procurement-auth-login" @click="submitProcurementLogin">
          登录并进入管理
        </el-button>
      </div>
    </div>

    <section v-if="!effectiveAuthRole" class="procurement-auth-preview" aria-label="供应商管理能力预览">
      <article>
        <span>登录后第一步</span>
        <strong>维护正式供应商</strong>
        <small>新增、停用、分类和联系信息只在采购端统一管理。</small>
      </article>
      <article>
        <span>登录后第二步</span>
        <strong>处理注册审核</strong>
        <small>新申请供应商审核通过后，直接转入正式供应商档案。</small>
      </article>
      <article>
        <span>登录后第三步</span>
        <strong>分配供应商账号</strong>
        <small>给供应商开通报价入口，避免报价、结算、档案混在一起。</small>
      </article>
    </section>

    <el-alert
      v-else-if="effectiveAuthRole !== 'admin'"
      class="procurement-permission-alert"
      type="warning"
      :closable="false"
      title="当前账号无权进入采购端供应商管理"
      description="供应商账号只能进入供应平台录价、查看报价历史和结算；采购端供应商管理需要管理员账号。"
      show-icon
    />

    <div v-else class="procurement-view-switch">
      <button type="button" :class="{ active: currentView === 'archive' }" @click="currentView = 'archive'">
        <strong>供应商管理</strong>
        <small>维护正式供应商与账号</small>
      </button>
      <button type="button" :class="{ active: currentView === 'applications' }" @click="currentView = 'applications'">
        <strong>注册审核</strong>
        <small>处理新申请并转正式供应商</small>
      </button>
      <button type="button" :class="{ active: currentView === 'accounts' }" @click="currentView = 'accounts'">
        <strong>账号管理</strong>
        <small>管理员、供应商账号与权限</small>
      </button>
    </div>

    <SupplierRegistrationAdminPanel v-if="effectiveAuthRole === 'admin' && currentView === 'applications'" />
    <AccountAdminPanel
      v-else-if="effectiveAuthRole === 'admin' && currentView === 'accounts'"
      :current-user-id="localAuthSession?.user.id"
    />

    <div v-else-if="effectiveAuthRole === 'admin'" class="procurement-layout">
      <section class="procurement-list-shell">
        <div class="procurement-list-head">
          <strong>供应商管理</strong>
          <span>{{ filteredSuppliers.length }} 家</span>
        </div>
        <div class="procurement-list-toolbar">
          <el-input v-model="keyword" clearable placeholder="搜索供应商、联系人、分类、账号" />
          <el-select v-model="categoryFilter" clearable filterable placeholder="按分类筛选">
            <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="statusFilter" placeholder="状态">
            <el-option label="全部状态" value="all" />
            <el-option label="仅启用" value="active" />
            <el-option label="仅停用" value="inactive" />
          </el-select>
        </div>
        <div class="procurement-list-summary">
          <article>
            <span>筛选结果</span>
            <strong>{{ filteredSuppliers.length }}</strong>
          </article>
          <article>
            <span>启用中</span>
            <strong>{{ activeSupplierCount }}</strong>
          </article>
          <article>
            <span>最近录价</span>
            <strong>{{ latestQuotedAtLabel }}</strong>
          </article>
        </div>
        <div class="procurement-card-list">
          <button
            v-for="item in filteredSuppliers"
            :key="item.id"
            type="button"
            class="procurement-supplier-card"
            :class="{ active: selectedSupplierId === item.id }"
            @click="selectSupplier(item.id)"
          >
            <div class="procurement-supplier-card-head">
              <strong>{{ item.supplier_name }}</strong>
              <span :class="['procurement-status-chip', item.is_active ? 'active' : 'inactive']">
                {{ item.is_active ? '启用' : '停用' }}
              </span>
            </div>
            <div class="procurement-supplier-card-meta">
              <span>{{ item.market_category || '待分类' }}</span>
              <span>{{ item.channel || '待标渠道' }}</span>
              <span>{{ item.quote_count || 0 }} 条报价</span>
            </div>
            <div class="procurement-supplier-card-submeta">
              <span>{{ item.account_username || '未配置账号' }}</span>
              <span>{{ item.account_is_active === false ? '账号停用' : '账号可用' }}</span>
            </div>
            <small>{{ formatTime(item.latest_quoted_at) }}</small>
          </button>
          <div v-if="!filteredSuppliers.length" class="procurement-empty">
            <strong>还没有供应商</strong>
            <p>先创建供应商，后续注册审核通过后也会落到这里。</p>
          </div>
        </div>
      </section>

      <section class="procurement-form-shell">
        <div class="procurement-selected-banner" v-if="selectedSupplier">
          <span>当前选中供应商</span>
          <strong>{{ selectedSupplier.supplier_name }}</strong>
          <small>{{ selectedSupplier.market_category || '待分类' }} · {{ selectedSupplier.channel || '待标渠道' }} · {{ selectedSupplier.market_scope || '本地市场' }}</small>
        </div>

        <div class="procurement-form-head">
          <strong>{{ selectedSupplier ? '编辑供应商' : '新增供应商' }}</strong>
          <span>{{ selectedSupplier ? `ID ${selectedSupplier.id}` : '新建' }}</span>
        </div>

        <div class="procurement-form-grid">
          <label>
            <span>供应商名称</span>
            <el-input v-model="supplierForm.supplier_name" placeholder="例如：莲菜档口A" />
          </label>
          <label>
            <span>联系人</span>
            <el-input v-model="supplierForm.contact_name" placeholder="例如：老王" />
          </label>
          <label>
            <span>联系电话</span>
            <el-input v-model="supplierForm.contact_phone" placeholder="例如：13800000000" />
          </label>
          <label>
            <span>市场范围</span>
            <el-input v-model="supplierForm.market_scope" placeholder="本地市场 / 周边市场" />
          </label>
          <label>
            <span>主营分类</span>
            <el-select v-model="supplierForm.market_category" clearable filterable placeholder="选择分类">
              <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </label>
          <label>
            <span>默认渠道</span>
            <el-select v-model="supplierForm.channel" clearable filterable placeholder="选择渠道">
              <el-option v-for="item in channelOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </label>
        </div>

        <label class="procurement-full">
          <span>备注</span>
          <el-input v-model="supplierForm.notes" type="textarea" :rows="3" placeholder="例如：只做干调、下午统一发车、支持月结" />
        </label>

        <div class="procurement-account-card">
          <div class="procurement-form-head compact">
            <strong>供应商账号</strong>
            <span>{{ accountSummaryLabel }}</span>
          </div>
          <div class="procurement-form-grid">
            <label>
              <span>登录账号</span>
              <el-input v-model="accountForm.account_username" placeholder="例如：lencai-a" />
            </label>
            <label>
              <span>显示名称</span>
              <el-input v-model="accountForm.account_display_name" placeholder="例如：莲菜档口A" />
            </label>
            <label>
              <span>{{ selectedSupplier?.account_username ? '重置密码' : '初始密码' }}</span>
              <el-input v-model="accountForm.account_password" type="password" show-password placeholder="新建账号必须填写；编辑时留空保持原密码" />
            </label>
            <label>
              <span>账号状态</span>
              <el-switch v-model="accountForm.account_is_active" inline-prompt active-text="启" inactive-text="停" />
            </label>
          </div>
        </div>

        <div class="procurement-form-actions">
          <label class="procurement-status-toggle">
            <span>供应商状态</span>
            <el-switch v-model="supplierForm.is_active" inline-prompt active-text="启" inactive-text="停" />
          </label>
          <div class="procurement-form-buttons">
            <el-button plain @click="resetSupplierForm">新建空白</el-button>
            <el-button type="primary" :loading="saving" @click="saveSupplierForm">
              {{ selectedSupplier ? '保存修改' : '创建供应商' }}
            </el-button>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import ElAlert from 'element-plus/es/components/alert/index.mjs'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'

import {
  clearAuthSession,
  createSupplier,
  extractApiErrorDetail,
  fetchSupplierOverview,
  fetchSuppliers,
  getApiErrorStatus,
  login,
  readAuthSession,
  updateSupplier,
  writeAuthSession,
} from '../api'
import AccountAdminPanel from './AccountAdminPanel.vue'
import SupplierRegistrationAdminPanel from './SupplierRegistrationAdminPanel.vue'
import type { AuthLoginResponse, AuthUserRole, SupplierItem, SupplierOverviewResponse, SupplierUpdatePayload } from '../types'

const props = defineProps<{
  authRole?: AuthUserRole | null
}>()

const ACCOUNT_USERNAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.@-]{2,63}$/
const MIN_ACCOUNT_PASSWORD_LENGTH = 8
const currentView = ref<'archive' | 'applications' | 'accounts'>('archive')
const loading = ref(false)
const saving = ref(false)
const authSubmitting = ref(false)
const localAuthSession = ref<AuthLoginResponse | null>(readAuthSession())
const effectiveAuthRole = computed<AuthUserRole | null>(() => props.authRole || localAuthSession.value?.user.role || null)
const authError = ref('')
const suppliers = ref<SupplierItem[]>([])
const overview = ref<SupplierOverviewResponse | null>(null)
const selectedSupplierId = ref<number | null>(null)
const keyword = ref('')
const categoryFilter = ref('')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')

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

const accountForm = reactive({
  account_username: '',
  account_password: '',
  account_display_name: '',
  account_is_active: true,
})

const authForm = reactive({
  username: 'admin',
  password: '',
})

const selectedSupplier = computed(() => suppliers.value.find((item) => item.id === selectedSupplierId.value) || null)
const activeSupplierCount = computed(() => suppliers.value.filter((item) => item.is_active).length)
const categoryCount = computed(() => new Set(suppliers.value.map((item) => item.market_category).filter(Boolean)).size)
const totalQuoteCount = computed(() => suppliers.value.reduce((sum, item) => sum + Number(item.quote_count || 0), 0))
const latestQuotedAtLabel = computed(() => formatTime(overview.value?.summary.latest_quoted_at))
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
    ].filter(Boolean).some((value) => String(value).toLowerCase().includes(search))
  })
})
const accountSummaryLabel = computed(() => {
  if (!selectedSupplier.value?.account_username) return '未配置'
  return `${selectedSupplier.value.account_username} · ${accountForm.account_is_active ? '账号已启用' : '账号已停用'}`
})

function formatTime(value?: string | null) {
  if (!value) return '暂无'
  return String(value).replace('T', ' ').slice(5, 16)
}

function fillSupplierForm(item: SupplierItem | null) {
  supplierForm.supplier_name = item?.supplier_name || ''
  supplierForm.contact_name = item?.contact_name || ''
  supplierForm.contact_phone = item?.contact_phone || ''
  supplierForm.market_scope = item?.market_scope || '本地市场'
  supplierForm.market_category = item?.market_category || ''
  supplierForm.channel = item?.channel || '微信小程序'
  supplierForm.notes = item?.notes || ''
  supplierForm.is_active = item?.is_active == null ? true : Boolean(item.is_active)
  accountForm.account_username = item?.account_username || ''
  accountForm.account_password = ''
  accountForm.account_display_name = item?.account_display_name || ''
  accountForm.account_is_active = item?.account_is_active == null ? true : Boolean(item.account_is_active)
}

function resetSupplierForm() {
  selectedSupplierId.value = null
  fillSupplierForm(null)
}

function selectSupplier(id: number) {
  selectedSupplierId.value = id
}

function validateAccountFormBeforeSave() {
  const username = accountForm.account_username.trim()
  const password = accountForm.account_password.trim()
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

async function loadAll() {
  if (effectiveAuthRole.value !== 'admin') {
    suppliers.value = []
    overview.value = null
    selectedSupplierId.value = null
    return
  }
  loading.value = true
  try {
    const [supplierData, overviewData] = await Promise.all([
      fetchSuppliers(false),
      fetchSupplierOverview(),
    ])
    suppliers.value = supplierData.items || []
    overview.value = overviewData
    authError.value = ''
    if (!suppliers.value.some((item) => item.id === selectedSupplierId.value)) {
      selectedSupplierId.value = suppliers.value[0]?.id ?? null
    }
  } catch (error) {
    const status = getApiErrorStatus(error)
    if (status === 401 || status === 403) {
      if (status === 401) {
        clearAuthSession()
        localAuthSession.value = null
      }
      authError.value = status === 401 ? '登录状态已失效，请重新登录后进入供应商管理' : '当前账号没有权限进入供应商管理'
    } else {
      authError.value = extractApiErrorDetail(error) || '供应商管理读取失败，请确认采购端登录状态和权限'
    }
    ElMessage.error(authError.value)
  } finally {
    loading.value = false
  }
}

async function submitProcurementLogin() {
  if (!authForm.username.trim() || !authForm.password.trim()) {
    authError.value = '请填写采购端账号和密码'
    return
  }
  authSubmitting.value = true
  authError.value = ''
  try {
    const session = await login({ username: authForm.username.trim(), password: authForm.password })
    writeAuthSession(session)
    localAuthSession.value = session
    if (session.user.role !== 'admin') {
      authError.value = '当前账号不是采购管理员，无法进入供应商管理'
      return
    }
    ElMessage.success('采购端登录成功，正在进入供应商管理')
    await loadAll()
  } catch (error) {
    authError.value = extractApiErrorDetail(error) || '登录失败，请检查账号密码'
  } finally {
    authSubmitting.value = false
  }
}

async function saveSupplierForm() {
  if (effectiveAuthRole.value !== 'admin') {
    ElMessage.warning('当前账号没有权限进入供应商管理')
    return
  }
  if (!supplierForm.supplier_name.trim()) {
    ElMessage.warning('请填写供应商名称')
    return
  }
  if (!validateAccountFormBeforeSave()) {
    return
  }
  saving.value = true
  try {
    const payload: SupplierUpdatePayload = {
      supplier_name: supplierForm.supplier_name.trim(),
      contact_name: supplierForm.contact_name.trim() || undefined,
      contact_phone: supplierForm.contact_phone.trim() || undefined,
      market_scope: supplierForm.market_scope.trim() || undefined,
      market_category: supplierForm.market_category.trim() || undefined,
      channel: supplierForm.channel.trim() || undefined,
      notes: supplierForm.notes.trim() || undefined,
      is_active: supplierForm.is_active,
      account_username: accountForm.account_username.trim() || undefined,
      account_password: accountForm.account_password.trim() || undefined,
      account_display_name: accountForm.account_display_name.trim() || undefined,
      account_is_active: accountForm.account_is_active,
    }
    if (!selectedSupplierId.value) {
      const created = await createSupplier(payload)
      selectedSupplierId.value = created.id
      ElMessage.success('供应商已创建')
    } else {
      await updateSupplier(selectedSupplierId.value, payload)
      ElMessage.success('供应商已更新')
    }
    await loadAll()
  } catch (error) {
    ElMessage.error(extractApiErrorDetail(error) || '供应商保存失败')
  } finally {
    saving.value = false
  }
}

watch(selectedSupplier, (item) => {
  fillSupplierForm(item)
}, { immediate: true })

watch(effectiveAuthRole, async (role, previousRole) => {
  if (role === 'admin' && previousRole !== 'admin') {
    authError.value = ''
    await loadAll()
  }
  if (role !== 'admin') {
    suppliers.value = []
    overview.value = null
    selectedSupplierId.value = null
  }
})

onMounted(async () => {
  if (effectiveAuthRole.value === 'admin') {
    await loadAll()
  }
})
</script>

<style scoped>
.procurement-supplier-admin {
  display: grid;
  gap: 14px;
}

.procurement-head,
.procurement-stats,
.procurement-auth-gate,
.procurement-auth-preview,
.procurement-view-switch,
.procurement-layout,
.procurement-list-shell,
.procurement-form-shell,
.procurement-supplier-card,
.procurement-account-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.procurement-head,
.procurement-stats,
.procurement-layout {
  padding: 16px 18px;
}

.procurement-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
}

.procurement-head h2 {
  margin: 4px 0 6px;
  font-size: 22px;
  color: #020817;
}

.procurement-head p:last-child {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.55;
}

.procurement-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.procurement-stats article {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.procurement-stats span {
  color: #64748b;
  font-size: 12px;
}

.procurement-stats strong {
  color: #020817;
  font-size: 24px;
}

.procurement-auth-gate {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(260px, 0.9fr);
  gap: 16px;
  align-items: center;
  padding: 18px;
  border-color: #bfdbfe;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 58%, #f8fafc 100%);
}

.procurement-auth-gate strong {
  display: block;
  margin: 4px 0 8px;
  color: #0f172a;
  font-size: 18px;
}

.procurement-auth-gate span {
  display: block;
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
}

.procurement-auth-form {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid #dbe4ef;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.86);
}

.procurement-auth-error {
  margin: 0;
  color: #dc2626;
  font-size: 12px;
}

.procurement-auth-preview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding: 14px;
  border-color: #dbeafe;
  background: linear-gradient(135deg, #ffffff, #f8fbff);
}

.procurement-auth-preview article {
  display: grid;
  gap: 6px;
  min-height: 116px;
  padding: 14px 15px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
}

.procurement-auth-preview span {
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
}

.procurement-auth-preview strong {
  color: #0f172a;
  font-size: 17px;
}

.procurement-auth-preview small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.procurement-permission-alert {
  border-radius: 8px;
}

.procurement-view-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 0;
  border: 0;
  box-shadow: none;
  background: transparent;
}

.procurement-view-switch button {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid #dbe4ef;
  border-radius: 8px;
  background: #fff;
  text-align: left;
  font: inherit;
  cursor: pointer;
}

.procurement-view-switch button.active {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.procurement-view-switch strong {
  color: #0f172a;
  font-size: 13px;
}

.procurement-view-switch small {
  color: #64748b;
  font-size: 11px;
  line-height: 1.45;
}

.procurement-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 16px;
}

.procurement-list-shell,
.procurement-form-shell {
  display: grid;
  gap: 12px;
  padding: 14px;
}

.procurement-list-head,
.procurement-form-head,
.procurement-selected-banner {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
}

.procurement-list-head strong,
.procurement-form-head strong,
.procurement-selected-banner strong {
  color: #0f172a;
  font-size: 16px;
}

.procurement-list-head span,
.procurement-form-head span,
.procurement-selected-banner span,
.procurement-selected-banner small {
  color: #64748b;
  font-size: 12px;
}

.procurement-list-toolbar,
.procurement-list-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 10px;
}

.procurement-list-summary {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.procurement-list-summary article {
  display: grid;
  gap: 4px;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.procurement-list-summary article span {
  color: #64748b;
  font-size: 11px;
}

.procurement-list-summary article strong {
  color: #0f172a;
  font-size: 20px;
}

.procurement-card-list {
  display: grid;
  gap: 10px;
}

.procurement-supplier-card {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  text-align: left;
}

.procurement-supplier-card.active {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.procurement-supplier-card-head,
.procurement-supplier-card-meta,
.procurement-supplier-card-submeta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
}

.procurement-supplier-card-head strong {
  color: #0f172a;
  font-size: 14px;
}

.procurement-supplier-card-meta span,
.procurement-supplier-card-submeta span,
.procurement-supplier-card small {
  color: #64748b;
  font-size: 12px;
}

.procurement-status-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.procurement-status-chip.active {
  background: #ecfdf5;
  color: #15803d;
}

.procurement-status-chip.inactive {
  background: #f8fafc;
  color: #64748b;
}

.procurement-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.procurement-form-grid label,
.procurement-full,
.procurement-status-toggle {
  display: grid;
  gap: 8px;
}

.procurement-form-grid span,
.procurement-full span,
.procurement-status-toggle span {
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.procurement-account-card {
  display: grid;
  gap: 12px;
  padding: 14px;
}

.procurement-form-head.compact strong {
  font-size: 14px;
}

.procurement-form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.procurement-form-buttons {
  display: flex;
  gap: 10px;
}

.procurement-empty {
  display: grid;
  place-items: center;
  min-height: 180px;
  text-align: center;
  color: #64748b;
}

.procurement-empty strong {
  color: #0f172a;
}

@media (max-width: 1180px) {
  .procurement-stats,
  .procurement-auth-gate,
  .procurement-auth-preview,
  .procurement-layout,
  .procurement-form-grid,
  .procurement-list-summary {
    grid-template-columns: 1fr;
  }
}
</style>
