'use client'
import React, {useEffect, useState} from 'react'
import {Table, Typography, Tag, Spin, Empty, Card} from 'antd'
import {get} from '@/lib/request'
import {useUserStore} from '@/store'
import {dateFormat} from '@/utils/time'

const ws = () => useUserStore.getState().getWorkspaceId()

/* 共享模型：后端 /model/shared 已提供 */
export default function SharedModelPage() {
  const [list, setList] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    get(`/workspace/${ws()}/model/shared`)
      .then((res: any) => setList(res.data || []))
      .catch(() => setList([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Card style={{borderRadius: 8}}>
      <Typography.Title level={4} style={{marginTop: 0, marginBottom: 16}}>共享模型</Typography.Title>
      {loading ? (
        <div style={{textAlign: 'center', padding: 60}}><Spin size="large" /></div>
      ) : list.length === 0 ? (
        <Empty description="暂无共享模型" />
      ) : (
        <Table
          dataSource={list}
          rowKey="id"
          pagination={{pageSize: 20}}
          columns={[
            {title: '名称', dataIndex: 'name', key: 'name'},
            {title: '类型', dataIndex: 'model_type', key: 'model_type', width: 120, render: (v: string) => <Tag>{v}</Tag>},
            {title: '创建时间', dataIndex: 'create_time', key: 'create_time', width: 180, render: (v: string) => dateFormat(v)},
          ]}
        />
      )}
    </Card>
  )
}
