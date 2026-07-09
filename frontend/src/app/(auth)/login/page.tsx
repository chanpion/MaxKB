'use client'
import {useState} from 'react'
import {Form, Input, Button, Card, Typography, App} from 'antd'
import {UserOutlined, LockOutlined} from '@ant-design/icons'
import {useRouter} from '@/i18n/navigation'
import {useLoginStore, useUserStore} from '@/store'
import {loginApi} from '@/lib/api/login'
import {useTranslations} from 'next-intl'
import LocaleSwitch from '@/components/LocaleSwitch'
import ThemeToggle from '@/components/ThemeToggle'
import {HOME_PATH} from '@/lib/constants'

export default function LoginPage() {
  const t = useTranslations('login')
  const router = useRouter()
  const {message} = App.useApp()
  const setToken = useLoginStore((s) => s.setToken)
  const setUserInfo = useUserStore((s) => s.setUserInfo)
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: {username: string; password: string}) => {
    setLoading(true)
    try {
      const res: any = await loginApi.login(values)
      if (res?.data?.token) {
        setToken(res.data.token)
        const profile: any = await loginApi.getUserProfile()
        setUserInfo(profile?.data ?? null)
        message.success(t('success'))
        router.replace(HOME_PATH)
      } else {
        message.error(res?.message || 'login failed')
      }
    } catch (e: any) {
      message.error(e?.message || 'login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg,#1677FF 0%,#0958D9 50%,#061178 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          borderRadius: '50%',
          filter: 'blur(80px)',
          opacity: 0.5,
          background: 'rgba(255,255,255,0.25)',
          width: 420,
          height: 420,
          top: -120,
          right: -80,
        }}
      />
      <div
        style={{
          position: 'absolute',
          borderRadius: '50%',
          filter: 'blur(80px)',
          opacity: 0.4,
          background: 'rgba(255,255,255,0.18)',
          width: 360,
          height: 360,
          bottom: -120,
          left: -60,
        }}
      />
      <div style={{position: 'absolute', top: 20, right: 24, display: 'flex', gap: 8}}>
        <LocaleSwitch />
        <ThemeToggle />
      </div>
      <Card
        style={{
          width: 400,
          padding: '8px 12px',
          borderRadius: 16,
          boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
          backdropFilter: 'blur(10px)',
          background: 'rgba(255,255,255,0.95)',
        }}
      >
        <div style={{textAlign: 'center', marginBottom: 24}}>
          <div style={{fontSize: 40, marginBottom: 8}}>🧠</div>
          <Typography.Title level={3} style={{margin: 0}}>
            MaxKB
          </Typography.Title>
          <Typography.Text type="secondary">{t('desc')}</Typography.Text>
        </div>
        <Form
          layout="vertical"
          onFinish={onFinish}
          initialValues={{username: 'admin', password: 'MaxKB@123..'}}
        >
          <Form.Item name="username" rules={[{required: true, message: t('usernameRequired')}]}>
            <Input prefix={<UserOutlined />} placeholder={t('username')} size="large" />
          </Form.Item>
          <Form.Item name="password" rules={[{required: true, message: t('passwordRequired')}]}>
            <Input.Password prefix={<LockOutlined />} placeholder={t('password')} size="large" />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              size="large"
              loading={loading}
              style={{
                background: 'linear-gradient(90deg,#1677FF,#0958D9)',
                border: 'none',
                fontWeight: 600,
              }}
            >
              {t('submit')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
