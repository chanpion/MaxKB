'use client'
import React, {forwardRef, useImperativeHandle, useRef, useState} from 'react'
import {Modal, Button} from 'antd'
import KnowledgeBaseForm from './BaseForm'
import knowledgeApi from '@/lib/api/knowledge/knowledge'
import {useFolderStore, useUserStore} from '@/store'
import {useTranslations} from 'next-intl'
import {MsgSuccess} from '@/utils/message'

export interface CreateKnowledgeDialogRef {
  open: (folder: any) => void
}

const CreateKnowledgeDialog = forwardRef<CreateKnowledgeDialogRef, {onRefresh?: () => void}>(
  function CreateKnowledgeDialog({onRefresh}, ref) {
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
      if (await baseRef.current?.validate()) {
        const form = baseRef.current.form.getFieldsValue()
        const obj = {folder_id: currentFolder?.id, ...form}
        setLoading(true)
        knowledgeApi
          .postKnowledge(obj)
          .then(async () => {
            await user.profile()
            setLoading(false)
            setOpen(false)
            MsgSuccess(t('common.createSuccess'))
            onRefresh?.()
          })
          .catch(() => setLoading(false))
      }
    }

    return (
      <Modal
        title={t('views.knowledge.knowledgeType.createGeneralKnowledge')}
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
      </Modal>
    )
  },
)

export default CreateKnowledgeDialog
