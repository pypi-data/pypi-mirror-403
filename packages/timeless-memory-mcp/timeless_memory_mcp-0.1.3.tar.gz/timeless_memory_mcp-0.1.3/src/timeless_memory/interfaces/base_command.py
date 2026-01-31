"""
命令基類 - 統一命令抽象
所有命令都繼承此基類，確保 MCP/CLI 行為一致
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class CommandResult:
    """
    命令執行結果
    統一的回傳格式，可被不同的 Formatter 處理
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = {"success": self.success}
        
        if self.data is not None:
            result.update(self.data)
        
        if self.message:
            result["message"] = self.message
        
        if self.error:
            result["error"] = self.error
        
        if self.metadata:
            result["_metadata"] = self.metadata
        
        return result
    
    @classmethod
    def success_result(
        cls,
        message: str = None,
        data: Dict[str, Any] = None,
        **metadata
    ) -> 'CommandResult':
        """建立成功結果"""
        return cls(
            success=True,
            message=message,
            data=data,
            metadata=metadata
        )
    
    @classmethod
    def error_result(
        cls,
        error: str,
        data: Dict[str, Any] = None,
        **metadata
    ) -> 'CommandResult':
        """建立錯誤結果"""
        return cls(
            success=False,
            error=error,
            data=data,
            metadata=metadata
        )


class BaseCommand(ABC):
    """
    命令基類
    所有命令都應繼承此類並實作 execute() 方法
    """
    
    # 命令元資訊
    name: str = ""
    description: str = ""
    category: str = ""  # memory, entity, relation, source, index, etc.
    
    def __init__(self):
        """初始化命令"""
        if not self.name:
            self.name = self.__class__.__name__.lower().replace("command", "")
    
    @abstractmethod
    def execute(self, **kwargs) -> CommandResult:
        """
        執行命令
        
        Args:
            **kwargs: 命令參數
        
        Returns:
            CommandResult: 統一的執行結果
        """
        pass
    
    def validate_params(self, **kwargs) -> Optional[str]:
        """
        驗證參數
        
        Args:
            **kwargs: 命令參數
        
        Returns:
            錯誤訊息，或 None 表示驗證通過
        """
        return None
    
    def get_param_schema(self) -> Dict[str, Any]:
        """
        取得參數 schema（用於 MCP tool 定義）
        
        Returns:
            參數 schema 字典
        """
        return {}
    
    def get_cli_args(self) -> List[Dict[str, Any]]:
        """
        取得 CLI 參數定義
        
        Returns:
            參數定義列表，每個元素是 argparse 的參數設定
        """
        return []


class MemoryCommand(BaseCommand):
    """記憶管理命令基類"""
    category = "memory"


class EntityCommand(BaseCommand):
    """實體管理命令基類"""
    category = "entity"


class RelationCommand(BaseCommand):
    """關係管理命令基類"""
    category = "relation"


class IndexCommand(BaseCommand):
    """索引管理命令基類"""
    category = "index"


class ResolverCommand(BaseCommand):
    """實體解析命令基類"""
    category = "resolver"
