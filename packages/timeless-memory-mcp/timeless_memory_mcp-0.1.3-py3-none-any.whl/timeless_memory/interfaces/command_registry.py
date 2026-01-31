"""
命令註冊器 - 自動註冊命令到 MCP/CLI
提供統一的命令管理和路由
"""
from typing import Dict, Type, Optional, List, Any
from .base_command import BaseCommand, CommandResult


class CommandRegistry:
    """
    命令註冊器
    管理所有可用的命令，提供統一的註冊和查找介面
    """
    
    _instance: Optional['CommandRegistry'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._commands: Dict[str, Type[BaseCommand]] = {}
        self._instances: Dict[str, BaseCommand] = {}
        self._initialized = True
    
    def register(
        self,
        command_class: Type[BaseCommand],
        name: Optional[str] = None
    ) -> None:
        """
        註冊命令
        
        Args:
            command_class: 命令類別
            name: 命令名稱（可選，預設使用類別名稱）
        """
        if name is None:
            # 從類別名稱推導命令名稱
            # CreateMemoryCommand -> create_memory
            class_name = command_class.__name__
            if class_name.endswith("Command"):
                class_name = class_name[:-7]  # 移除 "Command" 後綴
            
            # 駝峰式轉蛇形
            name = self._camel_to_snake(class_name)
        
        self._commands[name] = command_class
    
    def get_command(self, name: str) -> Optional[BaseCommand]:
        """
        取得命令實例
        
        Args:
            name: 命令名稱
        
        Returns:
            命令實例，或 None
        """
        if name not in self._commands:
            return None
        
        # 懶載入命令實例
        if name not in self._instances:
            self._instances[name] = self._commands[name]()
        
        return self._instances[name]
    
    def execute(self, name: str, **kwargs) -> CommandResult:
        """
        執行命令
        
        Args:
            name: 命令名稱
            **kwargs: 命令參數
        
        Returns:
            CommandResult: 執行結果
        """
        command = self.get_command(name)
        
        if command is None:
            return CommandResult.error_result(
                error=f"未知命令: {name}"
            )
        
        # 參數驗證
        validation_error = command.validate_params(**kwargs)
        if validation_error:
            return CommandResult.error_result(
                error=f"參數錯誤: {validation_error}"
            )
        
        # 執行命令
        try:
            return command.execute(**kwargs)
        except Exception as e:
            return CommandResult.error_result(
                error=f"命令執行失敗: {str(e)}"
            )
    
    def list_commands(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出所有命令
        
        Args:
            category: 分類過濾（可選）
        
        Returns:
            命令資訊列表
        """
        commands = []
        
        for name, command_class in self._commands.items():
            instance = self.get_command(name)
            
            # 分類過濾
            if category and instance.category != category:
                continue
            
            commands.append({
                "name": name,
                "description": instance.description,
                "category": instance.category,
            })
        
        return commands
    
    def get_mcp_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        取得所有命令的 MCP tool 定義
        
        Returns:
            {tool_name: tool_definition}
        """
        tools = {}
        
        for name in self._commands:
            command = self.get_command(name)
            tools[name] = {
                "description": command.description,
                "parameters": command.get_param_schema()
            }
        
        return tools
    
    def get_cli_commands(self) -> Dict[str, Dict[str, Any]]:
        """
        取得所有命令的 CLI 定義
        
        Returns:
            {command_name: cli_definition}
        """
        commands = {}
        
        for name in self._commands:
            command = self.get_command(name)
            commands[name] = {
                "description": command.description,
                "args": command.get_cli_args(),
                "category": command.category
            }
        
        return commands
    
    @staticmethod
    def _camel_to_snake(name: str) -> str:
        """
        駝峰式轉蛇形
        
        Examples:
            CreateMemory -> create_memory
            EntityCreate -> entity_create
        """
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append('_')
            result.append(char.lower())
        return ''.join(result)


# 全域單例
_registry = CommandRegistry()


def get_command_registry() -> CommandRegistry:
    """取得命令註冊器單例"""
    return _registry


def register_command(
    command_class: Type[BaseCommand],
    name: Optional[str] = None
):
    """
    便利函式：註冊命令
    可用作裝飾器
    
    Examples:
        @register_command
        class CreateMemoryCommand(MemoryCommand):
            ...
        
        @register_command(name="custom_name")
        class MyCommand(BaseCommand):
            ...
    """
    if isinstance(command_class, type):
        # 直接呼叫：register_command(MyCommand)
        _registry.register(command_class, name)
        return command_class
    else:
        # 作為裝飾器：@register_command(name="...")
        def decorator(cls):
            _registry.register(cls, command_class)  # command_class 實際是 name
            return cls
        return decorator
