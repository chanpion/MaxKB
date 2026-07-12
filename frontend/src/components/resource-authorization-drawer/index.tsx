'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Drawer, Table, Switch, Button, message, Typography} from 'antd'
import {useTranslations} from 'next-intl'

export interface ResourceAuthorizationDrawerRef {
  open: (resourceId: string) => void
}

// 资源授权抽屉（MODEL / KNOWLEDGE）。workspace 模式下为桩实现，展示授权目标列表。
const ResourceAuthorizationDrawer = forwardRef<ResourceAuthorizationDrawerRef, {type?: string}>(
  function ResourceAuthorizationDrawer({type = 'KNOWLEDGE'}, ref) {
    const [open, setOpen] = useState(false)
    const [resourceId, setResourceId] = useState('')
    const [data, setData] = useState<Array<any>>([
      {key: 'user', name: '工作空间成员', authorized: true},
      {key: 'workspace', name: '当前工作空间', authorized: true},
    ])
    const t = useTranslations()

    useImperativeHandle(ref, () => ({
      open: (id: string) => {
        setResourceId(id)
        setOpen(true)
      },
    }))

    const toggle = (key: string, val: boolean) => {
      setData((d) => d.map((row) => (row.key === key ? {...row, authorized: val} : row)))
    }

    const save = () => {
      // workspace 模式：桩实现
      message.success(t('common.saveSuccess'))
      setOpen(false)
    }

    return (
      <Drawer
        title={t('views.system.resourceAuthorization.title')}
        open={open}
        onClose={() => setOpen(false)}
        width={480}
        destroyOnHidden
        extra={
          <Button type="primary" onClick={save}>
            {t('common.save')}
          </Button>
        }
      >
        <Typography.Paragraph type="secondary">
          {type} · {resourceId}
        </Typography.Paragraph>
        <Table
          dataSource={data}
          pagination={false}
          columns={[
            {title: t('common.name'), dataIndex: 'name'},
            {
              title: t('common.authorization'),
              dataIndex: 'authorized',
              render: (val: boolean, row: any) => (
                <Switch checked={val} onChange={(v) => toggle(row.key, v)} />
              ),
            },
          ]}
        />
      </Drawer>
    )
  },
)

export default ResourceAuthorizationDrawer
