'use client'
import React from 'react'
import {Tooltip} from 'antd'
import {QuestionCircleOutlined} from '@ant-design/icons'

// 表单项标签：支持纯文本或带 tooltip 的对象型 label
export default function FormItemLabel({formField}: {formField: any}) {
  const label = formField.label
  if (typeof label === 'string') {
    return <>{label}</>
  }
  if (label && typeof label === 'object' && 'label' in label) {
    return (
      <span style={{display: 'inline-flex', alignItems: 'center', gap: 4}}>
        <span>{label.label}</span>
        {label.tooltip && (
          <Tooltip title={label.tooltip}>
            <QuestionCircleOutlined style={{color: '#faad14'}} />
          </Tooltip>
        )}
      </span>
    )
  }
  return <>{String(label ?? '')}</>
}
