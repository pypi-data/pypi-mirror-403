"""OpenAI Client Implementation"""
import random
from typing import AsyncIterator, Optional, Union, List, Dict, Any
from pathlib import Path
from openai import AsyncOpenAI
from openai._exceptions import APIError as OpenAIAPIError, APIConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    retry_if_exception,
    RetryCallState,
)

from .base import BaseClient
from ..exceptions import APIError, NetworkError, ValidationError, RateLimitError, ServerError
from ..utils import validate_prompt, create_openai_image_message
from ..models import GenerateResponse, StreamingResponse, TokenUsage


class RetryAfterWait:
    """Custom wait strategy that prioritizes Retry-After header, falls back to exponential backoff"""
    
    def __init__(self, base_delay: float = 2.0, enable_backoff: bool = True, max_wait: float = 60.0):
        self.base_delay = base_delay
        self.enable_backoff = enable_backoff
        self.max_wait = max_wait
    
    def __call__(self, retry_state: RetryCallState) -> float:
        """Calculate wait time based on Retry-After header or exponential backoff"""
        exception = retry_state.outcome.exception()
        
        # Try to extract Retry-After header from OpenAI API error
        if isinstance(exception, OpenAIAPIError):
            retry_after = self._extract_retry_after(exception)
            if retry_after:
                return min(retry_after, self.max_wait)
        
        # Fall back to exponential backoff
        if self.enable_backoff:
            attempt = retry_state.attempt_number - 1  # attempt_number is 1-indexed
            exponential_delay = self.base_delay * (2 ** attempt)
            jitter = random.uniform(0.5, 1.5)
            wait_time = exponential_delay * jitter
            return min(wait_time, self.max_wait)
        else:
            # Linear backoff
            attempt = retry_state.attempt_number - 1
            return self.base_delay * (attempt + 1)
    
    @staticmethod
    def _extract_retry_after(error: OpenAIAPIError) -> Optional[float]:
        """Extract Retry-After value from error response headers"""
        try:
            if hasattr(error, 'response') and error.response:
                headers = getattr(error.response, 'headers', None)
                if headers:
                    retry_after = headers.get('Retry-After') or headers.get('retry-after')
                    if retry_after:
                        try:
                            return float(retry_after)
                        except (ValueError, TypeError):
                            pass
        except Exception:
            pass
        return None


def _is_retryable_error(exception: Exception) -> bool:
    """Check if an exception should be retried"""
    # Network errors (APIConnectionError) should be retried
    if isinstance(exception, APIConnectionError):
        return True
    
    # Rate limit errors (429) should be retried
    if isinstance(exception, OpenAIAPIError):
        status_code = getattr(exception, 'status_code', None)
        if status_code == 429:
            return True
        # Server errors (5xx) should be retried
        if status_code and 500 <= status_code < 600:
            return True
    
    return False


def _convert_openai_error(error: Exception) -> Exception:
    """Convert OpenAI API errors to our custom exceptions"""
    if isinstance(error, APIConnectionError):
        return NetworkError(f"Network error when calling OpenAI API: {str(error)}")
    
    if isinstance(error, OpenAIAPIError):
        status_code = getattr(error, 'status_code', None)
        
        if status_code == 429:
            retry_after = RetryAfterWait._extract_retry_after(error)
            error_msg = f"Rate limit exceeded (429): {str(error)}"
            if retry_after:
                error_msg += f" Retry-After: {retry_after} seconds"
            return RateLimitError(error_msg)
        
        if status_code and 500 <= status_code < 600:
            return ServerError(f"Server error ({status_code}): {str(error)}")
        
        return APIError(f"OpenAI API error: {str(error)}")
    
    return APIError(f"Unexpected error: {str(error)}")


class OpenAIClient(BaseClient):
    """OpenAI async client"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        rate_limit_retry_delay: float = 2.0,
        enable_rate_limit_backoff: bool = True
    ):
        """
        Initialize OpenAI client
        
        :param api_key: API key, default read from environment variable
        :param base_url: API base URL, default read from environment variable
        :param model: Model name, default read from environment variable
        :param max_retries: Maximum number of retries for transient errors (network, rate limit, server errors), default 3
        :param rate_limit_retry_delay: Initial delay in seconds for rate limit retries, default 2.0
        :param enable_rate_limit_backoff: Enable exponential backoff for rate limit errors, default True
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_retries = max_retries
        self.rate_limit_retry_delay = rate_limit_retry_delay
        self.enable_rate_limit_backoff = enable_rate_limit_backoff
        # Reduce default retries to avoid request accumulation during rate limiting
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, max_retries=0)
        # Create wait strategy instance for retry logic
        self._retry_wait = RetryAfterWait(
            base_delay=rate_limit_retry_delay,
            enable_backoff=enable_rate_limit_backoff,
            max_wait=60.0
        )
    
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
        image_message = create_openai_image_message(image_path, text)
        messages.append(image_message)
        return messages
    
    def _get_retry_decorator(self):
        """Get retry decorator configured with instance settings"""
        return retry(
            stop=stop_after_attempt(self.max_retries + 1),
            retry=retry_if_exception(_is_retryable_error),
            wait=self._retry_wait,
            reraise=True,
            before_sleep=self._log_retry_attempt,
        )
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        temperature=0.6,
        **kwargs
    ) -> Union[GenerateResponse, StreamingResponse]:
        """
        Generate response with automatic rate limit handling and exponential backoff
        
        :param messages: Message list (can include image messages created with add_image_to_messages)
        :param stream: Whether to stream response
        :param temperature: Temperature parameter
        :return: StreamingResponse for streaming, GenerateResponse for non-streaming
        """
        async def _generate_impl():
            """Internal implementation of generate"""
            # Build request parameters
            request_params = {
                'model': self.model,
                'messages': messages,
                'stream': stream,
                "temperature": temperature,
                **kwargs
            }
            
            if stream:
                response = await self.client.chat.completions.create(**request_params)
                return await self._handle_streaming_response(response)
            else:
                response = await self.client.chat.completions.create(**request_params)
                content = response.choices[0].message.content or ""
                print(response)

                usage = None
                if response.usage:
                    usage = TokenUsage(
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        total_tokens=response.usage.total_tokens
                    )
                
                return GenerateResponse(content=content, usage=usage)
        
        # Apply retry decorator
        retry_decorator = self._get_retry_decorator()
        decorated_func = retry_decorator(_generate_impl)
        
        try:
            return await decorated_func()
        except (APIConnectionError, OpenAIAPIError) as e:
            # Convert OpenAI errors to our custom exceptions
            raise _convert_openai_error(e) from e
        except Exception as e:
            raise APIError(f"Unexpected error: {str(e)}") from e
    
    def _log_retry_attempt(self, retry_state: RetryCallState):
        """Log retry attempts"""
        exception = retry_state.outcome.exception()
        wait_time = self._retry_wait(retry_state)
        
        if isinstance(exception, APIConnectionError):
            print(f"Network error encountered. Waiting {wait_time:.2f} seconds before retry {retry_state.attempt_number}/{self.max_retries + 1}...")
        elif isinstance(exception, OpenAIAPIError):
            status_code = getattr(exception, 'status_code', None)
            if status_code == 429:
                print(f"Rate limit error (429) encountered. Waiting {wait_time:.2f} seconds before retry {retry_state.attempt_number}/{self.max_retries + 1}...")
            elif status_code and 500 <= status_code < 600:
                print(f"Server error ({status_code}) encountered. Waiting {wait_time:.2f} seconds before retry {retry_state.attempt_number}/{self.max_retries + 1}...")
    
    async def _handle_streaming_response(self, response) -> StreamingResponse:
        """
        Handle OpenAI streaming response
        
        :param response: OpenAI streaming response object
        :return: StreamingResponse object
        """
        usage = None
        
        async def stream_generator() -> AsyncIterator[str]:
            nonlocal usage
            async for chunk in response:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content

                if hasattr(chunk, 'usage'):
                    usage = TokenUsage(
                        prompt_tokens=chunk.usage["prompt_tokens"],
                        completion_tokens=chunk.usage["completion_tokens"],
                        total_tokens=chunk.usage["total_tokens"]
                    )


        async def get_usage():
            return usage
        
        return StreamingResponse(stream_generator(), usage_getter=get_usage)
    
    async def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = "auto",
        temperature: float = 0.6,
        **kwargs
    ):
        """
        Generate response with tools support, returns raw OpenAI response object
        This method includes automatic rate limit handling and exponential backoff
        
        :param messages: Message list
        :param tools: List of tool schemas (optional)
        :param tool_choice: Tool choice parameter (default: "auto")
        :param temperature: Temperature parameter
        :param kwargs: Additional parameters to pass to API
        :return: Raw OpenAI response object (for accessing tool_calls, etc.)
        """
        async def _generate_with_tools_impl():
            """Internal implementation of generate_with_tools"""
            # Build request parameters
            request_params = {
                'model': self.model,
                'messages': messages,
                'temperature': temperature,
                **kwargs
            }
            
            # Add tools if provided
            if tools is not None:
                request_params['tools'] = tools
            if tool_choice is not None:
                request_params['tool_choice'] = tool_choice
            
            response = await self.client.chat.completions.create(**request_params)
            return response
        
        # Apply retry decorator
        retry_decorator = self._get_retry_decorator()
        decorated_func = retry_decorator(_generate_with_tools_impl)
        
        try:
            return await decorated_func()
        except (APIConnectionError, OpenAIAPIError) as e:
            # Convert OpenAI errors to our custom exceptions
            raise _convert_openai_error(e) from e
        except Exception as e:
            raise APIError(f"Unexpected error: {str(e)}") from e


