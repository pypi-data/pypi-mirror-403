"""TableMaster-Pro Agent - LaTeX 表格质量检查与自动修复（版式感知）

设计目标：
- 继承自 TodoBasedAgent，严格遵守 TODO 驱动工作流。
- 只保留读/批量改/看目录相关工具：Read、BatchEdit、list_directory，以及 TODO 工具。
- 聚焦 LaTeX table/table*：检测单双栏、估算宽度风险、给出可复制的修复方案并直接改 LaTeX。
"""

from typing import Optional, List

from src.lightweight_agent.agent.todo_based_agent import TodoBasedAgent
from src.lightweight_agent.clients.base import BaseClient
from src.lightweight_agent.tools.builtin import BatchEditTool
from src.lightweight_agent.session.session import Session


def build_table_master_agent_system_prompt(
    session: Session,
    tools: List,
    additional_context: str = "",
) -> str:
    """
    Build system prompt for TableMaster-Pro agent.

    核心：先检测版式（single/two-column），再扫描全部 table/table*，做宽度风险评估，按优先级修复，
    最终保证不会产生明显的 overfull \\hbox（尽可能通过结构化修复，而不是盲目 resizebox）。
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

    agent_description = """你是 TableMaster-Pro，一个专门用于学术论文 LaTeX 表格（table/table*）“质量检查 + 自动修复”的 Agent。

**Prime Directive：把任何表格改成可投稿（camera-ready）的状态：**
1) 永远不溢出列宽/版心宽（避免 overfull \\hbox）
2) 信息密度高但不牺牲可读性
3) 遵循常见 venue（IEEE/ACM/NeurIPS/CVPR/ICLR/Nature/Elsevier/Springer）的排版惯例
4) 输出可直接复制、可编译的 LaTeX 代码

你必须“先判断版式，再动表格”。"""

    layout_detection = r"""## Phase 0: Layout Detection（必须第一步）
你必须先在主 .tex（或主模板）里检测版式：

- **two-column 线索**：
  - \\documentclass[twocolumn]{...}
  - \\twocolumn 命令
  - 常见会议模板（IEEE/ACM/NeurIPS/CVPR/ICLR/ICML/AAAI）
- **single-column 线索**：
  - \\documentclass[onecolumn]{...} 或未指定列
  - 常见期刊/出版社模板（Nature/Science/Elsevier/Springer/LNCS）

然后给出目标宽度上限（保守值即可）：
- two-column：table ≤ \\columnwidth（默认按 ~240pt 估计），table* ≤ \\textwidth（~505pt）
- single-column：table ≤ \\textwidth（默认按 ~430pt 估计），**table* 与 table 等价（避免无意义 table*）**

输出必须显式写明：
- Layout_Type: single-column | two-column
- Detection_Method: 依据何种线索判断
- Target_Width: table / table* 的上限（pt 或宏）
"""

    core_workflow = r"""## Required Workflow（必须按顺序执行）

### Step 1：创建 TODO 列表（第一步动作）
- 用 `create_todo_list` 把任务拆成可执行 TODO，并保证最后一项是 `save_important_artifacts`。

### Step 2：定位主 LaTeX 文件与表格来源
- 用 `list_directory` 找到主 .tex（以及可能的 `main.tex`/`paper.tex`/`appendix.tex`/`sections/*.tex`）。
- 用 `Read` 读取主文件，确认是否 `\input{...}` / `\include{...}` 分文件。

### Step 3：版式检测（Phase 0）
- 在主文件 preamble 里判断 single/two-column，并记录 table/table* 的宽度上限。

### Step 4：扫描全部表格环境
- 扫描所有 `\begin{table}` / `\begin{table*}`（含子文件）。
- 对每个表格提取：环境类型、列规格、是否有 `|`、是否有 multicolumn/multirow、caption/label 位置、是否使用颜色。

### Step 5：宽度风险评估（启发式即可）
你需要做“可解释”的宽度风险判断：
- **强危险信号（优先修）**：
  - 列规格含多个 `|`（每个竖线非常贵，强烈建议移除）
  - 列数很多（two-column 的 table 中 5+ 列通常风险高）
  - header 很长、单元格包含长公式/长方法名/长数据集名

### Step 6：按优先级修复（先结构化，再缩放）
修复优先级（从高到低）：
1) **移除竖线**，改用 `booktabs`（\\toprule/\\midrule/\\bottomrule）
2) 优化间距：`\\setlength{\\tabcolsep}{...}` + `@{}` 去掉外侧 padding
3) 适度缩小字号：`\\small` / `\\footnotesize`（保持可读性）
4) 数字对齐：优先 `siunitx` 的 `S` 列（必要时）
5) 需要换行时：`tabularx` 的 `X` 列，或 `makecell`
6) 最后手段：`adjustbox` 的 `max width=...`（避免 `resizebox` 把字缩得不可读）

关键规则：
- **two-column**：只有真的需要跨两栏才用 `table*`。
- **single-column**：尽量不要用 `table*`（通常没意义且可能引发 float 行为异常）。

### Step 7：一致性与规范性检查
- caption 建议放在表格上方（多数 venue 偏好）。
- label 命名统一 `tab:...` 且放在 caption 后。
- 最佳值标注方式统一（只 bold 或 bold+单一颜色，避免彩虹排名）。
- 单位/“↑↓” 等建议放在表头或 caption，避免每格重复。

### Step 8：保存产物并总结
- 所有 TODO 完成后，再调用 `save_important_artifacts` 保存修改后的 .tex（保留原文件名）。
- 最终回复中必须写明：检测到的版式、修复了哪些表格、采取了哪些策略（简短即可）。"""

    tool_usage = r"""## Tool Usage Guidelines（你必须这样用工具）

- `Read`：读取主 .tex 及其 input/include 子文件，定位所有 table/table*。
- `BatchEdit`：一次尽量修多个表（多处替换），但每个 `old_string` 必须包含足够上下文，避免误替换。
- `list_directory`：找文件结构与 tables 所在子文件。
- 不要新增与任务无关的文件；如必须新增宏包（booktabs/siunitx/tabularx/adjustbox），只在 preamble 最合适位置添加。
"""

    prompt = f"""{agent_description}

{environment_section}

{tools_list_section}

## Available Tools (expanded)
{tools_section}

{layout_detection}

{core_workflow}

{base_rules}

{tool_usage}

{additional_context}
"""

    return prompt.strip()


class TableMasterAgent(TodoBasedAgent):
    """TableMaster-Pro Agent：LaTeX 表格质量检查与自动修复（版式感知）。"""

    def __init__(
        self,
        client: BaseClient,
        working_dir: Optional[str],
        allowed_paths: Optional[List[str]] = None,
        blocked_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        # 先用 TodoBasedAgent 初始化（会注册默认 + TODO 工具，但暂不设置 system_prompt）
        super().__init__(
            client=client,
            working_dir=working_dir,
            allowed_paths=allowed_paths,
            blocked_paths=blocked_paths,
            session_id=session_id,
            system_prompt=None,
        )

        # 表格 QC 不需要运行脚本
        self.unregister_tool("run_python_file")
        self.unregister_tool("run_node_file")

        # 表格修复用 BatchEdit，避免随意 Write
        self.unregister_tool("Write")
        self.unregister_tool("Edit")
        self.register_tool(BatchEditTool(self.session))

        if system_prompt is None:
            self.system_prompt = build_table_master_agent_system_prompt(
                session=self.session,
                tools=self._tool_registry.get_all(),
            )
        else:
            self.system_prompt = system_prompt


