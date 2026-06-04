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
      <article><span>已停用</span><strong>{{ inactiveCount }}</strong></article>
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
              <el-option v-for="item in suppliers" :key="item.id" :label="item.supplier_name" :value="item.id" />
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
              placeholder="至少选择一家供应商"
            >
              <el-option v-for="item in suppliers" :key="`procurement-supplier-${item.id}`" :label="item.supplier_name" :value="item.id" />
            </el-select>
          </label>
          <label>
            <span>默认行情地区</span>
            <el-input v-model="accountForm.market_scope" placeholder="例如：南京、南京市场、河南本地市场、全国" />
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
          <strong>权限边界</strong>
          <p>管理员账号可进入采购端和账号中心；供应商账号只能进入绑定供应商的数据范围。</p>
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
  fetchSuppliers,
  updateAuthUser,
} from '../lazyApi'
import type { AuthUserItem, AuthUserRole, SupplierItem } from '../types'

const props = defineProps<{
  currentUserId?: number | null
}>()

const ACCOUNT_USERNAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.@-]{2,63}$/
const MIN_ACCOUNT_PASSWORD_LENGTH = 8

const users = ref<AuthUserItem[]>([])
const suppliers = ref<SupplierItem[]>([])
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
const inactiveCount = computed(() => users.value.filter((item) => item.is_active === false).length)

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
    return marketScope || '未绑定供应商'
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
  if (accountForm.role === 'procurement' && accountForm.procurement_supplier_ids.length === 0) {
    ElMessage.warning('采购账号至少绑定一家供应商')
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
.account-admin-stats {
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

.account-admin-layout {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  overflow: hidden;
}

.account-admin-list {
  display: grid;
  align-content: start;
  gap: 10px;
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
  .account-admin-layout,
  .account-form-grid {
    grid-template-columns: 1fr;
  }

  .account-admin-list {
    border-right: 0;
    border-bottom: 1px solid #e2e8f0;
  }
}
</style>
