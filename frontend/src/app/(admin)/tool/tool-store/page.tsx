'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Button, Card, Empty, List, Tag, Typography, message} from 'antd'
import {AppstoreOutlined, ArrowLeftOutlined, ToolOutlined} from '@ant-design/icons'
import {useRouter} from '@/i18n/navigation'
import {useTranslations} from 'next-intl'
import {toolApi} from '@/lib/api/tool/tool'

const TYPE_TAG: Record<string, {color: string; label: string}> = {
  FUNCTION: {color: 'blue', label: '函数'},
  SKILL: {color: 'purple', label: '技能'},
  MCP: {color: 'green', label: 'MCP'},
  DATA_SOURCE: {color: 'orange', label: '数据源'},
}

export default function ToolStorePage() {
  const t = useTranslations('menu')
  const router = useRouter()
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const load = () => {
    setLoading(true)
    toolApi
      .getToolListAll({workspace_id: 'default'})
      .then((res: any) => {
        const data = res?.data ?? res
        setItems(data?.shared_tools || [])
      })
      .catch(() => message.error('加载工具库失败'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div>
      <div style={{display: 'flex', alignItems: 'center', marginBottom: 12, gap: 12}}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.push('/tool')}>返回</Button>
        <Breadcrumb items={[{title: <><AppstoreOutlined /> {t('tool')}</>}, {title: '工具库'}]} />
      </div>

      <Card style={{borderRadius: 8}}>
        {items.length === 0 ? (
          <Empty description={loading ? '加载中…' : '工具库暂无共享工具'} />
        ) : (
          <List
            grid={{gutter: 16, column: 3}}
            dataSource={items}
            loading={loading}
            renderItem={(it) => (
              <List.Item>
                <Card size="small" hoverable>
                  <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                    <ToolOutlined style={{color: '#1677ff', fontSize: 18}} />
                    <Typography.Text strong>{it.name}</Typography.Text>
                    <Tag color={TYPE_TAG[it.tool_type]?.color}>{TYPE_TAG[it.tool_type]?.label}</Tag>
                  </div>
                  <div style={{marginTop: 8, color: '#8c8c8c', fontSize: 13, minHeight: 40}}>
                    {it.desc || '暂无描述'}
                  </div>
                </Card>
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  )
}
