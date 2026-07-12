'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Card, Form, Input, Button, Typography, message, Spin, Tabs, InputNumber} from 'antd'
import {HomeOutlined, SettingOutlined, SaveOutlined, BgColorsOutlined, SafetyOutlined, MailOutlined} from '@ant-design/icons'
import {useTranslations} from 'next-intl'
import {useRouter, usePathname} from '@/i18n/navigation'
import {systemApi} from '@/lib/api/system'

const tabItems = [
  {key: 'theme', label: <><BgColorsOutlined /> 主题</>},
  {key: 'auth', label: <><SafetyOutlined /> 认证</>},
  {key: 'email', label: <><MailOutlined /> 邮件</>},
]

export default function EmailPage() {
  const t = useTranslations('menu')
  const router = useRouter()
  const pathname = usePathname()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const activeKey = pathname.split('/').pop() || 'theme'

  useEffect(() => {
    systemApi.getEmailSetting().then((res: any) => { form.setFieldsValue(res.data) }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleSave = () => {
    form.validateFields().then((values) => {
      setSaving(true)
      systemApi.putEmailSetting(values).then(() => { message.success('保存成功') }).catch(() => {}).finally(() => setSaving(false))
    })
  }

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>
  return (
    <div>
      <Breadcrumb style={{marginBottom: 12}} items={[{title: <><HomeOutlined /> {t('home')}</>}, {title: <><SettingOutlined /> 系统设置</>}]} />
      <Tabs activeKey={activeKey} items={tabItems} onChange={(key) => router.push(`/system/setting/${key}`)} style={{marginBottom: 8}} />
      <Card style={{borderRadius: 8}} title="邮件设置">
        <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving} style={{float: 'right', marginBottom: 16}}>保存</Button>
        <Form form={form} layout="vertical" style={{maxWidth: 480}}>
          <Form.Item name="smtp_host" label="SMTP 主机"><Input /></Form.Item>
          <Form.Item name="smtp_port" label="SMTP 端口"><InputNumber style={{width: '100%'}} /></Form.Item>
          <Form.Item name="smtp_user" label="SMTP 用户"><Input /></Form.Item>
          <Form.Item name="smtp_password" label="SMTP 密码"><Input.Password /></Form.Item>
          <Form.Item name="from_email" label="发件人地址"><Input /></Form.Item>
        </Form>
      </Card>
    </div>
  )
}
