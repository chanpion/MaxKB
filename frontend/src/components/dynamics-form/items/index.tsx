'use client'
import React from 'react'
import {Input, Select, Radio, Checkbox, Slider, Switch, DatePicker, Upload, Tree, TreeSelect, Tag} from 'antd'
import type {FormField} from '../type'

export interface DynamicItemProps {
  value?: any
  onChange?: (v: any) => void
  formField: FormField
}

function optionsOf(formField: FormField): Array<{label: any; value: any}> {
  const list = formField.option_list || []
  const textField = formField.text_field || 'key'
  const valueField = formField.value_field || 'value'
  return list.map((item: any) => ({
    label: item[textField],
    value: item[valueField],
  }))
}

function pickAttrs(attrs?: Record<string, any>): Record<string, any> {
  if (!attrs) return {}
  const allowed = ['placeholder', 'maxLength', 'showCount', 'allowClear', 'disabled', 'rows', 'step', 'min', 'max', 'precision', 'mode', 'multiple']
  const out: Record<string, any> = {}
  for (const k of allowed) {
    if (k in attrs) out[k] = attrs[k]
  }
  return out
}

const TextInput: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Input value={value} onChange={(e) => onChange?.(e.target.value)} {...pickAttrs(formField.attrs)} />
)

const PasswordInput: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Input.Password value={value} onChange={(e) => onChange?.(e.target.value)} {...pickAttrs(formField.attrs)} />
)

const TextareaInput: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Input.TextArea
    value={value}
    onChange={(e) => onChange?.(e.target.value)}
    autoSize={{minRows: 3}}
    {...pickAttrs(formField.attrs)}
  />
)

const JsonInput: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Input.TextArea
    value={typeof value === 'string' ? value : value ? JSON.stringify(value, null, 2) : ''}
    onChange={(e) => onChange?.(e.target.value)}
    autoSize={{minRows: 4}}
    style={{fontFamily: 'monospace'}}
    {...pickAttrs(formField.attrs)}
  />
)

const NumberInput: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Input
    type="number"
    value={value}
    onChange={(e) => onChange?.(e.target.value === '' ? undefined : Number(e.target.value))}
    {...pickAttrs(formField.attrs)}
  />
)

const SingleSelect: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Select
    value={value}
    onChange={onChange}
    options={optionsOf(formField)}
    style={{width: '100%'}}
    allowClear
    showSearch
    optionFilterProp="label"
    {...pickAttrs(formField.attrs)}
  />
)

const MultiSelect: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Select
    mode="multiple"
    value={value}
    onChange={onChange}
    options={optionsOf(formField)}
    style={{width: '100%'}}
    allowClear
    showSearch
    optionFilterProp="label"
    {...pickAttrs(formField.attrs)}
  />
)

const RadioItem: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Radio.Group value={value} onChange={(e) => onChange?.(e.target.value)} options={optionsOf(formField)} />
)

const RadioButtonItem: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Radio.Group value={value} onChange={(e) => onChange?.(e.target.value)} optionType="button" buttonStyle="solid" options={optionsOf(formField)} />
)

const RadioRow: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Radio.Group value={value} onChange={(e) => onChange?.(e.target.value)} options={optionsOf(formField)} />
)

const RadioCard: React.FC<DynamicItemProps> = ({value, onChange, formField}) => {
  const opts = optionsOf(formField)
  return (
    <div style={{display: 'flex', flexWrap: 'wrap', gap: 8, width: '100%'}}>
      {opts.map((opt) => {
        const active = value === opt.value
        return (
          <div
            key={String(opt.value)}
            onClick={() => onChange?.(opt.value)}
            style={{
              cursor: 'pointer',
              flex: '1 1 calc(50% - 8px)',
              minWidth: 140,
              padding: '10px 14px',
              borderRadius: 8,
              border: `1px solid ${active ? '#1677ff' : 'var(--ant-color-border, #d9d9d9)'}`,
              color: active ? '#1677ff' : 'inherit',
              background: active ? 'rgba(22,119,255,0.06)' : 'transparent',
            }}
          >
            {opt.label}
          </div>
        )
      })}
    </div>
  )
}

const MultiRow: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Checkbox.Group value={value} onChange={onChange} options={optionsOf(formField)} />
)

const SliderItem: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Slider value={value ?? 0} onChange={onChange} {...pickAttrs(formField.attrs)} />
)

const SwitchItem: React.FC<DynamicItemProps> = ({value, onChange}) => (
  <Switch checked={!!value} onChange={onChange} />
)

const DatePickerItem: React.FC<DynamicItemProps> = ({value, onChange}) => (
  <DatePicker value={value ? (value as any) : null} onChange={(d) => onChange?.(d)} style={{width: '100%'}} />
)

const UploadInput: React.FC<DynamicItemProps> = ({value, onChange}) => (
  <Upload
    beforeUpload={(file) => {
      onChange?.(file)
      return false
    }}
    maxCount={1}
    fileList={value ? [value] : []}
  >
    <Input placeholder="点击上传文件" readOnly />
  </Upload>
)

const ModelItem: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Select
    value={value}
    onChange={onChange}
    options={optionsOf(formField)}
    style={{width: '100%'}}
    allowClear
    showSearch
    optionFilterProp="label"
  />
)

const KnowledgeItem: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Select
    value={value}
    onChange={onChange}
    options={optionsOf(formField)}
    style={{width: '100%'}}
    allowClear
    showSearch
    optionFilterProp="label"
  />
)

const TreeSelectItem: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <TreeSelect
    value={value}
    onChange={onChange}
    treeData={formField.option_list}
    style={{width: '100%'}}
    allowClear
    treeDefaultExpandAll
  />
)

const TreeItem: React.FC<DynamicItemProps> = ({value, onChange, formField}) => (
  <Tree
    selectable
    selectedKeys={value ? [value] : []}
    onSelect={(keys) => onChange?.(keys[0])}
    treeData={formField.option_list}
  />
)

// 输入类型 -> 组件 注册表（完整覆盖 Vue 端 items/*）
export const itemRegistry: Record<string, React.FC<DynamicItemProps>> = {
  TextInput,
  PasswordInput,
  TextareaInput,
  JsonInput,
  NumberInput,
  SingleSelect,
  MultiSelect,
  Radio: RadioItem,
  RadioButton: RadioButtonItem,
  RadioRow,
  RadioCard,
  MultiRow,
  Slider: SliderItem,
  SwitchInput: SwitchItem,
  DatePicker: DatePickerItem,
  UploadInput,
  Model: ModelItem,
  Knowledge: KnowledgeItem,
  TreeSelect: TreeSelectItem,
  Tree: TreeItem,
}

export function getItemComponent(inputType: string): React.FC<DynamicItemProps> {
  return itemRegistry[inputType] || TextInput
}
