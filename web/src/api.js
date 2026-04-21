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
export const api = axios.create({
    // Production defaults to the reverse-proxied /api path.
    baseURL: apiBaseUrl,
    timeout: 15000,
});
export const dataSourceState = reactive({
    mode: 'live',
    lastError: '',
});
function isAxiosError(error) {
    return typeof error === 'object' && error !== null && 'isAxiosError' in error;
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
        return '当前请求没有权限，请检查接口认证设置';
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
export async function fetchSourceCoverage() {
    return requestWithState(async () => {
        const { data } = await api.get('/source/coverage');
        return data;
    }, { affectGlobalState: false });
}
export async function fetchCrawlStatus() {
    return requestWithState(async () => {
        const { data } = await api.get('/crawl/status');
        return data;
    }, { affectGlobalState: false });
}
export async function triggerCrawlRun() {
    return requestWithState(async () => {
        const { data } = await api.post('/crawl/run');
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
        const { data } = await api.get('/market/summary', { params });
        return data;
    });
}
export async function fetchProductOptions(params) {
    return requestWithState(async () => {
        const { data } = await api.get('/product/options', { params });
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
export async function fetchSalesDemoContent(scene) {
    return requestWithState(async () => {
        const { data } = await api.get('/sales/demo-content', { params: { scene } });
        return data;
    }, { affectGlobalState: false });
}
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
export async function updateSupplier(supplierId, payload) {
    return requestWithState(async () => {
        const { data } = await api.put(`/suppliers/${supplierId}`, payload);
        return data;
    }, { affectGlobalState: false });
}
export async function fetchSupplierQuotesBySupplier(supplierId, limit = 20) {
    return requestWithState(async () => {
        const { data } = await api.get(`/suppliers/${supplierId}/quotes`, { params: { limit } });
        return data;
    }, { affectGlobalState: false });
}
