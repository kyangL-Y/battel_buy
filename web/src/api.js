import axios from 'axios';
import { reactive } from 'vue';
const MARKET_SNAPSHOT_URL = (import.meta.env.VITE_MARKET_SNAPSHOT_URL || '/data/market-snapshot.json').trim();
const MARKET_SNAPSHOT_MODE = (import.meta.env.VITE_MARKET_SNAPSHOT_MODE || 'auto').trim().toLowerCase();
function normalizeApiBaseUrl(rawValue) {
    const value = (rawValue || '').trim();
    if (!value && import.meta.env.PROD && typeof window !== 'undefined') {
        const { protocol, hostname, port } = window.location;
        if (port && port !== '80' && port !== '443') {
            return `${protocol}//${hostname}/api`;
        }
    }
    const normalizedValue = value || '/api';
    if (!normalizedValue) {
        return '/api';
    }
    return normalizedValue.endsWith('/') ? normalizedValue.slice(0, -1) : normalizedValue;
}
const apiBaseUrl = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
const AUTH_STORAGE_KEY = 'battel.auth.session';
const PRODUCT_TREND_RESPONSE_CACHE_TTL_MS = 15000;
const productTrendRequests = new Map();
const productTrendResponseCache = new Map();
export const api = axios.create({
    // Production defaults to the reverse-proxied /api path.
    baseURL: apiBaseUrl,
    timeout: 30000,
});
const publicApi = axios.create({
    baseURL: apiBaseUrl,
    timeout: 30000,
});
const AUTH_REQUEST_TIMEOUT = 60000;
function normalizeSnapshotIdentity(value) {
    return String(value || '').trim().toLowerCase();
}
let marketSnapshotPromise = null;
function markStaticDataSource() {
    dataSourceState.mode = 'static';
    dataSourceState.lastError = '';
}
async function loadMarketSnapshot() {
    if (!MARKET_SNAPSHOT_URL || MARKET_SNAPSHOT_MODE === 'off') {
        return null;
    }
    if (!marketSnapshotPromise) {
        marketSnapshotPromise = fetch(MARKET_SNAPSHOT_URL, { credentials: 'same-origin' })
            .then(async (response) => {
            if (!response.ok)
                return null;
            return await response.json();
        })
            .catch(() => null);
    }
    return marketSnapshotPromise;
}
function paginateItems(items, limit = 0, offset = 0) {
    const safeOffset = Math.max(0, Number(offset) || 0);
    const safeLimit = Math.max(0, Number(limit) || 0);
    const total = items.length;
    const end = safeLimit === 0 ? total : Math.min(safeOffset + safeLimit, total);
    return {
        items: items.slice(safeOffset, end),
        total,
        limit: safeLimit,
        offset: safeOffset,
        has_more: end < total,
    };
}
function normalizeText(value) {
    return String(value ?? '').trim();
}
const LIANCAI_TOP_ALIASES = {
    干调类: ['干调类', '调味品', '调味料', '调味品酱料类', '干货调料', '干货类', '香辛料'],
    调味品: ['调味品', '干调类', '调味料', '调味品酱料类', '干货调料', '香辛料'],
    米面粮油: ['米面粮油', '粮油米面', '粮油类', '主食类'],
    粮油米面: ['粮油米面', '米面粮油', '粮油类', '主食类'],
    蔬菜类: ['蔬菜类', '蔬菜', '净菜类'],
    肉禽蛋类: ['肉禽蛋类', '鲜猪肉', '鲜禽类', '禽蛋类', '牛羊肉'],
    水产类: ['水产类', '鲜活水产', '水产', '海鲜水产'],
};
function matchesLiancaiTopCategory(actualValue, expectedValue) {
    const actual = normalizeText(actualValue);
    const expected = normalizeText(expectedValue);
    if (!expected)
        return true;
    if (actual === expected)
        return true;
    const aliases = LIANCAI_TOP_ALIASES[expected] || [];
    return aliases.some((alias) => actual === alias || actual.includes(alias) || alias.includes(actual));
}
function matchesSourceText(text, sourceName) {
    if (!sourceName)
        return true;
    return text.includes(sourceName) || (sourceName.includes('莲菜网') && text.includes('莲菜网'));
}
function filterSnapshotSummaryRows(rows, params) {
    const province = normalizeText(params.province);
    const city = normalizeText(params.city);
    const keyword = normalizeText(params.keyword);
    const sourceName = normalizeText(params.source_name);
    const subcategory = normalizeText(params.liancai_subcategory);
    const liancaiKeyword = normalizeText(params.liancai_keyword);
    const brand = normalizeText(params.liancai_brand);
    return rows.filter((row) => {
        if (province && !normalizeText(row.region_label).includes(province))
            return false;
        if (city && !normalizeText(row.region_label).includes(city))
            return false;
        if (keyword && !normalizeText(row.product_name).includes(keyword))
            return false;
        if (sourceName) {
            const sourceText = [
                row.source_names,
                row.source_display_names,
                row.lowest_price_site,
                row.highest_price_site,
            ].map(normalizeText).filter(Boolean).join(' ');
            if (!matchesSourceText(sourceText, sourceName))
                return false;
        }
        if (!matchesLiancaiTopCategory(row.liancai_top_category, params.liancai_top_category))
            return false;
        if (subcategory && normalizeText(row.liancai_subcategory) !== subcategory)
            return false;
        if (liancaiKeyword && normalizeText(row.liancai_keyword) !== liancaiKeyword && !normalizeText(row.product_name).includes(liancaiKeyword))
            return false;
        if (brand && normalizeText(row.liancai_brand_name) !== brand && !normalizeText(row.product_name).includes(brand))
            return false;
        return true;
    });
}
function filterSnapshotProductOptions(options, params) {
    const keyword = normalizeText(params.keyword).toLowerCase();
    const sourceName = normalizeText(params.source_name);
    const subcategory = normalizeText(params.liancai_subcategory);
    const liancaiKeyword = normalizeText(params.liancai_keyword);
    const brand = normalizeText(params.liancai_brand);
    return options.filter((item) => {
        if (keyword) {
            const haystack = [
                item.price_identity_label,
                item.price_identity_key,
                item.source_name,
                item.source_category,
                item.liancai_top_category,
                item.liancai_subcategory,
                item.liancai_keyword,
                item.liancai_brand_name,
            ].map((value) => normalizeText(value).toLowerCase()).join(' ');
            if (!haystack.includes(keyword))
                return false;
        }
        if (sourceName && !matchesSourceText(normalizeText(item.source_name), sourceName))
            return false;
        if (!matchesLiancaiTopCategory(item.liancai_top_category, params.liancai_top_category))
            return false;
        if (subcategory && normalizeText(item.liancai_subcategory) !== subcategory)
            return false;
        if (liancaiKeyword && normalizeText(item.liancai_keyword) !== liancaiKeyword && !normalizeText(item.price_identity_label).includes(liancaiKeyword))
            return false;
        if (brand && normalizeText(item.liancai_brand_name) !== brand && !normalizeText(item.price_identity_label).includes(brand))
            return false;
        return true;
    });
}
function buildSnapshotProductOptions(rows) {
    return rows
        .filter((row) => normalizeText(row.price_identity_key) && normalizeText(row.product_name))
        .map((row) => ({
        price_identity_key: normalizeText(row.price_identity_key),
        price_identity_label: normalizeText(row.product_name),
        site_count: Number(row.site_count || row.market_count || 0),
        price_observation_count: Number(row.price_observation_count || row.market_count || row.site_count || 0),
        latest_captured_at: row.latest_captured_at || null,
        source_name: row.source_names || row.source_display_names || null,
        source_category: row.category || null,
        liancai_top_category: row.liancai_top_category || null,
        liancai_subcategory: row.liancai_subcategory || null,
        liancai_keyword: row.liancai_keyword || null,
        liancai_brand_name: row.liancai_brand_name || null,
        image_url: row.image_url || null,
    }));
}
function findSnapshotProductTrend(trendMap, identityKey) {
    if (!trendMap)
        return null;
    if (trendMap[identityKey]) {
        return trendMap[identityKey];
    }
    const normalizedIdentityKey = normalizeSnapshotIdentity(identityKey);
    const matchedEntry = Object.entries(trendMap).find(([key]) => normalizeSnapshotIdentity(key) === normalizedIdentityKey);
    return (matchedEntry == null ? void 0 : matchedEntry[1]) ?? null;
}
export function buildSnapshotProductSummary(identityKey, rows) {
    const normalizedIdentityKey = normalizeSnapshotIdentity(identityKey);
    const row = (rows || []).find((item) => normalizeSnapshotIdentity(item?.price_identity_key) === normalizedIdentityKey);
    if (!row) {
        return null;
    }
    const normalizedLowestPrice = row.current_lowest_price ?? row.lowest_price ?? null;
    const normalizedHighestPrice = row.current_highest_price ?? row.highest_price ?? null;
    const normalizedLowestSite = row.current_lowest_site ?? row.lowest_price_site ?? row.region_label ?? null;
    const normalizedHighestSite = row.current_highest_site ?? row.highest_price_site ?? row.region_label ?? null;
    return {
        ...row,
        price_identity_key: identityKey,
        product_name: row.product_name,
        average_price: row.average_price,
        lowest_price: row.lowest_price,
        highest_price: row.highest_price,
        current_lowest_price: normalizedLowestPrice,
        current_highest_price: normalizedHighestPrice,
        current_lowest_site: normalizedLowestSite,
        current_highest_site: normalizedHighestSite,
        site_count: row.site_count || row.market_count || null,
        price_span: normalizedLowestPrice != null && normalizedHighestPrice != null
            ? Number(normalizedHighestPrice) - Number(normalizedLowestPrice)
            : row.price_span ?? null,
        latest_captured_at: row.latest_captured_at || null,
    };
}
function canUseStorage() {
    return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}
export function readAuthSession() {
    if (!canUseStorage()) {
        return null;
    }
    try {
        const rawValue = window.localStorage.getItem(AUTH_STORAGE_KEY);
        if (!rawValue) {
            return null;
        }
        return JSON.parse(rawValue);
    }
    catch {
        return null;
    }
}
export function writeAuthSession(session) {
    if (!canUseStorage()) {
        return;
    }
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
}
export function clearAuthSession() {
    if (!canUseStorage()) {
        return;
    }
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
}
export function getAccessToken() {
    return readAuthSession()?.access_token || '';
}
api.interceptors.request.use((config) => {
    const token = getAccessToken();
    if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});
export const dataSourceState = reactive({
    mode: 'live',
    lastError: '',
});
function isAxiosError(error) {
    return typeof error === 'object' && error !== null && 'isAxiosError' in error;
}
export function extractApiErrorDetail(error) {
    if (!isAxiosError(error)) {
        return '';
    }
    const axiosError = error;
    const detail = axiosError.response?.data?.detail;
    if (typeof detail === 'string') {
        return detail.trim();
    }
    return '';
}
export function getApiErrorStatus(error) {
    if (!isAxiosError(error)) {
        return 0;
    }
    const axiosError = error;
    if (!axiosError.response) {
        return 0;
    }
    return Number(axiosError.response.status || 0);
}
function formatApiErrorMessage(error) {
    if (!isAxiosError(error)) {
        return '接口请求失败，请稍后重试';
    }
    const axiosError = error;
    const status = Number(axiosError.response?.status || 0);
    if (status >= 500) {
        return '服务暂时不可用，请稍后刷新或检查后端服务';
    }
    if (status === 404) {
        return '接口地址不可用，请检查服务配置';
    }
    if (status === 401 || status === 403) {
        return status === 401 ? '登录状态已失效，请重新登录' : '当前账号没有权限执行这个操作';
    }
    if (axiosError.code === 'ECONNABORTED') {
        return '接口响应超时，请稍后重试';
    }
    if (axiosError.code === 'ERR_NETWORK' || /ECONNREFUSED|Network Error/i.test(String(axiosError.message || ''))) {
        return '无法连接后端服务，请先启动 API 再刷新页面';
    }
    return '接口请求失败，请稍后重试';
}
async function requestWithState(request, options = {}) {
    const { affectGlobalState = true } = options;
    try {
        const result = await request();
        if (affectGlobalState) {
            dataSourceState.mode = 'live';
            dataSourceState.lastError = '';
        }
        return result;
    }
    catch (error) {
        if (affectGlobalState && isAxiosError(error)) {
            dataSourceState.mode = 'error';
            dataSourceState.lastError = formatApiErrorMessage(error);
        }
        throw error;
    }
}
export async function fetchLocationOptions() {
    try {
        return await requestWithState(async () => {
            const { data } = await api.get('/location/options');
            return data;
        });
    }
    catch (error) {
        const snapshot = await loadMarketSnapshot();
        if (snapshot?.location_options) {
            markStaticDataSource();
            return snapshot.location_options;
        }
        throw error;
    }
}
export async function login(payload) {
    return requestWithState(async () => {
        const { data } = await api.post('/auth/login', payload, { timeout: AUTH_REQUEST_TIMEOUT });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchCurrentUser() {
    return requestWithState(async () => {
        const { data } = await api.get('/auth/me', { timeout: AUTH_REQUEST_TIMEOUT });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchAuthUsers(params = {}) {
    return requestWithState(async () => {
        const { data } = await api.get('/auth/users', { params, timeout: AUTH_REQUEST_TIMEOUT });
        return data;
    }, { affectGlobalState: false });
}
export async function createAuthUser(payload) {
    return requestWithState(async () => {
        const { data } = await api.post('/auth/users', payload, { timeout: AUTH_REQUEST_TIMEOUT });
        return data;
    }, { affectGlobalState: false });
}
export async function updateAuthUser(userId, payload) {
    return requestWithState(async () => {
        const { data } = await api.put(`/auth/users/${userId}`, payload, { timeout: AUTH_REQUEST_TIMEOUT });
        return data;
    }, { affectGlobalState: false });
}
export async function deleteAuthUser(userId) {
    return requestWithState(async () => {
        const { data } = await api.delete(`/auth/users/${userId}`, { timeout: AUTH_REQUEST_TIMEOUT });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSourceCoverage() {
    try {
        return await requestWithState(async () => {
            const { data } = await api.get('/source/coverage', { timeout: 45000 });
            return data;
        }, { affectGlobalState: false });
    }
    catch (error) {
        const snapshot = await loadMarketSnapshot();
        if (snapshot?.source_coverage) {
            markStaticDataSource();
            return { items: snapshot.source_coverage.items ?? [] };
        }
        throw error;
    }
}
export async function updateSourceCoverage(payload) {
    return requestWithState(async () => {
        const { data } = await api.put('/source/coverage', payload);
        return data;
    }, { affectGlobalState: false });
}
export async function updateSourceStrategy(payload) {
    return requestWithState(async () => {
        const { data } = await api.put('/source/strategy', payload);
        return data;
    }, { affectGlobalState: false });
}
export async function fetchGlobalAlertRules() {
    return requestWithState(async () => {
        const { data } = await api.get('/settings/alerts');
        return data;
    }, { affectGlobalState: false });
}
export async function updateGlobalAlertRules(items) {
    return requestWithState(async () => {
        const { data } = await api.put('/settings/alerts', { items });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchCrawlStatus() {
    return requestWithState(async () => {
        const { data } = await api.get('/crawl/status');
        return data;
    }, { affectGlobalState: false });
}
export async function triggerCrawlRun(payload = {}) {
    return requestWithState(async () => {
        const { data } = await api.post('/crawl/run', payload);
        return data;
    }, { affectGlobalState: false });
}
export async function updateCrawlSchedule(payload) {
    return requestWithState(async () => {
        const { data } = await api.post('/crawl/schedule', payload);
        return data;
    }, { affectGlobalState: false });
}
export async function fetchMarketSummary(params) {
    try {
        return await requestWithState(async () => {
            const { data } = await api.get('/market/summary', { params, timeout: 60000 });
            return data;
        });
    }
    catch (error) {
        const snapshot = await loadMarketSnapshot();
        const snapshotRows = snapshot?.market_summary?.items;
        const snapshotHasAnyImage = Array.isArray(snapshotRows)
            && snapshotRows.some((row) => String((row == null ? void 0 : row.image_url) || '').trim());
        if (snapshotRows && snapshotHasAnyImage) {
            markStaticDataSource();
            return paginateItems(filterSnapshotSummaryRows(snapshotRows, params), params.limit, params.offset);
        }
        throw error;
    }
}
export async function fetchProductOptions(params) {
    try {
        return await requestWithState(async () => {
            const { data } = await api.get('/product/options', { params, timeout: 45000 });
            return data;
        }, { affectGlobalState: false });
    }
    catch (error) {
        const snapshot = await loadMarketSnapshot();
        if (snapshot?.product_options?.items || snapshot?.market_summary?.items) {
            markStaticDataSource();
            const sourceOptions = snapshot.product_options?.items?.length
                ? snapshot.product_options.items
                : buildSnapshotProductOptions(filterSnapshotSummaryRows(snapshot.market_summary?.items ?? [], params));
            return paginateItems(filterSnapshotProductOptions(sourceOptions, params), params.limit, params.offset);
        }
        throw error;
    }
}
export async function fetchProductSummary(identityKey, params) {
    return requestWithState(async () => {
        const { data } = await api.get(`/product/${encodeURIComponent(identityKey)}/summary`, { params });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchProductTrend(identityKey, params) {
    const requestKey = JSON.stringify({
        identityKey,
        mode: params.mode || '',
        site_name: params.site_name || '',
        series_key: params.series_key || '',
        province: params.province || '',
        city: params.city || '',
        source_name: params.source_name || '',
        liancai_top_category: params.liancai_top_category || '',
        liancai_subcategory: params.liancai_subcategory || '',
        liancai_keyword: params.liancai_keyword || '',
        liancai_brand: params.liancai_brand || '',
    });
    const cachedResponse = productTrendResponseCache.get(requestKey);
    if (cachedResponse && cachedResponse.expiresAt > Date.now()) {
        return cachedResponse.data;
    }
    const existingRequest = productTrendRequests.get(requestKey);
    if (existingRequest) {
        return existingRequest;
    }
    const requestPromise = requestWithState(async () => {
        const { data } = await api.get(`/product/${encodeURIComponent(identityKey)}/trend`, {
            params,
            timeout: 45000,
        });
        productTrendResponseCache.set(requestKey, {
            expiresAt: Date.now() + PRODUCT_TREND_RESPONSE_CACHE_TTL_MS,
            data,
        });
        return data;
    }, { affectGlobalState: false }).catch(async (error) => {
        const snapshot = await loadMarketSnapshot();
        const snapshotTrendEntry = findSnapshotProductTrend(snapshot?.product_trends, decodeURIComponent(identityKey));
        if (!snapshotTrendEntry)
            throw error;
        const requestedMode = params.mode === 'single_market' ? 'single_market' : 'cross_market';
        let snapshotItems = [];
        if (requestedMode === 'single_market') {
            const siteKey = normalizeText(params.series_key || params.site_name);
            const singleMarketMap = snapshotTrendEntry.single_market || {};
            if (siteKey && singleMarketMap[siteKey]?.items?.length) {
                snapshotItems = singleMarketMap[siteKey]?.items ?? [];
            }
            else if (siteKey) {
                const matchedEntry = Object.entries(singleMarketMap).find(([key]) => normalizeText(key) === siteKey);
                snapshotItems = matchedEntry?.[1]?.items ?? [];
            }
            else {
                snapshotItems = Object.values(singleMarketMap)[0]?.items ?? [];
            }
        }
        else {
            snapshotItems = snapshotTrendEntry.cross_market?.items ?? [];
        }
        markStaticDataSource();
        const data = {
            mode: requestedMode,
            items: snapshotItems,
        };
        productTrendResponseCache.set(requestKey, {
            expiresAt: Date.now() + PRODUCT_TREND_RESPONSE_CACHE_TTL_MS,
            data,
        });
        return data;
    });
    productTrendRequests.set(requestKey, requestPromise);
    requestPromise.finally(() => {
        productTrendRequests.delete(requestKey);
    });
    return requestPromise;
}
export async function fetchLiancaiCategorySummary(params) {
    try {
        return await requestWithState(async () => {
            const { data } = await api.get('/liancai/category-summary', { params });
            return data;
        }, { affectGlobalState: false });
    }
    catch (error) {
        const snapshot = await loadMarketSnapshot();
        if (snapshot?.liancai_category_summary) {
            markStaticDataSource();
            return { items: snapshot.liancai_category_summary.items ?? [] };
        }
        throw error;
    }
}
export async function fetchLiancaiFacets(params) {
    const facetKey = `${normalizeText(params.liancai_top_category)}\u0001${normalizeText(params.liancai_subcategory)}`;
    try {
        return await requestWithState(async () => {
            const { data } = await api.get('/liancai/facets', { params, timeout: 45000 });
            return data;
        }, { affectGlobalState: false });
    }
    catch (error) {
        const snapshot = await loadMarketSnapshot();
        if (snapshot?.liancai_facets) {
            markStaticDataSource();
            return snapshot.liancai_facets[facetKey] ?? { keywords: [], brands: [] };
        }
        throw error;
    }
}
export async function generateMenuPlan(payload) {
    return requestWithState(async () => {
        const { data } = await publicApi.post('/menu/plan', payload);
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSignalsOverview(params) {
    return requestWithState(async () => {
        const { data } = await api.get('/signals/overview', { params, timeout: 30000 });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSignalDetail(identityKey, params) {
    return requestWithState(async () => {
        const { data } = await api.get(`/signals/${encodeURIComponent(identityKey)}`, { params, timeout: 30000 });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchProcurementRecommendation(payload) {
    return requestWithState(async () => {
        const { data } = await publicApi.post('/procurement/recommend', payload, { timeout: 30000 });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSalesDecisionContent(scene) {
    return requestWithState(async () => {
        const { data } = await api.get('/sales/decision-content', { params: { scene } });
        return data;
    }, { affectGlobalState: false });
}
export const fetchSalesDemoContent = fetchSalesDecisionContent;
export async function fetchPricingPackages() {
    return requestWithState(async () => {
        const { data } = await api.get('/pricing/packages');
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSuppliers(activeOnly = true) {
    return requestWithState(async () => {
        const { data } = await api.get('/suppliers', { params: { active_only: activeOnly } });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSupplierOverview(limit = 12) {
    return requestWithState(async () => {
        const { data } = await api.get('/suppliers/overview', { params: { limit } });
        return data;
    }, { affectGlobalState: false });
}
export async function createSupplier(payload) {
    return requestWithState(async () => {
        const { data } = await api.post('/suppliers', payload);
        return data;
    }, { affectGlobalState: false });
}
export async function createSupplierRegistrationRequest(payload) {
    return requestWithState(async () => {
        const { data } = await api.post('/supplier-registration-requests', payload);
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSupplierRegistrationRequests(params = {}) {
    return requestWithState(async () => {
        const { data } = await api.get('/supplier-registration-requests', { params });
        return data;
    }, { affectGlobalState: false });
}
export async function approveSupplierRegistrationRequest(requestId, payload) {
    return requestWithState(async () => {
        const { data } = await api.post(`/supplier-registration-requests/${requestId}/approve`, payload);
        return data;
    }, { affectGlobalState: false });
}
export async function rejectSupplierRegistrationRequest(requestId, payload) {
    return requestWithState(async () => {
        const { data } = await api.post(`/supplier-registration-requests/${requestId}/reject`, payload);
        return data;
    }, { affectGlobalState: false });
}
export async function fetchProductSupplierQuotes(identityKey) {
    return requestWithState(async () => {
        const { data } = await api.get(`/product/${encodeURIComponent(identityKey)}/supplier-quotes`);
        return data;
    }, { affectGlobalState: false });
}
export async function submitSupplierQuote(payload) {
    return requestWithState(async () => {
        const { data } = await api.post('/supplier-prices', payload);
        return data;
    }, { affectGlobalState: false });
}
export async function importSupplierQuotes(payload) {
    return requestWithState(async () => {
        const { data } = await api.post('/supplier-prices/import', payload);
        return data;
    }, { affectGlobalState: false });
}
export async function previewImportSupplierQuotes(payload) {
    return requestWithState(async () => {
        const { data } = await api.post('/supplier-prices/import-preview', payload);
        return data;
    }, { affectGlobalState: false });
}
export async function invalidateSupplierQuote(recordId, payload = {}) {
    return requestWithState(async () => {
        const { data } = await api.post(`/supplier-prices/${recordId}/invalidate`, payload);
        return data;
    }, { affectGlobalState: false });
}
export async function updateSupplier(supplierId, payload) {
    return requestWithState(async () => {
        const { data } = await api.put(`/suppliers/${supplierId}`, payload);
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSupplierQuotesBySupplier(supplierId, options = {}) {
    return requestWithState(async () => {
        const { data } = await api.get(`/suppliers/${supplierId}/quotes`, { params: options });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSupplierQuoteActions(supplierId, options = {}) {
    return requestWithState(async () => {
        const { data } = await api.get(`/suppliers/${supplierId}/quote-actions`, { params: options });
        return data;
    }, { affectGlobalState: false });
}
export async function createSupplierQuoteAction(supplierId, payload) {
    return requestWithState(async () => {
        const { data } = await api.post(`/suppliers/${supplierId}/quote-actions`, payload);
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSupplierSettlementsBySupplier(supplierId, options = {}) {
    return requestWithState(async () => {
        const { data } = await api.get(`/suppliers/${supplierId}/settlements`, { params: options });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSupplierSettlementDetail(recordId) {
    return requestWithState(async () => {
        const { data } = await api.get(`/supplier-settlements/${recordId}`);
        return data;
    }, { affectGlobalState: false });
}
export async function createSupplierSettlement(supplierId, payload) {
    return requestWithState(async () => {
        const { data } = await api.post(`/suppliers/${supplierId}/settlements`, payload);
        return data;
    }, { affectGlobalState: false });
}
export async function updateSupplierSettlement(recordId, payload) {
    return requestWithState(async () => {
        const { data } = await api.put(`/supplier-settlements/${recordId}`, payload);
        return data;
    }, { affectGlobalState: false });
}
export async function cancelSupplierSettlement(recordId, payload = {}) {
    return requestWithState(async () => {
        const { data } = await api.post(`/supplier-settlements/${recordId}/cancel`, payload);
        return data;
    }, { affectGlobalState: false });
}
export async function buildSupplierSettlementsFromQuotes(supplierId, payload) {
    return requestWithState(async () => {
        const { data } = await api.post(`/suppliers/${supplierId}/settlements/build-from-quotes`, payload);
        return data;
    }, { affectGlobalState: false });
}
