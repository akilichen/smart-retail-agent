import os
from dotenv import load_dotenv

load_dotenv()

# 模型配置
LLM_MODEL = "deepseek-v4-flash"
EMBEDDING_MODEL = "BAAI/bge-m3"
LLM_TEMPERATURE = 0

# 如果使用国内服务商，从环境变量读取base_url
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")

# 向量库配置
CHROMA_PERSIST_DIR = "./knowledge/chroma_db"
CHROMA_COLLECTION_PRODUCTS = "products"
CHROMA_COLLECTION_FAQ = "faq"

# Agent配置
MAX_RECURSION_LIMIT = 30