"""TODO-based Agent - Agent that uses TODO list for task planning"""
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from .react_agent import ReActAgent
from .prompt_builder import build_todo_based_system_prompt
from ..clients.base import BaseClient
from ..tools.builtin import CreateTodoListTool, UpdateTodoStatusTool, SaveImportantArtifactsTool

if TYPE_CHECKING:
    from ..clients.banana_image_client import BananaImageClient


class TodoBasedAgent(ReActAgent):
    """TODO-based Agent that extends ReActAgent with TODO list management"""
    
    def __init__(
        self,
        client: BaseClient,
        working_dir: Optional[str],
        allowed_paths: Optional[List[str]] = None,
        blocked_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        vision_client: Optional[BaseClient] = None,
        image_client: Optional["BananaImageClient"] = None
    ):
        """
        Initialize TODO-based Agent
        
        :param client: LLM client instance
        :param working_dir: Default working directory (optional)
        :param allowed_paths: List of allowed paths
        :param blocked_paths: List of blocked paths
        :param session_id: Session ID (optional, auto-generated UUID if not provided)
        :param system_prompt: Custom system prompt (optional)
        :param vision_client: Optional separate client for vision tools (if not provided, vision tools will not be available)
        :param image_client: Optional BananaImageClient for image editing (if not provided, image editing is not available)
        """
        # Initialize parent ReActAgent (without system_prompt first)
        super().__init__(
            client=client,
            working_dir=working_dir,
            allowed_paths=allowed_paths,
            blocked_paths=blocked_paths,
            session_id=session_id,
            system_prompt=None,  # We'll set it after registering TODO tools
            vision_client=vision_client,
            image_client=image_client
        )
        
        # Register TODO tools
        self._register_todo_tools()
        
        # Build TODO-based system prompt with all tools (including TODO tools)
        if system_prompt is None:
            self.system_prompt = build_todo_based_system_prompt(
                session=self.session,
                tools=self._tool_registry.get_all()
            )
        else:
            self.system_prompt = system_prompt
    
    def _register_todo_tools(self) -> None:
        """
        Register additional TODO-related tools.
        
        Note: This method registers TODO-specific tools in addition to the default tools
        already registered by ReActAgent (ReadTool, WriteTool, EditTool, ListDirTool, RunPythonFileTool).
        The TodoBasedAgent has access to all 8 tools total (5 default + 3 TODO tools).
        """
        todo_tools = [
            CreateTodoListTool(self.session),
            UpdateTodoStatusTool(self.session),
            SaveImportantArtifactsTool(self.session)
        ]
        for tool in todo_tools:
            self._tool_registry.register(tool)
    
    def get_todo_list(self) -> List[dict]:
        """
        Get current TODO list for this session
        
        :return: List of TODO items
        """
        session_id = self.session.get_session_id()
        return CreateTodoListTool.get_todo_list(session_id)
    
    def is_all_todos_completed(self) -> bool:
        """
        Check if all TODO items are completed
        
        :return: True if all items are completed, False otherwise
        """
        todo_list = self.get_todo_list()
        if not todo_list:
            return False
        
        return all(item["status"] == "completed" for item in todo_list)
    
    def get_todo_summary(self) -> dict:
        """
        Get TODO list summary
        
        :return: Dictionary with TODO statistics
        """
        todo_list = self.get_todo_list()
        if not todo_list:
            return {
                "total": 0,
                "pending": 0,
                "in_progress": 0,
                "completed": 0,
                "failed": 0,
                "all_completed": False
            }
        
        status_counts = {
            "pending": sum(1 for item in todo_list if item["status"] == "pending"),
            "in_progress": sum(1 for item in todo_list if item["status"] == "in_progress"),
            "completed": sum(1 for item in todo_list if item["status"] == "completed"),
            "failed": sum(1 for item in todo_list if item["status"] == "failed")
        }
        
        return {
            "total": len(todo_list),
            **status_counts,
            "all_completed": status_counts["completed"] == len(todo_list)
        }
    
    def get_artifacts(self) -> List[Dict[str, Any]]:
        """
        Get saved artifacts for this session
        
        :return: List of artifacts
        """
        session_id = self.session.get_session_id()
        return SaveImportantArtifactsTool.get_artifacts(session_id)
    
    def get_delivery_summary(self) -> Dict[str, Any]:
        """
        Get delivery summary for this session
        
        :return: Delivery summary dictionary
        """
        session_id = self.session.get_session_id()
        return SaveImportantArtifactsTool.get_delivery_summary(session_id)

