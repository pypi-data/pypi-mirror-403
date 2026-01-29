"""Write Tool - Write File"""
import json
import re
from typing import Dict, Any
from pathlib import Path
from ..base import Tool


class WriteTool(Tool):
    """Write file tool"""
    
    # Patterns for blocking code that should be commented out
    # Format: (pattern, description)
    BLOCKING_PATTERNS = [
        (r'plt\.show\(\)', 'plt.show()'),
        (r'matplotlib\.pyplot\.show\(\)', 'matplotlib.pyplot.show()'),
        (r'input\(', 'input()'),
        (r'raw_input\(', 'raw_input()'),
    ]
    
    def __init__(self, session, allow_overwrite: bool = True):
        """
        Initialize write tool
        
        :param session: Session instance
        :param allow_overwrite: Whether to allow overwriting existing files
        """
        super().__init__(session)
        self.allow_overwrite = allow_overwrite
    
    def _remove_blocking_code(self, content: str) -> tuple[str, list[str]]:
        """
        Remove or comment out blocking code patterns
        
        :param content: Original content
        :return: Tuple of (processed_content, warnings)
        """
        warnings = []
        processed_content = content
        lines = processed_content.split('\n')
        modified_lines = []
        
        for line in lines:
            original_line = line
            modified_line = line
            
            # Check each pattern
            for pattern, description in self.BLOCKING_PATTERNS:
                if re.search(pattern, line):
                    # Check if already commented
                    stripped = line.strip()
                    if not stripped.startswith('#'):
                        # Comment out the entire line
                        # Find indentation
                        indent = len(line) - len(line.lstrip())
                        # Comment out the line, preserving original content
                        modified_line = ' ' * indent + '# ' + stripped + '  # Commented out to prevent blocking'
                        warnings.append(f"Commented out blocking code: {description}")
                        break  # Only process first match per line
            
            modified_lines.append(modified_line)
        
        processed_content = '\n'.join(modified_lines)
        return processed_content, warnings
    
    @property
    def name(self) -> str:
        return "Write"
    
    @property
    def description(self) -> str:
        return "Write file content. Can create new files or overwrite existing files (if allowed)."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["file_path", "content"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute write file
        
        :param kwargs: Contains file_path and content
        :return: JSON formatted execution result
        """
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        
        if not file_path:
            return json.dumps({
                "error": "file_path parameter is required"
            })
        if content is None:
            return json.dumps({
                "error": "content parameter is required"
            })
        
        try:
            # Validate path
            resolved_path = self.session.validate_path(file_path)
            
            # Check if file already exists, overwrite not allowed
            if resolved_path.exists() and not self.allow_overwrite:
                return json.dumps({
                    "error": f"File '{resolved_path}' already exists and overwrite is not allowed"
                })
            
            # Only process blocking code for Python files
            warnings = []
            if resolved_path.suffix.lower() == '.py':
                # Remove blocking code (e.g., plt.show()) to prevent program hanging
                processed_content, warnings = self._remove_blocking_code(content)
            else:
                # For non-Python files, use content as-is
                processed_content = content
            
            # Write file
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            # Calculate actual bytes written
            bytes_written = len(processed_content.encode('utf-8'))
            
            result = {
                "message": f"Successfully wrote to file '{resolved_path}'",
                "bytes_written": bytes_written,
                "file_path": str(resolved_path)
            }
            
            # Add warnings if blocking code was found and removed
            if warnings:
                result["warnings"] = warnings
                result["note"] = "Some blocking code (e.g., plt.show()) was automatically commented out to prevent program hanging"
            
            return json.dumps(result)
        
        except ValueError as e:
            return json.dumps({
                "error": str(e)
            })
        except Exception as e:
            return json.dumps({
                "error": f"Failed to write file '{file_path}': {str(e)}"
            })

