'use client'
import {useState} from 'react'
import {Modal, Typography} from 'antd'

const {Text} = Typography

export default function AboutDialog({open, onClose}: {open: boolean; onClose: () => void}) {
  return (
    <Modal title="关于 MaxKB" open={open} onCancel={onClose} footer={null} width={400} centered>
      <div style={{textAlign: 'center', padding: '16px 0'}}>
        <div style={{fontSize: 48, marginBottom: 12}}>🧠</div>
        <Text strong style={{fontSize: 18}}>
          MaxKB
        </Text>
        <br />
        <Text type="secondary">企业级智能体平台</Text>
        <div style={{marginTop: 16, color: '#8f959e', fontSize: 13, lineHeight: 2}}>
          <div>版本：v1.0.0</div>
          <div>Copyright © {new Date().getFullYear()} MaxKB</div>
          <div>All rights reserved.</div>
        </div>
      </div>
    </Modal>
  )
}
