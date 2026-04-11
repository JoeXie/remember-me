# RememberMe - CLI + MCP 双模服务器

为 Claude Code 和其他 MCP 客户端提供长期记忆管理的双模工具。支持 CLI 命令行直接调用和 MCP 服务器集成两种方式。

基于 Qdrant 向量数据库，支持语义化检索和用户/会话隔离。

## 特性

- **双模支持**: CLI 命令 + MCP 服务器集成
- **语义搜索** - 使用向量相似度进行自然语言查询
- **多用户支持** - 通过 `userId` 隔离不同用户记忆
- **会话追踪** - 支持 `runId` 关联特定代理会话
- **内容去重** - MD5 哈希检测重复记忆
- **自动向量化** - 集成 OpenAI 兼容嵌入服务

## 快速开始

```bash
# 安装
pip install -e .

# CLI 使用
rememberme add "用户偏好深色主题"
rememberme search "偏好" --limit 5
rememberme status

# MCP 模式（用于 Claude Code）
python -m rememberme
```

## 安装

本指南从下载代码仓库开始，指导您完成 RememberMe 的完整安装和配置。

### 前置要求

- **Python 3.10+**
- **Qdrant**（向量数据库）- [通过 Docker 安装](https://qdrant.tech/documentation/guides/)
- **嵌入 API**（OpenAI 兼容）- 如 Doubao、OpenAI、LocalAI

### 步骤 1: 克隆仓库

```bash
git clone https://github.com/JoeXie/remember-me.git
cd remember-me
```

或从 GitHub 下载并解压压缩包。

### 步骤 2: 安装依赖

```bash
pip install -e .
```

这将以开发模式安装 RememberMe 并创建 `rememberme` 命令。

### 步骤 3: 配置环境变量

复制环境变量示例文件并编辑：

```bash
cp .env.example .env
```

编辑 `.env` 配置您的凭据：

```bash
# 必需：嵌入 API 凭据
EMBEDDING_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3

# 必需：嵌入模型配置
EMBEDDING_MODEL=doubao-embedding-vision
EMBEDDING_DIMENSIONS=2048

# 可选：Qdrant 连接（默认配置如下）
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=memories

# 可选：默认用户 ID
DEFAULT_USER_ID=user_default
```

### 步骤 4: 启动 Qdrant

确保 Qdrant 正在运行：

```bash
# 使用 Docker
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# 或使用 Podman
podman run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 步骤 5: 验证安装

检查连接状态：

```bash
rememberme status
```

预期输出：
```
## RememberMe 状态

- **Qdrant**: `已连接`
  - 主机: `localhost:6333`
  - 集合: `memories`
- **记忆数量**: `0` 条
```

### 步骤 6: 执行第一条命令

```bash
# 添加一条记忆
rememberme add "用户偏好深色主题"

# 搜索记忆
rememberme search "偏好"

# 查看帮助
rememberme --help
```

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| `QdrantOfflineError` | 确保 Qdrant 正在运行（`docker run -p 6333:6333 qdrant/qdrant`） |
| `ValidationError` | 检查 `.env` 中的 `EMBEDDING_API_KEY` 和 `OPENAI_BASE_URL` |
| 命令未找到 | 重新运行 `pip install -e .` 创建 `rememberme` 命令 |
| 集合错误 | RememberMe 会在首次运行时自动创建集合 |

## CLI 命令

```bash
# 添加新记忆
rememberme add "用户偏好深色主题"

# 搜索记忆
rememberme search "用户偏好"
rememberme search "项目决策" --limit 10

# 查看状态
rememberme status

# 删除记忆
rememberme delete <memory_id>

# 删除所有记忆
rememberme delete-all --force

# JSON 输出（程序调用）
rememberme add "内容" --json
rememberme search "查询" --json
```

### CLI 选项

| 选项 | 描述 |
|------|------|
| `--user-id` | 用户 ID 范围（默认为 DEFAULT_USER_ID 环境变量） |
| `--debug` | 启用调试日志 |

## 架构

```
                    双模入口
                  ┌─────────────────┐
                  │  __main__.py    │
                  │  自动检测模式   │
                  └────────┬────────┘
                           │
          ┌────────────────┼────────────────┐
          │                                 │
          ▼                                 ▼
    ┌───────────┐                    ┌─────────────┐
    │  CLI 模式 │                    │ MCP 模式    │
    │  (Click)  │                    │  (stdio)    │
    └─────┬─────┘                    └──────┬──────┘
          │                                 │
          ▼                                 │
    MemoryManager                            │
    (core/memory_manager.py)                  │
          │                                 │
          └────────────────┼────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │     MemoryStore         │
              │   (Qdrant 操作层)        │
              └─────────────────────────┘
```

## MCP 服务器集成

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

### 可用 MCP 工具

- `add_memory` - 添加记忆
- `search_memories` - 语义搜索
- `get_memory` - 获取单条记忆
- `update_memory` - 更新记忆
- `delete_memory` - 删除记忆
- `delete_all_memories` - 清除所有记忆

## OpenClaw Skill 集成

对于 OpenClaw 代理，安装 RememberMe skill 以启用自动召回和自动存储：

```bash
# 从本地仓库安装 skill
/skill install path/to/RememberMe/skills/using-rememberme-cli --always true
```

**重要提示：** 安装时请设置 `always: true`，以确保每次对话时都自动执行召回和存储。

该 skill 提供：
- **自动召回**：在响应前根据上下文自动搜索记忆
- **自动存储**：在响应后评估并存储新事实

## 配置

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `QDRANT_HOST` | Qdrant 服务器地址 | `localhost` |
| `QDRANT_PORT` | Qdrant 端口 | `6333` |
| `QDRANT_COLLECTION_NAME` | 集合名称 | `memories` |
| `QDRANT_API_KEY` | Qdrant API 密钥 | - |
| `EMBEDDING_API_KEY` | 嵌入 API 密钥 | **必需** |
| `EMBEDDING_MODEL` | 嵌入模型（OpenAI 兼容） | `doubao-embedding-vision` |
| `EMBEDDING_DIMENSIONS` | 向量维度 | `2048` |
| `OPENAI_BASE_URL` | 嵌入 API 端点 | 必需 |
| `DEFAULT_USER_ID` | 默认用户 ID | `user_default` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

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

## 项目结构

```
src/rememberme/
├── __main__.py          # 双模入口（CLI + MCP 自动检测）
├── config.py            # 配置管理
├── models.py            # 数据模型
├── embeddings.py        # 嵌入服务
├── memory_store.py      # Qdrant 操作
│
├── core/                # 核心业务逻辑
│   ├── __init__.py
│   ├── exceptions.py    # 自定义异常
│   └── memory_manager.py
│
├── cli/                 # CLI 接口
│   ├── __init__.py
│   ├── commands.py      # Click 命令
│   ├── formatter.py    # 输出格式化
│   └── lazy.py          # 延迟加载
│
├── mcp/                 # MCP 适配层
│   ├── __init__.py
│   └── adapter.py       # MCP 服务器
│
└── skill/               # OpenClaw Skill
    └── manage_personal_memory.py

skills/                   # OpenClaw skills（独立分发）
└── using-rememberme-cli/
    └── SKILL.md

tests/
├── test_models.py
├── test_config.py
└── test_embeddings.py
```

## 运行测试

```bash
pytest tests/
```

## License

MIT
