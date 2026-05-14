from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_agent.config.settings import BASE_DIR
from ai_agent.models.constants import MODELS
from ai_agent.models.model import ALL_MINILM_L6_V2


def build_vector_store(file_path: str):
    # 加载文档
    loader = TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)
    # 读取文档内容
    docs = loader.load()
    # 切分文档器 五百字一块，每块向前重叠五十个字
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    # 切分文档
    chunks = splitter.split_documents(docs)
    # 模型存储地址 避免每次启动都加载
    model_path = str(BASE_DIR / MODELS / ALL_MINILM_L6_V2)
    # 加载向量化模型 直接读本地
    embeddings = HuggingFaceEmbeddings(model_name=model_path)
    # 向量化文档
    store = Chroma.from_documents(chunks, embeddings, collection_name="company_docs")
    return store
