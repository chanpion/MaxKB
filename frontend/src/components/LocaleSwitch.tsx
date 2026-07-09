'use client'
import {Dropdown, Button} from 'antd'
import {GlobalOutlined} from '@ant-design/icons'
import {useLocale} from 'next-intl'
import {useRouter} from '@/i18n/navigation'
import {useUserStore} from '@/store'
import {LOCALE_KEY} from '@/lib/constants'

export default function LocaleSwitch() {
  const locale = useLocale()
  const setLanguage = useUserStore((s) => s.setLanguage)
  const router = useRouter()

  const change = (lang: string) => {
    // 写入 cookie 供 next-intl middleware 识别，并重渲染当前页面
    document.cookie = `NEXT_LOCALE=${lang}; path=/; max-age=${60 * 60 * 24 * 365}`
    localStorage.setItem(LOCALE_KEY, lang)
    setLanguage(lang)
    router.refresh()
  }

  return (
    <Dropdown
      menu={{
        items: [
          {key: 'zh', label: '简体中文', disabled: locale === 'zh'},
          {key: 'en', label: 'English', disabled: locale === 'en'},
        ],
        onClick: ({key}) => change(key),
      }}
    >
      <Button type="text" icon={<GlobalOutlined />}>
        {locale === 'zh' ? '简体中文' : 'English'}
      </Button>
    </Dropdown>
  )
}
