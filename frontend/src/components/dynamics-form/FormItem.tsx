'use client'
import React from 'react'
import {Form} from 'antd'
import {getItemComponent} from './items'
import type {FormField} from './type'

export default function FormItem({formField}: {formField: FormField}) {
  const ItemComponent = getItemComponent(formField.input_type)
  const propsInfo = formField.props_info || {}
  const labelText =
    typeof formField.label === 'string' ? formField.label : formField.label?.label || ''
  const errMsg = propsInfo.err_msg || `${labelText} ${'必填'}`

  const rules =
    formField.trigger_type === 'CHILD_FORMS'
      ? []
      : propsInfo.rules ||
        (formField.required === false
          ? []
          : [{required: true, message: errMsg}])

  return (
    <Form.Item
      name={formField.field}
      label={labelText}
      rules={rules}
      style={propsInfo.item_style}
      className={formField.required_asterisk ? 'hide-asterisk' : ''}
    >
      <ItemComponent formField={formField} />
    </Form.Item>
  )
}
