"""
百度AI搜索 MCP服务器

提供百度AI搜索功能的MCP工具，可在Cursor等支持MCP的应用中使用。

运行方式:
    uvx baidu-ai-search-mcp
    
或者:
    python -m baidu_ai_search_mcp
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from .client import BaiduAIClient, AISearchResult

# 加载环境变量
load_dotenv()

# 创建MCP服务器
mcp = FastMCP(
    "百度AI搜索",
    json_response=True
)

# 全局客户端实例
_client: Optional[BaiduAIClient] = None


def get_client() -> BaiduAIClient:
    """获取或创建百度AI客户端"""
    global _client
    
    if _client is None:
        api_key = os.getenv("BAIDU_API_KEY")
        if not api_key:
            raise ValueError(
                "未配置 BAIDU_API_KEY 环境变量。\n"
                "请设置环境变量: BAIDU_API_KEY=your-api-key\n"
                "获取API Key: https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application"
            )
        
        model = os.getenv("BAIDU_MODEL", "ernie-3.5-8k")
        _client = BaiduAIClient(api_key=api_key, model=model)
    
    return _client


def format_result(result: AISearchResult, include_references: bool = True) -> str:
    """格式化搜索结果"""
    output = result.content
    
    if include_references and result.references:
        output += "\n\n---\n**参考来源:**\n"
        for ref in result.references:
            output += f"- [{ref.id}] [{ref.title}]({ref.url})\n"
    
    return output


@mcp.tool()
async def baidu_ai_ask(
    question: str,
    enable_deep_search: bool = False,
    time_filter: str = ""
) -> str:
    """
    向百度AI搜索提问，获取基于实时搜索的智能回答。
    
    百度AI搜索会搜索全网最新信息，并使用大模型进行智能总结。
    每天有100次免费调用额度。
    
    Args:
        question: 要询问的问题，如"今天有什么重要新闻？"或"Python异步编程最佳实践"
        enable_deep_search: 是否开启深度搜索，开启后会搜索更多内容但耗时更长
        time_filter: 时间过滤，可选值: week(一周内)/month(一月内)/semiyear(半年内)/year(一年内)
        
    Returns:
        AI生成的回答，包含参考来源链接
    """
    try:
        client = get_client()
        
        result = await client.ask(
            question=question,
            enable_deep_search=enable_deep_search,
            search_recency_filter=time_filter if time_filter else None
        )
        
        return format_result(result)
        
    except ValueError as e:
        return f"配置错误: {str(e)}"
    except Exception as e:
        return f"请求失败: {str(e)}"


@mcp.tool()
async def baidu_ai_search(
    query: str,
    max_results: int = 5
) -> str:
    """
    使用百度AI进行智能搜索，返回搜索结果摘要和链接。
    
    适用于需要获取多个搜索结果而非单一回答的场景。
    
    Args:
        query: 搜索查询词
        max_results: 返回的最大结果数量（1-10）
        
    Returns:
        搜索结果列表，包含标题、摘要和链接
    """
    try:
        client = get_client()
        
        result = await client.ask(
            question=query,
            enable_corner_markers=True
        )
        
        # 格式化为搜索结果样式
        output = f"**搜索结果: {query}**\n\n"
        output += result.content + "\n\n"
        
        if result.references:
            output += "---\n**相关链接:**\n"
            for i, ref in enumerate(result.references[:max_results]):
                output += f"\n**{i+1}. {ref.title}**\n"
                if ref.content:
                    output += f"   {ref.content}\n"
                output += f"   🔗 {ref.url}\n"
        
        return output
        
    except Exception as e:
        return f"搜索失败: {str(e)}"


@mcp.tool()
async def baidu_ai_news(
    topic: str = "",
    time_range: str = "week"
) -> str:
    """
    获取最新新闻资讯。
    
    使用百度AI搜索获取指定主题的最新新闻。
    
    Args:
        topic: 新闻主题，如"科技"、"财经"、"体育"，留空则获取综合新闻
        time_range: 时间范围，可选: week(一周)/month(一月)
        
    Returns:
        新闻摘要和来源链接
    """
    try:
        client = get_client()
        
        question = f"最新{topic}新闻" if topic else "今天有什么重要新闻"
        
        result = await client.ask(
            question=question,
            search_recency_filter=time_range,
            instruction="请以新闻摘要的形式回答，列出最重要的几条新闻，每条包含时间、标题和简要内容。"
        )
        
        return format_result(result)
        
    except Exception as e:
        return f"获取新闻失败: {str(e)}"


def main():
    """MCP服务器入口点"""
    # 检查API Key配置
    if not os.getenv("BAIDU_API_KEY"):
        print("警告: 未配置 BAIDU_API_KEY 环境变量", file=sys.stderr)
        print("请设置环境变量: BAIDU_API_KEY=your-api-key", file=sys.stderr)
    
    # 使用stdio传输（适用于Cursor集成）
    mcp.run()


# 运行服务器
if __name__ == "__main__":
    main()
