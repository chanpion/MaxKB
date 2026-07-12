'use client'
import {useEffect, useRef, useState} from 'react'
import {Row, Col, Card, Statistic, Button, Dropdown, Select, DatePicker, Typography, Progress, Empty} from 'antd'
import {
  AppstoreOutlined, DatabaseOutlined, FileTextOutlined, MessageOutlined,
  PlusOutlined, DownOutlined, ArrowRightOutlined,
} from '@ant-design/icons'
import * as echarts from 'echarts'
import {useTranslations} from 'next-intl'
import {homepageApi} from '@/lib/api/home'
import {numberFormat} from '@/utils/common'

export default function HomePage() {
  const t = useTranslations('home')
  const tMenu = useTranslations('menu')
  const [stats, setStats] = useState([
    {title: t('statApplication'), value: 0, icon: <AppstoreOutlined />, color: '#3370FF'},
    {title: t('statKnowledge'), value: 0, icon: <DatabaseOutlined />, color: '#7F3BF5'},
    {title: t('statDocument'), value: 0, icon: <FileTextOutlined />, color: '#2CA91F'},
    {title: t('statConversation'), value: 0, icon: <MessageOutlined />, color: '#FF8800'},
  ])
  const [monitorData, setMonitorData] = useState<any[]>([])
  const [historyDay, setHistoryDay] = useState<number>(7)
  const [dateRange, setDateRange] = useState({start_time: '', end_time: ''})
  const [loading, setLoading] = useState(false)
  const [tokensRanking, setTokensRanking] = useState<any[]>([])
  const [questionRanking, setQuestionRanking] = useState<any[]>([])
  const [userTokensRanking, setUserTokensRanking] = useState<any[]>([])
  const [tokenTotal, setTokenTotal] = useState(0)
  const [chatTotal, setChatTotal] = useState(0)
  const chartRef1 = useRef<HTMLDivElement>(null)
  const chartRef2 = useRef<HTMLDivElement>(null)
  const chartRef3 = useRef<HTMLDivElement>(null)
  const chartRef4 = useRef<HTMLDivElement>(null)

  const beforeDay = (d: number) => {
    const date = new Date()
    date.setDate(date.getDate() - d)
    return date.toISOString().split('T')[0]
  }
  const nowDate = new Date().toISOString().split('T')[0]

  useEffect(() => {
    Promise.allSettled([
      homepageApi.getApplicationAggregation(),
      homepageApi.getKnowledgeAggregation(),
      homepageApi.getToolAggregation(),
      homepageApi.getModelAggregation(),
    ]).then((results) => {
      setStats((prev) => prev.map((s, i) => {
        const r = results[i]
        return {...s, value: r.status === 'fulfilled' ? (r.value as any)?.data?.total ?? 0 : 0}
      }))
    })
    fetchMonitorData(7)
  }, [])

  const fetchMonitorData = (days: number) => {
    const start = beforeDay(days)
    const end = nowDate
    setDateRange({start_time: start, end_time: end})
    setLoading(true)

    homepageApi.getMonitorAggregation({start_time: start, end_time: end}).then((res: any) => {
      setMonitorData(res.data || [])
    }).catch(() => {})

    homepageApi.getChatRecordAggregation({start_time: start, end_time: end}).then((res: any) => {
      setChatTotal(res.data || 0)
    }).catch(() => {})

    homepageApi.getTokensAggregation({start_time: start, end_time: end}).then((res: any) => {
      setTokenTotal(res.data || 0)
    }).catch(() => {})

    homepageApi.getTokensRanking({start_time: start, end_time: end}).then((res: any) => {
      setTokensRanking(res.data?.records || [])
    }).catch(() => {})

    homepageApi.getQuestionsRanking({start_time: start, end_time: end}).then((res: any) => {
      setQuestionRanking(res.data?.records || [])
    }).catch(() => {})

    homepageApi.getUserTokensRanking({start_time: start, end_time: end}).then((res: any) => {
      setUserTokensRanking(res.data?.records || [])
    }).catch(() => {})

    setLoading(false)
  }

  const handleDayChange = (val: number) => {
    setHistoryDay(val)
    fetchMonitorData(val)
  }

  // Render chart
  useEffect(() => {
    if (!monitorData.length) return
    const xData = monitorData.map((d: any) => d.day)

    const charts = [
      {ref: chartRef1, id: 'customerCharts', name: t('activeUsers'), yData: [
        {name: t('activeUsers'), data: monitorData.map((d: any) => d.customer_num || 0)},
        {name: t('newUsers'), data: monitorData.map((d: any) => d.customer_added_count || 0)},
      ]},
      {ref: chartRef2, id: 'chatRecordCharts', name: t('chatCount'), yData: [
        {data: monitorData.map((d: any) => d.chat_record_count || 0)},
      ]},
      {ref: chartRef3, id: 'tokensCharts', name: t('charts.tokensTotal'), yData: [
        {data: monitorData.map((d: any) => d.tokens_num || 0)},
      ]},
      {ref: chartRef4, id: 'starCharts', name: t('charts.userSatisfaction'), yData: [
        {name: t('charts.approval'), data: monitorData.map((d: any) => d.star_num || 0)},
        {name: t('charts.disapproval'), data: monitorData.map((d: any) => d.trample_num || 0)},
      ]},
    ]

    charts.forEach(({ref, name, yData}) => {
      if (!ref.current) return
      const chart = echarts.init(ref.current)
      chart.setOption({
        tooltip: {trigger: 'axis'},
        grid: {left: 40, right: 16, top: 10, bottom: 24},
        xAxis: {type: 'category', data: xData, axisLabel: {fontSize: 11}},
        yAxis: {type: 'value', splitLine: {lineStyle: {color: '#f0f0f0'}}},
        series: yData.map((y: any) => ({
          name: y.name, type: 'line', smooth: true, data: y.data,
          areaStyle: {opacity: 0.15}, lineStyle: {width: 2},
        })),
      })
      const handleResize = () => chart.resize()
      window.addEventListener('resize', handleResize)
      return () => window.removeEventListener('resize', handleResize)
    })
  }, [monitorData, t])

  const quickCreateItems = [
    {key: 'application', label: tMenu('application'), children: [
      {key: 'app-simple', label: '简单智能体'},
      {key: 'app-workflow', label: '工作流智能体'},
      {key: 'app-import', label: '导入应用'},
    ]},
    {key: 'knowledge', label: tMenu('knowledge'), children: [
      {key: 'kn-general', label: '通用知识库'},
      {key: 'kn-web', label: 'Web 站点'},
      {key: 'kn-lark', label: '飞书'},
      {key: 'kn-workflow', label: '工作流'},
      {key: 'kn-import', label: '导入'},
    ]},
    {key: 'tool', label: tMenu('tool'), children: [
      {key: 'tl-tool', label: '工具'},
      {key: 'tl-workflow', label: '工作流'},
      {key: 'tl-skill', label: '技能'},
      {key: 'tl-mcp', label: 'MCP'},
      {key: 'tl-datasource', label: '数据源'},
      {key: 'tl-import', label: '导入'},
    ]},
    {key: 'model', label: tMenu('model')},
  ]

  const dayOptions = [
    {value: 7, label: t('pastDayOptions.past7Days')},
    {value: 30, label: t('pastDayOptions.past30Days')},
    {value: 90, label: t('pastDayOptions.past90Days')},
    {value: 183, label: t('pastDayOptions.past183Days')},
  ]

  const monitorCards = [
    {id: 'customer', name: t('activeUsers'), sum: [monitorData.reduce((a:number,d:any)=>a+(d.customer_num||0),0)]},
    {id: 'chat', name: t('chatCount'), sum: [chatTotal]},
    {id: 'tokens', name: t('charts.tokensTotal'), sum: [tokenTotal]},
  ]

  const rankCard = (title: string, data: any[], total: number, valueKey: string) => (
    <Card style={{borderRadius: 8, minHeight: 360, marginBottom: 16}} styles={{body: {padding: 20}}}>
      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 16}}>
        <Typography.Text strong>{title}</Typography.Text>
        <Button type="link" size="small"><ArrowRightOutlined /></Button>
      </div>
      {data.length === 0 ? <Empty /> : data.map((item: any, i: number) => (
        <div key={i} style={{display: 'flex', alignItems: 'center', marginTop: 16, gap: 12}}>
          <span style={{width: 22, height: 22, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 600, fontSize: 12, border: '2px solid #fff',
            color: ['#c85719','#2b5fd9','#cc710a'][i] || '#8f959e',
            background: ['linear-gradient(180deg,#fee4b1,#feca88)','linear-gradient(180deg,#c6d7ff,#b6d2f7)','linear-gradient(180deg,#ffe1cf,#f4c5af)'][i] || '#f0f0f0',
          }}>{i + 1}</span>
          <div style={{flex: 1, minWidth: 0}}>
            <Typography.Text ellipsis style={{fontSize: 14}}>{item.name || item.asker?.username}</Typography.Text>
            <Typography.Text type="secondary" style={{fontSize: 12, display: 'block'}}>
              {t('chats')} {numberFormat(item.chat_record_count || 0)}
            </Typography.Text>
          </div>
          <div style={{textAlign: 'right', width: 100}}>
            <Progress percent={total ? Number((((item[valueKey]||0) / total) * 100).toFixed(1)) : 0} showInfo={false} size="small" />
            <Typography.Text type="secondary" style={{fontSize: 12}}>{numberFormat(item[valueKey] || 0)}</Typography.Text>
          </div>
        </div>
      ))}
    </Card>
  )

  return (
    <div style={{maxWidth: 1280, margin: '0 auto'}}>
      {/* Stats Overview */}
      <Row gutter={[16, 16]}>
        {stats.map((s) => (
          <Col xs={12} sm={12} md={12} lg={6} xl={6} key={s.title}>
            <Card hoverable styles={{body: {padding: 20}}} style={{borderRadius: 8, cursor: 'pointer'}}>
              <Statistic title={<span style={{fontSize: 14, color: '#646a73'}}>{s.title}</span>}
                value={s.value}
                prefix={<span style={{color: s.color, marginRight: 6, fontSize: 20}}>{s.icon}</span>}
                valueStyle={{fontSize: 32, fontWeight: 500}} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* Quick Create */}
      <Card style={{marginTop: 16, borderRadius: 8}} styles={{body: {padding: '16px 24px'}}}>
        <Typography.Text strong style={{fontSize: 14, marginRight: 24, color: '#1a1a1a'}}>{t('quick')}</Typography.Text>
        {quickCreateItems.map((item) => (
          item.children ? (
            <Dropdown key={item.key} menu={{items: item.children.map((c) => ({key: c.key, label: c.label}))}} trigger={['hover']}>
              <Button type="link" style={{marginRight: 8, padding: '4px 12px'}}>
                <PlusOutlined /> {item.label} <DownOutlined />
              </Button>
            </Dropdown>
          ) : (
            <Button key={item.key} type="link" style={{marginRight: 8, padding: '4px 12px'}}>
              <PlusOutlined /> {item.label}
            </Button>
          )
        ))}
      </Card>

      {/* Statistics & Charts */}
      <Card style={{marginTop: 16, borderRadius: 8}} title={
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <span>{t('monitoringStatistics')}</span>
          <Select value={historyDay} onChange={handleDayChange} style={{width: 140}}
            options={dayOptions.map((d) => ({label: d.label, value: d.value}))} />
        </div>
      }>
        <Row gutter={[16, 16]}>
          {monitorCards.map((m) => (
            <Col xs={12} sm={12} md={12} lg={8} xl={8} key={m.id}>
              <Card style={{borderRadius: 8}} styles={{body: {padding: 12}}}>
                <Typography.Text type="secondary" style={{fontSize: 13}}>{m.name}</Typography.Text>
                <Typography.Title level={3} style={{margin: '4px 0 0'}}>{numberFormat(m.sum[0])}</Typography.Title>
              </Card>
            </Col>
          ))}
        </Row>
        <Row gutter={[16, 16]} style={{marginTop: 8}}>
          <Col xs={24} sm={24} md={12} lg={12} xl={12}>
            <Card style={{borderRadius: 8}}><div ref={chartRef1} style={{height: 280}} /></Card>
          </Col>
          <Col xs={24} sm={24} md={12} lg={12} xl={12}>
            <Card style={{borderRadius: 8}}><div ref={chartRef2} style={{height: 280}} /></Card>
          </Col>
          <Col xs={24} sm={24} md={12} lg={12} xl={12}>
            <Card style={{borderRadius: 8}}><div ref={chartRef3} style={{height: 280}} /></Card>
          </Col>
          <Col xs={24} sm={24} md={12} lg={12} xl={12}>
            <Card style={{borderRadius: 8}}><div ref={chartRef4} style={{height: 280}} /></Card>
          </Col>
        </Row>
      </Card>

      {/* Rankings */}
      <Row gutter={[16, 16]} style={{marginTop: 16}}>
        <Col xs={24} sm={24} md={12} lg={8} xl={8}>
          {rankCard(`Tokens · Top ${tMenu('application')}`, tokensRanking, tokenTotal, 'total_tokens')}
        </Col>
        <Col xs={24} sm={24} md={12} lg={8} xl={8}>
          {rankCard(`${t('chatCount')} · Top ${tMenu('application')}`, questionRanking, chatTotal, 'chat_record_count')}
        </Col>
        <Col xs={24} sm={24} md={12} lg={8} xl={8}>
          {rankCard(`Tokens · Top User`, userTokensRanking, tokenTotal, 'total_tokens')}
        </Col>
      </Row>
    </div>
  )
}
