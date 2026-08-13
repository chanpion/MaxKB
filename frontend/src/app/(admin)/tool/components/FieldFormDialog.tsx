'use client'
import React from 'react'
import {Button, Card, Form, Input, Select, Space, Typography} from 'antd'
import {DeleteOutlined, PlusOutlined} from '@ant-design/icons'

const TYPES = [
  {value: 'str', label: '字符串'},
  {value: 'int', label: '整数'},
  {value: 'float', label: '浮点数'},
  {value: 'bool', label: '布尔'},
  {value: 'dict', label: '对象'},
  {value: 'list', label: '数组'},
  {value: 'file', label: '文件'},
]

export interface FieldItem {
  name: string
  type: string
  required: boolean
  default_value?: string
  description?: string
}

/**
 * 字段表单（input_field_list / init_field_list）行增删编辑。
 * value: FieldItem[]; onChange 回写。
 */
export default function FieldFormDialog({
  value = [],
  onChange,
  title = '字段',
  showDefault = true,
}: {
  value?: FieldItem[]
  onChange?: (v: FieldItem[]) => void
  title?: string
  showDefault?: boolean
}) {
  const update = (next: FieldItem[]) => onChange?.(next)

  const setAt = (i: number, patch: Partial<FieldItem>) => {
    const next = value.map((it, idx) => (idx === i ? {...it, ...patch} : it))
    update(next)
  }
  const addRow = () => update([...value, {name: '', type: 'str', required: false}])
  const removeRow = (i: number) => update(value.filter((_, idx) => idx !== i))

  return (
    <Card size="small" title={title} styles={{body: {padding: 8}}}>
      <Space direction="vertical" style={{width: '100%'}} size={8}>
        {value.map((it, i) => (
          <div key={i} style={{display: 'flex', gap: 8, alignItems: 'flex-start'}}>
            <Form.Item style={{margin: 0, flex: 1}}>
              <Input
                placeholder="字段名"
                value={it.name}
                onChange={(e) => setAt(i, {name: e.target.value})}
              />
            </Form.Item>
            <Form.Item style={{margin: 0, width: 110}}>
              <Select value={it.type} onChange={(v) => setAt(i, {type: v})} options={TYPES} />
            </Form.Item>
            <Form.Item style={{margin: 0, width: 90}}>
              <Select
                value={it.required ? 'req' : 'opt'}
                onChange={(v) => setAt(i, {required: v === 'req'})}
                options={[
                  {value: 'req', label: '必填'},
                  {value: 'opt', label: '可选'},
                ]}
              />
            </Form.Item>
            {showDefault && (
              <Form.Item style={{margin: 0, flex: 1}}>
                <Input
                  placeholder="默认值"
                  value={it.default_value}
                  onChange={(e) => setAt(i, {default_value: e.target.value})}
                />
              </Form.Item>
            )}
            <Button type="text" danger icon={<DeleteOutlined />} onClick={() => removeRow(i)} />
          </div>
        ))}
        {value.length === 0 && (
          <Typography.Text type="secondary" style={{fontSize: 12}}>
            暂无字段，点击下方按钮添加
          </Typography.Text>
        )}
        <Button type="dashed" block icon={<PlusOutlined />} onClick={addRow}>
          添加字段
        </Button>
      </Space>
    </Card>
  )
}
