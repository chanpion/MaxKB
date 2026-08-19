'use client'
import React from 'react'
import {Typography, Empty, Card} from 'antd'

export default function KnowledgeChatUserPage() {
  return (
    <Card style={{borderRadius: 8}}>
      <Typography.Title level={5} style={{marginTop: 0, marginBottom: 16}}>对话用户</Typography.Title>
      <Empty
        description="当前后端版本未提供知识库对话用户授权接口，该功能暂不可用。"
      />
    </Card>
  )
}
