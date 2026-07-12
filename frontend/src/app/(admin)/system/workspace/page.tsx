'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Table, Button, Space, Typography, Modal, Form, Input, message, Spin} from 'antd'
import {HomeOutlined, TeamOutlined, PlusOutlined} from '@ant-design/icons'
import {useTranslations} from 'next-intl'
import {systemApi} from '@/lib/api/system'
import {dateFormat} from '@/utils/time'

export default function WorkspacePage() {
  const t = useTranslations('menu')
  const [list, setList] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const load = () => {
    systemApi.getWorkspaceList().then((res: any) => { setList(res.data || []) }).catch(() => {}).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const handleCreate = () => {
    form.validateFields().then((values) => {
      systemApi.postWorkspace(values).then(() => { message.success('创建成功'); setCreateOpen(false); form.resetFields(); load() }).catch(() => {})
    })
  }

  return (
    <div>
      <Breadcrumb style={{marginBottom: 16}} items={[{title: <><HomeOutlined /> {t('home')}</>}, {title: <><TeamOutlined /> 工作区管理</>}]} />
      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 16}}>
        <Typography.Title level={4} style={{margin: 0}}>工作区管理</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>创建工作区</Button>
      </div>
      <Table dataSource={list} columns={[
        {title: '名称', dataIndex: 'name', key: 'name'},
        {title: '成员数', dataIndex: 'member_count', key: 'member_count', width: 100},
        {title: '创建时间', dataIndex: 'create_time', key: 'create_time', width: 180, render: (t: string) => dateFormat(t)},
      ]} rowKey="id" loading={loading} pagination={false} />
      <Modal title="创建工作区" open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); form.resetFields() }}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{required: true}]}><Input /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
