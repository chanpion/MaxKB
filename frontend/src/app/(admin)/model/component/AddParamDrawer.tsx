'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Drawer, Form, Input, Select, Switch, Button, message} from 'antd'
import {useTranslations} from 'next-intl'
import {input_type_list} from './data'

export interface AddParamDrawerRef {
  open: (data?: any, index?: any) => void
}

const AddParamDrawer = forwardRef<AddParamDrawerRef, {onRefresh: (data: any, index: any) => void}>(
  function AddParamDrawer({onRefresh}, ref) {
    const [open, setOpen] = useState(false)
    const [index, setIndex] = useState<any>(null)
    const [form] = Form.useForm()
    const t = useTranslations()

    useImperativeHandle(ref, () => ({
      open: (data?: any, idx?: any) => {
        setIndex(idx ?? null)
        setOpen(true)
        if (data) {
          form.setFieldsValue({
            field: data.field,
            label: typeof data.label === 'string' ? data.label : data.label?.label,
            input_type: data.input_type,
            default_value: data.default_value,
            required: !!data.required,
          })
        } else {
          form.resetFields()
          form.setFieldsValue({input_type: 'TextInput', required: false})
        }
      },
    }))

    const submit = () => {
      form.validateFields().then((vals) => {
        const data = {
          field: vals.field,
          label: vals.label,
          input_type: vals.input_type,
          default_value: vals.default_value,
          required: vals.required,
        }
        onRefresh(data, index)
        setOpen(false)
        message.success(t('common.saveSuccess'))
      })
    }

    return (
      <Drawer
        title={t('dynamicsForm.paramForm.title')}
        open={open}
        onClose={() => setOpen(false)}
        width={420}
        destroyOnHidden
        footer={
          <Button type="primary" onClick={submit} block>
            {t('common.save')}
          </Button>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item name="field" label={t('dynamicsForm.paramForm.field.label')} rules={[{required: true}]}>
            <Input />
          </Form.Item>
          <Form.Item name="label" label={t('dynamicsForm.paramForm.name.label')} rules={[{required: true}]}>
            <Input />
          </Form.Item>
          <Form.Item name="input_type" label={t('dynamicsForm.paramForm.input_type.label')} rules={[{required: true}]}>
            <Select options={input_type_list.map((i) => ({label: i.label, value: i.value}))} />
          </Form.Item>
          <Form.Item name="default_value" label={t('dynamicsForm.default.label')}>
            <Input />
          </Form.Item>
          <Form.Item name="required" label={t('common.required')} valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Drawer>
    )
  },
)

export default AddParamDrawer
