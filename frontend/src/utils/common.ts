import type {Dict} from '@/lib/api/type/common'

/**
 * 解析 i18n 名称（后端可能直接返回显示名或 i18n 键）
 */
export function i18n_name(name?: string): string {
  if (!name) return ''
  return name
}

/**
 * 数字千分位格式化
 */
export function numberFormat(value?: number | string, fractionDigits = 0): string {
  if (value === undefined || value === null || value === '') return '0'
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '0'
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })
}
