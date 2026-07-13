'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Button, Card, Spin, Typography, Tabs, Empty} from 'antd'
import {HomeOutlined, FileTextOutlined, QuestionCircleOutlined, BookOutlined, ExperimentOutlined, SettingOutlined, NodeIndexOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {useRouter} from '@/i18n/navigation'
import {useTranslations} from 'next-intl'
import knowledgeApi from '@/lib/api/knowledge/knowledge'

export default function KnowledgeWorkflowPage() {
  const t = useTranslations()
  const router = useRouter()
  const params = useParams()
  const kid = params.id as string
  const [loading, setLoading] = useState(true)
  const [detail, setDetail] = useState<any>({})

  useEffect(() => {
    knowledgeApi.getKnowledgeDetail(kid).then((res: any) => {
      setDetail(res.data || {})
    }).catch(() => {}).finally(() => setLoading(false))
  }, [kid])

  const tabItems = [
    {key: 'document', label: <><FileTextOutlined /> 文档</>},
    {key: 'problem', label: <><QuestionCircleOutlined /> 问题</>},
    {key: 'termbase', label: <><BookOutlined /> 术语库</>},
    {key: 'hit-test', label: <><ExperimentOutlined /> 命中测试</>},
    {key: 'workflow', label: <><NodeIndexOutlined /> 工作流</>},
    {key: 'setting', label: <><SettingOutlined /> 设置</>},
  ]

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>

  return (
    <div>
      <Breadcrumb style={{marginBottom: 12}} items={[
        {title: <><HomeOutlined /> {t('menu.home')}</>},
        {title: <><FileTextOutlined /> {detail.name || t('menu.knowledge')}</>},
      ]} />
      <Tabs activeKey="workflow" items={tabItems}
        onChange={(key) => router.push(`/knowledge/${kid}/${key}`)}
        style={{marginBottom: 8}} />
      <Card style={{borderRadius: 8}}>
        <Typography.Title level={5} style={{marginTop: 0}}>
          知识库工作流
        </Typography.Title>
        <Empty description="工作流编辑器即将上线" />
      </Card>
    </div>
  )
}
