'use client'
import React from 'react'
import {Breadcrumb, Typography, Empty} from 'antd'
import {HomeOutlined, SettingOutlined, DatabaseOutlined} from '@ant-design/icons'
import {useTranslations} from 'next-intl'

/* 资源管理-知识库：后端暂未提供跨工作区资源列举端点。占位页待后端实现后填充。 */
export default function ResourceKnowledgePage() {
  const t = useTranslations('menu')
  return (
    <div>
      <Breadcrumb style={{marginBottom: 16}} items={[
        {title: <><HomeOutlined /> {t('home')}</>},
        {title: <><SettingOutlined /> 系统管理</>},
        {title: '资源管理 / 知识库'},
      ]} />
      <Typography.Title level={4} style={{marginBottom: 16}}>资源管理 · 知识库</Typography.Title>
      <Empty description="后端接口待实现（重构后端尚未提供跨工作区资源管理端点）" style={{marginTop: 60}} />
    </div>
  )
}
