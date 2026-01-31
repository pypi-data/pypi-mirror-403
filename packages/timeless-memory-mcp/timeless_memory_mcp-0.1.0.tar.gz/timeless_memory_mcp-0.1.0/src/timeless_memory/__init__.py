"""
Timeless Memory MCP Server
個人記憶系統 - 雙索引架構（Markdown + SQLite FTS5）

支援多實例：設定 TIMELESS_HOME 環境變數指向不同目錄
  - 個人: ~/Documents/timeless-memory (預設)
  - 公司: ~/Documents/company-memory
"""

__version__ = "0.1.0"

from pathlib import Path
import os

# 嘗試載入 .env 檔案（如果存在）
try:
    from dotenv import load_dotenv
    # 從當前工作目錄或父目錄尋找 .env
    load_dotenv(verbose=False)
except ImportError:
    # python-dotenv 未安裝，跳過
    pass

# 預設根目錄
DEFAULT_HOME = Path.home() / "Documents" / "timeless-memory"


def get_home() -> Path:
    """取得 Timeless Memory 根目錄（支援 TIMELESS_HOME 環境變數）"""
    return Path(os.getenv("TIMELESS_HOME", str(DEFAULT_HOME)))


def get_data_dir() -> Path:
    """取得資料目錄（支援環境變數覆寫）"""
    if os.getenv("TIMELESS_DATA_DIR"):
        return Path(os.getenv("TIMELESS_DATA_DIR"))
    return get_home() / "data"


def get_index_dir() -> Path:
    """取得 Markdown 索引目錄"""
    if os.getenv("TIMELESS_INDEX_DIR"):
        return Path(os.getenv("TIMELESS_INDEX_DIR"))
    return get_home() / "索引"


def get_db_path() -> Path:
    """取得 SQLite 資料庫路徑"""
    if os.getenv("TIMELESS_DB_PATH"):
        return Path(os.getenv("TIMELESS_DB_PATH"))
    return get_home() / ".database" / "memories.db"
