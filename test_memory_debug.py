"""메모리 기능 디버깅 테스트"""

import asyncio
import requests
import json

async def test_memory_with_debug():
    print('=== 메모리 기능 디버깅 테스트 ===')
    
    # 첫 번째 질문 - 자기소개
    first_question = '나는 김상방이야. 지금 틈이 생겨서 고민중이야.'
    print(f'\n1. 첫 번째 질문: {first_question}')
    
    response1 = requests.post('http://localhost:8000/chat/test', json={
        'user_message': first_question,
        'user_id': 'debug_user'
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        session_id = data1['session_id']
        print(f'세션 ID: {session_id}')
        print(f'대화 수: {data1.get("conversation_count")}')
        
        # 두 번째 질문 - 기억 테스트
        second_question = '내 이름이 머라고? 그리고 지금 무슨 문제를 고민하고 있다고?'
        print(f'\n2. 두 번째 질문 (기억 테스트): {second_question}')
        
        response2 = requests.post('http://localhost:8000/chat/test', json={
            'user_message': second_question,
            'session_id': session_id,
            'user_id': 'debug_user'
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f'대화 수: {data2.get("conversation_count")}')
            summary2 = data2.get('executive_summary', '')
            print(f'\n응답: {summary2}')
            
            # 기억 여부 확인
            has_name = '김상방' in summary2
            has_problem = '틈' in summary2 or '고민' in summary2
            
            print(f'\n기억 확인:')
            print(f'- 김상방 언급: {has_name}')
            print(f'- 고민/틈 언급: {has_problem}')
            
            if has_name and has_problem:
                print('\n✅ 메모리 기능 정상 작동!')
            else:
                print('\n❌ 메모리 기능 문제 확인됨')
        else:
            print(f'두 번째 요청 실패: {response2.status_code} - {response2.text}')
    else:
        print(f'첫 번째 요청 실패: {response1.status_code} - {response1.text}')

if __name__ == "__main__":
    asyncio.run(test_memory_with_debug())