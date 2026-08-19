'use client'
import React, {useEffect, useState} from 'react'
import {Card, Form, Input, Button, message, Spin} from 'antd'
import {SaveOutlined} from '@ant-design/icons'
import {systemApi} from '@/lib/api/system'

export default function AuthPage() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    systemApi.getAuthSetting().then((res: any) => {
      form.setFieldsValue(res.data)
    }).catch(() => {}).finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form])

  const handleSave = () => {
    form.validateFields().then((values) => {
      setSaving(true)
      systemApi.putAuthSetting(values).then(() => { message.success('保存成功') }).catch(() => {}).finally(() => setSaving(false))
    })
  }

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>
  return (
    <Card style={{borderRadius: 8}} title="认证设置">
      <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: 16}}>
        <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}>保存</Button>
      </div>
      <Form form={form} layout="vertical" style={{maxWidth: 480}}>
        <Form.Item name="login_method" label="登录方式"><Input placeholder="如: username,email" /></Form.Item>
      </Form>
    </Card>
  )
}
