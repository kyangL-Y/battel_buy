<template>
  <section class="panel supplier-admin-panel content-shell-panel" :class="{ mobile }">
    <div class="panel-header content-panel-header">
      <div>
        <p class="panel-kicker">供应商后台</p>
        <h2>供应商与录价管理</h2>
        <p class="panel-hint">维护本地供应商资料，直接录入报价，前台按商品做公开价对比。</p>
      </div>
      <div class="inline-actions compact-actions">
        <el-button plain :loading="loading" @click="reloadAll">刷新后台</el-button>
      </div>
    </div>

    <div class="supplier-admin-metrics">
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
        <small>{{ recentQuoteRows[0]?.supplier_name || '后台最近一次录价时间' }}</small>
      </article>
      <article class="supplier-admin-metric">
        <span>累计报价</span>
        <strong>{{ totalQuoteCount }}</strong>
        <small>供应商后台已沉淀的报价记录</small>
      </article>
    </div>

    <div class="supplier-admin-toolbar">
      <el-input v-model="keyword" placeholder="搜索供应商、联系人、分类" clearable />
      <el-select v-model="categoryFilter" clearable filterable placeholder="按分类筛选">
        <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="状态">
        <el-option label="全部状态" value="all" />
        <el-option label="仅启用" value="active" />
        <el-option label="仅停用" value="inactive" />
      </el-select>
    </div>

    <div class="supplier-admin-layout">
      <section class="supplier-admin-column supplier-list-column">
        <div class="supplier-column-head">
          <strong>供应商列表</strong>
          <span>{{ filteredSuppliers.length }} 家</span>
        </div>
        <div class="supplier-card-list">
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
            <p>{{ item.contact_name || '联系人待补充' }}</p>
            <small>{{ formatTime(item.latest_quoted_at) }}</small>
          </button>
          <div v-if="!filteredSuppliers.length" class="supplier-card-empty">
            <strong>还没有供应商</strong>
            <p>先在右侧新建一个供应商，再开始录价。</p>
          </div>
        </div>
      </section>

      <section class="supplier-admin-column supplier-form-column">
        <div class="supplier-column-head">
          <strong>{{ selectedSupplier ? '编辑供应商' : '新增供应商' }}</strong>
          <span>{{ selectedSupplier ? `ID ${selectedSupplier.id}` : '新建' }}</span>
        </div>
        <div class="supplier-form-card">
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
          <div class="supplier-form-actions">
            <el-switch v-model="supplierForm.is_active" inline-prompt active-text="启" inactive-text="停" />
            <div class="supplier-form-action-buttons">
              <el-button plain @click="resetSupplierForm">新建空白</el-button>
              <el-button type="primary" :loading="supplierSaving" @click="saveSupplier">
                {{ selectedSupplier ? '保存修改' : '创建供应商' }}
              </el-button>
            </div>
          </div>
        </div>

        <div class="supplier-form-card">
          <div class="supplier-column-head compact">
            <strong>给当前商品录价</strong>
            <span>{{ selectedProductLabelResolved || '未选商品' }}</span>
          </div>
          <div v-if="productCompareSummary" class="supplier-compare-summary">
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
          <div class="supplier-form-grid">
            <label class="supplier-form-field supplier-form-field-full">
              <span>商品</span>
              <el-select :model-value="selectedProductKey" filterable placeholder="选择商品" @change="handleProductChange">
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
              <el-input-number v-model="quoteForm.quote_price" :min="0" :precision="2" :step="0.1" controls-position="right" />
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
          </div>
          <label class="supplier-form-field supplier-form-field-full">
            <span>报价备注</span>
            <el-input v-model="quoteForm.remarks" type="textarea" :rows="mobile ? 3 : 2" placeholder="例如：今天早市价，整箱可送" />
          </label>
          <div class="supplier-form-actions">
            <div class="supplier-inline-tip">
              <strong>{{ selectedSupplier?.supplier_name || '请先选择或创建供应商' }}</strong>
              <span>{{ selectedProductLabelResolved || selectedProductKey || '请选择商品' }}</span>
            </div>
            <el-button type="primary" :loading="quoteSaving" :disabled="quoteSubmitDisabled" @click="saveQuote">提交报价</el-button>
          </div>
        </div>
      </section>

      <section class="supplier-admin-column supplier-quotes-column">
        <div class="supplier-form-card">
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
            <p>先创建供应商并录入报价，这里会自动汇总干调类、蔬菜类等分类。</p>
          </div>
        </div>

        <div class="supplier-column-head">
          <strong>最近报价记录</strong>
          <span>{{ selectedSupplier ? selectedSupplier.supplier_name : '未选择供应商' }}</span>
        </div>
        <div v-if="selectedSupplierQuoteRows.length" class="supplier-quote-list">
          <article v-for="item in selectedSupplierQuoteRows" :key="`${item.supplier_id}-${item.quoted_at}-${item.price_identity_key}`" class="supplier-quote-row">
            <div class="supplier-quote-row-head">
              <strong>{{ item.product_name || item.price_identity_label || item.price_identity_key }}</strong>
              <span>{{ formatPrice(item.quote_price) }}</span>
            </div>
            <div class="supplier-quote-row-meta">
              <span>{{ item.market_category || item.category || '待分类' }}</span>
              <span>{{ item.quote_unit || '未标单位' }}</span>
              <span>{{ item.inventory_status || '库存待确认' }}</span>
            </div>
            <div class="supplier-quote-row-foot">
              <small>{{ formatTime(item.quoted_at) }}</small>
              <small>{{ item.remarks || '无备注' }}</small>
            </div>
          </article>
        </div>
        <div v-else class="supplier-card-empty">
          <strong>{{ selectedSupplier ? '这家供应商还没有录价' : '请先选择供应商' }}</strong>
          <p>{{ selectedSupplier ? '在中间表单里选择商品并录入报价。' : '左侧选择供应商后，这里会显示最近报价。' }}</p>
        </div>

        <div class="supplier-form-card">
          <div class="supplier-column-head compact">
            <strong>后台最新录价</strong>
            <span>{{ recentQuoteRows.length }} 条</span>
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
                <span>{{ formatPrice(item.quote_price) }}</span>
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
            <strong>还没有后台录价</strong>
            <p>录价后这里会按时间倒序展示，便于快速回看最近更新。</p>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import {
  createSupplier,
  fetchProductSupplierQuotes,
  fetchSupplierOverview,
  fetchSupplierQuotesBySupplier,
  fetchSuppliers,
  submitSupplierQuote,
  updateSupplier,
} from '../api'
import type {
  ProductOptionItem,
  SupplierCategorySummaryItem,
  SupplierItem,
  SupplierOverviewResponse,
  SupplierQuoteCompareResponse,
  SupplierQuoteCreatePayload,
  SupplierQuoteItem,
} from '../types'

const props = defineProps<{
  productOptions: ProductOptionItem[]
  selectedIdentityKey: string
  selectedProductLabel: string
  mobile: boolean
}>()

const emit = defineEmits<{
  (event: 'select-product', value: string): void
}>()

const loading = ref(false)
const supplierSaving = ref(false)
const quoteSaving = ref(false)
const keyword = ref('')
const categoryFilter = ref('')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')
const suppliers = ref<SupplierItem[]>([])
const overview = ref<SupplierOverviewResponse | null>(null)
const productCompare = ref<SupplierQuoteCompareResponse | null>(null)
const selectedSupplierId = ref<number | null>(null)
const selectedSupplierQuoteRows = ref<SupplierQuoteItem[]>([])

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

const quoteForm = reactive({
  quote_price: undefined as number | undefined,
  quote_unit: '斤',
  box_price: undefined as number | undefined,
  tax_price: undefined as number | undefined,
  inventory_status: '现货',
  remarks: '',
})

const selectedSupplier = computed(() => suppliers.value.find((item) => item.id === selectedSupplierId.value) || null)
const selectedProductKey = computed(() => props.selectedIdentityKey || props.productOptions[0]?.price_identity_key || '')
const selectedProductOption = computed(
  () => props.productOptions.find((item) => item.price_identity_key === selectedProductKey.value) || props.productOptions[0] || null,
)
const selectedProductLabelResolved = computed(
  () => selectedProductOption.value?.price_identity_label || props.selectedProductLabel || selectedProductKey.value || '',
)
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
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(search))
  })
})
const categorySummaryItems = computed<SupplierCategorySummaryItem[]>(() => overview.value?.category_items ?? [])
const recentQuoteRows = computed(() => overview.value?.recent_quotes ?? [])
const productCompareSummary = computed(() => productCompare.value?.summary ?? null)
const selectedSupplierCurrentQuote = computed(
  () => productCompare.value?.items.find((item) => item.supplier_id === selectedSupplierId.value) ?? null,
)
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
const quoteSubmitDisabled = computed(
  () => !selectedSupplier.value || !selectedSupplier.value.is_active || !selectedProductKey.value,
)
const selectedSupplierComparisonLabel = computed(() => {
  if (selectedSupplier.value && !selectedSupplier.value.is_active) {
    return '供应商已停用，当前不可继续录价'
  }
  return selectedSupplierCurrentQuote.value?.comparison_label || '录价后会自动和公开最低价做对比'
})

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

function resetSupplierForm() {
  selectedSupplierId.value = null
  supplierForm.supplier_name = ''
  supplierForm.contact_name = ''
  supplierForm.contact_phone = ''
  supplierForm.market_scope = '本地市场'
  supplierForm.market_category = ''
  supplierForm.channel = '微信小程序'
  supplierForm.notes = ''
  supplierForm.is_active = true
  selectedSupplierQuoteRows.value = []
}

function resetQuoteForm() {
  quoteForm.quote_price = undefined
  quoteForm.quote_unit = '斤'
  quoteForm.box_price = undefined
  quoteForm.tax_price = undefined
  quoteForm.inventory_status = '现货'
  quoteForm.remarks = ''
}

async function loadSuppliers() {
  const response = await fetchSuppliers(false)
  suppliers.value = response.items ?? []
  const hasSelected = suppliers.value.some((item) => item.id === selectedSupplierId.value)
  if (!hasSelected) {
    selectedSupplierId.value = suppliers.value[0]?.id ?? null
  }
}

async function loadOverview() {
  overview.value = await fetchSupplierOverview(12)
}

async function loadSupplierQuotes() {
  if (!selectedSupplierId.value) {
    selectedSupplierQuoteRows.value = []
    return
  }
  const response = await fetchSupplierQuotesBySupplier(selectedSupplierId.value, 20)
  selectedSupplierQuoteRows.value = response.items ?? []
}

async function loadProductCompare() {
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
}

async function reloadAll() {
  loading.value = true
  try {
    await Promise.all([loadSuppliers(), loadOverview(), loadProductCompare()])
    fillSupplierForm(selectedSupplier.value)
    await loadSupplierQuotes()
  } catch {
    ElMessage.error('供应商后台加载失败，请确认后端服务正常')
  } finally {
    loading.value = false
  }
}

function selectSupplier(id: number) {
  selectedSupplierId.value = id
}

async function saveSupplier() {
  if (!supplierForm.supplier_name.trim()) {
    ElMessage.warning('请填写供应商名称')
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
    quoted_by: selectedSupplier.value.contact_name || undefined,
  }

  quoteSaving.value = true
  try {
    await submitSupplierQuote(payload)
    ElMessage.success('报价已录入并同步到前台对比')
    resetQuoteForm()
    await reloadAll()
  } catch {
    ElMessage.error('报价提交失败，请稍后重试')
  } finally {
    quoteSaving.value = false
  }
}

function handleProductChange(value: string) {
  if (!value) return
  emit('select-product', value)
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
  fillSupplierForm(selectedSupplier.value)
  await loadSupplierQuotes()
})

watch(
  () => selectedProductKey.value,
  async () => {
    await loadProductCompare()
  },
)

watch(
  () => props.productOptions,
  () => {
    if (!props.selectedIdentityKey && props.productOptions[0]?.price_identity_key) {
      emit('select-product', props.productOptions[0].price_identity_key)
    }
  },
  { immediate: true },
)

void reloadAll()
</script>

<style scoped>
.supplier-admin-panel,
.supplier-admin-layout,
.supplier-admin-metrics,
.supplier-admin-toolbar,
.supplier-card-list,
.supplier-category-list,
.supplier-compare-summary,
.supplier-form-grid,
.supplier-overview-quote-list,
.supplier-quote-list {
  display: grid;
  gap: 12px;
}

.supplier-admin-metrics {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.supplier-admin-metric,
.supplier-card,
.supplier-form-card,
.supplier-category-row,
.supplier-compare-card,
.supplier-overview-quote-row,
.supplier-quote-row,
.supplier-card-empty {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.92);
}

.supplier-admin-metric,
.supplier-form-card,
.supplier-category-row,
.supplier-compare-card,
.supplier-overview-quote-row,
.supplier-quote-row,
.supplier-card-empty {
  padding: 16px;
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
  font-size: 24px;
}

.supplier-admin-toolbar {
  grid-template-columns: 1.2fr 0.9fr 0.7fr;
}

.supplier-admin-layout {
  grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.2fr) minmax(0, 0.88fr);
  align-items: start;
}

.supplier-admin-column {
  display: grid;
  gap: 12px;
}

.supplier-column-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.supplier-column-head strong {
  color: var(--ink-900);
  font-size: 16px;
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

.supplier-card-head strong,
.supplier-quote-row-head strong {
  color: var(--ink-900);
  font-size: 15px;
}

.supplier-category-row,
.supplier-compare-card,
.supplier-overview-quote-row {
  display: grid;
  gap: 8px;
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

.supplier-form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.supplier-form-field {
  display: grid;
  gap: 8px;
}

.supplier-form-field span,
.supplier-inline-tip span {
  color: var(--ink-500);
  font-size: 12px;
}

.supplier-form-field-full {
  grid-column: 1 / -1;
}

.supplier-form-action-buttons {
  display: flex;
  gap: 8px;
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
}

.supplier-overview-quote-list {
  max-height: 360px;
  overflow: auto;
}

.supplier-quote-row {
  display: grid;
  gap: 8px;
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

.compact-empty {
  padding: 14px;
}

.supplier-card-empty strong {
  display: block;
  margin-bottom: 6px;
  color: var(--ink-900);
}

.mobile .supplier-admin-metrics,
.mobile .supplier-admin-toolbar,
.mobile .supplier-admin-layout {
  grid-template-columns: 1fr;
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
}

.mobile .supplier-form-grid {
  grid-template-columns: 1fr;
}

.mobile .supplier-form-actions {
  align-items: flex-start;
  flex-direction: column;
}
</style>
