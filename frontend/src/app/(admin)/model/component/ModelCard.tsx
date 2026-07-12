'use client'
import React, {useState, useEffect, useRef} from 'react'
import {Dropdown, Button, Tag, Tooltip} from 'antd'
import {MoreOutlined, WarningFilled} from '@ant-design/icons'
import CardBox from '@/components/CardBox'
import DownloadLoading from '@/components/DownloadLoading'
import {RawIcon} from '@/components/AppIcon'
import {i18n_name} from '@/utils/common'
import {dateFormat} from '@/utils/time'
import {modelType} from '@/enums/model'
import {useTranslations} from 'next-intl'
import {MsgConfirm, MsgSuccess} from '@/utils/message'
import {loadSharedApi} from '@/lib/api/shared-api'
import {SourceTypeEnum} from '@/enums/common'
import EditModel from './EditModel'
import ParamSettingDialog from './ParamSettingDialog'
import ResourceAuthorizationDrawer from '@/components/resource-authorization-drawer'
import WorkspaceAuthorizationDrawer from '@/components/workspace-authorization-drawer'
import ResourceMappingDrawer from '@/components/resource_mapping'

export default function ModelCard({
  model,
  provider_list,
  onChange,
  apiType = 'workspace',
}: {
  model: any
  provider_list: Array<any>
  onChange?: () => void
  apiType?: 'workspace' | 'systemShare' | 'systemManage'
}) {
  const t = useTranslations()
  const [downModel, setDownModel] = useState<any>(null)
  const editModelRef = useRef<any>(null)
  const paramRef = useRef<any>(null)
  const authRef = useRef<any>(null)
  const wsAuthRef = useRef<any>(null)
  const mapRef = useRef<any>(null)
  const interval = useRef<any>()

  const current = downModel || model
  const providerIcon = provider_list.find((p) => p.provider === model.provider)?.icon
  const isSystemShare = apiType === 'systemShare'

  const initInterval = () => {
    interval.current = setInterval(() => {
      if (current.status === 'DOWNLOAD') {
        loadSharedApi({type: 'model', systemType: apiType})
          .getModelMetaById(model.id)
          .then((ok: any) => setDownModel(ok.data))
      } else if (downModel) {
        onChange?.()
        setDownModel(undefined)
      }
    }, 6000)
  }

  useEffect(() => {
    initInterval()
    return () => clearInterval(interval.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const errMessage = () => {
    const msg = current?.meta?.message
    if (msg === 'pull model manifest: file does not exist') {
      return `${model.model_name} ${t('views.model.tip.noModel')}`
    }
    return msg || ''
  }

  const cancelDownload = () => {
    loadSharedApi({type: 'model', systemType: apiType})
      .pauseDownload(model.id)
      .then(() => {
        setDownModel(undefined)
        onChange?.()
      })
  }

  const deleteModel = () => {
    MsgConfirm(
      `${t('views.model.delete.confirmTitle')}${model.name} ?`,
      model.resource_count > 0
        ? t('views.model.delete.resourceCountMessage', {count: model.resource_count})
        : '',
      {confirmButtonText: t('common.confirm'), confirmButtonClass: 'danger'},
    )
      .then(() => {
        loadSharedApi({type: 'model', systemType: apiType})
          .deleteModel(model.id)
          .then(() => {
            onChange?.()
            MsgSuccess(t('common.deleteSuccess'))
          })
      })
      .catch(() => {})
  }

  const menuItems = [
    {key: 'edit', label: t('common.edit'), onClick: () => editModelRef.current?.open(provider_list.find((p) => p.provider === model.provider), model)},
    isSystemShare && {
      key: 'authWs',
      label: t('views.shared.authorized_workspace'),
      onClick: () => wsAuthRef.current?.open(model.id),
    },
    (['TTS', 'STT', 'LLM', 'IMAGE', 'TTI', 'ITV', 'EMBEDDING', 'TTV'].includes(current.model_type) && {
      key: 'param',
      label: t('views.model.modelForm.title.paramSetting'),
      onClick: () => paramRef.current?.open(model),
    }),
    apiType === 'workspace' && {
      key: 'auth',
      label: t('views.system.resourceAuthorization.title'),
      onClick: () => authRef.current?.open(model.id),
    },
    {key: 'map', label: t('views.system.resourceMapping.title'), onClick: () => mapRef.current?.open('MODEL', model)},
    {type: 'divider' as const},
    {key: 'delete', label: t('common.delete'), danger: true, onClick: deleteModel},
  ].filter(Boolean) as any[]

  return (
    <>
      <CardBox
        icon={<RawIcon html={providerIcon} />}
        title={model.name}
        subTitle={
          <span style={{fontSize: 12, color: 'rgba(0,0,0,0.45)'}}>
            {i18n_name(model.nick_name)}
            <span style={{margin: '0 4px'}}>{t('common.createdIn')}</span>
            {dateFormat(model.create_time)}
          </span>
        }
        tag={
          isSystemShare ? <Tag color="default">{t('views.shared.title')}</Tag> : null
        }
        mouseEnter={
          <Dropdown menu={{items: menuItems}} trigger={['click']}>
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        }
        style={{minHeight: 135}}
      >
        <ul style={{listStyle: 'none', padding: 0, margin: 0, fontSize: 13}}>
          <li style={{display: 'flex', marginBottom: 4, overflow: 'hidden'}}>
            <span style={{color: 'rgba(0,0,0,0.45)', flexShrink: 0, marginRight: 8}}>{t('views.model.modelForm.model_type.label')}</span>
            <span className="ellipsis-1" style={{flex: 1, minWidth: 0}}>{t(modelType[current.model_type] || current.model_type)}</span>
          </li>
          <li style={{display: 'flex', overflow: 'hidden'}}>
            <span style={{color: 'rgba(0,0,0,0.45)', flexShrink: 0, marginRight: 8}}>{t('views.model.modelForm.base_model.label')}</span>
            <span className="ellipsis-1" style={{flex: 1, minWidth: 0}}>{current.model_name}</span>
          </li>
        </ul>
        {(current.status === 'ERROR' || current.status === 'PAUSE_DOWNLOAD') && (
          <Tooltip title={errMessage()}>
            <WarningFilled style={{color: '#ff4d4f'}} />
          </Tooltip>
        )}
        {current.status === 'DOWNLOAD' && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'rgba(255,255,255,0.92)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 8,
            }}
          >
            <DownloadLoading />
            <Button type="link" onClick={cancelDownload} style={{marginTop: 12}}>
              {t('views.model.download.cancelDownload')}
            </Button>
          </div>
        )}
      </CardBox>
      <EditModel ref={editModelRef} onChange={onChange} apiType={apiType} />
      <ParamSettingDialog ref={paramRef} />
      <ResourceAuthorizationDrawer ref={authRef} type={SourceTypeEnum.MODEL} />
      <WorkspaceAuthorizationDrawer ref={wsAuthRef} type={SourceTypeEnum.MODEL} />
      <ResourceMappingDrawer ref={mapRef} />
    </>
  )
}
