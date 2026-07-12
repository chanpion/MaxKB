'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Form, Input, Button, Card, Select, message, Spin, Typography} from 'antd'
import {HomeOutlined, AppstoreOutlined, ArrowLeftOutlined, SaveOutlined, KeyOutlined, MessageOutlined} from '@ant-design/icons'
import {useParams, useRouter, usePathname} from '@/i18n/navigation'
import {useTranslations} from 'next-intl'
import {applicationApi} from '@/lib/api/application'

export default function AppSettingPage() {
  const t = useTranslations('menu')
  const router = useRouter()
  const params = useParams()
  const id = params.id as string
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    applicationApi.getSetting(id).then((res: any) => {
      form.setFieldsValue(res.data)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [id])

  const handleSave = () => {
    form.validateFields().then((values) => {
      setSaving(true)
      applicationApi.putSetting(id, values).then(() => {
        message.success('保存成功')
      }).catch(() => {}).finally(() => setSaving(false))
    })
  }

  const tabItems = [
    {key: 'overview', label: '概览'},
    {key: 'setting', label: '设置'},
    {key: 'access', label: '访问'},
    {key: 'chat-log', label: '聊天日志'},
  ]

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>

  return (
    <div>
      <div style={{display: 'flex', alignItems: 'center', marginBottom: 12, gap: 12}}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.push(`/application/${id}/overview`)}>返回</Button>
        <Breadcrumb items={[
          {title: <><HomeOutlined /> {t('home')}</>},
          {title: <><AppstoreOutlined /> {t('application')}</>},
          {title: '设置'},
        ]} />
      </div>
      <Tabs activeKey="setting" items={tabItems}
        onChange={(key) => router.push(`/application/${id}/${key}`)}
        style={{marginBottom: 8}} />
      <Card style={{borderRadius: 8}}>
        <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: 16}}>
          <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}>保存</Button>
        </div>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{required: true}]}>
            <Input />
          </Form.Item>
          <Form.Item name="desc" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
