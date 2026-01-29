# ============================================================================
# 在线功能模块：获取热门技能和安装技能
# ============================================================================

import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional


# ============================================================================
# 在线技能数据类
# ============================================================================
@dataclass
class OnlineSkill:
    """在线技能数据"""
    name: str                  # 技能名称
    repo: str                  # 仓库地址
    downloads: str             # 下载量
    description: str           # 描述
    author: str = "Unknown"    # 作者


# ============================================================================
# 热门技能列表（来自 skills.sh）
# ============================================================================
TRENDING_SKILLS = [
    OnlineSkill(
        name="vercel-react-best-practices",
        repo="vercel-labs/agent-skills",
        downloads="37.9K",
        description="40+ 条 React/Next.js 优化规则",
        author="Vercel"
    ),
    OnlineSkill(
        name="web-design-guidelines",
        repo="vercel-labs/agent-skills",
        downloads="28.8K",
        description="100+ 条 UI/UX 审查规则",
        author="Vercel"
    ),
    OnlineSkill(
        name="remotion-best-practices",
        repo="remotion-dev/skills",
        downloads="19.1K",
        description="Remotion 视频制作最佳实践",
        author="Remotion"
    ),
    OnlineSkill(
        name="frontend-design",
        repo="anthropics/skills",
        downloads="7.7K",
        description="Anthropic 官方前端设计指南",
        author="Anthropic"
    ),
    OnlineSkill(
        name="skill-creator",
        repo="anthropics/skills",
        downloads="3.8K",
        description="Anthropic 技能创建工具",
        author="Anthropic"
    ),
    OnlineSkill(
        name="building-native-ui",
        repo="expo/skills",
        downloads="2.8K",
        description="Expo React Native UI 开发指南",
        author="Expo"
    ),
    OnlineSkill(
        name="agent-browser",
        repo="vercel-labs/agent-browser",
        downloads="2.7K",
        description="AI Agent 浏览器自动化工具",
        author="Vercel"
    ),
    OnlineSkill(
        name="better-auth-best-practices",
        repo="better-auth/skills",
        downloads="2.4K",
        description="认证授权最佳实践",
        author="Better Auth"
    ),
    OnlineSkill(
        name="supabase-best-practices",
        repo="supabase/supabase",
        downloads="1.5K",
        description="Supabase 后端开发最佳实践",
        author="Supabase"
    ),
    OnlineSkill(
        name="stripe-best-practices",
        repo="stripe/ai",
        downloads="222",
        description="Stripe 支付集成最佳实践",
        author="Stripe"
    ),
]


# ============================================================================
# 在线功能函数
# ============================================================================
def get_trending_skills() -> List[OnlineSkill]:
    """
    获取热门技能列表
    
    返回:
        热门技能列表
    """
    return TRENDING_SKILLS


def search_online_skills(query: str) -> List[OnlineSkill]:
    """
    搜索在线技能
    
    参数:
        query: 搜索关键词
    
    返回:
        匹配的技能列表
    """
    query_lower = query.lower()
    results = []
    
    for skill in TRENDING_SKILLS:
        if (query_lower in skill.name.lower() or 
            query_lower in skill.description.lower() or
            query_lower in skill.author.lower()):
            results.append(skill)
    
    return results


def get_skills_install_path() -> str:
    """
    获取技能安装目录路径（支持多平台）
    
    返回:
        技能安装目录的绝对路径
    """
    import platform
    import os
    
    system = platform.system()
    
    if system == "Windows":
        # Windows: %APPDATA%\Codeium\windsurf\skills
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            return os.path.join(appdata, "Codeium", "windsurf", "skills")
        return os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Codeium", "windsurf", "skills")
    else:
        # macOS / Linux: ~/.codeium/windsurf/skills
        return os.path.join(os.path.expanduser("~"), ".codeium", "windsurf", "skills")


def install_skill(repo: str, skill_name: Optional[str] = None) -> bool:
    """
    安装技能到 Windsurf skills 目录（使用 npx skills add）
    
    参数:
        repo: 仓库地址（如 vercel-labs/agent-skills）
        skill_name: 技能名称（可选）
    
    返回:
        是否安装成功
    """
    import os
    
    # 获取正确的安装路径
    install_path = get_skills_install_path()
    
    # 确保目录存在
    os.makedirs(install_path, exist_ok=True)
    
    # 保存当前工作目录
    original_cwd = os.getcwd()
    
    try:
        # 切换到安装目录
        os.chdir(install_path)
        
        # 构建命令
        cmd = ["npx", "skills", "add", repo]
        if skill_name:
            cmd.extend(["--skill", skill_name])
        
        print(f"安装目录: {install_path}")
        print(f"执行: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("错误: 未找到 npx 命令，请确保已安装 Node.js")
        return False
    except Exception as e:
        print(f"安装失败: {e}")
        return False
    finally:
        # 恢复原工作目录
        os.chdir(original_cwd)


def open_skills_website():
    """打开 skills.sh 网站"""
    import webbrowser
    webbrowser.open("https://skills.sh")
