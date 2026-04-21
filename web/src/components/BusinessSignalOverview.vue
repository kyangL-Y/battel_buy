<template>
  <section class="panel business-signal-panel">
    <div class="panel-header">
      <div>
        <p class="panel-kicker">{{ kicker }}</p>
        <h2>{{ title }}</h2>
        <p class="panel-hint">{{ subtitle }}</p>
      </div>
      <div class="business-signal-meta">
        <span>观察窗</span>
        <strong>{{ windowLabel }}</strong>
        <small>{{ reviewLabel }}</small>
      </div>
    </div>

    <div class="signal-card-grid">
      <article
        v-for="item in resolvedSignals"
        :key="item.title"
        class="signal-card"
        :class="`is-${item.severity}`"
      >
        <div class="signal-card-head">
          <span>{{ item.title }}</span>
          <em :class="`is-${item.trend}`">{{ item.changeLabel }}</em>
        </div>
        <strong>{{ item.value }}</strong>
        <p>{{ item.detail }}</p>
      </article>
    </div>

    <div class="signal-alert-shell">
      <div class="signal-alert-head">
        <strong>经营信号</strong>
        <span>{{ resolvedAlerts.length }} 条轻提醒</span>
      </div>
      <div v-if="resolvedAlerts.length" class="signal-alert-list">
        <div v-for="item in resolvedAlerts" :key="item.title" class="signal-alert-item">
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.detail }}</p>
          </div>
          <small>{{ item.owner }}</small>
        </div>
      </div>
      <div v-else class="table-empty-state signal-empty-state">
        <strong>当前没有需要提醒的经营信号</strong>
        <p>可直接承接到销售首页或老板摘要，不需要硬塞一整块大预警区。</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface BusinessSignal {
  title: string
  value: string
  changeLabel: string
  detail: string
  trend: 'up' | 'down' | 'flat'
  severity: 'good' | 'watch' | 'risk'
}

interface SignalAlert {
  title: string
  detail: string
  owner: string
}

const props = withDefaults(defineProps<{
  kicker?: string
  title?: string
  subtitle?: string
  windowLabel?: string
  reviewLabel?: string
  signals?: BusinessSignal[]
  alerts?: SignalAlert[]
}>(), {
  kicker: '经营信号',
  title: '今日经营概览',
  subtitle: '控制信息密度，每张卡只表达一个判断，适合直接做晨会或老板驾驶舱中段。',
  windowLabel: '近 7 天',
  reviewLabel: '每天 09:00 / 15:00 复核',
})

const fallbackSignals: BusinessSignal[] = [
  { title: '采购成本波动', value: '+3.8%', changeLabel: '较昨日上行', detail: '集中在高频蔬菜，不建议全品类同步调价。', trend: 'up', severity: 'watch' },
  { title: '报价成交率', value: '31%', changeLabel: '本周改善', detail: '套餐化表达后，客户反馈更容易理解。', trend: 'up', severity: 'good' },
  { title: '缺货暴露度', value: '2 类', changeLabel: '需盯防', detail: '若今晚不锁量，明日交付稳定性会下降。', trend: 'flat', severity: 'risk' },
  { title: '替代品可用度', value: '4 套', changeLabel: '可执行', detail: '已有替代组合，可在报价页直接展示。', trend: 'up', severity: 'good' },
  { title: '老板查看频次', value: '9 次', changeLabel: '本周新增', detail: '摘要页比明细页更容易被重复打开。', trend: 'up', severity: 'good' },
  { title: '异常来源占比', value: '12%', changeLabel: '需继续压降', detail: '仍有少量来源需要人工判读，不宜直接透出给客户。', trend: 'down', severity: 'watch' },
]

const fallbackAlerts: SignalAlert[] = [
  { title: '套餐 B 可作为成交主推', detail: '价格解释更顺，且能覆盖当前客户最在意的 3 个食材。', owner: '销售' },
  { title: '明晨前锁定高频品采购量', detail: '若今晚不锁量，明天同城报价可能出现临时抬价。', owner: '采购' },
  { title: '驾驶舱摘要建议缩成 1 屏', detail: '老板页面不宜超过 6 张核心卡，剩余信息收进轻提醒。', owner: '产品' },
]

const resolvedSignals = computed(() => props.signals?.length ? props.signals : fallbackSignals)
const resolvedAlerts = computed(() => props.alerts?.length ? props.alerts : fallbackAlerts)
</script>

<style scoped>
.business-signal-panel,
.signal-card-grid,
.signal-alert-shell,
.signal-alert-list {
  display: grid;
  gap: 12px;
}

.business-signal-meta,
.signal-card,
.signal-alert-item {
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(248, 250, 252, 0.88);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.business-signal-meta {
  display: grid;
  gap: 3px;
  min-width: 164px;
  padding: 12px 14px;
  border-radius: 16px;
}

.business-signal-meta span,
.business-signal-meta small,
.signal-card span,
.signal-card p,
.signal-alert-item p,
.signal-alert-item small {
  color: var(--ink-500);
  font-size: 11px;
}

.signal-card-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.signal-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 18px;
}

.signal-card-head,
.signal-alert-head,
.signal-alert-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.signal-card strong,
.signal-alert-item strong {
  color: var(--ink-900);
}

.signal-card strong {
  font-size: 19px;
  line-height: 1.1;
}

.signal-card p,
.signal-alert-item p {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
}

.signal-card em {
  width: fit-content;
  padding: 5px 8px;
  border-radius: 999px;
  font-style: normal;
  font-size: 10px;
  font-weight: 600;
}

.signal-card.is-good {
  background: rgba(236, 253, 245, 0.9);
}

.signal-card.is-watch {
  background: rgba(255, 251, 235, 0.92);
}

.signal-card.is-risk {
  background: rgba(254, 242, 242, 0.94);
}

.signal-card em.is-up {
  background: rgba(219, 234, 254, 0.92);
  color: var(--accent-blue);
}

.signal-card em.is-down {
  background: rgba(220, 252, 231, 0.92);
  color: var(--accent-emerald);
}

.signal-card em.is-flat {
  background: rgba(241, 245, 249, 0.94);
  color: var(--ink-700);
}

.signal-alert-shell {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(255, 255, 255, 0.82);
}

.signal-alert-head span {
  color: var(--ink-500);
  font-size: 11px;
}

.signal-alert-item {
  padding: 12px;
  border-radius: 14px;
}

.signal-empty-state {
  min-height: 180px;
}

@media (max-width: 1100px) {
  .signal-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .signal-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .signal-card,
  .signal-alert-shell {
    padding: 12px;
    border-radius: 14px;
  }

  .signal-card strong {
    font-size: 15px;
  }

  .signal-card p,
  .signal-alert-item p,
  .signal-alert-item small,
  .business-signal-meta span,
  .business-signal-meta small {
    font-size: 10px;
    line-height: 1.4;
  }

  .signal-alert-head,
  .signal-alert-item {
    flex-direction: column;
    align-items: stretch;
  }

  .signal-alert-shell,
  .signal-card,
  .business-signal-meta {
    border-radius: 16px;
  }
}

@media (max-width: 360px) {
  .signal-card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
