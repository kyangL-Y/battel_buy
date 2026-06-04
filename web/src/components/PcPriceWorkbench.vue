<template>







  <div class="pcw" data-testid="pc-price-workbench">







    <aside class="pcw-side">







      <div class="pcw-side-head">







        <span class="pcw-logo">食</span>







        <div class="pcw-brand-copy">







          <strong>食采云</strong>







          <small>价格工作台</small>







        </div>







      </div>







      <nav class="pcw-nav" aria-label="市场价格工作台导航">







        <div v-for="group in navGroups" :key="group.title" class="pcw-nav-group">







          <span>{{ group.title }}</span>







          <button







            v-for="item in group.items"







            :key="item.id"







            type="button"







            :class="['pcw-nav-item', { active: currentSection === item.id }]"







            :aria-current="currentSection === item.id ? 'page' : undefined"







            :data-section-id="item.id"







            @click="handleNavSelect(item.id)"







          >







            <span class="pcw-nav-icon" aria-hidden="true">







              <svg viewBox="0 0 24 24" focusable="false">







                <path v-for="path in item.icon" :key="path" :d="path" />







              </svg>







            </span>







            <span>{{ item.label }}</span>







            <b v-if="item.badge">{{ item.badge }}</b>







          </button>







        </div>







      </nav>







      <div class="pcw-side-systems">







        <div class="pcw-side-sync">







          <span>数据来源</span>







          <strong>{{ sideSourceLabel }}</strong>







        </div>







        <button type="button" class="pcw-system primary" aria-label="进入供应商管理后台" @click="emit('open-supplier-backend')">







          <span>供应商管理后台</span>







          <strong>管理报价与账号</strong>







        </button>







        <button type="button" class="pcw-system" aria-label="查看供应商管理" @click="handleNavSelect('suppliers')">







          <span>供应商管理</span>







          <strong>看覆盖与待补录</strong>







        </button>







        <button type="button" class="pcw-system" aria-label="进入系统设置" @click="openInlineSystemSettings">







          <span>数据与设置</span>







          <strong>同步与异常</strong>







        </button>







      </div>







    </aside>















    <section class="pcw-app">







      <header class="pcw-top">







        <div ref="locationPicker" class="pcw-location">







          <button







            type="button"







            class="pcw-location-button"







            :aria-expanded="locationMenuVisible"







            aria-haspopup="menu"







            @click="toggleLocationMenu"







          >







            <span class="pcw-pin" aria-hidden="true"></span>







            <strong>{{ displayLocationLabel }}</strong>







            <small>⌄</small>







          </button>







          <div v-if="locationMenuVisible" class="pcw-location-menu" role="menu">
            <button
              type="button"
              class="pcw-location-suggest"
              :disabled="props.locationSuggestionLoading"
              role="menuitem"
              @click="emit('request-location-suggestion')"
            >
              {{ props.locationSuggestionLoading ? '定位中...' : '用当前位置' }}
            </button>
            <button







              v-for="option in primaryLocationOptions"







              :key="option"







              type="button"







              :class="{ selected: displayLocationLabel === option }"







              role="menuitemradio"







              :aria-checked="displayLocationLabel === option"







              @click="selectLocation(option)"







            >







              {{ option }}







            </button>
            <button
              v-if="overflowLocationOptions.length && !locationMenuExpanded"
              type="button"
              class="pcw-location-more"
              @click="locationMenuExpanded = true"
            >
              更多地区
            </button>
            <div v-if="locationMenuExpanded && overflowLocationOptions.length" class="pcw-location-menu-group-label">更多地区</div>
            <button
              v-for="option in locationMenuExpanded ? overflowLocationOptions : []"
              :key="`overflow-${option}`"
              type="button"
              :class="{ selected: displayLocationLabel === option }"
              role="menuitemradio"
              :aria-checked="displayLocationLabel === option"
              @click="selectLocation(option)"
            >
              {{ option }}
            </button>







          </div>







        </div>







        <button type="button" class="pcw-menu" aria-label="返回汇总行情" @click="handleNavSelect('summary')">







          <span aria-hidden="true"></span>







        </button>







        <h1>{{ pageTitle }}</h1>







        <div class="pcw-top-actions">







          <button type="button" :disabled="props.refreshing" @click="emit('refresh')">{{ props.refreshing ? '刷新中' : '刷新' }}</button>







          <button type="button" @click="openMessagePanel">







            消息<span v-if="alertBadge">{{ alertBadge }}</span>







          </button>







          <button type="button" @click="emit('open-procurement-auth')">{{ procurementAuthButtonLabel }}</button>

          <button v-if="props.authRole === 'admin' || props.authRole === 'procurement'" type="button" @click="emit('logout-procurement-auth')">退出</button>

          <button type="button" class="pcw-user" @click="handleNavSelect('suppliers')">企业设置</button>







        </div>







      </header>















      <main ref="mainViewport" class="pcw-main">







        <section
          v-if="showWorkbenchFilter"







          ref="filterToolbar"







          class="pcw-filter"







          :class="{







            [`section-${currentSection}`]: true,







            'is-trend': currentSection === 'trend',







            'is-alert': currentSection === 'alerts',







            'is-module': currentSection !== 'summary' && currentSection !== 'trend' && currentSection !== 'alerts',







          }"







        >







          <div







            v-for="entry in displayedTopFilters"







            :key="`${currentSection}-${entry.index}-${entry.value}`"







            class="pcw-filter-item"







            :data-testid="currentSection === 'trend' && entry.index === 0 ? 'pcw-trend-product-filter' : undefined"







          >







            <button







              type="button"







              :class="{ active: isFilterSelected(entry.index), focused: activeFilterIndex === entry.index, open: activeFilterMenu === entry.index }"
              :disabled="!hasFilterChoices(entry.index)"







              :aria-expanded="activeFilterMenu === entry.index"







              :title="getFilterButtonTitle(entry.index, entry.value)"







              @click="handleFilterSelect(entry.index)"







            >







              <span>{{ getFilterButtonLabel(entry.index, entry.value) }}</span>







              <small>{{ hasFilterChoices(entry.index) ? '⌄' : '—' }}</small>







            </button>







            <div v-if="activeFilterMenu === entry.index" class="pcw-filter-menu" role="menu">







              <input







                v-if="(sectionFilterOptions[currentSection]?.[entry.index] || []).length > 1"







                v-model="filterSearchText"







                class="pcw-filter-search"







                type="search"







                placeholder="搜索"







                @click.stop







                @keydown.stop







              />







              <button







                v-for="option in getVisibleFilterOptions(entry.index)"







                :key="`${currentSection}-${entry.index}-${option.optionIndex}-${option.value}`"







                type="button"







                :class="{ selected: filterSelections[currentSection]?.[entry.index] === option.optionIndex }"







                role="menuitemradio"







                :aria-checked="filterSelections[currentSection]?.[entry.index] === option.optionIndex"











                :title="formatFilterLabel(option.value)"


                @click="selectFilterOption(entry.index, option.optionIndex)"







              >







                {{ formatFilterLabel(option.value) }}







              </button>







            </div>







          </div>







          <div v-if="currentSection === 'trend'" class="pcw-price-toggle">







            <button type="button" :class="{ active: priceMetric === 'avg' }" @click="priceMetric = 'avg'">均价</button>







            <button type="button" :class="{ active: priceMetric === 'low' }" @click="priceMetric = 'low'">最低价</button>







          </div>







          <button type="button" class="pcw-export" @click="handleExportData">导出数据</button>







        </section>







        <div v-if="actionFeedback" class="pcw-action-toast" role="status">{{ actionFeedback }}</div>















        <section v-if="topKpis.length" :class="['pcw-kpis', `is-${currentSection}`]" aria-label="今日指标">







          <article v-for="item in topKpis" :key="item.label">







            <span>{{ item.label }}</span>







            <strong>{{ item.value }}</strong>







            <small :class="item.tone">{{ item.detail }}</small>







          </article>







        </section>















        <section v-if="currentSection === 'summary'" key="pcw-section-summary" class="pcw-grid pcw-grid-summary-full">







          <div class="pcw-summary-main">







          <section class="pcw-card pcw-table-card">







            <div class="pcw-card-head">







              <h2>今日行情列表</h2>







              <span>{{ props.summaryStatusText || `共 ${displayRowTotal} 条` }}</span>







            </div>







            <table>







              <thead>







                <tr>







                  <th>商品</th>







                  <th>分类</th>














                  <th>均价(元/公斤)</th>







                  <th>最低价(元/公斤)</th>







                  <th>价差</th>














                  <th>有效报价</th>







                  <th>操作</th>







                </tr>







              </thead>







              <tbody>







                <tr v-if="!displayRows.length" class="pcw-empty-row" data-testid="pcw-summary-empty-row">







                  <td colspan="7">







                    <div class="pcw-empty-state">







                      <strong>{{ summaryEmptyTitle }}</strong>







                      <span>{{ summaryEmptyDetail }}</span>







                    </div>







                  </td>







                </tr>







                <tr v-for="row in displayRows" :key="row.name" data-testid="pcw-summary-data-row">







                  <td :title="row.name">







                    <button type="button" class="pcw-product" @click="openSummaryProductTrend(row.identityKey)">







                      <span
                        :class="['pcw-thumb', row.thumb, { 'has-image': Boolean(resolveSafeImageUrl(row.imageUrl)) }]"
                        :style="resolveSafeImageUrl(row.imageUrl) ? { '--pcw-thumb-image': `url('${resolveSafeImageUrl(row.imageUrl)}')` } : undefined"
                        @click.stop="openImagePreview(resolveSafeImageUrl(row.imageUrl), row.name)"
                      ></span>

                      <span class="pcw-product-copy">
                        <strong>{{ row.name }}</strong>
                        <small>{{ row.source }} · {{ formatDisplayCategoryPath(row) }}</small>
                      </span>







                    </button>







                  </td>







                  <td :title="formatDisplayCategoryPath(row)">{{ formatDisplayCategoryPath(row) }}</td>









                  <td>{{ row.avg }}</td>







                  <td>{{ row.low }}</td>







                  <td>{{ row.spread }}</td>














                  <td>{{ row.quotes }}</td>







                  <td><button type="button" class="pcw-link" @click="openSummaryProductTrend(row.identityKey)">查看报价</button></td>







                </tr>







              </tbody>







            </table>







            <div class="pcw-pages">







              <button type="button" :disabled="tablePage.summary <= 1" @click="changeTablePage('summary', -1)">‹</button>







              <button







                v-for="page in summaryPaginationPages"







                :key="`summary-${page}`"







                type="button"







                :class="{ active: tablePage.summary === page }"







                @click="setTablePage('summary', page)"







              >







                {{ page }}







              </button>







              <button type="button" :disabled="tablePage.summary >= summaryPageCount && !props.summaryHasMoreRows" @click="changeTablePage('summary', 1)">›</button>







              <label class="pcw-page-size">
                <span>每页</span>
                <select :value="pageSize" @change="handlePageSizeChange">
                  <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }} 条</option>
                </select>
              </label>







              <em>第 {{ tablePage.summary }} / {{ summaryPageCount }} 页</em>







            </div>





          </section>















          <section class="pcw-card pcw-summary-brief">
              <div class="pcw-card-head">
                <h2>今日待处理</h2>
                <button type="button" @click="handleNavSelect('purchase')">去执行 ›</button>
              </div>
              <div class="pcw-summary-brief-grid">
                <div class="pcw-summary-action-grid">
                  <button
                    v-for="item in summaryActionCards"
                    :key="`${item.label}-${item.title}`"
                    type="button"
                    class="pcw-summary-action-card"
                    @click="openWorkbenchActionSection(item.section, item.identityKey)"
                  >
                    <span>{{ item.label }}</span>
                    <strong>{{ item.title }}</strong>
                    <small>{{ item.detail }}</small>
                  </button>
                </div>
                <div class="pcw-summary-brief-timeline">
                  <div class="pcw-summary-brief-subhead">
                    <strong>价格变化</strong>
                    <button type="button" @click="openActionPanel('价格变化', timelineRows.map((item) => `${item.time} ${item.text}`), 'market')">查看明细 ›</button>
                  </div>
                  <div v-if="!timelineRows.length" class="pcw-panel-empty compact">
                    <strong>暂无价格变化</strong>
                    <span>有新价格后会显示在这里。</span>
                  </div>
                  <p v-for="item in timelineRows.slice(0, 4)" :key="item.time"><span>{{ item.time }}</span>{{ item.text }}</p>
                </div>
              </div>
          </section>

          </div>

          <aside v-if="currentSection === 'summary'" class="pcw-right">







            <section class="pcw-card pcw-summary-side-fill">
              <div class="pcw-card-head">
                <h2>采购概况</h2>
                <button type="button" @click="handleNavSelect('purchase')">去执行 ›</button>
              </div>
              <div class="pcw-summary-side-hero">
                <div>
                  <span>当前地区</span>
                  <strong>{{ displayLocationLabel }}</strong>
                </div>
                <p>先看覆盖、价差和待处理项。</p>
              </div>
              <div class="pcw-summary-side-metrics">
                <article>
                  <span>行情商品</span>
                  <strong>{{ displayRowTotal }}</strong>
                </article>
                <article>
                  <span>今日报价</span>
                  <strong>{{ visibleQuoteCount }}</strong>
                </article>
                <article>
                  <span>可比价格</span>
                  <strong>{{ summaryOpportunityRows.length }}</strong>
                </article>
                <article>
                  <span>处理建议</span>
                  <strong>{{ summaryAdviceRows.length }}</strong>
                </article>
              </div>
              <div class="pcw-summary-side-block">
                <div class="pcw-summary-side-block-head">
                  <span>处理建议</span>
                  <button type="button" @click="handleNavSelect('purchase')">去采购 ›</button>
                </div>
                <p v-for="(item, index) in summaryAdviceRows.slice(0, 2)" :key="`advice-${index}-${item}`">
                  {{ item }}
                </p>
              </div>
              <div class="pcw-summary-side-block">
                <div class="pcw-summary-side-block-head">
                  <span>价差机会</span>
                  <button type="button" @click="handleNavSelect('trend')">看趋势 ›</button>
                </div>
                <button
                  v-for="item in summaryOpportunityRows.slice(0, 3)"
                  :key="`side-opportunity-${item.identityKey}-${item.name}`"
                  type="button"
                  class="pcw-summary-side-opportunity"
                  @click="openWorkbenchActionSection('trend', item.identityKey)"
                >
                  <div>
                    <strong>{{ item.name }}</strong>
                    <small>{{ item.market }} · {{ item.quotes }} 条报价</small>
                  </div>
                  <div class="pcw-summary-opportunity-metrics">
                    <b>{{ item.low }}</b>
                    <span>价差 {{ item.spread }}</span>
                  </div>
                </button>
              </div>
            </section>

          </aside>







        </section>















        <section v-else-if="currentSection === 'trend'" key="pcw-section-trend" class="pcw-trend-page">







          <section class="pcw-card pcw-trend-chart-card">







            <div class="pcw-card-head">







              <h2>{{ selectedProductName || '当前商品' }}价格趋势</h2>







              <div class="pcw-segments">







                <button type="button" :class="{ active: chartRange === 7 }" @click="setChartRange(7)">7 日</button>







                <button type="button" :class="{ active: chartRange === 30 }" @click="setChartRange(30)">30 日</button>







                <button type="button" :class="{ active: chartRange === 90 }" @click="setChartRange(90)">90 日</button>







              </div>







            </div>







            <div class="pcw-legend trend">







              <span class="blue">均价（元/公斤）</span>







              <span class="green">最低价（元/公斤）</span>







            </div>







            <svg class="pcw-big-chart" viewBox="0 0 720 260" role="img" :aria-label="`${selectedProductName || '商品'}价格趋势`" @mouseleave="clearHoveredTrendPoint">







              <g class="grid">







                <path d="M50 20H690M50 70H690M50 120H690M50 170H690M50 220H690" />







                <path d="M50 20V220M156 20V220M262 20V220M368 20V220M474 20V220M580 20V220M690 20V220" />







              </g>







              <polyline class="line-blue" :points="bigTrendLinePoints" />







              <polyline class="line-green" :points="bigTrendLowLinePoints" />







              <path v-if="activeTrendDot" class="pcw-crosshair" :d="`M${activeTrendDot.x} 20V220`" />







              <g class="dots">







                <g v-for="(point, index) in bigTrendDots" :key="`${index}-${point.x}-${point.y}`" class="pcw-dot" tabindex="0" @mouseenter="setHoveredTrendPoint(index)" @focus="setHoveredTrendPoint(index)" @blur="clearHoveredTrendPoint">
                  <circle class="pcw-dot-hit" :cx="point.x" :cy="point.y" r="12" />
                  <circle :class="{ 'pcw-dot-active': activeTrendPointIndex === index }" :cx="point.x" :cy="point.y" :r="activeTrendPointIndex === index ? 5.8 : 4" />
                </g>







              </g>







              <g v-if="activeTrendTooltip" class="pcw-tooltip" :transform="`translate(${activeTrendTooltip.x} ${activeTrendTooltip.y})`">







                <rect x="0" y="0" width="188" height="76" rx="8" />







                <text x="14" y="25">{{ activeTrendTooltip.date }}</text>







                <text x="14" y="51">报价 {{ activeTrendTooltip.price }}</text>







                <text x="82" y="51">{{ activeTrendTooltip.market }}</text>







              </g>







              <g class="pcw-axis">







                <text v-for="label in bigTrendAxisLabels" :key="label.x" :x="label.x" y="246">{{ label.text }}</text>







              </g>







            </svg>







            <div v-if="activeTrendRow" class="pcw-trend-hover-inspector">
              <article>
                <span>当前时间点</span>
                <strong>{{ activeTrendTooltip?.date || '最新' }}</strong>
                <small>{{ activeTrendRow.captured_at ? formatShortDateTime(activeTrendRow.captured_at) : '最近趋势点' }}</small>
              </article>
              <article>
                <span>报价</span>
                <strong>{{ activeTrendTooltip?.price || '-' }}</strong>
                <small>{{ isUsingTrendSnapshot ? '菜价快照' : '价格记录' }}</small>
              </article>
              <article>
                <span>来源</span>
                <strong>{{ activeTrendTooltip?.market || '价格来源' }}</strong>
                <small>{{ activeTrendRow.source_name || activeTrendRow.site_name || activeTrendRow.trend_series_name || '价格来源' }}</small>
              </article>
            </div>
            <div v-if="trendPointRailRows.length" class="pcw-trend-point-rail">
              <button
                v-for="item in trendPointRailRows"
                :key="`${item.index}-${item.label}-${item.price}`"
                type="button"
                :class="{ active: activeTrendPointIndex === item.index }"
                @mouseenter="setHoveredTrendPoint(item.index)"
                @focus="setHoveredTrendPoint(item.index)"
                @click="setHoveredTrendPoint(item.index)"
              >
                <span>{{ item.label }}</span>
                <strong>{{ item.price }}</strong>
                <small>{{ item.source }}</small>
              </button>
            </div>

            <div v-if="!trendChartRows.length" class="pcw-chart-empty" data-testid="pcw-trend-empty-state">







              <strong>{{ trendEmptyTitle }}</strong>







              <span>{{ trendEmptyDetail }}</span>







            </div>







            <div v-if="!trendChartRows.length" class="pcw-trend-readiness" aria-label="趋势数据链路状态">







              <article v-for="item in trendReadinessCards" :key="item.label" :class="item.tone">







                <span>{{ item.label }}</span>







                <strong>{{ item.value }}</strong>







                <small>{{ item.detail }}</small>







              </article>







            </div>







          </section>















          <aside class="pcw-trend-side">







            <section v-if="trendQuoteRows.length" class="pcw-card pcw-trend-quotes">







              <div class="pcw-card-head">







                <h2>今日报价</h2>







                <button type="button" @click="openActionPanel('今日报价明细', quoteRows.map((item) => `${item.supplier} ${item.price}`), 'quotes')">查看明细 ›</button>







              </div>







              <table>







                <thead><tr><th>供应商</th><th>来源</th><th>报价</th><th>时间</th></tr></thead>







                <tbody>







                  <tr v-if="!trendQuoteRows.length" class="pcw-empty-row compact">







                    <td colspan="4">







                      <div class="pcw-empty-state">







                        <strong>暂无报价明细</strong>







                        <span>同步到趋势后会显示供应商、来源和报价时间。</span>







                      </div>







                    </td>







                  </tr>







                  <tr v-for="item in trendQuoteRows" :key="item[0]">







                    <td>{{ item[0] }}</td><td>{{ item[1] }}</td><td>{{ item[2] }}</td><td>{{ item[3] }}</td>







                  </tr>







                </tbody>







              </table>







            </section>







            <section class="pcw-card pcw-suggestion">







              <div class="pcw-card-head"><h2>采购建议</h2></div>







              <ul>







                <li v-for="item in trendSuggestions" :key="item">{{ item }}</li>







              </ul>







            </section>







            <section class="pcw-card pcw-trend-alert">







              <div class="pcw-card-head">







                <h2>价格预警</h2>







                <button type="button" @click="openAlertSettingsPanel">设置预警 ›</button>







              </div>







              <table>







                <thead><tr><th>提醒规则</th><th>当前值</th><th>状态</th></tr></thead>







                <tbody>







                  <tr v-for="row in trendAlertRows" :key="row[0]">







                    <td>{{ row[0] }}</td><td :class="row[2]">{{ row[1] }}</td><td><span>{{ row[3] }}</span></td>







                  </tr>







                </tbody>







              </table>







            </section>







          </aside>















            <section v-if="trendMarketRows.length" class="pcw-card pcw-market-compare">







            <div class="pcw-card-head"><h2>来源报价对比</h2></div>







            <table>







              <thead><tr><th>来源</th><th>当前报价</th><th>来源层级</th><th>同步时间</th><th>记录来源</th><th>操作</th></tr></thead>







              <tbody>







                <tr v-if="!trendMarketRows.length" class="pcw-empty-row compact">







                  <td colspan="6">







                    <div class="pcw-empty-state">







                      <strong>等待来源对比数据</strong>







                      <span>价格记录会按来源汇总在这里。</span>







                    </div>







                  </td>







                </tr>







                <tr v-for="row in trendMarketRows" :key="row[0]">







                  <td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td><td>{{ row[3] }}</td><td>{{ row[4] }}</td><td><button type="button" class="pcw-link" @click="handleTableAction('查看明细', row)">查看明细</button></td>







                </tr>







              </tbody>







            </table>







          </section>







          <section v-if="trendDynamics.length" class="pcw-card pcw-trend-dynamics">







            <div class="pcw-card-head"><h2>来源动态</h2><button type="button" @click="openActionPanel('来源动态', trendDynamicRows.map((item) => `${item.time} ${item.market} ${item.text}`), 'market')">查看明细 ›</button></div>







            <div v-if="!trendDynamics.length" class="pcw-panel-empty compact">







              <strong>暂无来源动态</strong>







              <span>报价变化同步后会生成动态记录。</span>







            </div>







            <p v-for="item in trendDynamics" :key="item.time"><b>{{ item.time }}</b><span>{{ item.market }}</span>{{ item.text }}</p>







          </section>







          <section v-if="peerRows.length" class="pcw-card pcw-peer-products">







            <div class="pcw-card-head"><h2>同类商品对比（今日均价）</h2></div>







            <table>







              <thead><tr><th>商品</th><th>今日均价</th><th>最低价来源</th><th>区域</th></tr></thead>







              <tbody>







                <tr v-if="!peerRows.length" class="pcw-empty-row compact">







                  <td colspan="4">







                    <div class="pcw-empty-state">







                      <strong>等待同类商品数据</strong>







                      <span>菜价更新后会展示同类商品均价对比。</span>







                    </div>







                  </td>







                </tr>







                <tr v-for="row in peerRows" :key="row[0]">







                  <td><span :class="['pcw-thumb', row[4]]"></span>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td><td>{{ row[3] }}</td>







                </tr>







              </tbody>







            </table>







          </section>







        </section>















        <section v-else-if="currentSection === 'alerts'" key="pcw-section-alerts" class="pcw-alert-page">







          <section class="pcw-alert-command">







            <div class="pcw-alert-command-copy">







              <span>价格提醒</span>







              <h2>先处理今天真正会影响采购决定的价格变化</h2>







              <p>这里直接告诉你发生了什么、会影响什么、建议下一步做什么；详细规则放到二级设置，不再让你先理解内部价格线。</p>







            </div>







            <div class="pcw-alert-command-actions">







              <button type="button" class="primary" @click="emit('refresh')">刷新</button>







              <button type="button" @click="openActionPanel('高优先级预警', priorityAlerts.map((item) => [item.title, item.type, item.detail].filter(Boolean).join(' ')), 'alerts')">查看明细 ›</button>
                        <button type="button" @click="openAlertSettingsPanel">设置提醒</button>







            </div>







            <div class="pcw-alert-command-metrics" aria-label="预警队列摘要">







              <article v-for="item in alertSimpleCards" :key="item.label" :class="item.tone">







                <span>{{ item.label }}</span>







                <strong>{{ item.value }}</strong>







                <small>{{ item.detail }}</small>







              </article>







            </div>







          </section>















          <section class="pcw-card pcw-alert-table-card">







            <div class="pcw-card-head">







              <div>







                <h2>今日价格提醒</h2>







                <span>{{ alertSimpleSummary }}</span>







              </div>







              <button type="button" @click="handleExportData">导出 ›</button>







            </div>







            <div class="pcw-alert-table-toolbar">







              <span v-for="item in alertQueuePills" :key="item.label" :class="item.tone">







                <b>{{ item.value }}</b>{{ item.label }}







              </span>







            </div>







            <table>







              <colgroup>







                <col class="pcw-alert-col-product" />
                <col class="pcw-alert-col-value" />
                <col class="pcw-alert-col-type" />
                <col class="pcw-alert-col-owner" />
                <col class="pcw-alert-col-state" />
                <col class="pcw-alert-col-actions" />
              </colgroup>







              <thead>







                <tr><th>菜品</th><th>当前价格</th><th>为什么提醒</th><th>建议怎么做</th><th>状态</th><th>下一步</th></tr>







              </thead>







              <tbody>







                <tr v-if="!alertTaskRows.length" class="pcw-empty-row compact">







                    <td colspan="6">







                    <div class="pcw-empty-state">







                      <strong>暂无价格预警</strong>







                      <span>今天还没有需要处理的价格提醒。你可以刷新一次菜价，或给常采商品加一条提醒。</span>







                    </div>







                  </td>







                </tr>







                <tr v-for="row in alertTaskRows" :key="row.name">
                  <td>
                    <span :class="['pcw-thumb', row.thumb]"></span>
                    <span class="pcw-alert-product-copy">
                      <strong>{{ row.name }}</strong>
                      <small>{{ row.market }}</small>
                    </span>
                  </td>
                  <td><strong class="pcw-alert-price">{{ row.value }}</strong></td>
                  <td>
                    <span :class="['pcw-alert-type', row.tone]">{{ row.type }}</span>
                    <small>{{ row.rule }}</small>
                  </td>
                  <td><span class="pcw-alert-owner">{{ row.owner }}</span></td>
                  <td><span :class="['pcw-alert-state', row.stateTone]">{{ row.state }}</span></td>
                  <td class="pcw-alert-actions">
                    <button type="button" class="pcw-link" @click="handleAlertTrendAction(row)">看趋势</button>
                    <button type="button" class="pcw-link" :title="`将带着价格预警上下文进入供应后台：${row.name}`" @click="handleAlertSupplierQuoteAction(row)">去供应商报价</button>
                    <button type="button" class="pcw-link" :disabled="row.stateTone === 'done'" @click="handleAlertResolveAction(row, 'resolved')">标记已处理</button>
                    <button type="button" class="pcw-link" :disabled="row.stateTone === 'done'" @click="handleAlertResolveAction(row, 'ignored')">忽略本次</button>
                  </td>
                </tr>







              </tbody>







            </table>







            <div class="pcw-pages">







              <button type="button" :disabled="tablePage.alerts <= 1" @click="changeTablePage('alerts', -1)">‹</button>







              <button







                v-for="page in alertPaginationPages"







                :key="`alerts-${page}`"







                type="button"







                :class="{ active: tablePage.alerts === page }"







                @click="setTablePage('alerts', page)"







              >







                {{ page }}







              </button>







              <button type="button" :disabled="tablePage.alerts >= alertPageCount" @click="changeTablePage('alerts', 1)">›</button>







              <em>共 {{ alertTaskTotal }} 条</em>







              <em>{{ pageSize }} 条/页</em>







              <em>第 {{ tablePage.alerts }} / {{ alertPageCount }} 页</em>







            </div>







          </section>















          <aside class="pcw-alert-side">







            <section class="pcw-card pcw-priority-alerts">







              <div class="pcw-card-head">







                <h2>高优先级预警</h2>







                <button type="button" @click="openActionPanel('高优先级预警', priorityAlerts.map((item) => `${item.title} ${item.type} ${item.detail}`), 'alerts')">查看明细 ›</button>







              </div>







              <article v-for="item in priorityAlerts" :key="item.title" :class="item.tone">







                <div>







                  <strong>{{ item.title }}</strong>







                  <span>{{ item.type }}</span>







                </div>







                <p>{{ item.detail }}</p>







                <time>{{ item.time }}</time>







              </article>







              <div v-if="!priorityAlerts.length" class="pcw-panel-empty compact">







                <strong>暂无高优先级预警</strong>







                <span>高风险、临期和异常波动会优先进入这里。</span>







              </div>







            </section>















            <section class="pcw-card pcw-alert-ops">







              <div class="pcw-card-head">







                <h2>处置节奏</h2>







                <span>{{ alertRuleCoverage }}</span>







              </div>







              <article v-for="item in alertWorkflowCards" :key="item.label" :class="item.tone">







                <span>{{ item.label }}</span>







                <strong>{{ item.value }}</strong>







                <small>{{ item.detail }}</small>







              </article>







            </section>







          </aside>
          <section class="pcw-card pcw-alert-advice">







            <div class="pcw-card-head"><h2>处理建议</h2></div>







            <ul>







              <li v-for="item in alertAdviceRows" :key="item">{{ item }}</li>







            </ul>







          </section>















          <section class="pcw-card pcw-rule-card">







            <div class="pcw-card-head">







              <h2>规则配置</h2>







              <button type="button" @click="openAlertSettingsPanel">设置规则 ›</button>







            </div>







            <div v-if="!alertRules.length" class="pcw-panel-empty compact">







              <strong>暂无规则输出</strong>







              <span>系统给出处理建议后会显示规则来源。</span>







            </div>







            <p v-for="item in alertRules" :key="item.type" :class="item.tone">







              <b>{{ item.icon }}</b>







              <strong>{{ item.type }}</strong>







              <span>{{ item.rule }}</span>







            </p>







          </section>















          <section class="pcw-card pcw-alert-records">







            <div class="pcw-card-head">







              <h2>最近处理记录</h2>







              <button type="button" @click="openActionPanel('最近处理记录', alertRecords.map((item) => `${item.time} ${item.text}`), 'alerts')">查看明细 ›</button>







            </div>







            <div v-if="!alertRecords.length" class="pcw-panel-empty compact">







              <strong>暂无处理记录</strong>







              <span>预警处理完成后会显示处理动作和结果。</span>







            </div>







            <p v-for="item in alertRecords" :key="item.time" :class="item.tone">







              <b></b>







              <span>{{ item.time }}</span>







              <strong>{{ item.text }}</strong>







              <em>{{ item.status }}</em>







            </p>







          </section>







        </section>















        <section v-else-if="currentSection === 'plan'" key="pcw-section-plan" class="pcw-plan-workspace" data-testid="pcw-menu-workspace">







          <MenuPlanPanel







            :menu-text="props.menuText || ''"







            :tables="props.menuTables || 1"







            :diners="props.menuDiners || 1"







            :preferred-location="props.menuPreferredLocation || ''"







            :location-candidates="props.menuLocationCandidates || []"







            :ingredient-rows="props.ingredientRows || []"







            :plan-rows="props.planRows || []"







            :parsed-menu-count="props.parsedMenuCount || 0"







            :matched-plan-count="props.matchedPlanCount || 0"







            :pending-plan-count="props.pendingPlanCount || 0"







            :total-cost-label="props.menuTotalCostLabel || '¥0.00'"







            :loading="Boolean(props.menuLoading)"







            @update:menu-text="emit('update:menu-text', $event)"







            @update:tables="emit('update:menu-tables', $event)"







            @update:diners="emit('update:menu-diners', $event)"







            @update:preferred-location="emit('update:menu-preferred-location', $event)"







            @submit="emit('submit-menu')"
            @view-market="emit('menu-view-market', $event)"
            @fill-supplier-price="emit('menu-fill-supplier-price', $event)"
            @confirm-row="emit('menu-confirm-row', $event)"
            @fill-missing-quotes="emit('menu-fill-missing-quotes')"














          />







        </section>















        <section v-else-if="currentSection === 'suppliers'" key="pcw-section-suppliers" class="pcw-supplier-admin-embedded">
          <ProcurementSupplierAdminPanel
            :auth-role="props.authRole || null"
          />
        </section>

        <section v-else :key="`pcw-section-module-${currentSection}`" :class="['pcw-module', `pcw-module-${currentSection}`, moduleDensityClass, moduleLayoutClass, { 'is-quotes-empty': isQuotesModuleEmpty }]">







          <section v-if="isGeneratedModuleLayout && !isPurchaseModuleEmpty" class="pcw-module-command">







            <div class="pcw-module-command-copy">







              <span>{{ moduleView.kicker }}</span>







              <h2>{{ moduleView.title }}</h2>







              <p>{{ moduleView.description }}</p>







            </div>







            <div class="pcw-module-command-actions">







              <button type="button" class="secondary" @click="handleModuleFilterFocus">筛选</button>







              <button type="button" class="primary" @click="handleModulePrimaryAction">{{ moduleView.action }}</button>







            </div>







            <div class="pcw-module-command-metrics">







              <article v-for="item in moduleCommandMetrics" :key="item.label" :class="item.tone">







                <span>{{ item.label }}</span>







                <strong>{{ item.value }}</strong>







                <small>{{ item.detail }}</small>







              </article>







            </div>







            <div v-if="isPurchaseModuleEmpty" class="pcw-module-command-empty-note">
              <strong>当前还没有可直接执行的采购动作</strong>
              <span>先去报价记录补齐供应商报价，或进入采购计划整理待确认项，再回到这里执行。</span>
            </div>

            <div v-else class="pcw-module-command-brief">







              <p v-for="item in moduleBriefItems" :key="item.label">







                <b>{{ item.label }}</b>







                <span>{{ item.text }}</span>







              </p>







            </div>







          </section>







          <section v-if="!isGeneratedModuleLayout" class="pcw-card pcw-module-hero">







            <div>







              <span>{{ moduleView.kicker }}</span>







              <h2>{{ moduleView.title }}</h2>







              <p>{{ moduleView.description }}</p>







            </div>







            <div class="pcw-module-actions">







              <button type="button" class="secondary" @click="handleModuleFilterFocus">筛选</button>







              <button type="button" class="primary" @click="handleModulePrimaryAction">{{ moduleView.action }}</button>







            </div>







          </section>















          <SettingsControlPanel
            v-if="currentSection === 'settings'"
            :crawl-status="props.crawlStatus || null"
            :source-coverage-rows="props.sourceCoverageRows || []"
            :settings-change-logs="props.settingsChangeLogs || []"
            :global-alert-rules="props.globalAlertRules || []"
            :auth-role="props.authRole || null"
            @refresh="emit('refresh')"
            @run-crawl="emit('run-crawl')"
            @run-source-crawl="emit('run-source-crawl', $event)"
            @update-crawl-schedule="emit('update-crawl-schedule', $event)"
            @update-source-config="emit('update-source-config', $event)"
            @update-source-strategy="emit('update-source-strategy', $event)"
            @update-global-alert-rules="emit('update-global-alert-rules', $event)"
          />

          <section v-if="currentSection === 'settings'" class="pcw-card pcw-settings-quick-panel">
            <div class="pcw-card-head">
              <h2>本页只保留来源配置和同步控制</h2>
              <button type="button" @click="handleSettingsRunCrawl">立即同步 ›</button>
            </div>
            <div class="pcw-settings-quick-grid">
              <article v-for="item in settingsQuickCards" :key="item.label" :class="item.tone">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
                <small>{{ item.detail }}</small>
              </article>
            </div>
          </section>

          <section v-else-if="currentSection === 'market'" class="pcw-market-health-board">
            <section class="pcw-card pcw-market-health-list">
              <div class="pcw-card-head">
                <h2>来源健康巡检</h2>
                <button type="button" @click="handleModulePrimaryAction">刷新行情 ›</button>
              </div>
              <div class="pcw-market-health-rows">
                <article v-for="item in marketHealthRows" :key="item.name" :class="item.tone">
                  <div>
                    <strong>{{ item.name }}</strong>
                    <small>{{ item.detail }}</small>
                  </div>
                  <span>{{ item.latest }}</span>
                  <b>{{ item.records }}</b>
                </article>
              </div>
            </section>
            <aside class="pcw-market-health-side">
              <section class="pcw-card pcw-market-health-pulse">
                <div class="pcw-card-head">
                  <h2>同步概况</h2>
                </div>
                <article v-for="item in marketCoverageCards" :key="item.label" :class="item.tone">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                  <small>{{ item.detail }}</small>
                </article>
              </section>
              <section class="pcw-card pcw-market-failure-list">
                <div class="pcw-card-head">
                  <h2>优先排查</h2>
                </div>
                <p v-for="item in marketFailureRows" :key="item.name">
                  <b>{{ item.name }}</b>
                  <span>{{ item.reason }}</span>
                </p>
              </section>
            </aside>
          </section>

          <section v-else-if="currentSection === 'reports'" class="pcw-report-workbench">
            <section class="pcw-card pcw-report-composition">
              <div class="pcw-card-head">
                <h2>品类结构</h2>
                <button type="button" @click="handleModulePrimaryAction">导出报表 ›</button>
              </div>
              <div class="pcw-report-bars">
                <article v-for="item in reportCategoryRows" :key="item.category">
                  <div>
                    <strong>{{ item.category }}</strong>
                    <small>{{ item.count }} 个商品 · {{ item.avg }}</small>
                  </div>
                  <span><i :style="{ width: `${item.percent}%` }"></i></span>
                  <b>{{ item.percent }}%</b>
                </article>
              </div>
            </section>
            <aside class="pcw-report-side">
              <section class="pcw-card pcw-report-export-card">
                <div class="pcw-card-head">
                  <h2>报表包</h2>
                </div>
                <article v-for="item in reportExportCards" :key="item.label">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                  <small>{{ item.detail }}</small>
                </article>
              </section>
              <section class="pcw-card pcw-report-risk-card">
                <div class="pcw-card-head">
                  <h2>风险摘要</h2>
                </div>
                <p v-for="item in reportRiskRows" :key="item.title" :class="item.tone">
                  <b>{{ item.title }}</b>
                  <span>{{ item.detail }}</span>
                </p>
              </section>
            </aside>
          </section>

          <section v-else-if="isPurchaseModuleEmpty" class="pcw-card pcw-module-empty-compact">
            <div class="pcw-card-head">
              <h2>采购还不能执行，先补齐一条链</h2>
            </div>
            <div class="pcw-purchase-empty-path">
              <article v-for="item in purchaseEmptyActions" :key="item.label">
                <span>{{ item.step }}</span>
                <strong>{{ item.label }}</strong>
                <small>{{ item.detail }}</small>
                <button type="button" @click="openWorkbenchActionSection(item.section, item.identityKey || '')">{{ item.action }}</button>
              </article>
            </div>
            <div class="pcw-purchase-empty-feed">
              <section>
                <strong>当前卡点</strong>
                <p v-for="item in purchaseEmptyBlockers" :key="item">{{ item }}</p>
              </section>
              <section>
                <strong>最近可参考趋势</strong>
                <button
                  v-for="item in purchaseTrendCarryRows"
                  :key="`${item.source}-${item.time}-${item.price}`"
                  type="button"
                  @click="openWorkbenchActionSection('trend', item.identityKey)"
                >
                  <span>{{ item.source }} · {{ item.time }}</span>
                  <b>{{ item.price }}</b>
                </button>
                <p v-if="!purchaseTrendCarryRows.length">先从汇总行情选择商品，再查看历史行情确认价格来源。</p>
              </section>
            </div>
          </section>

          <section v-else-if="isQuotesModuleEmpty" class="pcw-card pcw-quotes-empty-compact">
            <div class="pcw-card-head">
              <h2>报价待补</h2>
              <button type="button" @click="handleModulePrimaryAction">去报价后台 ›</button>
            </div>
            <div class="pcw-quotes-empty-grid">
              <article v-for="item in quoteEmptyActionCards" :key="item.label">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
                <small>{{ item.detail }}</small>
                <button type="button" @click="openWorkbenchActionSection(item.section, item.identityKey || '')">{{ item.action }}</button>
              </article>
            </div>
            <div class="pcw-quotes-empty-feed">
              <section>
                <strong>当前链路</strong>
                <p v-for="item in quoteEmptyWorkflowRows" :key="item">{{ item }}</p>
              </section>
              <section>
                <strong>下一步</strong>
                <p>供应商报价同步后，这里才展开表格、质量侧栏和报价流明细；无数据时不再占一整屏。</p>
              </section>
            </div>
          </section>

          <section v-else class="pcw-module-grid">







            <section class="pcw-card pcw-module-table">







              <div class="pcw-card-head">







                <h2>{{ moduleView.tableTitle }}</h2>







                <div class="pcw-module-card-actions">







                  <span :class="['pcw-module-count-badge', { warning: currentSection === 'settings' && moduleTableCount === 0 && allModuleTableRows.length > 0 }]">{{ currentSection === 'settings' ? `${moduleTableCount} / ${allModuleTableRows.length} 条` : `${moduleTableCount} 条` }}</span>
                  <button v-if="currentSection === 'settings' && allModuleTableRows.length > 0" type="button" class="secondary" @click="resetSectionFilters('settings')">清空筛选</button>







                  <button v-if="isGeneratedModuleLayout" type="button" @click="handleModulePrimaryAction">{{ moduleView.action }}</button>







                </div>







              </div>







              <p class="pcw-module-table-note">下方展示当前明细，表格与右侧面板会一起更新。</p>







              <table>







                <thead>







                  <tr>







                    <th v-for="column in moduleView.columns" :key="column">{{ column }}</th>







                  </tr>







                </thead>







                <tbody>







                  <tr v-if="!moduleHasTableRows" class="pcw-empty-row compact">







                    <td :colspan="moduleView.columns.length">







                      <div class="pcw-empty-state">







                        <strong>{{ moduleEmptyTitle }}</strong>







                        <span>{{ moduleEmptyDetail }}</span>
                        <button v-if="currentSection === 'settings' && allModuleTableRows.length > 0" type="button" class="pcw-empty-action-button" @click="resetSectionFilters('settings')">恢复全部来源</button>







                      </div>







                    </td>







                  </tr>







                  <tr v-for="row in moduleTableRows" :key="`${moduleView.kicker}-${row[0]}-${row[1] || ''}`">







                    <td v-for="(cell, index) in row" :key="`${row[0]}-${index}`">







                      <span v-if="index === 0" class="pcw-module-name">{{ cell }}</span>







                      <span v-else-if="moduleView.columns[index] === '状态'" :class="['pcw-module-status', moduleStatusTone(cell)]">{{ cell }}</span>







                      <span v-else-if="moduleView.columns[index]?.includes('进度')" class="pcw-module-progress">







                        <i :style="{ width: cell }"></i>







                        <em>{{ cell }}</em>







                      </span>







                      <span v-else-if="moduleView.columns[index] === '操作'" class="pcw-row-actions">







                        <button







                          v-for="action in splitActions(cell)"







                          :key="`${row[0]}-${action}`"







                          type="button"







                          @click="handleTableAction(action, row)"







                        >







                          {{ action }}







                        </button>







                      </span>







                      <span v-else>{{ cell }}</span>







                    </td>







                  </tr>







                </tbody>







              </table>







              <div v-if="moduleTablePageCount > 1" class="pcw-pages">







                <button type="button" :disabled="tablePage[currentSection] <= 1" @click="changeTablePage(currentSection, -1)">‹</button>







                <button







                  v-for="page in modulePaginationPages"







                  :key="`${currentSection}-${page}`"







                  type="button"







                  :class="{ active: tablePage[currentSection] === page }"







                  @click="setTablePage(currentSection, page)"







                >







                  {{ page }}







                </button>







                <button type="button" :disabled="tablePage[currentSection] >= moduleTablePageCount" @click="changeTablePage(currentSection, 1)">›</button>







                <em>共 {{ moduleTableCount }} 条</em>







              </div>







            </section>















            <aside class="pcw-module-side">







              <section class="pcw-card pcw-module-panel">







                <div class="pcw-card-head">







                  <h2>{{ moduleView.sideTitle }}</h2>







                  <button type="button" :disabled="!moduleHasSideItems" @click="openActionPanel(moduleView.sideTitle, moduleSideItems.map((item) => `${item.title} ${item.detail}`), currentSection)">查看明细 ›</button>







                </div>







                <div v-if="!moduleHasSideItems" class="pcw-panel-empty compact">







                  <strong>暂无{{ moduleView.sideTitle }}</strong>







                  <span>有新数据后会按优先级显示在这里。</span>







                </div>







                <article v-for="item in moduleSideItems" :key="item.title">







                  <span :class="item.tone">{{ item.label }}</span>







                  <strong>{{ item.title }}</strong>







                  <small>{{ item.detail }}</small>







                </article>







              </section>







              <section class="pcw-card pcw-module-flow">







                <div class="pcw-card-head">







                  <h2>{{ moduleView.flowTitle }}</h2>







                </div>







                <div v-if="!moduleHasFlowItems" class="pcw-panel-empty compact">







                  <strong>暂无{{ moduleView.flowTitle }}</strong>







                  <span>有新的同步、审核或处理记录后会自动生成流程。</span>







                </div>







                <p v-for="item in moduleFlowItems" :key="item.step">







                  <b>{{ item.step }}</b>







                  <span>{{ item.text }}</span>







                </p>







              </section>







            </aside>















            <section class="pcw-card pcw-module-chart-panel">







              <div class="pcw-card-head">







                <h2>{{ moduleView.kicker }}趋势</h2>







                <button type="button" :disabled="!moduleHasChartData" @click="setChartRange(chartRange === 7 ? 30 : 7)">近 {{ chartRange }} 日⌄</button>







              </div>







              <div class="pcw-legend">







                <span class="blue">{{ currentSection === 'market' ? '当前均价' : '处理量' }}</span>







                <span class="green">{{ currentSection === 'market' ? '当前低价' : '有效量' }}</span>







                <span class="warn">{{ currentSection === 'market' ? '当前高价' : '异常量' }}</span>







              </div>







              <svg viewBox="0 0 720 220" role="img" :aria-label="`${moduleView.kicker}趋势`">







                <g class="grid">







                  <path d="M44 24H690M44 68H690M44 112H690M44 156H690M44 200H690" />







                </g>







                <g class="pcw-module-bars">







                  <rect







                    v-for="bar in moduleChartBars"







                    :key="`${bar.x}-${bar.y}`"







                    :x="bar.x"







                    :y="bar.y"







                    :width="bar.width"







                    :height="bar.height"







                  />







                </g>







                <polyline v-if="moduleHasChartData" class="line-blue" :points="moduleChartLinePoints" />







                <polyline v-if="moduleHasChartData" class="line-green" :points="moduleChartLowLinePoints" />







                <g class="pcw-axis">







                  <text v-for="label in chartAxisLabels" :key="`module-${label.x}`" :x="label.x" y="216">{{ label.text }}</text>







                </g>







              </svg>







              <div v-if="!moduleHasChartData" class="pcw-chart-empty module">







                <strong>等待趋势数据</strong>







                <span>有数据后会绘制处理量与有效量趋势。</span>







              </div>







            </section>















            <section class="pcw-card pcw-module-activity">







              <div class="pcw-card-head">







                <h2>{{ moduleView.flowTitle }}明细</h2>







                <button type="button" :disabled="!moduleHasFlowItems" @click="openActionPanel(`${moduleView.flowTitle}明细`, moduleFlowItems.map((item) => `${item.step} ${item.text}`), currentSection)">查看明细 ›</button>







              </div>







              <div v-if="!moduleHasFlowItems" class="pcw-panel-empty compact">







                <strong>暂无处理明细</strong>







                <span>有处理记录后会显示时间、内容和状态。</span>







              </div>







              <article v-for="item in moduleFlowItems" :key="`${moduleView.kicker}-${item.step}`">







                <b>{{ item.step }}</b>







                <span>{{ item.text }}</span>







                <em>已同步</em>







              </article>







            </section>







          </section>







        </section>















        <section v-if="currentSection === 'summary' && alerts.length" class="pcw-bottom">







          <section class="pcw-card pcw-alerts">







            <div class="pcw-card-head">







              <h2>预警信息</h2>







              <button type="button" @click="handleNavSelect('alerts')">全部 {{ alerts.length }} ›</button>







            </div>







            <div v-if="!alerts.length" class="pcw-panel-empty compact">







              <strong>暂无预警</strong>







              <span>价格异常信号会在这里集中展示。</span>







            </div>







            <p v-for="item in alerts" :key="item.name" :class="item.tone">







              <strong>{{ item.name }}</strong>







              <span>{{ item.value }}</span>







              <small>{{ item.detail }}</small>







            </p>







          </section>







        </section>







      </main>







    </section>







    <el-dialog v-model="imagePreviewVisible" :title="imagePreviewTitle || '图片预览'" width="min(92vw, 960px)">
      <div class="pcw-image-preview-shell">
        <img v-if="imagePreviewUrl" :src="imagePreviewUrl" :alt="imagePreviewTitle || ''" class="pcw-image-preview" />
      </div>
    </el-dialog>
    <div v-if="actionPanel.visible" class="pcw-action-overlay" role="dialog" aria-modal="true" :aria-label="actionPanel.title" @click.self="closeActionPanel">







      <section class="pcw-action-panel" data-testid="pcw-action-panel">







        <header>







          <div>







            <span>{{ actionPanel.kindLabel }}</span>







            <h2>{{ actionPanel.title }}</h2>







            <p>{{ actionPanel.description }}</p>







          </div>







          <button type="button" aria-label="关闭操作面板" @click="closeActionPanel">×</button>







        </header>







        <div class="pcw-action-panel-body">







          <article v-for="item in actionPanelRows" :key="item.label">







            <span>{{ item.label }}</span>







            <strong>{{ item.value }}</strong>







          </article>







        </div>







        <footer>







          <button type="button" @click="handleExportData">导出当前页</button>







          <button type="button" class="primary" @click="closeActionPanel">关闭</button>







        </footer>







      </section>







    </div>







    <div v-if="messagePanelVisible" class="pcw-action-overlay" role="dialog" aria-modal="true" aria-label="消息中心" @click.self="closeMessagePanel">







      <section class="pcw-action-panel pcw-message-panel" data-testid="pcw-message-panel">







        <header>







          <div>







            <span>消息中心</span>







            <h2>业务提醒</h2>







            <p>来自预警、供应商报价和数据源状态。点击消息会进入对应功能页。</p>







          </div>







          <button type="button" aria-label="关闭消息中心" @click="closeMessagePanel">×</button>







        </header>







        <div class="pcw-message-list">







          <button







            v-for="item in messageItems"







            :key="`${item.section}-${item.title}`"







            type="button"







            :class="item.tone"







            @click="openMessageTarget(item.section)"







          >







            <span>{{ item.label }}</span>







            <strong>{{ item.title }}</strong>







            <small>{{ item.detail }}</small>







          </button>







        </div>







        <footer>







          <button type="button" class="primary" @click="closeMessagePanel">关闭</button>







        </footer>







      </section>







    </div>







    <div v-if="alertSettingsVisible" class="pcw-action-overlay" role="dialog" aria-modal="true" aria-label="价格预警设置" @click.self="closeAlertSettingsPanel">







      <section class="pcw-action-panel pcw-alert-settings-panel" data-testid="pcw-alert-settings-panel">







        <header>







          <div>







            <span>价格预警</span>







            <h2>用业务语言设置提醒</h2>







            <p>例如“高于我能接受的采购价时提醒我”或“低于可考虑补货价时提醒我”。规则保存在当前浏览器，最终提醒以系统同步结果为准。</p>







          </div>







          <button type="button" aria-label="关闭价格预警设置" @click="closeAlertSettingsPanel">×</button>







        </header>







<div class="pcw-alert-settings-form">

          <label>

            <span>预警商品</span>

            <select v-model="alertSettings.identityKey">
              <option value="">请选择商品</option>
              <option v-for="item in alertRuleProductOptions" :key="item.value" :value="item.value">
                {{ item.label }}
              </option>
            </select>

          </label>

          <label>

            <span>来源</span>

            <select v-model="alertSettings.sourceName">
              <option value="">全部来源</option>
              <option v-for="item in alertRuleSourceOptions" :key="item" :value="item">
                {{ item }}
              </option>
            </select>

          </label>







          <label>







            <span>达到多少分必须今天处理</span>







            <input v-model.number="alertSettings.highRiskScore" type="number" min="0" max="100" step="1" />







          </label>







          <label>







            <span>达到多少分先放入观察</span>







            <input v-model.number="alertSettings.watchRiskScore" type="number" min="0" max="100" step="1" />







          </label>







          <label>







            <span>最高价提醒</span>







            <input v-model.number="alertSettings.maxPrice" type="number" min="0" step="0.01" />







          </label>







          <label>







            <span>最低价提醒</span>







            <input v-model.number="alertSettings.minPrice" type="number" min="0" step="0.01" />







          </label>







        </div>







        <div class="pcw-alert-settings-preview">







          <article v-for="row in trendAlertRows" :key="row[0]">







            <span>{{ row[0] }}</span>







            <strong :class="row[2]">{{ row[1] }}</strong>







            <small>{{ row[3] }}</small>







          </article>







        </div>







        <footer>







          <button type="button" @click="resetAlertSettings">恢复默认</button>







          <button type="button" class="primary" @click="saveAlertSettings">保存设置</button>







        </footer>







      </section>







    </div>







  </div>







</template>















<script setup lang="ts">







import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  buildProductAlertHit,
  pickAlertRuleProductLabel,
  readProductAlertRules,
  upsertProductAlertRule,
  writeProductAlertRules,
} from '../utils/alertRules'
import {
  getModuleDensityClass,
  getModuleLayout,
  isGeneratedModuleSection,
  readInitialWorkbenchSection,
  syncWorkbenchSectionUrl,
} from './PcPriceWorkbench.shared'







import type { MessageSection, ModuleView, SectionId } from './PcPriceWorkbench.shared'

const MenuPlanPanel = defineAsyncComponent(() => import('./MenuPlanPanel.vue'))
const ProcurementSupplierAdminPanel = defineAsyncComponent(() => import('./ProcurementSupplierAdminPanel.vue'))
const SettingsControlPanel = defineAsyncComponent(() => import('./SettingsControlPanel.vue'))
let deferredWorkbenchStylesPromise: Promise<unknown> | null = null

function loadDeferredWorkbenchStyles(sectionId: SectionId) {
  if (sectionId === 'summary') {
    return
  }
  deferredWorkbenchStylesPromise ||= import('./PcPriceWorkbench.defer.css')
}







import type {







  CrawlStatusItem,
  AuthUserRole,
  GlobalAlertRuleItem,
  SettingsChangeLogItem,
  LiancaiCategorySummaryItem,







  MarketSummaryItem,







  MenuPlanRow,







  ProcurementRecommendationItem,







  ProductOptionItem,







  ProductTrendRow,







  SignalInsightItem,







  SignalOverviewResponse,







  SupplierOverviewResponse,
  SupplierQuoteItem,







  SourceCoverageItem,







} from '../types'























const ALERT_SETTINGS_KEY = 'battel.pc-workbench.alert-settings'







const defaultAlertSettings = {







  highRiskScore: 70,







  watchRiskScore: 40,







  identityKey: '',

  productLabel: '',

  sourceName: '',

  sourceLabel: '',

  maxPrice: 0,







  minPrice: 0,







}















const props = defineProps<{







  activeTab: string







  locationLabel: string







  rows: MarketSummaryItem[]







  summaryLoading?: boolean
  summaryStatusText?: string
  summaryHasMoreRows?: boolean
  sourceCoverageRows?: SourceCoverageItem[]
  crawlStatus?: CrawlStatusItem | null
  summaryLiancaiFilter?: {
    source_name?: string
    liancai_top_category?: string
    liancai_subcategory?: string
    liancai_keyword?: string
    liancai_brand?: string
    liancaiTopCategory?: string
    liancaiSubcategory?: string
    liancaiKeyword?: string
    liancaiBrand?: string
  }







  liancaiCategorySummaryItems?: LiancaiCategorySummaryItem[]
  liancaiFacetOptions?: { keywords?: string[]; brands?: string[] }







  productOptions?: ProductOptionItem[]







  selectedIdentityKey?: string







  productSummary?: Record<string, any> | null







  trendRows?: ProductTrendRow[]







  trendLoading?: boolean







  refreshing?: boolean







  signalOverview?: SignalOverviewResponse | null







  supplierOverview?: SupplierOverviewResponse | null
  productSupplierQuotes?: SupplierQuoteItem[]







  procurementRecommendations?: ProcurementRecommendationItem[]







  planRows?: MenuPlanRow[]







  menuText?: string







  menuTables?: number







  menuDiners?: number







  menuPreferredLocation?: string







  menuLocationCandidates?: string[]







  ingredientRows?: Record<string, any>[]







  parsedMenuCount?: number







  matchedPlanCount?: number







  pendingPlanCount?: number







  menuTotalCostLabel?: string







  menuLoading?: boolean
  locationSuggestionLoading?: boolean
  globalAlertRules?: GlobalAlertRuleItem[]
  settingsChangeLogs?: SettingsChangeLogItem[]
  authRole?: AuthUserRole | null
  authSupplierId?: number | null
  authDisplayName?: string | null







}>()















const emit = defineEmits<{







  (event: 'select-tab', value: 'signals' | 'summary' | 'trend' | 'alerts' | 'menu'): void
  (event: 'section-change', value: SectionId): void







  (event: 'select-product', value: string): void







  (event: 'ensure-trend'): void







  (event: 'update:menu-text', value: string): void







  (event: 'update:menu-tables', value: number): void







  (event: 'update:menu-diners', value: number): void







  (event: 'update:menu-preferred-location', value: string): void







  (event: 'submit-menu'): void
  (event: 'menu-view-market', row: MenuPlanRow): void
  (event: 'menu-fill-supplier-price', row: MenuPlanRow): void
  (event: 'menu-confirm-row', row: MenuPlanRow): void
  (event: 'menu-fill-missing-quotes'): void
  (event: 'request-location-options'): void
  (event: 'request-location-suggestion'): void
  (event: 'request-summary-next-page'): void














  (event: 'refresh'): void
  (event: 'open-procurement-auth'): void
  (event: 'logout-procurement-auth'): void
  (event: 'update-summary-liancai-filter', value: { source_name?: string; liancai_top_category?: string; liancai_subcategory?: string; liancai_keyword?: string; liancai_brand?: string }): void














  (event: 'open-supplier-backend'): void







  (event: 'run-crawl'): void
  (event: 'run-source-crawl', value: { source_url?: string; source_name?: string }): void
  (event: 'update-crawl-schedule', value: { enabled: boolean; interval_seconds: number; fetch_mode?: 'requests' | 'playwright' }): void
  (event: 'update-source-config', value: {
    source_url: string
    enabled: boolean
    configured_name?: string
    market_scope?: string
    market_category?: string
    notes?: string
  }): void
  (event: 'update-source-strategy', value: {
    source_name: string
    preferred_fetch_mode?: 'requests' | 'playwright' | 'api'
    strategy?: string
    timeout_seconds?: number
    retry_count?: number
    request_delay_seconds?: number
    blocked_status_codes?: number[]
    verify_ssl?: boolean
    api_strategy?: string
  }): void
  (event: 'update-global-alert-rules', value: GlobalAlertRuleItem[]): void







}>()















const procurementAuthButtonLabel = computed(() => {
  if (props.authRole === 'admin' || props.authRole === 'procurement') {
    return props.authDisplayName?.trim() || '采购账号'
  }
  return '采购登录'
})

const currentSection = ref<SectionId>(readInitialWorkbenchSection() ?? 'summary')

const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')
const imagePreviewTitle = ref('')

const settingsLatestCaptureAt = computed(() =>
  (props.sourceCoverageRows || [])
    .map((item) => item.latest_capture)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1),
)

const settingsScheduleEnabled = computed(() => Boolean(props.crawlStatus?.schedule_enabled))

const settingsLastFinishedLabel = computed(() => formatShortDateTime(props.crawlStatus?.last_finished_at || settingsLatestCaptureAt.value))

const settingsCrawlResultLabel = computed(() => {
  if (!props.crawlStatus) return props.sourceCoverageRows?.length ? `${props.sourceCoverageRows.length} 个来源就绪` : '未获取状态'
  if (props.crawlStatus.is_running) return '同步中'
  const success = Number(props.crawlStatus.last_success_count || 0)
  const failed = Number(props.crawlStatus.last_failed_count || 0)
  return success || failed ? `${success} 成功 / ${failed} 异常` : props.sourceCoverageRows?.length ? `${props.sourceCoverageRows.length} 个来源就绪` : '未获取状态'
})

const settingsCrawlProgressLabel = computed(() => {
  if (!props.crawlStatus) {
    return props.sourceCoverageRows?.length ? `已返回 ${props.sourceCoverageRows.length} 个来源` : '等待同步状态'
  }
  const completed = Number(props.crawlStatus.completed_sources || 0)
  const total = Number(props.crawlStatus.last_total_sources || 0)
  const currentIndex = Number(props.crawlStatus.current_source_index || 0)
  if (props.crawlStatus.is_running) {
    if (!total) return props.crawlStatus.current_source_detail || '准备同步数据来源'
    const activeIndex = Math.max(currentIndex, completed + 1)
    const sourceProgress = Math.round(Number(props.crawlStatus.current_source_progress || 0) * 100)
    return `第 ${activeIndex}/${total} 个来源 · 当前来源 ${sourceProgress}%`
  }
  return total ? `最近完成 ${completed || total}/${total} 个来源` : `已返回 ${props.sourceCoverageRows?.length || 0} 个来源`
})

const settingsScheduleDetail = computed(() => {
  if (!settingsScheduleEnabled.value) return '当前仅手动同步'
  return props.crawlStatus?.next_run_at ? `下次 ${formatShortDateTime(props.crawlStatus.next_run_at)}` : '每日自动同步'
})

const marketTrendSeries = computed(() => {
  const rows = (props.rows || [])
    .filter((row) => Number(row.average_price ?? 0) > 0)
    .map((row) => ({
      label: formatShortDateTime(row.latest_captured_at || row.captured_dates || null),
      avg: Number(row.average_price || 0),
      low: Number(row.lowest_price || row.average_price || 0),
      high: Number(row.highest_price || row.average_price || 0),
    }))
    .filter((item) => item.avg > 0)
  return rows.slice(-8)
})







const mainViewport = ref<HTMLElement | null>(null)







const filterToolbar = ref<HTMLElement | null>(null)







const locationPicker = ref<HTMLElement | null>(null)







const activeFilterIndex = ref(0)







const activeFilterMenu = ref<number | null>(null)







const filterSearchText = ref('')







const locationMenuVisible = ref(false)
const locationMenuExpanded = ref(false)







const selectedLocationLabel = ref('')







const pageSizeOptions = [8, 16, 32, 50, 100]
const pageSize = ref(8)







const tablePage = ref<Record<SectionId, number>>({







  summary: 1,







  trend: 1,







  alerts: 1,







  market: 1,







  suppliers: 1,







  purchase: 1,







  quotes: 1,







  plan: 1,







  reports: 1,







  settings: 1,







})







const filterSelections = ref<Record<SectionId, number[]>>({







  summary: [0, 0, 0, 0],







  trend: [0, 0, 0],







  alerts: [0, 0, 0, 0, 0],







  market: [0, 0, 0, 0],







  suppliers: [0, 0, 0, 0],







  purchase: [0, 0, 0, 0],







  quotes: [0, 0, 0, 0],







  plan: [0, 0, 0, 0],







  reports: [0, 0, 0, 0, 0],







  settings: [0, 0, 0, 0, 0],







})







const actionFeedback = ref('')

type AlertDispositionAction = 'resolved' | 'ignored' | 'quote'

type AlertDispositionRecord = {
  key: string
  time: string
  text: string
  status: string
  tone: 'done' | 'watch'
  action: AlertDispositionAction
}

const alertDispositionRecords = ref<AlertDispositionRecord[]>([])







const priceMetric = ref<'avg' | 'low'>('avg')







const chartRange = ref<7 | 30 | 90>(7)







const messagePanelVisible = ref(false)







const alertSettingsVisible = ref(false)







const alertSettings = ref(readAlertSettings())

const productAlertRules = ref(readProductAlertRules())







const actionPanel = ref({







  visible: false,







  title: '',







  description: '',







  kind: '' as SectionId | 'export',







  kindLabel: '工作台动作',







  rows: [] as string[],







})















const sectionToWorkspaceTab: Partial<Record<SectionId, 'signals' | 'summary' | 'trend' | 'alerts' | 'menu'>> = {







  summary: 'summary',







  trend: 'trend',







  alerts: 'alerts',







  plan: 'menu',







}















function syncSectionFromActiveTab(tab: string) {
  if (
    tab === 'summary'
    && ['trend', 'alerts', 'market', 'suppliers', 'quotes', 'reports', 'settings', 'purchase', 'plan'].includes(currentSection.value)
  ) {
    return
  }

  if (tab === 'menu' && currentSection.value === 'plan') {
    return
  }







  const nextSection = tab === 'trend'







    ? 'trend'







    : (tab === 'signals' || tab === 'alerts')







      ? 'alerts'







      : tab === 'menu'







        ? 'plan'







        : 'summary'







  if (currentSection.value !== nextSection) {







    currentSection.value = nextSection
    syncWorkbenchSectionUrl(nextSection)







  }







}















watch(







  () => props.activeTab,







  (tab) => {







    syncSectionFromActiveTab(tab)







  },







  { immediate: true },







)















watch(
  currentSection,
  (sectionId) => loadDeferredWorkbenchStyles(sectionId),
  { immediate: true },
)

const alertBadge = computed(() => {







  const count = props.signalOverview?.alert_count ?? props.signalOverview?.top_risks?.length ?? 0







  return count > 0 ? String(count) : ''







})















const sideSourceLabel = computed(() => {







  const sourceCount = props.sourceCoverageRows?.length || 0







  const quoteCount = props.rows.reduce((sum, row) => sum + Number(row.price_observation_count || row.market_count || row.site_count || 0), 0)







  if (!sourceCount && !quoteCount) return '等待同步'







  return `${sourceCount} 源 / ${quoteCount} 报价`







})















const navItems = computed(() => [







  { id: 'summary', target: 'summary', label: '汇总行情', icon: ['M4 19V5', 'M4 19h16', 'M8 15l3-4 3 2 4-7'] },







  { id: 'trend', target: 'trend', label: '单品趋势', icon: ['M4 6h16v12H4z', 'M7 15l3-4 3 2 4-5'] },







  { id: 'alerts', target: 'signals', label: '价格预警', badge: alertBadge.value, icon: ['M18 16v-5a6 6 0 0 0-12 0v5l-2 2h16z', 'M10 20h4'] },







  { id: 'market', target: 'summary', label: '市场管理', icon: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', 'M3.6 9h16.8', 'M3.6 15h16.8', 'M12 3c2 2.4 3 5.4 3 9s-1 6.6-3 9c-2-2.4-3-5.4-3-9s1-6.6 3-9z'] },







  { id: 'suppliers', target: 'suppliers', label: '供应商管理', icon: ['M5 10h14v9H5z', 'M7 10V7h10v3', 'M8 14h8'] },







  { id: 'purchase', target: 'menu', label: '我的采购', icon: ['M6 7h15l-2 8H8z', 'M6 7 5 4H3', 'M9 20h.01', 'M17 20h.01'] },







  { id: 'quotes', target: 'trend', label: '报价记录', icon: ['M7 3h10v18H7z', 'M10 8h4', 'M10 12h4', 'M10 16h2'] },







  { id: 'plan', target: 'menu', label: '采购计划', icon: ['M5 5h14v15H5z', 'M8 3v4', 'M16 3v4', 'M8 11h8', 'M8 15h5'] },







  { id: 'reports', target: 'signals', label: '数据报表', icon: ['M5 19V9', 'M12 19V5', 'M19 19v-7', 'M3 19h18'] },







  { id: 'settings', target: 'signals', label: '系统设置', icon: ['M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z', 'M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2 3.4-.2-.1a1.7 1.7 0 0 0-1.9.1 8 8 0 0 1-1.7 1l-.2.1a1.7 1.7 0 0 0-1.1 1.5V23H8v-.1a1.7 1.7 0 0 0-1.1-1.5l-.2-.1a8 8 0 0 1-1.7-1 1.7 1.7 0 0 0-1.9-.1l-.2.1-2-3.4.1-.1A1.7 1.7 0 0 0 1.6 15 8.1 8.1 0 0 1 1.5 13 1.7 1.7 0 0 0 .5 11.5L.3 11.4 2.3 8l.2.1a1.7 1.7 0 0 0 1.9-.1 8 8 0 0 1 1.7-1l.2-.1A1.7 1.7 0 0 0 7.4 5.4V5h4.1v.4a1.7 1.7 0 0 0 1.1 1.5l.2.1a8 8 0 0 1 1.7 1 1.7 1.7 0 0 0 1.9.1l.2-.1 2 3.4-.2.1a1.7 1.7 0 0 0-1 1.5 8.1 8.1 0 0 1 0 2z'] },







] as const)















const navGroups = computed(() => [







  { title: '今天先看', items: navItems.value.slice(0, 3) },







  { title: '去执行', items: navItems.value.slice(3, 8) },







  { title: '系统与复盘', items: navItems.value.slice(8) },







] as const)















const pageTitle = computed(() => {







  if (currentSection.value === 'summary' || currentSection.value === 'alerts') return '市场价格工作台'







  return navItems.value.find((item) => item.id === currentSection.value)?.label || '市场价格工作台'







})














const actionPanelRows = computed(() => {







  const rows = actionPanel.value.rows.length ? actionPanel.value.rows : ['当前暂无可展开的明细']







  return rows.slice(0, 8).map((value, index) => ({







    label: index === 0 ? '当前记录' : `明细 ${index + 1}`,







    value,







  }))







})















async function handleNavSelect(sectionId: SectionId) {
  syncWorkbenchSectionUrl(sectionId)
  emit('section-change', sectionId)







  if (currentSection.value === sectionId) {







    const workspaceTab = sectionToWorkspaceTab[sectionId]







    if (workspaceTab && props.activeTab !== workspaceTab) {







      emit('select-tab', workspaceTab)







    } else if (sectionId === 'trend') {







      emit('ensure-trend')







    }







    mainViewport.value?.scrollTo({ top: 0, behavior: 'smooth' })







    return







  }







  currentSection.value = sectionId







  const workspaceTab = sectionToWorkspaceTab[sectionId]







  if (workspaceTab && props.activeTab !== workspaceTab) {







    emit('select-tab', workspaceTab)







  } else if (sectionId === 'trend') {







    emit('ensure-trend')







  }







  activeFilterIndex.value = 0







  activeFilterMenu.value = null







  resetTablePage(sectionId)







  await nextTick()







  mainViewport.value?.scrollTo({ top: 0, behavior: 'auto' })







}















function openInlineSystemSettings() {
  void handleNavSelect('settings')
}

function handleSettingsRunCrawl() {
  if (props.crawlStatus?.is_running) return
  emit('run-crawl')
}

function openSummaryProductTrend(identityKey: string) {
  if (!identityKey) return
  emit('select-product', identityKey)
  void handleNavSelect('trend')
}

function openWorkbenchActionSection(sectionId: SectionId, identityKey = '') {
  if (sectionId === 'trend' && identityKey) {
    openSummaryProductTrend(identityKey)
    return
  }
  void handleNavSelect(sectionId)
}

function showMissingAlertIdentityHint(actionLabel: string, row: AlertTaskRow) {
  openActionPanel(
    `${actionLabel}缺少商品标识`,
    [
      `${row.name} 当前预警没有 identity_key，无法直接带入单品趋势或供应商报价。`,
      '请先在汇总行情或单品趋势中选择对应商品，再继续处理。',
    ],
    'alerts',
  )
}

function handleAlertTrendAction(row: AlertTaskRow) {
  const identityKey = row.identityKey?.trim()
  if (!identityKey) {
    showMissingAlertIdentityHint('看趋势', row)
    return
  }
  openSummaryProductTrend(identityKey)
}

function handleAlertSupplierQuoteAction(row: AlertTaskRow) {
  const identityKey = row.identityKey?.trim()
  if (!identityKey) {
    showMissingAlertIdentityHint('去供应商报价', row)
    return
  }
  upsertAlertDisposition(row, 'quote')
  if (typeof window === 'undefined') return
  const params = new URLSearchParams(window.location.search)
  params.set('mode', 'supplier')
  params.set('tab', 'supplier')
  params.set('section', 'quote')
  params.set('identity_key', identityKey)
  params.set('product', identityKey)
  params.set('product_label', row.name)
  params.set('source', 'price_alert')
  params.set('context_title', `价格预警：${row.name}`)
  params.set('alert_rule', row.rule)
  actionFeedback.value = `已生成“${row.name}”补价处理记录，并带着价格预警上下文进入供应后台报价管理`
  window.location.assign(`/supplier-backend?${params.toString()}`)
}

function buildAlertDispositionKey(row: AlertTaskRow) {
  return `${row.identityKey || row.name}|${row.type}|${row.rule}`
}

function formatAlertDispositionTime() {
  const now = new Date()
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${pad(now.getHours())}:${pad(now.getMinutes())}`
}

function upsertAlertDisposition(row: AlertTaskRow, action: AlertDispositionAction) {
  const key = buildAlertDispositionKey(row)
  const status = action === 'ignored' ? '已忽略' : action === 'quote' ? '已生成补价任务' : '已处理'
  const text = action === 'ignored'
    ? `${row.name} 本次预警已忽略，规则：${row.rule}`
    : action === 'quote'
      ? `${row.name} 已从价格预警转入供应商补价，规则：${row.rule}`
      : `${row.name} 价格预警已人工处理，规则：${row.rule}`
  const nextRecord: AlertDispositionRecord = {
    key,
    time: formatAlertDispositionTime(),
    text,
    status,
    tone: action === 'quote' ? 'watch' : 'done',
    action,
  }
  alertDispositionRecords.value = [
    nextRecord,
    ...alertDispositionRecords.value.filter((item) => item.key !== key),
  ].slice(0, 8)
}

function handleAlertResolveAction(row: AlertTaskRow, action: Extract<AlertDispositionAction, 'resolved' | 'ignored'>) {
  upsertAlertDisposition(row, action)
  actionFeedback.value = action === 'ignored'
    ? `已忽略“${row.name}”本次预警，并写入处理记录`
    : `已标记“${row.name}”价格预警处理完成`
}















function isFilterSelected(index: number) {







  const options = sectionFilterOptions.value[currentSection.value]?.[index] || []







  const selectedIndex = filterSelections.value[currentSection.value]?.[index] || 0







  const selectedValue = options[selectedIndex] || ''







  return activeFilterMenu.value === index || (selectedIndex > 0 && !isNeutralFilter(selectedValue))







}

function hasFilterChoices(index: number) {
  const options = sectionFilterOptions.value[currentSection.value]?.[index] || []
  return options.length > 1
}

function getFilterButtonLabel(index: number, value: string) {
  const label = formatFilterLabel(value)
  if (hasFilterChoices(index)) return label
  if (currentSection.value === 'summary' && index === 3) return '无更多细分'
  return label
}

function getFilterButtonTitle(index: number, value: string) {
  const label = getFilterButtonLabel(index, value)
  if (hasFilterChoices(index)) return `筛选：${label}`
  if (currentSection.value === 'summary' && index === 3) return '当前条件下没有可选细分'
  return `当前没有更多可选项：${label}`
}















function handleFilterSelect(index: number) {







  activeFilterIndex.value = index







  const options = sectionFilterOptions.value[currentSection.value]?.[index] || []







  if (options.length <= 1) {







    activeFilterMenu.value = null







    filterSearchText.value = ''







    return







  }







  const nextMenu = activeFilterMenu.value === index ? null : index







  activeFilterMenu.value = nextMenu







  filterSearchText.value = ''







}















function selectFilterOption(index: number, optionIndex: number) {







  const selectedOption = sectionFilterOptions.value[currentSection.value]?.[index]?.[optionIndex] || ''







  const currentSelections = [...(filterSelections.value[currentSection.value] || [])]







  currentSelections[index] = optionIndex
  if (currentSection.value === 'summary') {
    if (index === 1) {
      currentSelections[2] = 0
      currentSelections[3] = 0
    } else if (index === 2) {
      currentSelections[3] = 0
    }
  }







  filterSelections.value = {







    ...filterSelections.value,







    [currentSection.value]: currentSelections,







  }







  activeFilterIndex.value = index







  activeFilterMenu.value = null







  filterSearchText.value = ''







  resetTablePage(currentSection.value)

  if (currentSection.value === 'summary' && index >= 0 && index <= 3) {
    emit('update-summary-liancai-filter', buildSummaryLiancaiFilterFromSelections(currentSelections))
  }







  if (currentSection.value === 'trend' && index === 0 && optionIndex > 0) {







    const identityKey = findTrendProductIdentityByFilterValue(selectedOption)







    if (identityKey && identityKey !== props.selectedIdentityKey) {







      emit('select-product', identityKey)







    }







  }







}















function getVisibleFilterOptions(index: number) {







  const options = sectionFilterOptions.value[currentSection.value]?.[index] || []







  const keyword = filterSearchText.value.trim().toLowerCase()







  return options







    .map((value, optionIndex) => ({ value, optionIndex }))







    .filter((option) => !keyword || formatFilterLabel(option.value).toLowerCase().includes(keyword))







}















function toggleLocationMenu() {







  locationMenuVisible.value = !locationMenuVisible.value
  if (locationMenuVisible.value) {
    emit('request-location-options')
  }
  if (!locationMenuVisible.value) {
    locationMenuExpanded.value = false
  }







  activeFilterMenu.value = null







  filterSearchText.value = ''







}















function selectLocation(option: string) {







  selectedLocationLabel.value = option







  locationMenuVisible.value = false
  locationMenuExpanded.value = false
  locationMenuExpanded.value = false







  const marketFilterIndexBySection: Partial<Record<SectionId, number>> = {







    summary: 0,







    trend: 1,







    alerts: 0,







    market: 0,







    reports: 1,







  }







  const filterIndex = marketFilterIndexBySection[currentSection.value]







  if (filterIndex == null) return







  const options = sectionFilterOptions.value[currentSection.value]?.[filterIndex] || []







  const optionIndex = options.findIndex((item) => formatFilterLabel(item) === option)







  if (optionIndex >= 0) selectFilterOption(filterIndex, optionIndex)







}















function handleDocumentPointerDown(event: PointerEvent) {







  const hasFilterMenu = activeFilterMenu.value !== null







  if (!hasFilterMenu && !locationMenuVisible.value) return







  const target = event.target







  if (target instanceof Node && filterToolbar.value?.contains(target)) return







  if (target instanceof Node && locationPicker.value?.contains(target)) return







  if (hasFilterMenu) activeFilterMenu.value = null







  locationMenuVisible.value = false
  locationMenuExpanded.value = false







}















function handleDocumentKeydown(event: KeyboardEvent) {







  if (event.key !== 'Escape') return







  activeFilterMenu.value = null







  locationMenuVisible.value = false







  if (messagePanelVisible.value) closeMessagePanel()







  if (alertSettingsVisible.value) closeAlertSettingsPanel()







  if (actionPanel.value.visible) closeActionPanel()







}















function openMessagePanel() {







  messagePanelVisible.value = true







}















function closeMessagePanel() {







  messagePanelVisible.value = false







}















async function openMessageTarget(section: MessageSection) {







  closeMessagePanel()







  await handleNavSelect(section)







}















function openAlertSettingsPanel() {
  const currentIdentityKey = props.selectedIdentityKey || ''
  const currentProductLabel = pickAlertRuleProductLabel(
    currentIdentityKey,
    props.productOptions || [],
    selectedProductName.value,
  )
  alertSettings.value = normalizeAlertSettings({
    ...alertSettings.value,
    identityKey: alertSettings.value.identityKey || currentIdentityKey,
    productLabel: alertSettings.value.productLabel || currentProductLabel,
    sourceName: alertSettings.value.sourceName || '',
    sourceLabel: alertSettings.value.sourceLabel || '',
  })







  alertSettingsVisible.value = true







}















function closeAlertSettingsPanel() {







  alertSettingsVisible.value = false







}















function saveAlertSettings() {
  alertSettings.value = {
    ...alertSettings.value,
    productLabel: pickAlertRuleProductLabel(
      alertSettings.value.identityKey,
      props.productOptions || [],
      alertSettings.value.productLabel,
    ),
  }







  alertSettings.value = normalizeAlertSettings(alertSettings.value)







  writeAlertSettings(alertSettings.value)

  const nextRules = upsertProductAlertRule(readProductAlertRules(), {
    identityKey: alertSettings.value.identityKey,
    productLabel: alertSettings.value.productLabel,
    sourceName: String(alertSettings.value.sourceName || '').trim(),
    sourceLabel: String(alertSettings.value.sourceName || '').trim(),
    minPrice: alertSettings.value.minPrice,
    maxPrice: alertSettings.value.maxPrice,
    enabled: true,
  })

  productAlertRules.value = nextRules

  writeProductAlertRules(nextRules)







  closeAlertSettingsPanel()







  actionFeedback.value = '价格提醒已保存'







  window.setTimeout(() => {







    if (actionFeedback.value === '价格提醒已保存') actionFeedback.value = ''







  }, 1600)







}















function resetAlertSettings() {







  alertSettings.value = {
    ...defaultAlertSettings,
    identityKey: props.selectedIdentityKey || '',
    productLabel: pickAlertRuleProductLabel(
      props.selectedIdentityKey || '',
      props.productOptions || [],
      selectedProductName.value,
    ),
    sourceName: '',
    sourceLabel: '',
  }







  writeAlertSettings(alertSettings.value)







}















function setChartRange(value: 7 | 30 | 90) {







  chartRange.value = value







  actionFeedback.value = `已切换为近 ${value} 日视图`







  window.setTimeout(() => {







    if (actionFeedback.value === `已切换为近 ${value} 日视图`) actionFeedback.value = ''







  }, 1400)







}















async function handleModuleFilterFocus() {







  activeFilterIndex.value = 0







  mainViewport.value?.scrollTo({ top: 0, behavior: 'smooth' })







  await nextTick()







  const firstFilterButton = filterToolbar.value?.querySelector<HTMLButtonElement>('.pcw-filter-item > button')







  firstFilterButton?.focus()







  const options = sectionFilterOptions.value[currentSection.value]?.[0] || []







  if (options.length > 1) {







    activeFilterMenu.value = 0







    filterSearchText.value = ''







  } else {







    actionFeedback.value = '当前暂无可展开筛选项'







    window.setTimeout(() => {







      if (actionFeedback.value === '当前暂无可展开筛选项') actionFeedback.value = ''







    }, 1400)







  }







}















function handleModulePrimaryAction() {







  const section = currentSection.value
  if (section === 'settings') {
    handleSettingsRunCrawl()
    return
  }







  if (!moduleHasTableRows.value && !moduleHasSideItems.value && !moduleHasFlowItems.value) {







    const message = `${moduleView.value.kicker}暂无可处理数据，请先刷新`







    actionFeedback.value = message







    window.setTimeout(() => {







      if (actionFeedback.value === message) actionFeedback.value = ''







    }, 1800)







    return







  }







  if (section === 'suppliers' || section === 'quotes') {







    emit('open-supplier-backend')







    return







  }







  if (section === 'purchase' || section === 'plan') {







    emit('select-tab', 'menu')







    return







  }







  if (section === 'reports') {







    handleExportData()







    return







  }







  emit('refresh')







}















const supplierModuleView = computed<ModuleView>(() => {







  const overview = props.supplierOverview







  const summary = overview?.summary







  const categoryItems = overview?.category_items || []







  const recentQuotes = overview?.recent_quotes || []







  return {







    kicker: '供应商管理',







    title: '供应商报价覆盖',







    description: summary







      ? `已接入 ${summary.supplier_count} 个供应商，累计 ${summary.total_quote_count} 条报价。`







      : '等待供应商档案与报价同步。',







    action: '进入后台',







    metrics: [







      { label: '已接入供应商', value: String(summary?.supplier_count || 0), detail: '当前已纳入系统的供应商总数', tone: 'blue' },







      { label: '最近有报价', value: String(recentQuotes.length || 0), detail: recentQuotes.length ? '最近出现在报价台账里的记录' : '最近还没有新报价', tone: 'green' },







      { label: '待补报价', value: String(Math.max((summary?.active_supplier_count || 0) - recentQuotes.length, 0)), detail: categoryItems[0]?.market_category ? `优先补 ${categoryItems[0].market_category} 报价` : '当前最该补录的报价缺口', tone: 'warn' },







      { label: '停用供应商', value: String(Math.max((summary?.supplier_count || 0) - (summary?.active_supplier_count || 0), 0)), detail: '当前未参与报价协同的供应商', tone: 'blue' },







    ],







    tableTitle: '供应商报价覆盖',







    columns: ['供应商', '联系人', '主营分类', '最近报价', '报价单位', '状态', '操作'],







    tableRows: recentQuotes.slice(0, 8).map((item) => [







      item.supplier_name || '-',







      item.contact_name || '-',







      item.market_category || item.category || '-',







      item.quote_price == null ? '-' : formatNumber(item.quote_price),







      item.quote_unit || '-',







      item.status === 'invalid' || item.invalidated_at ? '无效' : '启用',







      '查看  去后台',







    ]),







    sideTitle: '报价提醒',







    sideItems: recentQuotes.slice(0, 4).map((item) => ({







      label: item.comparison_label || '报价',







      title: item.supplier_name || '未命名供应商',







      detail: `${item.product_name || item.price_identity_label || '商品'} ${formatNumber(item.quote_price)} ${item.quote_unit || ''}`.trim(),







      tone: item.status === 'invalid' || item.invalidated_at ? 'warn' : 'green',







    })),







    flowTitle: '协作流程',







    flow: categoryItems.slice(0, 4).map((item) => ({







      step: item.market_category || '分类',







      text: `${item.active_supplier_count}/${item.supplier_count} 家启用，${item.quote_count} 条报价`,







    })),







  }







})















const alertModuleView = computed<ModuleView>(() => {







  const items = signalItems.value







  const columns = ['商品', '市场', '类型', '风险分', '触发依据', '建议动作', '状态']







  return {







    kicker: '价格预警',







    title: '价格提醒',







    description: props.signalOverview?.headline || '价格变化和采购风险会显示在这里。',







    action: '刷新预警',







    metrics: [
      {
        label: '需要处理',
        value: String(alertPendingCount.value),
        detail: alertPendingCount.value ? '建议先处理这些商品' : '暂无紧急项',
        tone: alertPendingCount.value ? 'warn' : 'green',
      },
      {
        label: '涨价提醒',
        value: String(filteredAlertTaskRows.value.filter((row) => row.tone === 'up').length),
        detail: '可能直接抬高今天的采购成本',
        tone: 'danger',
      },
      {
        label: '降价提醒',
        value: String(filteredAlertTaskRows.value.filter((row) => row.tone === 'down').length),
        detail: '如果库存合适，可考虑先补一轮货',
        tone: 'green',
      },
      {
        label: '先放观察',
        value: String(alertWatchCount.value),
        detail: '先放观察池，晚点再看',
        tone: 'blue',
      },
    ],







    tableTitle: '预警任务列表',







    columns,







    tableRows: withEmptyRows(items.slice(0, 8).map((item) => [







      item.product_name || '-',







      item.recommended_market || item.recommended_site || '本地市场',







      item.signal_code || item.trend_label || '价格信号',







      `${Math.round(item.risk_score || 0)} 分`,







      item.reason_summary || '-',







      formatRecommendedAction(item.recommended_action, '-'),







      item.signal_level === 'high' || item.signal_level === 'critical' ? '待处理' : '观察中',







    ]), columns),







    sideTitle: '处理建议',







    sideItems: withEmptySideItems((props.signalOverview?.recommended_actions || []).slice(0, 4).map((item, index) => ({







      label: formatRecommendedAction(item.action, `建议${index + 1}`),







      title: item.title || '处理建议',







      detail: item.description || '-',







      tone: index === 0 ? 'warn' : 'blue',







    }))),







    flowTitle: '预警处理',







    flow: withEmptyFlow(items.slice(0, 4).map((item) => ({







      step: item.latest_captured_at ? formatTimeOnly(item.latest_captured_at) : item.signal_level,







      text: `${item.product_name}：${item.reason_summary || formatRecommendedAction(item.recommended_action, '价格变化已同步')}`,







    }))),







  }







})















const marketModuleView = computed<ModuleView>(() => {







  const rows = props.rows || []
  const hasRealRows = rows.length > 0







  const sources = props.sourceCoverageRows || []







  const columns = ['市场名称', '所属分类', '最近同步', '成功率', '报价源', '状态', '操作']







  const priceRows = rows.filter((row) => row.average_price != null)







  const fallbackMarkets = rows.slice(0, 5).map((row) => ({







    name: row.region_label || row.lowest_price_site || row.product_name || '本地市场',







    category: inferMarketCategory(row),







    latest: currentDateLabel,







    rate: row.average_price == null ? '待同步' : '已同步',







    status: row.average_price == null ? '待同步' : '在线',







  }))







  return {







    kicker: '市场管理',







    title: '市场行情',







    description: sources.length ? `${sources.length} 个来源正在更新价格。` : '等待来源同步。',







    action: '刷新行情',







    metrics: [







      { label: '价格来源', value: String(Math.max(sources.length, new Set(fallbackMarkets.map((item) => item.name)).size)), detail: sources.length ? '当前可用来源' : '从菜价汇总推算', tone: 'blue' },







      { label: '有新价格', value: String(priceRows.length || sources.filter((item) => item.enabled !== false).length), detail: '本轮拿到价格', tone: 'green' },







      { label: '报价记录', value: String(rows.reduce((sum, row) => sum + Number(row.price_observation_count || row.market_count || row.site_count || 0), 0) || priceRows.length), detail: '本轮报价量', tone: 'blue' },







      { label: '异常来源', value: String(props.signalOverview?.alert_count || 0), detail: props.signalOverview?.alert_count ? '建议先打开异常来源排查' : '当前没有异常来源', tone: props.signalOverview?.alert_count ? 'warn' : 'green' },







    ],







    tableTitle: '市场行情监控',







    columns,







    tableRows: withEmptyRows((sources.length







      ? sources.map((item) => [







        item.configured_name || item.source_name || item.source_url || '-',







        formatSourceCategoryPath(item),


        item.latest_capture ? formatShortDateTime(item.latest_capture) : '-',







        Number(item.failed_count || 0) > 0 ? `失败 ${item.failed_count} 次` : '正常',







        `${item.price_record_count || item.market_count || item.source_item_count || 0} 条`,







        item.status || (item.enabled === false ? '离线' : '在线'),







        '查看来源',







      ])







      : fallbackMarkets.map((item) => [







        item.name,







        item.category,







        item.latest,







        item.rate,







        '菜价汇总',







        item.status,







        '查看来源',







      ])), columns),







    sideTitle: '异常任务',







    sideItems: withEmptySideItems(signalItems.value.slice(0, 2).map((item) => ({







      label: item.signal_level,







      title: `${item.product_name} · ${item.recommended_market || item.recommended_site || '本地市场'}`,







      detail: item.reason_summary || formatRecommendedAction(item.recommended_action),







      tone: item.signal_level === 'high' || item.signal_level === 'critical' ? 'warn' : 'blue',







    }))),







    flowTitle: '市场状态',







    flow: withEmptyFlow(sources.slice(0, 2).map((item) => ({







      step: item.latest_capture ? formatMonthDay(item.latest_capture) : '来源',







      text: `${item.configured_name || item.source_name || item.source_url}：${item.price_record_count || 0} 条价格记录`,







    }))),







  }







})
















const quotesModuleView = computed<ModuleView>(() => {
  const quotes = focusedSupplierQuotes.value
  const hasFocusedQuotes = quotes.length > 0
  const hasTrendQuotes = trendQuoteRows.value.length > 0
  const summary = props.supplierOverview?.summary
  const columns = ['时间', '商品', '供应商', '报价', '单位', '差异', '录入方式', '状态', '操作']
  const quoteRows = quotes.slice(0, 10).map((item) => [
    item.quoted_at ? formatTimeOnly(item.quoted_at) : '--:--',
    item.product_name || item.price_identity_label || selectedProductName.value || '-',
    item.supplier_name || '-',
    formatNumber(item.quote_price),
    item.quote_unit || '-',
    formatSignedNumber(item.price_diff_to_market_average),
    item.channel || item.quoted_by || '系统同步',
    item.status === 'invalid' || item.invalidated_at ? '无效' : '有效',
    '查看记录',
  ])
  const fallbackTrendRows = hasFocusedQuotes ? [] : trendQuoteRows.value.slice(0, 10).map((item) => [
    item[3] || '--:--',
    selectedProductName.value || props.selectedIdentityKey || '当前商品',
    item[0] || '-',
    item[2] || '-',
    String(props.productSummary?.price_unit_basis || props.productSummary?.unit || '-'),
    '-',
    item[1] || '趋势报价',
    '趋势参考',
    '承接采购',
  ])
  const visibleRows = quoteRows.length ? quoteRows : fallbackTrendRows
  const description = hasFocusedQuotes
    ? `当前商品已承接 ${quotes.length} 条供应商报价，可直接进入采购确认。`
    : (hasTrendQuotes
      ? '当前商品有趋势/今日报价，但尚未进入供应商报价台账，已先作为待承接参考展示。'
      : (summary ? `供应商报价库累计 ${summary.total_quote_count} 条，最近报价 ${summary.latest_quoted_at ? formatShortDateTime(summary.latest_quoted_at) : '暂无时间'}。` : '等待供应商报价记录同步。'))

  return {
    kicker: '报价记录',
    title: '供应商报价',
    description,
    action: '去报价后台',
    metrics: [
      { label: '当前商品报价', value: String(quotes.length), detail: hasFocusedQuotes ? '已有供应商报价' : (hasTrendQuotes ? '可转采购参考' : '当前商品暂无报价'), tone: hasFocusedQuotes ? 'green' : 'warn' },
      { label: '报价记录', value: String(summary?.total_quote_count || quotes.length), detail: '供应商报价库', tone: 'blue' },
      { label: '有效记录', value: String(quotes.filter((item) => item.status !== 'invalid' && !item.invalidated_at).length), detail: '当前商品有效报价', tone: 'green' },
      { label: '覆盖供应商', value: String(new Set(quotes.map((item) => item.supplier_id || item.supplier_name)).size), detail: '当前商品供应商', tone: 'blue' },
    ],
    tableTitle: hasFocusedQuotes ? '当前商品报价记录' : '当前商品趋势报价承接',
    columns,
    tableRows: withEmptyRows(visibleRows, columns),
    sideTitle: '记录质量',
    sideItems: withEmptySideItems([
      { label: '当前', title: hasFocusedQuotes ? `当前商品 ${quotes.length} 条报价` : '当前商品暂无台账报价', detail: hasTrendQuotes ? '趋势报价可先承接到采购动作' : '等待供应商提交报价', tone: hasFocusedQuotes ? 'green' : 'warn' },
      { label: '有效', title: `有效记录 ${quotes.filter((item) => item.status !== 'invalid' && !item.invalidated_at).length} 条`, detail: '当前商品报价', tone: 'green' },
      { label: '同步', title: summary?.latest_quoted_at ? formatShortDateTime(summary.latest_quoted_at) : '暂无同步时间', detail: '最新报价时间', tone: 'blue' },
    ]),
    flowTitle: '报价流',
    flow: withEmptyFlow((hasFocusedQuotes ? quotes.slice(0, 4).map((item) => ({
      step: item.quoted_at ? formatTimeOnly(item.quoted_at) : '同步',
      text: `${item.supplier_name || '供应商'} 报价 ${formatNumber(item.quote_price)} ${item.quote_unit || ''}`.trim(),
    })) : trendQuoteRows.value.slice(0, 4).map((item) => ({
      step: item[3] || '趋势',
      text: `${selectedProductName.value || '当前商品'} ${item[0]} 报价 ${item[2]}，可转采购确认`,
    })))),
  }
})












const purchaseModuleView = computed<ModuleView>(() => {
  const recommendations = props.procurementRecommendations || []
  const quotes = focusedSupplierQuotes.value
  const validQuotes = quotes.filter((item) => item.quote_price != null && item.status !== 'invalid' && !item.invalidated_at)
  const lowestQuote = validQuotes.length ? [...validQuotes].sort((left, right) => Number(left.quote_price) - Number(right.quote_price))[0] : null
  const trendFallbackRows = validQuotes.length ? [] : trendQuoteRows.value.slice(0, 3)
  const quotePurchaseRows = validQuotes.slice(0, 5).map((item) => [
    item.product_name || item.price_identity_label || selectedProductName.value || props.selectedIdentityKey || '-',
    formatCurrency(props.productSummary?.average_price || props.productSummary?.current_lowest_price),
    formatCurrency(item.quote_price),
    '-',
    item.supplier_name || '-',
    item === lowestQuote ? '待确认·最低报价' : '待确认',
    '确认采购',
  ])
  const trendPurchaseRows = trendFallbackRows.map((item) => [
    selectedProductName.value || props.selectedIdentityKey || '当前商品',
    item[2] || '-',
    item[2] || '-',
    '-',
    item[0] || item[1] || '-',
    '待确认·趋势报价',
    '补入采购',
  ])
  const recommendationRows = recommendations.slice(0, 8).map((item) => [
    item.ingredient_name || item.identity_key || '-',
    formatCurrency(item.reference_price),
    formatCurrency(item.reference_price),
    item.impact_value == null ? '-' : formatNumber(item.impact_value),
    item.recommended_market || item.recommended_site || '-',
    item.signal_level === 'high' || item.signal_level === 'critical' ? '待确认' : '观察中',
    '查看建议',
  ])
  const tableRows = quotePurchaseRows.length ? quotePurchaseRows : (trendPurchaseRows.length ? trendPurchaseRows : recommendationRows)
  const columns = ['品名', '市场价(元/斤)', '建议采购价(元/斤)', '数量(斤)', '供应商', '状态', '操作']
  const description = quotePurchaseRows.length
    ? `已从当前商品报价记录生成 ${quotePurchaseRows.length} 条待确认采购动作，最低价供应商：${lowestQuote?.supplier_name || '待确认'}。`
    : (trendPurchaseRows.length
      ? '当前商品尚无供应商台账报价，已先承接趋势报价生成待确认采购动作。'
      : (recommendations.length ? `已生成 ${recommendations.length} 条采购建议。` : '等待采购建议或当前商品报价同步。'))

  return {
    kicker: '我的采购',
    title: '采购建议',
    description,
    action: '查看采购计划',
    metrics: [
      { label: '可采购报价', value: String(validQuotes.length), detail: validQuotes.length ? '当前能直接转采购确认的报价数' : '还没有可直接下单的报价', tone: validQuotes.length ? 'green' : 'warn' },
      { label: '等你确认', value: String((quotePurchaseRows.length || trendPurchaseRows.length) || recommendations.filter((item) => item.signal_level === 'high' || item.signal_level === 'critical').length), detail: quotePurchaseRows.length ? '先确认这些当前报价' : '先处理高风险/趋势建议', tone: 'warn' },
      { label: '最低可下单价', value: lowestQuote ? formatCurrency(lowestQuote.quote_price) : '-', detail: lowestQuote?.supplier_name || '还没有供应商可下单价', tone: lowestQuote ? 'green' : 'blue' },
      { label: '当前建议成本', value: formatCurrency(sumNumbers(recommendations.map((item) => item.estimated_cost))), detail: recommendations.length ? '按推荐口径估算的总成本' : '当前没有可估算成本', tone: 'blue' },
    ],
    tableTitle: quotePurchaseRows.length || trendPurchaseRows.length ? '当前商品待确认采购' : '采购任务列表',
    columns,
    tableRows: withEmptyRows(tableRows, columns),
    sideTitle: '采购建议',
    sideItems: withEmptySideItems((quotePurchaseRows.length ? validQuotes.slice(0, 4).map((item) => ({
      label: item === lowestQuote ? '最低' : '报价',
      title: item.supplier_name || '供应商报价',
      detail: `${item.product_name || item.price_identity_label || selectedProductName.value || '当前商品'} · ${formatCurrency(item.quote_price)} ${item.quote_unit || ''}`.trim(),
      tone: item === lowestQuote ? 'green' : 'blue',
    })) : recommendations.slice(0, 4).map((item) => ({
      label: item.signal_level,
      title: item.ingredient_name || item.identity_key || '采购建议',
      detail: item.reason_summary || formatRecommendedAction(item.recommended_action),
      tone: item.signal_level === 'high' || item.signal_level === 'critical' ? 'warn' : 'blue',
    })))),
    flowTitle: '采购动态',
    flow: withEmptyFlow((quotePurchaseRows.length ? validQuotes.slice(0, 4).map((item) => ({
      step: item === lowestQuote ? '最低' : '待确',
      text: `${item.supplier_name || '供应商'}：${formatCurrency(item.quote_price)} ${item.quote_unit || ''}，等待确认采购`,
    })) : recommendations.slice(0, 4).map((item) => ({
      step: String(Math.round(item.timing_score || 0)),
      text: `${item.ingredient_name || item.identity_key || '商品'}：${formatRecommendedAction(item.recommended_action, item.reason_summary || '建议已生成')}`,
    })))),
  }
})

const planModuleView = computed<ModuleView>(() => {







  const rows = props.planRows || []







  const columns = ['计划日期', '商品', '计划量', '预算价(元/斤)', '推荐供应商', '价格状态', '操作']







  return {







    kicker: '采购计划',







    title: '菜单采购计划',







    description: rows.length ? `按菜单用量生成 ${rows.length} 条计划明细。` : '等待菜单采购计划明细同步。',







    action: '生成计划',







    metrics: [







      { label: '计划明细', value: String(rows.length), detail: '菜单计划', tone: 'blue' },







      { label: '已执行', value: String(rows.filter((item) => /已|完成|执行/.test(item.price_status || '')).length), detail: rows.length ? `占比 ${formatPercent(rows.filter((item) => /已|完成|执行/.test(item.price_status || '')).length / rows.length)}` : '占比 0%', tone: 'green' },







      { label: '待采购', value: String(rows.filter((item) => !/已|完成|执行/.test(item.price_status || '')).length), detail: rows.length ? `占比 ${formatPercent(rows.filter((item) => !/已|完成|执行/.test(item.price_status || '')).length / rows.length)}` : '占比 0%', tone: 'warn' },







      { label: '预算金额', value: formatCurrency(sumNumbers(rows.map((item) => item.estimated_cost))), detail: '计划明细合计', tone: 'blue' },







    ],







    tableTitle: '计划明细',







    columns,







    tableRows: withEmptyRows(rows.slice(0, 8).map((item) => [







      currentDateLabel,







      item.ingredient_name || item.menu_name || '-',







      formatNumber(item.estimated_quantity),







      formatCurrency(item.reference_price),







      item.recommended_market || item.recommended_site || '-',







      item.price_status || '待确认',







      '查看计划',







    ]), columns),







    sideTitle: '今日待办',







    sideItems: withEmptySideItems((props.procurementRecommendations || []).slice(0, 4).map((item) => ({







      label: item.signal_level,







      title: item.ingredient_name || item.identity_key || '计划建议',







      detail: item.reason_summary || formatRecommendedAction(item.recommended_action),







      tone: item.signal_level === 'high' || item.signal_level === 'critical' ? 'warn' : 'blue',







    }))),







    flowTitle: '供应商协同',







    flow: withEmptyFlow(rows.slice(0, 4).map((item) => ({







      step: item.price_status || '计划',







      text: `${item.menu_name || '菜单'} / ${item.ingredient_name || '食材'}：${formatNumber(item.estimated_quantity)} ${item.quantity_unit || ''}`.trim(),







    }))),







  }







})















const reportsModuleView = computed<ModuleView>(() => {







  const rows = props.rows || []
  const hasRealRows = rows.length > 0







  const grouped = Array.from(rows.reduce((map, row) => {







    const category = inferMarketCategory(row)







    const existing = map.get(category) || { count: 0, prices: [] as number[], lows: [] as number[], sources: 0 }







    existing.count += 1







    if (row.average_price != null) existing.prices.push(Number(row.average_price))







    if (row.lowest_price != null) existing.lows.push(Number(row.lowest_price))







    existing.sources += Number(row.market_count || row.site_count || 0)







    map.set(category, existing)







    return map







  }, new Map<string, { count: number; prices: number[]; lows: number[]; sources: number }>()).entries())







  const columns = ['品类', '商品数', '平均价', '最低价', '报价源', '风险数', '主要来源', '状态']







  return {







    kicker: '数据报表',







    title: '菜价报表',







    description: `基于 ${rows.length} 条菜价和 ${props.sourceCoverageRows?.length || 0} 个来源生成。`,







    action: '导出报表',







    metrics: [







      { label: '汇总商品', value: String(rows.length), detail: '菜价汇总', tone: 'blue' },







      { label: '平均采购价', value: formatCurrency(averageNumbers(rows.map((item) => item.average_price))), detail: '平均价', tone: 'green' },







      { label: '风险信号', value: String(props.signalOverview?.alert_count || 0), detail: '价格提醒', tone: props.signalOverview?.alert_count ? 'warn' : 'green' },







      { label: '来源数量', value: String(props.sourceCoverageRows?.length || 0), detail: '数据来源配置', tone: 'blue' },







    ],







    tableTitle: '报表明细',







    columns,







    tableRows: withEmptyRows(grouped.map(([category, item]) => [







      category,







      String(item.count),







      formatCurrency(averageNumbers(item.prices)),







      formatCurrency(item.lows.length ? Math.min(...item.lows) : null),







      String(item.sources),







      String(signalItems.value.filter((signal) => inferMarketCategory(signal) === category).length),







      props.sourceCoverageRows?.find((source) => source.market_category === category)?.configured_name || props.sourceCoverageRows?.find((source) => source.market_category === category)?.source_name || '-',







      item.prices.length ? '已同步' : '待同步',







    ]), columns),







    sideTitle: '异常摘要',







    sideItems: hasRealRows ? withEmptySideItems(signalItems.value.slice(0, 4).map((item) => ({







      label: item.signal_level,







      title: item.product_name,







      detail: item.reason_summary || formatRecommendedAction(item.recommended_action),







      tone: item.signal_level === 'high' || item.signal_level === 'critical' ? 'warn' : 'blue',







    }))) : [],







    flowTitle: '报表目录',







    flow: hasRealRows ? withEmptyFlow((props.sourceCoverageRows || []).slice(0, 4).map((item) => ({







      step: item.latest_capture ? formatMonthDay(item.latest_capture) : '来源',







      text: `${item.configured_name || item.source_name || item.source_url}：${item.price_record_count || 0} 条记录，状态 ${item.status || (item.enabled === false ? '停用' : '启用')}`,







    }))) : [],







  }







})















const settingsModuleView = computed<ModuleView>(() => {







  const sources = props.sourceCoverageRows || []
  const failedSourceCount = sources.filter((item) => Number(item.failed_count || 0) > 0 || item.status === 'error' || item.last_failure).length
  const enabledSourceCount = sources.filter((item) => item.enabled !== false).length
  const crawlStatusLabel = props.crawlStatus?.is_running ? '运行中' : '空闲'







  const columns = ['来源', '渠道', '分类', '市场范围', '商品键', '价格记录', '最近同步', '状态']
  const hasRealSources = sources.length > 0







  return {







    kicker: '系统设置',







    title: '数据同步设置',







    description: sources.length ? `管理 ${sources.length} 个价格来源和同步状态。` : '这里设置价格来源，等待同步。',







    action: props.crawlStatus?.is_running ? '同步中' : '立即同步',







    metrics: [







      { label: '采集状态', value: crawlStatusLabel, detail: settingsCrawlProgressLabel.value, tone: props.crawlStatus?.is_running ? 'warn' : 'blue' },







      { label: '启用来源', value: String(enabledSourceCount), detail: `${sources.length} 个来源配置`, tone: 'green' },







      { label: '异常来源', value: String(failedSourceCount), detail: props.crawlStatus?.last_error ? '最近任务有异常' : '来源失败记录', tone: failedSourceCount || props.crawlStatus?.last_error ? 'warn' : 'green' },







      { label: '自动同步', value: settingsScheduleEnabled.value ? '开启' : '关闭', detail: settingsScheduleDetail.value, tone: settingsScheduleEnabled.value ? 'green' : 'blue' },







    ],







    tableTitle: '数据来源配置',







    columns,







    tableRows: withEmptyRows(sources.map((item) => [







      item.configured_name || item.source_name || item.source_url || '-',







      item.channel || item.strategy || '-',







      formatSourceCategoryPath(item),


      item.market_scope || '-',







      String(item.product_key_count || 0),







      String(item.price_record_count || 0),







      item.latest_capture ? formatShortDateTime(item.latest_capture) : '-',







      item.status || (item.enabled === false ? '停用' : '启用'),







    ]), columns),







    sideTitle: '采集异常与来源健康',







    sideItems: hasRealSources ? withEmptySideItems(sources.slice(0, 4).map((item) => ({







      label: item.enabled === false ? '停用' : '启用',







      title: item.configured_name || item.source_name || '数据来源',







      detail: item.last_failure || item.notes || `商品 ${item.product_key_count || 0} 个 · 价格记录 ${item.price_record_count || 0} 条`,







      tone: item.enabled === false || item.last_failure ? 'warn' : 'green',







    }))) : [],







    flowTitle: '系统同步状态',







    flow: hasRealSources ? withEmptyFlow([
      {
        step: props.crawlStatus?.is_running ? '运行' : '状态',
        text: settingsCrawlProgressLabel.value,
      },
      {
        step: '计划',
        text: settingsScheduleEnabled.value ? settingsScheduleDetail.value : '每日自动同步已关闭，可手动开启',
      },
      {
        step: '最近',
        text: `${settingsLastFinishedLabel.value} · ${settingsCrawlResultLabel.value}`,
      },
      ...sources.slice(0, 1).map((item) => ({
        step: item.latest_capture ? formatMonthDay(item.latest_capture) : '来源',
        text: `${item.configured_name || item.source_name || item.source_url}：${item.status || (item.enabled === false ? '停用' : '启用')}`,
      })),
    ]) : [],







  }







})















const sectionModuleViews = computed<Record<SectionId, ModuleView>>(() => ({
  summary: marketModuleView.value,
  trend: marketModuleView.value,
  alerts: alertModuleView.value,
  market: marketModuleView.value,
  suppliers: supplierModuleView.value,
  purchase: purchaseModuleView.value,
  quotes: quotesModuleView.value,
  plan: planModuleView.value,
  reports: reportsModuleView.value,
  settings: settingsModuleView.value,
}))

const moduleView = computed(() => sectionModuleViews.value[currentSection.value] || marketModuleView.value)















const currentDateLabel = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai' }).format(new Date())







const latestDataDateLabel = computed(() => {







  const candidates = [







    ...(props.sourceCoverageRows || []).map((item) => item.latest_capture),







    ...(props.trendRows || []).map((item) => item.captured_at),







    ...(props.supplierOverview?.recent_quotes || []).map((item) => item.quoted_at),







    props.supplierOverview?.summary?.latest_quoted_at,







    props.productSummary?.latest_captured_at,







  ]







    .map((value) => String(value || '').trim())







    .filter(Boolean)







    .sort()







  const latest = candidates.at(-1)







  if (!latest) return currentDateLabel







  const dateMatch = latest.match(/^(\d{4})-(\d{2})-(\d{2})/)







  return dateMatch ? `${dateMatch[2]}-${dateMatch[3]}` : latest.slice(0, 10)







})







const latestDataFilterLabel = computed(() => `最新数据 ${latestDataDateLabel.value}`)

function normalizeLocationMenuKey(value?: string | null) {
  return String(value || '')
    .trim()
    .replace(/本地市场/g, '')
    .replace(/自治区|自治州|特别行政区/g, '')
    .replace(/[省市区县盟旗]$/g, '')
    .trim()
    .toLowerCase()
}







const locationOptions = computed(() => {
  const baseLabel = String(props.locationLabel || '').trim()
  const seenKeys = new Set<string>()
  return [baseLabel, ...uniqueText(props.rows.map((row) => row.region_label))]
    .map((item) => String(item || '').trim())
    .filter(Boolean)
    .filter((item) => {
      const key = normalizeLocationMenuKey(item)
      if (!key || seenKeys.has(key)) return false
      seenKeys.add(key)
      return true
    })
})







const displayLocationLabel = computed(() => selectedLocationLabel.value || locationOptions.value[0] || props.locationLabel || '本地市场')
const primaryLocationOptions = computed(() => {
  const baseLabel = String(props.locationLabel || '').trim()
  const baseKey = normalizeLocationMenuKey(baseLabel)
  const preferred = locationOptions.value.filter((item) => {
    const key = normalizeLocationMenuKey(item)
    if (!key) return false
    if (item === baseLabel) return true
    if (item === '全国') return true
    return Boolean(baseKey && (key.includes(baseKey) || baseKey.includes(key)))
  })
  const fallback = locationOptions.value.filter((item) => !preferred.includes(item)).slice(0, 3)
  return uniqueText([...preferred, ...fallback], 6)
})
const overflowLocationOptions = computed(() => locationOptions.value.filter((item) => !primaryLocationOptions.value.includes(item)))















const summaryKpiRows = computed(() => filteredDisplayRows.value)

const kpis = computed(() => {



  const rows = summaryKpiRows.value



  const quoteTotal = props.rows.reduce((sum, row) => sum + Number(row.price_observation_count || row.market_count || row.site_count || 0), 0)



  const sourceTotal = props.sourceCoverageRows?.length || 0



  const comparableRows = rows.filter((row) => {
    const low = Number(row.lowest_price || 0)
    const high = Number(row.highest_price || 0)
    return low > 0 || high > 0
  })



  const opportunityRows = rows.filter((row) => {
    const low = Number(row.lowest_price || 0)
    const high = Number(row.highest_price || 0)
    return low > 0 && high > low
  })



  const riskCount = props.signalOverview?.alert_count ?? props.signalOverview?.top_risks?.length ?? 0



  const recommendationCount = props.procurementRecommendations?.length || 0



  const latestLabel = latestDataDateLabel.value && latestDataDateLabel.value !== '-' ? latestDataDateLabel.value : ''



  return [



    {
      label: '当前可选商品',
      value: rows.length ? String(rows.length) : '先筛选',
      detail: props.rows.length ? '按当前条件展示' : '等待行情同步',
      tone: 'blue',
    },



    {
      label: '低价机会',
      value: opportunityRows.length ? String(opportunityRows.length) : '去比价',
      detail: comparableRows.length ? `${comparableRows.length} 个商品可看高低价` : '打开商品看来源报价',
      tone: opportunityRows.length ? 'green' : 'blue',
    },



    {
      label: '待处理提醒',
      value: riskCount ? String(riskCount) : '先复核',
      detail: riskCount ? '异常价格/风险信号' : '暂无高风险预警',
      tone: riskCount ? 'warn' : 'green',
    },



    {
      label: '采购建议',
      value: recommendationCount ? String(recommendationCount) : '生成',
      detail: recommendationCount ? '系统已给出动作' : '先选商品再生成动作',
      tone: 'blue',
    },



  ]



})



const trendKpis = computed(() => {







  const rows = trendChartRows.value







  const fallback = selectedSummaryRow.value







  const currentPrices = rows







    .map((row) => Number(row.current_price))







    .filter((value) => !Number.isNaN(value))







  const min = currentPrices.length ? Math.min(...currentPrices) : fallback?.lowest_price ?? null







  const max = currentPrices.length ? Math.max(...currentPrices) : fallback?.highest_price ?? null







  const avg = currentPrices.length







    ? currentPrices.reduce((sum, value) => sum + value, 0) / currentPrices.length







    : fallback?.average_price ?? null







  const seriesCount = new Set(rows.map((row) => row.trend_series_key || row.trend_series_name || row.site_name).filter(Boolean)).size







  const latest = rows







    .map((row) => row.captured_at || '')







    .filter(Boolean)







    .sort()







    .at(-1)







  const fallbackCoverage = fallback ? Number(fallback.market_count || fallback.site_count || 0) : 0







  return [







    { label: '当前均价', value: formatNumber(avg), detail: isUsingTrendSnapshot.value ? '菜价快照' : latest ? formatShortDateTime(latest) : fallback ? '来自菜价汇总' : '等待走势数据', tone: 'blue' },







    { label: '最低价', value: formatNumber(min), detail: isUsingTrendSnapshot.value ? '菜价汇总最低价' : rows.length ? '走势最低点' : fallback ? '菜价汇总最低价' : '等待最低价', tone: 'green' },







    { label: '最高价', value: formatNumber(max), detail: isUsingTrendSnapshot.value ? '菜价汇总最高价' : rows.length ? '走势最高点' : fallback ? '菜价汇总最高价' : '等待最高价', tone: 'up' },







    { label: '覆盖市场', value: String(seriesCount || fallbackCoverage || 0), detail: isUsingTrendSnapshot.value ? '菜价快照已显示' : rows.length ? `${rows.length} 条走势记录` : fallback ? '菜价汇总覆盖' : '0 条走势记录', tone: 'blue' },














  ]







})















const sectionFilterOptions = computed<Record<SectionId, string[][]>>(() => {







  const rowSources = uniqueText([
    '莲菜网',
    'PFSC',
    'Chinaprice',
    '万邦国际',
    ...(props.sourceCoverageRows || []).map((row) => normalizeLiancaiSourceLabel(row.source_name || row.configured_name)),
    ...props.rows.flatMap((row) => splitJoinedText(row.source_names || row.source_display_names || row.lowest_price_site).map((item) => normalizeLiancaiSourceLabel(item))),
    ...(props.productOptions || []).map((item) => normalizeLiancaiSourceLabel(item.source_name)),
  ], 32)

  const liancaiTopOptions = uniqueText([
    ...(props.liancaiCategorySummaryItems || []).map((item) => item.liancai_top_category),
    ...props.rows.map((row) => row.liancai_top_category),
  ].filter(isMappedLiancaiCategoryLabel), 40)

  const liancaiSubOptions = uniqueText(
    [
      ...(props.liancaiCategorySummaryItems || [])
        .filter((item) => !String((currentSummaryLiancaiFilter.value as any).liancai_top_category || '').trim() || String(item.liancai_top_category || '').trim() === String((currentSummaryLiancaiFilter.value as any).liancai_top_category || '').trim())
        .map((item) => item.liancai_subcategory),
      ...props.rows
        .filter((row) => !String((currentSummaryLiancaiFilter.value as any).liancai_top_category || '').trim() || String(row.liancai_top_category || '').trim() === String((currentSummaryLiancaiFilter.value as any).liancai_top_category || '').trim())
        .map((row) => row.liancai_subcategory),
    ]
      .filter((item) => isMappedLiancaiCategoryLabel(item) && String(item).trim() !== '全部'),
    200,
  )
  const liancaiKeywordOptions = uniqueText(props.liancaiFacetOptions?.keywords || [], 200)
  const liancaiBrandOptions = uniqueText(props.liancaiFacetOptions?.brands || [], 200)
  const liancaiFacetOptions = uniqueText([
    ...liancaiKeywordOptions.map((item) => `品类:${item}`),
    ...liancaiBrandOptions.map((item) => `品牌:${item}`),
  ], 400)







  const rowCategories = uniqueText(props.rows.map((row) => inferMarketCategory(row)), 200)







  const summarySelections = filterSelections.value.summary || []
  const selectedSummarySource = formatFilterLabel((['全部来源', ...rowSources])[summarySelections[0] || 0] || '')
  const selectedSummaryTop = formatFilterLabel((['全部种类', ...liancaiTopOptions])[summarySelections[1] || 0] || '')
  const selectedSummarySub = formatFilterLabel((['全部子类', ...liancaiSubOptions])[summarySelections[2] || 0] || '')
  const selectedSummaryFacet = parseSummaryFacetOption((['全部细分', ...liancaiFacetOptions])[summarySelections[3] || 0] || '')
  const summaryProductRows = props.rows.filter((row) => {
    if (selectedSummarySource && !isNeutralFilter(selectedSummarySource)) {
      const sourceLabels = splitJoinedText(row.source_names || row.source_display_names || row.lowest_price_site).map((item) => normalizeLiancaiSourceLabel(item))
      if (!sourceLabels.some((label) => label.includes(selectedSummarySource) || selectedSummarySource.includes(label))) {
        return false
      }
    }
    if (selectedSummaryTop && !isNeutralFilter(selectedSummaryTop) && String(row.liancai_top_category || '').trim() !== selectedSummaryTop) return false
    if (selectedSummarySub && !isNeutralFilter(selectedSummarySub) && String(row.liancai_subcategory || '').trim() !== selectedSummarySub) return false
    if (selectedSummaryFacet.keyword) {
      const keyword = selectedSummaryFacet.keyword
      const rowKeyword = String(row.liancai_keyword || '').trim()
      if (rowKeyword !== keyword && !String(row.product_name || '').includes(keyword)) return false
    }
    if (selectedSummaryFacet.brand) {
      const brand = selectedSummaryFacet.brand
      const rowBrand = String(row.liancai_brand_name || '').trim()
      if (rowBrand !== brand && !String(row.product_name || '').includes(brand)) return false
    }
    return true
  })
  const rowProducts = uniqueText((summaryProductRows.length ? summaryProductRows : props.rows).map((row) => simplifyProductName(row.product_name)), 400)







  const rowDates = uniqueText([







    ...props.rows.flatMap((row) => splitJoinedText(row.captured_dates).map(formatDateFilterValue)),







    ...props.rows.map((row) => formatDateFilterValue(row.latest_captured_at)),







  ], 32)







  const optionProducts = uniqueText((props.productOptions || []).map((item) => item.price_identity_label), 400)







  const quoteSuppliers = uniqueText((props.supplierOverview?.recent_quotes || []).map((item) => item.supplier_name))







const sourceCategories = uniqueText((props.sourceCoverageRows || []).map((item) => item.market_category || item.market_scope))
  const categoryOptions = uniqueText([...liancaiTopOptions, ...liancaiSubOptions, ...liancaiKeywordOptions, ...liancaiBrandOptions, ...rowCategories], 400)







  return {







    summary: liancaiTopOptions.length
      ? [
          ['全部来源', ...rowSources],
          ['全部种类', ...liancaiTopOptions],
          ['全部子类', ...liancaiSubOptions],
          ['全部细分', ...liancaiFacetOptions],
          ['全部商品', ...rowProducts],
          ['全部日期', ...rowDates],
        ]
      : [['全部来源', ...rowSources], ['全部分类', ...categoryOptions], ['全部商品', ...rowProducts], ['全部日期', ...rowDates]],







    trend: [[`${selectedProductName.value || '全部商品'}⌄`, ...uniqueText([...optionProducts, ...rowProducts], 80)], ['全部来源', ...rowSources], ['最近7日']],







    alerts: [['全部来源', ...rowSources], ['全部分类', ...categoryOptions], ['全部商品', ...rowProducts], ['预警状态⌄', '待处理', '观察中', '已确认'], ['全部日期', ...rowDates]],







    market: [['全部来源', ...rowSources], ['全部分类⌄', ...sourceCategories, ...categoryOptions], ['运行状态⌄', '在线', '离线', '异常'], ['全部日期', ...rowDates]],







    suppliers: [['全部分类⌄', ...sourceCategories, ...rowCategories], ['报价单位⌄'], ['报价状态⌄', '启用', '无效', '待补报价'], [latestDataFilterLabel.value]],







    purchase: [['全部品类⌄', ...categoryOptions], ['采购状态⌄', '待确认', '观察中', '异常'], ['供应商⌄', ...quoteSuppliers, ...rowSources], [latestDataFilterLabel.value]],







    quotes: [['全部供应商⌄', ...quoteSuppliers], ['全部商品⌄', ...rowProducts], ['记录状态⌄', '有效', '无效'], [latestDataFilterLabel.value]],







    plan: [['计划周期：本周⌄'], ['全部品类⌄', ...categoryOptions], ['执行状态⌄', '待确认', '已执行', '待采购'], [latestDataFilterLabel.value]],







    reports: [['报表类型⌄', '行情日报', '价格波动分析', '供应商报价覆盖'], ['全部来源', ...rowSources], ['全部品类⌄', ...categoryOptions], ['近7日⌄'], [latestDataFilterLabel.value]],







    settings: [['全部分类⌄', '数据源', '权限', '告警'], ['全部组织'], ['启用状态⌄', '启用', '停用'], ['全部日期'], ['全部关键词']],







  }







})







const moduleHealthKpis = computed<Record<Exclude<SectionId, 'summary' | 'trend' | 'alerts'>, { label: string; value: string; detail: string; tone: string }>>(() => ({







  market: { label: '覆盖区域', value: String(new Set(props.rows.map((item) => item.region_label || item.lowest_price_site).filter(Boolean)).size || props.sourceCoverageRows?.length || 0), detail: '当前覆盖到的地区/来源', tone: 'blue' },







  suppliers: { label: '近24小时活跃', value: String(props.supplierOverview?.summary?.active_supplier_count || 0), detail: '最近有报价动作的供应商', tone: 'green' },







  purchase: { label: '高风险建议', value: String(props.procurementRecommendations?.filter((item) => item.signal_level === 'high' || item.signal_level === 'critical').length || 0), detail: '建议优先处理的采购异常任务', tone: 'warn' },







  quotes: { label: '最近记录', value: String(props.supplierOverview?.recent_quotes?.length || 0), detail: '供应商报价库', tone: 'green' },







  plan: { label: '风险项', value: String(props.planRows?.filter((item) => item.reference_price == null).length || 0), detail: '缺少参考价', tone: 'warn' },







  reports: { label: '数据完整度', value: props.rows.length ? `${Math.round((props.rows.filter((item) => item.average_price != null).length / props.rows.length) * 1000) / 10}%` : '0%', detail: '均价覆盖率', tone: 'green' },







  settings: { label: '来源配置', value: String(props.sourceCoverageRows?.length || 0), detail: '平台数据源', tone: 'green' },







}))

function shouldKeepSectionKpi(sectionId: SectionId, item: { label: string; value: string; detail: string; tone: string }) {
  const value = String(item.value || '').trim()
  const isZeroLike = value === '0' || value === '0%' || value === '-' || value === '¥0.00'
  if (sectionId === 'suppliers') {
    return ['待补报价', '最近有报价', '已接入供应商'].includes(item.label) || (!isZeroLike && item.label === '停用供应商')
  }
  if (sectionId === 'purchase' && isPurchaseModuleEmpty.value) {
    return false
  }
  if (sectionId === 'market') {
    return ['异常来源', '当前有返回', '已配置来源'].includes(item.label) || (!isZeroLike && item.label === '本轮报价记录')
  }
  return !isZeroLike || ['采集状态', '自动同步', '高风险建议', '待补报价', '等你确认', '异常来源'].includes(item.label)
}















function findTrendProductIdentityByFilterValue(value: string) {







  const label = formatFilterLabel(value)







  const matchedOption = (props.productOptions || []).find((item) => {







    const optionLabel = formatFilterLabel(item.price_identity_label)







    return optionLabel === label || simplifyProductName(optionLabel) === label || item.price_identity_key === label







  })







  if (matchedOption?.price_identity_key) return matchedOption.price_identity_key







  const matchedRow = props.rows.find((item) => {







    const rowLabel = formatFilterLabel(item.product_name)







    return rowLabel === label || simplifyProductName(rowLabel) === label







  })







  return matchedRow?.price_identity_key || ''







}















const topFilters = computed(() => {







  const options = sectionFilterOptions.value[currentSection.value]







  const selections = filterSelections.value[currentSection.value] || []







  return options.map((item, index) => item[selections[index] || 0] || item[0] || '')







})







const displayedTopFilters = computed(() => {
  const values = topFilters.value
  let visibleIndexes = values.map((_, index) => index)

  if (currentSection.value === 'summary') {
    visibleIndexes = [0, 1, 2, 4]
  } else if (currentSection.value === 'trend') {
    visibleIndexes = [0, 1, 2]
  }

  return visibleIndexes
    .filter((index) => values[index] != null)
    .map((index) => ({ index, value: values[index] }))
})

const showWorkbenchFilter = computed(() => currentSection.value !== 'suppliers')

const topKpis = computed(() => {
  if (currentSection.value === 'suppliers') return []







  if (currentSection.value === 'trend') return trendKpis.value







  if (currentSection.value === 'summary') return kpis.value







  if (currentSection.value === 'alerts') return alertSimpleCards.value







  return [...moduleView.value.metrics, moduleHealthKpis.value[currentSection.value as Exclude<SectionId, 'summary' | 'trend' | 'alerts'>]]
    .filter((item) => shouldKeepSectionKpi(currentSection.value, item))







})







const summaryStillBootstrapping = computed(() => Boolean(
  props.summaryLoading || (!props.rows.length && !(props.productOptions || []).length)
))

const summaryEmptyTitle = computed(() => (
  summaryStillBootstrapping.value
    ? '正在加载菜价'
    : '当前筛选无行情数据'
))







const summaryEmptyDetail = computed(() => (







  summaryStillBootstrapping.value







    ? '正在读取菜价和商品，请稍候。'







    : '请调整来源、分类、商品或日期，也可以点击刷新。'







))







const trendEmptyTitle = computed(() => (props.trendLoading ? '正在加载价格走势' : '当前商品暂无走势数据'))







const trendEmptyDetail = computed(() => (







  props.trendLoading







    ? '正在读取趋势、供应商报价和市场来源。'







    : `当前为近 ${chartRange.value} 日视图。选择其他商品或刷新后，会展示均价、最低价和最新报价点。`







))







const allModuleTableRows = computed(() => moduleView.value.tableRows.filter((row) => !isEmptyModuleRow(row)))







const filteredModuleTableRows = computed(() => allModuleTableRows.value.filter((row) => rowMatchesActiveFilters(row, currentSection.value)))







const moduleTableCount = computed(() => filteredModuleTableRows.value.length)







const moduleTableRows = computed(() => paginateRows(filteredModuleTableRows.value, currentSection.value))







const moduleSideItems = computed(() => moduleView.value.sideItems.filter((item) => !isEmptyModuleSideItem(item)))







const moduleFlowItems = computed(() => moduleView.value.flow.filter((item) => !isEmptyModuleFlowItem(item)))







const moduleHasTableRows = computed(() => filteredModuleTableRows.value.length > 0)







const moduleHasSideItems = computed(() => moduleSideItems.value.length > 0)







const moduleHasFlowItems = computed(() => moduleFlowItems.value.length > 0)
const isPurchaseModuleEmpty = computed(() => currentSection.value === 'purchase' && !moduleHasTableRows.value && !moduleHasSideItems.value && !moduleHasFlowItems.value)
const isQuotesModuleEmpty = computed(() => currentSection.value === 'quotes' && !moduleHasTableRows.value)

const quoteEmptyActionCards = computed(() => {
  const focusedIdentityKey = props.selectedIdentityKey || selectedSummaryRow.value?.price_identity_key || ''
  return [
    {
      label: '当前商品报价',
      value: String(focusedSupplierQuotes.value.length),
      detail: focusedSupplierQuotes.value.length ? '已有供应商报价可复核' : '当前商品暂无供应商报价',
      action: '看趋势',
      section: 'trend' as SectionId,
      identityKey: focusedIdentityKey,
    },
    {
      label: '趋势可承接',
      value: String(trendQuoteRows.value.length),
      detail: trendQuoteRows.value.length ? '可先从趋势报价转采购动作' : '暂无趋势报价可承接',
      action: '单品趋势',
      section: 'trend' as SectionId,
      identityKey: focusedIdentityKey,
    },
    {
      label: '供应商报价库',
      value: String(props.supplierOverview?.summary?.total_quote_count || 0),
      detail: props.supplierOverview?.summary?.latest_quoted_at
        ? `最近 ${formatShortDateTime(props.supplierOverview.summary?.latest_quoted_at)}`
        : '等待供应商提交报价',
      action: '报价后台',
      section: 'quotes' as SectionId,
      identityKey: '',
    },
  ]
})

const quoteEmptyWorkflowRows = computed(() => [
  selectedProductName.value ? `${selectedProductName.value} 当前未命中供应商报价记录。` : '当前筛选条件未命中供应商报价记录。',
  trendQuoteRows.value.length ? `已有 ${trendQuoteRows.value.length} 条历史报价，可先复核价格走势。` : '历史行情和供应商报价都为空时，只保留待补报价。',
  '补齐供应商、报价、单位和状态后，报价记录表格会自动展开。',
])

const purchaseEmptyActions = computed(() => {
  const identityKey = props.selectedIdentityKey || selectedSummaryRow.value?.price_identity_key || ''
  return [
    {
      step: '01',
      label: '先选采购商品',
      detail: selectedProductName.value ? `当前商品：${selectedProductName.value}` : '从汇总行情里选一个采购商品。',
      action: '去汇总选品',
      section: 'summary' as SectionId,
      identityKey: '',
    },
    {
      step: '02',
      label: '补供应商报价',
      detail: '没有可下单报价时，不展开采购表格，先进入报价记录补价。',
      action: '补报价',
      section: 'quotes' as SectionId,
      identityKey,
    },
    {
      step: '03',
      label: '生成采购计划',
      detail: '报价链补齐后，再回采购计划按菜单和数量生成执行动作。',
      action: '采购计划',
      section: 'plan' as SectionId,
      identityKey: '',
    },
  ]
})

const purchaseEmptyBlockers = computed(() => [
  focusedSupplierQuotes.value.length ? `当前商品已有 ${focusedSupplierQuotes.value.length} 条报价，但还没有有效可采购报价。` : '当前商品没有供应商可下单报价。',
  trendChartRows.value.length ? `已有 ${trendChartRows.value.length} 个价格点，可先复核价格方向。` : '历史行情还未形成可承接价格点。',
  props.planRows?.length ? `采购计划已有 ${props.planRows.length} 条明细，等待报价补齐后执行。` : '采购计划暂未生成可执行明细。',
])

const moduleEmptyTitle = computed(() => {
  if (currentSection.value === 'settings') {
    if (!(props.sourceCoverageRows || []).length) return '当前没有价格来源'
    if (!moduleTableCount.value && allModuleTableRows.value.length > 0) return '当前筛选未命中来源'
  }
  return '暂无可展示数据'
})

const moduleEmptyDetail = computed(() => {
  if (currentSection.value === 'settings') {
    if (!(props.sourceCoverageRows || []).length) {
      return '当前没有同步到价格来源，请先检查同步状态、账号权限或服务状态。'
    }
    if (!moduleTableCount.value && allModuleTableRows.value.length > 0) {
      return `当前价格来源 ${allModuleTableRows.value.length} 条，但被顶部筛选条件过滤为 0 条。请重置筛选后再看。`
    }
  }
  return `刷新或系统同步后会展示${moduleView.value.tableTitle}记录。`
})







const moduleHasChartData = computed(() => {
  if (currentSection.value === 'market') return marketTrendSeries.value.length > 0
  return moduleHasTableRows.value || moduleHasSideItems.value || moduleHasFlowItems.value
})







const isGeneratedModuleLayout = computed(() => isGeneratedModuleSection(currentSection.value))

const moduleLayout = computed(() => getModuleLayout(currentSection.value))







const moduleLayoutClass = computed(() => `pcw-module-layout-${moduleLayout.value}`)







const moduleDensityClass = computed(() => getModuleDensityClass(currentSection.value))







const moduleCommandMetrics = computed(() => moduleView.value.metrics.slice(0, 3))







const moduleBriefItems = computed(() => {







  const firstSide = moduleSideItems.value[0]







  const firstFlow = moduleFlowItems.value[0]







  const tableCount = moduleTableCount.value







  const sectionBriefs: Record<Exclude<SectionId, 'summary' | 'trend' | 'alerts'>, Array<{ label: string; text: string }>> = {







    market: [







      { label: '巡检重点', text: firstSide ? firstSide.detail : '先看异常市场和失败来源，再复核报价覆盖。' },







      { label: '当前动作', text: firstFlow ? firstFlow.text : '刷新行情后按来源状态补齐市场覆盖。' },







      { label: '记录范围', text: `${tableCount} 条市场/来源记录可用` },







    ],







    suppliers: [







      { label: '协作重点', text: firstSide ? firstSide.detail : '优先找出启用供应商里的报价缺口。' },







      { label: '跟进动作', text: firstFlow ? firstFlow.text : '进入后台补齐联系人、主营分类和报价单位。' },







      { label: '覆盖范围', text: `${tableCount} 条供应商报价记录` },







    ],







    purchase: [







      { label: '执行重点', text: firstSide ? firstSide.detail : '先确认高风险采购建议，再处理观察项。' },







      { label: '推进动作', text: firstFlow ? firstFlow.text : '把采购建议转成菜单采购计划。' },







      { label: '任务池', text: `${tableCount} 条待处理采购任务` },







    ],







    quotes: [







      { label: '核验重点', text: firstSide ? firstSide.detail : '先过滤无效报价，再核对供应商和商品。' },







      { label: '报价动态', text: firstFlow ? firstFlow.text : '等待供应商报价同步。' },







      { label: '台账范围', text: `${tableCount} 条报价记录` },







    ],







    plan: [







      { label: '排产重点', text: firstSide ? firstSide.detail : '先处理缺参考价和待采购明细。' },







      { label: '协同动作', text: firstFlow ? firstFlow.text : '按菜单用量推送供应商协同。' },







      { label: '计划池', text: `${tableCount} 条计划明细` },







    ],







    reports: [







      { label: '洞察重点', text: firstSide ? firstSide.detail : '优先看品类风险、均价覆盖和来源完整度。' },







      { label: '报表动作', text: firstFlow ? firstFlow.text : '导出前先确认数据同步状态。' },







      { label: '分析范围', text: `${tableCount} 个品类分组` },







    ],







    settings: [







      { label: '运维重点', text: firstSide ? firstSide.detail : '先处理停用、失败和无最近同步的来源。' },







      { label: '配置动作', text: firstFlow ? firstFlow.text : '在当前页直接同步数据源并设置每日同步。' },







      { label: '配置范围', text: `${tableCount} 个来源配置项` },







    ],







  }







  return sectionBriefs[currentSection.value as Exclude<SectionId, 'summary' | 'trend' | 'alerts'>] || []







})







const moduleTablePageCount = computed(() => getPageCount(filteredModuleTableRows.value.length))







const modulePaginationPages = computed(() => buildPaginationPages(moduleTablePageCount.value, tablePage.value[currentSection.value] || 1))















const quoteRows = computed(() => {







  const rows = props.supplierOverview?.recent_quotes || []







  return rows.slice(0, 3).map((item) => ({







    tag: item.comparison_label || (item.status === 'invalid' ? '需复核' : '最新报价'),







    supplier: item.supplier_name || '未命名供应商',







    price: `${formatNumber(item.quote_price)} ${item.quote_unit || ''}`.trim(),







  }))







})















const timelineRows = computed(() => {







  const quoteEvents = (props.supplierOverview?.recent_quotes || []).slice(0, 4).map((item) => ({







    time: item.quoted_at ? formatTimeOnly(item.quoted_at) : '--:--',







    text: `${item.supplier_name || '供应商'} ${item.product_name || item.price_identity_label || '商品'} 报价 ${formatNumber(item.quote_price)} ${item.quote_unit || ''}`.trim(),







  }))







  if (quoteEvents.length) return quoteEvents

  return filteredDisplayRows.value.slice(0, 4).map((item) => ({
    time: item.source || item.capturedDate || '菜价',
    text: `${item.name} 均价 ${item.avg}，最低价 ${item.low}`,
  }))







})















const signalItems = computed<SignalInsightItem[]>(() => [







  ...(props.signalOverview?.top_risks || []),







  ...(props.signalOverview?.top_opportunities || []),







])















const alerts = computed(() => signalItems.value.slice(0, 3).map((item) => ({







  name: `${item.product_name} · ${item.recommended_market || item.recommended_site || '本地市场'}`,







  value: `${Math.round(item.risk_score)} 风险分`,







  detail: formatRecommendedAction(item.recommended_action),







  tone: item.signal_level === 'high' || item.signal_level === 'critical' ? 'rise' : item.trend_label === '下降' ? 'fall' : 'warn',







})))















const messageItems = computed<Array<{ label: string; title: string; detail: string; tone: string; section: MessageSection }>>(() => {







  const signalMessages = signalItems.value.slice(0, 4).map((item) => ({







    label: formatSignalType(item),







    title: item.product_name || '价格信号',







    detail: item.reason_summary || formatRecommendedAction(item.recommended_action, '点击查看价格预警'),







    tone: item.signal_level === 'high' || item.signal_level === 'critical' ? 'warn' : 'blue',







    section: 'alerts' as MessageSection,







  }))







  const quoteMessages = (props.supplierOverview?.recent_quotes || []).slice(0, 3).map((item) => ({







    label: '供应商报价',







    title: item.supplier_name || '供应商',







    detail: `${item.product_name || item.price_identity_label || '商品'} ${formatNumber(item.quote_price)} ${item.quote_unit || ''}`.trim(),







    tone: item.status === 'invalid' || item.invalidated_at ? 'warn' : 'green',







    section: 'quotes' as MessageSection,







  }))







  const sourceMessages = (props.sourceCoverageRows || [])







    .filter((item) => Number(item.failed_count || 0) > 0 || item.last_failure)







    .slice(0, 2)







    .map((item) => ({







      label: '数据源异常',







      title: item.configured_name || item.source_name || item.source_url || '数据来源',







      detail: item.last_failure || `失败 ${item.failed_count || 0} 次`,







      tone: 'warn',







      section: 'market' as MessageSection,







    }))







  const messages = [...signalMessages, ...quoteMessages, ...sourceMessages]







  return messages.length ? messages.slice(0, 8) : [{







    label: '系统状态',







    title: '暂无未读业务提醒',







    detail: '预警、报价、数据源异常会在这里集中展示。',







    tone: 'green',







    section: 'summary' as MessageSection,







  }]







})















type AlertTaskRow = {
  identityKey?: string
  name: string
  market: string
  type: string
  value: string
  rule: string
  owner: string
  state: string
  tone: string
  stateTone: string
  thumb: string
  riskValue: number
}

const configuredAlertTaskRows = computed(() => {
  return productAlertRules.value
    .map((rule) => {
      const hit = buildProductAlertHit(
        rule,
        props.rows,
        rule.identityKey === props.selectedIdentityKey ? trendChartRows.value : [],
      )
      if (!hit) return null
      return {
        identityKey: rule.identityKey,
        name: hit.productLabel,
        market: hit.market,
        type: hit.type,
        value: formatNumber(hit.currentPrice),
        rule: hit.rule,
        owner: '先看同品走势，再决定是否处理',
        state: hit.triggered ? '待处理' : '观察中',
        tone: hit.tone,
        stateTone: hit.triggered ? 'pending' : 'watch',
        thumb: inferThumbTone(hit.productLabel),
        riskValue: hit.triggered ? 88 : 42,
      }
    })
    .filter((item): item is AlertTaskRow => Boolean(item))







  const settings = normalizeAlertSettings(alertSettings.value)







  const currentPrice = Number(trendChartRows.value.at(-1)?.current_price ?? selectedSummaryRow.value?.average_price ?? 0)







  if (!currentPrice) return []







  const productName = selectedProductName.value || selectedSummaryRow.value?.product_name || '当前商品'







  const marketName = selectedSummaryRow.value?.region_label || selectedSummaryRow.value?.lowest_price_site || '本地市场'







  const rows: Array<{







    identityKey?: string






    name: string







    market: string







    type: string







    value: string







    rule: string







    owner: string







    state: string







    tone: string







    stateTone: string







    thumb: string







    riskValue: number







  }> = []







  if (settings.maxPrice > 0) {







    const triggered = currentPrice >= settings.maxPrice







    rows.push({



      identityKey: settings.identityKey || props.selectedIdentityKey || '',



      name: productName,







      market: marketName,







        type: '高于目标价',







      value: formatNumber(currentPrice),







        rule: `当前 ${formatNumber(currentPrice)} 元，已经高于你设定的目标价 ${formatNumber(settings.maxPrice)} 元`,







        owner: '先看低价市场，再决定是否立即下单',







      state: triggered ? '待处理' : '观察中',







      tone: 'up',







      stateTone: triggered ? 'pending' : 'watch',







      thumb: inferThumbTone(productName),







      riskValue: triggered ? 88 : 42,







    })







  }







  if (settings.minPrice > 0) {







    const triggered = currentPrice <= settings.minPrice







    rows.push({



      identityKey: settings.identityKey || props.selectedIdentityKey || '',



      name: productName,







      market: marketName,







        type: '低于补货价',







      value: formatNumber(currentPrice),







        rule: `当前 ${formatNumber(currentPrice)} 元，已经低于你设定的补货参考价 ${formatNumber(settings.minPrice)} 元`,







        owner: '可先补一轮货，再确认库存和供应稳定性',







      state: triggered ? '待处理' : '观察中',







      tone: 'down',







      stateTone: triggered ? 'pending' : 'watch',







      thumb: inferThumbTone(productName),







      riskValue: triggered ? 82 : 38,







    })







  }







  return rows







})















const signalAlertTaskRows = computed(() => signalItems.value.map((item) => ({



  identityKey: item.identity_key || '',



  name: item.product_name,







  market: item.recommended_market || item.recommended_site || '本地市场',







  type: formatSignalType(item),







  value: item.current_price != null || item.current_lowest_price != null || item.average_price != null
    ? formatNumber(Number(item.current_price ?? item.current_lowest_price ?? item.average_price))
    : `${Math.round(item.risk_score)} 分`,







  rule: item.reason_summary,







  owner: formatRecommendedAction(item.recommended_action),







  state: item.signal_level === 'high' || item.signal_level === 'critical' ? '待处理' : '观察中',







  tone: item.trend_label === '上涨' ? 'up' : item.trend_label === '下降' ? 'down' : 'warn',







  stateTone: item.signal_level === 'high' || item.signal_level === 'critical' ? 'pending' : 'watch',







  thumb: inferThumbTone(item.product_name),







  riskValue: Math.min(100, Math.max(0, Math.round(item.risk_score || 0))),







})))















const marketAlertTaskRows = computed<AlertTaskRow[]>(() => {
  const rows: AlertTaskRow[] = []
  const seen = new Set<string>()

  for (const row of props.rows) {
    const productName = simplifyProductName(row.product_name)
    if (!productName || productName === '未命名商品') continue

    const averagePrice = Number(row.average_price)
    const lowestPrice = Number(row.lowest_price)
    const highestPrice = Number(row.highest_price)
    const hasAveragePrice = Number.isFinite(averagePrice) && averagePrice > 0
    const hasLowestPrice = Number.isFinite(lowestPrice) && lowestPrice > 0
    const hasHighestPrice = Number.isFinite(highestPrice) && highestPrice > 0
    const sourceCount = Number(row.market_count ?? row.site_count ?? 0)
    const sourceLabel = summarizeSourceNames(row.source_names || row.source_display_names || row.lowest_price_site || row.region_label)
    const lowestSite = row.lowest_price_site || sourceLabel
    const highestSite = row.highest_price_site || sourceLabel
    const spread = hasLowestPrice && hasHighestPrice ? highestPrice - lowestPrice : 0
    const spreadRate = hasLowestPrice && spread > 0 ? spread / lowestPrice : 0
    const averageLowRate = hasAveragePrice && hasLowestPrice ? (averagePrice - lowestPrice) / lowestPrice : 0
    const rowKey = row.price_identity_key || productName

    let alertRow: AlertTaskRow | null = null
    if (spreadRate >= 0.35 && sourceCount >= 2) {
      alertRow = {
        identityKey: row.price_identity_key || '',
        name: productName,
        market: sourceLabel,
        type: '跨市场价差偏大',
        value: `${formatNumber(lowestPrice)} - ${formatNumber(highestPrice)}`,
        rule: `${lowestSite} 和 ${highestSite} 相差 ${formatNumber(spread)} 元，建议先确认低价来源是否稳定`,
        owner: `先看 ${lowestSite} 的供货稳定性，再决定是否切换来源`,
        state: '待处理',
        tone: 'warn',
        stateTone: 'pending',
        thumb: inferThumbTone(row),
        riskValue: Math.min(100, Math.max(50, Math.round(spreadRate * 100))),
      }
    } else if (averageLowRate >= 0.2 && sourceCount >= 2) {
      alertRow = {
        identityKey: row.price_identity_key || '',
        name: productName,
        market: sourceLabel,
        type: '出现低价机会',
        value: formatNumber(lowestPrice),
        rule: `最低价比均价低 ${formatNumber(averagePrice - lowestPrice)} 元，可以先评估是否补货`,
        owner: `优先联系 ${lowestSite}，再确认今天是否适合补货`,
        state: '观察中',
        tone: 'down',
        stateTone: 'watch',
        thumb: inferThumbTone(row),
        riskValue: Math.min(100, Math.max(35, Math.round(averageLowRate * 100))),
      }
    } else if (hasAveragePrice && hasLowestPrice && hasHighestPrice && spread > 0) {
      alertRow = {
        identityKey: row.price_identity_key || '',
        name: productName,
        market: sourceLabel,
        type: '今天有多个报价可比',
        value: formatNumber(averagePrice),
        rule: `今日最低 ${formatNumber(lowestPrice)}，最高 ${formatNumber(highestPrice)}，采购前建议先复核最低价来源`,
        owner: lowestSite ? `先看 ${lowestSite}，再决定采购去向` : '先复核最低价来源，再决定采购去向',
        state: '观察中',
        tone: 'blue',
        stateTone: 'watch',
        thumb: inferThumbTone(row),
        riskValue: Math.min(100, Math.max(20, Math.round(spreadRate * 100))),
      }
    }

    if (!alertRow) continue
    const duplicateKey = `${rowKey}|${alertRow.type}|${alertRow.value}`
    if (seen.has(duplicateKey)) continue
    seen.add(duplicateKey)
    rows.push(alertRow)
  }

  return rows
    .sort((left, right) => right.riskValue - left.riskValue)
    .slice(0, 80)
})

function applyAlertDisposition(row: AlertTaskRow): AlertTaskRow {
  const record = alertDispositionRecords.value.find((item) => item.key === buildAlertDispositionKey(row))
  if (!record) return row
  if (record.action === 'quote') {
    return {
      ...row,
      owner: '已生成补价任务，等待供应商报价回写',
      state: '补价中',
      stateTone: 'watch',
    }
  }
  return {
    ...row,
    owner: record.status,
    state: record.status,
    stateTone: 'done',
  }
}

const allAlertTaskRows = computed(() => {
  const rows: AlertTaskRow[] = []
  const seen = new Set<string>()

  for (const rawRow of [...configuredAlertTaskRows.value, ...signalAlertTaskRows.value, ...marketAlertTaskRows.value]) {
    const row = applyAlertDisposition(rawRow)
    const key = `${row.name}|${row.type}|${row.value}`
    if (seen.has(key)) continue
    seen.add(key)
    rows.push(row)
  }

  return rows
})







const filteredAlertTaskRows = computed(() => allAlertTaskRows.value.filter((row) => rowMatchesActiveFilters([







  row.name,







  row.market,







  row.type,







  row.rule,







  row.owner,







  row.state,







], 'alerts')))







const alertTaskTotal = computed(() => filteredAlertTaskRows.value.length)







const alertTaskRows = computed(() => paginateRows(filteredAlertTaskRows.value, 'alerts'))







const alertPageCount = computed(() => getPageCount(alertTaskTotal.value))







const alertPaginationPages = computed(() => buildPaginationPages(alertPageCount.value, tablePage.value.alerts || 1))







const alertPendingCount = computed(() => filteredAlertTaskRows.value.filter((row) => row.stateTone === 'pending').length)







const alertWatchCount = computed(() => filteredAlertTaskRows.value.filter((row) => row.stateTone === 'watch').length)







const alertDoneCount = computed(() => filteredAlertTaskRows.value.filter((row) => row.stateTone === 'done').length)







const alertRuleCount = computed(() => {
  return productAlertRules.value.filter((item) => item.enabled && (Number(item.maxPrice) > 0 || Number(item.minPrice) > 0)).length







  const settings = normalizeAlertSettings(alertSettings.value)







  return [







    settings.highRiskScore,







    settings.watchRiskScore,







    settings.maxPrice,







    settings.minPrice,







  ].filter((item) => Number(item) > 0).length







})







const alertRuleCoverage = computed(() => (alertRuleCount.value ? `${alertRuleCount.value} 条本机规则启用` : '等待规则启用'))







const alertQueueSummary = computed(() => (







  alertTaskTotal.value







    ? `${alertPendingCount.value} 条待处理，${alertWatchCount.value} 条观察中`







    : '当前筛选下暂无预警任务'







))







const alertQueuePills = computed(() => [







  { label: '待处理', value: String(alertPendingCount.value), tone: alertPendingCount.value ? 'warn' : 'green' },







  { label: '观察中', value: String(alertWatchCount.value), tone: 'blue' },







  { label: '已确认', value: String(alertDoneCount.value), tone: 'green' },







  { label: '当前页', value: `${alertTaskRows.value.length}/${alertTaskTotal.value}`, tone: 'muted' },







])

const alertSimpleSummary = computed(() => (
  alertTaskTotal.value
    ? `共有 ${alertTaskTotal.value} 个菜品需要关注，先看“待处理”，再决定今天的采购动作。`
    : '今天没有需要你立即处理的价格提醒。'
))

const alertSimpleCards = computed(() => [
  {
    label: '需要处理',
    value: String(alertPendingCount.value),
    detail: alertPendingCount.value ? '建议先处理这些商品' : '暂无紧急项',
    tone: alertPendingCount.value ? 'warn' : 'green',
  },
  {
    label: '涨价提醒',
    value: String(filteredAlertTaskRows.value.filter((row) => row.tone === 'up').length),
    detail: '可能直接抬高今天的采购成本',
    tone: 'danger',
  },
  {
    label: '降价提醒',
    value: String(filteredAlertTaskRows.value.filter((row) => row.tone === 'down').length),
    detail: '如果库存合适，可考虑先补一轮货',
    tone: 'green',
  },
  {
    label: '先放观察',
    value: String(alertWatchCount.value),
    detail: '先放观察池，晚点再看',
    tone: 'blue',
  },
])







const alertCommandCards = computed(() => [







  {







    label: '预警队列',







    value: String(alertTaskTotal.value),







    detail: alertTaskTotal.value ? '按当前筛选聚合' : '暂无待展示任务',







    tone: alertPendingCount.value ? 'warn' : 'green',







  },







  {







    label: '高优先级',







    value: String(priorityAlerts.value.length),







    detail: priorityAlerts.value.length ? '建议优先处置' : '暂无高风险项',







    tone: priorityAlerts.value.length ? 'danger' : 'green',







  },







  {







    label: '建议动作',







    value: String(props.signalOverview?.recommended_actions?.length || 0),







    detail: props.signalOverview?.recommended_actions?.length ? '已有处理建议' : '等待动作建议',







    tone: 'blue',







  },







  {







    label: '规则覆盖',







    value: String(alertRuleCount.value),







    detail: alertRuleCoverage.value,







    tone: 'muted',







  },







])







const alertWorkflowCards = computed(() => [







  {







    label: '识别',







    value: String(signalItems.value.length || props.signalOverview?.alert_count || 0),







    detail: hasAlertSignals.value ? '已有价格提醒' : '等待价格提醒',







    tone: hasAlertSignals.value ? 'blue' : 'muted',







  },







  {







    label: '分派',







    value: String(alertPendingCount.value),







    detail: alertPendingCount.value ? '需要负责人确认' : '暂无待分派',







    tone: alertPendingCount.value ? 'warn' : 'green',







  },







  {







    label: '复核',







    value: String(alertWatchCount.value),







    detail: '低风险进入观察池',







    tone: 'blue',







  },







])















const priorityAlerts = computed(() => signalItems.value.slice(0, 4).map((item) => ({







  title: `${item.product_name} · ${item.recommended_market || item.recommended_site || '本地市场'}`,







  type: formatRecommendedAction(item.recommended_action),







  detail: item.reason_summary,







  time: item.latest_captured_at ? formatTimeOnly(item.latest_captured_at) : '--:--',







  tone: item.trend_label === '上涨' ? 'up' : item.trend_label === '下降' ? 'down' : 'warn',







})))















const alertRules = computed(() => (props.signalOverview?.recommended_actions || []).slice(0, 3).map((item, index) => ({







  icon: String(index + 1),







  type: item.title,







  rule: item.description,







  tone: index === 0 ? 'up' : index === 1 ? 'down' : 'warn',







})))















const alertRecords = computed(() => [
  ...alertDispositionRecords.value,
  ...(props.signalOverview?.recommended_actions || []).slice(0, Math.max(0, 4 - alertDispositionRecords.value.length)).map((item, index) => ({







  time: item.confidence == null ? '--' : `${Math.round(item.confidence)}%`,







  text: item.description,







  status: formatRecommendedAction(item.action, '待确认'),







  tone: index === 0 ? 'watch' : 'done',







})),
])















const hasAlertSignals = computed(() => signalItems.value.length > 0 || Number(props.signalOverview?.alert_count || 0) > 0)















const focusedSignals = computed(() => signalItems.value.filter((item) => item.identity_key === props.selectedIdentityKey || item.product_name === selectedProductName.value))















const trendReadinessCards = computed(() => {







  const fallback = selectedSummaryRow.value







  const latestQuote = focusedSupplierQuotes.value[0]







  const signal = focusedSignals.value[0]







  return [







    {







      label: '行情快照',







      value: formatNumber(fallback?.average_price),







      detail: fallback ? `${fallback.region_label || fallback.lowest_price_site || '本地市场'} · ${fallback.market_count || fallback.site_count || 0} 个报价源` : '等待菜价汇总',







      tone: 'blue',







    },







    {







      label: '供应商报价',







      value: String(focusedSupplierQuotes.value.length),







      detail: latestQuote ? `${latestQuote.supplier_name || '供应商'} ${formatNumber(latestQuote.quote_price)} ${latestQuote.quote_unit || ''}`.trim() : '暂无供应商报价',







      tone: focusedSupplierQuotes.value.length ? 'green' : 'muted',







    },







    {







      label: '价格变化',







      value: focusedSignals.value.length ? `${focusedSignals.value.length} 条` : '正常',







      detail: signal?.reason_summary || '当前商品未触发高风险信号',







      tone: focusedSignals.value.length ? 'warn' : 'green',







    },







  ]







})















const trendQuoteRows = computed(() => {







  const trendRows = (props.trendRows || []).slice(0, 6).map((item) => [







    item.source_name || item.trend_series_name || item.site_name || '-',







    item.market_name || item.region_label || item.city || '-',







    formatNumber(item.current_price),







    item.captured_at ? formatTimeOnly(item.captured_at) : '--',







  ])







  if (trendRows.length) return trendRows







  return focusedSupplierQuotes.value.slice(0, 6).map((item) => [







    item.supplier_name || '未命名供应商',







    item.market_scope || item.market_category || item.channel || '供应商报价',







    `${formatNumber(item.quote_price)} ${item.quote_unit || ''}`.trim(),







    item.quoted_at ? formatTimeOnly(item.quoted_at) : '--',







  ])







})















const trendMarketRows = computed(() => {







  const trendRows = (props.trendRows || []).slice(0, 6).map((item) => [







    item.source_name || item.trend_series_name || item.site_name || '-',







    formatNumber(item.current_price),







    item.source_tier || '-',







    item.captured_at ? formatTimeOnly(item.captured_at) : '--',







    item.source_name || item.site_name || '-',







  ])







  if (trendRows.length) return trendRows







  return focusedMarketRows.value.slice(0, 6).map((item) => [







    summarizeSourceNames(item.source_names || item.source_display_names || item.lowest_price_site),







    formatNumber(item.average_price ?? item.lowest_price),







    item.market_count || item.site_count ? '菜价汇总' : '待补来源',







    currentDateLabel,







    `${item.market_count || item.site_count || 0} 个报价源`,







  ])







})















const trendDynamics = computed(() => {







  const trendEvents = (props.trendRows || []).slice(0, 5).map((item) => ({







    time: item.captured_at ? formatTimeOnly(item.captured_at) : '--:--',







    market: item.source_name || item.site_name || item.market_name || item.region_label || '价格来源',







    text: `${item.product_name || selectedProductName.value || '商品'} 报价 ${formatNumber(item.current_price)}，来源 ${item.source_name || item.source_tier || '价格来源'}`,







  }))







  if (trendEvents.length) return trendEvents







  const quoteEvents = focusedSupplierQuotes.value.slice(0, 3).map((item) => ({







    time: item.quoted_at ? formatTimeOnly(item.quoted_at) : '--:--',







    market: item.market_scope || item.market_category || '供应商报价',







    text: `${item.supplier_name || '供应商'} 提交 ${item.product_name || item.price_identity_label || selectedProductName.value || '商品'} 报价 ${formatNumber(item.quote_price)} ${item.quote_unit || ''}`.trim(),







  }))







  const signalEvents = focusedSignals.value.slice(0, 2)







    .map((item) => ({







      time: item.latest_captured_at ? formatTimeOnly(item.latest_captured_at) : '--:--',







      market: item.recommended_market || item.recommended_site || '价格变化',







      text: item.reason_summary,







    }))







  return [...quoteEvents, ...signalEvents]







})















const peerRows = computed(() => props.rows.slice(0, 4).map((item) => [







  item.product_name,







  formatNumber(item.average_price),







  item.lowest_price_site || '最低价',







  item.region_label || '本地市场',







  inferThumbTone(item),







]))















const selectedProductName = computed(() => {







  const matchedOption = (props.productOptions || []).find((item) => item.price_identity_key === props.selectedIdentityKey)







  if (matchedOption?.price_identity_label) return matchedOption.price_identity_label







  const matchedRow = props.rows.find((item) => item.price_identity_key === props.selectedIdentityKey)







  return matchedRow?.product_name || props.productSummary?.product_name || ''







})

const alertRuleProductOptions = computed(() => (props.productOptions || []).map((item) => ({
  value: item.price_identity_key,
  label: item.price_identity_label,
})).filter((item) => item.value && item.label))

const alertRuleSourceOptions = computed(() => {
  const options = new Set<string>()
  for (const row of props.trendRows || []) {
    const label = String(row.source_name || row.site_name || '').trim()
    if (label) options.add(label)
  }
  const summarySources = String(selectedSummaryRow.value?.source_names || selectedSummaryRow.value?.source_display_names || '').split(',')
  for (const item of summarySources) {
    const label = item.trim()
    if (label) options.add(label)
  }
  const fallback = String(selectedSummaryRow.value?.lowest_price_site || '').trim()
  if (fallback) options.add(fallback)
  return Array.from(options)
})















const selectedSummaryRow = computed(() => {







  const selectedKey = props.selectedIdentityKey







  const selectedName = selectedProductName.value







  return props.rows.find((item) => item.price_identity_key === selectedKey)







    || props.rows.find((item) => selectedName && item.product_name === selectedName)







    || props.rows[0]







    || null







})















const focusedMarketRows = computed(() => {







  const selectedKey = props.selectedIdentityKey







  const selectedName = selectedProductName.value







  const matched = props.rows.filter((item) => item.price_identity_key === selectedKey || (selectedName && item.product_name === selectedName))







  return matched.length ? matched : props.rows







})















const focusedSupplierQuotes = computed(() => {







  const selectedKey = props.selectedIdentityKey







  const selectedName = selectedProductName.value







  const productQuotes = props.productSupplierQuotes || []







  const overviewQuotes = props.supplierOverview?.recent_quotes || []







  const matchesSelectedProduct = (item: SupplierQuoteItem) => item.price_identity_key === selectedKey || item.product_name === selectedName || item.price_identity_label === selectedName







  const productMatched = productQuotes.filter(matchesSelectedProduct)







  if (productMatched.length) return productMatched







  if (productQuotes.length) return productQuotes







  const overviewMatched = overviewQuotes.filter(matchesSelectedProduct)







  return overviewMatched.length ? overviewMatched : overviewQuotes







})















const hoveredTrendPointIndex = ref<number | null>(null)

const rawTrendChartRows = computed(() => filterTrendRowsByRange(props.trendRows || [], chartRange.value)







  .filter((item) => item.current_price != null && !Number.isNaN(Number(item.current_price))))

const fallbackTrendChartRows = computed<ProductTrendRow[]>(() => {
  const summary = selectedSummaryRow.value
  if (!summary) return []

  const averagePrice = Number(summary.average_price)
  if (!Number.isFinite(averagePrice) || averagePrice <= 0) return []

  const lowestPrice = Number(summary.lowest_price)
  const highestPrice = Number(summary.highest_price)
  const safeLowest = Number.isFinite(lowestPrice) && lowestPrice > 0 ? lowestPrice : averagePrice
  const safeHighest = Number.isFinite(highestPrice) && highestPrice > 0 ? highestPrice : averagePrice
  const capturedDates = splitJoinedText(summary.captured_dates)
    .map(formatDateFilterValue)
    .filter(Boolean)
    .sort(compareTrendCapturedAt)
  const latestDate = formatDateFilterValue(summary.latest_captured_at) || capturedDates.at(-1) || ''
  const labels = capturedDates.length >= 3
    ? capturedDates.slice(-3)
    : ['低价', '均价', latestDate || '最高价']
  const prices = [safeLowest, averagePrice, safeHighest]

  return prices.map((price, index) => ({
    product_name: summary.product_name,
    trend_series_name: summary.lowest_price_site || summary.region_label || '菜价汇总',
    trend_series_key: summary.price_identity_key || summary.product_name,
    source_name: summary.lowest_price_site || summary.region_label || '菜价汇总',
    site_name: summary.lowest_price_site || summary.region_label || '菜价汇总',
    market_name: summary.lowest_price_site || summary.region_label || '菜价汇总',
    current_price: price,
    captured_at: labels[index] || latestDate || String(index + 1),
  }))
})

const trendChartRows = computed(() => {
  if (rawTrendChartRows.value.length >= 2) return sortTrendRowsOldToNew(rawTrendChartRows.value)
  if (fallbackTrendChartRows.value.length) return sortTrendRowsOldToNew(fallbackTrendChartRows.value)
  return sortTrendRowsOldToNew(rawTrendChartRows.value)
})

const isUsingTrendSnapshot = computed(() => rawTrendChartRows.value.length < 2 && fallbackTrendChartRows.value.length > 0)















const bigTrendDots = computed(() => buildLineDots(trendChartRows.value, 50, 690, 36, 198))







const bigTrendLinePoints = computed(() => stringifyDots(bigTrendDots.value))







const bigTrendLowLinePoints = computed(() => stringifyDots(bigTrendDots.value.map((point) => ({ x: point.x, y: Math.min(220, point.y + 32) }))))

const activeTrendPointIndex = computed(() => {
  const rowCount = trendChartRows.value.length
  if (!rowCount) return -1
  const hoveredIndex = hoveredTrendPointIndex.value
  if (hoveredIndex != null && hoveredIndex >= 0 && hoveredIndex < rowCount) return hoveredIndex
  return rowCount - 1
})

const activeTrendDot = computed(() => {
  const index = activeTrendPointIndex.value
  return index >= 0 ? bigTrendDots.value[index] || null : null
})
const activeTrendRow = computed(() => {
  const index = activeTrendPointIndex.value
  return index >= 0 ? trendChartRows.value[index] || null : null
})

const trendPointRailRows = computed(() => {
  const rows = trendChartRows.value
  if (!rows.length) return []
  const indexes = rows.length <= 6
    ? rows.map((_, index) => index)
    : Array.from(new Set([
        0,
        Math.floor((rows.length - 1) * 0.2),
        Math.floor((rows.length - 1) * 0.4),
        Math.floor((rows.length - 1) * 0.6),
        Math.floor((rows.length - 1) * 0.8),
        rows.length - 1,
      ]))
  return indexes.map((index) => {
    const row = rows[index]
    return {
      index,
      label: row?.captured_at ? formatMonthDay(row.captured_at) : `点 ${index + 1}`,
      price: formatNumber(row?.current_price),
      source: row?.source_name || row?.site_name || row?.trend_series_name || row?.market_name || '价格来源',
    }
  })
})







const bigTrendAxisLabels = computed(() => {







  const dots = bigTrendDots.value







  return trendChartRows.value.map((row, index) => ({







    x: dots[index]?.x || 50,







    text: row.captured_at ? formatMonthDay(row.captured_at) : String(index + 1),







  }))







})







const activeTrendTooltip = computed(() => {
  const index = activeTrendPointIndex.value
  const row = index >= 0 ? trendChartRows.value[index] : null
  if (!row) return null

  const point = activeTrendDot.value
  const tooltipWidth = 188
  const tooltipHeight = 76
  const pointX = point?.x ?? 690
  const pointY = point?.y ?? 72
  const x = pointX > 520
    ? Math.max(50, pointX - tooltipWidth - 14)
    : Math.min(690 - tooltipWidth, Math.max(50, pointX + 14))
  const y = Math.min(220 - tooltipHeight, Math.max(20, pointY - 46))

  return {
    date: row.captured_at ? formatMonthDay(row.captured_at) : '最新',
    price: formatNumber(row.current_price),
    market: truncateSvgText(row.market_name || row.site_name || row.trend_series_name || '价格来源', 8),
    x: Number(x.toFixed(1)),
    y: Number(y.toFixed(1)),
  }
})

function setHoveredTrendPoint(index: number) {
  hoveredTrendPointIndex.value = index
}

function clearHoveredTrendPoint() {
  hoveredTrendPointIndex.value = null
}

function truncateSvgText(value: string, maxLength: number) {
  const text = String(value || '').trim()
  if (text.length <= maxLength) return text
  return `${text.slice(0, maxLength)}…`
}

function resolveSummaryLiancaiFilter(value: string) {
  const label = formatFilterLabel(value)
  if (!label || isNeutralFilter(label)) return { liancai_top_category: '', liancai_subcategory: '' }

  const items = props.liancaiCategorySummaryItems || []
  const matchedTop = items.some((item) => String(item.liancai_top_category || '').trim() === label)
  if (matchedTop) return { liancai_top_category: label, liancai_subcategory: '' }

  const matchedSubcategory = items.find((item) => String(item.liancai_subcategory || '').trim() === label)
  if (matchedSubcategory) {
    return {
      liancai_top_category: String(matchedSubcategory.liancai_top_category || '').trim(),
      liancai_subcategory: label,
    }
  }

  const matchedKeyword = items.find((item) => String(item.liancai_keyword || '').trim() === label)
  if (matchedKeyword) {
    return {
      liancai_top_category: String(matchedKeyword.liancai_top_category || '').trim(),
      liancai_subcategory: String(matchedKeyword.liancai_subcategory || '').trim(),
      liancai_keyword: label,
    } as { liancai_top_category: string; liancai_subcategory: string; liancai_keyword: string }
  }

  const matchedBrand = items.find((item) => String(item.liancai_brand_name || '').trim() === label)
  if (matchedBrand) {
    return {
      liancai_top_category: String(matchedBrand.liancai_top_category || '').trim(),
      liancai_subcategory: String(matchedBrand.liancai_subcategory || '').trim(),
      liancai_brand: label,
    } as { liancai_top_category: string; liancai_subcategory: string; liancai_brand: string }
  }

  return null
}

function parseSummaryFacetOption(value: string) {
  const label = formatFilterLabel(value)
  if (!label || isNeutralFilter(label)) return { keyword: '', brand: '' }
  if (label.startsWith('品类:')) return { keyword: label.slice(3).trim(), brand: '' }
  if (label.startsWith('品牌:')) return { keyword: '', brand: label.slice(3).trim() }
  return { keyword: '', brand: '' }
}

function buildSummaryLiancaiFilterFromSelections(selections: number[]) {
  const options = sectionFilterOptions.value.summary || []
  const sourceName = formatFilterLabel(options[0]?.[selections[0] || 0] || '')
  const top = formatFilterLabel(options[1]?.[selections[1] || 0] || '')
  const sub = formatFilterLabel(options[2]?.[selections[2] || 0] || '')
  const facet = parseSummaryFacetOption(options[3]?.[selections[3] || 0] || '')
  return {
    source_name: isNeutralFilter(sourceName) ? '' : sourceName,
    liancai_top_category: isNeutralFilter(top) ? '' : top,
    liancai_subcategory: isNeutralFilter(sub) ? '' : sub,
    liancai_keyword: facet.keyword,
    liancai_brand: facet.brand,
  }
}

const currentSummaryLiancaiFilter = computed(() => {
  const explicit = props.summaryLiancaiFilter || {}
  return {
    source_name: String(explicit.source_name || '').trim(),
    liancai_top_category: String(explicit.liancai_top_category || explicit.liancaiTopCategory || '').trim(),
    liancai_subcategory: String(explicit.liancai_subcategory || explicit.liancaiSubcategory || '').trim(),
    liancai_keyword: String(explicit.liancai_keyword || explicit.liancaiKeyword || '').trim(),
    liancai_brand: String(explicit.liancai_brand || explicit.liancaiBrand || '').trim(),
  }
})

function summarySourceMatches(rowSource: string, selectedSource: string) {
  const source = normalizeLiancaiSourceLabel(rowSource)
  const selected = normalizeLiancaiSourceLabel(selectedSource)
  if (!selected) return true
  if (!source) return false
  if (source === selected) return true
  if (selected === 'Chinaprice') return source.includes('Chinaprice') || source.includes('万邦')
  if (selected.includes('万邦')) return source.includes('Chinaprice') || source.includes('万邦')
  return source.includes(selected) || selected.includes(source)
}

function summaryCategoryMatches(rowCategory: string, selectedCategory: string) {
  const category = String(rowCategory || '').trim()
  const selected = String(selectedCategory || '').trim()
  if (!selected) return true
  if (!category) return false
  if (category === selected) return true
  const aliases: Record<string, string[]> = {
    干调类: ['干调类', '调味品', '调味料', '调味品酱料类', '干货调料', '干货类', '香辛料'],
    调味品: ['调味品', '干调类', '调味料', '调味品酱料类', '干货调料', '香辛料'],
    米面粮油: ['米面粮油', '粮油米面', '粮油类', '主食类'],
    粮油米面: ['粮油米面', '米面粮油', '粮油类', '主食类'],
    蔬菜类: ['蔬菜类', '蔬菜', '净菜类'],
    肉禽蛋类: ['肉禽蛋类', '鲜猪肉', '鲜禽类', '禽蛋类', '牛羊肉'],
    水产类: ['水产类', '鲜活水产', '水产', '海鲜水产'],
  }
  return (aliases[selected] || []).some((alias) => category === alias || category.includes(alias) || alias.includes(category))
}

function summaryDisplayRowMatchesLiancaiFilter(row: {
  source?: string
  category?: string
  subcategory?: string
  keyword?: string
  brandName?: string
  name?: string
}) {
  const active = currentSummaryLiancaiFilter.value as any
  const selectedSource = String(active.source_name || '').trim()
  const selectedTop = String(active.liancai_top_category || '').trim()
  const selectedSub = String(active.liancai_subcategory || '').trim()
  const selectedKeyword = String(active.liancai_keyword || '').trim()
  const selectedBrand = String(active.liancai_brand || '').trim()
  if (selectedSource && !summarySourceMatches(String(row.source || ''), selectedSource)) return false
  if (selectedTop && !summaryCategoryMatches(String(row.category || ''), selectedTop)) return false
  if (selectedSub && String(row.subcategory || '').trim() !== selectedSub) return false
  if (selectedKeyword) {
    const keyword = String(row.keyword || '').trim()
    if (keyword !== selectedKeyword && !String(row.name || '').includes(selectedKeyword)) return false
  }
  if (selectedBrand) {
    const brand = String(row.brandName || '').trim()
    if (brand !== selectedBrand && !String(row.name || '').includes(selectedBrand)) return false
  }
  return true
}

const summaryLiancaiPanel = computed(() => {
  const items = props.liancaiCategorySummaryItems || []
  if (!items.length) return null

  const topOptions = uniqueText(
    items.map((item) => item.liancai_top_category).filter(isMappedLiancaiCategoryLabel),
    40,
  )
  const activeTop = String((currentSummaryLiancaiFilter.value as any).liancai_top_category || '').trim()
  const activeSub = String((currentSummaryLiancaiFilter.value as any).liancai_subcategory || '').trim()
  const activeKeyword = String((currentSummaryLiancaiFilter.value as any).liancai_keyword || '').trim()
  const activeBrand = String((currentSummaryLiancaiFilter.value as any).liancai_brand || '').trim()

  const scopedByTop = activeTop
    ? items.filter((item) => String(item.liancai_top_category || '').trim() === activeTop)
    : items
  const subOptions = uniqueText(
    scopedByTop
      .map((item) => item.liancai_subcategory)
      .filter((item) => isMappedLiancaiCategoryLabel(item) && String(item).trim() !== '全部'),
    200,
  )
  const scopedBySub = activeSub
    ? scopedByTop.filter((item) => String(item.liancai_subcategory || '').trim() === activeSub)
    : scopedByTop
  const keywordOptions = uniqueText(props.liancaiFacetOptions?.keywords || [], 200)
  const brandOptions = uniqueText(props.liancaiFacetOptions?.brands || [], 200)

  if (!topOptions.length) return null
  return { topOptions, subOptions, keywordOptions, brandOptions, activeTop, activeSub, activeKeyword, activeBrand }
})

function applySummaryLiancaiPanelFilter(level: 'top' | 'sub' | 'keyword' | 'brand', value: string) {
  const label = String(value || '').trim()
  if (!label) return
  const active = currentSummaryLiancaiFilter.value as any
  if (level === 'top') {
    emit('update-summary-liancai-filter', { liancai_top_category: label, liancai_subcategory: '', liancai_keyword: '', liancai_brand: '' })
    return
  }
  if (level === 'sub') {
    emit('update-summary-liancai-filter', { liancai_top_category: String(active.liancai_top_category || '').trim(), liancai_subcategory: label, liancai_keyword: '', liancai_brand: '' })
    return
  }
  if (level === 'keyword') {
    emit('update-summary-liancai-filter', {
      liancai_top_category: String(active.liancai_top_category || '').trim(),
      liancai_subcategory: String(active.liancai_subcategory || '').trim(),
      liancai_keyword: label,
      liancai_brand: '',
    })
    return
  }
  emit('update-summary-liancai-filter', {
    liancai_top_category: String(active.liancai_top_category || '').trim(),
    liancai_subcategory: String(active.liancai_subcategory || '').trim(),
    liancai_keyword: '',
    liancai_brand: label,
  })
}







const trendSuggestions = computed(() => {







  const signalTexts = focusedSignals.value.slice(0, 3).map((item) => item.reason_summary)







  if (signalTexts.length) return signalTexts







  const rows = trendChartRows.value







  if (!rows.length) return ['等待价格走势更新后生成采购建议。']







  const latest = rows.at(-1)







  return [







    `${selectedProductName.value || latest?.product_name || '当前商品'} 最新报价 ${formatNumber(latest?.current_price)}，来源 ${latest?.source_name || latest?.site_name || '价格来源'}。`,







    `已加载 ${rows.length} 条行情记录，可结合最低报价和供应商报价复核采购动作。`,







  ]







})







const summaryAdviceRows = computed(() => {







  const recommendations = (props.procurementRecommendations || []).slice(0, 4).map((item) => {







    const name = item.ingredient_name || item.identity_key || '当前商品'







    const action = formatRecommendedAction(item.recommended_action, '建议适量采购')







    return action.startsWith(name) ? action : `${name}${action.startsWith('建议') ? action : `建议${action}`}`







  })







  if (recommendations.length) return recommendations







  return trendSuggestions.value.slice(0, 4)







})







const visibleQuoteCount = computed(() => focusedSupplierQuotes.value.length || quoteRows.value.length)

const summaryActionCards = computed(() => {
  const rows = (props.rows || []).filter((item) => Number(item.average_price || 0) > 0)
  const widestRow = [...rows].sort((left, right) => (
    Number(right.highest_price || right.average_price || 0) - Number(right.lowest_price || right.average_price || 0)
  ) - (
    Number(left.highest_price || left.average_price || 0) - Number(left.lowest_price || left.average_price || 0)
  ))[0]
  const lowestAverageRow = [...rows].sort((left, right) => Number(left.average_price || 0) - Number(right.average_price || 0))[0]
  const focusedIdentityKey = selectedSummaryRow.value?.price_identity_key || props.selectedIdentityKey || ''
  const recommendationCount = props.procurementRecommendations?.length || 0

  return [
    {
      label: '默认追踪',
      title: selectedProductName.value || selectedSummaryRow.value?.product_name || '查看单品走势',
      detail: trendChartRows.value.length ? `已有 ${trendChartRows.value.length} 个价格点` : '先把当前商品的价格走势看明白',
      section: 'trend' as SectionId,
      identityKey: focusedIdentityKey,
    },
    {
      label: '最大价差',
      title: widestRow?.product_name || '等待价差商品',
      detail: widestRow
        ? `价差 ${formatSpread(widestRow.lowest_price, widestRow.highest_price)} · ${widestRow.lowest_price_site || widestRow.region_label || '本地市场'}`
        : '当前还没有可复核的价差商品',
      section: 'trend' as SectionId,
      identityKey: widestRow?.price_identity_key || '',
    },
    {
      label: '最低均价',
      title: lowestAverageRow?.product_name || '等待低价商品',
      detail: lowestAverageRow
        ? `均价 ${formatNumber(lowestAverageRow.average_price)} · 最低 ${formatNumber(lowestAverageRow.lowest_price || lowestAverageRow.average_price)}`
        : '当前没有低价参考',
      section: 'trend' as SectionId,
      identityKey: lowestAverageRow?.price_identity_key || '',
    },
    {
      label: '采购承接',
      title: recommendationCount ? `${recommendationCount} 条采购建议` : `${visibleQuoteCount.value} 条报价待承接`,
      detail: recommendationCount ? '去我的采购把建议接成动作' : '先核价，再回采购执行',
      section: recommendationCount ? 'purchase' as SectionId : 'quotes' as SectionId,
      identityKey: '',
    },
  ]
})

const summaryOpportunityRows = computed(() => (
  [...(props.rows || [])]
    .filter((item) => Number(item.lowest_price || item.average_price || 0) > 0)
    .sort((left, right) => (
      Number(right.highest_price || right.average_price || 0) - Number(right.lowest_price || right.average_price || 0)
    ) - (
      Number(left.highest_price || left.average_price || 0) - Number(left.lowest_price || left.average_price || 0)
    ))
    .slice(0, 4)
    .map((item) => ({
      name: item.product_name || item.price_identity_key || '当前商品',
      market: item.lowest_price_site || item.region_label || '本地市场',
      low: formatNumber(item.lowest_price || item.average_price),
      spread: formatSpread(item.lowest_price, item.highest_price),
      quotes: String(item.price_observation_count || item.market_count || item.site_count || 0),
      identityKey: item.price_identity_key || item.product_name || '',
    }))
))

const purchaseTrendCarryRows = computed(() => trendChartRows.value.slice(-4).reverse().map((item) => ({
  source: item.source_name || item.trend_series_name || item.site_name || '价格来源',
  market: item.market_name || item.region_label || item.city || '本地市场',
  price: formatNumber(item.current_price),
  time: item.captured_at ? formatShortDateTime(item.captured_at) : '最新',
  identityKey: props.selectedIdentityKey || selectedSummaryRow.value?.price_identity_key || '',
})))

const purchaseRunbookSteps = computed(() => {
  const currentProductName = selectedProductName.value || selectedSummaryRow.value?.product_name || '当前商品'
  const recommendationCount = props.procurementRecommendations?.length || 0
  return [
    {
      step: '先补价',
      title: '补齐供应商可下单价',
      detail: visibleQuoteCount.value
        ? `当前已抓到 ${visibleQuoteCount.value} 条报价，先核报价来源与库存。`
        : `当前商品 ${currentProductName} 还没有可直接下单的供应商报价。`,
      actionLabel: '去报价记录',
      section: 'quotes' as SectionId,
      identityKey: '',
    },
    {
      step: '再看趋势',
      title: '确认今天该不该下单',
      detail: trendChartRows.value.length
        ? `已有 ${trendChartRows.value.length} 个趋势点，先看最低价和价格来源。`
        : '先查看最近走势和来源变化。',
      actionLabel: '看价格走势',
      section: 'trend' as SectionId,
      identityKey: props.selectedIdentityKey || selectedSummaryRow.value?.price_identity_key || '',
    },
    {
      step: '后执行',
      title: '把建议接成采购动作',
      detail: recommendationCount
        ? `当前已有 ${recommendationCount} 条采购建议，可回我的采购承接。`
        : '整理完报价和趋势后，再去采购计划确认执行。',
      actionLabel: '去采购计划',
      section: 'plan' as SectionId,
      identityKey: '',
    },
  ]
})

const purchaseExecutionNotes = computed(() => {
  const currentProductName = selectedProductName.value || selectedSummaryRow.value?.product_name || '当前商品'
  if (props.procurementRecommendations?.length) {
    return (props.procurementRecommendations || [])
      .slice(0, 3)
      .map((item) => `${item.ingredient_name || item.identity_key || currentProductName}：${item.reason_summary || formatRecommendedAction(item.recommended_action, '先按建议处理')}`)
  }
  if (trendSuggestions.value.length) {
    return trendSuggestions.value.slice(0, 3)
  }
  return [
    `${currentProductName} 先补供应商报价，再决定是否今天直接下单。`,
    '如果最低价来源持续走低，优先确认来源是否稳定。',
    '回采购计划前，先把供应商、报价和库存核在一条链上。',
  ]
})

const settingsQuickCards = computed(() => {
  const sources = props.sourceCoverageRows || []
  const enabledCount = sources.filter((item) => item.enabled !== false).length
  const failedCount = sources.filter((item) => Number(item.failed_count || 0) > 0).length
  const latestCapture = sources
    .map((item) => item.latest_capture)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1)
  return [
    {
      label: '来源配置',
      value: `${enabledCount}/${sources.length}`,
      detail: sources.length ? '启用来源 / 全部来源' : '暂无来源配置',
      tone: enabledCount ? 'green' : 'warn',
    },
    {
      label: '异常来源',
      value: String(failedCount),
      detail: failedCount ? '优先检查失败来源策略' : '暂无失败来源',
      tone: failedCount ? 'warn' : 'green',
    },
    {
      label: '最近同步',
      value: latestCapture ? formatMonthDay(latestCapture) : '-',
      detail: latestCapture ? formatShortDateTime(latestCapture) : '等待同步',
      tone: latestCapture ? 'blue' : 'warn',
    },
  ]
})

const marketHealthRows = computed(() => {
  const sources = props.sourceCoverageRows || []
  const rows = sources.length
    ? sources.map((item) => {
      const failed = Number(item.failed_count || 0) > 0 || Boolean(item.last_failure)
      return {
        name: item.configured_name || item.source_name || item.source_url || '未命名来源',
        detail: failed ? (item.last_failure || `失败 ${item.failed_count || 0} 次`) : formatSourceCategoryPath(item),
        latest: item.latest_capture ? formatShortDateTime(item.latest_capture) : '未同步',
        records: `${item.price_record_count || item.market_count || item.source_item_count || 0} 条`,
        tone: item.enabled === false ? 'off' : failed ? 'warn' : 'ok',
      }
    })
    : marketModuleView.value.tableRows.map((item) => ({
      name: String(item[0] || '行情来源'),
      detail: String(item[1] || '菜价汇总'),
      latest: String(item[2] || '-'),
      records: String(item[4] || '-'),
      tone: String(item[5] || '').includes('离线') ? 'off' : 'ok',
    }))
  return rows.slice(0, 8)
})

const marketCoverageCards = computed(() => {
  const sources = props.sourceCoverageRows || []
  const enabledCount = sources.filter((item) => item.enabled !== false).length
  const recordTotal = sources.reduce((sum, item) => sum + Number(item.price_record_count || item.market_count || item.source_item_count || 0), 0)
  const latestCapture = sources.map((item) => item.latest_capture).filter((value): value is string => Boolean(value)).sort().at(-1)
  return [
    { label: '启用来源', value: `${enabledCount}/${sources.length}`, detail: '来源同步状态', tone: enabledCount ? 'ok' : 'warn' },
    { label: '价格记录', value: String(recordTotal || props.rows.length), detail: '来源累计记录', tone: 'ok' },
    { label: '最近同步', value: latestCapture ? formatMonthDay(latestCapture) : '-', detail: latestCapture ? formatShortDateTime(latestCapture) : '等待同步', tone: latestCapture ? 'ok' : 'warn' },
  ]
})

const marketFailureRows = computed(() => {
  const failedSources = (props.sourceCoverageRows || [])
    .filter((item) => Number(item.failed_count || 0) > 0 || item.last_failure || item.enabled === false)
    .slice(0, 4)
    .map((item) => ({
      name: item.configured_name || item.source_name || item.source_url || '未命名来源',
      reason: item.last_failure || (item.enabled === false ? '来源已停用' : `失败 ${item.failed_count || 0} 次`),
    }))
  return failedSources.length ? failedSources : [
    { name: '暂无异常来源', reason: '当前先关注覆盖、同步时间和价格记录量。' },
  ]
})

const reportCategoryRows = computed(() => {
  const rows = reportsModuleView.value.tableRows
    .filter((item) => !isEmptyModuleRow(item))
    .map((item) => ({
      category: String(item[0] || '未归类'),
      count: Number(item[1] || 0),
      avg: String(item[2] || '-'),
    }))
    .sort((left, right) => right.count - left.count)
    .slice(0, 8)
  const maxCount = Math.max(...rows.map((item) => item.count), 1)
  return rows.map((item) => ({
    ...item,
    percent: Math.max(4, Math.round((item.count / maxCount) * 100)),
  }))
})

const reportExportCards = computed(() => [
  { label: '行情日报', value: String(props.rows.length), detail: '可导出商品明细' },
  { label: '来源数量', value: String(props.sourceCoverageRows?.length || 0), detail: '来源配置数量' },
  { label: '均价覆盖', value: props.rows.length ? `${Math.round((props.rows.filter((item) => item.average_price != null).length / props.rows.length) * 100)}%` : '0%', detail: '可统计均价比例' },
])

const reportRiskRows = computed(() => {
  const risks = signalItems.value.slice(0, 4).map((item) => ({
    title: item.product_name || item.identity_key || '风险商品',
    detail: item.reason_summary || formatRecommendedAction(item.recommended_action),
    tone: item.signal_level === 'high' || item.signal_level === 'critical' ? 'warn' : 'blue',
  }))
  return risks.length ? risks : [
    { title: '暂无风险信号', detail: '当前报表以品类结构、均价完整度和来源数量为主。', tone: 'green' },
  ]
})

const trendAlertRows = computed(() => {







  const settings = normalizeAlertSettings(alertSettings.value)







  const currentPrice = Number(trendChartRows.value.at(-1)?.current_price ?? selectedSummaryRow.value?.average_price ?? 0)







  if (focusedSignals.value.length) {







    return focusedSignals.value.slice(0, 3).map((item) => [







      formatSignalType(item),







      `${Math.round(item.risk_score)} 分`,







      Number(item.risk_score || 0) >= settings.highRiskScore







        ? 'up'







        : Number(item.risk_score || 0) >= settings.watchRiskScore ? 'warn' : 'down',







      Number(item.risk_score || 0) >= settings.highRiskScore







        ? '需处理'







        : Number(item.risk_score || 0) >= settings.watchRiskScore ? '观察' : '正常',







    ])







  }







  if (currentPrice && settings.maxPrice && currentPrice >= settings.maxPrice) {







    return [['最高提醒价', `${formatNumber(currentPrice)} / ${formatNumber(settings.maxPrice)}`, 'up', '需处理']]







  }







  if (currentPrice && settings.minPrice && currentPrice <= settings.minPrice) {







    return [['最低提醒价', `${formatNumber(currentPrice)} / ${formatNumber(settings.minPrice)}`, 'down', '低价提醒']]







  }







  return [['价格提醒', `${props.signalOverview?.alert_count || 0} 条`, props.signalOverview?.alert_count ? 'warn' : 'down', props.signalOverview?.alert_count ? '需查看' : '正常']]







})







const alertAdviceRows = computed(() => {







  const actions = (props.signalOverview?.recommended_actions || []).map((item) => item.description)







  if (actions.length) return actions.slice(0, 3)







  const rows = priorityAlerts.value.map((item) => item.detail)







  return rows.length ? rows : ['等待价格变化同步后生成处理建议。']







})















const productOptionDisplayRows = computed(() => (props.productOptions || []).map((item) => ({
  name: simplifyProductName(item.price_identity_label),
  category: String(item.liancai_top_category || item.source_category || item.liancai_subcategory || item.source_name || '').trim() || '商品',
  subcategory: String(item.liancai_subcategory || '').trim() || undefined,
  keyword: String(item.liancai_keyword || '').trim() || undefined,
  brandName: String(item.liancai_brand_name || '').trim() || undefined,
  source: normalizeLiancaiSourceLabel(item.source_name) || '商品',
  capturedDate: formatDateFilterValue(item.latest_captured_at),
  capturedDates: formatDateFilterValue(item.latest_captured_at),
  avg: '-',
  low: '-',
  spread: '-',
  change: '待同步',
  changeTone: 'warn',
  quotes: String(item.price_observation_count || item.site_count || 1),
  thumb: 'blue',
  imageUrl: item.image_url || '',
  identityKey: item.price_identity_key || item.price_identity_label,
})))

function resolveSafeImageUrl(value?: string | null) {
  const url = String(value || '').trim()
  if (!url) return ''
  if (/^https?:\/\/mst\.liancaiwang\.cn\/upload\//i.test(url)) {
    return url.replace(/^https?:\/\/mst\.liancaiwang\.cn\/upload\//i, 'https://cdnlcw.liancaiwang.cn/')
  }
  return url
}

function resetSectionFilters(sectionId: SectionId) {
  const options = sectionFilterOptions.value[sectionId] || []
  filterSelections.value = {
    ...filterSelections.value,
    [sectionId]: options.map(() => 0),
  }
  activeFilterMenu.value = null
  filterSearchText.value = ''
  activeFilterIndex.value = 0
  resetTablePage(sectionId)
}

function openImagePreview(url?: string | null, title = '') {
  const safeUrl = resolveSafeImageUrl(url)
  if (!safeUrl) return
  imagePreviewUrl.value = safeUrl
  imagePreviewTitle.value = String(title || '').trim()
  imagePreviewVisible.value = true
}

const allDisplayRows = computed(() => {







  const summaryRows = props.rows.map((row) => ({







    name: simplifyProductName(row.product_name),







    category: inferMarketCategory(row),







    subcategory: String(row.liancai_subcategory || '').trim() || undefined,
    keyword: String(row.liancai_keyword || '').trim() || undefined,
    brandName: String(row.liancai_brand_name || '').trim() || undefined,







    source: summarizeSourceNames(row.source_names || row.source_display_names || row.lowest_price_site),







    capturedDate: formatDateFilterValue(row.latest_captured_at),







    capturedDates: splitJoinedText(row.captured_dates).map(formatDateFilterValue).join(' '),







    avg: formatNumber(row.average_price),







    low: formatNumber(row.lowest_price),







    spread: formatSpread(row.lowest_price, row.highest_price),







    change: row.average_price == null ? '待同步' : '已同步',







    changeTone: row.average_price == null ? 'warn' : 'blue',







    quotes: String(row.price_observation_count || row.market_count || row.site_count || 0),







    thumb: inferThumbTone(row),
    imageUrl: row.image_url || '',







    identityKey: row.price_identity_key || row.product_name,







  })).sort((left, right) => {
    const leftIsSupplier = String(left.source || '').includes('供应平台')
    const rightIsSupplier = String(right.source || '').includes('供应平台')
    if (leftIsSupplier && !rightIsSupplier) return -1
    if (!leftIsSupplier && rightIsSupplier) return 1
    return 0
  })





  return summaryRows.length ? summaryRows : productOptionDisplayRows.value



})







const filteredDisplayRows = computed(() => allDisplayRows.value.filter((row) => rowMatchesActiveFilters([







  row.name,
  row.category,
  row.subcategory || '',
  row.keyword || '',
  row.brandName || '',
  row.source,







  row.capturedDate,







  row.capturedDates,







  row.change,






], 'summary') && summaryDisplayRowMatchesLiancaiFilter(row)).sort((left, right) => {
  const currentIdentityKey = String(props.rows.find((item) => item.price_identity_key)?.price_identity_key || '').trim()
  const leftIsCurrentSupplier = String(left.identityKey || '').trim() === currentIdentityKey && String(left.source || '').includes('供应平台')
  const rightIsCurrentSupplier = String(right.identityKey || '').trim() === currentIdentityKey && String(right.source || '').includes('供应平台')
  if (leftIsCurrentSupplier && !rightIsCurrentSupplier) return -1
  if (!leftIsCurrentSupplier && rightIsCurrentSupplier) return 1
  return 0
}))







const displayRowTotal = computed(() => filteredDisplayRows.value.length)







const displayRows = computed(() => paginateRows(filteredDisplayRows.value, 'summary'))







const loadedSummaryPageCount = computed(() => getPageCount(displayRowTotal.value))
const summaryPageCount = computed(() => loadedSummaryPageCount.value + (props.summaryHasMoreRows ? 1 : 0))







const summaryPaginationPages = computed(() => buildPaginationPages(summaryPageCount.value, tablePage.value.summary || 1))















const chartAxisLabels = computed(() => {







  const now = new Date()







  const xs = [82, 218, 346, 474, 634]







  return xs.map((x, index) => {







    const date = new Date(now)







    date.setDate(now.getDate() - (xs.length - index - 1))







    return { x, text: formatMonthDay(date.toISOString()) }







  })







})















const alertChartBars = computed(() => {







  const values = [







    signalItems.value.filter((item) => item.trend_label === '上涨').length,







    signalItems.value.filter((item) => item.trend_label === '下降').length,







    signalItems.value.filter((item) => item.trend_label !== '上涨' && item.trend_label !== '下降').length,







  ]







  return buildBarSet(values, [72, 102, 132], 30, 20, 210)







})















const alertChartLinePoints = computed(() => {







  const base = Math.max(signalItems.value.length, props.signalOverview?.alert_count || 0, 1)







  return stringifyDots([88, 244, 392, 530, 668].map((x, index) => ({







    x,







    y: Math.max(42, 160 - Math.min(base + index, base * 2) * 12),







  })))







})















const moduleChartSeries = computed(() => {







  if (!moduleHasChartData.value) {
    return { barValues: [] as number[], primaryValues: [] as number[], secondaryValues: [] as number[] }
  }
  if (currentSection.value === 'market') {
    return {
      barValues: marketTrendSeries.value.map((item) => item.high),
      primaryValues: marketTrendSeries.value.map((item) => item.avg),
      secondaryValues: marketTrendSeries.value.map((item) => item.low),
    }
  }







  const metricValues = moduleView.value.metrics.map((item, index) => scoreModuleMetric(item, index))







  const tableValues = filteredModuleTableRows.value.slice(0, 8).map((row, index) => scoreModuleRow(row, index))







  const sideValues = moduleSideItems.value.slice(0, 6).map((item, index) => scoreModuleSideItem(item, index))







  const flowValues = moduleFlowItems.value.slice(0, 6).map((item, index) => scoreModuleFlowItem(item, index))







  const combinedValues = [...metricValues, ...tableValues, ...sideValues, ...flowValues]

  return {
    barValues: expandChartValues(combinedValues, 8, `${currentSection.value}-bars`),
    primaryValues: expandChartValues([...tableValues, ...metricValues, ...sideValues], 5, `${currentSection.value}-primary`),
    secondaryValues: expandChartValues([...flowValues, ...sideValues, ...metricValues.slice().reverse(), ...tableValues.slice().reverse()], 5, `${currentSection.value}-secondary`),
  }







})















const moduleChartBars = computed(() => {

  if (!moduleHasChartData.value) return []

  return buildBarSet(moduleChartSeries.value.barValues, [78, 118, 206, 246, 334, 374, 462, 502], 34, 24, 200)

})

const moduleChartLinePoints = computed(() => {







  if (!moduleHasChartData.value) return ''
  return buildModuleValueLinePoints(moduleChartSeries.value.primaryValues)







  const count = Math.max(moduleTableRows.value.length, 1)







  return stringifyDots([94, 230, 358, 486, 646].map((x, index) => ({







    x,







    y: Math.max(54, 142 - (count + index) * 8),







  })))







})















const moduleChartLowLinePoints = computed(() => {







  if (!moduleHasChartData.value) return ''
  return buildModuleValueLinePoints(moduleChartSeries.value.secondaryValues)
  if (currentSection.value === 'market') {
    return buildModuleValueLinePoints(marketTrendSeries.value.map((item) => item.low))
  }







  const count = Math.max(moduleFlowItems.value.length, 1)







  return stringifyDots([94, 230, 358, 486, 646].map((x, index) => ({







    x,







    y: Math.max(82, 162 - (count + index) * 6),







  })))







})















function extractChartNumbers(value?: string | number | null) {

  const matches = String(value ?? '').match(/-?\d+(?:\.\d+)?/g)

  return (matches || []).map((item) => Math.abs(Number(item))).filter((item) => Number.isFinite(item) && item > 0)

}

function scoreChartText(value?: string | number | null, scale = 1) {

  const text = String(value ?? '').replace(/\s+/g, '')

  return text ? Math.max(1, Math.min(text.length * scale, 48)) : 0

}

function scoreModuleMetric(item: { label: string; value: string; detail: string }, index: number) {

  const numericScore = averageNumbers([
    ...extractChartNumbers(item.value),
    ...extractChartNumbers(item.detail),
  ]) || 0

  return numericScore + scoreChartText(item.label, 1.4) + scoreChartText(item.detail, 0.28) + (index + 1) * 5

}

function scoreModuleRow(row: string[], index: number) {

  return row.reduce((sum, cell, cellIndex) => {
    const numbers = extractChartNumbers(cell)
    const numericScore = numbers.length ? (averageNumbers(numbers) || 0) : 0
    const textScore = scoreChartText(cell, cellIndex === 0 ? 1.3 : 0.75)

    return sum + numericScore + textScore + (cellIndex + 1) * 2
  }, (index + 1) * 4)

}

function scoreModuleSideItem(item: { label: string; title: string; detail: string }, index: number) {

  return (
    (averageNumbers([
      ...extractChartNumbers(item.label),
      ...extractChartNumbers(item.detail),
    ]) || 0)
    + scoreChartText(item.title, 1.1)
    + scoreChartText(item.detail, 0.42)
    + (index + 1) * 3
  )

}

function scoreModuleFlowItem(item: { step: string; text: string }, index: number) {

  return (
    (averageNumbers([
      ...extractChartNumbers(item.step),
      ...extractChartNumbers(item.text),
    ]) || 0)
    + scoreChartText(item.step, 1.2)
    + scoreChartText(item.text, 0.38)
    + (index + 1) * 4
  )

}

function expandChartValues(values: number[], size: number, seedText: string) {

  const seed = Array.from(seedText).reduce((sum, char) => sum + char.charCodeAt(0), 0)
  const cleanValues = values.map((item) => Math.abs(Number(item))).filter((item) => Number.isFinite(item) && item > 0)

  if (!cleanValues.length) {
    return Array.from({ length: size }, (_, index) => 12 + ((seed + index * 11) % 37))
  }

  const expanded = [...cleanValues]

  while (expanded.length < size) {
    const source = cleanValues[expanded.length % cleanValues.length]
    const modifier = 1 + (((seed + expanded.length) % 5) * 0.09)
    expanded.push(Number((source * modifier + ((seed + expanded.length) % 9)).toFixed(2)))
  }

  return expanded.slice(0, size)

}

function uniqueText(values: Array<string | null | undefined>, limit = 200) {







  return Array.from(new Set(values.map((item) => String(item || '').trim()).filter(Boolean))).slice(0, limit)







}















function splitJoinedText(value?: string | null) {







  return String(value || '')







    .split(/[、,，]/)







    .map((item) => item.trim())







    .filter(Boolean)







}















function formatDateFilterValue(value?: string | null) {







  const text = String(value || '').trim()







  if (!text) return ''







  const dateMatch = text.match(/^(\d{4})-(\d{2})-(\d{2})/)







  if (dateMatch) return `${dateMatch[2]}-${dateMatch[3]}`







  const shortMatch = text.match(/^(\d{2})-(\d{2})/)







  return shortMatch ? `${shortMatch[1]}-${shortMatch[2]}` : text.slice(0, 10)







}















function simplifyProductName(value?: string | null) {







  return String(value || '未命名商品')







    .split(/[|｜]/)[0]







    .replace(/\s+/g, ' ')







    .trim() || '未命名商品'







}















function summarizeSourceNames(value?: string | null) {







  const items = splitJoinedText(value)







  if (!items.length) return '未知来源'







  return uniqueText(items.map((item) => normalizeLiancaiSourceLabel(item)), 3).join('、')







}















function normalizeLiancaiSourceLabel(value?: string | null) {
  const label = String(value || '').trim()
  if (!label) return ''
  return label.includes('莲菜网') ? '莲菜网' : label
}

function normalizeFilterValue(value: string) {







  return String(value)







    .replace(/⌄/g, '')







    .replace(/^计划周期：/, '')







    .replace(/^全部/, '')







    .replace(/^搜索/, '')







    .trim()







}

function isMappedLiancaiCategoryLabel(value: unknown) {
  const label = String(value || '').trim()
  return Boolean(label && label !== '未映射' && label !== '未归类')
}















function formatFilterLabel(value: string) {







  return String(value || '').replace(/\s*⌄/g, '').trim()







}















function isNeutralFilter(value: string) {







  const raw = String(value || '').trim()







  if (raw.startsWith('全部')) return true







  if (raw.startsWith('最新数据')) return true







  const normalized = normalizeFilterValue(value)







  return !normalized







    || /^20\d{2}-\d{2}-\d{2}$/.test(normalized)







    || /^近\d+日$/.test(normalized)







    || normalized === '本周'







    || normalized === '报表类型'







    || normalized === '设置分类'
    || normalized === '全部分类'
    || normalized === '全部组织'
    || normalized === '全部日期'
    || normalized === '全部关键词'
    || normalized === '搜索配置'







    || normalized === '供应商'







    || normalized === '采购状态'







    || normalized === '运行状态'







    || normalized === '预警状态'







    || normalized === '执行状态'







    || normalized === '记录状态'







    || normalized === '报价状态'







    || normalized === '报价单位'







}















function getActiveSemanticFilters(sectionId: SectionId) {







  const options = sectionFilterOptions.value[sectionId] || []







  const selections = filterSelections.value[sectionId] || []







  return options







    .map((item, index) => {
      if (sectionId === 'summary' && index >= 0 && index <= 3) return ''
      return item[selections[index] || 0] || item[0] || ''
    })







    .filter((item) => !isNeutralFilter(item))







    .map((item) => normalizeFilterValue(item))







    .map((item) => item.replace(/市场$/, '').replace(/状态$/, '').trim())







    .filter(Boolean)







}















function rowMatchesActiveFilters(row: Array<string | number | null | undefined>, sectionId: SectionId) {







  const filters = getActiveSemanticFilters(sectionId)







  if (!filters.length) return true







  const text = row.map((item) => String(item || '')).join(' ')







  return filters.every((filter) => text.includes(filter))







}















function formatSignalType(item: SignalInsightItem) {







  const raw = String(item.signal_code || '').trim()







  if (raw && !/^[a-z][a-z0-9_-]*$/i.test(raw)) return raw







  if (item.trend_label === '上涨') return '上涨预警'







  if (item.trend_label === '下降') return '下跌预警'







  if (item.trend_label === '波动') return '波动预警'







  return '价格预警'







}
















function formatRecommendedAction(value?: string | null, fallback = '先复核价格来源') {
  const raw = String(value || '').trim()
  if (!raw) return fallback
  const normalized = raw.toLowerCase()
  const actionMap: Record<string, string> = {
    switch_market: '切换低价市场',
    quote_supplier: '联系供应商报价',
    request_supplier_quote: '联系供应商报价',
    contact_supplier: '联系供应商确认',
    watch: '先观察',
    monitor: '继续观察',
    buy_now: '尽快采购',
    purchase_now: '尽快采购',
    adjust_plan: '调整采购计划',
    review_source: '复核价格来源',
  }
  return actionMap[normalized] || raw.replace(/_/g, ' ')
}

function getPageCount(total: number) {







  return Math.max(1, Math.ceil(total / pageSize.value))







}















function paginateRows<T>(rows: T[], sectionId: SectionId) {







  const page = Math.min(Math.max(tablePage.value[sectionId] || 1, 1), getPageCount(rows.length))







  const start = (page - 1) * pageSize.value







  return rows.slice(start, start + pageSize.value)







}















function buildPaginationPages(pageCount: number, currentPage = 1, maxVisible = 7) {







  const total = Math.max(1, pageCount)
  const visible = Math.max(1, Math.min(maxVisible, total))
  const half = Math.floor(visible / 2)
  let start = Math.max(1, currentPage - half)
  let end = Math.min(total, start + visible - 1)
  start = Math.max(1, end - visible + 1)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)







}















function resetTablePage(sectionId: SectionId) {







  tablePage.value = { ...tablePage.value, [sectionId]: 1 }







}


function resetAllTablePages() {
  tablePage.value = Object.keys(tablePage.value).reduce((result, key) => {
    result[key as SectionId] = 1
    return result
  }, {} as Record<SectionId, number>)
}


function setPageSize(size: number) {
  const nextSize = pageSizeOptions.includes(size) ? size : pageSizeOptions[0]
  if (pageSize.value === nextSize) return
  pageSize.value = nextSize
  resetAllTablePages()
}


function handlePageSizeChange(event: Event) {
  const target = event.target as HTMLSelectElement | null
  setPageSize(Number(target?.value || pageSize.value))
}















function setTablePage(sectionId: SectionId, page: number) {







  const maxPage = sectionId === 'summary' ? summaryPageCount.value : getPageCount(getTableTotal(sectionId))
  tablePage.value = { ...tablePage.value, [sectionId]: Math.min(Math.max(page, 1), maxPage) }
  if (sectionId === 'summary' && props.summaryHasMoreRows && tablePage.value.summary >= loadedSummaryPageCount.value) {
    emit('request-summary-next-page')
  }







}















function changeTablePage(sectionId: SectionId, delta: number) {







  setTablePage(sectionId, (tablePage.value[sectionId] || 1) + delta)







}















function getTableTotal(sectionId: SectionId) {







  if (sectionId === 'summary') return displayRowTotal.value







  if (sectionId === 'alerts') return alertTaskTotal.value







  if (sectionId === currentSection.value) return moduleTableCount.value







  return pageSize.value







}















function splitActions(value: string) {







  return String(value || '')







    .split(/\s+/)







    .map((item) => item.trim())







    .filter(Boolean)







}















function handleTableAction(action: string, row: Array<string | number | null | undefined>) {







  const subject = String(row[0] || '当前记录')







  if (action.includes('后台')) {







    emit('open-supplier-backend')







    actionFeedback.value = `已打开供应平台：${subject}`







    window.setTimeout(() => {







      if (actionFeedback.value === `已打开供应平台：${subject}`) actionFeedback.value = ''







    }, 1800)







    return







  }







  const detailRows = row.map((item, index) => `${moduleView.value?.columns?.[index] || `字段 ${index + 1}`}：${String(item || '-')}`)







  openActionPanel(`${action} · ${subject}`, detailRows, currentSection.value)







  actionFeedback.value = `${action}：${subject}`







  window.setTimeout(() => {







    if (actionFeedback.value === `${action}：${subject}`) actionFeedback.value = ''







  }, 1800)







}















function openActionPanel(







  title: string,







  rows: Array<string | number | null | undefined>,







  kind: SectionId | 'export',







) {







  const sectionLabel = navItems.value.find((item) => item.id === currentSection.value)?.label || pageTitle.value







  const normalizedRows = rows.map((item) => String(item || '-')).filter(Boolean)







  actionPanel.value = {







    visible: true,







    title,







    description: `来自 ${sectionLabel} 的当前明细。可用于核对当前记录；需要调整供应商、报价或来源时请进入对应管理台处理。`,







    kind,







    kindLabel: sectionLabel,







    rows: normalizedRows,







  }







}















function closeActionPanel() {







  actionPanel.value.visible = false







}















function handleExportData() {







  const exportData = getCurrentExportData()







  const csv = toCsv(exportData.headers, exportData.rows)







  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })







  const url = URL.createObjectURL(blob)







  const link = document.createElement('a')







  link.href = url







  link.download = `${exportData.filename}-${currentDateLabel}.csv`







  document.body.appendChild(link)







  link.click()







  link.remove()







  URL.revokeObjectURL(url)







  actionFeedback.value = `已导出 ${exportData.rows.length} 条数据`







}















function getCurrentExportData() {







  if (currentSection.value === 'summary') {







    return {







      filename: '汇总行情',







      headers: ['商品', '分类', '来源', '均价', '最低价', '价差', '较昨日', '有效报价'],







      rows: filteredDisplayRows.value.map((row) => [row.name, formatDisplayCategoryPath(row), row.source, row.avg, row.low, row.spread, row.change, row.quotes]),


    }







  }







  if (currentSection.value === 'alerts') {







    return {







      filename: '价格预警',







      headers: ['商品', '市场', '预警类型', '当前值', '触发规则', '负责人', '状态'],







      rows: filteredAlertTaskRows.value.map((row) => [row.name, row.market, row.type, row.value, row.rule, row.owner, row.state]),







    }







  }







  return {







    filename: moduleView.value.kicker,







    headers: moduleView.value.columns,







    rows: filteredModuleTableRows.value,







  }







}















function toCsv(headers: string[], rows: Array<Array<string | number | null | undefined>>) {







  const escapeCell = (value: string | number | null | undefined) => `"${String(value ?? '').replace(/"/g, '""')}"`







  return [headers.map(escapeCell).join(','), ...rows.map((row) => row.map(escapeCell).join(','))].join('\n')







}















function normalizeAlertSettings(value: typeof defaultAlertSettings) {







  const highRiskScore = clampNumber(value.highRiskScore, 0, 100, defaultAlertSettings.highRiskScore)







  const watchRiskScore = Math.min(highRiskScore, clampNumber(value.watchRiskScore, 0, 100, defaultAlertSettings.watchRiskScore))

  const identityKey = String((value as { identityKey?: string }).identityKey || '').trim()
  const productLabel = String((value as { productLabel?: string }).productLabel || '').trim()
  const sourceName = String((value as { sourceName?: string }).sourceName || '').trim()
  const sourceLabel = String((value as { sourceLabel?: string }).sourceLabel || '').trim()







  let maxPrice = Math.max(0, Number(value.maxPrice || 0))







  let minPrice = Math.max(0, Number(value.minPrice || 0))







  if (maxPrice > 0 && minPrice > 0 && minPrice > maxPrice) {







    const nextMaxPrice = minPrice







    minPrice = maxPrice







    maxPrice = nextMaxPrice







  }







  return {







    highRiskScore,







    watchRiskScore,

    identityKey,

    productLabel,

    sourceName,

    sourceLabel,







    maxPrice,







    minPrice,







  }







}















function clampNumber(value: number, min: number, max: number, fallback: number) {







  const numeric = Number(value)







  if (Number.isNaN(numeric)) return fallback







  return Math.min(Math.max(numeric, min), max)







}















function readAlertSettings() {







  if (typeof window === 'undefined') return { ...defaultAlertSettings }







  try {







    const raw = window.localStorage.getItem(ALERT_SETTINGS_KEY)







    return normalizeAlertSettings(raw ? { ...defaultAlertSettings, ...JSON.parse(raw) } : defaultAlertSettings)







  } catch {







    return { ...defaultAlertSettings }







  }







}















function writeAlertSettings(value: typeof defaultAlertSettings) {







  if (typeof window === 'undefined') return







  window.localStorage.setItem(ALERT_SETTINGS_KEY, JSON.stringify(normalizeAlertSettings(value)))







}















function withEmptyRows(rows: string[][], columns: string[]) {







  if (rows.length) return rows







  return [columns.map((_, index) => (index === 0 ? '等待数据' : '-'))]







}















function isEmptyModuleRow(row: string[]) {







  return row[0] === '等待数据'







}















function isEmptyModuleSideItem(item: { title: string; detail: string }) {







  return (
    (item.title === '等待数据' && item.detail === '系统同步后自动更新此处内容')
    || (item.title === '暂无可展示数据' && item.detail === '当前没有可确认的记录')
  )







}















function isEmptyModuleFlowItem(item: { step: string; text: string }) {







  return (
    (item.step === '同步' && item.text === '等待数据同步后生成处理记录')
    || (item.step === '空' && item.text === '当前没有可展示的流程记录')
  )







}















function withEmptySideItems(items: Array<{ label: string; title: string; detail: string; tone: string }>) {







  if (items.length) return items







  return [{ label: '空', title: '暂无可展示数据', detail: '当前没有可确认的记录', tone: 'blue' }]







}















function withEmptyFlow(items: Array<{ step: string; text: string }>) {







  if (items.length) return items







  return [{ step: '空', text: '当前没有可展示的流程记录' }]







}















onMounted(() => {







  document.addEventListener('pointerdown', handleDocumentPointerDown)







  document.addEventListener('keydown', handleDocumentKeydown)







})















onBeforeUnmount(() => {







  document.removeEventListener('pointerdown', handleDocumentPointerDown)







  document.removeEventListener('keydown', handleDocumentKeydown)







})















function buildBarSet(values: number[], xs: number[], width: number, minY: number, maxY: number) {







  const maxValue = Math.max(...values, 1)







  return xs.map((x, index) => {







    const value = values[index % values.length] || 0







    const height = Math.max(12, Math.round(((maxY - minY) * value) / maxValue))







    return { x, y: maxY - height, width, height }







  })







}















function formatNumber(value?: number | string | null, fallback = '-') {







  return value == null || Number.isNaN(Number(value)) ? fallback : Number(value).toFixed(2)







}















function formatCurrency(value?: number | string | null, fallback = '-') {







  const formatted = formatNumber(value, fallback)







  return formatted === fallback ? fallback : `¥${formatted}`







}















function formatSignedNumber(value?: number | string | null, fallback = '-') {







  if (value == null || Number.isNaN(Number(value))) return fallback







  const numeric = Number(value)







  return `${numeric > 0 ? '+' : ''}${numeric.toFixed(2)}`







}















function sumNumbers(values: Array<number | string | null | undefined>) {







  return values.reduce((sum, value) => (value == null || Number.isNaN(Number(value)) ? sum : sum + Number(value)), 0)







}















function averageNumbers(values: Array<number | string | null | undefined>) {







  const numericValues = values







    .map((value) => Number(value))







    .filter((value) => !Number.isNaN(value))







  return numericValues.length ? numericValues.reduce((sum, value) => sum + value, 0) / numericValues.length : null







}















function formatPercent(value?: number | string | null, fallback = '-') {







  if (value == null || Number.isNaN(Number(value))) return fallback







  return `${Math.round(Number(value))}%`







}















function formatSpread(low?: number | string | null, high?: number | string | null, fallback = '-') {







  if (low == null || high == null) return fallback







  return Math.max(Number(high) - Number(low), 0).toFixed(2)







}















function formatShortDateTime(value?: string | null) {







  if (!value) return '暂无时间'







  const parsedDate = new Date(String(value).replace(' ', 'T'))







  if (Number.isNaN(parsedDate.getTime())) return String(value)







  return new Intl.DateTimeFormat('zh-CN', {







    timeZone: 'Asia/Shanghai',







    month: '2-digit',







    day: '2-digit',







    hour: '2-digit',







    minute: '2-digit',







    hour12: false,







  }).format(parsedDate)







}















function formatTimeOnly(value?: string | null) {







  const formatted = formatShortDateTime(value)







  const matched = formatted.match(/(\d{2}:\d{2})$/)







  return matched?.[1] || formatted







}















function formatMonthDay(value?: string | null) {







  if (!value) return '--'







  const parsedDate = new Date(String(value).replace(' ', 'T'))







  if (Number.isNaN(parsedDate.getTime())) return String(value).slice(0, 5)







  return new Intl.DateTimeFormat('zh-CN', {







    timeZone: 'Asia/Shanghai',







    month: '2-digit',







    day: '2-digit',







  }).format(parsedDate).replace('/', '-')







}















function parseTrendDate(value?: string | null) {







  if (!value) return null







  const parsedDate = new Date(String(value).replace(' ', 'T'))







  return Number.isNaN(parsedDate.getTime()) ? null : parsedDate







}















function compareTrendCapturedAt(left?: string | null, right?: string | null) {
  const leftTime = parseTrendDate(left)?.getTime()
  const rightTime = parseTrendDate(right)?.getTime()
  if (leftTime != null && rightTime != null) return leftTime - rightTime
  if (leftTime != null) return -1
  if (rightTime != null) return 1
  return String(left || '').localeCompare(String(right || ''), 'zh-CN', { numeric: true })
}

function sortTrendRowsOldToNew(rows: ProductTrendRow[]) {
  return rows
    .map((row, index) => ({ row, index }))
    .sort((left, right) => {
      const leftTime = parseTrendDate(left.row.captured_at)?.getTime()
      const rightTime = parseTrendDate(right.row.captured_at)?.getTime()
      if (leftTime != null && rightTime != null) return leftTime - rightTime
      return left.index - right.index
    })
    .map((item) => item.row)
}

function filterTrendRowsByRange(rows: ProductTrendRow[], range: 7 | 30 | 90) {







  const sortedRows = sortTrendRowsOldToNew(rows)







  const datedRows = sortedRows.filter((item) => parseTrendDate(item.captured_at))







  if (!datedRows.length) return sortedRows.slice(-range)







  const latestTime = Math.max(...datedRows.map((item) => parseTrendDate(item.captured_at)?.getTime() ?? 0))







  const startTime = latestTime - (range - 1) * 24 * 60 * 60 * 1000







  const rangedRows = datedRows.filter((item) => {







    const capturedTime = parseTrendDate(item.captured_at)?.getTime() ?? 0







    return capturedTime >= startTime && capturedTime <= latestTime







  })







  return rangedRows.length ? rangedRows : datedRows.slice(-Math.min(range, datedRows.length))







}















function buildLineDots(rows: ProductTrendRow[], minX: number, maxX: number, minY: number, maxY: number) {







  if (!rows.length) return []







  const prices = rows.map((row) => Number(row.current_price))







  const minPrice = Math.min(...prices)







  const maxPrice = Math.max(...prices)







  const priceSpan = Math.max(maxPrice - minPrice, 0.01)







  return rows.map((row, index) => {







    const x = rows.length === 1 ? (minX + maxX) / 2 : minX + ((maxX - minX) * index) / (rows.length - 1)







    const normalized = (Number(row.current_price) - minPrice) / priceSpan







    const y = maxY - normalized * (maxY - minY)







    return { x: Number(x.toFixed(1)), y: Number(y.toFixed(1)) }







  })







}















function stringifyDots(points: Array<{ x: number; y: number }>) {


  return points.map((point) => `${point.x},${point.y}`).join(' ')


}

function buildModuleValueLinePoints(values: number[]) {
  const cleanValues = values.filter((value) => Number.isFinite(value) && value > 0)
  if (!cleanValues.length) return ''
  const minValue = Math.min(...cleanValues)
  const maxValue = Math.max(...cleanValues)
  const spread = Math.max(maxValue - minValue, 1)
  const step = cleanValues.length > 1 ? 552 / (cleanValues.length - 1) : 0
  return stringifyDots(cleanValues.map((value, index) => ({
    x: cleanValues.length > 1 ? 94 + step * index : 360,
    y: maxValue === minValue ? 112 : 190 - ((value - minValue) / spread) * 136,
  })))
}





function formatSourceCategoryPath(item?: SourceCoverageItem | null) {


  const category = String(item?.market_category || '').trim()


  const subcategory = String(item?.market_subcategory || '').trim()


  const scope = String(item?.market_scope || '').trim()


  if (category && subcategory && category !== subcategory) {


    return `${category} / ${subcategory}`


  }


  return category || subcategory || scope || '-'


}





function formatDisplayCategoryPath(row?: { category?: string | null; subcategory?: string | null } | null) {


  const category = String(row?.category || '').trim()


  const subcategory = String(row?.subcategory || '').trim()


  if (category && subcategory && category !== subcategory && subcategory !== '全部') {


    return `${category} / ${subcategory}`


  }


  return category || subcategory || '-'


}





function inferMarketCategory(rowOrProductName?: { product_name?: string | null; liancai_top_category?: string | null; liancai_subcategory?: string | null } | string | null) {


  if (rowOrProductName && typeof rowOrProductName === 'object') {


    const liancaiTopCategory = String(rowOrProductName.liancai_top_category || '').trim()


    if (liancaiTopCategory) return liancaiTopCategory


    const liancaiSubcategory = String(rowOrProductName.liancai_subcategory || '').trim()


    if (liancaiSubcategory && liancaiSubcategory !== '全部') return liancaiSubcategory


    const value = String(rowOrProductName.product_name || '')


    if (/鱼|虾|蟹|水产|带鱼|鲈鱼|鲤鱼/.test(value)) return '水产'







    if (/蛋|鸡|鸭|肉|牛|羊|猪/.test(value)) return '禽肉蛋'







    if (/米|面|油|调料|酱|醋/.test(value)) return '粮油干调'







    if (/苹果|梨|瓜|桃|橙|水果/.test(value)) return '水果'







    return '蔬菜'







  }







  const value = String(rowOrProductName || '')







  if (/鱼|虾|蟹|水产|带鱼|鲈鱼|鲤鱼/.test(value)) return '水产'







  if (/蛋|鸡|鸭|肉|牛|羊|猪/.test(value)) return '禽肉蛋'







  if (/米|面|油|调料|酱|醋/.test(value)) return '粮油干调'







  if (/苹果|梨|瓜|桃|橙|水果/.test(value)) return '水果'







  return '蔬菜'







}















function inferThumbTone(rowOrProductName?: { product_name?: string | null; liancai_top_category?: string | null; liancai_subcategory?: string | null } | string | null) {
  const category = inferMarketCategory(rowOrProductName)
  const topCategory =
    typeof rowOrProductName === 'object' && rowOrProductName
      ? String(rowOrProductName.liancai_top_category || '').trim()
      : ''
  const productName = typeof rowOrProductName === 'object' && rowOrProductName ? rowOrProductName.product_name : rowOrProductName
  const text = `${productName || ''}${category}${topCategory}`.replace(/\s+/g, '')
  if (/垃圾桶|收纳箱|包装|餐具|清洁|用品|耗材|纸巾|手套|托盘|保鲜膜|垃圾袋|易耗/.test(text)) return 'kitchen'
  if (/鲜活水产|水产|海鲜|鱼|虾|蟹|带鱼|鲜鱼|鲈|鲤|贝|螺/.test(text)) return 'fish'
  if (/禽蛋|鸡蛋|鸭蛋|鹌鹑|蛋/.test(text)) return 'egg'
  if (/鲜禽|鲜猪肉|牛羊肉|猪|牛|羊|鸡|鸭|鹅|肉|排|里脊|五花|禽肉蛋/.test(text)) return 'meat'
  if (/水果|苹果|梨|香蕉|橙|橘|柑|葡萄|西瓜|哈密瓜|草莓|桃|芒果/.test(text)) return 'fruit'
  if (/豆制品|豆腐|豆皮|腐竹|豆干/.test(text)) return 'soy'
  if (/米面粮油|粮油干调|米|面|豆油|食用油|面粉|挂面|杂粮/.test(text)) return 'grain'
  if (/干调|调味品|调味|香辛|辣椒|花椒|八角|孜然|酱|醋|料酒|盐|糖/.test(text)) return 'dry'
  if (/冻|冻品|丸|肠|半成品|速冻/.test(text)) return 'frozen'
  if (/酒|饮料|牛奶|酸奶|乳/.test(text)) return 'drink'
  if (/土豆|马铃薯|薯/.test(text)) return 'potato'
  if (/黄瓜|瓜/.test(text)) return 'cuke'
  if (/菠菜|白菜|叶|青菜|蔬菜/.test(text)) return 'leaf'
  return 'greens'
}








function moduleStatusTone(value: string) {







  if (/异常|风险|缺货|权限异常|无效/.test(value)) return 'danger'







  if (/待|审批|关注|复核|确认|部分|重复|观察/.test(value)) return 'warn'







  if (/已|启用|正常|通过|完成|入库|下单|低价机会|有效|稳定/.test(value)) return 'success'







  return 'blue'







}















</script>















<style scoped>







.pcw{min-height:100vh;display:grid;grid-template-columns:236px minmax(0,1fr);background:radial-gradient(circle at 18% 0,rgba(37,99,235,.12),transparent 32%),linear-gradient(180deg,#f1f5fb 0%,#eaf1f8 100%);color:#12213c;font-family:"Fira Sans","PingFang SC","Microsoft YaHei",sans-serif}







.pcw button{font:inherit;cursor:pointer}.pcw-side{display:grid;grid-template-rows:auto 1fr auto;gap:18px;padding:18px 14px;border-right:1px solid rgba(15,23,42,.08);background:linear-gradient(180deg,#10233f 0%,#172c4c 58%,#0f1c32 100%);box-shadow:14px 0 34px rgba(15,23,42,.14)}.pcw-side-head,.pcw-location,.pcw-top,.pcw-card-head,.pcw-product,.pcw-pages,.pcw-legend{display:flex;align-items:center}.pcw-side-head{gap:10px;height:42px}.pcw-logo{display:grid;place-items:center;width:34px;height:34px;border-radius:11px;background:linear-gradient(135deg,#60a5fa,#2563eb);color:#fff;font-weight:800;box-shadow:0 12px 24px rgba(37,99,235,.32)}.pcw-nav{display:grid;gap:8px}.pcw-nav-item{display:grid;grid-template-columns:18px 1fr auto;gap:10px;align-items:center;height:44px;padding:0 12px;border:1px solid transparent;border-radius:12px;background:transparent;color:#b8c7da;text-align:left;transition:background .18s ease,border-color .18s ease,color .18s ease,transform .18s ease}.pcw-nav-item:hover{background:rgba(255,255,255,.08);color:#fff}.pcw-nav-item.active{background:linear-gradient(135deg,#2563eb,#1d4ed8);border-color:rgba(147,197,253,.38);color:#fff;box-shadow:0 14px 28px rgba(37,99,235,.34);transform:translateX(2px)}.pcw-nav-icon{width:15px;height:15px;border:1.8px solid currentColor;border-radius:4px}.pcw-nav-item b{display:grid;place-items:center;min-width:18px;height:18px;border-radius:999px;background:#ef4444;color:#fff;font-size:11px}.pcw-side-systems{display:grid;gap:8px}.pcw-system{display:grid;gap:3px;padding:11px 12px;border:1px solid rgba(148,163,184,.22);border-radius:12px;background:rgba(255,255,255,.08);color:#dbeafe;text-align:left}.pcw-system.primary{background:rgba(37,99,235,.22);border-color:rgba(147,197,253,.34)}.pcw-system span{color:#9fb2ca;font-size:11px}.pcw-system strong{font-size:13px;color:#fff}







.pcw-app{min-width:0;display:grid;grid-template-rows:64px 1fr}.pcw-top{gap:20px;padding:0 24px;border-bottom:1px solid rgba(226,232,240,.86);background:rgba(255,255,255,.86);backdrop-filter:blur(18px);box-shadow:0 10px 28px rgba(15,23,42,.05)}.pcw-location{gap:8px;min-width:170px}.pcw-pin{width:16px;height:16px;border-radius:50%;background:#2563eb;box-shadow:inset 0 0 0 5px #dbeafe}.pcw-menu{width:34px;height:34px;border:0;background:linear-gradient(#4b5870,#4b5870) center/16px 2px no-repeat}.pcw-top h1{margin:0;flex:1;font-size:20px;letter-spacing:0}.pcw-top-actions{display:flex;align-items:center;gap:12px}.pcw-top-actions button{min-height:34px;border:0;background:transparent;color:#3c4d66}.pcw-top-actions span{margin-left:4px;padding:1px 6px;border-radius:999px;background:#ef4444;color:#fff;font-size:10px}.pcw-user{padding:0 12px!important;border-radius:999px!important;background:#f1f5f9!important}







.pcw-main{display:grid;gap:16px;padding:22px;overflow:auto}.pcw-filter{display:grid;grid-template-columns:repeat(4,132px) 1fr;gap:12px;padding:14px;border:1px solid rgba(148,163,184,.22);border-radius:16px;background:rgba(255,255,255,.9);box-shadow:0 14px 34px rgba(15,23,42,.06)}.pcw-filter.is-trend{grid-template-columns:180px 230px 180px 1fr auto 126px}.pcw-filter.is-alert,.pcw-filter.is-module{grid-template-columns:132px 132px 132px 132px 132px 1fr}.pcw-filter button{height:38px;border:1px solid #dfe6ef;border-radius:10px;background:#fff;color:#22324a;box-shadow:0 3px 10px rgba(15,23,42,.04)}.pcw-filter .pcw-export{justify-self:end;width:104px}.pcw-filter.is-trend .pcw-export{width:126px}.pcw-price-toggle{display:flex;justify-self:end}.pcw-price-toggle button{min-width:70px;border-radius:0}.pcw-price-toggle button:first-child{border-radius:6px 0 0 6px}.pcw-price-toggle button:last-child{border-radius:0 6px 6px 0}.pcw-price-toggle button.active{background:#2563eb;border-color:#2563eb;color:#fff}.pcw-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));border:1px solid rgba(148,163,184,.2);border-radius:18px;background:rgba(255,255,255,.92);box-shadow:0 18px 40px rgba(15,23,42,.07);overflow:hidden}.pcw-kpis article{display:grid;gap:8px;padding:18px 22px;border-right:1px solid #e8edf4;background:linear-gradient(180deg,rgba(255,255,255,.96),rgba(248,250,252,.9))}.pcw-kpis article:last-child{border-right:0}.pcw-kpis span,.pcw-card-head span,.pcw-card-head button,.pcw-kpis small,th,td{color:#607089;font-size:12px}.pcw-kpis strong{font-size:28px;line-height:1;color:#142542}.up,.rise{color:#ef4444!important}.down,.fall{color:#16a34a!important}.warn{color:#f97316!important}.blue{color:#2563eb!important}.green{color:#16a34a!important}







.pcw-grid{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:12px;align-items:start}.pcw-card{min-width:0;border:1px solid #e2e8f0;border-radius:8px;background:#fff}.pcw-card-head{justify-content:space-between;gap:12px;height:42px;padding:0 16px;border-bottom:1px solid #edf1f6}.pcw-card-head h2{margin:0;font-size:16px;letter-spacing:0}.pcw-card-head button{border:0;background:transparent}.pcw-table-card{overflow:hidden}table{width:100%;border-collapse:collapse}th{height:34px;background:#f8fafc;font-weight:600;text-align:left}th,td{padding:0 12px;border-bottom:1px solid #edf1f6;white-space:nowrap}td{height:40px;color:#24344d}.pcw-product{gap:10px;padding:0;border:0;background:transparent;color:#172641}.pcw-thumb{width:26px;height:26px;border-radius:7px;background:#dcfce7}.pcw-thumb.greens{background:linear-gradient(135deg,#2f8d46,#dcfce7)}.pcw-thumb.fish{background:linear-gradient(135deg,#64748b,#e2e8f0)}.pcw-thumb.leaf{background:linear-gradient(135deg,#16a34a,#bbf7d0)}.pcw-thumb.cuke{background:linear-gradient(135deg,#15803d,#d9f99d)}.pcw-thumb.potato{background:linear-gradient(135deg,#ca8a04,#fef3c7)}.pcw-thumb.egg{background:linear-gradient(135deg,#f59e0b,#ffedd5)}.pcw-link{border:0;background:transparent;color:#2563eb;font-weight:700}.pcw-pages{gap:8px;padding:11px 16px}.pcw-pages button{width:30px;height:30px;border:1px solid #dfe6ef;border-radius:6px;background:#fff;color:#4b5d75}.pcw-pages button.active{border-color:#2563eb;color:#2563eb}.pcw-pages em{margin-left:18px;color:#52627a;font-style:normal;font-size:12px}







.pcw-right{display:grid;gap:12px}.pcw-right-table{table-layout:fixed}.pcw-right-table th,.pcw-right-table td{height:36px;padding:0 10px;overflow:hidden;text-overflow:ellipsis}.pcw-right-table th:nth-child(1){width:52%}.pcw-right-table th:nth-child(2){width:30%}.pcw-right-table th:nth-child(3){width:18%;text-align:right}.pcw-right-table td:nth-child(3){text-align:right}.pcw-right-table td:first-child{display:grid;grid-template-columns:auto minmax(0,1fr);align-items:center;gap:8px}.pcw-right-table td:first-child strong{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#142542;font-size:13px}.pcw-right-tag{display:inline-flex;align-items:center;height:20px;padding:0 6px;border-radius:4px;background:#ecfdf5;color:#16a34a;font-size:10px;font-weight:800}.pcw-chart{position:relative;display:grid;overflow:hidden;min-height:232px;padding-bottom:0}.pcw-legend{gap:18px;padding:10px 16px}.pcw-legend span{font-size:11px}.pcw-legend span:before{content:"";display:inline-block;width:16px;height:4px;margin-right:6px;border-radius:999px;background:currentColor;vertical-align:middle}.pcw-chart svg{width:100%;height:150px;padding:0 10px}.grid path{fill:none;stroke:#e8edf4;stroke-width:1}.line-blue,.line-green{fill:none;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}.line-blue{stroke:#2563eb}.line-green{stroke:#16a34a}.dots circle{fill:#2563eb}.pcw-axis.mini text{fill:#7a899e;font-size:9px}.pcw-chart-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:8px 14px 10px;border-top:1px solid #edf1f6;background:#fbfdff}.pcw-chart-foot span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#64748b;font-size:12px}.pcw-chart-foot button{border:0;background:transparent;color:#2563eb;font-size:12px;font-weight:800}.pcw-chart-empty.mini{top:53%;width:min(276px,76%);padding:11px 14px}







.pcw-bottom{display:grid;grid-template-columns:minmax(0,1fr) 420px;gap:12px}.pcw-timeline,.pcw-alerts{padding-bottom:12px}.pcw-timeline p,.pcw-alerts p{margin:0 16px;padding:10px 0;border-bottom:1px solid #edf1f6;color:#24344d;font-size:13px}.pcw-timeline span{display:inline-block;width:52px;color:#7a899e}.pcw-alerts p{display:grid;grid-template-columns:1fr auto auto;gap:12px;border-left:3px solid #ef4444;padding-left:10px}.pcw-alerts p.fall{border-left-color:#16a34a}.pcw-alerts p.warn{border-left-color:#f97316}.pcw-alerts small{color:#7a899e}.pcw-module-hero{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:18px 20px;background:linear-gradient(135deg,#fff,#f8fbff)}.pcw-module-hero span{color:#2563eb;font-size:12px;font-weight:700}.pcw-module-hero h2{margin:5px 0 6px;font-size:22px;letter-spacing:0;color:#142542}.pcw-module-hero p{max-width:760px;margin:0;color:#607089;font-size:13px;line-height:1.55}.pcw-module-hero button{height:36px;min-width:96px;border:1px solid #bfdbfe;border-radius:6px;background:#2563eb;color:#fff;font-weight:700}.pcw-module-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.pcw-module-kpis article{display:grid;gap:8px;padding:16px 18px}.pcw-module-kpis span,.pcw-module-kpis small{color:#607089;font-size:12px}.pcw-module-kpis strong{font-size:24px;color:#142542;line-height:1}.pcw-module-grid{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:12px;align-items:start}.pcw-module-table{overflow:hidden}.pcw-module-table table{table-layout:fixed}.pcw-module-table th,.pcw-module-table td{padding:0 10px}.pcw-module-table td span:not(.pcw-module-progress):not(.pcw-module-status){display:inline-block;max-width:100%;overflow:hidden;text-overflow:ellipsis;vertical-align:middle}.pcw-module-table tr.is-empty td{height:58px;background:#fbfdff;color:#94a3b8}.pcw-module-table tr.is-empty .pcw-module-name{font-weight:700;color:#64748b}.pcw-module-name{font-weight:700;color:#142542}.pcw-module-status{display:inline-flex;align-items:center;min-height:24px;padding:0 9px;border-radius:999px;background:#eff6ff;color:#2563eb;font-weight:700;font-size:11px}.pcw-module-side{display:grid;gap:12px}.pcw-module-panel article{display:grid;gap:6px;margin:0 14px;padding:12px 0;border-bottom:1px solid #edf1f6}.pcw-module-panel article span{width:max-content;padding:2px 7px;border-radius:4px;background:#eff6ff;color:#2563eb;font-size:10px;font-weight:700}.pcw-module-panel article span.green,.pcw-module-panel article span.down,.pcw-module-panel article span.fall{background:#ecfdf5;color:#16a34a}.pcw-module-panel article span.warn,.pcw-module-panel article span.up,.pcw-module-panel article span.rise{background:#fff7ed;color:#f97316}.pcw-module-panel article strong{color:#142542;font-size:14px}.pcw-module-panel article small{color:#607089;font-size:12px;line-height:1.45}.pcw-module-flow{padding-bottom:10px}.pcw-module-flow p{display:grid;grid-template-columns:54px 1fr;gap:10px;align-items:start;margin:0 16px;padding:11px 0;border-bottom:1px solid #edf1f6}.pcw-module-flow b{color:#2563eb;font-size:12px}.pcw-module-flow span{color:#34445d;font-size:13px;line-height:1.45}







.pcw-module-status.success{background:#ecfdf5;color:#16a34a}.pcw-module-status.warn{background:#fff7ed;color:#f97316}.pcw-module-status.danger{background:#fef2f2;color:#dc2626}.pcw-module-progress{position:relative;display:grid;grid-template-columns:minmax(68px,1fr) 38px;gap:8px;align-items:center;min-width:110px}.pcw-module-progress:before{content:"";grid-column:1;grid-row:1;height:6px;border-radius:999px;background:#e2e8f0}.pcw-module-progress i{grid-column:1;grid-row:1;display:block;height:6px;max-width:100%;border-radius:999px;background:#2563eb}.pcw-module-progress em{color:#52627a;font-style:normal;font-size:12px}







.pcw-module-actions{display:flex;align-items:center;gap:10px}.pcw-module-actions button{height:36px;min-width:92px;border:1px solid #dbe4f0;border-radius:6px;background:#fff;color:#24344d;font-weight:700}.pcw-module-actions button.primary{background:#2563eb;border-color:#2563eb;color:#fff}.pcw-module-grid{grid-template-areas:"table side" "chart side" "activity activity"}.pcw-module-table{grid-area:table}.pcw-module-side{grid-area:side}.pcw-module-chart-panel{grid-area:chart}.pcw-module-activity{grid-area:activity}.pcw-module-chart-panel svg{width:100%;height:228px;padding:0 16px 12px}.pcw-module-bars rect:nth-child(odd){fill:#bfdbfe}.pcw-module-bars rect:nth-child(even){fill:#bbf7d0}.pcw-module-chart-panel .line-blue{stroke-width:3.2}.pcw-module-chart-panel .line-green{stroke-width:2.4}.pcw-module-activity{display:grid;padding-bottom:4px}.pcw-module-activity article{display:grid;grid-template-columns:76px 1fr 76px;gap:12px;align-items:center;margin:0 16px;padding:11px 0;border-bottom:1px solid #edf1f6}.pcw-module-activity b{color:#2563eb;font-size:12px}.pcw-module-activity span{color:#24344d;font-size:13px}.pcw-module-activity em{justify-self:end;color:#16a34a;font-style:normal;font-size:12px;font-weight:700}.pcw-module-market .pcw-module-hero{background:linear-gradient(135deg,#fff,#f1f7ff)}.pcw-module-suppliers .pcw-module-hero,.pcw-module-purchase .pcw-module-hero{background:linear-gradient(135deg,#fff,#f4fbf6)}.pcw-module-quotes .pcw-module-hero,.pcw-module-reports .pcw-module-hero{background:linear-gradient(135deg,#fff,#f8fbff)}.pcw-module-settings .pcw-module-hero{background:linear-gradient(135deg,#fff,#fff7ed)}







.pcw-action-toast{position:fixed;right:28px;bottom:24px;z-index:20;padding:10px 14px;border:1px solid #bfdbfe;border-radius:8px;background:#eff6ff;color:#1d4ed8;font-size:13px;font-weight:800;box-shadow:0 12px 28px rgba(37,99,235,.14);pointer-events:none}







.pcw-action-overlay{position:fixed;inset:0;z-index:40;display:grid;justify-content:end;background:rgba(15,23,42,.24);backdrop-filter:blur(4px)}







.pcw-action-panel{display:grid;grid-template-rows:auto 1fr auto;width:min(430px,calc(100vw - 32px));height:100%;background:#fff;box-shadow:-24px 0 42px rgba(15,23,42,.18)}







.pcw-action-panel header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:22px;border-bottom:1px solid #e8eef7}







.pcw-action-panel header span{color:#2563eb;font-size:12px;font-weight:800}







.pcw-action-panel header h2{margin:6px 0 8px;color:#101c31;font-size:20px;letter-spacing:0}







.pcw-action-panel header p{margin:0;color:#607089;font-size:13px;line-height:1.55}







.pcw-action-panel header button{display:grid;place-items:center;width:32px;height:32px;border:1px solid #dbe5f1;border-radius:8px;background:#fff;color:#40516b;font-size:22px;line-height:1}







.pcw-action-panel-body{display:grid;align-content:start;gap:10px;padding:18px 22px;overflow:auto;background:#f8fbff}







.pcw-action-panel-body article{display:grid;gap:6px;padding:13px 14px;border:1px solid #dfe7f1;border-radius:8px;background:#fff}







.pcw-action-panel-body span{color:#64748b;font-size:12px}







.pcw-action-panel-body strong{color:#142542;font-size:14px;line-height:1.45;word-break:break-word}







.pcw-action-panel footer{display:flex;justify-content:flex-end;gap:10px;padding:16px 22px;border-top:1px solid #e8eef7;background:#fff}







.pcw-action-panel footer button{height:36px;min-width:88px;border:1px solid #dbe5f1;border-radius:7px;background:#fff;color:#24344d;font-weight:800}







.pcw-action-panel footer button.primary{border-color:#2563eb;background:#2563eb;color:#fff}







.pcw-filter-item{position:relative;min-width:0}.pcw-filter-item>button{display:flex!important;align-items:center;justify-content:space-between;gap:10px;width:100%}.pcw-filter-item>button small{font-size:11px;color:#7b8aa0}.pcw-filter-item>button.open{border-color:#2563eb;color:#1d4ed8;box-shadow:0 0 0 3px #eff6ff}.pcw-filter-menu{position:absolute;top:44px;left:0;z-index:20;display:grid;gap:4px;width:max(180px,100%);max-height:260px;padding:8px;border:1px solid #dbe5f1;border-radius:8px;background:#fff;box-shadow:0 18px 38px rgba(15,23,42,.14);overflow:auto}.pcw-filter-search{height:34px;margin-bottom:4px;padding:0 10px;border:1px solid #dbe5f1;border-radius:6px;background:#f8fafc;color:#10203d;font:inherit;font-size:12px;outline:none}.pcw-filter-search:focus{border-color:#2563eb;background:#fff;box-shadow:0 0 0 3px #eff6ff}.pcw-filter-menu button{height:auto;min-height:34px;padding:8px 10px;border:0;border-radius:6px;background:#fff;color:#24344d;text-align:left;box-shadow:none}.pcw-filter-menu button:hover,.pcw-filter-menu button.selected{background:#eff6ff;color:#1d4ed8;font-weight:800}







.pcw-table-card table{table-layout:fixed}.pcw-table-card th,.pcw-table-card td{overflow:hidden;text-overflow:ellipsis}.pcw-table-card th:nth-child(1){width:128px}.pcw-table-card th:nth-child(2){width:78px}.pcw-table-card th:nth-child(3){width:150px}.pcw-table-card th:nth-child(4),.pcw-table-card th:nth-child(5){width:118px}.pcw-table-card th:nth-child(6),.pcw-table-card th:nth-child(7),.pcw-table-card th:nth-child(8),.pcw-table-card th:nth-child(9){width:78px}







.pcw-location{position:relative}.pcw-location-button{display:flex;align-items:center;gap:8px;min-width:0;height:38px;padding:0;border:0;background:transparent;color:#172641;text-align:left}.pcw-location-button strong{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pcw-location-button:hover strong,.pcw-location-button[aria-expanded="true"] strong{color:#2563eb}.pcw-location-button:focus{outline:0}.pcw-location-button:focus-visible{border-radius:8px;box-shadow:0 0 0 3px #eff6ff}.pcw-location-menu{position:absolute;top:46px;left:0;z-index:30;display:grid;gap:4px;width:max(190px,100%);max-height:260px;padding:8px;border:1px solid #dbe5f1;border-radius:8px;background:#fff;box-shadow:0 18px 38px rgba(15,23,42,.14);overflow:auto}.pcw-location-menu button{min-height:34px;padding:8px 10px;border:0;border-radius:6px;background:#fff;color:#24344d;text-align:left}.pcw-location-menu button:hover,.pcw-location-menu button.selected{background:#eff6ff;color:#1d4ed8;font-weight:800}.pcw-location-suggest{min-height:34px;padding:8px 10px;border:1px dashed #cfe2ff!important;border-radius:8px!important;background:#f8fbff!important;color:#1d4ed8!important;font-weight:800;text-align:center!important}.pcw-location-more{min-height:34px;padding:8px 10px;border:1px dashed #cfe2ff!important;border-radius:8px!important;background:#f8fbff!important;color:#1d4ed8!important;font-weight:800;text-align:center!important}.pcw-location-menu-group-label{padding:6px 10px 2px;color:#64748b;font-size:11px;font-weight:800;letter-spacing:.04em}

.pcw-app{overflow:visible}
.pcw-top{overflow:visible;z-index:35}
.pcw-location-menu,.pcw-filter-menu{z-index:70}







.pcw-message-list{display:grid;align-content:start;gap:10px;padding:18px 22px;overflow:auto;background:#f8fbff}.pcw-message-list button{display:grid;gap:6px;width:100%;padding:14px;border:1px solid #dfe7f1;border-radius:8px;background:#fff;text-align:left}.pcw-message-list button.warn{border-color:#fed7aa;background:#fff7ed}.pcw-message-list button.green{border-color:#bbf7d0;background:#f0fdf4}.pcw-message-list span{font-size:12px;font-weight:800;color:#2563eb}.pcw-message-list strong{font-size:15px;color:#10203d}.pcw-message-list small{font-size:12px;line-height:1.45;color:#607089}







.pcw-alert-settings-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding:18px 22px;background:#f8fbff}.pcw-alert-settings-form label{display:grid;gap:8px;padding:12px;border:1px solid #dfe7f1;border-radius:8px;background:#fff}.pcw-alert-settings-form span{font-size:12px;font-weight:800;color:#40516b}.pcw-alert-settings-form input,.pcw-alert-settings-form select{height:36px;padding:0 10px;border:1px solid #dbe5f1;border-radius:6px;color:#10203d;background:#fff}.pcw-alert-settings-preview{display:grid;gap:10px;padding:0 22px 18px;background:#f8fbff}.pcw-alert-settings-preview article{display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:center;padding:12px 14px;border:1px solid #dfe7f1;border-radius:8px;background:#fff}.pcw-alert-settings-preview span,.pcw-alert-settings-preview small{font-size:12px;color:#607089}.pcw-alert-settings-preview strong{font-size:14px}







.pcw-row-actions{display:inline-flex!important;align-items:center;gap:8px}







.pcw-row-actions button{height:26px;padding:0;border:0;background:transparent;color:#2563eb;font-size:12px;font-weight:800}







.pcw-row-actions button:hover{text-decoration:underline}









.pcw-side{box-shadow:8px 0 24px rgba(15,23,42,.03)}.pcw-side-head strong{font-size:18px;letter-spacing:.2px;color:#0f1f3d}.pcw-logo{box-shadow:0 10px 18px rgba(37,99,235,.22)}.pcw-nav{gap:6px}.pcw-nav-item{position:relative;min-height:44px;color:#31415c;transition:background-color .18s ease,color .18s ease,box-shadow .18s ease}.pcw-nav-item:hover{background:#f3f7ff;color:#2563eb}.pcw-nav-item.active,.pcw-nav-item.active:hover{background:#2563eb;color:#fff;box-shadow:0 12px 22px rgba(37,99,235,.22)}.pcw-nav-item.active:after{content:"";position:absolute;right:10px;width:4px;height:4px;border-radius:999px;background:rgba(255,255,255,.8)}.pcw-nav-icon{display:inline-block;justify-self:center}.pcw-top{box-shadow:0 1px 0 rgba(15,23,42,.02)}.pcw-location{position:relative;padding-right:22px}.pcw-location:after{content:"";position:absolute;right:0;width:1px;height:22px;background:#d8e0ea}.pcw-top-actions button{position:relative;padding:0 6px;border-radius:6px}.pcw-top-actions button:hover{background:#f3f6fb;color:#2563eb}.pcw-user{min-width:76px}.pcw-filter{align-items:center;min-height:66px;box-shadow:0 8px 20px rgba(15,23,42,.025)}.pcw-filter button{position:relative;text-align:left;padding:0 14px;font-weight:500;white-space:nowrap;transition:border-color .18s ease,box-shadow .18s ease,color .18s ease}.pcw-filter button:not(.pcw-export):hover{border-color:#bfd2ff;color:#2563eb;box-shadow:0 0 0 3px #eff6ff}.pcw-filter .pcw-export{display:inline-flex;align-items:center;justify-content:center;gap:7px;width:126px;min-width:126px;text-align:center;font-weight:700;line-height:1}.pcw-filter .pcw-export:before{content:"";flex:0 0 auto;width:12px;height:12px;border:1.7px solid currentColor;border-top:0;border-radius:0 0 2px 2px;background:linear-gradient(currentColor,currentColor) center 1px/1.7px 8px no-repeat}.pcw-kpis{min-height:114px;box-shadow:0 8px 20px rgba(15,23,42,.025)}.pcw-kpis article{justify-content:center}.pcw-kpis strong{font-weight:800;letter-spacing:.2px}.pcw-card{box-shadow:0 8px 20px rgba(15,23,42,.025)}.pcw-card-head h2{font-weight:800;color:#12213c}.pcw-card-head button:hover{color:#2563eb}tbody tr{transition:background-color .16s ease}tbody tr:hover{background:#fbfdff}th{color:#5b6b82}td{color:#10203d}.pcw-product strong,.pcw-module-name{font-weight:800}.pcw-link:hover{text-decoration:underline}.pcw-thumb{position:relative;overflow:hidden;box-shadow:inset 0 0 0 1px rgba(255,255,255,.65),0 2px 5px rgba(15,23,42,.12)}.pcw-thumb:before,.pcw-thumb:after{content:"";position:absolute;border-radius:999px;background:rgba(255,255,255,.62)}.pcw-thumb:before{width:14px;height:8px;left:5px;top:6px;transform:rotate(-18deg)}.pcw-thumb:after{width:10px;height:5px;right:4px;bottom:6px;transform:rotate(20deg)}.pcw-thumb.fish:before{width:15px;height:7px;left:5px;top:9px}.pcw-thumb.fish:after{right:3px;bottom:8px;width:6px;height:6px;clip-path:polygon(0 50%,100% 0,100% 100%)}.pcw-thumb.egg:before,.pcw-thumb.potato:before{width:9px;height:11px;left:5px;top:7px}.pcw-thumb.egg:after,.pcw-thumb.potato:after{width:9px;height:10px;right:5px;bottom:5px}.pcw-module-panel article:last-child,.pcw-module-flow p:last-child,.pcw-module-activity article:last-child,.pcw-quotes article:last-child,.pcw-timeline p:last-child,.pcw-alerts p:last-child{border-bottom:0}







.pcw{grid-template-columns:220px minmax(0,1fr)}







.pcw-side{position:sticky;top:0;height:100vh;min-height:0;box-sizing:border-box;gap:12px;padding:18px 12px 16px;border-right-color:#dfe7f1;background:linear-gradient(180deg,#fff 0%,#fff 78%,#fbfdff 100%);box-shadow:7px 0 22px rgba(15,23,42,.035)}







.pcw-side-head{height:44px;padding:0 4px}







.pcw-side-head strong{font-size:18px;line-height:32px;letter-spacing:0;color:#0f1f3d}







.pcw-logo{width:32px;height:32px;border-radius:10px;background:linear-gradient(135deg,#1d4ed8,#3b82f6);box-shadow:0 10px 18px rgba(37,99,235,.22);font-size:16px;line-height:1}







.pcw-nav{align-content:start;gap:24px;min-height:0;padding-top:22px;overflow:auto;scrollbar-width:none}







.pcw-nav::-webkit-scrollbar{display:none}







.pcw-nav-group{display:grid;gap:20px}







.pcw-nav-group>span{display:none}







.pcw-nav-item{position:relative;grid-template-columns:18px minmax(0,1fr) auto;gap:12px;align-items:center;height:42px;min-height:42px;padding:0 12px;border:1px solid transparent;border-radius:7px;background:transparent;color:#334155;font-size:14px;font-weight:500;line-height:42px;letter-spacing:0;transition:background-color .16s ease,border-color .16s ease,color .16s ease,box-shadow .16s ease,transform .12s ease}







.pcw-nav-item:hover{border-color:transparent;background:#f8fbff;color:#2563eb}







.pcw-nav-item:active{transform:translateY(1px)}







.pcw-nav-item:focus{outline:0}







.pcw-nav-item:focus-visible{border-color:#bfdbfe;box-shadow:0 0 0 3px #eff6ff}







.pcw-nav-item.active,.pcw-nav-item.active:hover{border-color:#2563eb;background:#2563eb;color:#fff;box-shadow:0 9px 18px rgba(37,99,235,.2);transform:none}







.pcw-nav-item.active:before{content:none}







.pcw-nav-item.active:after{content:none}







.pcw-nav-item>span:not(.pcw-nav-icon){min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}







.pcw-nav-icon{display:grid!important;place-items:center;width:15px!important;height:15px!important;border:1.7px solid currentColor!important;border-radius:4px!important}







.pcw-nav-icon:before,.pcw-nav-icon:after{content:none!important}







.pcw-nav-icon svg{display:none}







.pcw-nav-icon path{fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}







.pcw-nav-item b{display:grid;place-items:center;min-width:18px;height:18px;padding:0 5px;border-radius:999px;background:#ef4444;color:#fff;font-size:11px;font-weight:800;line-height:18px;box-shadow:0 4px 10px rgba(239,68,68,.22)}







.pcw-side-systems{gap:7px;padding-top:10px;border-top:1px solid #edf2f7}







.pcw-system{position:relative;gap:2px;min-height:46px;padding:8px 10px;border-color:#dbe4ef;background:#f8fafc;border-radius:8px;transition:background-color .16s ease,border-color .16s ease,box-shadow .16s ease,transform .12s ease}







.pcw-system:hover{border-color:#bfdbfe;background:#f3f7ff}







.pcw-system:active{transform:translateY(1px)}







.pcw-system:focus{outline:0}







.pcw-system:focus-visible{border-color:#bfdbfe;box-shadow:0 0 0 3px #eff6ff}







.pcw-system.primary{background:#eef6ff;border-color:#bfdbfe;box-shadow:inset 3px 0 0 #2563eb}







.pcw-system span{font-size:11px;line-height:14px;color:#64748b}







.pcw-system strong{font-size:13px;line-height:18px;color:#0f172a}







.pcw-main{align-content:start}







.pcw-filter{min-height:64px}







.pcw-empty-row:hover{background:transparent}







.pcw-empty-row td{height:88px;padding:0 16px;background:#fbfdff;text-align:center}







.pcw-empty-row.compact td{height:72px}







.pcw-empty-state,.pcw-panel-empty{display:grid;place-items:center;gap:6px;color:#64748b}







.pcw-empty-state strong,.pcw-panel-empty strong{color:#334155;font-size:13px}







.pcw-empty-state span,.pcw-panel-empty span{color:#94a3b8;font-size:12px}







.pcw-panel-empty{min-height:96px;margin:0 14px}







.pcw-panel-empty.compact{min-height:74px}







.pcw-timeline .pcw-panel-empty span,.pcw-alerts .pcw-panel-empty span{display:block;width:auto;color:#94a3b8}







.pcw-module-table .pcw-empty-row td:first-child{display:table-cell;font-weight:400;color:#64748b}







.pcw-module-table .pcw-empty-row td{height:76px}







.pcw-module-panel .pcw-panel-empty,.pcw-module-flow .pcw-panel-empty,.pcw-module-activity .pcw-panel-empty{margin:0 14px}







.pcw-module-panel .pcw-panel-empty span,.pcw-module-flow .pcw-panel-empty span,.pcw-module-activity .pcw-panel-empty span{display:block;width:auto;color:#94a3b8}







.pcw-module-chart-panel{position:relative;overflow:hidden;min-height:314px}







.pcw-chart-empty.module{top:58%;width:min(390px,74%)}







.pcw-trend-chart-card{position:relative;overflow:hidden}







.pcw-chart-empty{position:absolute;left:50%;top:55%;display:grid;gap:7px;width:min(360px,70%);padding:15px 18px;border:1px solid #e2e8f0;border-radius:10px;background:rgba(255,255,255,.9);box-shadow:0 12px 28px rgba(15,23,42,.08);text-align:center;transform:translate(-50%,-50%)}







.pcw-chart-empty strong{color:#334155;font-size:14px}







.pcw-chart-empty span{color:#94a3b8;font-size:12px;line-height:1.55}







.pcw-chart-empty button{justify-self:center;height:30px;padding:0 12px;border:1px solid #bfd2ff;border-radius:6px;background:#eef4ff;color:#2563eb;font-size:12px;font-weight:800}







.pcw-chart-empty.mini{top:60%;width:min(292px,76%);padding:12px 14px}







.pcw-chart-empty.alert{top:58%;width:min(380px,72%)}







.pcw-trend-readiness{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:-12px 16px 16px}







.pcw-trend-readiness article{display:grid;gap:5px;min-width:0;padding:10px 12px;border:1px solid #e2e8f0;border-radius:8px;background:#fbfdff}







.pcw-trend-readiness span{color:#64748b;font-size:11px;font-weight:700}







.pcw-trend-readiness strong{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#13233d;font-size:16px;line-height:20px}







.pcw-trend-readiness small{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#7a899e;font-size:11px}







.pcw-trend-readiness article.blue{border-color:#dbeafe;background:#f8fbff}







.pcw-trend-readiness article.green{border-color:#dcfce7;background:#fbfffd}







.pcw-trend-readiness article.warn{border-color:#fed7aa;background:#fffaf5}







.pcw-trend-readiness article.muted{border-color:#e5e7eb;background:#f8fafc}







.pcw-trend-side .pcw-card-head{height:40px}







.pcw-trend-side th,.pcw-trend-side td{padding:0 10px}







.pcw-suggestion li{margin-bottom:4px}







.pcw-trend-dynamics .pcw-panel-empty span{display:block;width:auto;color:#94a3b8}







.pcw-alert-table-card .pcw-empty-row td:first-child{display:table-cell;font-weight:400;color:#64748b}







.pcw-alert-table-card .pcw-empty-row td{height:76px}







.pcw-alert-table-card table{table-layout:fixed}







.pcw-alert-col-product{width:92px}







.pcw-alert-col-market{width:74px}







.pcw-alert-col-type{width:82px}







.pcw-alert-col-value{width:92px}







.pcw-alert-col-owner{width:84px}







.pcw-alert-col-state{width:72px}







.pcw-alert-col-action{width:78px}







.pcw-alert-table-card th,.pcw-alert-table-card td{padding-inline:10px;overflow:hidden;text-overflow:ellipsis}







.pcw-alert-table-card td:first-child strong{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}







.pcw-alert-table-card .pcw-link{display:inline-flex;width:100%;justify-content:flex-start;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}







.pcw-brand-copy{display:grid;gap:1px;min-width:0}







.pcw-brand-copy strong{line-height:19px}







.pcw-brand-copy small{color:#94a3b8;font-size:10px;font-weight:700;line-height:12px;white-space:nowrap}







.pcw-side-sync{display:grid;gap:4px;padding:9px 10px;border:1px solid #e5edf6;border-radius:8px;background:linear-gradient(135deg,#f8fbff,#fff)}







.pcw-side-sync span{color:#64748b;font-size:11px;font-weight:700;line-height:14px}







.pcw-side-sync strong{color:#0f172a;font-size:13px;line-height:18px}







.pcw-menu{position:relative;display:grid;place-items:center;border-radius:10px!important;background:#f8fafc!important;transition:background-color .16s ease,box-shadow .16s ease,color .16s ease}







.pcw-menu span,.pcw-menu:before,.pcw-menu:after{content:"";display:block;width:16px;height:2px;border-radius:999px;background:#475569}







.pcw-menu:before{position:absolute;transform:translateY(-6px)}







.pcw-menu:after{position:absolute;transform:translateY(6px)}







.pcw-menu:hover{background:#eff6ff!important;box-shadow:0 0 0 3px #eff6ff}







.pcw-menu:hover span,.pcw-menu:hover:before,.pcw-menu:hover:after{background:#2563eb}







.pcw-top-actions button{display:inline-flex;align-items:center;justify-content:center;gap:4px;min-width:44px;transition:background-color .16s ease,color .16s ease,box-shadow .16s ease}







.pcw-top-actions button:focus{outline:0}







.pcw-top-actions button:focus-visible{box-shadow:0 0 0 3px #eff6ff;color:#2563eb}







.pcw-top-actions span{display:inline-grid;place-items:center;min-width:18px;height:18px;margin-left:2px;padding:0 5px;line-height:18px}







.pcw-filter button:focus{outline:0}







.pcw-filter button:focus-visible,.pcw-card-head button:focus-visible,.pcw-link:focus-visible,.pcw-product:focus-visible{outline:0;box-shadow:0 0 0 3px #eff6ff;border-radius:6px}







.pcw-filter button.active{border-color:#2563eb;background:#eff6ff;color:#1d4ed8;font-weight:800;box-shadow:inset 0 0 0 1px rgba(37,99,235,.08)}







.pcw-filter .pcw-export:before{content:none}







.pcw-card-head button:disabled{color:#cbd5e1;cursor:not-allowed}







.pcw-card-head button:disabled:hover{color:#cbd5e1}







.pcw-module-actions{flex:0 0 auto}







.pcw-module-actions button{transition:background-color .16s ease,border-color .16s ease,color .16s ease,box-shadow .16s ease,transform .12s ease}







.pcw-module-actions button:hover{border-color:#bfdbfe;box-shadow:0 0 0 3px #eff6ff;color:#2563eb}







.pcw-module-actions button:active{transform:translateY(1px)}







.pcw-module-actions button:focus{outline:0}







.pcw-module-actions button:focus-visible{box-shadow:0 0 0 3px #eff6ff}







.pcw-module-actions button.primary:hover{border-color:#1d4ed8;background:#1d4ed8;color:#fff}







.pcw-module-actions button.secondary{background:#fff;color:#334155}







.pcw-module-side .pcw-card{min-height:0}







.pcw-module-panel article,.pcw-module-flow p,.pcw-module-activity article{min-width:0}







.pcw-module-panel article strong,.pcw-module-panel article small,.pcw-module-flow span,.pcw-module-activity span{min-width:0;overflow:hidden;text-overflow:ellipsis}







.pcw-nav-item b{background:#ef4444;color:#fff;box-shadow:0 4px 10px rgba(239,68,68,.22)}







.pcw-nav-item.active b{background:#fff;color:#ef4444;box-shadow:none}







.pcw-brand-copy small{display:none}







.pcw-kpis article{align-content:center;justify-content:start;text-align:left}







.pcw-thumb{box-shadow:inset 0 0 0 1px rgba(255,255,255,.65)!important}







.pcw-thumb:before,.pcw-thumb:after{content:none!important}







.pcw-system.primary strong:after{content:"";display:inline-block;width:6px;height:6px;margin-left:6px;border-radius:999px;background:#16a34a;box-shadow:0 0 0 3px #dcfce7;vertical-align:1px}







.pcw-filter button.active{border-color:#dfe6ef;background:#fff;color:#22324a;font-weight:500;box-shadow:none}







.pcw-table-card table{table-layout:fixed}







.pcw-table-card th:nth-child(1),.pcw-table-card td:nth-child(1){width:114px}







.pcw-table-card th:nth-child(2),.pcw-table-card td:nth-child(2){width:62px}







.pcw-table-card th:nth-child(3),.pcw-table-card td:nth-child(3){width:142px}







.pcw-table-card th:nth-child(4),.pcw-table-card td:nth-child(4){width:100px}







.pcw-table-card th:nth-child(5),.pcw-table-card td:nth-child(5){width:100px}







.pcw-table-card th:nth-child(6),.pcw-table-card td:nth-child(6){width:50px}







.pcw-table-card th:nth-child(7),.pcw-table-card td:nth-child(7){width:60px}







.pcw-table-card th:nth-child(8),.pcw-table-card td:nth-child(8){width:66px}







.pcw-table-card th:nth-child(9),.pcw-table-card td:nth-child(9){width:64px}







.pcw-table-card th,.pcw-table-card td{padding-inline:8px;overflow:hidden;text-overflow:ellipsis}







.pcw-table-card td{height:40px}







.pcw-table-card td>*{min-width:0}







.pcw-product strong{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}







.pcw-pages{min-height:52px;box-sizing:border-box}







.pcw-chart .pcw-legend{padding:11px 16px 8px}







.pcw-chart svg{height:132px;padding:0 14px 8px}







.pcw-timeline p,.pcw-alerts p{min-height:38px;box-sizing:border-box}







.pcw-top{height:64px;padding-inline:24px;border-bottom-color:#e5ebf3;background:#fff;box-shadow:none}







.pcw-location{min-width:168px}







.pcw-location strong{font-size:14px;color:#172641}







.pcw-location small{font-size:11px;color:#3b4d66}







.pcw-top h1{font-size:20px;font-weight:800;color:#10203d}







.pcw-menu{width:34px;height:34px;background:transparent!important}







.pcw-menu span{width:14px;height:2px;background:#334155}







.pcw-menu:before,.pcw-menu:after{content:none}







.pcw-top-actions{gap:10px}







.pcw-top-actions button{min-height:32px;padding-inline:8px;color:#334155}







.pcw-user{min-width:76px;background:#f3f7fb!important;color:#334155!important}







.pcw-main{gap:12px;padding:22px 22px 24px;background:#f5f7fb}







.pcw-card,.pcw-filter,.pcw-kpis{border-color:#dfe7f1;box-shadow:0 1px 2px rgba(15,23,42,.025)}







.pcw-card-head{height:40px;border-bottom-color:#edf2f7}







.pcw-card-head h2{font-size:16px;line-height:20px}







.pcw-card-head button,.pcw-card-head span{font-size:12px}







.pcw-kpis{min-height:114px}







.pcw-kpis article{padding:18px 22px 16px}







.pcw-kpis span{line-height:16px}







.pcw-kpis small{line-height:16px}







.pcw-filter{min-height:66px}







.pcw-filter button{height:36px}







.pcw-side{border-right-color:#dfe7f1;box-shadow:none}







.pcw-nav{gap:24px}







.pcw-side-systems{gap:8px}







.pcw-system{min-height:56px;background:#f8fbff}







.pcw-system.primary{background:#eef6ff;box-shadow:none}







.pcw-system.primary strong:after{content:none}







.pcw-table-card th{height:36px;color:#455a77;font-size:12px;font-weight:700;background:#f8fafc}







.pcw-table-card td{height:40px;color:#061b3a;font-size:12px;font-weight:500}







.pcw-table-card td:nth-child(4),.pcw-table-card td:nth-child(5),.pcw-table-card td:nth-child(6){font-weight:500}







.pcw-table-card td:nth-child(7){font-weight:700}







.pcw-product{width:100%;gap:10px}







.pcw-product strong{font-size:12px;font-weight:800;color:#071b39}







.pcw-thumb{width:26px!important;height:26px!important;border-radius:7px!important;box-shadow:inset 0 0 0 1px rgba(255,255,255,.55)!important}







.pcw-thumb.greens{background:linear-gradient(135deg,#2f9b61 0%,#9be0ad 100%)}







.pcw-thumb.leaf{background:linear-gradient(135deg,#20b865 0%,#82dda4 100%)}







.pcw-thumb.cuke{background:linear-gradient(135deg,#328f3d 0%,#a8d86a 100%)}







.pcw-thumb.fish{background:linear-gradient(135deg,#8fa0b5 0%,#cfd8e4 100%)}







.pcw-thumb.potato{background:linear-gradient(135deg,#d39a18 0%,#f3d568 100%)}







.pcw-thumb.egg{background:linear-gradient(135deg,#f3a536 0%,#ffd077 100%)}







.pcw-chart{min-height:216px;padding-bottom:10px}







.pcw-chart .pcw-card-head{height:40px}







.pcw-chart .pcw-legend{gap:18px;padding:12px 16px 6px}







.pcw-chart .pcw-legend span{font-weight:700}







.pcw-chart .pcw-legend span:before{width:16px;height:4px}







.pcw-chart svg{height:134px;padding:0 12px 8px}







.pcw-chart .grid path{stroke:#edf2f7;stroke-width:1}







.pcw-chart .line-blue,.pcw-chart .line-green{stroke-width:2.7}







.pcw-chart .dots circle{r:2.6;fill:#2563eb;stroke:#fff;stroke-width:1.5}







.pcw-pages button{border-color:#dbe6f4;color:#35506e;font-weight:600}







.pcw-pages button.active{background:#eef5ff;border-color:#2563eb;color:#2563eb}







.pcw-pages em{margin-left:16px;color:#475d78}







.pcw-side-sync{display:none}







.pcw-side-systems{border-top:0;padding-top:0}







.pcw-grid{grid-template-columns:minmax(0,1fr) 360px}







.pcw-bottom{grid-template-columns:minmax(0,1fr) 420px;align-items:start}







.pcw-timeline,.pcw-alerts{min-height:198px;padding-bottom:8px}







.pcw-timeline .pcw-card-head,.pcw-alerts .pcw-card-head{height:42px}







.pcw-timeline p{display:flex;align-items:center;min-height:39px;padding:7px 0;font-size:13px;line-height:20px}







.pcw-timeline p span{flex:0 0 52px;width:52px;color:#6f8098}







.pcw-alerts p{min-height:36px;padding-block:7px;grid-template-columns:minmax(0,1fr) 76px 82px;align-items:center;font-size:13px;line-height:20px}







.pcw-alerts strong,.pcw-alerts small{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}







.pcw-alerts span{justify-self:end;font-weight:700}







.pcw-alerts small{justify-self:end;color:#6f8098}







.pcw-table-card{min-height:450px}







.pcw-right{grid-template-rows:auto auto}







.pcw-side-head{height:42px;padding-inline:2px}







.pcw-nav{padding-top:18px;gap:22px}







.pcw-nav-group{gap:18px}







.pcw-nav-item{height:42px;min-height:42px;padding-inline:12px;border-radius:7px;color:#2f405a}







.pcw-nav-item:hover{background:#f6f9ff;color:#2563eb}







.pcw-nav-item.active,.pcw-nav-item.active:hover{background:#2563eb;border-color:#2563eb;color:#fff;box-shadow:0 12px 22px rgba(37,99,235,.28)}







.pcw-nav-icon{width:14px!important;height:14px!important;border-width:1.6px!important;border-radius:4px!important}







.pcw-nav-item b{right:auto;min-width:18px;height:18px;font-size:11px}







.pcw-top{gap:22px}







.pcw-location{min-width:170px;padding-right:24px}







.pcw-location:after{right:0;height:22px;background:#dbe3ee}







.pcw-pin{width:16px;height:16px;box-shadow:inset 0 0 0 5px #dbeafe}







.pcw-menu{width:30px;height:30px;margin-left:0}







.pcw-menu span{width:14px;background:#334155}







.pcw-kpis article{grid-template-rows:16px 30px 16px;gap:6px;padding:18px 22px 14px;align-content:center}







.pcw-kpis span{align-self:end;color:#5c6f89}







.pcw-kpis strong{align-self:center;font-size:28px;line-height:30px}







.pcw-kpis small{align-self:start}







.pcw-filter{padding:14px 14px 13px}







.pcw-filter button{font-size:14px}







.pcw{grid-template-columns:192px minmax(0,1fr);background:#f4f7fb}







.pcw-side{padding:18px 12px 18px;background:#fff}







.pcw-side-head{gap:10px;height:44px;padding-inline:4px}







.pcw-logo{position:relative;width:34px;height:28px;border-radius:0;background:transparent;color:transparent;box-shadow:none;overflow:visible}







.pcw-logo:before{content:"";position:absolute;left:3px;top:8px;width:28px;height:16px;border-radius:999px;background:#2f7df6;box-shadow:-4px 3px 0 #2f7df6,7px -5px 0 #2f7df6,0 6px 12px rgba(47,125,246,.22)}







.pcw-logo:after{content:"";position:absolute;left:11px;top:13px;width:8px;height:8px;border-radius:50%;background:#fff;box-shadow:7px 0 0 rgba(255,255,255,.86)}







.pcw-brand-copy strong{font-size:18px;font-weight:800;line-height:28px;color:#111d33}







.pcw-nav{padding-top:20px;gap:20px}







.pcw-nav-group{gap:16px}







.pcw-nav-item{height:40px;min-height:40px;padding-inline:11px;border-color:transparent;border-radius:7px;background:transparent;color:#40516b;box-shadow:none;font-weight:500;line-height:40px}







.pcw-nav-item:hover{background:#f3f7ff;color:#2563eb;box-shadow:none}







.pcw-nav-item.active,.pcw-nav-item.active:hover{border-color:#dbeafe;background:#eaf2ff;color:#2563eb;box-shadow:none}







.pcw-nav-item.active b{background:#ef4444;color:#fff;box-shadow:0 4px 10px rgba(239,68,68,.18)}







.pcw-side-systems{display:flex;align-items:center;min-height:40px;margin-top:auto;padding:0 4px;border-top:0}







.pcw-side-systems:before{content:"‹  收起菜单";display:flex;align-items:center;width:100%;height:36px;color:#64748b;font-size:13px;font-weight:700}







.pcw-side-systems .pcw-system,.pcw-side-systems .pcw-side-sync{display:none}







.pcw-top{gap:20px;height:64px;padding-inline:24px;background:#fff}







.pcw-location{min-width:168px;padding-right:22px}







.pcw-location:after{height:22px;background:#d9e2ee}







.pcw-top h1{font-size:20px;font-weight:800;color:#111d33}







.pcw-main{gap:12px;padding:20px 22px 24px;background:#f4f7fb}







.pcw-filter{grid-template-columns:repeat(4,132px) minmax(0,1fr) 112px;gap:12px;min-height:42px;padding:0;border:0;background:transparent;box-shadow:none}







.pcw-filter button{height:38px;border:1px solid #dfe7f1;border-radius:7px;background:#fff;color:#22324a;text-align:left;box-shadow:0 1px 2px rgba(15,23,42,.02)}







.pcw-filter button.active{border-color:#dfe7f1;background:#fff;color:#22324a;font-weight:500;box-shadow:0 1px 2px rgba(15,23,42,.02)}







.pcw-filter .pcw-export{width:112px;min-width:112px;justify-self:end;justify-content:center;text-align:center;font-weight:700;color:#2563eb}







.pcw-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;min-height:104px;border:0;background:transparent;box-shadow:none}







.pcw-kpis article{min-height:104px;padding:16px 20px 14px;border:1px solid #dfe7f1;border-radius:8px;background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.025)}







.pcw-kpis article:last-child{border-right:1px solid #dfe7f1}







.pcw-grid{grid-template-columns:minmax(0,1fr) 360px;gap:12px}







.pcw-card{border-color:#dfe7f1;border-radius:8px;box-shadow:0 1px 2px rgba(15,23,42,.025)}







.pcw-more-quotes{height:38px;margin:2px 14px 14px;border:1px solid #dbe7f6;border-radius:7px;background:#f8fbff;color:#2563eb;font-size:13px;font-weight:800}







.pcw-chart{min-height:220px}







.pcw-bottom{grid-template-columns:minmax(0,1.28fr) minmax(260px,.66fr) 420px;gap:12px;align-items:start}







.pcw-timeline,.pcw-advice,.pcw-alerts{min-height:198px;padding-bottom:8px}







.pcw-timeline .pcw-card-head,.pcw-advice .pcw-card-head,.pcw-alerts .pcw-card-head{height:42px}







.pcw-advice ul{margin:0;padding:9px 18px 12px 30px;color:#24344d;font-size:13px;line-height:1.62}







.pcw-advice li{padding:4px 0}







.pcw-alerts p{grid-template-columns:minmax(0,1fr) 70px 78px}







.pcw-filter.section-suppliers,.pcw-filter.section-quotes{grid-template-columns:repeat(4,152px) minmax(0,1fr)}







.pcw-filter.section-market,.pcw-filter.section-purchase,.pcw-filter.section-plan,.pcw-filter.section-reports,.pcw-filter.section-settings{grid-template-columns:repeat(5,132px) minmax(0,1fr)}







.pcw-filter.section-alerts{grid-template-columns:repeat(5,132px) minmax(0,1fr)}







.pcw-kpis.is-alerts article{position:relative;padding-left:72px}







.pcw-kpis.is-alerts article:before{content:"";position:absolute;left:22px;top:28px;width:48px;height:48px;border-radius:50%;background:#eff6ff}







.pcw-kpis.is-alerts article:after{content:"";position:absolute;left:38px;top:43px;width:17px;height:17px;border:2px solid #2563eb;border-radius:5px;box-sizing:border-box}







.pcw-kpis.is-alerts article:nth-child(2):before{background:#fef2f2}







.pcw-kpis.is-alerts article:nth-child(2):after{border:0;border-radius:0;background:#ef4444;clip-path:polygon(50% 0,100% 55%,70% 55%,70% 100%,30% 100%,30% 55%,0 55%)}







.pcw-kpis.is-alerts article:nth-child(3):before{background:#ecfdf5}







.pcw-kpis.is-alerts article:nth-child(3):after{border:0;border-radius:0;background:#16a34a;clip-path:polygon(30% 0,70% 0,70% 45%,100% 45%,50% 100%,0 45%,30% 45%)}







.pcw-kpis.is-alerts article:nth-child(4):before{background:#fff7ed}







.pcw-kpis.is-alerts article:nth-child(4):after{border:0;width:24px;height:16px;left:34px;top:45px;background:#f97316;clip-path:polygon(0 60%,18% 60%,28% 20%,42% 82%,58% 0,70% 62%,100% 62%,100% 75%,64% 75%,58% 52%,42% 100%,28% 44%,24% 75%,0 75%)}







.pcw-kpis.is-alerts article:nth-child(5):before{background:#f8fafc}







.pcw-kpis.is-alerts article:nth-child(5):after{border-color:#64748b;border-radius:50%}







.pcw-alert-table-card td{height:40px}







.pcw-alert-table-card .pcw-pages{min-height:52px}







.pcw-module-a11y-title{position:absolute;width:1px;height:1px;margin:0;overflow:hidden;opacity:0;pointer-events:none}







.pcw-module-table-note{display:none;margin:0;padding:0 16px 10px;color:#607089;font-size:12px;line-height:1.45}







.pcw-module-card-actions{display:flex;align-items:center;gap:10px}







.pcw-module-card-actions button{height:30px;min-width:82px;padding:0 12px;border:1px solid #bfd2ff;border-radius:6px;background:#eef5ff;color:#2563eb;font-size:12px;font-weight:800}







.pcw-module-market .pcw-module-hero,.pcw-module-suppliers .pcw-module-hero,.pcw-module-purchase .pcw-module-hero,.pcw-module-quotes .pcw-module-hero,.pcw-module-plan .pcw-module-hero,.pcw-module-reports .pcw-module-hero,.pcw-module-settings .pcw-module-hero{display:none}







.pcw-module-market .pcw-module-grid,.pcw-module-suppliers .pcw-module-grid,.pcw-module-purchase .pcw-module-grid,.pcw-module-quotes .pcw-module-grid,.pcw-module-plan .pcw-module-grid,.pcw-module-reports .pcw-module-grid,.pcw-module-settings .pcw-module-grid{grid-template-columns:minmax(0,1fr) 420px;grid-template-areas:"table panel" "chart flow";gap:12px;align-items:start}







.pcw-module-quotes .pcw-module-grid{grid-template-areas:"table panel" "chart flow" "chart activity"}







.pcw-module-market .pcw-module-side,.pcw-module-suppliers .pcw-module-side,.pcw-module-purchase .pcw-module-side,.pcw-module-quotes .pcw-module-side,.pcw-module-plan .pcw-module-side,.pcw-module-reports .pcw-module-side,.pcw-module-settings .pcw-module-side{display:contents}







.pcw-module-market .pcw-module-panel,.pcw-module-suppliers .pcw-module-panel,.pcw-module-purchase .pcw-module-panel,.pcw-module-quotes .pcw-module-panel,.pcw-module-plan .pcw-module-panel,.pcw-module-reports .pcw-module-panel,.pcw-module-settings .pcw-module-panel{grid-area:panel}







.pcw-module-market .pcw-module-flow,.pcw-module-suppliers .pcw-module-flow,.pcw-module-purchase .pcw-module-flow,.pcw-module-quotes .pcw-module-flow,.pcw-module-plan .pcw-module-flow,.pcw-module-reports .pcw-module-flow,.pcw-module-settings .pcw-module-flow{grid-area:flow}







.pcw-module-market .pcw-module-activity,.pcw-module-suppliers .pcw-module-activity{display:none}







.pcw-module-quotes .pcw-module-activity{grid-area:activity}







.pcw-module-market .pcw-module-table-note,.pcw-module-purchase .pcw-module-table-note,.pcw-module-plan .pcw-module-table-note,.pcw-module-reports .pcw-module-table-note,.pcw-module-settings .pcw-module-table-note{display:block}







.pcw-module-market .pcw-module-table td,.pcw-module-suppliers .pcw-module-table td,.pcw-module-purchase .pcw-module-table td,.pcw-module-quotes .pcw-module-table td,.pcw-module-plan .pcw-module-table td,.pcw-module-reports .pcw-module-table td,.pcw-module-settings .pcw-module-table td{height:48px}







.pcw-module-market .pcw-module-table th,.pcw-module-suppliers .pcw-module-table th,.pcw-module-purchase .pcw-module-table th,.pcw-module-quotes .pcw-module-table th,.pcw-module-plan .pcw-module-table th,.pcw-module-reports .pcw-module-table th,.pcw-module-settings .pcw-module-table th{height:38px;background:#f8fafc;color:#52647f}







.pcw-module-market .pcw-module-name,.pcw-module-suppliers .pcw-module-name,.pcw-module-purchase .pcw-module-name,.pcw-module-quotes .pcw-module-name,.pcw-module-plan .pcw-module-name,.pcw-module-reports .pcw-module-name,.pcw-module-settings .pcw-module-name{position:relative;padding-left:34px;color:#0f1f3d;font-weight:800}







.pcw-module-market .pcw-module-name:before,.pcw-module-suppliers .pcw-module-name:before,.pcw-module-purchase .pcw-module-name:before,.pcw-module-quotes .pcw-module-name:before,.pcw-module-plan .pcw-module-name:before,.pcw-module-reports .pcw-module-name:before,.pcw-module-settings .pcw-module-name:before{content:"";position:absolute;left:0;top:50%;width:26px;height:26px;border-radius:8px;background:linear-gradient(135deg,#16a34a,#86efac);transform:translateY(-50%)}







.pcw-module-market tbody tr:nth-child(2n) .pcw-module-name:before,.pcw-module-purchase tbody tr:nth-child(2n) .pcw-module-name:before,.pcw-module-plan tbody tr:nth-child(2n) .pcw-module-name:before,.pcw-module-reports tbody tr:nth-child(2n) .pcw-module-name:before,.pcw-module-settings tbody tr:nth-child(2n) .pcw-module-name:before{background:linear-gradient(135deg,#2563eb,#93c5fd)}







.pcw-module-market tbody tr:nth-child(3n) .pcw-module-name:before,.pcw-module-purchase tbody tr:nth-child(3n) .pcw-module-name:before,.pcw-module-plan tbody tr:nth-child(3n) .pcw-module-name:before,.pcw-module-reports tbody tr:nth-child(3n) .pcw-module-name:before,.pcw-module-settings tbody tr:nth-child(3n) .pcw-module-name:before{background:linear-gradient(135deg,#f97316,#fed7aa)}







.pcw-module-suppliers tbody tr:nth-child(2n) .pcw-module-name:before{background:linear-gradient(135deg,#2563eb,#93c5fd)}







.pcw-module-suppliers tbody tr:nth-child(3n) .pcw-module-name:before{background:linear-gradient(135deg,#0ea5e9,#38bdf8)}







.pcw-module-quotes tbody tr:nth-child(2n) .pcw-module-name:before{background:linear-gradient(135deg,#64748b,#e2e8f0)}







.pcw-module-quotes tbody tr:nth-child(3n) .pcw-module-name:before{background:linear-gradient(135deg,#ca8a04,#fde68a)}







.pcw-module-market .pcw-module-panel article,.pcw-module-suppliers .pcw-module-panel article,.pcw-module-purchase .pcw-module-panel article,.pcw-module-quotes .pcw-module-panel article,.pcw-module-plan .pcw-module-panel article,.pcw-module-reports .pcw-module-panel article,.pcw-module-settings .pcw-module-panel article{grid-template-columns:48px minmax(0,1fr) 50px;align-items:center;gap:10px;min-height:52px}







.pcw-module-market .pcw-module-panel article span,.pcw-module-suppliers .pcw-module-panel article span,.pcw-module-purchase .pcw-module-panel article span,.pcw-module-quotes .pcw-module-panel article span,.pcw-module-plan .pcw-module-panel article span,.pcw-module-reports .pcw-module-panel article span,.pcw-module-settings .pcw-module-panel article span{grid-row:1 / span 2;display:grid;place-items:center;width:34px;height:22px;padding:0;border-radius:5px}







.pcw-module-market .pcw-module-panel article small,.pcw-module-suppliers .pcw-module-panel article small,.pcw-module-purchase .pcw-module-panel article small,.pcw-module-quotes .pcw-module-panel article small,.pcw-module-plan .pcw-module-panel article small,.pcw-module-reports .pcw-module-panel article small,.pcw-module-settings .pcw-module-panel article small{grid-column:2}







.pcw-module-market .pcw-module-flow p,.pcw-module-suppliers .pcw-module-flow p,.pcw-module-purchase .pcw-module-flow p,.pcw-module-plan .pcw-module-flow p,.pcw-module-reports .pcw-module-flow p,.pcw-module-settings .pcw-module-flow p{grid-template-columns:42px 1fr;position:relative;padding-left:8px}







.pcw-module-market .pcw-module-flow b,.pcw-module-suppliers .pcw-module-flow b,.pcw-module-purchase .pcw-module-flow b,.pcw-module-plan .pcw-module-flow b,.pcw-module-reports .pcw-module-flow b,.pcw-module-settings .pcw-module-flow b{display:grid;place-items:center;width:28px;height:28px;border-radius:8px;background:#2563eb;color:#fff}







.pcw-module-quotes .pcw-module-flow p,.pcw-module-quotes .pcw-module-activity article{grid-template-columns:58px 1fr 44px;min-height:48px}







.pcw-module-quotes .pcw-module-activity em{color:#2563eb}







.pcw-module-chart-panel{min-height:316px}







.pcw-module-chart-panel svg{height:248px}







.pcw{grid-template-columns:190px minmax(0,1fr);background:#f5f7fb;color:#111f36}







.pcw-side{padding:18px 12px;border-right-color:#dfe6ef}







.pcw-nav{gap:8px;padding-top:18px}







.pcw-nav-group{gap:8px}







.pcw-nav-item{grid-template-columns:20px minmax(0,1fr) auto;height:44px;min-height:44px;padding:0 12px;border:1px solid transparent;border-radius:8px;color:#23364f;font-weight:500;line-height:1;box-shadow:none}







.pcw-nav-item:hover{border-color:#e7eef8;background:#f7faff;color:#2563eb}







.pcw-nav-item.active,.pcw-nav-item.active:hover{border-color:#d7e6ff;background:#eaf2ff;color:#2563eb;box-shadow:none}







.pcw-nav-item.active:after{content:none}







.pcw-nav-icon{display:grid!important;place-items:center;width:18px!important;height:18px!important;border:0!important;border-radius:0!important;color:currentColor}







.pcw-nav-icon svg{display:block!important;width:18px;height:18px;overflow:visible}







.pcw-nav-icon path{fill:none!important;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}







.pcw-nav-item b{min-width:18px;height:18px;border-radius:999px;background:#ef4444;color:#fff;font-size:11px;font-weight:800;line-height:18px}







.pcw-menu{display:none!important}







.pcw-top{gap:20px;padding-inline:24px;background:#fff}







.pcw-top h1{font-size:20px;font-weight:800;color:#101c31}







.pcw-location{min-width:170px}







.pcw-top-actions button{font-size:14px;color:#10203a}







.pcw-filter{grid-template-columns:repeat(4,132px) minmax(0,1fr) 112px;gap:12px;min-height:40px;padding:0;border:0;background:transparent;box-shadow:none}







.pcw-filter button{height:38px;border:1px solid #dbe5f1;border-radius:7px;background:#fff;color:#1f3149;box-shadow:0 1px 2px rgba(15,23,42,.02)}







.pcw-filter button.active{border-color:#dbe5f1;background:#fff;color:#1f3149;font-weight:500;box-shadow:0 1px 2px rgba(15,23,42,.02)}







.pcw-filter .pcw-export{width:112px;min-width:112px;justify-self:end;justify-content:center;color:#2563eb;font-weight:800}







.pcw-filter.is-alert,.pcw-filter.section-alerts{grid-template-columns:repeat(5,132px) minmax(0,1fr) 112px}







.pcw-filter.section-market,.pcw-filter.section-purchase,.pcw-filter.section-plan{grid-template-columns:repeat(4,156px) minmax(0,1fr) 112px}







.pcw-filter.section-reports,.pcw-filter.section-settings{grid-template-columns:repeat(5,132px) minmax(0,1fr) 112px}







.pcw-filter.section-suppliers,.pcw-filter.section-quotes{grid-template-columns:repeat(4,152px) minmax(0,1fr) 112px}







.pcw-kpis{gap:12px;min-height:104px;border:0;background:transparent;box-shadow:none}







.pcw-kpis article{min-height:104px;padding:16px 20px 14px;border:1px solid #dfe7f1!important;border-radius:8px;background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.025)}







.pcw-kpis strong{font-size:28px;color:#0d1d36}







.pcw-kpis.is-market article,.pcw-kpis.is-suppliers article,.pcw-kpis.is-purchase article,.pcw-kpis.is-quotes article,.pcw-kpis.is-plan article,.pcw-kpis.is-reports article,.pcw-kpis.is-settings article{position:relative;padding-left:86px}







.pcw-kpis.is-market article:before,.pcw-kpis.is-suppliers article:before,.pcw-kpis.is-purchase article:before,.pcw-kpis.is-quotes article:before,.pcw-kpis.is-plan article:before,.pcw-kpis.is-reports article:before,.pcw-kpis.is-settings article:before{content:"";position:absolute;left:22px;top:26px;width:52px;height:52px;border-radius:50%;background:#eff6ff}







.pcw-kpis.is-market article:after,.pcw-kpis.is-suppliers article:after,.pcw-kpis.is-purchase article:after,.pcw-kpis.is-quotes article:after,.pcw-kpis.is-plan article:after,.pcw-kpis.is-reports article:after,.pcw-kpis.is-settings article:after{content:"";position:absolute;left:39px;top:43px;width:18px;height:18px;background:#2563eb}







.pcw-kpis.is-market article:nth-child(1):after{clip-path:polygon(15% 90%,15% 20%,85% 20%,85% 90%,68% 90%,68% 52%,54% 52%,54% 90%,42% 90%,42% 52%,28% 52%,28% 90%)}







.pcw-kpis.is-market article:nth-child(2):before,.pcw-kpis.is-suppliers article:nth-child(2):before,.pcw-kpis.is-plan article:nth-child(2):before{background:#ecfdf5}







.pcw-kpis.is-market article:nth-child(2):after,.pcw-kpis.is-suppliers article:nth-child(2):after,.pcw-kpis.is-plan article:nth-child(2):after{background:#16a34a;clip-path:circle(48% at 50% 50%)}







.pcw-kpis.is-market article:nth-child(3):before,.pcw-kpis.is-quotes article:nth-child(1):before,.pcw-kpis.is-reports article:nth-child(1):before{background:#fff7ed}







.pcw-kpis.is-market article:nth-child(3):after,.pcw-kpis.is-quotes article:nth-child(1):after,.pcw-kpis.is-reports article:nth-child(1):after{background:#f97316;clip-path:polygon(10% 90%,10% 62%,28% 62%,28% 36%,46% 36%,46% 18%,64% 18%,64% 90%)}







.pcw-kpis.is-market article:nth-child(4):before,.pcw-kpis.is-plan article:nth-child(5):before{background:#fef2f2}







.pcw-kpis.is-market article:nth-child(4):after,.pcw-kpis.is-plan article:nth-child(5):after{background:#ef4444;clip-path:polygon(50% 0,100% 90%,0 90%)}







.pcw-kpis.is-market article:nth-child(5):before,.pcw-kpis.is-settings article:nth-child(1):before{background:#f5f3ff}







.pcw-kpis.is-market article:nth-child(5):after,.pcw-kpis.is-settings article:nth-child(1):after{background:#7c3aed;clip-path:circle(46% at 50% 50%)}







.pcw-kpis.is-suppliers article:nth-child(1):after,.pcw-kpis.is-purchase article:nth-child(1):after{clip-path:polygon(50% 0,100% 38%,84% 100%,16% 100%,0 38%)}







.pcw-kpis.is-suppliers article:nth-child(3):before,.pcw-kpis.is-purchase article:nth-child(3):before,.pcw-kpis.is-plan article:nth-child(3):before{background:#fff7ed}







.pcw-kpis.is-suppliers article:nth-child(3):after,.pcw-kpis.is-purchase article:nth-child(3):after,.pcw-kpis.is-plan article:nth-child(3):after{background:#f97316;clip-path:circle(48% at 50% 50%)}







.pcw-kpis.is-suppliers article:nth-child(4):after,.pcw-kpis.is-reports article:nth-child(2):after{clip-path:polygon(10% 52%,40% 82%,90% 20%,100% 30%,42% 96%,0 62%)}







.pcw-kpis.is-purchase article:nth-child(2):before,.pcw-kpis.is-reports article:nth-child(3):before{background:#fef2f2}







.pcw-kpis.is-purchase article:nth-child(2):after,.pcw-kpis.is-reports article:nth-child(3):after{background:#ef4444;clip-path:polygon(50% 0,100% 90%,0 90%)}







.pcw-kpis.is-plan article:nth-child(4):after,.pcw-kpis.is-quotes article:nth-child(4):after,.pcw-kpis.is-reports article:nth-child(4):after{clip-path:circle(46% at 50% 50%)}







.pcw-kpis.is-settings article:after{clip-path:polygon(50% 0,63% 28%,94% 20%,78% 50%,94% 80%,63% 72%,50% 100%,37% 72%,6% 80%,22% 50%,6% 20%,37% 28%)}







.pcw-card{border-color:#dfe7f1;border-radius:8px;box-shadow:0 1px 2px rgba(15,23,42,.025)}







.pcw-card-head{height:42px;border-bottom-color:#edf2f7}







.pcw-grid{grid-template-columns:minmax(0,1fr) 360px}







.pcw-table-card{min-height:450px}







.pcw-table-card td{height:40px}







.pcw-right{gap:12px}







.pcw-chart{min-height:220px}







.pcw-chart svg{height:134px}







.pcw-bottom{grid-template-columns:minmax(0,1.28fr) minmax(260px,.66fr) 420px}







.pcw-timeline,.pcw-advice,.pcw-alerts{min-height:198px}







.pcw-alert-table-card td{height:40px}







.pcw-module-market .pcw-module-grid,.pcw-module-suppliers .pcw-module-grid,.pcw-module-purchase .pcw-module-grid,.pcw-module-quotes .pcw-module-grid,.pcw-module-plan .pcw-module-grid,.pcw-module-reports .pcw-module-grid,.pcw-module-settings .pcw-module-grid{grid-template-columns:minmax(0,1fr) 430px;grid-template-areas:"table panel" "chart flow" "chart activity";gap:12px}







.pcw-module-market .pcw-module-activity,.pcw-module-suppliers .pcw-module-activity{display:grid}







.pcw-module-panel,.pcw-module-flow{min-height:178px}







.pcw-module-table{min-height:352px}







.pcw-module-table td{height:46px!important}







.pcw-module-chart-panel{min-height:320px}







.pcw-module-panel article,.pcw-module-flow p,.pcw-module-activity article{min-height:58px}







.pcw-module-panel article strong,.pcw-module-flow span,.pcw-module-activity span{min-width:0;overflow:hidden;text-overflow:ellipsis}







.pcw-module-flow p{position:relative}







.pcw-module-flow p:not(:last-child):after{content:"";position:absolute;left:29px;top:43px;bottom:-17px;width:1px;background:#dbe7f6}







.pcw-module-flow b{z-index:1}







.pcw-module-activity article{grid-template-columns:62px minmax(0,1fr) 66px}







.pcw-module-activity em{border-radius:999px;background:#ecfdf5;color:#16a34a;padding:3px 8px;font-size:11px}







.pcw-module-market .pcw-module-chart-panel,.pcw-module-suppliers .pcw-module-chart-panel,.pcw-module-purchase .pcw-module-chart-panel,.pcw-module-plan .pcw-module-chart-panel,.pcw-module-reports .pcw-module-chart-panel{min-height:332px}







.pcw-module-quotes .pcw-module-grid,.pcw-module-settings .pcw-module-grid{grid-template-areas:"table panel" "chart flow" "activity activity"}







.pcw-module-quotes .pcw-module-activity,.pcw-module-settings .pcw-module-activity{grid-area:activity}















.pcw-card::before{content:"";display:block;height:3px;background:linear-gradient(90deg,#2563eb,#60a5fa 56%,#f59e0b);opacity:.86}.pcw-table-card::before,.pcw-trend-chart-card::before{background:linear-gradient(90deg,#1d4ed8,#60a5fa,#22c55e)}.pcw-module-market .pcw-module-main::before,.pcw-module-market .pcw-module-side::before{background:linear-gradient(90deg,#0ea5e9,#2563eb,#22c55e)}.pcw-module-plan .pcw-module-main::before,.pcw-module-plan .pcw-module-side::before{background:linear-gradient(90deg,#7c3aed,#2563eb,#f59e0b)}.pcw-module-reports .pcw-module-main::before,.pcw-module-reports .pcw-module-side::before{background:linear-gradient(90deg,#0891b2,#2563eb,#14b8a6)}.pcw-module-settings .pcw-module-main::before,.pcw-module-settings .pcw-module-side::before{background:linear-gradient(90deg,#64748b,#2563eb,#94a3b8)}.pcw-card-head h2{letter-spacing:-.01em}.pcw-card-head h2::after{content:"";display:block;width:28px;height:3px;margin-top:7px;border-radius:999px;background:#2563eb}.pcw-module-market .pcw-card-head h2::after{background:#0ea5e9}.pcw-module-plan .pcw-card-head h2::after{background:#7c3aed}.pcw-module-reports .pcw-card-head h2::after{background:#0891b2}.pcw-module-settings .pcw-card-head h2::after{background:#64748b}.pcw-empty-row td,.pcw-panel-empty,.pcw-chart-empty{background:linear-gradient(135deg,#f8fbff,#eef6ff);border-radius:14px;color:#64748b}.pcw-chart-empty{min-height:210px;display:grid;place-content:center;text-align:center;border:1px dashed #bfdbfe}.pcw-panel-empty strong,.pcw-chart-empty strong{color:#1e3a8a}.pcw-module-hero{position:relative;overflow:hidden;border:1px solid rgba(37,99,235,.12);background:linear-gradient(135deg,#f8fbff 0%,#eef6ff 55%,#fff7ed 100%)}.pcw-module-hero::after{content:"";position:absolute;right:-60px;top:-72px;width:180px;height:180px;border-radius:999px;background:rgba(37,99,235,.1)}.pcw-module-copy,.pcw-module-actions{position:relative;z-index:1}.pcw-module-actions button.primary,.pcw-more-quotes,.pcw-top-actions button.primary{background:linear-gradient(135deg,#2563eb,#1d4ed8);border-color:#1d4ed8;box-shadow:0 12px 22px rgba(37,99,235,.2)}.pcw-module-actions button:not(.primary),.pcw-card-head button,.pcw-top-actions button:not(.primary){border-color:#dbeafe;background:#f8fbff;color:#1d4ed8}.pcw table th{font-weight:700;color:#475569;background:#f8fafc}.pcw table td{color:#26364f}.pcw tbody tr:hover{background:#f8fbff}.pcw-segments{padding:3px;border-radius:999px;background:#eef4ff}.pcw-segments button{border:0;border-radius:999px}.pcw-segments button.active{background:#2563eb;color:#fff;box-shadow:0 8px 16px rgba(37,99,235,.24)}







.pcw-module-command{display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"copy actions" "metrics brief";gap:12px;margin-bottom:12px;padding:16px 18px;border:1px solid #dfe7f1;border-radius:8px;background:#fff;box-shadow:0 8px 20px rgba(15,23,42,.025)}







.pcw-module-command-copy{grid-area:copy;min-width:0}.pcw-module-command-copy span{color:#2563eb;font-size:12px;font-weight:800}.pcw-module-command-copy h2{margin:4px 0 6px;color:#10203d;font-size:22px;line-height:1.18;letter-spacing:0}.pcw-module-command-copy p{max-width:820px;margin:0;color:#607089;font-size:13px;line-height:1.55}.pcw-module-command-actions{grid-area:actions;display:flex;align-items:flex-start;gap:8px}.pcw-module-command-actions button{height:34px;min-width:84px;padding:0 13px;border:1px solid #dbe4ef;border-radius:6px;background:#fff;color:#24344d;font-weight:800}.pcw-module-command-actions button.primary{border-color:#2563eb;background:#2563eb;color:#fff}.pcw-module-command-metrics{grid-area:metrics;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.pcw-module-command-metrics article{display:grid;gap:4px;min-width:0;padding:11px 12px;border:1px solid #e2e8f0;border-radius:7px;background:#fbfdff}.pcw-module-command-metrics span,.pcw-module-command-metrics small{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#64748b;font-size:12px}.pcw-module-command-metrics strong{color:#10203d;font-size:22px;line-height:1}.pcw-module-command-metrics article.warn{border-color:#fed7aa;background:#fffaf5}.pcw-module-command-metrics article.green{border-color:#bbf7d0;background:#fbfffd}.pcw-module-command-metrics article.blue{border-color:#bfdbfe;background:#f8fbff}.pcw-module-command-brief{grid-area:brief;display:grid;gap:7px;min-width:340px}.pcw-module-command-brief p{display:grid;grid-template-columns:72px minmax(0,1fr);gap:10px;align-items:center;margin:0;padding:8px 10px;border:1px solid #edf2f7;border-radius:7px;background:#fbfdff}.pcw-module-command-brief b{color:#334155;font-size:12px}.pcw-module-command-brief span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#607089;font-size:12px}







.pcw-module-layout-coverage .pcw-module-command{background:linear-gradient(135deg,#f8fbff,#fff 62%,#ecfeff)}.pcw-module-layout-network .pcw-module-command{background:linear-gradient(135deg,#f8fbff,#fff 62%,#f0fdf4)}.pcw-module-layout-workflow .pcw-module-command{background:linear-gradient(135deg,#fff7ed,#fff 58%,#f8fbff)}.pcw-module-layout-ledger .pcw-module-command{background:linear-gradient(135deg,#f8fafc,#fff 58%,#f8fbff)}.pcw-module-layout-insight .pcw-module-command{background:linear-gradient(135deg,#ecfeff,#fff 58%,#f8fbff)}.pcw-module-layout-ops .pcw-module-command{background:linear-gradient(135deg,#f8fafc,#fff 58%,#eef2ff)}







.pcw-module-layout-coverage .pcw-module-grid{grid-template-columns:390px minmax(0,1fr);grid-template-areas:"panel table" "flow table" "chart activity";gap:12px}.pcw-module-layout-network .pcw-module-grid{grid-template-columns:360px minmax(0,1fr);grid-template-areas:"panel table" "flow table" "activity chart";gap:12px}.pcw-module-layout-workflow .pcw-module-grid{grid-template-columns:minmax(0,1fr) 380px;grid-template-areas:"flow panel" "table panel" "table activity" "chart chart";gap:12px}.pcw-module-layout-ledger .pcw-module-grid{grid-template-columns:minmax(0,1fr) 340px;grid-template-areas:"table panel" "table activity" "chart flow";gap:12px}.pcw-module-layout-insight .pcw-module-grid{grid-template-columns:minmax(0,1fr) 360px;grid-template-areas:"chart panel" "table panel" "table flow" "activity activity";gap:12px}.pcw-module-layout-ops .pcw-module-grid{grid-template-columns:360px minmax(0,1fr);grid-template-areas:"panel table" "flow table" "activity chart";gap:12px}







.pcw-module-layout-workflow .pcw-module-flow,.pcw-module-layout-insight .pcw-module-chart-panel,.pcw-module-layout-ops .pcw-module-panel{min-height:220px}.pcw-module-layout-ledger .pcw-module-table,.pcw-module-layout-coverage .pcw-module-table,.pcw-module-layout-network .pcw-module-table{min-height:506px}.pcw-module-layout-workflow .pcw-module-table{min-height:420px}.pcw-module-layout-insight .pcw-module-chart-panel svg{height:270px}.pcw-module-layout-ledger .pcw-module-activity,.pcw-module-layout-network .pcw-module-activity,.pcw-module-layout-ops .pcw-module-activity{min-height:190px}.pcw-module-layout-coverage .pcw-module-panel article{grid-template-columns:42px minmax(0,1fr)}.pcw-module-layout-workflow .pcw-module-flow p{grid-template-columns:52px minmax(0,1fr);min-height:64px}.pcw-module-layout-ledger .pcw-module-table td{height:42px!important}.pcw-module-layout-insight .pcw-module-table-note,.pcw-module-layout-ops .pcw-module-table-note{display:block}@media (max-width:1180px){.pcw{grid-template-columns:190px minmax(0,1fr)}.pcw-side{padding-inline:10px}.pcw-nav-item{grid-template-columns:20px minmax(0,1fr) auto;padding-inline:8px}.pcw-right{grid-template-columns:repeat(2,minmax(0,1fr))}.pcw-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}.pcw-kpis article{border-bottom:1px solid #e8edf4}.pcw-filter,.pcw-filter.is-trend,.pcw-filter.is-alert,.pcw-filter.is-module{grid-template-columns:repeat(2,1fr)}.pcw-module-hero{align-items:flex-start}.pcw-module-actions{flex-direction:column;align-items:stretch}.pcw-module-actions button{width:104px}}















/* reference-style polish: airy B端 dashboards, softer cards, stronger blue hierarchy */







.pcw{







  --pcw-bg:#f5f7fb;







  --pcw-surface:#ffffff;







  --pcw-surface-soft:#f8fbff;







  --pcw-border:#dfe7f1;







  --pcw-border-strong:#cfd9e6;







  --pcw-ink:#10203d;







  --pcw-text:#24344d;







  --pcw-muted:#64748b;







  --pcw-faint:#94a3b8;







  --pcw-primary:#2563eb;







  --pcw-primary-soft:#eaf2ff;







  --pcw-success:#16a34a;







  --pcw-warn:#f97316;







  --pcw-danger:#ef4444;







  --pcw-ring:rgba(37,99,235,.12);







  grid-template-columns:192px minmax(0,1fr);







  background:var(--pcw-bg);







  color:var(--pcw-ink);







}







.pcw-side{







  padding:18px 12px;







  border-right:1px solid var(--pcw-border);







  background:var(--pcw-surface);







  box-shadow:none;







}







.pcw-side-head{gap:10px;height:44px;padding-inline:4px}







.pcw-logo{







  width:34px;height:34px;border-radius:10px;







  background:linear-gradient(135deg,#1d4ed8,#3b82f6);







  box-shadow:0 10px 18px rgba(37,99,235,.2);







  color:transparent;







}







.pcw-logo:before{content:"";position:absolute;left:3px;top:8px;width:28px;height:16px;border-radius:999px;background:#2f7df6;box-shadow:-4px 3px 0 #2f7df6,7px -5px 0 #2f7df6,0 6px 12px rgba(47,125,246,.22)}







.pcw-logo:after{content:"";position:absolute;left:11px;top:13px;width:8px;height:8px;border-radius:50%;background:#fff;box-shadow:7px 0 0 rgba(255,255,255,.86)}







.pcw-brand-copy strong{font-size:18px;font-weight:800;line-height:28px;color:#111d33}







.pcw-brand-copy small{display:none}







.pcw-nav{padding-top:20px;gap:20px}







.pcw-nav-group{gap:16px}







.pcw-nav-group>span{display:none}







.pcw-nav-item{







  height:40px;min-height:40px;padding-inline:11px;







  border:1px solid transparent;border-radius:8px;







  background:transparent;color:#40516b;font-size:14px;font-weight:500;







  box-shadow:none;line-height:40px;







}







.pcw-nav-item:hover{background:#f3f7ff;color:var(--pcw-primary)}







.pcw-nav-item.active,.pcw-nav-item.active:hover{border-color:#dbeafe;background:#eaf2ff;color:var(--pcw-primary);box-shadow:none}







.pcw-nav-item b{background:var(--pcw-danger);color:#fff;box-shadow:0 4px 10px rgba(239,68,68,.18)}







.pcw-side-systems{







  display:flex;align-items:center;min-height:40px;margin-top:auto;







  padding:0 4px;border-top:0;







}







.pcw-side-systems:before{content:"‹  收起菜单";display:flex;align-items:center;width:100%;height:36px;color:#64748b;font-size:13px;font-weight:700}







.pcw-side-systems .pcw-system,.pcw-side-systems .pcw-side-sync{display:none}







.pcw-app{grid-template-rows:64px 1fr}







.pcw-top{







  gap:20px;height:64px;padding-inline:24px;







  border-bottom:1px solid var(--pcw-border);







  background:#fff;box-shadow:none;







}







.pcw-location{min-width:168px;padding-right:22px}







.pcw-location:after{content:"";position:absolute;right:0;height:22px;width:1px;background:#d9e2ee}







.pcw-location-button,.pcw-top-actions button{border-radius:8px;color:#334155;font-size:13px;font-weight:600}







.pcw-location-button strong{font-size:14px;color:#172641}







.pcw-pin{width:16px;height:16px;box-shadow:inset 0 0 0 5px #dbeafe}







.pcw-menu{width:30px;height:30px;background:transparent!important}







.pcw-menu span{width:14px;height:2px;background:#334155}







.pcw-menu:before,.pcw-menu:after{content:none}







.pcw-top-actions{gap:10px}







.pcw-top-actions button{min-height:32px;padding-inline:8px}







.pcw-top-actions button:hover{background:#f3f6fb;color:var(--pcw-primary)}







.pcw-user{min-width:76px;background:#f3f7fb!important;color:#334155!important}







.pcw-main{gap:12px;padding:20px 22px 24px;background:var(--pcw-bg)}







.pcw-filter{







  grid-template-columns:repeat(4,132px) minmax(0,1fr) 112px;







  gap:12px;min-height:42px;padding:0;







  border:0;background:transparent;box-shadow:none;







}







.pcw-filter button{







  height:38px;border:1px solid var(--pcw-border);border-radius:7px;







  background:#fff;color:#1f3149;box-shadow:0 1px 2px rgba(15,23,42,.02);







}







.pcw-filter button.active{border-color:var(--pcw-border);background:#fff;color:#1f3149;font-weight:500;box-shadow:0 1px 2px rgba(15,23,42,.02)}







.pcw-filter button:not(.pcw-export):hover,.pcw-filter-item>button.open{border-color:#bfd2ff;color:var(--pcw-primary);box-shadow:0 0 0 3px var(--pcw-ring)}







.pcw-filter .pcw-export{width:112px;min-width:112px;justify-self:end;justify-content:center;color:var(--pcw-primary);font-weight:800}







.pcw-filter.section-alerts,.pcw-filter.is-alert{grid-template-columns:repeat(5,132px) minmax(0,1fr) 112px}







.pcw-filter.section-market,.pcw-filter.section-purchase,.pcw-filter.section-plan{grid-template-columns:repeat(4,156px) minmax(0,1fr) 112px}







.pcw-filter.section-reports,.pcw-filter.section-settings{grid-template-columns:repeat(5,132px) minmax(0,1fr) 112px}







.pcw-filter.section-suppliers,.pcw-filter.section-quotes{grid-template-columns:repeat(4,152px) minmax(0,1fr) 112px}







.pcw-kpis{gap:12px;min-height:104px;border:0;background:transparent;box-shadow:none}







.pcw-kpis article{







  min-height:104px;padding:16px 20px 14px;







  border:1px solid var(--pcw-border)!important;border-radius:8px;







  background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.025);







}







.pcw-kpis strong{font-size:28px;color:#0d1d36}







.pcw-kpis span,.pcw-card-head span,.pcw-card-head button,.pcw-kpis small,th,td{font-size:12px}







.pcw-grid{grid-template-columns:minmax(0,1fr) 360px;gap:12px}







.pcw-right{gap:12px}







.pcw-card{







  border:1px solid var(--pcw-border);border-radius:8px;







  background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.025);overflow:hidden;







}







.pcw-card-head{







  height:42px;padding:0 16px;border-bottom:1px solid #edf2f7;background:#fff;







}







.pcw-card-head h2{color:var(--pcw-ink);font-size:16px;font-weight:700;letter-spacing:-.01em}







.pcw-card-head h2::after{content:"";display:block;width:28px;height:3px;margin-top:7px;border-radius:999px;background:var(--pcw-primary)}







.pcw-card-head button{height:30px;padding:0 10px;border:1px solid var(--pcw-border);border-radius:8px;background:#fff;color:#334155;font-weight:600}







.pcw-card-head button:hover{border-color:#94a3b8;background:#f8fafc;color:var(--pcw-ink)}







.pcw-table-card{min-height:450px}







.pcw-table-card table,.pcw-right-table{font-size:13px}







th{height:38px;background:#f8fafc;color:#64748b;font-size:11px;font-weight:700;letter-spacing:.02em}







td{height:44px;color:#334155}







th,td{border-bottom:1px solid var(--pcw-border);padding:0 14px}







tbody tr:hover td{background:#fafafa}







.pcw-product strong,.pcw-right-table td:first-child strong,.pcw-module-name{color:var(--pcw-ink)}







.pcw-thumb{width:26px!important;height:26px!important;border-radius:7px!important;box-shadow:inset 0 0 0 1px rgba(255,255,255,.55)!important}







.pcw-thumb.greens{background:linear-gradient(135deg,#2f9b61 0%,#9be0ad 100%)}







.pcw-thumb.leaf{background:linear-gradient(135deg,#20b865 0%,#82dda4 100%)}







.pcw-thumb.cuke{background:linear-gradient(135deg,#328f3d 0%,#a8d86a 100%)}







.pcw-thumb.fish{background:linear-gradient(135deg,#8fa0b5 0%,#cfd8e4 100%)}







.pcw-thumb.potato{background:linear-gradient(135deg,#d39a18 0%,#f3d568 100%)}







.pcw-thumb.egg{background:linear-gradient(135deg,#f3a536 0%,#ffd077 100%)}







.pcw-link{color:var(--pcw-primary);font-weight:700;text-decoration:underline;text-underline-offset:3px}







.pcw-pages{gap:6px;padding:12px 16px;border-top:1px solid var(--pcw-border);background:#fcfcfd}







.pcw-pages button{border-color:var(--pcw-border);border-radius:8px;box-shadow:none}







.pcw-pages button.active{border-color:var(--pcw-primary);background:var(--pcw-primary);color:#fff}







.pcw-pages em{color:#64748b}







.pcw-empty-row td{height:132px;background:#fff}







.pcw-empty-state,.pcw-panel-empty{gap:8px;max-width:360px;margin:auto;color:var(--pcw-muted);text-align:center}







.pcw-empty-state::before,.pcw-panel-empty::before{content:"";display:block;width:36px;height:36px;margin:0 auto 2px;border:1px solid var(--pcw-border);border-radius:10px;background:linear-gradient(#fff,#f8fafc);box-shadow:inset 0 -1px 0 rgba(15,23,42,.04)}







.pcw-empty-state strong,.pcw-panel-empty strong{color:var(--pcw-ink);font-size:14px;font-weight:700}







.pcw-empty-state span,.pcw-panel-empty span{color:var(--pcw-muted);font-size:12px;line-height:1.6}







.pcw-right-tag{border-radius:999px;background:#f1f5f9;color:#334155}







.pcw-chart{min-height:220px}







.pcw-chart .pcw-legend{gap:18px;padding:12px 16px 6px}







.pcw-chart .pcw-legend span{font-weight:700}







.pcw-chart .pcw-legend span:before{width:16px;height:4px}







.pcw-chart svg{height:134px;padding:0 12px 8px}







.pcw-chart .grid path{stroke:#edf2f7;stroke-width:1}







.pcw-chart .line-blue,.pcw-chart .line-green{stroke-width:2.7}







.pcw-chart .dots circle{r:2.6;fill:var(--pcw-primary);stroke:#fff;stroke-width:1.5}







.pcw-chart-foot{border-top:1px solid var(--pcw-border);background:#fcfcfd}







.pcw-alert-table-card td{height:40px}







.pcw-module-market .pcw-module-grid,.pcw-module-suppliers .pcw-module-grid,.pcw-module-purchase .pcw-module-grid,.pcw-module-quotes .pcw-module-grid,.pcw-module-plan .pcw-module-grid,.pcw-module-reports .pcw-module-grid,.pcw-module-settings .pcw-module-grid{grid-template-columns:minmax(0,1fr) 430px;grid-template-areas:"table panel" "chart flow" "chart activity";gap:12px}







.pcw-module-market .pcw-module-activity,.pcw-module-suppliers .pcw-module-activity{display:grid}







.pcw-module-panel,.pcw-module-flow{min-height:178px}







.pcw-module-table{min-height:352px}







.pcw-module-table td{height:46px!important}







.pcw-module-chart-panel{min-height:320px}







.pcw-module-panel article,.pcw-module-flow p,.pcw-module-activity article{min-height:58px}







.pcw-module-activity em{border-radius:999px;background:#ecfdf5;color:#16a34a;padding:3px 8px;font-size:11px}







.pcw-action-toast{border-color:var(--pcw-border);border-radius:10px;background:var(--pcw-ink);color:#fff;box-shadow:0 12px 28px rgba(15,23,42,.18)}@media (max-width:1180px){.pcw{grid-template-columns:196px minmax(0,1fr)}.pcw-right{grid-template-columns:repeat(2,minmax(0,1fr))}.pcw-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}.pcw-filter,.pcw-filter.section-alerts,.pcw-filter.is-alert,.pcw-filter.section-market,.pcw-filter.section-purchase,.pcw-filter.section-plan,.pcw-filter.section-reports,.pcw-filter.section-settings,.pcw-filter.section-suppliers,.pcw-filter.section-quotes{grid-template-columns:repeat(2,minmax(0,1fr));}}















/* detail-pass: remove dashboard noise and push pages closer to 食采云 reference */







.pcw-card::before,







.pcw-card-head h2::after{content:none!important;display:none!important}







.pcw-card{box-shadow:0 8px 22px rgba(15,23,42,.035)}







.pcw-card-head{height:48px}







.pcw-filter{display:flex;flex-wrap:wrap;align-items:center;padding:10px;border:1px solid var(--pcw-border);background:#fff;box-shadow:0 8px 22px rgba(15,23,42,.025)}







.pcw-filter-item{flex:0 0 132px}.pcw-filter.section-suppliers .pcw-filter-item,.pcw-filter.section-quotes .pcw-filter-item{flex-basis:152px}.pcw-filter.section-market .pcw-filter-item,.pcw-filter.section-purchase .pcw-filter-item,.pcw-filter.section-plan .pcw-filter-item{flex-basis:156px}







.pcw-filter .pcw-export{margin-left:auto;background:#f8fbff;border-color:#bfd2ff;border-radius:10px;color:var(--pcw-primary)}







.pcw-filter button.active{border-color:#bfdbfe;background:#eaf2ff;color:var(--pcw-primary);font-weight:800;box-shadow:none}







.pcw-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}.pcw-kpis article{position:relative;padding-left:20px}.pcw-kpis article:before{content:"";position:absolute;left:0;top:18px;bottom:18px;width:3px;border-radius:999px;background:var(--pcw-primary)}.pcw-kpis article:after{content:none!important}.pcw-kpis article:nth-child(2):before{background:var(--pcw-success)}.pcw-kpis article:nth-child(3):before{background:var(--pcw-warn)}.pcw-kpis article:nth-child(4):before{background:var(--pcw-danger)}







.pcw-empty-row td{height:84px}.pcw-empty-state::before,.pcw-panel-empty::before{content:none}.pcw-chart-empty{min-height:auto;padding:12px 16px;border-style:solid;background:rgba(255,255,255,.94)}







th{font-size:12px;letter-spacing:0;background:#f7faff}tbody tr:hover td{background:#f8fbff}.pcw-table-card td:nth-child(4),.pcw-table-card td:nth-child(5){color:#10203d;font-weight:800;text-align:right}.pcw-table-card th:nth-child(4),.pcw-table-card th:nth-child(5){text-align:right}.pcw-table-card td:nth-child(7){font-weight:800}







.pcw-right-table thead{display:none}.pcw-right-table td{height:46px}.pcw-right-table td:nth-child(2){color:var(--pcw-primary);font-weight:800}.pcw-right-table tr:not(:last-child) td{border-bottom:1px solid #eef3f8}.pcw-right-tag{background:#eaf2ff;color:var(--pcw-primary)}







.pcw-trend-page{grid-template-columns:minmax(0,1.36fr) 360px;gap:14px}.pcw-trend-chart-card{min-height:360px}.pcw-segments{padding:3px;border:1px solid #dbe7f6;border-radius:999px;background:#f8fbff}.pcw-segments button{height:30px;border:0;border-radius:999px;background:transparent}.pcw-segments button.active{background:var(--pcw-primary);color:#fff;box-shadow:0 6px 14px rgba(37,99,235,.2)}.pcw-legend.trend{justify-content:flex-end;padding:12px 16px 4px}.pcw-alert-command-metrics article{border-radius:12px;padding:14px 14px 14px 18px}.pcw-alert-command-metrics article:before{top:14px;bottom:14px;width:4px}.pcw-alert-table-card td{height:46px}.pcw-alert-table-card td:nth-child(4){font-weight:800}.pcw-alert-table-card .pcw-module-status,.pcw-module-status{border-radius:999px}







.pcw-side-systems:before{content:none}.pcw-side-systems{display:grid;gap:8px}.pcw-side-systems .pcw-system,.pcw-side-systems .pcw-side-sync{display:grid}.pcw-side-sync{padding:8px 10px;border-radius:10px;background:#f8fbff}@media (max-width:1180px){.pcw{grid-template-columns:196px minmax(0,1fr)}.pcw-right{grid-template-columns:repeat(2,minmax(0,1fr))}.pcw-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}.pcw-filter,.pcw-filter.section-alerts,.pcw-filter.is-alert,.pcw-filter.section-market,.pcw-filter.section-purchase,.pcw-filter.section-plan,.pcw-filter.section-reports,.pcw-filter.section-settings,.pcw-filter.section-suppliers,.pcw-filter.section-quotes{display:flex}.pcw-filter-item{flex:1 1 180px}.pcw-filter .pcw-export{margin-left:0}}







/* page-pass: per-page refinement for 食采云 style */







.pcw-main{gap:14px;padding:18px 20px 22px;background:var(--pcw-bg)}







.pcw-grid{grid-template-columns:minmax(0,1fr) 336px;gap:14px}







.pcw-bottom{grid-template-columns:minmax(0,1fr) 360px 360px;gap:14px}







.pcw-table-card{min-height:430px;overflow:hidden}







.pcw-table-card table{table-layout:fixed}







.pcw-table-card th:first-child,.pcw-table-card td:first-child{padding-left:18px}







.pcw-product{display:flex;align-items:center;gap:9px;min-width:0}.pcw-product strong{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pcw-product span:not(.pcw-thumb){display:block;color:#94a3b8;font-size:11px;line-height:1.2}







.pcw-right{gap:14px}.pcw-right-table tr{display:grid;grid-template-columns:minmax(0,1fr) 74px 52px;align-items:center;padding:0 12px}.pcw-right-table td,.pcw-right-table th{display:block!important;height:auto;padding:10px 0;border-bottom:0}.pcw-right-table td:first-child{display:flex!important;align-items:center;gap:8px;min-width:0}.pcw-right-table td:first-child strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pcw-right-table td:nth-child(2){justify-self:end}.pcw-right-table td:nth-child(3){justify-self:end;color:#64748b;font-size:12px}.pcw-right-table tr:not(:last-child){border-bottom:1px solid #eef3f8}







.pcw-chart{position:relative;overflow:hidden}.pcw-chart svg{height:146px}.pcw-chart-foot{height:42px;padding:0 14px}.pcw-chart-foot button{color:var(--pcw-primary);font-weight:800}







.pcw-timeline p{display:grid;grid-template-columns:54px minmax(0,1fr);gap:8px;margin:0 16px;padding:11px 0;color:#24344d}.pcw-timeline p span{width:auto;color:#64748b;font-size:12px;font-weight:700}







.pcw-alerts p{grid-template-columns:minmax(0,1fr) auto;gap:6px 10px;margin:0 14px;padding:10px 0 10px 12px;border-left:3px solid var(--pcw-danger);color:#24344d}.pcw-alerts p strong{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pcw-alerts p span{justify-self:end;color:#10203d;font-weight:800}.pcw-alerts p small{grid-column:1/-1;color:#64748b}.pcw-alerts p.fall{border-left-color:var(--pcw-success)}.pcw-alerts p.warn{border-left-color:var(--pcw-warn)}







.pcw-trend-page{grid-template-columns:minmax(0,1.42fr) 352px;grid-template-areas:"chart side" "market side" "dynamics peers";gap:14px}.pcw-trend-chart-card{min-height:382px}.pcw-trend-chart-card .pcw-card-head{height:52px}.pcw-trend-side{gap:14px}.pcw-trend-quotes thead{display:none}.pcw-trend-quotes tr{display:grid;grid-template-columns:minmax(0,1fr) 58px 72px 50px;align-items:center;padding:0 12px}.pcw-trend-quotes td{height:auto;padding:10px 0;border-bottom:0}.pcw-trend-quotes tr:not(:last-child){border-bottom:1px solid #eef3f8}.pcw-trend-alert thead{display:none}.pcw-trend-alert tr{display:grid;grid-template-columns:minmax(0,1fr) 70px 58px;align-items:center;padding:0 12px}.pcw-trend-alert td{height:auto;padding:10px 0;border-bottom:0}.pcw-trend-alert tr:not(:last-child){border-bottom:1px solid #eef3f8}.pcw-trend-dynamics p{display:grid;grid-template-columns:54px auto minmax(0,1fr);align-items:center;gap:8px}.pcw-trend-dynamics p span{margin:0}.pcw-alert-command-copy h2{font-size:21px}.pcw-alert-command-metrics article{border-radius:12px;background:#fff}.pcw-alert-command-actions button{border-radius:9px}.pcw-alert-table-card{overflow:hidden}.pcw-alert-table-card table{table-layout:fixed}.pcw-alert-table-card th,.pcw-alert-table-card td{padding:0 10px}.pcw-alert-table-card td:first-child{display:flex;align-items:center;gap:8px;min-width:0}.pcw-alert-table-card td:first-child strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}@media (max-width:1320px){.pcw-bottom{grid-template-columns:minmax(0,1fr) 360px}.pcw-alerts{grid-column:1/-1}.pcw-trend-page{grid-template-columns:minmax(0,1fr) 340px}}@media (max-width:1180px){.pcw-trend-page{grid-template-areas:"chart" "side" "market" "dynamics" "peers"}.pcw-bottom{display:grid}.pcw-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}







/* final-pass: quiet remaining shell chrome and tighten hierarchy */







.pcw-side{border-right-color:#dfe7f1;background:linear-gradient(180deg,#fff 0%,#fff 82%,#fbfdff 100%)}







.pcw-side-head{height:42px;padding:0 4px}.pcw-side-head strong{font-size:18px;color:#10203d;letter-spacing:0}







.pcw-logo{width:32px;height:32px;border-radius:10px;background:linear-gradient(135deg,#2563eb,#3b82f6)}







.pcw-nav{gap:8px;padding-top:18px}.pcw-nav-item{min-height:42px;border-radius:10px;color:#31415c}.pcw-nav-item.active,.pcw-nav-item.active:hover{box-shadow:none}







.pcw-top{height:54px;padding:0 20px;border-bottom:1px solid #e8eef6;background:#fff;box-shadow:none}.pcw-top-actions button{border-radius:8px}







.pcw-location{padding-right:18px}.pcw-location:after{height:18px;background:#e2e8f0}







.pcw-kpis article{padding-top:16px;padding-bottom:16px}.pcw-kpis strong{font-size:26px;line-height:1.05}.pcw-kpis span{font-size:12px}.pcw-kpis em{font-size:11px}







.pcw-filter{gap:10px}.pcw-filter button{height:36px;border-radius:10px;background:#fff}.pcw-filter .pcw-export{height:36px}







.pcw-card{border:1px solid #dfe7f1;background:#fff}.pcw-card-head{padding:0 14px}.pcw-card-head h2{font-size:15px}.pcw-card-head button{height:28px;padding:0 10px;border-radius:8px}







.pcw-table-card th,.pcw-table-card td,.pcw-right-table td,.pcw-trend-quotes td,.pcw-trend-alert td,.pcw-alert-table-card td{font-size:12px}







.pcw-table-card tbody tr:hover td,.pcw-trend-quotes tr:hover td,.pcw-trend-alert tr:hover td,.pcw-alert-table-card tbody tr:hover td{background:#f8fbff}







.pcw-empty-state,.pcw-panel-empty{max-width:320px}.pcw-empty-state span,.pcw-panel-empty span{line-height:1.55}







.pcw-trend-chart-card{overflow:hidden}.pcw-trend-chart-card .pcw-card-head{height:50px}.pcw-trend-chart-card .pcw-legend{padding-top:10px}.pcw-trend-chart-card .pcw-chart-empty{border-radius:12px}







.pcw-alert-command-metrics{gap:10px}.pcw-alert-command-metrics strong{font-size:20px}.pcw-alert-table-toolbar{gap:8px}.pcw-alert-table-toolbar span{height:25px;padding:0 9px}







.pcw-module-command{border-radius:14px}.pcw-module-hero{border-radius:14px}.pcw-module-panel,.pcw-module-flow,.pcw-module-activity{border-radius:14px}@media (max-width:1180px){.pcw-side{position:sticky}.pcw-top{height:auto;min-height:54px;flex-wrap:wrap;padding:10px 16px}.pcw-filter{padding:10px}.pcw-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.pcw-bottom{grid-template-columns:1fr}}







/* final-pass-2: reduce toolbars and sidebar chrome */







.pcw-side-systems{display:flex;align-items:center;gap:8px;min-height:40px;padding:0 4px;border-top:0}.pcw-side-systems:before{content:"收起菜单";display:flex;align-items:center;justify-content:flex-start;width:100%;height:36px;color:#64748b;font-size:13px;font-weight:700}















.pcw-filter{display:flex;flex-wrap:wrap;align-items:center;gap:10px 12px;min-height:40px;padding:0;border:0;background:transparent;box-shadow:none}.pcw-filter-item{flex:0 0 132px}.pcw-filter button{height:36px;border-radius:8px;border-color:#dbe5f1;background:#fff;box-shadow:none;font-size:13px}.pcw-filter .pcw-export{height:36px;margin-left:auto;border-color:#bfdbfe;background:#eef5ff;color:var(--pcw-primary)}.pcw-filter button.active{border-color:#bfdbfe;background:#eaf2ff;color:var(--pcw-primary);font-weight:700}







.pcw-card-head{height:46px;padding:0 18px;border-bottom:1px solid #eef3f8}.pcw-card-head h2{font-size:15px;font-weight:700;color:#10203d}.pcw-card-head button{height:auto;padding:0;border:0;background:transparent;color:#64748b;font-size:12px;font-weight:600;box-shadow:none}.pcw-card-head button:hover{background:transparent;color:var(--pcw-primary)}







.pcw-link{border:0;background:transparent;color:var(--pcw-primary);font-weight:700;text-decoration:none}.pcw-link:hover{text-decoration:underline;text-underline-offset:3px}







th{height:36px;background:#f8fafc;color:#64748b;font-size:12px;font-weight:600}td{height:42px;color:#334155}tbody tr:hover td{background:#f8fbff}







.pcw-alert-table-toolbar{padding:10px 14px}.pcw-alert-table-toolbar span{height:24px;padding:0 8px;border-radius:999px;background:#f8fbff;border:1px solid #e2e8f0}.pcw-alert-table-toolbar b{background:#eaf2ff}@media (max-width:1180px){.pcw-side-systems{min-height:36px}.pcw-filter{gap:8px 10px}.pcw-filter-item{flex:1 1 160px}}







/* final-pass-3: page identity refinements */







.pcw-kpis.is-summary article{padding-left:74px}.pcw-kpis.is-summary article:before{left:18px;top:50%;bottom:auto;width:38px;height:38px;border-radius:12px;transform:translateY(-50%);background:#eaf2ff;box-shadow:inset 0 0 0 1px #dbeafe}.pcw-kpis.is-summary article:after{content:""!important;display:block!important;position:absolute;left:30px;top:50%;width:14px;height:14px;border:2px solid var(--pcw-primary);border-top-color:transparent;border-radius:50%;transform:translateY(-50%) rotate(-28deg);background:transparent}.pcw-kpis.is-summary article:nth-child(2):before{background:#ecfdf5;box-shadow:inset 0 0 0 1px #bbf7d0}.pcw-kpis.is-summary article:nth-child(2):after{border-color:var(--pcw-success);border-top-color:transparent}.pcw-kpis.is-summary article:nth-child(3):before{background:#fff7ed;box-shadow:inset 0 0 0 1px #fed7aa}.pcw-kpis.is-summary article:nth-child(3):after{border-color:var(--pcw-warn);border-top-color:transparent}.pcw-kpis.is-summary article:nth-child(4):before{background:#fef2f2;box-shadow:inset 0 0 0 1px #fecaca}.pcw-kpis.is-summary article:nth-child(4):after{border-color:var(--pcw-danger);border-top-color:transparent}







.pcw-trend-chart-card{background:linear-gradient(180deg,#fff 0%,#f8fbff 100%)}.pcw-trend-chart-card .grid path{stroke:#e8eef6}.pcw-trend-chart-card .line-blue{stroke-width:3}.pcw-trend-chart-card .line-green{stroke-width:2.7}.pcw-alert-command-copy{padding-left:4px}.pcw-alert-command-copy span{color:var(--pcw-danger)}







.pcw-top-actions .pcw-user{min-width:72px;background:#f8fbff;color:#334155}.pcw-top-actions .pcw-user:hover{background:#eef5ff;color:var(--pcw-primary)}@media (max-width:1180px){.pcw-kpis.is-summary article{padding-left:68px}}







/* final-pass-4: user-facing visual polish, closer to 食采云 mobile/B端看板 */







.pcw{font-family:"Inter","PingFang SC","Microsoft YaHei",system-ui,sans-serif}







.pcw-main{gap:16px;background:linear-gradient(180deg,#f6f8fc 0%,#f3f7fb 100%)}







.pcw-side{box-sizing:border-box}







.pcw-top{height:56px}.pcw-top h1{font-size:19px}.pcw-location-button small{color:#7a8aa3}.pcw-top-actions button:not(.pcw-user){color:#52647f}.pcw-top-actions span{box-shadow:0 0 0 2px #fff}







.pcw-filter{margin-bottom:-2px}.pcw-filter button{min-width:0;padding-inline:12px;color:#24344d}.pcw-filter-item>button small{color:#94a3b8}.pcw-filter .pcw-export{background:#fff;color:#1d4ed8}.pcw-filter .pcw-export:hover{background:#eef5ff;border-color:#bfdbfe}







.pcw-kpis{gap:14px}.pcw-kpis article{min-height:96px;border-radius:12px!important}.pcw-kpis span{color:#607089;font-weight:700}.pcw-kpis strong{font-size:25px;letter-spacing:-.02em}.pcw-kpis small{color:#7a8aa3}







.pcw-card{border-radius:12px;box-shadow:0 1px 2px rgba(15,23,42,.025)}.pcw-card-head{height:44px}.pcw-card-head h2{font-size:15px;font-weight:800}.pcw-card-head span{color:#7a8aa3}.pcw-card-head button{color:#64748b}.pcw-card-head button:hover{color:#2563eb;text-decoration:none}







.pcw-table-card{min-height:420px}.pcw-table-card th{height:38px;background:#f7faff;color:#52647f;font-weight:700}.pcw-table-card td{height:42px}.pcw-table-card tbody tr:nth-child(even) td{background:#fcfdff}.pcw-table-card tbody tr:hover td{background:#eef6ff}.pcw-table-card td:nth-child(4),.pcw-table-card td:nth-child(5){font-variant-numeric:tabular-nums}.pcw-row-actions button,.pcw-link{text-decoration:none}.pcw-row-actions button:hover,.pcw-link:hover{text-decoration:underline;text-underline-offset:3px}







.pcw-right-table tr{min-height:48px}.pcw-right-tag{height:20px;padding-inline:7px;background:#eef6ff;color:#2563eb;font-weight:800}







.pcw-chart svg{height:150px}.pcw-chart-foot{height:40px;background:#fbfdff}.pcw-chart-foot span{color:#7a8aa3}.pcw-legend span{color:#52647f}







.pcw-bottom{grid-template-columns:minmax(0,1fr) 340px 360px}.pcw-timeline,.pcw-advice,.pcw-alerts{min-height:190px}.pcw-timeline p,.pcw-advice li,.pcw-alerts p{font-size:13px}.pcw-timeline p span{color:#7a8aa3}.pcw-advice li:before{top:17px;background:#2563eb}.pcw-alerts p{border-left-width:4px}.pcw-alerts p span{font-variant-numeric:tabular-nums}







.pcw-trend-page{grid-template-columns:minmax(0,1.45fr) 348px}.pcw-trend-chart-card{min-height:376px}.pcw-segments{background:#f5f8fd}.pcw-segments button{font-size:12px;font-weight:700}.pcw-trend-quotes tr,.pcw-trend-alert tr{min-height:46px}.pcw-trend-dynamics p span{background:#eef5ff;color:#2563eb;font-weight:700}.pcw-alert-command-copy h2{font-size:20px}.pcw-alert-command-metrics article{box-shadow:0 1px 2px rgba(15,23,42,.025)}.pcw-alert-table-card td{height:42px}@media (max-width:1320px){.pcw-bottom{grid-template-columns:minmax(0,1fr) 340px}.pcw-advice{grid-column:1/-1}.pcw-trend-page{grid-template-columns:minmax(0,1fr) 340px}}@media (max-width:1180px){.pcw-main{padding:16px}.pcw-kpis{gap:10px}.pcw-filter{padding:0}.pcw-filter-item{flex:1 1 160px}.pcw-filter .pcw-export{margin-left:0}}







/* final-pass-5: align closer to provided Codex design drafts — visible navigation hierarchy, compact data cards, real-data sidebar */







.pcw{







  --pcw-bg:#f3f6fb;







  --pcw-primary:#2563eb;







  --pcw-primary-deep:#1d4ed8;







  --pcw-primary-soft:#edf5ff;







  --pcw-border:#dfe7f1;







  --pcw-ink:#0f1f3d;







  --pcw-muted:#64748b;







  --pcw-faint:#94a3b8;







  grid-template-columns:204px minmax(0,1fr);







  background:#f3f6fb;







}







.pcw-side{width:204px;padding:18px 12px 14px;background:#fff;border-right:1px solid #dfe7f1}







.pcw-side-head{height:46px;margin-bottom:4px;padding:0 6px}







.pcw-logo{width:34px;height:34px;border-radius:12px;background:linear-gradient(135deg,#1d4ed8,#60a5fa);box-shadow:0 10px 20px rgba(37,99,235,.18)}







.pcw-logo:before{left:4px;top:9px;width:27px;height:15px;background:#2f7df6;box-shadow:-3px 3px 0 #2f7df6,7px -5px 0 #2f7df6,0 6px 12px rgba(47,125,246,.18)}







.pcw-logo:after{left:12px;top:14px;width:7px;height:7px}







.pcw-brand-copy{gap:0}.pcw-brand-copy strong{font-size:18px;line-height:22px;color:#0f1f3d}.pcw-brand-copy small{display:block;color:#94a3b8;font-size:10px;font-weight:600;line-height:14px}







.pcw-nav{gap:14px;padding-top:14px}.pcw-nav-group{gap:6px}.pcw-nav-group>span{display:block;padding:0 10px 2px;color:#a0aec0;font-size:11px;font-weight:800;letter-spacing:.08em}







.pcw-nav-item{height:40px;min-height:40px;border-radius:10px;color:#334155;font-size:13px}.pcw-nav-item:hover{background:#f6f9ff;color:#1d4ed8}.pcw-nav-item.active,.pcw-nav-item.active:hover{background:#eaf2ff;border-color:#cfe2ff;color:#1d4ed8;font-weight:800;box-shadow:inset 3px 0 0 #2563eb}.pcw-nav-icon{width:17px!important;height:17px!important}







.pcw-side-systems{display:grid;gap:8px;min-height:auto;margin-top:auto;padding:10px 2px 0;border-top:1px solid #edf2f7}.pcw-side-systems:before{content:none!important}.pcw-side-systems .pcw-system,.pcw-side-systems .pcw-side-sync{display:grid!important}.pcw-side-sync{gap:2px;padding:9px 10px;border:1px solid #e5edf6;border-radius:12px;background:#f8fbff}.pcw-side-sync span,.pcw-system span{font-size:11px;color:#7a8aa3}.pcw-side-sync strong,.pcw-system strong{font-size:13px;color:#10203d}.pcw-system{min-height:46px;padding:8px 10px;border-radius:12px;background:#fff;border-color:#e5edf6}.pcw-system.primary{background:#edf5ff;border-color:#cfe2ff;box-shadow:inset 3px 0 0 #2563eb}







.pcw-top{height:58px;padding:0 22px;border-bottom-color:#e6edf6}.pcw-top h1{font-size:20px;letter-spacing:-.01em}.pcw-location{min-width:176px}.pcw-top-actions{gap:8px}.pcw-top-actions button{height:32px;padding:0 10px;border-radius:10px}.pcw-user{background:#eef5ff!important;color:#1d4ed8!important;font-weight:800}







.pcw-main{gap:16px;padding:18px 20px 22px;background:linear-gradient(180deg,#f7f9fd 0%,#f3f6fb 100%)}







.pcw-filter{gap:10px 12px;margin:0;padding:10px 12px;border:1px solid #e1e9f3;border-radius:14px;background:#fff;box-shadow:0 8px 20px rgba(15,23,42,.025)}.pcw-filter button{height:36px;border-radius:10px;border-color:#dbe5f1;background:#fff;font-size:13px}.pcw-filter .pcw-export{background:#eef5ff;border-color:#cfe2ff;color:#1d4ed8}.pcw-filter button.active,.pcw-filter-item>button.open{border-color:#bfdbfe;background:#edf5ff;color:#1d4ed8;font-weight:800}







.pcw-kpis{gap:14px}.pcw-kpis article{min-height:98px;border-radius:14px!important;background:linear-gradient(180deg,#fff,#fbfdff);box-shadow:0 8px 20px rgba(15,23,42,.026)}.pcw-kpis span{font-size:12px;font-weight:800;color:#607089}.pcw-kpis strong{font-size:26px;color:#0f1f3d}.pcw-kpis small{font-size:11px;color:#7a8aa3}.pcw-kpis.is-summary article{padding-left:76px}.pcw-kpis.is-summary article:before{left:18px;width:40px;height:40px;border-radius:14px}







.pcw-card{border-radius:14px;border-color:#dfe7f1;box-shadow:0 8px 20px rgba(15,23,42,.026)}.pcw-card-head{height:46px;padding:0 18px}.pcw-card-head h2{font-size:15px;font-weight:800;color:#10203d}.pcw-card-head span{font-weight:700;color:#7a8aa3}.pcw-card-head button{color:#64748b}.pcw-card-head button:hover{color:#1d4ed8}







.pcw-grid{grid-template-columns:minmax(0,1fr) 348px;gap:16px}.pcw-bottom{grid-template-columns:minmax(0,1fr) 348px 360px;gap:16px}.pcw-right{gap:16px}.pcw-table-card{min-height:426px}.pcw-table-card th{height:38px;background:#f7faff;color:#52647f;font-weight:800}.pcw-table-card td{height:42px;color:#24344d}.pcw-table-card th:first-child,.pcw-table-card td:first-child{padding-left:18px}.pcw-table-card tbody tr:nth-child(even) td{background:#fcfdff}.pcw-table-card tbody tr:hover td{background:#eef6ff}.pcw-product strong{font-weight:800}.pcw-link{color:#1d4ed8;font-weight:800}







.pcw-right-table tr{min-height:48px}.pcw-right-tag{background:#edf5ff;color:#1d4ed8}.pcw-chart svg{height:152px}.pcw-chart-foot{height:40px;background:#fbfdff}.pcw-timeline,.pcw-advice,.pcw-alerts{min-height:188px}.pcw-alerts p{border-left-width:4px}







.pcw-trend-page{grid-template-columns:minmax(0,1.45fr) 360px;gap:16px}.pcw-trend-chart-card{min-height:382px}.pcw-segments{border-radius:999px;background:#f5f8fd}.pcw-segments button{font-weight:800}.pcw-trend-side{gap:16px}.pcw-alert-command-copy h2{font-size:21px}.pcw-alert-command-metrics article{border-radius:13px}.pcw-alert-table-card td{height:42px}@media (max-width:1320px){.pcw-trend-page{grid-template-columns:minmax(0,1fr) 348px}}@media (max-width:1180px){.pcw{grid-template-columns:196px minmax(0,1fr)}.pcw-side{width:196px}}







/* final-pass-6: low-risk PC workbench detail polish */







.pcw{--pcw-card-shadow:0 10px 24px rgba(15,23,42,.035);--pcw-card-shadow-hover:0 14px 30px rgba(15,23,42,.055)}







.pcw-main{gap:17px;padding:20px 22px 24px}







.pcw-side{box-shadow:1px 0 0 rgba(15,23,42,.02)}







.pcw-nav{gap:16px}.pcw-nav-group{gap:7px}.pcw-nav-group>span{padding-left:12px;color:#9aa8ba;font-size:10px;line-height:16px}.pcw-nav-item{padding-inline:12px}.pcw-nav-item.active,.pcw-nav-item.active:hover{background:linear-gradient(90deg,#eaf2ff,#f5f9ff);border-color:#c7dcff;box-shadow:inset 3px 0 0 var(--pcw-primary)}







.pcw-top-actions{padding:3px;border:1px solid #e6edf6;border-radius:13px;background:#f8fbff}.pcw-top-actions button{height:30px;padding-inline:10px}.pcw-top-actions button:not(.pcw-user):hover{background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.04)}.pcw-top-actions .pcw-user{min-width:78px;border:1px solid #cfe2ff!important;background:#fff!important}







.pcw-filter{gap:10px;padding:10px 12px}.pcw-filter-item{flex-basis:136px}.pcw-filter.section-suppliers .pcw-filter-item,.pcw-filter.section-quotes .pcw-filter-item{flex-basis:154px}.pcw-filter.section-market .pcw-filter-item,.pcw-filter.section-purchase .pcw-filter-item,.pcw-filter.section-plan .pcw-filter-item{flex-basis:158px}.pcw-filter .pcw-export{position:relative;margin-left:auto;box-shadow:inset 0 0 0 1px rgba(37,99,235,.04)}







.pcw-kpis{gap:16px}.pcw-kpis article{min-height:96px;padding-top:15px;padding-bottom:15px;box-shadow:var(--pcw-card-shadow)}.pcw-kpis strong{font-variant-numeric:tabular-nums}.pcw-kpis small{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pcw-kpis.is-summary article{padding-left:78px}







.pcw-card{box-shadow:var(--pcw-card-shadow);transition:box-shadow .16s ease,border-color .16s ease}.pcw-card-head{height:48px}.pcw-card-head h2{display:flex;align-items:center;gap:8px}.pcw-card-head button{border-radius:999px}.pcw-card-head button:hover{background:#eef5ff;color:#1d4ed8}







.pcw-grid{grid-template-columns:minmax(0,1fr) 356px;gap:17px}.pcw-right{gap:17px}.pcw-bottom{grid-template-columns:minmax(0,1fr) 352px 360px;gap:17px}.pcw-table-card{min-height:432px}.pcw-table-card th,.pcw-table-card td{padding-inline:10px}.pcw-table-card th:first-child,.pcw-table-card td:first-child{padding-left:18px}.pcw-table-card td{height:43px}.pcw-pages{min-height:50px}.pcw-pages button{width:28px;height:28px}.pcw-pages em:first-of-type{margin-left:auto}







.pcw-right-table tr{padding-inline:14px}.pcw-right-table td:nth-child(2){font-weight:900}.pcw-chart svg{height:154px}.pcw-chart-foot{padding-inline:16px}







.pcw-module-command-actions,.pcw-alert-command-actions,.pcw-module-actions,.pcw-segments{column-gap:8px}.pcw-module-command-actions button,.pcw-alert-command-actions button,.pcw-module-actions button{border-radius:10px}







/* final-pass-7: PC density and right-column balance */







.pcw-nav-item.active:before{content:"";position:absolute;left:10px;top:50%;width:6px;height:6px;border-radius:999px;background:#2563eb;transform:translateY(-50%);box-shadow:0 0 0 4px #dbeafe}.pcw-nav-item.active{padding-left:24px}.pcw-nav-item.active .pcw-nav-icon{color:#1d4ed8}







.pcw-filter{align-items:center}.pcw-filter-item>button span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pcw-filter-menu{border-radius:12px;box-shadow:0 18px 42px rgba(15,23,42,.12)}.pcw-filter-search{border-radius:9px;background:#fbfdff}.pcw-price-toggle{padding:2px;border:1px solid #dbe5f1;border-radius:999px;background:#fff}.pcw-price-toggle button{height:30px;border:0;border-radius:999px!important;box-shadow:none;text-align:center}.pcw-price-toggle button.active{background:#2563eb;color:#fff}







.pcw-table-card th{height:36px}.pcw-table-card td{height:40px}.pcw-table-card tbody tr{transition:background-color .14s ease}.pcw-table-card td:nth-child(4),.pcw-table-card td:nth-child(5),.pcw-table-card td:nth-child(6),.pcw-table-card td:nth-child(8){font-variant-numeric:tabular-nums}.pcw-table-card td:nth-child(8){color:#475569;font-weight:700}.pcw-table-card .pcw-link{display:inline-flex;align-items:center;justify-content:center;min-width:58px;height:26px;border-radius:999px;background:#eef5ff;color:#1d4ed8;font-size:12px}.pcw-table-card .pcw-link:hover{background:#dbeafe;text-decoration:none}







.pcw-pages{gap:5px;background:#fbfdff}.pcw-pages button:not(:disabled):hover{border-color:#bfdbfe;background:#eef5ff;color:#1d4ed8}.pcw-pages button:disabled{background:#f8fafc;color:#cbd5e1;cursor:not-allowed}.pcw-pages em{margin-left:10px;color:#7a8aa3}







.pcw-right{grid-template-rows:auto minmax(226px,auto)}.pcw-right-table tr{grid-template-columns:minmax(0,1fr) 78px 48px;min-height:46px}.pcw-right-table td:first-child strong{font-size:12px}.pcw-right-tag{height:18px;padding-inline:6px;font-size:10px}.pcw-right-table .pcw-link{height:24px;padding:0 8px;border-radius:999px;background:#f8fbff;font-size:12px}.pcw-chart{min-height:232px}.pcw-chart .pcw-legend{justify-content:center;padding-top:10px}.pcw-chart svg{height:158px}.pcw-chart-foot{height:38px}.pcw-chart-empty.mini{top:54%;width:min(286px,78%);border-radius:12px}







.pcw-empty-row td{height:78px}.pcw-empty-state,.pcw-panel-empty{gap:5px}.pcw-empty-state strong,.pcw-panel-empty strong{font-size:13px}.pcw-empty-state span,.pcw-panel-empty span{color:#7a8aa3}.pcw-panel-empty.compact{min-height:66px}







.pcw-module-table td,.pcw-alert-table-card td{height:42px!important}.pcw-module-chart-panel svg{height:238px}@media (max-width:1320px){.pcw-grid{grid-template-columns:minmax(0,1fr) 340px}.pcw-bottom{grid-template-columns:minmax(0,1fr) 340px}.pcw-advice{grid-column:1/-1}}@media (max-width:1180px){.pcw-main{padding:16px}.pcw-kpis{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.pcw-filter-item{flex:1 1 160px}.pcw-filter .pcw-export{margin-left:0}.pcw-nav-item.active{padding-left:12px}.pcw-nav-item.active:before{content:none}}







/* final-pass-8: interaction stability and compact responsive safeguards */







.pcw{min-width:0}.pcw-app{overflow:hidden}.pcw-main{scrollbar-gutter:stable both-edges}.pcw-main::-webkit-scrollbar{width:10px;height:10px}.pcw-main::-webkit-scrollbar-thumb{border:2px solid transparent;border-radius:999px;background:#cbd5e1;background-clip:content-box}.pcw-main::-webkit-scrollbar-track{background:transparent}







.pcw-filter-menu{overflow:auto;overscroll-behavior:contain}.pcw-filter-menu::-webkit-scrollbar{width:8px}.pcw-filter-menu::-webkit-scrollbar-thumb{border:2px solid #fff;border-radius:999px;background:#cbd5e1}.pcw-filter-search:focus{outline:0;border-color:#bfdbfe;box-shadow:0 0 0 3px #eff6ff;background:#fff}







.pcw-filter-menu{


  width:min(520px,max(240px,calc(100vw - 48px)));


  max-width:calc(100vw - 48px);


  max-height:min(420px,calc(100vh - 180px));


}


.pcw-filter-search{


  width:100%;


  min-width:0;


  box-sizing:border-box;


}


.pcw-filter-menu button{


  display:block;


  width:100%;


  line-height:1.35;


  white-space:normal;


  overflow-wrap:anywhere;


}


.pcw-filter-item:nth-last-child(-n+2) .pcw-filter-menu{


  left:auto;


  right:0;


}





.pcw-filter-item>button small,.pcw-location-button small{transition:transform .16s ease,color .16s ease}.pcw-filter-item>button.open small,.pcw-location-button[aria-expanded="true"] small{transform:rotate(180deg);color:#2563eb}.pcw-filter button:disabled,.pcw-top-actions button:disabled{opacity:.58;cursor:not-allowed}.pcw-top-actions button:disabled:hover{background:transparent;box-shadow:none;color:#94a3b8}.pcw-right-table{min-width:0}.pcw-empty-row td{white-space:normal}.pcw-action-toast{position:fixed;right:24px;bottom:24px;z-index:80;max-width:min(360px,calc(100vw - 48px));pointer-events:none}







.pcw-card-head h2,.pcw-top h1{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pcw-card-head span{max-width:46%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pcw-dot{outline:none}.pcw-dot-hit{fill:transparent!important;pointer-events:all}.pcw-dot circle:not(.pcw-dot-hit){transition:r .14s ease,stroke .14s ease}.pcw-dot-active{fill:#1d4ed8!important;stroke:#fff;stroke-width:2}@media (prefers-reduced-motion:reduce){.pcw *{scroll-behavior:auto!important;transition:none!important;animation:none!important}.pcw-card:hover{transform:none}}@media (max-width:900px){.pcw{grid-template-columns:1fr}.pcw-side{position:relative;width:auto;grid-row:auto;padding:12px 14px}.pcw-side-head{height:38px}.pcw-nav{display:grid;grid-auto-flow:column;grid-auto-columns:max-content;gap:8px;overflow-x:auto;padding:8px 0 2px}.pcw-nav-group{display:contents}.pcw-nav-group>span{display:none}.pcw-nav-item{min-width:118px}.pcw-side-systems{display:none}.pcw-app{grid-template-rows:auto 1fr}.pcw-top{position:sticky;top:0;z-index:30;gap:10px;padding:10px 14px}.pcw-location{min-width:0}.pcw-top-actions{margin-left:0}.pcw-filter{display:flex;flex-wrap:wrap}.pcw-filter-item{flex:1 1 150px}.pcw-filter .pcw-export{width:auto;min-width:112px}.pcw-kpis{grid-template-columns:1fr}.pcw-card-head span{max-width:52%}.pcw-action-toast{right:12px;bottom:12px;max-width:calc(100vw - 24px)}}@media (max-width:1100px){
  .pcw-filter.section-summary .pcw-filter-item{flex:1 1 180px}
  .pcw-filter.section-summary .pcw-export{width:100%;min-width:0}
}@media (max-width:720px){
  .pcw-location{min-width:0;max-width:100%}
  .pcw-location-button{max-width:100%}
  .pcw-location-menu{left:0;right:auto;width:min(320px,calc(100vw - 32px))}
  .pcw-filter.section-summary .pcw-filter-item{flex:1 1 100%}
}







/* final-pass-9: readability and overflow polish */







.pcw-main{gap:18px}.pcw-right .pcw-card,.pcw-bottom .pcw-card,.pcw-module-panel,.pcw-module-flow,.pcw-module-activity{box-shadow:0 6px 16px rgba(15,23,42,.025)}







.pcw-table-card th,.pcw-alert-table-card th,.pcw-module-table th{font-weight:800;letter-spacing:.01em}.pcw-table-card td,.pcw-alert-table-card td,.pcw-module-table td{line-height:1.35}.pcw-table-card td{height:42px}.pcw-alert-table-card td,.pcw-module-table td{height:46px}.pcw-table-card td:nth-child(4),.pcw-table-card td:nth-child(5),.pcw-table-card td:nth-child(6),.pcw-table-card td:nth-child(8),.pcw-right-table td:nth-child(2),.pcw-module-table td:nth-child(n+2){font-variant-numeric:tabular-nums}







.pcw-product,.pcw-right-table td:first-child,.pcw-timeline p,.pcw-alerts p,.pcw-module-panel article,.pcw-module-flow p,.pcw-module-activity article{min-width:0}.pcw-product strong,.pcw-right-table strong,.pcw-timeline p,.pcw-alerts p strong,.pcw-module-name,.pcw-module-panel article b,.pcw-module-panel article small,.pcw-module-flow p span,.pcw-module-activity article strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}







.pcw-right-table{table-layout:fixed}.pcw-right-table th:nth-child(1){width:50%}.pcw-right-table th:nth-child(2){width:28%}.pcw-right-table th:nth-child(3){width:22%}.pcw-right-table td{height:40px}.pcw-right-table td:nth-child(2){white-space:nowrap;text-align:right}.pcw-right-table .pcw-link{min-width:54px;height:26px;padding:0 10px;border-radius:999px;background:#eef5ff;text-decoration:none}.pcw-right-table .pcw-link:hover{background:#dbeafe;color:#1d4ed8}







.pcw-timeline p{display:grid;grid-template-columns:58px minmax(0,1fr);gap:10px;align-items:center}.pcw-timeline p span{width:auto}.pcw-alerts p{grid-template-columns:minmax(0,1fr) auto auto;align-items:center}.pcw-alerts p em,.pcw-alerts p strong{min-width:0}.pcw-card-head button,.pcw-link{transition:background-color .14s ease,color .14s ease,border-color .14s ease,box-shadow .14s ease}.pcw-link:focus-visible{box-shadow:0 0 0 3px #dbeafe}@media (max-width:1320px){.pcw-main{gap:16px}.pcw-grid,.pcw-bottom,.pcw-right,.pcw-module-grid{gap:14px}.pcw-table-card table,.pcw-alert-table-card table,.pcw-module-table table{min-width:760px}}@media (max-width:900px){.pcw-main{gap:14px;padding:14px}.pcw-table-card td,.pcw-alert-table-card td,.pcw-module-table td{height:44px}.pcw-timeline p,.pcw-alerts p{white-space:normal}.pcw-timeline p{grid-template-columns:52px minmax(0,1fr)}}







/* final-pass-10: PC workbench first-screen balance and dense-table readability */







@media (min-width:1181px){



















  .pcw-main{padding:18px 22px 24px;gap:16px;scrollbar-gutter:auto;align-items:stretch;justify-items:stretch;grid-template-columns:minmax(0,1fr)}







  .pcw-filter{z-index:18;box-sizing:border-box;width:auto!important;max-width:100%}







  .pcw-kpis{grid-template-columns:repeat(5,minmax(132px,1fr));gap:14px;box-sizing:border-box;width:auto!important;max-width:100%}







  .pcw-kpis article{min-width:0;min-height:92px;padding:14px 18px 13px}







  .pcw-kpis.is-summary article{padding-left:72px}







  .pcw-kpis.is-summary article:before{left:18px;width:38px;height:38px}







  .pcw-kpis span,.pcw-kpis small{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}







  .pcw-grid{grid-template-columns:minmax(760px,1fr) minmax(328px,348px);align-items:start;box-sizing:border-box;width:auto!important;max-width:100%}







  .pcw-bottom{grid-template-columns:minmax(0,1fr) minmax(318px,348px) minmax(320px,360px);align-items:start;box-sizing:border-box;width:auto!important;max-width:100%}







  .pcw-table-card{min-height:428px}







  .pcw-table-card table{min-width:820px}







  .pcw-table-card th:nth-child(1),.pcw-table-card td:nth-child(1){width:138px}







  .pcw-table-card th:nth-child(2),.pcw-table-card td:nth-child(2){width:76px}







  .pcw-table-card th:nth-child(3),.pcw-table-card td:nth-child(3){width:150px}







  .pcw-table-card th:nth-child(4),.pcw-table-card td:nth-child(4),.pcw-table-card th:nth-child(5),.pcw-table-card td:nth-child(5){width:96px}







  .pcw-table-card th:nth-child(6),.pcw-table-card td:nth-child(6){width:58px}







  .pcw-table-card th:nth-child(7),.pcw-table-card td:nth-child(7){width:66px}







  .pcw-table-card th:nth-child(8),.pcw-table-card td:nth-child(8){width:68px}







  .pcw-table-card th:nth-child(9),.pcw-table-card td:nth-child(9){width:72px}







  .pcw-right{grid-template-rows:minmax(198px,auto) minmax(236px,auto)}







  .pcw-chart{min-height:236px}







  .pcw-chart svg{height:160px}







  .pcw-module-layout-coverage .pcw-module-grid,.pcw-module-layout-network .pcw-module-grid,.pcw-module-layout-ops .pcw-module-grid{grid-template-columns:minmax(420px,.92fr) minmax(0,1.08fr);grid-template-areas:"table panel" "table flow" "chart activity";box-sizing:border-box;width:100%}







  .pcw-module-layout-workflow .pcw-module-grid,.pcw-module-layout-ledger .pcw-module-grid,.pcw-module-layout-insight .pcw-module-grid{grid-template-columns:minmax(0,1fr) minmax(330px,370px);box-sizing:border-box;width:100%}







  .pcw-module-layout-coverage .pcw-module-table,.pcw-module-layout-network .pcw-module-table,.pcw-module-layout-ops .pcw-module-table{min-height:420px}







  .pcw-module-layout-coverage .pcw-module-table table,.pcw-module-layout-network .pcw-module-table table,.pcw-module-layout-ops .pcw-module-table table{min-width:760px}







  .pcw-peer-products table{min-width:100%!important}







  .pcw-peer-products th,.pcw-peer-products td{padding-inline:10px}







}@media (min-width:1440px){







  .pcw-grid{grid-template-columns:minmax(860px,1fr) 360px}







  .pcw-bottom{grid-template-columns:minmax(0,1fr) 352px 368px}







  .pcw-trend-page{grid-template-columns:minmax(0,1.5fr) 372px}







  .pcw-module-layout-coverage .pcw-module-grid,.pcw-module-layout-network .pcw-module-grid,.pcw-module-layout-ops .pcw-module-grid{grid-template-columns:minmax(520px,.98fr) minmax(0,1.02fr)}







}@media (min-width:1181px) and (max-width:1360px){







  .pcw-filter{gap:8px;padding:9px 10px}.pcw-filter-item{flex-basis:128px}.pcw-filter.section-market .pcw-filter-item,.pcw-filter.section-purchase .pcw-filter-item,.pcw-filter.section-plan .pcw-filter-item{flex-basis:146px}.pcw-filter.section-suppliers .pcw-filter-item,.pcw-filter.section-quotes .pcw-filter-item{flex-basis:142px}







  .pcw-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}







  .pcw-bottom{grid-template-columns:minmax(0,1fr) minmax(320px,348px)}







  .pcw-alerts{grid-column:1/-1}







  .pcw-module-layout-coverage .pcw-module-grid,.pcw-module-layout-network .pcw-module-grid,.pcw-module-layout-ops .pcw-module-grid{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}







  .pcw-module-layout-coverage .pcw-module-table table,.pcw-module-layout-network .pcw-module-table table,.pcw-module-layout-ops .pcw-module-table table{min-width:680px}







}















/* final-pass-11: module-page interactions, action hierarchy, and low-width desktop stability */







.pcw-filter button.focused:not(.active):not(.open){border-color:#dbe5f1;background:#fff;color:#1f3149;box-shadow:inset 0 0 0 1px rgba(37,99,235,.04)}







.pcw-filter button.active:not(.open){border-color:#bfdbfe;background:#f8fbff;color:#1d4ed8;font-weight:800}







.pcw-filter button.active:not(.open) small{color:#2563eb}







.pcw-filter button:focus-visible,.pcw-module-command-actions button:focus-visible,.pcw-module-card-actions button:focus-visible,.pcw-system:focus-visible{outline:0;box-shadow:0 0 0 3px #dbeafe}







.pcw-module-command{align-items:start;grid-template-columns:minmax(0,1fr) minmax(172px,auto);position:relative;overflow:hidden}







.pcw-module-command:before{content:"";position:absolute;left:0;top:18px;bottom:18px;width:4px;border-radius:999px;background:#2563eb}







.pcw-module-layout-workflow .pcw-module-command:before{background:#f97316}.pcw-module-layout-ledger .pcw-module-command:before{background:#64748b}.pcw-module-layout-insight .pcw-module-command:before{background:#0891b2}.pcw-module-layout-ops .pcw-module-command:before{background:#7c3aed}







.pcw-module-command-copy{padding-left:6px}.pcw-module-command-copy h2,.pcw-module-command-copy p{min-width:0;overflow:hidden;text-overflow:ellipsis}.pcw-module-command-actions{align-self:start;padding:3px;border:1px solid #e6edf6;border-radius:13px;background:#f8fbff}.pcw-module-command-actions button{height:32px;min-width:78px;border:0;background:transparent;color:#52647f}.pcw-module-command-actions button.primary{background:#2563eb;color:#fff;box-shadow:0 8px 16px rgba(37,99,235,.18)}.pcw-module-command-actions button.secondary:hover{background:#fff;color:#1d4ed8}







.pcw-module-card-actions{gap:8px}.pcw-module-card-actions span{background:#f8fafc}.pcw-module-card-actions button{height:28px;min-width:76px;border:0;background:#eef5ff;color:#1d4ed8;border-radius:999px}.pcw-module-card-actions button:hover{background:#dbeafe}







.pcw-module-command-brief p{grid-template-columns:68px minmax(0,1fr);background:rgba(255,255,255,.72)}.pcw-module-command-brief b,.pcw-module-command-brief span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}







.pcw-module-panel article strong,.pcw-module-panel article small,.pcw-module-flow p span,.pcw-module-activity article span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pcw-module-panel article{border-radius:10px}.pcw-module-panel article:hover,.pcw-module-flow p:hover,.pcw-module-activity article:hover{background:#f8fbff}@media (min-width:1181px) and (max-width:1360px){.pcw-module-command{grid-template-columns:1fr;grid-template-areas:"copy" "actions" "metrics" "brief"}.pcw-module-command-actions{justify-self:start}.pcw-module-command-brief{min-width:0}.pcw-module-layout-workflow .pcw-module-grid,.pcw-module-layout-ledger .pcw-module-grid,.pcw-module-layout-insight .pcw-module-grid{grid-template-columns:minmax(0,1fr)}.pcw-module-layout-workflow .pcw-module-grid>*,.pcw-module-layout-ledger .pcw-module-grid>*,.pcw-module-layout-insight .pcw-module-grid>*{grid-area:auto}.pcw-module-table table{min-width:720px}}@media (max-width:900px){.pcw-module-command{grid-template-columns:1fr;grid-template-areas:"copy" "actions" "metrics" "brief"}.pcw-module-command-metrics{grid-template-columns:1fr}.pcw-module-command-brief{min-width:0}.pcw-module-command-actions{justify-self:start}}















/* legacy-reference alignment: keep the earlier 食采云/Codex draft rhythm, avoid later shadcn-like chrome */


.pcw-card:hover{transform:none;border-color:#dfe7f1;box-shadow:0 8px 20px rgba(15,23,42,.026)}


.pcw-card-head{background:#fff}


.pcw-card-head h2:before{content:none!important;display:none!important}


.pcw-card-head span{padding:0;border-radius:0;background:transparent;color:#7a8aa3}


.pcw-top-actions{padding:0;border:0;background:transparent}

.pcw-filter{position:relative;top:auto;backdrop-filter:none}


.pcw-filter .pcw-export:after{content:none!important;display:none!important}





/* legacy-reference calibration: measured against .tmp/pc-price-workbench.png (sidebar ~219px, top bar ~64px) */

@media (min-width:1181px){

  .pcw{grid-template-columns:220px minmax(0,1fr)}

  .pcw-side{width:220px;padding:18px 14px 14px}

  .pcw-top{height:64px}

  .pcw-app{grid-template-rows:64px 1fr}

  .pcw-main{padding:20px 22px 24px;gap:16px}

}



.pcw-thumb {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23f0fdf4'/%3E%3Cpath d='M12 28c7-12 17-15 25-14-1 9-5 18-18 21 1-5 5-10 12-15-8 3-13 8-16 17' fill='%2316a34a'/%3E%3C/svg%3E");
  background: #f8fafc var(--pcw-thumb-image) center / cover no-repeat !important;
  cursor: zoom-in;
}
.pcw-thumb.has-image {
  background-position: center !important;
  background-size: cover !important;
}

.pcw-image-preview-shell {
  display: grid;
  place-items: center;
}

.pcw-image-preview {
  max-width: 100%;
  max-height: 76vh;
  border-radius: 12px;
}
.pcw-thumb.greens,
.pcw-thumb.leaf {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23f0fdf4'/%3E%3Cpath d='M12 28c7-12 17-15 25-14-1 9-5 18-18 21 1-5 5-10 12-15-8 3-13 8-16 17' fill='%2316a34a'/%3E%3C/svg%3E");
}
.pcw-thumb.cuke {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23ecfccb'/%3E%3Cpath d='M13 29c5-11 16-17 25-15-3 11-12 18-25 15Z' fill='%2322c55e'/%3E%3Cpath d='M18 26c4-4 9-7 15-9' stroke='%23dcfce7' stroke-width='3' stroke-linecap='round'/%3E%3C/svg%3E");
}
.pcw-thumb.fish {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23e0f2fe'/%3E%3Cpath d='M10 25c7-8 17-10 26 0-9 10-19 8-26 0Z' fill='%230ea5e9'/%3E%3Cpath d='M35 25l7-6v12l-7-6Z' fill='%230284c7'/%3E%3Ccircle cx='17' cy='23' r='2' fill='%23fff'/%3E%3C/svg%3E");
}
.pcw-thumb.egg,
.pcw-thumb.potato {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff7ed'/%3E%3Cellipse cx='19' cy='26' rx='8' ry='11' fill='%23f8fafc'/%3E%3Cellipse cx='30' cy='23' rx='8' ry='11' fill='%23fde68a'/%3E%3C/svg%3E");
}
.pcw-thumb.meat {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff1f2'/%3E%3Cpath d='M13 30c2-9 9-15 18-16 4 1 6 4 5 8-1 8-10 14-18 12-3-1-5-2-5-4Z' fill='%23fb7185'/%3E%3Ccircle cx='29' cy='22' r='5' fill='%23ffe4e6'/%3E%3C/svg%3E");
}
.pcw-thumb.fruit {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff7ed'/%3E%3Ccircle cx='22' cy='27' r='10' fill='%23f97316'/%3E%3Ccircle cx='31' cy='25' r='8' fill='%23facc15'/%3E%3Cpath d='M26 14c4-3 8-3 11 0-4 1-8 3-10 7' fill='%2322c55e'/%3E%3C/svg%3E");
}
.pcw-thumb.soy,
.pcw-thumb.grain {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fefce8'/%3E%3Cellipse cx='17' cy='25' rx='6' ry='9' fill='%23eab308'/%3E%3Cellipse cx='26' cy='23' rx='6' ry='9' fill='%23facc15'/%3E%3Cellipse cx='33' cy='28' rx='5' ry='8' fill='%23ca8a04'/%3E%3C/svg%3E");
}
.pcw-thumb.dry {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23fff7ed'/%3E%3Cpath d='M16 15c9 2 15 8 17 17-9-1-16-7-17-17Z' fill='%23dc2626'/%3E%3Cpath d='M25 13c4 5 6 11 5 18' stroke='%23b91c1c' stroke-width='3' stroke-linecap='round'/%3E%3C/svg%3E");
}
.pcw-thumb.frozen {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23eff6ff'/%3E%3Cpath d='M24 11v26M13 18l22 12M35 18 13 30' stroke='%232563eb' stroke-width='3' stroke-linecap='round'/%3E%3Ccircle cx='24' cy='24' r='4' fill='%2393c5fd'/%3E%3C/svg%3E");
}
.pcw-thumb.drink {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23ecfeff'/%3E%3Cpath d='M18 15h13l-2 22h-9l-2-22Z' fill='%2306b6d4'/%3E%3Cpath d='M19 20h11' stroke='%23cffafe' stroke-width='3'/%3E%3Cpath d='M31 14l4-4' stroke='%230e7490' stroke-width='3' stroke-linecap='round'/%3E%3C/svg%3E");
}
.pcw-thumb.kitchen {
  --pcw-thumb-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='14' fill='%23f1f5f9'/%3E%3Cpath d='M16 19h17l-2 18H18l-2-18Z' fill='%2364748b'/%3E%3Cpath d='M14 17h21M20 17c0-4 9-4 9 0' stroke='%23334155' stroke-width='3' stroke-linecap='round' fill='none'/%3E%3C/svg%3E");
}

.pcw-grid-summary-full {
  grid-template-columns: minmax(0, 1fr) 292px !important;
  align-items: start;
}

.pcw-summary-main {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.pcw-grid-summary-full .pcw-table-card {
  min-height: 0 !important;
}

.pcw-grid-summary-full .pcw-table-card td:nth-child(1),
.pcw-grid-summary-full .pcw-table-card td:nth-child(2),
.pcw-grid-summary-full .pcw-table-card td:nth-child(3) {
  white-space: normal !important;
  line-height: 1.35;
}

.pcw-grid-summary-full .pcw-product {
  align-items: flex-start;
  white-space: normal !important;
}

.pcw-grid-summary-full .pcw-product strong {
  overflow: visible !important;
  text-overflow: clip !important;
  white-space: normal !important;
}

.pcw-grid-summary-full .pcw-table-card tbody tr {
  box-shadow: inset 0 -1px #edf1f6;
}

.pcw-grid-summary-full .pcw-table-card tbody td {
  border-bottom: 0 !important;
  vertical-align: middle;
}

.pcw-grid-summary-full .pcw-product .pcw-thumb.has-image {
  background-color: #f8fafc !important;
}

.pcw-grid-summary-full .pcw-product-copy {
  display: grid !important;
  gap: 5px;
  min-width: 0;
}

.pcw-grid-summary-full .pcw-product-copy strong {
  display: -webkit-box !important;
  overflow: hidden !important;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  color: #10203d;
  font-size: 15px;
  line-height: 1.35;
  white-space: normal !important;
}

.pcw-grid-summary-full .pcw-product-copy small {
  display: block;
  overflow: hidden;
  color: #64748b;
  font-size: 11px;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* PC summary compact density: keep all core columns visible at 1366px. */
.pcw-grid-summary-full .pcw-table-card table {
  min-width: 920px !important;
}

.pcw-grid-summary-full .pcw-table-card th,
.pcw-grid-summary-full .pcw-table-card td {
  padding-inline: 8px !important;
}

.pcw-grid-summary-full .pcw-table-card th:nth-child(1),
.pcw-grid-summary-full .pcw-table-card td:nth-child(1) {
  width: 240px !important;
}

.pcw-grid-summary-full .pcw-table-card th:nth-child(2),
.pcw-grid-summary-full .pcw-table-card td:nth-child(2) {
  width: 92px !important;
}

.pcw-grid-summary-full .pcw-table-card th:nth-child(3),
.pcw-grid-summary-full .pcw-table-card td:nth-child(3) {
  width: 96px !important;
}

.pcw-grid-summary-full .pcw-table-card th:nth-child(4),
.pcw-grid-summary-full .pcw-table-card td:nth-child(4),
.pcw-grid-summary-full .pcw-table-card th:nth-child(5),
.pcw-grid-summary-full .pcw-table-card td:nth-child(5) {
  width: 92px !important;
}

.pcw-grid-summary-full .pcw-table-card th:nth-child(6),
.pcw-grid-summary-full .pcw-table-card td:nth-child(6) {
  width: 76px !important;
}

.pcw-grid-summary-full .pcw-table-card th:nth-child(7),
.pcw-grid-summary-full .pcw-table-card td:nth-child(7) {
  width: 86px !important;
}

.pcw-grid-summary-full .pcw-product {
  grid-template-columns: 56px minmax(0, 1fr);
  gap: 8px;
}

.pcw-grid-summary-full .pcw-product .pcw-thumb {
  width: 56px !important;
  height: 56px !important;
  border-radius: 10px !important;
  flex-basis: 56px;
}

.pcw-grid-summary-full .pcw-table-card tbody tr {
  min-height: 62px;
}

.pcw-grid-summary-full .pcw-table-card tbody td {
  padding-block: 4px !important;
}

/* PC clarity pass: keep only the actions that help the current purchase flow. */
.pcw-side-systems .pcw-side-sync,
.pcw-side-systems .pcw-system:not(.primary),
.pcw-top-actions .pcw-user {
  display: none !important;
}

.pcw-side-systems {
  border-top: 0 !important;
  padding-top: 0 !important;
}

.pcw-page-size {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  color: #64748b;
  font-size: 12px;
  font-style: normal;
  white-space: nowrap;
}

.pcw-page-size select {
  height: 30px;
  padding: 0 28px 0 10px;
  border: 1px solid #dbe6f4;
  border-radius: 8px;
  background: #ffffff;
  color: #10203d;
  font: inherit;
  font-weight: 700;
}



.pcw-module-count-badge {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border: 1px solid #dbe5f1;
  border-radius: 999px;
  background: #f8fbff;
  color: #52647f;
  font-size: 12px;
  font-weight: 700;
}

.pcw-module-count-badge.warning {
  border-color: #fed7aa;
  background: #fff7ed;
  color: #c2410c;
}

.pcw-empty-action-button {
  justify-self: center;
  min-height: 32px;
  padding: 0 12px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 800;
}

.pcw-kpis.is-market article,
.pcw-kpis.is-suppliers article,
.pcw-kpis.is-purchase article,
.pcw-kpis.is-quotes article,
.pcw-kpis.is-plan article,
.pcw-kpis.is-reports article,
.pcw-kpis.is-settings article {
  padding-left: 86px;
}

.pcw-supplier-admin-embedded {
  min-width: 0;
}

.pcw-supplier-admin-embedded :deep(.supplier-admin-panel) {
  border: 1px solid #dfe7f1;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .025);
}

.pcw-supplier-admin-embedded :deep(.supplier-admin-panel.embedded) {
  padding: 0;
}

.pcw-module-market .pcw-module-grid {
  grid-template-columns: minmax(0, 1fr) 300px !important;
  grid-template-areas:
    "table panel"
    "chart flow"
    "activity activity" !important;
}

.pcw-module-market .pcw-module-table {
  min-height: 360px !important;
}

.pcw-module-market .pcw-module-chart-panel svg {
  height: 258px;
}

.pcw-module-market .pcw-module-panel article,
.pcw-module-market .pcw-module-flow p {
  min-height: 44px !important;
  padding-top: 8px !important;
  padding-bottom: 8px !important;
}

.pcw-module-market .pcw-module-panel article small,
.pcw-module-market .pcw-module-flow span {
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.pcw-kpis.is-market article::before,
.pcw-kpis.is-suppliers article::before,
.pcw-kpis.is-purchase article::before,
.pcw-kpis.is-quotes article::before,
.pcw-kpis.is-plan article::before,
.pcw-kpis.is-reports article::before,
.pcw-kpis.is-settings article::before {
  left: 22px;
  top: 50%;
  bottom: auto;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  transform: translateY(-50%);
  background: #eff6ff;
  box-shadow: inset 0 0 0 1px #dbeafe;
}

.pcw-kpis.is-market article::after,
.pcw-kpis.is-suppliers article::after,
.pcw-kpis.is-purchase article::after,
.pcw-kpis.is-quotes article::after,
.pcw-kpis.is-plan article::after,
.pcw-kpis.is-reports article::after,
.pcw-kpis.is-settings article::after {
  content: "" !important;
  position: absolute;
  left: 37px;
  top: 50%;
  width: 22px;
  height: 22px;
  transform: translateY(-50%);
  background: var(--pcw-primary);
}

.pcw-kpis.is-plan article:nth-child(1)::after {
  width: 24px;
  height: 26px;
  border: 2px solid var(--pcw-primary);
  border-radius: 5px;
  background:
    linear-gradient(var(--pcw-primary), var(--pcw-primary)) 6px 7px / 12px 2px no-repeat,
    linear-gradient(var(--pcw-primary), var(--pcw-primary)) 6px 13px / 12px 2px no-repeat,
    linear-gradient(var(--pcw-primary), var(--pcw-primary)) 6px 19px / 8px 2px no-repeat;
}

.pcw-kpis.is-plan article:nth-child(2)::before {
  background: #ecfdf5;
  box-shadow: inset 0 0 0 1px #bbf7d0;
}

.pcw-kpis.is-plan article:nth-child(2)::after {
  background: var(--pcw-success);
  clip-path: polygon(11% 52%, 39% 80%, 90% 18%, 100% 30%, 41% 96%, 0 62%);
}

.pcw-kpis.is-plan article:nth-child(3)::before {
  background: #fff7ed;
  box-shadow: inset 0 0 0 1px #fed7aa;
}

.pcw-kpis.is-plan article:nth-child(3)::after {
  border: 2px solid var(--pcw-warn);
  border-radius: 50%;
  background:
    linear-gradient(var(--pcw-warn), var(--pcw-warn)) 10px 4px / 2px 8px no-repeat,
    linear-gradient(var(--pcw-warn), var(--pcw-warn)) 10px 10px / 7px 2px no-repeat;
}

.pcw-kpis.is-plan article:nth-child(4)::before,
.pcw-kpis.is-plan article:nth-child(5)::before {
  background: #fef2f2;
  box-shadow: inset 0 0 0 1px #fecaca;
}

.pcw-kpis.is-plan article:nth-child(4)::after {
  content: "¥" !important;
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  left: 34px;
  border: 2px solid var(--pcw-danger);
  border-radius: 50%;
  background: transparent;
  color: var(--pcw-danger);
  font-size: 19px;
  font-weight: 900;
  line-height: 1;
}

.pcw-kpis.is-plan article:nth-child(5)::after {
  background: var(--pcw-danger);
  clip-path: polygon(50% 0, 100% 90%, 0 90%);
}

.pcw-liancai-panel {
  margin: 0 18px 18px;
  padding: 16px 18px;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  border: 1px solid #d9e7ff;
}

.pcw-liancai-panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.pcw-liancai-panel-head strong {
  font-size: 15px;
  color: #10213f;
}

.pcw-liancai-panel-head small {
  font-size: 12px;
  color: #6b7a94;
}

.pcw-liancai-panel-group {
  display: grid;
  grid-template-columns: 68px 1fr;
  gap: 10px;
  align-items: start;
  margin-top: 10px;
}

.pcw-liancai-panel-group > span {
  padding-top: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #62738f;
}

.pcw-liancai-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pcw-liancai-chip {
  border: 1px solid #d7e3f7;
  background: #fff;
  color: #24364f;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  line-height: 1.2;
  cursor: pointer;
}

.pcw-liancai-chip.active {
  border-color: var(--pcw-primary);
  background: #eaf2ff;
  color: var(--pcw-primary);
  font-weight: 700;
}

.pcw-filter.section-summary {
  gap: 8px 10px;
}

.pcw-filter.section-summary .pcw-filter-item {
  flex: 1 1 142px;
  max-width: 168px;
}

.pcw-filter.section-summary .pcw-export {
  margin-left: auto;
}

.pcw-pages {
  min-height: 70px !important;
  padding: 16px 20px !important;
  gap: 10px !important;
  flex-wrap: wrap;
  justify-content: flex-start;
  align-items: center;
}

.pcw-pages button {
  width: auto !important;
  min-width: 38px !important;
  height: 38px !important;
  padding: 0 11px !important;
  border-radius: 10px !important;
  font-size: 14px !important;
  font-weight: 800 !important;
}

.pcw-pages button.active {
  min-width: 42px !important;
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.18);
}

.pcw-pages em,
.pcw-page-size {
  margin-left: 8px !important;
  white-space: nowrap;
}

.pcw-page-size select {
  min-height: 34px;
  min-width: 104px;
  border-radius: 10px;
  font-weight: 700;
}@media (max-width: 1320px){
  .pcw-alert-table-card table {
    min-width: 880px !important;
  }

  .pcw-alert-col-product { width: 20% !important; }
  .pcw-alert-col-type { width: 21% !important; }
  .pcw-alert-col-owner { width: 16% !important; }
  .pcw-alert-col-actions { width: 22% !important; }
}@media (min-width: 1321px) and (max-width: 1400px){
  .pcw-alert-table-card table {
    min-width: 960px !important;
  }
}

.pcw-alert-table-card {
  overflow-x: visible !important;
}

.pcw-alert-table-card table {
  width: 100% !important;
  min-width: 0 !important;
}

.pcw-alert-col-product { width: 21% !important; }
.pcw-alert-col-value { width: 10% !important; }
.pcw-alert-col-type { width: 23% !important; }
.pcw-alert-col-owner { width: 18% !important; }
.pcw-alert-col-state { width: 9% !important; }
.pcw-alert-col-actions { width: 19% !important; }


/* Price alert final visual guard: table fills the card and keeps actions visible on PC. */
.pcw-alert-table-card {
  width: 100%;
  min-width: 0;
  overflow: hidden !important;
}

.pcw-alert-table-card table {
  width: 100% !important;
  min-width: 0 !important;
  table-layout: fixed !important;
}

.pcw-alert-col-product { width: 20% !important; }
.pcw-alert-col-value { width: 10% !important; }
.pcw-alert-col-type { width: 22% !important; }
.pcw-alert-col-owner { width: 16% !important; }
.pcw-alert-col-state { width: 10% !important; }
.pcw-alert-col-actions { width: 22% !important; }

.pcw-alert-table-card th,
.pcw-alert-table-card td {
  min-width: 0;
  padding-inline: 10px !important;
}

.pcw-alert-table-card td:nth-child(6),
.pcw-alert-table-card th:nth-child(6) {
  padding-right: 14px !important;
}@media (min-width: 901px) and (max-width: 1320px){
  .pcw-alert-col-product { width: 18% !important; }
  .pcw-alert-col-type { width: 20% !important; }
  .pcw-alert-col-owner { width: 15% !important; }
  .pcw-alert-col-actions { width: 27% !important; }

  .pcw-alert-table-card th,
  .pcw-alert-table-card td {
    padding-inline: 8px !important;
  }
}

/* Desktop delivery pass: lift the PC shell closer to the mobile redesign language
   without changing structure or test-facing copy. */
@media (min-width: 901px) {
  .pcw {
    background:
      radial-gradient(circle at 18% 0, rgba(37, 99, 235, 0.09), transparent 28%),
      linear-gradient(180deg, #eef4ff 0%, #f8fafc 34%, #ffffff 100%);
  }

  .pcw-side {
    gap: 16px;
    padding: 20px 16px 18px;
    border-right-color: rgba(203, 213, 225, 0.9);
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
    box-shadow: 1px 0 0 rgba(15, 23, 42, 0.02);
  }

  .pcw-side-head {
    height: 48px;
    padding: 0 2px;
  }

  .pcw-logo {
    width: 38px;
    height: 38px;
    border-radius: 14px;
    background: linear-gradient(145deg, #1d4ed8, #2563eb 72%, #60a5fa);
    box-shadow: 0 12px 24px rgba(37, 99, 235, 0.2);
  }

  .pcw-brand-copy strong {
    font-size: 20px;
    line-height: 1.1;
    letter-spacing: -0.02em;
    color: #071226;
  }

  .pcw-brand-copy small {
    color: #64748b;
    font-size: 12px;
  }

  .pcw-nav-group {
    gap: 8px;
  }

  .pcw-nav-group > span {
    padding-left: 12px;
    color: #94a3b8;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.08em;
  }

  .pcw-nav-item {
    height: 44px;
    min-height: 44px;
    border-radius: 14px;
    color: #334155;
    font-weight: 600;
  }

  .pcw-nav-item:hover {
    background: #f8fbff;
    color: #2563eb;
  }

  .pcw-nav-item.active,
  .pcw-nav-item.active:hover {
    border-color: rgba(191, 219, 254, 0.9);
    background: linear-gradient(145deg, #eaf2ff, #f7faff);
    color: #1d4ed8;
    box-shadow: inset 3px 0 0 #2563eb;
  }

  .pcw-side-sync,
  .pcw-system {
    border-radius: 14px;
    border-color: rgba(226, 232, 240, 0.96);
    background: #ffffff;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
  }

  .pcw-system.primary {
    background: linear-gradient(145deg, #eff6ff, #ffffff);
    border-color: rgba(191, 219, 254, 0.9);
  }

  .pcw-system span,
  .pcw-side-sync span {
    color: #64748b;
  }

  .pcw-system strong,
  .pcw-side-sync strong {
    color: #0f172a;
  }

  .pcw-main {
    gap: 18px;
    padding: 24px;
  }

  .pcw-top {
    min-height: 60px;
    padding: 0 22px;
    border: 1px solid rgba(226, 232, 240, 0.96);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.04);
  }

  .pcw-top h1 {
    color: #071226;
    font-size: 18px;
    letter-spacing: -0.02em;
  }

  .pcw-filter {
    min-height: 68px;
    padding: 12px 14px;
    border-color: rgba(226, 232, 240, 0.96);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
  }

  .pcw-filter button {
    height: 40px;
    border-radius: 12px;
    border-color: #dbe5f1;
    box-shadow: none;
    font-weight: 600;
  }

  .pcw-kpis {
    gap: 14px;
    border: 0;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
    overflow: visible;
  }

  .pcw-kpis article {
    min-height: 102px;
    padding: 18px 18px 16px;
    border: 1px solid rgba(226, 232, 240, 0.96);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.98);
    box-shadow: 0 12px 24px rgba(15, 23, 42, 0.04);
  }

  .pcw-kpis strong {
    color: #0f172a;
    font-size: 30px;
  }

  .pcw-kpis span,
  .pcw-kpis small {
    color: #64748b;
  }

  .pcw-card {
    border-color: rgba(226, 232, 240, 0.96);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.98);
    box-shadow: 0 12px 24px rgba(15, 23, 42, 0.04);
  }

  .pcw-card-head {
    height: 50px;
    padding: 0 20px;
    border-bottom-color: rgba(237, 242, 247, 0.96);
    background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  }

  .pcw-card-head h2 {
    font-size: 16px;
    font-weight: 800;
    color: #10203d;
    letter-spacing: -0.01em;
  }

  .pcw-card-head span {
    color: #7a8aa3;
    font-weight: 700;
  }

  .pcw-table-card th,
  .pcw-alert-table-card th,
  .pcw-module-table th,
  th {
    background: #f8fbff;
    color: #52647f;
    font-weight: 800;
  }

  .pcw-table-card tbody tr:nth-child(even) td {
    background: #fcfdff;
  }

  .pcw-table-card tbody tr:hover td {
    background: #eef6ff;
  }

  .pcw-table-card .pcw-link {
    min-width: 66px;
    height: 28px;
    border-radius: 999px;
    background: #eef5ff;
    color: #1d4ed8;
    font-weight: 800;
  }
}

/* Final stabilization: override legacy collisions around location, filters and KPI density. */
.pcw-app {
  overflow: visible;
}

.pcw-top {
  overflow: visible;
  z-index: 90;
}

.pcw-location {
  position: relative;
  z-index: 95;
  min-width: 0;
  max-width: 320px;
  flex: 0 1 240px;
}

.pcw-location-button {
  width: 100%;
  min-width: 0;
}

.pcw-location-menu {
  z-index: 120;
  width: min(320px, calc(100vw - 32px));
  max-height: min(420px, calc(100vh - 120px));
  overflow: auto;
  overscroll-behavior: contain;
}

.pcw-filter {
  display: flex !important;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 10px 12px;
}

.pcw-filter-item {
  flex: 1 1 160px;
  min-width: 150px;
  max-width: 240px;
}

.pcw-filter.section-summary .pcw-filter-item {
  flex: 1 1 180px;
  min-width: 170px;
  max-width: none;
}

.pcw-filter .pcw-export {
  margin-left: auto;
  flex: 0 0 auto;
}

.pcw-filter-menu {
  z-index: 115;
  width: min(320px, max(180px, 100%));
  max-height: min(360px, calc(100vh - 180px));
  overflow: auto;
  overscroll-behavior: contain;
}

.pcw-kpis {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.pcw-kpis.is-summary {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.pcw-kpis.is-trend {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.pcw-module-command-empty-note {
  display: grid;
  gap: 4px;
  min-width: 0;
  margin-top: 2px;
  padding: 12px 14px;
  border: 1px dashed #fbbf24;
  border-radius: 12px;
  background: #fffaf0;
  color: #9a3412;
}

.pcw-module-command-empty-note strong {
  color: #9a3412;
  font-size: 13px;
}

.pcw-module-command-empty-note span {
  color: #b45309;
  font-size: 12px;
  line-height: 1.45;
}

.pcw-module-empty-compact {
  display: grid;
  gap: 12px;
  padding: 16px 18px;
}

.pcw-module-empty-compact-body {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.pcw-module-empty-compact-body article {
  display: grid;
  gap: 4px;
  min-height: 92px;
  padding: 12px 14px;
  border: 1px solid #dfe7f1;
  border-radius: 12px;
  background: #fff;
}

.pcw-module-empty-compact-body span {
  color: #607089;
  font-size: 12px;
  font-weight: 700;
}

.pcw-module-empty-compact-body strong {
  color: #10203d;
  font-size: 18px;
  line-height: 1.1;
}

.pcw-module-empty-compact-body small {
  color: #7a8aa3;
  font-size: 12px;
  line-height: 1.45;
}

.pcw-module-empty-compact-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.pcw-module-empty-compact-actions button {
  height: 34px;
  padding: 0 14px;
  border: 1px solid #dbe4ef;
  border-radius: 8px;
  background: #fff;
  color: #24344d;
  font-weight: 700;
}

.pcw-module-empty-compact-actions button.primary {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
}

.pcw-purchase-empty-path {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding: 16px;
}

.pcw-purchase-empty-path article {
  display: grid;
  gap: 8px;
  min-height: 168px;
  padding: 16px;
  border: 1px solid #dfe7f1;
  border-radius: 14px;
  background: linear-gradient(180deg, #fff, #f8fbff);
}

.pcw-purchase-empty-path span {
  width: max-content;
  padding: 3px 8px;
  border-radius: 999px;
  background: #fff7ed;
  color: #c2410c;
  font-size: 12px;
  font-weight: 900;
}

.pcw-purchase-empty-path strong {
  color: #10203d;
  font-size: 18px;
  line-height: 1.2;
}

.pcw-purchase-empty-path small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.pcw-purchase-empty-path button {
  height: 34px;
  margin-top: auto;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 800;
}

.pcw-purchase-empty-feed {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 0.82fr);
  gap: 12px;
  padding: 0 16px 16px;
}

.pcw-purchase-empty-feed section {
  display: grid;
  gap: 8px;
  align-content: start;
  padding: 14px;
  border: 1px solid #edf1f6;
  border-radius: 12px;
  background: #fbfdff;
}

.pcw-purchase-empty-feed strong {
  color: #10203d;
  font-size: 14px;
}

.pcw-purchase-empty-feed p,
.pcw-purchase-empty-feed span {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.pcw-purchase-empty-feed button {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  padding: 10px 0;
  border: 0;
  border-bottom: 1px solid #edf1f6;
  background: transparent;
  text-align: left;
}

.pcw-purchase-empty-feed button:last-child {
  border-bottom: 0;
}

.pcw-purchase-empty-feed b {
  color: #16a34a;
  font-size: 15px;
}



.pcw-summary-brief {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-width: 0;
  overflow: hidden;
}

.pcw-summary-brief-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(320px, 0.9fr);
  gap: 12px;
  min-width: 0;
  padding: 14px 16px 16px;
}

.pcw-summary-brief .pcw-summary-action-grid {
  padding: 0;
}

.pcw-summary-brief-timeline {
  display: grid;
  align-content: start;
  min-width: 0;
  padding-left: 12px;
  border-left: 1px solid #edf1f6;
}

.pcw-summary-brief-subhead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 26px;
  margin-bottom: 6px;
}

.pcw-summary-brief-subhead strong {
  color: #10203d;
  font-size: 13px;
}

.pcw-summary-brief-subhead button {
  border: 0;
  background: transparent;
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
}

.pcw-summary-brief-timeline p {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  min-width: 0;
  margin: 0;
  padding: 8px 0;
  border-bottom: 1px solid #edf1f6;
  color: #24344d;
  font-size: 12px;
}

.pcw-summary-brief-timeline p:last-child {
  border-bottom: 0;
}

.pcw-summary-brief-timeline p span {
  color: #7a899e;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pcw-summary-actions {
  grid-column: 1 / -1;
}

.pcw-summary-action-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  padding: 14px 16px 16px;
}

.pcw-summary-action-card {
  display: grid;
  gap: 6px;
  min-height: 116px;
  padding: 14px 15px;
  border: 1px solid #dfe7f1;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  text-align: left;
}

.pcw-summary-action-card span,
.pcw-summary-opportunity small {
  color: #607089;
  font-size: 12px;
  font-weight: 700;
}

.pcw-summary-action-card strong {
  color: #10203d;
  font-size: 18px;
  line-height: 1.2;
}

.pcw-summary-action-card small {
  color: #7a8aa3;
  font-size: 12px;
  line-height: 1.45;
}

.pcw-summary-opportunities {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  align-content: start;
  padding-bottom: 16px;
}

.pcw-summary-opportunities .pcw-card-head,
.pcw-summary-opportunities .pcw-panel-empty {
  grid-column: 1 / -1;
}

.pcw-summary-opportunity {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  width: auto;
  margin: 0;
  padding: 13px 14px;
  border: 1px solid #e6edf6;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  appearance: none;
  text-align: left;
}

.pcw-summary-opportunity:last-child {
  border-bottom: 1px solid #e6edf6;
}

.pcw-summary-opportunity strong {
  display: block;
  color: #10203d;
  font-size: 14px;
}

.pcw-summary-opportunity-metrics {
  display: grid;
  gap: 4px;
  justify-items: end;
}

.pcw-summary-opportunity-metrics b {
  color: #1d4ed8;
  font-size: 18px;
}

.pcw-summary-opportunity-metrics span {
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
}

.pcw-summary-side-fill {
  display: grid;
  align-content: start;
  gap: 10px;
  overflow: hidden;
}

.pcw-summary-side-hero {
  display: grid;
  gap: 6px;
  padding: 0 14px;
}

.pcw-summary-side-hero span {
  color: #607089;
  font-size: 12px;
  font-weight: 800;
}

.pcw-summary-side-hero strong {
  color: #10203d;
  font-size: 18px;
  line-height: 1.2;
}

.pcw-summary-side-hero p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.35;
}

.pcw-summary-side-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  padding: 0 14px;
}

.pcw-summary-side-metrics article {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 9px 10px;
  border: 1px solid #dfe7f1;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.pcw-summary-side-metrics span {
  color: #607089;
  font-size: 11px;
  font-weight: 800;
}

.pcw-summary-side-metrics strong {
  color: #10203d;
  font-size: 18px;
  line-height: 1;
}

.pcw-summary-side-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 12px 14px 0;
}

.pcw-summary-side-card {
  display: grid;
  gap: 6px;
  min-height: 102px;
  padding: 12px;
  border: 1px solid #dfe7f1;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  text-align: left;
}

.pcw-summary-side-card span,
.pcw-summary-side-block-head span {
  color: #607089;
  font-size: 12px;
  font-weight: 800;
}

.pcw-summary-side-card strong {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  color: #10203d;
  font-size: 14px;
  line-height: 1.25;
}

.pcw-summary-side-card small {
  color: #7a8aa3;
  font-size: 11px;
  line-height: 1.35;
}

.pcw-summary-side-block {
  display: grid;
  gap: 6px;
  margin: 0 14px 10px;
  padding-top: 10px;
  border-top: 1px solid #edf1f6;
}

.pcw-summary-side-block-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.pcw-summary-side-block-head button {
  border: 0;
  background: transparent;
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
}

.pcw-summary-side-block p,
.pcw-summary-side-opportunity {
  margin: 0;
}

.pcw-summary-side-block p {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  color: #34445d;
  font-size: 12px;
  line-height: 1.4;
}

.pcw-summary-side-opportunity {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  width: 100%;
  padding: 8px 0;
  border: 0;
  border-bottom: 1px solid #edf1f6;
  background: transparent;
  text-align: left;
}

.pcw-summary-side-opportunity:last-child {
  border-bottom: 0;
}

.pcw-summary-side-opportunity strong {
  display: block;
  overflow: hidden;
  color: #10203d;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pcw-summary-side-opportunity small {
  color: #607089;
  font-size: 11px;
  font-weight: 700;
}

.pcw-purchase-runbook {
  display: grid;
  gap: 14px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #edf1f6;
}

.pcw-purchase-runbook-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.pcw-purchase-runbook-grid article,
.pcw-purchase-runbook-panel {
  display: grid;
  gap: 8px;
  padding: 14px 15px;
  border: 1px solid #dfe7f1;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.pcw-purchase-runbook-grid article span {
  color: #f97316;
  font-size: 12px;
  font-weight: 800;
}

.pcw-purchase-runbook-grid article strong,
.pcw-purchase-runbook-panel strong {
  color: #10203d;
  font-size: 18px;
  line-height: 1.2;
}

.pcw-purchase-runbook-grid article small,
.pcw-purchase-runbook-list-item small,
.pcw-purchase-runbook-notes p {
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.pcw-purchase-runbook-grid article button,
.pcw-purchase-runbook-list-item,
.pcw-purchase-runbook-panel .pcw-card-head button {
  border-radius: 10px;
}

.pcw-purchase-runbook-grid article button {
  height: 34px;
  margin-top: 2px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 800;
}

.pcw-purchase-runbook-feed {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.9fr);
  gap: 12px;
}

.pcw-purchase-runbook-panel .pcw-card-head {
  height: auto;
  min-height: 0;
  padding: 0 0 10px;
  border-bottom: 1px solid #edf1f6;
}

.pcw-purchase-runbook-list {
  display: grid;
}

.pcw-purchase-runbook-list-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  padding: 11px 0;
  border-bottom: 1px solid #edf1f6;
  background: transparent;
  text-align: left;
}

.pcw-purchase-runbook-list-item:last-child {
  border-bottom: 0;
}

.pcw-purchase-runbook-list-item b {
  color: #16a34a;
  font-size: 16px;
}

.pcw-purchase-runbook-notes {
  display: grid;
  gap: 10px;
}

.pcw-purchase-runbook-notes p {
  margin: 0;
  padding-left: 14px;
  border-left: 3px solid #dbeafe;
}

.pcw-module-quotes.is-quotes-empty {
  gap: 12px;
}

.pcw-module-quotes.is-quotes-empty .pcw-module-command {
  min-height: 0;
  padding: 18px 20px;
}

.pcw-quotes-empty-compact {
  display: grid;
  align-content: start;
  overflow: hidden;
}

.pcw-quotes-empty-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding: 14px 16px;
}

.pcw-quotes-empty-grid article {
  display: grid;
  gap: 7px;
  min-height: 132px;
  padding: 14px 15px;
  border: 1px solid #dfe7f1;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.pcw-quotes-empty-grid span {
  color: #607089;
  font-size: 12px;
  font-weight: 800;
}

.pcw-quotes-empty-grid strong {
  color: #10203d;
  font-size: 24px;
  line-height: 1;
}

.pcw-quotes-empty-grid small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.pcw-quotes-empty-grid button {
  height: 32px;
  margin-top: auto;
  border: 1px solid #bfdbfe;
  border-radius: 9px;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 800;
}

.pcw-quotes-empty-feed {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.72fr);
  gap: 12px;
  padding: 0 16px 16px;
}

.pcw-quotes-empty-feed section {
  display: grid;
  gap: 8px;
  padding: 13px 14px;
  border: 1px solid #edf1f6;
  border-radius: 12px;
  background: #fbfdff;
}

.pcw-quotes-empty-feed strong {
  color: #10203d;
  font-size: 14px;
}

.pcw-quotes-empty-feed p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.pcw-settings-quick-panel {
  display: grid;
  overflow: hidden;
}

.pcw-settings-quick-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding: 14px 16px 16px;
}

.pcw-settings-quick-grid article {
  display: grid;
  gap: 6px;
  min-height: 104px;
  padding: 14px 15px;
  border: 1px solid #dfe7f1;
  border-radius: 12px;
  background: #fbfdff;
}

.pcw-settings-quick-grid article.green {
  border-color: #bbf7d0;
  background: #f7fffb;
}

.pcw-settings-quick-grid article.warn {
  border-color: #fed7aa;
  background: #fffaf5;
}

.pcw-settings-quick-grid span {
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}

.pcw-settings-quick-grid strong {
  color: #10203d;
  font-size: 24px;
  line-height: 1;
}

.pcw-settings-quick-grid small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.pcw-market-health-board,
.pcw-report-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
}

.pcw-market-health-list,
.pcw-report-composition {
  overflow: hidden;
}

.pcw-market-health-rows,
.pcw-report-bars {
  display: grid;
  gap: 10px;
  padding: 14px;
}

.pcw-market-health-rows article {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 116px 76px;
  gap: 12px;
  align-items: center;
  min-height: 58px;
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-left: 4px solid #22c55e;
  border-radius: 12px;
  background: #fff;
}

.pcw-market-health-rows article.warn {
  border-left-color: #f97316;
  background: #fffaf5;
}

.pcw-market-health-rows article.off {
  border-left-color: #94a3b8;
  background: #f8fafc;
}

.pcw-market-health-rows strong,
.pcw-market-health-rows small,
.pcw-market-health-rows span,
.pcw-market-health-rows b {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pcw-market-health-rows strong,
.pcw-report-bars strong {
  color: #10203d;
  font-size: 14px;
}

.pcw-market-health-rows small,
.pcw-market-health-rows span,
.pcw-report-bars small {
  color: #64748b;
  font-size: 12px;
}

.pcw-market-health-rows b {
  justify-self: end;
  color: #0f766e;
  font-size: 13px;
}

.pcw-market-health-side,
.pcw-report-side {
  display: grid;
  gap: 16px;
}

.pcw-market-health-pulse,
.pcw-report-export-card,
.pcw-market-failure-list,
.pcw-report-risk-card {
  overflow: hidden;
}

.pcw-market-health-pulse article,
.pcw-report-export-card article {
  display: grid;
  gap: 5px;
  margin: 0 14px;
  padding: 13px 0;
  border-bottom: 1px solid #edf1f6;
}

.pcw-market-health-pulse article:last-child,
.pcw-report-export-card article:last-child {
  border-bottom: 0;
}

.pcw-market-health-pulse span,
.pcw-report-export-card span,
.pcw-market-failure-list span,
.pcw-report-risk-card span {
  color: #64748b;
  font-size: 12px;
}

.pcw-market-health-pulse strong,
.pcw-report-export-card strong {
  color: #10203d;
  font-size: 26px;
  line-height: 1;
}

.pcw-market-failure-list p,
.pcw-report-risk-card p {
  display: grid;
  gap: 5px;
  margin: 0 14px;
  padding: 12px 0;
  border-bottom: 1px solid #edf1f6;
}

.pcw-market-failure-list p:last-child,
.pcw-report-risk-card p:last-child {
  border-bottom: 0;
}

.pcw-market-failure-list b,
.pcw-report-risk-card b {
  color: #10203d;
  font-size: 13px;
}

.pcw-report-bars article {
  display: grid;
  grid-template-columns: minmax(0, 190px) minmax(0, 1fr) 52px;
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: linear-gradient(135deg, #fff, #f8feff);
}

.pcw-report-bars span {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #e2e8f0;
}

.pcw-report-bars i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #0891b2, #22c55e);
}

.pcw-report-bars b {
  justify-self: end;
  color: #0891b2;
  font-size: 13px;
}

.pcw-report-risk-card p.warn b {
  color: #c2410c;
}

.pcw-report-risk-card p.green b {
  color: #15803d;
}

.pcw-filter {
  gap: 8px 10px;
  min-height: 0;
  padding: 8px 10px;
}

.pcw-filter button {
  height: 34px;
  padding-inline: 11px;
  font-size: 12px;
}

.pcw-kpis {
  gap: 10px;
}

.pcw-kpis article {
  min-height: 82px;
  padding: 12px 16px;
}

.pcw-kpis strong {
  font-size: 22px;
}

.pcw-kpis small {
  line-height: 1.3;
}

.pcw-trend-chart-card {
  min-height: 0;
}@media (max-width: 1100px){
  .pcw-grid-summary-full {
    grid-template-columns: 1fr !important;
  }

  .pcw-summary-action-grid,
  .pcw-summary-brief-grid,
  .pcw-summary-side-metrics,
  .pcw-summary-side-grid,
  .pcw-summary-opportunities,
  .pcw-purchase-runbook-grid,
  .pcw-purchase-empty-path {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .pcw-purchase-runbook-feed,
  .pcw-purchase-empty-feed {
    grid-template-columns: 1fr;
  }

  .pcw-summary-brief-timeline {
    padding-left: 0;
    padding-top: 12px;
    border-top: 1px solid #edf1f6;
    border-left: 0;
  }

  .pcw-quotes-empty-grid,
  .pcw-quotes-empty-feed,
  .pcw-settings-quick-grid,
  .pcw-market-health-board,
  .pcw-report-workbench,
  .pcw-report-bars article {
    grid-template-columns: 1fr;
  }

  .pcw-location {
    max-width: 100%;
    flex-basis: 100%;
  }

  .pcw-filter.section-summary .pcw-filter-item {
    flex: 1 1 calc(50% - 10px);
    min-width: 0;
  }
}@media (max-width: 720px){
  .pcw-bottom,
  .pcw-summary-action-grid,
  .pcw-summary-brief-grid,
  .pcw-summary-side-metrics,
  .pcw-summary-side-grid,
  .pcw-summary-opportunities,
  .pcw-purchase-runbook-grid,
  .pcw-purchase-empty-path,
  .pcw-trend-point-rail {
    grid-template-columns: 1fr;
  }

  .pcw-location-menu,
  .pcw-filter-menu {
    width: min(320px, calc(100vw - 24px));
  }

  .pcw-filter.section-summary .pcw-filter-item,
  .pcw-filter .pcw-export {
    flex: 1 1 100%;
    min-width: 0;
    max-width: none;
    width: 100%;
  }
}

.pcw-quotes {
  display: grid;
  align-self: start;
  min-height: 0 !important;
  overflow: hidden;
  background: linear-gradient(180deg, #fff 0%, #fbfdff 100%);
}

.pcw-quotes .pcw-card-head {
  background: #fff;
}

.pcw-build-badge {
  display: inline-flex;
  align-items: center;
  margin-left: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #e8f1ff;
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  vertical-align: middle;
}



</style>
