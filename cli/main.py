"""
Memory CLI 工具
支持交互式 init 和模板
"""

import os
import sys
import argparse
import yaml
from datetime import datetime

from memory import MemoryManager


def cmd_init(args):
    """初始化 Memory"""
    if args.global_init:
        memory_dir = os.path.expanduser("~/.memory")
    else:
        memory_dir = os.path.join(os.getcwd(), ".memory")
    
    if os.path.exists(memory_dir) and not args.force:
        print(f"⚠️  Memory 已存在: {memory_dir}")
        print(f"   使用 --force 强制重新初始化")
        return
    
    os.makedirs(memory_dir, exist_ok=True)
    
    project_name = args.project_name or os.path.basename(os.getcwd())
    template = args.template or "minimal"
    
    if not args.yes:
        print(f"\n📦 Memory 初始化")
        print(f"   目录: {memory_dir}")
        print(f"   项目: {project_name}")
        print(f"   模板: {template}")
        print()
        
        confirm = input("确认初始化? [Y/n]: ").strip().lower()
        if confirm and confirm != 'y':
            print("已取消")
            return
    
    config = _generate_config(project_name, template, args.global_init)
    
    config_path = os.path.join(memory_dir, "config.yaml")
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    os.makedirs(os.path.join(memory_dir, "rules"), exist_ok=True)
    os.makedirs(os.path.join(memory_dir, "sessions"), exist_ok=True)
    os.makedirs(os.path.join(memory_dir, "knowledge"), exist_ok=True)
    os.makedirs(os.path.join(memory_dir, "backups"), exist_ok=True)
    
    if template != "minimal":
        rules_path = os.path.join(memory_dir, "rules", "project.md")
        rules_content = _generate_rules(project_name, template)
        with open(rules_path, 'w', encoding='utf-8') as f:
            f.write(rules_content)
    
    print(f"\n✅ Memory 初始化完成: {memory_dir}")
    print(f"   配置文件: {config_path}")
    
    if template != "minimal":
        print(f"   规则文件: {rules_path}")


def _generate_config(project_name: str, template: str, is_global: bool) -> dict:
    """生成配置"""
    config = {
        'version': '2.0.0',
    }
    
    if not is_global:
        config['project'] = {
            'name': project_name,
            'path': os.getcwd(),
        }
    
    if template == "minimal":
        config['memory_types'] = {
            'decision': {'enabled': True},
            'milestone': {'enabled': True},
        }
    elif template == "standard":
        config['memory_types'] = {
            'decision': {'enabled': True, 'sync_to_global': False},
            'milestone': {'enabled': True, 'sync_to_global': False},
            'issue': {'enabled': True},
            'knowledge': {'enabled': True, 'sync_to_global': True},
        }
    else:  # full
        config['memory_types'] = {
            'decision': {'enabled': True, 'sync_to_global': True},
            'milestone': {'enabled': True, 'sync_to_global': True},
            'issue': {'enabled': True},
            'knowledge': {'enabled': True, 'sync_to_global': True},
            'session': {'enabled': True},
            'archive': {'enabled': True},
        }
    
    config['storage'] = {
        'type': 'sqlite',
        'path': 'memory.db',
        'wal_mode': True,
        'busy_timeout': 30000,
        'enable_fts': True,
    }
    
    config['search'] = {
        'highlight': True,
        'tokenizer': 'jieba',
    }
    
    if template in ("standard", "full"):
        config['backup'] = {
            'auto': True,
            'max_backups': 7,
        }
    
    return config


def _generate_rules(project_name: str, template: str) -> str:
    """生成规则文件"""
    content = f"""# {project_name} 项目规则

> 由 Memory 系统自动生成

## 项目信息

- 项目名称: {project_name}
- 创建时间: {datetime.now().strftime('%Y-%m-%d')}
- 模板类型: {template}

"""
    
    if template == "standard":
        content += """## 记忆类型

| 类型 | 说明 |
|:---|:---|
| decision | 重要技术决策 |
| milestone | 项目里程碑 |
| issue | 问题记录 |
| knowledge | 知识文档 |

"""
    elif template == "full":
        content += """## 记忆类型

| 类型 | 说明 | 同步到全局 |
|:---|:---|:---|
| decision | 重要技术决策 | 可选 |
| milestone | 项目里程碑 | 可选 |
| issue | 问题记录 | 否 |
| knowledge | 知识文档 | 是 |
| session | 会话记录 | 否 |
| archive | 归档内容 | 否 |

## 开发规范

请参考项目文档...

"""
    
    return content


def cmd_status(args):
    """查看状态"""
    memory_dir = os.path.expanduser("~/.memory")
    project_dir = os.path.join(os.getcwd(), ".memory")
    
    print("📊 Memory 状态\n")
    
    if os.path.exists(memory_dir):
        print(f"✅ 全局 Memory: {memory_dir}")
        db_path = os.path.join(memory_dir, "memory.db")
        config_path = os.path.join(memory_dir, "config.yaml")
        
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"   数据库: {size / 1024:.1f} KB")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
                version = cfg.get('version', 'unknown')
                print(f"   版本: {version}")
        
        if args.verbose:
            memory = MemoryManager()
            count = memory.count(scope="global")
            print(f"   记忆数: {count}")
            memory.close()
    else:
        print(f"⚠️  全局 Memory 未初始化")
    
    print()
    
    if os.path.exists(project_dir):
        print(f"✅ 项目 Memory: {project_dir}")
        db_path = os.path.join(project_dir, "memory.db")
        
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"   数据库: {size / 1024:.1f} KB")
        
        if args.verbose:
            memory = MemoryManager(project_path=os.getcwd())
            count = memory.count(scope="project")
            print(f"   记忆数: {count}")
            memory.close()
    else:
        print(f"⚠️  项目 Memory 未初始化")
        print(f"   运行 'memory init' 初始化")


def cmd_add(args):
    """添加记忆"""
    memory = MemoryManager(project_path=args.project)
    
    memory_id = memory.add(
        content=args.content,
        type=args.type,
        tags=args.tags.split(',') if args.tags else None,
        priority=args.priority,
        scope=args.scope
    )
    
    print(f"✅ 记忆已添加: ID={memory_id}")
    memory.close()


def cmd_search(args):
    """搜索记忆"""
    memory = MemoryManager(project_path=args.project)
    
    results = memory.search(
        query=args.query,
        limit=args.limit,
        scope=args.scope
    )
    
    if not results:
        print("未找到相关记忆")
        memory.close()
        return
    
    print(f"找到 {len(results)} 条结果:\n")
    for r in results:
        print(f"  [{r['id']}] {r['type']}")
        print(f"  {r['content'][:80]}...")
        if r.get('tags'):
            print(f"  标签: {', '.join(r['tags'])}")
        print()
    
    memory.close()


def cmd_list(args):
    """列出记忆"""
    memory = MemoryManager(project_path=args.project)
    
    results = memory.list(
        type=args.type,
        limit=args.limit,
        scope=args.scope
    )
    
    if not results:
        print("暂无记忆")
        memory.close()
        return
    
    print(f"共 {len(results)} 条记忆:\n")
    for r in results:
        print(f"  [{r['id']}] {r['type']} | {r['created_at'][:19]}")
        print(f"  {r['content'][:60]}...")
        print()
    
    memory.close()


def cmd_page(args):
    """分页获取"""
    memory = MemoryManager(project_path=args.project)
    
    result = memory.page(
        page=args.page,
        page_size=args.page_size,
        memory_type=args.type,
        scope=args.scope
    )
    
    print(f"第 {result['page'] + 1}/{result['total_pages']} 页")
    print(f"共 {result['total']} 条\n")
    
    for r in result['messages']:
        print(f"  [{r['id']}] {r['content'][:50]}...")
    
    memory.close()


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="Memory 系统 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init
    parser_init = subparsers.add_parser('init', help='初始化 Memory')
    parser_init.add_argument('--global', dest='global_init', action='store_true',
                           help='初始化全局 Memory (~/.memory)')
    parser_init.add_argument('--template', choices=['minimal', 'standard', 'full'],
                           help='选择模板')
    parser_init.add_argument('--project-name', help='项目名称')
    parser_init.add_argument('--yes', '-y', action='store_true',
                           help='非交互模式')
    parser_init.add_argument('--force', '-f', action='store_true',
                           help='强制重新初始化')
    
    # status
    parser_status = subparsers.add_parser('status', help='查看状态')
    parser_status.add_argument('--verbose', '-v', action='store_true',
                              help='显示详细信息')
    
    # add
    parser_add = subparsers.add_parser('add', help='添加记忆')
    parser_add.add_argument('content', help='记忆内容')
    parser_add.add_argument('--type', default='decision', help='记忆类型')
    parser_add.add_argument('--tags', help='标签（逗号分隔）')
    parser_add.add_argument('--priority', type=int, default=0, help='优先级')
    parser_add.add_argument('--scope', default='project', choices=['project', 'global'],
                          help='作用域')
    parser_add.add_argument('--project', help='项目路径')
    
    # search
    parser_search = subparsers.add_parser('search', help='搜索记忆')
    parser_search.add_argument('query', help='搜索关键词')
    parser_search.add_argument('--limit', type=int, default=10, help='结果数量')
    parser_search.add_argument('--scope', default='project', 
                            choices=['project', 'global', 'both'],
                            help='作用域')
    parser_search.add_argument('--project', help='项目路径')
    
    # list
    parser_list = subparsers.add_parser('list', help='列出记忆')
    parser_list.add_argument('--type', help='记忆类型')
    parser_list.add_argument('--limit', type=int, default=20, help='结果数量')
    parser_list.add_argument('--scope', default='project',
                            choices=['project', 'global'],
                            help='作用域')
    parser_list.add_argument('--project', help='项目路径')
    
    # page
    parser_page = subparsers.add_parser('page', help='分页获取')
    parser_page.add_argument('--page', type=int, default=0, help='页码')
    parser_page.add_argument('--page-size', type=int, default=20, help='每页数量')
    parser_page.add_argument('--type', help='记忆类型')
    parser_page.add_argument('--scope', default='project',
                           choices=['project', 'global'],
                           help='作用域')
    parser_page.add_argument('--project', help='项目路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        'init': cmd_init,
        'status': cmd_status,
        'add': cmd_add,
        'search': cmd_search,
        'list': cmd_list,
        'page': cmd_page,
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()
