'use client'
import React, {useEffect, useState} from 'react'
import {Button, Drawer, Form, Input, Select, message, Space, Typography} from 'antd'
import {toolApi} from '@/lib/api/tool/tool'

const AUTH_TYPES = [
  {value: 'NONE', label: '无'},
  {value: 'API_KEY', label: 'API Key'},
  {value: 'OAUTH', label: 'OAuth'},
]

export default function McpToolFormDrawer({
  open,
  tool,
  folderId,
  onClose,
  onSaved,
}: {
  open: boolean
  tool?: any | null
  folderId?: string
  onClose: () => void
  onSaved: () => void
}) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const isEdit = !!tool?.id

  useEffect(() => {
    if (!open) return
    if (tool) {
      form.setFieldsValue({
        name: tool.name,
        desc: tool.desc,
        url: tool.mcp_url || tool.url,
        tool_name: tool.mcp_tool_name || tool.tool_name,
        auth_type: tool.auth_type || 'NONE',
        auth_value: tool.auth_value,
        label: tool.label,
      })
    } else {
      form.resetFields()
      form.setFieldsValue({auth_type: 'NONE'})
    }
  }, [open, tool, form])

  const submit = async () => {
    const values = await form.validateFields()
    const payload = {
      name: values.name,
      desc: values.desc,
      tool_type: 'MCP',
      label: values.label,
      folder_id: folderId || tool?.folder_id || 'default',
      mcp_url: values.url,
      mcp_tool_name: values.tool_name,
      auth_type: values.auth_type,
      auth_value: values.auth_value,
    }
    setLoading(true)
    try {
      if (isEdit) await toolApi.putTool(tool.id, payload)
      else await toolApi.postTool(payload)
      message.success('保存成功')
      onSaved()
      onClose()
    } catch (e: any) {
      message.error(e?.message || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Drawer
      title={isEdit ? '编辑 MCP 工具' : '新建 MCP 工具'}
      width={640}
      open={open}
      onClose={onClose}
      extra={
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button type="primary" loading={loading} onClick={submit}>
            保存
          </Button>
        </Space>
      }
    >
      <Form form={form} layout="vertical">
        <Form.Item name="name" label="名称" rules={[{required: true, message: '请输入名称'}]}>
          <Input placeholder="MCP 工具名称" />
        </Form.Item>
        <Form.Item name="desc" label="描述">
          <Input.TextArea rows={2} placeholder="工具作用说明" />
        </Form.Item>
        <Form.Item name="label" label="标签">
          <Input placeholder="例如：日程管理" />
        </Form.Item>
        <Form.Item name="url" label="MCP 服务地址" rules={[{required: true, message: '请输入服务地址'}]}>
          <Input placeholder="http://localhost:8000/mcp" />
        </Form.Item>
        <Form.Item name="tool_name" label="工具名" rules={[{required: true, message: '请输入工具名'}]}>
          <Input placeholder="MCP 服务端暴露的工具标识" />
        </Form.Item>
        <Form.Item name="auth_type" label="认证方式">
          <Select options={AUTH_TYPES} />
        </Form.Item>
        <Form.Item name="auth_value" label="认证凭据" tooltip="API Key 或 Token">
          <Input.Password placeholder="可选" />
        </Form.Item>
        <Typography.Text type="secondary" style={{fontSize: 12}}>
          保存后可在列表中点击「调试」验证工具可用性。
        </Typography.Text>
      </Form>
    </Drawer>
  )
}
