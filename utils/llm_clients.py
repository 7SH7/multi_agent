import asyncio
import openai
import google.generativeai as genai
import anthropic
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from config.settings import LLM_CONFIGS


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any]


class LLMError(Exception):
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class OpenAIClient:
    def __init__(self):
        self.client = openai.AsyncOpenAI(
            api_key=LLM_CONFIGS['openai']['api_key']
        )
        self.model = LLM_CONFIGS['openai']['model']
        self.max_tokens = LLM_CONFIGS['openai']['max_tokens']

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """리소스 정리"""
        if hasattr(self.client, '_client') and hasattr(self.client._client, 'aclose'):
            await self.client._client.aclose()

    async def generate_response(self, messages: List[Dict[str, str]],
                                temperature: float = 0.2) -> LLMResponse:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=self.max_tokens
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model,
                tokens_used=response.usage.total_tokens,
                confidence=0.85,
                timestamp=datetime.now(),
                metadata={
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens
                }
            )
        except Exception as e:
            raise LLMError(f"OpenAI API 오류: {str(e)}")


class GeminiClient:
    def __init__(self):
        genai.configure(api_key=LLM_CONFIGS['google']['api_key'])
        self.model = genai.GenerativeModel(LLM_CONFIGS['google']['model'])
        self.max_tokens = LLM_CONFIGS['google']['max_tokens']

    async def generate_response(self, messages: List[Dict[str, str]],
                                temperature: float = 0.2) -> LLMResponse:
        try:
            # Convert messages to Gemini format
            prompt = self._convert_messages_to_prompt(messages)

            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=self.max_tokens
                )
            )

            return LLMResponse(
                content=response.text,
                model=str(LLM_CONFIGS['google']['model']),
                tokens_used=response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
                confidence=0.82,
                timestamp=datetime.now(),
                metadata={
                    'candidate_count': len(response.candidates) if hasattr(response, 'candidates') else 1
                }
            )
        except Exception as e:
            raise LLMError(f"Gemini API 오류: {str(e)}")

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                prompt_parts.append(f"시스템 지시사항: {content}")
            elif role == 'user':
                prompt_parts.append(f"사용자: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"어시스턴트: {content}")
        return "\n\n".join(prompt_parts)


class ClovaClient:
    def __init__(self):
        self.api_key = LLM_CONFIGS['naver']['api_key']
        self.api_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
        self.model = LLM_CONFIGS['naver']['model']

    async def generate_response(self, messages: List[Dict[str, str]],
                                temperature: float = 0.2) -> LLMResponse:
        try:
            headers = {
                'X-NCP-APIGW-TEST-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }

            # Convert to Clova format
            prompt = self._convert_messages_to_prompt(messages)

            data = {
                'messages': [{'role': 'user', 'content': prompt}],
                'topP': 0.8,
                'topK': 0,
                'maxTokens': LLM_CONFIGS['naver']['max_tokens'],
                'temperature': temperature,
                'repeatPenalty': 5.0,
                'stopBefore': [],
                'includeAiFilters': True
            }

            response = await asyncio.to_thread(
                requests.post, self.api_url, headers=headers, json=data
            )
            response.raise_for_status()

            result = response.json()
            content = result.get('result', {}).get('message', {}).get('content', '')

            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=result.get('usage', {}).get('total_tokens', 0),
                confidence=0.80,
                timestamp=datetime.now(),
                metadata={
                    'response_time': response.elapsed.total_seconds()
                }
            )
        except Exception as e:
            raise LLMError(f"Clova API 오류: {str(e)}")

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])


class AnthropicClient:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(
            api_key=LLM_CONFIGS['anthropic']['api_key']
        )
        self.model = LLM_CONFIGS['anthropic']['model']
        self.max_tokens = LLM_CONFIGS['anthropic']['max_tokens']

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """리소스 정리"""
        await self.client.close()

    async def generate_response(self, messages: List[Dict[str, str]],
                                temperature: float = 0.2) -> LLMResponse:
        try:
            # Convert messages format for Claude
            claude_messages = []
            system_message = None

            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                elif msg['role'] in ['user', 'assistant']:
                    claude_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })

            # API 파라미터 구성
            create_params = {
                "model": self.model,
                "messages": claude_messages,
                "max_tokens": self.max_tokens,
                "temperature": temperature
            }
            
            # system 메시지가 있으면 올바른 형식으로 추가
            if system_message:
                create_params["system"] = system_message  # 문자열로 전달 (최신 버전에서 지원)

            response = await self.client.messages.create(**create_params)

            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                confidence=0.88,
                timestamp=datetime.now(),
                metadata={
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'api_version': '0.60.0'
                }
            )
        except Exception as e:
            raise LLMError(f"Anthropic API 오류: {str(e)}")
    
    async def generate_simple_response(self, messages: List[Dict[str, str]]) -> str:
        """대화 형태의 간단한 응답 생성"""
        try:
            response = await self.generate_response(messages)
            return response.content
        except Exception as e:
            return f"Claude 응답 생성 중 오류가 발생했습니다: {str(e)}"


def get_llm_client(client_type: str):
    clients = {
        'openai': OpenAIClient,
        'gemini': GeminiClient,
        'clova': ClovaClient,
        'anthropic': AnthropicClient
    }

    if client_type not in clients:
        raise ValueError(f"지원하지 않는 클라이언트: {client_type}")

    return clients[client_type]()