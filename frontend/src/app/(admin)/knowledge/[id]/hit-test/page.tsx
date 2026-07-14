'use client'
import React, {useState} from 'react'
import {Breadcrumb, Card, Input, Button, Typography, List, Tag, Spin, InputNumber, Space} from 'antd'
import {HomeOutlined, FileTextOutlined, SearchOutlined} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {post} from '@/lib/request'
import {useUserStore} from '@/store'

function ws() { return useUserStore.getState().getWorkspaceId() }

export default function HitTestPage() {
  const params = useParams()
  const kid = params.id as string
  const [query, setQuery] = useState('')
  const [topNumber, setTopNumber] = useState(10)
  const [similarity, setSimilarity] = useState(0)
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const handleSearch = () => {
    if (!query.trim()) return
    setLoading(true); setSearched(true)
    post(`/workspace/${ws()}/knowledge/${kid}/hit_test`, {
      query_text: query,
      top_number: topNumber,
      similarity: similarity,
      search_mode: 'embedding',
    }).then((res: any) => {
      setResults(res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  return (
    <div>
      <Breadcrumb style={{marginBottom: 12}} items={[
        {title: <><HomeOutlined /> 首页</>},
        {title: <><FileTextOutlined /> 知识库详情</>},
      ]} />
      <Card style={{borderRadius: 8, marginBottom: 16}}>
        <div style={{display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center'}}>
          <Input value={query} onChange={(e) => setQuery(e.target.value)} onPressEnter={handleSearch}
            placeholder="输入测试查询语句..." size="large" style={{flex: 1, minWidth: 240}} />
          <Space size="small" style={{alignItems: 'center'}}>
            <span>相似度阈值:</span>
            <InputNumber min={0} max={1} step={0.01} value={similarity}
              onChange={(v) => setSimilarity(v ?? 0)} style={{width: 90}} />
            <span>命中条数:</span>
            <InputNumber min={1} max={100} value={topNumber}
              onChange={(v) => setTopNumber(v ?? 10)} style={{width: 90}} />
          </Space>
          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} loading={loading}>测试</Button>
        </div>
      </Card>
      {loading ? <div style={{textAlign: 'center', padding: 40}}><Spin size="large" /></div>
      : searched && results.length === 0 ? <Typography.Text type="secondary">未找到相关结果</Typography.Text>
      : <List dataSource={results} renderItem={(item: any) => (
          <List.Item style={{background: '#fff', borderRadius: 8, marginBottom: 8, padding: 16}}>
            <div style={{width: '100%'}}>
              <Space size={4} style={{marginBottom: 6}}>
                <Tag color="blue">{item.knowledge_name || '知识库'}</Tag>
                {item.document_name && <Tag color="cyan">{item.document_name}</Tag>}
              </Space>
              <Typography.Paragraph style={{marginBottom: 4, whiteSpace: 'pre-wrap'}}>{item.content}</Typography.Paragraph>
              <div>
                <Typography.Text type="secondary" style={{fontSize: 12}}>
                  相似度: {((item.similarity || 0) * 100).toFixed(1)}%
                </Typography.Text>
              </div>
            </div>
          </List.Item>
        )} />}
    </div>
  )
}
