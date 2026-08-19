'use client'
import React, {useEffect, useMemo, useState} from 'react'
import {Menu} from 'antd'
import {
  AppstoreOutlined,
  SettingOutlined,
  KeyOutlined,
  MessageOutlined,
  FileTextOutlined,
  NodeIndexOutlined,
  QuestionCircleOutlined,
  BookOutlined,
  ExperimentOutlined,
  UserOutlined,
  TeamOutlined,
  SafetyCertificateOutlined,
  DatabaseOutlined,
  ShareAltOutlined,
  MenuOutlined,
} from '@ant-design/icons'
import {useThemeStore} from '@/store'
import type {NavItem} from '@/config/menu'

const ICON_MAP: Record<string, React.ReactNode> = {
  appstore: <AppstoreOutlined />,
  setting: <SettingOutlined />,
  key: <KeyOutlined />,
  message: <MessageOutlined />,
  'file-text': <FileTextOutlined />,
  node: <NodeIndexOutlined />,
  question: <QuestionCircleOutlined />,
  book: <BookOutlined />,
  experiment: <ExperimentOutlined />,
  user: <UserOutlined />,
  team: <TeamOutlined />,
  safety: <SafetyCertificateOutlined />,
  database: <DatabaseOutlined />,
  share: <ShareAltOutlined />,
}

function toAntdItems(items: NavItem[]): any[] {
  return items.map((item) => {
    const children = item.children ? toAntdItems(item.children) : undefined
    return {
      key: item.key,
      icon: item.icon ? ICON_MAP[item.icon] : undefined,
      label: item.label,
      children,
    }
  })
}

interface SidebarProps {
  items: NavItem[]
  selectedKey: string
  onSelect: (key: string) => void
  /** 系统菜单需展开全部子级，详情页无需 */
  expandChildren?: boolean
}

export default function Sidebar({items, selectedKey, onSelect, expandChildren = false}: SidebarProps) {
  const isDark = useThemeStore((s) => s.isDark)
  const [openKeys, setOpenKeys] = useState<string[]>([])

  // 系统菜单：根据当前选中项自动展开其所属父级分组
  useEffect(() => {
    if (!expandChildren) return
    for (const item of items) {
      if (item.children?.some((c) => selectedKey === c.key || selectedKey.startsWith(c.key + '/'))) {
        setOpenKeys((prev) => (prev.includes(item.key) ? prev : [...prev, item.key]))
        return
      }
    }
  }, [items, selectedKey, expandChildren])

  const borderColor = isDark ? '#303030' : '#dee0e3'

  return (
    <div
      style={{
        width: 240,
        flexShrink: 0,
        height: '100%',
        background: isDark ? '#1f1f1f' : '#ffffff',
        borderRight: `1px solid ${borderColor}`,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <div style={{flex: 1, overflow: 'auto', padding: '8px 0'}}>
        <Menu
          mode="inline"
          inlineCollapsed={false}
          selectedKeys={[selectedKey]}
          openKeys={expandChildren ? openKeys : undefined}
          onOpenChange={expandChildren ? setOpenKeys : undefined}
          items={toAntdItems(items)}
          onClick={({key}) => onSelect(key)}
          style={{border: 'none', background: 'transparent'}}
        />
      </div>
    </div>
  )
}
