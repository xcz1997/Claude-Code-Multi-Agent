# 项目知识库

> **格式要求**: 严格遵循 `.claude/output-styles/markdown-focused.md` 格式规范

## 代码模式

### Hook 用户项目目录识别模式

**场景**: `SessionStart` Hook 需要检测用户复制到框架目录中的实际项目类型，而非框架自身的文件。

**核心思路**:
- 定义 `FRAMEWORK_DIRS` 排除集合（`.claude`, `project_document` 等），过滤框架自身目录
- 对候选子目录执行特征检测：匹配 `PROJECT_INDICATOR_FILES`（如 `Cargo.toml`, `package.json`）和 `PROJECT_INDICATOR_SUFFIXES`（如 `.xcodeproj`, `.sln`）
- 找到用户项目后，仅基于该目录收集上下文送入 Ollama 分析
- 未找到用户项目时，降级扫描根目录（向后兼容）

**涉及文件**: `.claude/hooks/handlers/session_start.py`

### Ollama 客户端多模式调用模式

**场景**: `OllamaClient` 需要同时支持本地 CLI、远程 Ollama API 和 OpenAI 兼容接口。

**路由逻辑**:

| 条件 | 调用方式 | 端点 |
|------|---------|------|
| `OLLAMA_BASE_URL` 为空 | CLI（`subprocess`） | `ollama run` |
| URL 不含 `/v1` | Ollama 原生 API | `/api/generate` |
| URL 含 `/v1` | OpenAI 兼容接口 | `/v1/chat/completions` |

**关键设计决策**:
- 使用标准库 `urllib.request` 实现 HTTP 调用，避免引入额外 Python 依赖
- `OLLAMA_API_KEY` 通过 `Authorization: Bearer` 头传递
- 通过 URL 中是否包含 `/v1` 自动判断接口类型，用户无需额外配置

**涉及文件**: `.claude/hooks/core/ollama_client.py`, `.claude/hooks/core/config.py`

### 认证模式
- 待补充

## 常见问题

### Q: 项目类型检测不准确怎么办？
A: 检查 `.claude/hooks/prompts.json` 中 `detect_project_type` 的提示词，确认目标语言/框架在候选列表中。当前支持 14 种类型：`nodejs/python/rust/go/java/php/swift/kotlin/dart/c_cpp/csharp/ruby/elixir/other`。

### Q: 如何使用远程 Ollama 或第三方 API？
A: 在 `.env` 中配置 `OLLAMA_BASE_URL`（API 地址）和 `OLLAMA_API_KEY`（Token），不配置则默认使用本地 CLI。

## 技术决策记录

### 用户项目目录识别采用排除法 + 特征检测
- **背景**: `_detect_project` 扫描框架根目录，读到 `pyproject.toml` 后误判为 Python 项目
- **决策**: 先排除已知框架目录，再对候选目录做特征文件检测
- **原因**: 排除法确定性高，特征检测覆盖面广，两者结合准确度最优

### Ollama HTTP API 使用标准库实现
- **背景**: Hook 脚本声明 `dependencies = []`，不能引入第三方包
- **决策**: 使用 `urllib.request` 而非 `requests`/`httpx`
- **原因**: 零额外依赖，保持 hook 脚本的轻量和可移植性

## 学习资源
- 待补充

---
*本文档由 Claude Code 自动维护，请勿手动编辑格式*