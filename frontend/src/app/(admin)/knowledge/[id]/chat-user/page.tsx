'use client'
import React from 'react'
import {Breadcrumb, Typography, Empty, Card} from 'antd'
import {HomeOutlined, FileTextOutlined} from '@ant-design/icons'

export default function KnowledgeChatUserPage() {
  return (
    <div>
      <Breadcrumb style={{marginBottom: 12}} items={[
        {title: <><HomeOutlined /> 首页</>},
        {title: <><FileTextOutlined /> 知识库详情</>},
      ]} />
      <Typography.Title level={5} style={{marginBottom: 16}}>对话用户</Typography.Title>
      <Card style={{borderRadius: 8}}>
        <Empty
          description="当前后端版本未提供知识库对话用户授权接口，该功能暂不可用。"
        />
      </Card>
    </div>
  )
}
