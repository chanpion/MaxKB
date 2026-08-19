'use client'
import React from 'react'
import {Card, Typography, Empty} from 'antd'

/* 对话认证：后端暂未提供对话用户认证管理端点。占位页待后端实现后填充。 */
export default function ChatAuthenticationPage() {
  return (
    <Card style={{borderRadius: 8}}>
      <Typography.Title level={4} style={{marginTop: 0, marginBottom: 16}}>对话认证</Typography.Title>
      <Empty description="后端接口待实现（重构后端尚未提供对话用户认证管理端点）" style={{marginTop: 60}} />
    </Card>
  )
}
