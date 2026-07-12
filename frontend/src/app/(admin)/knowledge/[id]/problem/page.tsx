'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Table, Button, Space, Typography, Tag, Spin, Modal, Form, Input, message, Popconfirm, Tabs} from 'antd'
import {HomeOutlined, FileTextOutlined, QuestionCircleOutlined, PlusOutlined, EditOutlined, DeleteOutlined, ExperimentOutlined, BookOutlined, SettingOutlined, UserOutlined} from '@ant-design/icons'
import {useParams, useRouter, usePathname} from '@/i18n/navigation'
import {get, post, del} from '@/lib/request'
import {useUserStore} from '@/store'

function ws() { return useUserStore.getState().getWorkspaceId() }

export default function ProblemPage() {
  const router = useRouter()
  const pathname = usePathname()
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
  useEffect(() => { load() }, [kid])

  const handleCreate = () => {
    form.validateFields().then((values) => {
      post(`${prefix}`, values).then(() => { message.success('创建成功'); setCreateOpen(false); form.resetFields(); load() }).catch(() => {})
    })
  }

  const handleDelete = (id: string) => {
    del(`${prefix}/${id}`).then(() => { message.success('删除成功'); load() }).catch(() => {})
  }

  const tabItems = [
    {key: 'document', label: <><FileTextOutlined /> 文档</>},
    {key: 'problem', label: <><QuestionCircleOutlined /> 问题</>},
    {key: 'termbase', label: <><BookOutlined /> 术语库</>},
    {key: 'hit-test', label: <><ExperimentOutlined /> 命中测试</>},
    {key: 'chat-user', label: <><UserOutlined /> 对话用户</>},
    {key: 'setting', label: <><SettingOutlined /> 设置</>},
  ]

  return (
    <div>
      <Breadcrumb style={{marginBottom: 12}} items={[
        {title: <><HomeOutlined /> 首页</>},
        {title: <><FileTextOutlined /> 知识库详情</>},
      ]} />
      <Tabs activeKey="problem" items={tabItems}
        onChange={(key) => router.push(`/knowledge/${kid}/${key}`)}
        style={{marginBottom: 8}} />
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
    </div>
  )
}
