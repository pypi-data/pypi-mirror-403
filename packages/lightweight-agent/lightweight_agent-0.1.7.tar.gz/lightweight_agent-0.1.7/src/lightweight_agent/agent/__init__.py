"""Agent Module"""
from .react_agent import ReActAgent
from .todo_based_agent import TodoBasedAgent
from .prompt_builder import build_system_prompt

# Extension agents
from .extension.citation_agent import CitationAgent
from .extension.figure_agent import FigureAgent
from .extension.polish_agent import PolishAgent
from .extension.matplotlib_fix_agent import MatplotlibFixAgent
from .extension.proposal_agent import ProposalAgent
from .extension.revision_agent import RevisionAgent
from src.lightweight_agent.agent.extension.discarded.table_master_agent import TableMasterAgent

__all__ = [
    "ReActAgent",
    "TodoBasedAgent",
    "build_system_prompt",
    "CitationAgent",
    "FigureAgent",
    "PolishAgent",
    "MatplotlibFixAgent",
    "ProposalAgent",
    "RevisionAgent",
    "TableMasterAgent",
    "ImageEditAgent",
]

