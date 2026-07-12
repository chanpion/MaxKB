'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Card, Button, Typography, Spin, Tag, message, Space, Tabs} from 'antd'
import {HomeOutlined, AppstoreOutlined, ArrowLeftOutlined, KeyOutlined, ReloadOutlined, CopyOutlined, SettingOutlined, MessageOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {useRouter, usePathname} from '@/i18n/navigation'
import {useTranslations} from 'next-intl'
import {applicationApi} from '@/lib/api/application'

export default function AppAccessPage() {
  const t = useTranslations('menu')
  const router = useRouter()
  const params = useParams()
  const id = params.id as string
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState('')

  useEffect(() => {
    applicationApi.getAccessToken(id).then((res: any) => {
      setToken(res.data?.access_token || '')
    }).catch(() => {}).finally(() => setLoading(false))
  }, [id])

  const refreshToken = () => {
    applicationApi.putAccessToken(id).then((res: any) => {
      setToken(res.data?.access_token || '')
      message.success('已刷新')
    }).catch(() => {})
  }

  const tabItems = [
    {key: 'overview', label: '概览'},
    {key: 'setting', label: '设置'},
    {key: 'access', label: '访问'},
    {key: 'chat-log', label: '聊天日志'},
  ]

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>

  const chatUrl = `${window.location.origin}/chat/${token}`

  return (
    <div>
      <div style={{display: 'flex', alignItems: 'center', marginBottom: 12, gap: 12}}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.push(`/application/${id}/overview`)}>返回</Button>
        <Breadcrumb items={[
          {title: <><HomeOutlined /> {t('home')}</>},
          {title: <><AppstoreOutlined /> {t('application')}</>},
          {title: '访问配置'},
        ]} />
      </div>
      <Tabs activeKey="access" items={tabItems}
        onChange={(key) => router.push(`/application/${id}/${key}`)}
        style={{marginBottom: 8}} />
      <Card style={{borderRadius: 8}} title="访问地址">
        <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
          <Typography.Text code style={{flex: 1, padding: '8px 12px', fontSize: 13}}>
            {chatUrl || '请先刷新 Token'}
          </Typography.Text>
          <Button icon={<CopyOutlined />} onClick={() => { navigator.clipboard.writeText(chatUrl); message.success('已复制') }} />
          <Button icon={<ReloadOutlined />} onClick={refreshToken}>刷新 Token</Button>
        </div>
      </Card>
    </div>
  )
}
