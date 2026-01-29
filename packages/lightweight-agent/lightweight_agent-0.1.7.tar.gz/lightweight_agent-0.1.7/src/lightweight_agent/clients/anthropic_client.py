"""Anthropic Client Implementation"""
from typing import AsyncIterator, Optional, Union, List, Dict, Any
from pathlib import Path
import json
from anthropic import AsyncAnthropic
from anthropic._exceptions import APIError as AnthropicAPIError, APIConnectionError

from .base import BaseClient
from ..exceptions import APIError, NetworkError, ValidationError
from ..utils import validate_prompt, create_anthropic_image_message
from ..models import GenerateResponse, StreamingResponse, TokenUsage


class AnthropicClient(BaseClient):
    """Anthropic async client"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Anthropic client
        
        :param api_key: API key, default read from environment variable
        :param base_url: API base URL, default read from environment variable
        :param model: Model name, default read from environment variable
        """
        
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        
        # Initialize Anthropic client
        client_kwargs = {'api_key': self.api_key,
                         'base_url':self.base_url,
                         'max_retries':3,
                         }

        self.client = AsyncAnthropic(**client_kwargs)
    
    def add_image_to_messages(
        self,
        messages: List[Dict[str, Any]],
        image_path: Union[str, Path],
        text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Add image to messages list for vision API
        
        :param messages: Existing message list
        :param image_path: Path to image file
        :param text: Optional text prompt to accompany the image
        :return: Updated messages list with image message
        """
        image_message = create_anthropic_image_message(image_path, text)
        messages.append(image_message)
        return messages
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        system: str = "",
        max_tokens = 4096*2,
        **kwargs
    ) -> Union[GenerateResponse, StreamingResponse]:
        """
        Generate response
        
        :param messages: Message list (can include image messages created with add_image_to_messages)
        :param stream: Whether to stream response
        :param system: System prompt
        :param max_tokens: Maximum tokens
        :param kwargs: Other Anthropic API parameters (such as temperature, etc.)
        :return: StreamingResponse for streaming, GenerateResponse for non-streaming
        """
        
        try:
            # Build request parameters
            request_params = {
                'model': self.model,
                'system':system,
                'messages': messages,
                'stream': stream,
                "max_tokens":max_tokens,
                **kwargs
            }
            
            if stream:
                response = await self.client.messages.create(**request_params)
                return await self._handle_streaming_response(response)
            else:
                response = await self.client.messages.create(**request_params)
                if response.content and len(response.content) > 0:
                    content = response.content[0].text
                
                usage = None
                if hasattr(response, 'usage') and response.usage:
                    usage = TokenUsage(
                        prompt_tokens=response.usage.input_tokens,
                        completion_tokens=response.usage.output_tokens,
                        total_tokens=response.usage.input_tokens + response.usage.output_tokens
                    )
                
                return GenerateResponse(content=content, usage=usage)
        
        except APIConnectionError as e:
            raise NetworkError(f"Network error when calling Anthropic API: {str(e)}") from e
        except AnthropicAPIError as e:
            # Extract detailed error information
            error_details = str(e)
            if hasattr(e, 'status_code'):
                error_details += f" (Status: {e.status_code})"
            if hasattr(e, 'body') and e.body:
                try:
                    if isinstance(e.body, dict):
                        error_details += f" (Body: {json.dumps(e.body, ensure_ascii=False)})"
                    else:
                        error_details += f" (Body: {str(e.body)})"
                except:
                    pass
            if hasattr(e, 'message') and e.message:
                error_details += f" (Message: {e.message})"
            raise APIError(f"Anthropic API error: {error_details}") from e
        except Exception as e:
            raise APIError(f"Unexpected error: {str(e)}") from e
    
    async def _handle_streaming_response(self, response) -> StreamingResponse:
        """
        Handle Anthropic streaming response
        
        :param response: Anthropic streaming response object
        :return: StreamingResponse object
        """
        usage = None
        
        async def stream_generator() -> AsyncIterator[str]:
            nonlocal usage
            async for event in response:
                if event.type == 'content_block_delta':
                    if event.delta.type == 'text_delta':
                        yield event.delta.text
                elif event.type == 'message_start':
                    pass
                elif event.type == 'content_block_start':
                    pass
                elif event.type == 'content_block_stop':
                    pass
                elif event.type == 'message_delta':
                    if hasattr(event, 'usage') and event.usage:
                        usage = TokenUsage(
                            prompt_tokens=event.usage.input_tokens,
                            completion_tokens=event.usage.output_tokens,
                            total_tokens=event.usage.input_tokens + event.usage.output_tokens
                        )
                elif event.type == 'message_stop':
                    pass
        
        async def get_usage():
            return usage
        
        return StreamingResponse(stream_generator(), usage_getter=get_usage)
