"""
展示如何在MCP服务器中使用依赖图查询功能
"""
import json
from typing import Dict, List, Any

# 模拟MCP工具注册和使用
def register_dependency_tools():
    """注册依赖图查询相关的MCP工具"""
    
    tools = {
        "list_available_methods": {
            "description": "列出代码库中所有可用的方法",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 50
                    }
                }
            }
        },
        
        "analyze_dependencies": {
            "description": "分析指定方法的k层依赖关系",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "target_methods": {
                        "type": ["string", "array"],
                        "description": "目标方法名或方法名列表",
                        "items": {"type": "string"}
                    },
                    "depth": {
                        "type": "integer",
                        "description": "依赖分析深度（k层），不指定则使用配置默认值",
                        "minimum": 1,
                        "maximum": 5
                    },
                    "direction": {
                        "type": "string",
                        "description": "依赖方向",
                        "enum": ["in", "out", "both"],
                        "default": "both"
                    }
                },
                "required": ["target_methods"]
            }
        },
        
        "get_dependency_report": {
            "description": "生成指定方法的依赖关系分析报告",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "target_methods": {
                        "type": ["string", "array"],
                        "description": "目标方法名或方法名列表",
                        "items": {"type": "string"}
                    },
                    "depth": {
                        "type": "integer",
                        "description": "依赖分析深度（k层），不指定则使用配置默认值",
                        "minimum": 1,
                        "maximum": 5
                    }
                },
                "required": ["target_methods"]
            }
        }
    }
    
    return tools

def example_mcp_interactions():
    """展示LLM如何使用这些MCP工具的示例对话"""
    
    print("=" * 80)
    print("MCP依赖图查询工具使用示例")
    print("=" * 80)
    
    # 示例1: LLM想了解代码库中有哪些方法
    print("\n🤖 LLM: 我想了解这个代码库中都有哪些方法可以分析")
    print("📡 MCP调用: list_available_methods")
    print("📤 参数: {\"limit\": 20}")
    
    example_response_1 = {
        "total_methods": 31,
        "methods": [
            {"name": "CreateUser", "context": "所在类: UserService", "operations": ["创建操作"]},
            {"name": "GetUserById", "context": "所在类: UserService", "operations": ["查询操作"]},
            {"name": "AddOrder", "context": "所在类: User", "operations": ["更新操作"]},
            {"name": "DeleteUser", "context": "所在类: UserService", "operations": ["删除操作"]}
        ],
        "truncated": True
    }
    
    print("📥 返回结果:")
    print(json.dumps(example_response_1, indent=2, ensure_ascii=False))
    
    # 示例2: LLM想分析特定方法的依赖关系
    print("\n\n🤖 LLM: 我想分析CreateUser方法的2层依赖关系，看看它都依赖哪些其他组件")
    print("📡 MCP调用: analyze_dependencies")
    print("📤 参数: {\"target_methods\": \"CreateUser\", \"depth\": 2, \"direction\": \"out\"}")
    
    example_response_2 = {
        "query_info": {
            "target_methods": "CreateUser",
            "depth": 2,
            "direction": "out",
            "found_target_nodes": 2
        },
        "statistics": {
            "total_nodes": 5,
            "total_edges": 3,
            "compression_ratio": 0.31,
            "node_types": {"class": 2, "interface": 1, "method": 2},
            "layer_distribution": {"0": 2, "1": 2, "2": 1}
        },
        "nodes": [
            {
                "name": "CreateUser",
                "type": "method",
                "is_target": True,
                "dependency_layer": 0
            },
            {
                "name": "IUserService", 
                "type": "interface",
                "is_target": False,
                "dependency_layer": 1
            }
        ]
    }
    
    print("📥 返回结果:")
    print(json.dumps(example_response_2, indent=2, ensure_ascii=False))
    
    # 示例3: LLM想要一个详细的分析报告
    print("\n\n🤖 LLM: 请给我生成一个关于CreateUser和DeleteUser方法的详细依赖分析报告")
    print("📡 MCP调用: get_dependency_report")
    print("📤 参数: {\"target_methods\": [\"CreateUser\", \"DeleteUser\"], \"depth\": 3}")
    
    example_response_3 = {
        "target_methods": ["CreateUser", "DeleteUser"],
        "depth": 3,
        "report": """# 依赖关系分析报告

**分析目标**: CreateUser, DeleteUser
**依赖深度**: 3 层
**分析时间**: 2025-09-11 20:30:00

统计摘要
- 相关节点总数: 8
- 依赖关系总数: 6
- 压缩比例: 44.44%
- 图密度: 0.214
- 是否为有向无环图: 是

节点类型分布
- class: 3 个
- interface: 2 个
- method: 3 个

依赖层级分布
- 第0层: 2 个节点（目标方法）
- 第1层: 3 个节点（直接依赖）
- 第2层: 2 个节点（间接依赖）
- 第3层: 1 个节点（深层依赖）

关键发现
- CreateUser方法依赖IUserService接口
- DeleteUser方法同样依赖IUserService接口
- 两个方法共享相同的基础设施组件
- 存在适当的接口抽象，便于测试和扩展

建议
- 这两个方法的依赖结构合理
- 接口抽象有助于保持代码的可维护性
- 可以考虑为这些方法编写单元测试时mock IUserService接口
""",
        "report_length": 756,
        "found_target_nodes": 2
    }
    
    print("📥 返回结果:")
    print(json.dumps({k: v for k, v in example_response_3.items() if k != 'report'}, indent=2, ensure_ascii=False))
    print(f"\n📄 报告内容:\n{example_response_3['report']}")
    
    # 使用场景总结
    print("\n" + "=" * 80)
    print("MCP工具的典型使用场景")
    print("=" * 80)
    
    scenarios = [
        {
            "场景": "代码理解",
            "描述": "LLM需要理解一个新的代码库，想知道有哪些主要功能",
            "工具": "list_available_methods → analyze_dependencies",
            "价值": "快速获得代码库的功能概览和核心依赖关系"
        },
        {
            "场景": "影响分析", 
            "描述": "修改某个方法前，想了解会影响哪些其他组件",
            "工具": "analyze_dependencies (direction='in')",
            "价值": "评估修改的影响范围，降低引入bug的风险"
        },
        {
            "场景": "重构规划",
            "描述": "计划重构某个模块，需要了解其依赖结构",
            "工具": "analyze_dependencies (direction='both') → get_dependency_report",
            "价值": "制定合理的重构策略，识别关键依赖关系"
        },
        {
            "场景": "测试策略",
            "描述": "为某个功能编写测试，需要了解需要mock哪些依赖",
            "工具": "analyze_dependencies (direction='out')",
            "价值": "识别外部依赖，确定mock策略"
        },
        {
            "场景": "架构审查",
            "描述": "审查代码架构，查找循环依赖或过度耦合",
            "工具": "get_dependency_report (高深度分析)",
            "价值": "发现架构问题，优化系统设计"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. **{scenario['场景']}**")
        print(f"   描述: {scenario['描述']}")
        print(f"   推荐工具: {scenario['工具']}")
        print(f"   价值: {scenario['价值']}")
    
    print("\n核心优势:")
    print("• **按需查询**: LLM可以根据需要主动选择分析目标")
    print("• **可控粒度**: 通过depth参数控制分析深度，平衡详细程度和性能")
    print("• **多维分析**: 支持入度、出度、双向依赖分析")
    print("• **智能压缩**: 自动将全局图压缩为相关的局部子图")
    print("• **配置灵活**: 支持通过config.yaml统一管理默认参数")

if __name__ == "__main__":
    example_mcp_interactions()