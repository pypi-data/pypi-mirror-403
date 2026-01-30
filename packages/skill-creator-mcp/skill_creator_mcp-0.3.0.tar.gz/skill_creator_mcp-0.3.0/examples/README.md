# 基本使用示例

本目录包含 Skill-Creator MCP Server 的基本使用示例。

## 示例列表

### 1. 初始化新技能

**场景**：创建一个名为 "git-helper" 的简单工具技能

```python
# 通过 MCP 客户端调用
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def create_git_helper_skill():
    async with stdio_client(ServerParameters(
        command="uv",
        args=["--directory", "/path/to/skill-creator-mcp", "run", "python", "-m", "skill_creator_mcp"]
    )) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "init_skill",
                {
                    "name": "git-helper",
                    "template": "minimal",
                    "output_dir": "./skills"
                }
            )

            print(result)
```

**在 Claude Code 中使用**：
```
你：创建一个名为 git-helper 的技能，使用 minimal 模板
```

### 2. 验证技能

**场景**：验证刚创建的 git-helper 技能

```python
async def validate_git_helper_skill():
    async with stdio_client(...) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "validate_skill",
                {
                    "skill_path": "./skills/git-helper"
                }
            )

            if result["valid"]:
                print("验证通过！")
            else:
                print("验证失败：", result["errors"])
```

**在 Claude Code 中使用**：
```
你：验证 ./skills/git-helper 技能
```

### 3. 分析技能质量

**场景**：分析 git-helper 技能的代码质量

```python
async def analyze_git_helper_skill():
    async with stdio_client(...) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "analyze_skill",
                {
                    "skill_path": "./skills/git-helper",
                    "analyze_structure": True,
                    "analyze_complexity": True,
                    "analyze_quality": True
                }
            )

            print(f"总体评分: {result['quality']['overall_score']}")
            print(f"结构评分: {result['quality']['structure_score']}")
```

**在 Claude Code 中使用**：
```
你：分析 ./skills/git-helper 技能的质量
```

### 4. 访问技能模板

**场景**：获取 tool-based 模板内容

```python
async def get_tool_template():
    async with stdio_client(...) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 读取模板资源
            resource = await session.read_resource("skill://templates/tool-based")
            template_content = resource.contents[0].text

            print(template_content)
```

### 5. 获取最佳实践指南

**场景**：获取 Agent-Skills 开发最佳实践

```python
async def get_best_practices():
    async with stdio_client(...) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            resource = await session.read_resource("skill://best-practices")
            practices = resource.contents[0].text

            print(practices)
```

### 6. 使用创建技能提示

**场景**：获取创建技能的 AI 指导提示

```python
async def get_create_skill_prompt():
    async with stdio_client(...) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 获取创建技能的提示模板
            prompt = await session.get_prompt(
                "create-skill",
                {
                    "name": "my-skill",
                    "template": "tool-based"
                }
            )

            print(prompt.messages[0].content.text)
```

## 完整工作流示例

### 创建 → 验证 → 分析 工作流

```python
import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession

async def full_skill_workflow():
    """完整的技能开发工作流"""

    server_params = StdioServerParameters(
        command="uv",
        args=["--directory", "/path/to/skill-creator-mcp", "run", "python", "-m", "skill_creator_mcp"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. 创建技能
            print("1. 创建技能...")
            init_result = await session.call_tool(
                "init_skill",
                {
                    "name": "pdf-helper",
                    "template": "tool-based",
                    "output_dir": "./skills"
                }
            )
            print(f"   ✓ 创建成功: {init_result['skill_path']}")

            # 2. 验证技能
            print("2. 验证技能...")
            validate_result = await session.call_tool(
                "validate_skill",
                {
                    "skill_path": init_result['skill_path']
                }
            )
            if validate_result["valid"]:
                print(f"   ✓ 验证通过，评分: {validate_result['score']}")

            # 3. 分析技能
            print("3. 分析技能...")
            analyze_result = await session.call_tool(
                "analyze_skill",
                {
                    "skill_path": init_result['skill_path']
                }
            )
            quality = analyze_result['quality']
            print(f"   ✓ 总体评分: {quality['overall_score']}")
            print(f"   ✓ 结构评分: {quality['structure_score']}")
            print(f"   ✓ 文档评分: {quality['documentation_score']}")

            print("\n工作流完成！")

if __name__ == "__main__":
    asyncio.run(full_skill_workflow())
```

## 技能模板对比

### Minimal 模板
- **文件数**：最少
- **适用场景**：简单工具封装
- **目录结构**：SKILL.md + 基础目录

### Tool-Based 模板
- **文件数**：中等
- **适用场景**：封装现有 CLI 工具或 API
- **目录结构**：包含 references/tool-integration.md

### Workflow-Based 模板
- **文件数**：中等
- **适用场景**：多步骤工作流自动化
- **目录结构**：包含 references/workflow-steps.md

### Analyzer-Based 模板
- **文件数**：中等
- **适用场景**：代码分析、数据处理
- **目录结构**：包含 references/analysis-methods.md
