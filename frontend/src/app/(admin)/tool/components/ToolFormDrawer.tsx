'use client'
import React, {useEffect, useState} from 'react'
import {Button, Drawer, Form, Input, Select, message, Space, Typography} from 'antd'
import {toolApi} from '@/lib/api/tool/tool'
import FieldFormDialog, {type FieldItem} from './FieldFormDialog'

const TOOL_TYPES = [
  {value: 'FUNCTION', label: '函数工具'},
  {value: 'SKILL', label: '技能工具'},
  {value: 'MCP', label: 'MCP 工具'},
  {value: 'DATA_SOURCE', label: '数据源'},
]

export default function ToolFormDrawer({
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
  const [inputFields, setInputFields] = useState<FieldItem[]>([])
  const [initFields, setInitFields] = useState<FieldItem[]>([])
  const isEdit = !!tool?.id

  useEffect(() => {
    if (!open) return
    if (tool) {
      form.setFieldsValue({
        name: tool.name,
        desc: tool.desc,
        tool_type: tool.tool_type || 'FUNCTION',
        code: tool.code,
        label: tool.label,
      })
      setInputFields(tool.input_field_list || [])
      setInitFields(tool.init_field_list || [])
    } else {
      form.resetFields()
      form.setFieldsValue({tool_type: 'FUNCTION'})
      setInputFields([])
      setInitFields([])
    }
  }, [open, tool, form])

  const submit = async () => {
    const values = await form.validateFields()
    const payload = {
      name: values.name,
      desc: values.desc,
      tool_type: values.tool_type,
      code: values.code,
      label: values.label,
      folder_id: folderId || tool?.folder_id || 'default',
      input_field_list: inputFields,
      init_field_list: initFields,
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

  const type = Form.useWatch('tool_type', form)

  return (
    <Drawer
      title={isEdit ? '编辑工具' : '新建工具'}
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
          <Input placeholder="工具名称" />
        </Form.Item>
        <Form.Item name="tool_type" label="类型" rules={[{required: true}]}>
          <Select options={TOOL_TYPES} disabled={isEdit} />
        </Form.Item>
        <Form.Item name="desc" label="描述">
          <Input.TextArea rows={2} placeholder="工具作用说明" />
        </Form.Item>
        <Form.Item name="label" label="标签">
          <Input placeholder="例如：天气查询" />
        </Form.Item>
        {type === 'FUNCTION' && (
          <Form.Item name="code" label="函数代码" rules={[{required: true, message: '请输入代码'}]}>
            <Input.TextArea
              rows={10}
              style={{fontFamily: 'monospace', fontSize: 13}}
              placeholder={'def execute(**kwargs):\n    return {"result": "ok"}'}
            />
          </Form.Item>
        )}
        <FieldFormDialog title="输入字段 (input_field_list)" value={inputFields} onChange={setInputFields} />
        <div style={{height: 12}} />
        <FieldFormDialog title="初始化参数 (init_field_list)" value={initFields} onChange={setInitFields} showDefault />
      </Form>
      {type !== 'FUNCTION' && (
        <Typography.Text type="secondary" style={{fontSize: 12}}>
          {type === 'MCP' ? 'MCP 工具请在「MCP 配置」中填写服务地址与工具名。' : ''}
        </Typography.Text>
      )}
    </Drawer>
  )
}
