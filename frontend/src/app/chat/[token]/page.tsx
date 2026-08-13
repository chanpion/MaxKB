'use client'
import {use} from 'react'
import {Card} from 'antd'
import ChatPanel from '@/components/chat/ChatPanel'

export default function PublicChatPage({params}: {params: Promise<{token: string}>}) {
  const {token} = use(params)
  return (
    <div style={{height: '100vh', background: '#f5f6f7'}}>
      <Card
        style={{height: '100%', borderRadius: 0, border: 'none'}}
        bodyStyle={{height: '100%', padding: 0}}
      >
        <ChatPanel accessToken={token} embedded showSource />
      </Card>
    </div>
  )
}
