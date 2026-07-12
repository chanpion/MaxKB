import createNextIntlPlugin from 'next-intl/plugin'

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts')

/** @type {import('next').NextConfig} */
const nextConfig = {
  // 应用挂载在站点根路径（不再使用 /frontend 前缀）
  basePath: '',
  output: 'standalone',
  reactStrictMode: true,
  async rewrites() {
    // 注意 basePath:false —— axios 直发 /admin/api（不含应用前缀），
    // 禁止 Rewrite 自动叠加 basePath
    const raw = process.env.API_TARGET ?? 'http://127.0.0.1:8080'
    // 移除尾部斜杠，避免拼接路径时出现双斜杠
    const target = raw.replace(/\/+$/, '')

    // next-intl localePrefix:'never' 会在内部将 /foo 重写为 /zh/foo，
    // 这些 fallback 规则将带语言前缀的路径映射回实际页面路由
    const localeFallbacks = ['zh', 'en'].flatMap((locale) => [
      { source: `/${locale}/:path*`, destination: '/:path*' },
      { source: `/${locale}`, destination: '/' },
    ])

    return [
      // API / 静态资源代理放最后，避免吞掉页面路由
      ...localeFallbacks,
      { source: '/admin/api/:path*', basePath: false, destination: `${target}/admin/api/:path*` },
      { source: '/chat/api/:path*', basePath: false, destination: `${target}/chat/api/:path*` },
      { source: '/oss/:path*', basePath: false, destination: `${target}/oss/:path*` },
      { source: '/doc/:path*', basePath: false, destination: `${target}/doc/:path*` },
      { source: '/schema/:path*', basePath: false, destination: `${target}/schema/:path*` },
      { source: '/static/:path*', basePath: false, destination: `${target}/static/:path*` },
    ]
  },
}

export default withNextIntl(nextConfig)
