"""BibTeX Extract Tool - Extract BibTeX entries from text files"""
import json
from typing import Dict, Any
from ...base import Tool
from .citaion_engine import BibTeXManager


class BibTeXExtractTool(Tool):
    """Tool for extracting BibTeX entries from text files"""
    
    def __init__(self, session):
        """
        Initialize BibTeX Extract Tool
        
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
        return "bibtex_extract"
    
    @property
    def description(self) -> str:
        return """Extract BibTeX entries from a text file. The extracted entries are stored in memory and can be used by other BibTeX tools (insert, save) in the same session. Duplicate entries (based on cite key) are automatically removed, keeping only the first occurrence."""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_file": {
                    "type": "string",
                    "description": "Path to the text file containing BibTeX entries"
                }
            },
            "required": ["input_file"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Extract BibTeX entries from file
        
        :param kwargs: Contains input_file
        :return: JSON formatted execution result
        """
        input_file = kwargs.get("input_file")
        
        if not input_file:
            return json.dumps({
                "error": "input_file parameter is required"
            }, ensure_ascii=False)
        
        try:
            # Validate path
            resolved_input_path = self.session.validate_path(input_file)
            
            if not resolved_input_path.exists():
                return json.dumps({
                    "error": f"File '{resolved_input_path}' does not exist"
                }, ensure_ascii=False)
            
            if not resolved_input_path.is_file():
                return json.dumps({
                    "error": f"'{resolved_input_path}' is not a file"
                }, ensure_ascii=False)
            
            # Extract entries using BibTeXManager
            bib_list = self._manager.extract_bib_entries(str(resolved_input_path))
            
            return json.dumps({
                "message": f"Successfully extracted {len(bib_list)} BibTeX entries",
                "count": len(bib_list),
                "cite_keys": self._manager.cite_keys,
                "bib_entries": bib_list
            }, ensure_ascii=False)
        
        except ValueError as e:
            return json.dumps({
                "error": str(e)
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to extract BibTeX entries: {str(e)}"
            }, ensure_ascii=False)

