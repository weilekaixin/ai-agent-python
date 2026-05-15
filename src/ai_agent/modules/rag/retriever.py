from langchain_core.vectorstores import VectorStore


def get_retriever(store: VectorStore):
    """把向量库变成检索器"""
    return store.as_retriever(search_kwargs={"k": 3})
