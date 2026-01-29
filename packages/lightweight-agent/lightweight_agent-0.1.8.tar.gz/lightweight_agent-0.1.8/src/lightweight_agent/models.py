"""Response Model Definitions"""
from dataclasses import dataclass
from typing import Optional, AsyncIterator


@dataclass
class TokenUsage:
    """Token usage statistics"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
    
    def __str__(self) -> str:
        return (
            f"TokenUsage(prompt={self.prompt_tokens}, "
            f"completion={self.completion_tokens}, "
            f"total={self.total_tokens})"
        )


@dataclass
class GenerateResponse:
    """Generate response result"""
    content: str
    usage: Optional[TokenUsage] = None
    
    def __str__(self) -> str:
        """String representation"""
        return self.content


class StreamingResponse:
    """Streaming response wrapper, supports getting token usage information when stream ends"""
    
    def __init__(self, stream: AsyncIterator[str], usage_getter=None):
        """
        Initialize streaming response
        
        :param stream: Async iterator
        :param usage_getter: Async callback function to get usage information (optional)
        """
        self._stream = stream
        self._usage_getter = usage_getter
        self._usage: Optional[TokenUsage] = None
        self._consumed = False
    
    def __aiter__(self):
        return self
    
    async def __anext__(self) -> str:
        try:
            chunk = await self._stream.__anext__()
            return chunk
        except StopAsyncIteration:
            if self._usage_getter and self._usage is None:
                try:
                    self._usage = await self._usage_getter()
                except Exception:
                    pass
            self._consumed = True
            raise
    
    @property
    def usage(self) -> Optional[TokenUsage]:
        return self._usage
    
    async def get_usage(self) -> Optional[TokenUsage]:
        if not self._consumed:
            try:
                async for _ in self:
                    pass
            except StopAsyncIteration:
                pass
            self._consumed = True
        return self._usage

