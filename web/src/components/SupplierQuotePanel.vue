<template>
  <section class="supplier-panel" :class="{ mobile }">
    <div class="supplier-panel-head">
      <div>
        <p class="panel-kicker">本地供应商</p>
        <h3>供应商报价对比</h3>
        <p>按当前商品查看本地报价，并可直接补录新报价。</p>
      </div>
      <button type="button" class="supplier-refresh-button" :disabled="!selectedIdentityKey || loading" @click="reloadAll">
        {{ loading ? '同步中...' : '刷新报价' }}
      </button>
    </div>

    <div v-if="quoteSummary" class="supplier-summary-strip">
      <article class="supplier-summary-card">
        <span>供应商数</span>
        <strong>{{ quoteSummary.supplier_count }}</strong>
        <small>当前商品已有本地报价</small>
      </article>
      <article class="supplier-summary-card">
        <span>最低本地价</span>
        <strong>{{ formatPrice(quoteSummary.lowest_quote) }}</strong>
        <small>{{ quoteSummary.lowest_quote_supplier || '待补录' }}</small>
      </article>
      <article class="supplier-summary-card">
        <span>公开最低价</span>
        <strong>{{ formatPrice(quoteSummary.market_lowest_price) }}</strong>
        <small>{{ formatPrice(quoteSummary.market_average_price) }} 为公开均价</small>
      </article>
      <article class="supplier-summary-card">
        <span>最近录价</span>
        <strong>{{ formatTime(quoteSummary.latest_quoted_at) }}</strong>
        <small>{{ productLabel || quoteSummary.product_name }}</small>
      </article>
    </div>

    <div v-if="selectedIdentityKey" class="supplier-entry-card">
      <div class="supplier-entry-head">
        <strong>快速录价</strong>
        <span>适合供应商在后台录入，也适合运营临时补价。</span>
      </div>
      <div class="supplier-entry-grid">
        <label class="supplier-field">
          <span>选择已有供应商</span>
          <el-select
            :model-value="selectedSupplierId"
            clearable
            filterable
            placeholder="可选，优先复用已有供应商"
            @change="handleSupplierSelect"
          >
            <el-option
              v-for="item in supplierOptions"
              :key="item.id"
              :label="item.supplier_name"
              :value="item.id"
            />
          </el-select>
        </label>
        <label class="supplier-field">
          <span>供应商名称</span>
          <el-input v-model="form.supplier_name" placeholder="例如：莲菜档口A" />
        </label>
        <label class="supplier-field">
          <span>联系人</span>
          <el-input v-model="form.contact_name" placeholder="例如：老王" />
        </label>
        <label class="supplier-field">
          <span>市场分类</span>
          <el-select v-model="form.market_category" clearable filterable placeholder="干调类 / 蔬菜类">
            <el-option v-for="item in marketCategoryOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </label>
        <label class="supplier-field">
          <span>来源渠道</span>
          <el-select v-model="form.channel" clearable filterable placeholder="来源渠道">
            <el-option v-for="item in channelOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </label>
        <label class="supplier-field">
          <span>库存状态</span>
          <el-input v-model="form.inventory_status" placeholder="现货 / 预定 / 缺货" />
        </label>
        <label class="supplier-field">
          <span>报价</span>
          <el-input-number v-model="form.quote_price" :min="0" :precision="2" :step="0.1" controls-position="right" />
        </label>
        <label class="supplier-field">
          <span>计价单位</span>
          <el-input v-model="form.quote_unit" placeholder="斤 / 箱 / 件" />
        </label>
        <label class="supplier-field">
          <span>箱价</span>
          <el-input-number v-model="form.box_price" :min="0" :precision="2" :step="0.5" controls-position="right" />
        </label>
        <label class="supplier-field">
          <span>含税价</span>
          <el-input-number v-model="form.tax_price" :min="0" :precision="2" :step="0.5" controls-position="right" />
        </label>
      </div>
      <label class="supplier-field supplier-field-full">
        <span>备注</span>
        <el-input v-model="form.remarks" type="textarea" :rows="mobile ? 3 : 2" placeholder="例如：早市价、满箱可送、下午 3 点前发车" />
      </label>
      <div class="supplier-entry-actions">
        <div class="supplier-entry-tip">
          <strong>{{ productLabel || '当前商品' }}</strong>
          <span>{{ selectedIdentityKey }}</span>
        </div>
        <el-button type="primary" :loading="saving" @click="submitQuoteEntry">提交报价</el-button>
      </div>
    </div>

    <div v-if="quoteRows.length" class="supplier-quote-list">
      <article v-for="item in quoteRows" :key="`${item.supplier_id}-${item.quoted_at}`" class="supplier-quote-card">
        <div class="supplier-quote-head">
          <div>
            <strong>{{ item.supplier_name }}</strong>
            <p>{{ item.market_category || '待分类' }} · {{ item.channel || '待标注渠道' }}</p>
          </div>
          <div class="supplier-quote-price">
            <strong>{{ formatPrice(item.quote_price) }}</strong>
            <small>{{ item.quote_unit || '未标单位' }}</small>
          </div>
        </div>
        <div class="supplier-quote-meta">
          <span>{{ item.comparison_label || '待比对' }}</span>
          <span v-if="item.box_price != null">箱价 {{ formatPrice(item.box_price) }}</span>
          <span v-if="item.tax_price != null">含税 {{ formatPrice(item.tax_price) }}</span>
        </div>
        <div class="supplier-quote-foot">
          <span>{{ item.inventory_status || '库存待确认' }}</span>
          <span>{{ formatTime(item.quoted_at) }}</span>
        </div>
        <p v-if="item.remarks" class="supplier-quote-remarks">{{ item.remarks }}</p>
      </article>
    </div>

    <div v-else-if="selectedIdentityKey && !loading" class="supplier-empty-state">
      <strong>还没有本地供应商报价</strong>
      <p>先补录一条报价，前台就能和公开市场价格做对比。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { fetchProductSupplierQuotes, fetchSuppliers, submitSupplierQuote } from '../api'
import type {
  SupplierItem,
  SupplierQuoteCompareSummary,
  SupplierQuoteCreatePayload,
  SupplierQuoteItem,
} from '../types'

const props = defineProps<{
  selectedIdentityKey: string
  productLabel: string
  mobile: boolean
}>()

const loading = ref(false)
const saving = ref(false)
const supplierOptions = ref<SupplierItem[]>([])
const quoteSummary = ref<SupplierQuoteCompareSummary | null>(null)
const quoteRows = ref<SupplierQuoteItem[]>([])
const selectedSupplierId = ref<number | undefined>(undefined)

const form = reactive({
  supplier_name: '',
  contact_name: '',
  market_category: '',
  channel: '微信小程序',
  inventory_status: '现货',
  quote_price: undefined as number | undefined,
  quote_unit: '斤',
  box_price: undefined as number | undefined,
  tax_price: undefined as number | undefined,
  remarks: '',
})

const marketCategoryOptions = computed(() => {
  const base = ['蔬菜类', '干调类', '水产类', '冻品类', '肉禽蛋类', '粮油米面类']
  const dynamic = supplierOptions.value
    .map((item) => String(item.market_category || '').trim())
    .filter(Boolean)
  return Array.from(new Set([...base, ...dynamic]))
})

const channelOptions = computed(() => {
  const base = ['微信小程序', 'Excel', '门店直报', '电话报价']
  const dynamic = supplierOptions.value
    .map((item) => String(item.channel || '').trim())
    .filter(Boolean)
  return Array.from(new Set([...base, ...dynamic]))
})

function resetForm(keepSupplier = false) {
  if (!keepSupplier) {
    selectedSupplierId.value = undefined
    form.supplier_name = ''
    form.contact_name = ''
    form.market_category = ''
    form.channel = '微信小程序'
  }
  form.inventory_status = '现货'
  form.quote_price = undefined
  form.quote_unit = '斤'
  form.box_price = undefined
  form.tax_price = undefined
  form.remarks = ''
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

async function loadSupplierOptions() {
  try {
    const response = await fetchSuppliers(true)
    supplierOptions.value = response.items ?? []
  } catch {
    supplierOptions.value = []
  }
}

async function loadQuoteRows() {
  if (!props.selectedIdentityKey) {
    quoteSummary.value = null
    quoteRows.value = []
    return
  }
  const response = await fetchProductSupplierQuotes(props.selectedIdentityKey)
  quoteSummary.value = response.summary
  quoteRows.value = response.items ?? []
}

async function reloadAll() {
  if (!props.selectedIdentityKey) return
  loading.value = true
  try {
    await Promise.all([loadSupplierOptions(), loadQuoteRows()])
  } catch {
    ElMessage.error('供应商报价加载失败，请确认后端服务正常')
  } finally {
    loading.value = false
  }
}

function handleSupplierSelect(value?: number) {
  selectedSupplierId.value = value || undefined
  const supplier = supplierOptions.value.find((item) => item.id === value)
  if (!supplier) return
  form.supplier_name = supplier.supplier_name
  form.contact_name = String(supplier.contact_name || '')
  form.market_category = String(supplier.market_category || '')
  form.channel = String(supplier.channel || '') || '微信小程序'
}

async function submitQuoteEntry() {
  if (!props.selectedIdentityKey) {
    ElMessage.warning('请先选择一个商品')
    return
  }
  if (!String(form.supplier_name || '').trim()) {
    ElMessage.warning('请填写供应商名称')
    return
  }
  if (form.quote_price == null || Number(form.quote_price) <= 0) {
    ElMessage.warning('请填写有效报价')
    return
  }

  const payload: SupplierQuoteCreatePayload = {
    price_identity_key: props.selectedIdentityKey,
    supplier_id: selectedSupplierId.value,
    supplier_name: form.supplier_name.trim(),
    contact_name: form.contact_name.trim() || undefined,
    market_scope: '本地市场',
    market_category: form.market_category.trim() || undefined,
    channel: form.channel.trim() || undefined,
    product_name: props.productLabel || undefined,
    price_identity_label: props.productLabel || undefined,
    quote_price: Number(form.quote_price),
    quote_unit: form.quote_unit.trim() || undefined,
    box_price: form.box_price == null ? undefined : Number(form.box_price),
    tax_price: form.tax_price == null ? undefined : Number(form.tax_price),
    inventory_status: form.inventory_status.trim() || undefined,
    remarks: form.remarks.trim() || undefined,
    quoted_by: form.contact_name.trim() || undefined,
  }

  saving.value = true
  try {
    await submitSupplierQuote(payload)
    ElMessage.success('供应商报价已录入')
    await reloadAll()
    resetForm(true)
  } catch {
    ElMessage.error('报价提交失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

watch(
  () => props.selectedIdentityKey,
  async (identityKey) => {
    resetForm()
    quoteSummary.value = null
    quoteRows.value = []
    if (!identityKey) return
    await reloadAll()
  },
  { immediate: true },
)
</script>

<style scoped>
.supplier-panel {
  display: grid;
  gap: 16px;
  margin-top: 18px;
}

.supplier-panel-head,
.supplier-entry-head,
.supplier-entry-actions,
.supplier-quote-head,
.supplier-quote-foot,
.supplier-quote-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.supplier-panel-head h3 {
  margin: 4px 0 6px;
  font-size: 20px;
  color: #11253d;
}

.supplier-panel-head p,
.supplier-entry-head span,
.supplier-empty-state p,
.supplier-quote-head p,
.supplier-quote-foot span,
.supplier-quote-meta span,
.supplier-quote-remarks,
.supplier-summary-card small,
.supplier-entry-tip span {
  margin: 0;
  color: #6c7d96;
  line-height: 1.5;
}

.supplier-refresh-button {
  padding: 10px 16px;
  border: 1px solid rgba(47, 128, 237, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: #244a7c;
  font-weight: 600;
  cursor: pointer;
}

.supplier-refresh-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.supplier-summary-strip,
.supplier-quote-list,
.supplier-entry-grid {
  display: grid;
  gap: 12px;
}

.supplier-summary-strip {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.supplier-summary-card,
.supplier-entry-card,
.supplier-quote-card,
.supplier-empty-state {
  border: 1px solid rgba(47, 128, 237, 0.12);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(245, 249, 255, 0.92));
  box-shadow: 0 18px 34px rgba(19, 57, 110, 0.08);
}

.supplier-summary-card,
.supplier-empty-state {
  padding: 16px;
}

.supplier-summary-card span,
.supplier-field span,
.supplier-entry-tip strong {
  display: block;
  font-size: 12px;
  color: #7890ad;
}

.supplier-summary-card strong,
.supplier-quote-price strong,
.supplier-entry-tip strong {
  display: block;
  margin: 6px 0 4px;
  color: #12263f;
  font-size: 22px;
}

.supplier-entry-card {
  padding: 18px;
}

.supplier-entry-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 14px;
}

.supplier-field {
  display: grid;
  gap: 8px;
}

.supplier-field-full {
  margin-top: 12px;
}

.supplier-entry-actions {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed rgba(120, 144, 173, 0.24);
}

.supplier-entry-tip {
  display: grid;
  gap: 4px;
}

.supplier-quote-list {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.supplier-quote-card {
  padding: 16px;
}

.supplier-quote-head strong {
  color: #132e4f;
  font-size: 18px;
}

.supplier-quote-price {
  text-align: right;
}

.supplier-quote-price small {
  color: #7890ad;
}

.supplier-quote-meta {
  margin-top: 12px;
  flex-wrap: wrap;
}

.supplier-quote-meta span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(47, 128, 237, 0.08);
  color: #244a7c;
  font-size: 12px;
}

.supplier-quote-foot {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed rgba(120, 144, 173, 0.24);
}

.supplier-quote-remarks {
  margin-top: 12px;
  font-size: 13px;
}

.supplier-empty-state {
  text-align: center;
}

.supplier-empty-state strong {
  display: block;
  margin-bottom: 8px;
  color: #132e4f;
  font-size: 18px;
}

.mobile .supplier-summary-strip,
.mobile .supplier-quote-list {
  grid-template-columns: 1fr;
}

@media (max-width: 1180px) {
  .supplier-summary-strip,
  .supplier-quote-list {
    grid-template-columns: 1fr;
  }
}

.mobile .supplier-entry-grid {
  grid-template-columns: 1fr;
}

.mobile .supplier-panel-head,
.mobile .supplier-entry-head,
.mobile .supplier-entry-actions,
.mobile .supplier-quote-head,
.mobile .supplier-quote-foot {
  align-items: flex-start;
  flex-direction: column;
}

.mobile .supplier-quote-price {
  text-align: left;
}

@media (max-width: 720px) {
  .supplier-entry-grid,
  .supplier-quote-list,
  .supplier-summary-strip {
    grid-template-columns: 1fr;
  }
}
</style>
