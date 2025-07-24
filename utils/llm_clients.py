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
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code


class OpenAIClient:
    def __init__(self):
        self.client = openai.AsyncOpenAI(
            api_key=LLM_CONFIGS['openai']['api_key']
        )
        self.model = LLM_CONFIGS['openai']['model']
        self.max_tokens = LLM_CONFIGS['openai']['max_tokens']

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
        genai.configure(api_key=LLM_CONFIGS['gemini']['api_key'])
        self.model = genai.GenerativeModel(LLM_CONFIGS['gemini']['model'])
        self.max_tokens = LLM_CONFIGS['gemini']['max_tokens']

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
                model=LLM_CONFIGS['gemini']['model'],
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
        self.client_id = LLM_CONFIGS['clova']['client_id']
        self.client_secret = LLM_CONFIGS['clova']['client_secret']
        self.api_url = LLM_CONFIGS['clova']['api_url']
        self.model = LLM_CONFIGS['clova']['model']

    async def generate_response(self, messages: List[Dict[str, str]],
                                temperature: float = 0.2) -> LLMResponse:
        try:
            headers = {
                'X-NCP-APIGW-API-KEY-ID': self.client_id,
                'X-NCP-APIGW-API-KEY': self.client_secret,
                'Content-Type': 'application/json'
            }

            # Convert to Clova format
            prompt = self._convert_messages_to_prompt(messages)

            data = {
                'model': self.model,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': temperature,
                'max_tokens': LLM_CONFIGS['clova']['max_tokens']
            }

            response = await asyncio.to_thread(
                requests.post, self.api_url, headers=headers, json=data
            )
            response.raise_for_status()

            result = response.json()
            content = result['choices'][0]['message']['content']

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
        self.client = anthropic.Anthropic(
            api_key=LLM_CONFIGS['anthropic']['api_key']
        )
        self.model = LLM_CONFIGS['anthropic']['model']
        self.max_tokens = LLM_CONFIGS['anthropic']['max_tokens']

    async def generate_response(self, messages: List[Dict[str, str]],
                                temperature: float = 0.2) -> LLMResponse:
        try:
            # Convert messages format for Claude
            claude_messages = []
            system_message = ""

            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    claude_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })

            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                messages=claude_messages,
                system=system_message if system_message else None,
                max_tokens=self.max_tokens,
                temperature=temperature
            )

            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                confidence=0.88,
                timestamp=datetime.now(),
                metadata={
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            )
        except Exception as e:
            raise LLMError(f"Anthropic API 오류: {str(e)}")


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