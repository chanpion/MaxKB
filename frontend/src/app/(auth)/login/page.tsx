'use client'
import {useState, useEffect} from 'react'
import {Form, Input, Button, Card, Typography, App, Dropdown, Space} from 'antd'
import {UserOutlined, LockOutlined, SafetyOutlined, CheckOutlined, DownOutlined} from '@ant-design/icons'
import {useRouter} from '@/i18n/navigation'
import {useLoginStore, useUserStore} from '@/store'
import {loginApi} from '@/lib/api/login'
import {useTranslations} from 'next-intl'
import {HOME_PATH} from '@/lib/constants'
import JSEncrypt from 'jsencrypt'

const LANGUAGES = [
  {value: 'zh', label: '简体中文'},
  {value: 'en', label: 'English'},
]
const LANG_MAP: Record<string, string> = {zh: '简体中文', en: 'English'}

export default function LoginPage() {
  const t = useTranslations('login')
  const router = useRouter()
  const {message} = App.useApp()
  const setToken = useLoginStore((s) => s.setToken)
  const setUserInfo = useUserStore((s) => s.setUserInfo)
  const fetchRsa = useUserStore((s) => s.fetchRsa)
  const getRsaKey = useUserStore((s) => s.rsaKey)
  const getLanguage = useUserStore((s) => s.getLanguage)
  const setLanguage = useUserStore((s) => s.setLanguage)
  const [loading, setLoading] = useState(false)
  const [captchaImg, setCaptchaImg] = useState<string>('')
  const currentLang = LANG_MAP[getLanguage()] || '简体中文'

  useEffect(() => {
    fetchRsa().catch(() => {})
  }, [fetchRsa])

  const refreshCaptcha = (username?: string) => {
    loginApi
      .getCaptcha(username)
      .then((res: any) => {
        const img = res?.data?.captcha ?? ''
        setCaptchaImg(img || '')
      })
      .catch(() => setCaptchaImg(''))
  }

  useEffect(() => {
    refreshCaptcha()
  }, [])

  const onUsernameBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    refreshCaptcha(e.target.value || undefined)
  }

  const onFinish = async (values: {username: string; password: string; captcha?: string}) => {
    const rsaKey = getRsaKey || (await fetchRsa())
    if (!rsaKey) {
      message.error(t('rsaFailed') || '公钥获取失败，请刷新页面')
      return
    }
    setLoading(true)
    try {
      const js = new JSEncrypt()
      js.setPublicKey(rsaKey)
      const jsonData = JSON.stringify({
        username: values.username,
        password: values.password,
        captcha: values.captcha || '',
      })
      const encryptedData = js.encrypt(jsonData)
      if (!encryptedData) {
        message.error(t('encryptFailed') || '加密失败，请重试')
        setLoading(false)
        return
      }
      const res: any = await loginApi.login({encryptedData, username: values.username})
      if (res?.data?.token) {
        setToken(res.data.token)
        const profile: any = await loginApi.getUserProfile()
        setUserInfo(profile?.data ?? null)
        message.success(t('success'))
        router.replace(HOME_PATH)
      } else {
        message.error(res?.message || 'login failed')
        refreshCaptcha(values.username)
      }
    } catch (e: any) {
      message.error(e?.message || 'login failed')
      refreshCaptcha(values.username)
    } finally {
      setLoading(false)
    }
  }

  const changeLang = (lang: string) => {
    setLanguage(lang)
    if (typeof window !== 'undefined') {
      window.location.reload()
    }
  }

  const langItems = LANGUAGES.map((lang) => ({
    key: lang.value,
    label: (
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: 140}}>
        <span>{lang.label}</span>
        {lang.value === getLanguage() && <CheckOutlined style={{color: '#1677FF'}} />}
      </div>
    ),
    onClick: () => changeLang(lang.value),
  }))

  return (
    <div style={{display: 'flex', height: '100vh', width: '100%', background: '#f0f2f5'}}>
      {/* Left: branding panel */}
      <div
        style={{
          flex: '0 0 40%',
          maxWidth: '40%',
          background: 'linear-gradient(135deg, #3370FF 0%, #7F3BF5 100%)',
          backgroundImage: `url('data:image/svg+xml,${encodeURIComponent(
            `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 900">
              <rect fill="url(#g)" width="800" height="900"/>
              <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#3370FF"/><stop offset="100%" stop-color="#7F3BF5"/>
              </linearGradient></defs>
              <circle cx="100" cy="200" r="300" fill="rgba(255,255,255,0.06)"/>
              <circle cx="600" cy="700" r="250" fill="rgba(255,255,255,0.05)"/>
              <circle cx="300" cy="600" r="180" fill="rgba(255,255,255,0.04)"/>
              <circle cx="700" cy="300" r="120" fill="rgba(255,255,255,0.03)"/>
            </svg>`,
          )}')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{textAlign: 'center', color: '#fff', zIndex: 1}}>
          <div style={{fontSize: 72, marginBottom: 16}}>🧠</div>
          <div style={{fontSize: 32, fontWeight: 700, letterSpacing: 2}}>MaxKB</div>
          <div style={{fontSize: 16, opacity: 0.85, marginTop: 8}}>{t('desc')}</div>
        </div>
      </div>

      {/* Right: login form */}
      <div style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative'}}>
        {/* Language Switcher */}
        <div style={{position: 'absolute', right: 24, top: 24}}>
          <Dropdown menu={{items: langItems}} trigger={['click']} placement="bottomRight">
            <Button type="text" onClick={(e) => e.preventDefault()}>
              <Space>
                <span>{currentLang}</span>
                <DownOutlined />
              </Space>
            </Button>
          </Dropdown>
        </div>

        <Card
          style={{
            width: 420,
            padding: '8px 12px',
            borderRadius: 16,
            boxShadow: '0 8px 40px rgba(0,0,0,0.08)',
          }}
        >
          <div style={{textAlign: 'center', marginBottom: 24}}>
            <Typography.Title level={3} style={{margin: 0}}>
              {t('title') || '登录 MaxKB'}
            </Typography.Title>
            <Typography.Text type="secondary">{t('desc')}</Typography.Text>
          </div>

          <Form
            layout="vertical"
            onFinish={onFinish}
            initialValues={{username: 'admin', password: 'MaxKB@123..'}}
          >
            <Form.Item name="username" rules={[{required: true, message: t('usernameRequired')}]}>
              <Input prefix={<UserOutlined />} placeholder={t('username')} size="large" onBlur={onUsernameBlur} />
            </Form.Item>
            <Form.Item name="password" rules={[{required: true, message: t('passwordRequired')}]}>
              <Input.Password prefix={<LockOutlined />} placeholder={t('password')} size="large" />
            </Form.Item>
            {captchaImg ? (
              <Form.Item name="captcha" rules={[{required: true, message: t('captchaRequired') || '请输入验证码'}]}>
                <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                  <Input prefix={<SafetyOutlined />} placeholder={t('captcha') || '验证码'} size="large" style={{flex: 1}} />
                  <img
                    src={captchaImg}
                    alt="captcha"
                    height={38}
                    style={{borderRadius: 6, cursor: 'pointer', border: '1px solid #d9d9d9'}}
                    onClick={() => refreshCaptcha()}
                    title={t('refreshCaptcha') || '点击刷新验证码'}
                  />
                </div>
              </Form.Item>
            ) : null}
            <Form.Item>
              <Button type="primary" htmlType="submit" block size="large" loading={loading}
                style={{background: 'linear-gradient(90deg,#1677FF,#0958D9)', border: 'none', fontWeight: 600}}
              >
                {t('submit')}
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </div>
    </div>
  )
}
