"""Tool Registry"""
from typing import Dict, List, Optional
from .base import Tool


class ToolRegistry:
    """Tool registry, manages all available tools"""
    
    def __init__(self):
        """Initialize Tool registry"""
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """
        Register a tool
        
        :param tool: Tool instance
        :raises ValueError: If tool name already exists
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> None:
        """
        Unregister a tool
        
        :param name: Tool name
        """
        if name in self._tools:
            del self._tools[name]
    
    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool
        
        :param name: Tool name
        :return: Tool instance, None if not found
        """
        return self._tools.get(name)
    
    def get_all(self) -> List[Tool]:
        """
        Get all tools
        
        :return: List of tools
        """
        return list(self._tools.values())
    
    def get_schemas(self) -> List[Dict]:
        """
        Get function calling schemas for all tools
        
        :return: List of schemas
        """
        return [tool.get_schema() for tool in self._tools.values()]
    
    def __contains__(self, name: str) -> bool:
        """Check if tool is registered"""
        return name in self._tools
    
    def __len__(self) -> int:
        """Return number of tools"""
        return len(self._tools)

