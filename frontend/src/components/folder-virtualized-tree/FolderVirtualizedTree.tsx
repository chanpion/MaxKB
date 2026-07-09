'use client'
import React, {useEffect, useState} from 'react'
import {Tree, Spin} from 'antd'
import folderApi from '@/lib/api/workspace/folder'
import {useFolderStore, useUserStore} from '@/store'
import AppIcon from '@/components/AppIcon'
import type {SourceTypeEnum} from '@/enums/common'

export default function FolderVirtualizedTree({
  source,
  onSelect,
}: {
  source: string | SourceTypeEnum
  onSelect?: (node: any) => void
}) {
  const [treeData, setTreeData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedKeys, setSelectedKeys] = useState<string[]>(['all'])
  const folderStore = useFolderStore()
  const userStore = useUserStore()

  const load = () => {
    setLoading(true)
    folderApi
      .getFolder(source as string, {})
      .then((ok: any) => {
        const folders = (ok.data || []).map((f: any) => ({key: f.id, title: f.name, ...f}))
        setTreeData([
          {key: 'all', title: '全部', icon: <AppIcon iconName="app-all-menu-active" />, isRoot: true},
          {key: 'share', title: '共享', icon: <AppIcon iconName="app-shared-active" />, isRoot: true},
          ...folders,
        ])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source])

  useEffect(() => {
    const id = folderStore.currentFolder?.id
    if (id === 'share') setSelectedKeys(['share'])
    else if (id) setSelectedKeys([id])
    else setSelectedKeys(['all'])
  }, [folderStore.currentFolder])

  const handleSelect = (keys: any[]) => {
    const key = keys[0]
    if (!key) return
    setSelectedKeys([key])
    const nodeId = key === 'all' ? userStore.getWorkspaceId() : key
    folderStore.setCurrentFolder({id: nodeId, name: key === 'all' ? '全部' : key === 'share' ? '共享' : key})
    onSelect?.(key === 'all' ? {id: nodeId} : {id: key})
  }

  if (loading) return <Spin />

  return (
    <Tree
      treeData={treeData}
      selectedKeys={selectedKeys}
      onSelect={handleSelect}
      blockNode
      defaultExpandAll
      style={{maxHeight: 'calc(100vh - 200px)', overflow: 'auto'}}
    />
  )
}
