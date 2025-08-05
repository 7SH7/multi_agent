#!/usr/bin/env python3
"""
Docker 서비스 상태 확인 스크립트
ChromaDB와 Elasticsearch 연결 테스트
"""

import asyncio
import chromadb
from elasticsearch import Elasticsearch

def test_docker_chromadb():
    """Docker ChromaDB 연결 테스트"""
    print("🔍 ChromaDB (Docker) 연결 테스트...")
    try:
        # Docker ChromaDB (포트 8001)
        client = chromadb.HttpClient(host="localhost", port=8001)
        client.heartbeat()
        print("✅ ChromaDB Docker 서비스 연결 성공!")
        
        # 컬렉션 목록 확인
        collections = client.list_collections()
        print(f"   컬렉션 수: {len(collections)}")
        
        return True
    except Exception as e:
        print(f"❌ ChromaDB Docker 연결 실패: {str(e)}")
        return False

def test_elasticsearch():
    """Elasticsearch 연결 테스트"""
    print("🔍 Elasticsearch 연결 테스트...")
    try:
        # Docker Elasticsearch (포트 9200)
        es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])
        
        # 클러스터 health 확인
        health = es.cluster.health()
        print("✅ Elasticsearch 연결 성공!")
        print(f"   클러스터 상태: {health['status']}")
        print(f"   노드 수: {health['number_of_nodes']}")
        
        return True
    except Exception as e:
        print(f"❌ Elasticsearch 연결 실패: {str(e)}")
        return False

def test_redis():
    """Redis 연결 테스트"""
    print("🔍 Redis 연결 테스트...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis 연결 성공!")
        return True
    except Exception as e:
        print(f"❌ Redis 연결 실패: {str(e)}")
        return False

def check_docker_containers():
    """Docker 컨테이너 상태 확인"""
    print("🔍 Docker 컨테이너 상태 확인...")
    try:
        import subprocess
        result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Docker 컨테이너 목록:")
            print(result.stdout)
        else:
            print("❌ Docker 명령 실행 실패")
            
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Docker 상태 확인 실패: {str(e)}")
        return False

async def comprehensive_test():
    """종합 테스트"""
    print("=" * 50)
    print("🚀 Smart Factory Docker 서비스 종합 테스트")
    print("=" * 50)
    
    # Docker 컨테이너 상태 먼저 확인
    docker_ok = check_docker_containers()
    print()
    
    if not docker_ok:
        print("⚠️  Docker가 실행되지 않았거나 컨테이너가 시작되지 않았습니다.")
        print("   다음 명령으로 서비스를 시작하세요:")
        print("   docker-compose up -d redis chroma elasticsearch")
        return
    
    # 각 서비스 테스트
    results = {}
    results['redis'] = test_redis()
    print()
    results['chromadb'] = test_docker_chromadb()
    print()
    results['elasticsearch'] = test_elasticsearch()
    print()
    
    # 결과 요약
    print("=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    total_services = len(results)
    success_count = sum(results.values())
    
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service.upper()}: {'연결 성공' if status else '연결 실패'}")
    
    print()
    print(f"📈 성공률: {success_count}/{total_services} ({success_count/total_services*100:.1f}%)")
    
    if success_count == total_services:
        print("🎉 모든 서비스가 정상적으로 연결되었습니다!")
        print("🚀 이제 Multi-Agent RAG 시스템을 테스트할 수 있습니다.")
    else:
        print("⚠️  일부 서비스 연결에 문제가 있습니다.")
        print("   Docker 컨테이너가 모두 실행되었는지 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(comprehensive_test())