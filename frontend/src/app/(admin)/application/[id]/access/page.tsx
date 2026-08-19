'use client'
import React, {useEffect, useState} from 'react'
import {Card, Button, Typography, Spin, message, Space} from 'antd'
import {ReloadOutlined, CopyOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {applicationApi} from '@/lib/api/application'

export default function AppAccessPage() {
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

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>

  const chatUrl = `${window.location.origin}/chat/${token}`

  return (
    <Card style={{borderRadius: 8}} title="访问地址">
      <Space direction="vertical" size={16} style={{width: '100%'}}>
        <Typography.Paragraph type="secondary" style={{margin: 0}}>
          将下方链接分享给用户，即可打开该智能体的对话页面。
        </Typography.Paragraph>
        <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
          <Typography.Text code style={{flex: 1, padding: '8px 12px', fontSize: 13}}>
            {chatUrl || '请先刷新 Token'}
          </Typography.Text>
          <Button icon={<CopyOutlined />} onClick={() => { navigator.clipboard.writeText(chatUrl); message.success('已复制') }} />
          <Button icon={<ReloadOutlined />} onClick={refreshToken}>刷新 Token</Button>
        </div>
      </Space>
    </Card>
  )
}
