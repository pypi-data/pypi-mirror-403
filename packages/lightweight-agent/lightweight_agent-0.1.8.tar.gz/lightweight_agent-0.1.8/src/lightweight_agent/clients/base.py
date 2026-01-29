"""Base Client Abstract Class"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Union, List, Dict, Any

from ..models import GenerateResponse, StreamingResponse


class BaseClient(ABC):
    """LLM client abstract base class"""
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        **kwargs
    ) -> Union[GenerateResponse, StreamingResponse]:
        """
        Generate response
        
        :param messages: List[Dict[str, Any]]
        :param stream: Whether to stream response
        :param kwargs: Other parameters
        :return: StreamingResponse for streaming, GenerateResponse for non-streaming
        """
        pass
    
