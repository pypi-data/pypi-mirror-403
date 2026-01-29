"""Banana Image Client Implementation"""
import os
from typing import Optional, Union
from pathlib import Path

try:
    from google import genai
    from google.genai import types
    from PIL import Image
except ImportError:
    genai = None
    types = None
    Image = None

from ..exceptions import APIError, NetworkError, ValidationError, ConfigurationError


class BananaImageClient:
    """Banana API 图像编辑客户端（专用）"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        vertexai: bool = True
    ):
        """
        初始化 Banana Image Client
        
        :param api_key: API key，默认从环境变量 BANANA_API_KEY 读取
        :param base_url: API base URL，默认从环境变量 BANANA_BASE_URL 读取
        :param model: 模型名称，默认从环境变量 BANANA_MODEL 读取
        :param vertexai: 是否使用 VertexAI 模式，默认 True（目前只支持 vertexai=True）
        """
        # 检查依赖
        if genai is None or types is None or Image is None:
            raise ConfigurationError(
                "google-genai and Pillow are required for BananaImageClient. "
                "Install with: pip install google-genai pillow"
            )
        
        # 从参数或环境变量获取配置
        self.api_key = api_key or os.getenv("BANANA_API_KEY")
        self.base_url = base_url or os.getenv("BANANA_BASE_URL")
        self.model = model or os.getenv("BANANA_MODEL")
        self.vertexai = vertexai
        
        # 验证必需参数
        if not self.api_key:
            raise ConfigurationError("API key is required. Set BANANA_API_KEY environment variable or pass api_key parameter.")
        if not self.base_url:
            raise ConfigurationError("Base URL is required. Set BANANA_BASE_URL environment variable or pass base_url parameter.")
        if not self.model:
            raise ConfigurationError("Model is required. Set BANANA_MODEL environment variable or pass model parameter.")
        
        # 初始化 Google GenAI client
        try:
            self.client = genai.Client(
                vertexai=self.vertexai,
                http_options=types.HttpOptions(
                    base_url=self.base_url,
                    headers={'Authorization': self.api_key},
                ),
            )
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Banana client: {str(e)}") from e
    
    async def edit_image(
        self,
        prompt: str,
        image_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> Image.Image:
        """
        编辑图像并返回 PIL Image 对象
        
        :param prompt: 图像编辑提示词
        :param image_path: 输入图像文件路径
        :param output_path: 可选，输出图像保存路径。如果不提供，只返回 Image 对象不保存
        :return: PIL Image 对象
        :raises ValidationError: 图像文件无效或无法读取
        :raises APIError: API 调用失败
        :raises NetworkError: 网络错误
        """
        # 验证并加载输入图像
        image_path = Path(image_path)
        if not image_path.exists():
            raise ValidationError(f"Image file not found: {image_path}")
        
        if not image_path.is_file():
            raise ValidationError(f"Path is not a file: {image_path}")
        
        try:
            input_image = Image.open(image_path)
        except Exception as e:
            raise ValidationError(f"Failed to open image file: {str(e)}") from e
        
        # 调用 API
        try:
            response = await self._generate_content_async(prompt, input_image)
        except Exception as e:
            # 检查是否是网络错误
            error_str = str(e).lower()
            if "connection" in error_str or "network" in error_str or "timeout" in error_str:
                raise NetworkError(f"Network error when calling Banana API: {str(e)}") from e
            # 其他错误作为 API 错误
            raise APIError(f"Banana API error: {str(e)}") from e
        
        # 处理响应，提取图像
        output_image = None
        text_output = []
        
        for part in response.parts:
            if part.text is not None:
                text_output.append(part.text)
            elif part.inline_data is not None:
                try:
                    output_image = part.as_image()
                except Exception as e:
                    raise APIError(f"Failed to extract image from response: {str(e)}") from e
        
        # 验证是否获得了图像
        if output_image is None:
            error_msg = "No image found in API response"
            if text_output:
                error_msg += f". Text response: {', '.join(text_output)}"
            raise APIError(error_msg)
        
        # 可选：保存图像
        if output_path:
            try:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_image.save(output_path)
            except Exception as e:
                raise ValidationError(f"Failed to save image to {output_path}: {str(e)}") from e
        
        return output_image
    
    async def _generate_content_async(self, prompt: str, image: Image.Image):
        """
        异步调用 generate_content API
        
        :param prompt: 提示词
        :param image: PIL Image 对象
        :return: API 响应对象
        """
        # Google GenAI SDK 的 generate_content 是同步的，需要在异步上下文中运行
        import asyncio
        
        def _sync_call():
            return self.client.models.generate_content(
                model=self.model,
                contents=[prompt, image],
            )
        
        # 在线程池中运行同步调用，避免阻塞事件循环
        # 使用 get_running_loop() 而不是 get_event_loop() 以兼容 Python 3.10+
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 如果没有运行的事件循环，创建一个新的
            loop = asyncio.get_event_loop()
        
        return await loop.run_in_executor(None, _sync_call)

