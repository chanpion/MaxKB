'use client'
import {Button, Tooltip} from 'antd'
import {GithubOutlined, LinkOutlined} from '@ant-design/icons'

export default function HeaderActions() {
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 4}}>
      <Tooltip title="查看价格">
        <Button
          type="default"
          shape="round"
          size="small"
          icon={<span style={{fontSize: 14}}>⚡</span>}
          onClick={() => window.open('https://maxkb.cn/pricing.html', '_blank')}
          style={{fontSize: 13}}
        >
          升级
        </Button>
      </Tooltip>
      <Tooltip title="GitHub">
        <Button
          type="text"
          icon={<GithubOutlined />}
          onClick={() => window.open('https://github.com/1Panel-dev/MaxKB', '_blank')}
        />
      </Tooltip>
      <Tooltip title="用户手册">
        <Button
          type="text"
          icon={<LinkOutlined />}
          onClick={() => window.open('https://maxkb.cn/docs', '_blank')}
        />
      </Tooltip>
    </div>
  )
}
