/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/props-fallback.d.ts" />
import { computed } from 'vue';
const props = withDefaults(defineProps(), {
    kicker: '老板驾驶舱',
    title: '今日经营摘要',
    subtitle: '更像汇报页，不像分析页。默认先给结果，再决定是否深挖价格细节。',
    riskLabel: '可控偏紧',
    riskTone: 'watch',
    riskNote: '波动集中在高频食材',
    noteSummary: '今天的重点不是看更多数据，而是把高波动商品控制在采购可解释范围内，避免销售现场回答“为什么这周又贵了”。',
});
const fallbackKpis = [
    { label: '预计采购额', value: '12.8 万', detail: '较昨日 +6.4%', emphasis: true },
    { label: '毛利安全垫', value: '8.7%', detail: '仍高于预警线 1.2pct' },
    { label: '关键缺货风险', value: '2 项', detail: '需提前锁量' },
    { label: '今日需拍板', value: '3 件', detail: '套餐报价与替代品' },
];
const fallbackFocusItems = [
    { title: '高频叶菜波动偏快', summary: '若继续上涨，建议今晚前确认替代组合，不要等到明早配送前再改。', owner: '采购' },
    { title: '套餐报价已具备解释力', summary: '已有足够素材支撑“为什么不是最低价”，适合销售直接带老板过一遍。', owner: '销售' },
    { title: '冷链品类仍有让利空间', summary: '若今日促单，优先给出高频品和稳价品的组合包，而非全面降价。', owner: '运营' },
];
const fallbackDecisionPoints = [
    { title: '今日动作', value: '先锁高频品', detail: '先稳供应再谈结构优化' },
    { title: '客户话术', value: '讲稳定性', detail: '不只讲单次低价' },
    { title: '销售承接', value: '推老板版', detail: '先给摘要再给明细' },
];
const resolvedKpis = computed(() => props.kpis?.length ? props.kpis : fallbackKpis);
const resolvedFocusItems = computed(() => props.focusItems?.length ? props.focusItems : fallbackFocusItems);
const resolvedDecisionPoints = computed(() => props.decisionPoints?.length ? props.decisionPoints : fallbackDecisionPoints);
const __VLS_defaults = {
    kicker: '老板驾驶舱',
    title: '今日经营摘要',
    subtitle: '更像汇报页，不像分析页。默认先给结果，再决定是否深挖价格细节。',
    riskLabel: '可控偏紧',
    riskTone: 'watch',
    riskNote: '波动集中在高频食材',
    noteSummary: '今天的重点不是看更多数据，而是把高波动商品控制在采购可解释范围内，避免销售现场回答“为什么这周又贵了”。',
};
const __VLS_ctx = {
    ...{},
    ...{},
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_intrinsics;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['boss-risk-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-risk-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-risk-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-note-point']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-note-point']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-focus-item']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-risk-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-risk-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-risk-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-risk-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-focus-item']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-note-point']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-kpi-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-kpi-card']} */ ;
/** @type {__VLS_StyleScopedClasses['is-emphasis']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-main-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-focus-card']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-section-head']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-focus-item']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-focus-item']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-note-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-note-point']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-kpi-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-main-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-note-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-risk-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-focus-card']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-focus-item']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    ...{ class: "panel boss-cockpit-panel" },
});
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-cockpit-panel']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "panel-header" },
});
/** @type {__VLS_StyleScopedClasses['panel-header']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "panel-kicker" },
});
/** @type {__VLS_StyleScopedClasses['panel-kicker']} */ ;
(__VLS_ctx.kicker);
__VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
(__VLS_ctx.title);
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "panel-hint" },
});
/** @type {__VLS_StyleScopedClasses['panel-hint']} */ ;
(__VLS_ctx.subtitle);
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "boss-risk-chip" },
    ...{ class: (`is-${__VLS_ctx.riskTone}`) },
});
/** @type {__VLS_StyleScopedClasses['boss-risk-chip']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
(__VLS_ctx.riskLabel);
__VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
(__VLS_ctx.riskNote);
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "boss-kpi-grid" },
});
/** @type {__VLS_StyleScopedClasses['boss-kpi-grid']} */ ;
for (const [item] of __VLS_vFor((__VLS_ctx.resolvedKpis))) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        key: (item.label),
        ...{ class: "summary-card compact-summary-card boss-kpi-card" },
        ...{ class: (item.emphasis ? 'is-emphasis' : '') },
    });
    /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
    /** @type {__VLS_StyleScopedClasses['compact-summary-card']} */ ;
    /** @type {__VLS_StyleScopedClasses['boss-kpi-card']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (item.label);
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (item.value);
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    (item.detail);
    // @ts-ignore
    [kicker, title, subtitle, riskTone, riskLabel, riskNote, resolvedKpis,];
}
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "boss-main-grid" },
});
/** @type {__VLS_StyleScopedClasses['boss-main-grid']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
    ...{ class: "boss-focus-card" },
});
/** @type {__VLS_StyleScopedClasses['boss-focus-card']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "boss-section-head" },
});
/** @type {__VLS_StyleScopedClasses['boss-section-head']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
(__VLS_ctx.resolvedFocusItems.length);
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "boss-focus-list" },
});
/** @type {__VLS_StyleScopedClasses['boss-focus-list']} */ ;
for (const [item] of __VLS_vFor((__VLS_ctx.resolvedFocusItems))) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        key: (item.title),
        ...{ class: "boss-focus-item" },
    });
    /** @type {__VLS_StyleScopedClasses['boss-focus-item']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (item.title);
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
    (item.summary);
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    (item.owner);
    // @ts-ignore
    [resolvedFocusItems, resolvedFocusItems,];
}
__VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
    ...{ class: "boss-focus-card boss-note-card" },
});
/** @type {__VLS_StyleScopedClasses['boss-focus-card']} */ ;
/** @type {__VLS_StyleScopedClasses['boss-note-card']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "boss-section-head" },
});
/** @type {__VLS_StyleScopedClasses['boss-section-head']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "boss-note-copy" },
});
/** @type {__VLS_StyleScopedClasses['boss-note-copy']} */ ;
(__VLS_ctx.noteSummary);
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "boss-note-grid" },
});
/** @type {__VLS_StyleScopedClasses['boss-note-grid']} */ ;
for (const [point] of __VLS_vFor((__VLS_ctx.resolvedDecisionPoints))) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        key: (point.title),
        ...{ class: "boss-note-point" },
    });
    /** @type {__VLS_StyleScopedClasses['boss-note-point']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (point.title);
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (point.value);
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    (point.detail);
    // @ts-ignore
    [noteSummary, resolvedDecisionPoints,];
}
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({
    __typeProps: {},
    props: {},
});
export default {};
