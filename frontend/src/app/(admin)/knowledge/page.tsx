'use client'
import React from 'react'
import {Breadcrumb} from 'antd'
import {HomeOutlined, FolderOutlined} from '@ant-design/icons'
import FolderVirtualizedTree from '@/components/folder-virtualized-tree/FolderVirtualizedTree'
import KnowledgeListContainer from './component/KnowledgeListContainer'
import {SourceTypeEnum} from '@/enums/common'
import {useFolderStore} from '@/store'
import {useTranslations} from 'next-intl'

export default function KnowledgePage() {
  const t = useTranslations('menu')
  const folder = useFolderStore()
  const breadcrumbItems = [
    {title: <><HomeOutlined /> {t('home')}</>},
    {title: <><FolderOutlined /> {folder.currentFolder?.name || t('knowledge')}</>},
  ]

  return (
    <div style={{display: 'flex', gap: 16, height: 'calc(100vh - 56px - 48px)'}}>
      <div style={{width: 240, background: '#fff', borderRadius: 8, padding: 8, flexShrink: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        <div style={{padding: '8px 8px 4px', fontWeight: 500, fontSize: 14}}>{t('knowledge')}</div>
        <FolderVirtualizedTree source={SourceTypeEnum.KNOWLEDGE} />
      </div>
      <div
        style={{
          flex: 1, overflow: 'hidden', background: '#fff', borderRadius: 8, padding: 16,
          display: 'flex', flexDirection: 'column',
        }}
      >
        <Breadcrumb items={breadcrumbItems} style={{marginBottom: 8}} />
        <KnowledgeListContainer />
      </div>
    </div>
  )
}
