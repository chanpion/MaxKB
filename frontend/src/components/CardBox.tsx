'use client'
import React, {useState} from 'react'
import {Card} from 'antd'
import {useThemeStore} from '@/store/theme'

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
  /** 强调色（hex），用于图标徽章底色与顶部色条，不传则使用默认中性样式 */
  accent?: string
  children?: React.ReactNode
}

function hexToRgba(hex: string, alpha: number) {
  const m = hex.replace('#', '')
  const r = parseInt(m.substring(0, 2), 16)
  const g = parseInt(m.substring(2, 4), 16)
  const b = parseInt(m.substring(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

const cardBodyStyle: React.CSSProperties = {
  padding: '14px 16px 46px',
  display: 'flex',
  flexDirection: 'column',
  flex: 1,
  boxSizing: 'border-box',
}

const cardHeaderStyle: React.CSSProperties = {
  padding: '14px 16px 0',
  minHeight: 48,
}

const DEFAULT_ACCENT = '#1677ff'

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
  accent,
  children,
}: CardBoxProps) {
  const [hover, setHover] = useState(false)
  const isDark = useThemeStore((s) => s.isDark)
  const accentColor = accent || DEFAULT_ACCENT
  const iconBg = hexToRgba(accentColor, isDark ? 0.22 : 0.12)
  const cardBg = isDark ? '#1f1f1f' : '#ffffff'
  const borderColor = isDark ? '#303030' : '#eef0f2'
  const hoverBorder = hover && !disabled ? accentColor : borderColor
  const shadow = hover && !disabled
    ? `0 8px 24px ${hexToRgba(accentColor, isDark ? 0.28 : 0.16)}`
    : isDark
      ? '0 1px 2px rgba(0,0,0,0.4)'
      : '0 1px 2px rgba(0,0,0,0.04)'

  return (
    <div
      className={className}
      style={{position: 'relative', height: '100%', transition: 'transform 0.2s ease', ...(hover && !disabled ? {transform: 'translateY(-2px)'} : {}), ...style}}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onClick={() => {
        if (!disabled && onClick) onClick()
      }}
    >
      <Card
        hoverable={false}
        style={{
          height: '100%',
          minHeight: 196,
          borderRadius: 12,
          background: cardBg,
          border: `1px solid ${hoverBorder}`,
          boxShadow: shadow,
          overflow: 'hidden',
          transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
        }}
        styles={{body: cardBodyStyle, header: cardHeaderStyle}}
        title={
          <div style={{display: 'flex', alignItems: 'flex-start', gap: 10, position: 'relative'}}>
            {icon && (
              <div
                style={{
                  flexShrink: 0,
                  width: 38,
                  height: 38,
                  borderRadius: 10,
                  background: iconBg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginTop: 2,
                  transition: 'background 0.2s ease',
                }}
              >
                {icon}
              </div>
            )}
            <div style={{flex: 1, minWidth: 0}}>
              <div
                className="ellipsis-1"
                style={{fontSize: 14, fontWeight: 600, lineHeight: '22px', color: isDark ? 'rgba(255,255,255,0.92)' : '#1f1f1f'}}
              >
                {title}
              </div>
              {subTitle && (
                <div style={{fontSize: 12, color: isDark ? 'rgba(255,255,255,0.45)' : 'rgba(0,0,0,0.45)', marginTop: 2}}>
                  {subTitle}
                </div>
              )}
            </div>
            {tag && <div style={{flexShrink: 0}}>{tag}</div>}
          </div>
        }
      >
        {description && (
          <div
            style={{
              color: isDark ? 'rgba(255,255,255,0.45)' : 'rgba(0,0,0,0.45)',
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
            borderTop: `1px solid ${borderColor}`,
            paddingTop: 6,
          }}
        >
          {footer}
        </div>
      )}
      {mouseEnter && hover && (
        <div style={{position: 'absolute', top: 10, right: 10, zIndex: 10}} onClick={(e) => e.stopPropagation()}>
          {mouseEnter}
        </div>
      )}
    </div>
  )
}
