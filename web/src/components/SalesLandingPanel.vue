<template>
  <section class="panel sales-landing-panel">
    <div class="panel-header">
      <div>
        <p class="panel-kicker">{{ kicker }}</p>
        <h2>{{ title }}</h2>
        <p class="panel-hint">{{ subtitle }}</p>
      </div>
      <div class="landing-context-chip">
        <span>当前重点</span>
        <strong>{{ focusLabel }}</strong>
        <small>{{ refreshLabel }}</small>
      </div>
    </div>

    <div class="landing-hero">
      <div class="landing-hero-copy">
        <strong>{{ heroTitle }}</strong>
        <p>{{ heroSummary }}</p>
      </div>
      <div class="landing-hero-actions">
        <div
          v-for="metric in resolvedHeroMetrics"
          :key="metric.label"
          class="summary-card compact-summary-card landing-hero-metric"
          :class="metric.tone ? `is-${metric.tone}` : ''"
        >
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
          <small>{{ metric.detail }}</small>
        </div>
      </div>
    </div>

    <div class="landing-grid">
      <article v-for="item in resolvedQuickWins" :key="item.title" class="landing-card landing-quick-card">
        <div class="landing-card-head">
          <strong>{{ item.title }}</strong>
          <span>{{ item.tag }}</span>
        </div>
        <p>{{ item.summary }}</p>
        <small>{{ item.detail }}</small>
      </article>

      <article v-for="item in resolvedActionCards" :key="item.title" class="landing-card landing-action-card">
        <div class="landing-card-head">
          <strong>{{ item.title }}</strong>
          <span>{{ item.badge }}</span>
        </div>
        <p>{{ item.caption }}</p>
        <div class="landing-action-footer">
          <em>{{ item.emphasis }}</em>
          <small>{{ item.footnote }}</small>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface LandingMetric {
  label: string
  value: string
  detail: string
  tone?: 'default' | 'good' | 'warn'
}

interface LandingCard {
  title: string
  tag: string
  summary: string
  detail: string
}

interface LandingActionCard {
  title: string
  badge: string
  caption: string
  emphasis: string
  footnote: string
}

const props = withDefaults(defineProps<{
  kicker?: string
  title?: string
  subtitle?: string
  focusLabel?: string
  refreshLabel?: string
  heroTitle?: string
  heroSummary?: string
  heroMetrics?: LandingMetric[]
  quickWins?: LandingCard[]
  actionCards?: LandingActionCard[]
}>(), {
  kicker: '经营首页',
  title: '真实行情承接',
  subtitle: '首屏只展示真实行情、经营信号和采购承接信息。',
  focusLabel: '真实数据',
  refreshLabel: '等待同步',
  heroTitle: '行情、信号、采购动作在同一屏承接',
  heroSummary: '基于真实同步的数据先讲风险和机会，再进入采购或供应商报价。',
})

const fallbackHeroMetrics: LandingMetric[] = [
  { label: '行情记录', value: '0 条', detail: '等待同步', tone: 'default' },
  { label: '经营信号', value: '0 条', detail: '等待同步', tone: 'default' },
  { label: '采购建议', value: '0 条', detail: '等待同步', tone: 'default' },
]

const fallbackQuickWins: LandingCard[] = [
  { title: '等待真实机会', tag: '经营信号', summary: '同步到机会信号后会展示可执行动作。', detail: '暂无真实机会。' },
  { title: '等待真实风险', tag: '经营信号', summary: '同步到风险信号后会展示采购或报价建议。', detail: '暂无真实风险。' },
]

const fallbackActionCards: LandingActionCard[] = [
  { title: '老板摘要', badge: '真实信号', caption: '等待经营信号摘要。', emphasis: '暂无动作', footnote: '刷新后重试' },
  { title: '采购承接', badge: '真实建议', caption: '等待菜单采购或供应商报价建议。', emphasis: '暂无动作', footnote: '刷新后重试' },
  { title: '供应商承接', badge: '真实报价', caption: '等待供应商报价记录。', emphasis: '暂无动作', footnote: '刷新后重试' },
]

const resolvedHeroMetrics = computed(() => props.heroMetrics?.length ? props.heroMetrics : fallbackHeroMetrics)
const resolvedQuickWins = computed(() => props.quickWins?.length ? props.quickWins : fallbackQuickWins)
const resolvedActionCards = computed(() => props.actionCards?.length ? props.actionCards : fallbackActionCards)
</script>

<style scoped>
.sales-landing-panel {
  display: grid;
  gap: 16px;
  padding: 18px;
  border-color: var(--border-soft);
  background: var(--surface-card-soft);
}

.landing-context-chip,
.landing-card {
  border: 1px solid var(--border-soft);
  background: var(--surface-card);
  box-shadow: var(--shadow-card);
}

.landing-context-chip {
  display: grid;
  gap: 3px;
  min-width: 156px;
  padding: 12px 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
}

.landing-context-chip span,
.landing-context-chip small,
.landing-card span,
.landing-card small {
  color: var(--ink-500);
  font-size: 11px;
}

.landing-context-chip strong,
.landing-card strong {
  color: var(--ink-900);
}

.landing-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
  gap: 16px;
  min-height: 220px;
  padding: 20px;
  overflow: hidden;
  border-radius: var(--radius-card);
  border: 1px solid var(--border-soft);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94)),
    linear-gradient(135deg, rgba(37, 99, 235, 0.05), transparent);
  box-shadow: var(--shadow-card);
}

.landing-hero::after {
  content: "";
  position: absolute;
  right: 18px;
  top: 18px;
  width: 96px;
  height: 96px;
  border-radius: 28px;
  border: 1px solid rgba(96, 165, 250, 0.14);
  background: rgba(239, 246, 255, 0.52);
  transform: rotate(10deg);
}

.landing-hero-copy {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 12px;
  align-content: center;
}

.landing-hero-copy strong {
  max-width: 560px;
  color: #ffffff;
  font-size: clamp(28px, 4vw, 44px);
  line-height: 1.05;
  letter-spacing: -0.06em;
}

.landing-hero-copy p,
.landing-card p {
  margin: 0;
  line-height: 1.65;
}

.landing-hero-copy p {
  max-width: 520px;
  color: rgba(239, 246, 255, 0.86);
  font-size: 14px;
}

.landing-card p {
  color: var(--ink-700);
  font-size: 13px;
}

.landing-hero-actions,
.landing-grid {
  display: grid;
  gap: 12px;
}

.landing-hero-actions {
  position: relative;
  z-index: 1;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-content: end;
}

.landing-hero-metric {
  min-height: 108px;
  border-color: var(--border-soft);
  background: var(--surface-card);
  box-shadow: none;
}

.landing-hero-metric span,
.landing-hero-metric small {
  color: var(--ink-500);
}

.landing-hero-metric strong {
  color: var(--ink-900);
}

.landing-hero-metric.is-good::before {
  background: var(--accent-emerald);
}

.landing-hero-metric.is-warn::before {
  background: var(--accent-amber);
}

.landing-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.landing-quick-card,
.landing-action-card {
  grid-column: auto;
}

.landing-card {
  display: grid;
  gap: 12px;
  min-height: 152px;
  padding: 16px;
  border-radius: 20px;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.landing-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-brand-soft);
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.1);
}

.landing-card-head,
.landing-action-footer {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.landing-card-head span,
.landing-action-footer em {
  width: fit-content;
  padding: 5px 9px;
  border-radius: 999px;
  background: var(--surface-brand-soft);
  color: var(--accent-blue);
  font-size: 10px;
  font-style: normal;
  font-weight: 700;
}

.landing-action-card .landing-card-head span {
  background: rgba(254, 243, 199, 0.86);
  color: #a16207;
}

.landing-action-footer {
  align-items: center;
}

.landing-action-footer small {
  text-align: right;
}

@media (max-width: 1100px) {
  .landing-hero,
  .landing-grid,
  .landing-hero-actions {
    grid-template-columns: 1fr;
  }

  .landing-quick-card,
  .landing-action-card {
    grid-column: auto;
  }
}

@media (max-width: 720px) {
  .sales-landing-panel {
    padding: 14px;
    gap: 12px;
  }

  .landing-context-chip,
  .landing-card {
    border-radius: 16px;
  }

  .landing-hero {
    min-height: 0;
    padding: 18px;
    border-radius: 22px;
  }

  .landing-hero-copy strong {
    font-size: 26px;
  }

  .landing-hero-actions {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .landing-hero-metric {
    min-height: 92px;
    padding: 10px;
  }

  .landing-card-head,
  .landing-action-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .landing-action-footer small {
    text-align: left;
  }
}
</style>
