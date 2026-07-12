'use client'
import {ConfigProvider, App as AntdApp, theme} from 'antd'
import {useThemeStore} from '@/store/theme'

export default function Providers({children}: {children: React.ReactNode}) {
  const isDark = useThemeStore((s) => s.isDark)
  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677FF',
          borderRadius: 8,
          borderRadiusLG: 12,
          fontFamily:
            'PingFang SC, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
          colorBgLayout: isDark ? '#141414' : '#f5f6f7',
          colorTextSecondary: isDark ? 'rgba(255,255,255,0.65)' : '#646a73',
          colorBorder: isDark ? '#303030' : '#e5e6e8',
        },
      }}
    >
      <AntdApp>{children}</AntdApp>
    </ConfigProvider>
  )
}
