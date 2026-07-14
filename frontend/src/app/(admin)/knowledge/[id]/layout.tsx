'use client'
import React, {useEffect, useState} from 'react'
import {Menu} from 'antd'
import {
  FileTextOutlined,
  NodeIndexOutlined,
  QuestionCircleOutlined,
  BookOutlined,
  ExperimentOutlined,
  UserOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import {useParams} from 'next/navigation'
import {useRouter, usePathname} from '@/i18n/navigation'
import knowledgeApi from '@/lib/api/knowledge/knowledge'
import {useThemeStore} from '@/store'

const MENU = [
  {key: 'document', icon: <FileTextOutlined />, label: '文档'},
  {key: 'workflow', icon: <NodeIndexOutlined />, label: '工作流'},
  {key: 'problem', icon: <QuestionCircleOutlined />, label: '问题'},
  {key: 'termbase', icon: <BookOutlined />, label: '术语库'},
  {key: 'hit-test', icon: <ExperimentOutlined />, label: '命中测试'},
  {key: 'chat-user', icon: <UserOutlined />, label: '对话用户'},
  {key: 'setting', icon: <SettingOutlined />, label: '设置'},
]

export default function KnowledgeDetailLayout({children}: {children: React.ReactNode}) {
  const {id} = useParams()
  const router = useRouter()
  const pathname = usePathname()
  const isDark = useThemeStore((s) => s.isDark)
  const [name, setName] = useState('')

  // 路由第 4 段即当前 section；进入段落页（document/[docId]）时高亮"文档"
  const activeKey = pathname.split('/')[3] || 'document'

  useEffect(() => {
    knowledgeApi.getKnowledgeDetail(id as string)
      .then((r: any) => setName(r.data?.name || ''))
      .catch(() => {})
  }, [id])

  const panelBorder = isDark ? '#303030' : '#eef0f2'
  const panelBg = isDark ? '#1f1f1f' : '#ffffff'

  return (
    <div style={{display: 'flex', gap: 16, height: 'calc(100vh - 56px - 48px)'}}>
      {/* 左侧竖向菜单 */}
      <div
        style={{
          width: 220,
          background: panelBg,
          borderRadius: 12,
          border: `1px solid ${panelBorder}`,
          flexShrink: 0,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '16px 16px 14px',
            background: 'linear-gradient(135deg, rgba(22,119,255,0.10), rgba(19,194,194,0.06))',
            borderBottom: `1px solid ${panelBorder}`,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: 8,
                background: 'linear-gradient(135deg, #1677ff, #13c2c2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
              }}
            >
              <FileTextOutlined style={{fontSize: 15}} />
            </div>
            <span
              style={{
                fontWeight: 600,
                fontSize: 15,
                color: isDark ? 'rgba(255,255,255,0.92)' : '#1f1f1f',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
              title={name}
            >
              {name || '知识库'}
            </span>
          </div>
        </div>
        <div style={{flex: 1, overflow: 'auto', padding: '8px 0'}}>
          <Menu
            mode="inline"
            selectedKeys={[activeKey]}
            items={MENU}
            onClick={({key}) => router.push(`/knowledge/${id}/${key}`)}
            style={{border: 'none', background: 'transparent'}}
          />
        </div>
      </div>

      {/* 右侧内容区 */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          background: panelBg,
          borderRadius: 12,
          padding: 20,
          border: `1px solid ${panelBorder}`,
        }}
      >
        {children}
      </div>
    </div>
  )
}
