'use client'
import {create} from 'zustand'
import {loadSharedApi} from '@/lib/api/shared-api'
import type {Provider} from '@/lib/api/type/model'

interface ModelStore {
  providerList: Array<Provider>
  setProviderList: (list: Array<Provider>) => void
  asyncGetProvider: () => Promise<any>
}

export const useModelStore = create<ModelStore>((set) => ({
  providerList: [],
  setProviderList: (list) => set({providerList: list}),
  asyncGetProvider: () => {
    return loadSharedApi({type: 'provider'}).getProvider().then((ok: any) => {
      set({providerList: ok.data || []})
      return ok
    })
  },
}))
