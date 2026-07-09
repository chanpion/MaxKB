import createMiddleware from 'next-intl/middleware'
import {NextRequest, NextResponse} from 'next/server'
import {routing} from './src/i18n/routing'
import {TOKEN_COOKIE, LOGIN_PATH, HOME_PATH} from './src/lib/constants'

const intlMiddleware = createMiddleware(routing)

export default function middleware(req: NextRequest) {
  const {pathname} = req.nextUrl

  // pathname 包含 basePath，例如 /frontend/login、/frontend/home
  const token = req.cookies.get(TOKEN_COOKIE)?.value
  const isLogin = pathname === LOGIN_PATH
  const isRoot = pathname === '/frontend' || pathname === '/frontend/'

  // 未登录且非登录页 -> 跳转登录
  if (!token && !isLogin && pathname !== '/frontend/404') {
    const url = req.nextUrl.clone()
    url.pathname = LOGIN_PATH
    return NextResponse.redirect(url)
  }
  // 已登录访问登录页 -> 跳转首页
  if (token && isLogin) {
    const url = req.nextUrl.clone()
    url.pathname = HOME_PATH
    return NextResponse.redirect(url)
  }
  // 访问根路径 -> 按登录态分流
  if (isRoot) {
    const url = req.nextUrl.clone()
    url.pathname = token ? HOME_PATH : LOGIN_PATH
    return NextResponse.redirect(url)
  }

  return intlMiddleware(req)
}

// matcher 由 Next 在 basePath 剥离后匹配，因此不能含 /frontend 前缀；
// 排除静态资源、API 与带后缀的文件
export const config = {
  matcher: ['/((?!_next|api|static|favicon|.*\\..*).*)'],
}
