# ============================================================================
# 命令行接口模块
# ============================================================================

import argparse
import sys
from typing import List

from .core import SkillManager, Skill
from .online import get_trending_skills, search_online_skills, install_skill, open_skills_website, OnlineSkill
from . import __version__


# ============================================================================
# 终端颜色配置
# ============================================================================
class Colors:
    """终端颜色代码"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def color_text(text: str, color: str) -> str:
    """给文本添加颜色"""
    return f"{color}{text}{Colors.RESET}"


# ============================================================================
# 格式化输出函数
# ============================================================================
def print_skill_brief(skill: Skill, index: int = None):
    """
    打印技能简要信息
    
    参数:
        skill: 技能对象
        index: 序号（可选）
    """
    prefix = f"{index}. " if index else "• "
    name = color_text(skill.name, Colors.GREEN + Colors.BOLD)
    version = color_text(f"v{skill.version}", Colors.DIM)
    
    print(f"{prefix}{name} {version}")
    print(f"   {skill.get_summary()}")
    
    if skill.keywords:
        keywords_str = ", ".join(skill.keywords[:5])
        if len(skill.keywords) > 5:
            keywords_str += f" (+{len(skill.keywords) - 5})"
        print(f"   {color_text('关键词:', Colors.CYAN)} {keywords_str}")
    print()


def print_online_skill(skill: OnlineSkill, index: int = None):
    """
    打印在线技能信息
    
    参数:
        skill: 在线技能对象
        index: 序号（可选）
    """
    prefix = f"{index}. " if index else "• "
    name = color_text(skill.name, Colors.GREEN + Colors.BOLD)
    downloads = color_text(f"⬇ {skill.downloads}", Colors.YELLOW)
    author = color_text(f"by {skill.author}", Colors.DIM)
    
    print(f"{prefix}{name} {downloads} {author}")
    print(f"   {skill.description}")
    print(f"   {color_text('仓库:', Colors.CYAN)} {skill.repo}")
    print()


def print_skill_detail(skill: Skill):
    """
    打印技能详细信息
    
    参数:
        skill: 技能对象
    """
    print()
    print(color_text("=" * 60, Colors.DIM))
    print(color_text(f"  {skill.name}", Colors.GREEN + Colors.BOLD))
    print(color_text("=" * 60, Colors.DIM))
    print()
    
    print(f"{color_text('版本:', Colors.CYAN)} {skill.version}")
    print(f"{color_text('作者:', Colors.CYAN)} {skill.author}")
    print(f"{color_text('路径:', Colors.CYAN)} {skill.path}")
    print()
    
    print(color_text("描述:", Colors.CYAN))
    print(f"  {skill.description}")
    print()
    
    if skill.keywords:
        print(color_text("关键词:", Colors.CYAN))
        print(f"  {', '.join(skill.keywords)}")
        print()
    
    # 显示SKILL.md内容摘要（前30行）
    print(color_text("内容预览:", Colors.CYAN))
    lines = skill.content.split('\n')
    preview_lines = lines[:30]
    for line in preview_lines:
        print(f"  {line}")
    if len(lines) > 30:
        print(color_text(f"  ... (还有 {len(lines) - 30} 行)", Colors.DIM))
    print()


def print_categories(manager: SkillManager):
    """
    按类别打印技能
    
    参数:
        manager: 技能管理器
    """
    categories = manager.get_categories()
    
    print()
    print(color_text("Windsurf Skills 分类列表", Colors.HEADER + Colors.BOLD))
    print(color_text("=" * 50, Colors.DIM))
    print()
    
    for category, skills in categories.items():
        print(color_text(f"📁 {category} ({len(skills)})", Colors.YELLOW + Colors.BOLD))
        for skill in skills:
            print(f"   • {color_text(skill.name, Colors.GREEN)}")
        print()


# ============================================================================
# 命令处理函数
# ============================================================================
def cmd_list(args, manager: SkillManager):
    """列出所有技能"""
    skills = manager.list_all()
    
    if args.category:
        print_categories(manager)
        return
    
    print()
    print(color_text(f"Windsurf Skills ({len(skills)} 个技能)", Colors.HEADER + Colors.BOLD))
    print(color_text("=" * 50, Colors.DIM))
    print()
    
    for i, skill in enumerate(skills, 1):
        print_skill_brief(skill, i)


def cmd_search(args, manager: SkillManager):
    """搜索技能"""
    query = args.query
    results = manager.search(query)
    
    print()
    if not results:
        print(color_text(f"未找到匹配 '{query}' 的技能", Colors.YELLOW))
        print()
        print("建议：")
        print("  • 尝试使用更短的关键词")
        print("  • 使用 'wskill list' 查看所有可用技能")
        print("  • 尝试英文关键词（如 dashboard, kaggle, ui）")
        return
    
    print(color_text(f"搜索 '{query}' 找到 {len(results)} 个技能:", Colors.HEADER + Colors.BOLD))
    print(color_text("=" * 50, Colors.DIM))
    print()
    
    for i, skill in enumerate(results, 1):
        print_skill_brief(skill, i)


def cmd_show(args, manager: SkillManager):
    """显示技能详情"""
    name = args.name
    skill = manager.get_skill(name)
    
    if not skill:
        print(color_text(f"未找到名为 '{name}' 的技能", Colors.RED))
        print()
        
        # 尝试模糊匹配
        similar = manager.search(name)
        if similar:
            print("您是否在找：")
            for s in similar[:3]:
                print(f"  • {color_text(s.name, Colors.GREEN)}")
        return
    
    print_skill_detail(skill)


def cmd_path(args, manager: SkillManager):
    """显示技能目录路径"""
    print(manager.skills_path)


def cmd_trending(args):
    """显示热门在线技能"""
    skills = get_trending_skills()
    
    print()
    print(color_text("🔥 热门 Agent Skills (来自 skills.sh)", Colors.HEADER + Colors.BOLD))
    print(color_text("=" * 55, Colors.DIM))
    print()
    
    for i, skill in enumerate(skills, 1):
        print_online_skill(skill, i)
    
    print(color_text("提示:", Colors.CYAN), "使用以下命令安装技能:")
    print(f"  wskill install <技能名>")
    print(f"  或访问 https://skills.sh 查看更多")
    print()


def cmd_install(args):
    """安装在线技能"""
    skill_name = args.skill
    
    # 查找技能
    skills = search_online_skills(skill_name)
    
    if not skills:
        print(color_text(f"未找到技能 '{skill_name}'", Colors.YELLOW))
        print()
        print("可用的热门技能:")
        for skill in get_trending_skills()[:5]:
            print(f"  • {color_text(skill.name, Colors.GREEN)}")
        return
    
    skill = skills[0]
    print()
    print(color_text(f"正在安装: {skill.name}", Colors.HEADER + Colors.BOLD))
    print(f"  来源: {skill.repo}")
    print(f"  描述: {skill.description}")
    print()
    
    success = install_skill(skill.repo, skill.name)
    
    if success:
        print(color_text("✓ 安装成功!", Colors.GREEN))
    else:
        print(color_text("✗ 安装失败，请检查网络或手动安装:", Colors.RED))
        print(f"  npx skills add {skill.repo} --skill \"{skill.name}\"")


def cmd_web(args):
    """打开 skills.sh 网站"""
    print("正在打开 skills.sh ...")
    open_skills_website()


# ============================================================================
# 主函数
# ============================================================================
def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        prog='wskill',
        description='Windsurf Skill Manager - 搜索和管理Windsurf技能',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  wskill list              列出本地所有技能
  wskill list -c           按类别列出技能
  wskill search kaggle     搜索包含kaggle的技能
  wskill show ui-ux-pro-max  查看技能详情
  wskill trending          查看热门在线技能
  wskill install react     安装热门技能
  wskill web               打开 skills.sh 网站
        '''
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'wskill {__version__}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # --------------------------------------------------------------------
    # list 命令
    # --------------------------------------------------------------------
    list_parser = subparsers.add_parser('list', aliases=['ls', 'l'], help='列出所有技能')
    list_parser.add_argument(
        '-c', '--category',
        action='store_true',
        help='按类别分组显示'
    )
    
    # --------------------------------------------------------------------
    # search 命令
    # --------------------------------------------------------------------
    search_parser = subparsers.add_parser('search', aliases=['s', 'find'], help='搜索技能')
    search_parser.add_argument('query', help='搜索关键词')
    
    # --------------------------------------------------------------------
    # show 命令
    # --------------------------------------------------------------------
    show_parser = subparsers.add_parser('show', aliases=['info', 'i'], help='显示技能详情')
    show_parser.add_argument('name', help='技能名称')
    
    # --------------------------------------------------------------------
    # path 命令
    # --------------------------------------------------------------------
    path_parser = subparsers.add_parser('path', help='显示技能目录路径')
    
    # --------------------------------------------------------------------
    # trending 命令（在线热门技能）
    # --------------------------------------------------------------------
    trending_parser = subparsers.add_parser('trending', aliases=['hot', 't'], help='查看热门在线技能')
    
    # --------------------------------------------------------------------
    # install 命令（安装在线技能）
    # --------------------------------------------------------------------
    install_parser = subparsers.add_parser('install', aliases=['add', 'get'], help='安装在线技能')
    install_parser.add_argument('skill', help='要安装的技能名称')
    
    # --------------------------------------------------------------------
    # web 命令（打开 skills.sh）
    # --------------------------------------------------------------------
    web_parser = subparsers.add_parser('web', aliases=['open'], help='打开 skills.sh 网站')
    
    # 解析参数
    args = parser.parse_args()
    
    # 初始化管理器
    manager = SkillManager()
    
    # 执行命令
    if args.command in ['list', 'ls', 'l']:
        cmd_list(args, manager)
    elif args.command in ['search', 's', 'find']:
        cmd_search(args, manager)
    elif args.command in ['show', 'info', 'i']:
        cmd_show(args, manager)
    elif args.command == 'path':
        cmd_path(args, manager)
    elif args.command in ['trending', 'hot', 't']:
        cmd_trending(args)
    elif args.command in ['install', 'add', 'get']:
        cmd_install(args)
    elif args.command in ['web', 'open']:
        cmd_web(args)
    else:
        # 默认显示帮助
        parser.print_help()


if __name__ == '__main__':
    main()
