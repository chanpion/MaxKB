'use client'
import React, {forwardRef, useImperativeHandle, useRef, useState} from 'react'
import {Modal, Form, Input, Select, Button} from 'antd'
import DynamicsForm from '@/components/dynamics-form'
import providerApi from '@/lib/api/model/provider'
import modelApi from '@/lib/api/model/model'
import {useTranslations} from 'next-intl'
import {MsgSuccess, MsgError} from '@/utils/message'
import type {FormField} from '@/components/dynamics-form/type'

export interface EditModelRef {
  open: (provider: any, model: any) => void
}

const EditModel = forwardRef<EditModelRef, {onChange?: () => void; apiType?: string}>(
  function EditModel({onChange, apiType = 'workspace'}, ref) {
    const t = useTranslations()
    const [open, setOpen] = useState(false)
    const [provider, setProvider] = useState<any>(null)
    const [model, setModel] = useState<any>(null)
    const [modelTypeList, setModelTypeList] = useState<any[]>([])
    const [baseModelList, setBaseModelList] = useState<any[]>([])
    const [modelFormField, setModelFormField] = useState<FormField[]>([])
    const [baseForm, setBaseForm] = useState<any>({name: '', model_type: '', model_name: ''})
    const [loading, setLoading] = useState(false)
    const baseFormRef = useRef<any>(null)
    const dynamicsFormRef = useRef<any>(null)

    useImperativeHandle(ref, () => ({
      open: (p: any, m: any) => {
        setProvider(p)
        setModel(m)
        setOpen(true)
        providerApi
          .listModelType(p.provider)
          .then((ok: any) => setModelTypeList(ok.data || []))
        modelApi.getModelById(m.id).then((ok: any) => {
          const d = ok.data
          setBaseForm({name: d.name, model_type: d.model_type, model_name: d.model_name})
          providerApi
            .getModelCreateForm(p.provider, d.model_type, d.model_name)
            .then((f: any) => {
              setModelFormField(f.data || [])
              if (dynamicsFormRef.current) dynamicsFormRef.current.render(f.data || [], d.credential || {})
            })
        })
      },
    }))

    const submit = () => {
      baseFormRef.current
        ?.validateFields()
        .then(() =>
          dynamicsFormRef.current
            ?.validate()
            .then(() => {
              const credential = dynamicsFormRef.current?.getFormData() || {}
              setLoading(true)
              modelApi
                .updateModel(model.id, {...baseForm, credential})
                .then(() => {
                  setLoading(false)
                  setOpen(false)
                  MsgSuccess(t('common.saveSuccess'))
                  onChange?.()
                })
                .catch(() => setLoading(false))
            })
            .catch(() => MsgError(t('views.model.tip.createErrorMessage'))),
        )
        .catch(() => {})
    }

    return (
      <Modal
        open={open}
        width={600}
        onCancel={() => setOpen(false)}
        destroyOnHidden
        title={t('common.edit')}
        footer={[
          <Button key="c" onClick={() => setOpen(false)}>
            {t('common.cancel')}
          </Button>,
          <Button key="ok" type="primary" loading={loading} onClick={submit}>
            {t('common.save')}
          </Button>,
        ]}
      >
        <Form ref={baseFormRef} layout="vertical">
          <Form.Item
            name="name"
            label={t('views.model.modelForm.modeName.label')}
            rules={[{required: true, message: t('views.model.modelForm.modeName.requiredMessage')}]}
          >
            <Input value={baseForm.name} onChange={(e) => setBaseForm((b: any) => ({...b, name: e.target.value}))} maxLength={64} showCount />
          </Form.Item>
          <Form.Item name="model_type" label={t('views.model.modelForm.model_type.label')} rules={[{required: true}]}>
            <Select
              value={baseForm.model_type}
              onChange={(v) => setBaseForm((b: any) => ({...b, model_type: v}))}
              options={modelTypeList.map((i) => ({label: i.key, value: i.value}))}
            />
          </Form.Item>
          <Form.Item name="model_name" label={t('views.model.modelForm.base_model.label')} rules={[{required: true}]}>
            <Select
              value={baseForm.model_name}
              onChange={(v) => setBaseForm((b: any) => ({...b, model_name: v}))}
              options={baseModelList.map((i) => ({label: i.name, value: i.name}))}
            />
          </Form.Item>
        </Form>
        {modelFormField.length > 0 && <DynamicsForm ref={dynamicsFormRef} renderData={modelFormField} />}
      </Modal>
    )
  },
)

export default EditModel
