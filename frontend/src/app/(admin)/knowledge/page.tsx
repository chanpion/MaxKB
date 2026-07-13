'use client'
import React from 'react'
import {Breadcrumb} from 'antd'
import {HomeOutlined, FolderOutlined} from '@ant-design/icons'
import FolderVirtualizedTree from '@/components/folder-virtualized-tree/FolderVirtualizedTree'
import KnowledgeListContainer from './component/KnowledgeListContainer'
import {SourceTypeEnum} from '@/enums/common'
import {useFolderStore, useThemeStore} from '@/store'
import {useTranslations} from 'next-intl'

export default function KnowledgePage() {
  const t = useTranslations('menu')
  const folder = useFolderStore()
  const isDark = useThemeStore((s) => s.isDark)
  const breadcrumbItems = [
    {title: <><HomeOutlined /> {t('home')}</>},
    {title: <><FolderOutlined /> {folder.currentFolder?.name || t('knowledge')}</>},
  ]

  const panelBorder = isDark ? '#303030' : '#eef0f2'
  const panelBg = isDark ? '#1f1f1f' : '#ffffff'

  return (
    <div style={{display: 'flex', gap: 16, height: 'calc(100vh - 56px - 48px)'}}>
      <div
        style={{
          width: 280,
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
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
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
            <FolderOutlined style={{fontSize: 15}} />
          </div>
          <span style={{fontWeight: 600, fontSize: 15, color: isDark ? 'rgba(255,255,255,0.92)' : '#1f1f1f'}}>
            {t('knowledge')}
          </span>
        </div>
        <FolderVirtualizedTree source={SourceTypeEnum.KNOWLEDGE} />
      </div>
      <div
        style={{
          flex: 1, overflow: 'hidden', background: panelBg, borderRadius: 12, padding: 16,
          border: `1px solid ${panelBorder}`,
          display: 'flex', flexDirection: 'column',
        }}
      >
        <Breadcrumb items={breadcrumbItems} style={{marginBottom: 8}} />
        <KnowledgeListContainer />
      </div>
    </div>
  )
}
