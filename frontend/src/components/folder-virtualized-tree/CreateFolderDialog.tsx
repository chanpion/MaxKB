'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Modal, Form, Input, message} from 'antd'
import folderApi from '@/lib/api/workspace/folder'
import {useUserStore, useFolderStore} from '@/store'
import {useTranslations} from 'next-intl'

export interface CreateFolderDialogRef {
  open: (source: string, parentId?: string, data?: any) => void
}

const CreateFolderDialog = forwardRef<CreateFolderDialogRef, {onRefresh?: () => void}>(
  function CreateFolderDialog({onRefresh}, ref) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [form] = Form.useForm()
    const [source, setSource] = useState('')
    const [parentId, setParentId] = useState('')
    const t = useTranslations()

    useImperativeHandle(ref, () => ({
      open: (src: string, parentId?: string) => {
        setSource(src)
        setParentId(parentId || '')
        setOpen(true)
        form.resetFields()
      },
    }))

    const submit = () => {
      form.validateFields().then((vals) => {
        setLoading(true)
        folderApi
          .postFolder(source, {...vals, parent_id: parentId || 'default'})
          .then(() => {
            return useUserStore.getState().profile()
          })
          .then(() => {
            useFolderStore.getState().setCurrentFolder({
              id: parentId || useUserStore.getState().getWorkspaceId(),
            })
            setLoading(false)
            setOpen(false)
            message.success(t('common.createSuccess'))
            onRefresh?.()
          })
          .catch(() => setLoading(false))
      })
    }

    return (
      <Modal
        title={t('components.folder.addFolder')}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={submit}
        confirmLoading={loading}
        okText={t('common.add')}
        cancelText={t('common.cancel')}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label={t('common.name')}
            rules={[{required: true, message: t('components.folder.folderNamePlaceholder')}]}
          >
            <Input maxLength={64} showCount placeholder={t('components.folder.folderNamePlaceholder')} />
          </Form.Item>
          <Form.Item name="desc" label={t('common.desc')}>
            <Input.TextArea maxLength={128} showCount autoSize={{minRows: 3}} />
          </Form.Item>
        </Form>
      </Modal>
    )
  },
)

export default CreateFolderDialog
