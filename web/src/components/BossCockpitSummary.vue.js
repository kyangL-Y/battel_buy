/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/props-fallback.d.ts" />
import { computed } from 'vue';
const props = withDefaults(defineProps(), {
    kicker: '老板驾驶舱',
    title: '今日经营摘要',
    subtitle: '先读取真实经营信号，再决定是否深挖价格细节。',
    riskLabel: '等待信号',
    riskTone: 'stable',
    riskNote: '经营信号接口暂无返回',
    noteSummary: '当前暂无真实经营摘要，请先刷新行情或检查经营信号接口。',
});
const fallbackKpis = [
    { label: '经营信号', value: '0 条', detail: '等待接口返回', emphasis: true },
    { label: '风险商品', value: '0 项', detail: '暂无真实风险' },
    { label: '机会商品', value: '0 项', detail: '暂无真实机会' },
    { label: '建议动作', value: '0 件', detail: '暂无真实建议' },
];
const fallbackFocusItems = [
    { title: '等待真实信号', summary: '经营信号接口返回后会显示需要优先关注的商品和动作。', owner: '系统' },
];
const fallbackDecisionPoints = [
    { title: '今日动作', value: '暂无', detail: '等待真实建议' },
    { title: '风险判断', value: '暂无', detail: '等待真实信号' },
    { title: '采购承接', value: '暂无', detail: '等待菜单或报价数据' },
];
const resolvedKpis = computed(() => props.kpis?.length ? props.kpis : fallbackKpis);
const resolvedFocusItems = computed(() => props.focusItems?.length ? props.focusItems : fallbackFocusItems);
const resolvedDecisionPoints = computed(() => props.decisionPoints?.length ? props.decisionPoints : fallbackDecisionPoints);
const __VLS_defaults = {
    kicker: '老板驾驶舱',
    title: '今日经营摘要',
    subtitle: '先读取真实经营信号，再决定是否深挖价格细节。',
    riskLabel: '等待信号',
    riskTone: 'stable',
    riskNote: '经营信号接口暂无返回',
    noteSummary: '当前暂无真实经营摘要，请先刷新行情或检查经营信号接口。',
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
