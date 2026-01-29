"""Save Important Artifacts Tool - Save important artifacts for delivery"""
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..base import Tool


class SaveImportantArtifactsTool(Tool):
    """Save important artifacts tool"""
    
    # Class-level storage for artifacts (shared across all instances)
    _artifacts_storage: Dict[str, List[Dict[str, Any]]] = {}
    # Map session_id to working_dir for persistence
    _session_working_dirs: Dict[str, Path] = {}
    
    def __init__(self, session):
        """
        Initialize SaveImportantArtifactsTool
        
        :param session: Session instance
        """
        super().__init__(session)
        # Register working_dir for this session
        session_id = self.session.get_session_id()
        self._session_working_dirs[session_id] = self.session.working_dir
        # Load existing artifacts from file
        self._load_from_file(session_id)
    
    def _get_persistence_file(self, session_id: str) -> Path:
        """
        Get persistence file path for artifacts
        
        :param session_id: Session ID
        :return: Path to persistence file
        """
        if session_id in self._session_working_dirs:
            working_dir = self._session_working_dirs[session_id]
            return working_dir / ".artifacts.json"
        # Fallback to current session's working_dir
        return self.session.working_dir / ".artifacts.json"
    
    def _load_from_file(self, session_id: str) -> None:
        """
        Load artifacts from persistence file
        
        :param session_id: Session ID
        """
        persistence_file = self._get_persistence_file(session_id)
        if persistence_file.exists():
            try:
                with open(persistence_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Support both old format (list) and new format (dict with session_id)
                    if isinstance(data, list):
                        self._artifacts_storage[session_id] = data
                    elif isinstance(data, dict):
                        # New format: {session_id: artifacts}
                        if session_id in data:
                            self._artifacts_storage[session_id] = data[session_id]
                        else:
                            self._artifacts_storage[session_id] = []
                    else:
                        self._artifacts_storage[session_id] = []
            except Exception:
                # If loading fails, start with empty list
                self._artifacts_storage[session_id] = []
        else:
            self._artifacts_storage[session_id] = []
    
    def _save_to_file(self, session_id: str) -> None:
        """
        Save artifacts to persistence file
        
        :param session_id: Session ID
        """
        persistence_file = self._get_persistence_file(session_id)
        try:
            artifacts = self._artifacts_storage.get(session_id, [])
            # Save as JSON with proper encoding
            with open(persistence_file, 'w', encoding='utf-8') as f:
                json.dump(artifacts, f, ensure_ascii=False, indent=2)
        except Exception:
            # Silently fail if save fails (don't break the tool)
            pass
    
    @property
    def name(self) -> str:
        return "save_important_artifacts"
    
    @property
    def description(self) -> str:
        return """Save important file artifacts that need to be delivered to users after task completion.

Use cases:
- Mark important output files after task completion
- Add metadata (title, description, importance) to final deliverables
- Generate delivery checklist

Notes:
- important_score range: 1-10 (10 means most important)
- Files must be within the working directory
- Files must exist"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "artifacts": {
                    "description": "List of file artifacts to save",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file": {
                                "description": "File path (relative or absolute)",
                                "type": "string"
                            },
                            "title": {
                                "description": "Artifact title",
                                "type": "string"
                            },
                            "important_score": {
                                "description": "Importance score (1-10, 10 is most important)",
                                "type": "integer"
                            },
                            "description": {
                                "description": "Detailed description of the artifact",
                                "type": "string"
                            }
                        },
                        "required": ["file", "title", "important_score", "description"]
                    }
                }
            },
            "required": ["artifacts"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute save important artifacts
        
        :param kwargs: Contains artifacts list
        :return: JSON formatted execution result
        """
        artifacts = kwargs.get("artifacts")
        
        if not artifacts:
            return json.dumps({
                "error": "artifacts parameter is required"
            })
        
        if not isinstance(artifacts, list):
            return json.dumps({
                "error": "artifacts must be a list"
            })
        
        try:
            # Get session ID to associate artifacts with session
            session_id = self.session.get_session_id()
            
            # Initialize artifacts list for this session if not exists
            if session_id not in self._artifacts_storage:
                self._artifacts_storage[session_id] = []
            
            saved_artifacts = []
            errors = []
            
            for artifact in artifacts:
                if not isinstance(artifact, dict):
                    errors.append("Invalid artifact format: must be a dictionary")
                    continue
                
                # Validate required fields
                required_fields = ["file", "title", "important_score", "description"]
                missing_fields = [field for field in required_fields if field not in artifact]
                if missing_fields:
                    errors.append(f"Missing required fields: {', '.join(missing_fields)}")
                    continue
                
                file_path = artifact["file"]
                title = artifact["title"]
                important_score = artifact["important_score"]
                description = artifact["description"]
                
                # Validate important_score
                if not isinstance(important_score, int) or important_score < 1 or important_score > 10:
                    errors.append(f"Invalid important_score for '{file_path}': must be an integer between 1 and 10")
                    continue
                
                # Validate and resolve file path
                try:
                    resolved_path = self.session.validate_path(file_path)
                except ValueError as e:
                    errors.append(f"Invalid file path '{file_path}': {str(e)}")
                    continue
                
                # Check if file exists
                if not resolved_path.exists():
                    errors.append(f"File does not exist: '{resolved_path}'")
                    continue
                
                if not resolved_path.is_file():
                    errors.append(f"Path is not a file: '{resolved_path}'")
                    continue
                
                # Create artifact entry
                artifact_entry = {
                    "id": str(uuid.uuid4()),
                    "file": str(resolved_path),
                    "original_path": file_path,
                    "title": title,
                    "important_score": important_score,
                    "description": description,
                    "saved_at": self.session.get_system_info()["current_time"]
                }
                
                # Add to storage
                self._artifacts_storage[session_id].append(artifact_entry)
                saved_artifacts.append(artifact_entry)
            
            # Sort artifacts by importance score (descending)
            self._artifacts_storage[session_id].sort(key=lambda x: x["important_score"], reverse=True)
            
            # Save to file
            self._save_to_file(session_id)
            
            result = {
                "message": f"Successfully saved {len(saved_artifacts)} artifact(s)",
                "saved_count": len(saved_artifacts),
                "total_artifacts": len(self._artifacts_storage[session_id]),
                "saved_artifacts": saved_artifacts
            }
            
            if errors:
                result["errors"] = errors
                result["warning"] = f"Some artifacts failed to save: {len(errors)} error(s)"
            
            return json.dumps(result, ensure_ascii=False)
        
        except Exception as e:
            return json.dumps({
                "error": f"Failed to save artifacts: {str(e)}"
            })
    
    @classmethod
    def _load_from_file_class(cls, session_id: str) -> None:
        """
        Load artifacts from persistence file (class method version)
        
        :param session_id: Session ID
        """
        if session_id not in cls._session_working_dirs:
            return
        
        working_dir = cls._session_working_dirs[session_id]
        persistence_file = working_dir / ".artifacts.json"
        
        if persistence_file.exists():
            try:
                with open(persistence_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Support both old format (list) and new format (dict with session_id)
                    if isinstance(data, list):
                        cls._artifacts_storage[session_id] = data
                    elif isinstance(data, dict):
                        # New format: {session_id: artifacts}
                        if session_id in data:
                            cls._artifacts_storage[session_id] = data[session_id]
                        else:
                            cls._artifacts_storage[session_id] = []
                    else:
                        cls._artifacts_storage[session_id] = []
            except Exception:
                # If loading fails, start with empty list
                cls._artifacts_storage[session_id] = []
    
    @classmethod
    def _save_to_file_class(cls, session_id: str) -> None:
        """
        Save artifacts to persistence file (class method version)
        
        :param session_id: Session ID
        """
        if session_id not in cls._session_working_dirs:
            return
        
        working_dir = cls._session_working_dirs[session_id]
        persistence_file = working_dir / ".artifacts.json"
        
        try:
            artifacts = cls._artifacts_storage.get(session_id, [])
            # Save as JSON with proper encoding
            with open(persistence_file, 'w', encoding='utf-8') as f:
                json.dump(artifacts, f, ensure_ascii=False, indent=2)
        except Exception:
            # Silently fail if save fails (don't break the tool)
            pass
    
    @classmethod
    def get_artifacts(cls, session_id: str) -> List[Dict[str, Any]]:
        """
        Get artifacts list for a session
        
        :param session_id: Session ID
        :return: List of artifacts
        """
        # Try to load from file if not in memory
        if session_id not in cls._artifacts_storage:
            cls._load_from_file_class(session_id)
        
        if session_id in cls._artifacts_storage:
            return cls._artifacts_storage[session_id].copy()
        return []
    
    @classmethod
    def get_delivery_summary(cls, session_id: str) -> Dict[str, Any]:
        """
        Get delivery summary for a session
        
        :param session_id: Session ID
        :return: Delivery summary dictionary
        """
        artifacts = cls.get_artifacts(session_id)
        
        if not artifacts:
            return {
                "total_artifacts": 0,
                "high_priority": 0,
                "medium_priority": 0,
                "low_priority": 0,
                "artifacts": []
            }
        
        # Categorize by priority
        high_priority = [a for a in artifacts if a["important_score"] >= 8]
        medium_priority = [a for a in artifacts if 5 <= a["important_score"] < 8]
        low_priority = [a for a in artifacts if a["important_score"] < 5]
        
        return {
            "total_artifacts": len(artifacts),
            "high_priority": len(high_priority),
            "medium_priority": len(medium_priority),
            "low_priority": len(low_priority),
            "artifacts": artifacts
        }
    
    @classmethod
    def get_artifact_by_id(cls, session_id: str, artifact_id: str) -> Dict[str, Any]:
        """
        Get a specific artifact by ID
        
        :param session_id: Session ID
        :param artifact_id: Artifact ID
        :return: Artifact dictionary or None
        """
        artifacts = cls.get_artifacts(session_id)
        for artifact in artifacts:
            if artifact["id"] == artifact_id:
                return artifact
        return None
    
    @classmethod
    def clear_artifacts(cls, session_id: str) -> None:
        """
        Clear all artifacts for a session
        
        :param session_id: Session ID
        """
        if session_id in cls._artifacts_storage:
            cls._artifacts_storage[session_id] = []
            # Save empty list to file
            cls._save_to_file_class(session_id)