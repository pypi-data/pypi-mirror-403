"""Vision Tool - Analyze images using LLM vision capabilities"""
import json
import logging
from typing import Dict, Any
from pathlib import Path

from ...base import Tool
from ....clients.openai_client import OpenAIClient
from ....utils import create_openai_image_message, create_anthropic_image_message

# Set up logger
logger = logging.getLogger(__name__)

try:
    from ....clients.anthropic_client import AnthropicClient  # type: ignore
except Exception:  # pragma: no cover
    AnthropicClient = None  # type: ignore


class VisionTool(Tool):
    """Tool for analyzing images using LLM vision capabilities"""
    
    def __init__(self, session):
        """
        Initialize Vision Tool
        
        :param session: Session instance
        """
        super().__init__(session)
    
    @property
    def name(self) -> str:
        return "vision_analyze"
    
    @property
    def description(self) -> str:
        return """Analyze images using vision capabilities. This tool can describe image content, extract text from images, identify objects, analyze scenes, and answer questions about images. Supports common image formats (jpg, png, gif, webp)."""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Absolute path to the image file to analyze"
                },
                "prompt": {
                    "type": "string",
                    "description": "Optional prompt describing what to analyze in the image. If not provided, a general description will be generated."
                }
            },
            "required": ["image_path"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Analyze image using LLM vision capabilities
        
        :param kwargs: Contains image_path and optional prompt
        :return: JSON formatted execution result
        """
        image_path = kwargs.get("image_path")
        prompt = kwargs.get("prompt")
        
        logger.info(f"[vision_analyze] Starting image analysis. image_path={image_path}, prompt={'provided' if prompt else 'not provided'}")
        
        if not image_path:
            logger.error("[vision_analyze] Missing image_path parameter")
            return json.dumps({
                "error": "image_path parameter is required"
            }, ensure_ascii=False)
        
        resolved_image_path = None
        file_size = None
        try:
            # Validate path
            logger.debug(f"[vision_analyze] Validating path: {image_path}")
            resolved_image_path = self.session.validate_path(image_path)
            logger.debug(f"[vision_analyze] Resolved path: {resolved_image_path}")
            
            if not resolved_image_path.exists():
                logger.error(f"[vision_analyze] Image file does not exist: {resolved_image_path}")
                return json.dumps({
                    "error": f"Image file '{resolved_image_path}' does not exist"
                }, ensure_ascii=False)
            
            if not resolved_image_path.is_file():
                logger.error(f"[vision_analyze] Path is not a file: {resolved_image_path}")
                return json.dumps({
                    "error": f"'{resolved_image_path}' is not a file"
                }, ensure_ascii=False)
            
            # Check if file is an image
            valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
            file_extension = resolved_image_path.suffix.lower()
            logger.debug(f"[vision_analyze] File extension: {file_extension}")
            
            if file_extension not in valid_extensions:
                logger.error(f"[vision_analyze] Unsupported image format: {file_extension}")
                return json.dumps({
                    "error": f"Unsupported image format. Supported formats: {', '.join(valid_extensions)}"
                }, ensure_ascii=False)
            
            # Check image file size (Anthropic limit is ~5MB, OpenAI limit is ~20MB)
            # We'll use 4MB as a safe limit
            max_size_mb = 4
            max_size_bytes = max_size_mb * 1024 * 1024
            file_size = resolved_image_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            logger.info(f"[vision_analyze] Image file size: {file_size_mb:.2f}MB ({file_size} bytes)")
            
            if file_size > max_size_bytes:
                logger.error(f"[vision_analyze] Image file too large: {file_size_mb:.2f}MB > {max_size_mb}MB")
                return json.dumps({
                    "error": f"Image file too large: {file_size_mb:.2f}MB. Maximum size: {max_size_mb}MB. Please compress or resize the image."
                }, ensure_ascii=False)
            
            # Get client from session - vision_client must be explicitly provided
            client = getattr(self.session, 'vision_client', None)
            if client is None:
                logger.error("[vision_analyze] vision_client is not set. Vision tools require a separate vision_client to be provided.")
                return json.dumps({
                    "error": "vision_client is not configured. Vision tools require a separate vision_client to be provided when initializing the agent/session."
                }, ensure_ascii=False)
            
            # Determine client type and model
            if isinstance(client, OpenAIClient):
                client_type = "OpenAI"
                client_model = getattr(client, 'model', 'unknown')
            elif AnthropicClient is not None and isinstance(client, AnthropicClient):
                client_type = "Anthropic"
                client_model = getattr(client, 'model', 'unknown')
            else:
                client_type = type(client).__name__
                client_model = getattr(client, 'model', 'unknown')
            
            # Determine client type and create appropriate message
            if isinstance(client, OpenAIClient):
                logger.info("[vision_analyze] Using OpenAI client format")
                # OpenAI format
                default_prompt = prompt or "请详细分析这张图片，包括其中的内容、物体、场景和文字（如果有）。"
                logger.debug(f"[vision_analyze] Creating OpenAI image message with prompt length: {len(default_prompt)}")
                
                image_message = create_openai_image_message(
                    image_path=str(resolved_image_path),
                    text=default_prompt
                )
                
                # Log image message details (without full base64 data)
                if image_message.get("content"):
                    for item in image_message["content"]:
                        if item.get("type") == "image_url":
                            image_url = item.get("image_url", {}).get("url", "")
                            if image_url.startswith("data:"):
                                media_type = image_url.split(";")[0].replace("data:", "")
                                base64_length = len(image_url.split(",")[-1]) if "," in image_url else 0
                                logger.info(f"[vision_analyze] Image encoded: media_type={media_type}, base64_length={base64_length} chars")
                
                messages = [
                    {"role": "system", "content": "你是一个专业的图片分析助手，能够详细准确地描述和分析图片内容。"},
                    image_message
                ]
                
                # Call LLM
                logger.info("[vision_analyze] Calling OpenAI API...")
                response = await client.generate(messages, stream=False)
                logger.info(f"[vision_analyze] OpenAI API response received. Content length: {len(response.content) if response.content else 0}")
                
                if response.usage:
                    logger.info(f"[vision_analyze] Token usage: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}, total={response.usage.total_tokens}")
                
                result = {
                    "success": True,
                    "image_path": str(resolved_image_path),
                    # "prompt": default_prompt,
                    "analysis": response.content,
                    # "usage": {
                    #     "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    #     "completion_tokens": response.usage.completion_tokens if response.usage else None,
                    #     "total_tokens": response.usage.total_tokens if response.usage else None
                    # }
                }
                
            elif AnthropicClient is not None and isinstance(client, AnthropicClient):
                logger.info("[vision_analyze] Using Anthropic client format")
                # Anthropic format
                try:
                    default_prompt = prompt or "请详细分析这张图片，包括其中的内容、物体、场景和文字（如果有）。"
                    logger.debug(f"[vision_analyze] Creating Anthropic image message with prompt length: {len(default_prompt)}")
                    
                    image_message = create_anthropic_image_message(
                        image_path=str(resolved_image_path),
                        text=default_prompt
                    )
                    
                    # Log image message details (without full base64 data)
                    if image_message.get("content"):
                        for item in image_message["content"]:
                            if item.get("type") == "image":
                                source = item.get("source", {})
                                media_type = source.get("media_type", "unknown")
                                base64_data = source.get("data", "")
                                base64_length = len(base64_data)
                                logger.info(f"[vision_analyze] Image encoded: media_type={media_type}, base64_length={base64_length} chars, file_extension={file_extension}")
                                
                                # Verify media_type matches file extension
                                expected_types = {
                                    '.jpg': 'image/jpeg',
                                    '.jpeg': 'image/jpeg',
                                    '.png': 'image/png',
                                    '.gif': 'image/gif',
                                    '.webp': 'image/webp'
                                }
                                expected_type = expected_types.get(file_extension)
                                if expected_type and media_type != expected_type:
                                    logger.warning(f"[vision_analyze] Media type mismatch: file extension suggests {expected_type}, but detected {media_type}")
                    
                    system = "你是一个专业的图片分析助手，能够详细准确地描述和分析图片内容。"
                    messages = [image_message]
                    
                    # Log request details (client_model and client_type are already defined above)
                    logger.info(f"[vision_analyze] Calling Anthropic API with model={client_model}, system_prompt_length={len(system)}")
                    logger.debug(f"[vision_analyze] Messages structure: {len(messages)} message(s), content items: {sum(len(m.get('content', [])) for m in messages)}")
                    
                    # Call LLM
                    response = await client.generate(messages, stream=False, system=system)
                    logger.info(f"[vision_analyze] Anthropic API response received. Content length: {len(response.content) if response.content else 0}")
                    
                    if response.usage:
                        logger.info(f"[vision_analyze] Token usage: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}, total={response.usage.total_tokens}")
                    
                    result = {
                        "success": True,
                        "image_path": str(resolved_image_path),
                        # "prompt": default_prompt,
                        "analysis": response.content,
                        # "usage": {
                        #     "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                        #     "completion_tokens": response.usage.completion_tokens if response.usage else None,
                        #     "total_tokens": response.usage.total_tokens if response.usage else None
                        # }
                    }
                except Exception as e:
                    # Provide more detailed error information for Anthropic API errors
                    error_type = type(e).__name__
                    error_msg = str(e)
                    
                    logger.error(f"[vision_analyze] Anthropic API error occurred: {error_type}: {error_msg}")
                    
                    # Try to extract more details from the exception
                    error_details = {
                        "error_type": error_type,
                        "error_message": error_msg
                    }
                    
                    if hasattr(e, '__cause__') and e.__cause__:
                        cause_msg = str(e.__cause__)
                        error_details["cause"] = cause_msg
                        logger.error(f"[vision_analyze] Error cause: {cause_msg}")
                    
                    if hasattr(e, 'response') and hasattr(e.response, 'text'):
                        response_text = e.response.text
                        error_details["api_response"] = response_text
                        logger.error(f"[vision_analyze] API response text: {response_text}")
                    
                    # Try to extract status code and body from Anthropic API error
                    if hasattr(e, 'status_code'):
                        error_details["status_code"] = e.status_code
                        logger.error(f"[vision_analyze] HTTP status code: {e.status_code}")
                    
                    if hasattr(e, 'body'):
                        try:
                            if isinstance(e.body, dict):
                                error_details["api_error_body"] = e.body
                                logger.error(f"[vision_analyze] API error body: {json.dumps(e.body, ensure_ascii=False)}")
                            else:
                                error_details["api_error_body"] = str(e.body)
                                logger.error(f"[vision_analyze] API error body: {str(e.body)}")
                        except Exception as parse_error:
                            logger.error(f"[vision_analyze] Failed to parse error body: {parse_error}")
                    
                    # Build comprehensive error message
                    full_error_msg = f"Failed to analyze image with Anthropic API: {error_msg}"
                    if error_details.get("status_code"):
                        full_error_msg += f" (Status: {error_details['status_code']})"
                    
                    return json.dumps({
                        "error": full_error_msg,
                        "error_details": error_details,
                        "image_path": str(resolved_image_path),
                        "image_info": {
                            "file_size_mb": f"{file_size_mb:.2f}",
                            "file_size_bytes": file_size,
                            "file_extension": file_extension,
                            "file_path": str(resolved_image_path)
                        },
                        "client_info": {
                            "client_type": client_type,
                            "model": client_model,
                            "base_url": getattr(client, 'base_url', 'default')
                        },
                        "suggestion": "Please check: 1) Image file is valid and readable, 2) Image size is within limits (max 5MB for Anthropic), 3) Image format matches media_type, 4) API credentials are correct, 5) Base URL is correct"
                    }, ensure_ascii=False)
            else:
                # client_type is already defined above
                logger.error(f"[vision_analyze] Unsupported client type: {client_type}")
                return json.dumps({
                    "error": f"Unsupported client type: {client_type}. Vision tool only supports OpenAIClient and AnthropicClient."
                }, ensure_ascii=False)
            
            logger.info(f"[vision_analyze] Image analysis completed successfully")
            return json.dumps(result, ensure_ascii=False)
        
        except ValueError as e:
            logger.error(f"[vision_analyze] Path validation error: {str(e)}")
            return json.dumps({
                "error": f"Path validation error: {str(e)}"
            }, ensure_ascii=False)
        except Exception as e:
            # Provide detailed error information
            error_msg = str(e)
            error_type = type(e).__name__
            
            logger.error(f"[vision_analyze] Unexpected error: {error_type}: {error_msg}", exc_info=True)
            
            # Try to extract more details from the exception
            error_details = {
                "error": f"Failed to analyze image: {error_msg}",
                "error_type": error_type
            }
            
            # Add context if available
            if image_path:
                error_details["image_path"] = str(image_path)
            if resolved_image_path and resolved_image_path.exists():
                try:
                    file_size_bytes = resolved_image_path.stat().st_size
                    error_details["file_size_mb"] = f"{file_size_bytes / (1024*1024):.2f}"
                    error_details["file_size_bytes"] = file_size_bytes
                except:
                    pass
            
            return json.dumps(error_details, ensure_ascii=False)

