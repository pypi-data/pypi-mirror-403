"""
輸出格式化器 - 統一輸出格式
為不同介面（MCP/CLI）提供適當的輸出格式
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
import json

from .base_command import CommandResult


class Formatter(ABC):
    """格式化器基類"""
    
    @abstractmethod
    def format(self, result: CommandResult) -> Any:
        """
        格式化輸出
        
        Args:
            result: 命令執行結果
        
        Returns:
            格式化後的輸出
        """
        pass


class JsonFormatter(Formatter):
    """
    JSON 格式化器
    用於 MCP Server 輸出
    """
    
    def __init__(self, indent: int = None):
        """
        初始化
        
        Args:
            indent: JSON 縮排層級（None 為緊湊格式）
        """
        self.indent = indent
    
    def format(self, result: CommandResult) -> Dict[str, Any]:
        """
        格式化為 JSON 字典
        
        Args:
            result: 命令執行結果
        
        Returns:
            字典格式的結果
        """
        return result.to_dict()
    
    def format_string(self, result: CommandResult) -> str:
        """
        格式化為 JSON 字串
        
        Args:
            result: 命令執行結果
        
        Returns:
            JSON 字串
        """
        return json.dumps(
            self.format(result),
            ensure_ascii=False,
            indent=self.indent
        )


class ConsoleFormatter(Formatter):
    """
    控制台格式化器
    用於 CLI 輸出，提供人類友善的格式
    """
    
    def __init__(
        self,
        use_emoji: bool = True,
        use_color: bool = False
    ):
        """
        初始化
        
        Args:
            use_emoji: 是否使用表情符號
            use_color: 是否使用顏色（ANSI）
        """
        self.use_emoji = use_emoji
        self.use_color = use_color
    
    def format(self, result: CommandResult) -> str:
        """
        格式化為控制台輸出
        
        Args:
            result: 命令執行結果
        
        Returns:
            格式化的字串
        """
        lines = []
        
        # 狀態圖示
        if result.success:
            prefix = "✅" if self.use_emoji else "[OK]"
        else:
            prefix = "❌" if self.use_emoji else "[ERROR]"
        
        # 主要訊息
        if result.message:
            lines.append(f"{prefix} {result.message}")
        elif result.error:
            lines.append(f"{prefix} {result.error}")
        
        # 資料輸出
        if result.data:
            lines.append("")
            lines.extend(self._format_data(result.data))
        
        return "\n".join(lines)
    
    def _format_data(self, data: Dict[str, Any], indent: int = 0) -> list:
        """
        格式化資料字典
        
        Args:
            data: 資料字典
            indent: 縮排層級
        
        Returns:
            格式化的行列表
        """
        lines = []
        prefix = "  " * indent
        
        for key, value in data.items():
            # 跳過內部元資料
            if key.startswith("_"):
                continue
            
            # 格式化 key
            display_key = self._format_key(key)
            
            if isinstance(value, dict):
                lines.append(f"{prefix}{display_key}:")
                lines.extend(self._format_data(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{display_key}:")
                lines.extend(self._format_list(value, indent + 1))
            else:
                lines.append(f"{prefix}{display_key}: {value}")
        
        return lines
    
    def _format_list(self, items: list, indent: int = 0) -> list:
        """
        格式化列表
        
        Args:
            items: 列表項目
            indent: 縮排層級
        
        Returns:
            格式化的行列表
        """
        lines = []
        prefix = "  " * indent
        
        for item in items:
            if isinstance(item, dict):
                # 字典項目
                for key, value in item.items():
                    if key.startswith("_"):
                        continue
                    display_key = self._format_key(key)
                    lines.append(f"{prefix}- {display_key}: {value}")
            else:
                # 簡單項目
                lines.append(f"{prefix}- {item}")
        
        return lines
    
    def _format_key(self, key: str) -> str:
        """
        格式化 key 名稱
        
        Examples:
            memory_id -> Memory ID
            entity_type -> Entity Type
            total -> Total
        """
        # 移除底線並首字母大寫
        words = key.split('_')
        return ' '.join(word.capitalize() for word in words)
    
    def format_table(
        self,
        headers: list,
        rows: list,
        max_width: int = 80
    ) -> str:
        """
        格式化為表格
        
        Args:
            headers: 表頭列表
            rows: 資料行列表
            max_width: 最大寬度
        
        Returns:
            格式化的表格字串
        """
        if not rows:
            return "（無資料）"
        
        # 計算每列的最大寬度
        col_widths = []
        for i, header in enumerate(headers):
            max_len = len(str(header))
            for row in rows:
                if i < len(row):
                    max_len = max(max_len, len(str(row[i])))
            col_widths.append(min(max_len + 2, max_width // len(headers)))
        
        # 建立分隔線
        separator = "+" + "+".join("-" * w for w in col_widths) + "+"
        
        # 格式化表頭
        header_line = "|" + "|".join(
            str(h).ljust(w) for h, w in zip(headers, col_widths)
        ) + "|"
        
        # 格式化資料行
        data_lines = []
        for row in rows:
            line = "|" + "|".join(
                str(row[i] if i < len(row) else "").ljust(col_widths[i])
                for i in range(len(headers))
            ) + "|"
            data_lines.append(line)
        
        # 組合表格
        table = [
            separator,
            header_line,
            separator,
            *data_lines,
            separator
        ]
        
        return "\n".join(table)


class CompactFormatter(ConsoleFormatter):
    """
    緊湊格式化器
    用於簡潔輸出，適合腳本使用
    """
    
    def __init__(self):
        super().__init__(use_emoji=False, use_color=False)
    
    def format(self, result: CommandResult) -> str:
        """
        格式化為緊湊輸出
        
        Args:
            result: 命令執行結果
        
        Returns:
            單行或簡潔的輸出
        """
        if result.success:
            if result.message:
                return result.message
            elif result.data:
                # 只輸出關鍵資料
                if "id" in result.data:
                    return result.data["id"]
                elif "total" in result.data:
                    return str(result.data["total"])
                else:
                    return "OK"
            else:
                return "OK"
        else:
            return f"ERROR: {result.error}"


def get_formatter(format_type: str = "json") -> Formatter:
    """
    取得格式化器
    
    Args:
        format_type: 格式類型 - json/console/compact
    
    Returns:
        對應的格式化器
    """
    formatters = {
        "json": JsonFormatter(),
        "console": ConsoleFormatter(),
        "compact": CompactFormatter(),
    }
    
    return formatters.get(format_type, JsonFormatter())
