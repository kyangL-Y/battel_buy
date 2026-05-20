/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="D:/nodejs/node_cache/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/props-fallback.d.ts" />
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { ElMessage } from 'element-plus/es/components/message/index.mjs';
import { dataSourceState, fetchCrawlStatus, fetchLocationOptions, fetchMarketSummary, fetchProductOptions, fetchProductSummary, fetchProductTrend, fetchSourceCoverage, generateMenuPlan, triggerCrawlRun, updateCrawlSchedule } from './api';
import { useViewport } from './composables/useViewport';
const MarketSummaryPanel = defineAsyncComponent(() => import('./components/MarketSummaryPanel.vue'));
const ProductTrendPanel = defineAsyncComponent(() => import('./components/ProductTrendPanel.vue'));
const MenuPlanPanel = defineAsyncComponent(() => import('./components/MenuPlanPanel.vue'));
const TopHeadlineCards = defineAsyncComponent(() => import('./components/TopHeadlineCards.vue'));
const { isMobileViewport } = useViewport();
const searchParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams();
const initialTab = searchParams.get('tab');
const MARKET_SUMMARY_INITIAL_LIMIT = 500;
const tabs = [
    { key: 'summary', label: '汇总行情', code: 'SUM' },
    { key: 'trend', label: '单品趋势', code: 'TRD' },
    { key: 'menu', label: '菜单采购', code: 'BUY' },
];
const tabHints = {
    summary: '查看汇总报价',
    trend: '查看价格走势',
    menu: '生成采购建议',
};
const defaultTab = tabs.some((item) => item.key === initialTab) ? initialTab : 'summary';
const activeTab = ref(defaultTab);
const provinces = ref([]);
const cities = ref([]);
const provinceCityMap = ref({});
const marketRows = ref([]);
const sourceCoverageRows = ref([]);
const productOptions = ref([]);
const selectedIdentityKey = ref('');
const selectedSiteName = ref('');
const selectedProductFallbackLabel = ref('');
const productSummary = ref(null);
const trendRows = ref([]);
const trendSiteOptions = ref([]);
const trendLoading = ref(false);
const trendMode = ref('cross_market');
const ingredientRows = ref([]);
const planRows = ref([]);
const menuPlanLoading = ref(false);
const crawlStatus = ref(null);
const pageError = ref('');
const summaryLoading = ref(false);
const locationLoading = ref(false);
const coverageLoading = ref(false);
const productOptionsLoading = ref(false);
const crawlActionLoading = ref(false);
const scheduleActionLoading = ref(false);
const dailyScheduleEnabled = ref(false);
const productOptionsContextKey = ref('');
let crawlStatusTimer;
let productOptionsPromise = null;
let trendRequestSequence = 0;
let trendPrefetchContextKey = '';
const trendPrefetchPromises = new Map();
const filters = reactive({
    province: '',
    city: '',
    keyword: '',
});
const menuForm = reactive({
    menuText: '',
    tables: 10,
    diners: 100,
    preferredLocation: '',
});
const parsedMenuCount = computed(() => menuForm.menuText.split('\n').map((item) => item.trim()).filter(Boolean).length);
const matchedPlanCount = computed(() => planRows.value.filter((item) => item.price_status === '已匹配报价').length);
const pendingPlanCount = computed(() => planRows.value.filter((item) => item.price_status !== '已匹配报价').length);
const menuTotalCostLabel = computed(() => {
    const total = planRows.value.reduce((sum, item) => sum + (Number(item.estimated_cost) || 0), 0);
    return total > 0 ? `${total.toFixed(2)} 元` : '-';
});
const filteredCities = computed(() => {
    if (!filters.province) {
        return cities.value;
    }
    if (!Object.keys(provinceCityMap.value).length) {
        return [];
    }
    const provinceCities = provinceCityMap.value[filters.province] || [];
    return provinceCities;
});
const menuLocationCandidates = computed(() => {
    const options = ['当前位置'];
    for (const item of filteredCities.value) {
        if (item && !options.includes(item)) {
            options.push(item);
        }
    }
    for (const item of provinces.value) {
        if (item && !options.includes(item)) {
            options.push(item);
        }
    }
    return options;
});
const lowestPriceSignal = computed(() => {
    const rowsWithLowestPrice = marketRows.value.filter((item) => item.lowest_price != null && !Number.isNaN(Number(item.lowest_price)));
    if (!rowsWithLowestPrice.length) {
        return '暂无信号';
    }
    const bestRow = rowsWithLowestPrice.reduce((currentBest, row) => {
        if (!currentBest) {
            return row;
        }
        return Number(row.lowest_price) < Number(currentBest.lowest_price) ? row : currentBest;
    }, rowsWithLowestPrice[0]);
    return `${bestRow.product_name} · ${Number(bestRow.lowest_price).toFixed(2)}`;
});
const crawlResultLabel = computed(() => {
    if (!crawlStatus.value)
        return '暂无';
    if (crawlStatus.value.is_running)
        return '抓取中';
    const success = Number(crawlStatus.value.last_success_count || 0);
    const failed = Number(crawlStatus.value.last_failed_count || 0);
    if (!success && !failed)
        return '暂无';
    return `${success} 成功 / ${failed} 异常`;
});
const crawlProgressPercent = computed(() => {
    if (!crawlStatus.value)
        return 0;
    const reported = Number(crawlStatus.value.progress_percent || 0);
    return reported;
});
const crawlProgressLabel = computed(() => {
    if (!crawlStatus.value)
        return '等待获取';
    const completed = Number(crawlStatus.value.completed_sources || 0);
    const total = Number(crawlStatus.value.last_total_sources || 0);
    const currentIndex = Number(crawlStatus.value.current_source_index || 0);
    if (crawlStatus.value.is_running) {
        if (total) {
            const activeIndex = Math.max(currentIndex, completed + 1);
            const sourceProgress = Math.round(Number(crawlStatus.value.current_source_progress || 0) * 100);
            return `正在获取第 ${activeIndex}/${total} 个报价源 · 当前源 ${sourceProgress}%`;
        }
        return '准备抓取';
    }
    if (total) {
        return `最近一次完成 ${completed || total}/${total} 个报价源`;
    }
    return '等待获取';
});
const crawlLastFinishedLabel = computed(() => formatBeijingDateTime(crawlStatus.value?.last_finished_at, '暂无', true));
const crawlNextRunLabel = computed(() => formatBeijingDateTime(crawlStatus.value?.next_run_at, '未安排', true));
const selectedProductLabel = computed(() => {
    const current = productOptions.value.find((item) => item.price_identity_key === selectedIdentityKey.value);
    return current?.price_identity_label ?? selectedProductFallbackLabel.value;
});
const hasLiveSummary = computed(() => marketRows.value.length > 0);
const showBlockingError = computed(() => dataSourceState.mode === 'error' && !hasLiveSummary.value);
const activeTabMeta = computed(() => {
    if (activeTab.value === 'trend') {
        return {
            kicker: '价格走势',
            title: '单品趋势',
            description: '看同一商品在不同市场的价格变化。',
            metricLabel: '走势记录',
            metricValue: `${trendRows.value.length} 条`,
        };
    }
    if (activeTab.value === 'menu') {
        return {
            kicker: '菜单采购',
            title: '菜单采购',
            description: '拆菜单、比报价、生成采购建议。',
            metricLabel: '采购建议',
            metricValue: `${planRows.value.length} 条`,
        };
    }
    return {
        kicker: '汇总行情',
        title: '汇总行情',
        description: '按商品快速比较不同市场报价。',
        metricLabel: '汇总商品',
        metricValue: `${marketRows.value.length} 条`,
    };
});
const SUMMARY_CACHE_KEY = 'battel.market-summary.cache.v2';
const PRODUCT_OPTIONS_CACHE_KEY = 'battel.product-options.cache.v2';
const PRODUCT_SUMMARY_CACHE_KEY = 'battel.product-summary.cache.v2';
const PRODUCT_TREND_CACHE_KEY = 'battel.product-trend.cache.v2';
const BEIJING_DATE_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
});
const BEIJING_DATETIME_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
});
function buildFilterParams() {
    return {
        province: filters.province || undefined,
        city: filters.city || undefined,
    };
}
function formatBeijingDateTime(value, fallback = '暂无', compact = false) {
    if (!value)
        return fallback;
    const text = String(value).trim();
    if (!text)
        return fallback;
    const parsedDate = new Date(text.replace(' ', 'T'));
    if (Number.isNaN(parsedDate.getTime())) {
        return text;
    }
    const hasTime = /[T\s]\d{1,2}:\d{2}/.test(text);
    const parts = (hasTime ? BEIJING_DATETIME_FORMATTER : BEIJING_DATE_FORMATTER).formatToParts(parsedDate);
    const year = parts.find((item) => item.type === 'year')?.value ?? '';
    const month = parts.find((item) => item.type === 'month')?.value ?? '';
    const day = parts.find((item) => item.type === 'day')?.value ?? '';
    if (!hasTime) {
        return compact ? `${year}/${month}/${day}` : `${year}年${month}月${day}日`;
    }
    const hour = parts.find((item) => item.type === 'hour')?.value ?? '';
    const minute = parts.find((item) => item.type === 'minute')?.value ?? '';
    const second = parts.find((item) => item.type === 'second')?.value ?? '';
    return compact ? `${year}/${month}/${day} ${hour}:${minute}` : `${year}年${month}月${day}日 ${hour}:${minute}:${second}`;
}
function buildContextKey(params) {
    return JSON.stringify({
        province: params.province || '',
        city: params.city || '',
    });
}
function buildTrendRequestKey(identityKey, mode, siteKey) {
    return JSON.stringify({
        identityKey,
        mode,
        siteKey: siteKey || '',
    });
}
function extractTrendSiteOptions(rows) {
    return Array.from(new Set(rows
        .map((row) => row.trend_series_key || row.trend_series_name || row.site_name)
        .filter(Boolean)));
}
function getPrefetchSnapshotQueue(identityKey) {
    const existing = trendPrefetchPromises.get(identityKey);
    if (existing) {
        return existing;
    }
    const promise = prefetchTrendSnapshot(identityKey).finally(() => {
        trendPrefetchPromises.delete(identityKey);
    });
    trendPrefetchPromises.set(identityKey, promise);
    return promise;
}
function readLocalCache(storageKey, cacheKey) {
    if (typeof window === 'undefined')
        return null;
    try {
        const raw = window.localStorage.getItem(storageKey);
        if (!raw)
            return null;
        const payload = JSON.parse(raw);
        return payload[cacheKey] ?? null;
    }
    catch {
        return null;
    }
}
function writeLocalCache(storageKey, cacheKey, value) {
    if (typeof window === 'undefined')
        return;
    try {
        const raw = window.localStorage.getItem(storageKey);
        const payload = raw ? JSON.parse(raw) : {};
        payload[cacheKey] = value;
        window.localStorage.setItem(storageKey, JSON.stringify(payload));
    }
    catch {
        // Ignore cache write failures.
    }
}
function readSummaryCache(params) {
    const cacheKey = buildContextKey(params);
    const cached = readLocalCache(SUMMARY_CACHE_KEY, cacheKey);
    return Array.isArray(cached) ? cached : null;
}
function writeSummaryCache(params, rows) {
    writeLocalCache(SUMMARY_CACHE_KEY, buildContextKey(params), rows);
}
function appendMenuLines(lines) {
    const normalized = lines.map((item) => item.trim()).filter(Boolean);
    if (!normalized.length)
        return;
    const existing = menuForm.menuText.split('\n').map((item) => item.trim()).filter(Boolean);
    menuForm.menuText = [...existing, ...normalized].join('\n');
    ElMessage.success(`已导入 ${normalized.length} 条菜单项`);
}
function normalizeLocationList(values) {
    if (!Array.isArray(values)) {
        return [];
    }
    return Array.from(new Set(values
        .map((item) => String(item ?? '').trim())
        .filter(Boolean))).sort((left, right) => left.localeCompare(right, 'zh-CN'));
}
function normalizeProvinceCityMap(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) {
        return {};
    }
    const normalizedEntries = Object.entries(input)
        .map(([province, value]) => [String(province ?? '').trim(), normalizeLocationList(value)])
        .filter(([province]) => Boolean(province));
    return Object.fromEntries(normalizedEntries);
}
function pickPreferredProductOption(options) {
    if (!options.length) {
        return null;
    }
    const multiMarketOption = options.find((item) => Number(item.site_count || 0) > 1);
    return multiMarketOption || options[0];
}
function handleSelectProduct(identityKey) {
    const selectedRow = marketRows.value.find((item) => item.price_identity_key === identityKey);
    selectedProductFallbackLabel.value = selectedRow?.product_name || selectedProductFallbackLabel.value;
    if (selectedIdentityKey.value !== identityKey) {
        selectedSiteName.value = '';
    }
    selectedIdentityKey.value = identityKey;
    void prefetchNearbyTrendSnapshots(identityKey);
    if (activeTab.value !== 'trend') {
        void activateTab('trend');
    }
}
async function activateTab(tabKey) {
    const wasTrendTab = activeTab.value === 'trend';
    activeTab.value = tabKey;
    if (tabKey !== 'trend')
        return;
    await ensureProductOptionsLoaded();
    const firstOption = pickPreferredProductOption(productOptions.value);
    const identityKey = selectedIdentityKey.value || firstOption?.price_identity_key || '';
    if (!identityKey)
        return;
    if (!selectedIdentityKey.value) {
        selectedIdentityKey.value = identityKey;
        selectedProductFallbackLabel.value = firstOption?.price_identity_label || selectedProductFallbackLabel.value;
    }
    if (wasTrendTab && selectedIdentityKey.value === identityKey) {
        return;
    }
    await reloadTrend(identityKey);
}
async function reloadSummary() {
    summaryLoading.value = true;
    try {
        pageError.value = '';
        const params = buildFilterParams();
        const cachedRows = readSummaryCache(params);
        if (cachedRows?.length) {
            marketRows.value = cachedRows;
        }
        const summary = await fetchMarketSummary({ ...params, limit: MARKET_SUMMARY_INITIAL_LIMIT });
        marketRows.value = summary.items ?? [];
        writeSummaryCache(params, marketRows.value);
    }
    catch (error) {
        pageError.value = dataSourceState.lastError || '报价接口读取失败，请检查 API 服务';
    }
    finally {
        summaryLoading.value = false;
    }
}
async function reloadLocations(force = false) {
    if (locationLoading.value ||
        (!force && provinces.value.length > 0 && cities.value.length > 0 && Object.keys(provinceCityMap.value).length > 0)) {
        return;
    }
    locationLoading.value = true;
    try {
        const locationData = await fetchLocationOptions();
        provinces.value = normalizeLocationList(locationData.provinces);
        cities.value = normalizeLocationList(locationData.cities);
        provinceCityMap.value = normalizeProvinceCityMap(locationData.province_city_map);
    }
    catch (error) {
        pageError.value = dataSourceState.lastError || '地区选项读取失败，请检查 API 服务';
    }
    finally {
        locationLoading.value = false;
    }
}
async function handleCityDropdownVisible(visible) {
    if (!visible) {
        return;
    }
    if (!filters.province) {
        if (!cities.value.length) {
            await reloadLocations(true);
        }
        return;
    }
    const provinceCities = provinceCityMap.value[filters.province] || [];
    if (!provinceCities.length) {
        await reloadLocations(true);
    }
}
async function reloadSourceCoverage() {
    if (coverageLoading.value)
        return;
    coverageLoading.value = true;
    try {
        const sourceCoverageData = await fetchSourceCoverage();
        sourceCoverageRows.value = sourceCoverageData.items ?? [];
    }
    catch (error) {
        if (!sourceCoverageRows.value.length) {
            pageError.value = dataSourceState.lastError || '来源覆盖接口读取失败，请检查 API 服务';
        }
    }
    finally {
        coverageLoading.value = false;
    }
}
function stopCrawlPolling() {
    if (typeof window === 'undefined')
        return;
    if (crawlStatusTimer) {
        window.clearInterval(crawlStatusTimer);
        crawlStatusTimer = undefined;
    }
}
async function reloadCrawlStatus() {
    try {
        const data = await fetchCrawlStatus();
        crawlStatus.value = data.item ?? null;
        dailyScheduleEnabled.value = Boolean(data.item?.schedule_enabled);
    }
    catch (error) {
        // Keep previous crawl status if the endpoint is temporarily unavailable.
    }
}
function startCrawlPolling() {
    if (typeof window === 'undefined')
        return;
    stopCrawlPolling();
    crawlStatusTimer = window.setInterval(async () => {
        const wasRunning = Boolean(crawlStatus.value?.is_running);
        await reloadCrawlStatus();
        const isRunning = Boolean(crawlStatus.value?.is_running);
        if (wasRunning && !isRunning) {
            stopCrawlPolling();
            await reloadAll();
            await ensureProductOptionsLoaded(true);
            if (activeTab.value === 'trend') {
                await reloadTrend();
            }
            if (crawlStatus.value?.last_error) {
                ElMessage.warning(`抓取完成，但存在异常：${crawlStatus.value.last_error}`);
            }
            else {
                ElMessage.success('最新数据已重新获取');
            }
        }
    }, 3000);
}
async function handleManualCrawl() {
    crawlActionLoading.value = true;
    try {
        const data = await triggerCrawlRun();
        crawlStatus.value = data.item ?? null;
        if (data.accepted) {
            ElMessage.success('已开始抓取最新数据');
            startCrawlPolling();
        }
        else {
            ElMessage.warning('当前已有抓取任务在执行');
        }
    }
    catch (error) {
        ElMessage.error('启动抓取失败，请确认后端服务正常');
    }
    finally {
        crawlActionLoading.value = false;
    }
}
async function handleScheduleToggle(value) {
    scheduleActionLoading.value = true;
    try {
        const data = await updateCrawlSchedule({
            enabled: value,
            interval_seconds: 86400,
            fetch_mode: crawlStatus.value?.schedule_fetch_mode || 'requests',
        });
        crawlStatus.value = data.item ?? null;
        dailyScheduleEnabled.value = Boolean(data.item?.schedule_enabled);
        ElMessage.success(value ? '已开启每日自动获取' : '已关闭每日自动获取');
    }
    catch (error) {
        dailyScheduleEnabled.value = Boolean(crawlStatus.value?.schedule_enabled);
        ElMessage.error('更新自动获取设置失败');
    }
    finally {
        scheduleActionLoading.value = false;
    }
}
async function ensureProductOptionsLoaded(force = false) {
    const params = buildFilterParams();
    const contextKey = buildContextKey(params);
    if (!force) {
        const cachedOptions = readLocalCache(PRODUCT_OPTIONS_CACHE_KEY, contextKey);
        if (cachedOptions?.length && (!productOptions.value.length || productOptionsContextKey.value !== contextKey)) {
            productOptions.value = cachedOptions;
            productOptionsContextKey.value = contextKey;
            if (!selectedIdentityKey.value) {
                selectedIdentityKey.value = cachedOptions[0].price_identity_key;
                selectedProductFallbackLabel.value = cachedOptions[0].price_identity_label;
            }
        }
        if (productOptionsContextKey.value === contextKey && productOptions.value.length) {
            void prefetchTopTrendSnapshots(contextKey);
            return;
        }
    }
    if (productOptionsPromise && productOptionsLoading.value) {
        await productOptionsPromise;
        void prefetchTopTrendSnapshots(contextKey);
        return;
    }
    productOptionsPromise = (async () => {
        productOptionsLoading.value = true;
        try {
            const optionsData = await fetchProductOptions(params);
            productOptions.value = optionsData.items ?? [];
            productOptionsContextKey.value = contextKey;
            writeLocalCache(PRODUCT_OPTIONS_CACHE_KEY, contextKey, productOptions.value);
            if (!selectedIdentityKey.value && productOptions.value.length) {
                const preferredOption = pickPreferredProductOption(productOptions.value);
                selectedIdentityKey.value = preferredOption?.price_identity_key || '';
                selectedProductFallbackLabel.value = preferredOption?.price_identity_label || '';
            }
        }
        catch (error) {
            if (!productOptions.value.length) {
                productOptions.value = [];
                productOptionsContextKey.value = '';
            }
            pageError.value = dataSourceState.lastError || '商品列表接口读取失败，请检查 API 服务';
        }
        finally {
            productOptionsLoading.value = false;
            productOptionsPromise = null;
        }
    })();
    await productOptionsPromise;
    void prefetchTopTrendSnapshots(contextKey);
}
async function reloadAll() {
    await reloadSummary();
    void reloadSourceCoverage();
    void reloadCrawlStatus();
}
async function reloadTrend(identityKeyOverride) {
    const identityKey = identityKeyOverride || selectedIdentityKey.value;
    if (!identityKey) {
        productSummary.value = null;
        trendRows.value = [];
        trendSiteOptions.value = [];
        selectedSiteName.value = '';
        trendLoading.value = false;
        return;
    }
    const requestId = ++trendRequestSequence;
    trendLoading.value = true;
    const summaryCacheKey = identityKey;
    const summaryCached = readLocalCache(PRODUCT_SUMMARY_CACHE_KEY, summaryCacheKey);
    if (summaryCached) {
        productSummary.value = summaryCached;
    }
    else {
        productSummary.value = null;
    }
    const currentSiteKey = selectedSiteName.value || undefined;
    const currentTrendCacheKey = buildTrendRequestKey(identityKey, trendMode.value, currentSiteKey);
    const crossMarketTrendCacheKey = buildTrendRequestKey(identityKey, 'cross_market');
    const cachedTrendRows = readLocalCache(PRODUCT_TREND_CACHE_KEY, currentTrendCacheKey);
    const cachedCrossMarketRows = readLocalCache(PRODUCT_TREND_CACHE_KEY, crossMarketTrendCacheKey);
    const usedCachedTrend = Boolean(cachedTrendRows?.length);
    if (cachedTrendRows?.length) {
        trendRows.value = cachedTrendRows;
    }
    if (cachedCrossMarketRows?.length) {
        trendSiteOptions.value = extractTrendSiteOptions(cachedCrossMarketRows);
    }
    else if (trendMode.value === 'cross_market' && cachedTrendRows?.length) {
        trendSiteOptions.value = extractTrendSiteOptions(cachedTrendRows);
    }
    else {
        trendSiteOptions.value = [];
    }
    try {
        const filterParams = buildFilterParams();
        const summaryRequest = fetchProductSummary(identityKey, filterParams);
        const loadCrossMarketRows = async () => {
            if (cachedCrossMarketRows?.length) {
                return cachedCrossMarketRows;
            }
            const response = await fetchProductTrend(identityKey, { mode: 'cross_market', ...filterParams });
            const rows = response.items ?? [];
            writeLocalCache(PRODUCT_TREND_CACHE_KEY, crossMarketTrendCacheKey, rows);
            return rows;
        };
        let trend;
        if (trendMode.value === 'single_market') {
            const crossMarketRows = await loadCrossMarketRows();
            trendSiteOptions.value = extractTrendSiteOptions(crossMarketRows);
            const siteName = selectedSiteName.value || trendSiteOptions.value[0] || '';
            if (siteName && selectedSiteName.value !== siteName) {
                selectedSiteName.value = siteName;
            }
            trend = siteName
                ? await fetchProductTrend(identityKey, {
                    mode: 'single_market',
                    series_key: siteName,
                    ...filterParams,
                })
                : { items: [] };
        }
        else {
            trend = await fetchProductTrend(identityKey, {
                mode: 'cross_market',
                ...filterParams,
            });
            const crossMarketRows = trend.items ?? [];
            trendSiteOptions.value = extractTrendSiteOptions(crossMarketRows);
            writeLocalCache(PRODUCT_TREND_CACHE_KEY, crossMarketTrendCacheKey, crossMarketRows);
        }
        const summary = await summaryRequest;
        if (requestId !== trendRequestSequence || identityKey !== selectedIdentityKey.value) {
            return;
        }
        productSummary.value = summary.item ?? null;
        if (productSummary.value) {
            writeLocalCache(PRODUCT_SUMMARY_CACHE_KEY, summaryCacheKey, productSummary.value);
        }
        trendRows.value = trend.items ?? [];
        writeLocalCache(PRODUCT_TREND_CACHE_KEY, buildTrendRequestKey(identityKey, trendMode.value, selectedSiteName.value), trendRows.value);
        void prefetchNearbyTrendSnapshots(identityKey);
    }
    catch (error) {
        if (requestId !== trendRequestSequence || identityKey !== selectedIdentityKey.value) {
            return;
        }
        pageError.value = dataSourceState.lastError || '趋势接口读取失败，请检查 API 服务';
        if (!usedCachedTrend) {
            trendRows.value = [];
        }
    }
    finally {
        if (requestId === trendRequestSequence && identityKey === selectedIdentityKey.value) {
            trendLoading.value = false;
        }
    }
}
async function prefetchTrendSnapshot(identityKey) {
    if (!identityKey)
        return;
    const summaryCacheKey = identityKey;
    const trendCacheKey = buildTrendRequestKey(identityKey, 'cross_market');
    const cachedSummary = readLocalCache(PRODUCT_SUMMARY_CACHE_KEY, summaryCacheKey);
    const cachedTrend = readLocalCache(PRODUCT_TREND_CACHE_KEY, trendCacheKey);
    if (cachedSummary && cachedTrend?.length) {
        return;
    }
    try {
        const [summary, trend] = await Promise.all([
            cachedSummary ? Promise.resolve({ item: cachedSummary }) : fetchProductSummary(identityKey, buildFilterParams()),
            cachedTrend?.length ? Promise.resolve({ items: cachedTrend }) : fetchProductTrend(identityKey, { mode: 'cross_market', ...buildFilterParams() }),
        ]);
        if (summary.item) {
            writeLocalCache(PRODUCT_SUMMARY_CACHE_KEY, summaryCacheKey, summary.item);
        }
        if (trend.items?.length) {
            writeLocalCache(PRODUCT_TREND_CACHE_KEY, trendCacheKey, trend.items);
        }
    }
    catch {
        // Ignore prefetch failures and keep interactive fetch as fallback.
    }
}
async function prefetchTopTrendSnapshots(contextKey) {
    if (!productOptions.value.length)
        return;
    trendPrefetchContextKey = contextKey;
    const keys = productOptions.value
        .slice(0, 12)
        .map((item) => item.price_identity_key)
        .filter(Boolean);
    await runPrefetchQueue(keys, contextKey);
}
async function prefetchNearbyTrendSnapshots(identityKey) {
    if (!identityKey || !productOptions.value.length)
        return;
    const contextKey = buildContextKey(buildFilterParams());
    const currentIndex = productOptions.value.findIndex((item) => item.price_identity_key === identityKey);
    if (currentIndex < 0)
        return;
    const keys = productOptions.value
        .slice(Math.max(0, currentIndex - 3), currentIndex + 4)
        .map((item) => item.price_identity_key)
        .filter(Boolean);
    await runPrefetchQueue(keys, contextKey);
}
async function runPrefetchQueue(identityKeys, contextKey) {
    const uniqueKeys = Array.from(new Set(identityKeys.filter(Boolean)));
    if (!uniqueKeys.length)
        return;
    trendPrefetchContextKey = contextKey;
    const concurrency = Math.min(3, uniqueKeys.length);
    let cursor = 0;
    await Promise.all(Array.from({ length: concurrency }, async () => {
        while (cursor < uniqueKeys.length) {
            if (trendPrefetchContextKey !== contextKey) {
                return;
            }
            const key = uniqueKeys[cursor];
            cursor += 1;
            await getPrefetchSnapshotQueue(key);
        }
    }));
}
async function submitMenuPlan() {
    menuPlanLoading.value = true;
    try {
        const data = await generateMenuPlan({
            menu_text: menuForm.menuText,
            diners: menuForm.diners,
            tables: menuForm.tables,
            preferred_province: filters.province || undefined,
            preferred_city: filters.city || undefined,
            preferred_location: menuForm.preferredLocation || undefined,
        });
        ingredientRows.value = data.ingredient_items ?? [];
        planRows.value = data.procurement_plan ?? [];
        ElMessage.success('采购方案已生成');
    }
    catch (error) {
        ElMessage.error('采购方案生成失败，请确认 API 已启动');
    }
    finally {
        menuPlanLoading.value = false;
    }
}
watch([() => filters.province, () => filters.city], async () => {
    productOptions.value = [];
    productOptionsContextKey.value = '';
    selectedIdentityKey.value = '';
    selectedSiteName.value = '';
    selectedProductFallbackLabel.value = '';
    trendLoading.value = false;
    trendPrefetchContextKey = '';
    await reloadAll();
});
watch(() => filters.province, async (province) => {
    if (province && !(provinceCityMap.value[province] || []).length) {
        await reloadLocations(true);
    }
    const availableCities = province ? (provinceCityMap.value[province] || []) : cities.value;
    if (filters.city && !availableCities.includes(filters.city)) {
        filters.city = '';
    }
    const locationCandidates = new Set(['当前位置', ...availableCities, ...provinces.value]);
    if (menuForm.preferredLocation && !locationCandidates.has(menuForm.preferredLocation)) {
        menuForm.preferredLocation = '';
    }
});
watch([selectedIdentityKey, trendMode, selectedSiteName], async ([identityKey, mode, site], [prevIdentityKey, prevMode, prevSite]) => {
    if (activeTab.value !== 'trend')
        return;
    if (!identityKey)
        return;
    if (identityKey === prevIdentityKey && mode === prevMode && site === prevSite)
        return;
    await reloadTrend();
});
onMounted(async () => {
    void reloadLocations();
    await reloadAll();
    void ensureProductOptionsLoaded().then(() => {
        const identityKey = selectedIdentityKey.value || pickPreferredProductOption(productOptions.value)?.price_identity_key || '';
        if (identityKey && activeTab.value !== 'trend') {
            void prefetchTrendSnapshot(identityKey);
        }
    });
    if (activeTab.value === 'trend') {
        await activateTab('trend');
    }
    if (crawlStatus.value?.is_running) {
        startCrawlPolling();
    }
});
onBeforeUnmount(() => {
    stopCrawlPolling();
});
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_intrinsics;
let __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "app-shell dashboard-shell" },
});
/** @type {__VLS_StyleScopedClasses['app-shell']} */ ;
/** @type {__VLS_StyleScopedClasses['dashboard-shell']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.aside, __VLS_intrinsics.aside)({
    ...{ class: "control-rail" },
});
/** @type {__VLS_StyleScopedClasses['control-rail']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    ...{ class: "rail-card brand-card" },
});
/** @type {__VLS_StyleScopedClasses['rail-card']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-card']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "brand-lockup" },
});
/** @type {__VLS_StyleScopedClasses['brand-lockup']} */ ;
if (!__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "brand-mark" },
    });
    /** @type {__VLS_StyleScopedClasses['brand-mark']} */ ;
}
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "brand-stack" },
});
/** @type {__VLS_StyleScopedClasses['brand-stack']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "eyebrow" },
});
/** @type {__VLS_StyleScopedClasses['eyebrow']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h1, __VLS_intrinsics.h1)({
    ...{ class: "page-title" },
});
/** @type {__VLS_StyleScopedClasses['page-title']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "header-copy" },
});
/** @type {__VLS_StyleScopedClasses['header-copy']} */ ;
if (!__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "brand-notes" },
    });
    /** @type {__VLS_StyleScopedClasses['brand-notes']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
}
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    ...{ class: "rail-card rail-nav-card" },
});
/** @type {__VLS_StyleScopedClasses['rail-card']} */ ;
/** @type {__VLS_StyleScopedClasses['rail-nav-card']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "rail-section-head" },
});
/** @type {__VLS_StyleScopedClasses['rail-section-head']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "rail-section-kicker" },
});
/** @type {__VLS_StyleScopedClasses['rail-section-kicker']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "rail-tabs" },
});
/** @type {__VLS_StyleScopedClasses['rail-tabs']} */ ;
for (const [tab] of __VLS_vFor((__VLS_ctx.tabs))) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.activateTab(tab.key);
                // @ts-ignore
                [isMobileViewport, isMobileViewport, tabs, activateTab,];
            } },
        key: (tab.key),
        type: "button",
        ...{ class: "rail-tab" },
        'data-tab': (tab.key),
        ...{ class: ({ active: __VLS_ctx.activeTab === tab.key }) },
        'aria-label': (`切换到${tab.label}`),
        'aria-pressed': (__VLS_ctx.activeTab === tab.key),
    });
    /** @type {__VLS_StyleScopedClasses['rail-tab']} */ ;
    /** @type {__VLS_StyleScopedClasses['active']} */ ;
    if (!__VLS_ctx.isMobileViewport) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "rail-tab-icon" },
        });
        /** @type {__VLS_StyleScopedClasses['rail-tab-icon']} */ ;
        (tab.code);
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
        ...{ class: "rail-tab-copy" },
    });
    /** @type {__VLS_StyleScopedClasses['rail-tab-copy']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (tab.label);
    if (!__VLS_ctx.isMobileViewport) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (__VLS_ctx.tabHints[tab.key]);
    }
    // @ts-ignore
    [isMobileViewport, isMobileViewport, activeTab, activeTab, tabHints,];
}
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    ...{ class: "rail-card filter-card" },
});
/** @type {__VLS_StyleScopedClasses['rail-card']} */ ;
/** @type {__VLS_StyleScopedClasses['filter-card']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "rail-section-head" },
});
/** @type {__VLS_StyleScopedClasses['rail-section-head']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "rail-section-kicker" },
});
/** @type {__VLS_StyleScopedClasses['rail-section-kicker']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "rail-action-group" },
});
/** @type {__VLS_StyleScopedClasses['rail-action-group']} */ ;
let __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.elButton | typeof __VLS_components.ElButton | typeof __VLS_components.elButton | typeof __VLS_components.ElButton} */
elButton;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
    ...{ 'onClick': {} },
    type: "primary",
    loading: (__VLS_ctx.crawlActionLoading || __VLS_ctx.crawlStatus?.is_running),
}));
const __VLS_2 = __VLS_1({
    ...{ 'onClick': {} },
    type: "primary",
    loading: (__VLS_ctx.crawlActionLoading || __VLS_ctx.crawlStatus?.is_running),
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
let __VLS_5;
const __VLS_6 = ({ click: {} },
    { onClick: (__VLS_ctx.handleManualCrawl) });
const { default: __VLS_7 } = __VLS_3.slots;
// @ts-ignore
[crawlActionLoading, crawlStatus, handleManualCrawl,];
var __VLS_3;
var __VLS_4;
let __VLS_8;
/** @ts-ignore @type {typeof __VLS_components.elButton | typeof __VLS_components.ElButton | typeof __VLS_components.elButton | typeof __VLS_components.ElButton} */
elButton;
// @ts-ignore
const __VLS_9 = __VLS_asFunctionalComponent1(__VLS_8, new __VLS_8({
    ...{ 'onClick': {} },
}));
const __VLS_10 = __VLS_9({
    ...{ 'onClick': {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_9));
let __VLS_13;
const __VLS_14 = ({ click: {} },
    { onClick: (__VLS_ctx.reloadAll) });
const { default: __VLS_15 } = __VLS_11.slots;
// @ts-ignore
[reloadAll,];
var __VLS_11;
var __VLS_12;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "rail-filter-stack" },
});
/** @type {__VLS_StyleScopedClasses['rail-filter-stack']} */ ;
let __VLS_16;
/** @ts-ignore @type {typeof __VLS_components.elSelect | typeof __VLS_components.ElSelect | typeof __VLS_components.elSelect | typeof __VLS_components.ElSelect} */
elSelect;
// @ts-ignore
const __VLS_17 = __VLS_asFunctionalComponent1(__VLS_16, new __VLS_16({
    modelValue: (__VLS_ctx.filters.province),
    'aria-label': "省份筛选",
    clearable: true,
    filterable: true,
    placeholder: "省份筛选",
}));
const __VLS_18 = __VLS_17({
    modelValue: (__VLS_ctx.filters.province),
    'aria-label': "省份筛选",
    clearable: true,
    filterable: true,
    placeholder: "省份筛选",
}, ...__VLS_functionalComponentArgsRest(__VLS_17));
const { default: __VLS_21 } = __VLS_19.slots;
for (const [item] of __VLS_vFor((__VLS_ctx.provinces))) {
    let __VLS_22;
    /** @ts-ignore @type {typeof __VLS_components.elOption | typeof __VLS_components.ElOption} */
    elOption;
    // @ts-ignore
    const __VLS_23 = __VLS_asFunctionalComponent1(__VLS_22, new __VLS_22({
        key: (item),
        label: (item),
        value: (item),
    }));
    const __VLS_24 = __VLS_23({
        key: (item),
        label: (item),
        value: (item),
    }, ...__VLS_functionalComponentArgsRest(__VLS_23));
    // @ts-ignore
    [filters, provinces,];
}
// @ts-ignore
[];
var __VLS_19;
let __VLS_27;
/** @ts-ignore @type {typeof __VLS_components.elSelect | typeof __VLS_components.ElSelect | typeof __VLS_components.elSelect | typeof __VLS_components.ElSelect} */
elSelect;
// @ts-ignore
const __VLS_28 = __VLS_asFunctionalComponent1(__VLS_27, new __VLS_27({
    ...{ 'onVisibleChange': {} },
    key: (__VLS_ctx.filters.province || 'all-cities'),
    modelValue: (__VLS_ctx.filters.city),
    'aria-label': "城市筛选",
    clearable: true,
    filterable: true,
    loading: (__VLS_ctx.locationLoading),
    placeholder: (__VLS_ctx.filters.province ? '选择该省城市' : '城市优先'),
}));
const __VLS_29 = __VLS_28({
    ...{ 'onVisibleChange': {} },
    key: (__VLS_ctx.filters.province || 'all-cities'),
    modelValue: (__VLS_ctx.filters.city),
    'aria-label': "城市筛选",
    clearable: true,
    filterable: true,
    loading: (__VLS_ctx.locationLoading),
    placeholder: (__VLS_ctx.filters.province ? '选择该省城市' : '城市优先'),
}, ...__VLS_functionalComponentArgsRest(__VLS_28));
let __VLS_32;
const __VLS_33 = ({ visibleChange: {} },
    { onVisibleChange: (__VLS_ctx.handleCityDropdownVisible) });
const { default: __VLS_34 } = __VLS_30.slots;
for (const [item] of __VLS_vFor((__VLS_ctx.filteredCities))) {
    let __VLS_35;
    /** @ts-ignore @type {typeof __VLS_components.elOption | typeof __VLS_components.ElOption} */
    elOption;
    // @ts-ignore
    const __VLS_36 = __VLS_asFunctionalComponent1(__VLS_35, new __VLS_35({
        key: (item),
        label: (item),
        value: (item),
    }));
    const __VLS_37 = __VLS_36({
        key: (item),
        label: (item),
        value: (item),
    }, ...__VLS_functionalComponentArgsRest(__VLS_36));
    // @ts-ignore
    [filters, filters, filters, locationLoading, handleCityDropdownVisible, filteredCities,];
}
// @ts-ignore
[];
var __VLS_30;
var __VLS_31;
let __VLS_40;
/** @ts-ignore @type {typeof __VLS_components.elInput | typeof __VLS_components.ElInput} */
elInput;
// @ts-ignore
const __VLS_41 = __VLS_asFunctionalComponent1(__VLS_40, new __VLS_40({
    modelValue: (__VLS_ctx.filters.keyword),
    type: "search",
    inputmode: "search",
    enterkeyhint: "search",
    'aria-label': "搜索商品关键词",
    placeholder: "搜索商品关键词",
    clearable: true,
}));
const __VLS_42 = __VLS_41({
    modelValue: (__VLS_ctx.filters.keyword),
    type: "search",
    inputmode: "search",
    enterkeyhint: "search",
    'aria-label': "搜索商品关键词",
    placeholder: "搜索商品关键词",
    clearable: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_41));
if (!__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "rail-context-inline" },
    });
    /** @type {__VLS_StyleScopedClasses['rail-context-inline']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "rail-inline-pill" },
    });
    /** @type {__VLS_StyleScopedClasses['rail-inline-pill']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.filters.city || __VLS_ctx.filters.province || '全部市场');
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "rail-inline-pill" },
    });
    /** @type {__VLS_StyleScopedClasses['rail-inline-pill']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.selectedProductLabel || '未选择');
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "rail-inline-pill" },
    });
    /** @type {__VLS_StyleScopedClasses['rail-inline-pill']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.marketRows.length);
}
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "crawl-ops-card" },
});
/** @type {__VLS_StyleScopedClasses['crawl-ops-card']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "crawl-ops-head" },
});
/** @type {__VLS_StyleScopedClasses['crawl-ops-head']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "rail-section-kicker" },
});
/** @type {__VLS_StyleScopedClasses['rail-section-kicker']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h3, __VLS_intrinsics.h3)({});
let __VLS_45;
/** @ts-ignore @type {typeof __VLS_components.elSwitch | typeof __VLS_components.ElSwitch} */
elSwitch;
// @ts-ignore
const __VLS_46 = __VLS_asFunctionalComponent1(__VLS_45, new __VLS_45({
    ...{ 'onChange': {} },
    modelValue: (__VLS_ctx.dailyScheduleEnabled),
    loading: (__VLS_ctx.scheduleActionLoading),
    inlinePrompt: true,
    activeText: "开",
    inactiveText: "关",
}));
const __VLS_47 = __VLS_46({
    ...{ 'onChange': {} },
    modelValue: (__VLS_ctx.dailyScheduleEnabled),
    loading: (__VLS_ctx.scheduleActionLoading),
    inlinePrompt: true,
    activeText: "开",
    inactiveText: "关",
}, ...__VLS_functionalComponentArgsRest(__VLS_46));
let __VLS_50;
const __VLS_51 = ({ change: {} },
    { onChange: (__VLS_ctx.handleScheduleToggle) });
var __VLS_48;
var __VLS_49;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "crawl-progress-wrap" },
});
/** @type {__VLS_StyleScopedClasses['crawl-progress-wrap']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "crawl-progress-head" },
});
/** @type {__VLS_StyleScopedClasses['crawl-progress-head']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
(__VLS_ctx.crawlProgressLabel);
__VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
(__VLS_ctx.crawlProgressPercent);
let __VLS_52;
/** @ts-ignore @type {typeof __VLS_components.elProgress | typeof __VLS_components.ElProgress} */
elProgress;
// @ts-ignore
const __VLS_53 = __VLS_asFunctionalComponent1(__VLS_52, new __VLS_52({
    percentage: (__VLS_ctx.crawlProgressPercent),
    strokeWidth: (10),
    showText: (false),
    status: (__VLS_ctx.crawlStatus?.is_running ? undefined : 'success'),
}));
const __VLS_54 = __VLS_53({
    percentage: (__VLS_ctx.crawlProgressPercent),
    strokeWidth: (10),
    showText: (false),
    status: (__VLS_ctx.crawlStatus?.is_running ? undefined : 'success'),
}, ...__VLS_functionalComponentArgsRest(__VLS_53));
if (__VLS_ctx.crawlStatus?.is_running && __VLS_ctx.crawlStatus?.current_source_name) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
        ...{ class: "crawl-progress-note" },
    });
    /** @type {__VLS_StyleScopedClasses['crawl-progress-note']} */ ;
    (__VLS_ctx.crawlStatus.current_source_name);
}
if (__VLS_ctx.crawlStatus?.is_running && __VLS_ctx.crawlStatus?.current_source_detail) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
        ...{ class: "crawl-progress-note secondary" },
    });
    /** @type {__VLS_StyleScopedClasses['crawl-progress-note']} */ ;
    /** @type {__VLS_StyleScopedClasses['secondary']} */ ;
    (__VLS_ctx.crawlStatus.current_source_detail);
}
if (__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "crawl-compact-inline" },
    });
    /** @type {__VLS_StyleScopedClasses['crawl-compact-inline']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "crawl-mini-stat" },
    });
    /** @type {__VLS_StyleScopedClasses['crawl-mini-stat']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.dailyScheduleEnabled ? '每日开启' : '已关闭');
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "crawl-mini-stat" },
    });
    /** @type {__VLS_StyleScopedClasses['crawl-mini-stat']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.crawlResultLabel);
}
else {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "crawl-ops-grid" },
    });
    /** @type {__VLS_StyleScopedClasses['crawl-ops-grid']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "crawl-mini-stat" },
    });
    /** @type {__VLS_StyleScopedClasses['crawl-mini-stat']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.dailyScheduleEnabled ? '每日开启' : '已关闭');
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "crawl-mini-stat" },
    });
    /** @type {__VLS_StyleScopedClasses['crawl-mini-stat']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.crawlLastFinishedLabel);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "crawl-mini-stat" },
    });
    /** @type {__VLS_StyleScopedClasses['crawl-mini-stat']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.crawlNextRunLabel);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "crawl-mini-stat" },
    });
    /** @type {__VLS_StyleScopedClasses['crawl-mini-stat']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.crawlResultLabel);
}
if (__VLS_ctx.crawlStatus?.last_error) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
        ...{ class: "crawl-error-text" },
    });
    /** @type {__VLS_StyleScopedClasses['crawl-error-text']} */ ;
    (__VLS_ctx.crawlStatus.last_error);
}
__VLS_asFunctionalElement1(__VLS_intrinsics.main, __VLS_intrinsics.main)({
    ...{ class: "workspace-shell" },
});
/** @type {__VLS_StyleScopedClasses['workspace-shell']} */ ;
if (!__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
        ...{ class: "workspace-topbar" },
    });
    /** @type {__VLS_StyleScopedClasses['workspace-topbar']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "workspace-topbar-copy" },
    });
    /** @type {__VLS_StyleScopedClasses['workspace-topbar-copy']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "workspace-heading-row" },
    });
    /** @type {__VLS_StyleScopedClasses['workspace-heading-row']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
        ...{ class: "workspace-kicker" },
    });
    /** @type {__VLS_StyleScopedClasses['workspace-kicker']} */ ;
    (__VLS_ctx.activeTabMeta.kicker);
    __VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
    (__VLS_ctx.activeTabMeta.title);
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
        ...{ class: "workspace-subcopy" },
    });
    /** @type {__VLS_StyleScopedClasses['workspace-subcopy']} */ ;
    (__VLS_ctx.activeTabMeta.description);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "workspace-topbar-chips" },
    });
    /** @type {__VLS_StyleScopedClasses['workspace-topbar-chips']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "workspace-mini-chip" },
    });
    /** @type {__VLS_StyleScopedClasses['workspace-mini-chip']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.filters.city || __VLS_ctx.filters.province || '全部市场');
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "workspace-mini-chip" },
    });
    /** @type {__VLS_StyleScopedClasses['workspace-mini-chip']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (__VLS_ctx.activeTabMeta.metricLabel);
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.activeTabMeta.metricValue);
    if (__VLS_ctx.selectedProductLabel) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "workspace-mini-chip accent-chip" },
        });
        /** @type {__VLS_StyleScopedClasses['workspace-mini-chip']} */ ;
        /** @type {__VLS_StyleScopedClasses['accent-chip']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.selectedProductLabel);
    }
}
if (__VLS_ctx.showBlockingError) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
        ...{ class: "active-strip compact source-warning-strip" },
    });
    /** @type {__VLS_StyleScopedClasses['active-strip']} */ ;
    /** @type {__VLS_StyleScopedClasses['compact']} */ ;
    /** @type {__VLS_StyleScopedClasses['source-warning-strip']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
        ...{ class: "active-strip-copy" },
    });
    /** @type {__VLS_StyleScopedClasses['active-strip-copy']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "source-warning-text" },
    });
    /** @type {__VLS_StyleScopedClasses['source-warning-text']} */ ;
    (__VLS_ctx.pageError || __VLS_ctx.dataSourceState.lastError || '接口连接失败');
}
if (!__VLS_ctx.isMobileViewport) {
    let __VLS_57;
    /** @ts-ignore @type {typeof __VLS_components.TopHeadlineCards} */
    TopHeadlineCards;
    // @ts-ignore
    const __VLS_58 = __VLS_asFunctionalComponent1(__VLS_57, new __VLS_57({
        marketRowCount: (__VLS_ctx.marketRows.length),
        lowestPriceSignal: (__VLS_ctx.lowestPriceSignal),
        productSummary: (__VLS_ctx.productSummary),
        menuTotalCostLabel: (__VLS_ctx.menuTotalCostLabel),
    }));
    const __VLS_59 = __VLS_58({
        marketRowCount: (__VLS_ctx.marketRows.length),
        lowestPriceSignal: (__VLS_ctx.lowestPriceSignal),
        productSummary: (__VLS_ctx.productSummary),
        menuTotalCostLabel: (__VLS_ctx.menuTotalCostLabel),
    }, ...__VLS_functionalComponentArgsRest(__VLS_58));
}
__VLS_asFunctionalElement1(__VLS_intrinsics.main, __VLS_intrinsics.main)({
    ...{ class: "content-area" },
});
/** @type {__VLS_StyleScopedClasses['content-area']} */ ;
if (__VLS_ctx.activeTab === 'summary') {
    let __VLS_62;
    /** @ts-ignore @type {typeof __VLS_components.MarketSummaryPanel} */
    MarketSummaryPanel;
    // @ts-ignore
    const __VLS_63 = __VLS_asFunctionalComponent1(__VLS_62, new __VLS_62({
        ...{ 'onKeywordChange': {} },
        ...{ 'onSelectProduct': {} },
        rows: (__VLS_ctx.marketRows),
        sourceCoverageRows: (__VLS_ctx.sourceCoverageRows),
        keyword: (__VLS_ctx.filters.keyword),
        loading: (__VLS_ctx.summaryLoading),
    }));
    const __VLS_64 = __VLS_63({
        ...{ 'onKeywordChange': {} },
        ...{ 'onSelectProduct': {} },
        rows: (__VLS_ctx.marketRows),
        sourceCoverageRows: (__VLS_ctx.sourceCoverageRows),
        keyword: (__VLS_ctx.filters.keyword),
        loading: (__VLS_ctx.summaryLoading),
    }, ...__VLS_functionalComponentArgsRest(__VLS_63));
    let __VLS_67;
    const __VLS_68 = ({ keywordChange: {} },
        { onKeywordChange: (...[$event]) => {
                if (!(__VLS_ctx.activeTab === 'summary'))
                    return;
                __VLS_ctx.filters.keyword = $event;
                // @ts-ignore
                [isMobileViewport, isMobileViewport, isMobileViewport, isMobileViewport, activeTab, crawlStatus, crawlStatus, crawlStatus, crawlStatus, crawlStatus, crawlStatus, crawlStatus, crawlStatus, crawlStatus, filters, filters, filters, filters, filters, filters, filters, selectedProductLabel, selectedProductLabel, selectedProductLabel, marketRows, marketRows, marketRows, dailyScheduleEnabled, dailyScheduleEnabled, dailyScheduleEnabled, scheduleActionLoading, handleScheduleToggle, crawlProgressLabel, crawlProgressPercent, crawlProgressPercent, crawlResultLabel, crawlResultLabel, crawlLastFinishedLabel, crawlNextRunLabel, activeTabMeta, activeTabMeta, activeTabMeta, activeTabMeta, activeTabMeta, showBlockingError, pageError, dataSourceState, lowestPriceSignal, productSummary, menuTotalCostLabel, sourceCoverageRows, summaryLoading,];
            } });
    const __VLS_69 = ({ selectProduct: {} },
        { onSelectProduct: (__VLS_ctx.handleSelectProduct) });
    var __VLS_65;
    var __VLS_66;
}
if (__VLS_ctx.activeTab !== 'summary') {
    __VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
        ...{ class: "detail-workspace" },
    });
    /** @type {__VLS_StyleScopedClasses['detail-workspace']} */ ;
    if (__VLS_ctx.activeTab === 'trend') {
        let __VLS_70;
        /** @ts-ignore @type {typeof __VLS_components.ProductTrendPanel} */
        ProductTrendPanel;
        // @ts-ignore
        const __VLS_71 = __VLS_asFunctionalComponent1(__VLS_70, new __VLS_70({
            ...{ 'onSelectProduct': {} },
            ...{ 'onUpdate:trendMode': {} },
            ...{ 'onUpdate:selectedSiteName': {} },
            ...{ 'onRefreshTrend': {} },
            productOptions: (__VLS_ctx.productOptions),
            selectedIdentityKey: (__VLS_ctx.selectedIdentityKey),
            productSummary: (__VLS_ctx.productSummary),
            trendRows: (__VLS_ctx.trendRows),
            siteOptions: (__VLS_ctx.trendSiteOptions),
            loading: (__VLS_ctx.trendLoading),
            trendMode: (__VLS_ctx.trendMode),
            selectedSiteName: (__VLS_ctx.selectedSiteName),
        }));
        const __VLS_72 = __VLS_71({
            ...{ 'onSelectProduct': {} },
            ...{ 'onUpdate:trendMode': {} },
            ...{ 'onUpdate:selectedSiteName': {} },
            ...{ 'onRefreshTrend': {} },
            productOptions: (__VLS_ctx.productOptions),
            selectedIdentityKey: (__VLS_ctx.selectedIdentityKey),
            productSummary: (__VLS_ctx.productSummary),
            trendRows: (__VLS_ctx.trendRows),
            siteOptions: (__VLS_ctx.trendSiteOptions),
            loading: (__VLS_ctx.trendLoading),
            trendMode: (__VLS_ctx.trendMode),
            selectedSiteName: (__VLS_ctx.selectedSiteName),
        }, ...__VLS_functionalComponentArgsRest(__VLS_71));
        let __VLS_75;
        const __VLS_76 = ({ selectProduct: {} },
            { onSelectProduct: (__VLS_ctx.handleSelectProduct) });
        const __VLS_77 = ({ 'update:trendMode': {} },
            { 'onUpdate:trendMode': (...[$event]) => {
                    if (!(__VLS_ctx.activeTab !== 'summary'))
                        return;
                    if (!(__VLS_ctx.activeTab === 'trend'))
                        return;
                    __VLS_ctx.trendMode = $event;
                    // @ts-ignore
                    [activeTab, activeTab, productSummary, handleSelectProduct, handleSelectProduct, productOptions, selectedIdentityKey, trendRows, trendSiteOptions, trendLoading, trendMode, trendMode, selectedSiteName,];
                } });
        const __VLS_78 = ({ 'update:selectedSiteName': {} },
            { 'onUpdate:selectedSiteName': (...[$event]) => {
                    if (!(__VLS_ctx.activeTab !== 'summary'))
                        return;
                    if (!(__VLS_ctx.activeTab === 'trend'))
                        return;
                    __VLS_ctx.selectedSiteName = $event;
                    // @ts-ignore
                    [selectedSiteName,];
                } });
        const __VLS_79 = ({ refreshTrend: {} },
            { onRefreshTrend: (__VLS_ctx.reloadTrend) });
        var __VLS_73;
        var __VLS_74;
    }
    if (__VLS_ctx.activeTab === 'menu') {
        let __VLS_80;
        /** @ts-ignore @type {typeof __VLS_components.MenuPlanPanel} */
        MenuPlanPanel;
        // @ts-ignore
        const __VLS_81 = __VLS_asFunctionalComponent1(__VLS_80, new __VLS_80({
            ...{ 'onSubmit': {} },
            ...{ 'onImportLines': {} },
            menuText: (__VLS_ctx.menuForm.menuText),
            tables: (__VLS_ctx.menuForm.tables),
            diners: (__VLS_ctx.menuForm.diners),
            preferredLocation: (__VLS_ctx.menuForm.preferredLocation),
            locationCandidates: (__VLS_ctx.menuLocationCandidates),
            ingredientRows: (__VLS_ctx.ingredientRows),
            planRows: (__VLS_ctx.planRows),
            parsedMenuCount: (__VLS_ctx.parsedMenuCount),
            matchedPlanCount: (__VLS_ctx.matchedPlanCount),
            pendingPlanCount: (__VLS_ctx.pendingPlanCount),
            totalCostLabel: (__VLS_ctx.menuTotalCostLabel),
            loading: (__VLS_ctx.menuPlanLoading),
        }));
        const __VLS_82 = __VLS_81({
            ...{ 'onSubmit': {} },
            ...{ 'onImportLines': {} },
            menuText: (__VLS_ctx.menuForm.menuText),
            tables: (__VLS_ctx.menuForm.tables),
            diners: (__VLS_ctx.menuForm.diners),
            preferredLocation: (__VLS_ctx.menuForm.preferredLocation),
            locationCandidates: (__VLS_ctx.menuLocationCandidates),
            ingredientRows: (__VLS_ctx.ingredientRows),
            planRows: (__VLS_ctx.planRows),
            parsedMenuCount: (__VLS_ctx.parsedMenuCount),
            matchedPlanCount: (__VLS_ctx.matchedPlanCount),
            pendingPlanCount: (__VLS_ctx.pendingPlanCount),
            totalCostLabel: (__VLS_ctx.menuTotalCostLabel),
            loading: (__VLS_ctx.menuPlanLoading),
        }, ...__VLS_functionalComponentArgsRest(__VLS_81));
        let __VLS_85;
        const __VLS_86 = ({ submit: {} },
            { onSubmit: (__VLS_ctx.submitMenuPlan) });
        const __VLS_87 = ({ importLines: {} },
            { onImportLines: (__VLS_ctx.appendMenuLines) });
        var __VLS_83;
        var __VLS_84;
    }
}
// @ts-ignore
[activeTab, menuTotalCostLabel, reloadTrend, menuForm, menuForm, menuForm, menuForm, menuLocationCandidates, ingredientRows, planRows, parsedMenuCount, matchedPlanCount, pendingPlanCount, menuPlanLoading, submitMenuPlan, appendMenuLines,];
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
