'use client'
import {create} from 'zustand'

interface FolderStore {
  currentFolder: any
  setCurrentFolder: (folder: any) => void
  refreshCounter: number
  incrementRefresh: () => void
}

export const useFolderStore = create<FolderStore>((set) => ({
  currentFolder: {},
  setCurrentFolder: (folder) => set({currentFolder: folder}),
  refreshCounter: 0,
  incrementRefresh: () => set((state) => ({refreshCounter: state.refreshCounter + 1})),
}))
