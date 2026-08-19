'use client'
import React, {useEffect, useState} from 'react'
import {Card, Spin, Typography, Empty} from 'antd'
import {useParams} from 'next/navigation'

export default function KnowledgeWorkflowPage() {
  const params = useParams()
  const kid = params.id as string
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(false)
  }, [kid])

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>

  return (
    <Card style={{borderRadius: 8}}>
      <Typography.Title level={5} style={{marginTop: 0}}>
        知识库工作流
      </Typography.Title>
      <Empty description="工作流编辑器即将上线" />
    </Card>
  )
}
