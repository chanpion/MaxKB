'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Table, Button, Typography, Tag, Space, Tabs, Spin} from 'antd'
import {HomeOutlined, AppstoreOutlined, ArrowLeftOutlined, MessageOutlined, SettingOutlined, KeyOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {useRouter, usePathname} from '@/i18n/navigation'
import {useTranslations} from 'next-intl'
import {get} from '@/lib/request'
import {useUserStore} from '@/store'
import {dateFormat} from '@/utils/time'

function ws() { return useUserStore.getState().getWorkspaceId() }

export default function ChatLogPage() {
  const t = useTranslations('menu')
  const router = useRouter()
  const params = useParams()
  const id = params.id as string
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    get(`/workspace/${ws()}/application/${id}/chat/1/20`).then((res: any) => {
      setLogs(res.data?.records || res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [id])

  const tabItems = [
    {key: 'overview', label: '概览'},
    {key: 'setting', label: '设置'},
    {key: 'access', label: '访问'},
    {key: 'chat-log', label: '聊天日志'},
  ]

  const columns = [
    {title: '用户', dataIndex: 'abstract', key: 'abstract', ellipsis: true},
    {title: '消息数', dataIndex: 'chat_record_count', key: 'chat_record_count', width: 80},
    {title: '时间', dataIndex: 'update_time', key: 'update_time', width: 180,
      render: (t: string) => dateFormat(t)},
  ]

  return (
    <div>
      <div style={{display: 'flex', alignItems: 'center', marginBottom: 12, gap: 12}}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.push(`/application/${id}/overview`)}>返回</Button>
        <Breadcrumb items={[
          {title: <><HomeOutlined /> {t('home')}</>},
          {title: <><AppstoreOutlined /> {t('application')}</>},
          {title: '聊天日志'},
        ]} />
      </div>
      <Tabs activeKey="chat-log" items={tabItems}
        onChange={(key) => router.push(`/application/${id}/${key}`)}
        style={{marginBottom: 8}} />
      <Table dataSource={logs} columns={columns} rowKey="id" loading={loading}
        pagination={{pageSize: 20}} size="middle" />
    </div>
  )
}
