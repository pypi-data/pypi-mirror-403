"""Run Python File Tool - Execute Python Script"""
import json
import subprocess
import sys
from typing import Dict, Any
from pathlib import Path
from ..base import Tool


class RunPythonFileTool(Tool):
    """Run Python file tool"""
    
    @property
    def name(self) -> str:
        return "run_python_file"
    
    @property
    def description(self) -> str:
        return "Execute a Python script from a file in the working directory. The script will be run with the current Python interpreter."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file": {
                    "type": "string",
                    "description": "The path to the Python file to execute (relative to working directory or absolute path)"
                }
            },
            "required": ["file"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute Python file
        
        :param kwargs: Contains file
        :return: JSON formatted execution result
        """
        file_path = kwargs.get("file")
        
        if not file_path:
            return json.dumps({
                "error": "file parameter is required"
            }, ensure_ascii=False)
        
        try:
            # Validate path
            resolved_path = self.session.validate_path(file_path)
            
            # Check if file exists
            if not resolved_path.exists():
                return json.dumps({
                    "error": f"File '{resolved_path}' does not exist"
                }, ensure_ascii=False)
            
            if not resolved_path.is_file():
                return json.dumps({
                    "error": f"'{resolved_path}' is not a file"
                }, ensure_ascii=False)
            
            # Check if it's a Python file
            if resolved_path.suffix != '.py':
                return json.dumps({
                    "error": f"'{resolved_path}' is not a Python file (.py)"
                }, ensure_ascii=False)
            
            # Execute Python script
            # Use the current Python interpreter
            python_executable = sys.executable
            
            # Change to the file's directory for execution context
            script_dir = resolved_path.parent
            script_file = resolved_path.name
            
            # Run the script
            result = subprocess.run(
                [python_executable, script_file],
                cwd=str(script_dir),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Prepare result
            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
            
            # Format output message
            if result.returncode == 0:
                message = "Script executed successfully"
                if result.stdout:
                    message += f"\n\nOutput:\n{result.stdout}"
            else:
                message = f"Script execution failed with return code {result.returncode}"
                if result.stderr:
                    message += f"\n\nError:\n{result.stderr}"
                if result.stdout:
                    message += f"\n\nOutput:\n{result.stdout}"
            
            output["message"] = message
            
            return json.dumps(output, ensure_ascii=False)
        
        except subprocess.TimeoutExpired:
            return json.dumps({
                "error": f"Script execution timed out after 5 minutes",
                "success": False
            }, ensure_ascii=False)
        except ValueError as e:
            return json.dumps({
                "error": str(e)
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to execute Python file '{file_path}': {str(e)}",
                "success": False
            }, ensure_ascii=False)

