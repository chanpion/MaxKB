'use client'
import React, {useEffect, useState} from 'react'
import {Table, Button, Space, Typography, Tag, Spin, Modal, Form, Input, message, Popconfirm, Card} from 'antd'
import {PlusOutlined, EditOutlined, DeleteOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {get, post, del} from '@/lib/request'
import {useUserStore} from '@/store'

function ws() { return useUserStore.getState().getWorkspaceId() }

export default function ProblemPage() {
  const params = useParams()
  const kid = params.id as string
  const [list, setList] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()
  const prefix = `/workspace/${ws()}/knowledge/${kid}/problem`

  const load = () => {
    setLoading(true)
    get(`${prefix}`).then((res: any) => setList(res.data || [])).catch(() => {}).finally(() => setLoading(false))
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load() }, [kid])

  const handleCreate = () => {
    form.validateFields().then((values) => {
      post(`${prefix}`, [values.content]).then(() => { message.success('创建成功'); setCreateOpen(false); form.resetFields(); load() }).catch(() => {})
    })
  }

  const handleDelete = (id: string) => {
    del(`${prefix}/${id}`).then(() => { message.success('删除成功'); load() }).catch(() => {})
  }

  return (
    <Card style={{borderRadius: 8}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16}}>
        <Typography.Title level={5} style={{margin: 0}}>问题管理</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>创建问题</Button>
      </div>
      <Table dataSource={list} columns={[
        {title: '问题', dataIndex: 'content', key: 'content'},
        {title: '操作', key: 'action', width: 100,
          render: (_: any, row: any) => (
            <Popconfirm title="确认删除？" onConfirm={() => handleDelete(row.id)}>
              <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
            </Popconfirm>
          )},
      ]} rowKey="id" loading={loading} pagination={false} size="middle" />
      <Modal title="创建问题" open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); form.resetFields() }}>
        <Form form={form} layout="vertical">
          <Form.Item name="content" label="问题内容" rules={[{required: true, message: '请输入问题'}]}>
            <Input.TextArea rows={3} placeholder="请输入问题" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
