'use client'
import {useEffect, useState} from 'react'
import {Spin} from 'antd'
import {useRouter} from '@/i18n/navigation'
import {useLoginStore, useThemeStore} from '@/store'
import Logo from '@/components/layout/Logo'
import TopMenu from '@/components/layout/TopMenu'
import UserAvatar from '@/components/layout/UserAvatar'
import {LOGIN_PATH} from '@/lib/constants'

const HEADER_HEIGHT = 56

export default function AdminLayout({children}: {children: React.ReactNode}) {
  const router = useRouter()
  const getToken = useLoginStore((s) => s.getToken)
  const isDark = useThemeStore((s) => s.isDark)
  const [checked, setChecked] = useState(false)

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

  const headerBg = isDark
    ? 'linear-gradient(90deg, #1f1f1f 0%, #2a2a2a 100%)'
    : 'linear-gradient(90deg, #ebf1ff 24.34%, #e5fbf8 56.18%, #f2ebfe 90.18%)'
  const headerBorder = isDark ? '#333' : '#e5e6e8'

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

      {/* Body: full-width content */}
      <div style={{paddingTop: HEADER_HEIGHT, minHeight: '100vh'}}>
        <div style={{padding: 24, maxWidth: 1400, margin: '0 auto'}}>
          {children}
        </div>
      </div>
    </div>
  )
}
