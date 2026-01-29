"""ReAct Agent Core Implementation"""
import json
from enum import Enum, auto
from typing import Optional, Dict, Any, List, TYPE_CHECKING


from .. import OpenAIClient
from ..session.session import Session
from ..clients.base import BaseClient
from ..tools.registry import ToolRegistry
from ..tools.base import Tool
from ..tools.builtin import ReadTool, WriteTool, EditTool, ListDirTool, RunPythonFileTool, RunNodeFileTool
from ..tools.extensions import SkillTool
from ..models import GenerateResponse, TokenUsage
from ..exceptions import NetworkError, RateLimitError, ServerError
from .prompt_builder import build_system_prompt
from .pretty_print import (
    print_system_prompt,
    print_user_message,
    print_assistant_message,
    print_tool_result,
    print_token_usage
)

# Optional: Anthropic is an optional dependency. ReAct loop should still work with OpenAI-only installs.
try:
    from ..clients.anthropic_client import AnthropicClient  # type: ignore
except Exception:  # pragma: no cover
    AnthropicClient = None  # type: ignore

if TYPE_CHECKING:
    from ..clients.banana_image_client import BananaImageClient



class AgentMessageType(Enum):
    SYSTEM=auto()
    USER=auto()
    ASSISTANT=auto()
    ASSISTANT_WITH_TOOL_CALL=auto()
    TOOL_RESPONSE=auto()
    ERROR_TOOL_RESPONSE=auto()
    TOKEN=auto()
    MAXIMUM=auto()


class ReActAgent:
    """ReAct Agent - Reasoning and Acting Loop"""
    
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
        enable_reflection=False,
        reflection_counter=4
    ):
        """
        Initialize ReAct Agent
        
        :param client: LLM client instance
        :param working_dir: Default working directory (optional)
        :param allowed_paths: List of allowed paths
        :param blocked_paths: List of blocked paths
        :param session_id: Session ID (optional, auto-generated UUID if not provided)
        :param system_prompt: Custom system prompt (optional)
        :param vision_client: Optional separate client for vision tools (if not provided, vision tools will not be available)
        :param image_client: Optional BananaImageClient for image editing (if not provided, image editing is not available)
        """
        self.client = client
        self._session = Session(
                working_dir=working_dir,
                client=client,
                allowed_paths=allowed_paths,
                blocked_paths=blocked_paths,
                session_id=session_id,
            vision_client=vision_client,
            image_client=image_client
            )

        # Tool registry
        self._tool_registry = ToolRegistry()
        self._register_default_tools()

        # Default system prompt
        self.system_prompt = system_prompt if system_prompt else build_system_prompt(
            session=self.session,
            tools=self._tool_registry.get_all()
        )

        #reflection
        self.tool_call_list=[]#记录tool call 然后可从后检索来判断是否连续调用 然后反思触发则清除
        self.reflection_counter=reflection_counter #工具连续几次调用触发反思

    def is_consecutive_tool_call(self,tool_name:str)->bool:
        self.tool_call_list.append(tool_name)

        same=self.tool_call_list[-self.reflection_counter:]#取得后四个工具名称

        if len(set(same))==1:#如果后四个工具名称相同 则启动反思
            return True
        return False


    def start_reflection(self,tool_name:str):
        self.tool_call_list.clear()#清除
        return f"""当前工具:{tool_name},已经连续执行{self.reflection_counter},判断是否正常"""

    @property
    def session(self) -> Session:
        """Get Session instance (raises error if not initialized)"""
        if self._session is None:
            raise ValueError("Session not initialized. Please provide working_dir or call run() with working_dir.")
        return self._session
    
    def _register_default_tools(self) -> None:
        """Register default tools"""
        tools = [
            ReadTool(self.session),
            WriteTool(self.session),
            EditTool(self.session),
            ListDirTool(self.session),
            RunPythonFileTool(self.session),
            RunNodeFileTool(self.session),
            SkillTool(self.session),
        ]
        for tool in tools:
            self._tool_registry.register(tool)
    
    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool
        
        :param tool: Tool instance
        """
        if self._session is None:
            raise ValueError("Session not initialized. Cannot register tools without a session.")
        self._tool_registry.register(tool)
    
    def unregister_tool(self, name: str) -> None:
        """
        Unregister a tool
        
        :param name: Tool name
        """
        self._tool_registry.unregister(name)
    
    async def run(
        self,
        prompt: str,
        max_iterations=40,
        stream: bool = False
    ):
        """
        Execute ReAct loop, automatically iterating until no tool calls
        
        :param prompt: User prompt
        :param max_iterations: Maximum number of iterations (default: 60)
        :param stream: Whether to stream output (not supported yet, interface reserved)
        :return: Agent's final response (automatically exits when no tool calls)
        
        Note:
        - If LLM returns no tool call, automatically exit and return response
        - If LLM returns tool calls, execute tools and continue loop
        - Automatically loop until LLM returns non-tool-call response
        """
        # Add system prompt
        self.session.add_message("system", self.system_prompt)
        yield AgentMessageType.SYSTEM, self.system_prompt
        # print_system_prompt(self.system_prompt)
        
        # Add user message
        self.session.add_message("user", prompt)
        yield AgentMessageType.USER, prompt
        # print_user_message(prompt)
        
        # Initialize token usage tracking
        total_usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        
        # ReAct loop: automatically iterate until no tool calls
        max_iterations = max_iterations  # Prevent infinite loop
        iteration = 0
        stop_flag = False

        while iteration < max_iterations and not stop_flag:
            iteration += 1

            # Get tool schemas
            tool_schemas = self._tool_registry.get_schemas()

            if isinstance(self.client, OpenAIClient):
                # Get message list (OpenAI format)
                messages = self.session.get_messages()
                try:
                    # All retry logic is handled in the client layer (openai_client.py)
                    # The client will retry NetworkError, RateLimitError, and ServerError
                    # If it still fails after retries, it will raise the appropriate exception
                    response = await self.client.generate_with_tools(
                        messages=messages,
                        tools=tool_schemas,
                        tool_choice="auto"
                    )
                except (NetworkError, RateLimitError, ServerError) as e:
                    # These errors have been retried by the client, but still failed
                    stop_flag = True
                    error_msg = f"API call failed after client retries: {str(e)}"
                    raise RuntimeError(error_msg) from e
                except Exception as e:
                    # Other errors (APIError, ValidationError, etc.) are not retried
                    stop_flag = True
                    error_msg = f"API call failed: {str(e)}"
                    raise RuntimeError(error_msg) from e

                if response is None:
                    stop_flag = True
                    raise RuntimeError("API returned empty response")

                if isinstance(response, str):
                    stop_flag = True
                    raise RuntimeError(
                        f"API returned unexpected string response (possibly error page): {response[:200]}...")

                # Extract token usage from response
                round_usage = None
                if hasattr(response, 'usage') and response.usage:
                    # Create TokenUsage for this round
                    round_usage = TokenUsage(
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        total_tokens=response.usage.total_tokens
                    )
                    # Accumulate to total usage
                    total_usage.prompt_tokens += response.usage.prompt_tokens
                    total_usage.completion_tokens += response.usage.completion_tokens
                    total_usage.total_tokens += response.usage.total_tokens
                
                # Extract message from response with error handling
                try:
                    if not hasattr(response, 'choices') or not response.choices:
                        stop_flag = True
                        raise RuntimeError("API response has no choices")
                    message = response.choices[0].message
                    tool_calls = message.tool_calls
                except (IndexError, AttributeError) as e:
                    stop_flag = True
                    raise RuntimeError(f"Failed to extract message from API response: {str(e)}") from e
                
                if tool_calls:
                    tool_calls_dict = []
                    for tool_call in tool_calls:
                        tool_calls_dict.append({
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        })
                    
                    assistant_content = message.content if message.content else ""
                    try:
                        self.session.add_message(
                            role="assistant",
                            content=assistant_content,
                            tool_calls=tool_calls_dict
                        )
                    except Exception as e:
                        stop_flag = True
                        raise RuntimeError(f"Failed to add assistant message to session: {str(e)}") from e
                    
                    yield AgentMessageType.ASSISTANT_WITH_TOOL_CALL, assistant_content, tool_calls_dict, round_usage
                    
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        tool_call_id = tool_call.id
                        
                        # Parse function arguments with error handling
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError as e:
                            error_content = json.dumps(
                                {"error": f"Invalid JSON in tool arguments: {str(e)}"},
                                ensure_ascii=False
                            )
                            try:
                                self.session.add_message(
                                    role="tool",
                                    content=error_content,
                                    tool_call_id=tool_call_id
                                )
                            except Exception as session_error:
                                # If session update fails, this is critical - stop the loop
                                stop_flag = True
                                raise RuntimeError(f"Failed to add JSON parse error message to session: {str(session_error)}") from session_error
                            yield AgentMessageType.ERROR_TOOL_RESPONSE, tool_call_id, error_content
                            continue  # Continue to next tool call
                        
                        tool = self._tool_registry.get(function_name)
                        if tool:
                            try:
                                tool_call_result = await tool.execute(**function_args)
                            except Exception as e:
                                # Tool execution failed - record error and continue loop
                                # This allows LLM to see the error and potentially retry or take alternative action
                                error_content = json.dumps(
                                    {"error": f"Tool execution failed: {str(e)}"},
                                    ensure_ascii=False
                                )
                                try:
                                    self.session.add_message(
                                        role="tool",
                                        content=error_content,
                                        tool_call_id=tool_call_id
                                    )
                                except Exception as session_error:
                                    # If session update fails, this is critical - stop the loop
                                    stop_flag = True
                                    raise RuntimeError(f"Failed to add tool error message to session: {str(session_error)}") from session_error
                                yield AgentMessageType.ERROR_TOOL_RESPONSE, tool_call_id, error_content
                                continue  # Continue to next tool call
                            
                            # Serialize tool result with error handling
                            try:
                                result_content = json.dumps(tool_call_result, ensure_ascii=False)
                            except (TypeError, ValueError) as e:
                                # Serialization failed - record error and continue
                                error_content = json.dumps(
                                    {"error": f"Failed to serialize tool result: {str(e)}"},
                                    ensure_ascii=False
                                )
                                try:
                                    self.session.add_message(
                                        role="tool",
                                        content=error_content,
                                        tool_call_id=tool_call_id
                                    )
                                except Exception as session_error:
                                    stop_flag = True
                                    raise RuntimeError(f"Failed to add serialization error message to session: {str(session_error)}") from session_error
                                yield AgentMessageType.ERROR_TOOL_RESPONSE, tool_call_id, error_content
                                continue  # Continue to next tool call
                            
                            try:
                                self.session.add_message(
                                    role="tool",
                                    content=result_content,
                                    tool_call_id=tool_call_id
                                )
                            except Exception as e:
                                # Session update failed - this is critical, stop the loop
                                stop_flag = True
                                raise RuntimeError(f"Failed to add tool result message to session: {str(e)}") from e
                            yield AgentMessageType.TOOL_RESPONSE, tool_call_id, tool_call_result
                        else:
                            error_content = json.dumps(
                                {"error": f"Tool '{function_name}' not found"},
                                ensure_ascii=False
                            )
                            try:
                                self.session.add_message(
                                    role="tool",
                                    content=error_content,
                                    tool_call_id=tool_call_id
                                )
                            except Exception:
                                pass  # If session update fails, still yield the error
                            yield AgentMessageType.ERROR_TOOL_RESPONSE, tool_call_id, error_content
                    
                    continue
                else:
                    assistant_content = message.content if message.content else ""
                    try:
                        self.session.add_message(
                            role="assistant",
                            content=assistant_content
                        )
                    except Exception as e:
                        stop_flag = True
                        raise RuntimeError(f"Failed to add assistant message to session: {str(e)}") from e
                    stop_flag = True
                    yield AgentMessageType.ASSISTANT, assistant_content, round_usage, total_usage

            else:
                stop_flag = True
                raise NotImplementedError(f"Client type {type(self.client)} not yet supported in ReAct loop")

        if not stop_flag:
            yield AgentMessageType.MAXIMUM, "Reached maximum iterations. Please check the task.", total_usage