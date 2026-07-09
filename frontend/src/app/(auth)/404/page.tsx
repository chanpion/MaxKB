'use client'
import {Result, Button} from 'antd'
import {useRouter} from '@/i18n/navigation'
import {useLoginStore} from '@/store'
import {HOME_PATH, LOGIN_PATH} from '@/lib/constants'

export default function NotFoundPage() {
  const router = useRouter()
  const token = useLoginStore((s) => s.token)
  const target = token ? HOME_PATH : LOGIN_PATH
  return (
    <div style={{minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <Result
        status="404"
        title="404"
        subTitle="页面不存在 / Page not found"
        extra={
          <Button type="primary" onClick={() => router.replace(target)}>
            返回 / Back
          </Button>
        }
      />
    </div>
  )
}
