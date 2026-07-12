'use client'
import React, {useState} from 'react'
import {Card} from 'antd'

export interface CardBoxProps {
  title?: React.ReactNode
  description?: React.ReactNode
  icon?: React.ReactNode
  subTitle?: React.ReactNode
  tag?: React.ReactNode
  footer?: React.ReactNode
  mouseEnter?: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  className?: string
  style?: React.CSSProperties
  children?: React.ReactNode
}

const cardBodyStyle: React.CSSProperties = {
  padding: '16px 16px 46px',
  display: 'flex',
  flexDirection: 'column',
  flex: 1,
  boxSizing: 'border-box',
}

const cardHeaderStyle: React.CSSProperties = {
  padding: '12px 16px 0',
  minHeight: 48,
}

export default function CardBox({
  title,
  description,
  icon,
  subTitle,
  tag,
  footer,
  mouseEnter,
  onClick,
  disabled,
  className,
  style,
  children,
}: CardBoxProps) {
  const [hover, setHover] = useState(false)
  return (
    <div
      className={className}
      style={{position: 'relative', height: '100%', ...style}}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onClick={() => {
        if (!disabled && onClick) onClick()
      }}
    >
      <Card
        hoverable={!disabled}
        style={{height: '100%', minHeight: 180, borderRadius: 8}}
        styles={{body: cardBodyStyle, header: cardHeaderStyle}}
        title={
          <div style={{display: 'flex', alignItems: 'flex-start', gap: 8, position: 'relative'}}>
            {icon && <div style={{flexShrink: 0, marginTop: 2}}>{icon}</div>}
            <div style={{flex: 1, minWidth: 0}}>
              <div
                className="ellipsis-1"
                style={{fontSize: 14, fontWeight: 500, lineHeight: '22px', marginBottom: subTitle ? 0 : 0}}
              >
                {title}
              </div>
              {subTitle && <div style={{fontSize: 12, color: 'rgba(0,0,0,0.45)', marginTop: 2}}>{subTitle}</div>}
            </div>
            {tag && <div style={{flexShrink: 0}}>{tag}</div>}
          </div>
        }
      >
        {description && (
          <div
            style={{
              color: 'rgba(0,0,0,0.45)',
              fontSize: 13,
              lineHeight: '22px',
              display: '-webkit-box',
              WebkitBoxOrient: 'vertical',
              WebkitLineClamp: 2,
              overflow: 'hidden',
              minHeight: 44,
            }}
          >
            {description}
          </div>
        )}
        {children}
      </Card>
      {footer && (
        <div
          style={{
            position: 'absolute',
            bottom: 8,
            left: 16,
            right: 16,
            height: 30,
            display: 'flex',
            alignItems: 'center',
          }}
        >
          {footer}
        </div>
      )}
      {mouseEnter && hover && (
        <div style={{position: 'absolute', top: 8, right: 8, zIndex: 10}} onClick={(e) => e.stopPropagation()}>
          {mouseEnter}
        </div>
      )}
    </div>
  )
}
