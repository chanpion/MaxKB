'use client'
import React, {forwardRef, useImperativeHandle, useState, useEffect} from 'react'
import {Drawer, Table, Typography, Tag, Empty, Spin, message} from 'antd'
import {useTranslations} from 'next-intl'
import {systemApi} from '@/lib/api/system'

export interface WorkspaceAuthorizationDrawerRef {
  open: (resourceId: string) => void
}

/* 资源授权给工作空间抽屉（systemShare 模式）。
   读取已共享到工作空间的映射；新增共享依赖后端 systemShare 授权接口（待实现）。 */
const WorkspaceAuthorizationDrawer = forwardRef<WorkspaceAuthorizationDrawerRef, {type?: string}>(
  function WorkspaceAuthorizationDrawer({type = 'MODEL'}, ref) {
    const [open, setOpen] = useState(false)
    const [resourceId, setResourceId] = useState('')
    const [list, setList] = useState<any[]>([])
    const [loading, setLoading] = useState(false)
    const t = useTranslations()

    useImperativeHandle(ref, () => ({
      open: (id: string) => {
        setResourceId(id)
        setOpen(true)
      },
    }))

    useEffect(() => {
      if (open && resourceId) {
        setLoading(true)
        systemApi.getResourceMapping(type, resourceId, 'WORKSPACE')
          .then((res: any) => setList(res.data || []))
          .catch(() => setList([]))
          .finally(() => setLoading(false))
      }
    }, [open, resourceId])

    return (
      <Drawer
        title={t('views.shared.authorized_workspace')}
        open={open}
        onClose={() => setOpen(false)}
        width={480}
        destroyOnClose
        extra={
          <span style={{color: '#999', fontSize: 12}} onClick={() => message.info('后端共享授权接口待实现')}>
            新增共享
          </span>
        }
      >
        <Typography.Paragraph type="secondary">{type} · {resourceId}</Typography.Paragraph>
        {loading ? (
          <div style={{textAlign: 'center', padding: 40}}><Spin /></div>
        ) : list.length === 0 ? (
          <Empty description="尚未共享到工作空间" />
        ) : (
          <Table
            dataSource={list}
            rowKey="id"
            pagination={false}
            size="small"
            columns={[
              {title: '源类型', dataIndex: 'source_type', key: 'source_type', render: (v: string) => <Tag>{v}</Tag>},
              {title: '工作空间', dataIndex: 'target_id', key: 'target_id', ellipsis: true},
            ]}
          />
        )}
      </Drawer>
    )
  },
)

export default WorkspaceAuthorizationDrawer
