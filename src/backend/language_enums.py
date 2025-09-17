"""
Defines supported programming languages for Repo Analyzer.
"""

from enum import Enum

class Language(Enum):
    """
    Enum for supported programming languages in Repo Analyzer.
    """
    PYTHON = "python"
    JAVA = "java"
    TYPESCRIPT = "typescript"
    CSHARP = "csharp"
