import type { MarketSummaryItem } from '../types'

type MarketCategoryRule = {
  key: string
  label: string
  keywords: RegExp
}

export const MARKET_CATEGORY_RULES: MarketCategoryRule[] = [
  {
    key: 'vegetable',
    label: '蔬菜',
    keywords: /菜|花菜|白菜|生菜|西兰花|菠菜|芹菜|萝卜|瓜|豆角|番茄|土豆|莲藕|茄子|椒|菌菇|香菇/i,
  },
  {
    key: 'dry',
    label: '干调',
    keywords: /干|调|椒|八角|桂皮|花椒|孜然|辣椒|木耳|香菇干|腐竹|银耳|香料|调味|酱|醋|料酒/i,
  },
  {
    key: 'seafood',
    label: '水产',
    keywords: /鱼|虾|蟹|贝|鲈|海参|海鲜|蛤|螺|鲍|鳝/i,
  },
  {
    key: 'frozen',
    label: '冻品',
    keywords: /冻|丸|肠|翅|爪|半成品|速冻|培根|火锅料/i,
  },
  {
    key: 'meat',
    label: '肉禽蛋',
    keywords: /鸡|鸭|鹅|猪|牛|羊|排|里脊|五花|蛋|肉/i,
  },
  {
    key: 'grain',
    label: '粮油米面',
    keywords: /米|面|粉|油|豆|杂粮|面粉|挂面|面条|淀粉/i,
  },
]

export function resolveMarketCategory(rowOrProductName?: MarketSummaryItem | string | null) {
  if (rowOrProductName && typeof rowOrProductName === 'object') {
    const liancaiTopCategory = String(rowOrProductName.liancai_top_category || '').trim()
    if (liancaiTopCategory) return liancaiTopCategory
    const liancaiSubcategory = String(rowOrProductName.liancai_subcategory || '').trim()
    if (liancaiSubcategory && liancaiSubcategory !== '全部') return liancaiSubcategory
    const normalizedName = String(rowOrProductName.product_name || '').trim()
    if (!normalizedName) return '默认分类'
    const matchedRule = MARKET_CATEGORY_RULES.find((rule) => rule.keywords.test(normalizedName))
    return matchedRule?.label || '默认分类'
  }

  const normalizedName = String(rowOrProductName || '').trim()
  if (!normalizedName) {
    return '默认分类'
  }

  const matchedRule = MARKET_CATEGORY_RULES.find((rule) => rule.keywords.test(normalizedName))
  return matchedRule?.label || '默认分类'
}

export function resolveMarketCategoryMeta(row?: MarketSummaryItem | null) {
  const liancaiSubcategory = String(row?.liancai_subcategory || '').trim()
  const liancaiTopCategory = String(row?.liancai_top_category || '').trim()
  if (liancaiSubcategory || liancaiTopCategory) {
    const primary = liancaiTopCategory || (liancaiSubcategory !== '全部' ? liancaiSubcategory : '') || '默认分类'
    const secondary = liancaiSubcategory && liancaiSubcategory !== '全部' && liancaiSubcategory !== primary
      ? liancaiSubcategory
      : ''
    return {
      primary,
      secondary,
    }
  }
  return {
    primary: resolveMarketCategory(row || ''),
    secondary: '',
  }
}

export function buildMarketCategoryTabs(rows: MarketSummaryItem[]) {
  const counts = new Map<string, number>()

  rows.forEach((row) => {
    const label = resolveMarketCategory(row)
    counts.set(label, (counts.get(label) || 0) + 1)
  })

  const tabs = Array.from(counts.entries())
    .map(([label, count]) => ({
      key: label,
      label,
      count,
    }))
    .sort((left, right) => right.count - left.count)

  return [
    {
      key: '全部',
      label: '全部',
      count: rows.length,
    },
    ...tabs,
  ]
}
