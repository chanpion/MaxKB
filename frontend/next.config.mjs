import createNextIntlPlugin from 'next-intl/plugin'

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts')

/** @type {import('next').NextConfig} */
const nextConfig = {
  // 新模块统一挂载前缀，与现有 /admin、/chat 路径隔离，原 ui/ 零改动
  basePath: '/frontend',
  output: 'standalone',
  reactStrictMode: true,
  async rewrites() {
    // 注意 basePath:false —— axios 直发 /admin/api（不含 /frontend 前缀），
    // 禁止 Rewrite 自动叠加 basePath，否则实际匹配会变成 /frontend/admin/api
    const target = process.env.API_TARGET ?? 'http://127.0.0.1:8080'
    return [
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
