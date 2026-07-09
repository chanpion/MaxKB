'use client'
import React from 'react'
import {Spin} from 'antd'

// 模型下载进度占位动画（对齐 Vue DownloadLoading）
export default function DownloadLoading({label = '下载中'}: {label?: string}) {
  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8}}>
      <Spin size="large" />
      <span style={{fontSize: 13, color: 'rgba(0,0,0,0.55)'}}>{label}...</span>
    </div>
  )
}
