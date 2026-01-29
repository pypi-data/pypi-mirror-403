"""Batch Edit Tool - Batch Edit File"""
import json
from typing import Dict, Any, List
from ..base import Tool


class BatchEditTool(Tool):
    """Batch edit file tool - supports multiple edits in one call"""
    
    @property
    def name(self) -> str:
        return "BatchEdit"
    
    @property
    def description(self) -> str:
        return "Batch edit file content. Modify multiple locations in a file at once. Each edit is independent - successful edits are saved even if some edits fail."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to modify"
                },
                "edits": {
                    "type": "array",
                    "description": "List of edits to perform",
                    "items": {
                        "type": "object",
                        "properties": {
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
                        "required": ["old_string", "new_string"]
                    },
                    "minItems": 1
                }
            },
            "required": ["file_path", "edits"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute batch edit file
        
        :param kwargs: Contains file_path, edits
        :return: JSON formatted execution result
        """
        file_path = kwargs.get("file_path")
        edits = kwargs.get("edits", [])
        
        if not file_path:
            return json.dumps({
                "error": "file_path parameter is required"
            })
        
        if not edits or not isinstance(edits, list):
            return json.dumps({
                "error": "edits parameter is required and must be a non-empty list"
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
            
            # Process edits from back to front (to avoid line number changes affecting subsequent edits)
            results: List[Dict[str, Any]] = []
            success_count = 0
            fail_count = 0
            
            # Process edits in reverse order (from end to beginning)
            for i, edit in enumerate(reversed(edits)):
                edit_id = edit.get("id", f"edit_{len(edits) - i}")
                old_string = edit.get("old_string")
                new_string = edit.get("new_string")
                replace_all = edit.get("replace_all", False)
                
                if old_string is None or new_string is None:
                    results.append({
                        "id": edit_id,
                        "status": "failed",
                        "error": "old_string and new_string are required"
                    })
                    fail_count += 1
                    continue
                
                try:
                    # Check if old_string exists
                    if old_string not in content:
                        results.append({
                            "id": edit_id,
                            "status": "failed",
                            "error": "The specified text was not found in the file"
                        })
                        fail_count += 1
                        continue
                    
                    # Replace
                    if replace_all:
                        new_content = content.replace(old_string, new_string)
                        replacements = content.count(old_string)
                    else:
                        new_content = content.replace(old_string, new_string, 1)
                        replacements = 1
                    
                    # Update content for next edit
                    content = new_content
                    
                    results.append({
                        "id": edit_id,
                        "status": "success",
                        "replacements": replacements
                    })
                    success_count += 1
                    
                except Exception as e:
                    results.append({
                        "id": edit_id,
                        "status": "failed",
                        "error": str(e)
                    })
                    fail_count += 1
            
            # Reverse results to match original edit order
            results.reverse()
            
            # Write file if at least one edit succeeded
            if success_count > 0:
                with open(resolved_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                status = "success" if fail_count == 0 else "partial_success"
                message = (
                    f"All {success_count} edits succeeded" 
                    if fail_count == 0 
                    else f"{success_count} edits succeeded, {fail_count} edits failed"
                )
                
                return json.dumps({
                    "status": status,
                    "message": message,
                    "success_count": success_count,
                    "fail_count": fail_count,
                    "file_path": str(resolved_path),
                    "results": results
                }, indent=2)
            else:
                # All edits failed, don't write file
                return json.dumps({
                    "status": "failed",
                    "message": "All edits failed",
                    "success_count": 0,
                    "fail_count": fail_count,
                    "file_path": str(resolved_path),
                    "results": results
                }, indent=2)
        
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
                "error": f"Failed to batch edit file '{file_path}': {str(e)}"
            })

