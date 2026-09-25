<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。点击某模块的待处理量可下钻查看分布。</p>
      </div>
    </header>

    <div v-if="loadError" class="overview-error">
      <span class="error-text">{{ loadError }}</span>
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
              <td>{{ moduleLabel(row.name) }}</td>
              <td>{{ row.created }}</td>
              <td>
                <button
                  class="pending-trigger"
                  type="button"
                  :class="{ active: drill.expanded === row.name }"
                  :aria-expanded="drill.expanded === row.name"
                  @click="toggleRow(row.name)"
                >
                  {{ row.pending }}
                </button>
              </td>
              <td>{{ row.abnormal }}</td>
            </tr>
            <tr v-if="drill.expanded === row.name" class="drill-row">
              <td colspan="4">
                <PendingDrilldown :module="row.name" />
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </template>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'
import { useDrillStore } from '@/stores/drill'
import PendingDrilldown from './Dashboard/PendingDrilldown.vue'
import { moduleLabel } from './Dashboard/modules'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])
const loadError = ref('')

const drill = useDrillStore()

function toggleRow(module: string) {
  drill.toggle(module)
}

async function loadOverview() {
  loadError.value = ''
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
    // 返回概览后若仍停在某个展开模块，后台静默刷新其下钻数据；失败则保留上次结果，不打断查看
    if (drill.expanded) {
      void drill.fetchBreakdown(drill.expanded, true)
    }
  } catch (error) {
    // 接口异常时看板不显示成一片空白：保留错误说明并提供重试，而不是用假的 0 填充
    loadError.value = error instanceof Error ? error.message : '运营概览读取失败'
  }
}

onMounted(loadOverview)
</script>

<style scoped>
.pending-trigger {
  border: none;
  background: none;
  padding: 0;
  color: var(--brand);
  font: inherit;
  cursor: pointer;
  text-decoration: underline dotted;
}
.pending-trigger.active {
  font-weight: 600;
  text-decoration: none;
}
.drill-row > td {
  padding: 10px 12px;
  background: #f6f8fb;
}
.overview-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #fff;
  border: 1px solid #f2c2bd;
  border-radius: 8px;
  padding: 14px 16px;
}
</style>
