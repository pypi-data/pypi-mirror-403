"""Create Todo List Tool - Create TODO list for task planning"""
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List
from ..base import Tool


class CreateTodoListTool(Tool):
    """Create TODO list tool"""
    
    # Class-level storage for TODO lists (shared across all instances)
    _todo_storage: Dict[str, Dict[str, Any]] = {}
    # Map session_id to working_dir for persistence
    _session_working_dirs: Dict[str, Path] = {}
    
    def __init__(self, session):
        """
        Initialize CreateTodoListTool
        
        :param session: Session instance
        """
        super().__init__(session)
        # Register working_dir for this session
        session_id = self.session.get_session_id()
        self._session_working_dirs[session_id] = self.session.working_dir
        # Load existing todo list from file
        self._load_from_file(session_id)
    
    def _get_persistence_file(self, session_id: str) -> Path:
        """
        Get persistence file path for todo list
        
        :param session_id: Session ID
        :return: Path to persistence file
        """
        if session_id in self._session_working_dirs:
            working_dir = self._session_working_dirs[session_id]
            return working_dir / ".todo_list.json"
        # Fallback to current session's working_dir
        return self.session.working_dir / ".todo_list.json"
    
    def _load_from_file(self, session_id: str) -> None:
        """
        Load todo list from persistence file
        
        :param session_id: Session ID
        """
        persistence_file = self._get_persistence_file(session_id)
        if persistence_file.exists():
            try:
                with open(persistence_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Support both old format (dict) and new format (dict with session_id)
                    if isinstance(data, dict):
                        if "items" in data:
                            # Old format: direct dict with items
                            self._todo_storage[session_id] = data
                        elif session_id in data:
                            # New format: {session_id: todo_data}
                            self._todo_storage[session_id] = data[session_id]
                        else:
                            self._todo_storage[session_id] = {"items": [], "created_at": None}
                    else:
                        self._todo_storage[session_id] = {"items": [], "created_at": None}
            except Exception:
                # If loading fails, start with empty dict
                self._todo_storage[session_id] = {"items": [], "created_at": None}
        else:
            self._todo_storage[session_id] = {"items": [], "created_at": None}
    
    def _save_to_file(self, session_id: str) -> None:
        """
        Save todo list to persistence file
        
        :param session_id: Session ID
        """
        persistence_file = self._get_persistence_file(session_id)
        try:
            todo_data = self._todo_storage.get(session_id, {"items": [], "created_at": None})
            # Save as JSON with proper encoding
            with open(persistence_file, 'w', encoding='utf-8') as f:
                json.dump(todo_data, f, ensure_ascii=False, indent=2)
        except Exception:
            # Silently fail if save fails (don't break the tool)
            pass
    
    @property
    def name(self) -> str:
        return "create_todo_list"
    
    @property
    def description(self) -> str:
        return "Create a TODO list for task planning and tracking. Used to plan and track task progress."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "todo_items": {
                    "type": "array",
                    "description": "List of TODO items",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "Task description"
                            },
                            "required_tools": {
                                "type": "array",
                                "description": "Tools required to complete this task",
                                "items": {"type": "string"}
                            },
                            "success_criteria": {
                                "type": "string",
                                "description": "Success criteria"
                            }
                        },
                        "required": ["description", "required_tools", "success_criteria"]
                    }
                }
            },
            "required": ["todo_items"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute create TODO list
        
        :param kwargs: Contains todo_items
        :return: JSON formatted execution result
        """
        todo_items = kwargs.get("todo_items")
        
        if not todo_items:
            return json.dumps({
                "error": "todo_items parameter is required"
            })
        
        if not isinstance(todo_items, list):
            return json.dumps({
                "error": "todo_items must be a list"
            })
        
        try:
            # Get session ID to associate TODO list with session
            session_id = self.session.get_session_id()
            
            # Create TODO items with IDs and status
            todo_list = []
            for item in todo_items:
                if not isinstance(item, dict):
                    continue
                
                # Validate required fields
                if "description" not in item or "required_tools" not in item or "success_criteria" not in item:
                    continue
                
                todo_item = {
                    "id": str(uuid.uuid4()),
                    "description": item["description"],
                    "required_tools": item["required_tools"],
                    "success_criteria": item["success_criteria"],
                    "status": "pending"
                }
                todo_list.append(todo_item)
            
            # Store TODO list in session storage
            self._todo_storage[session_id] = {
                "items": todo_list,
                "created_at": self.session.get_system_info()["current_time"]
            }
            
            # Save to file
            self._save_to_file(session_id)
            
            return json.dumps({
                "message": f"Successfully created TODO list with {len(todo_list)} items",
                "todo_list": todo_list,
                "total_items": len(todo_list)
            }, ensure_ascii=False)
        
        except Exception as e:
            return json.dumps({
                "error": f"Failed to create TODO list: {str(e)}"
            })
    
    @classmethod
    def _load_from_file_class(cls, session_id: str) -> None:
        """
        Load todo list from persistence file (class method version)
        
        :param session_id: Session ID
        """
        if session_id not in cls._session_working_dirs:
            return
        
        working_dir = cls._session_working_dirs[session_id]
        persistence_file = working_dir / ".todo_list.json"
        
        if persistence_file.exists():
            try:
                with open(persistence_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Support both old format (dict) and new format (dict with session_id)
                    if isinstance(data, dict):
                        if "items" in data:
                            # Old format: direct dict with items
                            cls._todo_storage[session_id] = data
                        elif session_id in data:
                            # New format: {session_id: todo_data}
                            cls._todo_storage[session_id] = data[session_id]
                        else:
                            cls._todo_storage[session_id] = {"items": [], "created_at": None}
                    else:
                        cls._todo_storage[session_id] = {"items": [], "created_at": None}
            except Exception:
                # If loading fails, start with empty dict
                cls._todo_storage[session_id] = {"items": [], "created_at": None}
    
    @classmethod
    def _save_to_file_class(cls, session_id: str) -> None:
        """
        Save todo list to persistence file (class method version)
        
        :param session_id: Session ID
        """
        if session_id not in cls._session_working_dirs:
            return
        
        working_dir = cls._session_working_dirs[session_id]
        persistence_file = working_dir / ".todo_list.json"
        
        try:
            todo_data = cls._todo_storage.get(session_id, {"items": [], "created_at": None})
            # Save as JSON with proper encoding
            with open(persistence_file, 'w', encoding='utf-8') as f:
                json.dump(todo_data, f, ensure_ascii=False, indent=2)
        except Exception:
            # Silently fail if save fails (don't break the tool)
            pass
    
    @classmethod
    def get_todo_list(cls, session_id: str) -> List[Dict[str, Any]]:
        """
        Get TODO list for a session
        
        :param session_id: Session ID
        :return: List of TODO items
        """
        # Try to load from file if not in memory
        if session_id not in cls._todo_storage:
            cls._load_from_file_class(session_id)
        
        if session_id in cls._todo_storage:
            return cls._todo_storage[session_id].get("items", [])
        return []
    
    @classmethod
    def get_todo_item(cls, session_id: str, item_id: str) -> Dict[str, Any]:
        """
        Get a specific TODO item
        
        :param session_id: Session ID
        :param item_id: TODO item ID
        :return: TODO item dictionary or None
        """
        todo_list = cls.get_todo_list(session_id)
        for item in todo_list:
            if item["id"] == item_id:
                return item
        return None

