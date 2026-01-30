"""
OMNIMIND Memory Layer - Semantic Memory
ความรู้ถาวร (Level 3)
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import os
import json


@dataclass
class KnowledgeEntry:
    """Single entry in semantic memory (Knowledge Graph node)"""
    id: str
    content: str
    category: str
    confidence: float = 0.8
    source: str = "unknown"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class SemanticMemory:
    """
    Semantic Memory - ความรู้ถาวร
    
    คุณสมบัติ:
    - เก็บ Facts, concepts, relationships
    - ขนาดไม่จำกัด (external storage)
    - ใช้ ChromaDB สำหรับ vector search
    - มี confidence scores
    - Track source ของข้อมูล
    """
    
    def __init__(self, db_path: str = "data/semantic_db", 
                 embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.db_path = db_path
        self.embedding_model_name = embedding_model
        self._collection = None
        self._embedding_model = None
        self._client = None
        self._entry_counter = 0
        self._fallback_storage: List[Dict] = []
        
        # Ensure directory exists
        os.makedirs(db_path, exist_ok=True)
    
    def _init_db(self):
        """Initialize ChromaDB and embedding model"""
        if self._collection is not None:
            return
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            self._client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            self._collection = self._client.get_or_create_collection(
                name="semantic_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            
            self._entry_counter = self._collection.count()
            
        except ImportError:
            # Only warn once if fallback is empty
            if not self._fallback_storage:
                print("⚠️ ChromaDB not installed. Using in-memory fallback.")
            self._collection = None
            # _fallback_storage is already initialized in __init__
    
    def _load_embedding_model(self):
        """Load sentence transformer model"""
        if self._embedding_model is not None:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        except ImportError:
            print("⚠️ sentence-transformers not installed. Embeddings disabled.")
            self._embedding_model = None
        except Exception as e:
            # Catch other errors like Keras/TensorFlow compatibility issues
            print(f"⚠️ sentence-transformers load failed ({type(e).__name__}). Embeddings disabled.")
            self._embedding_model = None
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text"""
        self._load_embedding_model()
        if self._embedding_model is None:
            return None
        return self._embedding_model.encode(text).tolist()
    
    def _generate_id(self) -> str:
        """Generate unique entry ID"""
        self._entry_counter += 1
        return f"sem_{self._entry_counter:06d}"
    
    def add(self, content: str, category: str = "general",
            confidence: float = 0.8, source: str = "user",
            metadata: Dict[str, Any] = None) -> KnowledgeEntry:
        """
        Add new knowledge entry
        """
        self._init_db()
        
        entry = KnowledgeEntry(
            id=self._generate_id(),
            content=content,
            category=category,
            confidence=confidence,
            source=source,
            metadata=metadata or {}
        )
        
        embedding = self._get_embedding(content)
        
        if self._collection is not None:
            self._collection.add(
                ids=[entry.id],
                documents=[content],
                embeddings=[embedding] if embedding else None,
                metadatas=[{
                    "category": category,
                    "confidence": confidence,
                    "source": source,
                    "created_at": entry.created_at.isoformat(),
                    **(metadata or {})
                }]
            )
        else:
            # Fallback storage
            self._fallback_storage.append({
                **entry.to_dict(),
                "embedding": embedding
            })
        
        return entry
    
    def search(self, query: str, limit: int = 5, 
               min_confidence: float = 0.0,
               category: Optional[str] = None) -> List[Tuple[KnowledgeEntry, float]]:
        """
        Search for relevant knowledge using semantic similarity
        """
        self._init_db()
        
        results = []
        
        if self._collection is not None and self._collection.count() > 0:
            query_embedding = self._get_embedding(query)
            
            where_filter = {}
            if min_confidence > 0:
                where_filter["confidence"] = {"$gte": min_confidence}
            if category:
                where_filter["category"] = category
            
            search_results = self._collection.query(
                query_embeddings=[query_embedding] if query_embedding else None,
                query_texts=[query] if not query_embedding else None,
                n_results=limit,
                where=where_filter if where_filter else None
            )
            
            if search_results and search_results['ids']:
                for i, doc_id in enumerate(search_results['ids'][0]):
                    meta = search_results['metadatas'][0][i]
                    distance = search_results['distances'][0][i] if search_results.get('distances') else 0
                    similarity = 1 - distance  # Convert distance to similarity
                    
                    entry = KnowledgeEntry(
                        id=doc_id,
                        content=search_results['documents'][0][i],
                        category=meta.get('category', 'general'),
                        confidence=meta.get('confidence', 0.8),
                        source=meta.get('source', 'unknown'),
                        metadata={k: v for k, v in meta.items() 
                                 if k not in ['category', 'confidence', 'source', 'created_at']}
                    )
                    results.append((entry, similarity))
        
        else:
            # Fallback: simple keyword search
            query_lower = query.lower()
            for item in self._fallback_storage:
                if query_lower in item['content'].lower():
                    entry = KnowledgeEntry(
                        id=item['id'],
                        content=item['content'],
                        category=item['category'],
                        confidence=item['confidence'],
                        source=item['source'],
                    )
                    results.append((entry, 0.5))
            results = results[:limit]
        
        return results
    
    def update_confidence(self, entry_id: str, new_confidence: float):
        """Update confidence score of an entry"""
        self._init_db()
        
        if self._collection is not None:
            # Get current entry
            result = self._collection.get(ids=[entry_id])
            if result and result['ids']:
                meta = result['metadatas'][0]
                meta['confidence'] = new_confidence
                meta['updated_at'] = datetime.now().isoformat()
                
                self._collection.update(
                    ids=[entry_id],
                    metadatas=[meta]
                )
    
    def delete(self, entry_id: str):
        """Delete a knowledge entry"""
        self._init_db()
        
        if self._collection is not None:
            self._collection.delete(ids=[entry_id])
        else:
            self._fallback_storage = [
                e for e in self._fallback_storage if e['id'] != entry_id
            ]
    
    def get_by_category(self, category: str, limit: int = 20) -> List[KnowledgeEntry]:
        """Get entries by category"""
        self._init_db()
        
        entries = []
        
        if self._collection is not None:
            results = self._collection.get(
                where={"category": category},
                limit=limit
            )
            
            if results and results['ids']:
                for i, doc_id in enumerate(results['ids']):
                    meta = results['metadatas'][i]
                    entries.append(KnowledgeEntry(
                        id=doc_id,
                        content=results['documents'][i],
                        category=meta.get('category', 'general'),
                        confidence=meta.get('confidence', 0.8),
                        source=meta.get('source', 'unknown'),
                    ))
        
        return entries
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        self._init_db()
        
        if self._collection is not None:
            count = self._collection.count()
        else:
            count = len(self._fallback_storage)
        
        return {
            "total_entries": count,
            "embedding_model": self.embedding_model_name,
            "db_path": self.db_path,
        }
