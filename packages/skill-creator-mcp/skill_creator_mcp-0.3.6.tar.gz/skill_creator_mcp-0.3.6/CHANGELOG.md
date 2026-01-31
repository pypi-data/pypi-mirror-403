# Changelog

All notable changes to the skill-creator-mcp project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.4] - 2026-01-29

### Fixed
- 文档数据不一致（CLAUDE.md工具数量从18改为13，测试数量从615/586改为566）
- 文档数据不一致（README.md测试数量从586改为566）
- 测试数量记录错误（从v0.3.3的586更新为v0.3.4声明时的568，实际为566）
- 打包工具推荐方式更新（从package_agent_skill改为package_skill）
- Phase 0工具说明位置优化（从特性章节移到开发章节）
- 清理server.py重复导入（time模块）
- 添加文档一致性验证脚本
- 代码质量全面清理与优化：
  - 工具数量统一为12个（删除已移除工具的文档引用）
  - 测试数量统一为566个（更新所有README徽章和CLAUDE.md）
  - 版本号统一为v0.3.4
  - 清理~160行未使用代码
  - 删除PackageAgentSkillInput类（40行）
  - 删除validation_helpers.py模块（92行）

## [0.3.3] - 2026-01-28

### Added
- 7个需求收集原子工具（会话管理3、问题获取2、验证工具2）
- Prompt模板外部化到Agent-Skill
- 需求收集工作流文档

### Changed
- 架构边界重构：拆分collect_requirements为原子工具
- 工具数量从16个增加到23个
- 测试数量从533个增加到615个
- 测试覆盖率为95%

### Fixed
- 函数重复定义问题（check_requirement_completeness）
- mypy类型检查错误
- 文档数据不一致（测试数量、工具数量、覆盖率）

## [0.3.2] - 2026-01-27

### Fixed
- 计划管理流程规范化

## [0.3.1] - 2026-01-27

### Added
- Agent-Skill打包规范

## [0.3.0] - 2026-01-26

### Added
- GitHub MCP 集成测试
- Thinking MCP 集成测试
- 完整的集成测试套件（601个测试用例）

### Changed
- 更新工具数量声明从11个到23个
- 统一版本号为v0.3.0

### Fixed
- SKILL.md工具数量声明不一致问题
- README.md版本号不一致问题

## [0.2.1-alpha] - 2026-01-24

### Added
- 需求澄清工具（collect_requirements）
- Phase 0 技术验证工具
- 健康检查工具

### Changed
- 重构工具实现
- 优化缓存机制

## [0.2.0] - 2026-01-20

### Added
- MCP Server 基础架构
- 核心开发工具（init, validate, analyze, refactor, package）
- 批量操作工具
- 资源和提示词系统
- 完整测试套件（400+ 测试用例）

## [0.1.0] - 2026-01-15

### Added
- 项目初始化
- 基础 MCP 工具
- 文档结构
