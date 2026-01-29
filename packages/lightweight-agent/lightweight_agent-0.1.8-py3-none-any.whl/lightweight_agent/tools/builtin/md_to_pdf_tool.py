"""Markdown to PDF Tool - Convert Markdown files to PDF"""
import json
from typing import Dict, Any
from markdown_pdf import MarkdownPdf, Section
from ..base import Tool


class MdToPdfTool(Tool):
    """Markdown to PDF conversion tool"""
    
    @property
    def name(self) -> str:
        return "md_to_pdf"
    
    @property
    def description(self) -> str:
        return "Convert a Markdown file to PDF format. Reads the Markdown content from a file and generates a PDF document."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "markdown_path": {
                    "type": "string",
                    "description": "The absolute path to the input Markdown file"
                },
                "output_path": {
                    "type": "string",
                    "description": "The absolute path to the output PDF file. If not provided, will use the same name as the input file with .pdf extension"
                }
            },
            "required": ["markdown_path"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute Markdown to PDF conversion
        
        :param kwargs: Contains markdown_path and optional output_path
        :return: JSON formatted execution result
        """
        markdown_path = kwargs.get("markdown_path")
        output_path = kwargs.get("output_path")
        
        if not markdown_path:
            return json.dumps({
                "error": "markdown_path parameter is required"
            })
        
        try:
            # Validate and resolve markdown file path
            resolved_md_path = self.session.validate_path(markdown_path)
            
            if not resolved_md_path.exists():
                return json.dumps({
                    "error": f"Markdown file '{resolved_md_path}' does not exist"
                })
            
            if not resolved_md_path.is_file():
                return json.dumps({
                    "error": f"'{resolved_md_path}' is not a file"
                })
            
            # Determine output path
            if output_path:
                resolved_output_path = self.session.validate_path(output_path)
            else:
                # Use same directory and name as input file, but with .pdf extension
                resolved_output_path = resolved_md_path.parent / f"{resolved_md_path.stem}.pdf"
            
            # Ensure output directory exists
            resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read Markdown content
            with open(resolved_md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
            
            # Create PDF from Markdown
            pdf = MarkdownPdf()
            pdf.add_section(Section(md_content))
            pdf.save(str(resolved_output_path))
            
            result = {
                "message": f"Successfully converted Markdown to PDF",
                "input_file": str(resolved_md_path),
                "output_file": str(resolved_output_path)
            }
            
            return json.dumps(result)
        
        except ValueError as e:
            return json.dumps({
                "error": str(e)
            })
        except Exception as e:
            return json.dumps({
                "error": f"Failed to convert Markdown to PDF: {str(e)}"
            })

