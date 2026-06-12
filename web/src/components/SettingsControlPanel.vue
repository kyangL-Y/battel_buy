<template>
  <section class="pcw-card pcw-settings-shell">
    <header class="pcw-settings-hero">
      <div class="pcw-settings-hero-copy">
        <p>系统设置</p>
        <h2>同步、来源、策略、提醒统一管理</h2>
        <small>支持导出和导入设置快照，便于备份和迁移。{{ settingsManagementLocked ? '当前账号只可查看。' : '' }}</small>
      </div>
      <div class="pcw-settings-hero-actions">
        <button type="button" class="secondary" @click="exportSettingsSnapshot">导出快照</button>
        <button type="button" class="secondary" :disabled="settingsManagementLocked" @click="triggerSettingsSnapshotImport">导入快照</button>
        <button type="button" class="secondary" @click="emit('refresh')">刷新状态</button>
      </div>
      <input ref="settingsSnapshotFileInput" class="pcw-settings-file-input" type="file" accept=".json,application/json" @change="handleSettingsSnapshotFileChange" />
    </header>

    <section class="pcw-settings-overview-grid">
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
      <article class="pcw-settings-overview-snapshot">
        <span>设置快照</span>
        <strong>{{ settingsSnapshotSummaryCountLabel }}</strong>
        <small>{{ settingsSnapshotGeneratedLabel }}</small>
      </article>
    </section>

    <section class="pcw-settings-ops-strip" aria-label="系统设置运维状态">
      <article v-for="operationCard in settingsOperationsCards" :key="operationCard.label" :class="operationCard.tone">
        <span>{{ operationCard.label }}</span>
        <strong>{{ operationCard.value }}</strong>
        <small>{{ operationCard.detail }}</small>
      </article>
    </section>

    <div class="pcw-settings-body-grid">
      <section class="pcw-settings-main-column">
        <section class="pcw-settings-readiness-grid" aria-label="发布前巡检">
          <article v-for="readinessRow in settingsReadinessRows" :key="readinessRow.label" :class="readinessRow.tone">
            <span>{{ readinessRow.label }}</span>
            <strong>{{ readinessRow.value }}</strong>
            <small>{{ readinessRow.detail }}</small>
          </article>
        </section>

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
          <label class="full">
            <span>自动采集目标</span>
            <select v-model="settingsScheduleDraftTargetScope" :disabled="settingsManagementLocked" @change="markSettingsScheduleDraftChanged">
              <option value="all_saved">全部已保存地区</option>
              <option value="province">仅省级默认地区</option>
              <option value="city">仅市级默认地区</option>
            </select>
          </label>
          <label v-if="settingsScheduleDraftTargetScope === 'province' || settingsScheduleDraftTargetScope === 'city'">
            <span>默认省份</span>
            <input v-model="settingsScheduleDraftTargetProvince" :disabled="settingsManagementLocked" type="text" placeholder="例如：河南省" @input="markSettingsScheduleDraftChanged" />
          </label>
          <label v-if="settingsScheduleDraftTargetScope === 'city'">
            <span>默认城市</span>
            <input v-model="settingsScheduleDraftTargetCity" :disabled="settingsManagementLocked" type="text" placeholder="例如：郑州市" @input="markSettingsScheduleDraftChanged" />
          </label>
          <div class="pcw-settings-operation-note full">
            <strong>同步调度是全平台统一任务</strong>
            <span>默认省市只作为自动采集的默认目标，不限制行情页展示；行情展示仍按用户选择和已抓取地区返回。</span>
          </div>
          <div class="pcw-settings-inline-actions">
            <button type="submit" :disabled="settingsManagementLocked || !settingsScheduleDirty">保存设置</button>
            <button type="button" class="secondary" :disabled="settingsManagementLocked || crawlStatus?.is_running" @click="emit('run-crawl')">
              {{ crawlStatus?.is_running ? '同步中' : '立即同步' }}
            </button>
            <button type="button" class="secondary" @click="emit('refresh')">刷新状态</button>
          </div>
        </form>

        <form v-else-if="settingsActivePanel === 'source' && settingsSourceOptions.length" class="pcw-settings-source-form" @submit.prevent="saveSettingsSourceConfig">
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

        <section v-else-if="settingsActivePanel === 'source'" class="pcw-settings-empty-state">
          <strong>暂无来源配置</strong>
          <small>当前没有可编辑的来源。先刷新来源状态，或回到来源健康页确认是否已经抓取过市场数据。</small>
          <div class="pcw-settings-inline-actions">
            <button type="button" class="secondary" @click="emit('refresh')">刷新来源状态</button>
            <button type="button" @click="emit('open-section', 'market')">查看来源健康</button>
          </div>
        </section>

        <form v-else-if="settingsActivePanel === 'strategy' && settingsSelectedSource" class="pcw-settings-source-form" @submit.prevent="saveSettingsSourceStrategy">
          <label class="full">
            <span>当前来源</span>
            <select v-model="settingsSelectedSourceUrl" :disabled="settingsManagementLocked" @change="settingsStrategyDraftTouched = false; settingsSourceDraftTouched = false; syncSelectedSourceDraft()">
              <option v-for="item in settingsSourceOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </label>
          <div class="pcw-settings-run-feedback full">
            <strong>来源试跑反馈</strong>
            <span>{{ settingsSelectedSourceRunSummary }}</span>
          </div>
          <label>
            <span>采价方式</span>
            <select v-model="settingsStrategyDraftFetchMode" :disabled="settingsManagementLocked" @change="markSettingsStrategyDraftChanged">
              <option value="requests">快速采价</option>
              <option value="playwright">浏览器采价</option>
              <option value="api">系统采价</option>
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
            <span>系统采价方案</span>
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
            <button type="submit" :disabled="settingsManagementLocked || !settingsSelectedSource || !settingsStrategyDirty">保存采价方案</button>
          </div>
        </form>

        <section v-else-if="settingsActivePanel === 'strategy'" class="pcw-settings-empty-state">
          <strong>未选择来源</strong>
          <small>先在来源配置里选中一个来源，再调整采价方案。</small>
          <div class="pcw-settings-inline-actions">
            <button type="button" @click="settingsActivePanel = 'source'">选择来源</button>
            <button type="button" class="secondary" @click="emit('refresh')">刷新来源状态</button>
          </div>
        </section>

        <form v-else-if="settingsActivePanel === 'alerts'" class="pcw-settings-source-form pcw-settings-alert-form" @submit.prevent="saveGlobalAlertRules">
          <div class="pcw-settings-alert-head full">
            <strong>价格提醒规则</strong>
            <small>每条规则一行，适合在桌面端快速扫视和批量调整。</small>
          </div>
          <div class="pcw-settings-alert-rule-list">
            <div v-for="(item, index) in settingsGlobalAlertDraftRows" :key="`alert-rule-${index}`" class="pcw-settings-alert-rule-row">
              <label>
                <span>提醒商品</span>
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
            <button type="submit" :disabled="settingsManagementLocked || !settingsGlobalAlertDraftRows.some((item) => String(item.target_name || '').trim())">保存价格提醒</button>
          </div>
        </form>

        <section v-else-if="settingsActivePanel === 'access'" class="pcw-settings-admin-board">
          <div class="pcw-settings-board-head">
            <div>
              <strong>账号与权限</strong>
              <small>按账号角色和供应商绑定决定能看哪些数据、能执行哪些操作。</small>
            </div>
            <button type="button" :disabled="settingsManagementLocked" @click="emit('open-section', 'accounts')">进入账号管理</button>
          </div>
          <div class="pcw-settings-role-grid">
            <article v-for="item in settingsAccessRows" :key="item.role" :class="item.tone">
              <span>{{ item.role }}</span>
              <strong>{{ item.title }}</strong>
              <small>{{ item.detail }}</small>
            </article>
          </div>
          <div class="pcw-settings-permission-matrix" aria-label="权限控制矩阵">
            <article v-for="permissionRow in settingsPermissionRows" :key="permissionRow.label">
              <span>{{ permissionRow.label }}</span>
              <strong>{{ permissionRow.owner }}</strong>
              <small>{{ permissionRow.detail }}</small>
            </article>
          </div>
          <div class="pcw-settings-route-grid">
            <button type="button" :disabled="settingsManagementLocked" @click="emit('open-section', 'accounts')">
              <strong>账号管理</strong>
              <small>创建采购账号、分配供应商、设置默认行情地区。</small>
            </button>
            <button type="button" :disabled="settingsManagementLocked" @click="emit('open-section', 'suppliers')">
              <strong>供应商档案</strong>
              <small>维护供应商名称、状态、市场范围和报价入口。</small>
            </button>
            <button type="button" @click="emit('open-section', 'market')">
              <strong>来源健康</strong>
              <small>检查采集来源是否在线、是否有最近同步结果。</small>
            </button>
          </div>
        </section>

        <section v-else-if="settingsActivePanel === 'backup'" class="pcw-settings-admin-board">
          <div class="pcw-settings-board-head">
            <div>
              <strong>备份与迁移</strong>
              <small>当前快照导出同步调度、全部来源、采价方案和价格提醒；导入时先回填当前草稿。</small>
            </div>
            <button type="button" @click="exportSettingsSnapshot">导出快照</button>
          </div>
          <div class="pcw-settings-backup-grid">
            <article v-for="item in settingsBackupRows" :key="item.label">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.detail }}</small>
            </article>
          </div>
          <div class="pcw-settings-route-grid">
            <button type="button" @click="exportSettingsSnapshot">
              <strong>导出 JSON</strong>
              <small>下载当前设置快照，用于发布前留存或迁移预演。</small>
            </button>
            <button type="button" :disabled="settingsManagementLocked" @click="triggerSettingsSnapshotImport">
              <strong>导入预览</strong>
              <small>先预览快照，再应用到当前草稿，不会直接覆盖线上配置。</small>
            </button>
            <button type="button" @click="emit('refresh')">
              <strong>刷新状态</strong>
              <small>重新读取同步状态、来源状态和最近改动。</small>
            </button>
          </div>
        </section>

        <section v-else-if="settingsActivePanel === 'audit'" class="pcw-settings-admin-board">
          <div class="pcw-settings-board-head">
            <div>
              <strong>审计与变更</strong>
              <small>记录设置页最近改动，发布前用于核对调度、来源、策略和提醒。</small>
            </div>
            <button type="button" class="secondary" @click="emit('refresh')">刷新审计</button>
          </div>
          <div class="pcw-settings-audit-list">
            <article v-for="item in settingsAuditRows" :key="item.id">
              <span>{{ item.changed_at }}</span>
              <strong>{{ item.target_name }}</strong>
              <small>{{ item.actor_name }} · {{ item.summary }}</small>
            </article>
          </div>
        </section>
      </section>

      <aside class="pcw-settings-side-column">
        <section class="pcw-settings-rail-card">
          <div class="pcw-settings-rail-head">
            <div>
              <strong>设置快照</strong>
              <small>{{ settingsSnapshotGeneratedLabel }}</small>
            </div>
            <span>{{ settingsSnapshotSummaryCountLabel }}</span>
          </div>
          <p class="pcw-settings-rail-copy">导出会保存调度、全部来源、当前选中来源策略和提醒规则。导入后只填充草稿，再逐项保存。</p>
          <div class="pcw-settings-rail-stat-grid">
            <article>
              <span>来源</span>
              <strong>{{ settingsSnapshotSourceCount }}</strong>
            </article>
            <article>
              <span>提醒</span>
              <strong>{{ settingsSnapshotAlertCount }}</strong>
            </article>
            <article>
              <span>选中来源</span>
              <strong>{{ settingsSnapshotSelectedSourceLabel }}</strong>
            </article>
            <article>
              <span>调度</span>
              <strong>{{ settingsSnapshotScheduleModeLabel }}</strong>
            </article>
          </div>
          <div class="pcw-settings-inline-actions">
            <button type="button" @click="exportSettingsSnapshot">导出 JSON</button>
            <button type="button" class="secondary" :disabled="settingsManagementLocked" @click="triggerSettingsSnapshotImport">导入 JSON</button>
          </div>
        </section>

        <section v-if="settingsActivePanel === 'source' && settingsChangeLogs?.length" class="pcw-settings-rail-card">
          <div class="pcw-settings-rail-head">
            <div>
              <strong>最近改动</strong>
              <small>最近一次来源相关改动</small>
            </div>
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

        <section class="pcw-settings-rail-card">
          <div class="pcw-settings-rail-head">
            <div>
              <strong>{{ settingsActivePanelLabel }}</strong>
              <small>{{ settingsActivePanelDetail }}</small>
            </div>
          </div>
          <ul class="pcw-settings-rail-list">
            <li v-for="item in settingsActivePanelTips" :key="item">{{ item }}</li>
          </ul>
        </section>

        <section class="pcw-settings-rail-card">
          <div class="pcw-settings-rail-head">
            <div>
              <strong>配置生效范围</strong>
              <small>避免把全局设置误认为账号私有设置</small>
            </div>
          </div>
          <div class="pcw-settings-scope-list">
            <article v-for="scopeRow in settingsScopeRows" :key="scopeRow.label">
              <span>{{ scopeRow.label }}</span>
              <strong>{{ scopeRow.owner }}</strong>
              <small>{{ scopeRow.detail }}</small>
            </article>
          </div>
        </section>
      </aside>
    </div>

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

    <el-dialog v-model="settingsSnapshotPreviewVisible" title="导入设置快照" width="min(92vw, 760px)">
      <div class="pcw-settings-snapshot-preview">
        <p v-if="settingsSnapshotPreviewError" class="pcw-settings-snapshot-error">{{ settingsSnapshotPreviewError }}</p>
        <div v-if="settingsSnapshotImportedDocument" class="pcw-settings-snapshot-preview-shell">
          <section class="pcw-settings-snapshot-preview-meta">
            <article>
              <span>文件</span>
              <strong>{{ settingsSnapshotFileName || '未命名' }}</strong>
            </article>
            <article>
              <span>生成时间</span>
              <strong>{{ formatShortDateTime(settingsSnapshotImportedDocument.generated_at) }}</strong>
            </article>
            <article>
              <span>来源 / 提醒</span>
              <strong>{{ settingsSnapshotImportedDocument.summary.source_count }} / {{ settingsSnapshotImportedDocument.summary.alert_rule_count }}</strong>
            </article>
            <article>
              <span>选中来源</span>
              <strong>{{ settingsSnapshotImportedDocument.summary.selected_source_name || '未指定' }}</strong>
            </article>
          </section>
          <div class="pcw-settings-snapshot-preview-json">
            <strong>快照预览</strong>
            <pre>{{ settingsSnapshotPreviewText }}</pre>
          </div>
          <p class="pcw-settings-snapshot-preview-hint">导入后只会回填当前页面草稿，保存仍需逐项点击各分区的保存按钮。</p>
        </div>
      </div>
      <template #footer>
        <div class="pcw-settings-confirm-actions">
          <button type="button" class="secondary" @click="settingsSnapshotPreviewVisible = false">取消</button>
          <button type="button" :disabled="!settingsSnapshotImportedDocument" @click="applySettingsSnapshotDocument">应用到当前草稿</button>
        </div>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  buildSettingsSnapshotDocument,
  parseSettingsSnapshotDocument,
  serializeSettingsSnapshotDocument,
} from '../api'
import type {
  AuthUserRole,
  CrawlStatusItem,
  GlobalAlertRuleItem,
  SettingsChangeLogItem,
  SettingsSnapshotDocument,
  SourceCoverageItem,
} from '../types'

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
    target_scope?: 'all_saved' | 'province' | 'city'
    target_province?: string
    target_city?: string
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
  (event: 'open-section', value: 'accounts' | 'suppliers' | 'market'): void
}>()

type SettingsPanelKey = 'schedule' | 'source' | 'strategy' | 'alerts' | 'access' | 'backup' | 'audit'

const settingsActivePanel = ref<SettingsPanelKey>('schedule')
const settingsScheduleDraftEnabled = ref(false)
const settingsScheduleDraftMode = ref<'interval' | 'daily_time'>('daily_time')
const settingsScheduleDraftDailyRunTime = ref('03:30')
const settingsScheduleDraftInterval = ref(86400)
const settingsFetchModeDraft = ref<'requests' | 'playwright'>('requests')
const settingsScheduleDraftTargetScope = ref<'all_saved' | 'province' | 'city'>('all_saved')
const settingsScheduleDraftTargetProvince = ref('')
const settingsScheduleDraftTargetCity = ref('')
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
const settingsSnapshotFileInput = ref<HTMLInputElement | null>(null)
const settingsSnapshotPreviewVisible = ref(false)
const settingsSnapshotPreviewError = ref('')
const settingsSnapshotImportedDocument = ref<SettingsSnapshotDocument | null>(null)
const settingsSnapshotFileName = ref('')
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
const settingsCurrentScheduleTargetScope = computed(() => props.crawlStatus?.target_scope || 'all_saved')
const settingsCurrentScheduleTargetProvince = computed(() => String(props.crawlStatus?.target_province || ''))
const settingsCurrentScheduleTargetCity = computed(() => String(props.crawlStatus?.target_city || ''))
const fetchModeLabels: Record<'requests' | 'playwright' | 'api', string> = {
  requests: '快速采价',
  playwright: '浏览器采价',
  api: '系统采价',
}
const settingsScheduleDirty = computed(() =>
  settingsScheduleDraftEnabled.value !== Boolean(props.crawlStatus?.schedule_enabled)
  || settingsScheduleDraftMode.value !== (props.crawlStatus?.schedule_mode === 'interval' ? 'interval' : 'daily_time')
  || settingsScheduleDraftDailyRunTime.value !== String(props.crawlStatus?.schedule_daily_run_time || '03:30')
  || settingsScheduleDraftInterval.value !== Number(props.crawlStatus?.schedule_interval_seconds || 86400)
  || settingsFetchModeDraft.value !== (props.crawlStatus?.schedule_fetch_mode === 'playwright' ? 'playwright' : 'requests')
  || settingsScheduleDraftTargetScope.value !== settingsCurrentScheduleTargetScope.value
  || settingsScheduleDraftTargetProvince.value !== settingsCurrentScheduleTargetProvince.value
  || settingsScheduleDraftTargetCity.value !== settingsCurrentScheduleTargetCity.value
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
  const scopeLabel =
    settingsCurrentScheduleTargetScope.value === 'province'
      ? `省级默认 ${settingsCurrentScheduleTargetProvince.value || '未填'}`
      : settingsCurrentScheduleTargetScope.value === 'city'
        ? `市级默认 ${settingsCurrentScheduleTargetCity.value || '未填'}`
        : '全部已保存地区'
  return props.crawlStatus?.next_run_at ? `${modeLabel} · ${scopeLabel} · 下次 ${formatShortDateTime(props.crawlStatus.next_run_at)}` : `${modeLabel} · ${scopeLabel}`
})
const settingsPanelTabs = computed<Array<{ key: SettingsPanelKey; label: string; detail: string }>>(() => [
  { key: 'schedule', label: '同步调度', detail: settingsScheduleEnabled.value ? '自动任务已开启' : '手动同步优先' },
  { key: 'access', label: '权限账号', detail: settingsManagementLocked.value ? '当前只读' : '管理员可配置' },
  { key: 'source', label: '来源配置', detail: `${props.sourceCoverageRows?.length || 0} 个来源` },
  { key: 'strategy', label: '采价方案', detail: settingsSelectedSource.value?.source_name || '选择来源后配置' },
  { key: 'alerts', label: '价格提醒', detail: `${settingsGlobalAlertDraftRows.value.length} 条规则` },
  { key: 'backup', label: '备份迁移', detail: settingsSnapshotSummaryCountLabel.value },
  { key: 'audit', label: '审计变更', detail: `${props.settingsChangeLogs?.length || 0} 条记录` },
])
const settingsSourceHealthLabel = computed(() => {
  const sources = props.sourceCoverageRows || []
  const enabledCount = sources.filter((item) => item.enabled !== false).length
  const failedCount = sources.filter((item) => item.status === 'failed' || item.last_failure).length
  if (!sources.length) return '暂无来源'
  return failedCount ? `${enabledCount} 启用 / ${failedCount} 异常` : `${enabledCount} 启用`
})
const settingsEnabledSourceCount = computed(() => (props.sourceCoverageRows || []).filter((sourceRow) => sourceRow.enabled !== false).length)
const settingsFailedSourceCount = computed(() => (props.sourceCoverageRows || []).filter((sourceRow) => sourceRow.status === 'failed' || sourceRow.last_failure).length)
const settingsScheduleScopeLabel = computed(() => {
  if (settingsCurrentScheduleTargetScope.value === 'province') return `省级默认 ${settingsCurrentScheduleTargetProvince.value || '未填'}`
  if (settingsCurrentScheduleTargetScope.value === 'city') return `市级默认 ${settingsCurrentScheduleTargetCity.value || '未填'}`
  return '全部已保存地区'
})
const settingsAuditCountLabel = computed(() => {
  const count = props.settingsChangeLogs?.length || 0
  return count ? `${count} 条记录` : '等待记录'
})
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
const settingsSnapshotDocument = computed(() => buildSettingsSnapshotDocument({
  crawlStatus: props.crawlStatus,
  sourceCoverageRows: props.sourceCoverageRows,
  globalAlertRules: props.globalAlertRules,
  selectedSourceUrl: settingsSelectedSourceUrl.value,
}))
const settingsSnapshotSourceCount = computed(() => settingsSnapshotDocument.value.summary.source_count)
const settingsSnapshotAlertCount = computed(() => settingsSnapshotDocument.value.summary.alert_rule_count)
const settingsSnapshotSelectedSourceLabel = computed(() => settingsSnapshotDocument.value.summary.selected_source_name || '未指定')
const settingsSnapshotScheduleModeLabel = computed(() =>
  settingsSnapshotDocument.value.schedule.enabled
    ? (settingsSnapshotDocument.value.schedule.mode === 'interval' ? '自动 · 间隔' : '自动 · 定时')
    : '仅手动',
)
const settingsSnapshotGeneratedLabel = computed(() => `生成于 ${formatShortDateTime(settingsSnapshotDocument.value.generated_at)}`)
const settingsSnapshotSummaryCountLabel = computed(() => `${settingsSnapshotSourceCount.value} 来源 / ${settingsSnapshotAlertCount.value} 规则`)
const settingsSnapshotPreviewText = computed(() =>
  settingsSnapshotImportedDocument.value ? serializeSettingsSnapshotDocument(settingsSnapshotImportedDocument.value) : '',
)
const settingsAccessRows = computed(() => [
  {
    role: '管理员',
    title: settingsManagementLocked.value ? '当前账号无管理权' : '当前账号可管理',
    detail: '可维护账号、供应商、来源配置、同步调度、提醒规则和设置快照。',
    tone: settingsManagementLocked.value ? 'warn' : 'green',
  },
  {
    role: '采购账号',
    title: '按绑定供应商隔离',
    detail: '账号管理中分配供应商后，只显示对应供应商和采购链路数据。',
    tone: 'blue',
  },
  {
    role: '供应商账号',
    title: '只进入供应商报价端',
    detail: '供应商账号必须绑定供应商，删除供应商账号会解除采购侧可见关系。',
    tone: 'neutral',
  },
])
const settingsBackupRows = computed(() => [
  { label: '来源配置', value: `${settingsSnapshotSourceCount.value} 个`, detail: '包含展示名称、市场范围、分类、启停和策略。' },
  { label: '价格提醒', value: `${settingsSnapshotAlertCount.value} 条`, detail: '包含商品、阈值、分组和备注。' },
  { label: '同步调度', value: settingsSnapshotScheduleModeLabel.value, detail: settingsScheduleDetail.value },
  { label: '选中来源', value: settingsSnapshotSelectedSourceLabel.value, detail: settingsSnapshotGeneratedLabel.value },
])
const settingsReadinessRows = computed(() => [
  {
    label: '权限门禁',
    value: settingsManagementLocked.value ? '只读' : '管理员',
    detail: settingsManagementLocked.value ? '当前账号不能修改系统设置。' : '可维护账号、来源、调度和快照。',
    tone: settingsManagementLocked.value ? 'warn' : 'green',
  },
  {
    label: '同步边界',
    value: settingsScheduleScopeLabel.value,
    detail: settingsScheduleEnabled.value ? '自动同步按全局任务执行。' : '当前仅手动触发同步。',
    tone: settingsScheduleEnabled.value ? 'blue' : 'warn',
  },
  {
    label: '来源健康',
    value: settingsEnabledSourceCount.value ? `${settingsEnabledSourceCount.value} 启用` : '待配置',
    detail: settingsEnabledSourceCount.value
      ? (settingsFailedSourceCount.value ? `${settingsFailedSourceCount.value} 个来源有异常记录。` : '启用来源无异常记录。')
      : '当前没有启用来源，需先完成来源抓取或配置。',
    tone: settingsFailedSourceCount.value || !settingsEnabledSourceCount.value ? 'warn' : 'green',
  },
  {
    label: '提醒规则',
    value: `${settingsSnapshotAlertCount.value} 条`,
    detail: settingsSnapshotAlertCount.value ? '全局价格提醒可导出入快照。' : '发布前建议至少配置重点商品。',
    tone: settingsSnapshotAlertCount.value ? 'blue' : 'warn',
  },
  {
    label: '审计快照',
    value: props.settingsChangeLogs?.length ? '可追溯' : '待记录',
    detail: '保存设置前先确认变更弹窗，发布前导出 JSON。',
    tone: props.settingsChangeLogs?.length ? 'green' : 'neutral',
  },
])
const settingsPermissionRows = computed(() => [
  { label: '菜单权限', owner: '角色控制', detail: '管理员、采购账号、供应商账号进入不同后台入口。' },
  { label: '按钮权限', owner: settingsManagementLocked.value ? '已锁定' : '管理员可用', detail: '保存、导入、调度变更只对管理员开放。' },
  { label: '数据范围', owner: '供应商绑定', detail: '采购账号只显示分配给自己的供应商；删除供应商后绑定关系不可继续使用。' },
])
const settingsScopeRows = computed(() => [
  { label: '同步调度', owner: '全平台', detail: '所有账号共用一套同步时间和采集默认目标。' },
  { label: '默认行情地区', owner: '账号属性', detail: '只作为进入页面时的默认选择，不锁死其他已抓取地区。' },
  { label: '供应商可见性', owner: '采购账号', detail: '由账号管理中的供应商分配决定，不从系统设置直接改。' },
  { label: '来源配置', owner: '管理员', detail: '来源启停、展示名称和采价策略影响全平台数据采集。' },
])
const settingsAuditRows = computed(() => {
  const rows = props.settingsChangeLogs || []
  if (rows.length) return rows.slice(0, 8)
  return [
    {
      id: 'empty-audit',
      target_name: '暂无设置变更',
      actor_name: '系统',
      action_type: 'source_config',
      changed_at: '等待记录',
      summary: '保存同步、来源、策略或提醒后会在这里显示最近变更。',
    },
  ] as SettingsChangeLogItem[]
})
const settingsOperationsCards = computed(() => [
  {
    label: '权限边界',
    value: settingsManagementLocked.value ? '只读' : '管理员可写',
    detail: settingsManagementLocked.value ? '保存、导入和立即同步已锁定。' : '写入调度、来源和提醒前会二次确认。',
    tone: settingsManagementLocked.value ? 'warn' : 'green',
  },
  {
    label: '来源异常',
    value: settingsFailedSourceCount.value ? `${settingsFailedSourceCount.value} 个待查` : settingsEnabledSourceCount.value ? '暂无异常' : '待配置',
    detail: settingsFailedSourceCount.value
      ? '优先处理失败来源，再开放自动同步。'
      : settingsEnabledSourceCount.value
        ? `${settingsEnabledSourceCount.value} 个启用来源可参与同步。`
        : '暂无启用来源，自动同步不会产生新行情。',
    tone: settingsFailedSourceCount.value || !settingsEnabledSourceCount.value ? 'warn' : 'green',
  },
  {
    label: '调度生效',
    value: settingsScheduleEnabled.value ? '自动任务' : '手动同步',
    detail: settingsScheduleEnabled.value ? settingsScheduleScopeLabel.value : '不会自动拉取新行情。',
    tone: settingsScheduleEnabled.value ? 'blue' : 'warn',
  },
  {
    label: '发布留档',
    value: settingsSnapshotSummaryCountLabel.value,
    detail: props.settingsChangeLogs?.length ? `${props.settingsChangeLogs.length} 条变更可核对。` : '发布前建议导出设置快照。',
    tone: props.settingsChangeLogs?.length ? 'blue' : 'neutral',
  },
])
const settingsActivePanelLabel = computed(() => settingsPanelTabs.value.find((item) => item.key === settingsActivePanel.value)?.label || '系统设置')
const settingsActivePanelDetail = computed(() => settingsPanelTabs.value.find((item) => item.key === settingsActivePanel.value)?.detail || '')
const settingsActivePanelTips = computed(() => {
  if (settingsActivePanel.value === 'schedule') {
    return ['调度只改当前系统同步节奏。', '保存前先看右侧快照摘要。', '移动端会折叠成单列。']
  }
  if (settingsActivePanel.value === 'source') {
    return ['先选来源，再改展示名称、范围和备注。', '右侧显示最近改动。', '源列表为空时会显示空状态。']
  }
  if (settingsActivePanel.value === 'strategy') {
    return ['策略只作用于当前选中的来源。', '试跑结果会回写到反馈区。', '导入快照不会自动新增来源。']
  }
  if (settingsActivePanel.value === 'alerts') {
    return ['每条提醒规则占一行。', '推荐用商品名 + 分组一起维护。', '保存前先清掉空行。']
  }
  if (settingsActivePanel.value === 'access') {
    return ['采购账号可先不绑供应商。', '供应商账号必须绑定供应商。', '账号管理页负责最终保存。']
  }
  if (settingsActivePanel.value === 'backup') {
    return ['导入只回填草稿。', '账号和权限不包含在当前快照内。', '发布前建议导出一份快照。']
  }
  return ['当前审计来自设置操作记录。', '刷新后会同步最近状态。', '后端全量审计仍需独立接口承载。']
})

watch(
  () => settingsSnapshotPreviewVisible.value,
  (visible) => {
    if (!visible) {
      settingsSnapshotPreviewError.value = ''
    }
  },
)

watch(
  () => [
    props.crawlStatus?.schedule_enabled,
    props.crawlStatus?.schedule_mode,
    props.crawlStatus?.schedule_daily_run_time,
    props.crawlStatus?.schedule_interval_seconds,
    props.crawlStatus?.schedule_fetch_mode,
    props.crawlStatus?.target_scope,
    props.crawlStatus?.target_province,
    props.crawlStatus?.target_city,
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
  settingsScheduleDraftTargetScope.value = settingsCurrentScheduleTargetScope.value as 'all_saved' | 'province' | 'city'
  settingsScheduleDraftTargetProvince.value = settingsCurrentScheduleTargetProvince.value
  settingsScheduleDraftTargetCity.value = settingsCurrentScheduleTargetCity.value
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
  const targetProvince = settingsScheduleDraftTargetScope.value === 'province' || settingsScheduleDraftTargetScope.value === 'city'
    ? settingsScheduleDraftTargetProvince.value
    : ''
  const targetCity = settingsScheduleDraftTargetScope.value === 'city' ? settingsScheduleDraftTargetCity.value : ''
  const nextLines = [
    `自动同步：${settingsScheduleDraftEnabled.value ? '开启' : '关闭'}`,
    `同步方式：${modeLabel}`,
    settingsScheduleDraftMode.value === 'daily_time'
      ? `同步时间：${settingsScheduleDraftDailyRunTime.value || '03:30'}`
      : `同步频率：${settingsScheduleDraftInterval.value} 秒`,
    `采价方式：${formatFetchModeLabel(settingsFetchModeDraft.value)}`,
    `自动采集目标：${settingsScheduleDraftTargetScope.value === 'province' ? '省级默认地区' : settingsScheduleDraftTargetScope.value === 'city' ? '市级默认地区' : '全部已保存地区'}`,
    ...(settingsScheduleDraftTargetScope.value === 'province' || settingsScheduleDraftTargetScope.value === 'city'
      ? [targetProvince ? `默认省份：${targetProvince}` : '默认省份：未填写']
      : []),
    ...(settingsScheduleDraftTargetScope.value === 'city'
      ? [targetCity ? `默认城市：${targetCity}` : '默认城市：未填写']
      : []),
  ]
  openSettingsConfirm('保存系统同步设置', '以下改动会立即写入当前系统设置。', nextLines, () => {
    settingsScheduleDraftTouched.value = false
    emit('update-crawl-schedule', {
      enabled: settingsScheduleDraftEnabled.value,
      mode: settingsScheduleDraftMode.value,
      daily_run_time: settingsScheduleDraftMode.value === 'daily_time' ? settingsScheduleDraftDailyRunTime.value : null,
      interval_seconds: settingsScheduleDraftInterval.value,
      fetch_mode: settingsFetchModeDraft.value,
      target_scope: settingsScheduleDraftTargetScope.value,
      target_province: targetProvince,
      target_city: targetCity,
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
    `系统采价方案：${settingsStrategyDraftApiStrategy.value || '未填写'}`,
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
  openSettingsConfirm('保存价格提醒', '以下提醒会写入系统配置。', nextLines, () => {
    emit('update-global-alert-rules', normalizedItems)
  })
}

function triggerSettingsSnapshotImport() {
  settingsSnapshotPreviewError.value = ''
  settingsSnapshotImportedDocument.value = null
  settingsSnapshotFileName.value = ''
  settingsSnapshotPreviewVisible.value = false
  settingsSnapshotFileInput.value?.click()
}

async function handleSettingsSnapshotFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  try {
    const text = await file.text()
    const snapshot = parseSettingsSnapshotDocument(text)
    settingsSnapshotFileName.value = file.name
    settingsSnapshotImportedDocument.value = snapshot
    settingsSnapshotPreviewError.value = ''
    settingsSnapshotPreviewVisible.value = true
  } catch (error) {
    settingsSnapshotFileName.value = file.name
    settingsSnapshotImportedDocument.value = null
    settingsSnapshotPreviewError.value = error instanceof Error ? error.message : '快照文件读取失败'
    settingsSnapshotPreviewVisible.value = true
  }
}

function exportSettingsSnapshot() {
  const snapshotText = serializeSettingsSnapshotDocument(settingsSnapshotDocument.value)
  const blob = new Blob([snapshotText], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `battel-settings-snapshot-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.json`
  link.click()
  URL.revokeObjectURL(url)
}

function applySettingsSnapshotDocument() {
  const snapshot = settingsSnapshotImportedDocument.value
  if (!snapshot) return
  settingsScheduleDraftEnabled.value = Boolean(snapshot.schedule.enabled)
  settingsScheduleDraftMode.value = snapshot.schedule.mode
  settingsScheduleDraftDailyRunTime.value = String(snapshot.schedule.daily_run_time || '03:30')
  settingsScheduleDraftInterval.value = Number(snapshot.schedule.interval_seconds || 86400)
  settingsFetchModeDraft.value = snapshot.schedule.fetch_mode === 'playwright' ? 'playwright' : 'requests'
  settingsScheduleDraftTargetScope.value = snapshot.schedule.target_scope === 'province' || snapshot.schedule.target_scope === 'city'
    ? snapshot.schedule.target_scope
    : 'all_saved'
  settingsScheduleDraftTargetProvince.value = String(snapshot.schedule.target_province || '')
  settingsScheduleDraftTargetCity.value = String(snapshot.schedule.target_city || '')
  settingsScheduleDraftTouched.value = true

  const selectedSourceUrl = String(snapshot.selected_source_url || '').trim()
  if (selectedSourceUrl && settingsSourceOptions.value.some((item) => item.value === selectedSourceUrl)) {
    settingsSelectedSourceUrl.value = selectedSourceUrl
    settingsSourceDraftTouched.value = false
    syncSelectedSourceDraft()
    const selectedSource = snapshot.selected_source_strategy
    if (selectedSource) {
      settingsSourceDraftEnabled.value = selectedSource.enabled !== false
      settingsSourceDraftName.value = String(selectedSource.configured_name || '')
      settingsSourceDraftScope.value = String(selectedSource.market_scope || '')
      settingsSourceDraftCategory.value = String(selectedSource.market_category || '')
      settingsSourceDraftNotes.value = String(selectedSource.notes || '')
      settingsStrategyDraftFetchMode.value = selectedSource.preferred_fetch_mode || 'requests'
      settingsStrategyDraftName.value = String(selectedSource.strategy || '')
      settingsStrategyDraftTimeout.value = Number(selectedSource.timeout_seconds || 15)
      settingsStrategyDraftRetry.value = Number(selectedSource.retry_count ?? 2)
      settingsStrategyDraftDelay.value = Number(selectedSource.request_delay_seconds ?? 1)
      settingsStrategyDraftBlockedCodes.value = String((selectedSource.blocked_status_codes || [403, 429]).join(','))
      settingsStrategyDraftVerifySsl.value = selectedSource.verify_ssl !== false
      settingsStrategyDraftApiStrategy.value = String(selectedSource.api_strategy || 'off')
    }
  }

  settingsGlobalAlertDraftRows.value = snapshot.alert_rules.length
    ? snapshot.alert_rules.map((item) => ({
      target_name: String(item.target_name || ''),
      threshold: Number(item.threshold || 0),
      note: String(item.note || ''),
      group_name: String(item.group_name || ''),
    }))
    : [{ target_name: '', threshold: 0, note: '', group_name: '' }]
  settingsSnapshotPreviewVisible.value = false
  settingsActivePanel.value = 'schedule'
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

.pcw-settings-shell {
  display: grid;
  gap: 12px;
  min-width: 0;
  padding: 12px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background: #f8fbff;
}

.pcw-settings-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border: 1px solid #dbe5f1;
  border-radius: 8px;
  background: #fff;
}

.pcw-settings-hero-copy {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.pcw-settings-hero-copy p,
.pcw-settings-rail-head small,
.pcw-settings-rail-copy,
.pcw-settings-rail-list,
.pcw-settings-snapshot-preview-hint {
  margin: 0;
}

.pcw-settings-hero-copy p {
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
}

.pcw-settings-hero-copy h2 {
  margin: 0;
  color: #10203d;
  font-size: 18px;
  line-height: 1.3;
}

.pcw-settings-hero-copy small {
  color: #52647f;
  font-size: 12px;
  line-height: 1.5;
}

.pcw-settings-hero-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.pcw-settings-file-input {
  display: none;
}

.pcw-settings-overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.pcw-settings-overview-grid article,
.pcw-settings-rail-card {
  display: grid;
  gap: 6px;
  min-width: 0;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
}

.pcw-settings-rail-card {
  gap: 8px;
  padding: 10px;
}

.pcw-settings-overview-grid span,
.pcw-settings-overview-grid small,
.pcw-settings-rail-head small,
.pcw-settings-rail-copy,
.pcw-settings-rail-list,
.pcw-settings-snapshot-preview-hint {
  min-width: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.pcw-settings-overview-grid strong,
.pcw-settings-rail-head strong,
.pcw-settings-rail-stat-grid strong,
.pcw-settings-alert-head strong,
.pcw-settings-snapshot-preview-meta strong {
  min-width: 0;
  color: #10203d;
  font-size: 14px;
  line-height: 1.3;
}

.pcw-settings-overview-snapshot {
  box-shadow: inset 0 0 0 1px #bfdbfe;
}

.pcw-settings-ops-strip {
  display: none;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.pcw-settings-ops-strip article {
  position: relative;
  display: grid;
  gap: 5px;
  min-width: 0;
  min-height: 86px;
  padding: 13px 13px 13px 15px;
  border: 1px solid #dbe5f1;
  border-radius: 8px;
  background: #fff;
  text-align: left;
}

.pcw-settings-ops-strip article::before {
  content: "";
  position: absolute;
  left: 0;
  top: 14px;
  bottom: 14px;
  width: 3px;
  border-radius: 999px;
  background: #2563eb;
}

.pcw-settings-ops-strip article.green::before {
  background: #16a34a;
}

.pcw-settings-ops-strip article.green {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.pcw-settings-ops-strip article.blue {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.pcw-settings-ops-strip article.warn {
  border-color: #fed7aa;
  background: #fff7ed;
}

.pcw-settings-ops-strip article.warn::before {
  background: #f97316;
}

.pcw-settings-ops-strip span,
.pcw-settings-ops-strip small {
  min-width: 0;
  overflow: hidden;
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.pcw-settings-ops-strip strong {
  min-width: 0;
  overflow: hidden;
  color: #10203d;
  font-size: 16px;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pcw-settings-body-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 288px;
  gap: 10px;
  min-width: 0;
}

.pcw-settings-main-column,
.pcw-settings-side-column {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.pcw-settings-side-column {
  align-content: start;
}

.pcw-settings-readiness-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  min-width: 0;
}

.pcw-settings-readiness-grid article {
  display: grid;
  gap: 3px;
  min-width: 0;
  min-height: 76px;
  padding: 9px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
}

.pcw-settings-readiness-grid article.green {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.pcw-settings-readiness-grid article.blue {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.pcw-settings-readiness-grid article.warn {
  border-color: #fed7aa;
  background: #fff7ed;
}

.pcw-settings-readiness-grid span,
.pcw-settings-scope-list span,
.pcw-settings-permission-matrix span {
  min-width: 0;
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.35;
}

.pcw-settings-readiness-grid strong,
.pcw-settings-scope-list strong,
.pcw-settings-permission-matrix strong {
  min-width: 0;
  overflow: hidden;
  color: #10203d;
  font-size: 14px;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pcw-settings-readiness-grid small,
.pcw-settings-scope-list small,
.pcw-settings-permission-matrix small {
  min-width: 0;
  color: #52647f;
  font-size: 11px;
  line-height: 1.35;
}

.pcw-settings-readiness-grid small {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.pcw-settings-panel-tabs {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(126px, 1fr));
  gap: 8px;
  padding: 4px;
  border: 1px solid #dbe5f1;
  border-radius: 10px;
  background: #fff;
}

.pcw-settings-panel-tabs button {
  display: grid;
  gap: 3px;
  min-width: 0;
  min-height: 54px;
  padding: 8px 10px;
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
  gap: 9px;
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
.pcw-settings-form input,
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
.pcw-settings-form input,
.pcw-settings-source-form input,
.pcw-settings-source-form select {
  height: 36px;
}

.pcw-settings-source-form textarea {
  min-height: 78px;
  resize: vertical;
}

.pcw-settings-form select:focus,
.pcw-settings-form input:focus,
.pcw-settings-source-form input:focus,
.pcw-settings-source-form select:focus,
.pcw-settings-source-form textarea:focus {
  border-color: #2563eb;
  outline: none;
  box-shadow: 0 0 0 3px #eff6ff;
}

.pcw-settings-source-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
  padding-top: 8px;
  border-top: 1px solid #dbe5f1;
}

.pcw-settings-alert-form {
  padding-top: 12px;
}

.pcw-settings-alert-head {
  display: grid;
  gap: 4px;
}

.pcw-settings-source-form label.full {
  grid-column: 1 / -1;
}

.pcw-settings-operation-note {
  display: grid;
  gap: 4px;
  grid-column: 1 / -1;
  padding: 11px 12px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
}

.pcw-settings-operation-note strong {
  color: #10203d;
  font-size: 13px;
}

.pcw-settings-operation-note span {
  color: #52647f;
  font-size: 12px;
  line-height: 1.5;
}

.pcw-settings-empty-state {
  display: grid;
  gap: 6px;
  padding: 18px 14px;
  border: 1px dashed #bfdbfe;
  border-radius: 8px;
  background: #fff;
}

.pcw-settings-empty-state strong {
  color: #10203d;
  font-size: 14px;
}

.pcw-settings-empty-state small {
  color: #52647f;
  font-size: 12px;
  line-height: 1.5;
}

.pcw-settings-inline-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  grid-column: 1 / -1;
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
  gap: 8px;
}

.pcw-settings-log-list article {
  display: grid;
  gap: 3px;
  padding-top: 8px;
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

.pcw-settings-rail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.pcw-settings-rail-head span {
  flex: 0 0 auto;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.pcw-settings-rail-copy {
  color: #52647f;
}

.pcw-settings-rail-stat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}

.pcw-settings-rail-stat-grid article {
  display: grid;
  gap: 3px;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #f8fbff;
}

.pcw-settings-rail-stat-grid span,
.pcw-settings-rail-list {
  color: #64748b;
  font-size: 12px;
}

.pcw-settings-rail-list {
  display: grid;
  gap: 6px;
  padding-left: 16px;
}

.pcw-settings-rail-list li {
  line-height: 1.5;
}

.pcw-settings-scope-list {
  display: grid;
  gap: 6px;
}

.pcw-settings-scope-list article {
  display: grid;
  gap: 3px;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #f8fbff;
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

.pcw-settings-admin-board {
  display: grid;
  gap: 12px;
  min-width: 0;
  padding: 12px;
  border: 1px solid #dbe5f1;
  border-radius: 8px;
  background: #fff;
}

.pcw-settings-board-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
}

.pcw-settings-board-head div {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.pcw-settings-board-head strong,
.pcw-settings-route-grid strong,
.pcw-settings-role-grid strong,
.pcw-settings-backup-grid strong,
.pcw-settings-audit-list strong {
  min-width: 0;
  color: #10203d;
  font-size: 14px;
  line-height: 1.35;
}

.pcw-settings-board-head small,
.pcw-settings-route-grid small,
.pcw-settings-role-grid small,
.pcw-settings-backup-grid small,
.pcw-settings-audit-list small,
.pcw-settings-audit-list span {
  min-width: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.pcw-settings-board-head button,
.pcw-settings-route-grid button {
  min-height: 36px;
  padding: 0 14px;
  border: 1px solid #2563eb;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  font-weight: 800;
}

.pcw-settings-board-head button.secondary,
.pcw-settings-route-grid button.secondary {
  border-color: #dbe5f1;
  background: #fff;
  color: #24344d;
}

.pcw-settings-board-head button:disabled,
.pcw-settings-route-grid button:disabled {
  cursor: not-allowed;
  border-color: #cbd5e1;
  background: #e2e8f0;
  color: #64748b;
}

.pcw-settings-role-grid,
.pcw-settings-backup-grid,
.pcw-settings-route-grid,
.pcw-settings-permission-matrix {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.pcw-settings-backup-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.pcw-settings-role-grid article,
.pcw-settings-backup-grid article,
.pcw-settings-route-grid button,
.pcw-settings-permission-matrix article {
  display: grid;
  gap: 5px;
  min-width: 0;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fbff;
  text-align: left;
}

.pcw-settings-route-grid button {
  min-height: 92px;
  border-color: #dbeafe;
  background: #fff;
  color: inherit;
}

.pcw-settings-route-grid button:hover {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.pcw-settings-permission-matrix article {
  background: #fff;
}

.pcw-settings-role-grid span,
.pcw-settings-backup-grid span {
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
}

.pcw-settings-role-grid article.green {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.pcw-settings-role-grid article.warn {
  border-color: #fed7aa;
  background: #fff7ed;
}

.pcw-settings-role-grid article.blue {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.pcw-settings-audit-list {
  display: grid;
  gap: 10px;
}

.pcw-settings-audit-list article {
  display: grid;
  grid-template-columns: 86px minmax(130px, .34fr) minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  min-width: 0;
  padding: 11px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fbff;
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

.pcw-settings-snapshot-preview {
  display: grid;
  gap: 12px;
}

.pcw-settings-snapshot-error {
  margin: 0;
  color: #b91c1c;
  font-size: 13px;
  line-height: 1.5;
}

.pcw-settings-snapshot-preview-shell {
  display: grid;
  gap: 12px;
}

.pcw-settings-snapshot-preview-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.pcw-settings-snapshot-preview-meta article {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #f8fbff;
}

.pcw-settings-snapshot-preview-meta span {
  color: #64748b;
  font-size: 12px;
}

.pcw-settings-snapshot-preview-json {
  display: grid;
  gap: 8px;
}

.pcw-settings-snapshot-preview-json pre {
  overflow: auto;
  margin: 0;
  max-height: 280px;
  padding: 12px;
  border: 1px solid #dbe5f1;
  border-radius: 6px;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 12px;
  line-height: 1.55;
}

@media (max-width: 1180px) {
  .pcw-settings-hero,
  .pcw-settings-overview-grid,
  .pcw-settings-body-grid,
  .pcw-settings-form,
  .pcw-settings-source-form,
  .pcw-settings-panel-tabs,
  .pcw-settings-alert-rule-row,
  .pcw-settings-snapshot-preview-meta,
  .pcw-settings-rail-stat-grid,
  .pcw-settings-role-grid,
  .pcw-settings-backup-grid,
  .pcw-settings-ops-strip,
  .pcw-settings-route-grid,
  .pcw-settings-readiness-grid,
  .pcw-settings-permission-matrix,
  .pcw-settings-audit-list article {
    grid-template-columns: 1fr;
  }

  .pcw-settings-hero {
    align-items: start;
  }

  .pcw-settings-inline-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .pcw-settings-hero-actions {
    justify-content: flex-start;
  }

  .pcw-settings-board-head {
    display: grid;
  }
}
</style>
