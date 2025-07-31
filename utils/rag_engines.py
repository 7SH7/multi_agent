import asyncio
import chromadb
from elasticsearch import AsyncElasticsearch
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

@dataclass
class RAGResult:
    content: str
    score: float
    metadata: Dict[str, Any]
    source: str
    timestamp: datetime

class ChromaEngine:
    def __init__(self):
        # 새로운 ChromaDB 클라이언트 방식
        self.client = chromadb.PersistentClient(path="data/embeddings/chromadb")
        self.collection_name = "manufacturing_knowledge"
        self.collection = None
        self._initialize_collection()

    def _initialize_collection(self):
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Manufacturing equipment knowledge base"}
            )

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        try:
            ids = []
            texts = []
            metadatas = []

            for doc in documents:
                doc_id = hashlib.md5(doc['content'].encode()).hexdigest()
                ids.append(doc_id)
                texts.append(doc['content'])
                metadatas.append(doc.get('metadata', {}))

            await asyncio.to_thread(
                self.collection.add,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            print(f"ChromaDB 문서 추가 오류: {e}")
            return False

    async def search(self, query: str, top_k: int = 5) -> List[RAGResult]:
        try:
            results = await asyncio.to_thread(
                self.collection.query,
                query_texts=[query],
                n_results=top_k
            )

            rag_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    score = 1.0 - results['distances'][0][i] if results['distances'] else 0.8
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}

                    rag_results.append(RAGResult(
                        content=doc,
                        score=score,
                        metadata=metadata,
                        source="chromadb",
                        timestamp=datetime.now()
                    ))

            return rag_results
        except Exception as e:
            print(f"ChromaDB 검색 오류: {e}")
            return []

class ElasticsearchEngine:
    def __init__(self):
        self.client = AsyncElasticsearch([{
            'host': 'localhost',
            'port': 9200,
            'scheme': 'http'
        }], 
        retry_on_timeout=True,
        max_retries=3,
        request_timeout=5,
        # 버전 호환성 이슈로 인해 비활성화 상태 유지
        )
        self.index_name = "manufacturing_docs"
        self.is_available = False
        self._initialized = False

    async def _initialize_index(self):
        """지연 초기화 - 첫 번째 사용 시에만 호출됨"""
        if not self._initialized:
            await self._create_index_if_not_exists()
            self._initialized = True

    async def _wait_for_elasticsearch(self, max_retries=3, delay=1):
        """Elasticsearch 서버가 준비될 때까지 기다림"""
        for attempt in range(max_retries):
            try:
                await self.client.cluster.health(wait_for_status='yellow', timeout='3s')
                print(f"Elasticsearch 연결 성공 (시도 {attempt + 1})")
                self.is_available = True
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Elasticsearch 연결 시도 {attempt + 1} 실패, {delay}초 후 재시도...")
                    await asyncio.sleep(delay)
                else:
                    print(f"Elasticsearch 연결 최종 실패: {e}")
                    self.is_available = False
                    return False
        return False

    async def _create_index_if_not_exists(self):
        try:
            # Elasticsearch가 준비될 때까지 기다림
            if not await self._wait_for_elasticsearch():
                print("Elasticsearch 서버에 연결할 수 없어 인덱스 생성을 건너뜁니다.")
                return
                
            exists = await self.client.indices.exists(index=self.index_name)
            if not exists:
                mapping = {
                    "mappings": {
                        "properties": {
                            "content": {
                                "type": "text",
                                "analyzer": "standard"
                            },
                            "title": {
                                "type": "text",
                                "analyzer": "standard"
                            },
                            "category": {
                                "type": "keyword"
                            },
                            "timestamp": {
                                "type": "date"
                            },
                            "metadata": {
                                "type": "object"
                            }
                        }
                    },
                    "settings": {
                        "analysis": {
                            "analyzer": {
                                "standard": {
                                    "type": "standard"
                                }
                            }
                        }
                    }
                }

                await self.client.indices.create(
                    index=self.index_name,
                    mappings=mapping["mappings"],
                    settings=mapping["settings"]
                )
        except Exception as e:
            print(f"Elasticsearch 인덱스 생성 오류: {e}")

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        # 지연 초기화
        await self._initialize_index()
        
        try:
            actions = []
            for doc in documents:
                doc_id = hashlib.md5(doc['content'].encode()).hexdigest()
                action = {
                    "_index": self.index_name,
                    "_id": doc_id,
                    "_source": {
                        "content": doc['content'],
                        "title": doc.get('title', ''),
                        "category": doc.get('category', ''),
                        "timestamp": datetime.now().isoformat(),
                        "metadata": doc.get('metadata', {})
                    }
                }
                actions.append(action)

            from elasticsearch.helpers import async_bulk
            await async_bulk(self.client, actions)
            return True
        except Exception as e:
            print(f"Elasticsearch 문서 추가 오류: {e}")
            return False

    async def search(self, query: str, top_k: int = 5) -> List[RAGResult]:
        # 지연 초기화
        await self._initialize_index()
        
        # Elasticsearch가 사용 불가능한 경우 빈 결과 반환
        if not self.is_available:
            return []
            
        try:
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"content": {"query": query, "boost": 2}}},
                            {"match": {"title": {"query": query, "boost": 1.5}}}
                        ]
                    }
                },
                "size": top_k
            }

            response = await self.client.search(
                index=self.index_name,
                query=search_body["query"],
                size=search_body["size"]
            )

            rag_results = []
            for hit in response['hits']['hits']:
                rag_results.append(RAGResult(
                    content=hit['_source']['content'],
                    score=hit['_score'],
                    metadata=hit['_source'].get('metadata', {}),
                    source="elasticsearch",
                    timestamp=datetime.now()
                ))

            return rag_results
        except Exception as e:
            print(f"Elasticsearch 검색 오류: {e}")
            self.is_available = False  # 연결 상태 업데이트
            return []

    async def close(self):
        """Elasticsearch 클라이언트 리소스 정리"""
        try:
            await self.client.close()
        except Exception as e:
            print(f"Elasticsearch 클라이언트 종료 중 오류: {e}")

class HybridRAGEngine:
    def __init__(self):
        self.chroma_engine = ChromaEngine()
        self.elasticsearch_engine = ElasticsearchEngine()

    async def close(self):
        """하이브리드 RAG 엔진 리소스 정리"""
        try:
            await self.elasticsearch_engine.close()
        except Exception as e:
            print(f"HybridRAGEngine 종료 중 오류: {e}")

    async def search(self, query: str, top_k: int = 5) -> List[RAGResult]:
        # 병렬로 두 엔진에서 검색
        chroma_task = self.chroma_engine.search(query, top_k//2 + 1)
        es_task = self.elasticsearch_engine.search(query, top_k//2 + 1)

        chroma_results, es_results = await asyncio.gather(
            chroma_task, es_task, return_exceptions=True
        )

        # 결과 통합
        all_results = []

        if isinstance(chroma_results, list):
            all_results.extend(chroma_results)

        if isinstance(es_results, list):
            all_results.extend(es_results)

        # 중복 제거 및 점수 기반 정렬
        unique_results = []
        seen_content = set()

        for result in sorted(all_results, key=lambda x: x.score, reverse=True):
            content_hash = hashlib.md5(result.content.encode()).hexdigest()
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)

        return unique_results[:top_k]

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        chroma_task = self.chroma_engine.add_documents(documents)
        es_task = self.elasticsearch_engine.add_documents(documents)

        results = await asyncio.gather(chroma_task, es_task, return_exceptions=True)

        return all(isinstance(r, bool) and r for r in results)