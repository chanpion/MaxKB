'use client'
import React, {useEffect, useState} from 'react'
import {Card, Table, Button, Space, Typography, Modal, Form, Input, message, Tag, Popconfirm} from 'antd'
import {PlusOutlined, EditOutlined, DeleteOutlined} from '@ant-design/icons'
import {systemApi} from '@/lib/api/system'

export default function UserManagePage() {
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editUser, setEditUser] = useState<any>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  const loadUsers = () => {
    setLoading(true)
    systemApi.getUserManage(1).then((res: any) => {
      setUsers(res.data?.records || res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { loadUsers() }, [])

  const handleCreate = () => {
    form.validateFields().then((values) => {
      systemApi.postUserManage(values).then(() => {
        message.success('创建成功'); setCreateOpen(false); form.resetFields(); loadUsers()
      }).catch(() => {})
    })
  }

  const handleEdit = (row: any) => {
    setEditUser(row)
    editForm.setFieldsValue(row)
    setEditOpen(true)
  }

  const handleEditSave = () => {
    editForm.validateFields().then((values) => {
      systemApi.putUserManage(editUser.id, values).then(() => {
        message.success('修改成功'); setEditOpen(false); loadUsers()
      }).catch(() => {})
    })
  }

  const handleDelete = (id: string) => {
    systemApi.delUserManage(id).then(() => { message.success('删除成功'); loadUsers() }).catch(() => {})
  }

  const columns = [
    {title: '用户名', dataIndex: 'username', key: 'username'},
    {title: '昵称', dataIndex: 'nick_name', key: 'nick_name'},
    {title: '邮箱', dataIndex: 'email', key: 'email'},
    {title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '禁用'}</Tag>},
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
    <Card style={{borderRadius: 8}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16}}>
        <Typography.Title level={4} style={{margin: 0}}>用户管理</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>创建用户</Button>
      </div>
      <Table dataSource={users} columns={columns} rowKey="id" loading={loading} pagination={{pageSize: 20}} />

      <Modal title="创建用户" open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); form.resetFields() }}>
        <Form form={form} layout="vertical">
          <Form.Item name="username" label="用户名" rules={[{required: true, message: '请输入用户名'}]}>
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item name="nick_name" label="昵称">
            <Input placeholder="请输入昵称" />
          </Form.Item>
          <Form.Item name="email" label="邮箱" rules={[{type: 'email', message: '邮箱格式不正确'}]}>
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{required: true, message: '请输入密码'}]}>
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="编辑用户" open={editOpen} onOk={handleEditSave} onCancel={() => setEditOpen(false)}>
        <Form form={editForm} layout="vertical">
          <Form.Item name="username" label="用户名" rules={[{required: true, message: '请输入用户名'}]}>
            <Input />
          </Form.Item>
          <Form.Item name="nick_name" label="昵称"><Input /></Form.Item>
          <Form.Item name="email" label="邮箱"><Input /></Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
