"""Read Tool - Read File"""
import json
from typing import Dict, Any, Optional
from ..base import Tool


class ReadTool(Tool):
    """Read file tool"""
    
    @property
    def name(self) -> str:
        return "Read"
    
    @property
    def description(self) -> str:
        return "Read file content. Can read text file contents, supports specifying start line and line limit."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to read"
                },
                "offset": {
                    "type": "integer",
                    "description": "The line number to start reading from (1-based, default: 1)",
                    "default": None
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of lines to read (default: all lines)",
                    "default": None
                }
            },
            "required": ["file_path"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute read file
        
        :param kwargs: Contains file_path, offset, limit
        :return: JSON formatted file content
        """
        file_path = kwargs.get("file_path")
        offset = kwargs.get("offset")
        limit = kwargs.get("limit")
        
        if not file_path:
            return json.dumps({
                "error": "file_path parameter is required"
            })
        
        try:
            # Validate path
            resolved_path = self.session.validate_path(file_path)
            
            # Check if file exists
            if not resolved_path.exists():
                return json.dumps({
                    "error": f"File '{resolved_path}' does not exist"
                })
            
            if not resolved_path.is_file():
                return json.dumps({
                    "error": f"'{resolved_path}' is not a file"
                })
            
            # Read all lines from file
            with open(resolved_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # Process offset and limit
            start_idx = 0
            if offset is not None:
                # offset is 1-based, convert to 0-based index
                start_idx = max(0, offset - 1)
            
            end_idx = total_lines
            if limit is not None:
                end_idx = min(start_idx + limit, total_lines)
            
            # Extract specified range of lines
            selected_lines = lines[start_idx:end_idx]
            lines_returned = len(selected_lines)
            
            # Format content (with line numbers)
            content_parts = []
            for i, line in enumerate(selected_lines, start=start_idx + 1):
                content_parts.append(f"{i}:{line.rstrip()}")
            
            content = "\n".join(content_parts) if content_parts else ""
            
            return json.dumps({
                "content": content,
                "total_lines": total_lines,
                "lines_returned": lines_returned
            }, ensure_ascii=False)
        
        except ValueError as e:
            return json.dumps({
                "error": str(e)
            })
        except UnicodeDecodeError:
            return json.dumps({
                "error": f"File '{file_path}' is not a text file or contains invalid encoding"
            })
        except Exception as e:
            return json.dumps({
                "error": f"Failed to read file '{file_path}': {str(e)}"
            })

