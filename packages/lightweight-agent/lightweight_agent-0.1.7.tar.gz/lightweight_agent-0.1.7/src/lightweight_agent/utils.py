"""Utility Functions Module"""
from typing import AsyncIterator, Union, Optional, Tuple
import base64
import mimetypes
import logging
from pathlib import Path
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


async def handle_streaming_response(stream) -> AsyncIterator[str]:
    """
    Unified handling of streaming responses
    Note: This is a generic interface, specific implementation is handled by each client class
    
    :param stream: Streaming response object
    :return: Async iterator, yields a string chunk each time
    """
    # This function is mainly for type hints and possible unified processing in the future
    # Actual processing logic is implemented in respective client classes
    async for chunk in stream:
        yield chunk


def validate_prompt(prompt: str) -> None:
    """
    Validate prompt
    
    :param prompt: Prompt string
    :raises ValidationError: If prompt is empty or invalid
    """
    if not prompt or not isinstance(prompt, str):
        raise ValidationError("Prompt must be a non-empty string")
    
    if not prompt.strip():
        raise ValidationError("Prompt cannot be only whitespace")


def encode_image_to_base64(image_path: Union[str, Path]) -> Tuple[str, str]:
    """
    Encode image file to base64 string
    
    :param image_path: Path to image file
    :return: Tuple of (base64_string, media_type)
    :raises ValidationError: If file doesn't exist or cannot be read
    """
    image_path = Path(image_path)
    
    logger.debug(f"[encode_image_to_base64] Processing image: {image_path}")
    
    if not image_path.exists():
        logger.error(f"[encode_image_to_base64] Image file not found: {image_path}")
        raise ValidationError(f"Image file not found: {image_path}")
    
    # Try to detect actual image format using PIL if available
    actual_format = None
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            actual_format = img.format
            logger.debug(f"[encode_image_to_base64] PIL detected format: {actual_format}")
    except ImportError:
        logger.debug("[encode_image_to_base64] PIL not available, using mimetypes")
    except Exception as e:
        logger.warning(f"[encode_image_to_base64] Failed to open image with PIL: {e}, falling back to mimetypes")
    
    # Detect media type
    media_type, _ = mimetypes.guess_type(str(image_path))
    ext = image_path.suffix.lower()
    
    # Map PIL format to media type if available
    if actual_format:
        format_to_media_type = {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif',
            'WEBP': 'image/webp',
        }
        pil_media_type = format_to_media_type.get(actual_format.upper())
        if pil_media_type:
            media_type = pil_media_type
            logger.debug(f"[encode_image_to_base64] Using PIL-detected media_type: {media_type}")
    
    # Fallback to extension-based detection
    if not media_type or not media_type.startswith('image/'):
        type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        media_type = type_map.get(ext, 'image/jpeg')
        logger.debug(f"[encode_image_to_base64] Using extension-based media_type: {media_type} (extension: {ext})")
    
    # Warn if there's a mismatch between extension and detected format
    if actual_format:
        ext_to_format = {
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.png': 'PNG',
            '.gif': 'GIF',
            '.webp': 'WEBP',
        }
        expected_format = ext_to_format.get(ext)
        if expected_format and actual_format.upper() != expected_format:
            logger.warning(f"[encode_image_to_base64] Format mismatch: file extension suggests {expected_format}, but actual format is {actual_format}")
    
    # Read and encode
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        file_size = len(image_data)
        logger.debug(f"[encode_image_to_base64] Read {file_size} bytes from image file")
        
        base64_string = base64.b64encode(image_data).decode('utf-8')
        base64_length = len(base64_string)
        logger.debug(f"[encode_image_to_base64] Encoded to base64: {base64_length} chars, media_type: {media_type}")
        
        # Warn if base64 size is very large (approaching limits)
        if base64_length > 4 * 1024 * 1024:  # 4MB
            logger.warning(f"[encode_image_to_base64] Base64 encoded size is large: {base64_length / (1024*1024):.2f}MB")
        
        return base64_string, media_type
    except Exception as e:
        logger.error(f"[encode_image_to_base64] Failed to read/encode image: {e}")
        raise ValidationError(f"Failed to read image file: {str(e)}")


def create_openai_image_message(image_path: Union[str, Path], text: Optional[str] = None) -> dict:
    """
    Create OpenAI format image message
    
    :param image_path: Path to image file
    :param text: Optional text prompt
    :return: Message dict in OpenAI format
    """
    base64_string, media_type = encode_image_to_base64(image_path)
    
    content = []
    if text:
        content.append({"type": "text", "text": text})
    
    content.append({
        "type": "image_url",
        "image_url": {
            "url": f"data:{media_type};base64,{base64_string}"
        }
    })
    
    return {
        "role": "user",
        "content": content
    }


def create_anthropic_image_message(image_path: Union[str, Path], text: Optional[str] = None) -> dict:
    """
    Create Anthropic format image message
    
    :param image_path: Path to image file
    :param text: Optional text prompt
    :return: Message dict in Anthropic format
    """
    base64_string, media_type = encode_image_to_base64(image_path)
    
    content = []
    if text:
        content.append({"type": "text", "text": text})
    
    content.append({
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64_string
        }
    })
    
    return {
        "role": "user",
        "content": content
    }

