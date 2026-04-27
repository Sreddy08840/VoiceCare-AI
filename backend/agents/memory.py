from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import Dict, Any, List
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = "patient_memories"

qdrant_available = False
client = None
_memory_store: Dict[str, List[str]] = {}

try:
    if QDRANT_URL:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=10)
    else:
        # Fallback to local
        client = QdrantClient(host="localhost", port=6333, timeout=3)

    collections = client.get_collections().collections
    if not any(c.name == COLLECTION_NAME for c in collections):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
        )
        print(f"✅ Created Qdrant collection: {COLLECTION_NAME}")
    qdrant_available = True
    print(f"✅ Qdrant connected at: {QDRANT_URL or 'localhost:6333'}")
except Exception as e:
    print(f"⚠️  Qdrant not available ({e}). Using in-memory fallback.")

class MemoryAgent:
    def __init__(self):
        if not qdrant_available:
            global _memory_store
            if '_memory_store' not in globals():
                _memory_store = {}

    async def store_memory(self, phone_number: str, text: str, memory_type: str) -> Dict[str, Any]:
        """Store a preference or session summary."""
        if not qdrant_available:
            _memory_store.setdefault(phone_number, []).append(text)
            return {"status": "success", "message": "Memory stored (fallback)."}
        try:
            vector = [0.0] * 1536
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={"phone_number": phone_number, "text": text, "type": memory_type}
                    )
                ]
            )
            return {"status": "success", "message": "Memory stored."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def recall_memory(self, phone_number: str, query: str = "") -> Dict[str, Any]:
        """Retrieve past context for a patient."""
        if not qdrant_available:
            memories = _memory_store.get(phone_number, [])
            return {"status": "success", "memories": memories}
        try:
            vector = [0.0] * 1536
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                query_filter=models.Filter(
                    must=[models.FieldCondition(
                        key="phone_number",
                        match=models.MatchValue(value=phone_number)
                    )]
                ),
                limit=5
            )
            memories = [res.payload["text"] for res in results if res.payload]
            return {"status": "success", "memories": memories}
        except Exception as e:
            return {"status": "error", "message": str(e)}

