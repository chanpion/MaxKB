'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Button, Card, Tabs, Spin, Typography, message} from 'antd'
import {HomeOutlined, AppstoreOutlined, ArrowLeftOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {useRouter} from '@/i18n/navigation'
import {useTranslations} from 'next-intl'
import {applicationApi} from '@/lib/api/application'
import ChatPanel from '@/components/chat/ChatPanel'

export default function AppChatPage() {
  const t = useTranslations('menu')
  const router = useRouter()
  const params = useParams()
  const id = params.id as string
  const [app, setApp] = useState<any>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([applicationApi.getDetail(id), applicationApi.getAccessToken(id)])
      .then(([detail, tk]: any[]) => {
        setApp(detail?.data ?? detail)
        setToken(tk?.data?.access_token ?? tk?.access_token ?? tk ?? null)
      })
      .catch(() => message.error('加载失败'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>
  if (!app) return <Typography.Text type="secondary">智能体不存在</Typography.Text>

  const tabItems = [
    {key: 'overview', label: '概览'},
    {key: 'setting', label: '设置'},
    {key: 'access', label: '访问'},
    {key: 'chat', label: '体验'},
    {key: 'chat-log', label: '聊天日志'},
  ]

  return (
    <div>
      <div style={{display: 'flex', alignItems: 'center', marginBottom: 12, gap: 12}}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.push('/application')}>返回</Button>
        <Breadcrumb items={[
          {title: <><HomeOutlined /> {t('home')}</>},
          {title: <><AppstoreOutlined /> {t('application')}</>},
          {title: app.name},
        ]} />
      </div>
      <Tabs activeKey="chat" items={tabItems} onChange={(key) => router.push(`/application/${id}/${key}`)} style={{marginBottom: 8}} />

      <Card style={{borderRadius: 8, height: 'calc(100vh - 220px)'}} bodyStyle={{height: '100%', padding: 0}}>
        {token ? (
          <ChatPanel accessToken={token} showSource />
        ) : (
          <div style={{textAlign: 'center', paddingTop: 80}}>
            <Typography.Text type="secondary">未获取到对话令牌，请先在「访问」页生成。</Typography.Text>
          </div>
        )}
      </Card>
    </div>
  )
}
