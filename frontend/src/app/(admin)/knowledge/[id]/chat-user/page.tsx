'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Table, Typography, Tag, Tabs, Spin} from 'antd'
import {HomeOutlined, FileTextOutlined, UserOutlined, QuestionCircleOutlined, BookOutlined, ExperimentOutlined, SettingOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {useRouter} from '@/i18n/navigation'
import {get} from '@/lib/request'
import {useUserStore} from '@/store'
import {dateFormat} from '@/utils/time'

function ws() { return useUserStore.getState().getWorkspaceId() }

const tabItems = [
  {key: 'document', label: <><FileTextOutlined /> 文档</>},
  {key: 'problem', label: <><QuestionCircleOutlined /> 问题</>},
  {key: 'termbase', label: <><BookOutlined /> 术语库</>},
  {key: 'hit-test', label: <><ExperimentOutlined /> 命中测试</>},
  {key: 'chat-user', label: <><UserOutlined /> 对话用户</>},
  {key: 'setting', label: <><SettingOutlined /> 设置</>},
]

export default function KnowledgeChatUserPage() {
  const router = useRouter()
  const params = useParams()
  const kid = params.id as string
  const [list, setList] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    get(`/workspace/${ws()}/knowledge/${kid}/chat_user`).then((res: any) => {
      setList(res.data?.records || res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [kid])

  return (
    <div>
      <Breadcrumb style={{marginBottom: 12}} items={[
        {title: <><HomeOutlined /> 首页</>},
        {title: <><FileTextOutlined /> 知识库详情</>},
      ]} />
      <Tabs activeKey="chat-user" items={tabItems}
        onChange={(key) => router.push(`/knowledge/${kid}/${key}`)}
        style={{marginBottom: 8}} />
      <Typography.Title level={5} style={{marginBottom: 16}}>对话用户</Typography.Title>
      <Table dataSource={list} rowKey="id" loading={loading} pagination={{pageSize: 20}} columns={[
        {title: '用户', dataIndex: 'username', key: 'username'},
        {title: '对话数', dataIndex: 'chat_count', key: 'chat_count', width: 100},
        {title: '最后对话', dataIndex: 'last_chat_time', key: 'last_chat_time', width: 180, render: (t: string) => t ? dateFormat(t) : '-'},
      ]} />
    </div>
  )
}
