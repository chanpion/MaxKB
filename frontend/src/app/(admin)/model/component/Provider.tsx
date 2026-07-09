'use client'
import React, {useState, useEffect} from 'react'
import {Collapse} from 'antd'
import CommonList from '@/components/CommonList'
import {RawIcon} from '@/components/AppIcon'
import {useTranslations} from 'next-intl'

const localProviders = [
  'model_ollama_provider',
  'model_local_provider',
  'model_xinference_provider',
  'model_vllm_provider',
  'model_docker_ai_provider',
]

export default function Provider({
  data,
  active,
  onClick,
}: {
  data: Array<any>
  active?: any
  onClick?: (p: any) => void
}) {
  const t = useTranslations()
  const [online, setOnline] = useState<Array<any>>([])
  const [local, setLocal] = useState<Array<any>>([])

  useEffect(() => {
    const o: any[] = []
    const l: any[] = []
    ;(data || []).forEach((p) => {
      if (localProviders.includes(p.provider)) l.push(p)
      else o.push(p)
    })
    o.sort((a, b) => a.provider.localeCompare(b.provider))
    l.sort((a, b) => a.provider.localeCompare(b.provider))
    setOnline(o)
    setLocal(l)
  }, [data])

  const renderRow = (row: any) => (
    <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
      <RawIcon html={row.icon} />
      <span className="ellipsis-1">{row.name}</span>
    </div>
  )

  return (
    <div>
      <h4 style={{padding: '12px 16px 0', margin: '12px 0'}}>{t('views.model.provider')}</h4>
      <div
        onClick={() => onClick?.({provider: '', name: t('views.model.modelType.allModel')})}
        style={{
          padding: '10px 8px',
          cursor: 'pointer',
          borderRadius: 6,
          color: !active?.provider ? '#1677ff' : 'inherit',
          fontWeight: !active?.provider ? 500 : 400,
          background: !active?.provider ? 'rgba(22,119,255,0.1)' : 'transparent',
        }}
      >
        {t('views.model.modelType.allModel')}
      </div>
      <Collapse defaultActiveKey={['1', '2']} ghost>
        <Collapse.Panel header={t('views.model.modelType.publicModel')} key="1">
          <CommonList data={online} activeKey={active?.provider} onSelect={onClick}>
            {renderRow}
          </CommonList>
        </Collapse.Panel>
        <Collapse.Panel header={t('views.model.modelType.privateModel')} key="2">
          <CommonList data={local} activeKey={active?.provider} onSelect={onClick}>
            {renderRow}
          </CommonList>
        </Collapse.Panel>
      </Collapse>
    </div>
  )
}
