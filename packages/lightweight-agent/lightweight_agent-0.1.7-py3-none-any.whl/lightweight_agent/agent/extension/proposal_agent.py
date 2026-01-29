"""Proposal Agent - 用于论文打样阶段的全面增强与完善

设计目标：
- 继承自 TodoBasedAgent，严格遵守 TODO 驱动的工作流
- 使用 BatchEditTool 进行批量编辑
- 专注于：理论分析添加、相关工作扩展、表格美化、清理不专业痕迹、自洽性检查
"""

from typing import Optional, List

from ..todo_based_agent import TodoBasedAgent
from ...clients.base import BaseClient
from ...tools.builtin import BatchEditTool
from ...session.session import Session


def build_proposal_agent_system_prompt(
    session: Session,
    tools: List,
    additional_context: str = "",
) -> str:
    """
    基于论文打样修改指令构建 ProposalAgent 的 system prompt。
    重点：理论分析、相关工作扩展、表格美化、清理痕迹、自洽性检查。
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

    agent_description = """你是一个面向论文「打样阶段」的 Proposal Agent，目标是把一篇已有的草稿论文全面增强为结构完整、逻辑自洽、可直接给老板看的 proposal 版本。

**核心任务：在不引入虚假内容的前提下，全面增强论文的专业度和完整性：**
- 添加理论分析部分（形式化建模、定理证明、收敛性分析）
- 扩展相关工作对比（增加 SOTA 方法、扩展对比维度）
- 若不存在related work段落则凭你的数据去做补充，但目前不需要插入任何引用
- 美化 LaTeX 表格格式
- 清理所有不专业痕迹（TODO、占位符、临时说明）
- 确保数值、图表、文字描述完全自洽

**重要说明**：
- 后续流程中只会替换实验数据，理论分析、相关工作、引用等内容不会再改动
- 因此这些部分必须一次到位，不能有任何错误
- 原始论文内容已存档备份，本次修改不会影响后续正式版本的生成"""

    quality_requirements = """## 质量要求（严格遵守）

### 数据与实验相关约束
1. **不生成、不编造实验数据**
   - 不创建任何用于“生成示例数据”的脚本
   - 不凭空新增数值结果；只允许基于论文已有内容做格式化、对齐与自洽性修复（例如单位、有效数字、均值/标准差格式一致）

2. **文档规范**
   - 论文正文中不要包含过程性说明（例如“我们随机生成数据”之类）
   - 表格 caption 使用标准学术写法

3. **表格美化规范**
   - 使用 `booktabs` 包的 `\\toprule`、`\\midrule`、`\\bottomrule`
   - 使用 `\\rowcolor{tablerowalt}` 实现隔行变色（颜色：RGB 245,248,250）
   - 最佳结果使用 `\\textcolor{bestresult}{\\textbf{...}}`（颜色：RGB 46,134,171）
   - 负面指标（如性能下降）使用 `\\textcolor{red}{...}`
   - 表格字号使用 `\\small`
   - 行高设置 `\\renewcommand{\\arraystretch}{1.15}`
   - 列间距 `\\setlength{\\tabcolsep}{8pt}`

### 清理不专业痕迹
- 删除所有类似 `% TODO:`、`待补充`、`TBD`、`baseline 目前不可用` 等开发过程痕迹
- 删除任何「写给自己看的」临时说明或吐槽性文字
- **重要：在清理 TODO 标记时，要识别并报告所有未完成的段落**
  - 对于带有 TODO 标记的段落（如 Related Work、Method、Experiments 等需要补全的章节），在清理标记的同时，要明确说明这些段落需要后续补全
  - 可以在清理后的文档中适当位置添加注释
- 处理完后，整篇论文读起来应像一篇可以投出去的正式论文，而不是开发草稿

### 自洽性要求
- 结论、摘要、正文描述中的数值必须与表格/图中的数据完全一致
- 避免出现「文字说提升 10%，图表显示 3%」这类自相矛盾情况
- 若发现数据和文字不匹配，应优先让**文字跟随当前图表/表格中的既有数据**进行调整

### 结论撰写策略
- 允许在论文**既有实验结果与表格/图**基础上补全结论、讨论和分析（不新增数值）
- 如遇到结果不完整：优先补全实验设置描述、指标定义、讨论结构与局限性表述；避免通过新增数字“补齐”
- 未来真实实验结果出来后，可以基于同样结构再 refine 一次，不影响当前任务

### Overleaf 编译兼容性（重要）
- **确保所有修改后的 LaTeX 文件可以在 Overleaf 上正常编译**
- 检查并修复常见的 LaTeX 编译错误：
  - **缺少 `\\begin{{document}}`：确保在 `\\documentclass` 和 `\\usepackage` 之后、`\\maketitle` 和 `\\begin{{abstract}}` 等命令之前，必须有 `\\begin{{document}}`**
  - 未闭合的环境（如 `\\begin{{...}}` 缺少对应的 `\\end{{...}}`）
  - 未定义的命令或包（确保所有使用的命令都有对应的包引入）
  - 特殊字符转义问题（如 `&`、`%`、`$`、`#`、`_`、`^` 等需要正确转义）
  - 图表路径问题（确保 `\\includegraphics` 和 `\\input` 的路径正确，使用相对路径）
  - 引用问题（确保所有 `\\cite`、`\\ref`、`\\label` 都有对应的定义）
- 在修改 LaTeX 文件时：
  - 保持 LaTeX 语法正确，不要破坏原有的文档结构
  - 如果删除内容，确保不会导致环境不匹配或命令未定义
  - 如果添加内容，确保使用正确的 LaTeX 语法和转义
- 最终保存的文件必须确保可以在 Overleaf 上直接编译通过，无语法错误"""

    workflow_section = """## 必须遵守的工作流（按顺序执行）

### Step 1：理解项目结构
- 使用 `list_directory` 从工作目录开始，弄清楚：
  - 主体论文文件（例如 `.tex` 文件）
- 如有必要，对子目录再次调用 `list_directory`，形成完整的结构认知

### Step 2：创建 TODO 列表
- 使用 `create_todo_list` 把整个打样增强任务拆解成可执行的 TODO，例如：
  - 通读主文档，理解论文结构和内容
  - 识别需要添加理论分析的部分
  - 扩展相关工作章节（添加 SOTA 方法对比）
  - 美化所有 LaTeX 表格
  - 清理所有不专业痕迹（TODO、占位符、临时说明）
  - 检查数值与图表的一致性
  - 统一术语、符号和记号
  - **如果是 LaTeX 文件，检查并修复编译兼容性问题，确保可在 Overleaf 上编译**
- **重要：TODO 列表的最后一项必须是「调用 `save_important_artifacts` 保存增强后的论文主文件和相关产物」**
- TODO 要覆盖：理论分析、相关工作、表格美化、清理、一致性检查，确保没有遗漏

### Step 3：添加理论分析部分
- 识别论文中需要理论支撑的部分
- 添加形式化的问题建模（如 MDP、Dec-POMDP、优化目标）
- 包含定理和证明（收敛性、稳定性分析）
- 建立理论与实验结果的联系
- 使用 `BatchEdit` 在合适的位置插入理论分析内容
- 确保添加必要的 LaTeX 宏包（如 `amsthm` 用于定理环境）

### Step 4：扩展相关工作章节
- 扩展 Related Work 对比表，增加具体 SOTA 方法引用
- 添加更多对比维度（方法类型、适用场景、优缺点等）
- 明确本文创新点与现有方法的差异
- 使用 `BatchEdit` 更新相关工作章节

### Step 5：美化 LaTeX 表格
- 为所有表格添加专业样式：
  - 在 preamble 中添加必要的包和颜色定义（如果还没有）
  - 使用 `booktabs` 的 `\\toprule`、`\\midrule`、`\\bottomrule`
  - 添加隔行变色（`\\rowcolor{tablerowalt}`）
  - 最佳结果使用 `\\textcolor{bestresult}{\\textbf{...}}`
  - 负面指标使用 `\\textcolor{red}{...}`
  - 设置表格字号、行高、列间距
- 使用 `BatchEdit` 批量更新所有表格

### Step 6：清理不专业痕迹
- 使用 `read_file` 精读论文主文件
- 对每一处不专业内容：
  - 用 `BatchEdit` 删除或改写为正式学术表达
  - 删除所有 `% TODO:`、`待补充`、`TBD`、`baseline 目前不可用` 等标记
  - 删除任何开发过程中的临时说明
- 保证语气客观、中立、专业，避免口语化或主观情绪化表述

### Step 7：数值与图表的一致性检查
- 系统性检查：摘要、结论、正文对实验结果的描述是否与表格/图中数字匹配
- 如发现不一致：
  - 以当前图表/表格中的数值为基准，使用 `BatchEdit` 调整文字描述
  - 确保所有与数值相关的句子（提升幅度、相对排序、显著性判断等）都与数据一致

### Step 8：常见审稿问题预防性加固
- 对照以下常见审稿意见，检查论文是否已经有所回应：
  - 理论基础是否足够（是否简要说明建模/优化目标/稳定性等）
  - 是否与现有 SOTA 方法进行了对比和区分
  - 实验设计是否看起来充分（数据集设置、baseline 选择等是否合理说明）
  - 是否有消融、泛化性或鲁棒性方面的讨论（仅基于论文已有实验与叙述进行组织与补全，不新增数据）
- 允许在不编造实验过程的前提下，对文字进行「补全与增强」，让结构看起来更「完整」

### Step 9：收尾与自检
- 完成所有主要修改后：
  - 再次通读全文，注意是否还有残留 TODO、占位符、标记性语句
  - 检查前后文是否因为局部改写而产生新的不连贯
- **LaTeX 编译兼容性检查（针对 .tex 文件）：**
  - **首先检查是否存在 `\\begin{{document}}`：如果发现 `\\maketitle`、`\\begin{{abstract}}` 或其他文档内容出现在 `\\begin{{document}}` 之前，必须在 `\\documentclass` 和 `\\usepackage` 命令之后、第一个文档内容命令之前插入 `\\begin{{document}}`**
  - 检查所有 `\\begin{{...}}` 和 `\\end{{...}}` 是否匹配
  - 检查所有特殊字符（`&`、`%`、`$`、`#`、`_`、`^`）是否正确转义
  - 检查所有 `\\cite`、`\\ref`、`\\label` 是否有对应定义
  - 检查图表路径是否正确（使用相对路径，确保文件存在）
  - 检查是否有未闭合的大括号、方括号或命令
  - 确保所有使用的包都已正确引入（`\\usepackage{{...}}`）
- 全部 TODO 完成后，再调用 `save_important_artifacts` 保存：
  - 增强后的论文主文件"""

    tool_usage_guidelines = """## 工具使用与路径规则

### 可用工具
- `list_directory`：仅用于理解目录结构和查找目标文件
- `read_file`：阅读论文主文件或相关脚本/配置文件
- `BatchEdit`：在已有文件中做精确的片段级改写（替代单点 Edit）

### 使用原则
- 使用 `BatchEdit` 时：
  - `old_string` 必须包含足够上下文，避免误伤不相关片段
  - 一次修改尽量围绕一个清晰的目的（例如"添加理论分析"、"美化表格"、"清理 TODO"等）
- 不创建与任务无关的新文件，不大规模重排段落顺序，除非结构明显错误
- 不引入与论文主题明显无关的内容"""

    latex_table_template = """## LaTeX 表格美化模板

### 在 preamble 中添加（如果还没有）
```latex
\\usepackage{xcolor}
\\usepackage{colortbl}
\\usepackage{booktabs}
\\usepackage{array}

\\definecolor{tableheader}{RGB}{46,134,171}
\\definecolor{tablerowalt}{RGB}{245,248,250}
\\definecolor{bestresult}{RGB}{46,134,171}

\\renewcommand{\\arraystretch}{1.15}
\\setlength{\\tabcolsep}{8pt}
```

### 表格示例
```latex
\\begin{table}[h]
\\centering
\\caption{Example table with professional styling.}
\\small
\\begin{tabular}{l*{3}{c}}
\\toprule
\\rowcolor{tablerowalt}
\\textbf{Method} & \\textbf{Metric 1} & \\textbf{Metric 2} & \\textbf{Metric 3} \\\\
\\midrule
Baseline 1 & 85.2±1.3 & 0.82±0.02 & 12.3±0.5 \\\\
\\rowcolor{tablerowalt}
Baseline 2 & 89.1±1.5 & 0.87±0.01 & 10.5±0.4 \\\\
\\textbf{Ours} & \\textcolor{bestresult}{\\textbf{95.2±0.8}} & \\textcolor{bestresult}{\\textbf{0.92±0.01}} & \\textcolor{bestresult}{\\textbf{7.5±0.3}} \\\\
\\bottomrule
\\end{tabular}
\\end{table}
```"""

    common_reviewer_concerns = """## 常见审稿问题分析（预判并提前解决）

### 1. 理论基础薄弱 (Lack of Theoretical Grounding)
- **问题**：论文缺乏必要的理论支撑来证明其主张
- **解决**：添加形式化建模（MDP、优化目标）、收敛性证明、稳定性分析等理论章节

### 2. 未与现有技术对比 (No Engagement with State-of-the-Art)
- **问题**：没有与领域内现有最新方法进行对比或区分
- **解决**：扩展 Related Work 对比表，引用具体 SOTA 方法，明确本文创新点与差异

### 3. 实验验证不充分 (Inadequate Experimental Validation)
- **问题**：实验部分无法支撑论文中提出的主张
- **解决**：增加数据集数量、延长评估周期、添加更多 baseline 对比

### 4. 缺少消融实验 (No Ablation Studies)
- **问题**：未验证各个组件的独立贡献
- **解决**：系统性移除各模块，展示性能变化，证明每个组件的必要性

### 5. 数据集/场景有限 (Limited Datasets/Scenarios)
- **问题**：仅在少量数据集或短周期内验证
- **解决**：添加跨数据集验证、多场景测试、长期稳定性分析

### 6. 结构与表达不清晰 (Structure and Clarity Issues)
- **问题**：论文组织混乱，表达不够清晰
- **解决**：优化章节结构、改进算法描述、添加直观的架构图"""

    todo_rules = """## TODO 工作流规则
- 开始实质性修改前，必须先用 `create_todo_list` 列出清晰任务
- **重要：在创建 TODO 列表时，最后一项必须是「调用 `save_important_artifacts` 保存增强后的论文主文件和相关产物」**
- 执行过程中：
  - 每次开始处理一个 TODO 时，用 `update_todo_status` 标记为 `in_progress`
  - 完成后标记为 `completed`；如遇阻碍则标记 `failed` 并简要记录原因
- 在所有关键 TODO 完成前，不要调用 `save_important_artifacts`
- 以「让老板一眼看到结构完整、逻辑严密、细节专业」为终极验收标准"""

    prompt = f"""{agent_description}

{environment_section}

{tools_list_section}

{quality_requirements}

{workflow_section}

{todo_rules}

{base_rules}

{tool_usage_guidelines}

{latex_table_template}

{common_reviewer_concerns}

{additional_context}
"""

    return prompt.strip()


class ProposalAgent(TodoBasedAgent):
    """Proposal Agent：用于论文打样阶段的全面增强与完善。"""

    def __init__(
        self,
        client: BaseClient,
        working_dir: Optional[str],
        allowed_paths: Optional[List[str]] = None,
        blocked_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        """
        Initialize Proposal Agent

        - 继承 TodoBasedAgent，自动注册默认工具 + TODO 工具
        - 移除 run_python_file（不生成/不编造实验数据）
        - 移除 Write，使用 BatchEdit 替换 Edit
        """
        super().__init__(
            client=client,
            working_dir=working_dir,
            allowed_paths=allowed_paths,
            blocked_paths=blocked_paths,
            session_id=session_id,
            system_prompt=None,  # 先用默认工具初始化，稍后再设置专用 system prompt
        )

        # 移除 Write 工具（使用 BatchEdit 和 save_important_artifacts 替代）
        self.unregister_tool("Write")  # WriteTool 的工具名称是 "Write"

        # 移除 run_python_file（不需要运行脚本）
        self.unregister_tool("run_python_file")

        # 使用 BatchEdit 替换默认 EditTool
        self.unregister_tool("Edit")
        self.register_tool(BatchEditTool(self.session))

        # 构建专用 system prompt
        if system_prompt is None:
            self.system_prompt = build_proposal_agent_system_prompt(
                session=self.session,
                tools=self._tool_registry.get_all(),
            )
        else:
            self.system_prompt = system_prompt

