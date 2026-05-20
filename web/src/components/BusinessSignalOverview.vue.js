/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/props-fallback.d.ts" />
import { computed } from 'vue';
const props = withDefaults(defineProps(), {
    kicker: '经营信号',
    title: '今日经营概览',
    subtitle: '每张卡只展示经营信号接口返回的一个判断。',
    windowLabel: '近 7 天',
    reviewLabel: '每天 09:00 / 15:00 复核',
});
const fallbackSignals = [
    { title: '经营信号', value: '0 条', changeLabel: '等待接口', detail: '暂无真实经营信号返回。', trend: 'flat', severity: 'good' },
    { title: '风险提醒', value: '0 条', changeLabel: '等待接口', detail: '暂无真实风险提醒返回。', trend: 'flat', severity: 'good' },
    { title: '建议动作', value: '0 条', changeLabel: '等待接口', detail: '暂无真实建议动作返回。', trend: 'flat', severity: 'good' },
];
const fallbackAlerts = [
    { title: '等待真实提醒', detail: '经营信号接口返回后会在这里展示轻提醒。', owner: '系统' },
];
const resolvedSignals = computed(() => props.signals?.length ? props.signals : fallbackSignals);
const resolvedAlerts = computed(() => props.alerts?.length ? props.alerts : fallbackAlerts);
const __VLS_defaults = {
    kicker: '经营信号',
    title: '今日经营概览',
    subtitle: '每张卡只展示经营信号接口返回的一个判断。',
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
