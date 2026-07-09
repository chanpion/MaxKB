'use client'
import {ConfigProvider, App as AntdApp, theme} from 'antd'
import {useThemeStore} from '@/store/theme'

// 全局主题与消息上下文：解决 antd 暗色模式与 SSR 样式注水
export default function Providers({children}: {children: React.ReactNode}) {
  const isDark = useThemeStore((s) => s.isDark)
  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677FF',
          borderRadius: 8,
          fontFamily:
            'PingFang SC, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        },
      }}
    >
      <AntdApp>{children}</AntdApp>
    </ConfigProvider>
  )
}
