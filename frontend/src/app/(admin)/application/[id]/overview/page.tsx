'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Descriptions, Button, Card, Statistic, Row, Col, Tag, Spin, Typography, message, Space, Tabs} from 'antd'
import {HomeOutlined, AppstoreOutlined, ArrowLeftOutlined, CopyOutlined, CheckCircleOutlined, SettingOutlined, KeyOutlined, MessageOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {useRouter, usePathname} from '@/i18n/navigation'
import {useTranslations} from 'next-intl'
import {applicationApi} from '@/lib/api/application'

export default function AppOverviewPage() {
  const t = useTranslations('menu')
  const router = useRouter()
  const params = useParams()
  const id = params.id as string
  const [app, setApp] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    applicationApi.getDetail(id).then((res: any) => { setApp(res.data) }).catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>
  if (!app) return <Typography.Text type="secondary">智能体不存在</Typography.Text>

  const tabItems = [
    {key: 'overview', label: '概览'},
    {key: 'setting', label: '设置'},
    {key: 'access', label: '访问'},
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
      <Tabs activeKey="overview" items={tabItems}
        onChange={(key) => router.push(`/application/${id}/${key}`)}
        style={{marginBottom: 8}} />

      <Card style={{borderRadius: 8, marginBottom: 16}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
          <div>
            <Typography.Title level={4} style={{margin: 0}}>{app.name}</Typography.Title>
            <Typography.Text type="secondary">{app.desc || '暂无描述'}</Typography.Text>
          </div>
          <Tag color="blue">{app.model_name || '未配置模型'}</Tag>
        </div>
      </Card>

      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Card style={{borderRadius: 8}}><Statistic title="对话数" value={app.chat_record_count || 0} suffix="次" /></Card>
        </Col>
        <Col span={8}>
          <Card style={{borderRadius: 8}}><Statistic title="用户数" value={app.chat_user_count || 0} suffix="人" /></Card>
        </Col>
        <Col span={8}>
          <Card style={{borderRadius: 8}}><Statistic title="Tokens" value={(app.total_tokens || 0).toLocaleString()} suffix="tokens" /></Card>
        </Col>
      </Row>

      <Card style={{borderRadius: 8, marginTop: 16}} title="操作">
        <Space>
          <Button onClick={() => router.push(`/application/${id}/setting`)}>设置</Button>
          <Button onClick={() => router.push(`/application/${id}/access`)}>访问</Button>
        </Space>
      </Card>
    </div>
  )
}
