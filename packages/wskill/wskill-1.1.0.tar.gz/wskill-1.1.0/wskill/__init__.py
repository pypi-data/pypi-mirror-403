# ============================================================================
# Windsurf Skill Manager (wskill)
# 一个用于搜索和管理Windsurf技能的命令行工具和MCP服务器
# ============================================================================

__version__ = "1.1.0"
__author__ = "ChuanKang"

from .core import SkillManager
from .cli import main

__all__ = ["SkillManager", "main", "__version__"]
