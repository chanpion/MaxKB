'use client'
import React from 'react'

// 知识库详情页：导航由全局 Sidebar 承担，此处直接渲染内容
export default function KnowledgeDetailLayout({children}: {children: React.ReactNode}) {
  return <>{children}</>
}
