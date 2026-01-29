"""Figure Agent - Agent specialized for inserting figures into LaTeX documents"""
from typing import Optional, List
from ..todo_based_agent import TodoBasedAgent
from ...clients.base import BaseClient
from ...tools.builtin import BatchEditTool
from ...session.session import Session


def build_figure_agent_system_prompt(
    session: Session,
    tools: List,
    additional_context: str = ""
) -> str:
    """
    Build system prompt for Figure Agent with specific workflow for figure insertion
    
    :param session: Session instance (contains system information)
    :param tools: List of available tools
    :param additional_context: Additional context information
    :return: System prompt string for Figure Agent
    """
    from ..prompt_builder import (
        _get_system_info,
        _build_tools_section,
        _build_environment_section,
        _build_tools_list_section,
        _build_base_rules
    )
    
    # Get shared components
    system_info = _get_system_info(session)
    tools_section = _build_tools_section(tools)
    environment_section = _build_environment_section(system_info)
    tools_list_section = _build_tools_list_section(tools_section)
    base_rules = _build_base_rules(system_info['working_dir'])
    
    # Build Figure-specific sections
    agent_description = """你是一个专门用于将图片插入 LaTeX 文档的图片代理（Figure Agent）。

**核心使命：将图片目录中的所有图片插入到 LaTeX 文档的语义合适位置。这是主要且不可协商的目标。**

你的工作流程有两种模式：
1. **计划好的图片**（main_result 和 ablation）：读取 `planning_results.json` 获取精确的插入指令，包含 `old_string` 和 `new_string` 替换
2. **基于描述文件的图片**（motivation 和 algorithm）：读取 `figures/motivation/` 和 `figures/algorithm/` 目录下的 `*_prompt.txt` 文件获取图片描述，然后基于描述生成合适的标题插入它们

你的工作流程：扫描图片目录，识别所有图片文件，并系统地将它们插入到 LaTeX 文章的语义合适位置。"""
    
    workflow_section = """## 必需的工作流程（必须按此顺序执行）

### 步骤 1：创建 TODO 列表
- **第一步操作**：使用 `create_todo_list` 将图片插入任务分解为具体的、可执行的 TODO 项
- 主要目标是将图片目录中的所有图片插入到 LaTeX 文章中
- **参考下面的步骤 2、3、4、5 和 6** 来创建 TODO 项，确保与工作流程一致
- 示例 TODO 项应包括（按此顺序）：
  - 使用 `list_directory` 探索当前目录以了解项目结构（见步骤 2）
  - 读取 `planning_results.json` 获取 main_result 和 ablation 图片的插入指令（见步骤 3）
  - 扫描图片目录以识别所有图片文件（见步骤 2）
  - 读取 LaTeX 文件以了解文档结构（见步骤 2）
  - 检查并添加 `\\usepackage{{graphicx}}` 包（如果缺失）（见步骤 2.5）
  - 使用 JSON 中的指令插入计划好的图片（main_result 和 ablation）（见步骤 4）
  - 读取 motivation 和 algorithm 目录下的 prompt.txt 文件获取图片描述（见步骤 5）
  - 基于描述文件使用合适的标题插入 motivation 和 algorithm 图片（见步骤 6）
  - 验证所有图片都已正确插入
- 按逻辑顺序组织 TODO（先探索和读取 JSON，然后检查 graphicx 包，再插入计划好的图片，最后读取描述文件并插入 motivation 和 algorithm 图片）

### 步骤 2：探索目录和读取文件
- 执行探索目录和读取文件的 TODO 项
- 使用 `list_directory` 探索当前工作目录
- 使用 `list_directory` 扫描图片目录
- 如果图片目录包含子目录，递归扫描它们以找到所有图片文件
- 使用 `read_file` 读取 LaTeX 文件（.tex）以了解文档结构
- 识别文档章节（Introduction、Methodology、Experiments 等）
- 完成后将相应的 TODO 项标记为已完成

### 步骤 2.5：检查并添加 graphicx 包，检测双栏布局
- 执行检查并添加 `\\usepackage{{graphicx}}` 的 TODO 项
- **重要**：在插入任何图片之前，必须确保 LaTeX 文档包含 `\\usepackage{{graphicx}}` 包
- 使用 `read_file` 读取 LaTeX 文档的序言部分（`\\documentclass` 之后的部分）
- 检查文档中是否已包含 `\\usepackage{{graphicx}}` 或 `\\usepackage[options]{{graphicx}}`
- **同时检测双栏布局**：
  - 检查 `\\documentclass` 是否包含 `[twocolumn]` 选项（如 `\\documentclass[twocolumn]{{article}}`）
  - 检查文档中是否包含 `\\twocolumn` 命令
  - 如果检测到双栏布局，**必须**在插入图片时使用 `\\columnwidth` 而不是 `\\textwidth`（见下面的"双栏布局注意事项"）
- 如果**没有**找到 `graphicx` 包：
  - 找到 `\\documentclass` 行
  - 在 `\\documentclass` 之后、`\\begin{{document}}` 之前找到合适的位置（通常在第一个 `\\usepackage` 附近）
  - 使用 `BatchEdit` 工具添加 `\\usepackage{{graphicx}}`
  - 如果检测到双栏布局，考虑同时添加 `\\usepackage{{placeins}}` 以更好地控制浮动体位置
  - 示例：如果文档有 `\\documentclass{{article}}`，在其后添加 `\\usepackage{{graphicx}}`
  - 如果是双栏布局：`\\documentclass[twocolumn]{{article}}`，添加 `\\usepackage{{graphicx}}\n\\usepackage{{placeins}}`
- 如果**已经存在** `graphicx` 包，则跳过添加步骤，但仍需检测双栏布局
- 完成后将相应的 TODO 项标记为已完成

### 步骤 3：读取规划结果 JSON
- 执行读取 `planning_results.json` 的 TODO 项
- 使用 `read_file` 读取 `planning_results.json` 文件
- 解析 JSON 结构以了解：
  - `main_result_figures`：包含 `filename`、`old_string`、`new_string` 和 `description` 的图片列表
  - `ablation_figures`：包含 `filename`、`old_string`、`new_string` 和 `description` 的图片列表
- 注意：这些图片有预定义的插入位置和 LaTeX 代码
- 完成后将相应的 TODO 项标记为已完成

### 步骤 4：插入计划好的图片（main_result 和 ablation）
- 执行插入计划好的图片的 TODO 项
- 对于 `main_result_figures` 和 `ablation_figures` 中的每个图片：
  - 使用 `BatchEdit` 工具在 LaTeX 文档中将 `old_string` 替换为 `new_string`
  - `new_string` 已包含完整的 LaTeX 图片代码，包含正确的路径、标题和标签
  - **重要**：使用 JSON 中的确切 `old_string` 和 `new_string` - 不要修改它们
  - 确保 `new_string` 中的图片路径与实际文件位置匹配（如果路径不同，可能需要调整）
- **策略**：尽可能在一次 BatchEdit 调用中分组多个替换，以最小化工具调用
- 在尝试替换之前，验证所有 `old_string` 模式都存在于 LaTeX 文档中
- 完成后将相应的 TODO 项标记为已完成

### 步骤 5：读取描述文件（motivation 和 algorithm）
- 执行读取 motivation 和 algorithm 图片描述的 TODO 项
- 对于 `figures/motivation/` 和 `figures/algorithm/` 目录中的图片：
  - 扫描目录找到图片文件（如 `motivation_1_*.png`、`algorithm_1_*.png`）
  - 查找对应的描述文件（如 `motivation_1_prompt.txt`、`algorithm_1_prompt.txt`）
  - 使用 `read_file` 读取对应的 `*_prompt.txt` 文件获取图片的详细描述
  - 理解描述内容，确定：
    - 图片显示的内容（motivation 示例、算法图表等）
    - 应该插入到 LaTeX 文档的哪个位置（motivation 插入 Introduction，algorithm 插入 Methodology）
    - 基于描述生成合适的标题
- **注意**：如果目录中有多张图片，选择一张即可（通常选择编号最小的，如 `motivation_1`、`algorithm_1`）
- 完成后将相应的 TODO 项标记为已完成

### 步骤 6：插入基于描述文件的图片（motivation 和 algorithm）
- 执行插入基于描述文件的图片的 TODO 项
- 对于步骤 5 中读取描述的每张图片：
  - 读取 LaTeX 文档以找到语义合适的插入位置
  - 对于 motivation 图片：插入到 Introduction 部分，通常在问题陈述之后
  - 对于 algorithm 图片：插入到 Methodology/Algorithm 部分，通常在算法描述附近
  - 使用 `BatchEdit` 工具插入图片代码块
  - 生成合适的 LaTeX 代码，包含：
    - 正确的 `\\includegraphics` 路径（相对于 LaTeX 文件位置，例如 `figures/motivation/filename.png`）
    - 基于 prompt.txt 描述的描述性标题（简洁地总结图片显示的内容）
    - 唯一标签（例如 `fig:motivation`、`fig:algorithm`）
- **策略**：尽可能在一次 BatchEdit 调用中插入多张图片，以最小化工具调用
- 完成后将相应的 TODO 项标记为已完成

### 步骤 7：系统执行 TODO
- 按照创建顺序逐一处理每个 TODO 项
- 对于每个 TODO 项：
  1. 开始工作时，使用 `update_todo_status` 将其标记为 "in_progress"
  2. 使用适当的工具完成任务
  3. 完成后，使用 `update_todo_status` 将其标记为 "completed"
  4. 如果 TODO 失败，将其标记为 "failed" 并注明原因
- 上面的步骤 2、2.5、3、4、5 和 6 作为此系统 TODO 执行过程的一部分执行

### 步骤 8：保存重要成果
- **仅在所有 TODO 完成后**：使用 `save_important_artifacts` 保存：
  - 包含插入图片的修改后的 LaTeX 文件
  - 图片插入过程的文档或摘要
- **见下面的"关键约束"部分了解文件命名规则**

### 步骤 9：最终响应
- 保存成果后，在不使用任何工具的情况下提供最终摘要响应
- 最终响应（无工具调用）将终止对话
- 总结完成的工作、插入了多少张图片以及保存了哪些成果"""
    
    key_constraints = """## 关键约束

### 文件命名规则（关键）
- 使用 `save_important_artifacts` 保存成果时，**始终保留原始文件名和扩展名**
- **不要创建具有任意或非标准名称的新文件** - 只修改现有的 LaTeX 文件
- 保存修改后的 LaTeX 文件时，使用与原始文件完全相同的文件名
### 核心目标
- **插入图片目录中的所有图片** - 这是主要目标，必须实现
- 图片应放置在相对于周围文本的语义合适位置
    - 通过定期检查 TODO 状态来跟踪进度
    
    ### 双栏布局注意事项（防止文字与图片重叠）
    - **必须检测文档是否使用双栏布局**：
      - 检查 `\\documentclass` 是否包含 `[twocolumn]` 选项
      - 检查文档中是否包含 `\\twocolumn` 命令
    - **在双栏模式下，图片宽度必须使用 `\\columnwidth` 而不是 `\\textwidth`**：
      - 正确（双栏模式）：`\\includegraphics[width=0.95\\columnwidth]{{...}}`
      - 错误（双栏模式）：`\\includegraphics[width=0.95\\textwidth]{{...}}`（会导致图片超出列宽并与文字重叠）
      - 单栏模式可以使用 `\\textwidth`：`\\includegraphics[width=0.8\\textwidth]{{...}}`
    - **推荐在双栏模式下添加 `placeins` 包**：
      - 在序言中添加 `\\usepackage{{placeins}}`
      - 这有助于更好地控制浮动体位置，防止重叠
    - **图片宽度建议**：
      - 双栏模式：使用 `0.95\\columnwidth` 或 `0.9\\columnwidth`（留出边距）
      - 单栏模式：使用 `0.8\\textwidth` 或 `0.6\\textwidth`
    
    ### 关于 caption / label / 引用的强制要求
    - 每一个 `figure` 和 `table` 都必须满足：
      - 有清晰、专业的 `\\caption{{...}}`（不能省略）
      - 有**唯一**的 `\\label{{...}}` 标签，通常采用：
        - 图：`fig:...`（例如 `fig:main_result`、`fig:ablation`）
        - 表：`tab:...`（例如 `tab:main_results`、`tab:ablation`）
    - 正文中**所有**提到图表的地方都要通过 `\\ref{{...}}` 链接到对应标签：
      - 例如：`as is shown in Table~\\ref{{tab:main_results}}`、`as illustrated in Figure~\\ref{{fig:motivation}}`
      - 不允许出现“口头提到表/图但没有 `\\ref{{...}}` 跳转”的情况
    - `\\label{{...}}` 必须写在对应 `figure`/`table` 环境内部，通常放在 `\\caption{{...}}` 之后
    
    ### Caption 和文本内容的学术严谨性检查（必须严格遵守）
    - **在生成或修改任何 `\\caption{{...}}` 或文本内容时，必须严格检查以下规则**：
    
    #### 1. 数学模式转换 (Math Mode)
    - **所有数学变量、状态向量、函数符号必须正确包裹在数学模式中**：
      - 正确：`$R(t)$`、`$J$`、`$A^*$`、`$x_i$`、`$f(x)$`
      - 错误：`R(t)`、`J`、`A^*`（未使用数学模式）
    - **希腊字母必须使用数学模式**：
      - 正确：`$\\alpha$`、`$\\beta$`、`$\\Delta$`、`$\\theta$`
      - 错误：`alpha`、`beta`、`Delta`（未使用数学模式）
    - **数学运算符和关系符号必须在数学模式中**：
      - 正确：`$\\leq$`、`$\\geq$`、`$\\neq$`、`$\\in$`、`$\\sum$`、`$\\prod$`
      - 错误：`<=`、`>=`、`!=`、`in`（未使用数学模式）
    - **数值范围、负号、减号在数学上下文中应使用数学模式**：
      - 正确：`$-12.1$`、`$[0, 1]$`、`$x - y$`
      - 错误：`-12.1`、`[0, 1]`、`x - y`（在数学上下文中未使用数学模式）
    
    #### 2. 转义字符处理 (Character Escaping)
    - **百分号 (%)**：必须转义为 `\\%`
      - 正确：`10\\% improvement`、`accuracy of 95\\%`
      - 错误：`10% improvement`（会导致该行后续代码被注释掉，引发编译报错）
    - **下划线 (_)**：在文本模式中必须转义为 `\\_`
      - 正确：`variable\\_name`、`file\\_path`
      - 错误：`variable_name`（在文本模式中会引发编译错误）
      - 注意：在数学模式中（`$...$`）下划线不需要转义，如 `$x_i$` 是正确的
    - **和号 (&)**：必须转义为 `\\&`
      - 正确：`A \\& B`
      - 错误：`A & B`（在表格等环境中会引发错误）
    - **井号 (#)**：必须转义为 `\\#`
      - 正确：`number\\#1`
      - 错误：`number#1`（会引发编译错误）
    - **美元符号 ($)**：必须转义为 `\\$`
      - 正确：`cost is \\$100`
      - 错误：`cost is $100`（会被误认为数学模式开始）
    - **大括号 ({})**：在文本中必须转义为 `\\{{` 和 `\\}}`
      - 正确：`set \\{{1, 2, 3\\}}`
      - 错误：`set {1, 2, 3}`（会被误认为 LaTeX 命令）
    
    #### 3. 下标规范化 (Subscript Logic)
    - **变量下标（索引变量）应保持斜体**：
      - 正确：`$x_i$`、`$A_{ij}$`、`$n_k$`（下标是变量，保持斜体）
      - 注意：在数学模式中，下标默认是斜体，这是正确的
    - **说明性/缩写下标应使用 `\\mathrm{{}}` 或 `\\text{{}}` 转为正体**：
      - 正确：`$x_{\\mathrm{{co}}}$`、`$f_{\\mathrm{{max}}}$`、`$v_{\\mathrm{{in}}}$`、`$A_{\\text{{opt}}}$`
      - 错误：`$x_{co}$`、`$f_{max}$`、`$v_{in}$`（说明性下标应使用正体）
    - **常见说明性下标示例**：
      - `\\mathrm{{min}}`、`\\mathrm{{max}}`、`\\mathrm{{avg}}`、`\\mathrm{{std}}`
      - `\\mathrm{{in}}`、`\\mathrm{{out}}`、`\\mathrm{{co}}`、`\\mathrm{{opt}}`
      - `\\mathrm{{ref}}`、`\\mathrm{{true}}`、`\\mathrm{{pred}}`
    
    #### 4. 标点与结构 (Punctuation & Structure)
    - **Caption 开头应有一个清晰的标题（名词短语）**：
      - 正确：`\\caption{{Main results comparison. The proposed method outperforms baselines.}}`
      - 正确：`\\caption{{Algorithm workflow.}}`
    - **解释性句子的句末必须有句号**：
      - 正确：`\\caption{{Performance comparison. Our method achieves 95\\% accuracy.}}`
      - 错误：`\\caption{{Performance comparison. Our method achieves 95\\% accuracy}}`（缺少句号）
    - **英文字符与数字/公式之间的间距**：
      - LaTeX 通常自动处理间距，但需注意文本与公式的衔接
      - 正确：`accuracy of $95\\%$`（LaTeX 会自动添加适当间距）
      - 正确：`value $x_i$ is computed`（LaTeX 会自动添加适当间距）
    - **Caption 结构建议**：
      - 第一句：简洁的标题性描述（名词短语或简短句子）
      - 后续句子：详细解释（如果需要）
      - 示例：`\\caption{{Experimental setup. (a) Training configuration. (b) Evaluation metrics.}}`
    
    #### 5. 综合检查清单
    - 在生成或修改任何 caption 或文本内容后，必须逐一检查：
      1. ✅ 所有数学变量、符号是否都包裹在 `$...$` 中？
      2. ✅ 所有特殊字符（`%`, `_`, `&`, `#`, `$`, `{{`, `}}`）是否已正确转义？
      3. ✅ 说明性下标是否使用了 `\\mathrm{{}}` 或 `\\text{{}}`？
      4. ✅ Caption 是否有清晰的标题开头？
      5. ✅ 所有句子是否以句号结尾？
      6. ✅ 文本与公式之间的衔接是否自然？
    """
    
    tool_usage_guidelines = """## 工具使用指南

### list_directory
- 使用 `list_directory` 探索目录结构
- 扫描主图片目录以识别所有图片文件
- 如果有子目录，分别扫描每个子目录以列出所有图片文件
- 注意：`list_directory` 是非递归的 - 你需要为每个子目录单独调用它

### read_file
- 使用 `read_file` 读取 LaTeX 文档
- 使用 `read_file` 读取 `planning_results.json` 以获取计划图片的插入指令
- **读取描述文件**：读取 `figures/motivation/` 和 `figures/algorithm/` 目录下的 `*_prompt.txt` 文件获取图片描述
  - 例如：`figures/motivation/motivation_1_prompt.txt`、`figures/algorithm/algorithm_1_prompt.txt`
  - 描述文件包含图片的详细说明，用于生成合适的 LaTeX caption
- 理解文档结构（章节、子章节）
- 基于文档内容和图片上下文识别合适的插入位置
- 查找章节标记，如 `\\section{Introduction}`、`\\section{Methodology}`、`\\section{Experiments}`
- **检查 graphicx 包**：读取文档序言部分，检查是否包含 `\\usepackage{{graphicx}}`

### BatchEdit（图片插入和包管理）
- **效率要求**：在每次调用中插入**尽可能多的图片**，以最小化工具调用
- **添加 graphicx 包**（在插入图片之前）：
  - 如果文档中缺少 `\\usepackage{{graphicx}}`，使用 `BatchEdit` 添加它
  - 找到 `\\documentclass{{...}}` 行
  - 在其后找到合适的位置（通常在第一个 `\\usepackage` 之后）
  - 如果已有其他 `\\usepackage`，在它们之后添加；如果没有，直接在 `\\documentclass` 后添加
  - 示例替换：
    - `old_string`: `\\documentclass{{article}}`
    - `new_string`: `\\documentclass{{article}}\n\\usepackage{{graphicx}}`
    - 或者如果已有其他包：
    - `old_string`: `\\usepackage{{amsmath}}`
    - `new_string`: `\\usepackage{{amsmath}}\n\\usepackage{{graphicx}}`
  - **重要**：确保 `\\usepackage{{graphicx}}` 在 `\\begin{{document}}` 之前
- **对于计划好的图片（main_result 和 ablation）**：
  - 使用 `planning_results.json` 中的确切 `old_string` 和 `new_string`
  - `new_string` 已包含完整的 LaTeX 图片代码
  - 验证 `new_string` 中的图片路径是否与实际文件位置匹配（如需要则调整）
  - 尽可能在一次 BatchEdit 调用中分组多个替换
- **对于基于描述文件的图片（motivation 和 algorithm）**：
  - 仔细阅读 LaTeX 文档以理解完整上下文
  - 基于 prompt.txt 文件中的描述识别语义合适的位置
  - 按预期插入位置对图片进行分组
  - 尽可能在一次 BatchEdit 调用中插入多张图片
- **LaTeX 图片代码模板**（用于基于描述文件的图片）：
  - **单栏模式模板**：
  ```latex
  \\begin{{figure}}[htbp]
      \\centering
      \\includegraphics[width=0.8\\textwidth]{{figures/{subdir}/{filename}}}
      \\caption{{基于 prompt.txt 描述的简洁标题}}
      \\label{{fig:{label}}}
  \\end{{figure}}
  ```
  - **双栏模式模板**（必须使用 `\\columnwidth`）：
    ```latex
    \\begin{{figure}}[htbp]
        \\centering
        \\includegraphics[width=0.95\\columnwidth]{{figures/{subdir}/{filename}}}
        \\caption{{基于 prompt.txt 描述的简洁标题}}
        \\label{{fig:{label}}}
    \\end{{figure}}
    ```
- **重要**：
  - **在插入图片前，必须先检测文档是否使用双栏布局**（见步骤 2.5）
  - **根据布局模式选择正确的宽度单位**：
    - 双栏模式：**必须**使用 `\\columnwidth`（如 `0.95\\columnwidth`）
    - 单栏模式：使用 `\\textwidth`（如 `0.8\\textwidth`）
  - 在 BatchEdit 的 old_string 和 new_string 中使用双反斜杠（`\\\\`）
  - 对于计划好的图片：使用 JSON 中的确切字符串，但**如果检测到双栏布局，需要将 JSON 中的 `\\textwidth` 替换为 `\\columnwidth`**
  - 对于 motivation 和 algorithm 图片：基于 prompt.txt 文件中的描述生成简洁的描述性标题
  - 使用有意义且**全局唯一**的标签（如 `fig:motivation`、`fig:algorithm`、`fig:main_result_1`、`tab:main_results` 等），避免与现有 `\\label{{...}}` 冲突
  - 确保正文中凡是提到这些图表的地方，都通过 `\\ref{{...}}` 进行引用，例如 `as is shown in Table~\\ref{{tab:main_results}}`
  - 确保图片路径相对于 LaTeX 文件位置（如果存在子目录则包含子目录）

### save_important_artifacts
- 在**所有图片插入后**使用 `save_important_artifacts` 保存修改后的 LaTeX 文件
- **见上面的"关键约束"部分了解文件命名规则**"""
    
    # Assemble prompt
    prompt = f"""{agent_description}

{environment_section}

{tools_list_section}

{key_constraints}

{workflow_section}

{base_rules}

{tool_usage_guidelines}

{additional_context}
"""
    
    return prompt.strip()


class FigureAgent(TodoBasedAgent):
    """Figure Agent specialized for inserting figures into LaTeX documents"""
    
    def __init__(
        self,
        client: BaseClient,
        working_dir: Optional[str],
        allowed_paths: Optional[List[str]] = None,
        blocked_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize Figure Agent
        
        :param client: LLM client instance
        :param working_dir: Default working directory (optional)
        :param allowed_paths: List of allowed paths
        :param blocked_paths: List of blocked paths
        :param session_id: Session ID (optional, auto-generated UUID if not provided)
        :param system_prompt: Custom system prompt (optional)
        """
        # Initialize parent TodoBasedAgent (without system_prompt first)
        # This will register default tools (ReadTool, WriteTool, EditTool, ListDirTool, RunPythonFileTool)
        # and TODO tools (CreateTodoListTool, UpdateTodoStatusTool, SaveImportantArtifactsTool)
        super().__init__(
            client=client,
            working_dir=working_dir,
            allowed_paths=allowed_paths,
            blocked_paths=blocked_paths,
            session_id=session_id,
            system_prompt=None  # We'll set it after removing unnecessary tools and replacing EditTool
        )
        
        # Remove run_python_file tool (not needed for figure insertion tasks)
        self.unregister_tool("run_python_file")
        
        # Remove Write tool (not needed for figure insertion tasks - use batch_edit for modifications, save_important_artifacts for saving)
        self.unregister_tool("Write")  # WriteTool 的工具名称是 "Write"
        
        # Replace EditTool with BatchEditTool
        self.unregister_tool("Edit")
        self.register_tool(BatchEditTool(self.session))
        
        # Build Figure Agent system prompt with all tools (excluding run_python_file and Write)
        if system_prompt is None:
            self.system_prompt = build_figure_agent_system_prompt(
                session=self.session,
                tools=self._tool_registry.get_all()
            )
        else:
            self.system_prompt = system_prompt
    
    def _get_available_tools_info(self) -> str:
        """
        Get information about available tools for documentation purposes.
        
        Note: This method provides information about the tools available to FigureAgent.
        The FigureAgent has access to:
        - 3 default tools (ReadTool, BatchEditTool, ListDirTool) - WriteTool and EditTool removed/replaced
        - 3 TODO tools (CreateTodoListTool, UpdateTodoStatusTool, SaveImportantArtifactsTool)
        Total: 6 tools (reads prompt.txt files for motivation and algorithm figure descriptions)
        """
        return """The FigureAgent has access to:
        - 3 default tools (ReadTool, BatchEditTool, ListDirTool) - WriteTool and EditTool removed/replaced
        - 3 TODO tools (CreateTodoListTool, UpdateTodoStatusTool, SaveImportantArtifactsTool)
        Total: 6 tools (reads prompt.txt files for motivation and algorithm figure descriptions instead of using vision analysis)"""

