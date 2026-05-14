from pymilvus import connections

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Milvus
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_agent.config.settings import settings
from ai_agent.models.model import ALL_MINILM_L6_V2, COMPANY_DOCS


def build_vector_store(file_path: str):
    # 第一步 连接到 Milvus
    connections.connect(host=settings.milvus_host, port=settings.milvus_port)
    # 第二步 读文档
    loader = TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)
    docs = loader.load()
    # 第三步 切块
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    # 第四步 向量化模型
    embeddings = HuggingFaceEmbeddings(model_name=ALL_MINILM_L6_V2)
    # 第五步 存入 Milvus
    store = Milvus.from_documents(
        chunks,
        embeddings,
        collection_name=COMPANY_DOCS,
        drop_old=False,
    )
    return store
