'use client'
import {Result, Button} from 'antd'
import {useRouter} from '@/i18n/navigation'
import {useLoginStore} from '@/store'
import {HOME_PATH, LOGIN_PATH} from '@/lib/constants'
import {useTranslations} from 'next-intl'

export default function NotFoundPage() {
  const t = useTranslations('common')
  const router = useRouter()
  const token = useLoginStore((s) => s.token)
  const target = token ? HOME_PATH : LOGIN_PATH
  return (
    <div style={{minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column'}}>
      <img src="/404.png" alt="404" style={{width: 250, marginBottom: 24}} />
      <Result
        status="404"
        title="404"
        subTitle={t('notFound') || '页面不存在'}
        extra={
          <Button type="primary" onClick={() => router.replace(target)}>
            {t('back') || '返回'}
          </Button>
        }
      />
    </div>
  )
}
