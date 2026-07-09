// 模型类型映射，value 为后端 model_type，文本走 i18n 键
export const modelType: Record<string, string> = {
  EMBEDDING: 'views.model.modelType.EMBEDDING',
  LLM: 'views.model.modelType.LLM',
  STT: 'views.model.modelType.STT',
  TTS: 'views.model.modelType.TTS',
  IMAGE: 'views.model.modelType.IMAGE',
  TTI: 'views.model.modelType.TTI',
  RERANKER: 'views.model.modelType.RERANKER',
  TTV: 'views.model.modelType.TTV',
  ITV: 'views.model.modelType.ITV',
}

export const modelTypeList = [
  {text: 'views.model.modelType.LLM', value: 'LLM'},
  {text: 'views.model.modelType.EMBEDDING', value: 'EMBEDDING'},
  {text: 'views.model.modelType.RERANKER', value: 'RERANKER'},
  {text: 'views.model.modelType.STT', value: 'STT'},
  {text: 'views.model.modelType.TTS', value: 'TTS'},
  {text: 'views.model.modelType.IMAGE', value: 'IMAGE'},
  {text: 'views.model.modelType.TTI', value: 'TTI'},
  {text: 'views.model.modelType.ITV', value: 'ITV'},
  {text: 'views.model.modelType.TTV', value: 'TTV'},
]
