"""
Manager Factory - 統一管理器初始化
提供單例模式的 Manager 實例，避免重複初始化
"""
import sys
from typing import Optional, Tuple
from pathlib import Path

from timeless_memory import get_home, get_data_dir, get_db_path


def _log(msg: str):
    """輸出到 stderr（避免干擾 MCP stdio 通訊）"""
    print(msg, file=sys.stderr)
from .memory_manager import MemoryManager
from .index_manager import IndexManager
from .retrieval_engine import RetrievalEngine
from .entity_manager import EntityManager
from .relation_manager import RelationManager
from .resolver import EntityResolver


class ManagerFactory:
    """
    管理器工廠 - 單例模式
    確保所有介面層（MCP/CLI）使用相同的 Manager 實例
    """
    
    _instance: Optional['ManagerFactory'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._memory_manager: Optional[MemoryManager] = None
        self._index_manager: Optional[IndexManager] = None
        self._retrieval_engine: Optional[RetrievalEngine] = None
        self._entity_manager: Optional[EntityManager] = None
        self._relation_manager: Optional[RelationManager] = None
        self._entity_resolver: Optional[EntityResolver] = None
        
        self._initialized = True
    
    def get_managers(
        self,
        quiet: bool = False
    ) -> Tuple[
        MemoryManager,
        IndexManager,
        RetrievalEngine,
        EntityManager,
        RelationManager,
        EntityResolver
    ]:
        """
        取得所有管理器（懶載入）
        
        Args:
            quiet: 是否靜默模式（不輸出路徑資訊）
        
        Returns:
            (memory_manager, index_manager, retrieval_engine,
             entity_manager, relation_manager, entity_resolver)
        """
        if self._memory_manager is None:
            self._initialize_managers(quiet)
        
        return (
            self._memory_manager,
            self._index_manager,
            self._retrieval_engine,
            self._entity_manager,
            self._relation_manager,
            self._entity_resolver
        )
    
    def _initialize_managers(self, quiet: bool = False):
        """初始化所有管理器"""
        home = get_home()
        data_dir = get_data_dir()
        db_path = get_db_path()
        
        if not quiet:
            # CLI 模式下輸出路徑資訊（到 stderr 避免干擾 MCP）
            _log(f"🏠 TIMELESS_HOME: {home}")
            _log(f"📁 資料目錄: {data_dir}")
            _log(f"💾 資料庫: {db_path}")
            _log("")
        
        # 初始化索引管理器（單一 SQLite 索引）
        self._index_manager = IndexManager(str(db_path))
        
        # 初始化記憶管理器（不再需要 markdown_index）
        self._memory_manager = MemoryManager(
            str(data_dir),
            index_manager=self._index_manager
        )
        
        # 初始化檢索引擎
        self._retrieval_engine = RetrievalEngine(
            str(data_dir),
            self._index_manager,
            self._memory_manager
        )
        
        # 初始化實體管理器
        self._entity_manager = EntityManager(self._index_manager.conn)
        
        # 初始化關係管理器
        self._relation_manager = RelationManager(self._index_manager.conn)
        
        # 初始化實體解析器
        self._entity_resolver = EntityResolver(
            self._index_manager.conn,
            self._entity_manager
        )
    
    def reset(self):
        """重置所有管理器（用於清空資料後重新初始化）"""
        self._memory_manager = None
        self._index_manager = None
        self._retrieval_engine = None
        self._entity_manager = None
        self._relation_manager = None
        self._entity_resolver = None
    
    @property
    def memory_manager(self) -> MemoryManager:
        """取得記憶管理器"""
        if self._memory_manager is None:
            self._initialize_managers(quiet=True)
        return self._memory_manager
    
    @property
    def index_manager(self) -> IndexManager:
        """取得索引管理器"""
        if self._index_manager is None:
            self._initialize_managers(quiet=True)
        return self._index_manager
    
    @property
    def retrieval_engine(self) -> RetrievalEngine:
        """取得檢索引擎"""
        if self._retrieval_engine is None:
            self._initialize_managers(quiet=True)
        return self._retrieval_engine
    
    @property
    def entity_manager(self) -> EntityManager:
        """取得實體管理器"""
        if self._entity_manager is None:
            self._initialize_managers(quiet=True)
        return self._entity_manager
    
    @property
    def relation_manager(self) -> RelationManager:
        """取得關係管理器"""
        if self._relation_manager is None:
            self._initialize_managers(quiet=True)
        return self._relation_manager
    
    @property
    def entity_resolver(self) -> EntityResolver:
        """取得實體解析器"""
        if self._entity_resolver is None:
            self._initialize_managers(quiet=True)
        return self._entity_resolver


# 全域單例實例
_factory = ManagerFactory()


def get_manager_factory() -> ManagerFactory:
    """取得管理器工廠單例"""
    return _factory


def get_managers(quiet: bool = False):
    """
    便利函式：取得所有管理器
    
    Args:
        quiet: 是否靜默模式
    
    Returns:
        (memory_manager, index_manager, retrieval_engine,
         entity_manager, relation_manager, entity_resolver)
    """
    return _factory.get_managers(quiet=quiet)
