'use client'
import React, {useEffect, useState} from 'react'
import {Breadcrumb, Row, Col, Input, Select, Button, Card, Typography, Empty, Spin, Tag, Dropdown, Modal, Form, message, Space} from 'antd'
import {HomeOutlined, AppstoreOutlined, PlusOutlined, MoreOutlined, EditOutlined, DeleteOutlined, CopyOutlined} from '@ant-design/icons'
import FolderVirtualizedTree from '@/components/folder-virtualized-tree/FolderVirtualizedTree'
import {SourceTypeEnum} from '@/enums/common'
import {useFolderStore, useUserStore} from '@/store'
import {useTranslations} from 'next-intl'
import {useRouter} from '@/i18n/navigation'
import {applicationApi} from '@/lib/api/application'

export default function ApplicationPage() {
  const t = useTranslations('menu')
  const router = useRouter()
  const folder = useFolderStore()
  const user = useUserStore()
  const [list, setList] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const loadList = () => {
    setLoading(true)
    const params: any = {folder_id: folder.currentFolder?.id || user.getWorkspaceId()}
    if (search) params.name = search
    applicationApi.getList(params).then((res: any) => {
      setList(res.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadList() }, [folder.currentFolder?.id])

  const handleCreate = () => {
    form.validateFields().then((values) => {
      applicationApi.postCreate(values).then(() => {
        message.success('创建成功'); setCreateOpen(false); form.resetFields(); loadList()
      }).catch(() => {})
    })
  }

  const handleDelete = (id: string, name: string) => {
    Modal.confirm({title: '确认删除', content: `确认删除智能体「${name}」？`,
      onOk: () => applicationApi.delDelete(id).then(() => { message.success('删除成功'); loadList() }),
    })
  }

  return (
    <div style={{display: 'flex', gap: 16, height: 'calc(100vh - 56px - 48px)'}}>
      <div style={{width: 240, overflow: 'auto', background: '#fff', borderRadius: 8, padding: 8, flexShrink: 0, display: 'flex', flexDirection: 'column'}}>
        <div style={{padding: '8px 8px 4px', fontWeight: 500, fontSize: 14}}>{t('application')}</div>
        <FolderVirtualizedTree source={SourceTypeEnum.APPLICATION} />
      </div>
      <div style={{flex: 1, overflow: 'auto', background: '#fff', borderRadius: 8, padding: 16}}>
        <Breadcrumb style={{marginBottom: 16}} items={[
          {title: <><HomeOutlined /> {t('home')}</>},
          {title: <><AppstoreOutlined /> {t('application')}</>},
        ]} />
        <div style={{display: 'flex', alignItems: 'center', marginBottom: 16, gap: 8}}>
          <Input value={search} onChange={(e) => setSearch(e.target.value)} onPressEnter={loadList}
            placeholder="搜索智能体" style={{width: 240}} allowClear />
          <Button type="primary" icon={<PlusOutlined />} style={{marginLeft: 'auto'}} onClick={() => setCreateOpen(true)}>
            创建智能体
          </Button>
        </div>
        {loading ? <div style={{textAlign: 'center', padding: 60}}><Spin /></div>
        : list.length === 0 ? <Empty description="暂无智能体" />
        : <Row gutter={[16, 16]}>
            {list.map((item: any) => (
              <Col key={item.id} xs={24} sm={12} md={12} lg={8} xl={6}>
                <Card hoverable style={{borderRadius: 8}}
                  onClick={() => router.push(`/application/${item.id}/overview`)}
                  styles={{body: {padding: 20, minHeight: 166}}}>
                  <div style={{display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12}}>
                    <div style={{
                      width: 34, height: 34, borderRadius: 8, flexShrink: 0,
                      background: 'linear-gradient(135deg, rgba(51,112,255,0.14), rgba(19,194,194,0.12))',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <AppstoreOutlined style={{fontSize: 17, color: '#3370FF'}} />
                    </div>
                    <div style={{flex: 1, minWidth: 0}}>
                      <Typography.Text ellipsis strong style={{fontSize: 15}}>{item.name}</Typography.Text>
                      <div style={{marginTop: 2}}>
                        <Tag color={item.model_name ? 'blue' : 'default'} style={{marginRight: 0}}>
                          {item.model_name || '未配置'}
                        </Tag>
                      </div>
                    </div>
                  </div>
                  <Typography.Paragraph ellipsis={{rows: 2}} type="secondary"
                    style={{marginBottom: 8, fontSize: 13, minHeight: 40, lineHeight: '20px'}}>
                    {item.desc || '暂无描述'}
                  </Typography.Paragraph>
                  <Typography.Text type="secondary" style={{fontSize: 12}}>
                    创建人：{item.user_name || '—'}
                  </Typography.Text>
                </Card>
              </Col>
            ))}
          </Row>}
      </div>
      <Modal title="创建智能体" open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); form.resetFields() }}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{required: true, message: '请输入名称'}]}>
            <Input placeholder="请输入智能体名称" />
          </Form.Item>
          <Form.Item name="desc" label="描述">
            <Input.TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
