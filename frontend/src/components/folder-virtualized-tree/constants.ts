export const SORT_TYPES = {
  CREATE_TIME_ASC: 'createTime-asc',
  CREATE_TIME_DESC: 'createTime-desc',
  NAME_ASC: 'name-asc',
  NAME_DESC: 'name-desc',
  CUSTOM: 'custom',
} as const

export type SortType = (typeof SORT_TYPES)[keyof typeof SORT_TYPES]

export const SORT_MENU_CONFIG = [
  {
    title: 'components.folder.timeSort',
    items: [
      {value: SORT_TYPES.CREATE_TIME_DESC, labelKey: 'components.folder.descTime'},
      {value: SORT_TYPES.CREATE_TIME_ASC, labelKey: 'components.folder.ascTime'},
    ],
  },
  {
    title: 'components.folder.nameSort',
    items: [
      {value: SORT_TYPES.NAME_ASC, labelKey: 'components.folder.ascName'},
      {value: SORT_TYPES.NAME_DESC, labelKey: 'components.folder.descName'},
    ],
  },
  {
    title: 'components.folder.customSort',
    items: [{value: SORT_TYPES.CUSTOM, labelKey: 'components.folder.custom'}],
  },
]
