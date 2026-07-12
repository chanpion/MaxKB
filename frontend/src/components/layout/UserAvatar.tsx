'use client'
import {useState} from 'react'
import {Avatar, Dropdown, Divider} from 'antd'
import {
  UserOutlined,
  LogoutOutlined,
  KeyOutlined,
  LockOutlined,
  InfoCircleOutlined,
  GlobalOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import {useTranslations} from 'next-intl'
import {useRouter} from '@/i18n/navigation'
import {useLoginStore, useUserStore} from '@/store'
import {LOGIN_PATH} from '@/lib/constants'
import AboutDialog from './AboutDialog'

const LANGUAGES = [
  {value: 'zh', label: '简体中文'},
  {value: 'en', label: 'English'},
]

export default function UserAvatar() {
  const t = useTranslations('header')
  const router = useRouter()
  const userInfo = useUserStore((s) => s.userInfo)
  const setLanguage = useUserStore((s) => s.setLanguage)
  const getLanguage = useUserStore((s) => s.getLanguage)
  const clearToken = useLoginStore((s) => s.clearToken)
  const [aboutOpen, setAboutOpen] = useState(false)

  const onLogout = () => {
    clearToken()
    router.replace(LOGIN_PATH)
  }

  const items = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: t('profile'),
    },
    {
      key: 'system',
      icon: <SettingOutlined />,
      label: '系统管理',
      children: [
        {key: 'system-user', label: '用户管理', onClick: () => router.push('/system/user')},
        {key: 'system-role', label: '角色管理', onClick: () => router.push('/system/role')},
        {key: 'system-workspace', label: '工作区管理', onClick: () => router.push('/system/workspace')},
        {key: 'system-setting', label: '系统设置', onClick: () => router.push('/system/setting/theme')},
      ],
    },
    {
      key: 'reset-pwd',
      icon: <LockOutlined />,
      label: '修改密码',
      disabled: true,
    },
    {
      key: 'api-key',
      icon: <KeyOutlined />,
      label: 'API Key',
      disabled: true,
    },
    {type: 'divider' as const},
    {
      key: 'language',
      icon: <GlobalOutlined />,
      label: '语言 / Language',
      children: LANGUAGES.map((lang) => ({
        key: `lang-${lang.value}`,
        label: lang.label,
        onClick: () => {
          setLanguage(lang.value)
          if (typeof window !== 'undefined') {
            window.location.reload()
          }
        },
      })),
    },
    {
      key: 'about',
      icon: <InfoCircleOutlined />,
      label: '关于',
      onClick: () => setAboutOpen(true),
    },
    {type: 'divider' as const},
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: t('logout'),
      danger: true,
      onClick: onLogout,
    },
  ]

  return (
    <>
      <Dropdown menu={{items}} placement="bottomRight">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            cursor: 'pointer',
            padding: '4px 8px',
            borderRadius: 6,
          }}
        >
          <Avatar
            style={{
              background: 'linear-gradient(270deg, #9258f7 0%, #3370ff 100%)',
              verticalAlign: 'middle',
            }}
            size={32}
          >
            {userInfo?.nickname?.[0] || userInfo?.username?.[0] || 'U'}
          </Avatar>
          <div style={{lineHeight: 1.3}}>
            <div style={{fontSize: 14, fontWeight: 500}}>
              {userInfo?.nickname || userInfo?.username || 'User'}
            </div>
            <div style={{fontSize: 12, color: '#8f959e'}}>
              {userInfo?.role?.includes('workspace_manage') ? '管理员' : '用户'}
            </div>
          </div>
        </div>
      </Dropdown>
      <AboutDialog open={aboutOpen} onClose={() => setAboutOpen(false)} />
    </>
  )
}
