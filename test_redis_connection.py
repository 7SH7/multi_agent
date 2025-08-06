import redis.asyncio as redis
import asyncio

async def test_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        await r.ping()
        print('✅ Redis 연결 성공')
        
        # 세션 키 조회
        keys = await r.keys("chatbot_session:*")
        print(f'📊 현재 세션 수: {len(keys)}')
        
        if keys:
            # 최근 세션 정보 확인
            recent_session = keys[-1]
            session_data = await r.hgetall(recent_session)
            print(f'🔍 최근 세션 ({recent_session}):')
            print(f'   - conversation_count: {session_data.get("conversation_count", "없음")}')
            print(f'   - metadata 키: {session_data.get("metadata", "없음")[:100]}...')
        
        await r.close()
        
    except Exception as e:
        print(f'❌ Redis 연결 실패: {str(e)}')

if __name__ == "__main__":
    asyncio.run(test_redis())