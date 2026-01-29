"""List Directory Tool - List Directory Contents"""
from typing import Dict, Any, Optional
from pathlib import Path
from ..base import Tool


class ListDirTool(Tool):
    """List directory contents tool"""
    
    @property
    def name(self) -> str:
        return "list_directory"
    
    @property
    def description(self) -> str:
        return "List files and subdirectories in a directory. Can list recursively or only current directory level. Can view contents of specified directory."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "dir_path": {
                    "type": "string",
                    "description": "The path to the directory to list (relative to working directory or absolute path)"
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Whether to show hidden files (files starting with .)",
                    "default": False
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to recursively list all subdirectories and their contents",
                    "default": True
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth for recursive listing (None for unlimited, 0 for current directory only, 1 for current + 1 level, etc.)",
                    "default": None
                }
            },
            "required": ["dir_path"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute list directory
        
        :param kwargs: Contains dir_path, show_hidden, recursive, and max_depth
        :return: Directory contents list
        """
        dir_path = kwargs.get("dir_path")
        show_hidden = kwargs.get("show_hidden", False)
        recursive = kwargs.get("recursive", True)
        max_depth = kwargs.get("max_depth", None)
        
        if not dir_path:
            return f"Error: dir_path parameter is required"
        
        try:
            # Validate path
            resolved_path = self.session.validate_path(dir_path)
            
            # Check if path exists
            if not resolved_path.exists():
                return f"Error: Directory '{resolved_path}' does not exist"
            
            if not resolved_path.is_dir():
                return f"Error: '{resolved_path}' is not a directory"
            
            # List directory contents
            if recursive:
                items = self._list_recursive(resolved_path, resolved_path, show_hidden, max_depth, 0)
            else:
                items = []
                for item in sorted(resolved_path.iterdir()):
                    # Filter hidden files
                    if not show_hidden and item.name.startswith('.'):
                        continue
                    
                    if item.is_dir():
                        items.append(f"[DIR]  {item.name}/")
                    else:
                        size = item.stat().st_size
                        size_str = self._format_size(size)
                        items.append(f"[FILE] {item.name} ({size_str})")
            
            if not items:
                return f"Directory '{resolved_path}' is empty"
            
            result = f"Contents of '{resolved_path}'"
            if recursive:
                result += " (recursive"
                if max_depth is not None:
                    result += f", max_depth={max_depth}"
                result += ")"
            result += ":\n\n"
            result += "\n".join(items)
            result += f"\n\nTotal: {len(items)} items"
            
            return result
        
        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error: Failed to list directory '{dir_path}': {str(e)}"
    
    def _list_recursive(self, base_path: Path, current_path: Path, show_hidden: bool, max_depth: Optional[int], current_depth: int) -> list:
        """Recursively list directory contents with depth control"""
        items = []
        
        # Check depth limit
        if max_depth is not None and current_depth > max_depth:
            return items
        
        try:
            for item in sorted(current_path.iterdir()):
                # Filter hidden files
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                # Calculate relative path from base
                try:
                    rel_path = item.relative_to(base_path)
                    display_path = str(rel_path).replace('\\', '/')
                except ValueError:
                    display_path = item.name
                
                if item.is_dir():
                    items.append(f"[DIR]  {display_path}/")
                    # Recursively list subdirectories
                    if max_depth is None or current_depth < max_depth:
                        sub_items = self._list_recursive(base_path, item, show_hidden, max_depth, current_depth + 1)
                        items.extend(sub_items)
                else:
                    size = item.stat().st_size
                    size_str = self._format_size(size)
                    items.append(f"[FILE] {display_path} ({size_str})")
        except PermissionError:
            items.append(f"[ERROR] Permission denied: {current_path}")
        except Exception as e:
            items.append(f"[ERROR] Failed to list '{current_path}': {str(e)}")
        
        return items
    
    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

