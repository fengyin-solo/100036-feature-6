<template>
  <div class="drill-panel">
    <div v-if="state.loading" class="drill-hint">正在加载{{ label }}待处理分布…</div>

    <div v-else-if="state.error" class="drill-error">
      <span>{{ state.error }}</span>
      <button class="btn" type="button" @click="load">重试</button>
    </div>

    <template v-else-if="state.data">
      <!-- 空态：该模块整体没有数据 -->
      <div v-if="state.data.total === 0" class="drill-hint">
        {{ label }}暂时没有任何业务条目，登记后即可看到待处理分布。
      </div>
      <!-- 空态：有数据但没有待处理条目 -->
      <div v-else-if="state.data.pendingTotal === 0" class="drill-hint">
        {{ label }}当前没有待处理条目，所有记录都已流转完成。
      </div>

      <template v-else>
        <p class="drill-summary">
          共 <strong>{{ state.data.pendingTotal }}</strong> 条待处理，按状态与负责班组分布
          （与「<RouterLink :to="`/${module}`">{{ label }}</RouterLink>」页面同口径）
        </p>
        <table class="data-table drill-table">
          <thead>
            <tr>
              <th>负责班组</th>
              <th v-for="status in state.data.statuses" :key="status">{{ status }}</th>
              <th>小计</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in state.data.distribution" :key="row.team">
              <td>{{ row.team }}</td>
              <td v-for="(count, index) in row.counts" :key="state.data!.statuses[index]">
                {{ count === 0 ? '—' : count }}
              </td>
              <td>{{ row.total }}</td>
            </tr>
          </tbody>
        </table>

        <div class="trend-block">
          <h4 class="trend-title">近七天待处理趋势</h4>
          <svg class="trend-chart" viewBox="0 0 560 160" role="img" aria-label="近七天待处理量趋势曲线">
            <line :x1="padLeft" :x2="540" :y1="baseY" :y2="baseY" class="trend-axis" />
            <line :x1="padLeft" :x2="padLeft" :y1="10" :y2="baseY" class="trend-axis" />
            <template v-if="maxValue > 0">
              <polyline :points="linePoints" class="trend-line" />
              <polygon :points="areaPoints" class="trend-area" />
            </template>
            <g v-for="point in points" :key="point.date">
              <circle :cx="point.x" :cy="point.y" r="3.5" class="trend-dot" />
              <text :x="point.x" :y="point.y - 8" text-anchor="middle" class="trend-value">{{ point.value }}</text>
              <text :x="point.x" :y="baseY + 18" text-anchor="middle" class="trend-label">{{ point.label }}</text>
            </g>
          </svg>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'

import { useDrillStore } from '@/stores/drill'
import { moduleLabel } from '@/views/Dashboard/modules'

const props = defineProps<{ module: string }>()

const store = useDrillStore()
const label = computed(() => moduleLabel(props.module))
const state = computed(() => store.ensureState(props.module))

function load() {
  void store.fetchBreakdown(props.module)
}

onMounted(() => {
  // 已取过的数据保持原样（切换模块或返回概览后位置与内容都还在），只有报错时支持手动重试
  if (!state.value.data && !state.value.loading && !state.value.error) {
    load()
  }
})

const padLeft = 40
const baseY = 120
const chartWidth = 500

const maxValue = computed(() => Math.max(0, ...(state.value.data?.trend.map((p) => p.pending) ?? [0])))

const points = computed(() => {
  const trend = state.value.data?.trend ?? []
  const max = maxValue.value
  return trend.map((point, index) => ({
    date: point.date,
    label: point.date.slice(5),
    value: point.pending,
    x: padLeft + (trend.length <= 1 ? chartWidth / 2 : (chartWidth / (trend.length - 1)) * index),
    y: max === 0 ? baseY : baseY - (point.pending / max) * (baseY - 20),
  }))
})

const linePoints = computed(() => points.value.map((point) => `${point.x},${point.y}`).join(' '))

const areaPoints = computed(() => {
  const list = points.value
  if (!list.length) return ''
  return `${list[0].x},${baseY} ${list.map((p) => `${p.x},${p.y}`).join(' ')} ${list[list.length - 1].x},${baseY}`
})
</script>

<style scoped>
.drill-panel {
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 14px;
}
.drill-hint {
  color: var(--muted);
  font-size: 13px;
  padding: 10px 4px;
  text-align: center;
}
.drill-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #b42318;
  font-size: 13px;
  padding: 8px 4px;
}
.drill-summary {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--muted);
}
.drill-summary strong {
  color: var(--brand);
}
.drill-table {
  font-size: 12px;
}
.trend-block {
  margin-top: 14px;
}
.trend-title {
  margin: 0 0 6px;
  font-size: 13px;
}
.trend-chart {
  width: 100%;
  height: 200px;
}
.trend-axis {
  stroke: var(--border);
  stroke-width: 1;
}
.trend-line {
  fill: none;
  stroke: var(--brand);
  stroke-width: 2;
}
.trend-area {
  fill: rgba(31, 111, 235, 0.1);
  stroke: none;
}
.trend-dot {
  fill: var(--brand);
}
.trend-value {
  font-size: 10px;
  fill: #1f2937;
}
.trend-label {
  font-size: 10px;
  fill: var(--muted);
}
</style>
