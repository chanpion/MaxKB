import {EditionConst} from './data'

/**
 * 权限桩：仅 workspace 模式，所有权限恒为 true（按钮全部显示）。
 * 后续阶段可替换为真实 RBAC 判断。
 */
export function hasPermission(edition: string, _logic: 'AND' | 'OR' = 'AND'): boolean {
  void edition
  void _logic
  return true
}

export function isEE(): boolean {
  void EditionConst
  return false
}

export function isPE(): boolean {
  return false
}
