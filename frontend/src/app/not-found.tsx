import Image from 'next/image'
import Link from 'next/link'

export default function NotFound() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      background: '#f5f6f7',
    }}>
      <img src="/404.png" alt="404" width={250} style={{marginBottom: 24}} />
      <h1 style={{fontSize: 72, fontWeight: 700, color: '#d9d9d9', margin: 0}}>404</h1>
      <p style={{color: '#8f959e', marginTop: 8, fontSize: 14}}>页面不存在 / Page not found</p>
      <Link href="/" style={{marginTop: 24, color: '#1677FF'}}>返回 / Back</Link>
    </div>
  )
}
