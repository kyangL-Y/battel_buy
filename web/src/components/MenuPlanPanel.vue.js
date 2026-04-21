import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus/es/components/message/index.mjs';
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { useViewport } from '../composables/useViewport';
const props = defineProps();
const emit = defineEmits();
const fileInputRef = ref(null);
const { isMobileViewport } = useViewport();
const MENU_NAME_HEADER_PATTERNS = [/菜名/i, /菜单/i, /菜品/i, /品名/i, /^名称$/i];
const TEXT_ENCODINGS = ['utf-8', 'gb18030'];
function openFileDialog() {
    fileInputRef.value?.click();
}
function formatPrice(value) {
    if (value == null || Number.isNaN(Number(value))) {
        return '-';
    }
    return Number(value).toFixed(2);
}
function formatQuantity(value, unit) {
    if (value == null || Number.isNaN(Number(value))) {
        return unit ? `- ${unit}` : '-';
    }
    return `${Number(value).toFixed(2)} ${unit || ''}`.trim();
}
function getFileExtension(filename) {
    const parts = filename.toLowerCase().split('.');
    return parts.length > 1 ? parts.pop() || '' : '';
}
function normalizeImportedLines(lines) {
    return Array.from(new Set(lines
        .map((item) => item.replace(/\u0000/g, '').trim())
        .filter(Boolean)));
}
function decodeTextBuffer(buffer) {
    for (const encoding of TEXT_ENCODINGS) {
        try {
            return new TextDecoder(encoding).decode(buffer);
        }
        catch {
            // Try next encoding.
        }
    }
    return new TextDecoder().decode(buffer);
}
function parseImportedText(content, filename) {
    const lowerName = filename.toLowerCase();
    if (lowerName.endsWith('.csv')) {
        return normalizeImportedLines(content
            .split(/\r?\n/)
            .map((line) => line.split(',')[0]?.replace(/^"|"$/g, '').trim())
            .filter(Boolean));
    }
    return normalizeImportedLines(content.split(/\r?\n/).map((item) => item.trim()).filter(Boolean));
}
function findMenuColumnIndex(rows) {
    const headerRows = rows.slice(0, 3);
    for (const row of headerRows) {
        for (const [index, cell] of row.entries()) {
            if (MENU_NAME_HEADER_PATTERNS.some((pattern) => pattern.test(cell))) {
                return index;
            }
        }
    }
    return -1;
}
function parseTabularRows(rows) {
    const normalizedRows = rows
        .filter((row) => Array.isArray(row))
        .map((row) => row.map((cell) => String(cell ?? '').trim()))
        .filter((row) => row.some(Boolean));
    if (!normalizedRows.length) {
        return [];
    }
    const menuColumnIndex = findMenuColumnIndex(normalizedRows);
    if (menuColumnIndex >= 0) {
        return normalizeImportedLines(normalizedRows
            .slice(1)
            .map((row) => row[menuColumnIndex] || '')
            .filter(Boolean));
    }
    return normalizeImportedLines(normalizedRows
        .map((row) => row.find(Boolean) || '')
        .filter(Boolean));
}
async function parseSpreadsheetFile(file) {
    const xlsx = await import('xlsx');
    const buffer = await file.arrayBuffer();
    const workbook = xlsx.read(buffer, { type: 'array' });
    const firstSheetName = workbook.SheetNames[0];
    if (!firstSheetName) {
        return [];
    }
    const firstSheet = workbook.Sheets[firstSheetName];
    const rows = xlsx.utils.sheet_to_json(firstSheet, {
        header: 1,
        raw: false,
        defval: '',
    });
    return parseTabularRows(rows);
}
async function parseDocxFile(file) {
    const mammoth = await import('mammoth');
    const buffer = await file.arrayBuffer();
    const result = await mammoth.extractRawText({ arrayBuffer: buffer });
    return normalizeImportedLines(result.value
        .split(/\r?\n/)
        .flatMap((line) => line.split(/\t+/))
        .map((item) => item.trim())
        .filter(Boolean));
}
async function parsePdfFile(file) {
    const pdfjs = await import('pdfjs-dist/build/pdf.min.mjs');
    pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;
    const buffer = await file.arrayBuffer();
    const document = await pdfjs.getDocument({ data: new Uint8Array(buffer) }).promise;
    const lines = [];
    for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
        const page = await document.getPage(pageNumber);
        const textContent = await page.getTextContent();
        let currentLine = '';
        for (const item of textContent.items) {
            const text = String(item.str || '').trim();
            if (text) {
                currentLine = currentLine ? `${currentLine} ${text}` : text;
            }
            if (item.hasEOL && currentLine) {
                lines.push(currentLine);
                currentLine = '';
            }
        }
        if (currentLine) {
            lines.push(currentLine);
        }
    }
    return normalizeImportedLines(lines);
}
async function parseImportedFile(file) {
    const extension = getFileExtension(file.name);
    if (extension === 'txt' || extension === 'csv') {
        const buffer = await file.arrayBuffer();
        return parseImportedText(decodeTextBuffer(buffer), file.name);
    }
    if (extension === 'xlsx' || extension === 'xls') {
        return parseSpreadsheetFile(file);
    }
    if (extension === 'docx') {
        return parseDocxFile(file);
    }
    if (extension === 'pdf') {
        return parsePdfFile(file);
    }
    throw new Error('暂不支持该文件格式');
}
async function handleFileChange(event) {
    const input = event.target;
    const file = input.files?.[0];
    if (!file)
        return;
    try {
        const lines = await parseImportedFile(file);
        if (!lines.length) {
            ElMessage.warning('文件里没有识别到菜单项，PDF 需为可复制文本内容');
            return;
        }
        emit('import-lines', lines);
    }
    catch (error) {
        ElMessage.error(error instanceof Error ? error.message : '菜单文件读取失败');
    }
    finally {
        input.value = '';
    }
}
const pendingRows = computed(() => props.planRows.filter((item) => item.price_status !== '已匹配报价'));
const pendingPreviewRows = computed(() => pendingRows.value.slice(0, 4));
const pendingOverflowCount = computed(() => Math.max(0, pendingRows.value.length - pendingPreviewRows.value.length));
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
    ...{ class: "menu-workspace" },
});
/** @type {__VLS_StyleScopedClasses['menu-workspace']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "panel menu-command-panel" },
});
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['menu-command-panel']} */ ;
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
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "panel-hint" },
});
/** @type {__VLS_StyleScopedClasses['panel-hint']} */ ;
(__VLS_ctx.isMobileViewport ? '先录菜单，再生成采购建议。' : '录菜单、补食材、直接出采购建议。导入说明保留一行，首屏尽量只看关键字段。');
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "menu-grid" },
});
/** @type {__VLS_StyleScopedClasses['menu-grid']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "menu-form" },
});
/** @type {__VLS_StyleScopedClasses['menu-form']} */ ;
let __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.elInput | typeof __VLS_components.ElInput} */
elInput;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
    ...{ 'onUpdate:modelValue': {} },
    modelValue: (__VLS_ctx.menuText),
    type: "textarea",
    'aria-label': "菜单文本输入",
    rows: (__VLS_ctx.isMobileViewport ? 4 : 6),
    autosize: (__VLS_ctx.isMobileViewport ? { minRows: 4, maxRows: 8 } : false),
    placeholder: "每行一个菜名，例如：&#10;蒜蓉西兰花&#10;清蒸鲈鱼&#10;红烧排骨",
}));
const __VLS_2 = __VLS_1({
    ...{ 'onUpdate:modelValue': {} },
    modelValue: (__VLS_ctx.menuText),
    type: "textarea",
    'aria-label': "菜单文本输入",
    rows: (__VLS_ctx.isMobileViewport ? 4 : 6),
    autosize: (__VLS_ctx.isMobileViewport ? { minRows: 4, maxRows: 8 } : false),
    placeholder: "每行一个菜名，例如：&#10;蒜蓉西兰花&#10;清蒸鲈鱼&#10;红烧排骨",
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
let __VLS_5;
const __VLS_6 = ({ 'update:modelValue': {} },
    { 'onUpdate:modelValue': (...[$event]) => {
            __VLS_ctx.emit('update:menu-text', $event);
            // @ts-ignore
            [isMobileViewport, isMobileViewport, isMobileViewport, menuText, emit,];
        } });
var __VLS_3;
var __VLS_4;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "menu-import-row" },
});
/** @type {__VLS_StyleScopedClasses['menu-import-row']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.input)({
    ...{ onChange: (__VLS_ctx.handleFileChange) },
    ref: "fileInputRef",
    ...{ class: "hidden-file-input" },
    type: "file",
    accept: ".txt,.csv,.xlsx,.xls,.docx,.pdf",
});
/** @type {__VLS_StyleScopedClasses['hidden-file-input']} */ ;
let __VLS_7;
/** @ts-ignore @type {typeof __VLS_components.elButton | typeof __VLS_components.ElButton | typeof __VLS_components.elButton | typeof __VLS_components.ElButton} */
elButton;
// @ts-ignore
const __VLS_8 = __VLS_asFunctionalComponent1(__VLS_7, new __VLS_7({
    ...{ 'onClick': {} },
    'aria-label': "导入菜单文件",
}));
const __VLS_9 = __VLS_8({
    ...{ 'onClick': {} },
    'aria-label': "导入菜单文件",
}, ...__VLS_functionalComponentArgsRest(__VLS_8));
let __VLS_12;
const __VLS_13 = ({ click: {} },
    { onClick: (__VLS_ctx.openFileDialog) });
const { default: __VLS_14 } = __VLS_10.slots;
// @ts-ignore
[handleFileChange, openFileDialog,];
var __VLS_10;
var __VLS_11;
if (!__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
        ...{ class: "panel-hint menu-import-hint" },
    });
    /** @type {__VLS_StyleScopedClasses['panel-hint']} */ ;
    /** @type {__VLS_StyleScopedClasses['menu-import-hint']} */ ;
}
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "menu-actions" },
});
/** @type {__VLS_StyleScopedClasses['menu-actions']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "menu-action-field" },
});
/** @type {__VLS_StyleScopedClasses['menu-action-field']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "menu-action-label" },
});
/** @type {__VLS_StyleScopedClasses['menu-action-label']} */ ;
let __VLS_15;
/** @ts-ignore @type {typeof __VLS_components.elInputNumber | typeof __VLS_components.ElInputNumber} */
elInputNumber;
// @ts-ignore
const __VLS_16 = __VLS_asFunctionalComponent1(__VLS_15, new __VLS_15({
    ...{ 'onUpdate:modelValue': {} },
    'aria-label': "桌数",
    modelValue: (__VLS_ctx.tables),
    min: (1),
}));
const __VLS_17 = __VLS_16({
    ...{ 'onUpdate:modelValue': {} },
    'aria-label': "桌数",
    modelValue: (__VLS_ctx.tables),
    min: (1),
}, ...__VLS_functionalComponentArgsRest(__VLS_16));
let __VLS_20;
const __VLS_21 = ({ 'update:modelValue': {} },
    { 'onUpdate:modelValue': (...[$event]) => {
            __VLS_ctx.emit('update:tables', Number($event) || 1);
            // @ts-ignore
            [isMobileViewport, emit, tables,];
        } });
var __VLS_18;
var __VLS_19;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "menu-action-field" },
});
/** @type {__VLS_StyleScopedClasses['menu-action-field']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "menu-action-label" },
});
/** @type {__VLS_StyleScopedClasses['menu-action-label']} */ ;
let __VLS_22;
/** @ts-ignore @type {typeof __VLS_components.elInputNumber | typeof __VLS_components.ElInputNumber} */
elInputNumber;
// @ts-ignore
const __VLS_23 = __VLS_asFunctionalComponent1(__VLS_22, new __VLS_22({
    ...{ 'onUpdate:modelValue': {} },
    'aria-label': "人数",
    modelValue: (__VLS_ctx.diners),
    min: (1),
}));
const __VLS_24 = __VLS_23({
    ...{ 'onUpdate:modelValue': {} },
    'aria-label': "人数",
    modelValue: (__VLS_ctx.diners),
    min: (1),
}, ...__VLS_functionalComponentArgsRest(__VLS_23));
let __VLS_27;
const __VLS_28 = ({ 'update:modelValue': {} },
    { 'onUpdate:modelValue': (...[$event]) => {
            __VLS_ctx.emit('update:diners', Number($event) || 1);
            // @ts-ignore
            [emit, diners,];
        } });
var __VLS_25;
var __VLS_26;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "menu-action-field menu-location-field" },
});
/** @type {__VLS_StyleScopedClasses['menu-action-field']} */ ;
/** @type {__VLS_StyleScopedClasses['menu-location-field']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "menu-action-label" },
});
/** @type {__VLS_StyleScopedClasses['menu-action-label']} */ ;
let __VLS_29;
/** @ts-ignore @type {typeof __VLS_components.elSelect | typeof __VLS_components.ElSelect | typeof __VLS_components.elSelect | typeof __VLS_components.ElSelect} */
elSelect;
// @ts-ignore
const __VLS_30 = __VLS_asFunctionalComponent1(__VLS_29, new __VLS_29({
    ...{ 'onUpdate:modelValue': {} },
    modelValue: (__VLS_ctx.preferredLocation),
    'aria-label': "优先地区",
    clearable: true,
    filterable: true,
    placeholder: "当前位置 / 城市 / 省份",
}));
const __VLS_31 = __VLS_30({
    ...{ 'onUpdate:modelValue': {} },
    modelValue: (__VLS_ctx.preferredLocation),
    'aria-label': "优先地区",
    clearable: true,
    filterable: true,
    placeholder: "当前位置 / 城市 / 省份",
}, ...__VLS_functionalComponentArgsRest(__VLS_30));
let __VLS_34;
const __VLS_35 = ({ 'update:modelValue': {} },
    { 'onUpdate:modelValue': (...[$event]) => {
            __VLS_ctx.emit('update:preferred-location', String($event || ''));
            // @ts-ignore
            [emit, preferredLocation,];
        } });
const { default: __VLS_36 } = __VLS_32.slots;
for (const [item] of __VLS_vFor((__VLS_ctx.locationCandidates))) {
    let __VLS_37;
    /** @ts-ignore @type {typeof __VLS_components.elOption | typeof __VLS_components.ElOption} */
    elOption;
    // @ts-ignore
    const __VLS_38 = __VLS_asFunctionalComponent1(__VLS_37, new __VLS_37({
        key: (item),
        label: (item),
        value: (item),
    }));
    const __VLS_39 = __VLS_38({
        key: (item),
        label: (item),
        value: (item),
    }, ...__VLS_functionalComponentArgsRest(__VLS_38));
    // @ts-ignore
    [locationCandidates,];
}
// @ts-ignore
[];
var __VLS_32;
var __VLS_33;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "menu-submit-bar" },
});
/** @type {__VLS_StyleScopedClasses['menu-submit-bar']} */ ;
let __VLS_42;
/** @ts-ignore @type {typeof __VLS_components.elButton | typeof __VLS_components.ElButton | typeof __VLS_components.elButton | typeof __VLS_components.ElButton} */
elButton;
// @ts-ignore
const __VLS_43 = __VLS_asFunctionalComponent1(__VLS_42, new __VLS_42({
    ...{ 'onClick': {} },
    'aria-label': "生成采购方案",
    type: "primary",
    loading: (__VLS_ctx.loading),
}));
const __VLS_44 = __VLS_43({
    ...{ 'onClick': {} },
    'aria-label': "生成采购方案",
    type: "primary",
    loading: (__VLS_ctx.loading),
}, ...__VLS_functionalComponentArgsRest(__VLS_43));
let __VLS_47;
const __VLS_48 = ({ click: {} },
    { onClick: (...[$event]) => {
            __VLS_ctx.emit('submit');
            // @ts-ignore
            [emit, loading,];
        } });
const { default: __VLS_49 } = __VLS_45.slots;
// @ts-ignore
[];
var __VLS_45;
var __VLS_46;
if (!__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.aside, __VLS_intrinsics.aside)({
        ...{ class: "menu-guidance-card compact-guidance-card" },
    });
    /** @type {__VLS_StyleScopedClasses['menu-guidance-card']} */ ;
    /** @type {__VLS_StyleScopedClasses['compact-guidance-card']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "guidance-head" },
    });
    /** @type {__VLS_StyleScopedClasses['guidance-head']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
        ...{ class: "guidance-tag" },
    });
    /** @type {__VLS_StyleScopedClasses['guidance-tag']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.ul, __VLS_intrinsics.ul)({
        ...{ class: "menu-guidance-list" },
    });
    /** @type {__VLS_StyleScopedClasses['menu-guidance-list']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.li, __VLS_intrinsics.li)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.li, __VLS_intrinsics.li)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.li, __VLS_intrinsics.li)({});
}
if (!__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "menu-summary-strip" },
    });
    /** @type {__VLS_StyleScopedClasses['menu-summary-strip']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "summary-card menu-kpi" },
    });
    /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
    /** @type {__VLS_StyleScopedClasses['menu-kpi']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.parsedMenuCount);
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "summary-card menu-kpi" },
    });
    /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
    /** @type {__VLS_StyleScopedClasses['menu-kpi']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.matchedPlanCount);
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "summary-card menu-kpi" },
        ...{ class: ({ 'menu-kpi-pending': __VLS_ctx.pendingPlanCount > 0 }) },
    });
    /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
    /** @type {__VLS_StyleScopedClasses['menu-kpi']} */ ;
    /** @type {__VLS_StyleScopedClasses['menu-kpi-pending']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.pendingPlanCount);
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "summary-card menu-kpi menu-kpi-emphasis" },
    });
    /** @type {__VLS_StyleScopedClasses['summary-card']} */ ;
    /** @type {__VLS_StyleScopedClasses['menu-kpi']} */ ;
    /** @type {__VLS_StyleScopedClasses['menu-kpi-emphasis']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.totalCostLabel);
    __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
    if (__VLS_ctx.pendingPreviewRows.length) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "menu-pending-brief" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-pending-brief']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "menu-pending-head" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-pending-head']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.pendingPlanCount);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "menu-alert-tags compact-alert-tags" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-alert-tags']} */ ;
        /** @type {__VLS_StyleScopedClasses['compact-alert-tags']} */ ;
        for (const [row] of __VLS_vFor((__VLS_ctx.pendingPreviewRows))) {
            __VLS_asFunctionalElement1(__VLS_intrinsics.em, __VLS_intrinsics.em)({
                key: (`${row.ingredient_name}-${row.menu_name}`),
            });
            (row.ingredient_name || row.menu_name);
            // @ts-ignore
            [isMobileViewport, isMobileViewport, parsedMenuCount, matchedPlanCount, pendingPlanCount, pendingPlanCount, pendingPlanCount, totalCostLabel, pendingPreviewRows, pendingPreviewRows,];
        }
        if (__VLS_ctx.pendingOverflowCount > 0) {
            __VLS_asFunctionalElement1(__VLS_intrinsics.em, __VLS_intrinsics.em)({
                ...{ class: "overflow-tag" },
            });
            /** @type {__VLS_StyleScopedClasses['overflow-tag']} */ ;
            (__VLS_ctx.pendingOverflowCount);
        }
    }
}
else {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "menu-mobile-overview" },
    });
    /** @type {__VLS_StyleScopedClasses['menu-mobile-overview']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "menu-mobile-overview-pill" },
    });
    /** @type {__VLS_StyleScopedClasses['menu-mobile-overview-pill']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.parsedMenuCount);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "menu-mobile-overview-pill" },
    });
    /** @type {__VLS_StyleScopedClasses['menu-mobile-overview-pill']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.matchedPlanCount);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "menu-mobile-overview-pill" },
        ...{ class: ({ warning: __VLS_ctx.pendingPlanCount > 0 }) },
    });
    /** @type {__VLS_StyleScopedClasses['menu-mobile-overview-pill']} */ ;
    /** @type {__VLS_StyleScopedClasses['warning']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.pendingPlanCount);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "menu-mobile-overview-pill emphasis" },
    });
    /** @type {__VLS_StyleScopedClasses['menu-mobile-overview-pill']} */ ;
    /** @type {__VLS_StyleScopedClasses['emphasis']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (__VLS_ctx.totalCostLabel);
}
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "menu-analysis-grid" },
});
/** @type {__VLS_StyleScopedClasses['menu-analysis-grid']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "panel nested-panel" },
});
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['nested-panel']} */ ;
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
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "panel-hint" },
});
/** @type {__VLS_StyleScopedClasses['panel-hint']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
(__VLS_ctx.planRows.length);
let __VLS_50;
/** @ts-ignore @type {typeof __VLS_components.elSkeleton | typeof __VLS_components.ElSkeleton | typeof __VLS_components.elSkeleton | typeof __VLS_components.ElSkeleton} */
elSkeleton;
// @ts-ignore
const __VLS_51 = __VLS_asFunctionalComponent1(__VLS_50, new __VLS_50({
    loading: (__VLS_ctx.loading),
    animated: true,
    rows: (6),
}));
const __VLS_52 = __VLS_51({
    loading: (__VLS_ctx.loading),
    animated: true,
    rows: (6),
}, ...__VLS_functionalComponentArgsRest(__VLS_51));
const { default: __VLS_55 } = __VLS_53.slots;
if (__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "menu-mobile-card-list" },
        'data-testid': "menu-plan-mobile-list",
    });
    /** @type {__VLS_StyleScopedClasses['menu-mobile-card-list']} */ ;
    for (const [row] of __VLS_vFor((__VLS_ctx.planRows))) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
            key: (`${row.ingredient_name}-${row.menu_name}-${row.recommended_market}`),
            ...{ class: "menu-mobile-card" },
            'data-testid': "menu-plan-mobile-card",
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-card']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "menu-mobile-card-head" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-card-head']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "plan-ingredient-cell" },
        });
        /** @type {__VLS_StyleScopedClasses['plan-ingredient-cell']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (row.ingredient_name || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.menu_name || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: (['status-chip', row.price_status === '已匹配报价' ? 'ok' : 'pending']) },
        });
        /** @type {__VLS_StyleScopedClasses['status-chip']} */ ;
        (row.price_status || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "menu-mobile-metrics" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-metrics']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "menu-mobile-metric emphasis" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-metric']} */ ;
        /** @type {__VLS_StyleScopedClasses['emphasis']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({
            ...{ class: "menu-mobile-price" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-price']} */ ;
        (__VLS_ctx.formatPrice(row.estimated_cost));
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "menu-mobile-metric" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-metric']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.formatPrice(row.reference_price));
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.price_unit_basis === '元/公斤' ? '统一公斤口径' : (row.price_unit_basis || '口径待确认'));
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "menu-mobile-metric" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-metric']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.formatQuantity(row.estimated_quantity, row.quantity_unit));
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.quantity_unit || '数量');
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "menu-mobile-data-row" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-data-row']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (row.recommended_market || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.recommended_site || '未标注报价源');
        if (row.backup_market || row.backup_site) {
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                ...{ class: "menu-mobile-data-row secondary" },
            });
            /** @type {__VLS_StyleScopedClasses['menu-mobile-data-row']} */ ;
            /** @type {__VLS_StyleScopedClasses['secondary']} */ ;
            __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
            __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
            (row.backup_market || row.backup_site || '-');
            __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
            (row.backup_site || '无备选来源');
        }
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
            ...{ class: "menu-mobile-card-note" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-card-note']} */ ;
        (row.distance_label || row.source_priority_label || row.remarks || '按价格和地区综合排序');
        if (row.remarks && row.remarks !== row.distance_label && row.remarks !== row.source_priority_label) {
            __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
                ...{ class: "menu-mobile-card-note secondary" },
            });
            /** @type {__VLS_StyleScopedClasses['menu-mobile-card-note']} */ ;
            /** @type {__VLS_StyleScopedClasses['secondary']} */ ;
            (row.remarks);
        }
        // @ts-ignore
        [isMobileViewport, loading, parsedMenuCount, matchedPlanCount, pendingPlanCount, pendingPlanCount, totalCostLabel, pendingOverflowCount, pendingOverflowCount, planRows, planRows, formatPrice, formatPrice, formatQuantity,];
    }
    if (!__VLS_ctx.planRows.length) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "table-empty-state" },
        });
        /** @type {__VLS_StyleScopedClasses['table-empty-state']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
    }
}
else {
    let __VLS_56;
    /** @ts-ignore @type {typeof __VLS_components.elTable | typeof __VLS_components.ElTable | typeof __VLS_components.elTable | typeof __VLS_components.ElTable} */
    elTable;
    // @ts-ignore
    const __VLS_57 = __VLS_asFunctionalComponent1(__VLS_56, new __VLS_56({
        data: (__VLS_ctx.planRows),
        height: "410",
        size: "small",
    }));
    const __VLS_58 = __VLS_57({
        data: (__VLS_ctx.planRows),
        height: "410",
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_57));
    const { default: __VLS_61 } = __VLS_59.slots;
    let __VLS_62;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn | typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_63 = __VLS_asFunctionalComponent1(__VLS_62, new __VLS_62({
        label: "食材 / 菜品",
        minWidth: "172",
        showOverflowTooltip: true,
    }));
    const __VLS_64 = __VLS_63({
        label: "食材 / 菜品",
        minWidth: "172",
        showOverflowTooltip: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_63));
    const { default: __VLS_67 } = __VLS_65.slots;
    {
        const { default: __VLS_68 } = __VLS_65.slots;
        const [{ row }] = __VLS_vSlot(__VLS_68);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "plan-ingredient-cell" },
        });
        /** @type {__VLS_StyleScopedClasses['plan-ingredient-cell']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (row.ingredient_name || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.menu_name || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({
            ...{ class: "plan-inline-number" },
        });
        /** @type {__VLS_StyleScopedClasses['plan-inline-number']} */ ;
        (__VLS_ctx.formatQuantity(row.estimated_quantity, row.quantity_unit));
        // @ts-ignore
        [planRows, planRows, formatQuantity,];
    }
    // @ts-ignore
    [];
    var __VLS_65;
    let __VLS_69;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn | typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_70 = __VLS_asFunctionalComponent1(__VLS_69, new __VLS_69({
        label: "推荐 / 备选",
        minWidth: "176",
        showOverflowTooltip: true,
    }));
    const __VLS_71 = __VLS_70({
        label: "推荐 / 备选",
        minWidth: "176",
        showOverflowTooltip: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_70));
    const { default: __VLS_74 } = __VLS_72.slots;
    {
        const { default: __VLS_75 } = __VLS_72.slots;
        const [{ row }] = __VLS_vSlot(__VLS_75);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "plan-ingredient-cell" },
        });
        /** @type {__VLS_StyleScopedClasses['plan-ingredient-cell']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (row.recommended_market || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.recommended_site || '未标注报价源');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.backup_market || row.backup_site || '无备选市场');
        // @ts-ignore
        [];
    }
    // @ts-ignore
    [];
    var __VLS_72;
    let __VLS_76;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn | typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_77 = __VLS_asFunctionalComponent1(__VLS_76, new __VLS_76({
        label: "报价 / 成本",
        minWidth: "148",
    }));
    const __VLS_78 = __VLS_77({
        label: "报价 / 成本",
        minWidth: "148",
    }, ...__VLS_functionalComponentArgsRest(__VLS_77));
    const { default: __VLS_81 } = __VLS_79.slots;
    {
        const { default: __VLS_82 } = __VLS_79.slots;
        const [{ row }] = __VLS_vSlot(__VLS_82);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "plan-ingredient-cell" },
        });
        /** @type {__VLS_StyleScopedClasses['plan-ingredient-cell']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.formatPrice(row.reference_price));
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.price_unit_basis === '元/公斤' ? '统一公斤口径' : (row.price_unit_basis || '口径待确认'));
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({
            ...{ class: "plan-inline-number" },
        });
        /** @type {__VLS_StyleScopedClasses['plan-inline-number']} */ ;
        (__VLS_ctx.formatPrice(row.estimated_cost));
        // @ts-ignore
        [formatPrice, formatPrice,];
    }
    // @ts-ignore
    [];
    var __VLS_79;
    let __VLS_83;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn | typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_84 = __VLS_asFunctionalComponent1(__VLS_83, new __VLS_83({
        label: "状态 / 说明",
        minWidth: "180",
        showOverflowTooltip: true,
    }));
    const __VLS_85 = __VLS_84({
        label: "状态 / 说明",
        minWidth: "180",
        showOverflowTooltip: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_84));
    const { default: __VLS_88 } = __VLS_86.slots;
    {
        const { default: __VLS_89 } = __VLS_86.slots;
        const [{ row }] = __VLS_vSlot(__VLS_89);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "plan-status-cell" },
        });
        /** @type {__VLS_StyleScopedClasses['plan-status-cell']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: (['status-chip', row.price_status === '已匹配报价' ? 'ok' : 'pending']) },
        });
        /** @type {__VLS_StyleScopedClasses['status-chip']} */ ;
        (row.price_status || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.distance_label || row.source_priority_label || '按价格和地区综合排序');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.remarks || '无额外说明');
        // @ts-ignore
        [];
    }
    // @ts-ignore
    [];
    var __VLS_86;
    // @ts-ignore
    [];
    var __VLS_59;
}
// @ts-ignore
[];
var __VLS_53;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "panel nested-panel" },
});
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['nested-panel']} */ ;
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
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "panel-hint" },
});
/** @type {__VLS_StyleScopedClasses['panel-hint']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
(__VLS_ctx.ingredientRows.length);
let __VLS_90;
/** @ts-ignore @type {typeof __VLS_components.elSkeleton | typeof __VLS_components.ElSkeleton | typeof __VLS_components.elSkeleton | typeof __VLS_components.ElSkeleton} */
elSkeleton;
// @ts-ignore
const __VLS_91 = __VLS_asFunctionalComponent1(__VLS_90, new __VLS_90({
    loading: (__VLS_ctx.loading),
    animated: true,
    rows: (5),
}));
const __VLS_92 = __VLS_91({
    loading: (__VLS_ctx.loading),
    animated: true,
    rows: (5),
}, ...__VLS_functionalComponentArgsRest(__VLS_91));
const { default: __VLS_95 } = __VLS_93.slots;
if (__VLS_ctx.isMobileViewport) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "menu-mobile-card-list ingredient-mobile-list" },
        'data-testid': "ingredient-mobile-list",
    });
    /** @type {__VLS_StyleScopedClasses['menu-mobile-card-list']} */ ;
    /** @type {__VLS_StyleScopedClasses['ingredient-mobile-list']} */ ;
    for (const [row] of __VLS_vFor((__VLS_ctx.ingredientRows))) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
            key: (`${row.menu_name}-${row.ingredient_name}-${row.estimated_quantity}`),
            ...{ class: "menu-mobile-card ingredient-mobile-card" },
            'data-testid': "ingredient-mobile-card",
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-card']} */ ;
        /** @type {__VLS_StyleScopedClasses['ingredient-mobile-card']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "menu-mobile-card-head" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-card-head']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "plan-ingredient-cell" },
        });
        /** @type {__VLS_StyleScopedClasses['plan-ingredient-cell']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (row.ingredient_name || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.small, __VLS_intrinsics.small)({});
        (row.menu_name || '-');
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "price-chip avg" },
        });
        /** @type {__VLS_StyleScopedClasses['price-chip']} */ ;
        /** @type {__VLS_StyleScopedClasses['avg']} */ ;
        (__VLS_ctx.formatQuantity(row.estimated_quantity, row.quantity_unit));
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
            ...{ class: "menu-mobile-card-note" },
        });
        /** @type {__VLS_StyleScopedClasses['menu-mobile-card-note']} */ ;
        (row.remarks || '无额外备注');
        // @ts-ignore
        [isMobileViewport, loading, formatQuantity, ingredientRows, ingredientRows,];
    }
    if (!__VLS_ctx.ingredientRows.length) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "table-empty-state" },
        });
        /** @type {__VLS_StyleScopedClasses['table-empty-state']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
    }
}
else {
    let __VLS_96;
    /** @ts-ignore @type {typeof __VLS_components.elTable | typeof __VLS_components.ElTable | typeof __VLS_components.elTable | typeof __VLS_components.ElTable} */
    elTable;
    // @ts-ignore
    const __VLS_97 = __VLS_asFunctionalComponent1(__VLS_96, new __VLS_96({
        data: (__VLS_ctx.ingredientRows),
        height: "410",
        size: "small",
    }));
    const __VLS_98 = __VLS_97({
        data: (__VLS_ctx.ingredientRows),
        height: "410",
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_97));
    const { default: __VLS_101 } = __VLS_99.slots;
    let __VLS_102;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_103 = __VLS_asFunctionalComponent1(__VLS_102, new __VLS_102({
        prop: "menu_name",
        label: "菜品",
        minWidth: "144",
        showOverflowTooltip: true,
    }));
    const __VLS_104 = __VLS_103({
        prop: "menu_name",
        label: "菜品",
        minWidth: "144",
        showOverflowTooltip: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_103));
    let __VLS_107;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_108 = __VLS_asFunctionalComponent1(__VLS_107, new __VLS_107({
        prop: "ingredient_name",
        label: "食材",
        minWidth: "132",
        showOverflowTooltip: true,
    }));
    const __VLS_109 = __VLS_108({
        prop: "ingredient_name",
        label: "食材",
        minWidth: "132",
        showOverflowTooltip: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_108));
    let __VLS_112;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn | typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_113 = __VLS_asFunctionalComponent1(__VLS_112, new __VLS_112({
        label: "数量",
        width: "112",
    }));
    const __VLS_114 = __VLS_113({
        label: "数量",
        width: "112",
    }, ...__VLS_functionalComponentArgsRest(__VLS_113));
    const { default: __VLS_117 } = __VLS_115.slots;
    {
        const { default: __VLS_118 } = __VLS_115.slots;
        const [{ row }] = __VLS_vSlot(__VLS_118);
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "plan-inline-number" },
        });
        /** @type {__VLS_StyleScopedClasses['plan-inline-number']} */ ;
        (__VLS_ctx.formatQuantity(row.estimated_quantity, row.quantity_unit));
        // @ts-ignore
        [formatQuantity, ingredientRows, ingredientRows,];
    }
    // @ts-ignore
    [];
    var __VLS_115;
    let __VLS_119;
    /** @ts-ignore @type {typeof __VLS_components.elTableColumn | typeof __VLS_components.ElTableColumn} */
    elTableColumn;
    // @ts-ignore
    const __VLS_120 = __VLS_asFunctionalComponent1(__VLS_119, new __VLS_119({
        prop: "remarks",
        label: "备注",
        minWidth: "180",
        showOverflowTooltip: true,
    }));
    const __VLS_121 = __VLS_120({
        prop: "remarks",
        label: "备注",
        minWidth: "180",
        showOverflowTooltip: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_120));
    // @ts-ignore
    [];
    var __VLS_99;
}
// @ts-ignore
[];
var __VLS_93;
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({
    __typeEmits: {},
    __typeProps: {},
});
export default {};
