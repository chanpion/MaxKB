'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Form, Input, Button, Card, Select, message, Spin, Typography, Tabs} from 'antd'
import {HomeOutlined, FileTextOutlined, SaveOutlined, SettingOutlined, ExperimentOutlined, BookOutlined, QuestionCircleOutlined, UserOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {useRouter, usePathname} from '@/i18n/navigation'
import {knowledgeApi} from '@/lib/api/knowledge/knowledge'

export default function KnowledgeSettingPage() {
  const router = useRouter()
  const pathname = usePathname()
  const params = useParams()
  const kid = params.id as string
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    knowledgeApi.getKnowledgeDetail(kid).then((res: any) => {
      form.setFieldsValue(res.data)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [kid])

  const handleSave = () => {
    form.validateFields().then((values) => {
      setSaving(true)
      knowledgeApi.putKnowledge(kid, values).then(() => {
        message.success('保存成功')
      }).catch(() => {}).finally(() => setSaving(false))
    })
  }

  const tabItems = [
    {key: 'document', label: <><FileTextOutlined /> 文档</>},
    {key: 'problem', label: <><QuestionCircleOutlined /> 问题</>},
    {key: 'termbase', label: <><BookOutlined /> 术语库</>},
    {key: 'hit-test', label: <><ExperimentOutlined /> 命中测试</>},
    {key: 'setting', label: <><SettingOutlined /> 设置</>},
  ]

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>

  return (
    <div>
      <Breadcrumb style={{marginBottom: 12}} items={[
        {title: <><HomeOutlined /> 首页</>},
        {title: <><FileTextOutlined /> 知识库详情</>},
      ]} />
      <Tabs activeKey="setting" items={tabItems}
        onChange={(key) => router.push(`/knowledge/${kid}/${key}`)}
        style={{marginBottom: 8}} />
      <Card style={{borderRadius: 8}}>
        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 16}}>
          <Typography.Title level={5} style={{margin: 0}}>知识库设置</Typography.Title>
          <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}>保存</Button>
        </div>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{required: true, message: '请输入名称'}]}>
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
