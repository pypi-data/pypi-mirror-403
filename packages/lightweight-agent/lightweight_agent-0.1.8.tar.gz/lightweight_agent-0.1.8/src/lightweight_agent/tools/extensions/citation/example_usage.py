"""Example usage of BibTeX Tools"""
import asyncio
from lightweight_agent import ReActAgent, OpenAIClient
from lightweight_agent.tools.extensions import (
    BibTeXExtractTool,
    BibTeXInsertTool,
    BibTeXSaveTool
)


async def example():
    """Example of using BibTeX Tools"""
    
    # 1. 创建客户端和 Agent
    client = OpenAIClient(api_key="your-api-key")
    agent = ReActAgent(
        client=client,
        working_dir="./workspace"
    )
    
    # 2. 注册所有 BibTeX 工具
    extract_tool = BibTeXExtractTool(agent.session)
    insert_tool = BibTeXInsertTool(agent.session)
    save_tool = BibTeXSaveTool(agent.session)
    
    agent.register_tool(extract_tool)
    agent.register_tool(insert_tool)
    agent.register_tool(save_tool)
    
    # 3. 使用工具（通过 Agent 调用）
    # Agent 会自动调用工具，以下是手动调用的示例：
    
    # 提取 BibTeX 条目
    result = await extract_tool.execute(
        input_file="references.txt"
    )
    print("Extract result:", result)
    
    # 插入到 LaTeX 文件
    result = await insert_tool.execute(
        input_file="paper.tex",
        output_file="paper_with_citations.tex"
    )
    print("Insert result:", result)
    
    # 保存 BibTeX 条目
    result = await save_tool.execute(
        output_file="extracted_references.bib"
    )
    print("Save result:", result)


if __name__ == "__main__":
    asyncio.run(example())
