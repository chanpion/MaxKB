'use client'
import React, {useEffect, useState} from 'react'
import {Card, Form, Input, Button, message, Spin, InputNumber} from 'antd'
import {SaveOutlined} from '@ant-design/icons'
import {systemApi} from '@/lib/api/system'

export default function EmailPage() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    systemApi.getEmailSetting().then((res: any) => { form.setFieldsValue(res.data) }).catch(() => {}).finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form])

  const handleSave = () => {
    form.validateFields().then((values) => {
      setSaving(true)
      systemApi.putEmailSetting(values).then(() => { message.success('保存成功') }).catch(() => {}).finally(() => setSaving(false))
    })
  }

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>
  return (
    <Card style={{borderRadius: 8}} title="邮件设置">
      <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: 16}}>
        <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}>保存</Button>
      </div>
      <Form form={form} layout="vertical" style={{maxWidth: 480}}>
        <Form.Item name="smtp_host" label="SMTP 主机"><Input /></Form.Item>
        <Form.Item name="smtp_port" label="SMTP 端口"><InputNumber style={{width: '100%'}} /></Form.Item>
        <Form.Item name="smtp_user" label="SMTP 用户"><Input /></Form.Item>
        <Form.Item name="smtp_password" label="SMTP 密码"><Input.Password /></Form.Item>
        <Form.Item name="from_email" label="发件人地址"><Input /></Form.Item>
      </Form>
    </Card>
  )
}
