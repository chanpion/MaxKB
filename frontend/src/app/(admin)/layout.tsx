'use client'
import {useEffect, useState} from 'react'
import {Layout, Menu, Avatar, Dropdown, Button, Tooltip, Spin} from 'antd'
import {
  DashboardOutlined,
  DatabaseOutlined,
  ApiOutlined,
  AppstoreOutlined,
  ToolOutlined,
  ThunderboltOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons'
import {useRouter, usePathname} from '@/i18n/navigation'
import {useLoginStore, useUserStore, useThemeStore, useCommonStore} from '@/store'
import {useTranslations} from 'next-intl'
import LocaleSwitch from '@/components/LocaleSwitch'
import ThemeToggle from '@/components/ThemeToggle'
import {LOGIN_PATH, HOME_PATH} from '@/lib/constants'

const {Header, Sider, Content} = Layout

const menuItems = [
  {key: HOME_PATH, icon: <DashboardOutlined />, labelKey: 'home'},
  {key: '/frontend/knowledge', icon: <DatabaseOutlined />, labelKey: 'knowledge'},
  {key: '/frontend/model', icon: <ApiOutlined />, labelKey: 'model'},
  {key: '/frontend/application', icon: <AppstoreOutlined />, labelKey: 'application'},
  {key: '/frontend/tool', icon: <ToolOutlined />, labelKey: 'tool'},
  {key: '/frontend/trigger', icon: <ThunderboltOutlined />, labelKey: 'trigger'},
  {key: '/frontend/system', icon: <SettingOutlined />, labelKey: 'system'},
]

export default function AdminLayout({children}: {children: React.ReactNode}) {
  const tMenu = useTranslations('menu')
  const tHeader = useTranslations('header')
  const router = useRouter()
  const pathname = usePathname()
  const getToken = useLoginStore((s) => s.getToken)
  const clearToken = useLoginStore((s) => s.clearToken)
  const userInfo = useUserStore((s) => s.userInfo)
  const isDark = useThemeStore((s) => s.isDark)
  const collapsed = useCommonStore((s) => s.collapsed)
  const toggleCollapsed = useCommonStore((s) => s.toggleCollapsed)
  const [checked, setChecked] = useState(false)

  // 客户端兜底守卫：SSR 首屏读不到 localStorage，这里用 cookie/localStorage 二次校验
  useEffect(() => {
    const tk = getToken()
    if (!tk) {
      router.replace(LOGIN_PATH)
    } else {
      setChecked(true)
    }
  }, [getToken, router])

  if (!checked) {
    return (
      <div style={{display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center'}}>
        <Spin size="large" />
      </div>
    )
  }

  const items = menuItems.map((m) => ({key: m.key, icon: m.icon, label: tMenu(m.labelKey)}))

  const onLogout = () => {
    clearToken()
    router.replace(LOGIN_PATH)
  }

  const userMenu = {
    items: [
      {key: 'profile', icon: <UserOutlined />, label: tHeader('profile')},
      {type: 'divider' as const},
      {key: 'logout', icon: <LogoutOutlined />, label: tHeader('logout'), danger: true},
    ],
    onClick: ({key}: {key: string}) => {
      if (key === 'logout') onLogout()
    },
  }

  return (
    <Layout style={{minHeight: '100vh'}}>
      <Sider
        collapsible
        collapsed={collapsed}
        trigger={null}
        width={220}
        theme={isDark ? 'dark' : 'light'}
        style={{boxShadow: '2px 0 8px rgba(0,0,0,0.06)'}}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            color: '#1677FF',
            fontWeight: 600,
            fontSize: 18,
          }}
        >
          <span style={{fontSize: 22}}>🧠</span>
          {!collapsed && <span>MaxKB</span>}
        </div>
        <Menu
          theme={isDark ? 'dark' : 'light'}
          mode="inline"
          selectedKeys={[pathname || HOME_PATH]}
          items={items}
          onClick={({key}) => router.push(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: isDark ? '#141414' : '#fff',
            padding: '0 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
          }}
        >
          <Button type="text" icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} onClick={toggleCollapsed} />
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <LocaleSwitch />
            <ThemeToggle />
            <Dropdown menu={userMenu} placement="bottomRight">
              <div style={{display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer'}}>
                <Avatar style={{backgroundColor: '#1677FF'}}>
                  {userInfo?.nickname?.[0] || userInfo?.username?.[0] || 'U'}
                </Avatar>
                <span>{userInfo?.nickname || userInfo?.username || 'User'}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        <Content
          style={{
            margin: 16,
            padding: 24,
            background: isDark ? '#1f1f1f' : '#f5f7fa',
            minHeight: 'calc(100vh - 64px - 32px)',
            borderRadius: 12,
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}
