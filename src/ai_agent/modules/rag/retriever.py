from ai_agent.modules.rag.embedder import Embedder


def similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class Retriever:
    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.chunks: list[dict] = []

    def add(self, texts: list[str]) -> None:
        vectors = self.embedder.embed_documents(texts)
        for text, vector in zip(texts, vectors):
            self.chunks.append({"text": text, "vector": vector})

    def query(self, text: str, top_k: int = 3) -> list[str]:
        query_vec = self.embedder.embed_query(text)

        scored = []
        for chunk in self.chunks:
            score = similarity(query_vec, chunk["vector"])
            scored.append((score, chunk["text"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored[:top_k]]
