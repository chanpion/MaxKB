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
    const [editData, setEditData] = useState<any>(null)
    const t = useTranslations()

    useImperativeHandle(ref, () => ({
      open: (src: string, parentId?: string, data?: any) => {
        setSource(src)
        setParentId(parentId || '')
        setEditData(data || null)
        setOpen(true)
        form.resetFields()
        if (data) {
          form.setFieldsValue({name: data.name, desc: data.desc || ''})
        }
      },
    }))

    const submit = () => {
      form.validateFields().then((vals) => {
        setLoading(true)
        const apiCall = editData
          ? folderApi.putFolder(editData.id, source, {...vals, parent_id: parentId || 'default'})
          : folderApi.postFolder(source, {...vals, parent_id: parentId || 'default'})
        apiCall
          .then(() => {
            return useUserStore.getState().profile()
          })
          .then(() => {
            useFolderStore.getState().setCurrentFolder({
              id: parentId || useUserStore.getState().getWorkspaceId(),
            })
            setLoading(false)
            setOpen(false)
            message.success(t(editData ? 'common.editSuccess' : 'common.createSuccess'))
            onRefresh?.()
          })
          .catch(() => setLoading(false))
      })
    }

    const title = editData ? t('components.folder.editFolder') : t('components.folder.addFolder')

    return (
      <Modal
        title={title}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={submit}
        confirmLoading={loading}
        okText={t('common.add')}
        cancelText={t('common.cancel')}
        destroyOnHidden
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
