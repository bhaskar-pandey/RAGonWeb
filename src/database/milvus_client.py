"""
Milvus Vector Database Client
Simplified management of collection schema, indexing, and search.
"""
from typing import List, Dict, Optional
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, db, utility
from logger_config import get_logger
from config import settings

logger = get_logger(__name__)

class MilvusClient:
    """Client for Milvus operations: Manages schema, persistence, and vector search."""

    def __init__(self, host=settings.MILVUS_HOST, port=settings.MILVUS_PORT,
                 db_name=settings.MILVUS_DB_NAME, collection_name=settings.MILVUS_COLLECTION_NAME):
        self.collection_name = collection_name
        self.db_name = db_name

        # Initialize sequence
        connections.connect(alias="default", host=host, port=port)
        self._init_db()
        self.collection = self._init_collection()

    def _init_db(self):
        """Ensures the database exists and is selected."""
        if self.db_name not in db.list_database():
            db.create_database(self.db_name)
        db.using_database(self.db_name)

    def _init_collection(self) -> Collection:
        """Loads or creates the collection with the required schema and index."""
        if utility.has_collection(self.collection_name):
            col = Collection(self.collection_name)
            col.load() # Ensure collection is in memory
            return col

        schema = CollectionSchema(fields=[
            FieldSchema("id", DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema("content", DataType.VARCHAR, max_length=10000),
            FieldSchema("content_vector", DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION),
            FieldSchema("content_url", DataType.VARCHAR, max_length=2048)
        ])

        col = Collection(name=self.collection_name, schema=schema)
        col.create_index("content_vector", {
            "metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 100}
        })
        col.load()
        return col

    def insert_documents(self, documents: List[Dict]) -> List[int]:
        """Inserts dict-based documents and flushes to disk."""
        if not documents: return []

        data = [
            [doc["content"] for doc in documents],
            [doc["content_vector"] for doc in documents],
            [doc["content_url"] for doc in documents]
        ]

        res = self.collection.insert(data)
        self.collection.flush()
        return res.primary_keys

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        """Performs semantic search and returns formatted results with similarity scores."""
        # Note: collection.load() is handled in __init__ for efficiency
        raw_results = self.collection.search(
            data=[query_vector],
            anns_field="content_vector",
            param={"metric_type": "L2", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=["content", "content_url"]
        )

        return [{
            "content": hit.entity.get("content"),
            "content_url": hit.entity.get("content_url"),
            "distance": hit.distance,
            "similarity_score": 1 / (1 + hit.distance)
        } for hits in raw_results for hit in hits]

    def get_collection_stats(self) -> Dict:
        return {
            "num_entities": self.collection.num_entities,
            "fields": [f.name for f in self.collection.schema.fields]
        }

    def close(self):
        connections.disconnect("default")