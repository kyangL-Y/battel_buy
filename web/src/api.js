import axios from 'axios';
import { reactive } from 'vue';
function normalizeApiBaseUrl(rawValue) {
    const value = (rawValue || '/api').trim();
    if (!value) {
        return '/api';
    }
    return value.endsWith('/') ? value.slice(0, -1) : value;
}
const apiBaseUrl = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
const AUTH_STORAGE_KEY = 'battel.auth.session';
export const api = axios.create({
    // Production defaults to the reverse-proxied /api path.
    baseURL: apiBaseUrl,
    timeout: 30000,
});
const AUTH_REQUEST_TIMEOUT = 60000;
function normalizeSnapshotIdentity(value) {
    return String(value || '').trim().toLowerCase();
}
export function buildSnapshotProductSummary(identityKey, rows) {
    const normalizedIdentityKey = normalizeSnapshotIdentity(identityKey);
    const row = (rows || []).find((item) => normalizeSnapshotIdentity(item?.price_identity_key) === normalizedIdentityKey);
    if (!row) {
        return null;
    }
    return {
        ...row,
        price_identity_key: identityKey,
        product_name: row.product_name,
        average_price: row.average_price,
        lowest_price: row.lowest_price,
        highest_price: row.highest_price,
        site_count: row.site_count || row.market_count || null,
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
    return requestWithState(async () => {
        const { data } = await api.get('/location/options');
        return data;
    });
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
export async function fetchSourceCoverage() {
    return requestWithState(async () => {
        const { data } = await api.get('/source/coverage', { timeout: 45000 });
        return data;
    }, { affectGlobalState: false });
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
    return requestWithState(async () => {
        const { data } = await api.get('/market/summary', { params, timeout: 60000 });
        return data;
    });
}
export async function fetchProductOptions(params) {
    return requestWithState(async () => {
        const { data } = await api.get('/product/options', { params, timeout: 45000 });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchProductSummary(identityKey, params) {
    return requestWithState(async () => {
        const { data } = await api.get(`/product/${encodeURIComponent(identityKey)}/summary`, { params });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchProductTrend(identityKey, params) {
    return requestWithState(async () => {
        const { data } = await api.get(`/product/${encodeURIComponent(identityKey)}/trend`, {
            params,
            timeout: 45000,
        });
        return data;
    }, { affectGlobalState: false });
}
export async function fetchLiancaiCategorySummary() {
    return requestWithState(async () => {
        const { data } = await api.get('/liancai/category-summary');
        return data;
    }, { affectGlobalState: false });
}
export async function fetchLiancaiFacets(params) {
    return requestWithState(async () => {
        const { data } = await api.get('/liancai/facets', { params, timeout: 45000 });
        return data;
    }, { affectGlobalState: false });
}
export async function generateMenuPlan(payload) {
    return requestWithState(async () => {
        const { data } = await api.post('/menu/plan', payload);
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
        const { data } = await api.post('/procurement/recommend', payload, { timeout: 30000 });
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
