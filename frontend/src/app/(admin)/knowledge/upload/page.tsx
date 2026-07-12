'use client'
import React, {useState, useRef} from 'react'
import {Breadcrumb, Card, Button, Typography, Steps, Upload, message, Spin, Divider, Alert} from 'antd'
import {HomeOutlined, FileTextOutlined, UploadOutlined, ArrowLeftOutlined, CheckCircleOutlined, InboxOutlined} from '@ant-design/icons'
import {useRouter, useSearchParams} from '@/i18n/navigation'
import {useUserStore} from '@/store'
import {post} from '@/lib/request'

const {Dragger} = Upload

function ws() { return useUserStore.getState().getWorkspaceId() }

export default function KnowledgeUploadPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [active, setActive] = useState(0)
  const [loading, setLoading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([])
  const folderId = searchParams?.get('folderId') || ''

  const handleUpload = (file: File) => {
    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('folder_id', folderId || ws())
    post(`/workspace/${ws()}/knowledge/upload`, formData).then((res: any) => {
      message.success('上传成功')
      setUploadedFiles([...uploadedFiles, {name: file.name, status: 'success'}])
      setActive(1)
    }).catch(() => {}).finally(() => setLoading(false))
    return false
  }

  return (
    <div>
      <div style={{display: 'flex', alignItems: 'center', marginBottom: 16, gap: 12}}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.push('/knowledge')}>返回</Button>
        <Breadcrumb items={[
          {title: <><HomeOutlined /> 首页</>},
          {title: <><FileTextOutlined /> 上传文档</>},
        ]} />
      </div>

      <Steps current={active} style={{marginBottom: 24, maxWidth: 600}}
        items={[{title: '上传文档'}, {title: '导入完成'}]} />

      {active === 0 && (
        <Card style={{borderRadius: 8}}>
          <Dragger beforeUpload={handleUpload} showUploadList={false} accept=".txt,.pdf,.doc,.docx,.md,.csv,.json,.xml,.xlsx,.xls,.ppt,.pptx">
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">支持 txt, pdf, doc, docx, md, csv, json, xlsx 等格式</p>
          </Dragger>
          {loading && <div style={{textAlign: 'center', padding: 20}}><Spin tip="上传中..." /></div>}
        </Card>
      )}

      {active === 1 && (
        <Card style={{borderRadius: 8}}>
          <Alert type="success" showIcon icon={<CheckCircleOutlined />}
            message="上传完成" description={`成功上传 ${uploadedFiles.length} 个文件`}
            style={{marginBottom: 16}} />
          <Button type="primary" onClick={() => router.push('/knowledge')}>返回知识库</Button>
          <Button onClick={() => { setActive(0); setUploadedFiles([]) }} style={{marginLeft: 8}}>继续上传</Button>
        </Card>
      )}
    </div>
  )
}
