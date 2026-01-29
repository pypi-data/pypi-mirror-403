# ============================================================================
# wskill MCP 服务器
# 为 Windsurf 提供 skill 搜索和管理功能
# ============================================================================
#
# 项目信息:
#   - 名称: wskill - Windsurf Skill Manager
#   - 版本: 1.1.0
#   - 作者: ChuanKang (https://github.com/1837620622)
#   - 开源地址: https://github.com/1837620622/wskill
#   - 许可证: MIT License
#
# 功能说明:
#   - 搜索和管理本地 Windsurf 技能
#   - 发现 skills.sh 热门在线技能
#   - 一键安装在线技能到本地
#
# ============================================================================

from mcp.server.fastmcp import FastMCP
from typing import Optional
import json

from .core import SkillManager
from .online import (
    get_trending_skills,
    search_online_skills,
    install_skill,
    get_skills_install_path,
    OnlineSkill
)


# ============================================================================
# 初始化 MCP 服务器
# ============================================================================
mcp = FastMCP("wskill")

# 初始化本地技能管理器
skill_manager = SkillManager()


# ============================================================================
# 工具：列出本地技能
# ============================================================================
@mcp.tool()
def list_local_skills(category: Optional[str] = None) -> str:
    """
    列出本地已安装的 Windsurf 技能。
    
    参数:
        category: 可选，按类别筛选（如：云服务与部署、数据与可视化、AI与机器学习、前端与UI/UX、数据库、文档处理、开发工具）
    
    返回:
        本地技能列表（JSON格式）
    """
    skills = skill_manager.list_all()
    
    if category:
        categories = skill_manager.get_categories()
        if category in categories:
            skills = categories[category]
        else:
            return json.dumps({
                "error": f"未找到类别 '{category}'",
                "available_categories": list(categories.keys())
            }, ensure_ascii=False, indent=2)
    
    result = []
    for skill in skills:
        result.append({
            "name": skill.name,
            "version": skill.version,
            "description": skill.get_summary(),
            "author": skill.author,
            "keywords": skill.keywords[:5] if skill.keywords else [],
            "path": str(skill.path)
        })
    
    return json.dumps({
        "count": len(result),
        "skills": result
    }, ensure_ascii=False, indent=2)


# ============================================================================
# 工具：搜索本地技能
# ============================================================================
@mcp.tool()
def search_local_skills(query: str) -> str:
    """
    搜索本地已安装的 Windsurf 技能。
    
    参数:
        query: 搜索关键词（支持中英文）
    
    返回:
        匹配的技能列表（JSON格式）
    """
    results = skill_manager.search(query)
    
    if not results:
        return json.dumps({
            "count": 0,
            "message": f"未找到匹配 '{query}' 的本地技能",
            "suggestion": "尝试使用 list_local_skills 查看所有可用技能，或使用 search_online_skills 搜索在线技能"
        }, ensure_ascii=False, indent=2)
    
    result = []
    for skill in results:
        result.append({
            "name": skill.name,
            "version": skill.version,
            "description": skill.get_summary(),
            "keywords": skill.keywords[:5] if skill.keywords else []
        })
    
    return json.dumps({
        "count": len(result),
        "skills": result
    }, ensure_ascii=False, indent=2)


# ============================================================================
# 工具：获取本地技能详情
# ============================================================================
@mcp.tool()
def get_skill_detail(name: str) -> str:
    """
    获取本地技能的详细信息。
    
    参数:
        name: 技能名称
    
    返回:
        技能详细信息（JSON格式）
    """
    skill = skill_manager.get_skill(name)
    
    if not skill:
        similar = skill_manager.search(name)
        return json.dumps({
            "error": f"未找到名为 '{name}' 的技能",
            "similar_skills": [s.name for s in similar[:3]] if similar else []
        }, ensure_ascii=False, indent=2)
    
    return json.dumps({
        "name": skill.name,
        "version": skill.version,
        "author": skill.author,
        "description": skill.description,
        "keywords": skill.keywords,
        "path": str(skill.path),
        "content_preview": skill.content[:1000] + "..." if len(skill.content) > 1000 else skill.content
    }, ensure_ascii=False, indent=2)


# ============================================================================
# 工具：获取本地技能分类
# ============================================================================
@mcp.tool()
def get_skill_categories() -> str:
    """
    获取本地技能的分类列表。
    
    返回:
        技能分类及其包含的技能（JSON格式）
    """
    categories = skill_manager.get_categories()
    
    result = {}
    for category, skills in categories.items():
        result[category] = [s.name for s in skills]
    
    return json.dumps({
        "categories": result,
        "total_skills": sum(len(skills) for skills in categories.values())
    }, ensure_ascii=False, indent=2)


# ============================================================================
# 工具：获取热门在线技能
# ============================================================================
@mcp.tool()
def get_trending_online_skills() -> str:
    """
    获取 skills.sh 热门在线技能排行榜。
    
    返回:
        热门技能列表（JSON格式），包含下载量排名
    """
    skills = get_trending_skills()
    
    result = []
    for i, skill in enumerate(skills, 1):
        result.append({
            "rank": i,
            "name": skill.name,
            "repo": skill.repo,
            "downloads": skill.downloads,
            "description": skill.description,
            "author": skill.author
        })
    
    return json.dumps({
        "source": "skills.sh",
        "count": len(result),
        "skills": result,
        "install_command": "使用 install_online_skill 工具安装技能"
    }, ensure_ascii=False, indent=2)


# ============================================================================
# 工具：搜索在线技能
# ============================================================================
@mcp.tool()
def search_online_skills_tool(query: str) -> str:
    """
    搜索 skills.sh 在线技能。
    
    参数:
        query: 搜索关键词
    
    返回:
        匹配的在线技能列表（JSON格式）
    """
    results = search_online_skills(query)
    
    if not results:
        trending = get_trending_skills()[:5]
        return json.dumps({
            "count": 0,
            "message": f"未找到匹配 '{query}' 的在线技能",
            "trending_suggestions": [{"name": s.name, "downloads": s.downloads} for s in trending]
        }, ensure_ascii=False, indent=2)
    
    result = []
    for skill in results:
        result.append({
            "name": skill.name,
            "repo": skill.repo,
            "downloads": skill.downloads,
            "description": skill.description,
            "author": skill.author
        })
    
    return json.dumps({
        "count": len(result),
        "skills": result
    }, ensure_ascii=False, indent=2)


# ============================================================================
# 工具：安装在线技能
# ============================================================================
@mcp.tool()
def install_online_skill(skill_name: str) -> str:
    """
    安装 skills.sh 上的在线技能到本地 Windsurf skills 目录。
    
    参数:
        skill_name: 要安装的技能名称（如 react、frontend-design）
    
    返回:
        安装结果（JSON格式）
    """
    # 搜索匹配的技能
    results = search_online_skills(skill_name)
    
    if not results:
        return json.dumps({
            "success": False,
            "error": f"未找到技能 '{skill_name}'",
            "suggestion": "使用 get_trending_online_skills 查看可用技能"
        }, ensure_ascii=False, indent=2)
    
    skill = results[0]
    install_path = get_skills_install_path()
    
    # 执行安装
    success = install_skill(skill.repo, skill.name)
    
    if success:
        # 重新加载技能列表
        skill_manager._load_skills()
        
        return json.dumps({
            "success": True,
            "installed_skill": skill.name,
            "repo": skill.repo,
            "install_path": install_path,
            "message": f"技能 '{skill.name}' 安装成功！"
        }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({
            "success": False,
            "skill": skill.name,
            "error": "安装失败，请检查网络连接或手动安装",
            "manual_command": f"npx skills add {skill.repo} --skill \"{skill.name}\""
        }, ensure_ascii=False, indent=2)


# ============================================================================
# 工具：获取技能目录路径
# ============================================================================
@mcp.tool()
def get_skills_path() -> str:
    """
    获取 Windsurf 技能安装目录路径。
    
    返回:
        技能目录路径信息（JSON格式）
    """
    import platform
    
    return json.dumps({
        "platform": platform.system(),
        "skills_path": get_skills_install_path(),
        "local_skills_count": len(skill_manager.list_all())
    }, ensure_ascii=False, indent=2)


# ============================================================================
# 资源：技能目录
# ============================================================================
@mcp.resource("skills://local/list")
def resource_local_skills() -> str:
    """本地技能列表资源"""
    skills = skill_manager.list_all()
    return json.dumps([{
        "name": s.name,
        "description": s.get_summary()
    } for s in skills], ensure_ascii=False)


@mcp.resource("skills://online/trending")
def resource_trending_skills() -> str:
    """热门在线技能资源"""
    skills = get_trending_skills()
    return json.dumps([{
        "name": s.name,
        "downloads": s.downloads,
        "repo": s.repo
    } for s in skills], ensure_ascii=False)


# ============================================================================
# 主函数
# ============================================================================
def main():
    """MCP 服务器入口"""
    mcp.run()


if __name__ == "__main__":
    main()
