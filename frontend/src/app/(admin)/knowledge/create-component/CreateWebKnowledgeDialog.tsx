'use client'
import React, {forwardRef, useImperativeHandle, useRef, useState} from 'react'
import {Modal, Button, Form, Input} from 'antd'
import KnowledgeBaseForm from './BaseForm'
import knowledgeApi from '@/lib/api/knowledge/knowledge'
import {useFolderStore, useUserStore} from '@/store'
import {useTranslations} from 'next-intl'
import {MsgSuccess} from '@/utils/message'

export interface CreateWebKnowledgeDialogRef {
  open: (folder: any) => void
}

const CreateWebKnowledgeDialog = forwardRef<CreateWebKnowledgeDialogRef, {onRefresh?: () => void}>(
  function CreateWebKnowledgeDialog({onRefresh}, ref) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [currentFolder, setCurrentFolder] = useState<any>(null)
    const baseRef = useRef<any>(null)
    const [webForm] = Form.useForm()
    const folder = useFolderStore()
    const user = useUserStore()
    const t = useTranslations()

    useImperativeHandle(ref, () => ({
      open: (f: any) => {
        setCurrentFolder(f)
        setOpen(true)
        webForm.resetFields()
      },
    }))

    const submit = async () => {
      if (!(await baseRef.current?.validate())) return
      const valid = await webForm.validateFields().then(() => true).catch(() => false)
      if (!valid) return
      const form = baseRef.current.form.getFieldsValue()
      const obj = {folder_id: currentFolder?.id, ...form, ...webForm.getFieldsValue()}
      setLoading(true)
      knowledgeApi
        .postWebKnowledge(obj)
        .then(async () => {
          await user.profile()
          setLoading(false)
          setOpen(false)
          MsgSuccess(t('common.createSuccess'))
          onRefresh?.()
        })
        .catch(() => setLoading(false))
    }

    return (
      <Modal
        title={t('views.knowledge.knowledgeType.createWebKnowledge')}
        open={open}
        onCancel={() => setOpen(false)}
        destroyOnClose
        footer={[
          <Button key="c" onClick={() => setOpen(false)}>
            {t('common.cancel')}
          </Button>,
          <Button key="ok" type="primary" loading={loading} onClick={submit}>
            {t('common.create')}
          </Button>,
        ]}
      >
        <KnowledgeBaseForm ref={baseRef} />
        <Form form={webForm} layout="vertical">
          <Form.Item
            name="source_url"
            label={t('views.knowledge.form.source_url.label')}
            rules={[{required: true, message: t('views.knowledge.form.source_url.requiredMessage')}]}
          >
            <Input placeholder={t('views.knowledge.form.source_url.placeholder')} />
          </Form.Item>
          <Form.Item name="selector" label={t('views.knowledge.form.selector.label')}>
            <Input placeholder={t('views.knowledge.form.selector.placeholder')} />
          </Form.Item>
        </Form>
      </Modal>
    )
  },
)

export default CreateWebKnowledgeDialog
