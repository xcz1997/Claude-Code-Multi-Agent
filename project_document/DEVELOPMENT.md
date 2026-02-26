# 开发工作文档

> **格式要求**: 严格遵循 `.claude/output-styles/bullet-points.md` 格式规范

## 当前任务
- [x] GitHub 仓库管理设施搭建
- [x] SessionStart Hook 用户项目目录识别修复
- [x] Ollama 客户端 API Token 支持

## 任务详情
- GitHub 仓库管理设施
  - 状态: 已完成
  - 文件: `.github/` 目录
  - 描述: 完整的 GitHub 仓库管理基础设施
- SessionStart Hook 用户项目目录识别修复
  - 状态: 已完成
  - 文件: `.claude/hooks/handlers/session_start.py`, `.claude/hooks/prompts.json`
  - 描述: 修复项目类型检测扫描框架根目录而非用户项目目录的设计缺陷
- Ollama 客户端 API Token 支持
  - 状态: 已完成
  - 文件: `.claude/hooks/core/ollama_client.py`, `.claude/hooks/core/config.py`, `.env.example`
  - 描述: 支持通过 .env 配置 HTTP API 调用，兼容远程 Ollama 和 OpenAI 兼容接口

## 最近完成
- [2026-02-26] SessionStart Hook 用户项目目录识别修复 + Ollama API Token 支持
  - 修复: `_detect_project` 扫描框架根目录导致误判用户项目类型的设计缺陷
  - 新增: `_find_user_projects()` 排除框架目录，识别用户复制进来的项目
  - 新增: `_collect_dir_context()` 通用化上下文收集，支持任意目录
  - 扩展: Ollama 提示词项目类型从 7 种扩充到 14 种（增加 swift/kotlin/dart/c_cpp/csharp/ruby/elixir）
  - 新增: `OllamaClient` 支持 HTTP API 模式（Ollama API + OpenAI 兼容接口）
  - 新增: `.env` 配置 `OLLAMA_BASE_URL` 和 `OLLAMA_API_KEY`
  - 零额外依赖: 使用标准库 `urllib.request` 实现 HTTP 调用

- [2026-01-13] GitHub 仓库管理设施搭建
  - Issue 模板系统 (Bug报告、功能请求、Skill请求、问题咨询)
  - PR 模板和贡献指南
  - 自动化 Workflows (CI、Stale、Welcome、Auto-label、Release、Sync-upstream)
  - Bot 配置 (Dependabot)
  - 上游同步机制
  - 安全政策和行为准则

## 遇到的问题
- 暂无

## 技术决策
- 使用 GitHub Actions 实现 CI/CD 和自动化
- 采用 YAML 格式的 Issue 模板以获得更好的表单体验
- 上游同步采用 PR 方式而非直接合并，避免冲突

---
*本文档由 Claude Code 自动维护，请勿手动编辑格式*