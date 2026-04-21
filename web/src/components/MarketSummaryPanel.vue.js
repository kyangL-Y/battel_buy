/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/props-fallback.d.ts" />
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useViewport } from '../composables/useViewport';
const props = defineProps();
const emit = defineEmits();
const { isMobileViewport, isNarrowViewport } = useViewport();
function handleRowClick(row) {
    if (row.price_identity_key) {
        emit('select-product', row.price_identity_key);
    }
}
const topSummary = computed(() => {
    if (!sortedRows.value.length)
        return null;
    return sortedRows.value[0];
});
const sortedRows = computed(() => {
    const keyword = props.keyword.trim().toLowerCase();
    return keyword
        ? props.rows.filter((row) => [row.product_name, row.region_label, row.lowest_price_site, row.highest_price_site]
            .filter(Boolean)
            .some((value) => String(value).toLowerCase().includes(keyword)))
        : props.rows;
});
const currentPage = ref(1);
const viewportHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 960);
const pageSize = computed(() => {
    if (isMobileViewport.value)
        return 10;
    return isNarrowViewport.value ? 60 : 80;
});
const pageCount = computed(() => Math.max(1, Math.ceil(sortedRows.value.length / pageSize.value)));
const paginationLayout = computed(() => (isMobileViewport.value ? 'prev, next' : 'prev, pager, next'));
const pagedRows = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value;
    return sortedRows.value.slice(start, start + pageSize.value);
});
const tableHeight = computed(() => {
    const minimumHeight = isNarrowViewport.value ? 460 : 520;
    const targetHeight = Math.max(minimumHeight, viewportHeight.value - (isNarrowViewport.value ? 266 : 246));
    if (!pagedRows.value.length)
        return targetHeight;
    if (pagedRows.value.length <= 8)
        return Math.max(targetHeight, 580);
    if (pagedRows.value.length <= 18)
        return Math.max(targetHeight, 680);
    return Math.max(targetHeight, 760);
});
function formatPrice(value) {
    return value == null || Number.isNaN(Number(value)) ? '-' : `${Number(value).toFixed(2)}`;
}
function formatSpread(lowest, highest) {
    if (lowest == null || highest == null)
        return '-';
    return (Number(highest) - Number(lowest)).toFixed(2);
}
function coverageStatusClass(status) {
    if (status === '已入库')
        return 'coverage-chip ok';
    if (status === '重复偏多')
        return 'coverage-chip warn';
    if (status === '抓取异常')
        return 'coverage-chip error';
    return 'coverage-chip';
}
function syncViewportHeight() {
    viewportHeight.value = window.innerHeight;
}
onMounted(() => {
    window.addEventListener('resize', syncViewportHeight);
});
onBeforeUnmount(() => {
    window.removeEventListener('resize', syncViewportHeight);
});
watch(sortedRows, () => {
    if (currentPage.value > pageCount.value) {
        currentPage.value = 1;
    }
}, { deep: true });
watch(pageSize, () => {
    currentPage.value = 1;
});
const __VLS_ctx = {
    ...{},
    ...{},
    ...{},
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_intrinsics;
let __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    'element-loading-text': "正在更新右侧报价...",
    'element-loading-background': "rgba(247, 248, 250, 0.72)",
    ...{ class: "panel market-panel" },
});
__VLS_asFunctionalDirective(__VLS_directives.vLoading, {})(null, { ...__VLS_directiveBindingRestFields, value: (__VLS_ctx.loading) }, null, null);
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['market-panel']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "panel-header" },
});
/** @type {__VLS_StyleScopedClasses['panel-header']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "panel-header-copy" },
});
/** @type {__VLS_StyleScopedClasses['panel-header-copy']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "panel-kicker" },
});
/** @type {__VLS_StyleScopedClasses['panel-kicker']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "panel-hint" },
});
/** @type {__VLS_StyleScopedClasses['panel-hint']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "inline-actions compact-actions market-header-actions" },
});
/** @type {__VLS_StyleScopedClasses['inline-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['compact-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['market-header-actions']} */ ;
let __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.elInput | typeof __VLS_components.ElInput} */
elInput;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
    ...{ 'onUpdate:modelValue': {} },
    modelValue: (__VLS_ctx.keyword),
    type: "search",
    inputmode: "search",
    enterkeyhint: "search",
    'aria-label': "表内搜索商品",
    placeholder: "表内搜索商品",
    clearable: true,
}));
const __VLS_2 = __VLS_1({
    ...{ 'onUpdate:modelValue': {} },
    modelValue: (__VLS_ctx.keyword),
    type: "search",
    inputmode: "search",
    enterkeyhint: "search",
    'aria-label': "表内搜索商品",
    placeholder: "表内搜索商品",
    clearable: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
let __VLS_5;
const __VLS_6 = ({ 'update:modelValue': {} },
    { 'onUpdate:modelValue': (...[$event]) => {
            __VLS_ctx.emit('keyword-change', $event || '');
            // @ts-ignore
            [vLoading, loading, keyword, emit,];
        } });
var __VLS_3;
var __VLS_4;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "table-stat-chip" },
});
/** @type {__VLS_StyleScopedClasses['table-stat-chip']} */ ;
(__VLS_ctx.sortedRows.length);
if (__VLS_ctx.topSummary && __VLS_ctx.sortedRows.length) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "market-snapshot" },
    });
    /** @type {__VLS_StyleScopedClasses['market-snapshot']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "snapshot-pill emphasis-pill" },
    });
    /** @type {__VLS_StyleScopedClasses['snapshot-pill']} */ ;
    /** @type {__VLS_StyleScopedClasses['emphasis-pill']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.topSummary.product_name);
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    (__VLS_ctx.formatPrice(__VLS_ctx.topSummary.average_price));
    (__VLS_ctx.topSummary.price_unit_basis || '元/公斤');
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "snapshot-pill" },
    });
    /** @type {__VLS_StyleScopedClasses['snapshot-pill']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.topSummary.lowest_price_site || '-');
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    (__VLS_ctx.formatPrice(__VLS_ctx.topSummary.lowest_price));
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "snapshot-pill" },
    });
    /** @type {__VLS_StyleScopedClasses['snapshot-pill']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.topSummary.highest_price_site || '-');
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    (__VLS_ctx.formatPrice(__VLS_ctx.topSummary.highest_price));
}
if (__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "market-mobile-list" },
        'data-testid': "market-mobile-list",
    });
    /** @type {__VLS_StyleScopedClasses['market-mobile-list']} */ ;
    for (const [row] of __VLS_vFor((__VLS_ctx.pagedRows))) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.isMobileViewport))
                        return;
                    __VLS_ctx.handleRowClick(row);
                    // @ts-ignore
                    [sortedRows, sortedRows, topSummary, topSummary, topSummary, topSummary, topSummary, topSummary, topSummary, topSummary, formatPrice, formatPrice, formatPrice, isMobileViewport, pagedRows, handleRowClick,];
                } },
            key: (`${row.price_identity_key || row.product_name}-${row.lowest_price_site || ''}`),
            type: "button",
            ...{ class: "market-mobile-card" },
            'data-testid': "market-mobile-card",
        });
        /** @type {__VLS_StyleScopedClasses['market-mobile-card']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "market-mobile-card-head" },
        });
        /** @type {__VLS_StyleScopedClasses['market-mobile-card-head']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "market-mobile-product" },
        });
        /** @type {__VLS_StyleScopedClasses['market-mobile-product']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (row.product_name);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "product-cell-meta" },
        });
        /** @type {__VLS_StyleScopedClasses['product-cell-meta']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (row.region_label || '未标注地区');
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (row.price_unit_basis || '元/公斤');
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (row.market_count || 0);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "market-mobile-metrics" },
        });
        /** @type {__VLS_StyleScopedClasses['market-mobile-metrics']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "summary-card compact-summary-card" },
        });
        /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
        /** @type {__VLS_StyleScopedClasses['compact-summary-card']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.formatPrice(row.average_price));
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.price_unit_basis || '元/公斤');
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "summary-card compact-summary-card" },
        });
        /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
        /** @type {__VLS_StyleScopedClasses['compact-summary-card']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.formatPrice(row.lowest_price));
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.lowest_price_site || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "summary-card compact-summary-card" },
        });
        /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
        /** @type {__VLS_StyleScopedClasses['compact-summary-card']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.formatPrice(row.highest_price));
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.highest_price_site || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "market-mobile-footer" },
        });
        /** @type {__VLS_StyleScopedClasses['market-mobile-footer']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "spread-value" },
        });
        /** @type {__VLS_StyleScopedClasses['spread-value']} */ ;
        (__VLS_ctx.formatSpread(row.lowest_price, row.highest_price));
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "market-mobile-action" },
        });
        /** @type {__VLS_StyleScopedClasses['market-mobile-action']} */ ;
        // @ts-ignore
        [formatPrice, formatPrice, formatPrice, formatSpread,];
    }
    if (!__VLS_ctx.pagedRows.length) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "table-empty-state" },
        });
        /** @type {__VLS_StyleScopedClasses['table-empty-state']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
        if (__VLS_ctx.keyword) {
            let __VLS_7;
            /** @ts-ignore @type {typeof __VLS_components.elButton | typeof __VLS_components.ElButton | typeof __VLS_components.elButton | typeof __VLS_components.ElButton} */
            elButton;
            // @ts-ignore
            const __VLS_8 = __VLS_asFunctionalComponent1(__VLS_7, new __VLS_7({
                ...{ 'onClick': {} },
                type: "primary",
                plain: true,
            }));
            const __VLS_9 = __VLS_8({
                ...{ 'onClick': {} },
                type: "primary",
                plain: true,
            }, ...__VLS_functionalComponentArgsRest(__VLS_8));
            let __VLS_12;
            const __VLS_13 = ({ click: {} },
                { onClick: (...[$event]) => {
                        if (!(__VLS_ctx.isMobileViewport))
                            return;
                        if (!(!__VLS_ctx.pagedRows.length))
                            return;
                        if (!(__VLS_ctx.keyword))
                            return;
                        __VLS_ctx.emit('keyword-change', '');
                        // @ts-ignore
                        [keyword, emit, pagedRows,];
                    } });
            const { default: __VLS_14 } = __VLS_10.slots;
            // @ts-ignore
            [];
            var __VLS_10;
            var __VLS_11;
        }
    }
}
else {
    let __VLS_15;
    /** @ts-ignore @type {typeof __VLS_components.elTable | typeof __VLS_components.ElTable | typeof __VLS_components.elTable | typeof __VLS_components.ElTable} */
    elTable;
    // @ts-ignore
    const __VLS_16 = __VLS_asFunctionalComponent1(__VLS_15, new __VLS_15({
        ...{ 'onRowClick': {} },
        data: (__VLS_ctx.pagedRows),
        height: (__VLS_ctx.tableHeight),
    }));
    const __VLS_17 = __VLS_16({
        ...{ 'onRowClick': {} },
        data: (__VLS_ctx.pagedRows),
        height: (__VLS_ctx.tableHeight),
    }, ...__VLS_functionalComponentArgsRest(__VLS_16));
    let __VLS_20;
    const __VLS_21 = ({ rowClick: {} },
        { onRowClick: (__VLS_ctx.handleRowClick) });
    const { default: __VLS_22 } = __VLS_18.slots;
    let __VLS_23;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn | typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_24 = __VLS_asFunctionalComponent1(__VLS_23, new __VLS_23({
        label: "商品",
        minWidth: "220",
        fixed: "left",
    }));
    const __VLS_25 = __VLS_24({
        label: "商品",
        minWidth: "220",
        fixed: "left",
    }, ...__VLS_functionalComponentArgsRest(__VLS_24));
    const { default: __VLS_28 } = __VLS_26.slots;
    {
        const { default: __VLS_29 } = __VLS_26.slots;
        const [{ row }] = __VLS_vSlot(__VLS_29);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "product-cell" },
        });
        /** @type {__VLS_StyleScopedClasses['product-cell']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (row.product_name);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "product-cell-meta" },
        });
        /** @type {__VLS_StyleScopedClasses['product-cell-meta']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (row.region_label || '未标注地区');
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (row.price_unit_basis || '元/公斤');
        // @ts-ignore
        [pagedRows, handleRowClick, tableHeight,];
    }
    // @ts-ignore
    [];
    var __VLS_26;
    let __VLS_30;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_31 = __VLS_asFunctionalComponent1(__VLS_30, new __VLS_30({
        prop: "market_count",
        label: "覆盖",
        width: "74",
    }));
    const __VLS_32 = __VLS_31({
        prop: "market_count",
        label: "覆盖",
        width: "74",
    }, ...__VLS_functionalComponentArgsRest(__VLS_31));
    let __VLS_35;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn | typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_36 = __VLS_asFunctionalComponent1(__VLS_35, new __VLS_35({
        label: "最低价（元/公斤）",
        width: "132",
        sortable: true,
    }));
    const __VLS_37 = __VLS_36({
        label: "最低价（元/公斤）",
        width: "132",
        sortable: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_36));
    const { default: __VLS_40 } = __VLS_38.slots;
    {
        const { default: __VLS_41 } = __VLS_38.slots;
        const [{ row }] = __VLS_vSlot(__VLS_41);
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "price-chip low" },
        });
        /** @type {__VLS_StyleScopedClasses['price-chip']} */ ;
        /** @type {__VLS_StyleScopedClasses['low']} */ ;
        (__VLS_ctx.formatPrice(row.lowest_price));
        // @ts-ignore
        [formatPrice,];
    }
    // @ts-ignore
    [];
    var __VLS_38;
    let __VLS_42;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_43 = __VLS_asFunctionalComponent1(__VLS_42, new __VLS_42({
        prop: "lowest_price_site",
        label: "最低价市场",
        minWidth: "150",
        showOverflowTooltip: true,
    }));
    const __VLS_44 = __VLS_43({
        prop: "lowest_price_site",
        label: "最低价市场",
        minWidth: "150",
        showOverflowTooltip: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_43));
    let __VLS_47;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn | typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_48 = __VLS_asFunctionalComponent1(__VLS_47, new __VLS_47({
        label: "最高价（元/公斤）",
        width: "132",
        sortable: true,
    }));
    const __VLS_49 = __VLS_48({
        label: "最高价（元/公斤）",
        width: "132",
        sortable: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_48));
    const { default: __VLS_52 } = __VLS_50.slots;
    {
        const { default: __VLS_53 } = __VLS_50.slots;
        const [{ row }] = __VLS_vSlot(__VLS_53);
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "price-chip high" },
        });
        /** @type {__VLS_StyleScopedClasses['price-chip']} */ ;
        /** @type {__VLS_StyleScopedClasses['high']} */ ;
        (__VLS_ctx.formatPrice(row.highest_price));
        // @ts-ignore
        [formatPrice,];
    }
    // @ts-ignore
    [];
    var __VLS_50;
    let __VLS_54;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_55 = __VLS_asFunctionalComponent1(__VLS_54, new __VLS_54({
        prop: "highest_price_site",
        label: "最高价市场",
        minWidth: "150",
        showOverflowTooltip: true,
    }));
    const __VLS_56 = __VLS_55({
        prop: "highest_price_site",
        label: "最高价市场",
        minWidth: "150",
        showOverflowTooltip: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_55));
    let __VLS_59;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn | typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_60 = __VLS_asFunctionalComponent1(__VLS_59, new __VLS_59({
        label: "均价（元/公斤）",
        width: "132",
        sortable: true,
    }));
    const __VLS_61 = __VLS_60({
        label: "均价（元/公斤）",
        width: "132",
        sortable: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_60));
    const { default: __VLS_64 } = __VLS_62.slots;
    {
        const { default: __VLS_65 } = __VLS_62.slots;
        const [{ row }] = __VLS_vSlot(__VLS_65);
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "price-chip avg" },
        });
        /** @type {__VLS_StyleScopedClasses['price-chip']} */ ;
        /** @type {__VLS_StyleScopedClasses['avg']} */ ;
        (__VLS_ctx.formatPrice(row.average_price));
        // @ts-ignore
        [formatPrice,];
    }
    // @ts-ignore
    [];
    var __VLS_62;
    let __VLS_66;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn | typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_67 = __VLS_asFunctionalComponent1(__VLS_66, new __VLS_66({
        label: "价差",
        width: "92",
    }));
    const __VLS_68 = __VLS_67({
        label: "价差",
        width: "92",
    }, ...__VLS_functionalComponentArgsRest(__VLS_67));
    const { default: __VLS_71 } = __VLS_69.slots;
    {
        const { default: __VLS_72 } = __VLS_69.slots;
        const [{ row }] = __VLS_vSlot(__VLS_72);
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "spread-value" },
        });
        /** @type {__VLS_StyleScopedClasses['spread-value']} */ ;
        (__VLS_ctx.formatSpread(row.lowest_price, row.highest_price));
        // @ts-ignore
        [formatSpread,];
    }
    // @ts-ignore
    [];
    var __VLS_69;
    {
        const { empty: __VLS_73 } = __VLS_18.slots;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "table-empty-state" },
        });
        /** @type {__VLS_StyleScopedClasses['table-empty-state']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
        if (__VLS_ctx.keyword) {
            let __VLS_74;
            /** @ts-ignore @type {typeof __VLS_components.elButton | typeof __VLS_components.ElButton | typeof __VLS_components.elButton | typeof __VLS_components.ElButton} */
            elButton;
            // @ts-ignore
            const __VLS_75 = __VLS_asFunctionalComponent1(__VLS_74, new __VLS_74({
                ...{ 'onClick': {} },
                type: "primary",
                plain: true,
            }));
            const __VLS_76 = __VLS_75({
                ...{ 'onClick': {} },
                type: "primary",
                plain: true,
            }, ...__VLS_functionalComponentArgsRest(__VLS_75));
            let __VLS_79;
            const __VLS_80 = ({ click: {} },
                { onClick: (...[$event]) => {
                        if (!!(__VLS_ctx.isMobileViewport))
                            return;
                        if (!(__VLS_ctx.keyword))
                            return;
                        __VLS_ctx.emit('keyword-change', '');
                        // @ts-ignore
                        [keyword, emit,];
                    } });
            const { default: __VLS_81 } = __VLS_77.slots;
            // @ts-ignore
            [];
            var __VLS_77;
            var __VLS_78;
        }
        // @ts-ignore
        [];
    }
    // @ts-ignore
    [];
    var __VLS_18;
    var __VLS_19;
}
if (__VLS_ctx.sortedRows.length > __VLS_ctx.pageSize) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "table-pagination-bar" },
    });
    /** @type {__VLS_StyleScopedClasses['table-pagination-bar']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (__VLS_ctx.sortedRows.length);
    (__VLS_ctx.currentPage);
    (__VLS_ctx.pageCount);
    let __VLS_82;
    /** @ts-ignore @type {typeof __VLS_components.elPagination | typeof __VLS_components.ElPagination} */
    elPagination;
    // @ts-ignore
    const __VLS_83 = __VLS_asFunctionalComponent1(__VLS_82, new __VLS_82({
        currentPage: (__VLS_ctx.currentPage),
        pageSize: (__VLS_ctx.pageSize),
        layout: (__VLS_ctx.paginationLayout),
        total: (__VLS_ctx.sortedRows.length),
        size: "small",
    }));
    const __VLS_84 = __VLS_83({
        currentPage: (__VLS_ctx.currentPage),
        pageSize: (__VLS_ctx.pageSize),
        layout: (__VLS_ctx.paginationLayout),
        total: (__VLS_ctx.sortedRows.length),
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_83));
}
if (__VLS_ctx.sourceCoverageRows.length) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.details, __VLS_intrinsics.details)({
        ...{ class: "source-coverage-block" },
    });
    /** @type {__VLS_StyleScopedClasses['source-coverage-block']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.summary, __VLS_intrinsics.summary)({
        ...{ class: "source-coverage-summary" },
    });
    /** @type {__VLS_StyleScopedClasses['source-coverage-summary']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
        ...{ class: "panel-kicker" },
    });
    /** @type {__VLS_StyleScopedClasses['panel-kicker']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (__VLS_ctx.sourceCoverageRows.length);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "source-coverage-inner" },
    });
    /** @type {__VLS_StyleScopedClasses['source-coverage-inner']} */ ;
    if (__VLS_ctx.isMobileViewport) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "source-coverage-card-list" },
        });
        /** @type {__VLS_StyleScopedClasses['source-coverage-card-list']} */ ;
        for (const [row] of __VLS_vFor((__VLS_ctx.sourceCoverageRows))) {
            __VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
                key: (`${row.configured_name || row.source_name}-${row.source_url}`),
                ...{ class: "source-coverage-card" },
            });
            /** @type {__VLS_StyleScopedClasses['source-coverage-card']} */ ;
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                ...{ class: "source-coverage-card-head" },
            });
            /** @type {__VLS_StyleScopedClasses['source-coverage-card-head']} */ ;
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
            __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
            (row.configured_name || row.source_name || '未命名来源');
            __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
            (row.latest_capture || '暂无抓取记录');
            __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
                ...{ class: (__VLS_ctx.coverageStatusClass(row.status)) },
            });
            (row.status || '-');
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                ...{ class: "source-coverage-card-grid" },
            });
            /** @type {__VLS_StyleScopedClasses['source-coverage-card-grid']} */ ;
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                ...{ class: "source-coverage-stat" },
            });
            /** @type {__VLS_StyleScopedClasses['source-coverage-stat']} */ ;
            __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
            __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
            (row.product_key_count || 0);
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                ...{ class: "source-coverage-stat" },
            });
            /** @type {__VLS_StyleScopedClasses['source-coverage-stat']} */ ;
            __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
            __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
            (row.comparable_item_count || 0);
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                ...{ class: "source-coverage-stat" },
            });
            /** @type {__VLS_StyleScopedClasses['source-coverage-stat']} */ ;
            __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
            __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
            (row.source_item_count || 0);
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                ...{ class: "source-coverage-stat" },
            });
            /** @type {__VLS_StyleScopedClasses['source-coverage-stat']} */ ;
            __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
            __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
            (row.failed_count || 0);
            // @ts-ignore
            [sortedRows, sortedRows, sortedRows, isMobileViewport, pageSize, pageSize, currentPage, currentPage, pageCount, paginationLayout, sourceCoverageRows, sourceCoverageRows, sourceCoverageRows, coverageStatusClass,];
        }
    }
    else {
        let __VLS_87;
        /** @ts-ignore @type {typeof __VLS_components.elTable | typeof __VLS_components.ElTable | typeof __VLS_components.elTable | typeof __VLS_components.ElTable} */
        elTable;
        // @ts-ignore
        const __VLS_88 = __VLS_asFunctionalComponent1(__VLS_87, new __VLS_87({
            data: (__VLS_ctx.sourceCoverageRows),
            height: "240",
        }));
        const __VLS_89 = __VLS_88({
            data: (__VLS_ctx.sourceCoverageRows),
            height: "240",
        }, ...__VLS_functionalComponentArgsRest(__VLS_88));
        const { default: __VLS_92 } = __VLS_90.slots;
        let __VLS_93;
        /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
        elTableColumn;
        // @ts-ignore
        const __VLS_94 = __VLS_asFunctionalComponent1(__VLS_93, new __VLS_93({
            prop: "configured_name",
            label: "来源",
            minWidth: "160",
        }));
        const __VLS_95 = __VLS_94({
            prop: "configured_name",
            label: "来源",
            minWidth: "160",
        }, ...__VLS_functionalComponentArgsRest(__VLS_94));
        let __VLS_98;
        /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn | typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
        elTableColumn;
        // @ts-ignore
        const __VLS_99 = __VLS_asFunctionalComponent1(__VLS_98, new __VLS_98({
            prop: "status",
            label: "状态",
            width: "100",
        }));
        const __VLS_100 = __VLS_99({
            prop: "status",
            label: "状态",
            width: "100",
        }, ...__VLS_functionalComponentArgsRest(__VLS_99));
        const { default: __VLS_103 } = __VLS_101.slots;
        {
            const { default: __VLS_104 } = __VLS_101.slots;
            const [{ row }] = __VLS_vSlot(__VLS_104);
            __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
                ...{ class: (__VLS_ctx.coverageStatusClass(row.status)) },
            });
            (row.status || '-');
            // @ts-ignore
            [sourceCoverageRows, coverageStatusClass,];
        }
        // @ts-ignore
        [];
        var __VLS_101;
        let __VLS_105;
        /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
        elTableColumn;
        // @ts-ignore
        const __VLS_106 = __VLS_asFunctionalComponent1(__VLS_105, new __VLS_105({
            prop: "product_key_count",
            label: "入库键数",
            width: "96",
        }));
        const __VLS_107 = __VLS_106({
            prop: "product_key_count",
            label: "入库键数",
            width: "96",
        }, ...__VLS_functionalComponentArgsRest(__VLS_106));
        let __VLS_110;
        /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
        elTableColumn;
        // @ts-ignore
        const __VLS_111 = __VLS_asFunctionalComponent1(__VLS_110, new __VLS_110({
            prop: "source_item_count",
            label: "站内去重",
            width: "96",
        }));
        const __VLS_112 = __VLS_111({
            prop: "source_item_count",
            label: "站内去重",
            width: "96",
        }, ...__VLS_functionalComponentArgsRest(__VLS_111));
        let __VLS_115;
        /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
        elTableColumn;
        // @ts-ignore
        const __VLS_116 = __VLS_asFunctionalComponent1(__VLS_115, new __VLS_115({
            prop: "comparable_item_count",
            label: "可比商品",
            width: "96",
        }));
        const __VLS_117 = __VLS_116({
            prop: "comparable_item_count",
            label: "可比商品",
            width: "96",
        }, ...__VLS_functionalComponentArgsRest(__VLS_116));
        let __VLS_120;
        /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
        elTableColumn;
        // @ts-ignore
        const __VLS_121 = __VLS_asFunctionalComponent1(__VLS_120, new __VLS_120({
            prop: "market_count",
            label: "市场数",
            width: "84",
        }));
        const __VLS_122 = __VLS_121({
            prop: "market_count",
            label: "市场数",
            width: "84",
        }, ...__VLS_functionalComponentArgsRest(__VLS_121));
        let __VLS_125;
        /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
        elTableColumn;
        // @ts-ignore
        const __VLS_126 = __VLS_asFunctionalComponent1(__VLS_125, new __VLS_125({
            prop: "latest_capture",
            label: "最近抓取",
            minWidth: "160",
            showOverflowTooltip: true,
        }));
        const __VLS_127 = __VLS_126({
            prop: "latest_capture",
            label: "最近抓取",
            minWidth: "160",
            showOverflowTooltip: true,
        }, ...__VLS_functionalComponentArgsRest(__VLS_126));
        let __VLS_130;
        /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
        elTableColumn;
        // @ts-ignore
        const __VLS_131 = __VLS_asFunctionalComponent1(__VLS_130, new __VLS_130({
            prop: "failed_count",
            label: "失败数",
            width: "84",
        }));
        const __VLS_132 = __VLS_131({
            prop: "failed_count",
            label: "失败数",
            width: "84",
        }, ...__VLS_functionalComponentArgsRest(__VLS_131));
        // @ts-ignore
        [];
        var __VLS_90;
    }
}
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({
    __typeEmits: {},
    __typeProps: {},
});
export default {};
