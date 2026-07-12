'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Drawer, InputNumber, Button, message} from 'antd'
import knowledgeApi from '@/lib/api/knowledge/knowledge'
import {useTranslations} from 'next-intl'

export interface GenerateRelatedDialogRef {
  open: (list: any[], type: string, row: any) => void
}

// 生成关联问题对话框
const GenerateRelatedDialog = forwardRef<GenerateRelatedDialogRef, {}>(function GenerateRelatedDialog(_props, ref) {
  const [open, setOpen] = useState(false)
  const [row, setRow] = useState<any>(null)
  const [count, setCount] = useState(3)
  const [loading, setLoading] = useState(false)
  const t = useTranslations()

  useImperativeHandle(ref, () => ({
    open: (_list: any[], _type: string, r: any) => {
      setRow(r)
      setOpen(true)
    },
  }))

  const submit = () => {
    if (!row?.id) return
    setLoading(true)
    knowledgeApi
      .putGenerateRelated(row.id, {count})
      .then(() => {
        message.success(t('common.submitSuccess'))
        setOpen(false)
      })
      .catch(() => setLoading(false))
      .finally(() => setLoading(false))
  }

  return (
    <Drawer
      title={t('views.document.generateQuestion.title')}
      open={open}
      onClose={() => setOpen(false)}
      width={420}
      destroyOnHidden
      footer={
        <Button type="primary" loading={loading} onClick={submit} block>
          {t('common.confirm')}
        </Button>
      }
    >
      <div style={{marginBottom: 8}}>{t('views.document.generateQuestion.count')}</div>
      <InputNumber min={1} max={20} value={count} onChange={(v) => setCount(v || 1)} style={{width: '100%'}} />
    </Drawer>
  )
})

export default GenerateRelatedDialog
