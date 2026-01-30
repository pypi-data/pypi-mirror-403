"""
百度AI搜索客户端模块

基于百度千帆AI搜索API实现，提供智能搜索和问答功能。
API文档: https://cloud.baidu.com/doc/qianfan-api/s/em82g4tlk
"""

import httpx
import json
from typing import Optional, AsyncIterator
from dataclasses import dataclass


@dataclass
class SearchReference:
    """搜索引用结果"""
    id: int
    title: str
    url: str
    content: Optional[str] = None
    date: Optional[str] = None
    icon: Optional[str] = None
    type: str = "web"


@dataclass
class AISearchResult:
    """AI搜索结果"""
    content: str
    reasoning_content: Optional[str] = None
    references: list[SearchReference] = None
    is_safe: bool = True
    usage: Optional[dict] = None
    
    def __post_init__(self):
        if self.references is None:
            self.references = []


class BaiduAIClient:
    """
    百度AI搜索客户端
    
    使用百度千帆AI搜索API，提供智能搜索生成功能。
    每天有100次免费调用额度。
    
    使用方法:
        client = BaiduAIClient(api_key="your-api-key")
        result = await client.ask("今天有什么新闻？")
        print(result.content)
    """
    
    API_URL = "https://qianfan.baidubce.com/v2/ai_search/chat/completions"
    
    def __init__(
        self,
        api_key: str,
        model: str = "ernie-3.5-8k",
        timeout: float = 60.0
    ):
        """
        初始化客户端
        
        Args:
            api_key: 百度千帆API Key (格式: bce-v3/ALTAK***/xxx)
            model: 使用的模型，支持:
                   - ernie-3.5-8k (默认)
                   - ernie-4.0-turbo-8k
                   - ernie-4.0-turbo-128k
                   - deepseek-r1
                   - deepseek-v3
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        
    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _build_messages(
        self,
        question: str,
        history: Optional[list[dict]] = None
    ) -> list[dict]:
        """
        构建消息列表
        
        Args:
            question: 用户问题
            history: 对话历史 [{"role": "user", "content": "..."}, ...]
            
        Returns:
            消息列表，格式符合API要求
        """
        messages = []
        
        if history:
            messages.extend(history)
            
        messages.append({
            "role": "user",
            "content": question
        })
        
        return messages
    
    def _parse_references(self, refs_data: list) -> list[SearchReference]:
        """解析搜索引用"""
        references = []
        for ref in refs_data:
            references.append(SearchReference(
                id=ref.get("id", 0),
                title=ref.get("title", ""),
                url=ref.get("url", ""),
                content=ref.get("content"),
                date=ref.get("date"),
                icon=ref.get("icon"),
                type=ref.get("type", "web")
            ))
        return references
    
    async def ask(
        self,
        question: str,
        history: Optional[list[dict]] = None,
        stream: bool = False,
        enable_deep_search: bool = False,
        enable_corner_markers: bool = True,
        search_recency_filter: Optional[str] = None,
        instruction: Optional[str] = None
    ) -> AISearchResult:
        """
        向百度AI提问并获取回答
        
        Args:
            question: 用户问题
            history: 对话历史
            stream: 是否使用流式响应（当前非流式实现）
            enable_deep_search: 是否开启深度搜索（会产生更多API调用）
            enable_corner_markers: 是否返回角标标记参考来源
            search_recency_filter: 时间过滤，可选值: week/month/semiyear/year
            instruction: 人设指令，用于限制输出风格
            
        Returns:
            AISearchResult对象，包含回答内容和引用
            
        Raises:
            httpx.HTTPError: 网络请求错误
            ValueError: API返回错误
        """
        messages = self._build_messages(question, history)
        
        payload = {
            "messages": messages,
            "model": self.model,
            "stream": False,  # 非流式
            "enable_deep_search": enable_deep_search,
            "enable_corner_markers": enable_corner_markers
        }
        
        if search_recency_filter:
            payload["search_recency_filter"] = search_recency_filter
            
        if instruction:
            payload["instruction"] = instruction
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.API_URL,
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        # 检查错误响应
        if "code" in data and data["code"] != 0:
            raise ValueError(f"API错误: {data.get('message', '未知错误')} (code: {data['code']})")
        
        # 解析响应
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("API返回空响应")
        
        message = choices[0].get("message", {})
        content = message.get("content", "")
        reasoning_content = message.get("reasoning_content")
        
        # 解析引用
        references = self._parse_references(data.get("references", []))
        
        return AISearchResult(
            content=content,
            reasoning_content=reasoning_content,
            references=references,
            is_safe=data.get("is_safe", True),
            usage=data.get("usage")
        )
    
    async def ask_stream(
        self,
        question: str,
        history: Optional[list[dict]] = None,
        enable_deep_search: bool = False,
        instruction: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        流式问答（SSE）
        
        Args:
            question: 用户问题
            history: 对话历史
            enable_deep_search: 是否开启深度搜索
            instruction: 人设指令
            
        Yields:
            逐步返回的回答内容片段
        """
        messages = self._build_messages(question, history)
        
        payload = {
            "messages": messages,
            "model": self.model,
            "stream": True,
            "enable_deep_search": enable_deep_search
        }
        
        if instruction:
            payload["instruction"] = instruction
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                self.API_URL,
                headers=self._get_headers(),
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue


# 同步包装器，方便非异步环境使用
class BaiduAIClientSync:
    """
    百度AI搜索同步客户端（包装异步客户端）
    """
    
    def __init__(self, api_key: str, model: str = "ernie-3.5-8k", timeout: float = 60.0):
        self._async_client = BaiduAIClient(api_key, model, timeout)
    
    def ask(self, question: str, **kwargs) -> AISearchResult:
        """同步问答"""
        import asyncio
        return asyncio.run(self._async_client.ask(question, **kwargs))
