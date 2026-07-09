'use client'
import React from 'react'
import {
  FileTextOutlined,
  GlobalOutlined,
  CommentOutlined,
  ApartmentOutlined,
} from '@ant-design/icons'

// 按知识库类型渲染图标：0 通用(文档) / 1 Web / 2 飞书 / 3 工作流
export default function KnowledgeIcon({type}: {type?: number}) {
  const map: Record<number, React.ReactNode> = {
    0: <FileTextOutlined style={{fontSize: 22, color: '#1677ff'}} />,
    1: <GlobalOutlined style={{fontSize: 22, color: '#722ed1'}} />,
    2: <CommentOutlined style={{fontSize: 22, color: '#1677ff'}} />,
    3: <ApartmentOutlined style={{fontSize: 22, color: '#13c2c2'}} />,
  }
  return <>{map[type ?? 0] || map[0]}</>
}
