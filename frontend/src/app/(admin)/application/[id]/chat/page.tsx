'use client'
import React, {useEffect, useState} from 'react'
import {Card, Spin, Typography, message} from 'antd'
import {useParams} from 'next/navigation'
import {applicationApi} from '@/lib/api/application'
import ChatPanel from '@/components/chat/ChatPanel'

export default function AppChatPage() {
  const params = useParams()
  const id = params.id as string
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    applicationApi.getAccessToken(id)
      .then((tk: any) => {
        setToken(tk?.data?.access_token ?? tk?.access_token ?? tk ?? null)
      })
      .catch(() => message.error('加载失败'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>

  return (
    <Card style={{borderRadius: 8, height: 'calc(100vh - 220px)'}} styles={{body: {height: '100%', padding: 0}}}>
      {token ? (
        <ChatPanel accessToken={token} showSource />
      ) : (
        <div style={{textAlign: 'center', paddingTop: 80}}>
          <Typography.Text type="secondary">未获取到对话令牌，请先在「访问」页生成。</Typography.Text>
        </div>
      )}
    </Card>
  )
}
