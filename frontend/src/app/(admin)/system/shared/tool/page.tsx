'use client'
import React from 'react'
import {Breadcrumb, Typography, Empty} from 'antd'
import {HomeOutlined, SettingOutlined, ToolOutlined} from '@ant-design/icons'
import {useTranslations} from 'next-intl'

/* 共享工具：后端暂未提供 /tool/shared 端点。占位页待后端实现后填充。 */
export default function SharedToolPage() {
  const t = useTranslations('menu')
  return (
    <div>
      <Breadcrumb style={{marginBottom: 16}} items={[
        {title: <><HomeOutlined /> {t('home')}</>},
        {title: <><SettingOutlined /> 系统管理</>},
        {title: '共享工具'},
      ]} />
      <Typography.Title level={4} style={{marginBottom: 16}}>共享工具</Typography.Title>
      <Empty description="后端接口待实现（重构后端尚未提供 /tool/shared 端点）" style={{marginTop: 60}} />
    </div>
  )
}
