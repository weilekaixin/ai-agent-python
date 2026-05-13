import os

from sentence_transformers import SentenceTransformer

class Embedder:
    """文本向量化器"""

    def __init__(self):
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # float[][] result = model.encode(texts);
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        # float[][] tmp = model.encode(Lists.newArrayList(text));
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()
