/** 模块英文键与中文名称的对照：概览接口只返回英文键，下钻面板标题需要中文名称。 */
export const MODULE_LABELS: Record<string, string> = {
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

export function moduleLabel(key: string): string {
  return MODULE_LABELS[key] ?? key
}
