'use client'
import {Row, Col, Card, Statistic, Typography, Button} from 'antd'
import {
  AppstoreOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  MessageOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import {useUserStore} from '@/store'
import {useTranslations} from 'next-intl'

export default function HomePage() {
  const tHome = useTranslations('home')
  const tMenu = useTranslations('menu')
  const userInfo = useUserStore((s) => s.userInfo)

  const stats = [
    {title: tHome('statApplication'), value: 0, icon: <AppstoreOutlined />, color: '#1677FF'},
    {title: tHome('statKnowledge'), value: 0, icon: <DatabaseOutlined />, color: '#52C41A'},
    {title: tHome('statDocument'), value: 0, icon: <FileTextOutlined />, color: '#FAAD14'},
    {title: tHome('statConversation'), value: 0, icon: <MessageOutlined />, color: '#722ED1'},
  ]

  return (
    <div>
      <Typography.Title level={4} style={{marginTop: 0}}>
        {tHome('welcome', {name: userInfo?.nickname || userInfo?.username || 'User'})}
      </Typography.Title>
      <Typography.Text type="secondary">{tHome('subtitle')}</Typography.Text>

      <Row gutter={16} style={{marginTop: 24}}>
        {stats.map((s) => (
          <Col span={6} key={s.title}>
            <Card hoverable style={{borderRadius: 12}}>
              <Statistic
                title={s.title}
                value={s.value}
                prefix={<span style={{color: s.color, marginRight: 6}}>{s.icon}</span>}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Card style={{marginTop: 24, borderRadius: 12}} title={tHome('quick')}>
        <Button type="primary" icon={<PlusOutlined />} style={{marginRight: 12}}>
          {tMenu('application')}
        </Button>
        <Button icon={<PlusOutlined />} style={{marginRight: 12}}>
          {tMenu('knowledge')}
        </Button>
        <Button icon={<PlusOutlined />}>{tMenu('model')}</Button>
      </Card>
    </div>
  )
}
