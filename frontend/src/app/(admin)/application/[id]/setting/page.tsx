'use client'
import React, {useEffect, useState} from 'react'
import {Form, Input, Button, Card, message, Spin} from 'antd'
import {SaveOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {applicationApi} from '@/lib/api/application'

export default function AppSettingPage() {
  const params = useParams()
  const id = params.id as string
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [detail, setDetail] = useState<any>({})
  const [form] = Form.useForm()

  useEffect(() => {
    applicationApi.getDetail(id).then((res: any) => {
      setDetail(res.data || {})
      form.setFieldsValue(res.data)
    }).catch(() => {}).finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form, id])

  const handleSave = () => {
    form.validateFields().then((values) => {
      setSaving(true)
      applicationApi.putUpdate(id, {...detail, ...values}).then(() => {
        message.success('保存成功')
      }).catch(() => {}).finally(() => setSaving(false))
    })
  }

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>

  return (
    <Card style={{borderRadius: 8}} title="基本信息">
      <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: 16}}>
        <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}>保存</Button>
      </div>
      <Form form={form} layout="vertical" style={{maxWidth: 640}}>
        <Form.Item name="name" label="名称" rules={[{required: true}]}>
          <Input />
        </Form.Item>
        <Form.Item name="desc" label="描述">
          <Input.TextArea rows={3} />
        </Form.Item>
      </Form>
    </Card>
  )
}
