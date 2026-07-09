'use client'
import React from 'react'

export interface CommonListProps {
  data: Array<any>
  valueKey?: string
  activeKey?: any
  onSelect?: (item: any) => void
  children: (row: any) => React.ReactNode
  loading?: boolean
}

export default function CommonList({
  data,
  valueKey = 'provider',
  activeKey,
  onSelect,
  children,
  loading,
}: CommonListProps) {
  return (
    <ul className="common-list" style={{listStyle: 'none', margin: 0, padding: 0}}>
      {data.map((row) => {
        const active = activeKey !== undefined && row[valueKey] === activeKey
        return (
          <li
            key={row[valueKey]}
            onClick={() => onSelect?.(row)}
            className={active ? 'active' : ''}
            style={{
              padding: '8px 8px',
              cursor: 'pointer',
              borderRadius: 6,
              marginBottom: 2,
              color: active ? '#1677ff' : 'inherit',
              fontWeight: active ? 500 : 400,
              background: active ? 'rgba(22,119,255,0.1)' : 'transparent',
            }}
          >
            {children(row)}
          </li>
        )
      })}
    </ul>
  )
}
