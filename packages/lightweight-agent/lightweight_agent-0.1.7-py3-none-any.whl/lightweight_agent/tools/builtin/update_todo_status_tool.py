"""Update Todo Status Tool - Update TODO item status"""
import json
from typing import Dict, Any
from ..base import Tool
from .create_todo_list_tool import CreateTodoListTool


class UpdateTodoStatusTool(Tool):
    """Update TODO status tool"""
    
    @property
    def name(self) -> str:
        return "update_todo_status"
    
    @property
    def description(self) -> str:
        return "Update the status of a TODO item in the list. Status can be: pending, in_progress, completed, or failed."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "string",
                    "description": "TODO item ID"
                },
                "status": {
                    "type": "string",
                    "description": "New status",
                    "enum": ["pending", "in_progress", "completed", "failed"]
                }
            },
            "required": ["item_id", "status"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute update TODO status
        
        :param kwargs: Contains item_id and status
        :return: JSON formatted execution result
        """
        item_id = kwargs.get("item_id")
        status = kwargs.get("status")
        
        if not item_id:
            return json.dumps({
                "error": "item_id parameter is required"
            })
        
        if not status:
            return json.dumps({
                "error": "status parameter is required"
            })
        
        if status not in ["pending", "in_progress", "completed", "failed"]:
            return json.dumps({
                "error": f"Invalid status '{status}'. Must be one of: pending, in_progress, completed, failed"
            })
        
        try:
            # Get session ID
            session_id = self.session.get_session_id()
            
            # Get TODO list from storage
            todo_item = CreateTodoListTool.get_todo_item(session_id, item_id)
            
            if not todo_item:
                return json.dumps({
                    "error": f"TODO item with ID '{item_id}' not found"
                })
            
            # Update status
            old_status = todo_item["status"]
            todo_item["status"] = status
            
            # Save to file after update
            CreateTodoListTool._save_to_file_class(session_id)
            
            # Get all items to return updated list
            todo_list = CreateTodoListTool.get_todo_list(session_id)
            
            # Count statuses
            status_counts = {
                "pending": sum(1 for item in todo_list if item["status"] == "pending"),
                "in_progress": sum(1 for item in todo_list if item["status"] == "in_progress"),
                "completed": sum(1 for item in todo_list if item["status"] == "completed"),
                "failed": sum(1 for item in todo_list if item["status"] == "failed")
            }
            
            return json.dumps({
                "message": f"Successfully updated TODO item '{item_id}' status from '{old_status}' to '{status}'",
                "item_id": item_id,
                "old_status": old_status,
                "new_status": status,
                "status_summary": status_counts,
                "all_completed": status_counts["completed"] == len(todo_list) and len(todo_list) > 0
            }, ensure_ascii=False)
        
        except Exception as e:
            return json.dumps({
                "error": f"Failed to update TODO status: {str(e)}"
            })

