# 变更日志

> **格式要求**: 严格遵循 `.claude/output-styles/bullet-points.md` 格式规范
> **提交规范**: 遵循 commitlint 规范（type(scope): subject）

## [2026-02-26]
### 新增
- feat(session_start): 新增 `_find_user_projects()` 识别用户复制进来的项目目录
- feat(session_start): 新增 `_has_project_indicators()` 检测项目特征文件和目录后缀
- feat(session_start): 新增 `_collect_dir_context()` 通用化目录上下文收集
- feat(ollama_client): 新增 HTTP API 调用模式，支持远程 Ollama 和 OpenAI 兼容接口
- feat(config): 新增 `OLLAMA_BASE_URL` 和 `OLLAMA_API_KEY` 环境变量配置

### 修改
- 暂无

### 修复
- fix(session_start): 修复 `_detect_project` 扫描框架根目录而非用户项目目录导致项目类型误判的缺陷

### 改进
- refactor(prompts): 项目类型候选列表从 7 种扩充到 14 种，增加关键识别线索提示
- refactor(.env.example): 补充 API 配置说明和使用示例

## [2026-01-13]
### 新增
- feat(github): 添加完整的 GitHub 仓库管理设施
  - Issue 模板: bug_report.yml, feature_request.yml, skill_request.yml, question.yml
  - PR 模板: PULL_REQUEST_TEMPLATE.md
  - 贡献指南: CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md
  - 自动化 Workflows:
    - ci.yml - CI 流水线 (lint, test, validate)
    - stale.yml - 自动清理过期 Issue/PR
    - welcome.yml - 欢迎新贡献者
    - auto-label.yml - 自动标签
    - release.yml - 发布自动化
    - sync-upstream.yml - 上游同步机制
  - Bot 配置: dependabot.yml
  - 标签定义: labels.yml
  - 赞助配置: FUNDING.yml

### 修改
- 暂无

### 修复
- 暂无

### 重构
- 暂无

---
*本文档由 Claude Code 自动维护，请勿手动编辑格式*