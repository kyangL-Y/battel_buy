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
        <div class="supplier-summary-meta-stack">
          <small>{{ marketLowestSourceSummary }}</small>
          <small class="supplier-summary-secondary">{{ formatPrice(quoteSummary.market_average_price) }} 为公开均价</small>
        </div>
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

    <div v-if="quoteRows.length" class="supplier-quote-workbench">
      <div class="supplier-quote-toolbar">
        <div class="supplier-quote-toolbar-search">
          <el-input v-model="quoteKeyword" clearable placeholder="搜索供应商、分类、库存、备注" />
        </div>
        <div class="supplier-quote-filter-tabs" aria-label="报价筛选">
          <button
            v-for="item in quoteFilterTabs"
            :key="item.key"
            type="button"
            class="supplier-quote-filter-tab"
            :class="{ active: quoteStatusFilter === item.key }"
            @click="quoteStatusFilter = item.key"
          >
            <strong>{{ item.label }}</strong>
            <small>{{ item.count }}</small>
          </button>
        </div>
        <div class="supplier-quote-toolbar-meta">
          <span>显示 {{ filteredQuoteRows.length }} / {{ quoteRows.length }} 条</span>
          <button type="button" @click="selectAllFilteredQuotes">全选当前</button>
        </div>
      </div>

      <div v-if="selectedQuoteRows.length" class="supplier-quote-batch-bar">
        <div>
          <strong>已选 {{ selectedQuoteRows.length }} 条报价</strong>
          <span>可批量复制给采购或运营复核</span>
        </div>
        <div class="supplier-quote-batch-actions">
          <button type="button" @click="copySelectedQuotes">复制所选</button>
          <button type="button" @click="clearQuoteSelection">取消选择</button>
        </div>
      </div>

      <div v-if="filteredQuoteRows.length" class="supplier-quote-list">
        <article
          v-for="item in filteredQuoteRows"
          :key="quoteRowKey(item)"
          class="supplier-quote-card"
          :class="{
            selected: selectedQuoteKeys.includes(quoteRowKey(item)),
            active: activeQuoteDetailKey === quoteRowKey(item),
          }"
          role="button"
          tabindex="0"
          @click="openQuoteDetail(item)"
          @keydown.enter="openQuoteDetail(item)"
          @keydown.space.prevent="openQuoteDetail(item)"
        >
          <div class="supplier-quote-select-row">
            <label class="supplier-quote-select" @click.stop>
              <input
                type="checkbox"
                :checked="selectedQuoteKeys.includes(quoteRowKey(item))"
                @change="toggleQuoteSelection(item)"
              />
              <span>选择</span>
            </label>
            <button type="button" class="supplier-quote-detail-button" @click.stop="openQuoteDetail(item)">详情</button>
          </div>

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

      <div v-else class="supplier-empty-state">
        <strong>当前筛选下没有报价</strong>
        <p>可以清空搜索词，或切回全部报价继续查看。</p>
      </div>
    </div>

    <aside
      v-if="activeQuoteDetail"
      class="supplier-quote-detail-drawer"
      role="dialog"
      aria-modal="false"
      aria-label="报价详情"
    >
      <div class="supplier-quote-detail-panel">
        <div class="supplier-quote-detail-head">
          <div>
            <span>报价详情</span>
            <strong>{{ activeQuoteDetail.supplier_name }}</strong>
            <small>{{ activeQuoteDetail.price_identity_label || productLabel || activeQuoteDetail.product_name || '当前商品' }}</small>
          </div>
          <button type="button" @click="closeQuoteDetail">关闭</button>
        </div>

        <div class="supplier-quote-detail-grid">
          <article>
            <span>报价</span>
            <strong>{{ formatPrice(activeQuoteDetail.quote_price) }}</strong>
            <small>{{ activeQuoteDetail.quote_unit || '未标单位' }}</small>
          </article>
          <article>
            <span>箱价</span>
            <strong>{{ formatPrice(activeQuoteDetail.box_price) }}</strong>
            <small>可选字段</small>
          </article>
          <article>
            <span>含税价</span>
            <strong>{{ formatPrice(activeQuoteDetail.tax_price) }}</strong>
            <small>可选字段</small>
          </article>
          <article>
            <span>库存</span>
            <strong>{{ activeQuoteDetail.inventory_status || '库存待确认' }}</strong>
            <small>{{ formatTime(activeQuoteDetail.quoted_at) }}</small>
          </article>
        </div>

        <div class="supplier-quote-detail-meta">
          <span>{{ activeQuoteDetail.comparison_label || '待比对' }}</span>
          <span>{{ activeQuoteDetail.market_category || activeQuoteDetail.category || '待分类' }}</span>
          <span>{{ activeQuoteDetail.channel || '渠道待标注' }}</span>
          <span>{{ activeQuoteDetail.contact_name || activeQuoteDetail.quoted_by || '联系人待补充' }}</span>
        </div>
        <p class="supplier-quote-detail-note">{{ activeQuoteDetail.remarks || '暂无备注' }}</p>
      </div>
    </aside>

    <div v-else-if="selectedIdentityKey && !loading" class="supplier-empty-state">
      <strong>还没有本地供应商报价</strong>
      <p>先补录一条报价，前台就能和公开市场价格做对比。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { fetchProductSupplierQuotes, fetchSuppliers, getAccessToken, submitSupplierQuote } from '../lazyApi'
import { lazyElMessage as ElMessage } from '../lazyElementMessage'
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
const quoteKeyword = ref('')
const quoteStatusFilter = ref<'all' | 'below' | 'available' | 'out_of_stock'>('all')
const selectedQuoteKeys = ref<string[]>([])
const activeQuoteDetailKey = ref('')

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
const marketLowestSourceSummary = computed(() => {
  if (!quoteSummary.value) {
    return '公开来源待补充'
  }
  const marketSite = String(quoteSummary.value.market_lowest_site || '').trim()
  const sourceName = String(quoteSummary.value.market_lowest_source_name || '').trim()
  const sourceTier = String(quoteSummary.value.market_lowest_source_tier || '').trim()
  const parts = [marketSite]
  if (sourceName && (!marketSite || !marketSite.includes(sourceName))) {
    parts.push(sourceName)
  }
  if (sourceTier) {
    parts.push(sourceTier)
  }
  return parts.length ? Array.from(new Set(parts)).join(' · ') : '公开来源待补充'
})
const filteredQuoteRows = computed(() =>
  quoteRows.value.filter((item) => {
    if (quoteStatusFilter.value === 'below' && !isQuoteBelowMarket(item)) return false
    if (quoteStatusFilter.value === 'available' && !hasAvailableInventory(item)) return false
    if (quoteStatusFilter.value === 'out_of_stock' && hasAvailableInventory(item)) return false
    const keyword = quoteKeyword.value.trim().toLowerCase()
    if (!keyword) return true
    return [
      item.supplier_name,
      item.contact_name,
      item.market_category,
      item.category,
      item.channel,
      item.inventory_status,
      item.remarks,
      item.comparison_label,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(keyword))
  }),
)
const selectedQuoteRows = computed(() => {
  const selected = new Set(selectedQuoteKeys.value)
  return quoteRows.value.filter((item) => selected.has(quoteRowKey(item)))
})
const activeQuoteDetail = computed(() =>
  quoteRows.value.find((item) => quoteRowKey(item) === activeQuoteDetailKey.value) || null,
)
const quoteFilterTabs = computed(() => [
  { key: 'all' as const, label: '全部', count: quoteRows.value.length },
  { key: 'below' as const, label: '低于公开价', count: quoteRows.value.filter(isQuoteBelowMarket).length },
  { key: 'available' as const, label: '有货', count: quoteRows.value.filter(hasAvailableInventory).length },
  { key: 'out_of_stock' as const, label: '缺货', count: quoteRows.value.filter((item) => !hasAvailableInventory(item)).length },
])

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

function quoteRowKey(item: SupplierQuoteItem) {
  return [
    item.record_id ?? item.supplier_id,
    item.price_identity_key || props.selectedIdentityKey,
    item.quoted_at || item.supplier_name,
  ].join('-')
}

function isQuoteBelowMarket(item: SupplierQuoteItem) {
  if (item.price_diff_to_market_lowest == null) return false
  return Number(item.price_diff_to_market_lowest) < 0
}

function hasAvailableInventory(item: SupplierQuoteItem) {
  const inventory = String(item.inventory_status || '').trim()
  return !inventory || !/(缺货|无货|售罄|暂停)/.test(inventory)
}

function toggleQuoteSelection(item: SupplierQuoteItem) {
  const key = quoteRowKey(item)
  selectedQuoteKeys.value = selectedQuoteKeys.value.includes(key)
    ? selectedQuoteKeys.value.filter((itemKey) => itemKey !== key)
    : [...selectedQuoteKeys.value, key]
}

function selectAllFilteredQuotes() {
  selectedQuoteKeys.value = Array.from(new Set([...selectedQuoteKeys.value, ...filteredQuoteRows.value.map(quoteRowKey)]))
}

function clearQuoteSelection() {
  selectedQuoteKeys.value = []
}

function openQuoteDetail(item: SupplierQuoteItem) {
  activeQuoteDetailKey.value = quoteRowKey(item)
}

function closeQuoteDetail() {
  activeQuoteDetailKey.value = ''
}

async function copySelectedQuotes() {
  if (!selectedQuoteRows.value.length) return
  const text = selectedQuoteRows.value
    .map((item) => [
      item.supplier_name,
      formatPrice(item.quote_price),
      item.quote_unit || '未标单位',
      item.inventory_status || '库存待确认',
      item.comparison_label || '待比对',
      formatTime(item.quoted_at),
    ].join(' | '))
    .join('\n')
  try {
    if (!navigator.clipboard?.writeText) throw new Error('clipboard unavailable')
    await navigator.clipboard.writeText(text)
    ElMessage.success(`已复制 ${selectedQuoteRows.value.length} 条报价`)
  } catch {
    ElMessage.warning('浏览器未允许复制，请手动选择报价内容')
  }
}

async function loadSupplierOptions() {
  if (!getAccessToken()) {
    supplierOptions.value = []
    return
  }
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
  if (!getAccessToken()) {
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
  if (!getAccessToken()) {
    supplierOptions.value = []
    quoteSummary.value = null
    quoteRows.value = []
    loading.value = false
    return
  }
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
    quoteKeyword.value = ''
    quoteStatusFilter.value = 'all'
    selectedQuoteKeys.value = []
    activeQuoteDetailKey.value = ''
    if (!identityKey) return
    await reloadAll()
  },
  { immediate: true },
)

watch(quoteRows, (rows) => {
  const availableKeys = new Set(rows.map(quoteRowKey))
  selectedQuoteKeys.value = selectedQuoteKeys.value.filter((key) => availableKeys.has(key))
  if (activeQuoteDetailKey.value && !availableKeys.has(activeQuoteDetailKey.value)) {
    activeQuoteDetailKey.value = ''
  }
})
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

.supplier-quote-workbench {
  display: grid;
  gap: 12px;
}

.supplier-quote-toolbar,
.supplier-quote-batch-bar {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid rgba(47, 128, 237, 0.12);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 12px 24px rgba(19, 57, 110, 0.05);
}

.supplier-quote-toolbar {
  grid-template-columns: minmax(220px, 1fr) auto auto;
  align-items: center;
}

.supplier-quote-toolbar-search {
  min-width: 0;
}

.supplier-quote-filter-tabs,
.supplier-quote-toolbar-meta,
.supplier-quote-batch-actions,
.supplier-quote-select-row,
.supplier-quote-select,
.supplier-quote-detail-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-quote-filter-tab,
.supplier-quote-toolbar-meta button,
.supplier-quote-batch-actions button,
.supplier-quote-detail-button,
.supplier-quote-detail-head button {
  min-height: 34px;
  border: 1px solid rgba(47, 128, 237, 0.14);
  border-radius: 999px;
  background: rgba(248, 250, 252, 0.96);
  color: #244a7c;
  font: inherit;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.supplier-quote-filter-tab {
  display: grid;
  gap: 1px;
  min-width: 84px;
  padding: 6px 10px;
  text-align: left;
}

.supplier-quote-filter-tab.active {
  border-color: rgba(37, 99, 235, 0.34);
  background: #eff6ff;
  color: #1d4ed8;
}

.supplier-quote-filter-tab small,
.supplier-quote-toolbar-meta span,
.supplier-quote-batch-bar span,
.supplier-quote-select span,
.supplier-quote-detail-head span,
.supplier-quote-detail-head small,
.supplier-quote-detail-grid small {
  color: #7890ad;
  font-size: 11px;
}

.supplier-quote-toolbar-meta {
  justify-content: flex-end;
}

.supplier-quote-toolbar-meta button,
.supplier-quote-batch-actions button,
.supplier-quote-detail-button,
.supplier-quote-detail-head button {
  padding: 0 12px;
}

.supplier-quote-batch-bar {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  border-color: rgba(37, 99, 235, 0.24);
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.96), rgba(255, 255, 255, 0.98));
}

.supplier-quote-batch-bar strong {
  display: block;
  color: #12263f;
}

.supplier-quote-select-row {
  justify-content: space-between;
  margin-bottom: 8px;
}

.supplier-quote-select {
  color: #244a7c;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.supplier-quote-select input {
  width: 16px;
  height: 16px;
  accent-color: #2563eb;
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

.supplier-summary-meta-stack {
  display: grid;
  gap: 2px;
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

.supplier-summary-secondary {
  color: #8aa0ba;
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
  cursor: pointer;
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease,
    transform 160ms ease;
}

.supplier-quote-card:hover,
.supplier-quote-card.active {
  border-color: rgba(37, 99, 235, 0.28);
  box-shadow: 0 18px 34px rgba(37, 99, 235, 0.1);
  transform: translateY(-1px);
}

.supplier-quote-card.selected {
  border-color: rgba(37, 99, 235, 0.36);
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.98), rgba(255, 255, 255, 0.96));
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

.supplier-quote-detail-drawer {
  position: fixed;
  inset: 0 0 0 auto;
  z-index: 30;
  width: min(420px, calc(100vw - 24px));
  padding: 18px;
  background: rgba(15, 23, 42, 0.12);
  backdrop-filter: blur(6px);
}

.supplier-quote-detail-panel {
  display: grid;
  gap: 14px;
  height: 100%;
  overflow: auto;
  padding: 18px;
  border: 1px solid rgba(47, 128, 237, 0.16);
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 24px 54px rgba(15, 23, 42, 0.18);
}

.supplier-quote-detail-head {
  justify-content: space-between;
  align-items: flex-start;
}

.supplier-quote-detail-head div,
.supplier-quote-detail-grid article {
  display: grid;
  gap: 4px;
}

.supplier-quote-detail-head strong {
  color: #12263f;
  font-size: 22px;
}

.supplier-quote-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.supplier-quote-detail-grid article {
  padding: 12px;
  border: 1px solid rgba(47, 128, 237, 0.1);
  border-radius: 14px;
  background: #f8fbff;
}

.supplier-quote-detail-grid span,
.supplier-quote-detail-meta span {
  color: #7890ad;
  font-size: 12px;
}

.supplier-quote-detail-grid strong {
  color: #12263f;
  font-size: 18px;
}

.supplier-quote-detail-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.supplier-quote-detail-meta span {
  padding: 7px 10px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
}

.supplier-quote-detail-note {
  margin: 0;
  padding: 12px;
  border-radius: 14px;
  background: #f8fafc;
  color: #53657e;
  line-height: 1.6;
}

.mobile .supplier-summary-strip,
.mobile .supplier-quote-list {
  grid-template-columns: 1fr;
}

.mobile .supplier-quote-toolbar,
.mobile .supplier-quote-batch-bar {
  grid-template-columns: 1fr;
}

.mobile .supplier-quote-filter-tabs {
  overflow-x: auto;
  flex-wrap: nowrap;
  padding-bottom: 2px;
}

.mobile .supplier-quote-filter-tab {
  flex: 0 0 108px;
}

.mobile .supplier-quote-detail-drawer {
  inset: auto 0 0;
  width: 100%;
  max-height: 82vh;
  padding: 12px;
}

@media (max-width: 1180px) {
  .supplier-summary-strip,
  .supplier-quote-list {
    grid-template-columns: 1fr;
  }

  .supplier-quote-toolbar,
  .supplier-quote-batch-bar {
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

  .supplier-quote-detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
