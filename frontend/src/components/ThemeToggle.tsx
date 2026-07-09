'use client'
import {Button} from 'antd'
import {MoonOutlined, SunOutlined} from '@ant-design/icons'
import {useThemeStore} from '@/store'

export default function ThemeToggle() {
  const isDark = useThemeStore((s) => s.isDark)
  const toggle = useThemeStore((s) => s.toggle)
  return (
    <Button type="text" icon={isDark ? <SunOutlined /> : <MoonOutlined />} onClick={toggle} />
  )
}
