import type {Dict} from '@/lib/api/type/common'

/**
 * 时间格式化，对齐 Vue 端 dateFormat
 */
export function dateFormat(date?: any, format = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!date) return ''
  const d = new Date(date)
  if (isNaN(d.getTime())) return String(date)
  const pad = (n: number) => (n < 10 ? '0' + n : '' + n)
  const map: Dict<string> = {
    'YYYY': '' + d.getFullYear(),
    'MM': pad(d.getMonth() + 1),
    'DD': pad(d.getDate()),
    'HH': pad(d.getHours()),
    'mm': pad(d.getMinutes()),
    'ss': pad(d.getSeconds()),
  }
  return format
    .replace('YYYY', map['YYYY'])
    .replace('MM', map['MM'])
    .replace('DD', map['DD'])
    .replace('HH', map['HH'])
    .replace('mm', map['mm'])
    .replace('ss', map['ss'])
}
