import {cookies} from 'next/headers'
import {redirect} from 'next/navigation'
import {TOKEN_COOKIE} from '@/lib/constants'

// 兜底：当中间件未生效时，保证根路径 / 不会 404，按登录态分流。
// redirect() 会自动叠加 basePath（当前为空），故此处用无前缀路径。
export default function RootPage() {
  const token = cookies().get(TOKEN_COOKIE)?.value
  redirect(token ? '/home' : '/login')
}
