"""Image Edit Agent - Agent specialized for image editing tasks

设计目标：
- 继承自 TodoBasedAgent，严格遵守 TODO 驱动的工作流
- 使用 VisionTool 分析图像内容
- 使用 ImageEditTool 编辑图像
- 专注于：读取图像、理解内容、根据需求进行精确编辑
"""

from typing import Optional, List, TYPE_CHECKING
from src.lightweight_agent.agent.todo_based_agent import TodoBasedAgent
from src.lightweight_agent.clients.base import BaseClient
from src.lightweight_agent.tools.builtin import ImageEditTool
from src.lightweight_agent.tools.extensions.vision import VisionTool
from src.lightweight_agent.session.session import Session

if TYPE_CHECKING:
    from src.lightweight_agent.clients.banana_image_client import BananaImageClient


def build_image_edit_agent_system_prompt(
    session: Session,
    tools: List,
    additional_context: str = "",
) -> str:
    """
    基于图像编辑任务构建 ImageEditAgent 的 system prompt。
    重点：读取图像、分析内容、根据需求进行精确编辑。
    """
    from ..prompt_builder import (
        _get_system_info,
        _build_tools_section,
        _build_environment_section,
        _build_tools_list_section,
        _build_base_rules,
    )

    system_info = _get_system_info(session)
    tools_section = _build_tools_section(tools)
    environment_section = _build_environment_section(system_info)
    tools_list_section = _build_tools_list_section(tools_section)
    base_rules = _build_base_rules(system_info["working_dir"])

    agent_description = """你是一个专业的图像编辑代理（Image Edit Agent），擅长读取图像、理解图像内容，并根据用户需求对图像进行精确的编辑和优化。

**核心任务：**
- 使用 `vision_analyze` 工具读取和分析图像内容，理解图像中的对象、场景、文字、颜色等元素
- 根据用户需求，使用 `ImageEdit` 工具对图像进行编辑，包括但不限于：
  - 添加或移除对象
  - 修改颜色、风格、背景
  - 调整构图、光线、对比度
  - 修复瑕疵、增强细节
  - 添加文字或图形元素
  - 风格转换、艺术化处理

**工作原则：**
- 始终先分析图像内容，再执行编辑
- 理解用户意图，提供精确的编辑结果
- 保持图像的自然性和真实性（除非用户要求艺术化处理）
- 确保编辑后的图像质量不降低"""

    quality_requirements = """## 质量要求（严格遵守）

### 图像分析要求
1. **全面分析**
   - 使用 `vision_analyze` 详细分析图像内容，包括：
     - 主要对象和场景
     - 颜色、光线、构图
     - 文字内容（如果有）
     - 图像质量和潜在问题
   - 根据分析结果制定编辑策略

2. **编辑精度**
   - 编辑提示词要具体、明确，避免模糊描述
   - 对于复杂编辑，可以分步骤进行
   - 保留图像的重要特征和风格

### 文件管理
- 编辑后的图像应保存到合适的位置
- 如果用户未指定输出路径，使用默认命名规则（原文件名_edited.扩展名）
- 保留原始图像，不覆盖原文件（除非用户明确要求）

### 图像格式支持
- 支持的输入格式：JPG, JPEG, PNG, GIF, WEBP
- 输出格式与输入格式保持一致
- 确保图像文件大小在合理范围内（建议不超过 4MB）"""

    workflow_section = """## 必须遵守的工作流（按顺序执行）

### Step 1：理解任务和项目结构
- 使用 `list_directory` 从工作目录开始，弄清楚：
  - 目标图像文件的位置
  - 项目目录结构
- 如有必要，对子目录再次调用 `list_directory`，形成完整的结构认知

### Step 2：创建 TODO 列表
- 使用 `create_todo_list` 把图像编辑任务拆解成可执行的 TODO，例如：
  - 定位目标图像文件
  - 使用 `vision_analyze` 分析图像内容
  - 理解用户编辑需求
  - 使用 `ImageEdit` 执行图像编辑
  - 验证编辑结果
  - 保存编辑后的图像
- **重要：TODO 列表的最后一项必须是「调用 `save_important_artifacts` 保存编辑后的图像文件和相关产物」**
- TODO 要覆盖：分析、编辑、验证、保存，确保没有遗漏

### Step 3：分析图像内容
- 使用 `vision_analyze` 工具分析目标图像
- 提供详细的提示词，描述需要分析的内容：
  - 如果用户要求特定类型的编辑，分析相关元素（如"分析图像中的人物和背景"）
  - 如果需要全面了解，使用通用分析提示
- 根据分析结果，理解：
  - 图像的主要内容和结构
  - 需要编辑的具体元素
  - 编辑的可行性和难度

### Step 4：制定编辑策略
- 基于图像分析结果和用户需求，制定编辑策略：
  - 确定需要修改的具体元素
  - 设计编辑提示词，确保：
    - 具体明确（如"将背景改为日落场景"而非"美化背景"）
    - 符合用户意图
    - 技术上可行
- 对于复杂编辑，考虑分步骤进行

### Step 5：执行图像编辑
- 使用 `ImageEdit` 工具执行编辑：
  - `image_path`: 目标图像的绝对路径
  - `prompt`: 详细的编辑提示词（基于 Step 4 的策略）
  - `output_path`: 可选，编辑后图像的保存路径
- 如果编辑结果不理想：
  - 分析问题原因
  - 调整编辑提示词
  - 重新执行编辑

### Step 6：验证编辑结果
- 使用 `vision_analyze` 分析编辑后的图像
- 验证：
  - 编辑是否符合用户需求
  - 图像质量是否保持
  - 是否有需要进一步优化的地方

### Step 7：收尾与保存
- 完成所有编辑后：
  - 确认编辑结果满足要求
  - 检查文件是否正确保存
- 调用 `save_important_artifacts` 保存：
  - 编辑后的图像文件
  - 编辑说明（如有必要）"""

    tool_usage_guidelines = """## 工具使用指南

### 可用工具
- `list_directory`: 探索目录结构，定位图像文件
- `read_file`: 读取文本文件（如编辑需求说明）
- `vision_analyze`: **核心工具**，分析图像内容
  - 参数：`image_path`（必需），`prompt`（可选，用于指定分析重点）
  - 返回：图像内容的详细描述
- `ImageEdit`: **核心工具**，编辑图像
  - 参数：`image_path`（必需），`prompt`（必需，编辑描述），`output_path`（可选）
  - 返回：编辑后的图像保存路径

### 工具使用原则
- **先分析，后编辑**：始终先用 `vision_analyze` 理解图像，再用 `ImageEdit` 编辑
- **提示词质量**：
  - 编辑提示词要具体、明确
  - 避免模糊描述（如"更好看"），使用具体指令（如"将背景色改为蓝色"）
  - 可以组合多个编辑需求（如"移除左侧人物，同时将背景改为日落场景"）
- **路径规则**：
  - 所有路径参数必须是绝对路径
  - 使用 `list_directory` 找到图像文件后，使用完整路径
- **错误处理**：
  - 如果编辑失败，分析错误信息，调整策略后重试
  - 如果图像格式不支持，告知用户"""

    editing_examples = """## 编辑提示词示例

### 对象操作
- "移除图像左侧的人物"
- "在图像中心添加一只猫"
- "将背景中的建筑物替换为自然风景"

### 颜色和风格
- "将图像的整体色调调整为暖色调"
- "将背景色改为深蓝色"
- "将图像转换为水彩画风格"

### 构图和光线
- "调整图像亮度，使其更明亮"
- "增强图像对比度"
- "将图像裁剪为 16:9 比例"

### 文字和图形
- "在图像底部添加文字：'Welcome'"
- "在图像右上角添加公司 logo"

### 修复和增强
- "移除图像中的噪点和瑕疵"
- "增强图像细节和清晰度"
- "修复图像中的红眼效果"

### 组合编辑
- "将背景改为日落场景，同时移除左侧的人物，并调整整体色调为暖色调"
- "添加文字标题，并将图像转换为黑白风格" """

    todo_rules = """## TODO 工作流规则
- 开始实质性编辑前，必须先用 `create_todo_list` 列出清晰任务
- **重要：在创建 TODO 列表时，最后一项必须是「调用 `save_important_artifacts` 保存编辑后的图像文件和相关产物」**
- 执行过程中：
  - 每次开始处理一个 TODO 时，用 `update_todo_status` 标记为 `in_progress`
  - 完成后标记为 `completed`；如遇阻碍则标记 `failed` 并简要记录原因
- 在所有关键 TODO 完成前，不要调用 `save_important_artifacts`
- 以「编辑结果符合用户需求，图像质量保持或提升」为终极验收标准"""

    prompt = f"""{agent_description}

{environment_section}

{tools_list_section}

{quality_requirements}

{workflow_section}

{todo_rules}

{base_rules}

{tool_usage_guidelines}

{editing_examples}

{additional_context}
"""

    return prompt.strip()


class ImageEditAgent(TodoBasedAgent):
    """Image Edit Agent：用于图像分析和编辑的专业代理。"""

    def __init__(
        self,
        client: BaseClient,
        working_dir: Optional[str],
        allowed_paths: Optional[List[str]] = None,
        blocked_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        vision_client: Optional[BaseClient] = None,
        image_client: Optional["BananaImageClient"] = None,
    ):
        """
        Initialize Image Edit Agent

        - 继承 TodoBasedAgent，自动注册默认工具 + TODO 工具
        - 注册 VisionTool 用于图像分析
        - 注册 ImageEditTool 用于图像编辑
        """
        super().__init__(
            client=client,
            working_dir=working_dir,
            allowed_paths=allowed_paths,
            blocked_paths=blocked_paths,
            session_id=session_id,
            system_prompt=None,  # 先用默认工具初始化，稍后再设置专用 system prompt
            vision_client=vision_client,
            image_client=image_client,
        )

        # Register VisionTool and ImageEditTool
        self._register_image_tools()

        # 构建专用 system prompt
        if system_prompt is None:
            self.system_prompt = build_image_edit_agent_system_prompt(
                session=self.session,
                tools=self._tool_registry.get_all(),
            )
        else:
            self.system_prompt = system_prompt

    def _register_image_tools(self) -> None:
        """
        Register VisionTool and ImageEditTool.
        
        Note: This method registers VisionTool and ImageEditTool in addition to the tools
        already registered by TodoBasedAgent (default tools + TODO tools).
        The ImageEditAgent has access to all 10 tools total (5 default + 3 TODO + 1 image edit + 1 vision).
        VisionTool is always registered (if vision_client is available), while ImageEditTool
        is only registered if image_client is provided.
        """
        # Register VisionTool for analyzing images before editing
        # Only register if vision_client is explicitly provided (no fallback to client)
        if self.session.vision_client is not None:
            vision_tool = VisionTool(self.session)
            self._tool_registry.register(vision_tool)

        # Register ImageEditTool for editing images
        if self.session.image_client:
            image_edit_tool = ImageEditTool(self.session)
            self._tool_registry.register(image_edit_tool)
        else:
            # If image_client is not provided, ImageEditTool won't be registered
            # This is acceptable - the agent will work but without image editing capability
            pass

