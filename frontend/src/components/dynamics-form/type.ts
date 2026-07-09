// 动态表单字段定义，对齐 Vue 端 @/components/dynamics-form/type.ts
export interface FormField {
  field: string
  /** 输入框类型，对应 items/* 的组件名 */
  input_type: string
  label?: string | any
  required?: boolean
  default_value?: any
  show_default_value?: boolean
  /** {field: valueList} 仅当 field 命中 valueList 时才显示 */
  relation_show_field_dict?: Record<string, Array<any>>
  trigger_type?: 'OPTION_LIST' | 'CHILD_FORMS'
  attrs?: Record<string, any>
  props_info?: {
    style?: Record<string, any>
    item_style?: Record<string, any>
    rules?: any
    err_msg?: string
    tabs_label?: string
    [key: string]: any
  }
  text_field?: string
  value_field?: string
  option_list?: Array<any>
  provider?: string
  method?: string
  children?: Array<FormField>
  required_asterisk?: boolean
  [key: string]: any
}
