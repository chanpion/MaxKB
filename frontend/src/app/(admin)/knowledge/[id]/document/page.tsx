'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Table, Button, Space, Typography, Upload, Tag, message, Modal, Spin, Tabs} from 'antd'
import {HomeOutlined, FileTextOutlined, UploadOutlined, DeleteOutlined, ReloadOutlined, QuestionCircleOutlined, BookOutlined, ExperimentOutlined, SettingOutlined, UserOutlined} from '@ant-design/icons'
import {useParams, useRouter, usePathname} from '@/i18n/navigation'
import {useTranslations} from 'next-intl'
import {documentApi} from '@/lib/api/knowledge/document'
import {dateFormat} from '@/utils/time'

export default function KnowledgeDocumentPage() {
  const t = useTranslations('menu')
  const router = useRouter()
  const pathname = usePathname()
  const params = useParams()
  const kid = params.id as string
  const [docs, setDocs] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const loadDocs = () => {
    setLoading(true)
    documentApi.getDocumentList(kid).then((res: any) => {
      setDocs(res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { loadDocs() }, [kid])

  const handleDelete = (docId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后不可恢复，确认删除？',
      onOk: () => documentApi.delDocument(kid, docId).then(() => {
        message.success('删除成功')
        loadDocs()
      }),
    })
  }

  const columns = [
    {title: '文档名称', dataIndex: 'name', key: 'name', render: (n: string) => <><FileTextOutlined style={{marginRight: 8}} />{n}</>},
    {title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (s: string) => <Tag color={s === '1' ? 'green' : 'orange'}>{s === '1' ? '已完成' : '处理中'}</Tag>},
    {title: '段落数', dataIndex: 'paragraph_count', key: 'paragraph_count', width: 100},
    {title: '字符数', dataIndex: 'char_length', key: 'char_length', width: 100,
      render: (v: number) => (v || 0).toLocaleString()},
    {title: '创建时间', dataIndex: 'create_time', key: 'create_time', width: 180,
      render: (t: string) => dateFormat(t)},
    {title: '操作', key: 'action', width: 180,
      render: (_: any, row: any) => (
        <Space>
          <Button type="link" size="small" icon={<FileTextOutlined />}
            onClick={() => router.push(`/knowledge/${kid}/document/${row.id}`)}>段落</Button>
          <Button type="link" size="small" danger icon={<DeleteOutlined />}
            onClick={() => handleDelete(row.id)}>删除</Button>
        </Space>
      )},
  ]

  const tabItems = [
    {key: 'document', label: <><FileTextOutlined /> 文档</>,},
    {key: 'problem', label: <><QuestionCircleOutlined /> 问题</>,},
    {key: 'termbase', label: <><BookOutlined /> 术语库</>,},
    {key: 'hit-test', label: <><ExperimentOutlined /> 命中测试</>,},
    {key: 'chat-user', label: <><UserOutlined /> 对话用户</>,},
    {key: 'setting', label: <><SettingOutlined /> 设置</>,},
  ]

  return (
    <div>
      <Breadcrumb style={{marginBottom: 12}} items={[
        {title: <><HomeOutlined /> {t('home')}</>},
        {title: <><FileTextOutlined /> 知识库详情</>},
      ]} />
      <Tabs activeKey={pathname.split('/').pop()} items={tabItems}
        onChange={(key) => router.push(`/knowledge/${kid}/${key}`)}
        style={{marginBottom: 8}} />
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16}}>
        <Typography.Title level={4} style={{margin: 0}}>文档管理</Typography.Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadDocs}>刷新</Button>
          <Upload beforeUpload={(file) => {
            const form = new FormData()
            form.append('file', file)
            documentApi.postDocumentUpload(kid, form).then(() => {
              message.success('上传成功')
              loadDocs()
            }).catch(() => {})
            return false
          }} showUploadList={false}>
            <Button type="primary" icon={<UploadOutlined />}>上传文档</Button>
          </Upload>
        </Space>
      </div>
      <Table dataSource={docs} columns={columns} rowKey="id" loading={loading}
        pagination={{pageSize: 20}} size="middle" />
    </div>
  )
}
