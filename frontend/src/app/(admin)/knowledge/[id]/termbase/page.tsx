'use client'
import React, {useEffect, useState} from 'react'
import {Card, Table, Button, Typography, Input, Space, message, Popconfirm, Modal, Tag} from 'antd'
import {PlusOutlined, DeleteOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {termbaseApi} from '@/lib/api/knowledge/termbase'
import {dateFormat} from '@/utils/time'

export default function TermbasePage() {
  const params = useParams()
  const kid = params.id as string
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [newTerm, setNewTerm] = useState('')

  const load = () => {
    setLoading(true)
    const p: any = {}
    if (search) p.content = search
    termbaseApi.getList(kid, p).then((res: any) => {
      setData(res.data?.records || res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load() }, [kid])

  const handleCreate = () => {
    if (!newTerm.trim()) return
    termbaseApi.postCreate(kid, [newTerm]).then(() => {
      message.success('创建成功'); setCreateOpen(false); setNewTerm(''); load()
    }).catch(() => {})
  }

  const handleDelete = (id: string) => {
    termbaseApi.delDelete(kid, id).then(() => { message.success('删除成功'); load() }).catch(() => {})
  }

  return (
    <>
      <Card style={{borderRadius: 8}}>
        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 16}}>
          <Typography.Title level={5} style={{margin: 0}}>术语库</Typography.Title>
          <Space>
            <Input.Search value={search} onChange={(e) => setSearch(e.target.value)} onSearch={load}
              placeholder="搜索术语" style={{width: 200}} allowClear />
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>创建术语</Button>
          </Space>
        </div>
        <Table dataSource={data} rowKey="id" loading={loading} pagination={{pageSize: 20}} columns={[
          {title: '术语', dataIndex: 'content', key: 'content'},
          {title: '创建时间', dataIndex: 'create_time', key: 'create_time', width: 180,
            render: (t: string) => dateFormat(t)},
          {title: '操作', key: 'action', width: 80,
            render: (_: any, row: any) => (
              <Popconfirm title="确认删除？" onConfirm={() => handleDelete(row.id)}>
                <Button type="link" size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            )},
        ]} />
      </Card>
      <Modal title="创建术语" open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); setNewTerm('') }}>
        <Typography.Text>输入术语内容：</Typography.Text>
        <Input value={newTerm} onChange={(e) => setNewTerm(e.target.value)} placeholder="请输入术语" style={{marginTop: 8}} />
      </Modal>
    </>
  )
}
