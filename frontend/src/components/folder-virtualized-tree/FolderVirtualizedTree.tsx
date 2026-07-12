'use client'
import React, {useEffect, useState} from 'react'
import {Tree, Spin} from 'antd'
import type {TreeProps} from 'antd'
import {FolderOutlined, FolderOpenOutlined} from '@ant-design/icons'
import folderApi from '@/lib/api/workspace/folder'
import {useFolderStore, useUserStore} from '@/store'
import AppIcon from '@/components/AppIcon'
import type {SourceTypeEnum} from '@/enums/common'

const iconMap: Record<string, React.ReactNode> = {
  all: <AppIcon iconName="app-all-menu-active" />,
  share: <AppIcon iconName="app-shared-active" />,
}

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
        const raw = Array.isArray(ok.data) ? ok.data : (ok.data?.records || ok.data?.children || [])
        const folders = raw
          .filter((f: any) => f.id)
          .map((f: any) => {
            const children = f.children
              ? f.children.filter((c: any) => c.id).map((c: any) => ({key: c.id, title: c.name, isLeaf: true, ...c}))
              : undefined
            return {key: f.id, title: f.name, children, icon: <FolderOutlined />, ...f}
          })
        setTreeData([
          {key: 'all', title: '全部', icon: iconMap.all, isRoot: true},
          {key: 'share', title: '共享', icon: iconMap.share, isRoot: true},
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

  const handleSelect: TreeProps['onSelect'] = (keys: any[]) => {
    const key = keys[0]
    if (!key) return
    setSelectedKeys([key])
    const nodeId = key === 'all' ? userStore.getWorkspaceId() : key
    folderStore.setCurrentFolder({id: nodeId, name: key === 'all' ? '全部' : key === 'share' ? '共享' : key})
    onSelect?.(key === 'all' ? {id: nodeId} : {id: key})
  }

  if (loading) return <div style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center'}}><Spin /></div>

  return (
    <div style={{flex: 1, minHeight: 0, overflow: 'auto'}}>
      <Tree
        treeData={treeData}
        selectedKeys={selectedKeys}
        onSelect={handleSelect}
        blockNode
        defaultExpandAll
        showIcon
        style={{padding: '4px 0'}}
        titleRender={(node: any) => (
          <span style={{fontSize: 13, fontWeight: node.isRoot ? 500 : 400, color: node.isRoot ? '#1a1a1a' : '#333'}}>
            {node.title}
          </span>
        )}
      />
    </div>
  )
}
