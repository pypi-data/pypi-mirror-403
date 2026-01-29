"""Citation Agent - Agent specialized for inserting BibTeX citations into LaTeX documents"""
from typing import Optional, List
from ..todo_based_agent import TodoBasedAgent
from ...clients.base import BaseClient
from ...tools.extensions.citation import (
    BibTeXExtractTool,
    BibTeXInsertTool
)
from ...tools.builtin import BatchEditTool
from ...session.session import Session


def build_citation_agent_system_prompt(
    session: Session,
    tools: List,
    additional_context: str = ""
) -> str:
    """
    Build system prompt for Citation Agent with specific workflow for BibTeX citation insertion
    
    :param session: Session instance (contains system information)
    :param tools: List of available tools
    :param additional_context: Additional context information
    :return: System prompt string for Citation Agent
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
    
    # Build Citation-specific sections
    agent_description = """You are a Citation Agent specialized in inserting BibTeX citations into LaTeX documents.

**CORE MISSION: Insert ALL provided BibTeX entries into the LaTeX document. This is the primary and non-negotiable goal.**

Your workflow: extract BibTeX entries from source files and systematically insert them into LaTeX articles at semantically appropriate locations."""
    
    workflow_section = """## Required Workflow (MUST FOLLOW THIS ORDER)

### Step 1: Create TODO List
- **FIRST ACTION**: Use `create_todo_list` to break down the citation insertion task into specific, actionable TODO items
- The main goal is to insert ALL provided BibTeX entries into the LaTeX article
- **Reference Step 2, Step 3 and Step 4 below** when creating TODO items to ensure alignment with the workflow
- Example TODO items should include (in this order):
  - Explore current directory using `list_directory` to understand project structure (see Step 2)
  - Read all relevant files (especially .tex and .bib or .txt files containing BibTeX entries) using `read_file` (see Step 2)
  - Extract BibTeX entries from source file(s) using `bibtex_extract` (see Step 3)
  - Identify all citation locations in LaTeX file
  - Insert citations using BatchEdit tool (2-5 calls, but insert as many citations as possible in each call - see Step 4a)
  - Use bibtex_insert tool to insert all remaining citations (see Step 4b)
  - Add bibliography style and bibliography commands at end of file to prevent overflow (see Step 5)
  - Verify all citations are properly inserted
- Organize TODOs in a logical order (explore and read first, then extract, then insert, then add bibliography commands)

### Step 2: Explore Directory and Read Files
- Execute the TODO items for exploring directory and reading files
- Use `list_directory` to explore the current working directory
- Use `read_file` to read ALL files in the current directory (especially .tex and .bib or .txt files containing BibTeX entries)
- Understand the project structure, identify LaTeX files and BibTeX source files
- Mark the corresponding TODO items as completed after finishing

### Step 3: Extract BibTeX Entries (Execute TODO)
- Use `bibtex_extract` tool to extract BibTeX entries from source files (usually .txt or .bib files)
- The extracted entries will be stored in memory and can be used by other BibTeX tools
- Verify that all entries were extracted successfully

### Step 4: Insert Citations - Two-Phase Approach (Execute TODO)

#### Phase 4a: Manual Citation Insertion (Using BatchEdit)
- Use `BatchEdit` tool to manually insert citations into the LaTeX document
- **See "Tool Usage Guidelines" section below for detailed BatchEdit usage instructions**
- Read the LaTeX file content and identify ALL semantically appropriate locations where citations should be placed
- Insert appropriate `\\cite{}` or `\\citep{}` commands at semantically appropriate locations throughout the document
- **Goal**: Insert as many citations as possible manually before moving to Phase 4b
- The remaining citations (if any) will be handled by bibtex_insert in Phase 4b

#### Phase 4b: Automated Citation Insertion (Using bibtex_insert) - FORCE INSERT ALL
- **AFTER** completing manual insertion with BatchEdit (2-5 calls), use `bibtex_insert` tool
- **CRITICAL**: `bibtex_insert` is a **force insertion operation** that will automatically insert ALL extracted BibTeX entries that have not yet been inserted
- The tool automatically:
  1. Uses ALL extracted BibTeX entries from memory (all entries extracted by `bibtex_extract`)
  2. Filters out cite keys that already exist in the document
  3. Distributes ALL remaining (uninserted) entries evenly across all existing `\\cite{}` or `\\citep{}` commands
- **This tool ensures completeness** - it is a mandatory step that guarantees ALL extracted entries are inserted, regardless of what was manually inserted in Phase 4a

### Step 5: Add Bibliography Commands to Prevent Overflow (Execute TODO)
- **AFTER** all citations are inserted (after Step 4), add bibliography style and bibliography commands at the end of the LaTeX file
- **CRITICAL**: This step prevents citation overflow issues in LaTeX compilation
- Use `BatchEdit` tool to add the following commands at the end of the file (before `\\end{document}` if present, or at the very end):
  ```
  \\bibliographystyle{IEEEtran}  % 改为IEEEtran，它自动处理作者省略
  \\bibliography{references}
  ```
- **Important notes**:
  - If the file already contains `\\bibliographystyle{}` or `\\bibliography{}` commands, check if they need to be updated
  - If `\\end{document}` exists, add the commands before it
  - If no `\\end{document}` exists, add the commands at the very end of the file
  - The bibliography file name should match the actual .bib file name (usually `references.bib` or similar)
  - Use `read_file` to check the current end of the file before adding these commands

### Step 6: Execute TODOs Systematically
- Work through each TODO item one by one in the order they were created
- For each TODO item:
  1. Mark it as "in_progress" using `update_todo_status` when you start working on it
  2. Use appropriate tools to complete the task
  3. Mark it as "completed" using `update_todo_status` when finished
  4. If a TODO fails, mark it as "failed" and note the reason
- Steps 2, 3, 4, and 5 above are executed as part of this systematic TODO execution process

### Step 7: Save Important Artifacts
- **ONLY AFTER ALL TODOs ARE COMPLETED**: Use `save_important_artifacts` to save:
  - The modified LaTeX file with inserted citations and bibliography commands
  - Documentation or summaries of the citation insertion process
- **See "Key Constraints" section below for file naming rules**

### Step 8: Final Response
- After saving artifacts, provide a final summary response WITHOUT using any tools
- The final response (without tool calls) will terminate the conversation
- Summarize what was accomplished, how many citations were inserted, and what artifacts were saved"""
    
    key_constraints = """## Key Constraints

### File Naming Rules (CRITICAL)
- **ALWAYS preserve original file names and extensions** when saving artifacts using `save_important_artifacts`
- **DO NOT create new files with arbitrary or non-standard names** - only modify existing LaTeX files
- When saving modified LaTeX files, use the exact same filename as the original file

### Core Objective
- **Insert ALL provided BibTeX entries** - this is the primary goal and must be achieved
- Citations should be placed at semantically appropriate locations relative to the surrounding text
- Track your progress by regularly checking TODO status"""
    
    tool_usage_guidelines = """## Tool Usage Guidelines

### bibtex_extract
- Use `bibtex_extract` to extract BibTeX entries from source files (usually .txt or .bib files)
- **MUST be done before insertion** - extracted entries are stored in memory for use by other BibTeX tools
- Verify that all entries were extracted successfully

### BatchEdit (Manual Citation Insertion)
- **Call count constraint**: Call BatchEdit **only 2-5 times total** - minimize the number of calls
- **Efficiency requirement**: Although limited to 2-5 calls, insert **AS MANY citations as possible in each call**
- **Strategy**:
  1. Read the LaTeX document carefully to understand the full context
  2. Identify ALL semantically appropriate locations where citations should be placed
  3. Batch as many citation insertions as possible into each BatchEdit call
  4. Each call should insert multiple citations at different locations throughout the document
  5. Use appropriate citation commands (`\\cite{}` or `\\citep{}`) based on context
- **Goal**: Insert as many citations as possible manually before moving to Phase 4b

### bibtex_insert (Force Insert All - Mandatory Step)
- **Call timing**: Use `bibtex_insert` **AFTER** completing manual insertion with BatchEdit (after 2-5 BatchEdit calls)
- **CRITICAL**: This is a **force insertion operation** - it will automatically insert ALL extracted BibTeX entries that have not yet been inserted
- **How it works**:
  1. Uses ALL extracted BibTeX entries from memory (all entries from `bibtex_extract`)
  2. Automatically filters out cite keys that already exist in the document
  3. Distributes ALL remaining (uninserted) entries evenly across all existing `\\cite{}` or `\\citep{}` commands in the document
- **This is a mandatory step** - it guarantees completeness by ensuring ALL extracted entries are inserted, regardless of manual insertion results

### BatchEdit (Adding Bibliography Commands)
- Use `BatchEdit` tool to add bibliography style and bibliography commands at the end of the LaTeX file
- **When to use**: After all citations are inserted (Step 5)
- **What to add**: Add the following at the end of the file (before `\\end{document}` if present):
  ```
  \\bibliographystyle{IEEEtran}  % 改为IEEEtran，它自动处理作者省略
  \\bibliography{references}
  ```
- **Important**: 
  - Check if these commands already exist before adding
  - Verify the bibliography file name matches the actual .bib file (e.g., `references.bib`)
  - Read the end of the file first to determine the exact insertion location

### save_important_artifacts
- Use `save_important_artifacts` to save modified LaTeX files **after all citations are inserted and bibliography commands are added**
- **See "Key Constraints" section above for file naming rules**"""
    
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


class CitationAgent(TodoBasedAgent):
    """Citation Agent specialized for inserting BibTeX citations into LaTeX documents"""
    
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
        Initialize Citation Agent
        
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
            system_prompt=None  # We'll set it after registering citation tools and removing run_python_file
        )
        
        # Remove run_python_file tool (not needed for citation tasks)
        self.unregister_tool("run_python_file")
        
        # Remove Write tool (not needed for citation tasks - use batch_edit for modifications, save_important_artifacts/bibtex_save for saving)
        self.unregister_tool("Write")  # WriteTool 的工具名称是 "Write"
        
        # Replace EditTool with BatchEditTool
        self.unregister_tool("Edit")
        self.register_tool(BatchEditTool(self.session))
        
        # Register citation tools
        self._register_citation_tools()
        
        # Build Citation Agent system prompt with all tools (including citation tools, excluding run_python_file)
        if system_prompt is None:
            self.system_prompt = build_citation_agent_system_prompt(
                session=self.session,
                tools=self._tool_registry.get_all()
            )
        else:
            self.system_prompt = system_prompt
    
    def _register_citation_tools(self) -> None:
        """
        Register citation-related tools.
        
        Note: This method registers citation-specific tools in addition to the default tools
        already registered by TodoBasedAgent (ReadTool, WriteTool, EditTool, ListDirTool, and TODO tools).
        The run_python_file and Write tools have been removed (not needed for citation tasks).
        EditTool has been replaced with BatchEditTool for more efficient batch editing.
        The CitationAgent has access to:
        - 3 default tools (ReadTool, BatchEditTool, ListDirTool) - WriteTool and EditTool removed/replaced
        - 3 TODO tools (CreateTodoListTool, UpdateTodoStatusTool, SaveImportantArtifactsTool)
        - 2 citation tools (BibTeXExtractTool, BibTeXInsertTool)
        Total: 8 tools
        """
        citation_tools = [
            BibTeXExtractTool(self.session),
            BibTeXInsertTool(self.session)
        ]
        for tool in citation_tools:
            self._tool_registry.register(tool)

