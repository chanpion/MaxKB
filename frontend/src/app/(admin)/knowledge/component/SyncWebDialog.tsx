'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Modal, Radio, Button} from 'antd'
import knowledgeApi from '@/lib/api/knowledge/knowledge'
import {useTranslations} from 'next-intl'
import {MsgSuccess} from '@/utils/message'

export interface SyncWebDialogRef {
  open: (knowledgeId: string) => void
}

const SyncWebDialog = forwardRef<SyncWebDialogRef, {}>(function SyncWebDialog(_props, ref) {
  const [open, setOpen] = useState(false)
  const [knowledgeId, setKnowledgeId] = useState('')
  const [syncType, setSyncType] = useState('replace')
  const [loading, setLoading] = useState(false)
  const t = useTranslations()

  useImperativeHandle(ref, () => ({
    open: (id: string) => {
      setKnowledgeId(id)
      setSyncType('replace')
      setOpen(true)
    },
  }))

  const submit = () => {
    setLoading(true)
    knowledgeApi
      .putSyncWebKnowledge(knowledgeId, syncType)
      .then(() => {
        setLoading(false)
        setOpen(false)
        MsgSuccess(t('common.submitSuccess'))
      })
      .catch(() => setLoading(false))
  }

  return (
    <Modal
      title={t('views.knowledge.setting.sync')}
      open={open}
      onCancel={() => setOpen(false)}
      destroyOnClose
      footer={[
        <Button key="c" onClick={() => setOpen(false)}>
          {t('common.cancel')}
        </Button>,
        <Button key="ok" type="primary" loading={loading} onClick={submit}>
          {t('common.confirm')}
        </Button>,
      ]}
    >
      <Radio.Group value={syncType} onChange={(e) => setSyncType(e.target.value)}>
        <Radio value="replace">{t('views.knowledge.setting.syncReplace')}</Radio>
        <Radio value="complete">{t('views.knowledge.setting.syncComplete')}</Radio>
      </Radio.Group>
    </Modal>
  )
})

export default SyncWebDialog
