import {modelTypeList} from '@/enums/model'

export {modelTypeList}

export const allObj = {icon: '', provider: '', name: '全部模型'}

// 动态表单参数表使用的输入类型标签（用于在参数设置表格中展示）
export const input_type_list = [
  {value: 'TextInput', label: '文本'},
  {value: 'TextareaInput', label: '多行文本'},
  {value: 'JsonInput', label: 'JSON'},
  {value: 'PasswordInput', label: '密码'},
  {value: 'SingleSelect', label: '单选下拉'},
  {value: 'MultiSelect', label: '多选下拉'},
  {value: 'RadioCard', label: '单选卡片'},
  {value: 'RadioRow', label: '横向单选'},
  {value: 'MultiRow', label: '横向多选'},
  {value: 'Slider', label: '滑块'},
  {value: 'SwitchInput', label: '开关'},
  {value: 'DatePicker', label: '日期'},
]
