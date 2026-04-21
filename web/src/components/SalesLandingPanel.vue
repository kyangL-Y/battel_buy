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
  kicker: '销售首页',
  title: '本周增长落点',
  subtitle: '首屏只保留老板愿意停留 30 秒的信息，避免用大面积空卡片堆砌“气势”。',
  focusLabel: '华东餐饮客户',
  refreshLabel: '刚刚更新',
  heroTitle: '报价、线索、老板摘要三件事放在同一屏完成承接',
  heroSummary: '适合接在真实行情之后做销售化承接，先讲窗口，再给动作，不把用户丢进过深的分析页。',
})

const fallbackHeroMetrics: LandingMetric[] = [
  { label: '本周可转化线索', value: '18 家', detail: '较上周 +4 家', tone: 'good' },
  { label: '报价进入决策', value: '6 单', detail: '老板已看到方案', tone: 'default' },
  { label: '需销售跟进', value: '3 单', detail: '集中在套餐比价', tone: 'warn' },
]

const fallbackQuickWins: LandingCard[] = [
  { title: '区域热度', tag: '机会窗口', summary: '团餐与酒楼客户对“每日价格波动”接受度更高，适合先推老板驾驶舱版。', detail: '先给看板，再补套餐。' },
  { title: '成交抓手', tag: '销售话术', summary: '当客户只问“今天多少钱”，建议顺势给 7 日均价和低价来源，而不是整页表格。', detail: '突出省心，不强调算法。' },
]

const fallbackActionCards: LandingActionCard[] = [
  { title: '老板先看版', badge: '摘要型', caption: '先看利润、风险和今天建议，再决定是否进入明细。', emphasis: '适合 1 分钟汇报', footnote: '优先承接已有客户复访' },
  { title: '套餐报价版', badge: '成交型', caption: '把行情解释转成可比较套餐，降低“看不懂数据”的阻力。', emphasis: '适合本周促单', footnote: '建议绑定 2 个清晰梯度' },
  { title: '经营信号版', badge: '预警型', caption: '用成本、缺货、波动三类信号提醒老板今天要不要改采购。', emphasis: '适合每日晨会', footnote: '不要超过 6 张信号卡' },
]

const resolvedHeroMetrics = computed(() => props.heroMetrics?.length ? props.heroMetrics : fallbackHeroMetrics)
const resolvedQuickWins = computed(() => props.quickWins?.length ? props.quickWins : fallbackQuickWins)
const resolvedActionCards = computed(() => props.actionCards?.length ? props.actionCards : fallbackActionCards)
</script>

<style scoped>
.sales-landing-panel {
  display: grid;
  gap: 14px;
}

.landing-context-chip,
.landing-card {
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(248, 250, 252, 0.86);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.landing-context-chip {
  display: grid;
  gap: 3px;
  min-width: 148px;
  padding: 12px 14px;
  border-radius: 16px;
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
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  gap: 12px;
  padding: 14px;
  border-radius: 20px;
  background:
    linear-gradient(135deg, rgba(30, 64, 175, 0.08), rgba(255, 255, 255, 0.88)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(241, 245, 249, 0.92));
  border: 1px solid rgba(96, 165, 250, 0.18);
}

.landing-hero-copy {
  display: grid;
  gap: 8px;
  align-content: start;
}

.landing-hero-copy strong {
  font-size: 20px;
  line-height: 1.25;
  letter-spacing: -0.03em;
}

.landing-hero-copy p,
.landing-card p {
  margin: 0;
  color: var(--ink-700);
  font-size: 13px;
  line-height: 1.6;
}

.landing-hero-actions,
.landing-grid {
  display: grid;
  gap: 10px;
}

.landing-hero-actions {
  grid-template-columns: repeat(3, minmax(0, 1fr));
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

.landing-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 18px;
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
  background: rgba(239, 246, 255, 0.92);
  color: var(--accent-blue);
  font-size: 10px;
  font-style: normal;
  font-weight: 600;
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
}

@media (max-width: 720px) {
  .landing-context-chip,
  .landing-card {
    border-radius: 16px;
  }

  .landing-hero {
    padding: 12px;
    border-radius: 18px;
  }

  .landing-hero-copy strong {
    font-size: 18px;
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
