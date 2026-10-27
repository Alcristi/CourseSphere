"""Generate query embeddings for semantic course search."""

from fastembed import TextEmbedding

from database.config import EMBEDDING_CACHE


class EmbeddingService:
    def __init__(self, model=None):
        self.model = model

    def embed(self, texts):
        if self.model is None:
            self.model = TextEmbedding(
                model_name="BAAI/bge-small-en-v1.5",
                cache_dir=str(EMBEDDING_CACHE),
                threads=2,
                local_files_only=True,
            )
        vectors = [vector.tolist() for vector in self.model.embed(texts)]
        if len(vectors) != len(texts) or any(len(vector) != 384 for vector in vectors):
            raise ValueError("Expected one 384-dimensional embedding per rephrasing")
        return vectors
