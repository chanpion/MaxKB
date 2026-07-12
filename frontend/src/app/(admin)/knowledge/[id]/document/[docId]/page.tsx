'use client'
import React, {useEffect, useState, useRef} from 'react'
import {Breadcrumb, Card, Button, Typography, List, Spin, Input, Modal, Form, message, Space, Tag, Empty, Popconfirm} from 'antd'
import {HomeOutlined, FileTextOutlined, ArrowLeftOutlined, PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {useRouter} from '@/i18n/navigation'
import {paragraphApi} from '@/lib/api/knowledge/paragraph'
import {get} from '@/lib/request'
import {useUserStore} from '@/store'
import {dateFormat} from '@/utils/time'

function ws() { return useUserStore.getState().getWorkspaceId() }

export default function ParagraphPage() {
  const router = useRouter()
  const params = useParams()
  const kid = params.id as string
  const docId = params.docId as string
  const [doc, setDoc] = useState<any>(null)
  const [list, setList] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editItem, setEditItem] = useState<any>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  useEffect(() => {
    get(`/workspace/${ws()}/knowledge/${kid}/document/${docId}`).then((res: any) => {
      setDoc(res.data)
    }).catch(() => {})
    loadParagraphs()
  }, [kid, docId])

  const loadParagraphs = () => {
    setLoading(true)
    const params: any = {}
    if (search) params.content = search
    paragraphApi.getList(kid, docId, params).then((res: any) => {
      setList(res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  const handleCreate = () => {
    form.validateFields().then((values) => {
      paragraphApi.postCreate(kid, docId, values).then(() => {
        message.success('创建成功'); setCreateOpen(false); form.resetFields(); loadParagraphs()
      }).catch(() => {})
    })
  }

  const handleEdit = (item: any) => {
    setEditItem(item)
    editForm.setFieldsValue(item)
    setEditOpen(true)
  }

  const handleEditSave = () => {
    editForm.validateFields().then((values) => {
      paragraphApi.putUpdate(kid, docId, editItem.id, values).then(() => {
        message.success('修改成功'); setEditOpen(false); loadParagraphs()
      }).catch(() => {})
    })
  }

  const handleDelete = (pid: string) => {
    paragraphApi.delDelete(kid, docId, pid).then(() => { message.success('删除成功'); loadParagraphs() }).catch(() => {})
  }

  return (
    <div>
      <div style={{display: 'flex', alignItems: 'center', marginBottom: 16, gap: 12}}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.push(`/knowledge/${kid}/document`)}>返回</Button>
        <Breadcrumb items={[
          {title: <><HomeOutlined /> 首页</>},
          {title: <><FileTextOutlined /> {doc?.name || '文档段落'}</>},
        ]} />
      </div>
      <Card style={{borderRadius: 8, marginBottom: 16}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div>
            <Typography.Title level={5} style={{margin: 0}}>{doc?.name || '文档段落'}</Typography.Title>
            <Typography.Text type="secondary">{list.length} 个段落</Typography.Text>
          </div>
          <Space>
            <Input.Search value={search} onChange={(e) => setSearch(e.target.value)} onSearch={loadParagraphs}
              placeholder="搜索段落" style={{width: 240}} allowClear />
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>添加段落</Button>
          </Space>
        </div>
      </Card>
      {loading ? <div style={{textAlign: 'center', padding: 60}}><Spin size="large" /></div>
      : list.length === 0 ? <Empty description="暂无段落" />
      : <List dataSource={list} renderItem={(item: any, i: number) => (
          <List.Item style={{background: '#fff', borderRadius: 8, marginBottom: 8, padding: '16px 20px', display: 'block'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 8}}>
              <Typography.Text type="secondary">#{i + 1}</Typography.Text>
              <Space>
                <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(item)} />
                <Popconfirm title="确认删除？" onConfirm={() => handleDelete(item.id)}>
                  <Button type="link" size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            </div>
            {item.title && <Typography.Text strong style={{display: 'block', marginBottom: 4}}>{item.title}</Typography.Text>}
            <Typography.Paragraph style={{marginBottom: 4, whiteSpace: 'pre-wrap'}}>{item.content}</Typography.Paragraph>
            <Space size={4}>
              {item.is_active === false && <Tag color="default">已禁用</Tag>}
              {item.problem_list?.map((p: any) => <Tag key={p.id} color="blue">{p.content}</Tag>)}
            </Space>
          </List.Item>
        )} />}

      <Modal title="添加段落" open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); form.resetFields() }}>
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="标题"><Input placeholder="段落标题（可选）" /></Form.Item>
          <Form.Item name="content" label="内容" rules={[{required: true, message: '请输入内容'}]}>
            <Input.TextArea rows={5} placeholder="请输入段落内容" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="编辑段落" open={editOpen} onOk={handleEditSave} onCancel={() => setEditOpen(false)}>
        <Form form={editForm} layout="vertical">
          <Form.Item name="title" label="标题"><Input /></Form.Item>
          <Form.Item name="content" label="内容" rules={[{required: true}]}>
            <Input.TextArea rows={5} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
