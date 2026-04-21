export const locationOptionsResponse = {
  provinces: ['浙江省', '江苏省'],
  cities: ['杭州', '宁波', '苏州'],
  province_city_map: {
    浙江省: ['杭州', '宁波'],
    江苏省: ['苏州'],
  },
}

export const marketSummaryResponse = {
  items: [
    {
      product_name: '西兰花',
      price_identity_key: 'veg-broccoli',
      site_count: 4,
      market_count: 4,
      price_unit_basis: '元/公斤',
      lowest_price: 6.2,
      lowest_price_site: '城北市场',
      highest_price: 8.6,
      highest_price_site: '江南市场',
      average_price: 7.1,
      region_label: '杭州',
    },
    {
      product_name: '鲈鱼',
      price_identity_key: 'fish-bass',
      site_count: 3,
      market_count: 3,
      price_unit_basis: '元/公斤',
      lowest_price: 28.5,
      lowest_price_site: '滨江市场',
      highest_price: 32.0,
      highest_price_site: '城北市场',
      average_price: 30.1,
      region_label: '杭州',
    },
  ],
}

export const sourceCoverageResponse = {
  items: [
    {
      source_url: 'https://example.com/source-1',
      configured_name: '杭州农批',
      source_name: '杭州农批',
      product_key_count: 120,
      comparable_item_count: 86,
      source_item_count: 140,
      market_count: 4,
      latest_capture: '2026-04-18 08:20:00',
      failed_count: 0,
      status: '已入库',
    },
  ],
}

export const crawlStatusResponse = {
  item: {
    is_running: false,
    last_finished_at: '2026-04-18 08:20:00',
    completed_sources: 12,
    progress_percent: 100,
    last_total_sources: 12,
    last_success_count: 12,
    last_failed_count: 0,
    next_run_at: '2026-04-19 08:00:00',
    schedule_enabled: true,
    schedule_interval_seconds: 86400,
    schedule_fetch_mode: 'requests',
  },
}

export const productOptionsResponse = {
  items: [
    {
      price_identity_key: 'veg-broccoli',
      price_identity_label: '西兰花',
      site_count: 4,
    },
    {
      price_identity_key: 'fish-bass',
      price_identity_label: '鲈鱼',
      site_count: 3,
    },
  ],
}

export const productSummaryByKey: Record<string, { item: Record<string, string | number | null> }> = {
  'veg-broccoli': {
    item: {
      current_lowest_price: '6.20',
      current_lowest_site: '城北市场',
      current_highest_price: '8.60',
      current_highest_site: '江南市场',
      average_price: '7.10',
      latest_captured_at: '2026-04-18 08:20:00',
    },
  },
  'fish-bass': {
    item: {
      current_lowest_price: '28.50',
      current_lowest_site: '滨江市场',
      current_highest_price: '32.00',
      current_highest_site: '城北市场',
      average_price: '30.10',
      latest_captured_at: '2026-04-18 08:20:00',
    },
  },
}

const duplicateTrendRows = [
  {
    captured_at: '2026-04-16 08:00:00',
    current_price: 6.2,
  },
  {
    captured_at: '2026-04-17 08:00:00',
    current_price: 6.8,
  },
  {
    captured_at: '2026-04-18 08:00:00',
    current_price: 7.1,
  },
]

const alternateTrendRows = [
  {
    captured_at: '2026-04-16 08:00:00',
    current_price: 7.4,
  },
  {
    captured_at: '2026-04-17 08:00:00',
    current_price: 7.8,
  },
  {
    captured_at: '2026-04-18 08:00:00',
    current_price: 8.0,
  },
]

export const crossMarketTrendByKey: Record<string, { items: Array<Record<string, string | number | null>> }> = {
  'veg-broccoli': {
    items: [
      ...duplicateTrendRows.map((row) => ({
        ...row,
        site_name: '杭州农批 | 城北市场',
        market_name: '城北市场',
        region_label: '杭州',
      })),
      ...duplicateTrendRows.map((row) => ({
        ...row,
        site_name: '杭州农批 | 江南市场',
        market_name: '江南市场',
        region_label: '杭州',
      })),
      ...alternateTrendRows.map((row) => ({
        ...row,
        site_name: '宁波农批 | 鄞州市场',
        market_name: '鄞州市场',
        region_label: '宁波',
      })),
      ...alternateTrendRows.map((row) => ({
        ...row,
        site_name: '苏州农批 | 园区市场',
        market_name: '园区市场',
        region_label: '苏州',
      })),
    ],
  },
  'fish-bass': {
    items: [
      {
        site_name: '杭州农批 | 滨江市场',
        market_name: '滨江市场',
        region_label: '杭州',
        captured_at: '2026-04-16 08:00:00',
        current_price: 28.5,
      },
      {
        site_name: '杭州农批 | 滨江市场',
        market_name: '滨江市场',
        region_label: '杭州',
        captured_at: '2026-04-17 08:00:00',
        current_price: 29.4,
      },
      {
        site_name: '杭州农批 | 滨江市场',
        market_name: '滨江市场',
        region_label: '杭州',
        captured_at: '2026-04-18 08:00:00',
        current_price: 30.1,
      },
    ],
  },
}

export const singleMarketTrendByKey: Record<string, Record<string, { items: Array<Record<string, string | number | null>> }>> = {
  'veg-broccoli': {
    '杭州农批 · 城北市场': {
      items: duplicateTrendRows.map((row) => ({
        ...row,
        site_name: '杭州农批 | 城北市场',
        market_name: '城北市场',
        region_label: '杭州',
      })),
    },
  },
  'fish-bass': {
    '杭州农批 · 滨江市场': {
      items: [
        {
          site_name: '杭州农批 | 滨江市场',
          market_name: '滨江市场',
          region_label: '杭州',
          captured_at: '2026-04-16 08:00:00',
          current_price: 28.5,
        },
      ],
    },
  },
}

export const menuPlanResponse = {
  ingredient_items: [
    {
      menu_name: '蒜蓉西兰花',
      ingredient_name: '西兰花',
      estimated_quantity: 6,
      quantity_unit: '公斤',
      remarks: '按 10 桌估算',
    },
    {
      menu_name: '清蒸鲈鱼',
      ingredient_name: '鲈鱼',
      estimated_quantity: 8,
      quantity_unit: '公斤',
      remarks: '按 10 桌估算',
    },
  ],
  procurement_plan: [
    {
      menu_name: '蒜蓉西兰花',
      ingredient_name: '西兰花',
      estimated_quantity: 6,
      quantity_unit: '公斤',
      price_unit_basis: '元/公斤',
      reference_price: 7.1,
      estimated_cost: 42.6,
      recommended_market: '城北市场',
      recommended_site: '杭州农批',
      backup_market: '江南市场',
      backup_site: '杭州农批',
      source_priority_label: '主表优先',
      distance_label: '当前位置 8 公里',
      price_status: '已匹配报价',
      remarks: '价格稳定',
    },
    {
      menu_name: '清蒸鲈鱼',
      ingredient_name: '鲈鱼',
      estimated_quantity: 8,
      quantity_unit: '公斤',
      price_unit_basis: '元/公斤',
      reference_price: 30.1,
      estimated_cost: 240.8,
      recommended_market: '滨江市场',
      recommended_site: '杭州农批',
      backup_market: '城北市场',
      backup_site: '杭州农批',
      source_priority_label: '主表优先',
      distance_label: '当前位置 12 公里',
      price_status: '已匹配报价',
      remarks: '早市价格更优',
    },
  ],
}

export const signalsOverviewResponse = {
  generated_at: '2026-04-18',
  scope: {
    province: '浙江省',
    city: '杭州',
    focus: null,
  },
  headline: '杭州当前更适合先讲机会窗口，再讲风险规避。',
  overview_metrics: [
    { label: '信号总数', value: '6', detail: '可直接演示的商品信号' },
    { label: '高优先级', value: '2', detail: '值得先讲给老板听' },
    { label: '平均置信度', value: '78', detail: '规则判断置信度' },
    { label: '预估影响值', value: '26', detail: '可用于销售表达' },
  ],
  top_opportunities: [
    {
      identity_key: 'veg-broccoli',
      product_name: '西兰花',
      signal_code: 'overview',
      signal_level: 'medium',
      timing_score: 82,
      risk_score: 36,
      confidence: 80,
      recommended_action: '立即采购',
      reason_summary: '当前价格处于偏低区间，跨市场价差明显。',
      recommended_market: '城北市场',
      source_health: 'stable',
      trend_label: '下降',
    },
    {
      identity_key: 'fish-bass',
      product_name: '鲈鱼',
      signal_code: 'overview',
      signal_level: 'high',
      timing_score: 64,
      risk_score: 72,
      confidence: 76,
      recommended_action: '延后采购',
      reason_summary: '近几日价格继续上行，建议延后采购。',
      recommended_market: '滨江市场',
      source_health: 'stable',
      trend_label: '上涨',
    },
  ],
  top_risks: [
    {
      identity_key: 'fish-bass',
      product_name: '鲈鱼',
      signal_code: 'overview',
      signal_level: 'high',
      timing_score: 64,
      risk_score: 72,
      confidence: 76,
      recommended_action: '延后采购',
      reason_summary: '近几日价格继续上行，建议延后采购。',
      recommended_market: '滨江市场',
      source_health: 'stable',
      trend_label: '上涨',
    },
  ],
  recommended_actions: [
    { title: '优先锁定西兰花', description: '当前价格已回落到低位区间。', action: '立即采购', confidence: 80, impact_value: 12 },
    { title: '关注鲈鱼波动', description: '先讲风险，再给替代方案。', action: '延后采购', confidence: 76, impact_value: 14 },
  ],
  source_health: {
    status: 'healthy',
    product_count: 6,
    market_count: 4,
    latest_capture: '2026-04-18',
  },
  alert_count: 1,
  alert_items: [],
}

export const salesDemoContentResponse = {
  scene: 'sales',
  hero: {
    eyebrow: 'BATTEL SALE READY',
    title: '把价格工作台升级成可直接报价的经营决策产品。',
    description: '先让客户看懂今天的机会和风险，再展示采购建议和交付路径。',
    primary_cta: '进入老板驾驶舱',
    secondary_cta: '查看套餐',
  },
  proof_points: [
    { label: '可分析商品', value: '2' },
    { label: '覆盖市场', value: '4' },
    { label: '历史记录', value: '18' },
  ],
  scenes: [
    { title: '老板驾驶舱', description: '先展示今天该关注什么。', highlight: '3 分钟说清价值' },
    { title: '经营信号', description: '再解释为什么现在买、为什么现在不买。', highlight: '规则优先' },
    { title: '报价承接', description: '最后切到套餐和报价路径。', highlight: '直接成交' },
  ],
  storyline: ['先讲机会和风险。', '再落到真实单品与菜单。', '最后推进套餐报价。'],
}

export const pricingPackagesResponse = {
  items: [
    {
      name: '演示成交版',
      price_band: '轻量试点',
      target: '顾问型销售',
      recommended: false,
      features: ['老板摘要', '经营信号概览'],
      cta: '适合快速试点',
    },
    {
      name: '经营决策版',
      price_band: '主推报价',
      target: '采购团队',
      recommended: true,
      features: ['多地区经营信号', '采购增强建议', '报价承接页面'],
      cta: '适合作为正式主包报价',
    },
  ],
}

export const procurementRecommendResponse = {
  summary: {
    menu_count: 2,
    recommendation_count: 2,
    matched_count: 2,
    pending_count: 0,
    total_cost: 283.4,
  },
  ingredient_items: menuPlanResponse.ingredient_items,
  items: [
    {
      menu_name: '蒜蓉西兰花',
      ingredient_name: '西兰花',
      timing_score: 80,
      risk_score: 34,
      confidence: 82,
      signal_level: 'medium',
      recommended_action: '立即锁价',
      reason_summary: '当前价格回落，可优先锁量。',
    },
    {
      menu_name: '清蒸鲈鱼',
      ingredient_name: '鲈鱼',
      timing_score: 58,
      risk_score: 70,
      confidence: 74,
      signal_level: 'high',
      recommended_action: '分批采购',
      reason_summary: '价格偏强，建议分批确认。',
    },
  ],
}
