'use client'
import React, {useEffect, useMemo, useRef, useState, useCallback} from 'react'
import {Tree, Spin, Input, Dropdown, Button} from 'antd'
import {SearchOutlined, CheckOutlined} from '@ant-design/icons'
import type {TreeProps} from 'antd'
import {FolderOutlined} from '@ant-design/icons'
import folderApi from '@/lib/api/workspace/folder'
import {useFolderStore, useUserStore, useThemeStore} from '@/store'
import AppIcon from '@/components/AppIcon'
import type {SourceTypeEnum} from '@/enums/common'
import {SORT_MENU_CONFIG, SORT_TYPES, type SortType} from './constants'
import CreateFolderDialog from './CreateFolderDialog'
import MoveToDialog from './MoveToDialog'
import ResourceAuthorizationDrawer from '@/components/resource-authorization-drawer'
import permissionMap from '@/permission'
import {MsgConfirm} from '@/utils/message'
import {useTranslations} from 'next-intl'

const iconMap: Record<string, React.ReactNode> = {
  share: <AppIcon iconName="app-shared-active" />,
}

const SORT_COMPARATORS: Record<string, (a: any, b: any) => number> = {
  [SORT_TYPES.CREATE_TIME_ASC]: (a, b) => new Date(a.create_time).getTime() - new Date(b.create_time).getTime(),
  [SORT_TYPES.CREATE_TIME_DESC]: (a, b) => new Date(b.create_time).getTime() - new Date(a.create_time).getTime(),
  [SORT_TYPES.NAME_ASC]: (a, b) => (a.title || '').localeCompare(b.title || ''),
  [SORT_TYPES.NAME_DESC]: (a, b) => (b.title || '').localeCompare(a.title || ''),
  [SORT_TYPES.CUSTOM]: (a, b) => (a.order || 0) - (b.order || 0),
}

// 后端 getFolder 返回树结构 [workspace根节点]，真实文件夹在 rootNode.children 中。
// 剥离 workspace 根节点，只保留真实文件夹组成的树。
const buildFolderTree = (list: any[]): any[] =>
  (list || [])
    .filter((f: any) => f.id)
    .map((f: any) => {
      const hasChildren = Array.isArray(f.children) && f.children.length > 0
      return {
        ...f,
        key: f.id,
        title: f.name,
        icon: <FolderOutlined />,
        children: hasChildren ? buildFolderTree(f.children) : undefined,
        isLeaf: !hasChildren,
      }
    })

export default function FolderVirtualizedTree({
  source,
  onSelect,
  canOperation = true,
  showShared = false,
  onRefresh,
}: {
  source: string | SourceTypeEnum
  onSelect?: (node: any) => void
  canOperation?: boolean
  showShared?: boolean
  onRefresh?: () => void
}) {
  const [treeData, setTreeData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedKeys, setSelectedKeys] = useState<string[]>([])
  const [filterText, setFilterText] = useState('')
  const [currentSort, setCurrentSort] = useState<SortType>(SORT_TYPES.CREATE_TIME_DESC)
  const [hoverNodeId, setHoverNodeId] = useState<string | undefined>(undefined)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const folderStore = useFolderStore()
  const userStore = useUserStore()
  const isDark = useThemeStore((s) => s.isDark)
  const t = useTranslations()
  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const createFolderRef = useRef<any>(null)
  const moveToRef = useRef<any>(null)
  const authRef = useRef<any>(null)

  const sourceKey = source === 'KNOWLEDGE' ? 'knowledge' : 'model'
  const perm = permissionMap[sourceKey]?.workspace || {}

  const workspaceId = userStore.workspace_id || userStore.getWorkspaceId()
  const FOLDER_SORT_KEY = `${userStore.userInfo?.id || ''}-${workspaceId}-${source}-folder-sort-type`

  const load = () => {
    setLoading(true)
    folderApi
      .getFolder(source as string, {})
      .then((ok: any) => {
        const arr = Array.isArray(ok.data) ? ok.data : (ok.data?.records || ok.data?.children || [])
        // 后端返回 [workspace根节点]，真实文件夹在其 children 中；非数组兜底则直接使用列表本身。
        const rootList = Array.isArray(ok.data) && arr.length ? (arr[0]?.children || []) : arr
        const folders = buildFolderTree(rootList)
        setTreeData(folders)
        // 默认选中第一个真实文件夹
        const root = folders[0]
        const curId = folderStore.currentFolder?.id
        const valid = curId && curId !== 'all' && curId !== workspaceId
        if (root && !valid) {
          setSelectedKeys([root.key])
          folderStore.setCurrentFolder({id: root.id, name: root.title})
        }
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source])

  useEffect(() => {
    const saved = localStorage.getItem(FOLDER_SORT_KEY)
    if (saved) setCurrentSort(saved as SortType)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const id = folderStore.currentFolder?.id
    if (id === 'share') setSelectedKeys(['share'])
    else if (id && id !== 'all' && id !== workspaceId) setSelectedKeys([id])
    else {
      const root = treeData[0]
      setSelectedKeys(root ? [root.key] : [])
    }
  }, [folderStore.currentFolder, workspaceId, treeData])

  const handleSelect: TreeProps['onSelect'] = (keys: any[], info: any) => {
    const key = keys[0]
    if (!key) return
    setSelectedKeys([key])
    const isShare = key === 'share'
    const title = info?.node?.title ?? (isShare ? '共享' : key)
    folderStore.setCurrentFolder({id: key, name: title})
    onSelect?.({id: key})
  }

  const handleRefresh = useCallback(() => {
    load()
    folderStore.incrementRefresh()
    onRefresh?.()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source, onRefresh])

  const filteredTreeData = useMemo(() => {
    if (!filterText.trim()) return treeData
    const kw = filterText.trim().toLowerCase()
    const filterNodes = (nodes: any[]): any[] =>
      nodes
        .map((n) => ({
          ...n,
          children: n.children ? filterNodes(n.children) : undefined,
        }))
        .filter((n) => (n.title || '').toLowerCase().includes(kw) || (n.children && n.children.length > 0))
    return filterNodes(treeData)
  }, [treeData, filterText])

  const sortedFilteredTreeData = useMemo(() => {
    const sortTree = (nodes: any[]): any[] => {
      if (!nodes || nodes.length === 0) return nodes
      const compareFn = SORT_COMPARATORS[currentSort]
      if (!compareFn) return nodes
      const sorted = [...nodes].sort(compareFn)
      return sorted.map((n) => ({...n, children: n.children ? sortTree(n.children) : undefined}))
    }
    return sortTree(filteredTreeData)
  }, [filteredTreeData, currentSort])

  const displayTreeData = useMemo(() => {
    const items: any[] = []
    if (showShared && userStore.isEE()) {
      items.push({key: 'share', title: '共享', icon: iconMap.share, isRoot: true})
    }
    items.push(...sortedFilteredTreeData)
    return items
  }, [sortedFilteredTreeData, showShared, userStore])

  const switchSortMethod = (method: SortType) => {
    setCurrentSort(method)
    localStorage.setItem(FOLDER_SORT_KEY, method)
  }

  const sortIconName = useMemo(() => {
    if (currentSort.endsWith('asc')) return 'app-folder-asc'
    if (currentSort.endsWith('desc')) return 'app-folder-desc'
    return 'app-folder-custom'
  }, [currentSort])

  const handleMouseEnter = useCallback((nodeId: string) => {
    clearTimeout(hoverTimeoutRef.current)
    setHoverNodeId(nodeId)
  }, [])

  const handleMouseLeave = useCallback(() => {
    if (dropdownOpen) return
    clearTimeout(hoverTimeoutRef.current)
    hoverTimeoutRef.current = setTimeout(() => {
      setHoverNodeId(undefined)
    }, 300)
  }, [dropdownOpen])

  const onDropdownVisibleChange = (visible: boolean) => {
    setDropdownOpen(visible)
    if (!visible) setHoverNodeId(undefined)
  }

  const hasAnyFolderPermission = (node: any) => {
    return perm.create?.(node.id) || perm.edit?.(node.id) || perm.delete?.(node.id) || perm.auth?.(node.id)
  }

  const handleContextMenuClick = (node: any, key: string) => {
    switch (key) {
      case 'create':
        createFolderRef.current?.open(source, node.id)
        break
      case 'edit':
        createFolderRef.current?.open(source, node.parent_id, node)
        break
      case 'move':
        moveToRef.current?.open({id: node.id, folder_type: source}, true)
        break
      case 'auth':
        authRef.current?.open(node.id)
        break
      case 'delete':
        confirmDeleteFolder(node)
        break
    }
  }

  const confirmDeleteFolder = (node: any) => {
    MsgConfirm(
      `${t('common.deleteConfirm')}：${node.title}`,
      t('components.folder.deleteConfirmMessage'),
      {confirmButtonText: t('common.delete'), confirmButtonClass: 'danger'},
    )
      .then(() => {
        folderApi.delFolder(node.id, source).then(() => {
          if (selectedKeys[0] === node.id || selectedKeys[0] === node.key) {
            const parentId = node.parent_id || treeData[0]?.id || workspaceId
            folderStore.setCurrentFolder({id: parentId})
          }
          handleRefresh()
        })
      })
      .catch(() => {})
  }

  const buildContextMenuItems = (node: any) => {
    const items: any[] = []
    if (perm.create?.(node.id)) {
      items.push({key: 'create', icon: <AppIcon iconName="app-add-folder" />, label: t('components.folder.addChildFolder')})
    }
    if (perm.edit?.(node.id)) {
      items.push({key: 'edit', icon: <AppIcon iconName="app-edit" />, label: t('common.edit')})
    }
    if (node.parent_id && perm.edit?.(node.id)) {
      items.push({key: 'move', icon: <AppIcon iconName="app-migrate" />, label: t('common.moveTo')})
    }
    if (perm.auth?.(node.id)) {
      items.push({key: 'auth', icon: <AppIcon iconName="app-resource-authorization" />, label: t('views.system.resourceAuthorization.title')})
    }
    if (perm.delete?.(node.id)) {
      items.push(
        {type: 'divider'},
        {key: 'delete', icon: <AppIcon iconName="app-delete" />, label: t('common.delete'), disabled: !node.parent_id, danger: true},
      )
    }
    return items
  }

  const sortMenuItems = useMemo(() => {
    return SORT_MENU_CONFIG.flatMap((group, gi) => [
      ...(gi > 0 ? [{type: 'divider' as const}] : []),
      ...group.items.map((item) => ({
        key: item.value,
        label: (
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: 180}}>
            <span>{t(item.labelKey)}</span>
            {currentSort === item.value && <CheckOutlined style={{color: 'var(--ant-color-primary)'}} />}
          </div>
        ),
      })),
    ])
  }, [currentSort, t])

  if (loading) return <div style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center'}}><Spin /></div>

  return (
    <div style={{flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column'}}>
      <div
        style={{
          display: 'flex',
          gap: 8,
          padding: '12px 12px 8px',
        }}
      >
        <Input
          value={filterText}
          onChange={e => setFilterText(e.target.value)}
          placeholder={t('common.search')}
          allowClear
          prefix={<SearchOutlined style={{color: isDark ? 'rgba(255,255,255,0.45)' : 'rgba(0,0,0,0.4)'}} />}
          style={{flex: 1}}
          size="small"
        />
        <Dropdown menu={{items: sortMenuItems, onClick: ({key}) => switchSortMethod(key as SortType)}} trigger={['click']}>
          <Button size="small" style={{width: 32, padding: 0}} icon={<AppIcon iconName={sortIconName} />} />
        </Dropdown>
      </div>
      <div style={{flex: 1, minHeight: 0, overflow: 'auto', padding: '0 8px 8px'}}>
        <Tree
          className="kb-folder-tree"
          treeData={displayTreeData}
          selectedKeys={selectedKeys}
          onSelect={handleSelect}
          blockNode
          defaultExpandAll
          showIcon
          style={{padding: '4px 0', background: 'transparent'}}
          titleRender={(node: any) => {
            const showContext = canOperation && !node.isRoot && hasAnyFolderPermission(node)
            const isSelected = selectedKeys[0] === node.key
            const isHover = hoverNodeId === node.key
            const bg = isSelected
              ? 'rgba(22,119,255,0.12)'
              : isHover
                ? isDark
                  ? 'rgba(255,255,255,0.06)'
                  : 'rgba(0,0,0,0.04)'
                : 'transparent'
            const color = isSelected
              ? '#1677ff'
              : isDark
                ? 'rgba(255,255,255,0.85)'
                : 'rgba(0,0,0,0.65)'
            return (
              <div
                onMouseEnter={() => handleMouseEnter(node.key)}
                onMouseLeave={handleMouseLeave}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '7px 10px',
                  borderRadius: 8,
                  background: bg,
                  color,
                  transition: 'background 0.15s ease',
                  cursor: 'pointer',
                }}
              >
                <span
                  style={{
                    fontSize: 13,
                    fontWeight: node.isRoot || isSelected ? 600 : 400,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  {node.icon && <span style={{display: 'inline-flex', color: node.isRoot ? '#1677ff' : 'inherit'}}>{node.icon}</span>}
                  {node.title}
                </span>
                {showContext && isHover && (
                  <Dropdown
                    menu={{items: buildContextMenuItems(node), onClick: ({key}) => handleContextMenuClick(node, key)}}
                    trigger={['click']}
                    onOpenChange={onDropdownVisibleChange}
                  >
                    <Button type="text" size="small" icon={<AppIcon iconName="app-more" />} onClick={e => e.stopPropagation()} />
                  </Dropdown>
                )}
              </div>
            )
          }}
        />
      </div>
      <CreateFolderDialog ref={createFolderRef} onRefresh={handleRefresh} />
      <MoveToDialog ref={moveToRef} source={source as any} onRefresh={handleRefresh} />
      <ResourceAuthorizationDrawer ref={authRef} type={`${source}_FOLDER`} />
    </div>
  )
}

