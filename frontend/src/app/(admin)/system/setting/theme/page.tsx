'use client'
import React, {useEffect, useState} from 'react'
import {Card, Form, Input, Button, message, Spin} from 'antd'
import {SaveOutlined} from '@ant-design/icons'
import {systemApi} from '@/lib/api/system'

export default function ThemePage() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    systemApi.getThemeInfo().then((res: any) => {
      form.setFieldsValue(res.data)
    }).catch(() => {}).finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form])

  const handleSave = () => {
    form.validateFields().then((values) => {
      setSaving(true)
      systemApi.putThemeInfo(values).then(() => {
        message.success('保存成功')
      }).catch(() => {}).finally(() => setSaving(false))
    })
  }

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>

  return (
    <Card style={{borderRadius: 8}} title="外观设置">
      <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: 16}}>
        <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}>保存</Button>
      </div>
      <Form form={form} layout="vertical" style={{maxWidth: 480}}>
        <Form.Item name="theme" label="主题色"><Input placeholder="如: #3370FF" /></Form.Item>
        <Form.Item name="login_logo" label="登录 Logo"><Input placeholder="图片 URL" /></Form.Item>
      </Form>
    </Card>
  )
}
