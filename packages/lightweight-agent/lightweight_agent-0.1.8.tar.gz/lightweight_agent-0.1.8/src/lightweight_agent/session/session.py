"""Session Core Class"""
import os
import platform
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from ..clients.base import BaseClient
from ..models import TokenUsage
from .history import MessageHistory

if TYPE_CHECKING:
    from ..clients.banana_image_client import BananaImageClient


class Session:
    """Session management class, controls working directory, configuration, history, etc."""
    
    def __init__(
        self,
        working_dir: str,
        client: BaseClient,
        llm_config: Optional[Dict[str, Any]] = None,
        allowed_paths: Optional[List[str]] = None,
        blocked_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        vision_client: Optional[BaseClient] = None,
        image_client: Optional["BananaImageClient"] = None
    ):
        """
        Initialize Session
        
        :param working_dir: Working directory path (must be absolute path)
        :param client: LLM client instance
        :param llm_config: LLM configuration (temperature, max_tokens, etc.)
        :param allowed_paths: List of allowed paths (optional, None=only working directory, each path in the list must be absolute. Note: working directory is always allowed, no need to add to the list)
        :param blocked_paths: List of blocked paths (optional, each path in the list must be absolute)
        :param session_id: Session ID (optional, auto-generated UUID if not provided)
        :param vision_client: Optional separate client for vision tools (if not provided, vision tools will not be available)
        :param image_client: Optional BananaImageClient for image editing (if not provided, image editing is not available)
        :raises ValueError: If paths in working_dir, allowed_paths, or blocked_paths are not absolute paths
        """
        if not os.path.isabs(working_dir):
            raise ValueError(f"working_dir must be an absolute path, got: {working_dir}")
        
        self.working_dir = Path(working_dir).resolve()
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = client
        self.vision_client = vision_client  # Can be None - no fallback to client
        self.image_client = image_client
        
        if allowed_paths:
            for p in allowed_paths:
                if not os.path.isabs(p):
                    raise ValueError(f"allowed_paths must contain only absolute paths, got: {p}")
            self.allowed_paths = [Path(p).resolve() for p in allowed_paths]
        else:
            self.allowed_paths = []
        
        if blocked_paths:
            for p in blocked_paths:
                if not os.path.isabs(p):
                    raise ValueError(f"blocked_paths must contain only absolute paths, got: {p}")
            self.blocked_paths = [Path(p).resolve() for p in blocked_paths]
        else:
            self.blocked_paths = []
        
        self.history = MessageHistory()
        self.total_token_usage = TokenUsage()
        self.session_id = session_id if session_id else str(uuid.uuid4())
        
        self._os_name = platform.system()
        self._os_release = platform.release()
        self._os_version = platform.version()
        self._created_at = datetime.now()

    def get_session_id(self):
        return self.session_id
    
    def get_system_info(self) -> Dict[str, str]:
        """
        Get system information
        
        :return: Dictionary containing system information
        """
        return {
            "os_name": self._os_name,
            "os_release": self._os_release,
            "os_version": self._os_version,
            "created_at": self._created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def validate_path(self, path: str) -> Path:
        """
        Validate and resolve path, mainly used for tool calls
        
        :param path: Path (must be absolute path)
        :return: Resolved absolute path
        :raises ValueError: If path is not absolute, invalid, or blocked
        """
        if not os.path.isabs(path):
            raise ValueError(f"path must be an absolute path, got: {path}")
        
        resolved_path = Path(path).resolve()
        
        for blocked in self.blocked_paths:
            if resolved_path.is_relative_to(blocked):
                raise ValueError(f"Access to path '{resolved_path}' is blocked")

        if resolved_path.is_relative_to(self.working_dir):
            return resolved_path

        if self.allowed_paths:
            for allowed_path in self.allowed_paths:
                try:
                    if resolved_path.is_relative_to(allowed_path):
                        return resolved_path
                except (ValueError, AttributeError):
                    if str(resolved_path).startswith(str(allowed_path)):
                        return resolved_path
            raise ValueError(f"Access to path '{resolved_path}' is not allowed")
        else:
            raise ValueError(f"Path '{resolved_path}' is outside working directory '{self.working_dir}'")

    
    def add_message(
        self,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None
    ) -> None:
        """
        Add message to history
        
        :param role: Message role
        :param content: Message content
        :param tool_calls: Tool calls (only for assistant messages)
        :param tool_call_id: Tool call ID (only for tool messages)
        """
        self.history.add(role, content, tool_calls, tool_call_id)
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Get formatted message list (for API calls)
        
        :return: List of message dictionaries
        """
        return self.history.get_formatted()
    
    def update_token_usage(self, usage: TokenUsage) -> None:
        """
        Update cumulative token usage
        
        :param usage: Token usage information
        """
        self.total_token_usage.prompt_tokens += usage.prompt_tokens
        self.total_token_usage.completion_tokens += usage.completion_tokens
        self.total_token_usage.total_tokens += usage.total_tokens
    
    def clear_history(self) -> None:
        """Clear conversation history (keep system messages)"""
        self.history.clear(keep_system=True)

