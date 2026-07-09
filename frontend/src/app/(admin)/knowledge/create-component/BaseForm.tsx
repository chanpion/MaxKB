'use client'
import React, {forwardRef, useImperativeHandle, useRef, useState, useEffect} from 'react'
import {Form, Input, Select} from 'antd'
import knowledgeApi from '@/lib/api/knowledge/knowledge'
import {useTranslations} from 'next-intl'

export interface KnowledgeBaseFormRef {
  validate: () => Promise<boolean>
  form: any
}

// 知识库通用基础表单（名称 / 描述 / 向量模型）
const KnowledgeBaseForm = forwardRef<KnowledgeBaseFormRef, {}>(function KnowledgeBaseForm(_props, ref) {
  const [form] = Form.useForm()
  const [modelOptions, setModelOptions] = useState<any[]>([])
  const t = useTranslations()

  useImperativeHandle(ref, () => ({
    validate: () =>
      new Promise<boolean>((resolve) => {
        form
          .validateFields()
          .then(() => resolve(true))
          .catch(() => resolve(false))
      }),
    form,
  }))

  useEffect(() => {
    knowledgeApi
      .getKnowledgeModel()
      .then((ok: any) => {
        const list = (ok.data || []).map((m: any) => ({label: m.name, value: m.id}))
        setModelOptions(list)
      })
      .catch(() => setModelOptions([]))
  }, [])

  return (
    <Form form={form} layout="vertical">
      <Form.Item
        name="name"
        label={t('views.knowledge.form.knowledgeName.label')}
        rules={[{required: true, message: t('views.knowledge.form.knowledgeName.requiredMessage')}]}
      >
        <Input maxLength={64} showCount />
      </Form.Item>
      <Form.Item
        name="desc"
        label={t('views.knowledge.form.knowledgeDescription.label')}
        rules={[{required: true, message: t('views.knowledge.form.knowledgeDescription.requiredMessage')}]}
      >
        <Input.TextArea maxLength={256} showCount autoSize={{minRows: 3}} />
      </Form.Item>
      <Form.Item
        name="embedding_model_id"
        label={t('views.knowledge.form.EmbeddingModel.label')}
        rules={[{required: true, message: t('views.knowledge.form.EmbeddingModel.requiredMessage')}]}
      >
        <Select
          options={modelOptions}
          placeholder={t('views.knowledge.form.EmbeddingModel.placeholder')}
          showSearch
          optionFilterProp="label"
        />
      </Form.Item>
    </Form>
  )
})

export default KnowledgeBaseForm
