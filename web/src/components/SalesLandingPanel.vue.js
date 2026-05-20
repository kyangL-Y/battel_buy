/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/props-fallback.d.ts" />
import { computed } from 'vue';
const props = withDefaults(defineProps(), {
    kicker: '经营首页',
    title: '真实行情承接',
    subtitle: '首屏只展示真实行情、经营信号和采购承接信息。',
    focusLabel: '真实数据',
    refreshLabel: '等待同步',
    heroTitle: '行情、信号、采购动作在同一屏承接',
    heroSummary: '基于真实接口返回的信息先讲风险和机会，再进入采购或供应商报价。',
});
const fallbackHeroMetrics = [
    { label: '行情记录', value: '0 条', detail: '等待接口返回', tone: 'default' },
    { label: '经营信号', value: '0 条', detail: '等待接口返回', tone: 'default' },
    { label: '采购建议', value: '0 条', detail: '等待接口返回', tone: 'default' },
];
const fallbackQuickWins = [
    { title: '等待真实机会', tag: '经营信号', summary: '接口返回机会信号后会展示可执行动作。', detail: '暂无真实机会。' },
    { title: '等待真实风险', tag: '经营信号', summary: '接口返回风险信号后会展示采购或报价建议。', detail: '暂无真实风险。' },
];
const fallbackActionCards = [
    { title: '老板摘要', badge: '真实信号', caption: '等待经营信号接口返回摘要。', emphasis: '暂无动作', footnote: '刷新后重试' },
    { title: '采购承接', badge: '真实建议', caption: '等待菜单采购或供应商报价接口返回建议。', emphasis: '暂无动作', footnote: '刷新后重试' },
    { title: '供应商承接', badge: '真实报价', caption: '等待供应商报价接口返回记录。', emphasis: '暂无动作', footnote: '刷新后重试' },
];
const resolvedHeroMetrics = computed(() => props.heroMetrics?.length ? props.heroMetrics : fallbackHeroMetrics);
const resolvedQuickWins = computed(() => props.quickWins?.length ? props.quickWins : fallbackQuickWins);
const resolvedActionCards = computed(() => props.actionCards?.length ? props.actionCards : fallbackActionCards);
const __VLS_defaults = {
    kicker: '经营首页',
    title: '真实行情承接',
    subtitle: '首屏只展示真实行情、经营信号和采购承接信息。',
    focusLabel: '真实数据',
    refreshLabel: '等待同步',
    heroTitle: '行情、信号、采购动作在同一屏承接',
    heroSummary: '基于真实接口返回的信息先讲风险和机会，再进入采购或供应商报价。',
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
/** @type {__VLS_StyleScopedClasses['landing-context-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-context-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-context-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-card']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-card']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-context-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-card']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-hero-copy']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-hero-copy']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-card']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-hero-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-hero-metric']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-card']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-card-head']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-action-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-card-head']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-action-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-action-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-hero']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-hero-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-context-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-card']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-hero']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-hero-copy']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-card-head']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-action-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-action-footer']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    ...{ class: "panel sales-landing-panel" },
});
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['sales-landing-panel']} */ ;
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
    ...{ class: "landing-context-chip" },
});
/** @type {__VLS_StyleScopedClasses['landing-context-chip']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
(__VLS_ctx.focusLabel);
__VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
(__VLS_ctx.refreshLabel);
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "landing-hero" },
});
/** @type {__VLS_StyleScopedClasses['landing-hero']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "landing-hero-copy" },
});
/** @type {__VLS_StyleScopedClasses['landing-hero-copy']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
(__VLS_ctx.heroTitle);
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
(__VLS_ctx.heroSummary);
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "landing-hero-actions" },
});
/** @type {__VLS_StyleScopedClasses['landing-hero-actions']} */ ;
for (const [metric] of __VLS_vFor((__VLS_ctx.resolvedHeroMetrics))) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        key: (metric.label),
        ...{ class: "summary-card compact-summary-card landing-hero-metric" },
        ...{ class: (metric.tone ? `is-${metric.tone}` : '') },
    });
    /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
    /** @type {__VLS_StyleScopedClasses['compact-summary-card']} */ ;
    /** @type {__VLS_StyleScopedClasses['landing-hero-metric']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (metric.label);
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (metric.value);
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    (metric.detail);
    // @ts-ignore
    [kicker, title, subtitle, focusLabel, refreshLabel, heroTitle, heroSummary, resolvedHeroMetrics,];
}
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "landing-grid" },
});
/** @type {__VLS_StyleScopedClasses['landing-grid']} */ ;
for (const [item] of __VLS_vFor((__VLS_ctx.resolvedQuickWins))) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
        key: (item.title),
        ...{ class: "landing-card landing-quick-card" },
    });
    /** @type {__VLS_StyleScopedClasses['landing-card']} */ ;
    /** @type {__VLS_StyleScopedClasses['landing-quick-card']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "landing-card-head" },
    });
    /** @type {__VLS_StyleScopedClasses['landing-card-head']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (item.title);
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (item.tag);
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
    (item.summary);
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    (item.detail);
    // @ts-ignore
    [resolvedQuickWins,];
}
for (const [item] of __VLS_vFor((__VLS_ctx.resolvedActionCards))) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
        key: (item.title),
        ...{ class: "landing-card landing-action-card" },
    });
    /** @type {__VLS_StyleScopedClasses['landing-card']} */ ;
    /** @type {__VLS_StyleScopedClasses['landing-action-card']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "landing-card-head" },
    });
    /** @type {__VLS_StyleScopedClasses['landing-card-head']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (item.title);
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (item.badge);
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
    (item.caption);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "landing-action-footer" },
    });
    /** @type {__VLS_StyleScopedClasses['landing-action-footer']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.em, __VLS_intrinsics.em)({});
    (item.emphasis);
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    (item.footnote);
    // @ts-ignore
    [resolvedActionCards,];
}
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({
    __typeProps: {},
    props: {},
});
export default {};
