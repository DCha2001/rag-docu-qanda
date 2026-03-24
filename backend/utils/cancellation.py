import threading

# Maps document_id (str) → threading.Event
# When the event is set, the ingestion pipeline for that document will stop
# at the next batch boundary.
_registry: dict[str, threading.Event] = {}


class IngestionCancelledError(Exception):
    """Raised inside a pipeline thread when its cancellation event is set."""
    pass


def register(doc_id: str) -> threading.Event:
    """Create and store a cancellation event for a document. Call this
    before starting the ingestion pipeline."""
    event = threading.Event()
    _registry[doc_id] = event
    return event


def signal(doc_id: str) -> bool:
    """Set the cancellation event for a document. Returns True if the
    document was actively being processed, False if it wasn't registered
    (e.g. already finished)."""
    event = _registry.get(doc_id)
    if event:
        event.set()
        return True
    return False


def deregister(doc_id: str) -> None:
    """Remove the event from the registry. Call this in a finally block
    after the pipeline finishes (successfully or not)."""
    _registry.pop(doc_id, None)
