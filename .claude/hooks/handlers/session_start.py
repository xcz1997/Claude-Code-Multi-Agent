#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
SessionStart Hook - 会话启动处理器
功能：项目感知 + Skills 加载 + 关键 MCP 提示
"""
import sys
import json
from pathlib import Path
from typing import List, Dict

# 添加 core 模块路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.base_hook import BaseHook, HookResult
from core.logger import logger
from core.ollama_client import ollama
from core.document_manager import DocumentManager
from core.config import config


def get_skills_list() -> List[Dict[str, str]]:
    """扫描 skills 目录，提取名称和描述"""
    skills_dir = Path(__file__).parent.parent.parent / "skills"
    skills = []

    if not skills_dir.exists():
        return skills

    for skill_path in skills_dir.iterdir():
        if not skill_path.is_dir() or skill_path.name.startswith(('_', '.')):
            continue

        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            continue

        try:
            content = skill_md.read_text(encoding='utf-8')
            # 提取 YAML frontmatter 中的 name 和 description
            if content.startswith('---'):
                end = content.find('---', 3)
                if end > 0:
                    frontmatter = content[3:end]
                    name = skill_path.name
                    desc = ""
                    for line in frontmatter.split('\n'):
                        if line.startswith('name:'):
                            name = line.split(':', 1)[1].strip().strip('"\'')
                        elif line.startswith('description:'):
                            desc = line.split(':', 1)[1].strip().strip('"\'')
                    if desc:
                        skills.append({"name": name, "desc": desc[:80]})
        except Exception:
            continue

    return skills


def format_skills_hint(skills: List[Dict[str, str]]) -> str:
    """格式化 skills 提示（完整列表，只在会话开始时加载一次）"""
    if not skills:
        return ""

    lines = [config.get_prompt("session_start", "skills_hint_header")]
    for s in skills:  # 显示全部，因为只在会话开始时加载一次
        lines.append(config.get_prompt("session_start", "skills_hint_item", name=s['name'], desc=s['desc']))
    return "\n".join(lines)


class SessionStartHook(BaseHook):
    """会话启动 Hook"""

    def execute(self) -> HookResult:
        session_id = self.input_data.get('session_id', 'unknown')

        # 检测项目类型
        project_info = self._detect_project()

        context_parts = []

        # 1. 加载 Skills 列表（一次性，完整列表）
        skills = []
        try:
            skills = get_skills_list()
            if skills:
                skills_hint = format_skills_hint(skills)
                context_parts.append(skills_hint)
                context_parts.append(config.get_prompt("session_start", "skills_summary", count=len(skills)))
                logger.info(f"已加载 {len(skills)} 个 skills")
        except Exception as e:
            logger.error(f"获取 skills 列表失败: {e}")

        # 2. 项目信息
        project_type = project_info.get('type', 'unknown')
        context_parts.append(config.get_prompt("session_start", "project_type_label", type=project_type))
        
        if project_info.get('frameworks'):
            frameworks_str = ', '.join(project_info['frameworks'])
            context_parts.append(config.get_prompt("session_start", "frameworks_label", frameworks=frameworks_str))
        
        if project_info.get('characteristics'):
            characteristics_str = ', '.join(project_info['characteristics'])
            context_parts.append(config.get_prompt("session_start", "characteristics_label", characteristics=characteristics_str))
        
        confidence = project_info.get('confidence', 'low')
        if confidence != 'low':
            context_parts.append(config.get_prompt("session_start", "confidence_label", confidence=confidence))

        # 3. 初始化文档系统并读取文档内容
        doc_manager = DocumentManager(Path.cwd())
        doc_manager.initialize_documents()
        
        # 【核心改进】强制读取三个文档并注入上下文
        context_parts.append("\n\n【项目文档上下文】")
        context_parts.append(config.get_prompt("session_start", "document_context_header"))
        
        # 读取 DEVELOPMENT.md
        if doc_manager.development_doc.exists():
            try:
                dev_content = doc_manager.development_doc.read_text(encoding='utf-8')
                if dev_content.strip():
                    context_parts.append(config.get_prompt("session_start", "document_development_header") + dev_content[:2000])  # 限制长度避免上下文爆炸
            except Exception as e:
                logger.warning(f"读取 DEVELOPMENT.md 失败: {e}")
        
        # 读取 KNOWLEDGE.md
        if doc_manager.knowledge_doc.exists():
            try:
                knowledge_content = doc_manager.knowledge_doc.read_text(encoding='utf-8')
                if knowledge_content.strip():
                    context_parts.append(config.get_prompt("session_start", "document_knowledge_header") + knowledge_content[:2000])  # 限制长度
            except Exception as e:
                logger.warning(f"读取 KNOWLEDGE.md 失败: {e}")
        
        # 读取 CHANGELOG.md
        if doc_manager.changelog_doc.exists():
            try:
                changelog_content = doc_manager.changelog_doc.read_text(encoding='utf-8')
                if changelog_content.strip():
                    context_parts.append(config.get_prompt("session_start", "document_changelog_header") + changelog_content[:1000])  # 变更日志通常较短
            except Exception as e:
                logger.warning(f"读取 CHANGELOG.md 失败: {e}")
        
        # 4. Git 协作方式检查
        git_context = []
        ui_parts = []  # 初始化 UI 提示列表
        if not doc_manager.check_git_repo():
            git_context.append(config.get_prompt("session_start", "git_not_initialized"))
            ui_parts.append("⚠️ 需要初始化 Git")
        else:
            # 检查是否已配置工作流
            workflow = doc_manager.get_git_workflow()
            if not workflow:
                git_context.append(config.get_prompt("session_start", "git_workflow_not_configured"))
                ui_parts.append("🔀 需要配置 Git 工作流")
            else:
                git_context.append(config.get_prompt("session_start", "git_workflow_label", workflow=workflow))
        
        if git_context:
            context_parts.append("\n\n【Git 配置】")
            context_parts.extend(git_context)

        # 5. 关键 MCP 工具提示（移除 Memory，只保留其他工具）
        context_parts.append(config.get_prompt("session_start", "mcp_tools_header"))
        context_parts.append(config.get_prompt("session_start", "mcp_tools_sequential_thinking"))
        context_parts.append(config.get_prompt("session_start", "mcp_tools_task_manager"))
        context_parts.append(config.get_prompt("session_start", "mcp_tools_context7"))
        
        # 6. 文档维护提示（使用配置的提示词）
        context_parts.append(config.get_prompt("session_start", "document_maintenance_header"))
        context_parts.append(config.get_prompt("session_start", "document_maintenance_location"))
        context_parts.append(config.get_prompt("session_start", "document_maintenance_development"))
        context_parts.append(config.get_prompt("session_start", "document_maintenance_knowledge"))
        context_parts.append(config.get_prompt("session_start", "document_maintenance_changelog"))
        context_parts.append(config.get_prompt("session_start", "document_maintenance_architecture"))
        context_parts.append(config.get_prompt("session_start", "document_maintenance_project"))
        context_parts.append(config.get_prompt("session_start", "document_maintenance_requirement"))
        
        # 7. Git 分支策略参考
        context_parts.append(config.get_prompt("session_start", "git_branch_strategy_header"))
        context_parts.append(config.get_prompt("session_start", "git_branch_strategy_doc"))
        context_parts.append(config.get_prompt("session_start", "git_branch_strategy_workflow"))
        context_parts.append(config.get_prompt("session_start", "git_branch_strategy_naming"))
        context_parts.append(config.get_prompt("session_start", "git_branch_strategy_commit"))

        # 生成 UI 提示信息
        ui_parts.insert(0, config.get_prompt("session_start", "ui_project_type", type=project_info.get('type', 'unknown')))
        if skills:
            ui_parts.append(config.get_prompt("session_start", "ui_skills_loaded", count=len(skills)))
        ui_parts.append(config.get_prompt("session_start", "ui_documents_loaded"))

        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "\n".join(context_parts)
            },
            "systemMessage": " | ".join(ui_parts)
        }

        return self.allow(output)

    # 框架自身的目录，不应被识别为用户项目
    FRAMEWORK_DIRS = {
        '.claude', '.github', 'project_document', 'dist',
        'node_modules', '__pycache__', '.venv', '.git',
    }

    # 框架自身的根文件，不应作为用户项目的检测依据
    FRAMEWORK_ROOT_FILES = {
        'pyproject.toml', 'uv.lock', 'CLAUDE.md', 'LICENSE',
        'README.md', '.env', '.env.example', '.gitignore', '.python-version',
    }

    # 项目特征文件（文件名精确匹配）
    PROJECT_INDICATOR_FILES = {
        'package.json', 'pyproject.toml', 'requirements.txt', 'setup.py', 'setup.cfg',
        'Cargo.toml', 'go.mod', 'go.sum',
        'pom.xml', 'build.gradle', 'build.gradle.kts',
        'composer.json', 'Gemfile',
        'CMakeLists.txt', 'Makefile', 'meson.build',
        'pubspec.yaml', 'Package.swift',
        'Podfile', 'Cartfile',
        'mix.exs', 'rebar.config',
        'tsconfig.json', 'angular.json', 'next.config.js', 'next.config.mjs',
        'vue.config.js', 'nuxt.config.ts',
        'manage.py', 'app.py', 'main.py',
        'index.html', 'index.js', 'index.ts',
    }

    # 项目特征目录后缀（如 .xcodeproj, .xcworkspace, .sln）
    PROJECT_INDICATOR_SUFFIXES = {
        '.xcodeproj', '.xcworkspace', '.sln', '.csproj',
    }

    def _find_user_projects(self) -> List[Path]:
        """识别用户复制进来的项目目录（排除框架自身的目录）"""
        cwd = Path.cwd()
        candidates = []

        try:
            for item in sorted(cwd.iterdir()):
                if not item.is_dir():
                    continue
                # 排除点目录和框架已知目录
                if item.name.startswith('.') or item.name in self.FRAMEWORK_DIRS:
                    continue
                # 检查该目录是否包含项目特征
                if self._has_project_indicators(item):
                    candidates.append(item)
        except Exception:
            pass

        return candidates

    def _has_project_indicators(self, directory: Path) -> bool:
        """检查目录是否包含项目特征文件或目录"""
        try:
            for item in directory.iterdir():
                # 检查特征文件
                if item.is_file() and item.name in self.PROJECT_INDICATOR_FILES:
                    return True
                # 检查特征目录后缀（如 .xcodeproj）
                if item.is_dir() and any(item.name.endswith(s) for s in self.PROJECT_INDICATOR_SUFFIXES):
                    return True
            return False
        except Exception:
            return False

    def _collect_dir_context(self, target_dir: Path) -> List[str]:
        """收集指定目录的项目上下文信息"""
        context_parts = []

        # 1. 列出目录结构
        try:
            top_level_items = []
            for item in sorted(target_dir.iterdir()):
                if item.name.startswith('.'):
                    continue
                if item.is_dir():
                    top_level_items.append(f"目录: {item.name}/")
                else:
                    top_level_items.append(f"文件: {item.name}")
            if top_level_items:
                context_parts.append(f"项目目录结构（{target_dir.name}/）：\n" + "\n".join(top_level_items[:30]))
        except Exception:
            pass

        # 2. 读取关键配置文件
        config_files = {
            "package.json": "Node.js 项目配置",
            "pyproject.toml": "Python 项目配置",
            "requirements.txt": "Python 依赖",
            "Cargo.toml": "Rust 项目配置",
            "go.mod": "Go 项目配置",
            "pom.xml": "Maven 项目配置",
            "build.gradle": "Gradle 项目配置",
            "composer.json": "PHP 项目配置",
            "pubspec.yaml": "Flutter/Dart 项目配置",
            "Package.swift": "Swift 项目配置",
            "Podfile": "iOS CocoaPods 配置",
            "tsconfig.json": "TypeScript 配置",
            "Makefile": "构建配置",
        }

        for config_file, desc in config_files.items():
            config_path = target_dir / config_file
            if config_path.exists():
                try:
                    content = config_path.read_text(encoding='utf-8')[:1000]
                    context_parts.append(f"\n{desc} ({config_file}):\n{content}")
                except Exception:
                    pass

        # 3. 检查 Xcode 项目（目录形式的特征）
        try:
            for item in target_dir.iterdir():
                if item.is_dir() and any(item.name.endswith(s) for s in self.PROJECT_INDICATOR_SUFFIXES):
                    context_parts.append(f"\n检测到项目文件: {item.name}")
        except Exception:
            pass

        # 4. 读取 README（如果有）
        for readme_name in ["README.md", "README.txt", "README"]:
            readme_path = target_dir / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding='utf-8')[:500]
                    context_parts.append(f"\nREADME 内容:\n{content}")
                    break
                except Exception:
                    pass

        return context_parts

    def _detect_project(self) -> dict:
        """使用 Ollama 智能检测项目类型和框架（优先检测用户项目目录）"""
        cwd = Path.cwd()
        project_info = {"type": "unknown", "frameworks": []}

        # 优先寻找用户复制进来的项目目录
        user_projects = self._find_user_projects()

        context_parts = []

        if user_projects:
            # 基于用户项目目录收集上下文
            for proj_dir in user_projects[:3]:  # 最多扫描 3 个用户项目
                dir_context = self._collect_dir_context(proj_dir)
                context_parts.extend(dir_context)
                logger.info(f"检测到用户项目目录: {proj_dir.name}")
        else:
            # 降级：未找到用户项目，扫描根目录（当前行为）
            logger.debug("未检测到用户项目目录，降级扫描根目录")
            context_parts = self._collect_dir_context(cwd)

        # 使用 Ollama 分析项目类型
        if context_parts:
            project_context = "\n".join(context_parts)
            try:
                analysis = ollama.detect_project_type(project_context)
                project_info["type"] = analysis.get("type", "unknown")
                project_info["frameworks"] = analysis.get("frameworks", [])
                project_info["characteristics"] = analysis.get("characteristics", [])
                project_info["confidence"] = analysis.get("confidence", "low")
                if user_projects:
                    project_info["detected_dirs"] = [p.name for p in user_projects[:3]]
                logger.info(f"项目检测: {project_info['type']} (置信度: {project_info.get('confidence', 'low')})")
            except Exception as e:
                logger.debug(f"Ollama 项目检测失败，使用默认值: {e}")
        else:
            logger.debug("无法收集项目上下文，使用默认值")

        return project_info


if __name__ == '__main__':
    hook = SessionStartHook()
    sys.exit(hook.run())
