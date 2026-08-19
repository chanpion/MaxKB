// 左侧 Sidebar 静态菜单配置，对齐旧 ui（Vue3）router/modules/*.ts 的 meta 结构。
// NavItem.icon 为字符串图标名，由 Sidebar 组件映射到 @ant-design/icons 组件。

export interface NavItem {
  key: string
  label: string
  icon?: string
  children?: NavItem[]
}

// 应用详情页二级菜单（扁平，无子级）
export const appDetailMenu: NavItem[] = [
  {key: 'overview', label: '概览', icon: 'appstore'},
  {key: 'setting', label: '设置', icon: 'setting'},
  {key: 'access', label: '访问', icon: 'key'},
  {key: 'chat', label: '体验', icon: 'message'},
  {key: 'chat-log', label: '聊天日志', icon: 'file-text'},
]

// 知识库详情页二级菜单（扁平，无子级）
export const knowledgeDetailMenu: NavItem[] = [
  {key: 'document', label: '文档', icon: 'file-text'},
  {key: 'workflow', label: '工作流', icon: 'node'},
  {key: 'problem', label: '问题', icon: 'question'},
  {key: 'termbase', label: '术语库', icon: 'book'},
  {key: 'hit-test', label: '命中测试', icon: 'experiment'},
  {key: 'chat-user', label: '对话用户', icon: 'user'},
  {key: 'setting', label: '设置', icon: 'setting'},
]

// 系统管理二级菜单（含子级分组，对齐旧 ui system.ts）
export const systemMenu: NavItem[] = [
  {key: '/system/user', label: '用户管理', icon: 'user'},
  {key: '/system/workspace', label: '工作区管理', icon: 'team'},
  {key: '/system/role', label: '角色管理', icon: 'safety'},
  {
    key: '/system/resource-management',
    label: '资源管理',
    icon: 'database',
    children: [
      {key: '/system/resource-management/application', label: '应用'},
      {key: '/system/resource-management/knowledge', label: '知识库'},
      {key: '/system/resource-management/tool', label: '工具'},
      {key: '/system/resource-management/model', label: '模型'},
    ],
  },
  {
    key: '/system/shared',
    label: '共享资源',
    icon: 'share',
    children: [
      {key: '/system/shared/knowledge', label: '知识库'},
      {key: '/system/shared/tool', label: '工具'},
      {key: '/system/shared/model', label: '模型'},
    ],
  },
  {
    key: '/system/chat',
    label: '对话用户',
    icon: 'message',
    children: [
      {key: '/system/chat/chat-user', label: '对话用户'},
      {key: '/system/chat/group', label: '用户组'},
      {key: '/system/chat/authentication', label: '认证管理'},
    ],
  },
  {
    key: '/system/setting',
    label: '系统设置',
    icon: 'setting',
    children: [
      {key: '/system/setting/theme', label: '主题设置'},
      {key: '/system/setting/auth', label: '登录认证'},
      {key: '/system/setting/email', label: '邮件设置'},
    ],
  },
  {key: '/system/log', label: '操作日志', icon: 'file-text'},
]
