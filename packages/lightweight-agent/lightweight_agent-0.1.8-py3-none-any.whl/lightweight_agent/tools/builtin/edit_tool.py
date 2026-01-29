"""Edit Tool - Edit File"""
import json
from typing import Dict, Any
from ..base import Tool


class EditTool(Tool):
    """Edit file tool (based on search_replace)"""
    
    @property
    def name(self) -> str:
        return "Edit"
    
    @property
    def description(self) -> str:
        return "Edit file content. Modify files by finding and replacing specified text fragments."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to modify"
                },
                "old_string": {
                    "type": "string",
                    "description": "The text to replace"
                },
                "new_string": {
                    "type": "string",
                    "description": "The text to replace it with"
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences (default False)",
                    "default": False
                }
            },
            "required": ["file_path", "old_string", "new_string"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute edit file
        
        :param kwargs: Contains file_path, old_string, new_string, replace_all
        :return: JSON formatted execution result
        """
        file_path = kwargs.get("file_path")
        old_string = kwargs.get("old_string")
        new_string = kwargs.get("new_string")
        replace_all = kwargs.get("replace_all", False)
        
        if not file_path:
            return json.dumps({
                "error": "file_path parameter is required"
            })
        if old_string is None:
            return json.dumps({
                "error": "old_string parameter is required"
            })
        if new_string is None:
            return json.dumps({
                "error": "new_string parameter is required"
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
            
            # Read file
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if old_string exists
            if old_string not in content:
                return json.dumps({
                    "error": "The specified text was not found in the file. Please check the exact text including spaces and newlines."
                })
            
            # Replace
            if replace_all:
                new_content = content.replace(old_string, new_string)
                replacements = content.count(old_string)
            else:
                new_content = content.replace(old_string, new_string, 1)
                replacements = 1 if old_string in content else 0
            
            # Write back to file
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return json.dumps({
                "message": f"Successfully edited file '{resolved_path}'",
                "replacements": replacements,
                "file_path": str(resolved_path)
            })
        
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
                "error": f"Failed to edit file '{file_path}': {str(e)}"
            })

