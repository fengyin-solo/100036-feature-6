import { defineStore } from 'pinia'

import { fetchJson } from '@/api/client'

/** 运营概览下钻状态：跨路由保留展开位置与各模块已取到的分布数据。 */

export type DrilldownData = {
  module: string
  total: number
  pendingTotal: number
  statuses: string[]
  distribution: { team: string; counts: number[]; total: number }[]
  trend: { date: string; pending: number }[]
}

type ModuleState = {
  data: DrilldownData | null
  loading: boolean
  error: string
}

type DrillState = {
  expanded: string | null
  modules: Record<string, ModuleState>
}

function freshModuleState(): ModuleState {
  return { data: null, loading: false, error: '' }
}

export const useDrillStore = defineStore('dashboardDrill', {
  state: (): DrillState => ({
    // 停在哪个模块的展开位置：切换模块页或返回概览后依旧展开这一行
    expanded: null,
    modules: {},
  }),
  actions: {
    toggle(module: string) {
      this.expanded = this.expanded === module ? null : module
    },
    ensureState(module: string): ModuleState {
      if (!this.modules[module]) {
        this.modules[module] = freshModuleState()
      }
      return this.modules[module]
    },
    /** 拉取某个模块的下钻数据；silent 用于返回概览时的后台刷新，失败时保留旧数据。 */
    async fetchBreakdown(module: string, silent = false) {
      const state = this.ensureState(module)
      if (!silent) {
        state.loading = true
        state.error = ''
      }
      try {
        const data = await fetchJson<DrilldownData>(
          `/api/overview/modules/${module}/pending-breakdown`,
        )
        state.data = data
        state.loading = false
        state.error = ''
      } catch (error) {
        if (!silent) {
          state.loading = false
          state.error = error instanceof Error ? error.message : '下钻数据读取失败'
        }
      }
    },
  },
})
