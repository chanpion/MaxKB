'use client'
import React from 'react'
import FolderVirtualizedTree from '@/components/folder-virtualized-tree/FolderVirtualizedTree'
import KnowledgeListContainer from './component/KnowledgeListContainer'
import {SourceTypeEnum} from '@/enums/common'

export default function KnowledgePage() {
  return (
    <div style={{display: 'flex', gap: 16, height: 'calc(100vh - 200px)'}}>
      <div style={{width: 240, overflow: 'auto', background: '#fff', borderRadius: 8, padding: 8, flexShrink: 0}}>
        <FolderVirtualizedTree source={SourceTypeEnum.KNOWLEDGE} />
      </div>
      <div
        style={{
          flex: 1,
          overflow: 'hidden',
          background: '#fff',
          borderRadius: 8,
          padding: 16,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <KnowledgeListContainer />
      </div>
    </div>
  )
}
