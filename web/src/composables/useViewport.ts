import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const MOBILE_BREAKPOINT = 820
const NARROW_BREAKPOINT = 1100
const SHORT_HEIGHT_BREAKPOINT = 560

export function useViewport() {
  const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1440)
  const viewportHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 960)

  const syncViewportSize = () => {
    if (typeof window === 'undefined') {
      return
    }
    viewportWidth.value = window.innerWidth
    viewportHeight.value = window.innerHeight
  }

  onMounted(() => {
    syncViewportSize()
    window.addEventListener('resize', syncViewportSize)
  })

  onBeforeUnmount(() => {
    if (typeof window === 'undefined') {
      return
    }
    window.removeEventListener('resize', syncViewportSize)
  })

  return {
    viewportWidth,
    viewportHeight,
    isMobileViewport: computed(() => viewportWidth.value <= MOBILE_BREAKPOINT),
    isNarrowViewport: computed(() => viewportWidth.value <= NARROW_BREAKPOINT),
    isShortViewport: computed(() => viewportHeight.value <= SHORT_HEIGHT_BREAKPOINT),
  }
}
