import type {Metadata} from 'next'
import {NextIntlClientProvider} from 'next-intl'
import {getMessages} from 'next-intl/server'
import {AntdRegistry} from '@ant-design/nextjs-registry'
import Providers from '@/components/Providers'

export const metadata: Metadata = {
  title: 'MaxKB 管理控制台',
  description: 'MaxKB React Admin Console',
}

export default async function RootLayout({children}: {children: React.ReactNode}) {
  const messages = await getMessages()
  return (
    <html lang="zh" suppressHydrationWarning>
      <body style={{margin: 0}}>
        <AntdRegistry>
          <NextIntlClientProvider messages={messages}>
            <Providers>{children}</Providers>
          </NextIntlClientProvider>
        </AntdRegistry>
      </body>
    </html>
  )
}
