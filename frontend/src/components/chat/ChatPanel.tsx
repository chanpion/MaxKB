'use client'

import {useCallback, useEffect, useRef, useState} from 'react'
import {Avatar, Button, Card, Empty, Input, List, Spin, Tag, Tooltip, Typography, message} from 'antd'
import {DeleteOutlined, LikeOutlined, DislikeOutlined, SendOutlined, RobotOutlined, UserOutlined, ClearOutlined} from '@ant-design/icons'
import {
  openChat,
  getProfile,
  listConversations,
  listRecords,
  vote,
  deleteConversation,
  clearHistory,
  sendMessage,
  type ChatProfile,
  type Conversation,
  type ChatRecord,
} from '../../lib/api/chat'

const {Text, Paragraph} = Typography

export interface ChatPanelProps {
  accessToken: string
  /** 公开嵌入模式：隐藏历史侧栏，自动开新会话 */
  embedded?: boolean
  /** 是否展示引用来源 */
  showSource?: boolean
  className?: string
}

interface Bubble {
  role: 'user' | 'ai'
  text: string
  recordId?: string
  chatId?: string
  source?: any[]
  voteStatus?: number
}

export default function ChatPanel({accessToken, embedded = false, showSource, className}: ChatPanelProps) {
  const [profile, setProfile] = useState<ChatProfile | null>(null)
  const [bubbles, setBubbles] = useState<Bubble[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeChat, setActiveChat] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({top: scrollRef.current.scrollHeight, behavior: 'smooth'})
    })
  }, [])

  const loadProfile = useCallback(async () => {
    try {
      const p = await getProfile(accessToken)
      setProfile(p)
    } catch {
      /* 静默 */
    }
  }, [accessToken])

  const loadConversations = useCallback(async () => {
    try {
      const res = await listConversations(accessToken, 1, 30)
      setConversations(res.list || [])
    } catch {
      /* 静默 */
    }
  }, [accessToken])

  const openNewChat = useCallback(async () => {
    try {
      const {id} = await openChat(accessToken)
      setActiveChat(id)
      setBubbles([])
      return id
    } catch (e: any) {
      message.error(e?.message || '创建会话失败')
      return null
    }
  }, [accessToken])

  useEffect(() => {
    loadProfile()
    if (!embedded) loadConversations()
    else openNewChat()
  }, [loadProfile, loadConversations, openNewChat, embedded])

  const switchConversation = useCallback(
    async (chatId: string) => {
      setActiveChat(chatId)
      setLoading(true)
      try {
        const res = await listRecords(chatId)
        const list = res.list || []
        const next: Bubble[] = []
        list.forEach((r: ChatRecord) => {
          next.push({role: 'user', text: r.message || ''})
          next.push({
            role: 'ai',
            text: r.answer_text || r.answer || '',
            recordId: r.id,
            chatId: r.chat_id,
            source: r.source,
            voteStatus: r.vote_status,
          })
        })
        setBubbles(next)
      } catch {
        /* 静默 */
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  const doSend = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return
    let chatId = activeChat
    if (!chatId) chatId = await openNewChat()
    if (!chatId) return

    setInput('')
    setBubbles((b) => [...b, {role: 'user', text}, {role: 'ai', text: '', chatId}])
    scrollToBottom()
    setLoading(true)

    let acc = ''
    let source: any[] = []
    let recordId: string | undefined
    abortRef.current = sendMessage(chatId, text, {
      onChunk: (t) => {
        acc += t
        setBubbles((b) => {
          const copy = [...b]
          const last = copy[copy.length - 1]
          if (last?.role === 'ai') copy[copy.length - 1] = {...last, text: acc, source}
          return copy
        })
        scrollToBottom()
      },
      onNodeEnd: (node) => {
        if (Array.isArray(node?.source) && node.source.length) source = node.source
      },
      onAnswer: (full) => {
        acc = full || acc
      },
      onError: (msg) => message.error(msg),
      onDone: () => {
        setLoading(false)
        if (!embedded) loadConversations()
      },
    })
  }, [input, loading, activeChat, openNewChat, scrollToBottom, embedded, loadConversations])

  const doVote = useCallback(async (b: Bubble, status: number) => {
    if (!b.recordId || !b.chatId) return
    try {
      await vote(b.chatId, b.recordId, status)
      setBubbles((bs) => bs.map((x) => (x === b ? {...x, voteStatus: status} : x)))
    } catch (e: any) {
      message.error(e?.message || '操作失败')
    }
  }, [])

  const handleDelete = useCallback(
    async (chatId: string) => {
      try {
        await deleteConversation(chatId)
        setConversations((c) => c.filter((x) => x.id !== chatId))
        if (activeChat === chatId) {
          setActiveChat(null)
          setBubbles([])
        }
      } catch (e: any) {
        message.error(e?.message || '删除失败')
      }
    },
    [activeChat],
  )

  const handleClear = useCallback(async () => {
    try {
      await clearHistory(accessToken)
      setConversations([])
      setActiveChat(null)
      setBubbles([])
    } catch (e: any) {
      message.error(e?.message || '清空失败')
    }
  }, [accessToken])

  const renderSource = (src?: any[]) => {
    if (!src || !src.length) return null
    const show = showSource ?? profile?.show_source ?? true
    if (!show) return null
    return (
      <div className="mt-2 rounded-md bg-gray-50 p-2 text-xs">
        <Text type="secondary">引用来源</Text>
        {src.map((s, i) => (
          <div key={i} className="mt-1 border-l-2 border-blue-300 pl-2 text-gray-600">
            <div className="font-medium text-gray-700">{s.title || s.name || `片段 ${i + 1}`}</div>
            <Paragraph className="mb-0 text-gray-500" ellipsis={{rows: 2}}>
              {s.content || s.text || ''}
            </Paragraph>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={`flex h-full ${className || ''}`}>
      {!embedded && (
        <div className="flex w-64 flex-col border-r border-gray-100 bg-gray-50/60">
          <div className="flex items-center justify-between px-3 py-2">
            <Button type="text" size="small" icon={<ClearOutlined />} onClick={handleClear}>
              清空
            </Button>
            <Button type="primary" size="small" onClick={() => openNewChat()}>
              新对话
            </Button>
          </div>
          <div className="flex-1 overflow-auto px-2">
            {conversations.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无历史" className="mt-10" />
            ) : (
              <List
                dataSource={conversations}
                renderItem={(c) => (
                  <List.Item
                    className={`cursor-pointer rounded-md px-2 py-1.5 hover:bg-white ${activeChat === c.id ? 'bg-white' : ''}`}
                    onClick={() => switchConversation(c.id)}
                    actions={[
                      <Tooltip key="del" title="删除">
                        <DeleteOutlined
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(c.id)
                          }}
                        />
                      </Tooltip>,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<Avatar size="small" icon={<RobotOutlined />} />}
                      title={<span className="truncate text-sm">{c.name || '对话'}</span>}
                      description={<span className="text-xs text-gray-400">{c.update_time}</span>}
                    />
                  </List.Item>
                )}
              />
            )}
          </div>
        </div>
      )}

      <div className="flex flex-1 flex-col bg-white">
        <div className="flex items-center gap-2 border-b border-gray-100 px-4 py-2">
          {profile?.icon && <Avatar src={profile.icon} />}
          <span className="font-medium">{profile?.name || '智能对话'}</span>
          {profile?.type && <Tag color="blue">{profile.type}</Tag>}
        </div>

        <div ref={scrollRef} className="flex-1 space-y-4 overflow-auto px-4 py-4">
          {bubbles.length === 0 && (
            <div className="mt-16 text-center">
              <Empty description={profile?.prologue || '开始你的提问吧'} />
            </div>
          )}
          {bubbles.map((b, i) =>
            b.role === 'user' ? (
              <div key={i} className="flex justify-end">
                <div className="flex max-w-[80%] items-start gap-2">
                  <div className="rounded-lg bg-blue-500 px-3 py-2 text-sm text-white">{b.text}</div>
                  <Avatar icon={<UserOutlined />} className="bg-blue-400" />
                </div>
              </div>
            ) : (
              <div key={i} className="flex justify-start">
                <div className="flex max-w-[80%] items-start gap-2">
                  <Avatar icon={<RobotOutlined />} className="bg-green-500" />
                  <div className="rounded-lg bg-gray-100 px-3 py-2 text-sm text-gray-800">
                    {b.text || (loading ? <Spin size="small" /> : null)}
                    {renderSource(b.source)}
                    {b.recordId && !loading && (
                      <div className="mt-2 flex gap-2 text-gray-400">
                        <Tooltip title="赞">
                          <LikeOutlined
                            className={b.voteStatus === 1 ? 'text-blue-500' : ''}
                            onClick={() => doVote(b, 1)}
                          />
                        </Tooltip>
                        <Tooltip title="踩">
                          <DislikeOutlined
                            className={b.voteStatus === -1 ? 'text-red-500' : ''}
                            onClick={() => doVote(b, -1)}
                          />
                        </Tooltip>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ),
          )}
        </div>

        <div className="border-t border-gray-100 p-3">
          <div className="flex items-end gap-2">
            <Input.TextArea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="输入你的问题，回车发送"
              autoSize={{minRows: 1, maxRows: 4}}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault()
                  doSend()
                }
              }}
            />
            <Button type="primary" icon={<SendOutlined />} loading={loading} onClick={doSend}>
              发送
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
