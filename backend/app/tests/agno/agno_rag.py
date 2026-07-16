from agno.agent import Agent
from agno.knowledge.embedder.sentence_transformer import SentenceTransformerEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb
from agno.models.openai import OpenAIChat

# 1. 初始化本地嵌入器
model_path = "/Users/logenswolf/.cache/modelscope/models/BAAI--bge-m3/snapshots/master"

embedder = SentenceTransformerEmbedder(id=model_path)

# 2. 配置 Chroma 向量数据库
vector_db = ChromaDb(
    collection="my_docs",
    path="tmp/chromadb",
    persistent_client=True,
    embedder=embedder,
)

# 3. 创建知识库并加载文档
knowledge = Knowledge(vector_db=vector_db)
knowledge.insert(text_content="这是一段示例文本。")

# 4. 创建 RAG Agent
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    knowledge=knowledge,
    search_knowledge=True,
    instructions=["基于文档内容回答问题。"],
    markdown=True,
)

agent.print_response("文档中说了什么？")