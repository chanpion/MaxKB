'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Table, Button, Space, Typography, Tag, Modal, Form, Input, Select, message, Popconfirm, Switch, DatePicker} from 'antd'
import {HomeOutlined, ThunderboltOutlined, PlusOutlined, EditOutlined, DeleteOutlined} from '@ant-design/icons'
import {useTranslations} from 'next-intl'
import {triggerApi} from '@/lib/api/trigger'
import {dateFormat} from '@/utils/time'

export default function TriggerPage() {
  const t = useTranslations('menu')
  const [list, setList] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editItem, setEditItem] = useState<any>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  const load = () => {
    setLoading(true)
    triggerApi.getList().then((res: any) => {
      setList(res.data?.records || res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const handleCreate = () => {
    form.validateFields().then((values) => {
      triggerApi.postCreate(values).then(() => {
        message.success('创建成功'); setCreateOpen(false); form.resetFields(); load()
      }).catch(() => {})
    })
  }

  const handleEdit = (row: any) => {
    setEditItem(row)
    editForm.setFieldsValue(row)
    setEditOpen(true)
  }
  const handleEditSave = () => {
    editForm.validateFields().then((values) => {
      triggerApi.putUpdate(editItem.id, values).then(() => {
        message.success('修改成功'); setEditOpen(false); load()
      }).catch(() => {})
    })
  }
  const handleDelete = (id: string) => {
    triggerApi.delDelete(id).then(() => { message.success('删除成功'); load() }).catch(() => {})
  }

  const columns = [
    {title: '名称', dataIndex: 'name', key: 'name'},
    {title: '类型', dataIndex: 'trigger_type', key: 'trigger_type', width: 100,
      render: (v: string) => <Tag>{v === 'cron' ? '定时' : '事件'}</Tag>},
    {title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '禁用'}</Tag>},
    {title: '创建时间', dataIndex: 'create_time', key: 'create_time', width: 180,
      render: (t: string) => dateFormat(t)},
    {title: '操作', key: 'action', width: 150,
      render: (_: any, row: any) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(row)}>编辑</Button>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(row.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      )},
  ]

  return (
    <div>
      <Breadcrumb style={{marginBottom: 16}} items={[
        {title: <><HomeOutlined /> {t('home')}</>},
        {title: <><ThunderboltOutlined /> {t('trigger')}</>},
      ]} />
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16}}>
        <Typography.Title level={4} style={{margin: 0}}>{t('trigger')}</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>创建触发器</Button>
      </div>
      <Table dataSource={list} columns={columns} rowKey="id" loading={loading} pagination={{pageSize: 20}} />

      <Modal title="创建触发器" open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); form.resetFields() }}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{required: true}]}><Input /></Form.Item>
          <Form.Item name="trigger_type" label="类型" rules={[{required: true}]}>
            <Select options={[{value: 'cron', label: '定时'}, {value: 'event', label: '事件'}]} />
          </Form.Item>
          <Form.Item name="cron_expr" label="Cron 表达式">
            <Input placeholder="如: 0 0 * * *" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="编辑触发器" open={editOpen} onOk={handleEditSave} onCancel={() => setEditOpen(false)}>
        <Form form={editForm} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{required: true}]}><Input /></Form.Item>
          <Form.Item name="is_active" label="状态">
            <Select options={[{value: true, label: '启用'}, {value: false, label: '禁用'}]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
