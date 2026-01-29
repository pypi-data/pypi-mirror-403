"""System Prompt Builder"""
from typing import List, Dict
from ..tools.base import Tool
from ..session.session import Session


def _get_system_info(session: Session) -> Dict[str, str]:
    """
    Extract system information from session
    
    :param session: Session instance
    :return: Dictionary with current_time, os_info, and working_dir
    """
    system_info = session.get_system_info()
    return {
        "current_time": system_info["current_time"],
        "os_info": f"{system_info['os_name']} {system_info['os_release']}",
        "working_dir": session.working_dir
    }


def _build_tools_section(tools: List[Tool]) -> str:
    """
    Build tools description section
    
    :param tools: List of available tools
    :return: Formatted tools section string
    """
    tool_descriptions = [f"- {tool.name}: {tool.description}" for tool in tools]
    return "\n".join(tool_descriptions) if tool_descriptions else "No tools available."


def _build_environment_section(system_info: Dict[str, str]) -> str:
    """
    Build environment information section
    
    :param system_info: Dictionary with system information
    :return: Formatted environment section string
    """
    return f"""## Environment Information
- Current Time: {system_info['current_time']}
- Operating System: {system_info['os_info']}
- Working Directory: {system_info['working_dir']}"""


def _build_tools_list_section(tools_section: str) -> str:
    """
    Build available tools section
    
    :param tools_section: Formatted tools description string
    :return: Formatted tools list section string
    """
    return f"""## Available Tools
You have access to the following tools:
{tools_section}"""


def _build_base_rules(working_dir: str) -> str:
    """
    Build base rules section (common to all prompt types)
    
    :param working_dir: Working directory path
    :return: Formatted base rules section string
    """
    return f"""## Important Rules
- All file operations are restricted to the working directory: {working_dir}
- **CRITICAL: All path parameters in tool calls MUST be absolute paths**
  - If you receive an error "path must be an absolute path, got: ." or similar, you need to convert relative paths to absolute paths
  - Use the working directory ({working_dir}) as the base to construct absolute paths
  - Example: If working directory is "{working_dir}" and you need to access "file.txt", use "{working_dir}/file.txt" or "{working_dir}\\file.txt" (depending on OS)
  - Never use relative paths like ".", "..", "./file.txt", or "../file.txt" - always use full absolute paths
- Be precise and careful with file operations
- If a tool call fails, analyze the error and try alternative approaches"""


def build_system_prompt(
    session: Session,
    tools: List[Tool],
    additional_context: str = ""
) -> str:
    """
    Build system prompt with environment information
    
    :param session: Session instance (contains system information)
    :param tools: List of available tools
    :param additional_context: Additional context information
    :return: System prompt string
    """
    # Get shared components
    system_info = _get_system_info(session)
    tools_section = _build_tools_section(tools)
    environment_section = _build_environment_section(system_info)
    tools_list_section = _build_tools_list_section(tools_section)
    base_rules = _build_base_rules(system_info['working_dir'])
    
    # Build agent-specific sections
    agent_description = "You are a helpful AI assistant working in a controlled environment."
    
    agent_specific_rules = """- Always use tools when you need to interact with the file system or perform operations
- When you have completed the task or determined that you cannot proceed, provide a final response WITHOUT using any tools
- The final response (without tool calls) will terminate the conversation
- **IMPORTANT: Avoid blocking code in files you write**:
  - Do NOT use `plt.show()` or `matplotlib.pyplot.show()` - these will block program execution
  - Do NOT use `input()` or `raw_input()` - these will wait for user input and block execution
  - Instead, use `plt.savefig()` to save plots, or comment out blocking code
  - The write tool will automatically comment out blocking code, but it's better to avoid it from the start"""
    
    tool_usage_guidelines = """## Tool Usage
- When you need to use a tool, call it with the appropriate parameters
- **IMPORTANT: All path parameters must be absolute paths** - never use relative paths like ".", "..", or "./file.txt"
- If you see an error "path must be an absolute path", convert your relative path to an absolute path using the working directory
- After each tool call, you will receive the result
- Use the results to inform your next actions
- Continue using tools until the task is complete, then provide a final response"""
    
    # Assemble prompt
    prompt = f"""{agent_description}

{environment_section}

{tools_list_section}

{base_rules}
{agent_specific_rules}

{tool_usage_guidelines}

{additional_context}
"""
    
    return prompt.strip()


def build_todo_based_system_prompt(
    session: Session,
    tools: List[Tool],
    additional_context: str = ""
) -> str:
    """
    Build system prompt for TODO-based agent with specific workflow
    
    :param session: Session instance (contains system information)
    :param tools: List of available tools
    :param additional_context: Additional context information
    :return: System prompt string for TODO-based agent
    """
    # Get shared components
    system_info = _get_system_info(session)
    tools_section = _build_tools_section(tools)
    environment_section = _build_environment_section(system_info)
    tools_list_section = _build_tools_list_section(tools_section)
    base_rules = _build_base_rules(system_info['working_dir'])
    
    # Build TODO-specific sections
    agent_description = "You are a TODO-based AI assistant working in a controlled environment. Your primary role is to break down complex tasks into manageable TODO items and execute them systematically."
    
    workflow_section = """## Required Workflow (MUST FOLLOW THIS ORDER)

### Step 1: Explore the Working Directory
- **FIRST ACTION**: Use `list_directory` to explore the current working directory
- Understand the project structure and existing files
- This helps you understand the context before creating TODO items

### Step 2: Create TODO List
- After understanding the directory structure, use `create_todo_list` to break down the task into specific, actionable TODO items
- Each TODO item should be clear, specific, and executable
- Organize TODOs in a logical order (dependencies first, then independent tasks)

### Step 3: Execute TODOs Systematically
- Work through each TODO item one by one
- For each TODO item:
  1. Mark it as "in_progress" using `update_todo_status` when you start working on it
  2. Use appropriate tools to complete the task
  3. Mark it as "completed" using `update_todo_status` when finished
  4. If a TODO fails, mark it as "failed" and note the reason

### Step 4: Save Important Artifacts
- **ONLY AFTER ALL TODOs ARE COMPLETED**: Use `save_important_artifacts` to save:
  - Key files that were created or modified
  - Important outputs or results
  - Documentation or summaries
  - Any deliverables that are part of the task completion

### Step 5: Final Response
- After saving artifacts, provide a final summary response WITHOUT using any tools
- The final response (without tool calls) will terminate the conversation
- Summarize what was accomplished and what artifacts were saved"""
    
    todo_specific_rules = """- **ALWAYS start with `list_directory`** to understand the project structure
- **ALWAYS create a TODO list** before starting execution
- **ALWAYS update TODO status** as you progress (in_progress → completed/failed)
- **ALWAYS use `save_important_artifacts`** when all TODOs are completed
- Track your progress by regularly checking TODO status
- **IMPORTANT: Avoid blocking code in files you write**:
  - Do NOT use `plt.show()` or `matplotlib.pyplot.show()` - these will block program execution
  - Do NOT use `input()` or `raw_input()` - these will wait for user input and block execution
  - Instead, use `plt.savefig()` to save plots, or comment out blocking code
  - The write tool will automatically comment out blocking code, but it's better to avoid it from the start"""
    
    tool_usage_guidelines = """## Tool Usage Guidelines
- **IMPORTANT: All path parameters must be absolute paths** - never use relative paths like ".", "..", or "./file.txt"
- If you see an error "path must be an absolute path", convert your relative path to an absolute path using the working directory
- Use `list_directory` first to explore the environment (use absolute path for dir_path parameter)
- Use `create_todo_list` to plan your work
- Use `update_todo_status` to track progress on each TODO
- Use `save_important_artifacts` only after all TODOs are completed (use absolute paths for file paths)
- Use other tools (read_file, write_file, edit_file, etc.) to complete individual TODO items (all require absolute paths)
- Provide final response only after saving artifacts"""
    
    # Assemble prompt
    prompt = f"""{agent_description}

{environment_section}

{tools_list_section}

{workflow_section}

{base_rules}
{todo_specific_rules}

{tool_usage_guidelines}

{additional_context}
"""
    
    return prompt.strip()
