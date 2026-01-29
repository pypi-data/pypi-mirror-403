"""Image Edit Tool - Edit images using Banana Image Client"""
import json
from typing import Dict, Any, Optional
from pathlib import Path
from ..base import Tool


class ImageEditTool(Tool):
    """Image editing tool using Banana Image Client"""
    
    @property
    def name(self) -> str:
        return "ImageEdit"
    
    @property
    def description(self) -> str:
        return "Edit an image using AI based on a text prompt. Requires Banana Image Client to be configured in the session."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "The absolute path to the input image file to edit"
                },
                "prompt": {
                    "type": "string",
                    "description": "Text prompt describing the desired image edit (e.g., 'add a sunset in the background', 'remove the person on the left', 'change the color to blue')"
                },
                "output_path": {
                    "type": "string",
                    "description": "Optional. The absolute path where the edited image should be saved. If not provided, the edited image will be saved next to the input image with '_edited' suffix."
                }
            },
            "required": ["image_path", "prompt"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute image edit
        
        :param kwargs: Contains image_path, prompt, output_path (optional)
        :return: JSON formatted result
        """
        image_path = kwargs.get("image_path")
        prompt = kwargs.get("prompt")
        output_path = kwargs.get("output_path")
        
        if not image_path:
            return json.dumps({
                "error": "image_path parameter is required"
            })
        
        if not prompt:
            return json.dumps({
                "error": "prompt parameter is required"
            })
        
        # Check if image_client is available
        if not self.session.image_client:
            return json.dumps({
                "error": "Image editing is not available. BananaImageClient is not configured in the session."
            })
        
        try:
            # Validate input image path
            resolved_input_path = self.session.validate_path(image_path)
            
            # Check if file exists
            if not resolved_input_path.exists():
                return json.dumps({
                    "error": f"Image file '{resolved_input_path}' does not exist"
                })
            
            if not resolved_input_path.is_file():
                return json.dumps({
                    "error": f"'{resolved_input_path}' is not a file"
                })
            
            # Determine output path
            if output_path:
                resolved_output_path = self.session.validate_path(output_path)
            else:
                # Default: save next to input with '_edited' suffix
                stem = resolved_input_path.stem
                suffix = resolved_input_path.suffix
                resolved_output_path = resolved_input_path.parent / f"{stem}_edited{suffix}"
            
            # Call Banana Image Client to edit the image
            edited_image = await self.session.image_client.edit_image(
                prompt=prompt,
                image_path=resolved_input_path,
                output_path=resolved_output_path
            )
            
            return json.dumps({
                "success": True,
                "input_path": str(resolved_input_path),
                "output_path": str(resolved_output_path),
                "message": f"Image edited successfully and saved to '{resolved_output_path}'"
            }, ensure_ascii=False)
        
        except ValueError as e:
            return json.dumps({
                "error": str(e)
            })
        except Exception as e:
            return json.dumps({
                "error": f"Failed to edit image: {str(e)}"
            })

