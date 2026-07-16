'use client'
import React from 'react'
import {Breadcrumb, Typography, Empty} from 'antd'
import {HomeOutlined, SettingOutlined, MessageOutlined} from '@ant-design/icons'
import {useTranslations} from 'next-intl'

/* 对话用户：后端 chat.py 仅提供匿名/组件级端点，尚缺"对话用户管理"端点。占位页待后端实现后填充。 */
export default function ChatUserManagePage() {
  const t = useTranslations('menu')
  return (
    <div>
      <Breadcrumb style={{marginBottom: 16}} items={[
        {title: <><HomeOutlined /> {t('home')}</>},
        {title: <><SettingOutlined /> 系统管理</>},
        {title: '对话用户'},
      ]} />
      <Typography.Title level={4} style={{marginBottom: 16}}>对话用户</Typography.Title>
      <Empty description="后端接口待实现（重构后端尚未提供对话用户管理端点）" style={{marginTop: 60}} />
    </div>
  )
}
