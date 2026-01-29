# ============================================================================
# 核心模块：Skill解析和搜索功能
# ============================================================================

import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import yaml


# ============================================================================
# Skill数据类：存储单个技能的元数据
# ============================================================================
@dataclass
class Skill:
    """技能数据类"""
    name: str                          # 技能名称
    description: str                   # 技能描述
    author: str = "Unknown"            # 作者
    version: str = "1.0.0"             # 版本
    path: Path = None                  # 技能路径
    keywords: List[str] = field(default_factory=list)  # 关键词列表
    content: str = ""                  # SKILL.md完整内容
    
    def matches(self, query: str) -> bool:
        """
        检查技能是否匹配搜索查询
        
        参数:
            query: 搜索关键词
        
        返回:
            是否匹配
        """
        query_lower = query.lower()
        
        # 检查名称、描述、关键词
        if query_lower in self.name.lower():
            return True
        if query_lower in self.description.lower():
            return True
        for kw in self.keywords:
            if query_lower in kw.lower():
                return True
        
        return False
    
    def get_summary(self) -> str:
        """获取技能摘要"""
        desc = self.description
        if len(desc) > 80:
            desc = desc[:77] + "..."
        return desc


# ============================================================================
# SkillManager类：管理所有技能的核心类
# ============================================================================
class SkillManager:
    """Windsurf技能管理器"""
    
    @staticmethod
    def get_default_skills_path() -> Path:
        """
        获取默认技能目录路径（支持多平台）
        
        返回:
            技能目录路径
        """
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Windows: %APPDATA%\Codeium\windsurf\skills
            appdata = os.environ.get('APPDATA', '')
            if appdata:
                return Path(appdata) / "Codeium" / "windsurf" / "skills"
            # 备选路径
            return Path.home() / "AppData" / "Roaming" / "Codeium" / "windsurf" / "skills"
        elif system == "Darwin":
            # macOS: ~/.codeium/windsurf/skills
            return Path.home() / ".codeium" / "windsurf" / "skills"
        else:
            # Linux: ~/.codeium/windsurf/skills
            return Path.home() / ".codeium" / "windsurf" / "skills"
    
    # 默认技能目录（延迟计算）
    DEFAULT_SKILLS_PATH = None
    
    def __init__(self, skills_path: Optional[Path] = None):
        """
        初始化技能管理器
        
        参数:
            skills_path: 技能目录路径，默认根据操作系统自动检测
        """
        self.skills_path = skills_path or self.get_default_skills_path()
        self.skills: List[Skill] = []
        self._load_skills()
    
    def _parse_frontmatter(self, content: str) -> Dict:
        """
        解析YAML frontmatter
        
        参数:
            content: SKILL.md文件内容
        
        返回:
            解析后的元数据字典
        """
        # 匹配 --- 包围的YAML内容
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            try:
                yaml_content = match.group(1)
                return yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError:
                return {}
        return {}
    
    def _extract_keywords(self, description: str) -> List[str]:
        """
        从描述中提取关键词
        
        参数:
            description: 技能描述
        
        返回:
            关键词列表
        """
        keywords = []
        
        # 查找触发关键词部分
        if "触发关键词" in description or "关键词" in description:
            # 提取冒号后的内容
            parts = re.split(r'触发关键词[：:]|关键词[：:]', description)
            if len(parts) > 1:
                kw_part = parts[-1].strip().rstrip('。"\'')
                # 按逗号、顿号分割
                keywords = [k.strip() for k in re.split(r'[,，、]', kw_part) if k.strip()]
        
        return keywords
    
    def _load_skills(self):
        """加载所有技能"""
        self.skills = []
        
        if not self.skills_path.exists():
            return
        
        # 遍历技能目录
        for skill_dir in self.skills_path.iterdir():
            if not skill_dir.is_dir():
                continue
            if skill_dir.name.startswith('.'):
                continue
            
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            
            try:
                content = skill_file.read_text(encoding='utf-8')
                metadata = self._parse_frontmatter(content)
                
                name = metadata.get('name', skill_dir.name)
                description = metadata.get('description', '')
                
                # 清理描述中的引号
                if description.startswith('"') and description.endswith('"'):
                    description = description[1:-1]
                
                skill = Skill(
                    name=name,
                    description=description,
                    author=metadata.get('author', 'Unknown'),
                    version=metadata.get('version', '1.0.0'),
                    path=skill_dir,
                    keywords=self._extract_keywords(description),
                    content=content
                )
                self.skills.append(skill)
                
            except Exception as e:
                # 跳过无法解析的技能
                continue
        
        # 按名称排序
        self.skills.sort(key=lambda s: s.name)
    
    def list_all(self) -> List[Skill]:
        """
        列出所有技能
        
        返回:
            技能列表
        """
        return self.skills
    
    def search(self, query: str) -> List[Skill]:
        """
        搜索技能
        
        参数:
            query: 搜索关键词
        
        返回:
            匹配的技能列表
        """
        if not query:
            return self.skills
        
        results = []
        for skill in self.skills:
            if skill.matches(query):
                results.append(skill)
        
        return results
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """
        获取指定技能
        
        参数:
            name: 技能名称
        
        返回:
            技能对象或None
        """
        for skill in self.skills:
            if skill.name.lower() == name.lower():
                return skill
        return None
    
    def get_categories(self) -> Dict[str, List[Skill]]:
        """
        按类别分组技能
        
        返回:
            类别->技能列表的字典
        """
        categories = {
            "云服务与部署": [],
            "数据与可视化": [],
            "AI与机器学习": [],
            "前端与UI/UX": [],
            "数据库": [],
            "文档处理": [],
            "开发工具": [],
            "其他": []
        }
        
        # 关键词映射
        category_keywords = {
            "云服务与部署": ["aws", "cloudflare", "vercel", "railway", "deploy"],
            "数据与可视化": ["analytics", "charts", "metrics", "visualization", "mermaid"],
            "AI与机器学习": ["kaggle", "langchain", "ai", "agent", "fal"],
            "前端与UI/UX": ["ui", "ux", "frontend", "responsive", "mobile", "figma", "accessibility"],
            "数据库": ["mongodb", "database"],
            "文档处理": ["docx", "xlsx", "excel", "word"],
            "开发工具": ["bun", "github", "copilot", "git"]
        }
        
        for skill in self.skills:
            categorized = False
            skill_text = f"{skill.name} {skill.description}".lower()
            
            for category, keywords in category_keywords.items():
                for kw in keywords:
                    if kw in skill_text:
                        categories[category].append(skill)
                        categorized = True
                        break
                if categorized:
                    break
            
            if not categorized:
                categories["其他"].append(skill)
        
        # 移除空类别
        return {k: v for k, v in categories.items() if v}
