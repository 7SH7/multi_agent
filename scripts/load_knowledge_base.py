"""Knowledge base loading script for ChromaDB and Elasticsearch."""

import asyncio
import json
import os
import sys
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.rag_engines import ChromaEngine, ElasticsearchEngine


class KnowledgeBaseLoader:
    def __init__(self):
        self.chroma_engine = ChromaEngine()
        self.elasticsearch_engine = ElasticsearchEngine()
        self.data_dir = Path(__file__).parent.parent / "data" / "knowledge_base"

    def load_json_files(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all JSON files from knowledge base directory"""
        knowledge_data: Dict[str, List[Dict[str, Any]]] = {}

        if not self.data_dir.exists():
            print(f"❌ Knowledge base directory not found: {self.data_dir}")
            return knowledge_data

        json_files = list(self.data_dir.glob("*.json"))
        if not json_files:
            print(f"❌ No JSON files found in: {self.data_dir}")
            return knowledge_data

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    knowledge_data[json_file.stem] = data
                    print(f"✅ Loaded {len(data)} items from {json_file.name}")
            except Exception as e:
                print(f"❌ Error loading {json_file.name}: {e}")

        return knowledge_data

    async def load_to_chroma(self, knowledge_data: Dict[str, List[Dict[str, Any]]]):
        """Load knowledge data to ChromaDB"""
        print("📤 Loading data to ChromaDB...")

        try:
            await self.chroma_engine.initialize()

            total_loaded = 0
            for category, items in knowledge_data.items():
                print(f"📋 Processing {category} ({len(items)} items)...")

                for i, item in enumerate(items):
                    # Create document text
                    if category == "manufacturing_equipment":
                        text = f"{item['name']}: {item['description']} - {item['category']}"
                        metadata = {
                            "category": item["category"],
                            "type": item["type"],
                            "source": category
                        }
                    elif category == "troubleshooting_guide":
                        text = f"Problem: {item['problem']} - Solution: {item['solution']}"
                        metadata = {
                            "equipment": item["equipment"],
                            "severity": item["severity"],
                            "source": category
                        }
                    elif category == "safety_procedures":
                        text = f"{item['title']}: {item['procedure']}"
                        metadata = {
                            "equipment_type": item["equipment_type"],
                            "risk_level": item["risk_level"],
                            "source": category
                        }
                    elif category == "maintenance_manual":
                        text = f"{item['equipment']}: {item['procedure']} - {item['description']}"
                        metadata = {
                            "equipment": item["equipment"],
                            "frequency": item["frequency"],
                            "source": category
                        }
                    else:
                        text = str(item)
                        metadata = {"source": category}

                    # Add to ChromaDB
                    await self.chroma_engine.add_document(
                        text=text,
                        metadata=metadata,
                        doc_id=f"{category}_{i}"
                    )
                    total_loaded += 1

                print(f"✅ Loaded {len(items)} {category} items to ChromaDB")

            print(f"🎉 Total {total_loaded} documents loaded to ChromaDB")

        except Exception as e:
            print(f"❌ Error loading to ChromaDB: {e}")
            raise

    async def load_to_elasticsearch(self, knowledge_data: Dict[str, List[Dict[str, Any]]]):
        """Load knowledge data to Elasticsearch"""
        print("📤 Loading data to Elasticsearch...")

        try:
            await self.elasticsearch_engine.initialize()

            total_loaded = 0
            for category, items in knowledge_data.items():
                print(f"📋 Processing {category} ({len(items)} items)...")

                for i, item in enumerate(items):
                    # Prepare document for Elasticsearch
                    doc = {
                        **item,
                        "source_category": category,
                        "doc_id": f"{category}_{i}"
                    }

                    # Add to Elasticsearch
                    await self.elasticsearch_engine.add_document(
                        doc=doc,
                        doc_id=f"{category}_{i}"
                    )
                    total_loaded += 1

                print(f"✅ Loaded {len(items)} {category} items to Elasticsearch")

            print(f"🎉 Total {total_loaded} documents loaded to Elasticsearch")

        except Exception as e:
            print(f"❌ Error loading to Elasticsearch: {e}")
            raise


async def load_knowledge_to_chroma():
    """Load knowledge base to ChromaDB only"""
    loader = KnowledgeBaseLoader()
    knowledge_data = loader.load_json_files()

    if knowledge_data:
        await loader.load_to_chroma(knowledge_data)
    else:
        print("❌ No knowledge data to load")


async def load_knowledge_to_elasticsearch():
    """Load knowledge base to Elasticsearch only"""
    loader = KnowledgeBaseLoader()
    knowledge_data = loader.load_json_files()

    if knowledge_data:
        await loader.load_to_elasticsearch(knowledge_data)
    else:
        print("❌ No knowledge data to load")


async def process_knowledge_files():
    """Process and load knowledge base to both ChromaDB and Elasticsearch"""
    print("🚀 Starting knowledge base loading...")

    loader = KnowledgeBaseLoader()
    knowledge_data = loader.load_json_files()

    if not knowledge_data:
        print("❌ No knowledge data found to load")
        return

    try:
        # Load to both systems in parallel
        await asyncio.gather(
            loader.load_to_chroma(knowledge_data),
            loader.load_to_elasticsearch(knowledge_data)
        )

        print("🎉 Knowledge base loading completed successfully!")

        # Print summary
        total_items = sum(len(items) for items in knowledge_data.values())
        print(f"📊 Loaded {total_items} total items across {len(knowledge_data)} categories")
        for category, items in knowledge_data.items():
            print(f"   - {category}: {len(items)} items")

    except Exception as e:
        print(f"❌ Knowledge base loading failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(process_knowledge_files())