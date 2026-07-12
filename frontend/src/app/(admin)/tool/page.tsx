'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Row, Col, Select, Button, Card, Typography, Empty, Spin, Tag, Modal, Form, Input, message} from 'antd'
import {HomeOutlined, ToolOutlined, PlusOutlined, DeleteOutlined} from '@ant-design/icons'
import FolderVirtualizedTree from '@/components/folder-virtualized-tree/FolderVirtualizedTree'
import {SourceTypeEnum} from '@/enums/common'
import {useFolderStore, useUserStore} from '@/store'
import {useTranslations} from 'next-intl'
import {toolApi} from '@/lib/api/tool/tool'

export default function ToolPage() {
  const t = useTranslations('menu')
  const folder = useFolderStore()
  const user = useUserStore()
  const [toolList, setToolList] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [toolType, setToolType] = useState<string>('')
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const breadcrumbItems = [
    {title: <><HomeOutlined /> {t('home')}</>},
    {title: <><ToolOutlined /> {folder.currentFolder?.name || t('tool')}</>},
  ]

  const loadTools = () => {
    setLoading(true)
    const params: any = {folder_id: folder.currentFolder?.id || user.getWorkspaceId()}
    if (toolType) params.tool_type = toolType
    toolApi.getToolList(params).then((res: any) => {
      setToolList(res.data?.tools || res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { loadTools() }, [folder.currentFolder?.id, toolType])

  const handleCreate = () => {
    form.validateFields().then((values) => {
      toolApi.postTool({...values, folder_id: folder.currentFolder?.id || user.getWorkspaceId()})
        .then(() => { message.success('创建成功'); setCreateOpen(false); form.resetFields(); loadTools() })
        .catch(() => {})
    })
  }

  const handleDelete = (id: string, name: string) => {
    Modal.confirm({title: '确认删除', content: `确认删除工具「${name}」？`,
      onOk: () => toolApi.delTool(id).then(() => { message.success('删除成功'); loadTools() }),
    })
  }

  const toolTypeOptions = [
    {value: '', label: '全部'},
    {value: 'CUSTOM', label: '工具'},
    {value: 'SKILL', label: 'Skills'},
    {value: 'WORKFLOW', label: '工作流'},
    {value: 'MCP', label: 'MCP'},
    {value: 'DATA_SOURCE', label: '数据源'},
  ]

  return (
    <div style={{display: 'flex', gap: 16, height: 'calc(100vh - 56px - 48px)'}}>
      <div style={{width: 240, overflow: 'auto', background: '#fff', borderRadius: 8, padding: 8, flexShrink: 0, display: 'flex', flexDirection: 'column'}}>
        <div style={{padding: '8px 8px 4px', fontWeight: 500, fontSize: 14}}>{t('tool')}</div>
        <FolderVirtualizedTree source={SourceTypeEnum.TOOL} />
      </div>
      <div style={{flex: 1, overflow: 'auto', background: '#fff', borderRadius: 8, padding: 16}}>
        <Breadcrumb items={breadcrumbItems} style={{marginBottom: 16}} />
        <div style={{display: 'flex', alignItems: 'center', marginBottom: 16, gap: 8}}>
          <Select value={toolType} onChange={setToolType} style={{width: 120}} options={toolTypeOptions} />
          <Button type="primary" icon={<PlusOutlined />} style={{marginLeft: 'auto'}} onClick={() => setCreateOpen(true)}>
            添加工具
          </Button>
        </div>
        {loading ? (
          <div style={{textAlign: 'center', padding: 60}}><Spin /></div>
        ) : toolList.length === 0 ? (
          <Empty description="暂无工具" />
        ) : (
          <Row gutter={[16, 16]}>
            {toolList.map((item: any) => (
              <Col key={item.id} xs={24} sm={12} md={12} lg={8} xl={6}>
                <Card hoverable style={{borderRadius: 8}}
                  title={<div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                    <ToolOutlined style={{fontSize: 18, color: '#1677FF'}} />
                    <Typography.Text ellipsis>{item.name}</Typography.Text>
                  </div>}
                  extra={<Tag>{item.tool_type || 'CUSTOM'}</Tag>}
                  actions={[<DeleteOutlined key="del" onClick={() => handleDelete(item.id, item.name)} />]}>
                  <Typography.Paragraph ellipsis={{rows: 2}} type="secondary" style={{marginBottom: 0, minHeight: 40}}>
                    {item.desc || '暂无描述'}
                  </Typography.Paragraph>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </div>
      <Modal title="添加工具" open={createOpen} onOk={handleCreate} onCancel={() => setCreateOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="工具名称" rules={[{required: true, message: '请输入名称'}]}>
            <Input placeholder="请输入工具名称" />
          </Form.Item>
          <Form.Item name="desc" label="描述">
            <Input.TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
