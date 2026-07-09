'use client'
import React, {useEffect, useRef, useState} from 'react'
import {Row, Col, Input, Select, Button, Empty, Spin} from 'antd'
import Provider from './component/Provider'
import ModelCard from './component/ModelCard'
import CreateModelDialog from './component/CreateModelDialog'
import SelectProviderDialog from './component/SelectProviderDialog'
import {useModelStore} from '@/store'
import {loadSharedApi} from '@/lib/api/shared-api'
import {allObj, modelTypeList} from './component/data'
import {useTranslations} from 'next-intl'

export default function ModelPage() {
  const t = useTranslations()
  const modelStore = useModelStore()
  const [activeProvider, setActiveProvider] = useState<any>(allObj)
  const [modelList, setModelList] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [searchType, setSearchType] = useState('name')
  const [searchForm, setSearchForm] = useState<any>({name: '', model_type: ''})
  const createRef = useRef<any>(null)
  const selectRef = useRef<any>(null)

  const listModel = () => {
    setLoading(true)
    const params = activeProvider?.provider ? {provider: activeProvider.provider} : {}
    loadSharedApi({type: 'model'})
      .getModelList({...searchForm, ...params})
      .then((ok: any) => {
        setModelList(ok.data || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    modelStore.asyncGetProvider().then(() => {
      setActiveProvider(allObj)
      listModel()
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const clickList = (p: any) => {
    setActiveProvider(p)
    listModel()
  }
  const openCreate = (provider?: any) => {
    if (provider?.provider) createRef.current?.open(provider)
    else selectRef.current?.open()
  }

  return (
    <div style={{display: 'flex', gap: 16, height: 'calc(100vh - 200px)'}}>
      <div style={{width: 240, overflow: 'auto', background: '#fff', borderRadius: 8, padding: 8, flexShrink: 0}}>
        <Provider data={modelStore.providerList} active={activeProvider} onClick={clickList} />
      </div>
      <div style={{flex: 1, overflow: 'auto', background: '#fff', borderRadius: 8, padding: 16}}>
        <div style={{display: 'flex', alignItems: 'center', marginBottom: 16, gap: 8}}>
          <Select
            value={searchType}
            style={{width: 130}}
            onChange={setSearchType}
            options={[
              {label: t('common.name'), value: 'name'},
              {label: t('views.model.modelForm.model_type.label'), value: 'model_type'},
            ]}
          />
          {searchType === 'name' && (
            <Input
              value={searchForm.name}
              allowClear
              onChange={(e) => setSearchForm((s: any) => ({...s, name: e.target.value}))}
              onPressEnter={listModel}
              placeholder={t('common.searchBar.placeholder')}
              style={{width: 240}}
            />
          )}
          {searchType === 'model_type' && (
            <Select
              value={searchForm.model_type}
              allowClear
              onChange={(v) => setSearchForm((s: any) => ({...s, model_type: v}))}
              options={modelTypeList.map((i) => ({label: t(i.text), value: i.value}))}
              style={{width: 240}}
              placeholder={t('views.model.modelForm.model_type.placeholder')}
            />
          )}
          <Button type="primary" onClick={() => openCreate(activeProvider)} style={{marginLeft: 'auto'}}>
            {t('views.model.addModel')}
          </Button>
        </div>
        {loading ? (
          <div style={{textAlign: 'center', padding: 40}}>
            <Spin />
          </div>
        ) : modelList.length === 0 ? (
          <Empty description={t('common.noData')} />
        ) : (
          <Row gutter={[16, 16]}>
            {modelList.map((m) => (
              <Col key={m.id} xs={24} sm={12} md={8} lg={8}>
                <ModelCard model={m} provider_list={modelStore.providerList} onChange={listModel} apiType="workspace" />
              </Col>
            ))}
          </Row>
        )}
      </div>
      <CreateModelDialog ref={createRef} onChange={listModel} />
      <SelectProviderDialog ref={selectRef} onChange={(p) => createRef.current?.open(p)} />
    </div>
  )
}
