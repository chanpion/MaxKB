'use client'
import React, {useEffect, useRef, useState} from 'react'
import {Row, Col, Input, Select, Dropdown, Button, Empty, Checkbox, Tag, Upload, message} from 'antd'
import {MoreOutlined} from '@ant-design/icons'
import {useRouter} from '@/i18n/navigation'
import CardBox from '@/components/CardBox'
import KnowledgeIcon from '@/components/KnowledgeIcon'
import InfiniteScroll from '@/components/InfiniteScroll'
import AppIcon from '@/components/AppIcon'
import permissionMap from '@/permission'
import {useFolderStore, useUserStore, useKnowledgeStore} from '@/store'
import {loadSharedApi} from '@/lib/api/shared-api'
import knowledgeApi from '@/lib/api/knowledge/knowledge'
import {loginApi} from '@/lib/api/login'
import {SourceTypeEnum} from '@/enums/common'
import {useTranslations} from 'next-intl'
import {MsgConfirm, MsgSuccess} from '@/utils/message'
import {i18n_name} from '@/utils/common'
import {dateFormat} from '@/utils/time'
import {numberFormat} from '@/utils/common'
import CreateKnowledgeDialog from '../create-component/CreateKnowledgeDialog'
import CreateWebKnowledgeDialog from '../create-component/CreateWebKnowledgeDialog'
import CreateLarkKnowledgeDialog from '../create-component/CreateLarkKnowledgeDialog'
import CreateWorkflowKnowledgeDialog from '../create-component/CreateWorkflowKnowledgeDialog'
import CreateFolderDialog from '@/components/folder-virtualized-tree/CreateFolderDialog'
import MoveToDialog from '@/components/folder-virtualized-tree/MoveToDialog'
import GenerateRelatedDialog from '@/components/generate-related-dialog'
import ResourceAuthorizationDrawer from '@/components/resource-authorization-drawer'
import ResourceMappingDrawer from '@/components/resource_mapping'
import ExportKnowledgeDialog from './ExportKnowledgeDialog'
import SyncWebDialog from './SyncWebDialog'

export default function KnowledgeListContainer() {
  const t = useTranslations()
  const router = useRouter()
  const folder = useFolderStore()
  const user = useUserStore()
  const knowledge = useKnowledgeStore()
  const perm = permissionMap['knowledge']['workspace']
  // 后端 apps/knowledge 未提供 lark 路由（POST /knowledge/lark/save），飞书知识库能力暂不可用，降级隐藏入口。
  const ENABLE_LARK = false

  const [loading, setLoading] = useState(false)
  const loadingRef = useRef(false)
  const [searchForm, setSearchForm] = useState<{name: string; create_user?: string}>({name: ''})
  const [pagination, setPagination] = useState({current_page: 1, page_size: 30, total: 0})
  const [isBatch, setIsBatch] = useState(false)
  const [multipleSelection, setMultipleSelection] = useState<any[]>([])
  const [sortField, setSortField] = useState<string>('create_time')
  const [userOptions, setUserOptions] = useState<any[]>([])

  const [currentCreateDialog, setCurrentCreateDialog] = useState<React.ReactElement | null>(null)
  const [currentFolder, setCurrentFolder] = useState<any>(null)

  const createRef = useRef<any>(null)
  const webRef = useRef<any>(null)
  const larkRef = useRef<any>(null)
  const workflowRef = useRef<any>(null)
  const createFolderRef = useRef<any>(null)
  const moveRef = useRef<any>(null)
  const genRef = useRef<any>(null)
  const authRef = useRef<any>(null)
  const mapRef = useRef<any>(null)
  const exportRef = useRef<any>(null)
  const syncRef = useRef<any>(null)

  const fetchPage = (page: number, append: boolean) => {
    if (loadingRef.current) return
    loadingRef.current = true
    setLoading(true)
    const params: any = {
      folder_id: folder.currentFolder?.id || user.getWorkspaceId(),
      scope: 'WORKSPACE',
    }
    if (searchForm.name) params.name = searchForm.name
    if (searchForm.create_user) params.create_user = searchForm.create_user
    if (sortField) params.order = sortField
    knowledgeApi
      .getKnowledgeList(params)
      .then((ok: any) => {
        const records = ok.data || []
        const total = records.length
        if (append) knowledge.setKnowledgeList([...knowledge.knowledgeList, ...records])
        else knowledge.setKnowledgeList(records)
        setPagination((p) => ({...p, current_page: page, total}))
      })
      .catch(() => {})
      .finally(() => {
        loadingRef.current = false
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchPage(1, false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [folder.currentFolder?.id, folder.refreshCounter, sortField, searchForm.create_user])

  const onSearch = () => {
    setPagination((p) => ({...p, current_page: 1}))
    fetchPage(1, false)
  }

  const openCreateDialog = (type: string) => {
    const f = folder.currentFolder
    if (type === 'general') createRef.current?.open(f)
    else if (type === 'web') webRef.current?.open(f)
    else if (type === 'lark') larkRef.current?.open(f)
    else if (type === 'workflow') workflowRef.current?.open(f)
  }

  const refresh = () => fetchPage(1, false)

  const batchSelectedHandle = (bool: boolean) => {
    setIsBatch(bool)
    setMultipleSelection([])
  }

  const reEmbeddingKnowledge = (row: any) => {
    knowledgeApi.putReEmbeddingKnowledge(row.id).then(() => MsgSuccess(t('common.submitSuccess')))
  }

  const syncKnowledge = (row: any) => syncRef.current?.open(row.id)

  const openGenerateDialog = (row: any) => genRef.current?.open([], 'knowledge', row)

  const openMoveToDialog = (data?: any) => {
    const obj = data ? {id: data.id, folder_id: data.folder} : {id_list: multipleSelection}
    moveRef.current?.open(obj)
  }

  const openAuthorization = (row: any) => authRef.current?.open(row.id)
  const openResourceMapping = (row: any) => mapRef.current?.open('KNOWLEDGE', row)

  const exportKnowledge = (row: any) => {
    knowledgeApi.exportKnowledge(row.name, row.id).then(() => MsgSuccess(t('common.exportSuccess')))
  }
  const exportZipKnowledge = (row: any) => {
    knowledgeApi.exportZipKnowledge(row.name, row.id).then(() => MsgSuccess(t('common.exportSuccess')))
  }
  const exportKnowledgeBundle = (row: any) => {
    exportRef.current?.open((withSource: boolean) => {
      knowledgeApi
        .exportKnowledgeBundle(row.name, row.id, withSource)
        .then(() => MsgSuccess(t('common.exportSuccess')))
    })
  }

  const deleteKnowledge = (row: any) => {
    MsgConfirm(
      `${t('views.knowledge.delete.confirmTitle')}${row.name} ?`,
      row.resource_count > 0 ? t('views.knowledge.delete.resourceCountMessage', {count: row.resource_count}) : '',
      {confirmButtonText: t('common.confirm'), confirmButtonClass: 'danger'},
    )
      .then(() => {
        knowledgeApi.delKnowledge(row.id).then(() => {
          knowledge.setKnowledgeList(knowledge.knowledgeList.filter((v: any) => v.id !== row.id))
          MsgSuccess(t('common.deleteSuccess'))
        })
      })
      .catch(() => {})
  }

  const deleteMulKnowledge = () => {
    MsgConfirm(
      t('views.knowledge.delete.confirmBatch', {count: multipleSelection.length}),
      t('views.paragraph.delete.confirmMessage'),
      {confirmButtonText: t('common.confirm'), confirmButtonClass: 'danger'},
    )
      .then(() => {
        knowledgeApi.delMulKnowledge(multipleSelection).then(() => {
          batchSelectedHandle(false)
          refresh()
          MsgSuccess(t('views.document.delete.successMessage'))
        })
      })
      .catch(() => {})
  }

  const handleImport = (file: any) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('folder_id', folder.currentFolder?.id || user.getWorkspaceId())
    knowledgeApi
      .importKnowledgeBundle(formData)
      .then(async () => {
        await user.profile()
        MsgSuccess(t('common.importSuccess'))
        refresh()
      })
      .catch(() => {})
    return false
  }

  const menuItems = (row: any) => {
    const items: any[] = []
    if (row.type === 1 && perm.sync(row.id)) items.push({key: 'sync', label: t('views.knowledge.setting.sync')})
    if (perm.vector(row.id)) items.push({key: 'vector', label: t('views.knowledge.setting.vectorization')})
    if (perm.generate(row.id)) items.push({key: 'generate', label: t('views.document.generateQuestion.title')})
    if (perm.auth(row.id)) items.push({key: 'auth', label: t('views.system.resourceAuthorization.title')})
    if (perm.relate_map(row.id)) items.push({key: 'map', label: t('views.system.resourceMapping.title')})
    if (perm.edit(row.id)) items.push({key: 'move', label: t('common.moveTo')})
    items.push({type: 'divider'})
    items.push({key: 'exportExcel', label: `${t('views.document.setting.exportDocument')} Excel`})
    items.push({key: 'exportZip', label: `${t('views.document.setting.exportDocument')} ZIP`})
    items.push({key: 'exportBundle', label: t('views.document.setting.exportKnowledge')})
    items.push({type: 'divider'})
    if (perm.delete(row.id)) items.push({key: 'delete', label: t('common.delete'), danger: true})
    return items
  }

  const onMenuClick = (row: any, key: string) => {
    switch (key) {
      case 'sync': syncKnowledge(row); break
      case 'vector': reEmbeddingKnowledge(row); break
      case 'generate': openGenerateDialog(row); break
      case 'auth': openAuthorization(row); break
      case 'map': openResourceMapping(row); break
      case 'move': openMoveToDialog(row); break
      case 'exportExcel': exportKnowledge(row); break
      case 'exportZip': exportZipKnowledge(row); break
      case 'exportBundle': exportKnowledgeBundle(row); break
      case 'delete': deleteKnowledge(row); break
    }
  }

  const KB_ACCENT: Record<number, string> = {
    0: '#1677ff',
    1: '#722ed1',
    2: '#13c2c2',
    3: '#13c2c2',
  }

  const createDropdownItems = [
    {key: 'general', label: t('views.knowledge.knowledgeType.generalKnowledge')},
    {key: 'web', label: t('views.knowledge.knowledgeType.webKnowledge')},
    ENABLE_LARK && {key: 'lark', label: t('views.knowledge.knowledgeType.larkKnowledge')},
    {key: 'workflow', label: t('views.knowledge.knowledgeType.workflowKnowledge')},
    {key: 'folder', label: t('components.folder.addFolder')},
  ].filter(Boolean) as any[]

  return (
    <div style={{display: 'flex', flexDirection: 'column', height: '100%'}}>
      <div style={{display: 'flex', alignItems: 'center', marginBottom: 16, gap: 8, flexWrap: 'wrap'}}>
        <Select
          value={sortField}
          onChange={setSortField}
          style={{width: 120}}
          options={[
            {label: '创建时间', value: 'create_time'},
            {label: '名称 A-Z', value: 'name_asc'},
            {label: '名称 Z-A', value: 'name_desc'},
          ]}
        />
        <Input
          value={searchForm.name}
          allowClear
          onChange={(e) => setSearchForm((s) => ({...s, name: e.target.value}))}
          onPressEnter={onSearch}
          placeholder={t('common.searchBar.placeholder')}
          style={{width: 200}}
        />
        <Select
          showSearch
          allowClear
          value={searchForm.create_user}
          onChange={(v) => setSearchForm((s) => ({...s, create_user: v}))}
          placeholder="创建人"
          style={{width: 130}}
          filterOption={false}
          onSearch={(val) => {
            if (val) loginApi.getUserList({name: val}).then((res: any) => setUserOptions(res.data || []))
          }}
          options={userOptions.map((u: any) => ({label: u.nick_name || u.username, value: u.id}))}
        />
        {!isBatch ? (
          <>
            <Dropdown
              menu={{
                items: createDropdownItems,
                onClick: ({key}) => {
                  if (key === 'folder') createFolderRef.current?.open(SourceTypeEnum.KNOWLEDGE, folder.currentFolder?.id)
                  else openCreateDialog(key)
                },
              }}
            >
              <Button type="primary">{t('common.create')}</Button>
            </Dropdown>
            <Upload beforeUpload={handleImport} showUploadList={false} accept=".zip">
              <Button>{t('common.importCreate')}</Button>
            </Upload>
          </>
        ) : (
          <Button onClick={() => batchSelectedHandle(false)}>{t('views.paragraph.setting.cancelSelected')}</Button>
        )}
        {isBatch && (
          <Button disabled={multipleSelection.length === 0} onClick={() => openMoveToDialog()}>
            {t('common.moveTo')}
          </Button>
        )}
        {isBatch && (
          <Button danger disabled={multipleSelection.length === 0} onClick={deleteMulKnowledge}>
            {t('common.delete')}
          </Button>
        )}
        <span style={{color: 'rgba(0,0,0,0.45)', marginLeft: 'auto'}}>
          {t('common.selected')} {multipleSelection.length}/{pagination.total}
        </span>
        <Button onClick={() => batchSelectedHandle(!isBatch)} style={{marginLeft: 8}}>
          {isBatch ? t('views.paragraph.setting.cancelSelected') : t('views.paragraph.setting.batchSelected')}
        </Button>
      </div>

      <InfiniteScroll
        size={knowledge.knowledgeList.length}
        total={pagination.total}
        page_size={pagination.page_size}
        current_page={pagination.current_page}
        loading={loading}
        onLoad={() => fetchPage(pagination.current_page + 1, true)}
      >
        {knowledge.knowledgeList.length === 0 && !loading ? (
          <Empty description={t('common.noData')} />
        ) : (
          <Checkbox.Group value={multipleSelection} onChange={setMultipleSelection}>
            <Row gutter={[16, 16]}>
              {knowledge.knowledgeList.map((item: any) => (
                <Col key={item.id} xs={24} sm={12} md={12} lg={8} xl={8}>
                  <CardBox
                    accent={KB_ACCENT[item.type ?? 0]}
                    icon={<KnowledgeIcon type={item.type} />}
                    title={item.name}
                    description={item.desc}
                    onClick={() => router.push(`/knowledge/${item.id}/document`)}
                    subTitle={
                      <span style={{fontSize: 12, color: 'inherit', opacity: 0.55}}>
                        {i18n_name(item.nick_name)}
                        <span style={{margin: '0 4px'}}>{t('common.createdIn')}</span>
                        {dateFormat(item.create_time)}
                      </span>
                    }
                    tag={
                      isBatch ? (
                        <Checkbox value={item.id} />
                      ) : item.type === 1 ? (
                        <Tag color="purple" style={{borderRadius: 6, marginInlineEnd: 0}}>WEB</Tag>
                      ) : null
                    }
                    footer={
                      <div style={{display: 'flex', alignItems: 'center', gap: 14, fontSize: 12}}>
                        <span style={{display: 'inline-flex', alignItems: 'baseline', gap: 4}}>
                          <span style={{fontWeight: 700, fontSize: 14}}>{item?.document_count || 0}</span>
                          <span style={{opacity: 0.55}}>{t('views.knowledge.document_count')}</span>
                        </span>
                        <span style={{opacity: 0.25}}>|</span>
                        <span style={{display: 'inline-flex', alignItems: 'baseline', gap: 4}}>
                          <span style={{fontWeight: 700, fontSize: 14}}>{numberFormat(item?.char_length)}</span>
                          <span style={{opacity: 0.55}}>{t('common.character')}</span>
                        </span>
                      </div>
                    }
                    mouseEnter={
                      <Dropdown
                        menu={{
                          items: menuItems(item),
                          onClick: ({key}) => onMenuClick(item, key),
                        }}
                        trigger={['click']}
                      >
                        <Button type="text" icon={<MoreOutlined />} />
                      </Dropdown>
                    }
                  />
                </Col>
              ))}
            </Row>
          </Checkbox.Group>
        )}
      </InfiniteScroll>

      <CreateKnowledgeDialog ref={createRef} onRefresh={refresh} />
      <CreateWebKnowledgeDialog ref={webRef} onRefresh={refresh} />
      <CreateLarkKnowledgeDialog ref={larkRef} onRefresh={refresh} />
      <CreateWorkflowKnowledgeDialog ref={workflowRef} onRefresh={refresh} />
      <CreateFolderDialog ref={createFolderRef} onRefresh={refresh} />
      <MoveToDialog ref={moveRef} onRefresh={refresh} source={SourceTypeEnum.KNOWLEDGE} />
      <GenerateRelatedDialog ref={genRef} />
      <ResourceAuthorizationDrawer ref={authRef} type={SourceTypeEnum.KNOWLEDGE} />
      <ResourceMappingDrawer ref={mapRef} />
      <ExportKnowledgeDialog ref={exportRef} />
      <SyncWebDialog ref={syncRef} />
    </div>
  )
}
