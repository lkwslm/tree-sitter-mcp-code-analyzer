# 快速开始指南

## 系统概述

这是一个基于tree-sitter的C#代码分析工具，能够解析C#代码结构并生成知识图谱供LLM理解。系统具有良好的扩展性，可以轻松支持其他编程语言。

## 安装步骤

1. **克隆项目**（如果适用）或确保所有文件都在正确位置

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

## 基本使用

### 1. 分析单个文件
```bash
python main.py --input examples/User.cs --language csharp --output analysis_output
```

### 2. 分析整个目录
```bash
python main.py --input examples --language csharp --output analysis_output
```

### 3. 压缩模式（推荐用于LLM）
```bash
# 压缩代码结构到方法级别，大幅减少上下文长度
python main.py --input examples --language csharp --compress --output compressed_output
```

### 4. 完整模式
```bash
# 保留所有详细信息（属性、字段等独立节点）
python main.py --input examples --language csharp --no-compress --output full_output
```

### 5. 指定输出格式
```bash
python main.py --input examples --language csharp --format json llm_prompt
```

### 6. 使用配置文件
```bash
python main.py --config config.yaml
```

## 输出模式对比

### 压缩模式（推荐用于LLM）
- **节点数量**: 大幅减少（减少~75%）
- **结构层次**: 文件 > 命名空间 > 类/接口 → **停在类型级别**
- **成员信息**: 合并在类型节点的metadata中
- **方法操作**: 自动推断方法的主要操作类型
- **优点**: 适合LLM理解，上下文简洁

### 完整模式
- **节点数量**: 完整保留所有细节
- **结构层次**: 文件 > 命名空间 > 类 > 方法/属性/字段
- **成员信息**: 每个成员都作为独立节点
- **关系网络**: 更详细的类型关系
- **优点**: 适合深度代码分析

### 示例对比
```
压缩模式: 16个节点  vs  完整模式: 69个节点
压缩比例: 76% 减少
```

分析完成后会在输出目录生成以下文件：

1. **knowledge_graph.json** - 完整的知识图谱JSON格式
2. **llm_prompt.txt** - 适合LLM理解的结构化文本

## 生成的知识图谱内容

### 支持的代码元素
- **命名空间** (Namespace)
- **类** (Class) 
- **接口** (Interface)
- **结构体** (Struct)
- **枚举** (Enum)
- **方法** (Method)
- **属性** (Property) 
- **字段** (Field)
- **构造函数** (Constructor)

### 关系类型
- **contains** - 包含关系（命名空间包含类等）
- **inherits_from** - 继承关系
- **uses** - 使用关系（参数类型、返回类型等）
- **returns** - 返回类型关系
- **has_type** - 类型关系（字段、属性的类型）

## 配置选项

主要配置项在 `config.yaml` 中：

```yaml
input:
  path: "."                    # 输入路径
  language: "csharp"          # 编程语言
  file_extensions: ["cs"]     # 文件扩展名
  recursive: true             # 递归搜索

output:
  directory: "./output"       # 输出目录
  formats: ["json", "llm_prompt"]

parsing:
  include_private_members: true    # 包含私有成员
  include_generated_code: false    # 排除生成的代码

knowledge_graph:
  include_inheritance: true        # 包含继承关系
  include_type_usage: true        # 包含类型使用关系
```

## 高级功能

### 1. 创建默认配置文件
```bash
python main.py --create-config my_config.yaml
```

### 2. 查看支持的语言
```bash
python main.py --list-languages
```

### 3. 详细输出模式
```bash
python main.py --input examples --verbose
```

### 4. 静默模式
```bash
python main.py --input examples --quiet
```

## LLM集成示例

生成的 `llm_prompt.txt` 可以直接用于LLM：

```
## 代码结构概览
总计 69 个代码元素，41 个关系

### 代码元素统计:
- class: 5 个
- interface: 4 个  
- method: 31 个
- property: 13 个
...

### 主要类型:
- Class: User
- Class: PremiumUser
  继承自: User
- Interface: IUserService
...
```

## 扩展到其他语言

要支持新语言，需要：

1. 安装对应的tree-sitter语言包
2. 在 `src/languages/` 下创建新的解析器类
3. 继承 `BaseParser` 并实现必要方法
4. 在 `src/languages/__init__.py` 中注册新语言

## 故障排除

### 常见问题

1. **依赖安装失败**
   - 确保Python版本兼容（推荐3.9+）
   - 可能需要更新pip: `pip install --upgrade pip`

2. **解析结果为空**
   - 检查文件路径和扩展名设置
   - 确认代码语法正确

3. **配置错误**
   - 使用 `--create-config` 创建默认配置
   - 检查YAML格式是否正确

## 性能优化

- 大型项目可使用排除模式跳过不必要的文件
- 调整递归深度限制
- 使用配置文件批量处理

## 示例项目结构

```
my-tree-sitter/
├── src/                    # 源代码
├── examples/              # 示例C#代码
├── output/               # 分析输出
├── tests/                # 测试文件
├── config.yaml          # 配置文件
├── main.py             # 主程序入口
└── requirements.txt    # 依赖包列表
```

这个工具为LLM提供了深入理解C#代码结构的能力，帮助AI更好地协助代码开发和维护工作。