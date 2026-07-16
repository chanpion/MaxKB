'use client'
import React, {forwardRef, useImperativeHandle, useState, useEffect} from 'react'
import {Drawer, Table, Typography, Tag, Empty, Spin} from 'antd'
import {useTranslations} from 'next-intl'
import {systemApi} from '@/lib/api/system'

export interface ResourceMappingDrawerRef {
  open: (type: string, resource: any) => void
}

/* 资源映射抽屉：读取资源的映射关系（source → target）。 */
const ResourceMappingDrawer = forwardRef<ResourceMappingDrawerRef, {}>(function ResourceMappingDrawer(_props, ref) {
  const [open, setOpen] = useState(false)
  const [resource, setResource] = useState<any>(null)
  const [list, setList] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const t = useTranslations()

  useImperativeHandle(ref, () => ({
    open: (type: string, res: any) => {
      setResource({type, ...res})
      setOpen(true)
    },
  }))

  useEffect(() => {
    if (open && resource) {
      setLoading(true)
      systemApi.getResourceMapping(resource.type, resource.id)
        .then((res: any) => setList(res.data || []))
        .catch(() => setList([]))
        .finally(() => setLoading(false))
    }
  }, [open, resource])

  return (
    <Drawer
      title={t('views.system.resourceMapping.title')}
      open={open}
      onClose={() => setOpen(false)}
      width={480}
      destroyOnClose
    >
      <Typography.Paragraph type="secondary">{resource?.name}（{resource?.type}）</Typography.Paragraph>
      {loading ? (
        <div style={{textAlign: 'center', padding: 40}}><Spin /></div>
      ) : list.length === 0 ? (
        <Empty description="暂无映射" />
      ) : (
        <Table
          dataSource={list}
          rowKey="id"
          pagination={false}
          size="small"
          columns={[
            {title: '源类型', dataIndex: 'source_type', key: 'source_type', render: (v: string) => <Tag>{v}</Tag>},
            {title: '目标类型', dataIndex: 'target_type', key: 'target_type', render: (v: string) => <Tag>{v}</Tag>},
            {title: '目标 ID', dataIndex: 'target_id', key: 'target_id', ellipsis: true},
          ]}
        />
      )}
    </Drawer>
  )
})

export default ResourceMappingDrawer
