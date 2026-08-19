'use client'
import {useEffect, useState} from 'react'
import {Spin} from 'antd'
import {useRouter, usePathname} from '@/i18n/navigation'
import {useLoginStore, useThemeStore} from '@/store'
import Logo from '@/components/layout/Logo'
import TopMenu from '@/components/layout/TopMenu'
import UserAvatar from '@/components/layout/UserAvatar'
import Sidebar from '@/components/layout/Sidebar'
import AppBreadcrumb from '@/components/layout/AppBreadcrumb'
import {appDetailMenu, knowledgeDetailMenu, systemMenu} from '@/config/menu'
import {LOGIN_PATH} from '@/lib/constants'

const HEADER_HEIGHT = 56

// 布局模式：main（无 Sidebar，工作区主页）/ detail（详情页 + Sidebar + 面包屑）/ system（系统管理 + Sidebar）
type LayoutMode = 'main' | 'detail' | 'system'

function resolveLayout(pathname: string): LayoutMode {
  const seg = pathname.split('/').filter(Boolean)
  if (seg[0] === 'system') return 'system'
  if (seg[0] === 'application' && seg[1]) return 'detail'
  if (seg[0] === 'knowledge' && seg[1]) return 'detail'
  return 'main'
}

export default function AdminLayout({children}: {children: React.ReactNode}) {
  const router = useRouter()
  const pathname = usePathname()
  const getToken = useLoginStore((s) => s.getToken)
  const clearToken = useLoginStore((s) => s.clearToken)
  const isDark = useThemeStore((s) => s.isDark)
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    const tk = getToken()
    if (!tk) {
      // localStorage 无 token 但 cookie 可能残留，先清除 cookie 再跳登录，
      // 否则 middleware 读取残留 cookie 会把 /login 又弹回 /home 造成死循环
      clearToken()
      router.replace(LOGIN_PATH)
    } else {
      setChecked(true)
    }
  }, [getToken, clearToken, router])

  if (!checked) {
    return (
      <div style={{display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center'}}>
        <Spin size="large" />
      </div>
    )
  }

  const mode = resolveLayout(pathname)
  const seg = pathname.split('/').filter(Boolean)

  // 计算 Sidebar 选中项
  let sidebarItems = null
  let selectedKey = ''
  let breadcrumb: React.ReactNode = null
  if (mode === 'system') {
    sidebarItems = systemMenu
    selectedKey = pathname
  } else if (mode === 'detail') {
    if (seg[0] === 'application') {
      sidebarItems = appDetailMenu
      selectedKey = seg[2] || 'overview'
      breadcrumb = <AppBreadcrumb type="application" id={seg[1]} backTo="/application" />
    } else {
      sidebarItems = knowledgeDetailMenu
      selectedKey = seg[2] || 'document'
      breadcrumb = <AppBreadcrumb type="knowledge" id={seg[1]} backTo="/knowledge" />
    }
  }

  const headerBg = isDark
    ? 'linear-gradient(90deg, #1f1f1f 0%, #2a2a2a 100%)'
    : 'linear-gradient(90deg, #ebf1ff 24.34%, #e5fbf8 56.18%, #f2ebfe 90.18%)'
  const headerBorder = isDark ? '#333' : '#e5e6e8'

  const handleMenuSelect = (key: string) => {
    if (mode === 'system') {
      router.push(key)
    } else if (mode === 'detail') {
      const base = `/${seg[0]}/${seg[1]}`
      router.push(`${base}/${key}`)
    }
  }

  return (
    <div style={{minHeight: '100vh', background: isDark ? '#141414' : '#f5f6f7'}}>
      {/* Fixed Header: three-column layout */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          height: HEADER_HEIGHT,
          background: headerBg,
          borderBottom: `1px solid ${headerBorder}`,
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          padding: '0 20px',
          boxSizing: 'border-box',
        }}
      >
        <div style={{flex: '0 0 200px', display: 'flex', alignItems: 'center', gap: 8, marginTop: 4}}>
          <Logo />
        </div>

        <div style={{flex: 1, display: 'flex', justifyContent: 'center', height: '100%', overflow: 'hidden'}}>
          <TopMenu />
        </div>

        <div style={{flex: '0 0 200px', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 8}}>
          <UserAvatar />
        </div>
      </div>

      {/* Body */}
      <div style={{paddingTop: HEADER_HEIGHT, minHeight: '100vh'}}>
        {mode === 'main' ? (
          <div style={{padding: 24}}>{children}</div>
        ) : (
          <div style={{display: 'flex', alignItems: 'stretch', height: 'calc(100vh - 56px)'}}>
            {sidebarItems && (
              <Sidebar
                items={sidebarItems}
                selectedKey={selectedKey}
                onSelect={handleMenuSelect}
                expandChildren={mode === 'system'}
              />
            )}
            <div style={{flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column'}}>
              {mode === 'detail' && breadcrumb}
              <div style={{flex: 1, overflow: 'auto', padding: 24, boxSizing: 'border-box'}}>
                {children}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
