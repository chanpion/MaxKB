'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Modal, List} from 'antd'
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
      >
        <List
          dataSource={list}
          renderItem={(item) => (
            <List.Item style={{cursor: 'pointer'}} onClick={() => select(item)}>
              <span style={{display: 'flex', alignItems: 'center', gap: 8}}>
                <RawIcon html={item.icon} />
                <span>{item.name}</span>
              </span>
            </List.Item>
          )}
        />
      </Modal>
    )
  },
)

export default SelectProviderDialog
