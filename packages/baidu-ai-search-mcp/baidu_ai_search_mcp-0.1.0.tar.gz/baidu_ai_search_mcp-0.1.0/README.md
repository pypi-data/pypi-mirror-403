# 百度AI搜索 MCP服务

[![PyPI version](https://badge.fury.io/py/baidu-ai-search-mcp.svg)](https://badge.fury.io/py/baidu-ai-search-mcp)
[![Python](https://img.shields.io/pypi/pyversions/baidu-ai-search-mcp.svg)](https://pypi.org/project/baidu-ai-search-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

基于百度千帆AI搜索API的MCP服务，可在Cursor等支持MCP的应用中使用百度AI搜索功能。

## 功能特性

- **智能问答**: 基于百度搜索的AI智能回答，支持实时信息获取
- **深度搜索**: 可选开启深度搜索获取更全面的信息
- **新闻获取**: 快速获取各领域最新新闻
- **时间过滤**: 支持按时间范围筛选搜索结果
- **参考来源**: 返回回答的参考来源链接

## 安装

### 方式一：使用 uvx（推荐）

无需安装，直接在 Cursor MCP 配置中使用：

```json
{
  "mcpServers": {
    "baidu-ai-search": {
      "command": "uvx",
      "args": ["baidu-ai-search-mcp"],
      "env": {
        "BAIDU_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### 方式二：使用 pip 安装

```bash
pip install baidu-ai-search-mcp
```

然后在 Cursor MCP 配置中：

```json
{
  "mcpServers": {
    "baidu-ai-search": {
      "command": "python",
      "args": ["-m", "baidu_ai_search_mcp"],
      "env": {
        "BAIDU_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## 配置

### 获取 API Key

1. 访问 [百度千帆控制台](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
2. 创建应用并获取 API Key（格式：`bce-v3/ALTAK***/xxx`）

### Cursor 配置文件位置

- **Windows**: `%USERPROFILE%\.cursor\mcp.json`
- **macOS/Linux**: `~/.cursor/mcp.json`

### 完整配置示例

```json
{
  "mcpServers": {
    "baidu-ai-search": {
      "command": "uvx",
      "args": ["baidu-ai-search-mcp"],
      "env": {
        "BAIDU_API_KEY": "bce-v3/ALTAK-xxxxx/xxxxxxxxxx",
        "BAIDU_MODEL": "ernie-3.5-8k"
      }
    }
  }
}
```

配置完成后，重启 Cursor 即可使用。

## 可用工具

### baidu_ai_ask

向百度AI搜索提问，获取基于实时搜索的智能回答。

**参数**:
- `question` (必需): 要询问的问题
- `enable_deep_search` (可选): 是否开启深度搜索，默认 false
- `time_filter` (可选): 时间过滤 (week/month/semiyear/year)

**示例**:
```
使用 baidu_ai_ask 工具查询"Python 3.12有什么新特性？"
```

### baidu_ai_search

智能搜索，返回搜索结果摘要和链接。

**参数**:
- `query` (必需): 搜索查询词
- `max_results` (可选): 最大结果数量，默认 5

### baidu_ai_news

获取最新新闻资讯。

**参数**:
- `topic` (可选): 新闻主题（如"科技"、"财经"、"体育"）
- `time_range` (可选): 时间范围 (week/month)，默认 week

## 支持的模型

| 模型 | 特点 |
|------|------|
| ernie-3.5-8k | 默认模型，速度快，性价比高 |
| ernie-4.0-turbo-8k | 更智能，适合复杂问题 |
| ernie-4.0-turbo-128k | 支持长文本上下文 |
| deepseek-r1 | 深度推理，适合复杂分析 |
| deepseek-v3 | DeepSeek最新模型 |

通过 `BAIDU_MODEL` 环境变量设置使用的模型。

## API 配额

- 每天 **100次** 免费调用
- 超出后按量计费
- 详见 [计费说明](https://cloud.baidu.com/doc/qianfan-docs/s/Jm8r1826a)

## 开发

### 本地开发安装

```bash
git clone https://github.com/yourusername/baidu-ai-search-mcp.git
cd baidu-ai-search-mcp
pip install -e .
```

### 运行测试

```bash
# 设置环境变量
export BAIDU_API_KEY="your-api-key"

# 直接运行
python -m baidu_ai_search_mcp
```

## 常见问题

**Q: 提示 "未配置 BAIDU_API_KEY"**

A: 请确保在 `mcp.json` 的 `env` 中正确配置了 API Key。

**Q: 请求超时**

A: 深度搜索模式耗时较长，可尝试关闭 `enable_deep_search`。

**Q: 返回错误 "Authentication error"**

A: API Key 格式不正确或已过期，请检查配置。

## License

MIT
