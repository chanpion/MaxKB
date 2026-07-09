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
      style={{position: 'relative', ...style}}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onClick={() => {
        if (!disabled && onClick) onClick()
      }}
    >
      <Card
        hoverable={!disabled}
        style={{height: '100%'}}
        title={
          <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
            {icon}
            <span className="ellipsis-1">{title}</span>
          </div>
        }
        extra={tag}
      >
        {description && <div style={{color: 'rgba(0,0,0,0.45)', marginBottom: 8}}>{description}</div>}
        {subTitle && <div style={{marginBottom: 8}}>{subTitle}</div>}
        {children}
        {footer && <div style={{marginTop: 12}}>{footer}</div>}
      </Card>
      {mouseEnter && hover && (
        <div style={{position: 'absolute', top: 8, right: 8, zIndex: 10}} onClick={(e) => e.stopPropagation()}>
          {mouseEnter}
        </div>
      )}
    </div>
  )
}
