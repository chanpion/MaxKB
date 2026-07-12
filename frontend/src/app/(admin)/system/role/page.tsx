'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Table, Button, Space, Typography, Card, Tag, message, Tabs, Spin} from 'antd'
import {HomeOutlined, TeamOutlined, SettingOutlined, UserOutlined, AppstoreOutlined, ToolOutlined, DatabaseOutlined} from '@ant-design/icons'
import {useTranslations} from 'next-intl'
import {systemApi} from '@/lib/api/system'

export default function RolePage() {
  const t = useTranslations('menu')
  const [internalRoles, setInternalRoles] = useState<any[]>([])
  const [customRoles, setCustomRoles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    systemApi.getRoleList().then((res: any) => {
      const data = res.data || {}
      setInternalRoles(data.internal_role || [])
      setCustomRoles(data.custom_role || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const columns = [
    {title: '角色名称', dataIndex: 'name', key: 'name'},
    {title: '类型', dataIndex: 'role_type', key: 'role_type', width: 100,
      render: (v: string) => <Tag>{v === 'INTERNAL' ? '内置' : '自定义'}</Tag>},
    {title: '成员数', dataIndex: 'member_count', key: 'member_count', width: 80},
    {title: '描述', dataIndex: 'desc', key: 'desc', ellipsis: true},
  ]

  return (
    <div>
      <Breadcrumb style={{marginBottom: 16}} items={[
        {title: <><HomeOutlined /> {t('home')}</>},
        {title: <><TeamOutlined /> 角色管理</>},
      ]} />
      <Typography.Title level={4} style={{marginBottom: 16}}>角色管理</Typography.Title>
      {loading ? <div style={{textAlign: 'center', padding: 60}}><Spin size="large" /></div> : (
        <>
          <Card style={{borderRadius: 8, marginBottom: 16}} title="内置角色">
            <Table dataSource={internalRoles} columns={columns} rowKey="id" pagination={false} size="middle" />
          </Card>
          <Card style={{borderRadius: 8}} title="自定义角色">
            <Table dataSource={customRoles} columns={columns} rowKey="id" pagination={false} size="middle" />
          </Card>
        </>
      )}
    </div>
  )
}
