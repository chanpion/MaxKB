'use client'
import {useRouter, usePathname} from '@/i18n/navigation'
import {
  HomeOutlined,
  RobotOutlined,
  BookOutlined,
  ToolOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'
import {useTranslations} from 'next-intl'
import {useThemeStore} from '@/store'
import {HOME_PATH} from '@/lib/constants'

const menuItems = [
  {key: HOME_PATH, icon: <HomeOutlined />, labelKey: 'home'},
  {key: '/application', icon: <RobotOutlined />, labelKey: 'application'},
  {key: '/knowledge', icon: <BookOutlined />, labelKey: 'knowledge'},
  {key: '/tool', icon: <ToolOutlined />, labelKey: 'tool'},
  {key: '/model', icon: <ExperimentOutlined />, labelKey: 'model'},
]

export default function TopMenu() {
  const t = useTranslations('menu')
  const router = useRouter()
  const pathname = usePathname()
  const isDark = useThemeStore((s) => s.isDark)

  return (
    <div style={{display: 'flex', alignItems: 'center', height: '100%', gap: 2}}>
      {menuItems.map((item) => {
        const active = pathname === item.key || pathname.startsWith(item.key + '/')
        return (
          <div
            key={item.key}
            onClick={() => router.push(item.key)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 14px',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: active ? 600 : 400,
              color: active
                ? '#3370FF'
                : isDark
                  ? 'rgba(255,255,255,0.75)'
                  : '#4a4d54',
              background: active
                ? isDark
                  ? 'rgba(51,112,255,0.2)'
                  : '#ffffff'
                : 'transparent',
              boxShadow: active ? '0px 2px 4px rgba(0,0,0,0.08)' : 'none',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              if (!active) {
                e.currentTarget.style.background = isDark
                  ? 'rgba(255,255,255,0.08)'
                  : 'rgba(0,0,0,0.04)'
              }
            }}
            onMouseLeave={(e) => {
              if (!active) {
                e.currentTarget.style.background = 'transparent'
              }
            }}
          >
            <span style={{fontSize: 15}}>{item.icon}</span>
            <span className="topmenu-label">{t(item.labelKey)}</span>
          </div>
        )
      })}
    </div>
  )
}
