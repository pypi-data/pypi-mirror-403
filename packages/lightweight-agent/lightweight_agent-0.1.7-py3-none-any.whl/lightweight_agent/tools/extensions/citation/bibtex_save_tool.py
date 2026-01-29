"""BibTeX Save Tool - Save BibTeX entries to file"""
import json
from typing import Dict, Any
from ...base import Tool
from .citaion_engine import BibTeXManager


class BibTeXSaveTool(Tool):
    """Tool for saving extracted BibTeX entries to a file"""
    
    def __init__(self, session):
        """
        Initialize BibTeX Save Tool
        
        :param session: Session instance
        """
        super().__init__(session)
        # Use session-level storage to maintain BibTeXManager state per session
        # All BibTeX tools share the same manager instance for the same session
        session_id = session.get_session_id()
        if session_id not in BibTeXManager._shared_managers:
            BibTeXManager._shared_managers[session_id] = BibTeXManager()
        self._manager = BibTeXManager._shared_managers[session_id]
    
    @property
    def name(self) -> str:
        return "bibtex_save"
    
    @property
    def description(self) -> str:
        return """Save previously extracted BibTeX entries to a file. You must extract entries first using bibtex_extract tool."""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output_file": {
                    "type": "string",
                    "description": "Path to save the BibTeX entries file"
                }
            },
            "required": ["output_file"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Save BibTeX entries to file
        
        :param kwargs: Contains output_file
        :return: JSON formatted execution result
        """
        output_file = kwargs.get("output_file")
        
        if not output_file:
            return json.dumps({
                "error": "output_file parameter is required"
            }, ensure_ascii=False)
        
        if not self._manager.bib_list:
            return json.dumps({
                "error": "No BibTeX entries available. Please extract entries first using bibtex_extract tool"
            }, ensure_ascii=False)
        
        try:
            # Validate path
            resolved_output_path = self.session.validate_path(output_file)
            
            # Save entries using BibTeXManager
            success = self._manager.save_bib_list(str(resolved_output_path))
            
            if not success:
                return json.dumps({
                    "error": "Failed to save BibTeX entries to file"
                }, ensure_ascii=False)
            
            return json.dumps({
                "message": f"Successfully saved {len(self._manager.bib_list)} BibTeX entries to file",
                "output_file": str(resolved_output_path),
                "count": len(self._manager.bib_list)
            }, ensure_ascii=False)
        
        except ValueError as e:
            return json.dumps({
                "error": str(e)
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to save BibTeX entries: {str(e)}"
            }, ensure_ascii=False)

