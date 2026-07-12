'use client'
import React, {forwardRef, useImperativeHandle, useState} from 'react'
import {Modal, message} from 'antd'
import FolderVirtualizedTree from './FolderVirtualizedTree'
import knowledgeApi from '@/lib/api/knowledge/knowledge'
import folderApi from '@/lib/api/workspace/folder'
import {SourceTypeEnum} from '@/enums/common'
import {useTranslations} from 'next-intl'

export interface MoveToDialogRef {
  open: (data: any, isFolder?: boolean) => void
}

const MoveToDialog = forwardRef<MoveToDialogRef, {onRefresh?: (row?: any) => void; source?: SourceTypeEnum}>(
  function MoveToDialog({onRefresh, source = SourceTypeEnum.KNOWLEDGE}, ref) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [selectFolderId, setSelectFolderId] = useState('')
    const [detail, setDetail] = useState<any>(null)
    const [isBatch, setIsBatch] = useState(false)
    const [isFolder, setIsFolder] = useState(false)
    const t = useTranslations()

    useImperativeHandle(ref, () => ({
      open: (data: any, folder?: boolean) => {
        setDetail(data)
        setIsBatch(!!data?.id_list)
        setIsFolder(!!folder)
        setSelectFolderId('')
        setOpen(true)
      },
    }))

    const submit = () => {
      if (!selectFolderId) {
        message.error(t('components.folder.requiredMessage'))
        return
      }
      setLoading(true)
      const finish = () => {
        setLoading(false)
        setOpen(false)
        message.success(t('common.saveSuccess'))
        onRefresh?.(detail)
      }

      if (isFolder) {
        const body = {...detail, parent_id: selectFolderId}
        folderApi.putFolder(detail.id, detail.folder_type || source, body).then(finish).catch(() => setLoading(false))
        return
      }
      const obj = {...detail, folder_id: selectFolderId}
      if (isBatch) {
        knowledgeApi.putMulMoveKnowledge(obj).then(finish).catch(() => setLoading(false))
      } else if (detail?.type === 2) {
        knowledgeApi.putLarkKnowledge(detail.id, obj).then(finish).catch(() => setLoading(false))
      } else {
        knowledgeApi.putKnowledge(detail.id, obj).then(finish).catch(() => setLoading(false))
      }
    }

    return (
      <Modal
        title={t('common.moveTo')}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={submit}
        confirmLoading={loading}
        okText={t('common.confirm')}
        cancelText={t('common.cancel')}
        okButtonProps={{disabled: !selectFolderId || (isFolder && detail?.id === selectFolderId)}}
        destroyOnHidden
      >
        <FolderVirtualizedTree source={source} onSelect={(node) => setSelectFolderId(node.id)} />
      </Modal>
    )
  },
)

export default MoveToDialog
