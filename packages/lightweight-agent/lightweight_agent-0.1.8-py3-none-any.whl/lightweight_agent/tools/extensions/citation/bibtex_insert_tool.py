"""BibTeX Insert Tool - Insert BibTeX entries into LaTeX files"""
import json
from typing import Dict, Any
from ...base import Tool
from .citaion_engine import BibTeXManager


class BibTeXInsertTool(Tool):
    """Tool for inserting BibTeX entries into LaTeX file citations"""
    
    def __init__(self, session):
        """
        Initialize BibTeX Insert Tool
        
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
        return "bibtex_insert"
    
    @property
    def description(self) -> str:
        return """Insert previously extracted BibTeX entries into LaTeX file citations. The entries are evenly distributed across all \\cite{} or \\citep{} commands in the LaTeX file. You must extract entries first using bibtex_extract tool."""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_file": {
                    "type": "string",
                    "description": "Path to the LaTeX file to insert citations into"
                },
                "output_file": {
                    "type": "string",
                    "description": "Path to save the modified LaTeX file. If not provided, overwrites the input file."
                }
            },
            "required": ["input_file"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Insert BibTeX entries into LaTeX file
        
        :param kwargs: Contains input_file, output_file
        :return: JSON formatted execution result
        """
        input_file = kwargs.get("input_file")
        output_file = kwargs.get("output_file")
        
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
            
            if not self._manager.bib_list:
                return json.dumps({
                    "error": "No BibTeX entries available. Please extract entries first using bibtex_extract tool"
                }, ensure_ascii=False)
            
            # Insert entries using BibTeXManager
            resolved_output_path = None
            if output_file:
                resolved_output_path = self.session.validate_path(output_file)
            
            output_path = str(resolved_output_path) if resolved_output_path else None
            result = self._manager.insert_to_latex(
                latex_file=str(resolved_input_path),
                output_file=output_path
            )
            
            if result is None:
                return json.dumps({
                    "error": "Failed to insert BibTeX entries into LaTeX file"
                }, ensure_ascii=False)
            
            return json.dumps({
                "message": f"Successfully inserted BibTeX entries into LaTeX file",
                "output_file": str(resolved_output_path) if resolved_output_path else str(resolved_input_path),
                "entries_inserted": len(self._manager.cite_keys)
            }, ensure_ascii=False)
        
        except ValueError as e:
            return json.dumps({
                "error": str(e)
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to insert BibTeX entries: {str(e)}"
            }, ensure_ascii=False)

