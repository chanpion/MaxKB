'use client'
import {create} from 'zustand'
import {LOCALE_KEY} from '@/lib/constants'
import {loginApi} from '@/lib/api/login'

export interface UserInfo {
  id?: string
  username?: string
  nickname?: string
  email?: string
  role?: string[]
  permissions?: string[]
  language?: string
  workspace_list?: Array<{id: string; name: string}>
  [key: string]: any
}

interface UserStore {
  userInfo: UserInfo | null
  workspace_id: string
  setUserInfo: (u: UserInfo | null) => void
  getLanguage: () => string
  setLanguage: (lang: string) => void
  setWorkspaceId: (id: string) => void
  getWorkspaceId: () => string
  isPE: () => boolean
  isEE: () => boolean
  profile: () => Promise<any>
}

export const useUserStore = create<UserStore>((set, get) => ({
  userInfo: null,
  workspace_id: '',
  setUserInfo: (u) => set({userInfo: u}),
  getLanguage: () => {
    if (typeof window === 'undefined') return 'zh'
    return localStorage.getItem(LOCALE_KEY) || 'zh'
  },
  setLanguage: (lang) => {
    if (typeof window !== 'undefined') localStorage.setItem(LOCALE_KEY, lang)
    set({userInfo: {...(get().userInfo as UserInfo)}})
  },
  setWorkspaceId: (id) => {
    if (typeof window !== 'undefined') localStorage.setItem('workspace_id', id)
    set({workspace_id: id})
  },
  getWorkspaceId: () => {
    const id = get().workspace_id || (typeof window !== 'undefined' ? localStorage.getItem('workspace_id') || '' : '')
    if (!id || id === 'default') {
      const fallback = 'default'
      set({workspace_id: fallback})
      return fallback
    }
    set({workspace_id: id})
    return id
  },
  isPE: () => (get().userInfo?.role || []).includes('workspace_manage'),
  isEE: () => false,
  profile: () => {
    return loginApi.getUserProfile().then((ok: any) => {
      const data = ok.data
      set({userInfo: data})
      const list =
        data?.workspace_list && data.workspace_list.length > 0
          ? data.workspace_list
          : [{id: 'default', name: 'default'}]
      const current = get().getWorkspaceId()
      if (!current || !list.some((w: any) => w.id === current)) {
        get().setWorkspaceId(list[0].id)
      }
      return ok
    })
  },
}))
