'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Drawer, Table, Switch, Button, message, Typography} from 'antd'
import {useTranslations} from 'next-intl'

export interface WorkspaceAuthorizationDrawerRef {
  open: (resourceId: string) => void
}

// 系统资源授权给工作空间抽屉（systemShare 模式）。
// 当前为桩实现：展示可选工作空间列表供开关授权，保存暂未对接后端 systemShare 授权接口。
const WorkspaceAuthorizationDrawer = forwardRef<WorkspaceAuthorizationDrawerRef, {type?: string}>(
  function WorkspaceAuthorizationDrawer({type = 'MODEL'}, ref) {
    const [open, setOpen] = useState(false)
    const [resourceId, setResourceId] = useState('')
    const [data, setData] = useState<Array<any>>([{key: 'default', name: '默认工作空间', authorized: false}])
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
      // TODO: 对接后端 systemShare 授权接口（apps/models_provider 等），此处暂为桩实现。
      message.success(t('common.saveSuccess'))
      setOpen(false)
    }

    return (
      <Drawer
        title={t('views.shared.authorized_workspace')}
        open={open}
        onClose={() => setOpen(false)}
        width={480}
        destroyOnClose
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
              render: (val: boolean, row: any) => <Switch checked={val} onChange={(v) => toggle(row.key, v)} />,
            },
          ]}
        />
      </Drawer>
    )
  },
)

export default WorkspaceAuthorizationDrawer
