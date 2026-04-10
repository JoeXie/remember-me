# RememberMe MCP Server

MCP 服务器，为 Claude Code 和其他 MCP 客户端提供长期记忆管理能力。基于 Qdrant 向量数据库，支持语义化检索和更新用户记忆。

## 特性

- **语义搜索** - 使用向量相似度进行自然语言查询
- **多用户支持** - 通过 `userId` 隔离不同用户记忆
- **会话追踪** - 支持 `runId` 关联特定代理会话
- **内容去重** - MD5 哈希检测重复记忆
- **自动向量化** - 集成 OpenAI 兼容嵌入服务

## 架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Claude Code   │────▶│   Qdrant MCP    │────▶│   Qdrant DB     │
│   (MCP Client) │     │     Server      │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 安装

```bash
cd src/rememberme
pip install -e .
```

## 配置

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `QDRANT_HOST` | Qdrant 服务器地址 | `<HOST>` (如 `localhost`) |
| `QDRANT_PORT` | Qdrant 端口 | `<PORT>` (如 `6333`) |
| `QDRANT_COLLECTION_NAME` | 集合名称 | `memories` |
| `QDRANT_API_KEY` | Qdrant API 密钥 | - |
| `EMBEDDING_API_KEY` | 嵌入 API 密钥 | **必需** |
| `EMBEDDING_MODEL` | 嵌入模型（OpenAI 兼容） | `<EMBEDDING_MODEL>` (如 `doubao-embedding-vision`) |
| `EMBEDDING_DIMENSIONS` | 向量维度 | `<EMBEDDING_DIMENSIONS>` (如 `2048`) |
| `OPENAI_BASE_URL` | 嵌入 API 端点 | `<OPENAI_BASE_URL>` (如 `https://ark.cn-beijing.volces.com/api/coding/v3`) |
| `DEFAULT_USER_ID` | 默认用户 ID | `<DEFAULT_USER_ID>` (如 `user_peanut`) |
| `LOG_LEVEL` | 日志级别 | `INFO` |

> **占位符说明**: 表格中的 `<PLACEHOLDER>` 格式表示可替换的定制化参数，实际部署时请替换为具体值。

## Claude Code 集成

### 方式一：使用 claude code 配置命令

```bash
# 添加 MCP 服务器
claude mcp add rememberme -- python -m rememberme

# 或指定工作目录
claude mcp add rememberme -- bash -c "cd /path/to/RememberMe && python -m rememberme"
```

### 方式二：手动配置（持久化）

在 `~/.claude/settings.json` 中添加：

```json
{
  "mcpServers": {
    "rememberme": {
      "command": "python",
      "args": ["-m", "rememberme"],
      "env": {
        "QDRANT_HOST": "<HOST>",
        "QDRANT_PORT": "<PORT>",
        "EMBEDDING_API_KEY": "<YOUR_API_KEY>",
        "EMBEDDING_MODEL": "<EMBEDDING_MODEL>",
        "EMBEDDING_DIMENSIONS": "<EMBEDDING_DIMENSIONS>",
        "OPENAI_BASE_URL": "<OPENAI_BASE_URL>",
        "DEFAULT_USER_ID": "<DEFAULT_USER_ID>"
      }
    }
  }
}
```

### 验证连接

配置完成后，在 Claude Code 中执行：

```
/mcp list
```

应能看到 `rememberme` 服务器已启用。

### 可用工具

启用后，Claude Code 可直接使用以下记忆管理工具：
- `add_memory` - 添加记忆
- `search_memories` - 语义搜索
- `get_memory` - 获取单条记忆
- `update_memory` - 更新记忆
- `delete_memory` - 删除记忆
- `delete_all_memories` - 清除所有记忆

### 启动服务器

```bash
python -m rememberme
```

### MCP 工具

#### add_memory

添加新记忆。

```json
{
  "text": "用户偏好使用 Go 语言",
  "user_id": "<USER_ID>",
  "agent_id": "agent:main:<UUID>"
}
```

#### search_memories

语义搜索记忆。

```json
{
  "query": "用户喜欢什么编程语言",
  "user_id": "<USER_ID>",
  "limit": 5
}
```

#### get_memory

通过 ID 获取记忆。

```json
{
  "id": "<MEMORY_UUID>"
}
```

#### update_memory

更新记忆内容。

```json
{
  "id": "<MEMORY_UUID>",
  "text": "更新后的内容"
}
```

#### delete_memory

删除指定记忆。

```json
{
  "id": "<MEMORY_UUID>"
}
```

#### delete_all_memories

删除用户所有记忆。

```json
{
  "user_id": "<USER_ID>"
}
```

## 数据格式

Qdrant 中存储的 payload 结构：

```json
{
  "userId": "<USER_ID>",
  "data": "记忆内容",
  "hash": "<MD5_HASH>",
  "createdAt": "<TIMESTAMP>",
  "runId": "agent:main:<UUID>"
}
```

## 运行测试

```bash
cd tests
pip install pytest pytest-asyncio
pytest
```

## 项目结构

```
src/rememberme/
├── __init__.py          # 包初始化
├── __main__.py          # MCP 服务器入口
├── config.py            # 配置管理
├── models.py            # 数据模型
├── embeddings.py        # 嵌入服务
├── memory_store.py      # Qdrant 操作
├── pyproject.toml       # 依赖配置
└── .env.example         # 环境变量模板

tests/
├── __init__.py
├── test_models.py       # 数据模型测试
├── test_config.py       # 配置测试
└── test_embeddings.py  # 嵌入服务测试
```

## License

MIT
