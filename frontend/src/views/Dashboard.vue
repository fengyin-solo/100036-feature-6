<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>
    <div v-if="loadError" class="load-error">
      <span class="error-text">运营概览加载失败：{{ loadError }}</span>
      <button class="btn" type="button" @click="loadOverview">重试</button>
    </div>
    <template v-else>
      <div class="stat-row">
        <article v-for="card in cards" :key="card.label" class="stat-card">
          <span class="stat-label">{{ card.label }}</span>
          <strong class="stat-value">{{ card.value }}</strong>
        </article>
      </div>
      <table class="data-table">
        <thead>
          <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
        </thead>
        <tbody>
          <template v-for="row in moduleRows" :key="row.name">
            <tr>
              <td>{{ row.name }}</td>
              <td>{{ row.created }}</td>
              <td>
                <button
                  class="link"
                  type="button"
                  :aria-expanded="isExpanded(row.name)"
                  :title="isExpanded(row.name) ? '收起待处理分布' : '展开待处理分布'"
                  @click="toggleDrill(row.name)"
                >{{ row.pending }}</button>
              </td>
              <td>{{ row.abnormal }}</td>
            </tr>
            <tr v-if="isExpanded(row.name)" class="drill-row">
              <td colspan="4" class="drill-cell">
                <div v-if="drillState(row.name).status === 'loading'" class="drill-tip">
                  正在加载{{ moduleLabel(row.name) }}的待处理分布…
                </div>
                <div v-else-if="drillState(row.name).status === 'error'" class="drill-tip">
                  <span class="error-text">{{ moduleLabel(row.name) }}待处理分布加载失败：{{ drillState(row.name).message }}</span>
                  <button class="btn" type="button" @click="loadDrilldown(row.name)">重试</button>
                </div>
                <div v-else-if="drillState(row.name).data" class="drill-panel">
                  <div class="drill-head">
                    <strong>{{ moduleLabel(row.name) }} · 待处理 {{ drillState(row.name).data!.pending }} 条</strong>
                    <span class="drill-sub">与模块页面同源统计，该模块共 {{ drillState(row.name).data!.total }} 条记录</span>
                  </div>
                  <p v-if="drillState(row.name).data!.total === 0" class="drill-tip">
                    该模块暂无数据，可先到模块页面登记条目。
                  </p>
                  <p v-else-if="drillState(row.name).data!.pending === 0" class="drill-tip">
                    该模块当前没有待处理条目，都已在模块页面流转完毕。
                  </p>
                  <div v-else class="drill-grid">
                    <section class="drill-block">
                      <h3>按状态</h3>
                      <table class="data-table">
                        <tbody>
                          <tr v-for="item in drillState(row.name).data!.by_status" :key="item.name">
                            <td>{{ item.name }}</td>
                            <td>{{ item.count }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </section>
                    <section class="drill-block">
                      <h3>按负责班组</h3>
                      <table v-if="drillState(row.name).data!.by_team.length" class="data-table">
                        <tbody>
                          <tr v-for="item in drillState(row.name).data!.by_team" :key="item.name">
                            <td>{{ item.name }}</td>
                            <td>{{ item.count }}</td>
                          </tr>
                        </tbody>
                      </table>
                      <p v-else class="drill-tip">该模块的条目没有负责班组字段，暂不分布。</p>
                    </section>
                    <section class="drill-block drill-trend">
                      <h3>近七天待处理趋势</h3>
                      <template v-if="drillState(row.name).data!.date_field">
                        <svg
                          class="trend-chart"
                          :viewBox="`0 0 ${TREND_W} ${TREND_H}`"
                          role="img"
                          :aria-label="`${moduleLabel(row.name)}近七天待处理趋势`"
                        >
                          <line
                            :x1="TREND_PAD" :y1="TREND_H - TREND_PAD"
                            :x2="TREND_W - TREND_PAD" :y2="TREND_H - TREND_PAD"
                            class="trend-axis"
                          />
                          <polyline
                            :points="trendLine(trendPoints(drillState(row.name).data!.trend))"
                            class="trend-line"
                            fill="none"
                          />
                          <g v-for="point in trendPoints(drillState(row.name).data!.trend)" :key="point.date">
                            <circle :cx="point.x" :cy="point.y" r="3" class="trend-dot" />
                            <text :x="point.x" :y="point.y - 8" class="trend-value">{{ point.count }}</text>
                            <text :x="point.x" :y="TREND_H - 6" class="trend-date">{{ point.label }}</text>
                          </g>
                        </svg>
                        <p class="drill-sub">按「{{ drillState(row.name).data!.date_field }}」统计每日待处理条目数</p>
                      </template>
                      <p v-else class="drill-tip">该模块的条目没有日期字段，暂不统计趋势。</p>
                    </section>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </template>
  </section>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import { fetchJson } from '@/api/client'
import { useOverviewStore } from '@/stores/overview'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

type Drilldown = {
  module: string
  total: number
  pending: number
  owner_field: string | null
  date_field: string | null
  by_status: { name: string; count: number }[]
  by_team: { name: string; count: number }[]
  trend: { date: string; count: number }[]
}

type DrillState = { status: 'loading' | 'error' | 'ready'; data?: Drilldown; message?: string }

type TrendPoint = { date: string; count: number; x: number; y: number; label: string }

const MODULE_LABELS: Record<string, string> = {
  station: '光伏电站',
  array: '光伏方阵',
  inverter: '逆变器管理',
  combiner: '汇流箱管理',
  stringmon: '组串监测',
  irradiance: '辐照监测',
  cleaning: '组件清洗',
  inspection: '巡检任务',
  defect: '缺陷登记',
  repair: '消缺处理',
  sparepart: '备件领用',
  generation: '发电量核算',
  curtail: '限电记录',
  alarm: '告警中心',
  permit: '作业许可',
  contractor: '运维承包商',
  training: '培训考核',
  settlement: '电量结算',
}

const TREND_W = 560
const TREND_H = 160
const TREND_PAD = 28

const overviewStore = useOverviewStore()

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])
const loadError = ref('')
const drillStates = reactive<Record<string, DrillState>>({})

function isExpanded(name: string): boolean {
  return overviewStore.expandedModules.includes(name)
}

function moduleLabel(name: string): string {
  return MODULE_LABELS[name] ?? name
}

function drillState(name: string): DrillState {
  return drillStates[name] ?? { status: 'loading' }
}

function toggleDrill(name: string) {
  overviewStore.toggle(name)
  if (isExpanded(name)) {
    void loadDrilldown(name)
  }
}

async function loadOverview() {
  loadError.value = ''
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
    // 回到概览时重新拉取已展开模块的下钻数据，保证数字与模块页面一致
    const names = new Set(payload.modules.map((item) => item.name))
    await Promise.all(
      overviewStore.expandedModules.filter((name) => names.has(name)).map((name) => loadDrilldown(name)),
    )
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '接口请求失败'
    return
  }
  if (overviewStore.scrollY > 0) {
    await nextTick()
    window.scrollTo(0, overviewStore.scrollY)
  }
}

async function loadDrilldown(name: string) {
  drillStates[name] = { status: 'loading' }
  try {
    const data = await fetchJson<Drilldown>(`/api/overview/drilldown?module=${encodeURIComponent(name)}`)
    drillStates[name] = { status: 'ready', data }
  } catch (error) {
    drillStates[name] = {
      status: 'error',
      message: error instanceof Error ? error.message : '接口请求失败',
    }
  }
}

function trendPoints(trend: Drilldown['trend']): TrendPoint[] {
  const max = Math.max(...trend.map((item) => item.count), 1)
  const span = Math.max(trend.length - 1, 1)
  return trend.map((item, index) => ({
    date: item.date,
    count: item.count,
    x: TREND_PAD + (index * (TREND_W - 2 * TREND_PAD)) / span,
    y: TREND_H - TREND_PAD - (item.count / max) * (TREND_H - 2 * TREND_PAD),
    label: item.date.slice(5),
  }))
}

function trendLine(points: TrendPoint[]): string {
  return points.map((point) => `${point.x},${point.y}`).join(' ')
}

onMounted(() => {
  void loadOverview()
})

onBeforeRouteLeave(() => {
  overviewStore.rememberScroll(window.scrollY)
})
</script>

<style scoped>
.load-error {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
}
.drill-row > td {
  background: #f8fafc;
}
.drill-cell {
  padding: 12px;
}
.drill-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.drill-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.drill-sub {
  color: var(--muted);
  font-size: 12px;
  margin: 0;
}
.drill-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
.drill-block {
  flex: 1;
  min-width: 200px;
}
.drill-block h3 {
  margin: 0 0 6px;
  font-size: 13px;
}
.drill-trend {
  flex: 2;
  min-width: 320px;
}
.drill-tip {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  font-size: 13px;
  margin: 0;
}
.trend-chart {
  width: 100%;
  max-width: 560px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
}
.trend-axis {
  stroke: var(--border);
}
.trend-line {
  stroke: var(--brand);
  stroke-width: 2;
}
.trend-dot {
  fill: var(--brand);
}
.trend-value,
.trend-date {
  font-size: 10px;
  fill: var(--muted);
  text-anchor: middle;
}
</style>
