import { defineStore } from 'pinia'

/** 运营概览看板的交互状态：记住下钻展开位置和滚动高度，
 *  切到模块页面再返回概览时视图能停在原来的地方。
 */
export const useOverviewStore = defineStore('overview', {
  state: () => ({
    expandedModules: [] as string[],
    scrollY: 0,
  }),
  actions: {
    toggle(module: string) {
      const index = this.expandedModules.indexOf(module)
      if (index >= 0) {
        this.expandedModules.splice(index, 1)
      } else {
        this.expandedModules.push(module)
      }
    },
    rememberScroll(y: number) {
      this.scrollY = y
    },
  },
})
