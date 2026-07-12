'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Drawer, Table, Button, Tag, message} from 'antd'
import modelApi from '@/lib/api/model/model'
import {input_type_list} from './data'
import {useTranslations} from 'next-intl'

export interface ParamSettingDialogRef {
  open: (model: any) => void
}

const ParamSettingDialog = forwardRef<ParamSettingDialogRef, {}>(function ParamSettingDialog(_props, ref) {
  const [open, setOpen] = useState(false)
  const [model, setModel] = useState<any>(null)
  const [list, setList] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const t = useTranslations()
  const inputTypeLabel = (v: string) => input_type_list.find((i) => i.value === v)?.label || v

  useImperativeHandle(ref, () => ({
    open: (m: any) => {
      setModel(m)
      setList(m.model_params_form || [])
      setOpen(true)
    },
  }))

  const save = () => {
    setLoading(true)
    modelApi
      .updateModelParamsForm(model.id, list)
      .then(() => {
        setLoading(false)
        setOpen(false)
        message.success(t('common.saveSuccess'))
      })
      .catch(() => setLoading(false))
  }

  return (
    <Drawer
      title={t('views.model.modelForm.title.paramSetting')}
      open={open}
      onClose={() => setOpen(false)}
      width={520}
      destroyOnHidden
      footer={
        <Button type="primary" loading={loading} onClick={save} block>
          {t('common.save')}
        </Button>
      }
    >
      <Table
        size="small"
        dataSource={list}
        pagination={false}
        rowKey={(_r: any, idx?: number) => idx ?? 0}
        columns={[
          {title: t('dynamicsForm.paramForm.name.label'), dataIndex: 'label', render: (v: any) => (v && v.label ? v.label : v)},
          {title: t('dynamicsForm.paramForm.field.label'), dataIndex: 'field', width: 95},
          {
            title: t('dynamicsForm.paramForm.input_type.label'),
            width: 110,
            render: (v: any) => <Tag color="blue">{inputTypeLabel(v)}</Tag>,
          },
          {title: t('dynamicsForm.default.label'), dataIndex: 'default_value'},
        ]}
      />
    </Drawer>
  )
})

export default ParamSettingDialog
