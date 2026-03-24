import threading

from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from sentence_transformers import SentenceTransformer

from utils.cancellation import IngestionCancelledError

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


def embed(chunks: list, cancel: threading.Event | None = None) -> list[list[float]]:
    model = _get_model()
    texts = [c.text for c in chunks]
    batch_size = 64
    vectors = []

    #reimplemented batching logic to check for cancelation between batches.
    for i in range(0, len(texts), batch_size):
        if cancel and cancel.is_set():
            raise IngestionCancelledError("Embedding cancelled — document was deleted")

        batch = texts[i : i + batch_size]
        batch_vectors = model.encode(batch, show_progress_bar=False).tolist()
        vectors.extend(batch_vectors)

    return vectors
