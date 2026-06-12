<template>
  <section class="market-mobile-alert-page">
    <header class="market-mobile-alert-hero">
      <div>
        <p class="market-mobile-kicker">价格提醒</p>
        <h2>需要看一下的价格</h2>
        <span>{{ alertHeroText }}</span>
      </div>
      <strong>{{ alertDisplayBadge }}</strong>
    </header>

    <div class="market-mobile-alert-pills" aria-label="价格提醒概览">
      <article v-for="item in alertSummaryPills" :key="item.label" :class="item.tone">
        <strong>{{ item.value }}</strong>
        <span>{{ item.label }}</span>
      </article>
    </div>

    <section class="market-mobile-alert-card market-mobile-alert-feed-card">
      <div class="market-mobile-section-head">
        <div>
          <p class="market-mobile-kicker">{{ alertFeedKicker }}</p>
          <h2>{{ alertFeedTitle }}</h2>
        </div>
        <span>{{ alertFeedCountLabel }}</span>
      </div>

      <div class="market-mobile-alert-list">
        <article v-for="item in alertRows" :key="`${item.name}-${item.market}`" :class="['market-mobile-alert-row', item.tone]">
          <div class="market-mobile-alert-row-main">
            <div class="market-mobile-alert-thumb-shell">
              <img
                v-if="item.imageUrl && !brokenAlertImageUrls.has(item.imageUrl)"
                :src="item.imageUrl"
                :alt="item.name"
                class="market-mobile-alert-thumb-image"
                loading="lazy"
                decoding="async"
                @error="handleAlertImageError(item.imageUrl)"
                @click.stop="emit('open-image-preview', item.imageUrl, item.name)"
              />
              <span v-else :class="['market-mobile-thumb', item.thumb]"></span>
            </div>
            <div>
              <strong>{{ item.name }}</strong>
              <small>{{ item.market }} · {{ item.current }}</small>
            </div>
            <em>{{ item.state }}</em>
          </div>
          <p>{{ item.rule }}</p>
          <footer>
            <button type="button" @click="emit('open-trend', item)">看趋势</button>
            <button type="button" @click="emit('open-supplier', item)">找报价</button>
            <button v-if="item.state === '待处理'" type="button" class="primary" @click="emit('acknowledge', item)">标记处理</button>
            <button v-else type="button" disabled>已观察</button>
            <time>{{ item.time }}</time>
          </footer>
        </article>

        <div v-if="!alertRows.length" class="market-mobile-alert-empty">
          <strong>暂无价格提醒</strong>
          <p>超过提醒价格后会出现在这里。</p>
        </div>
      </div>
    </section>

    <section class="market-mobile-alert-card market-mobile-alert-rule-card" :class="{ collapsed: !showRuleForm }">
      <div class="market-mobile-section-head">
        <div>
          <p class="market-mobile-kicker">提醒设置</p>
          <h2>设置提醒价格</h2>
        </div>
        <button
          type="button"
          class="market-mobile-rule-toggle"
          @click="showRuleForm = !showRuleForm"
        >
          {{ showRuleForm ? '收起' : '新增提醒' }}
        </button>
      </div>

      <p v-if="!showRuleForm" class="market-mobile-rule-summary">
        选择商品后，设置到价提醒。
      </p>

      <div v-else class="market-mobile-rule-form">
        <label>
          <span>商品</span>
          <select v-model="ruleDraft.identityKey">
            <option value="">请选择商品</option>
            <option v-for="item in productOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
        </label>
        <label>
          <span>来源</span>
          <select v-model="ruleDraft.sourceName">
            <option value="">全部来源</option>
            <option v-for="item in sourceOptions" :key="item" :value="item">
              {{ item }}
            </option>
          </select>
        </label>
        <label><span>市场</span><strong>{{ locationLabel }}</strong></label>
        <label><span>最高价</span><input v-model.number="ruleDraft.maxPrice" type="number" min="0" step="0.01" placeholder="例如 12.50" /></label>
        <label><span>最低价</span><input v-model.number="ruleDraft.minPrice" type="number" min="0" step="0.01" placeholder="例如 8.80" /></label>
        <label><span>提醒价格</span><strong>{{ alertThresholdLabel }}</strong></label>
        <button type="button" @click="emit('save-rule')">保存提醒</button>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'

export type MobileAlertPageRow = {
  identityKey?: string
  name: string
  market: string
  current: string
  rule: string
  state: string
  time: string
  tone: string
  thumb: string
  imageUrl?: string
}

type MobileAlertProductOption = {
  value: string
  label: string
}

type MobileAlertRuleDraft = {
  identityKey: string
  productLabel: string
  sourceName: string
  sourceLabel: string
  minPrice: number
  maxPrice: number
}

const props = defineProps<{
  alertRows: MobileAlertPageRow[]
  alertBadge: number | string
  locationLabel: string
  productOptions: MobileAlertProductOption[]
  sourceOptions: string[]
}>()

const emit = defineEmits<{
  (event: 'open-image-preview', imageUrl: string, title: string): void
  (event: 'open-trend', item: MobileAlertPageRow): void
  (event: 'open-supplier', item: MobileAlertPageRow): void
  (event: 'acknowledge', item: MobileAlertPageRow): void
  (event: 'save-rule'): void
}>()

const ruleDraft = defineModel<MobileAlertRuleDraft>('ruleDraft', { required: true })
const showRuleForm = defineModel<boolean>('showRuleForm', { required: true })
const brokenAlertImageUrls = reactive(new Set<string>())

const alertHeroText = computed(() => {
  const pending = props.alertRows.filter((item) => item.state === '待处理').length
  if (pending > 0) return `当前有 ${pending} 个商品需要查看。`
  if (props.alertRows.length > 0) return `当前有 ${props.alertRows.length} 个商品正在观察。`
  return '暂无价格提醒。'
})

const alertDisplayBadge = computed(() => props.alertRows.filter((item) => item.state === '待处理').length)

const alertFeedKicker = computed(() => {
  const pending = props.alertRows.filter((item) => item.state === '待处理').length
  return pending > 0 ? '待办' : '关注'
})

const alertFeedTitle = computed(() => {
  const pending = props.alertRows.filter((item) => item.state === '待处理').length
  return pending > 0 ? '今天要处理的商品' : '今天观察的商品'
})

const alertFeedCountLabel = computed(() => {
  const pending = props.alertRows.filter((item) => item.state === '待处理').length
  return pending > 0 ? `${pending} 条待处理` : `${props.alertRows.length} 条观察`
})

const alertSummaryPills = computed(() => {
  const pending = props.alertRows.filter((item) => item.state === '待处理').length
  const up = props.alertRows.filter((item) => item.tone === 'up').length
  const down = props.alertRows.filter((item) => item.tone === 'down').length
  return [
    { label: '待处理', value: String(pending), tone: 'pending' },
    { label: '上涨', value: String(up), tone: 'up' },
    { label: '下跌', value: String(down), tone: 'down' },
  ]
})

const alertThresholdLabel = computed(() => {
  const lower = Number(ruleDraft.value.minPrice || 0)
  const upper = Number(ruleDraft.value.maxPrice || 0)
  if (lower > 0 && upper > 0) return `${lower.toFixed(2)} - ${upper.toFixed(2)}`
  if (upper > 0) return `>= ${upper.toFixed(2)}`
  if (lower > 0) return `<= ${lower.toFixed(2)}`
  return '未设置'
})

function handleAlertImageError(url: string | null | undefined) {
  const normalizedUrl = String(url || '').trim()
  if (!normalizedUrl) return
  brokenAlertImageUrls.add(normalizedUrl)
}
</script>

<style scoped>
.market-mobile-alert-page {
  display: grid;
  gap: 12px;
  padding: 0 0 calc(72px + env(safe-area-inset-bottom));
}

.market-mobile-alert-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  min-height: 96px;
  padding: 16px;
  border: 1px solid rgba(203, 213, 225, 0.72);
  border-radius: 22px;
  background:
    radial-gradient(circle at 90% 0%, rgba(96, 165, 250, 0.16), transparent 34%),
    linear-gradient(135deg, #f6f9ff 0%, #ffffff 56%, #f8fafc 100%);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}

.market-mobile-alert-hero div {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.market-mobile-alert-hero h2 {
  margin: 0;
  color: #0f172a;
  font-size: 20px;
  line-height: 1.12;
  letter-spacing: 0;
}

.market-mobile-alert-hero span {
  color: #475569;
  font-size: 12px;
  line-height: 1.45;
}

.market-mobile-alert-hero > strong {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 62px;
  height: 62px;
  border-radius: 20px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  font-size: 28px;
  line-height: 1;
  box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
}

.market-mobile-alert-hero > strong::after {
  content: "待处理";
  margin-top: 3px;
  color: rgba(255, 255, 255, 0.82);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0;
}

.market-mobile-alert-pills {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.market-mobile-alert-pills article {
  min-width: 0;
  padding: 10px 11px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
}

.market-mobile-alert-pills strong,
.market-mobile-alert-pills span {
  display: block;
}

.market-mobile-alert-pills strong {
  color: #0f172a;
  font-size: 18px;
  line-height: 1;
}

.market-mobile-alert-pills span {
  margin-top: 5px;
  color: currentColor;
  font-size: 10px;
  font-weight: 700;
}

.market-mobile-alert-pills .up strong { color: #dc2626; }
.market-mobile-alert-pills .down strong { color: #16a34a; }

.market-mobile-alert-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

.market-mobile-alert-list {
  display: grid;
  gap: 10px;
}

.market-mobile-alert-row {
  position: relative;
  display: grid;
  gap: 8px;
  min-width: 0;
  padding: 12px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
}

.market-mobile-alert-row::before {
  content: "";
  position: absolute;
  inset: 12px auto 12px 0;
  width: 4px;
  border-radius: 999px;
  background: #f97316;
}

.market-mobile-alert-row.up::before { background: #ef4444; }
.market-mobile-alert-row.down::before { background: #16a34a; }

.market-mobile-alert-row-main {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.market-mobile-alert-thumb-shell {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  overflow: hidden;
  border-radius: 15px;
  background: linear-gradient(145deg, #f8fafc, #eef4ff);
  box-shadow: inset 0 0 0 1px rgba(219, 234, 254, 0.95);
}

.market-mobile-alert-thumb-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: zoom-in;
}

.market-mobile-alert-row .market-mobile-thumb {
  width: 32px;
  height: 32px;
  border-radius: 10px;
}

.market-mobile-alert-row-main div {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.market-mobile-alert-row strong {
  overflow: hidden;
  color: #0f172a;
  font-size: 15px;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.market-mobile-alert-row small,
.market-mobile-alert-row p,
.market-mobile-alert-row time {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.35;
}

.market-mobile-alert-row small,
.market-mobile-alert-row p {
  display: -webkit-box;
  overflow: hidden;
  white-space: normal;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.market-mobile-alert-row p {
  padding-left: 2px;
  color: #334155;
  font-weight: 700;
}

.market-mobile-alert-row em {
  justify-self: end;
  max-width: 72px;
  padding: 6px 9px;
  border-radius: 999px;
  background: #fff7ed;
  color: #f97316;
  font-size: 11px;
  font-style: normal;
  font-weight: 900;
  line-height: 1;
  white-space: nowrap;
}

.market-mobile-alert-row.down em {
  background: #ecfdf5;
  color: #16a34a;
}

.market-mobile-alert-row.up em {
  background: #fef2f2;
  color: #dc2626;
}

.market-mobile-alert-row footer {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  align-items: center;
}

.market-mobile-alert-row button {
  min-width: 0;
  min-height: 44px;
  padding: 0 8px;
  border: 1px solid #dbe4ef;
  border-radius: 12px;
  background: #fff;
  color: #1e40af;
  font: inherit;
  font-size: 12px;
  font-weight: 900;
  touch-action: manipulation;
}

.market-mobile-alert-row button.primary {
  border-color: transparent;
  background: #2563eb;
  color: #fff;
}

.market-mobile-alert-row time {
  grid-column: 1 / -1;
  justify-self: end;
  color: #94a3b8;
  font-size: 11px;
}

.market-mobile-alert-empty {
  display: grid;
  gap: 5px;
  min-height: 76px;
  padding: 14px;
  border: 1px dashed rgba(96, 165, 250, 0.35);
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.92), rgba(255, 255, 255, 0.98));
}

.market-mobile-alert-empty strong {
  color: #0f172a;
  font-size: 14px;
  line-height: 1.25;
}

.market-mobile-alert-empty p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.market-mobile-alert-rule-card.collapsed {
  gap: 8px;
  box-shadow: none;
}

.market-mobile-rule-toggle {
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: 999px;
  background: #eff6ff;
  color: #2563eb;
  font: inherit;
  font-size: 12px;
  font-weight: 900;
  touch-action: manipulation;
}

.market-mobile-rule-summary {
  margin: 0;
  padding: 12px 14px;
  border: 1px dashed rgba(96, 165, 250, 0.28);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.9), rgba(255, 255, 255, 0.96));
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.market-mobile-rule-form {
  display: grid;
  gap: 8px;
  max-height: min(58vh, 430px);
  overflow-y: auto;
  padding-bottom: 6px;
  overscroll-behavior: contain;
}

.market-mobile-rule-form label {
  display: grid;
  grid-template-columns: 60px minmax(0, 1fr);
  align-items: center;
  min-height: 44px;
  padding: 0 12px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 14px;
  background: #fbfdff;
}

.market-mobile-rule-form span {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.market-mobile-rule-form strong {
  overflow: hidden;
  color: #0f172a;
  font-size: 13px;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.market-mobile-rule-form select,
.market-mobile-rule-form input {
  width: 100%;
  min-width: 0;
  border: none;
  background: transparent;
  color: #0f172a;
  font: inherit;
  font-size: 13px;
  line-height: 1.25;
  outline: none;
}

.market-mobile-rule-form button {
  position: sticky;
  bottom: 0;
  min-height: 48px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  font: inherit;
  font-size: 14px;
  font-weight: 900;
}

:deep(.market-mobile-kicker) {
  margin: 0;
  color: #2563eb;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0;
}

:deep(.market-mobile-section-head) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
}

:deep(.market-mobile-section-head h2) {
  margin: 0;
  color: #0f172a;
  font-size: 17px;
  line-height: 1.2;
  letter-spacing: 0;
}

:deep(.market-mobile-section-head > span) {
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}
</style>
