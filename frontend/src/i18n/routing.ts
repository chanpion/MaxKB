import {defineRouting} from 'next-intl/routing'

export const routing = defineRouting({
  // 复用 Vue 端现有语言集合
  locales: ['zh', 'en'],
  defaultLocale: 'zh',
  // 语言不作为路径前缀（/frontend/zh/...），由 cookie/Accept-Language 决定
  localePrefix: 'never',
})
