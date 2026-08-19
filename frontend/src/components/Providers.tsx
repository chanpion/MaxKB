'use client'
import {ConfigProvider, App as AntdApp, theme} from 'antd'
import {useThemeStore} from '@/store/theme'

const COLOR_PRIMARY = '#3370FF'
const COLOR_BG_LAYOUT_LIGHT = '#f5f6f7'
const COLOR_BG_LAYOUT_DARK = '#141414'

export default function Providers({children}: {children: React.ReactNode}) {
  const isDark = useThemeStore((s) => s.isDark)
  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: COLOR_PRIMARY,
          colorSuccess: '#34c724',
          colorWarning: '#ff8800',
          colorError: '#f54a45',
          colorInfo: COLOR_PRIMARY,
          colorLink: COLOR_PRIMARY,
          colorBgLayout: isDark ? COLOR_BG_LAYOUT_DARK : COLOR_BG_LAYOUT_LIGHT,
          colorTextBase: isDark ? 'rgba(255,255,255,0.9)' : '#1f2329',
          colorText: isDark ? 'rgba(255,255,255,0.9)' : '#1f2329',
          colorTextSecondary: isDark ? 'rgba(255,255,255,0.65)' : '#646a73',
          colorBorder: isDark ? '#303030' : '#dee0e3',
          colorBorderSecondary: isDark ? '#262626' : '#eef0f1',
          colorFillTertiary: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(31,35,41,0.04)',
          colorFillQuaternary: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(31,35,41,0.02)',
          borderRadius: 6,
          borderRadiusLG: 8,
          borderRadiusSM: 4,
          fontFamily:
            'PingFang SC, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
          fontSize: 14,
        },
        components: {
          Table: {
            headerBg: isDark ? '#1d1d1d' : '#f5f6f7',
            headerColor: isDark ? 'rgba(255,255,255,0.9)' : '#1f2329',
            headerSplitColor: isDark ? '#303030' : '#dee0e3',
            borderColor: isDark ? '#303030' : '#dee0e3',
            rowHoverBg: isDark ? 'rgba(255,255,255,0.06)' : '#eff0f1',
            cellPaddingBlock: 10,
            cellPaddingInline: 16,
          },
          Card: {
            borderRadiusLG: 8,
            colorBorderSecondary: isDark ? '#303030' : '#eef0f1',
          },
          Button: {
            borderRadius: 6,
            borderRadiusSM: 6,
            controlHeight: 32,
          },
          Input: {
            controlHeight: 32,
            borderRadius: 6,
          },
          Select: {
            controlHeight: 32,
            borderRadius: 6,
          },
          Menu: {
            itemHeight: 45,
            itemBorderRadius: 4,
            itemMarginInline: 8,
            itemSelectedBg: isDark ? 'rgba(51,112,255,0.2)' : '#eef4ff',
            itemSelectedColor: COLOR_PRIMARY,
            itemActiveBg: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(31,35,41,0.04)',
            itemHoverColor: isDark ? 'rgba(255,255,255,0.9)' : '#1f2329',
          },
          Modal: {
            borderRadiusLG: 8,
          },
          Tabs: {
            inkBarColor: COLOR_PRIMARY,
            itemSelectedColor: COLOR_PRIMARY,
            itemHoverColor: COLOR_PRIMARY,
          },
          Pagination: {
            itemActiveBg: COLOR_PRIMARY,
          },
          Switch: {
            colorPrimary: COLOR_PRIMARY,
          },
          Checkbox: {
            colorPrimary: COLOR_PRIMARY,
          },
          Radio: {
            colorPrimary: COLOR_PRIMARY,
          },
          Slider: {
            colorPrimary: COLOR_PRIMARY,
          },
          Progress: {
            defaultColor: COLOR_PRIMARY,
          },
          DatePicker: {
            controlHeight: 32,
            borderRadius: 6,
          },
          Cascader: {
            controlHeight: 32,
            borderRadius: 6,
          },
          Tree: {
            directoryNodeSelectedBg: COLOR_PRIMARY,
            directoryNodeSelectedColor: '#fff',
          },
        },
      }}
    >
      <AntdApp>{children}</AntdApp>
    </ConfigProvider>
  )
}
