'use client'
import React, {useEffect, useState} from 'react'
import {
  Breadcrumb, Table, Button, Space, Typography, Upload, Tag, message, Modal, Spin,
  Form, Radio, InputNumber,
} from 'antd'
import {HomeOutlined, FileTextOutlined, UploadOutlined, DeleteOutlined, ReloadOutlined, SettingOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {useRouter} from '@/i18n/navigation'
import {useTranslations} from 'next-intl'
import {documentApi} from '@/lib/api/knowledge/document'
import {dateFormat} from '@/utils/time'

export default function KnowledgeDocumentPage() {
  const t = useTranslations('menu')
  const router = useRouter()
  const params = useParams()
  const kid = params.id as string
  const [docs, setDocs] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [hitOpen, setHitOpen] = useState(false)
  const [hitSaving, setHitSaving] = useState(false)
  const [hitForm] = Form.useForm()

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

  const openHitModal = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先勾选要设置的文档')
      return
    }
    hitForm.setFieldsValue({hit_handling_method: 'optimization', directly_return_similarity: 0.9})
    setHitOpen(true)
  }

  const handleHitOk = () => {
    hitForm.validateFields().then((values: any) => {
      const payload: any = {
        id_list: selectedRowKeys,
        hit_handling_method: values.hit_handling_method,
      }
      if (values.hit_handling_method === 'directly_return') {
        payload.directly_return_similarity = values.directly_return_similarity
      }
      setHitSaving(true)
      documentApi.putBatchHitHandling(kid, payload).then(() => {
        message.success('命中设置已更新')
        setHitOpen(false)
        loadDocs()
      }).catch(() => {}).finally(() => setHitSaving(false))
    })
  }

  const columns = [
    {title: '文档名称', dataIndex: 'name', key: 'name', render: (n: string) => <><FileTextOutlined style={{marginRight: 8}} />{n}</>},
    {title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (s: string) => <Tag color={s === '1' ? 'green' : 'orange'}>{s === '1' ? '已完成' : '处理中'}</Tag>},
    {title: '命中方式', dataIndex: 'hit_handling_method', key: 'hit_handling_method', width: 120,
      render: (v: string) => v === 'directly_return' ? '直接返回' : '优化' },
    {title: '相似度', dataIndex: 'directly_return_similarity', key: 'directly_return_similarity', width: 100,
      render: (v: number) => (v ?? '-')},
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

  return (
    <div>
      <Breadcrumb style={{marginBottom: 12}} items={[
        {title: <><HomeOutlined /> {t('home')}</>},
        {title: <><FileTextOutlined /> 知识库详情</>},
      ]} />
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16}}>
        <Typography.Title level={4} style={{margin: 0}}>文档管理</Typography.Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadDocs}>刷新</Button>
          <Button icon={<SettingOutlined />} onClick={openHitModal}>批量设置命中方式</Button>
          <Upload beforeUpload={(file) => {
            const fileName = file.name
            documentApi.uploadSourceFile(kid, file).then((res: any) => {
              const path: string = res?.data ?? ''
              const source_file_id = path.split('/').pop()
              if (!source_file_id) { message.error('上传文件失败'); return }
              documentApi.createDocument(kid, {name: fileName, source_file_id}).then(() => {
                message.success('上传成功')
                loadDocs()
              }).catch(() => {})
            }).catch(() => {})
            return false
          }} showUploadList={false}>
            <Button type="primary" icon={<UploadOutlined />}>上传文档</Button>
          </Upload>
        </Space>
      </div>
      <Table
        dataSource={docs} columns={columns} rowKey="id" loading={loading}
        pagination={{pageSize: 20}} size="middle"
        rowSelection={{selectedRowKeys, onChange: (keys: any) => setSelectedRowKeys(keys)}}
      />

      <Modal
        title="批量设置命中方式"
        open={hitOpen}
        confirmLoading={hitSaving}
        okText="确定"
        cancelText="取消"
        onOk={handleHitOk}
        onCancel={() => setHitOpen(false)}
      >
        <Form form={hitForm} layout="vertical">
          <Form.Item name="hit_handling_method" label="命中方式" rules={[{required: true}]}>
            <Radio.Group>
              <Radio value="optimization">优化（向量检索后综合排序）</Radio>
              <Radio value="directly_return">直接返回（命中即返回）</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(p, c) => p.hit_handling_method !== c.hit_handling_method}>
            {({getFieldValue}) => getFieldValue('hit_handling_method') === 'directly_return' ? (
              <Form.Item
                name="directly_return_similarity"
                label="相似度阈值"
                rules={[{required: true, message: '请输入相似度阈值'}]}
              >
                <InputNumber min={0} max={2} step={0.1} style={{width: 200}} placeholder="0 ~ 2" />
              </Form.Item>
            ) : null}
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
