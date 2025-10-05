# MCP 路径解析器使用指南

## 概述

MCP 路径解析器为 Tree-Sitter MCP 代码分析器提供了智能路径检测功能，能够自动定位到 `./workspace/repo/username` 下的项目，支持多种路径解析策略和用户管理功能。

## 功能特性

### 🎯 智能路径解析
- **自动路径检测**: 自动定位到用户项目目录
- **多种匹配策略**: 支持精确匹配、项目名匹配、模糊匹配
- **路径建议**: 提供智能的项目路径建议

### 👥 用户管理
- **多用户支持**: 支持多个用户的项目管理
- **默认用户设置**: 可配置默认用户
- **用户项目统计**: 显示每个用户的项目数量

### ⚙️ 配置管理
- **灵活配置**: 支持自定义工作空间根目录、搜索策略等
- **配置持久化**: 配置自动保存到文件
- **备用配置**: 支持从现有配置文件迁移

## 配置文件

### 主配置文件: `config/path_resolver_config.json`

```json
{
  "workspace_root": "./workspace",
  "default_username": "lkwslm",
  "search_strategies": {
    "exact_match": {
      "enabled": true,
      "priority": 1
    },
    "project_name_match": {
      "enabled": true,
      "priority": 2
    },
    "fuzzy_match": {
      "enabled": true,
      "priority": 3,
      "threshold": 0.6
    }
  },
  "auto_detection": {
    "enabled": true,
    "fallback_to_current_dir": true,
    "suggest_alternatives": true,
    "max_suggestions": 5
  },
  "path_patterns": {
    "user_projects": "{workspace_root}/repo/{username}",
    "project_path": "{workspace_root}/repo/{username}/{project_name}"
  },
  "logging": {
    "enabled": true,
    "level": "INFO"
  }
}
```

## MCP 工具使用

### 1. 项目分析 (analyze_project)

现在支持智能路径解析：

```json
{
  "name": "analyze_project",
  "arguments": {
    "project_path": "tree-sitter-mcp-code-analyzer",
    "username": "lkwslm"
  }
}
```

**支持的路径格式:**
- 项目名: `"tree-sitter-mcp-code-analyzer"`
- 相对路径: `"./my-project"`
- 绝对路径: `"/full/path/to/project"`

### 2. 列出用户项目 (list_user_projects)

```json
{
  "name": "list_user_projects",
  "arguments": {
    "username": "lkwslm"  // 可选，默认使用配置的用户
  }
}
```

**返回示例:**
```
# 📁 用户 lkwslm 的项目列表

1. **tree-sitter-mcp-code-analyzer**
   📂 路径: `./workspace/repo/lkwslm/tree-sitter-mcp-code-analyzer`
   📝 描述: Tree-sitter based code analyzer with MCP support

2. **my-other-project**
   📂 路径: `./workspace/repo/lkwslm/my-other-project`
```

### 3. 列出可用用户 (list_available_users)

```json
{
  "name": "list_available_users",
  "arguments": {}
}
```

**返回示例:**
```
# 👥 可用用户列表

1. **lkwslm**
   📂 路径: `./workspace/repo/lkwslm`
   📁 项目数: 5
   ⭐ 默认用户

2. **other-user**
   📂 路径: `./workspace/repo/other-user`
   📁 项目数: 3
```

### 4. 获取项目建议 (get_project_suggestions)

```json
{
  "name": "get_project_suggestions",
  "arguments": {
    "partial_name": "tree",
    "username": "lkwslm"  // 可选
  }
}
```

**返回示例:**
```
# 🔍 项目建议 (匹配: 'tree')

1. **tree-sitter-mcp-code-analyzer**
   👤 用户: lkwslm
   📂 路径: `./workspace/repo/lkwslm/tree-sitter-mcp-code-analyzer`
   🎯 匹配度: 0.90
   📝 描述: Tree-sitter based code analyzer with MCP support
```

### 5. 设置默认用户 (set_default_user)

```json
{
  "name": "set_default_user",
  "arguments": {
    "username": "lkwslm"
  }
}
```

## 路径解析策略

### 1. 精确匹配 (Exact Match)
- 直接匹配完整路径
- 优先级最高

### 2. 项目名匹配 (Project Name Match)
- 在用户目录下查找匹配的项目名
- 支持部分匹配

### 3. 模糊匹配 (Fuzzy Match)
- 基于字符相似度的模糊匹配
- 可配置匹配阈值

## 使用场景

### 场景 1: 快速项目分析
```bash
# 只需要项目名，自动定位到正确路径
analyze_project("my-project")
# 自动解析为: ./workspace/repo/lkwslm/my-project
```

### 场景 2: 多用户环境
```bash
# 指定用户分析项目
analyze_project("project-name", username="other-user")
# 解析为: ./workspace/repo/other-user/project-name
```

### 场景 3: 项目发现
```bash
# 查找包含特定关键词的项目
get_project_suggestions("api")
# 返回所有包含"api"的项目建议
```

## 错误处理

### 常见错误及解决方案

1. **项目未找到**
   - 检查项目名是否正确
   - 使用 `get_project_suggestions` 获取建议
   - 确认用户名是否正确

2. **配置文件错误**
   - 检查配置文件格式是否正确
   - 系统会自动使用备用配置

3. **权限问题**
   - 确保对工作空间目录有读写权限

## 最佳实践

### 1. 配置管理
- 定期备份配置文件
- 根据团队需求调整搜索策略
- 设置合适的默认用户

### 2. 项目组织
- 保持清晰的目录结构: `workspace/repo/username/project`
- 为项目添加 README 文件以提供描述
- 使用有意义的项目名称

### 3. 性能优化
- 避免在工作空间中存放大量无关文件
- 定期清理不需要的项目
- 合理设置模糊匹配阈值

## 故障排除

### 调试模式
在配置文件中启用详细日志：
```json
{
  "logging": {
    "enabled": true,
    "level": "DEBUG"
  }
}
```

### 重置配置
删除配置文件并重启服务，系统会自动创建默认配置。

### 手动路径指定
如果自动解析失败，可以使用绝对路径：
```json
{
  "project_path": "/absolute/path/to/project"
}
```

## 更新日志

- **v1.0.0**: 初始版本，支持基本路径解析
- **v1.1.0**: 添加用户管理功能
- **v1.2.0**: 增强项目建议和配置管理
- **v1.3.0**: 添加模糊匹配和智能评分