'use client'
import React, {useEffect, useState} from 'react'
import {Card, Table, Typography} from 'antd'
import {useParams} from 'next/navigation'
import {get} from '@/lib/request'
import {useUserStore} from '@/store'
import {dateFormat} from '@/utils/time'

function ws() { return useUserStore.getState().getWorkspaceId() }

export default function ChatLogPage() {
  const params = useParams()
  const id = params.id as string
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    get(`/workspace/${ws()}/application/${id}/chat/1/20`).then((res: any) => {
      setLogs(res.data?.records || res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [id])

  const columns = [
    {title: '用户', dataIndex: 'abstract', key: 'abstract', ellipsis: true},
    {title: '消息数', dataIndex: 'chat_record_count', key: 'chat_record_count', width: 80},
    {title: '时间', dataIndex: 'update_time', key: 'update_time', width: 180,
      render: (t: string) => dateFormat(t)},
  ]

  return (
    <Card style={{borderRadius: 8}}>
      <Typography.Title level={4} style={{marginTop: 0}}>聊天日志</Typography.Title>
      <Table dataSource={logs} columns={columns} rowKey="id" loading={loading}
        pagination={{pageSize: 20}} size="middle" />
    </Card>
  )
}
