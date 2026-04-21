/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/props-fallback.d.ts" />
import { computed } from 'vue';
const props = withDefaults(defineProps(), {
    kicker: '销售首页',
    title: '本周增长落点',
    subtitle: '首屏只保留老板愿意停留 30 秒的信息，避免用大面积空卡片堆砌“气势”。',
    focusLabel: '华东餐饮客户',
    refreshLabel: '刚刚更新',
    heroTitle: '报价、线索、老板摘要三件事放在同一屏完成承接',
    heroSummary: '适合接在真实行情之后做销售化承接，先讲窗口，再给动作，不把用户丢进过深的分析页。',
});
const fallbackHeroMetrics = [
    { label: '本周可转化线索', value: '18 家', detail: '较上周 +4 家', tone: 'good' },
    { label: '报价进入决策', value: '6 单', detail: '老板已看到方案', tone: 'default' },
    { label: '需销售跟进', value: '3 单', detail: '集中在套餐比价', tone: 'warn' },
];
const fallbackQuickWins = [
    { title: '区域热度', tag: '机会窗口', summary: '团餐与酒楼客户对“每日价格波动”接受度更高，适合先推老板驾驶舱版。', detail: '先给看板，再补套餐。' },
    { title: '成交抓手', tag: '销售话术', summary: '当客户只问“今天多少钱”，建议顺势给 7 日均价和低价来源，而不是整页表格。', detail: '突出省心，不强调算法。' },
];
const fallbackActionCards = [
    { title: '老板先看版', badge: '摘要型', caption: '先看利润、风险和今天建议，再决定是否进入明细。', emphasis: '适合 1 分钟汇报', footnote: '优先承接已有客户复访' },
    { title: '套餐报价版', badge: '成交型', caption: '把行情解释转成可比较套餐，降低“看不懂数据”的阻力。', emphasis: '适合本周促单', footnote: '建议绑定 2 个清晰梯度' },
    { title: '经营信号版', badge: '预警型', caption: '用成本、缺货、波动三类信号提醒老板今天要不要改采购。', emphasis: '适合每日晨会', footnote: '不要超过 6 张信号卡' },
];
const resolvedHeroMetrics = computed(() => props.heroMetrics?.length ? props.heroMetrics : fallbackHeroMetrics);
const resolvedQuickWins = computed(() => props.quickWins?.length ? props.quickWins : fallbackQuickWins);
const resolvedActionCards = computed(() => props.actionCards?.length ? props.actionCards : fallbackActionCards);
const __VLS_defaults = {
    kicker: '销售首页',
    title: '本周增长落点',
    subtitle: '首屏只保留老板愿意停留 30 秒的信息，避免用大面积空卡片堆砌“气势”。',
    focusLabel: '华东餐饮客户',
    refreshLabel: '刚刚更新',
    heroTitle: '报价、线索、老板摘要三件事放在同一屏完成承接',
    heroSummary: '适合接在真实行情之后做销售化承接，先讲窗口，再给动作，不把用户丢进过深的分析页。',
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
