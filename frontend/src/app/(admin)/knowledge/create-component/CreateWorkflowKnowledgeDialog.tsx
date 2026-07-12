'use client'
import React, {forwardRef, useImperativeHandle, useRef, useState} from 'react'
import {Modal, Button, Alert} from 'antd'
import KnowledgeBaseForm from './BaseForm'
import knowledgeApi from '@/lib/api/knowledge/knowledge'
import {useFolderStore, useUserStore} from '@/store'
import {useTranslations} from 'next-intl'
import {MsgSuccess} from '@/utils/message'

export interface CreateWorkflowKnowledgeDialogRef {
  open: (folder: any) => void
}

const CreateWorkflowKnowledgeDialog = forwardRef<CreateWorkflowKnowledgeDialogRef, {onRefresh?: () => void}>(
  function CreateWorkflowKnowledgeDialog({onRefresh}, ref) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [currentFolder, setCurrentFolder] = useState<any>(null)
    const baseRef = useRef<any>(null)
    const folder = useFolderStore()
    const user = useUserStore()
    const t = useTranslations()

    useImperativeHandle(ref, () => ({
      open: (f: any) => {
        setCurrentFolder(f)
        setOpen(true)
      },
    }))

    const submit = async () => {
      if (!(await baseRef.current?.validate())) return
      const form = baseRef.current.form.getFieldsValue()
      const obj = {folder_id: currentFolder?.id, ...form}
      setLoading(true)
      knowledgeApi
        .createWorkflowKnowledge(obj)
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
        title={t('views.knowledge.knowledgeType.createWorkflowKnowledge')}
        open={open}
        onCancel={() => setOpen(false)}
        destroyOnHidden
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
        <Alert
          type="info"
          showIcon
          style={{marginTop: 12}}
          message={t('views.knowledge.knowledgeType.workflowInfo')}
        />
      </Modal>
    )
  },
)

export default CreateWorkflowKnowledgeDialog
