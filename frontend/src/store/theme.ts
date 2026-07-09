'use client'
import {create} from 'zustand'
import {THEME_KEY} from '@/lib/constants'

interface ThemeStore {
  isDark: boolean
  toggle: () => void
  setDark: (v: boolean) => void
}

export const useThemeStore = create<ThemeStore>((set, get) => ({
  isDark: typeof window !== 'undefined' && localStorage.getItem(THEME_KEY) === 'dark',
  toggle: () => {
    const next = !get().isDark
    if (typeof window !== 'undefined') localStorage.setItem(THEME_KEY, next ? 'dark' : 'light')
    set({isDark: next})
  },
  setDark: (v) => {
    if (typeof window !== 'undefined') localStorage.setItem(THEME_KEY, v ? 'dark' : 'light')
    set({isDark: v})
  },
}))
