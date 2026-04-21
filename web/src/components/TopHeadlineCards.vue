<template>
  <section class="headline-grid">
    <div class="headline-card primary-card">
      <span>报价商品</span>
      <strong>{{ marketRowCount }}</strong>
      <small>当前筛选结果</small>
    </div>
    <div class="headline-card accent-cyan soft-card">
      <span>最低价来源</span>
      <strong>{{ lowestPriceSignal }}</strong>
      <small>全表最低报价</small>
    </div>
    <div class="headline-card accent-emerald soft-card">
      <span>覆盖市场</span>
      <strong>{{ productSummary?.site_count ?? 0 }}</strong>
      <small>当前选中商品</small>
    </div>
    <div class="headline-card accent-amber soft-card">
      <span>采购估算</span>
      <strong>{{ menuTotalCostLabel }}</strong>
      <small>菜单测算</small>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  marketRowCount: number
  lowestPriceSignal: string
  productSummary: Record<string, any> | null
  menuTotalCostLabel: string
}>()
</script>
