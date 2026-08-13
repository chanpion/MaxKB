'use client'
import React, {useState} from 'react'
import {Button, Drawer, Input, Spin, Typography, message, Tag} from 'antd'
import {PlayCircleOutlined} from '@ant-design/icons'
import {toolApi} from '@/lib/api/tool/tool'

export default function ToolDebugDrawer({
  open,
  tool,
  onClose,
}: {
  open: boolean
  tool?: any | null
  onClose: () => void
}) {
  const [input, setInput] = useState('{}')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<string>('')

  const run = async () => {
    if (!tool?.id) return
    let payload: any = {}
    try {
      payload = input.trim() ? JSON.parse(input) : {}
    } catch {
      message.error('输入不是合法 JSON')
      return
    }
    setRunning(true)
    setResult('')
    try {
      const res: any = await toolApi.debugTool(tool.id, payload)
      setResult(JSON.stringify(res?.data ?? res, null, 2))
    } catch (e: any) {
      setResult(JSON.stringify(e?.data ?? e?.message ?? e, null, 2))
    } finally {
      setRunning(false)
    }
  }

  return (
    <Drawer title={`调试工具：${tool?.name || ''}`} width={560} open={open} onClose={onClose}>
      <Typography.Text type="secondary" style={{fontSize: 12}}>
        输入参数（JSON 格式，当前后端以连接/可用性测试返回）
      </Typography.Text>
      <Input.TextArea
        rows={8}
        style={{fontFamily: 'monospace', fontSize: 13, marginTop: 6}}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={'{\n  "param1": "value"\n}'}
      />
      <div style={{margin: '12px 0'}}>
        <Button type="primary" icon={<PlayCircleOutlined />} loading={running} onClick={run}>
          测试运行
        </Button>
        {tool?.tool_type && (
          <Tag color="blue" style={{marginLeft: 8}}>
            {tool.tool_type}
          </Tag>
        )}
      </div>
      <Typography.Text type="secondary" style={{fontSize: 12}}>
        返回结果
      </Typography.Text>
      <div
        style={{
          marginTop: 6,
          minHeight: 120,
          borderRadius: 8,
          border: '1px solid #f0f0f0',
          padding: 12,
          background: '#fafafa',
          fontFamily: 'monospace',
          fontSize: 13,
          whiteSpace: 'pre-wrap',
          overflow: 'auto',
        }}
      >
        {running ? <Spin /> : result || '—'}
      </div>
    </Drawer>
  )
}
