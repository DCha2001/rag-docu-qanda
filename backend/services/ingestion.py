from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def parse(file_path: str) -> list:
    return partition(filename=file_path)


def chunk(elements: list) -> list:
    return chunk_by_title(elements)


def embed(chunks: list) -> list[list[float]]:
    texts = [chunk.text for chunk in chunks]
    return _get_model().encode(texts, batch_size=64, show_progress_bar=True).tolist()
