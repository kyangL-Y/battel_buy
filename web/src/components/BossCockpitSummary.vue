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
  subtitle: '先读取真实经营信号，再决定是否深挖价格细节。',
  riskLabel: '等待信号',
  riskTone: 'stable',
  riskNote: '暂无经营信号',
  noteSummary: '当前暂无真实经营摘要，请先刷新行情或检查同步状态。',
})

const fallbackKpis: BossKpi[] = [
  { label: '经营信号', value: '0 条', detail: '等待同步', emphasis: true },
  { label: '风险商品', value: '0 项', detail: '暂无真实风险' },
  { label: '机会商品', value: '0 项', detail: '暂无真实机会' },
  { label: '建议动作', value: '0 件', detail: '暂无真实建议' },
]

const fallbackFocusItems: FocusItem[] = [
  { title: '等待真实信号', summary: '同步到经营信号后会显示需要优先关注的商品和动作。', owner: '系统' },
]

const fallbackDecisionPoints: DecisionPoint[] = [
  { title: '今日动作', value: '暂无', detail: '等待真实建议' },
  { title: '风险判断', value: '暂无', detail: '等待真实信号' },
  { title: '采购承接', value: '暂无', detail: '等待菜单或报价数据' },
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
