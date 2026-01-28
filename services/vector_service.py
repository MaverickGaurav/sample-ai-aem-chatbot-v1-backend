"""
Vector Service - Handles Qdrant vector embeddings for RAG
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional
from config import Config
import uuid


class VectorService:
    def __init__(self):
        self.enabled = False
        self.client = None
        self.model = None
        self.collection_name = Config.QDRANT_COLLECTION
        self.vector_size = 384  # all-MiniLM-L6-v2 dimension

        try:
            # Try to initialize Qdrant client
            self.client = QdrantClient(
                host=Config.QDRANT_HOST,
                port=Config.QDRANT_PORT
            )

            # Try to load sentence transformer model
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(Config.EMBEDDING_MODEL)
                self.enabled = True
                self._init_collection()
                print("✓ Vector Service initialized successfully")
            except Exception as e:
                print(f"⚠ Warning: Could not load embedding model: {e}")
                print("  Vector/RAG features will be disabled")
                self.enabled = False
        except Exception as e:
            print(f"⚠ Warning: Could not connect to Qdrant: {e}")
            print("  Vector/RAG features will be disabled")
            self.enabled = False

    def _init_collection(self):
        """Initialize Qdrant collection"""
        if not self.enabled or not self.client:
            return

        try:
            collections = self.client.get_collections().collections
            collection_exists = any(
                col.name == self.collection_name for col in collections
            )

            if not collection_exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            print(f"Warning: Could not initialize Qdrant collection: {e}")
            self.enabled = False

    def add_document(
            self,
            text: str,
            metadata: Dict,
            doc_id: Optional[str] = None
    ) -> str:
        """
        Add document to vector store

        Args:
            text: Document text
            metadata: Document metadata
            doc_id: Optional document ID

        Returns:
            Document ID
        """
        if not self.enabled:
            print("Vector service disabled - skipping document add")
            return ""

        try:
            doc_id = doc_id or str(uuid.uuid4())

            # Generate embedding
            embedding = self.model.encode(text).tolist()

            # Create point
            point = PointStruct(
                id=doc_id,
                vector=embedding,
                payload={
                    "text": text,
                    **metadata
                }
            )

            # Upsert to collection
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            return doc_id
        except Exception as e:
            print(f"Error adding document: {e}")
            return ""

    def search_similar(
            self,
            query: str,
            limit: int = 5,
            filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents

        Args:
            query: Search query
            limit: Maximum results
            filter_dict: Optional filter conditions

        Returns:
            List of similar documents
        """
        if not self.enabled:
            print("Vector service disabled - returning empty results")
            return []

        try:
            # Generate query embedding
            query_vector = self.model.encode(query).tolist()

            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filter_dict
            )

            # Format results
            documents = []
            for result in results:
                documents.append({
                    'id': result.id,
                    'score': result.score,
                    'text': result.payload.get('text', ''),
                    'metadata': {
                        k: v for k, v in result.payload.items()
                        if k != 'text'
                    }
                })

            return documents
        except Exception as e:
            print(f"Error searching: {e}")
            return []

    def delete_document(self, doc_id: str):
        """Delete document from vector store"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[doc_id]
            )
        except Exception as e:
            print(f"Error deleting document: {e}")

    def add_aem_page(
            self,
            page_path: str,
            page_content: str,
            metadata: Dict
    ) -> str:
        """
        Add AEM page to vector store

        Args:
            page_path: AEM page path
            page_content: Page HTML/text content
            metadata: Page metadata

        Returns:
            Document ID
        """
        full_metadata = {
            'source': 'aem',
            'page_path': page_path,
            **metadata
        }

        return self.add_document(
            text=page_content,
            metadata=full_metadata,
            doc_id=page_path.replace('/', '_')
        )

    def search_aem_content(
            self,
            query: str,
            limit: int = 5
    ) -> List[Dict]:
        """
        Search AEM content in vector store

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Relevant AEM pages
        """
        return self.search_similar(
            query=query,
            limit=limit,
            filter_dict={'source': 'aem'}
        )

    def check_health(self) -> bool:
        """Check if Qdrant is accessible"""
        if not self.enabled:
            return False
        try:
            self.client.get_collections()
            return True
        except:
            return False