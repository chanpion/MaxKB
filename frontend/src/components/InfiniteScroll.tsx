'use client'
import React, {useRef} from 'react'
import {Spin} from 'antd'

export interface InfiniteScrollProps {
  size: number
  total: number
  page_size: number
  current_page: number
  loading?: boolean
  onLoad: () => void
  children: React.ReactNode
}

export default function InfiniteScroll({
  size,
  total,
  page_size,
  current_page,
  loading,
  onLoad,
  children,
}: InfiniteScrollProps) {
  const ref = useRef<HTMLDivElement>(null)

  const handleScroll = () => {
    const el = ref.current
    if (!el || loading) return
    if (size >= total) return
    if (el.scrollHeight - el.scrollTop - el.clientHeight < 80) {
      onLoad()
    }
  }

  return (
    <div
      ref={ref}
      onScroll={handleScroll}
      style={{overflowY: 'auto', flex: 1}}
    >
      {children}
      {loading && (
        <div style={{textAlign: 'center', padding: 16}}>
          <Spin />
        </div>
      )}
      {!loading && size >= total && size > 0 && (
        <div style={{textAlign: 'center', color: 'rgba(0,0,0,0.4)', padding: 16}}>没有更多了</div>
      )}
    </div>
  )
}
