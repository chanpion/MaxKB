import {message, Modal} from 'antd'

// 对 antd message 的轻封装，便于在请求层 / 非组件逻辑中调用
export const MsgError = (msg: string) => message.error(msg)
export const MsgSuccess = (msg: string) => message.success(msg)
export const MsgWarning = (msg: string) => message.warning(msg)
export const MsgInfo = (msg: string) => message.info(msg)

// 确认弹窗，返回 Promise；点击确定 resolve，取消/关闭 reject
export const MsgConfirm = (
  content: string,
  title?: string,
  options?: {confirmButtonText?: string; cancelButtonText?: string; confirmButtonClass?: string},
) => {
  return new Promise<void>((resolve, reject) => {
    Modal.confirm({
      title: title || '提示',
      content,
      okText: options?.confirmButtonText || '确定',
      cancelText: options?.cancelButtonText || '取消',
      okButtonProps: options?.confirmButtonClass === 'danger' ? {danger: true} : undefined,
      onOk: () => resolve(),
      onCancel: () => reject(),
    })
  })
}

// 警告提示（对齐 Vue MsgAlert）
export const MsgAlert = (content: string, title?: string) => {
  Modal.warning({title: title || '警告', content})
}
