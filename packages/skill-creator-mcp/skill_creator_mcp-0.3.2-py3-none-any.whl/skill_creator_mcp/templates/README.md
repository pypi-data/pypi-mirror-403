# Templates 目录说明

## 设计意图

本目录为**刻意设计为空**，因为所有技能模板都**内嵌**在 `resources/templates.py` 模块中。

## 为什么采用内嵌设计？

### 1. 类型安全
- 模板内容作为 Python 常量定义，获得完整的类型检查
- 编译时验证模板类型，避免运行时错误
- IDE 自动补全和重构支持

### 2. 版本控制
- 模板与代码同步演进，避免版本不一致
- 代码审查时模板变更可见
- 单一代码库，降低维护复杂度

### 3. 部署简便
- 无需额外的文件打包和分发
- 模板随 MCP Server 一起安装
- 无路径解析问题

### 4. 性能优化
- 模板内容在模块导入时加载到内存
- 避免频繁的文件 I/O 操作
- 支持模板内容的动态生成

## 如何获取模板？

### 方法1：通过 MCP 资源访问（推荐）

```python
# 通过 MCP Client 读取
resource = await session.read_resource("http://skills/schema/templates/minimal")
template_content = resource.contents[0].text
```

### 方法2：通过 Python API

```python
from skill_creator_mcp.resources.templates import get_template_content, TemplateType

# 获取模板内容
content = get_template_content(TemplateType.MINIMAL)
```

### 方法3：通过 MCP Server 工具

```python
# 使用 init_skill 工具时指定模板类型
init_skill(name="my-skill", template="tool-based")
```

## 可用模板类型

| 模板类型 | 描述 | 适用场景 |
|---------|------|----------|
| `minimal` | 最小化模板 | 简单功能，快速原型 |
| `tool-based` | 工具集成型 | 封装特定工具或 API |
| `workflow-based` | 工作流型 | 多步骤任务流程 |
| `analyzer-based` | 分析型 | 数据分析或代码分析 |

## 模板文件结构

每个模板类型包含：
- `SKILL.md` - 主文档模板
- 引用文件（非 minimal 模板）- `tool-integration.md` / `workflow-steps.md` / `analysis-methods.md`
- 使用示例 - `usage-examples.md` / `decision-points.md` / `metrics.md`

## 未来扩展方向

如果需要添加自定义模板：

1. 在 `resources/templates.py` 中定义新的模板类型
2. 更新 `TemplateType` 字面量
3. 添加模板内容和引用文件
4. 更新文档和测试

## 相关文件

- `resources/templates.py` - 模板内容定义
- `resources/best_practices.py` - 最佳实践指南
- `resources/validation_rules.py` - 验证规则
