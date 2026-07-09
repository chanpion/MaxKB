'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Modal, Radio, Button} from 'antd'
import {useTranslations} from 'next-intl'

export interface ExportKnowledgeDialogRef {
  open: (onExport: (withSourceFile: boolean) => void) => void
}

const ExportKnowledgeDialog = forwardRef<ExportKnowledgeDialogRef, {}>(function ExportKnowledgeDialog(_props, ref) {
  const [open, setOpen] = useState(false)
  const [withSource, setWithSource] = useState(false)
  const [onExport, setOnExport] = useState<(b: boolean) => void>(() => {})
  const t = useTranslations()

  useImperativeHandle(ref, () => ({
    open: (cb: (withSourceFile: boolean) => void) => {
      setOnExport(() => cb)
      setWithSource(false)
      setOpen(true)
    },
  }))

  const submit = () => {
    onExport(withSource)
    setOpen(false)
  }

  return (
    <Modal
      title={t('views.document.setting.exportKnowledge')}
      open={open}
      onCancel={() => setOpen(false)}
      destroyOnClose
      footer={[
        <Button key="c" onClick={() => setOpen(false)}>
          {t('common.cancel')}
        </Button>,
        <Button key="ok" type="primary" onClick={submit}>
          {t('common.export')}
        </Button>,
      ]}
    >
      <Radio.Group value={withSource} onChange={(e) => setWithSource(e.target.value)}>
        <Radio value={false}>{t('views.knowledge.export.withoutSource')}</Radio>
        <Radio value>{t('views.knowledge.export.withSource')}</Radio>
      </Radio.Group>
    </Modal>
  )
})

export default ExportKnowledgeDialog
