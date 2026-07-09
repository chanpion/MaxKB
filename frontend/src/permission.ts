// 权限桩：model / knowledge 在 workspace 模式下的各方法恒返回 true。
// 对齐 Vue 端 permissionMap['model'|'knowledge'][apiType]，仅实现 workspace 分支。
type PermissionFn = (id?: string) => boolean

function trueFn(): PermissionFn {
  return () => true
}

const modelPermission = {
  create: trueFn(),
  delete: trueFn(),
  modify: trueFn(),
  edit: trueFn(),
  auth: trueFn(),
  relate_map: trueFn(),
  paramSetting: trueFn(),
  sync: trueFn(),
  vector: trueFn(),
  generate: trueFn(),
  export: trueFn(),
  folderRead: trueFn(),
  batchDelete: trueFn(),
  batchMove: trueFn(),
  is_share: () => true,
}

const knowledgePermission = {
  ...modelPermission,
  modify: trueFn(),
  sync: trueFn(),
  vector: trueFn(),
  generate: trueFn(),
  export: trueFn(),
  auth: trueFn(),
  relate_map: trueFn(),
  edit: trueFn(),
  delete: trueFn(),
  batchDelete: trueFn(),
  batchMove: trueFn(),
  folderRead: trueFn(),
}

const permissionMap = {
  model: {
    workspace: modelPermission,
    systemShare: modelPermission,
    systemManage: modelPermission,
  },
  knowledge: {
    workspace: knowledgePermission,
    systemShare: knowledgePermission,
    systemManage: knowledgePermission,
  },
}

export default permissionMap
