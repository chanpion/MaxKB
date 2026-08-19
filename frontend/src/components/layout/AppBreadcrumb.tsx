'use client'
import React, {useEffect, useState} from 'react'
import {ArrowLeftOutlined, RobotOutlined, BookOutlined} from '@ant-design/icons'
import {useRouter} from '@/i18n/navigation'
import {useThemeStore} from '@/store'
import {applicationApi} from '@/lib/api/application'
import knowledgeApi from '@/lib/api/knowledge/knowledge'

interface AppBreadcrumbProps {
  /** 面包屑类型：application | knowledge */
  type: 'application' | 'knowledge'
  id: string
  /** 返回目标路径，如 /application */
  backTo: string
  /** 是否显示返回按钮 */
  showBack?: boolean
}

export default function AppBreadcrumb({type, id, backTo, showBack = true}: AppBreadcrumbProps) {
  const router = useRouter()
  const isDark = useThemeStore((s) => s.isDark)
  const [name, setName] = useState('')

  useEffect(() => {
    if (type === 'application') {
      applicationApi
        .getDetail(id)
        .then((r: any) => setName(r.data?.name || ''))
        .catch(() => {})
    } else {
      knowledgeApi
        .getKnowledgeDetail(id)
        .then((r: any) => setName(r.data?.name || ''))
        .catch(() => {})
    }
  }, [type, id])

  const textColor = isDark ? 'rgba(255,255,255,0.9)' : '#1f2329'
  const secondaryColor = isDark ? 'rgba(255,255,255,0.65)' : '#646a73'
  const borderColor = isDark ? '#333' : '#dee0e3'

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '0 16px',
        height: 48,
        background: isDark ? '#1f1f1f' : '#ffffff',
        borderBottom: `1px solid ${borderColor}`,
        boxSizing: 'border-box',
      }}
    >
      {showBack && (
        <ArrowLeftOutlined
          onClick={() => router.push(backTo)}
          style={{cursor: 'pointer', color: secondaryColor, fontSize: 15}}
        />
      )}
      <div
        style={{
          width: 26,
          height: 26,
          borderRadius: 6,
          background: 'linear-gradient(135deg, #3370ff, #13c2c2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          flexShrink: 0,
        }}
      >
        {type === 'application' ? (
          <RobotOutlined style={{fontSize: 13}} />
        ) : (
          <BookOutlined style={{fontSize: 13}} />
        )}
      </div>
      <span
        style={{
          fontWeight: 600,
          fontSize: 14,
          color: textColor,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
        title={name}
      >
        {name || (type === 'application' ? '智能体' : '知识库')}
      </span>
    </div>
  )
}
