/// <reference types="vite/client" />

declare module 'element-plus/es/components/*/style/css'

declare module 'vue-router' {
  export type RouteLocationRaw = string | Record<string, unknown>
  export type RouteLocationNormalizedLoaded = Record<string, unknown>
  export type Router = Record<string, unknown>
  export type RouteRecordRaw = Record<string, unknown>
  export function useRoute(): RouteLocationNormalizedLoaded
  export function useRouter(): Router
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'

  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>
  export default component
}
