import { createApp, defineAsyncComponent, h } from 'vue'
import type { Component } from 'vue'
import './root.css'

const pathname = typeof window !== 'undefined'
  ? window.location.pathname.replace(/\/$/, '') || '/'
  : '/'
const RootLoading = {
  name: 'RootLoading',
  setup() {
    return () => h('div', { class: 'app-root-loader', role: 'status', 'aria-live': 'polite' }, [
      h('span', { class: 'app-root-loader-ring' }),
      h('strong', '正在打开系统'),
      h('small', '业务界面加载中'),
    ])
  },
}

const App = defineAsyncComponent({
  loader: () => import('./App.vue'),
  loadingComponent: RootLoading,
  delay: 0,
  suspensible: false,
})
const PlatformAdminApp = defineAsyncComponent({
  loader: () => import('./PlatformAdminApp.vue'),
  loadingComponent: RootLoading,
  delay: 0,
  suspensible: false,
})
const SupplierBackendApp = defineAsyncComponent({
  loader: () => import('./SupplierBackendApp.vue'),
  loadingComponent: RootLoading,
  delay: 0,
  suspensible: false,
})
const SupplierPortalApp = defineAsyncComponent({
  loader: () => import('./SupplierPortalApp.vue'),
  loadingComponent: RootLoading,
  delay: 0,
  suspensible: false,
})

const rootComponent = pathname === '/supplier-portal'
  ? SupplierPortalApp
  : pathname === '/supplier' || pathname === '/supplier-backend'
    ? SupplierBackendApp
    : pathname === '/admin'
      ? PlatformAdminApp
      : App

const app = createApp(rootComponent)

const elementComponentLoaders = {
  ElAlert: () => Promise.all([
    import('element-plus/es/components/alert/index.mjs'),
    import('element-plus/es/components/alert/style/css'),
  ]).then(([componentModule]) => componentModule.ElAlert),
  ElButton: () => Promise.all([
    import('element-plus/es/components/button/index.mjs'),
    import('element-plus/es/components/button/style/css'),
  ]).then(([componentModule]) => componentModule.ElButton),
  ElCheckbox: () => Promise.all([
    import('element-plus/es/components/checkbox/index.mjs'),
    import('element-plus/es/components/checkbox/style/css'),
  ]).then(([componentModule]) => componentModule.ElCheckbox),
  ElDatePicker: () => Promise.all([
    import('element-plus/es/components/date-picker/index.mjs'),
    import('element-plus/es/components/date-picker/style/css'),
  ]).then(([componentModule]) => componentModule.ElDatePicker),
  ElDialog: () => Promise.all([
    import('element-plus/es/components/dialog/index.mjs'),
    import('element-plus/es/components/dialog/style/css'),
  ]).then(([componentModule]) => componentModule.ElDialog),
  ElInput: () => Promise.all([
    import('element-plus/es/components/input/index.mjs'),
    import('element-plus/es/components/input/style/css'),
  ]).then(([componentModule]) => componentModule.ElInput),
  ElInputNumber: () => Promise.all([
    import('element-plus/es/components/input-number/index.mjs'),
    import('element-plus/es/components/input-number/style/css'),
  ]).then(([componentModule]) => componentModule.ElInputNumber),
  ElOption: () => Promise.all([
    import('element-plus/es/components/select/index.mjs'),
    import('element-plus/es/components/option/style/css'),
  ]).then(([componentModule]) => componentModule.ElOption),
  ElPagination: () => Promise.all([
    import('element-plus/es/components/pagination/index.mjs'),
    import('element-plus/es/components/pagination/style/css'),
  ]).then(([componentModule]) => componentModule.ElPagination),
  ElProgress: () => Promise.all([
    import('element-plus/es/components/progress/index.mjs'),
    import('element-plus/es/components/progress/style/css'),
  ]).then(([componentModule]) => componentModule.ElProgress),
  ElRadioButton: () => Promise.all([
    import('element-plus/es/components/radio/index.mjs'),
    import('element-plus/es/components/radio-button/style/css'),
  ]).then(([componentModule]) => componentModule.ElRadioButton),
  ElRadioGroup: () => Promise.all([
    import('element-plus/es/components/radio/index.mjs'),
    import('element-plus/es/components/radio-group/style/css'),
  ]).then(([componentModule]) => componentModule.ElRadioGroup),
  ElSelect: () => Promise.all([
    import('element-plus/es/components/select/index.mjs'),
    import('element-plus/es/components/select/style/css'),
  ]).then(([componentModule]) => componentModule.ElSelect),
  ElSkeleton: () => Promise.all([
    import('element-plus/es/components/skeleton/index.mjs'),
    import('element-plus/es/components/skeleton/style/css'),
  ]).then(([componentModule]) => componentModule.ElSkeleton),
  ElSwitch: () => Promise.all([
    import('element-plus/es/components/switch/index.mjs'),
    import('element-plus/es/components/switch/style/css'),
  ]).then(([componentModule]) => componentModule.ElSwitch),
  ElTable: () => Promise.all([
    import('element-plus/es/components/table/index.mjs'),
    import('element-plus/es/components/table/style/css'),
  ]).then(([componentModule]) => componentModule.ElTable),
  ElTableColumn: () => Promise.all([
    import('element-plus/es/components/table/index.mjs'),
    import('element-plus/es/components/table/style/css'),
  ]).then(([componentModule]) => componentModule.ElTableColumn),
}

Object.entries(elementComponentLoaders).forEach(([componentName, loadElementComponent]) => {
  app.component(componentName, defineAsyncComponent(loadElementComponent as () => Promise<Component>))
})

app.mount('#app')
