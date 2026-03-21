import structlog

logger = structlog.get_logger(__name___)

async def analyze_chunk(chunks : list, document_id: str):
    log = logger.bind(endpoint="analyze_chunk", document_id=document_id)

    lengths = [len(chunk) for chunk in chunks]
    
    stats = {
        "document_id": document_id,
        "chunk_count": len(chunks),
        "mean_length": sum(lengths) / len(lengths),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "short_chunks": sum(1 for l in lengths if l < 100),  # likely noise
        "long_chunks": sum(1 for l in lengths if l > 1500),  # likely too big
    }
    
    log.info("chunk_analysis", **stats)
    return stats
