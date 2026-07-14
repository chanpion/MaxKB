'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Button, Card, Spin, Typography, Empty} from 'antd'
import {HomeOutlined, FileTextOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {useTranslations} from 'next-intl'
import knowledgeApi from '@/lib/api/knowledge/knowledge'

export default function KnowledgeWorkflowPage() {
  const t = useTranslations()
  const params = useParams()
  const kid = params.id as string
  const [loading, setLoading] = useState(true)
  const [detail, setDetail] = useState<any>({})

  useEffect(() => {
    knowledgeApi.getKnowledgeDetail(kid).then((res: any) => {
      setDetail(res.data || {})
    }).catch(() => {}).finally(() => setLoading(false))
  }, [kid])

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>

  return (
    <div>
      <Breadcrumb style={{marginBottom: 12}} items={[
        {title: <><HomeOutlined /> {t('menu.home')}</>},
        {title: <><FileTextOutlined /> {detail.name || t('menu.knowledge')}</>},
      ]} />
      <Card style={{borderRadius: 8}}>
        <Typography.Title level={5} style={{marginTop: 0}}>
          知识库工作流
        </Typography.Title>
        <Empty description="工作流编辑器即将上线" />
      </Card>
    </div>
  )
}
