'use client'
import React, {forwardRef, useImperativeHandle, useRef, useState} from 'react'
import {Modal, Tabs, Form, Input, Select, Empty, Table, Tag, Button, Breadcrumb} from 'antd'
import DynamicsForm from '@/components/dynamics-form'
import {input_type_list} from './data'
import providerApi from '@/lib/api/model/provider'
import {loadSharedApi} from '@/lib/api/shared-api'
import {useTranslations} from 'next-intl'
import {MsgSuccess, MsgError} from '@/utils/message'
import type {FormField} from '@/components/dynamics-form/type'
import AddParamDrawer from './AddParamDrawer'

export interface CreateModelDialogRef {
  open: (provider: any, model_type?: string) => void
  close: () => void
}

const CreateModelDialog = forwardRef<CreateModelDialogRef, {onChange?: () => void; onSubmit?: () => void}>(
  function CreateModelDialog({onChange, onSubmit}, ref) {
    const t = useTranslations()
    const [open, setOpen] = useState(false)
    const [activeName, setActiveName] = useState('base-info')
    const [providerValue, setProviderValue] = useState<any>(null)
    const [modelTypeList, setModelTypeList] = useState<any[]>([])
    const [baseModelList, setBaseModelList] = useState<any[]>([])
    const [modelFormField, setModelFormField] = useState<FormField[]>([])
    const [baseForm, setBaseForm] = useState<any>({
      name: '',
      model_type: '',
      model_name: '',
      model_params_form: [],
    })
    const [loading, setLoading] = useState(false)
    const baseFormRef = useRef<any>(null)
    const dynamicsFormRef = useRef<any>(null)
    const addParamRef = useRef<any>(null)

    useImperativeHandle(ref, () => ({
      open: (provider: any, model_type?: string) => {
        setProviderValue(provider)
        setOpen(true)
        setActiveName('base-info')
        setBaseForm({name: '', model_type: model_type || '', model_name: '', model_params_form: []})
        setModelFormField([])
        setBaseModelList([])
        providerApi
          .listModelType(provider.provider)
          .then((ok: any) => setModelTypeList(ok.data || []))
          .catch(() => setModelTypeList([]))
        if (model_type) listBaseModel(model_type, false)
      },
      close: () => setOpen(false),
    }))

    const listBaseModel = (model_type: any, change?: boolean) => {
      if (change) setBaseForm((b: any) => ({...b, model_name: '', model_params_form: []}))
      if (providerValue)
        providerApi
          .listBaseModel(providerValue.provider, model_type)
          .then((ok: any) => setBaseModelList(ok.data || []))
          .catch(() => setBaseModelList([]))
    }

    const getModelForm = (model_name: string) => {
      if (!baseForm.model_type) {
        MsgError(t('views.model.modelForm.model_type.requiredMessage'))
        setBaseForm((b: any) => ({...b, model_name: ''}))
        return
      }
      if (providerValue) {
        providerApi
          .getModelCreateForm(providerValue.provider, baseForm.model_type, model_name)
          .then((ok: any) => {
            setModelFormField(ok.data || [])
            dynamicsFormRef.current?.render(ok.data || [])
          })
        providerApi
          .listBaseModelParamsForm(providerValue.provider, baseForm.model_type, model_name)
          .then((ok: any) => setBaseForm((b: any) => ({...b, model_params_form: ok.data || []})))
      }
    }

    const submit = () => {
      baseFormRef.current
        ?.validateFields()
        .then(() =>
          dynamicsFormRef.current
            ?.validate()
            .then(() => {
              const credential = dynamicsFormRef.current?.getFormData() || {}
              setLoading(true)
              loadSharedApi({type: 'model'})
                .createModel({...baseForm, credential, provider: providerValue.provider})
                .then(() => {
                  setLoading(false)
                  setOpen(false)
                  MsgSuccess(t('views.model.tip.createSuccessMessage'))
                  onChange?.()
                  onSubmit?.()
                })
                .catch(() => setLoading(false))
            })
            .catch(() => MsgError(t('views.model.tip.createErrorMessage'))),
        )
        .catch(() => {})
    }

    const openAddDrawer = (data?: any, index?: any) => addParamRef.current?.open(data, index)
    const refresh = (data: any, index: any) => {
      const list = [...baseForm.model_params_form]
      if (index !== null && index !== undefined) list.splice(index, 1, data)
      else list.push(data)
      setBaseForm((b: any) => ({...b, model_params_form: list}))
    }

    const toSelectProvider = () => {
      setOpen(false)
      onChange?.()
    }

    const inputTypeLabel = (v: string) => input_type_list.find((i) => i.value === v)?.label || v

    return (
      <Modal
        open={open}
        width={600}
        onCancel={() => setOpen(false)}
        destroyOnHidden
        title={
          <Breadcrumb
            items={[
              {title: <span style={{cursor: 'pointer'}} onClick={toSelectProvider}>{t('views.model.providerPlaceholder')}</span>},
              {title: `${t('common.add')} ${providerValue?.name || ''}`},
            ]}
          />
        }
        footer={[
          <Button key="cancel" onClick={() => setOpen(false)}>
            {t('common.cancel')}
          </Button>,
          <Button key="ok" type="primary" loading={loading} onClick={submit}>
            {t('common.save')}
          </Button>,
        ]}
      >
        <Tabs activeKey={activeName} onChange={setActiveName}>
          <Tabs.TabPane tab={t('views.model.modelForm.title.baseInfo')} key="base-info">
            <Form ref={baseFormRef} layout="vertical">
              <Form.Item
                name="name"
                label={t('views.model.modelForm.modeName.label')}
                rules={[{required: true, message: t('views.model.modelForm.modeName.requiredMessage')}]}
              >
                <Input
                  maxLength={64}
                  showCount
                  value={baseForm.name}
                  onChange={(e) => setBaseForm((b: any) => ({...b, name: e.target.value}))}
                />
              </Form.Item>
              <Form.Item
                name="model_type"
                label={t('views.model.modelForm.model_type.label')}
                rules={[{required: true, message: t('views.model.modelForm.model_type.requiredMessage')}]}
              >
                <Select
                  loading={false}
                  value={baseForm.model_type}
                  onChange={(v) => {
                    setBaseForm((b: any) => ({...b, model_type: v}))
                    listBaseModel(v, true)
                  }}
                  options={modelTypeList.map((i) => ({label: i.key, value: i.value}))}
                  placeholder={t('views.model.modelForm.model_type.placeholder')}
                />
              </Form.Item>
              <Form.Item
                name="model_name"
                label={t('views.model.modelForm.base_model.label')}
                rules={[{required: true, message: t('views.model.modelForm.base_model.requiredMessage')}]}
              >
                <Select
                  showSearch
                  value={baseForm.model_name}
                  onChange={(v) => {
                    setBaseForm((b: any) => ({...b, model_name: v}))
                    getModelForm(v)
                  }}
                  options={baseModelList.map((i) => ({label: i.name, value: i.name}))}
                  placeholder={t('views.model.modelForm.base_model.placeholder')}
                />
              </Form.Item>
            </Form>
            {modelFormField.length > 0 && <DynamicsForm ref={dynamicsFormRef} renderData={modelFormField} />}
          </Tabs.TabPane>
          <Tabs.TabPane tab={t('views.model.modelForm.title.advancedInfo')} key="advanced-info">
            {!baseForm.model_type || !baseForm.model_name ? (
              <Empty description={t('views.model.tip.emptyMessage1')} />
            ) : baseForm.model_type === 'RERANKER' ? (
              <Empty description={t('views.model.tip.emptyMessage2')} />
            ) : (
              <>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8}}>
                  <h5 style={{margin: 0}}>{t('views.model.modelForm.title.modelParams')}</h5>
                  <Button
                    type="link"
                    icon={<span>+</span>}
                    onClick={() => openAddDrawer()}
                    disabled={!['TTS', 'LLM', 'IMAGE', 'TTI', 'TTV', 'ITV', 'STT', 'EMBEDDING'].includes(baseForm.model_type)}
                  >
                    {t('common.add')}
                  </Button>
                </div>
                <Table
                  size="small"
                  dataSource={baseForm.model_params_form}
                  pagination={false}
                  rowKey={(_r: any, idx?: number) => idx ?? 0}
                  columns={[
                    {
                      title: t('dynamicsForm.paramForm.name.label'),
                      dataIndex: 'label',
                      render: (v: any) => (v && v.label ? v.label : v),
                    },
                    {title: t('dynamicsForm.paramForm.field.label'), dataIndex: 'field', width: 95},
                    {
                      title: t('dynamicsForm.paramForm.input_type.label'),
                      width: 110,
                      render: (v: any) => <Tag color="blue">{inputTypeLabel(v)}</Tag>,
                    },
                    {title: t('dynamicsForm.default.label'), dataIndex: 'default_value'},
                    {
                      title: t('common.operation'),
                      width: 90,
                      render: (_: any, _r: any, index: number) => (
                        <span>
                          <Button type="link" size="small" onClick={() => openAddDrawer(_r, index)}>
                            {t('common.modify')}
                          </Button>
                          <Button type="link" size="small" danger onClick={() => refresh(_r, index)}>
                            {t('common.delete')}
                          </Button>
                        </span>
                      ),
                    },
                  ]}
                />
              </>
            )}
          </Tabs.TabPane>
        </Tabs>
        <AddParamDrawer ref={addParamRef} onRefresh={refresh} />
      </Modal>
    )
  },
)

export default CreateModelDialog
