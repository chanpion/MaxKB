'use client'
import {create} from 'zustand'

interface CommonStore {
  collapsed: boolean
  toggleCollapsed: () => void
}

export const useCommonStore = create<CommonStore>((set, get) => ({
  collapsed: false,
  toggleCollapsed: () => set({collapsed: !get().collapsed}),
}))
