"""Tool Base Class"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..session.session import Session


class Tool(ABC):
    """Tool base class"""
    
    def __init__(self, session: Session):
        """
        Initialize Tool
        
        :param session: Session instance (for permission control)
        """
        self.session = session
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (unique identifier)"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description (for function calling)"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        Tool parameter definition (JSON Schema format)
        
        Example:
        {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "File path"
                }
            },
            "required": ["file_path"]
        }
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """
        Execute tool
        
        :param kwargs: Tool parameters
        :return: Execution result (string)
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get Tool's function calling schema
        
        :return: Function calling schema dictionary
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

