from langchain_chroma import Chroma


def get_retriever(store: Chroma):
    """把向量库变成检索器"""
    return store.as_retriever(search_kwargs={"k": 3})
