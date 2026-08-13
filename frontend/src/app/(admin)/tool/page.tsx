'use client'
import React, {useCallback, useEffect, useRef, useState} from 'react'
import {Button, Card, Dropdown, Empty, Input, Menu, Select, Space, Table, Tag, message, Typography, Tree, Modal} from 'antd'
import type {ColumnsType} from 'antd/es/table'
import {
  PlusOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  BugOutlined,
  AppstoreOutlined,
  FolderOutlined,
  SearchOutlined,
  ApartmentOutlined,
} from '@ant-design/icons'
import {useUserStore} from '@/store'
import {useRouter} from '@/i18n/navigation'
import {toolApi} from '@/lib/api/tool/tool'
import ToolFormDrawer from './components/ToolFormDrawer'
import McpToolFormDrawer from './components/McpToolFormDrawer'
import ToolDebugDrawer from './components/ToolDebugDrawer'
import {useTranslations} from 'next-intl'

const TYPE_TAG: Record<string, {color: string; label: string}> = {
  FUNCTION: {color: 'blue', label: '函数'},
  SKILL: {color: 'purple', label: '技能'},
  MCP: {color: 'green', label: 'MCP'},
  DATA_SOURCE: {color: 'orange', label: '数据源'},
}

interface ToolRow {
  id: string
  name: string
  desc?: string
  tool_type: string
  is_active?: boolean
}

export default function ToolPage() {
  const t = useTranslations('menu')
  const router = useRouter()
  const workspaceId = useUserStore((s) => s.getWorkspaceId?.() || s.workspace_id || 'default')
  const [tools, setTools] = useState<ToolRow[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(10)
  const [loading, setLoading] = useState(false)
  const [typeFilter, setTypeFilter] = useState<string | undefined>()
  const [folderTree, setFolderTree] = useState<any[]>([])
  const [selectedKeys, setSelectedKeys] = useState<string[]>(['all'])
  const [keyword, setKeyword] = useState('')

  const [formOpen, setFormOpen] = useState(false)
  const [mcpOpen, setMcpOpen] = useState(false)
  const [debugOpen, setDebugOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [debugTool, setDebugTool] = useState<any>(null)
  const selectedRowKeys = useRef<string[]>([])

  const currentFolderId = selectedKeys[0] === 'all' ? undefined : selectedKeys[0]

  const loadTools = useCallback(() => {
    setLoading(true)
    const params: any = {page, size, workspace_id: workspaceId, folder_id: currentFolderId, name: keyword || undefined, tool_type: typeFilter}
    toolApi
      .getToolList(params)
      .then((res: any) => {
        const data = res?.data ?? res
        const list = (data?.list || []).map((it: any) => ({
          id: it.id,
          name: it.name,
          desc: it.desc,
          tool_type: it.tool_type || 'FUNCTION',
          is_active: it.is_active,
        }))
        setTools(list)
        setTotal(data?.total ?? list.length)
      })
      .catch(() => message.error('加载工具失败'))
      .finally(() => setLoading(false))
  }, [page, size, workspaceId, currentFolderId, keyword, typeFilter])

  const loadFolders = useCallback(() => {
    toolApi
      .getFolder(workspaceId)
      .then((res: any) => {
        const raw = Array.isArray(res?.data) ? res.data : res?.data?.records || []
        const toNode = (f: any): any => ({
          key: f.id,
          title: f.name,
          icon: <FolderOutlined />,
          children: f.children?.length ? f.children.map(toNode) : undefined,
        })
        setFolderTree([{key: 'all', title: '全部工具', icon: <AppstoreOutlined />}, ...raw.map(toNode)])
      })
      .catch(() => {})
  }, [workspaceId])

  useEffect(() => {
    loadFolders()
  }, [loadFolders])

  useEffect(() => {
    loadTools()
  }, [loadTools])

  const handleSelect = (keys: any[]) => {
    if (keys.length) setSelectedKeys(keys)
  }

  const openCreate = (type: 'FUNCTION' | 'MCP' | 'SKILL' | 'DATA_SOURCE') => {
    setEditing(null)
    if (type === 'MCP') setMcpOpen(true)
    else {
      // 预置类型后打开通用表单
      setEditing({tool_type: type})
      setFormOpen(true)
    }
  }

  const openEdit = (row: ToolRow) => {
    toolApi
      .getToolDetail(row.id)
      .then((res: any) => {
        const full = res?.data ?? res
        setEditing(full)
        if (full.tool_type === 'MCP') setMcpOpen(true)
        else setFormOpen(true)
      })
      .catch(() => message.error('加载详情失败'))
  }

  const handleDelete = (row: ToolRow) => {
    Modal.confirm({
      title: '确认删除',
      content: `删除工具「${row.name}」？`,
      okText: '删除',
      okButtonProps: {danger: true},
      onOk: () =>
        toolApi
          .delTool(row.id)
          .then(() => {
            message.success('已删除')
            loadTools()
          })
          .catch((e: any) => message.error(e?.message || '删除失败')),
    })
  }

  const handleBatchDelete = () => {
    const ids = selectedRowKeys.current
    if (!ids.length) return message.warning('请先选择工具')
    Modal.confirm({
      title: '批量删除',
      content: `确认删除选中的 ${ids.length} 个工具？`,
      okText: '删除',
      okButtonProps: {danger: true},
      onOk: () =>
        toolApi
          .batchDelete(ids)
          .then(() => {
            message.success('已删除')
            selectedRowKeys.current = []
            loadTools()
          })
          .catch((e: any) => message.error(e?.message || '删除失败')),
    })
  }

  const columns: ColumnsType<ToolRow> = [
    {
      title: '名称',
      dataIndex: 'name',
      render: (name, row) => (
        <Space>
          <span className="font-medium">{name}</span>
          <Tag color={TYPE_TAG[row.tool_type]?.color}>{TYPE_TAG[row.tool_type]?.label}</Tag>
        </Space>
      ),
    },
    {title: '描述', dataIndex: 'desc', ellipsis: true, render: (v) => v || <Typography.Text type="secondary">—</Typography.Text>},
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 90,
      render: (v) => (v ? <Tag color="success">启用</Tag> : <Tag>停用</Tag>),
    },
    {
      title: '操作',
      width: 140,
      render: (_, row) => (
        <Space size={4}>
          <Button type="text" size="small" icon={<BugOutlined />} onClick={() => {setDebugTool(row); setDebugOpen(true)}} />
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => openEdit(row)} />
          <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(row)} />
        </Space>
      ),
    },
  ]

  const newMenu = (
    <Menu
      items={[
        {key: 'FUNCTION', label: '函数工具', onClick: () => openCreate('FUNCTION')},
        {key: 'MCP', label: 'MCP 工具', onClick: () => openCreate('MCP')},
        {key: 'SKILL', label: '技能工具', onClick: () => openCreate('SKILL')},
        {key: 'DATA_SOURCE', label: '数据源', onClick: () => openCreate('DATA_SOURCE')},
      ]}
    />
  )

  return (
    <div>
      <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12}}>
        <Typography.Title level={4} style={{margin: 0}}>
          工具
        </Typography.Title>
        <Space>
          <Button icon={<ApartmentOutlined />} onClick={() => router.push('/tool/tool-store')}>
            工具库
          </Button>
          <Button danger disabled={!selectedRowKeys.current.length} onClick={handleBatchDelete}>
            批量删除
          </Button>
          <Dropdown overlay={newMenu} trigger={['click']}>
            <Button type="primary" icon={<PlusOutlined />}>
              新建工具
            </Button>
          </Dropdown>
        </Space>
      </div>

      <div style={{display: 'flex', gap: 16, alignItems: 'stretch'}}>
        <Card style={{width: 240, borderRadius: 8}} bodyStyle={{padding: 8, height: 'calc(100vh - 200px)', overflow: 'auto'}}>
          <Tree
            treeData={folderTree}
            selectedKeys={selectedKeys}
            onSelect={handleSelect}
            defaultExpandAll
            blockNode
          />
        </Card>

        <Card style={{flex: 1, borderRadius: 8}} bodyStyle={{padding: 12}}>
          <Space style={{marginBottom: 12, width: '100%', justifyContent: 'space-between'}}>
            <Input
              allowClear
              prefix={<SearchOutlined />}
              placeholder="搜索工具名称"
              style={{width: 260}}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
            <Select
              allowClear
              placeholder="按类型筛选"
              style={{width: 180}}
              value={typeFilter}
              onChange={setTypeFilter}
              options={[
                {value: 'FUNCTION', label: '函数工具'},
                {value: 'MCP', label: 'MCP 工具'},
                {value: 'SKILL', label: '技能工具'},
                {value: 'DATA_SOURCE', label: '数据源'},
              ]}
            />
          </Space>

          <Table
            rowKey="id"
            loading={loading}
            columns={columns}
            dataSource={tools}
            rowSelection={{
              onChange: (keys) => (selectedRowKeys.current = keys as string[]),
            }}
            pagination={{
              current: page,
              pageSize: size,
              total,
              showSizeChanger: true,
              onChange: (p, s) => {
                setPage(p)
                setSize(s)
              },
            }}
            locale={{emptyText: <Empty description="暂无工具" />}}
          />
        </Card>
      </div>

      <ToolFormDrawer open={formOpen} tool={editing} folderId={currentFolderId} onClose={() => setFormOpen(false)} onSaved={loadTools} />
      <McpToolFormDrawer open={mcpOpen} tool={editing} folderId={currentFolderId} onClose={() => setMcpOpen(false)} onSaved={loadTools} />
      <ToolDebugDrawer open={debugOpen} tool={debugTool} onClose={() => setDebugOpen(false)} />
    </div>
  )
}
