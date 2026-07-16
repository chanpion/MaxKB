'use client'
import {create} from 'zustand'
import {LOCALE_KEY} from '@/lib/constants'
import {get as httpGet} from '@/lib/request'
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
  rsaKey: string | null
  fetchRsa: () => Promise<string | null>
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
  rsaKey: null,
  // RSA 公钥由后端公开端点 /system/profile 的 data.rsa 提供（无需登录）。
  // 注意：/user/profile 需要已登录 token 且不返回 rsa，不能用于登录前取公钥。
  fetchRsa: () => {
    return httpGet('/system/profile').then((res: any) => {
      const key = res?.data?.rsa ?? res?.rsa ?? null
      set({rsaKey: key})
      return key
    })
  },
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
  // 纯取值，禁止在 getter 内调用 set（会引发重渲染死循环）。
  // 写状态统一交给 setWorkspaceId / profile。
  getWorkspaceId: () => {
    const id = get().workspace_id || (typeof window !== 'undefined' ? localStorage.getItem('workspace_id') || '' : '')
    return id || 'default'
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
