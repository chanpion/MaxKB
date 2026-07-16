'use client'
import React, {forwardRef, useImperativeHandle, useState, useEffect} from 'react'
import {Drawer, Table, Button, Input, Select, message, Typography, Space, Popconfirm, Spin} from 'antd'
import {useTranslations} from 'next-intl'
import {systemApi} from '@/lib/api/system'

export interface ResourceAuthorizationDrawerRef {
  open: (resourceId: string) => void
}

/* 资源授权抽屉（KNOWLEDGE / APPLICATION / TOOL / MODEL）。
   读取资源已授权的用户（资源映射），并可按用户授予 / 撤销权限。 */
const ResourceAuthorizationDrawer = forwardRef<ResourceAuthorizationDrawerRef, {type?: string}>(
  function ResourceAuthorizationDrawer({type = 'KNOWLEDGE'}, ref) {
    const [open, setOpen] = useState(false)
    const [resourceId, setResourceId] = useState('')
    const [list, setList] = useState<any[]>([])
    const [loading, setLoading] = useState(false)
    const [userId, setUserId] = useState('')
    const [perm, setPerm] = useState<string[]>(['VIEW'])
    const t = useTranslations()

    useImperativeHandle(ref, () => ({
      open: (id: string) => {
        setResourceId(id)
        setOpen(true)
      },
    }))

    const load = () => {
      setLoading(true)
      systemApi.getResourceMapping(type, resourceId)
        .then((res: any) => setList(res.data || []))
        .catch(() => setList([]))
        .finally(() => setLoading(false))
    }
    useEffect(() => {
      if (open && resourceId) load()
    }, [open, resourceId])

    const grant = () => {
      if (!userId) {
        message.warning('请输入用户 ID')
        return
      }
      systemApi.postUserResourcePermission(userId, type, {
        target: resourceId,
        auth_type: 'ROLE',
        permission_list: perm,
      })
        .then(() => {
          message.success('授权成功')
          setUserId('')
          load()
        })
        .catch(() => {})
    }
    const revoke = (id: string) => {
      systemApi.delResourcePermission(id)
        .then(() => {
          message.success('已撤销')
          load()
        })
        .catch(() => {})
    }

    return (
      <Drawer
        title={t('views.system.resourceAuthorization.title')}
        open={open}
        onClose={() => setOpen(false)}
        width={480}
        destroyOnClose
        extra={
          <Button type="primary" onClick={grant} disabled={!userId}>
            授权
          </Button>
        }
      >
        <Typography.Paragraph type="secondary">{type} · {resourceId}</Typography.Paragraph>
        <Space style={{marginBottom: 16}}>
          <Input
            placeholder="用户 ID"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            style={{width: 200}}
          />
          <Select
            mode="multiple"
            value={perm}
            onChange={setPerm}
            style={{width: 220}}
            options={[
              {value: 'VIEW', label: '查看'},
              {value: 'EDIT', label: '编辑'},
              {value: 'MANAGE', label: '管理'},
            ]}
          />
        </Space>
        {loading ? (
          <div style={{textAlign: 'center', padding: 40}}><Spin /></div>
        ) : (
          <Table
            dataSource={list}
            rowKey="id"
            pagination={false}
            size="small"
            columns={[
              {title: '目标', dataIndex: 'target_id', key: 'target_id', ellipsis: true},
              {title: '类型', dataIndex: 'target_type', key: 'target_type'},
              {title: '权限', dataIndex: 'permission_list', key: 'permission_list', render: (v: string[]) => (v || []).join(',')},
              {
                title: '操作',
                key: 'op',
                width: 80,
                render: (_: any, row: any) => (
                  <Popconfirm title="确认撤销？" onConfirm={() => revoke(row.id)}>
                    <Button type="link" danger size="small">
                      撤销
                    </Button>
                  </Popconfirm>
                ),
              },
            ]}
          />
        )}
      </Drawer>
    )
  },
)

export default ResourceAuthorizationDrawer
