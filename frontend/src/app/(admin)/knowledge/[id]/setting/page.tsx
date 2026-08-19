'use client'
import React, {useEffect, useState} from 'react'
import {
  Form, Input, Button, Card, message, Spin, Typography,
  Select, Slider, InputNumber, Tooltip, Modal, Tag,
} from 'antd'
import {SaveOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import knowledgeApi from '@/lib/api/knowledge/knowledge'

const TYPE_INFO: Record<number, {label: string; desc: string}> = {
  0: {label: '通用型', desc: '上传文档、问答对，支持多种格式'},
  1: {label: 'Web 站点', desc: '通过 URL 爬取网页内容'},
  2: {label: '飞书', desc: '同步飞书文档'},
  4: {label: '工作流', desc: '通过工作流节点生成内容'},
}

export default function KnowledgeSettingPage() {
  const params = useParams()
  const kid = params.id as string
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [detail, setDetail] = useState<any>({})
  const [embeddingModels, setEmbeddingModels] = useState<any[]>([])
  const [form] = Form.useForm()
  const [reEmbedOpen, setReEmbedOpen] = useState(false)
  const [pendingValues, setPendingValues] = useState<any>(null)
  const [reEmbedding, setReEmbedding] = useState(false)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      knowledgeApi.getKnowledgeDetail(kid),
      knowledgeApi.getKnowledgeEmbeddingModel(),
    ]).then(([detailRes, modelRes]: any) => {
      const d = detailRes.data ?? {}
      setDetail(d)
      const meta = d.meta ?? {}
      form.setFieldsValue({
        name: d.name,
        desc: d.desc,
        embedding_model_id: d.embedding_model_id,
        file_count_limit: d.file_count_limit ?? 50,
        file_size_limit: d.file_size_limit ?? 100,
        source_url: meta.source_url ?? '',
        selector: meta.selector ?? '',
        app_id: meta.app_id ?? '',
        app_secret: meta.app_secret ?? '',
        folder_token: meta.folder_token ?? '',
      })
      const md = modelRes?.data ?? {}
      const merged = [...(md.model ?? []), ...(md.shared_model ?? [])]
      setEmbeddingModels(merged)
    }).catch(() => {}).finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kid])

  const doSave = (payload: any, reEmbed: boolean) => {
    setSaving(true)
    knowledgeApi.putKnowledge(kid, payload).then(() => {
      if (reEmbed) {
        setReEmbedding(true)
        knowledgeApi.putReEmbeddingKnowledge(kid).then(() => {
          message.success('保存成功，已触发重新向量化')
        }).catch(() => {
          message.success('保存成功')
        }).finally(() => setReEmbedding(false))
      } else {
        message.success('保存成功')
      }
    }).catch(() => {}).finally(() => {
      setSaving(false)
      setReEmbedOpen(false)
    })
  }

  const handleSave = () => {
    form.validateFields().then((values) => {
      const type = detail.type
      const payload: any = {
        name: values.name,
        desc: values.desc,
        embedding_model_id: values.embedding_model_id,
        file_count_limit: values.file_count_limit,
        file_size_limit: values.file_size_limit,
      }
      if (type === 1) {
        payload.meta = {source_url: values.source_url, selector: values.selector}
      }
      if (type === 2) {
        payload.meta = {
          app_id: values.app_id,
          app_secret: values.app_secret,
          folder_token: values.folder_token,
        }
      }
      const embeddingChanged = values.embedding_model_id !== detail.embedding_model_id
      if (embeddingChanged) {
        setPendingValues(payload)
        setReEmbedOpen(true)
        return
      }
      doSave(payload, false)
    })
  }

  if (loading) return <div style={{textAlign: 'center', padding: 80}}><Spin size="large" /></div>

  const typeInfo = TYPE_INFO[detail.type as number]

  return (
    <>
      <Card style={{borderRadius: 8}}>
        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 16}}>
          <Typography.Title level={5} style={{margin: 0}}>知识库设置</Typography.Title>
          <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}>保存</Button>
        </div>
        <Form form={form} layout="vertical" style={{maxWidth: 720}}>
          <Typography.Title level={5} style={{marginBottom: 16}}>基本信息</Typography.Title>
          <Form.Item name="name" label="名称" rules={[{required: true, message: '请输入名称'}]}>
            <Input maxLength={64} showCount />
          </Form.Item>
          <Form.Item name="desc" label="描述">
            <Input.TextArea rows={3} maxLength={256} showCount />
          </Form.Item>
          <Form.Item name="embedding_model_id" label="向量模型" rules={[{required: true, message: '请选择向量模型'}]}>
            <Select
              placeholder="请选择向量模型"
              options={embeddingModels.map((m) => ({label: m.name || m.model_name, value: m.id}))}
            />
          </Form.Item>

          {typeInfo && (
            <Form.Item label="类型">
              <Tag color="blue" style={{fontSize: 14, padding: '4px 10px'}}>{typeInfo.label}</Tag>
              <span style={{marginLeft: 8, color: '#888'}}>{typeInfo.desc}</span>
            </Form.Item>
          )}

          {detail.type === 1 && (
            <>
              <Form.Item name="source_url" label="数据源 URL" rules={[{required: true, message: '请输入数据源 URL'}]}>
                <Input placeholder="请输入站点地址" />
              </Form.Item>
              <Form.Item name="selector" label="选择器">
                <Input placeholder="CSS 选择器（可选）" />
              </Form.Item>
            </>
          )}

          {detail.type === 2 && (
            <>
              <Form.Item name="app_id" label="App ID" rules={[{required: true, message: '请输入 App ID'}]}>
                <Input placeholder="请输入飞书 App ID" />
              </Form.Item>
              <Form.Item name="app_secret" label="App Secret" rules={[{required: true, message: '请输入 App Secret'}]}>
                <Input.Password placeholder="请输入飞书 App Secret" />
              </Form.Item>
              <Form.Item name="folder_token" label="Folder Token" rules={[{required: true, message: '请输入 Folder Token'}]}>
                <Input placeholder="请输入飞书 Folder Token" />
              </Form.Item>
            </>
          )}

          {detail.type === 0 && (
            <>
              <Typography.Title level={5} style={{margin: '8px 0 16px'}}>其他设置</Typography.Title>
              <Form.Item label="文件数量限制" tooltip="知识库允许上传的最大文档数量">
                <Form.Item name="file_count_limit" noStyle>
                  <Slider min={1} max={1000} />
                </Form.Item>
                <InputNumber min={1} max={1000} style={{marginLeft: 16, width: 120}} />
              </Form.Item>
              <Form.Item label="文件大小限制 (MB)" tooltip="单个文件的最大体积">
                <Form.Item name="file_size_limit" noStyle>
                  <Slider min={1} max={1000} />
                </Form.Item>
                <InputNumber min={1} max={1000} style={{marginLeft: 16, width: 120}} />
              </Form.Item>
            </>
          )}
        </Form>
      </Card>

      <Modal
        title="提示"
        open={reEmbedOpen}
        confirmLoading={reEmbedding}
        okText="重新向量化"
        cancelText="仅保存"
        onOk={() => doSave(pendingValues, true)}
        onCancel={() => doSave(pendingValues, false)}
      >
        <p>修改向量模型后需要重新向量化，否则检索结果将不准确。</p>
        <p>是否立即重新向量化？</p>
      </Modal>
    </>
  )
}
