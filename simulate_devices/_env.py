"""
从项目根目录加载 .env，供各模拟脚本通过 os.getenv 读取配置。
"""
from pathlib import Path


def load_dotenv_from_project_root():
    try:
        from dotenv import load_dotenv
        _root = Path(__file__).resolve().parent.parent
        load_dotenv(_root / ".env")
    except ImportError:
        pass
