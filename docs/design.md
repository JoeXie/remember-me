# RememberMe MCP Server 技术规格文档

## 1. 项目概述

### 1.1 项目简介
RememberMe MCP Server 是一个基于 Model Context Protocol (MCP) 的轻量级服务器，为 Claude Code 和其他兼容 MCP 客户端提供长期记忆管理能力。使用 Qdrant 向量数据库进行向量化存储，支持语义化检索和更新用户记忆。

### 1.2 技术栈
- **编程语言**: Python 3.10+
- **MCP框架**: mcp>=1.6.0
- **向量数据库**: Qdrant 1.13.0+
- **嵌入模型**: 可配置（支持 OpenAI Embeddings 兼容接口）

### 1.3 架构设计

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Claude Code   │────▶│   Qdrant MCP    │────▶│   Local Qdrant  │
│   (MCP Client)  │     │     Server      │     │   Vector DB     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  嵌入生成服务    │
                       │  (OpenAI 兼容)  │
                       └─────────────────┘
```

## 2. 数据模型

### 2.1 Qdrant Payload 结构

```json
{
  "userId": "<USER_ID>",
  "data": "记忆内容文本",
  "hash": "内容MD5哈希值",
  "createdAt": "<TIMESTAMP>",
  "runId": "<AGENT_RUN_ID>"
}
```

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `userId` | string | 是 | 用户唯一标识 |
| `data` | string | 是 | 记忆内容文本 |
| `hash` | string | 是 | 内容 MD5 哈希（用于去重检测） |
| `createdAt` | string | 是 | 创建时间，ISO 8601 格式 |
| `runId` | string | 否 | 代理会话标识，格式: `agent:{type}:{uuid}` |
| `updatedAt` | string | 否 | 更新时间，ISO 8601 格式（仅更新时存在） |

### 2.2 向量配置

| 参数 | 值 | 描述 |
|------|-----|------|
| `size` | `<EMBEDDING_DIMENSIONS>` | 向量维度（必须与嵌入模型输出维度匹配） |
| `distance` | Cosine | 余弦相似度 |
| `m` | 16 | HNSW 索引参数 |
| `ef_construct` | 100 | HNSW 索引参数 |

> **注意**: 向量维度 `size` 必须与所选嵌入模型的输出维度匹配。不同模型可能输出不同维度的向量。

## 3. 配置项

### 3.1 环境变量

| 变量名 | 描述 | 默认值 | 必需 |
|--------|------|--------|------|
| `QDRANT_HOST` | Qdrant 服务器地址 | `<HOST>` (如 `localhost`) | 否 |
| `QDRANT_PORT` | Qdrant 端口 | `<PORT>` (如 `6333`) | 否 |
| `QDRANT_COLLECTION_NAME` | 集合名称 | `memories` | 否 |
| `QDRANT_API_KEY` | Qdrant API 密钥 | - | 否 |
| `EMBEDDING_API_KEY` | 嵌入 API 密钥 | - | **是** |
| `EMBEDDING_MODEL` | 嵌入模型名称（支持 OpenAI Embeddings 兼容接口） | `<EMBEDDING_MODEL>` (如 `doubao-embedding-vision`) | 否 |
| `EMBEDDING_DIMENSIONS` | 向量维度（需与模型输出维度匹配） | `<EMBEDDING_DIMENSIONS>` (如 `2048`) | 否 |
| `OPENAI_BASE_URL` | OpenAI 兼容 Embeddings API 端点 | `<OPENAI_BASE_URL>` (如 `https://ark.cn-beijing.volces.com/api/coding/v3`) | 否 |
| `DEFAULT_USER_ID` | 默认用户 ID | `<DEFAULT_USER_ID>` (如 `user_peanut`) | 否 |
| `LOG_LEVEL` | 日志级别 | `INFO` | 否 |

> **占位符说明**: 表格中的 `<PLACEHOLDER>` 格式表示可替换的定制化参数，实际部署时请替换为具体值。

## 4. MCP 工具接口

### 4.1 add_memory

添加新记忆。

**参数:**
| 名称 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `text` | string | 是 | 记忆内容 |
| `user_id` | string | 否 | 用户 ID（默认使用 `DEFAULT_USER_ID`） |
| `agent_id` | string | 否 | 代理 ID（存储为 `runId`） |

**请求示例:**
```json
{
  "text": "用户偏好使用 Go 语言进行后端开发",
  "user_id": "<USER_ID>",
  "agent_id": "agent:main:<UUID>"
}
```

**响应示例:**
```json
{
  "id": "<MEMORY_UUID>",
  "data": "用户偏好使用 Go 语言进行后端开发",
  "userId": "<USER_ID>",
  "runId": "agent:main:<UUID>",
  "hash": "<MD5_HASH>",
  "createdAt": "<TIMESTAMP>"
}
```

### 4.2 search_memories

语义化搜索记忆。

**参数:**
| 名称 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `query` | string | 是 | 搜索查询文本 |
| `user_id` | string | 否 | 用户 ID（默认使用 `DEFAULT_USER_ID`） |
| `agent_id` | string | 否 | 代理 ID（过滤特定代理的记忆） |
| `limit` | int | 否 | 返回结果数量，默认 5 |

**响应示例:**
```json
{
  "results": [
    {
      "id": "<MEMORY_UUID>",
      "data": "用户偏好使用 Go 语言进行后端开发",
      "score": 0.95,
      "createdAt": "<TIMESTAMP>"
    }
  ],
  "count": 1
}
```

### 4.3 get_memory

通过 ID 获取单个记忆。

**参数:**
| 名称 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `id` | string | 是 | 记忆 ID |

**响应示例:**
```json
{
  "id": "<MEMORY_UUID>",
  "data": "用户偏好使用 Go 语言进行后端开发",
  "userId": "<USER_ID>",
  "runId": "agent:main:<UUID>",
  "hash": "<MD5_HASH>",
  "createdAt": "<TIMESTAMP>"
}
```

### 4.4 update_memory

更新记忆内容。

**参数:**
| 名称 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `id` | string | 是 | 记忆 ID |
| `text` | string | 否 | 新的记忆内容 |
| `metadata` | dict | 否 | 元数据（此处仅支持 `runId`） |

**响应示例:**
```json
{
  "id": "<MEMORY_UUID>",
  "data": "更新后的记忆内容",
  "userId": "<USER_ID>",
  "hash": "<MD5_HASH>",
  "createdAt": "<TIMESTAMP>",
  "updatedAt": "<TIMESTAMP>"
}
```

### 4.5 delete_memory

删除指定记忆。

**参数:**
| 名称 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `id` | string | 是 | 记忆 ID |

**响应示例:**
```json
{
  "success": true,
  "id": "<MEMORY_UUID>"
}
```

### 4.6 delete_all_memories

删除用户所有记忆。

**参数:**
| 名称 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `user_id` | string | 否 | 用户 ID（默认使用 `DEFAULT_USER_ID`） |
| `agent_id` | string | 否 | 代理 ID（仅删除该代理的记忆） |

**响应示例:**
```json
{
  "success": true,
  "deleted_count": <COUNT>
}
```

## 5. 项目结构

```
rememberme-mcp/
├── src/
│   └── rememberme/
│       ├── __init__.py
│       ├── __main__.py          # MCP 服务器入口
│       ├── config.py            # 配置管理
│       ├── memory_store.py      # Qdrant 存储操作
│       ├── embeddings.py        # 嵌入生成服务
│       └── models.py            # 数据模型
├── tests/
│   └── ...
├── .env.example
├── pyproject.toml
└── README.md
```

## 6. 核心模块说明

### 6.1 config.py
- 管理所有配置项
- 支持环境变量自动加载
- 数据验证：`QDRANT_HOST`, `QDRANT_PORT`, `EMBEDDING_DIMENSIONS`

### 6.2 models.py
```python
@dataclass
class Memory:
    id: str
    userId: str           # 注意: 驼峰命名
    data: str             # 注意: 字段名为 data
    hash: str
    createdAt: str
    runId: Optional[str] = None
    updatedAt: Optional[str] = None
    score: Optional[float] = None  # 仅搜索结果中存在
```

### 6.3 memory_store.py
- `MemoryStore` 类：核心存储逻辑
- 自动集合创建（若不存在）
- 向量维度验证：`<EMBEDDING_DIMENSIONS>`
- 支持按 `userId` 和 `runId` 过滤
- 内容哈希：`hashlib.md5(data.encode()).hexdigest()`

### 6.4 embeddings.py
- `EmbeddingService` 类
- 批量嵌入生成
- 重试机制
- 向量维度：`<EMBEDDING_DIMENSIONS>`

### 6.5 __main__.py
- MCP 服务器入口
- 6 个工具定义
- stdio 通信

## 7. 向导式初始化

首次启动时，若集合不存在，自动创建：

```python
collection_config = {
    "vectors": {
        "size": <EMBEDDING_DIMENSIONS>,
        "distance": "Cosine"
    },
    "hnsw_config": {
        "m": 16,
        "ef_construct": 100
    }
}
```

## 8. 错误处理

| 错误类型 | HTTP 状态码 | 处理方式 |
|----------|-------------|----------|
| 集合不存在 | 404 | 自动创建集合后重试 |
| 向量维度不匹配 | 400 | 抛出配置错误 |
| 嵌入服务不可用 | 503 | 重试 3 次后返回错误 |
| 记忆不存在 | 404 | 返回 `null` 或 `false` |

## 9. 兼容性说明

本设计**仅支持**当前 Qdrant 中的 `memories` 集合格式：

```json
{
  "userId": "<USER_ID>",
  "data": "...",
  "hash": "md5_hash",
  "createdAt": "<TIMESTAMP>",
  "runId": "agent:main:<UUID>"  // 可选
}
```

不支持旧文档中提到的 `text`, `user_id`, `agent_id`, `metadata` 等字段名。
