import threading
import os

import voyageai
import unstructured_client
from unstructured_client.models import operations, shared

from utils.cancellation import IngestionCancelledError

_voyage_client: voyageai.Client | None = None
_unstructured_client: unstructured_client.UnstructuredClient | None = None


def _get_voyage_client() -> voyageai.Client:
    global _voyage_client
    if _voyage_client is None:
        _voyage_client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    return _voyage_client


def _get_unstructured_client() -> unstructured_client.UnstructuredClient:
    global _unstructured_client
    if _unstructured_client is None:
        _unstructured_client = unstructured_client.UnstructuredClient(
            api_key_auth=os.environ["UNSTRUCTURED_API_KEY"],
            server_url="https://api.unstructuredapp.io",
        )
    return _unstructured_client


class _Element:
    """Wraps Unstructured API response dicts into objects embed() can consume."""
    def __init__(self, d: dict):
        self.text = d.get("text", "")
        self.category = d.get("type", "NarrativeText")
        self.metadata = d.get("metadata", {})


def parse(file_path: str) -> list: #includes chunking via unstructured's chunking_strategy param
    """Parse and chunk a document via the Unstructured API. Returns chunked elements."""
    client = _get_unstructured_client()
    with open(file_path, "rb") as f:
        data = f.read()

    req = operations.PartitionRequest(
        partition_parameters=shared.PartitionParameters(
            files=shared.Files(content=data, file_name=os.path.basename(file_path)),
            strategy=shared.Strategy.FAST,
            languages=["eng"],
            chunking_strategy="by_title",
            max_characters=1500,
            new_after_n_chars=1000,
            combine_under_n_chars=200,
        )
    )
    response = client.general.partition(request=req)
    return [_Element(d) for d in response.elements]


def embed(chunks: list, cancel: threading.Event | None = None) -> list[list[float]]:
    client = _get_voyage_client()
    texts = [c.text for c in chunks]
    batch_size = 128
    vectors = []

    for i in range(0, len(texts), batch_size):
        if cancel and cancel.is_set():
            raise IngestionCancelledError("Embedding cancelled — document was deleted")

        batch = texts[i : i + batch_size]
        result = client.embed(batch, model="voyage-4-lite", input_type="document")
        vectors.extend(result.embeddings)

    return vectors
