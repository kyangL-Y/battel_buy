<template>
  <section class="panel registration-admin-panel" data-testid="supplier-registration-admin-panel">
    <div class="registration-admin-head">
      <div>
        <p class="panel-kicker">注册审核</p>
        <h2>供应商注册申请</h2>
        <p>管理员在这里审核新申请，并一键转成正式供应商。</p>
      </div>
      <div class="registration-admin-actions">
        <el-button plain :loading="loading" @click="loadRequests">刷新</el-button>
      </div>
    </div>

    <div class="registration-admin-toolbar">
      <el-input v-model="keyword" clearable placeholder="搜索公司、联系人、手机号、登录账号" />
      <el-select v-model="statusFilter" placeholder="审核状态">
        <el-option label="全部状态" value="all" />
        <el-option label="待审核" value="pending" />
        <el-option label="已通过" value="approved" />
        <el-option label="已驳回" value="rejected" />
      </el-select>
    </div>

    <div class="registration-admin-stats">
      <article><span>待审核</span><strong>{{ pendingCount }}</strong></article>
      <article><span>已通过</span><strong>{{ approvedCount }}</strong></article>
      <article><span>已驳回</span><strong>{{ rejectedCount }}</strong></article>
    </div>

    <div class="registration-admin-layout">
      <section class="registration-admin-list">
        <button
          v-for="item in requests"
          :key="item.id"
          type="button"
          class="registration-request-card"
          :class="{ active: selectedRequestId === item.id }"
          @click="selectRequest(item.id)"
        >
          <div class="registration-request-head">
            <strong>{{ item.company_name }}</strong>
            <span :class="['registration-status-chip', item.status]">{{ statusLabel(item.status) }}</span>
          </div>
          <div class="registration-request-meta">
            <span>{{ item.contact_name || '未填联系人' }}</span>
            <span>{{ item.contact_phone || '未填手机号' }}</span>
            <span>{{ item.username }}</span>
          </div>
          <small>{{ formatTime(item.created_at) }}</small>
        </button>
        <div v-if="!requests.length" class="registration-empty">
          <strong>暂无注册申请</strong>
          <p>新的供应商注册申请会出现在这里。</p>
        </div>
      </section>

      <section class="registration-admin-detail">
        <template v-if="selectedRequest">
          <div class="registration-detail-head">
            <div>
              <strong>{{ selectedRequest.company_name }}</strong>
              <small>{{ statusLabel(selectedRequest.status) }} · {{ selectedRequest.username }}</small>
            </div>
            <span v-if="selectedRequest.reviewed_by">{{ selectedRequest.reviewed_by }}</span>
          </div>

          <div class="registration-detail-grid">
            <label>
              <span>供应商名称</span>
              <el-input v-model="reviewForm.supplier_name" placeholder="默认沿用申请公司名" />
            </label>
            <label>
              <span>联系人</span>
              <el-input v-model="reviewForm.contact_name" />
            </label>
            <label>
              <span>手机号</span>
              <el-input v-model="reviewForm.contact_phone" />
            </label>
            <label>
              <span>登录账号</span>
              <el-input :model-value="selectedRequest.username" disabled />
            </label>
            <label>
              <span>分类</span>
              <el-input v-model="reviewForm.market_category" placeholder="例如：干调类" />
            </label>
            <label>
              <span>渠道</span>
              <el-input v-model="reviewForm.channel" placeholder="例如：微信小程序" />
            </label>
            <label>
              <span>市场范围</span>
              <el-input v-model="reviewForm.market_scope" placeholder="例如：本地市场" />
            </label>
            <label>
              <span>显示名称</span>
              <el-input v-model="reviewForm.account_display_name" placeholder="默认沿用联系人或供应商名称" />
            </label>
            <label>
              <span>初始密码</span>
              <el-input v-model="reviewForm.account_password" type="password" show-password placeholder="留空默认 12345678" />
            </label>
          </div>

          <label class="registration-detail-notes">
            <span>审核备注</span>
            <el-input v-model="reviewForm.review_notes" type="textarea" :rows="3" placeholder="记录审核结果、补充说明或驳回原因" />
          </label>

          <div class="registration-detail-actions">
            <el-button
              type="primary"
              :disabled="selectedRequest.status !== 'pending'"
              :loading="reviewing === 'approve'"
              @click="approveSelectedRequest"
            >
              通过并创建供应商
            </el-button>
            <el-button
              plain
              :disabled="selectedRequest.status !== 'pending'"
              :loading="reviewing === 'reject'"
              @click="rejectSelectedRequest"
            >
              驳回申请
            </el-button>
          </div>
        </template>

        <div v-else class="registration-empty detail">
          <strong>选择一条申请</strong>
          <p>右侧会显示申请详情和审核动作。</p>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'

import {
  approveSupplierRegistrationRequest,
  extractApiErrorDetail,
  fetchSupplierRegistrationRequests,
  getApiErrorStatus,
  rejectSupplierRegistrationRequest,
} from '../api'
import type { SupplierRegistrationRequestItem, SupplierRegistrationRequestStatus } from '../types'

const requests = ref<SupplierRegistrationRequestItem[]>([])
const loading = ref(false)
const reviewing = ref<'approve' | 'reject' | null>(null)
const selectedRequestId = ref<number | null>(null)
const statusFilter = ref<'all' | SupplierRegistrationRequestStatus>('pending')
const keyword = ref('')

const reviewForm = reactive({
  supplier_name: '',
  contact_name: '',
  contact_phone: '',
  market_scope: '本地市场',
  market_category: '',
  channel: '微信小程序',
  account_display_name: '',
  account_password: '',
  review_notes: '',
})

const selectedRequest = computed(() => requests.value.find((item) => item.id === selectedRequestId.value) || null)
const pendingCount = computed(() => requests.value.filter((item) => item.status === 'pending').length)
const approvedCount = computed(() => requests.value.filter((item) => item.status === 'approved').length)
const rejectedCount = computed(() => requests.value.filter((item) => item.status === 'rejected').length)

function statusLabel(status: SupplierRegistrationRequestStatus) {
  if (status === 'approved') return '已通过'
  if (status === 'rejected') return '已驳回'
  return '待审核'
}

function formatTime(value?: string | null) {
  return value ? String(value).replace('T', ' ').slice(0, 16) : '刚提交'
}

function fillReviewForm(item: SupplierRegistrationRequestItem | null) {
  reviewForm.supplier_name = item?.supplier_name || item?.company_name || ''
  reviewForm.contact_name = item?.contact_name || ''
  reviewForm.contact_phone = item?.contact_phone || ''
  reviewForm.market_scope = '本地市场'
  reviewForm.market_category = item?.market_category || ''
  reviewForm.channel = item?.channel || '微信小程序'
  reviewForm.account_display_name = item?.contact_name || item?.company_name || ''
  reviewForm.account_password = ''
  reviewForm.review_notes = item?.review_notes || ''
}

function selectRequest(requestId: number) {
  selectedRequestId.value = requestId
}

async function loadRequests() {
  loading.value = true
  try {
    const data = await fetchSupplierRegistrationRequests({
      status: statusFilter.value === 'all' ? undefined : statusFilter.value,
      keyword: keyword.value.trim() || undefined,
    })
    requests.value = data.items || []
    if (!requests.value.some((item) => item.id === selectedRequestId.value)) {
      selectedRequestId.value = requests.value[0]?.id ?? null
    }
  } catch (error) {
    const status = getApiErrorStatus(error)
    if (status === 401) {
      ElMessage.error('登录状态已失效，请重新登录采购管理员账号')
      return
    }
    if (status === 403) {
      ElMessage.error('当前账号没有权限查看注册审核列表')
      return
    }
    ElMessage.error(extractApiErrorDetail(error) || '注册申请列表读取失败')
  } finally {
    loading.value = false
  }
}

async function approveSelectedRequest() {
  if (!selectedRequest.value) return
  reviewing.value = 'approve'
  try {
    await approveSupplierRegistrationRequest(selectedRequest.value.id, {
      supplier_name: reviewForm.supplier_name.trim() || undefined,
      contact_name: reviewForm.contact_name.trim() || undefined,
      contact_phone: reviewForm.contact_phone.trim() || undefined,
      market_scope: reviewForm.market_scope.trim() || undefined,
      market_category: reviewForm.market_category.trim() || undefined,
      channel: reviewForm.channel.trim() || undefined,
      account_display_name: reviewForm.account_display_name.trim() || undefined,
      account_password: reviewForm.account_password.trim() || undefined,
      review_notes: reviewForm.review_notes.trim() || undefined,
    })
    ElMessage.success('注册申请已通过并转为正式供应商')
    await loadRequests()
  } catch {
    ElMessage.error('注册申请通过失败')
  } finally {
    reviewing.value = null
  }
}

async function rejectSelectedRequest() {
  if (!selectedRequest.value) return
  reviewing.value = 'reject'
  try {
    await rejectSupplierRegistrationRequest(selectedRequest.value.id, {
      review_notes: reviewForm.review_notes.trim() || '管理员驳回',
    })
    ElMessage.success('注册申请已驳回')
    await loadRequests()
  } catch {
    ElMessage.error('注册申请驳回失败')
  } finally {
    reviewing.value = null
  }
}

watch(selectedRequest, (item) => {
  fillReviewForm(item)
}, { immediate: true })

watch([statusFilter, keyword], async () => {
  await loadRequests()
})

onMounted(async () => {
  await loadRequests()
})
</script>

<style scoped>
.registration-admin-panel {
  display: grid;
  gap: 14px;
}

.registration-admin-head,
.registration-admin-toolbar,
.registration-admin-stats,
.registration-admin-layout,
.registration-request-card,
.registration-admin-detail {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.registration-admin-head,
.registration-admin-toolbar,
.registration-admin-stats {
  padding: 16px 18px;
}

.registration-admin-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
}

.registration-admin-head h2 {
  margin: 4px 0 6px;
  font-size: 22px;
  color: #020817;
}

.registration-admin-head p:last-child {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.55;
}

.registration-admin-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  gap: 12px;
}

.registration-admin-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.registration-admin-stats article {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.registration-admin-stats span {
  color: #64748b;
  font-size: 12px;
}

.registration-admin-stats strong {
  color: #020817;
  font-size: 24px;
}

.registration-admin-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 0;
  overflow: hidden;
}

.registration-admin-list {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-right: 1px solid #e2e8f0;
  background: #f8fafc;
}

.registration-request-card {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  text-align: left;
}

.registration-request-card.active {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.registration-request-head,
.registration-request-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
}

.registration-request-head strong {
  color: #020817;
  font-size: 14px;
}

.registration-request-meta span,
.registration-request-card small {
  color: #64748b;
  font-size: 12px;
}

.registration-status-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.registration-status-chip.pending {
  background: #fff7ed;
  color: #c2410c;
}

.registration-status-chip.approved {
  background: #ecfdf5;
  color: #15803d;
}

.registration-status-chip.rejected {
  background: #fef2f2;
  color: #dc2626;
}

.registration-admin-detail {
  display: grid;
  gap: 14px;
  padding: 18px;
}

.registration-detail-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
}

.registration-detail-head strong {
  color: #020817;
  font-size: 18px;
}

.registration-detail-head small,
.registration-detail-head span {
  color: #64748b;
  font-size: 12px;
}

.registration-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.registration-detail-grid label,
.registration-detail-notes {
  display: grid;
  gap: 8px;
}

.registration-detail-grid span,
.registration-detail-notes span {
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.registration-detail-actions {
  display: flex;
  gap: 10px;
}

.registration-empty {
  display: grid;
  place-items: center;
  min-height: 220px;
  text-align: center;
  color: #64748b;
}

.registration-empty strong {
  color: #0f172a;
}

@media (max-width: 980px) {
  .registration-admin-toolbar,
  .registration-admin-stats,
  .registration-admin-layout,
  .registration-detail-grid {
    grid-template-columns: 1fr;
  }

  .registration-admin-list {
    border-right: 0;
    border-bottom: 1px solid #e2e8f0;
  }
}
</style>
