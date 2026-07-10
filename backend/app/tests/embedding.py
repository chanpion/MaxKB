import os

from sentence_transformers import SentenceTransformer

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 加载模型（首次使用会自动下载，也可指定本地路径）
# model = SentenceTransformer('all-MiniLM-L6-v2')
model_path = '/Users/logenswolf/.cache/modelscope/models/BAAI--bge-m3/snapshots/master'
model = SentenceTransformer(model_path)

# 要向量化的文本
sentences = ["你好，世界！", "这是一段测试文本。"]

# 生成向量
embeddings = model.encode(sentences)

print(f"生成了 {len(embeddings)} 个向量，每个向量维度为 {embeddings[0].shape[0]}")
