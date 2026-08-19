'use client'
import React, {useEffect, useState} from 'react'
import {Card, Table, Typography, Select, Space, Spin} from 'antd'
import {systemApi} from '@/lib/api/system'
import {dateFormat} from '@/utils/time'

export default function OperateLogPage() {
  const [list, setList] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [type, setType] = useState<string>('')

  useEffect(() => {
    const params: any = {}
    if (type) params.type = type
    systemApi.getOperateLog(1, params).then((res: any) => {
      setList(res.data?.records || res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [type])

  return (
    <Card style={{borderRadius: 8}}>
      <Typography.Title level={4} style={{marginTop: 0, marginBottom: 16}}>操作日志</Typography.Title>
      <Space style={{marginBottom: 16}}>
        <Select value={type} onChange={setType} style={{width: 120}} allowClear placeholder="操作类型"
          options={[{value: '', label: '全部'}, {value: 'CREATE', label: '创建'}, {value: 'UPDATE', label: '修改'}, {value: 'DELETE', label: '删除'}]} />
      </Space>
      <Table dataSource={list} rowKey="id" loading={loading} pagination={{pageSize: 20}} columns={[
        {title: '操作人', dataIndex: 'username', key: 'username', width: 120},
        {title: '操作类型', dataIndex: 'type', key: 'type', width: 80},
        {title: '操作内容', dataIndex: 'detail', key: 'detail', ellipsis: true},
        {title: '时间', dataIndex: 'create_time', key: 'create_time', width: 180, render: (t: string) => dateFormat(t)},
      ]} />
    </Card>
  )
}
