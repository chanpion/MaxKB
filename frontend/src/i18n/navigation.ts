import {createNavigation} from 'next-intl/navigation'
import {routing} from './routing'

// 与 next-intl 路由联动的导航 API，自动携带 locale 上下文
export const {Link, redirect, usePathname, useRouter, getPathname} = createNavigation(routing)
