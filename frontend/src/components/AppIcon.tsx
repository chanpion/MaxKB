'use client'
import React from 'react'
import * as Icons from '@ant-design/icons'

const iconMap: Record<string, any> = {
  'app-more': Icons.MoreOutlined,
  'app-add-outlined': Icons.PlusOutlined,
  'app-edit': Icons.EditOutlined,
  'app-delete': Icons.DeleteOutlined,
  'app-warning': Icons.WarningOutlined,
  'app-folder': Icons.FolderOutlined,
  'app-sync': Icons.SyncOutlined,
  'app-vectorization': Icons.ThunderboltOutlined,
  'app-generate-question': Icons.QuestionOutlined,
  'app-lock': Icons.LockOutlined,
  'app-resource-authorization': Icons.SafetyCertificateOutlined,
  'app-resource-mapping': Icons.NodeIndexOutlined,
  'app-migrate': Icons.SwapOutlined,
  'app-setting': Icons.SettingOutlined,
  'app-export': Icons.ExportOutlined,
  'app-shared-active': Icons.ShareAltOutlined,
  'app-all-menu-active': Icons.AppstoreOutlined,
  'app-batch-delete': Icons.DeleteOutlined,
  'app-template-center': Icons.AppstoreOutlined,
}

export interface AppIconProps extends React.HTMLAttributes<HTMLSpanElement> {
  iconName: string
}

export default function AppIcon({iconName, ...rest}: AppIconProps) {
  if (typeof iconName === 'string' && iconName.trim().startsWith('<svg')) {
    return <span dangerouslySetInnerHTML={{__html: iconName}} {...rest} />
  }
  const Cmp = iconMap[iconName]
  if (Cmp) return <Cmp {...rest} />
  return <span {...rest} />
}

// 供应商/知识库原始 SVG 图标渲染（后端返回 icon 字段为 svg 字符串）
export function RawIcon({html, style}: {html?: string; style?: React.CSSProperties}) {
  if (!html) return null
  return (
    <span
      dangerouslySetInnerHTML={{__html: html}}
      style={{display: 'inline-block', height: 20, width: 20, ...style}}
    />
  )
}
