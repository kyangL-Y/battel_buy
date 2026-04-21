/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/props-fallback.d.ts" />
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useViewport } from '../composables/useViewport';
const props = defineProps();
const emit = defineEmits();
const trendChartRef = ref(null);
const { isMobileViewport, isNarrowViewport, isShortViewport } = useViewport();
let echartsModule = null;
let trendChart = null;
let resizeObserver = null;
const comparisonPageIndex = ref(0);
const currentProductOption = computed(() => props.productOptions.find((item) => item.price_identity_key === props.selectedIdentityKey) || null);
const availableSites = computed(() => props.siteOptions || []);
const isComparisonMode = computed(() => props.trendMode === 'cross_market');
const shouldCarryForwardPrice = computed(() => isComparisonMode.value);
const currentProductLabel = computed(() => currentProductOption.value?.price_identity_label || '');
const currentProductCoverageLabel = computed(() => {
    const siteCount = Number(currentProductOption.value?.site_count || 0);
    return siteCount ? `已覆盖 ${siteCount} 个市场` : '市场覆盖待确认';
});
const currentSiteLabel = computed(() => String(props.selectedSiteName || '').trim());
const currentScopeLabel = computed(() => (props.trendMode === 'cross_market'
    ? `跨市场 · ${availableSites.value.length || 0} 个市场`
    : (currentSiteLabel.value || '待选择单个市场')));
const currentOverviewRangeLabel = computed(() => (props.trendMode === 'cross_market'
    ? '比较范围：跨市场'
    : `当前市场：${currentSiteLabel.value || '待选择'}`));
const chartCategories = computed(() => buildChartCategories(props.trendRows));
const allChartSeries = computed(() => buildChartSeries(props.trendRows, chartCategories.value, shouldCarryForwardPrice.value));
const comparisonSeriesPages = computed(() => buildSeriesPages(allChartSeries.value, isComparisonMode.value));
const comparisonPageCount = computed(() => comparisonSeriesPages.value.length);
const visibleChartSeries = computed(() => {
    const page = comparisonSeriesPages.value[comparisonPageIndex.value];
    return page && page.length ? page : (comparisonSeriesPages.value[0] || []);
});
const visibleSeriesNameSet = computed(() => new Set(visibleChartSeries.value.map((item) => String(item.name || '').trim()).filter(Boolean)));
const recentTrendRows = computed(() => [...props.trendRows]
    .filter((row) => visibleSeriesNameSet.value.has(buildTrendSeriesName(row)))
    .sort((left, right) => String(right.captured_at || '').localeCompare(String(left.captured_at || '')))
    .slice(0, isMobileViewport.value ? 6 : 18));
const chartHeight = computed(() => {
    if (!isMobileViewport.value)
        return isNarrowViewport.value ? '460px' : '520px';
    if (isShortViewport.value) {
        if (comparisonPageCount.value > 1 || visibleChartSeries.value.length >= 4)
            return '340px';
        if (chartCategories.value.length >= 10)
            return '316px';
        return '292px';
    }
    if (comparisonPageCount.value > 1 || visibleChartSeries.value.length >= 4)
        return '404px';
    if (chartCategories.value.length >= 10)
        return '376px';
    return '348px';
});
const trendListCountLabel = computed(() => (isMobileViewport.value
    ? `${recentTrendRows.value.length} / ${props.trendRows.length} 条`
    : `${props.trendRows.length} 条`));
async function ensureTrendChart() {
    if (!trendChartRef.value)
        return null;
    if (!echartsModule) {
        const [{ use, init }, charts, components, renderers] = await Promise.all([
            import('echarts/core'),
            import('echarts/charts'),
            import('echarts/components'),
            import('echarts/renderers'),
        ]);
        use([
            charts.LineChart,
            components.GridComponent,
            components.TooltipComponent,
            components.LegendComponent,
            components.DatasetComponent,
            renderers.CanvasRenderer,
        ]);
        echartsModule = { use, init };
    }
    if (!trendChart) {
        trendChart = echartsModule.init(trendChartRef.value);
    }
    return trendChart;
}
function buildChartCategories(rows) {
    return Array.from(new Set(rows.map((row) => String(row.captured_at || '').trim()).filter(Boolean))).sort();
}
function buildChartSeries(rows, categories, carryForwardPrice) {
    const seriesBySite = new Map();
    rows.forEach((row) => {
        const siteName = buildTrendSeriesName(row);
        const capturedAt = String(row.captured_at || '').trim();
        const currentPrice = Number(row.current_price);
        if (!capturedAt || Number.isNaN(currentPrice))
            return;
        if (!seriesBySite.has(siteName)) {
            seriesBySite.set(siteName, new Map());
        }
        seriesBySite.get(siteName).set(capturedAt, currentPrice);
    });
    return Array.from(seriesBySite.entries()).map(([name, points]) => {
        let lastKnownPrice = null;
        const data = categories.map((category) => {
            const currentPrice = points.get(category);
            if (currentPrice != null) {
                lastKnownPrice = currentPrice;
            }
            if (currentPrice == null && !carryForwardPrice) {
                return null;
            }
            if (lastKnownPrice == null) {
                return null;
            }
            return {
                value: currentPrice != null ? currentPrice : lastKnownPrice,
                rawPrice: currentPrice != null ? currentPrice : lastKnownPrice,
                isActual: currentPrice != null,
            };
        });
        return {
            name,
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            connectNulls: carryForwardPrice,
            showSymbol: false,
            lineStyle: { width: 3 },
            emphasis: { focus: 'series' },
            data,
            latestValue: lastKnownPrice,
        };
    });
}
function buildSeriesPages(seriesItems, comparisonMode) {
    if (!seriesItems.length) {
        return [[]];
    }
    if (!comparisonMode) {
        return [seriesItems];
    }
    const uniqueSeries = [];
    const duplicateBuckets = new Map();
    for (const item of seriesItems) {
        const signature = JSON.stringify(item.data);
        if (!duplicateBuckets.has(signature)) {
            duplicateBuckets.set(signature, []);
        }
        duplicateBuckets.get(signature).push(item);
    }
    const duplicateGroups = [];
    for (const items of duplicateBuckets.values()) {
        if (items.length <= 1) {
            uniqueSeries.push(items[0]);
            continue;
        }
        duplicateGroups.push(items);
    }
    if (!duplicateGroups.length) {
        return [seriesItems];
    }
    const pages = duplicateGroups.map((items) => {
        const page = [];
        uniqueSeries.forEach((item) => page.push(item));
        items.forEach((item) => page.push(item));
        return page;
    });
    const filteredPages = pages.filter((page) => page.length >= 2);
    if (!filteredPages.length || filteredPages.length === 1) {
        return [seriesItems];
    }
    return filteredPages;
}
async function renderTrendChart() {
    if (!trendChartRef.value)
        return;
    await nextTick();
    await new Promise((resolve) => window.requestAnimationFrame(() => resolve(undefined)));
    const chart = await ensureTrendChart();
    if (!chart)
        return;
    if (!props.trendRows.length) {
        chart.clear();
        chart.resize();
        return;
    }
    const categories = chartCategories.value;
    const comparisonMode = isComparisonMode.value;
    const carryForwardPrice = shouldCarryForwardPrice.value;
    const series = visibleChartSeries.value;
    const isSparseTimeline = categories.length <= 3;
    chart.resize();
    chart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            formatter: (params) => {
                const rows = Array.isArray(params) ? params : [params];
                const axisLabel = rows[0]?.axisValueLabel || rows[0]?.axisValue || '';
                const lines = rows
                    .filter((item) => item?.data)
                    .map((item) => {
                    const data = item.data || {};
                    const value = Number(data.value);
                    const comparisonText = `${value.toFixed(2)}`;
                    const actualMarker = data.isActual || !carryForwardPrice ? '' : '（延用上次报价）';
                    return `${item.marker}${item.seriesName}：${comparisonText}${actualMarker}`;
                });
                return [axisLabel, ...lines].join('<br/>');
            },
        },
        legend: {
            type: 'scroll',
            top: isMobileViewport.value ? 8 : 10,
            left: isMobileViewport.value ? 12 : 18,
            right: isMobileViewport.value ? 12 : 52,
            icon: 'roundRect',
            itemWidth: isMobileViewport.value ? 16 : 22,
            itemHeight: 4,
            itemGap: isMobileViewport.value ? 12 : 18,
            pageIconSize: 10,
            pageButtonGap: 10,
            pageButtonItemGap: 6,
            textStyle: {
                color: '#63738c',
                fontSize: isMobileViewport.value ? 11 : 12,
                fontWeight: 600,
            },
            pageTextStyle: { color: '#63738c' },
            pageIconColor: '#365486',
            pageIconInactiveColor: '#b7c4d8',
            formatter: (name) => formatTrendLegendLabel(name),
        },
        grid: {
            left: isSparseTimeline ? (isMobileViewport.value ? '14%' : '12%') : (isMobileViewport.value ? 18 : 24),
            right: isSparseTimeline ? (isMobileViewport.value ? '10%' : '12%') : 18,
            top: isMobileViewport.value ? 84 : 62,
            bottom: isMobileViewport.value ? 56 : 24,
            containLabel: true,
        },
        xAxis: {
            type: 'category',
            boundaryGap: isSparseTimeline,
            axisLabel: {
                color: '#7c8ca4',
                formatter: (value) => formatTrendAxisLabel(value),
                hideOverlap: true,
                rotate: isMobileViewport.value ? 35 : 0,
                fontSize: isMobileViewport.value ? 10 : 12,
                margin: isMobileViewport.value ? 14 : 8,
            },
            axisLine: { lineStyle: { color: '#d7e2f0' } },
            data: categories,
        },
        yAxis: {
            type: 'value',
            name: '价格',
            axisLabel: { color: '#7c8ca4' },
            splitLine: { lineStyle: { color: 'rgba(47,128,237,0.08)' } },
        },
        series,
    }, true);
}
function formatPrice(value) {
    return value == null || Number.isNaN(Number(value)) ? '-' : Number(value).toFixed(2);
}
function buildTrendSeriesName(row) {
    if (row.trend_series_name) {
        return String(row.trend_series_name).trim();
    }
    const siteText = String(row.site_name || '').trim();
    const sourceName = siteText.includes('|') ? siteText.split('|')[0].trim() : siteText;
    const marketText = String(row.market_name || row.city || row.province || '').trim();
    const regionText = String(row.region_label || row.city || row.province || '').trim();
    if (sourceName && marketText && regionText && marketText !== regionText) {
        return `${sourceName} · ${marketText} · ${regionText}`;
    }
    if (sourceName && marketText) {
        return `${sourceName} · ${marketText}`;
    }
    return sourceName || marketText || '未知市场';
}
function buildTrendMeta(row) {
    if (row.trend_meta_label) {
        return String(row.trend_meta_label).trim();
    }
    const parts = [row.market_name, row.region_label, row.city, row.province]
        .map((item) => String(item || '').trim())
        .filter(Boolean);
    return parts.length ? Array.from(new Set(parts)).join(' · ') : '未标注市场';
}
function formatTrendAxisLabel(value) {
    const text = String(value || '').trim();
    if (!text)
        return '';
    const dateMatch = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2}))?/);
    if (!dateMatch)
        return text;
    const [, , month, day, hour, minute] = dateMatch;
    if (!isMobileViewport.value) {
        return hour && minute ? `${month}-${day} ${hour}:${minute}` : `${month}-${day}`;
    }
    return hour && minute ? `${month}-${day}\n${hour}:${minute}` : `${month}-${day}`;
}
function formatTrendLegendLabel(name) {
    const text = String(name || '').trim();
    if (!text)
        return '';
    if (!isMobileViewport.value)
        return text;
    const segments = text.split(/[·|]/).map((item) => item.trim()).filter(Boolean);
    const candidate = segments[segments.length - 1] || text;
    return candidate.length > 9 ? `${candidate.slice(0, 8)}…` : candidate;
}
function formatTrendTime(value) {
    const text = String(value || '').trim();
    if (!text)
        return '-';
    const dateMatch = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2}))?/);
    if (!dateMatch)
        return text;
    const [, , month, day, hour, minute] = dateMatch;
    return hour && minute ? `${month}-${day} ${hour}:${minute}` : `${month}-${day}`;
}
watch(() => [props.trendRows, props.selectedIdentityKey, props.trendMode, props.selectedSiteName, comparisonPageIndex.value], async () => {
    await renderTrendChart();
}, { deep: true });
watch(() => [props.trendMode, props.selectedIdentityKey, comparisonPageCount.value], () => {
    if (comparisonPageIndex.value >= comparisonPageCount.value) {
        comparisonPageIndex.value = 0;
    }
});
onMounted(async () => {
    await renderTrendChart();
    window.addEventListener('resize', renderTrendChart);
    if (typeof ResizeObserver !== 'undefined' && trendChartRef.value) {
        resizeObserver = new ResizeObserver(() => {
            void renderTrendChart();
        });
        resizeObserver.observe(trendChartRef.value);
    }
});
onBeforeUnmount(() => {
    window.removeEventListener('resize', renderTrendChart);
    resizeObserver?.disconnect();
    resizeObserver = null;
    trendChart?.dispose();
    trendChart = null;
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
/** @type {__VLS_StyleScopedClasses['trend-chart-nav']} */ ;
/** @type {__VLS_StyleScopedClasses['trend-chart-nav']} */ ;
/** @type {__VLS_StyleScopedClasses['trend-chart-mobile-button']} */ ;
/** @type {__VLS_StyleScopedClasses['trend-chart-mobile-button']} */ ;
/** @type {__VLS_StyleScopedClasses['trend-chart-mobile-button']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    ...{ class: "panel trend-workspace-panel" },
});
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['trend-workspace-panel']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "panel-header" },
});
/** @type {__VLS_StyleScopedClasses['panel-header']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "panel-kicker" },
});
/** @type {__VLS_StyleScopedClasses['panel-kicker']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
if (!__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
        ...{ class: "panel-hint" },
    });
    /** @type {__VLS_StyleScopedClasses['panel-hint']} */ ;
}
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "inline-actions" },
});
/** @type {__VLS_StyleScopedClasses['inline-actions']} */ ;
let __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.elRadioGroup | typeof __VLS_components.ElRadioGroup | typeof __VLS_components.elRadioGroup | typeof __VLS_components.ElRadioGroup} */
elRadioGroup;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
    ...{ 'onChange': {} },
    'aria-label': "趋势模式切换",
    modelValue: (__VLS_ctx.trendMode),
}));
const __VLS_2 = __VLS_1({
    ...{ 'onChange': {} },
    'aria-label': "趋势模式切换",
    modelValue: (__VLS_ctx.trendMode),
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
let __VLS_5;
const __VLS_6 = ({ change: {} },
    { onChange: (...[$event]) => {
            __VLS_ctx.emit('update:trend-mode', $event);
            // @ts-ignore
            [isMobileViewport, trendMode, emit,];
        } });
const { default: __VLS_7 } = __VLS_3.slots;
let __VLS_8;
/** @ts-ignore @type {typeof __VLS_components.elRadioButton | typeof __VLS_components.ElRadioButton | typeof __VLS_components.elRadioButton | typeof __VLS_components.ElRadioButton} */
elRadioButton;
// @ts-ignore
const __VLS_9 = __VLS_asFunctionalComponent1(__VLS_8, new __VLS_8({
    value: "cross_market",
}));
const __VLS_10 = __VLS_9({
    value: "cross_market",
}, ...__VLS_functionalComponentArgsRest(__VLS_9));
const { default: __VLS_13 } = __VLS_11.slots;
// @ts-ignore
[];
var __VLS_11;
let __VLS_14;
/** @ts-ignore @type {typeof __VLS_components.elRadioButton | typeof __VLS_components.ElRadioButton | typeof __VLS_components.elRadioButton | typeof __VLS_components.ElRadioButton} */
elRadioButton;
// @ts-ignore
const __VLS_15 = __VLS_asFunctionalComponent1(__VLS_14, new __VLS_14({
    value: "single_market",
}));
const __VLS_16 = __VLS_15({
    value: "single_market",
}, ...__VLS_functionalComponentArgsRest(__VLS_15));
const { default: __VLS_19 } = __VLS_17.slots;
// @ts-ignore
[];
var __VLS_17;
// @ts-ignore
[];
var __VLS_3;
var __VLS_4;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "trend-toolbar" },
});
/** @type {__VLS_StyleScopedClasses['trend-toolbar']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "trend-picker-inline" },
});
/** @type {__VLS_StyleScopedClasses['trend-picker-inline']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
let __VLS_20;
/** @ts-ignore @type {typeof __VLS_components.elSelect | typeof __VLS_components.ElSelect | typeof __VLS_components.elSelect | typeof __VLS_components.ElSelect} */
elSelect;
// @ts-ignore
const __VLS_21 = __VLS_asFunctionalComponent1(__VLS_20, new __VLS_20({
    ...{ 'onChange': {} },
    modelValue: (__VLS_ctx.selectedIdentityKey),
    'aria-label': "选择商品",
    placeholder: "选择单品",
    filterable: true,
}));
const __VLS_22 = __VLS_21({
    ...{ 'onChange': {} },
    modelValue: (__VLS_ctx.selectedIdentityKey),
    'aria-label': "选择商品",
    placeholder: "选择单品",
    filterable: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_21));
let __VLS_25;
const __VLS_26 = ({ change: {} },
    { onChange: (...[$event]) => {
            __VLS_ctx.emit('select-product', $event);
            // @ts-ignore
            [emit, selectedIdentityKey,];
        } });
const { default: __VLS_27 } = __VLS_23.slots;
for (const [item] of __VLS_vFor((__VLS_ctx.productOptions))) {
    let __VLS_28;
    /** @ts-ignore @type {typeof __VLS_components.elOption | typeof __VLS_components.ElOption} */
    elOption;
    // @ts-ignore
    const __VLS_29 = __VLS_asFunctionalComponent1(__VLS_28, new __VLS_28({
        key: (item.price_identity_key),
        label: (item.price_identity_label),
        value: (item.price_identity_key),
    }));
    const __VLS_30 = __VLS_29({
        key: (item.price_identity_key),
        label: (item.price_identity_label),
        value: (item.price_identity_key),
    }, ...__VLS_functionalComponentArgsRest(__VLS_29));
    // @ts-ignore
    [productOptions,];
}
// @ts-ignore
[];
var __VLS_23;
var __VLS_24;
if (__VLS_ctx.trendMode === 'single_market') {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "trend-picker-inline site-inline" },
    });
    /** @type {__VLS_StyleScopedClasses['trend-picker-inline']} */ ;
    /** @type {__VLS_StyleScopedClasses['site-inline']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    let __VLS_33;
    /** @ts-ignore @type {typeof __VLS_components.elSelect | typeof __VLS_components.ElSelect | typeof __VLS_components.elSelect | typeof __VLS_components.ElSelect} */
    elSelect;
    // @ts-ignore
    const __VLS_34 = __VLS_asFunctionalComponent1(__VLS_33, new __VLS_33({
        ...{ 'onChange': {} },
        modelValue: (__VLS_ctx.selectedSiteName),
        'aria-label': "选择市场",
        clearable: true,
        placeholder: "选择单个市场",
    }));
    const __VLS_35 = __VLS_34({
        ...{ 'onChange': {} },
        modelValue: (__VLS_ctx.selectedSiteName),
        'aria-label': "选择市场",
        clearable: true,
        placeholder: "选择单个市场",
    }, ...__VLS_functionalComponentArgsRest(__VLS_34));
    let __VLS_38;
    const __VLS_39 = ({ change: {} },
        { onChange: (...[$event]) => {
                if (!(__VLS_ctx.trendMode === 'single_market'))
                    return;
                __VLS_ctx.emit('update:selected-site-name', $event || '');
                // @ts-ignore
                [trendMode, emit, selectedSiteName,];
            } });
    const { default: __VLS_40 } = __VLS_36.slots;
    for (const [site] of __VLS_vFor((__VLS_ctx.availableSites))) {
        let __VLS_41;
        /** @ts-ignore @type {typeof __VLS_components.elOption | typeof __VLS_components.ElOption} */
        elOption;
        // @ts-ignore
        const __VLS_42 = __VLS_asFunctionalComponent1(__VLS_41, new __VLS_41({
            key: (site),
            label: (site),
            value: (site),
        }));
        const __VLS_43 = __VLS_42({
            key: (site),
            label: (site),
            value: (site),
        }, ...__VLS_functionalComponentArgsRest(__VLS_42));
        // @ts-ignore
        [availableSites,];
    }
    // @ts-ignore
    [];
    var __VLS_36;
    var __VLS_37;
}
if (!__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "trend-toolbar-count" },
    });
    /** @type {__VLS_StyleScopedClasses['trend-toolbar-count']} */ ;
    (__VLS_ctx.productOptions.length);
}
if (__VLS_ctx.isMobileViewport && (__VLS_ctx.currentProductLabel || __VLS_ctx.currentSiteLabel || __VLS_ctx.currentScopeLabel)) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "trend-selection-summary" },
    });
    /** @type {__VLS_StyleScopedClasses['trend-selection-summary']} */ ;
    if (__VLS_ctx.currentProductLabel) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-selection-item" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-selection-item']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.currentProductLabel);
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (__VLS_ctx.currentProductCoverageLabel);
    }
    if (__VLS_ctx.currentScopeLabel) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-selection-item" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-selection-item']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (__VLS_ctx.trendMode === 'cross_market' ? '比较范围' : '当前市场');
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.currentScopeLabel);
    }
}
if (__VLS_ctx.selectedIdentityKey) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "trend-content-shell" },
        ...{ class: ({ 'is-loading': __VLS_ctx.loading }) },
    });
    /** @type {__VLS_StyleScopedClasses['trend-content-shell']} */ ;
    /** @type {__VLS_StyleScopedClasses['is-loading']} */ ;
    if (__VLS_ctx.currentProductOption && __VLS_ctx.currentProductOption.site_count <= 1) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-single-source-tip" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-single-source-tip']} */ ;
        (__VLS_ctx.availableSites[0] || '当前来源');
    }
    if (__VLS_ctx.isComparisonMode) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-compare-tip" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-compare-tip']} */ ;
    }
    if (__VLS_ctx.productSummary && __VLS_ctx.isMobileViewport) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-mobile-overview" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-mobile-overview']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-mobile-pill" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-mobile-pill']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.productSummary.current_lowest_price ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (__VLS_ctx.productSummary.current_lowest_site ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-mobile-pill" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-mobile-pill']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.productSummary.average_price ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (__VLS_ctx.productSummary.latest_captured_at ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-mobile-pill" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-mobile-pill']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.availableSites.length || 0);
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (__VLS_ctx.currentOverviewRangeLabel);
    }
    else if (__VLS_ctx.productSummary) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-summary-strip" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-summary-strip']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "summary-card compact-summary-card" },
        });
        /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
        /** @type {__VLS_StyleScopedClasses['compact-summary-card']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.productSummary.current_lowest_price ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (__VLS_ctx.productSummary.current_lowest_site ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "summary-card compact-summary-card" },
        });
        /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
        /** @type {__VLS_StyleScopedClasses['compact-summary-card']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.productSummary.current_highest_price ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (__VLS_ctx.productSummary.current_highest_site ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "summary-card compact-summary-card" },
        });
        /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
        /** @type {__VLS_StyleScopedClasses['compact-summary-card']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.productSummary.average_price ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (__VLS_ctx.productSummary.latest_captured_at ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "summary-card compact-summary-card" },
        });
        /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
        /** @type {__VLS_StyleScopedClasses['compact-summary-card']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.availableSites.length || 0);
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (__VLS_ctx.currentOverviewRangeLabel);
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "trend-main-grid" },
    });
    /** @type {__VLS_StyleScopedClasses['trend-main-grid']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
    if (__VLS_ctx.productSummary && !__VLS_ctx.isMobileViewport) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-insight-strip" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-insight-strip']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (__VLS_ctx.productSummary.current_lowest_site ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (__VLS_ctx.productSummary.current_highest_site ?? '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (__VLS_ctx.productSummary.latest_captured_at ?? '-');
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "trend-chart-shell" },
    });
    /** @type {__VLS_StyleScopedClasses['trend-chart-shell']} */ ;
    if (!__VLS_ctx.isMobileViewport && __VLS_ctx.isComparisonMode && __VLS_ctx.comparisonPageCount > 1) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.selectedIdentityKey))
                        return;
                    if (!(!__VLS_ctx.isMobileViewport && __VLS_ctx.isComparisonMode && __VLS_ctx.comparisonPageCount > 1))
                        return;
                    __VLS_ctx.comparisonPageIndex -= 1;
                    // @ts-ignore
                    [isMobileViewport, isMobileViewport, isMobileViewport, isMobileViewport, isMobileViewport, trendMode, selectedIdentityKey, productOptions, availableSites, availableSites, availableSites, currentProductLabel, currentProductLabel, currentProductLabel, currentSiteLabel, currentScopeLabel, currentScopeLabel, currentScopeLabel, currentProductCoverageLabel, loading, currentProductOption, currentProductOption, isComparisonMode, isComparisonMode, productSummary, productSummary, productSummary, productSummary, productSummary, productSummary, productSummary, productSummary, productSummary, productSummary, productSummary, productSummary, productSummary, productSummary, productSummary, productSummary, currentOverviewRangeLabel, currentOverviewRangeLabel, comparisonPageCount, comparisonPageIndex,];
                } },
            type: "button",
            ...{ class: "trend-chart-nav trend-chart-nav-left" },
            disabled: (__VLS_ctx.comparisonPageIndex <= 0),
        });
        /** @type {__VLS_StyleScopedClasses['trend-chart-nav']} */ ;
        /** @type {__VLS_StyleScopedClasses['trend-chart-nav-left']} */ ;
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ref: "trendChartRef",
        ...{ class: "trend-chart" },
        ...{ style: ({ height: __VLS_ctx.chartHeight }) },
    });
    /** @type {__VLS_StyleScopedClasses['trend-chart']} */ ;
    if (!__VLS_ctx.isMobileViewport && __VLS_ctx.isComparisonMode && __VLS_ctx.comparisonPageCount > 1) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.selectedIdentityKey))
                        return;
                    if (!(!__VLS_ctx.isMobileViewport && __VLS_ctx.isComparisonMode && __VLS_ctx.comparisonPageCount > 1))
                        return;
                    __VLS_ctx.comparisonPageIndex += 1;
                    // @ts-ignore
                    [isMobileViewport, isComparisonMode, comparisonPageCount, comparisonPageIndex, comparisonPageIndex, chartHeight,];
                } },
            type: "button",
            ...{ class: "trend-chart-nav trend-chart-nav-right" },
            disabled: (__VLS_ctx.comparisonPageIndex >= __VLS_ctx.comparisonPageCount - 1),
        });
        /** @type {__VLS_StyleScopedClasses['trend-chart-nav']} */ ;
        /** @type {__VLS_StyleScopedClasses['trend-chart-nav-right']} */ ;
    }
    if (!__VLS_ctx.isMobileViewport && __VLS_ctx.isComparisonMode && __VLS_ctx.comparisonPageCount > 1) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-chart-page-indicator" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-chart-page-indicator']} */ ;
        (__VLS_ctx.comparisonPageIndex + 1);
        (__VLS_ctx.comparisonPageCount);
    }
    if (__VLS_ctx.isMobileViewport && __VLS_ctx.isComparisonMode && __VLS_ctx.comparisonPageCount > 1) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-chart-mobile-nav" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-chart-mobile-nav']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-chart-mobile-buttons" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-chart-mobile-buttons']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.selectedIdentityKey))
                        return;
                    if (!(__VLS_ctx.isMobileViewport && __VLS_ctx.isComparisonMode && __VLS_ctx.comparisonPageCount > 1))
                        return;
                    __VLS_ctx.comparisonPageIndex -= 1;
                    // @ts-ignore
                    [isMobileViewport, isMobileViewport, isComparisonMode, isComparisonMode, comparisonPageCount, comparisonPageCount, comparisonPageCount, comparisonPageCount, comparisonPageIndex, comparisonPageIndex, comparisonPageIndex,];
                } },
            type: "button",
            ...{ class: "trend-chart-mobile-button" },
            'aria-label': "查看上一组趋势",
            disabled: (__VLS_ctx.comparisonPageIndex <= 0),
        });
        /** @type {__VLS_StyleScopedClasses['trend-chart-mobile-button']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.selectedIdentityKey))
                        return;
                    if (!(__VLS_ctx.isMobileViewport && __VLS_ctx.isComparisonMode && __VLS_ctx.comparisonPageCount > 1))
                        return;
                    __VLS_ctx.comparisonPageIndex += 1;
                    // @ts-ignore
                    [comparisonPageIndex, comparisonPageIndex,];
                } },
            type: "button",
            ...{ class: "trend-chart-mobile-button" },
            'aria-label': "查看下一组趋势",
            disabled: (__VLS_ctx.comparisonPageIndex >= __VLS_ctx.comparisonPageCount - 1),
        });
        /** @type {__VLS_StyleScopedClasses['trend-chart-mobile-button']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "trend-chart-mobile-indicator" },
            'data-testid': "trend-mobile-page-indicator",
        });
        /** @type {__VLS_StyleScopedClasses['trend-chart-mobile-indicator']} */ ;
        (__VLS_ctx.comparisonPageIndex + 1);
        (__VLS_ctx.comparisonPageCount);
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "trend-list-shell" },
        ...{ class: ({ compact: __VLS_ctx.isMobileViewport }) },
    });
    /** @type {__VLS_StyleScopedClasses['trend-list-shell']} */ ;
    /** @type {__VLS_StyleScopedClasses['compact']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "trend-list-head" },
    });
    /** @type {__VLS_StyleScopedClasses['trend-list-head']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (__VLS_ctx.trendListCountLabel);
    if (__VLS_ctx.recentTrendRows.length) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-list" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-list']} */ ;
        for (const [row] of __VLS_vFor((__VLS_ctx.recentTrendRows))) {
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                key: (`${row.trend_series_key || row.site_name}-${row.captured_at}-${row.current_price}`),
                ...{ class: "trend-row" },
            });
            /** @type {__VLS_StyleScopedClasses['trend-row']} */ ;
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
            __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
            (__VLS_ctx.buildTrendSeriesName(row));
            __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
            (__VLS_ctx.buildTrendMeta(row));
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                ...{ class: "trend-price" },
            });
            /** @type {__VLS_StyleScopedClasses['trend-price']} */ ;
            (__VLS_ctx.formatPrice(row.current_price));
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                ...{ class: "trend-time" },
            });
            /** @type {__VLS_StyleScopedClasses['trend-time']} */ ;
            (__VLS_ctx.formatTrendTime(row.captured_at));
            // @ts-ignore
            [isMobileViewport, comparisonPageCount, comparisonPageCount, comparisonPageIndex, comparisonPageIndex, trendListCountLabel, recentTrendRows, recentTrendRows, buildTrendSeriesName, buildTrendMeta, formatPrice, formatTrendTime,];
        }
    }
    else {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-side-empty" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-side-empty']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
    }
    if (__VLS_ctx.loading) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-loading-mask" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-loading-mask']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "trend-loading-card" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-loading-card']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "trend-loading-dot" },
        });
        /** @type {__VLS_StyleScopedClasses['trend-loading-dot']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
    }
}
else {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "table-empty-state trend-empty-state" },
    });
    /** @type {__VLS_StyleScopedClasses['table-empty-state']} */ ;
    /** @type {__VLS_StyleScopedClasses['trend-empty-state']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
}
// @ts-ignore
[loading,];
const __VLS_export = (await import('vue')).defineComponent({
    __typeEmits: {},
    __typeProps: {},
});
export default {};
