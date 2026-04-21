<template>
  <section class="panel boss-cockpit-panel">
    <div class="panel-header">
      <div>
        <p class="panel-kicker">{{ kicker }}</p>
        <h2>{{ title }}</h2>
        <p class="panel-hint">{{ subtitle }}</p>
      </div>
      <div class="boss-risk-chip" :class="`is-${riskTone}`">
        <span>经营态势</span>
        <strong>{{ riskLabel }}</strong>
        <small>{{ riskNote }}</small>
      </div>
    </div>

    <div class="boss-kpi-grid">
      <div
        v-for="item in resolvedKpis"
        :key="item.label"
        class="summary-card compact-summary-card boss-kpi-card"
        :class="item.emphasis ? 'is-emphasis' : ''"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.detail }}</small>
      </div>
    </div>

    <div class="boss-main-grid">
      <article class="boss-focus-card">
        <div class="boss-section-head">
          <strong>今天先看</strong>
          <span>{{ resolvedFocusItems.length }} 项</span>
        </div>
        <div class="boss-focus-list">
          <div v-for="item in resolvedFocusItems" :key="item.title" class="boss-focus-item">
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.summary }}</p>
            </div>
            <small>{{ item.owner }}</small>
          </div>
        </div>
      </article>

      <article class="boss-focus-card boss-note-card">
        <div class="boss-section-head">
          <strong>老板摘要</strong>
          <span>一句话版</span>
        </div>
        <p class="boss-note-copy">{{ noteSummary }}</p>
        <div class="boss-note-grid">
          <div v-for="point in resolvedDecisionPoints" :key="point.title" class="boss-note-point">
            <span>{{ point.title }}</span>
            <strong>{{ point.value }}</strong>
            <small>{{ point.detail }}</small>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface BossKpi {
  label: string
  value: string
  detail: string
  emphasis?: boolean
}

interface FocusItem {
  title: string
  summary: string
  owner: string
}

interface DecisionPoint {
  title: string
  value: string
  detail: string
}

const props = withDefaults(defineProps<{
  kicker?: string
  title?: string
  subtitle?: string
  riskLabel?: string
  riskTone?: 'stable' | 'watch' | 'risk'
  riskNote?: string
  kpis?: BossKpi[]
  focusItems?: FocusItem[]
  noteSummary?: string
  decisionPoints?: DecisionPoint[]
}>(), {
  kicker: '老板驾驶舱',
  title: '今日经营摘要',
  subtitle: '更像汇报页，不像分析页。默认先给结果，再决定是否深挖价格细节。',
  riskLabel: '可控偏紧',
  riskTone: 'watch',
  riskNote: '波动集中在高频食材',
  noteSummary: '今天的重点不是看更多数据，而是把高波动商品控制在采购可解释范围内，避免销售现场回答“为什么这周又贵了”。',
})

const fallbackKpis: BossKpi[] = [
  { label: '预计采购额', value: '12.8 万', detail: '较昨日 +6.4%', emphasis: true },
  { label: '毛利安全垫', value: '8.7%', detail: '仍高于预警线 1.2pct' },
  { label: '关键缺货风险', value: '2 项', detail: '需提前锁量' },
  { label: '今日需拍板', value: '3 件', detail: '套餐报价与替代品' },
]

const fallbackFocusItems: FocusItem[] = [
  { title: '高频叶菜波动偏快', summary: '若继续上涨，建议今晚前确认替代组合，不要等到明早配送前再改。', owner: '采购' },
  { title: '套餐报价已具备解释力', summary: '已有足够素材支撑“为什么不是最低价”，适合销售直接带老板过一遍。', owner: '销售' },
  { title: '冷链品类仍有让利空间', summary: '若今日促单，优先给出高频品和稳价品的组合包，而非全面降价。', owner: '运营' },
]

const fallbackDecisionPoints: DecisionPoint[] = [
  { title: '今日动作', value: '先锁高频品', detail: '先稳供应再谈结构优化' },
  { title: '客户话术', value: '讲稳定性', detail: '不只讲单次低价' },
  { title: '销售承接', value: '推老板版', detail: '先给摘要再给明细' },
]

const resolvedKpis = computed(() => props.kpis?.length ? props.kpis : fallbackKpis)
const resolvedFocusItems = computed(() => props.focusItems?.length ? props.focusItems : fallbackFocusItems)
const resolvedDecisionPoints = computed(() => props.decisionPoints?.length ? props.decisionPoints : fallbackDecisionPoints)
</script>

<style scoped>
.boss-cockpit-panel,
.boss-main-grid,
.boss-kpi-grid,
.boss-note-grid,
.boss-focus-list {
  display: grid;
  gap: 12px;
}

.boss-risk-chip,
.boss-focus-card,
.boss-note-point,
.boss-focus-item {
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(248, 250, 252, 0.88);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.boss-risk-chip {
  display: grid;
  gap: 3px;
  min-width: 156px;
  padding: 12px 14px;
  border-radius: 16px;
}

.boss-risk-chip span,
.boss-risk-chip small,
.boss-note-point span,
.boss-note-point small,
.boss-focus-item small {
  color: var(--ink-500);
  font-size: 11px;
}

.boss-risk-chip.is-stable {
  background: rgba(209, 250, 229, 0.82);
}

.boss-risk-chip.is-watch {
  background: rgba(254, 243, 199, 0.82);
}

.boss-risk-chip.is-risk {
  background: rgba(254, 226, 226, 0.9);
}

.boss-risk-chip strong,
.boss-focus-item strong,
.boss-note-point strong {
  color: var(--ink-900);
}

.boss-kpi-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.boss-kpi-card.is-emphasis {
  background: rgba(239, 246, 255, 0.88);
}

.boss-kpi-card.is-emphasis::before {
  background: var(--accent-blue);
}

.boss-main-grid {
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
}

.boss-focus-card {
  padding: 14px;
  border-radius: 18px;
}

.boss-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.boss-section-head span {
  color: var(--ink-500);
  font-size: 11px;
}

.boss-focus-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-radius: 14px;
}

.boss-focus-item p,
.boss-note-copy {
  margin: 0;
  color: var(--ink-700);
  font-size: 13px;
  line-height: 1.6;
}

.boss-note-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 12px;
}

.boss-note-point {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: 14px;
}

@media (max-width: 1100px) {
  .boss-main-grid {
    grid-template-columns: 1fr;
  }

  .boss-kpi-grid,
  .boss-note-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .boss-risk-chip,
  .boss-focus-card {
    border-radius: 16px;
  }

  .boss-kpi-card,
  .boss-note-point {
    padding: 12px;
    border-radius: 14px;
  }

  .boss-kpi-card strong {
    font-size: 15px;
  }

  .boss-focus-item {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 360px) {
  .boss-kpi-grid,
  .boss-note-grid {
    grid-template-columns: 1fr;
  }
}
</style>
