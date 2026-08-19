'use client'
import React from 'react'
import {Card, Typography, Empty} from 'antd'

/* 共享工具：后端暂未提供 /tool/shared 端点。占位页待后端实现后填充。 */
export default function SharedToolPage() {
  return (
    <Card style={{borderRadius: 8}}>
      <Typography.Title level={4} style={{marginTop: 0, marginBottom: 16}}>共享工具</Typography.Title>
      <Empty description="后端接口待实现（重构后端尚未提供 /tool/shared 端点）" style={{marginTop: 60}} />
    </Card>
  )
}
