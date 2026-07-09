'use client'
import {create} from 'zustand'

interface KnowledgeStore {
  knowledgeList: Array<any>
  setKnowledgeList: (list: Array<any>) => void
}

export const useKnowledgeStore = create<KnowledgeStore>((set) => ({
  knowledgeList: [],
  setKnowledgeList: (list) => set({knowledgeList: list}),
}))
