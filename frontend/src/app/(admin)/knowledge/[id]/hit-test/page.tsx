'use client'
import React, {useState} from 'react'
import {Breadcrumb, Card, Input, Button, Typography, List, Tag, Spin, Tabs} from 'antd'
import {HomeOutlined, FileTextOutlined, ExperimentOutlined, SearchOutlined, QuestionCircleOutlined, BookOutlined, SettingOutlined, UserOutlined} from '@ant-design/icons'
import {useParams, useRouter, usePathname} from '@/i18n/navigation'
import {get, post} from '@/lib/request'
import {useUserStore} from '@/store'

function ws() { return useUserStore.getState().getWorkspaceId() }

export default function HitTestPage() {
  const router = useRouter()
  const pathname = usePathname()
  const params = useParams()
  const kid = params.id as string
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const handleSearch = () => {
    if (!query.trim()) return
    setLoading(true); setSearched(true)
    post(`/workspace/${ws()}/knowledge/${kid}/hit_test`, {query}).then((res: any) => {
      setResults(res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  const tabItems = [
    {key: 'document', label: <><FileTextOutlined /> 文档</>},
    {key: 'problem', label: <><QuestionCircleOutlined /> 问题</>},
    {key: 'termbase', label: <><BookOutlined /> 术语库</>},
    {key: 'hit-test', label: <><ExperimentOutlined /> 命中测试</>},
    {key: 'chat-user', label: <><UserOutlined /> 对话用户</>},
    {key: 'setting', label: <><SettingOutlined /> 设置</>},
  ]

  return (
    <div>
      <Breadcrumb style={{marginBottom: 12}} items={[
        {title: <><HomeOutlined /> 首页</>},
        {title: <><FileTextOutlined /> 知识库详情</>},
      ]} />
      <Tabs activeKey="hit-test" items={tabItems}
        onChange={(key) => router.push(`/knowledge/${kid}/${key}`)}
        style={{marginBottom: 8}} />
      <Card style={{borderRadius: 8, marginBottom: 16}}>
        <div style={{display: 'flex', gap: 8}}>
          <Input.Search value={query} onChange={(e) => setQuery(e.target.value)} onSearch={handleSearch}
            placeholder="输入测试查询语句..." enterButton="测试" size="large" style={{flex: 1}} />
        </div>
      </Card>
      {loading ? <div style={{textAlign: 'center', padding: 40}}><Spin size="large" /></div>
      : searched && results.length === 0 ? <Typography.Text type="secondary">未找到相关结果</Typography.Text>
      : <List dataSource={results} renderItem={(item: any) => (
          <List.Item style={{background: '#fff', borderRadius: 8, marginBottom: 8, padding: 16}}>
            <div>
              <Tag color="blue">{item.dataset_name || '知识库'}</Tag>
              <Typography.Text>{item.content}</Typography.Text>
              <div style={{marginTop: 4}}>
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
