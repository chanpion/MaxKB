'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Drawer, Empty, message, Typography} from 'antd'
import {useTranslations} from 'next-intl'

export interface ResourceMappingDrawerRef {
  open: (type: string, resource: any) => void
}

// 资源映射抽屉。workspace 模式下为桩实现。
const ResourceMappingDrawer = forwardRef<ResourceMappingDrawerRef, {}>(function ResourceMappingDrawer(_props, ref) {
  const [open, setOpen] = useState(false)
  const [resource, setResource] = useState<any>(null)
  const t = useTranslations()

  useImperativeHandle(ref, () => ({
    open: (type: string, res: any) => {
      setResource({type, ...res})
      setOpen(true)
    },
  }))

  return (
    <Drawer
      title={t('views.system.resourceMapping.title')}
      open={open}
      onClose={() => setOpen(false)}
      width={480}
      destroyOnClose
    >
      <Typography.Paragraph type="secondary">{resource?.name}</Typography.Paragraph>
      <Empty description={t('common.noData')} />
    </Drawer>
  )
})

export default ResourceMappingDrawer
