"""
查詢工具 - 統一查詢預處理邏輯
包含別名展開、查詢解析等功能
"""
from typing import List, Tuple, Optional

from .entity_manager import EntityManager


def expand_entity_aliases(
    query: str,
    entity_manager: EntityManager
) -> Tuple[str, List[str]]:
    """
    展開查詢中的實體別名
    
    當查詢以 @ 開頭時，嘗試解析為實體並展開其所有別名
    例如：@謝承緯 → 展開為 ["承緯", "CW", "陳小明"] 等別名
    
    Args:
        query: 搜尋關鍵字（可能以 @ 開頭）
        entity_manager: 實體管理器
    
    Returns:
        (主名稱, 別名列表)
        - 如果不是 @ 查詢，返回 (query, [])
        - 如果找到實體，返回 (實體名稱, [別名1, 別名2, ...])
        - 如果找不到實體，返回 (去掉@的名稱, [])
    
    Examples:
        >>> expand_entity_aliases("@謝承緯", entity_manager)
        ("謝承緯", ["承緯", "CW", "謝先生"])
        
        >>> expand_entity_aliases("普通查詢", entity_manager)
        ("普通查詢", [])
    """
    if not query.startswith("@"):
        return query, []
    
    # 移除 @ 前綴
    entity_name = query[1:].strip()
    
    # 嘗試不同的實體類型
    entity_types = ["person", "project", "topic", "place", "event", "organization"]
    
    for entity_type in entity_types:
        entity_id = f"{entity_type}-{entity_name}"
        entity = entity_manager.get(entity_id)
        
        if entity:
            # 提取別名字串列表
            alias_dicts = entity.get("aliases", [])
            aliases = []
            
            for item in alias_dicts:
                if isinstance(item, dict) and "alias" in item:
                    aliases.append(item["alias"])
                elif isinstance(item, str):
                    aliases.append(item)
            
            if aliases:
                return entity_name, aliases
    
    # 找不到實體，返回原始名稱（去掉 @）
    return entity_name, []


def build_search_queries(
    query: str,
    entity_manager: EntityManager,
    expand_aliases: bool = True,
    max_aliases: int = 5
) -> List[str]:
    """
    建立搜尋查詢列表（包含別名展開）
    
    Args:
        query: 原始查詢
        entity_manager: 實體管理器
        expand_aliases: 是否展開別名
        max_aliases: 最多使用幾個別名
    
    Returns:
        查詢列表 [主查詢, 別名1, 別名2, ...]
    
    Examples:
        >>> build_search_queries("@謝承緯", entity_manager)
        ["謝承緯", "承緯", "CW", "謝先生"]
        
        >>> build_search_queries("普通查詢", entity_manager)
        ["普通查詢"]
    """
    if not expand_aliases or not query.startswith("@"):
        return [query]
    
    main_name, aliases = expand_entity_aliases(query, entity_manager)
    
    # 建立查詢列表：主名稱 + 前 N 個別名
    queries = [main_name]
    if aliases:
        queries.extend(aliases[:max_aliases])
    
    return queries


def parse_date_range(
    date_after: Optional[str] = None,
    date_before: Optional[str] = None
) -> Optional[Tuple[str, str]]:
    """
    解析日期範圍
    
    Args:
        date_after: 開始日期（ISO 格式或 YYYY-MM-DD）
        date_before: 結束日期（ISO 格式或 YYYY-MM-DD）
    
    Returns:
        (start_date, end_date) 或 None
        
    Examples:
        >>> parse_date_range("2026-01-20", "2026-01-27")
        ("2026-01-20", "2026-01-27")
        
        >>> parse_date_range("2026-01-20T00:00:00", None)
        ("2026-01-20T00:00:00", "2099-12-31")
        
        >>> parse_date_range(None, None)
        None
    """
    if not date_after and not date_before:
        return None
    
    start = date_after or "1970-01-01"
    end = date_before or "2099-12-31"
    
    return (start, end)


def build_search_filters(
    speaker: Optional[str] = None,
    authority_min: Optional[int] = None,
    quality_min: Optional[int] = None,
    tags: Optional[List[str]] = None,
    date_after: Optional[str] = None,
    date_before: Optional[str] = None,
    category: Optional[str] = None
) -> dict:
    """
    建立搜尋過濾條件
    
    Args:
        speaker: 來源過濾（user/ai/external）
        authority_min: 最低權重
        quality_min: 最低品質
        tags: 標籤列表
        date_after: 開始日期
        date_before: 結束日期
        category: 分類
    
    Returns:
        過濾條件字典
        
    Examples:
        >>> build_search_filters(speaker="user", authority_min=5)
        {"speaker": "user", "authority": {"gte": 5}}
        
        >>> build_search_filters(date_after="2026-01-20")
        {"date_range": ("2026-01-20", "2099-12-31")}
    """
    filters = {}
    
    if speaker:
        filters['speaker'] = speaker
    
    if authority_min is not None:
        filters['authority'] = {'gte': authority_min}
    
    if quality_min is not None:
        filters['quality'] = {'gte': quality_min}
    
    if tags:
        filters['tags'] = tags
    
    # 處理日期範圍
    date_range = parse_date_range(date_after, date_before)
    if date_range:
        filters['date_range'] = date_range
    
    if category:
        filters['category'] = category
    
    return filters if filters else None


def normalize_query(query: str) -> str:
    """
    正規化查詢字串
    
    Args:
        query: 原始查詢
    
    Returns:
        正規化後的查詢
        
    Examples:
        >>> normalize_query("  hello   world  ")
        "hello world"
        
        >>> normalize_query("UPPERCASE")
        "UPPERCASE"
    """
    # 移除多餘空白
    normalized = " ".join(query.split())
    return normalized


def split_tags(tags_str: str, delimiter: str = ",") -> List[str]:
    """
    分割標籤字串
    
    Args:
        tags_str: 標籤字串（逗號分隔）
        delimiter: 分隔符
    
    Returns:
        標籤列表
        
    Examples:
        >>> split_tags("tag1,tag2,tag3")
        ["tag1", "tag2", "tag3"]
        
        >>> split_tags("tag1, tag2 , tag3 ")
        ["tag1", "tag2", "tag3"]
    """
    if not tags_str:
        return []
    
    tags = [tag.strip() for tag in tags_str.split(delimiter)]
    return [tag for tag in tags if tag]  # 移除空字串
