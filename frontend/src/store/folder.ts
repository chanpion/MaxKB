'use client'
import {create} from 'zustand'

interface FolderStore {
  currentFolder: any
  setCurrentFolder: (folder: any) => void
}

export const useFolderStore = create<FolderStore>((set) => ({
  currentFolder: {},
  setCurrentFolder: (folder) => set({currentFolder: folder}),
}))
