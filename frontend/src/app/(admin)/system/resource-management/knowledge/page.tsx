'use client'
import React from 'react'
import {Card, Typography, Empty} from 'antd'

/* 资源管理-知识库：后端暂未提供跨工作区资源列举端点。占位页待后端实现后填充。 */
export default function ResourceKnowledgePage() {
  return (
    <Card style={{borderRadius: 8}}>
      <Typography.Title level={4} style={{marginTop: 0, marginBottom: 16}}>资源管理 · 知识库</Typography.Title>
      <Empty description="后端接口待实现（重构后端尚未提供跨工作区资源管理端点）" style={{marginTop: 60}} />
    </Card>
  )
}
