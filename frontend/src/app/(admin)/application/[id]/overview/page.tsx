'use client'
import React, {useEffect, useState} from 'react'
import {Button, Card, Statistic, Row, Col, Tag, Spin, Typography, Space} from 'antd'
import {useParams} from 'next/navigation'
import {useRouter} from '@/i18n/navigation'
import {applicationApi} from '@/lib/api/application'

export default function AppOverviewPage() {
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

  return (
    <div>
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
