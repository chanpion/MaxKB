'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Modal} from 'antd'
import {RawIcon} from '@/components/AppIcon'
import {loadSharedApi} from '@/lib/api/shared-api'
import {useTranslations} from 'next-intl'

export interface SelectProviderDialogRef {
  open: () => void
}

const SelectProviderDialog = forwardRef<SelectProviderDialogRef, {onChange: (p: any) => void}>(
  function SelectProviderDialog({onChange}, ref) {
    const [open, setOpen] = useState(false)
    const [list, setList] = useState<any[]>([])
    const t = useTranslations()

    useImperativeHandle(ref, () => ({
      open: () => {
        setOpen(true)
        loadSharedApi({type: 'provider'})
          .getProvider()
          .then((ok: any) => setList(ok.data || []))
          .catch(() => setList([]))
      },
    }))

    const select = (p: any) => {
      setOpen(false)
      onChange(p)
    }

    return (
      <Modal
        title={t('views.model.providerPlaceholder')}
        open={open}
        onCancel={() => setOpen(false)}
        footer={null}
        destroyOnClose
        width={480}
      >
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8}}>
          {list.map((item) => (
            <div
              key={item.provider || item.name}
              onClick={() => select(item)}
              style={{
                display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px',
                cursor: 'pointer', borderRadius: 6, border: '1px solid #f0f0f0',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#1677FF'; e.currentTarget.style.background = 'rgba(22,119,255,0.04)' }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#f0f0f0'; e.currentTarget.style.background = 'transparent' }}
            >
              <RawIcon html={item.icon} />
              <span className="ellipsis-1">{item.name}</span>
            </div>
          ))}
        </div>
      </Modal>
    )
  },
)

export default SelectProviderDialog
