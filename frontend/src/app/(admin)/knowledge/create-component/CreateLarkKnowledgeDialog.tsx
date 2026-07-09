'use client'
import React, {forwardRef, useImperativeHandle, useRef, useState} from 'react'
import {Modal, Button, Form, Input} from 'antd'
import KnowledgeBaseForm from './BaseForm'
import knowledgeApi from '@/lib/api/knowledge/knowledge'
import {useFolderStore, useUserStore} from '@/store'
import {useTranslations} from 'next-intl'
import {MsgSuccess} from '@/utils/message'

export interface CreateLarkKnowledgeDialogRef {
  open: (folder: any) => void
}

const CreateLarkKnowledgeDialog = forwardRef<CreateLarkKnowledgeDialogRef, {onRefresh?: () => void}>(
  function CreateLarkKnowledgeDialog({onRefresh}, ref) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [currentFolder, setCurrentFolder] = useState<any>(null)
    const baseRef = useRef<any>(null)
    const [larkForm] = Form.useForm()
    const folder = useFolderStore()
    const user = useUserStore()
    const t = useTranslations()

    useImperativeHandle(ref, () => ({
      open: (f: any) => {
        setCurrentFolder(f)
        setOpen(true)
        larkForm.resetFields()
      },
    }))

    const submit = async () => {
      if (!(await baseRef.current?.validate())) return
      const valid = await larkForm.validateFields().then(() => true).catch(() => false)
      if (!valid) return
      const form = baseRef.current.form.getFieldsValue()
      const obj = {folder_id: currentFolder?.id, ...form, ...larkForm.getFieldsValue()}
      setLoading(true)
      knowledgeApi
        .postLarkKnowledge(obj)
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
        title={t('views.knowledge.knowledgeType.createLarkKnowledge')}
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
        <Form form={larkForm} layout="vertical">
          <Form.Item name="app_id" label="App ID" rules={[{required: true}]}>
            <Input placeholder="Lark App ID" />
          </Form.Item>
          <Form.Item name="app_secret" label="App Secret" rules={[{required: true}]}>
            <Input.Password placeholder="Lark App Secret" />
          </Form.Item>
        </Form>
      </Modal>
    )
  },
)

export default CreateLarkKnowledgeDialog
