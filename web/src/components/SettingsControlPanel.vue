<template>
  <section class="pcw-settings-inline-admin">
    <article>
      <span>采集状态</span>
      <strong>{{ crawlStatus?.is_running ? '运行中' : '空闲' }}</strong>
      <small>{{ settingsCrawlProgressLabel }}</small>
    </article>
    <article>
      <span>最近结果</span>
      <strong>{{ settingsCrawlResultLabel }}</strong>
      <small>最近完成：{{ settingsLastFinishedLabel }}</small>
    </article>
    <article>
      <span>自动同步</span>
      <strong>{{ settingsScheduleEnabled ? '已开启' : '已关闭' }}</strong>
      <small>{{ settingsScheduleDetail }}</small>
    </article>
    <nav class="pcw-settings-panel-tabs" aria-label="系统设置分区">
      <button
        v-for="item in settingsPanelTabs"
        :key="item.key"
        type="button"
        :class="{ active: settingsActivePanel === item.key }"
        @click="settingsActivePanel = item.key"
      >
        <strong>{{ item.label }}</strong>
        <small>{{ item.detail }}</small>
      </button>
    </nav>
    <form v-if="settingsActivePanel === 'schedule'" class="pcw-settings-form" @submit.prevent="saveSettingsSchedule">
      <label>
        <span>自动同步</span>
        <select v-model="settingsScheduleDraftEnabled" :disabled="settingsManagementLocked" @change="markSettingsScheduleDraftChanged">
          <option :value="true">开启</option>
          <option :value="false">关闭</option>
        </select>
      </label>
      <label>
        <span>同步方式</span>
        <select v-model="settingsScheduleDraftMode" :disabled="settingsManagementLocked" @change="markSettingsScheduleDraftChanged">
          <option value="daily_time">每天固定时间</option>
          <option value="interval">按间隔循环</option>
        </select>
      </label>
      <label v-if="settingsScheduleDraftMode === 'daily_time'">
        <span>同步时间</span>
        <input v-model="settingsScheduleDraftDailyRunTime" type="time" :disabled="settingsManagementLocked" @change="markSettingsScheduleDraftChanged" />
      </label>
      <label v-else>
        <span>同步频率</span>
        <select v-model.number="settingsScheduleDraftInterval" :disabled="settingsManagementLocked" @change="markSettingsScheduleDraftChanged">
          <option :value="3600">每 1 小时</option>
          <option :value="21600">每 6 小时</option>
          <option :value="43200">每 12 小时</option>
          <option :value="86400">每天一次</option>
          <option :value="604800">每周一次</option>
        </select>
      </label>
      <label>
        <span>采价方式</span>
        <select v-model="settingsFetchModeDraft" :disabled="settingsManagementLocked" @change="markSettingsScheduleDraftChanged">
          <option value="requests">快速采价</option>
          <option value="playwright">浏览器采价</option>
        </select>
      </label>
      <div class="pcw-settings-inline-actions">
        <button type="submit" :disabled="settingsManagementLocked || !settingsScheduleDirty">保存设置</button>
        <button type="button" class="secondary" :disabled="crawlStatus?.is_running" @click="emit('run-crawl')">
          {{ crawlStatus?.is_running ? '同步中' : '立即同步' }}
        </button>
        <button type="button" class="secondary" @click="emit('refresh')">刷新状态</button>
      </div>
    </form>

    <p v-if="settingsManagementLocked" class="pcw-settings-auth-hint">系统设置需要管理员登录后才能修改，当前账号只有查看权限。</p>

    <section v-if="settingsActivePanel === 'source' && settingsChangeLogs?.length" class="pcw-settings-log-panel">
      <div class="pcw-settings-log-head">
        <strong>最近一次改动记录</strong>
        <span>{{ settingsChangeLogs.length }} 条</span>
      </div>
      <div class="pcw-settings-log-list">
        <article v-for="item in settingsChangeLogs.slice(0, 5)" :key="item.id">
          <strong>{{ item.target_name }}</strong>
          <small>{{ item.actor_name }} · {{ item.changed_at }}</small>
          <span>{{ item.summary }}</span>
        </article>
      </div>
    </section>

    <form v-if="settingsActivePanel === 'source'" class="pcw-settings-source-form" @submit.prevent="saveSettingsSourceConfig">
      <label class="full">
        <span>数据来源</span>
        <select v-model="settingsSelectedSourceUrl" :disabled="settingsManagementLocked" @change="settingsSourceDraftTouched = false; syncSelectedSourceDraft()">
          <option v-for="item in settingsSourceOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
      </label>
      <label>
        <span>启用状态</span>
        <select v-model="settingsSourceDraftEnabled" :disabled="settingsManagementLocked" @change="markSettingsSourceDraftChanged">
          <option :value="true">启用</option>
          <option :value="false">停用</option>
        </select>
      </label>
      <label>
        <span>展示名称</span>
        <input v-model="settingsSourceDraftName" :disabled="settingsManagementLocked" type="text" @input="markSettingsSourceDraftChanged" />
      </label>
      <label>
        <span>市场范围</span>
        <input v-model="settingsSourceDraftScope" :disabled="settingsManagementLocked" type="text" @input="markSettingsSourceDraftChanged" />
      </label>
      <label>
        <span>分类</span>
        <input v-model="settingsSourceDraftCategory" :disabled="settingsManagementLocked" type="text" @input="markSettingsSourceDraftChanged" />
      </label>
      <label class="full">
        <span>备注</span>
        <textarea v-model="settingsSourceDraftNotes" :disabled="settingsManagementLocked" rows="3" @input="markSettingsSourceDraftChanged"></textarea>
      </label>
      <div class="pcw-settings-inline-actions">
        <button type="submit" :disabled="settingsManagementLocked || !settingsSourceDirty">保存来源配置</button>
        <button type="button" class="secondary" :disabled="settingsManagementLocked || !settingsSelectedSource" @click="settingsSourceDraftTouched = false; syncSelectedSourceDraft()">重置</button>
      </div>
    </form>

    <form v-if="settingsActivePanel === 'strategy'" class="pcw-settings-source-form" @submit.prevent="saveSettingsSourceStrategy">
      <div class="pcw-settings-run-feedback full">
        <strong>来源试跑反馈</strong>
        <span>{{ settingsSelectedSourceRunSummary }}</span>
      </div>
      <label>
        <span>采价方式</span>
        <select v-model="settingsStrategyDraftFetchMode" :disabled="settingsManagementLocked" @change="markSettingsStrategyDraftChanged">
          <option value="requests">快速采价</option>
          <option value="playwright">浏览器采价</option>
          <option value="api">接口采价</option>
        </select>
      </label>
      <label>
        <span>采价方案</span>
        <input v-model="settingsStrategyDraftName" :disabled="settingsManagementLocked" type="text" @input="markSettingsStrategyDraftChanged" />
      </label>
      <label>
        <span>超时秒数</span>
        <input v-model.number="settingsStrategyDraftTimeout" :disabled="settingsManagementLocked" type="number" min="1" max="300" @input="markSettingsStrategyDraftChanged" />
      </label>
      <label>
        <span>重试次数</span>
        <input v-model.number="settingsStrategyDraftRetry" :disabled="settingsManagementLocked" type="number" min="0" max="20" @input="markSettingsStrategyDraftChanged" />
      </label>
      <label>
        <span>采价间隔(秒)</span>
        <input v-model.number="settingsStrategyDraftDelay" :disabled="settingsManagementLocked" type="number" min="0" max="60" step="0.1" @input="markSettingsStrategyDraftChanged" />
      </label>
      <label>
        <span>接口方案</span>
        <input v-model="settingsStrategyDraftApiStrategy" :disabled="settingsManagementLocked" type="text" @input="markSettingsStrategyDraftChanged" />
      </label>
      <label>
        <span>失败返回码</span>
        <input v-model="settingsStrategyDraftBlockedCodes" :disabled="settingsManagementLocked" type="text" @input="markSettingsStrategyDraftChanged" />
      </label>
      <label>
        <span>网站安全校验</span>
        <select v-model="settingsStrategyDraftVerifySsl" :disabled="settingsManagementLocked" @change="markSettingsStrategyDraftChanged">
          <option :value="true">开启</option>
          <option :value="false">关闭</option>
        </select>
      </label>
      <div class="pcw-settings-inline-actions">
        <button type="button" class="secondary" :disabled="settingsManagementLocked || !settingsSelectedSource || crawlStatus?.is_running" @click="runSelectedSourceCrawl">试跑当前来源</button>
        <button type="submit" :disabled="settingsManagementLocked || !settingsSelectedSource">保存采价方案</button>
      </div>
    </form>

    <form v-if="settingsActivePanel === 'alerts'" class="pcw-settings-source-form" @submit.prevent="saveGlobalAlertRules">
      <div class="pcw-settings-alert-rule-list">
        <div v-for="(item, index) in settingsGlobalAlertDraftRows" :key="`alert-rule-${index}`" class="pcw-settings-alert-rule-row">
          <label>
            <span>预警目标</span>
            <input v-model="item.target_name" :disabled="settingsManagementLocked" type="text" />
          </label>
          <label>
            <span>提醒价格</span>
            <input v-model.number="item.threshold" :disabled="settingsManagementLocked" type="number" min="0" step="0.01" />
          </label>
          <label>
            <span>分组名</span>
            <input v-model="item.group_name" :disabled="settingsManagementLocked" type="text" />
          </label>
          <label class="full">
            <span>规则备注</span>
            <textarea v-model="item.note" :disabled="settingsManagementLocked" rows="3"></textarea>
          </label>
          <div class="pcw-settings-inline-actions">
            <button type="button" class="secondary" :disabled="settingsManagementLocked" @click="removeGlobalAlertRuleRow(index)">删除规则</button>
          </div>
        </div>
      </div>
      <div class="pcw-settings-inline-actions">
        <button type="button" class="secondary" :disabled="settingsManagementLocked" @click="addGlobalAlertRuleRow">新增规则</button>
        <button type="submit" :disabled="settingsManagementLocked || !settingsGlobalAlertDraftRows.some((item) => String(item.target_name || '').trim())">保存全局预警规则</button>
      </div>
    </form>

    <el-dialog v-model="settingsConfirmVisible" :title="settingsConfirmTitle || '确认保存'" width="min(92vw, 720px)">
      <div class="pcw-settings-confirm-shell">
        <p class="pcw-settings-confirm-copy">{{ settingsConfirmDescription }}</p>
        <ul class="pcw-settings-confirm-list">
          <li v-for="item in settingsConfirmLines" :key="item">{{ item }}</li>
        </ul>
      </div>
      <template #footer>
        <div class="pcw-settings-confirm-actions">
          <button type="button" class="secondary" @click="settingsConfirmVisible = false">取消</button>
          <button type="button" @click="confirmPendingSettingsChange">确认保存</button>
        </div>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { AuthUserRole, CrawlStatusItem, GlobalAlertRuleItem, SettingsChangeLogItem, SourceCoverageItem } from '../types'

const props = defineProps<{
  crawlStatus?: CrawlStatusItem | null
  sourceCoverageRows?: SourceCoverageItem[]
  settingsChangeLogs?: SettingsChangeLogItem[]
  globalAlertRules?: GlobalAlertRuleItem[]
  authRole?: AuthUserRole | null
}>()

const emit = defineEmits<{
  (event: 'refresh'): void
  (event: 'run-crawl'): void
  (event: 'run-source-crawl', value: { source_url?: string; source_name?: string }): void
  (event: 'update-crawl-schedule', value: {
    enabled: boolean
    mode?: 'interval' | 'daily_time'
    daily_run_time?: string | null
    interval_seconds: number
    fetch_mode?: 'requests' | 'playwright'
  }): void
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

type SettingsPanelKey = 'schedule' | 'source' | 'strategy' | 'alerts'

const settingsActivePanel = ref<SettingsPanelKey>('schedule')
const settingsScheduleDraftEnabled = ref(false)
const settingsScheduleDraftMode = ref<'interval' | 'daily_time'>('daily_time')
const settingsScheduleDraftDailyRunTime = ref('03:30')
const settingsScheduleDraftInterval = ref(86400)
const settingsFetchModeDraft = ref<'requests' | 'playwright'>('requests')
const settingsScheduleDraftTouched = ref(false)
const settingsSelectedSourceUrl = ref('')
const settingsSourceDraftEnabled = ref(true)
const settingsSourceDraftName = ref('')
const settingsSourceDraftScope = ref('')
const settingsSourceDraftCategory = ref('')
const settingsSourceDraftNotes = ref('')
const settingsSourceDraftTouched = ref(false)
const settingsStrategyDraftFetchMode = ref<'requests' | 'playwright' | 'api'>('requests')
const settingsStrategyDraftName = ref('')
const settingsStrategyDraftTimeout = ref(15)
const settingsStrategyDraftRetry = ref(2)
const settingsStrategyDraftDelay = ref(1)
const settingsStrategyDraftBlockedCodes = ref('403,429')
const settingsStrategyDraftVerifySsl = ref(true)
const settingsStrategyDraftApiStrategy = ref('off')
const settingsStrategyDraftTouched = ref(false)
const settingsGlobalAlertDraftRows = ref<GlobalAlertRuleItem[]>([])
const settingsConfirmVisible = ref(false)
const settingsConfirmTitle = ref('')
const settingsConfirmDescription = ref('')
const settingsConfirmLines = ref<string[]>([])
const pendingSettingsChange = ref<null | (() => void)>(null)

const settingsManagementLocked = computed(() => props.authRole !== 'admin')
const settingsLatestCaptureAt = computed(() =>
  (props.sourceCoverageRows || [])
    .map((item) => item.latest_capture)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1),
)
const settingsScheduleEnabled = computed(() => Boolean(props.crawlStatus?.schedule_enabled))
const fetchModeLabels: Record<'requests' | 'playwright' | 'api', string> = {
  requests: '快速采价',
  playwright: '浏览器采价',
  api: '接口采价',
}
const settingsScheduleDirty = computed(() =>
  settingsScheduleDraftEnabled.value !== Boolean(props.crawlStatus?.schedule_enabled)
  || settingsScheduleDraftMode.value !== (props.crawlStatus?.schedule_mode === 'interval' ? 'interval' : 'daily_time')
  || settingsScheduleDraftDailyRunTime.value !== String(props.crawlStatus?.schedule_daily_run_time || '03:30')
  || settingsScheduleDraftInterval.value !== Number(props.crawlStatus?.schedule_interval_seconds || 86400)
  || settingsFetchModeDraft.value !== (props.crawlStatus?.schedule_fetch_mode === 'playwright' ? 'playwright' : 'requests'),
)
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
  const modeLabel = props.crawlStatus?.schedule_mode === 'interval'
    ? `按间隔 ${formatIntervalLabel(Number(props.crawlStatus?.schedule_interval_seconds || 86400))}`
    : `每天 ${props.crawlStatus?.schedule_daily_run_time || '03:30'}`
  return props.crawlStatus?.next_run_at ? `${modeLabel} · 下次 ${formatShortDateTime(props.crawlStatus.next_run_at)}` : modeLabel
})
const settingsPanelTabs = computed<Array<{ key: SettingsPanelKey; label: string; detail: string }>>(() => [
  { key: 'schedule', label: '同步调度', detail: settingsScheduleEnabled.value ? '自动任务已开启' : '手动同步优先' },
  { key: 'source', label: '来源配置', detail: `${props.sourceCoverageRows?.length || 0} 个来源` },
  { key: 'strategy', label: '采价方案', detail: settingsSelectedSource.value?.source_name || '选择来源后配置' },
  { key: 'alerts', label: '预警规则', detail: `${settingsGlobalAlertDraftRows.value.length} 条规则` },
])
const settingsSourceOptions = computed(() => (props.sourceCoverageRows || []).map((item) => ({
  value: String(item.source_url || ''),
  label: item.configured_name || item.source_name || item.source_url || '未命名来源',
})).filter((item) => item.value))
const settingsSelectedSource = computed(() =>
  (props.sourceCoverageRows || []).find((item) => String(item.source_url || '') === settingsSelectedSourceUrl.value) || null,
)
const settingsSelectedSourceIsRunning = computed(() => {
  if (!props.crawlStatus?.is_running || !settingsSelectedSource.value) return false
  const targetUrl = String(props.crawlStatus.target_source_url || '').trim()
  const selectedUrl = String(settingsSelectedSource.value.source_url || '').trim()
  if (targetUrl && selectedUrl) return targetUrl === selectedUrl
  const targetName = String(props.crawlStatus.target_source_name || props.crawlStatus.current_source_name || '').trim()
  const selectedName = String(settingsSelectedSource.value.source_name || '').trim()
  return Boolean(targetName && selectedName && targetName === selectedName)
})
const settingsSelectedSourceRunSummary = computed(() => {
  const source = settingsSelectedSource.value
  if (!source) return '请选择来源后再试跑'
  if (settingsSelectedSourceIsRunning.value) {
    return props.crawlStatus?.current_source_detail || '当前来源试跑中'
  }
  const targetUrl = String(props.crawlStatus?.target_source_url || '').trim()
  const targetName = String(props.crawlStatus?.target_source_name || '').trim()
  const selectedUrl = String(source.source_url || '').trim()
  const selectedName = String(source.source_name || '').trim()
  const matchesSelected = (targetUrl && selectedUrl && targetUrl === selectedUrl)
    || (targetName && selectedName && targetName === selectedName)
  if (!matchesSelected) {
    return source.last_failure || source.status || '尚未试跑当前来源'
  }
  const success = Number(props.crawlStatus?.last_success_count || 0)
  const failed = Number(props.crawlStatus?.last_failed_count || 0)
  if (props.crawlStatus?.last_error) return `最近试跑失败：${props.crawlStatus.last_error}`
  return `最近试跑结果：${success} 成功 / ${failed} 异常`
})
const settingsStrategyDirty = computed(() => {
  const source = settingsSelectedSource.value
  if (!source?.source_name) return false
  return (
    settingsStrategyDraftFetchMode.value !== ((source.preferred_fetch_mode as 'requests' | 'playwright' | 'api' | null) || 'requests')
    || settingsStrategyDraftName.value !== String(source.strategy || '')
    || settingsStrategyDraftTimeout.value !== Number(source.timeout_seconds || 15)
    || settingsStrategyDraftRetry.value !== Number(source.retry_count ?? 2)
    || settingsStrategyDraftDelay.value !== Number(source.request_delay_seconds ?? 1)
    || settingsStrategyDraftBlockedCodes.value !== String((source.blocked_status_codes || [403, 429]).join(','))
    || settingsStrategyDraftVerifySsl.value !== (source.verify_ssl !== false)
    || settingsStrategyDraftApiStrategy.value !== String(source.api_strategy || 'off')
  )
})
const settingsSourceDirty = computed(() => {
  const source = settingsSelectedSource.value
  if (!source) return false
  return (
    settingsSourceDraftEnabled.value !== (source.enabled !== false)
    || settingsSourceDraftName.value !== String(source.configured_name || '')
    || settingsSourceDraftScope.value !== String(source.market_scope || '')
    || settingsSourceDraftCategory.value !== String(source.market_category || '')
    || settingsSourceDraftNotes.value !== String(source.notes || '')
  )
})

watch(
  () => [
    props.crawlStatus?.schedule_enabled,
    props.crawlStatus?.schedule_mode,
    props.crawlStatus?.schedule_daily_run_time,
    props.crawlStatus?.schedule_interval_seconds,
    props.crawlStatus?.schedule_fetch_mode,
  ] as const,
  () => {
    if (!settingsScheduleDraftTouched.value) syncSettingsScheduleDraft()
  },
  { immediate: true },
)
watch(
  () => settingsSourceOptions.value.map((item) => item.value).join('|'),
  () => {
    if (!settingsSelectedSourceUrl.value && settingsSourceOptions.value.length) {
      settingsSelectedSourceUrl.value = settingsSourceOptions.value[0].value
    }
    if (!settingsSourceOptions.value.some((item) => item.value === settingsSelectedSourceUrl.value)) {
      settingsSelectedSourceUrl.value = settingsSourceOptions.value[0]?.value || ''
    }
  },
  { immediate: true },
)
watch(
  () => [settingsSelectedSourceUrl.value, props.sourceCoverageRows] as const,
  () => {
    if (!settingsSourceDraftTouched.value) syncSelectedSourceDraft()
  },
  { immediate: true },
)
watch(
  () => props.globalAlertRules,
  () => {
    syncGlobalAlertDraftRows()
  },
  { immediate: true },
)

function formatShortDateTime(value?: string | null) {
  const text = String(value || '').trim()
  if (!text) return '暂无'
  const date = new Date(text)
  if (Number.isNaN(date.getTime())) return text
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  const hour = `${date.getHours()}`.padStart(2, '0')
  const minute = `${date.getMinutes()}`.padStart(2, '0')
  return `${month}/${day} ${hour}:${minute}`
}

function formatIntervalLabel(seconds: number) {
  if (seconds % 86400 === 0) return `${seconds / 86400} 天`
  if (seconds % 3600 === 0) return `${seconds / 3600} 小时`
  return `${seconds} 秒`
}

function formatFetchModeLabel(value?: 'requests' | 'playwright' | 'api' | null) {
  return value ? fetchModeLabels[value] : '未选择'
}

function syncSettingsScheduleDraft() {
  settingsScheduleDraftEnabled.value = Boolean(props.crawlStatus?.schedule_enabled)
  settingsScheduleDraftMode.value = props.crawlStatus?.schedule_mode === 'interval' ? 'interval' : 'daily_time'
  settingsScheduleDraftDailyRunTime.value = String(props.crawlStatus?.schedule_daily_run_time || '03:30')
  settingsScheduleDraftInterval.value = Number(props.crawlStatus?.schedule_interval_seconds || 86400)
  settingsFetchModeDraft.value = props.crawlStatus?.schedule_fetch_mode === 'playwright' ? 'playwright' : 'requests'
}

function syncSelectedSourceDraft() {
  const source = settingsSelectedSource.value
  if (!source) {
    settingsSourceDraftEnabled.value = true
    settingsSourceDraftName.value = ''
    settingsSourceDraftScope.value = ''
    settingsSourceDraftCategory.value = ''
    settingsSourceDraftNotes.value = ''
    settingsStrategyDraftFetchMode.value = 'requests'
    settingsStrategyDraftName.value = ''
    settingsStrategyDraftTimeout.value = 15
    settingsStrategyDraftRetry.value = 2
    settingsStrategyDraftDelay.value = 1
    settingsStrategyDraftBlockedCodes.value = '403,429'
    settingsStrategyDraftVerifySsl.value = true
    settingsStrategyDraftApiStrategy.value = 'off'
    return
  }
  settingsSourceDraftEnabled.value = source.enabled !== false
  settingsSourceDraftName.value = String(source.configured_name || '')
  settingsSourceDraftScope.value = String(source.market_scope || '')
  settingsSourceDraftCategory.value = String(source.market_category || '')
  settingsSourceDraftNotes.value = String(source.notes || '')
  settingsStrategyDraftFetchMode.value = (source.preferred_fetch_mode as 'requests' | 'playwright' | 'api' | null) || 'requests'
  settingsStrategyDraftName.value = String(source.strategy || '')
  settingsStrategyDraftTimeout.value = Number(source.timeout_seconds || 15)
  settingsStrategyDraftRetry.value = Number(source.retry_count ?? 2)
  settingsStrategyDraftDelay.value = Number(source.request_delay_seconds ?? 1)
  settingsStrategyDraftBlockedCodes.value = String((source.blocked_status_codes || [403, 429]).join(','))
  settingsStrategyDraftVerifySsl.value = source.verify_ssl !== false
  settingsStrategyDraftApiStrategy.value = String(source.api_strategy || 'off')
}

function syncGlobalAlertDraftRows() {
  const incomingRows = (props.globalAlertRules || []).map((item) => ({
    target_name: String(item.target_name || ''),
    threshold: Number(item.threshold || 0),
    note: String(item.note || ''),
    group_name: String(item.group_name || ''),
  }))
  settingsGlobalAlertDraftRows.value = incomingRows.length
    ? incomingRows
    : [{ target_name: '', threshold: 0, note: '', group_name: '' }]
}

function markSettingsScheduleDraftChanged() {
  settingsScheduleDraftTouched.value = true
}

function markSettingsSourceDraftChanged() {
  settingsSourceDraftTouched.value = true
}

function markSettingsStrategyDraftChanged() {
  settingsStrategyDraftTouched.value = true
}

function openSettingsConfirm(title: string, description: string, lines: string[], onConfirm: () => void) {
  settingsConfirmTitle.value = title
  settingsConfirmDescription.value = description
  settingsConfirmLines.value = lines.length ? lines : ['当前没有检测到变化。']
  pendingSettingsChange.value = onConfirm
  settingsConfirmVisible.value = true
}

function confirmPendingSettingsChange() {
  const action = pendingSettingsChange.value
  settingsConfirmVisible.value = false
  pendingSettingsChange.value = null
  if (action) action()
}

function saveSettingsSchedule() {
  const modeLabel = settingsScheduleDraftMode.value === 'daily_time' ? '每天固定时间' : '按间隔循环'
  const nextLines = [
    `自动同步：${settingsScheduleDraftEnabled.value ? '开启' : '关闭'}`,
    `同步方式：${modeLabel}`,
    settingsScheduleDraftMode.value === 'daily_time'
      ? `同步时间：${settingsScheduleDraftDailyRunTime.value || '03:30'}`
      : `同步频率：${settingsScheduleDraftInterval.value} 秒`,
    `采价方式：${formatFetchModeLabel(settingsFetchModeDraft.value)}`,
  ]
  openSettingsConfirm('保存系统同步设置', '以下改动会立即写入当前系统设置。', nextLines, () => {
    settingsScheduleDraftTouched.value = false
    emit('update-crawl-schedule', {
      enabled: settingsScheduleDraftEnabled.value,
      mode: settingsScheduleDraftMode.value,
      daily_run_time: settingsScheduleDraftMode.value === 'daily_time' ? settingsScheduleDraftDailyRunTime.value : null,
      interval_seconds: settingsScheduleDraftInterval.value,
      fetch_mode: settingsFetchModeDraft.value,
    })
  })
}

function saveSettingsSourceConfig() {
  if (!settingsSelectedSource.value?.source_url) return
  const nextLines = [
    `来源：${settingsSelectedSource.value.configured_name || settingsSelectedSource.value.source_name || settingsSelectedSource.value.source_url}`,
    `启用状态：${settingsSourceDraftEnabled.value ? '启用' : '停用'}`,
    `展示名称：${settingsSourceDraftName.value || '未填写'}`,
    `市场范围：${settingsSourceDraftScope.value || '未填写'}`,
    `分类：${settingsSourceDraftCategory.value || '未填写'}`,
    `备注：${settingsSourceDraftNotes.value || '未填写'}`,
  ]
  openSettingsConfirm('保存来源配置', '以下改动会直接写入来源配置文件。', nextLines, () => {
    settingsSourceDraftTouched.value = false
    emit('update-source-config', {
      source_url: String(settingsSelectedSource.value!.source_url),
      enabled: settingsSourceDraftEnabled.value,
      configured_name: settingsSourceDraftName.value,
      market_scope: settingsSourceDraftScope.value,
      market_category: settingsSourceDraftCategory.value,
      notes: settingsSourceDraftNotes.value,
    })
  })
}

function saveSettingsSourceStrategy() {
  if (!settingsSelectedSource.value?.source_name) return
  const nextLines = [
    `来源：${settingsSelectedSource.value.source_name}`,
    `采价方式：${formatFetchModeLabel(settingsStrategyDraftFetchMode.value)}`,
    `采价方案：${settingsStrategyDraftName.value || '未填写'}`,
    `超时秒数：${settingsStrategyDraftTimeout.value}`,
    `重试次数：${settingsStrategyDraftRetry.value}`,
    `采价间隔：${settingsStrategyDraftDelay.value} 秒`,
    `接口方案：${settingsStrategyDraftApiStrategy.value || '未填写'}`,
    `失败返回码：${settingsStrategyDraftBlockedCodes.value || '未填写'}`,
    `网站安全校验：${settingsStrategyDraftVerifySsl.value ? '开启' : '关闭'}`,
  ]
  openSettingsConfirm('保存采价方案', '以下改动会直接写入当前来源的采价配置。', nextLines, () => {
    settingsStrategyDraftTouched.value = false
    emit('update-source-strategy', {
      source_name: String(settingsSelectedSource.value!.source_name),
      preferred_fetch_mode: settingsStrategyDraftFetchMode.value,
      strategy: settingsStrategyDraftName.value,
      timeout_seconds: settingsStrategyDraftTimeout.value,
      retry_count: settingsStrategyDraftRetry.value,
      request_delay_seconds: settingsStrategyDraftDelay.value,
      blocked_status_codes: settingsStrategyDraftBlockedCodes.value.split(',').map((item) => Number(item.trim())).filter((item) => Number.isFinite(item)),
      verify_ssl: settingsStrategyDraftVerifySsl.value,
      api_strategy: settingsStrategyDraftApiStrategy.value,
    })
  })
}

function runSelectedSourceCrawl() {
  if (!settingsSelectedSource.value?.source_url) return
  emit('run-source-crawl', {
    source_url: String(settingsSelectedSource.value.source_url),
    source_name: String(settingsSelectedSource.value.source_name || ''),
  })
}

function addGlobalAlertRuleRow() {
  settingsGlobalAlertDraftRows.value = [
    ...settingsGlobalAlertDraftRows.value,
    { target_name: '', threshold: 0, note: '', group_name: '' },
  ]
}

function removeGlobalAlertRuleRow(index: number) {
  if (settingsGlobalAlertDraftRows.value.length <= 1) {
    settingsGlobalAlertDraftRows.value = [{ target_name: '', threshold: 0, note: '', group_name: '' }]
    return
  }
  settingsGlobalAlertDraftRows.value = settingsGlobalAlertDraftRows.value.filter((_, rowIndex) => rowIndex !== index)
}

function saveGlobalAlertRules() {
  const normalizedItems = settingsGlobalAlertDraftRows.value
    .map((item) => ({
      target_name: String(item.target_name || '').trim(),
      threshold: Number(item.threshold || 0),
      note: String(item.note || '').trim(),
      group_name: String(item.group_name || '').trim(),
    }))
    .filter((item) => item.target_name)
  const nextLines = normalizedItems.map((item) => `${item.target_name}：提醒价格 ${item.threshold}${item.group_name ? ` · 分组 ${item.group_name}` : ''}${item.note ? ` · ${item.note}` : ''}`)
  openSettingsConfirm('保存全局预警规则', '以下规则会作为系统级价格提醒写入后端配置。', nextLines, () => {
    emit('update-global-alert-rules', normalizedItems)
  })
}
</script>

<style scoped>
.pcw-settings-inline-admin {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  align-items: stretch;
  padding: 12px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background: #f8fbff;
}

.pcw-settings-inline-admin article {
  display: grid;
  gap: 5px;
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 7px;
  background: #fff;
}

.pcw-settings-inline-admin span,
.pcw-settings-inline-admin small {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #64748b;
  font-size: 12px;
}

.pcw-settings-inline-admin strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #10203d;
  font-size: 18px;
}

.pcw-settings-panel-tabs {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  padding: 4px;
  border: 1px solid #dbe5f1;
  border-radius: 10px;
  background: #fff;
}

.pcw-settings-panel-tabs button {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 10px 12px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  text-align: left;
}

.pcw-settings-panel-tabs button.active {
  background: #eff6ff;
  box-shadow: inset 0 0 0 1px #bfdbfe;
}

.pcw-settings-panel-tabs strong,
.pcw-settings-panel-tabs small {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pcw-settings-panel-tabs strong {
  color: #10203d;
  font-size: 13px;
}

.pcw-settings-panel-tabs small {
  color: #64748b;
  font-size: 12px;
}

.pcw-settings-form {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
  gap: 10px;
  align-items: end;
}

.pcw-settings-form label,
.pcw-settings-source-form label {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.pcw-settings-form label span,
.pcw-settings-source-form label span {
  font-weight: 800;
  color: #40516b;
}

.pcw-settings-form select,
.pcw-settings-source-form input,
.pcw-settings-source-form select,
.pcw-settings-source-form textarea {
  width: 100%;
  min-width: 0;
  padding: 9px 10px;
  border: 1px solid #dbe5f1;
  border-radius: 6px;
  background: #fff;
  color: #10203d;
  font: inherit;
  font-size: 13px;
}

.pcw-settings-form select,
.pcw-settings-source-form input,
.pcw-settings-source-form select {
  height: 36px;
}

.pcw-settings-source-form textarea {
  min-height: 78px;
  resize: vertical;
}

.pcw-settings-form select:focus,
.pcw-settings-source-form input:focus,
.pcw-settings-source-form select:focus,
.pcw-settings-source-form textarea:focus {
  border-color: #2563eb;
  outline: none;
  box-shadow: 0 0 0 3px #eff6ff;
}

.pcw-settings-source-form {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid #dbe5f1;
}

.pcw-settings-source-form label.full {
  grid-column: 1 / -1;
}

.pcw-settings-inline-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pcw-settings-inline-actions button,
.pcw-settings-confirm-actions button {
  min-height: 36px;
  padding: 0 14px;
  border: 1px solid #2563eb;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  font-weight: 800;
}

.pcw-settings-inline-actions button.secondary,
.pcw-settings-confirm-actions button.secondary {
  border-color: #dbe5f1;
  background: #fff;
  color: #24344d;
}

.pcw-settings-inline-actions button:disabled {
  cursor: not-allowed;
  border-color: #cbd5e1;
  background: #e2e8f0;
  color: #64748b;
}

.pcw-settings-auth-hint {
  grid-column: 1 / -1;
  margin: -2px 0 0;
  color: #b45309;
  font-size: 12px;
  font-weight: 700;
}

.pcw-settings-log-panel {
  grid-column: 1 / -1;
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid #dbe5f1;
  border-radius: 8px;
  background: #fff;
}

.pcw-settings-log-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.pcw-settings-log-head strong {
  color: #10203d;
  font-size: 14px;
}

.pcw-settings-log-head span {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.pcw-settings-log-list {
  display: grid;
  gap: 10px;
}

.pcw-settings-log-list article {
  display: grid;
  gap: 4px;
  padding-top: 10px;
  border-top: 1px solid #edf1f6;
}

.pcw-settings-log-list article:first-child {
  padding-top: 0;
  border-top: 0;
}

.pcw-settings-log-list small,
.pcw-settings-log-list span {
  color: #52647f;
  font-size: 12px;
  line-height: 1.5;
}

.pcw-settings-run-feedback {
  display: grid;
  gap: 4px;
  grid-column: 1 / -1;
  padding: 10px 12px;
  border: 1px solid #dbe5f1;
  border-radius: 8px;
  background: #f8fbff;
}

.pcw-settings-run-feedback strong {
  color: #10203d;
  font-size: 13px;
}

.pcw-settings-run-feedback span {
  color: #52647f;
  font-size: 12px;
  line-height: 1.45;
}

.pcw-settings-alert-rule-list {
  display: grid;
  gap: 12px;
  grid-column: 1 / -1;
}

.pcw-settings-alert-rule-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  padding: 12px;
  border: 1px solid #dbe5f1;
  border-radius: 8px;
  background: #fff;
}

.pcw-settings-confirm-shell {
  display: grid;
  gap: 12px;
}

.pcw-settings-confirm-copy {
  margin: 0;
  color: #52647f;
  font-size: 13px;
  line-height: 1.55;
}

.pcw-settings-confirm-list {
  margin: 0;
  padding-left: 18px;
  color: #10203d;
  font-size: 13px;
  line-height: 1.6;
}

.pcw-settings-confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 1180px) {
  .pcw-settings-inline-admin,
  .pcw-settings-form,
  .pcw-settings-source-form,
  .pcw-settings-panel-tabs,
  .pcw-settings-alert-rule-row {
    grid-template-columns: 1fr;
  }

  .pcw-settings-inline-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
