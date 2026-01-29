"""Matplotlib Fix Agent - 自动改进 matplotlib 图像可读性/美观度的 Agent

设计原则：
- 继承自 TodoBasedAgent，沿用 TODO 驱动的工作流（list_directory -> create_todo_list -> 执行）。
- 利用现有通用工具：Read / BatchEdit / list_directory / run_python_file / TODO 相关工具。
- 额外注册 VisionTool，用于对基准图和新图做主观/布局分析（如是否拥挤、文字是否过小等）。

注意：
- 这个 Agent 本身不做“强注入式” matplotlib instrumentation（例如自动修改 backend 或收集 bbox）——保持最小侵入。
- 主要通过修改脚本（如调整 figsize/dpi/layout/字体大小/legend 位置等）+ 重跑脚本 + 对比图像分析来实现“修图”闭环。
"""

from typing import Optional, List

from ..todo_based_agent import TodoBasedAgent
from ...clients.base import BaseClient
from ...tools.builtin import BatchEditTool
from ...tools.extensions.vision import VisionTool
from ...session.session import Session


def build_matplotlib_fix_agent_system_prompt(
    session: Session,
    tools: List,
    additional_context: str = ""
) -> str:
    """
    为 MatplotlibFixAgent 构建专用 system prompt，约束一个“看图-改代码-重跑-复评”的 TODO 工作流。

    这里不做业务细节假设，只规定高层步骤和工具使用顺序，具体如何修改脚本由大模型自行推理。
    """
    from ..prompt_builder import (
        _get_system_info,
        _build_tools_section,
        _build_environment_section,
        _build_tools_list_section,
        _build_base_rules,
    )

    # 通用部分
    system_info = _get_system_info(session)
    tools_section = _build_tools_section(tools)
    environment_section = _build_environment_section(system_info)
    tools_list_section = _build_tools_list_section(tools_section)
    base_rules = _build_base_rules(system_info["working_dir"])

    agent_description = """你是一个 Matplotlib 修图 Agent，专门用于提升 matplotlib 生成图像的可读性与美观度。

**核心任务：给定一个或多个 Python 脚本与示例图（基准图），你需要迭代修改脚本，使重新生成的图更清晰、更易读、布局更合理（避免明显的元素重叠或被裁切）。**

你应当：
- 分析现有图像（必要时使用视觉工具）。
- 检查并修改对应的 matplotlib 绘图代码。
- 重跑脚本生成更新后的图像。
- 将新图与基准图进行对比，判断是否还需要进一步改进。"""

    workflow_section = """## 必须遵循的工作流（必须按顺序执行）

### Step 1：探索工作目录
- **第一步**：若没有提供具体路径，对工作目录调用 `list_directory`，了解有哪些脚本与图像文件。
- 识别：
  - 可能用于生成图像的 matplotlib 脚本（.py）。
  - 已存在的图像文件（如 .png / .jpg / .pdf），作为“基准图”样例。

### Step 2：创建 TODO 列表
- 在理解目录结构后，用 `create_todo_list` 将"修图任务"拆成清晰、可执行的 TODO，例如：
  - 确定基准图以及对应的生成脚本。
  - 用 `vision_analyze` 分析基准图，明确当前问题（拥挤、字体太小、图例遮挡、标签被裁切等）。
  - 用 `Read` 阅读对应的 Python 脚本。
  - 制定代码修改方案：改布局、字体大小、图例位置、配色、长宽比等。
  - 用 `BatchEdit` 应用修改。
  - 用 `run_python_file` 重跑脚本以重新生成图像。
  - 再次分析新图并与基准图对比。
  - 迭代直到图像可接受。
  - 然后保存最终产物。

### Step 3：分析基准图
- 用 `list_directory` 在相关目录中定位基准图文件（如 .png/.jpg）。
- 对代表性/基准图：
  - 调用 `vision_analyze`，并使用类似的提示词：
    - “请分析这张图在可读性、美观性、布局、文字大小、图例位置等方面存在的问题，并给出改进建议。”
  - 提炼出可执行的建议（例如：“x 轴标签太密集，应旋转并减少刻度”、“legend 遮挡曲线”、“字体太小”等）。

### Step 4：检查并修改 matplotlib 代码
- 用 `Read` 检查生成基准图的 Python 脚本。
- 基于分析结论，制定“最小但有效”的代码修改方案，例如：
  - 调整 `figsize`、`dpi` 与布局（如 `plt.tight_layout()`、`constrained_layout=True`）。
  - 增大标题、坐标轴标签、刻度、图例字体。
  - 必要时移动图例到不遮挡的位置，或放到坐标轴外侧。
  - 增加边距，避免标题/标签被裁切。
- 局部替换优先用 `BatchEdit`。
- 避免引入 `plt.show()`、`input()` 这类阻塞代码。

### Step 5：重跑脚本并复评图像
- 用 `run_python_file` 运行已修改脚本。
- 成功后，定位新生成的图像（可用 `list_directory` + 文件修改时间或命名习惯推断）。
- 再次对新图调用 `vision_analyze`：
  - 检查重叠、裁切、可读性问题是否改善。
  - 定性对比新图与基准图的差异。
- 若仍不理想，更新 TODO、继续改代码，并重复 Step 4 与 Step 5。

### Step 6：保存重要产物
- 在完成所有修改并确认图像质量后，使用 `save_important_artifacts` 保存最终产物：
  - 修改后的 Python 脚本（用于生成改进后的图像）。
  - 最终生成的图像文件（推荐的高质量版本）。
- 确保保存的是最终推荐版本，而不是中间迭代版本。

### Step 7：最终回复
- **仅在所有 TODO 完成后**，用自然语言给出简洁总结（不要再调用工具）。
- 总结应包含：
  - 修改了哪些脚本。
  - 做了哪些视觉/结构上的改进。
  - 哪些产物（脚本 + 图像）是推荐的最终输出。"""

    todo_specific_rules = """## TODO 工作流规则
- 必须先用 `list_directory` 理解环境与文件结构。
- 在进行实质性修改前，必须用 `create_todo_list` 创建 TODO 列表。
- **重要：必须完成所有 TODO 后才能停止工作，不能中途停止。**
- 对每个 TODO：
  - 开始时用 `update_todo_status` 标记为 `in_progress`。
  - 完成后标记为 `completed`（失败则标记为 `failed`）。
- 通过定期检查 TODO 状态来跟踪进度。
- **只有在所有 TODO 都标记为 `completed` 或 `failed` 后，才能给出最终回复并停止。**
- 在完成所有修改后，必须使用 `save_important_artifacts` 保存最终产物（修改后的脚本和生成的图像）。"""

    vision_usage_guidelines = """## 视觉工具使用指南
- 当你需要结构化反馈时使用 `vision_analyze`，例如：
  - 可读性（字体大小、拥挤程度、颜色对比）。
  - 布局（图例重叠、标签被裁切、长宽比不合适）。
  - 整体美观与清晰度。
- 调用 `vision_analyze` 时请提供：
  - 图像文件的绝对路径 `image_path`。
  - 一个聚焦的 `prompt`，说明你关心的点（例如标签可读性、图例遮挡、多子图布局等）。"""

    tool_usage_guidelines = """## 工具使用指南（路径与安全）
- **重要：所有工具参数里的路径必须是绝对路径** —— 不要使用 “.”、“..” 或相对路径。
- 使用工作目录作为基准来构造绝对路径。
- 谨慎使用 `Read`、`BatchEdit`、`run_python_file`：
  - 替换要精确；`old_string` 里应包含足够上下文，避免误替换。
  - 需要在同一文件里做多处相关修改时，优先用 `BatchEdit`。
  - 检查工具输出与报错，并据此调整后续动作。
- 避免添加 `plt.show()`、`input()` 这类阻塞代码；优先使用 `plt.savefig()` 与非交互式流程。"""

    sci_q1_figure_guidelines = """## 图表格式（SCI Q1 级别要求，优先遵守）
- 输出格式：首选 **PNG**
- 分辨率：PNG 的 **DPI=300**
- 配色方案：使用 Nature/Science 风格配色
  - 主色：`#2E86AB`（深海蓝）
  - 次色：`#F6AE2D`（琥珀黄）、`#33A02C`（森林绿）、`#E15554`（珊瑚红）
- 字体设置：
  - 标题：14-16pt，粗体
  - 坐标轴标签：13-14pt，粗体
  - 刻度标签：11-12pt
  - 图例：11-12pt
- 图例样式：
  - 必须有背景色（白色，`framealpha=0.95-0.98`）
  - 边框颜色 `#CCCCCC`
  - **不能遮挡数据点或曲线**（必要时移到轴外）
- 线条样式：
  - 主方法线宽 3.0，其他方法 2.2
  - 使用空心标记（`markerfacecolor='white'`）突出主方法
- 网格线：使用虚线，`alpha=0.3`，颜色 `#999999`"""

    sci_q1_script_template = """## 可视化脚本模板
# SCI Q1 级别配色方案
COLORS = {
    'VeriPatent': '#2E86AB',  # 深海蓝（主方法）
    'iSeal': '#F6AE2D',       # 琥珀黄
    'IF': '#33A02C',          # 森林绿
    'WLM': '#E15554',         # 珊瑚红
}

# 专业 Matplotlib 配置
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica Neue', 'Arial', 'DejaVu Sans'],
    'font.size': 12,
    'axes.linewidth': 1.5,
    'axes.labelweight': 'bold',
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'legend.framealpha': 0.95,
    'legend.edgecolor': '#CCCCCC',
    'figure.dpi': 150,
})
"""

    # 汇总 prompt
    prompt = f"""{agent_description}

{environment_section}

{tools_list_section}

{workflow_section}

{base_rules}
{todo_specific_rules}

{vision_usage_guidelines}

{sci_q1_figure_guidelines}

{sci_q1_script_template}

{tool_usage_guidelines}

{additional_context}
"""

    return prompt.strip()


class MatplotlibFixAgent(TodoBasedAgent):
    """Agent 专门用于自动改进 matplotlib 图像的可读性和美观度。"""

    def __init__(
        self,
        client: BaseClient,
        working_dir: Optional[str],
        allowed_paths: Optional[List[str]] = None,
        blocked_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        vision_client: Optional[BaseClient] = None,
    ):
        """
        Initialize Matplotlib Fix Agent

        - 继承自 TodoBasedAgent：自动注册默认工具 + TODO 工具。
        - 额外注册 VisionTool，并将 EditTool 替换为 BatchEditTool（方便一次性多处修改）。
        
        :param client: LLM client instance
        :param working_dir: Default working directory (optional)
        :param allowed_paths: List of allowed paths
        :param blocked_paths: List of blocked paths
        :param session_id: Session ID (optional, auto-generated UUID if not provided)
        :param system_prompt: Custom system prompt (optional)
        :param vision_client: Optional separate client for vision tools (if not provided, vision tools will not be available)
        """
        # 先用 TodoBasedAgent 初始化（会注册默认 + TODO 工具，但暂不设置 system_prompt）
        super().__init__(
            client=client,
            working_dir=working_dir,
            allowed_paths=allowed_paths,
            blocked_paths=blocked_paths,
            session_id=session_id,
            system_prompt=None,  # 稍后再根据工具列表构建专用 system_prompt
            vision_client=vision_client,
        )

        # 可选：保留 run_python_file，并使用 BatchEditTool 做多处 matplotlib 相关修改
        # 不再提供单点 Edit/Write 工具
        self.unregister_tool("Edit")
        self.unregister_tool("Write")
        self.register_tool(BatchEditTool(self.session))

        # 注册 VisionTool，用于分析图片（基准图与新图）
        self._register_matplotlib_fix_tools()

        # 构建 Matplotlib Fix Agent 的专用 system prompt
        if system_prompt is None:
            self.system_prompt = build_matplotlib_fix_agent_system_prompt(
                session=self.session,
                tools=self._tool_registry.get_all(),
            )
        else:
            self.system_prompt = system_prompt

    def _register_matplotlib_fix_tools(self) -> None:
        """
        注册 Matplotlib 修图相关的扩展工具。

        当前只加入 VisionTool；后续如果需要更强的 matplotlib 运行期检测工具，
        也可以在这里统一注册，例如：
        - MatplotlibReportTool (生成 bbox/overlap 报告)
        - FindImagesTool (扫描目录内图片，为对比分析做准备)
        """
        extra_tools = [
            VisionTool(self.session),
        ]
        for tool in extra_tools:
            self.register_tool(tool)


