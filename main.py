# -*- coding: utf-8 -*-
"""
命令行界面
提供命令行工具来运行代码分析器
"""
import argparse
import sys
from pathlib import Path
import json

# 添加src路径
sys.path.append(str(Path(__file__).parent / 'src'))

from src.analyzer import CodeAnalyzer
from src.config.analyzer_config import AnalyzerConfig

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='Tree-sitter代码分析器 - 生成代码结构知识图谱',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py --input ./MyProject --language csharp --output ./analysis_output
  python main.py --input MyClass.cs --format json llm_prompt
  python main.py --config my_config.yaml
  python main.py --list-languages
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='输入文件或目录路径'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='输出目录路径'
    )
    
    parser.add_argument(
        '--language', '-l',
        type=str,
        choices=['csharp', 'cs'],
        help='编程语言类型'
    )
    
    parser.add_argument(
        '--format', '-f',
        nargs='+',
        choices=['json', 'llm_prompt'],
        help='输出格式（可以指定多个）'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='配置文件路径（YAML或JSON格式）'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='+',
        help='排除的文件/目录模式'
    )
    
    parser.add_argument(
        '--include-private',
        action='store_true',
        help='包含私有成员'
    )
    
    parser.add_argument(
        '--compress',
        action='store_true',
        help='压缩代码结构到方法级别（减少上LLM下文长度）'
    )
    
    parser.add_argument(
        '--no-compress',
        action='store_true',
        help='不压缩，保留完整的代码结构'
    )
    
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        default=True,
        help='递归搜索子目录（默认启用）'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_false',
        dest='recursive',
        help='不递归搜索子目录'
    )
    
    parser.add_argument(
        '--list-languages',
        action='store_true',
        help='列出支持的编程语言'
    )
    
    parser.add_argument(
        '--create-config',
        type=str,
        help='创建默认配置文件到指定路径'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出模式'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式'
    )
    
    return parser

def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # 处理特殊命令
        if args.list_languages:
            analyzer = CodeAnalyzer()
            languages = analyzer.list_supported_languages()
            print("支持的编程语言:")
            for lang in languages:
                info = analyzer.get_language_info(lang)
                extensions = ', '.join(info.get('file_extensions', []))
                print(f"  {lang}: {extensions}")
            return 0
        
        if args.create_config:
            config = AnalyzerConfig()
            config.create_default_config_file(args.create_config)
            print(f"默认配置文件已创建: {args.create_config}")
            return 0
        
        # 加载配置
        config = AnalyzerConfig(args.config)
        
        # 应用命令行参数覆盖配置
        if args.input:
            config.set('input.path', args.input)
        
        if args.output:
            config.set('output.directory', args.output)
        
        if args.language:
            config.set('input.language', args.language)
        
        if args.format:
            config.set('output.formats', args.format)
        
        if args.exclude:
            config.set('input.exclude_patterns', args.exclude)
        
        if args.include_private:
            config.set('parsing.include_private_members', True)
        
        if args.compress:
            config.set('knowledge_graph.compress_members', True)
        
        if args.no_compress:
            config.set('knowledge_graph.compress_members', False)
        
        config.set('input.recursive', args.recursive)
        
        # 设置日志级别
        if args.verbose:
            config.set('logging.level', 'DEBUG')
        elif args.quiet:
            config.set('logging.level', 'ERROR')
        
        # 验证必要参数
        if not config.get('input.path'):
            print("错误: 必须指定输入路径（--input）", file=sys.stderr)
            return 1
        
        # 创建分析器并运行分析
        analyzer = CodeAnalyzer(config)
        result = analyzer.analyze()
        
        if result['success']:
            print("分析完成!")
            
            # 显示统计信息
            stats = result['statistics']
            print(f"\n统计信息:")
            print(f"  节点总数: {stats['total_nodes']}")
            print(f"  关系总数: {stats['total_relationships']}")
            
            print(f"\n节点类型:")
            for node_type, count in stats['node_types'].items():
                print(f"  {node_type}: {count}")
            
            print(f"\n输出文件:")
            for format_name, file_path in result['output_files'].items():
                print(f"  {format_name}: {file_path}")
            
            return 0
        else:
            print(f"分析失败: {result.get('error', '未知错误')}", file=sys.stderr)
            return 1
            
    except KeyboardInterrupt:
        print("\n分析被用户中断", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"发生错误: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())