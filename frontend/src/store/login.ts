'use client'
import {create} from 'zustand'
import {TOKEN_KEY, TOKEN_COOKIE} from '@/lib/constants'

// token 同步：localStorage 供 axios 读取（与 Vue 一致），cookie 供 middleware 读取
function syncCookie(token: string | null) {
  if (typeof document === 'undefined') return
  if (token) {
    document.cookie = `${TOKEN_COOKIE}=${token}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`
  } else {
    document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0`
  }
}

interface LoginStore {
  token: string | null
  getToken: () => string | null
  setToken: (t: string | null) => void
  clearToken: () => void
}

export const useLoginStore = create<LoginStore>((set) => ({
  token: typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null,
  getToken: () => (typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null),
  setToken: (t) => {
    if (t) {
      localStorage.setItem(TOKEN_KEY, t)
      syncCookie(t)
    } else {
      localStorage.removeItem(TOKEN_KEY)
      syncCookie(null)
    }
    set({token: t})
  },
  clearToken: () => {
    localStorage.removeItem(TOKEN_KEY)
    syncCookie(null)
    set({token: null})
  },
}))
