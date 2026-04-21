/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/props-fallback.d.ts" />
import { computed } from 'vue';
const props = withDefaults(defineProps(), {
    kicker: '经营信号',
    title: '今日经营概览',
    subtitle: '控制信息密度，每张卡只表达一个判断，适合直接做晨会或老板驾驶舱中段。',
    windowLabel: '近 7 天',
    reviewLabel: '每天 09:00 / 15:00 复核',
});
const fallbackSignals = [
    { title: '采购成本波动', value: '+3.8%', changeLabel: '较昨日上行', detail: '集中在高频蔬菜，不建议全品类同步调价。', trend: 'up', severity: 'watch' },
    { title: '报价成交率', value: '31%', changeLabel: '本周改善', detail: '套餐化表达后，客户反馈更容易理解。', trend: 'up', severity: 'good' },
    { title: '缺货暴露度', value: '2 类', changeLabel: '需盯防', detail: '若今晚不锁量，明日交付稳定性会下降。', trend: 'flat', severity: 'risk' },
    { title: '替代品可用度', value: '4 套', changeLabel: '可执行', detail: '已有替代组合，可在报价页直接展示。', trend: 'up', severity: 'good' },
    { title: '老板查看频次', value: '9 次', changeLabel: '本周新增', detail: '摘要页比明细页更容易被重复打开。', trend: 'up', severity: 'good' },
    { title: '异常来源占比', value: '12%', changeLabel: '需继续压降', detail: '仍有少量来源需要人工判读，不宜直接透出给客户。', trend: 'down', severity: 'watch' },
];
const fallbackAlerts = [
    { title: '套餐 B 可作为成交主推', detail: '价格解释更顺，且能覆盖当前客户最在意的 3 个食材。', owner: '销售' },
    { title: '明晨前锁定高频品采购量', detail: '若今晚不锁量，明天同城报价可能出现临时抬价。', owner: '采购' },
    { title: '驾驶舱摘要建议缩成 1 屏', detail: '老板页面不宜超过 6 张核心卡，剩余信息收进轻提醒。', owner: '产品' },
];
const resolvedSignals = computed(() => props.signals?.length ? props.signals : fallbackSignals);
const resolvedAlerts = computed(() => props.alerts?.length ? props.alerts : fallbackAlerts);
const __VLS_defaults = {
    kicker: '经营信号',
    title: '今日经营概览',
    subtitle: '控制信息密度，每张卡只表达一个判断，适合直接做晨会或老板驾驶舱中段。',
    windowLabel: '近 7 天',
    reviewLabel: '每天 09:00 / 15:00 复核',
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
/** @type {__VLS_StyleScopedClasses['business-signal-meta']} */ ;
/** @type {__VLS_StyleScopedClasses['business-signal-meta']} */ ;
/** @type {__VLS_StyleScopedClasses['business-signal-meta']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-alert-item']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-alert-item']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-alert-item']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-alert-item']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-alert-item']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-alert-shell']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-alert-head']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-alert-item']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-alert-head']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-alert-item']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-alert-shell']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['business-signal-meta']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    ...{ class: "panel business-signal-panel" },
});
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['business-signal-panel']} */ ;
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
    ...{ class: "business-signal-meta" },
});
/** @type {__VLS_StyleScopedClasses['business-signal-meta']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
(__VLS_ctx.windowLabel);
__VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
(__VLS_ctx.reviewLabel);
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "signal-card-grid" },
});
/** @type {__VLS_StyleScopedClasses['signal-card-grid']} */ ;
for (const [item] of __VLS_vFor((__VLS_ctx.resolvedSignals))) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
        key: (item.title),
        ...{ class: "signal-card" },
        ...{ class: (`is-${item.severity}`) },
    });
    /** @type {__VLS_StyleScopedClasses['signal-card']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "signal-card-head" },
    });
    /** @type {__VLS_StyleScopedClasses['signal-card-head']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (item.title);
    __VLS_asFunctionalElement1(__VLS_intrinsics.em, __VLS_intrinsics.em)({
        ...{ class: (`is-${item.trend}`) },
    });
    (item.changeLabel);
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (item.value);
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
    (item.detail);
    // @ts-ignore
    [kicker, title, subtitle, windowLabel, reviewLabel, resolvedSignals,];
}
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "signal-alert-shell" },
});
/** @type {__VLS_StyleScopedClasses['signal-alert-shell']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "signal-alert-head" },
});
/** @type {__VLS_StyleScopedClasses['signal-alert-head']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
(__VLS_ctx.resolvedAlerts.length);
if (__VLS_ctx.resolvedAlerts.length) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "signal-alert-list" },
    });
    /** @type {__VLS_StyleScopedClasses['signal-alert-list']} */ ;
    for (const [item] of __VLS_vFor((__VLS_ctx.resolvedAlerts))) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            key: (item.title),
            ...{ class: "signal-alert-item" },
        });
        /** @type {__VLS_StyleScopedClasses['signal-alert-item']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (item.title);
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
        (item.detail);
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (item.owner);
        // @ts-ignore
        [resolvedAlerts, resolvedAlerts, resolvedAlerts,];
    }
}
else {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "table-empty-state signal-empty-state" },
    });
    /** @type {__VLS_StyleScopedClasses['table-empty-state']} */ ;
    /** @type {__VLS_StyleScopedClasses['signal-empty-state']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
}
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({
    __typeProps: {},
    props: {},
});
export default {};
