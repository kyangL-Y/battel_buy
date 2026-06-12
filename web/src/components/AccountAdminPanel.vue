<template>
  <section class="panel account-admin-panel" data-testid="account-admin-panel">
    <div class="account-admin-head">
      <div>
        <p class="panel-kicker">账号管理</p>
        <h2>系统账号中心</h2>
        <p>集中维护管理员账号、供应商账号、绑定范围、启停状态和密码重置。</p>
      </div>
      <div class="account-admin-actions">
        <el-button plain :loading="loading" @click="loadAll">刷新</el-button>
        <el-button type="primary" @click="resetForm">新建账号</el-button>
      </div>
    </div>

    <div class="account-admin-toolbar">
      <el-input v-model="keyword" clearable placeholder="搜索账号、显示名、供应商、联系人" />
        <el-select v-model="roleFilter" placeholder="角色">
          <el-option label="全部角色" value="all" />
          <el-option label="管理员" value="admin" />
          <el-option label="采购账号" value="procurement" />
          <el-option label="供应商" value="supplier" />
        </el-select>
      <el-select v-model="statusFilter" placeholder="状态">
        <el-option label="全部状态" value="all" />
        <el-option label="启用中" value="active" />
        <el-option label="已停用" value="inactive" />
      </el-select>
    </div>

    <div class="account-admin-stats">
      <article><span>账号总数</span><strong>{{ users.length }}</strong></article>
      <article><span>管理员</span><strong>{{ adminCount }}</strong></article>
      <article><span>供应商账号</span><strong>{{ supplierCount }}</strong></article>
      <article><span>采购账号</span><strong>{{ procurementCount }}</strong></article>
      <article><span>已停用</span><strong>{{ inactiveCount }}</strong></article>
      <article><span>采购未分配</span><strong>{{ unassignedProcurementCount }}</strong></article>
    </div>

    <div v-if="procurementAssignmentUsers.length" class="account-procurement-assignment">
      <div>
        <span>采购分配待办</span>
        <strong>{{ procurementAssignmentTitle }}</strong>
        <p>{{ procurementAssignmentDescription }}</p>
      </div>
      <div class="account-procurement-assignment-list">
        <button
          v-for="procurementUser in procurementAssignmentUsers"
          :key="procurementUser.id"
          type="button"
          @click="selectUser(procurementUser)"
        >
          {{ procurementUser.display_name || procurementUser.username }}
        </button>
      </div>
    </div>

    <div class="account-admin-layout">
      <section class="account-admin-list">
        <button
          v-for="item in users"
          :key="item.id"
          type="button"
          class="account-card"
          :class="{ active: selectedUserId === item.id }"
          @click="selectUser(item)"
        >
          <div class="account-card-head">
            <strong>{{ item.display_name || item.username }}</strong>
            <span :class="['account-status-chip', item.is_active === false ? 'inactive' : 'active']">
              {{ item.is_active === false ? '停用' : '启用' }}
            </span>
          </div>
          <div class="account-card-meta">
            <span>{{ item.username }}</span>
            <span>{{ roleLabel(item.role) }}</span>
            <span v-if="item.id === currentUserId">当前登录</span>
          </div>
          <small>{{ accountScopeLabel(item) }} · {{ formatTime(item.last_login_at || item.updated_at) }}</small>
          <div class="account-card-actions" @click.stop>
            <el-button size="small" plain :disabled="item.id === currentUserId" :loading="actionUserId === item.id" @click="toggleAccountActive(item)">
              {{ item.is_active === false ? '启用' : '停用' }}
            </el-button>
            <el-button size="small" type="danger" plain :disabled="item.id === currentUserId" :loading="actionUserId === item.id" @click="deleteAccount(item)">
              归档删除
            </el-button>
          </div>
        </button>
        <div v-if="!users.length" class="account-empty">
          <strong>没有匹配账号</strong>
          <p>调整筛选条件或新建一个账号。</p>
        </div>
      </section>

      <section class="account-admin-detail">
        <div class="account-detail-head">
          <div>
            <strong>{{ selectedUserId ? '编辑账号' : '新建账号' }}</strong>
            <small>{{ selectedUserId ? `ID ${selectedUserId}` : '创建管理员或供应商账号' }}</small>
          </div>
          <span v-if="selectedUserId === currentUserId" class="account-self-badge">当前登录账号</span>
        </div>

        <div class="account-form-grid">
          <label>
            <span>登录账号</span>
            <el-input v-model="accountForm.username" placeholder="例如：admin-ops / lencai-a" />
          </label>
          <label>
            <span>显示名称</span>
            <el-input v-model="accountForm.display_name" placeholder="例如：运营管理员 / 莲菜档口A" />
          </label>
          <label>
            <span>角色</span>
            <el-select v-model="accountForm.role" placeholder="选择角色" @change="handleRoleChange">
              <el-option label="管理员" value="admin" />
              <el-option label="采购账号" value="procurement" />
              <el-option label="供应商" value="supplier" />
            </el-select>
          </label>
          <label v-if="accountForm.role === 'supplier'">
            <span>绑定供应商</span>
            <el-select
              v-model="accountForm.supplier_id"
              clearable
              filterable
              placeholder="供应商账号必须绑定"
            >
              <el-option v-for="item in activeSupplierOptions" :key="item.id" :label="item.supplier_name" :value="item.id" />
            </el-select>
          </label>
          <label v-if="accountForm.role === 'procurement'">
            <span>租户供应商</span>
            <el-select
              v-model="accountForm.procurement_supplier_ids"
              multiple
              clearable
              filterable
              collapse-tags
              collapse-tags-tooltip
              placeholder="可先不选，后续再分配"
            >
              <el-option
                v-for="item in activeSupplierOptions"
                :key="`procurement-supplier-${item.id}`"
                :label="item.supplier_name"
                :value="item.id"
              />
            </el-select>
          </label>
          <label>
            <span>默认行情地区</span>
            <el-select
              v-model="accountForm.market_scope"
              clearable
              filterable
              :loading="locationLoading"
              placeholder="选择全国、省份或城市"
            >
              <el-option
                v-for="item in marketScopeOptions"
                :key="`${item.section}-${item.value}`"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </label>
          <label>
            <span>{{ selectedUserId ? '重置密码' : '初始密码' }}</span>
            <el-input v-model="accountForm.password" type="password" show-password :placeholder="selectedUserId ? '留空则保持原密码' : '新建账号必须填写，至少 8 位'" />
          </label>
          <label class="account-switch-field">
            <span>账号状态</span>
            <el-switch v-model="accountForm.is_active" inline-prompt active-text="启" inactive-text="停" />
          </label>
        </div>

        <div class="account-detail-note">
          <strong>{{ accountDetailNoteTitle }}</strong>
          <p>{{ accountDetailNoteDescription }}</p>
        </div>

        <div class="account-detail-actions">
          <el-button plain @click="resetForm">清空新建</el-button>
          <el-button
            v-if="selectedUser"
            plain
            :disabled="selectedUser.id === currentUserId"
            :loading="actionUserId === selectedUser.id"
            @click="toggleAccountActive(selectedUser)"
          >
            {{ selectedUser.is_active === false ? '启用账号' : '停用账号' }}
          </el-button>
          <el-button
            v-if="selectedUser"
            type="danger"
            plain
            :disabled="selectedUser.id === currentUserId"
            :loading="actionUserId === selectedUser.id"
            @click="deleteAccount(selectedUser)"
          >
            归档删除
          </el-button>
          <el-button type="primary" :loading="saving" @click="saveAccount">
            {{ selectedUserId ? '保存账号' : '创建账号' }}
          </el-button>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessageBox } from 'element-plus/es/components/message-box/index.mjs'
import { lazyElMessage as ElMessage } from '../lazyElementMessage'

import {
  createAuthUser,
  deleteAuthUser,
  extractApiErrorDetail,
  fetchAuthUsers,
  fetchLocationOptions,
  fetchSuppliers,
  updateAuthUser,
} from '../lazyApi'
import type { AuthUserItem, AuthUserRole, SupplierItem } from '../types'

const props = defineProps<{
  currentUserId?: number | null
}>()

const ACCOUNT_USERNAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.@-]{2,63}$/
const MIN_ACCOUNT_PASSWORD_LENGTH = 8

type MarketScopeOption = {
  value: string
  label: string
  section: 'all' | 'province' | 'city' | 'custom'
}

const users = ref<AuthUserItem[]>([])
const suppliers = ref<SupplierItem[]>([])
const locationLoading = ref(false)
const locationProvinces = ref<string[]>([])
const provinceCityMap = ref<Record<string, string[]>>({})
const loading = ref(false)
const saving = ref(false)
const actionUserId = ref<number | null>(null)
const selectedUserId = ref<number | null>(null)
const keyword = ref('')
const roleFilter = ref<'all' | AuthUserRole>('all')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')

const accountForm = reactive({
  username: '',
  password: '',
  role: 'supplier' as AuthUserRole,
  supplier_id: null as number | null,
  procurement_supplier_ids: [] as number[],
  display_name: '',
  market_scope: '',
  is_active: true,
})

const currentUserId = computed(() => props.currentUserId ?? null)
const selectedUser = computed(() => users.value.find((item) => item.id === selectedUserId.value) || null)
const adminCount = computed(() => users.value.filter((item) => item.role === 'admin').length)
const supplierCount = computed(() => users.value.filter((item) => item.role === 'supplier').length)
const procurementCount = computed(() => users.value.filter((item) => item.role === 'procurement').length)
const inactiveCount = computed(() => users.value.filter((item) => item.is_active === false).length)
const unassignedProcurementCount = computed(() =>
  users.value.filter((item) => item.role === 'procurement' && !(item.procurement_supplier_ids || []).length).length,
)
const unassignedProcurementUsers = computed(() =>
  users.value.filter((item) => item.role === 'procurement' && item.is_active !== false && !(item.procurement_supplier_ids || []).length),
)
const procurementUsers = computed(() =>
  users.value.filter((item) => item.role === 'procurement' && item.is_active !== false),
)
const procurementAssignmentUsers = computed(() =>
  (unassignedProcurementUsers.value.length ? unassignedProcurementUsers.value : procurementUsers.value).slice(0, 4),
)
const procurementAssignmentTitle = computed(() => {
  if (unassignedProcurementUsers.value.length) return `${unassignedProcurementUsers.value.length} 个采购账号还没有供应商范围`
  return '采购账号已分配供应商范围'
})
const procurementAssignmentDescription = computed(() => {
  if (unassignedProcurementUsers.value.length) {
    return '先点账号，再在右侧“租户供应商”里勾选该采购账号能看的供应商。'
  }
  return '点击采购账号可复核或调整“租户供应商”，供应商相关页面只会显示分配给该采购账号的供应商。'
})
const accountDetailNoteTitle = computed(() => {
  if (accountForm.role === 'procurement') return '采购账号分配'
  if (accountForm.role === 'supplier') return '供应商账号边界'
  return '管理员权限边界'
})
const accountDetailNoteDescription = computed(() => {
  if (accountForm.role === 'procurement') {
    return '采购账号可以先设置默认行情地区；必须在“租户供应商”里分配供应商后，供应商管理、报价记录和采购相关模块才会显示对应供应商数据。'
  }
  if (accountForm.role === 'supplier') {
    return '供应商账号必须绑定一个启用供应商；登录后只能查看和维护该供应商自己的报价、结算和操作记录。'
  }
  return '管理员账号可进入采购端和账号中心，维护账号、供应商范围、启停状态和密码重置。'
})
const marketScopeOptions = computed(() => {
  const scopeOptions: MarketScopeOption[] = []
  const usedValues = new Set<string>()

  const appendScopeOption = (option: MarketScopeOption) => {
    const scopeValue = option.value.trim()
    if (!scopeValue || usedValues.has(scopeValue)) return
    usedValues.add(scopeValue)
    scopeOptions.push({ ...option, value: scopeValue })
  }

  appendScopeOption({ value: '全国', label: '全国', section: 'all' })

  for (const provinceName of locationProvinces.value) {
    appendScopeOption({ value: provinceName, label: provinceName, section: 'province' })
    for (const cityName of provinceCityMap.value[provinceName] || []) {
      const cityLabel = cityName === provinceName ? cityName : `${provinceName} / ${cityName}`
      appendScopeOption({ value: cityName, label: cityLabel, section: 'city' })
    }
  }

  const currentScope = accountForm.market_scope.trim()
  if (currentScope && !usedValues.has(currentScope)) {
    appendScopeOption({ value: currentScope, label: `${currentScope}（历史值）`, section: 'custom' })
  }

  return scopeOptions
})
const activeSupplierOptions = computed(() =>
  suppliers.value.filter((item) => item.is_active !== false),
)

function roleLabel(role: AuthUserRole) {
  if (role === 'admin') return '管理员'
  if (role === 'procurement') return '采购账号'
  return '供应商'
}

function accountScopeLabel(item: AuthUserItem) {
  const marketScope = String(item.market_scope || '').trim()
  if (item.role === 'admin') return marketScope || '全局权限'
  if (item.role === 'procurement') {
    const supplierCount = (item.procurement_supplier_ids || []).length
    if (marketScope && supplierCount > 0) return `${marketScope} · ${supplierCount} 家供应商`
    if (supplierCount > 0) return `${supplierCount} 家供应商`
    return marketScope ? `${marketScope} · 未绑定供应商` : '未绑定供应商'
  }
  if (marketScope && item.supplier_profile?.supplier_name) {
    return `${item.supplier_profile.supplier_name} · ${marketScope}`
  }
  return marketScope || item.supplier_profile?.supplier_name || '未绑定供应商'
}

function formatTime(value?: string | null) {
  if (!value) return '暂无登录'
  return String(value).replace('T', ' ').slice(0, 16)
}

function normalizeLocationNames(names?: string[]) {
  return Array.from(new Set((names || []).map((name) => String(name || '').trim()).filter(Boolean)))
}

function normalizeProvinceCityOptions(options: Record<string, string[]> = {}) {
  const provinceOptions: Record<string, string[]> = {}
  for (const [provinceName, cityNames] of Object.entries(options)) {
    const normalizedProvince = String(provinceName || '').trim()
    if (!normalizedProvince) continue
    provinceOptions[normalizedProvince] = normalizeLocationNames(cityNames)
  }
  return provinceOptions
}

function handleRoleChange() {
  if (accountForm.role === 'admin') {
    accountForm.supplier_id = null
    accountForm.procurement_supplier_ids = []
    return
  }
  if (accountForm.role === 'procurement') {
    accountForm.supplier_id = null
    return
  }
  accountForm.procurement_supplier_ids = []
}

function fillForm(item: AuthUserItem | null) {
  selectedUserId.value = item?.id ?? null
  accountForm.username = item?.username || ''
  accountForm.password = ''
  accountForm.role = item?.role || 'supplier'
  accountForm.supplier_id = item?.role === 'supplier' ? item.supplier_id ?? null : null
  accountForm.procurement_supplier_ids = item?.role === 'procurement' ? [...(item.procurement_supplier_ids || [])] : []
  accountForm.display_name = item?.display_name || ''
  accountForm.market_scope = item?.market_scope || ''
  accountForm.is_active = item?.is_active == null ? true : Boolean(item.is_active)
}

function resetForm() {
  fillForm(null)
}

function selectUser(item: AuthUserItem) {
  fillForm(item)
}

function validateBeforeSave() {
  const username = accountForm.username.trim()
  const password = accountForm.password.trim()
  if (!ACCOUNT_USERNAME_PATTERN.test(username)) {
    ElMessage.warning('登录账号需为 3-64 位，只能包含字母、数字、下划线、中划线、点或 @')
    return false
  }
  if (accountForm.role === 'supplier' && !accountForm.supplier_id) {
    ElMessage.warning('供应商账号必须绑定供应商')
    return false
  }
  if (accountForm.role === 'supplier' && !activeSupplierOptions.value.some((item) => item.id === accountForm.supplier_id)) {
    ElMessage.warning('只能绑定启用中的供应商')
    return false
  }
  if (
    accountForm.role === 'procurement'
    && accountForm.procurement_supplier_ids.some((supplierId) => !activeSupplierOptions.value.some((item) => item.id === supplierId))
  ) {
    ElMessage.warning('采购账号只能分配启用中的供应商')
    return false
  }
  if (!selectedUserId.value && !password) {
    ElMessage.warning('新建账号必须填写初始密码')
    return false
  }
  if (password && password.length < MIN_ACCOUNT_PASSWORD_LENGTH) {
    ElMessage.warning(`账号密码至少 ${MIN_ACCOUNT_PASSWORD_LENGTH} 位`)
    return false
  }
  if (selectedUserId.value === currentUserId.value && accountForm.role !== 'admin') {
    ElMessage.warning('不能把当前登录管理员降级为供应商')
    return false
  }
  if (selectedUserId.value === currentUserId.value && !accountForm.is_active) {
    ElMessage.warning('不能停用当前登录账号')
    return false
  }
  return true
}

async function loadAll() {
  loading.value = true
  try {
    const [userData, supplierData] = await Promise.all([
      fetchAuthUsers({
        role: roleFilter.value === 'all' ? undefined : roleFilter.value,
        status: statusFilter.value === 'all' ? undefined : statusFilter.value,
        keyword: keyword.value.trim() || undefined,
      }),
      fetchSuppliers(false),
      loadLocationOptions(),
    ])
    users.value = userData.items || []
    suppliers.value = supplierData.items || []
    if (selectedUserId.value && !users.value.some((item) => item.id === selectedUserId.value)) {
      resetForm()
    }
    if (!selectedUserId.value && users.value.length) {
      fillForm(users.value[0])
    } else if (selectedUser.value) {
      fillForm(selectedUser.value)
    }
  } catch (error) {
    ElMessage.error(extractApiErrorDetail(error) || '账号列表读取失败')
  } finally {
    loading.value = false
  }
}

async function loadLocationOptions() {
  if (locationLoading.value || locationProvinces.value.length) return
  locationLoading.value = true
  try {
    const locationResponse = await fetchLocationOptions()
    locationProvinces.value = normalizeLocationNames(locationResponse.provinces)
    provinceCityMap.value = normalizeProvinceCityOptions(locationResponse.province_city_map)
  } catch {
    locationProvinces.value = []
    provinceCityMap.value = {}
  } finally {
    locationLoading.value = false
  }
}

async function saveAccount() {
  if (!validateBeforeSave()) return
  saving.value = true
  try {
      const payload = {
        username: accountForm.username.trim(),
        role: accountForm.role,
        supplier_id: accountForm.role === 'supplier' ? accountForm.supplier_id : null,
        procurement_supplier_ids: accountForm.role === 'procurement' ? accountForm.procurement_supplier_ids : [],
        display_name: accountForm.display_name.trim() || undefined,
        market_scope: accountForm.market_scope.trim() || undefined,
        is_active: accountForm.is_active,
      }
    if (selectedUserId.value) {
      await updateAuthUser(selectedUserId.value, {
        ...payload,
        password: accountForm.password.trim() || undefined,
      })
      ElMessage.success('账号已更新')
    } else {
      const created = await createAuthUser({
        ...payload,
        password: accountForm.password.trim(),
      })
      selectedUserId.value = created.id
      ElMessage.success('账号已创建')
    }
    await loadAll()
  } catch (error) {
    ElMessage.error(extractApiErrorDetail(error) || '账号保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleAccountActive(item: AuthUserItem) {
  if (item.id === currentUserId.value) {
    ElMessage.warning('不能停用当前登录账号')
    return
  }
  actionUserId.value = item.id
  try {
      await updateAuthUser(item.id, {
        username: item.username,
        role: item.role,
        supplier_id: item.role === 'supplier' ? item.supplier_id ?? null : null,
        procurement_supplier_ids: item.role === 'procurement' ? (item.procurement_supplier_ids || []) : [],
        display_name: item.display_name || undefined,
        market_scope: item.market_scope || undefined,
        is_active: item.is_active === false,
      })
    ElMessage.success(item.is_active === false ? '账号已启用' : '账号已停用')
    await loadAll()
  } catch (error) {
    ElMessage.error(extractApiErrorDetail(error) || '账号状态更新失败')
  } finally {
    actionUserId.value = null
  }
}

async function deleteAccount(item: AuthUserItem) {
  if (item.id === currentUserId.value) {
    ElMessage.warning('不能删除当前登录账号')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认归档删除账号「${item.display_name || item.username}」？删除后该账号无法登录，历史记录会保留用于审计。`,
      '归档删除账号',
      {
        confirmButtonText: '确认归档',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  } catch {
    return
  }
  actionUserId.value = item.id
  try {
    await deleteAuthUser(item.id)
    ElMessage.success('账号已归档删除')
    if (selectedUserId.value === item.id) {
      resetForm()
    }
    await loadAll()
  } catch (error) {
    ElMessage.error(extractApiErrorDetail(error) || '账号删除失败')
  } finally {
    actionUserId.value = null
  }
}

watch([roleFilter, statusFilter], async () => {
  await loadAll()
})

watch(keyword, async () => {
  await loadAll()
})

onMounted(async () => {
  await loadAll()
})
</script>

<style scoped>
.account-admin-panel {
  display: grid;
  gap: 14px;
}

.account-admin-head,
.account-admin-toolbar,
.account-admin-stats,
.account-procurement-assignment,
.account-admin-layout,
.account-card,
.account-admin-detail,
.account-detail-note {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.account-admin-head,
.account-admin-toolbar,
.account-admin-stats,
.account-procurement-assignment {
  padding: 16px 18px;
}

.account-admin-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
}

.account-admin-head h2 {
  margin: 4px 0 6px;
  color: #020817;
  font-size: 22px;
}

.account-admin-head p:last-child {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.55;
}

.account-admin-actions,
.account-detail-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.account-admin-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 150px 150px;
  gap: 12px;
}

.account-admin-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.account-admin-stats article {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.account-admin-stats span,
.account-card-meta,
.account-card small,
.account-detail-head small,
.account-detail-note p {
  color: #64748b;
  font-size: 12px;
}

.account-admin-stats strong {
  color: #020817;
  font-size: 24px;
}

.account-procurement-assignment {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 0.54fr);
  align-items: center;
  gap: 14px;
  border-color: #bfdbfe;
  background: linear-gradient(135deg, #f8fbff, #eff6ff);
}

.account-procurement-assignment span,
.account-procurement-assignment p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.account-procurement-assignment strong {
  display: block;
  margin: 4px 0;
  color: #0f172a;
  font-size: 16px;
}

.account-procurement-assignment-list {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.account-procurement-assignment-list button {
  min-height: 32px;
  padding: 0 12px;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: #fff;
  color: #1d4ed8;
  font-weight: 700;
  cursor: pointer;
}

.account-admin-layout {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  overflow: hidden;
}

.account-admin-list {
  display: grid;
  align-content: start;
  gap: 10px;
  max-height: min(720px, calc(100vh - 300px));
  min-height: 320px;
  overflow: auto;
  padding: 14px;
  border-right: 1px solid #e2e8f0;
  background: #f8fafc;
}

.account-card {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  text-align: left;
}

.account-card.active {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.account-card-head,
.account-card-meta,
.account-card-actions,
.account-detail-head {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
}

.account-card-actions {
  justify-content: flex-start;
}

.account-card-head strong,
.account-detail-head strong,
.account-detail-note strong {
  color: #020817;
}

.account-status-chip,
.account-self-badge {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.account-status-chip.active {
  background: #ecfdf5;
  color: #15803d;
}

.account-status-chip.inactive {
  background: #fef2f2;
  color: #dc2626;
}

.account-self-badge {
  background: #eff6ff;
  color: #1d4ed8;
}

.account-admin-detail {
  display: grid;
  align-content: start;
  gap: 14px;
  position: sticky;
  top: 14px;
  max-height: min(720px, calc(100vh - 300px));
  min-height: 320px;
  overflow: auto;
  padding: 18px;
}

.account-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.account-form-grid label,
.account-switch-field,
.account-detail-note {
  display: grid;
  gap: 8px;
}

.account-form-grid label > span,
.account-detail-note strong {
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.account-detail-note {
  padding: 12px 14px;
  background: #f8fafc;
}

.account-detail-note p {
  margin: 0;
  line-height: 1.55;
}

.account-empty {
  display: grid;
  place-items: center;
  min-height: 220px;
  text-align: center;
  color: #64748b;
}

.account-empty strong {
  color: #0f172a;
}

@media (max-width: 980px) {
  .account-admin-head,
  .account-admin-actions,
  .account-detail-actions {
    justify-content: stretch;
  }

  .account-admin-toolbar,
  .account-admin-stats,
  .account-procurement-assignment,
  .account-admin-layout,
  .account-form-grid {
    grid-template-columns: 1fr;
  }

  .account-procurement-assignment-list {
    justify-content: flex-start;
  }

  .account-admin-list {
    max-height: none;
    min-height: 0;
    overflow: visible;
    border-right: 0;
    border-bottom: 1px solid #e2e8f0;
  }

  .account-admin-detail {
    position: static;
    max-height: none;
    min-height: 0;
    overflow: visible;
  }
}
</style>
