'use client'
import React, {
  forwardRef,
  useImperativeHandle,
  useState,
  useRef,
  useEffect,
} from 'react'
import {Form} from 'antd'
import FormItem from './FormItem'
import type {FormField} from './type'

export interface DynamicsFormRef {
  render: (fields: FormField[], data?: Record<string, any>) => void
  validate: () => Promise<void>
  getFormData: () => Record<string, any>
}

interface Props {
  value?: Record<string, any>
  renderData?: FormField[] | (() => Promise<{data: FormField[]}>) | string
  model?: Record<string, any>
}

function isVisible(field: FormField, values: Record<string, any>): boolean {
  if (field.relation_show_field_dict) {
    for (const key of Object.keys(field.relation_show_field_dict)) {
      const v = values[key]
      if (v === undefined || v === null || v === '') return false
      const allowed = field.relation_show_field_dict[key]
      if (allowed && allowed.length > 0) {
        return allowed.includes(v)
      }
    }
  }
  return true
}

function computeDefaults(
  fields: FormField[],
  data?: Record<string, any>,
): Record<string, any> {
  const out: Record<string, any> = {...(data || {})}
  fields.forEach((f) => {
    if (data && data[f.field] !== undefined) {
      out[f.field] = data[f.field]
    } else if (
      f.default_value !== undefined &&
      (f.show_default_value === true || f.show_default_value === undefined)
    ) {
      out[f.field] = f.default_value
    }
  })
  return out
}

const DynamicsForm = forwardRef<DynamicsFormRef, Props>(function DynamicsForm(
  {value, renderData, model},
  ref,
) {
  const [form] = Form.useForm()
  const [fieldList, setFieldList] = useState<FormField[]>([])
  const [values, setValues] = useState<Record<string, any>>({})

  const render = (fields: FormField[], data?: Record<string, any>) => {
    setFieldList(fields || [])
    const defaults = computeDefaults(fields || [], data)
    form.resetFields()
    form.setFieldsValue(defaults)
    setValues(defaults)
  }

  useImperativeHandle(ref, () => ({
    render,
    validate: () => form.validateFields().then(() => undefined),
    getFormData: () => form.getFieldsValue(true),
  }))

  useEffect(() => {
    if (Array.isArray(renderData)) {
      render(renderData, value)
    } else if (typeof renderData === 'function') {
      Promise.resolve((renderData as any)()).then((ok: any) => {
        render(ok?.data || ok, value)
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const visibleFields = fieldList.filter((f) => isVisible(f, values))

  return (
    <Form
      form={form}
      layout="vertical"
      requiredMark
      onValuesChange={(_, all) => setValues(all)}
      initialValues={value}
    >
      {visibleFields.map((field) => (
        <FormItem key={field.field} formField={field} />
      ))}
    </Form>
  )
})

export default DynamicsForm
