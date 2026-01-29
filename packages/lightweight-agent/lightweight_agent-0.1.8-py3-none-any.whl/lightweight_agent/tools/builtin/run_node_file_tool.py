"""Run Node.js File Tool - Execute Node Script"""
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import Tool


class RunNodeFileTool(Tool):
    """Run a Node.js script with the system node executable."""

    @property
    def name(self) -> str:
        return "run_node_file"

    @property
    def description(self) -> str:
        return (
            "Execute a Node.js script from a file. Useful for workflows that rely on "
            "node-based utilities such as pptx/html conversion scripts."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file": {
                    "type": "string",
                    "description": "Absolute or working-dir-relative path to the Node.js file (.js/.mjs/.cjs).",
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of string arguments passed to the script.",
                },
                "node_path": {
                    "type": "string",
                    "description": "Optional path to the node executable (defaults to 'node' on PATH).",
                },
            },
            "required": ["file"],
        }

    @staticmethod
    def _is_node_file(path: Path) -> bool:
        return path.suffix.lower() in {".js", ".mjs", ".cjs"}

    async def execute(self, **kwargs) -> str:
        file_path = kwargs.get("file")
        args: Optional[List[str]] = kwargs.get("args")
        node_path: Optional[str] = kwargs.get("node_path")

        if not file_path:
            return json.dumps({"error": "file parameter is required"}, ensure_ascii=False)

        try:
            resolved_path = self.session.validate_path(file_path)

            if not resolved_path.exists():
                return json.dumps(
                    {"error": f"File '{resolved_path}' does not exist"}, ensure_ascii=False
                )

            if not resolved_path.is_file():
                return json.dumps(
                    {"error": f"'{resolved_path}' is not a file"}, ensure_ascii=False
                )

            if not self._is_node_file(resolved_path):
                return json.dumps(
                    {
                        "error": (
                            f"'{resolved_path}' is not a Node.js file (.js/.mjs/.cjs required)"
                        )
                    },
                    ensure_ascii=False,
                )

            node_executable = node_path or "node"
            if Path(node_executable).is_file():
                # allow absolute/relative explicit node path
                effective_node = str(Path(node_executable).resolve())
            else:
                found = shutil.which(node_executable)
                if not found:
                    return json.dumps(
                        {
                            "error": (
                                f"Node.js executable '{node_executable}' not found. "
                                "Ensure Node is installed and on PATH, or provide node_path."
                            )
                        },
                        ensure_ascii=False,
                    )
                effective_node = found

            script_dir = resolved_path.parent
            script_file = resolved_path.name

            cmd = [effective_node, script_file]
            if args:
                cmd.extend([str(a) for a in args])

            result = subprocess.run(
                cmd,
                cwd=str(script_dir),
                capture_output=True,
                text=True,
                timeout=300,
            )

            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }

            if result.returncode == 0:
                message = "Node script executed successfully"
                if result.stdout:
                    message += f"\n\nOutput:\n{result.stdout}"
            else:
                message = f"Node script failed with return code {result.returncode}"
                if result.stderr:
                    message += f"\n\nError:\n{result.stderr}"
                if result.stdout:
                    message += f"\n\nOutput:\n{result.stdout}"

            output["message"] = message
            return json.dumps(output, ensure_ascii=False)

        except subprocess.TimeoutExpired:
            return json.dumps(
                {"error": "Node script execution timed out after 5 minutes", "success": False},
                ensure_ascii=False,
            )
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps(
                {"error": f"Failed to execute Node.js file '{file_path}': {str(e)}", "success": False},
                ensure_ascii=False,
            )

