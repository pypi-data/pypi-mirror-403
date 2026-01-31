"""
Timeless Memory MCP Server（精簡版）
雙索引架構：Markdown（架構 A）+ SQLite FTS5（架構 B）

精簡設計：32 個工具 → 7 個統一工具
- memory: 記憶管理（6 actions）
- entity: 實體管理（9 actions）
- relation: 關係管理（4 actions）
- memory_entity: 記憶-實體連結（3 actions）
- resolver: 實體解析（4 actions）
- system: 系統管理（6 actions）
- chat: Google Chat 整合（6 actions）
"""
import sys
from typing import List, Optional, Dict, Any
from mcp.server.fastmcp import FastMCP


def _log(msg: str):
    """輸出到 stderr（避免干擾 MCP stdio 通訊）"""
    print(msg, file=sys.stderr)

from timeless_memory import get_home, get_data_dir, get_index_dir, get_db_path
from timeless_memory.core import get_managers
from timeless_memory.core.query_utils import (
    build_search_queries,
    build_search_filters
)
from timeless_memory.integrations import ChatManager

# 初始化 MCP Server
mcp = FastMCP("timeless-memory")


def _get_managers():
    """
    懶載入管理器（使用統一的 ManagerFactory）
    
    Returns:
        (memory_manager, index_manager, retrieval_engine,
         entity_manager, relation_manager, entity_resolver)
    """
    return get_managers(quiet=True)


# ChatManager 單例
_chat_manager = None

def _get_chat_manager() -> ChatManager:
    """懶載入 ChatManager"""
    global _chat_manager
    if _chat_manager is None:
        _chat_manager = ChatManager()
    return _chat_manager


# ===== 1. MEMORY 工具（合併 6 個） =====

@mcp.tool()
def memory(
    action: str,
    # create/update 參數
    content: str = None,
    speaker: str = "user",
    authority: int = 3,
    quality: int = 3,
    tags: List[str] = None,
    keywords: str = "",
    category: str = "情節記憶",
    context: str = "",
    # update/delete/get 參數
    memory_id: str = None,
    # search 參數
    query: str = None,
    authority_min: int = None,
    quality_min: int = None,
    date_after: str = None,
    date_before: str = None,
    limit: int = 20,
    index_mode: str = "both",
    expand_aliases: bool = True
) -> dict:
    """
    統一的記憶管理工具
    
    Actions:
        - create: 建立記憶（需要 content）
        - update: 更新記憶（需要 memory_id）
        - delete: 刪除記憶（需要 memory_id）
        - list: 列出記憶（可選 category, limit）
        - search: 搜尋記憶（需要 query）
        - browse: 瀏覽分類（需要 category）
    
    Args:
        action: 操作類型
        content: 記憶內容
        speaker: 來源 (user/ai/external)
        authority: 權重 1-10
        quality: 品質 1-5
        tags: 標籤列表
        keywords: 關鍵字
        category: 分類
        context: 情境說明
        memory_id: 記憶 ID
        query: 搜尋關鍵字
        authority_min: 最低權重
        quality_min: 最低品質
        date_after: 開始日期
        date_before: 結束日期
        limit: 結果數量
        index_mode: 索引模式 (both/sqlite/markdown)
        expand_aliases: 是否展開別名
    
    Returns:
        操作結果
    """
    memory_manager, index_manager, retrieval_engine, entity_manager, _, _ = _get_managers()
    
    if action == "create":
        if not content:
            return {"success": False, "error": "content 參數為必填"}
        
        metadata = {
            "speaker": speaker,
            "authority": authority,
            "quality": quality,
            "tags": tags or [],
            "keywords": keywords,
            "context": context
        }
        result = memory_manager.create_memory(content, metadata, category)
        return {"success": True, **result}
    
    elif action == "update":
        if not memory_id:
            return {"success": False, "error": "memory_id 參數為必填"}
        
        metadata = {}
        if authority: metadata['authority'] = authority
        if quality: metadata['quality'] = quality
        if tags: metadata['tags'] = tags
        if keywords: metadata['keywords'] = keywords
        
        success = memory_manager.update_memory(
            memory_id,
            content=content,
            metadata=metadata if metadata else None
        )
        return {
            "success": success,
            "message": "記憶已更新" if success else "找不到記憶"
        }
    
    elif action == "delete":
        if not memory_id:
            return {"success": False, "error": "memory_id 參數為必填"}
        
        success = memory_manager.delete_memory(memory_id)
        return {
            "success": success,
            "message": "記憶已刪除" if success else "找不到記憶"
        }
    
    elif action == "list":
        memories = memory_manager.list_memories(category=category, limit=limit)
        return {
            "success": True,
            "memories": memories,
            "total": len(memories)
        }
    
    elif action == "search":
        if not query:
            return {"success": False, "error": "query 參數為必填"}
        
        search_queries = build_search_queries(query, entity_manager, expand_aliases)
        filters = build_search_filters(
            speaker=speaker if speaker != "user" else None,
            authority_min=authority_min,
            quality_min=quality_min,
            tags=tags,
            date_after=date_after,
            date_before=date_before
        )
        
        # 簡化：只使用 SQLite 搜尋
        all_results = []
        seen_ids = set()
        for q in search_queries:
            results = retrieval_engine.search(query=q, filters=filters, limit=limit)
            for r in results:
                if r['id'] not in seen_ids:
                    seen_ids.add(r['id'])
                    all_results.append(r)
        
        return {
            "success": True,
            "results": all_results[:limit],
            "total": len(all_results),
            "query": query,
            "expanded_aliases": search_queries[1:] if len(search_queries) > 1 else None
        }
    
    elif action == "browse":
        if not category:
            return {"success": False, "error": "category 參數為必填"}
        
        memories = index_manager.browse_by_category(category, limit)
        return {
            "success": True,
            "category": category,
            "memories": memories,
            "total": len(memories)
        }
    
    else:
        return {
            "success": False,
            "error": f"未知的 action: {action}",
            "available_actions": ["create", "update", "delete", "list", "search", "browse"]
        }


# ===== 2. ENTITY 工具（合併 9 個） =====

@mcp.tool()
def entity(
    action: str,
    # create 參數
    entity_type: str = None,
    name: str = None,
    role: str = None,
    department: str = None,
    contact: str = None,
    aliases: List[str] = None,
    # get/update/delete/add_alias/resolve/search 參數
    entity_id: str = None,
    # update 參數
    properties: dict = None,
    # add_alias 參數
    alias: str = None,
    # merge 參數
    source_id: str = None,
    target_id: str = None,
    # search/resolve 參數
    query: str = None,
    # list 參數
    limit: int = 50,
    # batch_create 參數
    entities: List[dict] = None
) -> dict:
    """
    統一的實體管理工具
    
    Actions:
        - create: 建立實體（需要 entity_type, name）
        - batch_create: 批次建立實體（需要 entities 列表）
        - get: 取得實體（需要 entity_id）
        - list: 列出實體（可選 entity_type, limit）
        - update: 更新實體（需要 entity_id）
        - delete: 刪除實體（需要 entity_id）
        - add_alias: 新增別名（需要 entity_id, alias）
        - merge: 合併實體（需要 source_id, target_id）
        - resolve: 解析名稱（需要 name）
        - search: 搜尋實體（需要 query）
    
    ⚠️ 重要：建立 person 實體時，務必包含 chat_id！
    - chat_id 是 Google Chat 的 user_id（如 "10671516"）
    - 必須放在 properties.chat_id 或 aliases 中
    - 這樣才能將人物對應回原始聊天記錄
    
    person 實體建立範例：
    {
        "entity_type": "person",
        "name": "謝承緯",
        "aliases": ["hsieh", "chenwei", "10671516"],  # chat_id 加入別名
        "properties": {"chat_id": "10671516"}         # chat_id 也存入 properties
    }
    
    Args:
        action: 操作類型
        entity_type: 實體類型 (person/project/topic/place/event/organization)
        name: 實體名稱
        role: 角色
        department: 部門
        contact: 聯絡方式
        aliases: 別名列表（person 應包含 chat_id）
        entity_id: 實體 ID
        properties: 屬性字典（person 應包含 chat_id）
        alias: 單個別名
        source_id: 來源實體 ID
        target_id: 目標實體 ID
        query: 搜尋關鍵字
        limit: 結果數量
        entities: 批次建立的實體列表
    
    批次建立格式（person 必須包含 chat_id）:
        [{"entity_type": "person", "name": "張三", "aliases": ["10671516"], "properties": {"chat_id": "10671516"}}]
    
    Returns:
        操作結果
    """
    _, _, _, entity_manager, _, _ = _get_managers()
    
    if action == "create":
        if not entity_type or not name:
            return {"success": False, "error": "entity_type 和 name 參數為必填"}
        
        props = {}
        if role: props["role"] = role
        if department: props["department"] = department
        if contact: props["contact"] = contact
        
        return entity_manager.create(entity_type, name, props if props else None, aliases)
    
    elif action == "get":
        if not entity_id:
            return {"success": False, "error": "entity_id 參數為必填"}
        
        result = entity_manager.get(entity_id)
        if not result:
            return {"success": False, "message": f"實體不存在: {entity_id}"}
        return {"success": True, **result}
    
    elif action == "list":
        entities = entity_manager.list(entity_type, limit)
        return {
            "success": True,
            "entities": entities,
            "total": len(entities)
        }
    
    elif action == "update":
        if not entity_id:
            return {"success": False, "error": "entity_id 參數為必填"}
        
        return entity_manager.update(entity_id, name, properties)
    
    elif action == "delete":
        if not entity_id:
            return {"success": False, "error": "entity_id 參數為必填"}
        
        return entity_manager.delete(entity_id)
    
    elif action == "add_alias":
        if not entity_id or not alias:
            return {"success": False, "error": "entity_id 和 alias 參數為必填"}
        
        return entity_manager.add_alias(entity_id, alias)
    
    elif action == "merge":
        if not source_id or not target_id:
            return {"success": False, "error": "source_id 和 target_id 參數為必填"}
        
        return entity_manager.merge(source_id, target_id)
    
    elif action == "resolve":
        if not name:
            return {"success": False, "error": "name 參數為必填"}
        
        result = entity_manager.resolve(name)
        if not result:
            return {"success": True, "found": False, "name": name}
        return {"success": True, "found": True, **result}
    
    elif action == "search":
        if not query:
            return {"success": False, "error": "query 參數為必填"}
        
        results = entity_manager.search(query, entity_type)
        return {
            "success": True,
            "results": results,
            "total": len(results)
        }
    
    elif action == "batch_create":
        if not entities or not isinstance(entities, list):
            return {"success": False, "error": "entities 參數為必填，格式為實體列表"}
        
        created = []
        skipped = []
        errors = []
        
        for ent in entities:
            ent_type = ent.get("entity_type")
            ent_name = ent.get("name")
            ent_aliases = ent.get("aliases", [])
            ent_props = ent.get("properties", {})
            
            if not ent_type or not ent_name:
                errors.append({"entity": ent, "error": "缺少 entity_type 或 name"})
                continue
            
            # 檢查是否已存在
            existing = entity_manager.get(f"{ent_type}-{ent_name}")
            if existing:
                # 更新別名
                for a in ent_aliases:
                    if a not in existing.get("aliases", []):
                        entity_manager.add_alias(existing["id"], a)
                skipped.append({"name": ent_name, "id": existing["id"]})
            else:
                # 建立新實體
                try:
                    result = entity_manager.create(ent_type, ent_name, ent_props if ent_props else None, ent_aliases)
                    if result.get("success"):
                        created.append({"name": ent_name, "id": result.get("id")})
                    else:
                        errors.append({"entity": ent, "error": result.get("message", "建立失敗")})
                except Exception as e:
                    errors.append({"entity": ent, "error": str(e)})
        
        return {
            "success": True,
            "created": created,
            "skipped": skipped,
            "errors": errors,
            "summary": f"建立 {len(created)} 個，跳過 {len(skipped)} 個，失敗 {len(errors)} 個"
        }
    
    else:
        return {
            "success": False,
            "error": f"未知的 action: {action}",
            "available_actions": ["create", "batch_create", "get", "list", "update", "delete", "add_alias", "merge", "resolve", "search"]
        }


# ===== 3. RELATION 工具（合併 4 個） =====

@mcp.tool()
def relation(
    action: str,
    # create/delete/query 參數
    from_id: str = None,
    relation_type: str = None,
    to_id: str = None,
    # get_related 參數
    entity_id: str = None,
    # query 參數
    limit: int = 50,
    # batch_create 參數
    relations: List[dict] = None
) -> dict:
    """
    統一的關係管理工具
    
    Actions:
        - create: 建立關係（需要 from_id, relation_type, to_id）
        - batch_create: 批次建立關係（需要 relations 列表）
        - delete: 刪除關係（需要 from_id, relation_type, to_id）
        - query: 查詢關係（可選 from_id, relation_type, to_id）
        - get_related: 取得相關實體（需要 entity_id）
    
    Args:
        action: 操作類型
        from_id: 來源實體 ID
        relation_type: 關係類型
        to_id: 目標實體 ID
        entity_id: 實體 ID（用於 get_related）
        limit: 結果數量
        relations: 批次建立的關係列表，每個元素格式: {"from_id": "person-張三", "relation_type": "works_on", "to_id": "project-xxx"}
    
    Returns:
        操作結果
    """
    _, _, _, _, relation_manager, _ = _get_managers()
    
    if action == "create":
        if not from_id or not relation_type or not to_id:
            return {"success": False, "error": "from_id, relation_type, to_id 參數為必填"}
        
        return relation_manager.create(from_id, relation_type, to_id)
    
    elif action == "batch_create":
        if not relations or not isinstance(relations, list):
            return {"success": False, "error": "relations 參數為必填，格式為關係列表"}
        
        created = []
        skipped = []
        errors = []
        
        for rel in relations:
            rel_from = rel.get("from_id")
            rel_type = rel.get("relation_type")
            rel_to = rel.get("to_id")
            
            if not rel_from or not rel_type or not rel_to:
                errors.append({"relation": rel, "error": "缺少 from_id, relation_type 或 to_id"})
                continue
            
            # 檢查是否已存在
            existing = relation_manager.query(from_id=rel_from, to_id=rel_to, limit=100)
            already_exists = any(
                r.get("relation") == rel_type 
                for r in existing
            )
            
            if already_exists:
                skipped.append({"from": rel_from, "type": rel_type, "to": rel_to})
            else:
                try:
                    result = relation_manager.create(rel_from, rel_type, rel_to)
                    if result.get("success"):
                        created.append({"from": rel_from, "type": rel_type, "to": rel_to})
                    else:
                        errors.append({"relation": rel, "error": result.get("message", "建立失敗")})
                except Exception as e:
                    errors.append({"relation": rel, "error": str(e)})
        
        return {
            "success": True,
            "created": created,
            "skipped": skipped,
            "errors": errors,
            "summary": f"建立 {len(created)} 個，跳過 {len(skipped)} 個，失敗 {len(errors)} 個"
        }
    
    elif action == "delete":
        if not from_id or not relation_type or not to_id:
            return {"success": False, "error": "from_id, relation_type, to_id 參數為必填"}
        
        return relation_manager.delete_by_entities(from_id, relation_type, to_id)
    
    elif action == "query":
        relations_result = relation_manager.query(from_id, relation_type, to_id, limit)
        return {
            "success": True,
            "relations": relations_result,
            "total": len(relations_result)
        }
    
    elif action == "get_related":
        if not entity_id:
            return {"success": False, "error": "entity_id 參數為必填"}
        
        return relation_manager.get_related(entity_id, relation_type)
    
    else:
        return {
            "success": False,
            "error": f"未知的 action: {action}",
            "available_actions": ["create", "batch_create", "delete", "query", "get_related"]
        }


# ===== 4. MEMORY_ENTITY 工具（合併 3 個） =====

@mcp.tool()
def memory_entity(
    action: str,
    memory_id: str = None,
    entity_id: str = None,
    relation_type: str = "mentions",
    limit: int = 50
) -> dict:
    """
    統一的記憶-實體連結工具
    
    Actions:
        - link: 連結記憶與實體（需要 memory_id, entity_id）
        - get_entities: 取得記憶相關實體（需要 memory_id）
        - get_memories: 取得實體相關記憶（需要 entity_id）
    
    Args:
        action: 操作類型
        memory_id: 記憶 ID
        entity_id: 實體 ID
        relation_type: 關係類型（預設 mentions）
        limit: 結果數量
    
    Returns:
        操作結果
    """
    _, _, _, _, relation_manager, _ = _get_managers()
    
    if action == "link":
        if not memory_id or not entity_id:
            return {"success": False, "error": "memory_id 和 entity_id 參數為必填"}
        
        return relation_manager.link_memory(memory_id, entity_id, relation_type)
    
    elif action == "get_entities":
        if not memory_id:
            return {"success": False, "error": "memory_id 參數為必填"}
        
        entities = relation_manager.get_memory_entities(memory_id)
        return {
            "success": True,
            "entities": entities,
            "total": len(entities)
        }
    
    elif action == "get_memories":
        if not entity_id:
            return {"success": False, "error": "entity_id 參數為必填"}
        
        memories = relation_manager.get_entity_memories(entity_id, relation_type, limit)
        return {
            "success": True,
            "memories": memories,
            "total": len(memories)
        }
    
    else:
        return {
            "success": False,
            "error": f"未知的 action: {action}",
            "available_actions": ["link", "get_entities", "get_memories"]
        }


# ===== 5. RESOLVER 工具（合併 4 個） =====

@mcp.tool()
def resolver(
    action: str,
    # resolve 參數
    name: str = None,
    memory_id: str = None,
    context: str = None,
    # pending 參數
    limit: int = 50,
    # confirm 參數
    pending_id: int = None,
    entity_id: str = None,
    create_new: bool = False,
    new_entity_type: str = None,
    new_entity_name: str = None
) -> dict:
    """
    統一的實體解析工具
    
    Actions:
        - resolve: 解析名稱（需要 name）
        - pending: 取得待確認列表
        - confirm: 確認待確認項目（需要 pending_id）
        - reject: 拒絕待確認項目（需要 pending_id）
    
    Args:
        action: 操作類型
        name: 要解析的名稱
        memory_id: 來源記憶 ID
        context: 上下文
        limit: 結果數量
        pending_id: 待確認項目 ID
        entity_id: 選擇的實體 ID
        create_new: 是否建立新實體
        new_entity_type: 新實體類型
        new_entity_name: 新實體名稱
    
    Returns:
        操作結果
    """
    _, _, _, _, _, entity_resolver = _get_managers()
    
    if action == "resolve":
        if not name:
            return {"success": False, "error": "name 參數為必填"}
        
        return entity_resolver.auto_resolve(name, memory_id, context)
    
    elif action == "pending":
        pending = entity_resolver.get_pending(limit)
        return {
            "success": True,
            "pending": pending,
            "total": len(pending)
        }
    
    elif action == "confirm":
        if pending_id is None:
            return {"success": False, "error": "pending_id 參數為必填"}
        
        return entity_resolver.confirm(
            pending_id, entity_id, create_new, new_entity_type, new_entity_name
        )
    
    elif action == "reject":
        if pending_id is None:
            return {"success": False, "error": "pending_id 參數為必填"}
        
        return entity_resolver.reject(pending_id)
    
    else:
        return {
            "success": False,
            "error": f"未知的 action: {action}",
            "available_actions": ["resolve", "pending", "confirm", "reject"]
        }


# ===== 6. SYSTEM 工具（合併 6 個） =====

@mcp.tool()
def system(
    action: str,
    # init/clear 參數
    clear: bool = False
) -> dict:
    """
    統一的系統管理工具
    
    Actions:
        - stats: 取得統計資訊
        - tags: 列出所有標籤
        - categories: 列出所有分類
        - rebuild: 重建索引
        - init: 初始化資料庫
        - clear: 清空所有資料
    
    Args:
        action: 操作類型
        clear: 是否清空資料（用於 init）
    
    Returns:
        操作結果
    """
    memory_manager, index_manager, *_ = _get_managers()
    
    if action == "stats":
        stats = index_manager.get_stats()
        stats['home'] = str(get_home())
        stats['data_dir'] = str(get_data_dir())
        stats['index_dir'] = str(get_index_dir())
        stats['db_path'] = str(get_db_path())
        return {"success": True, **stats}
    
    elif action == "tags":
        result = index_manager.get_all_tags()
        result['index_file'] = str(get_index_dir() / "標籤索引.md")
        return {"success": True, **result}
    
    elif action == "categories":
        result = index_manager.get_categories()
        result['index_file'] = str(get_index_dir() / "分類索引.md")
        return {"success": True, **result}
    
    elif action == "rebuild":
        index_manager.rebuild(memory_manager)
        stats = index_manager.get_stats()
        
        # 取得知識圖譜統計
        _, _, _, entity_manager, relation_manager, _ = _get_managers()
        entity_count = len(entity_manager.list(limit=9999))
        relation_count = len(relation_manager.query(limit=9999))
        
        # 分析 Google Chat 資料（如果存在）
        chat_info = None
        try:
            chat_manager = _get_chat_manager()
            analyze_result = chat_manager.analyze(include_content=False)
            if analyze_result.get("success"):
                summary = analyze_result.get("summary", {})
                chat_info = {
                    "user_ids": summary.get("total_user_ids", 0),
                    "projects": summary.get("total_projects", 0),
                    "spaces": summary.get("total_spaces", 0),
                    "mentions": summary.get("total_mentions", 0)
                }
        except Exception:
            pass
        
        # 建立 TODO 提醒
        todos = []
        
        # 1. 知識圖譜 TODO
        if chat_info:
            unmapped_users = chat_info["user_ids"] - entity_count if entity_count < chat_info["user_ids"] else 0
            if unmapped_users > 0 or entity_count == 0:
                todos.append({
                    "task": "建立人物實體",
                    "description": f"分析 {chat_info['user_ids']} 個 User IDs，建立人物實體並設定 Chat ID 為別名",
                    "command": "chat(action='analyze') → entity(action='batch_create', entities=[...])"
                })
            
            if chat_info["projects"] > 0:
                todos.append({
                    "task": "建立專案實體",
                    "description": f"根據 {chat_info['projects']} 個專案建立實體",
                    "command": "entity(action='batch_create', entities=[{entity_type='project', ...}])"
                })
            
            if entity_count > 0:
                todos.append({
                    "task": "建立人物-專案關聯",
                    "description": "根據聊天室參與者建立 works_on 關聯",
                    "command": "relation(action='batch_create', relations=[...])"
                })
        
        # 2. 每月摘要 TODO
        data_dir = get_data_dir()
        google_chat_dir = data_dir / "google-chat"
        if google_chat_dir.exists():
            spaces = [d.name for d in google_chat_dir.iterdir() if d.is_dir()]
            if spaces:
                todos.append({
                    "task": "建立每月聊天室摘要",
                    "description": f"為 {len(spaces)} 個聊天室建立 monthly-summary-YYYY-MM.md",
                    "spaces": spaces[:10],  # 只顯示前 10 個
                    "format": "monthly-summary-{space_name}-YYYY-MM.md"
                })
        
        # 輸出 TODO 到 stderr（不干擾 MCP）
        _log("\n" + "=" * 60)
        _log("📋 索引重建後 TODO")
        _log("=" * 60)
        
        for i, todo in enumerate(todos, 1):
            _log(f"\n{i}. {todo['task']}")
            _log(f"   {todo['description']}")
            if 'command' in todo:
                _log(f"   指令: {todo['command']}")
            if 'spaces' in todo:
                _log(f"   聊天室: {', '.join(todo['spaces'][:5])}")
                if len(todo['spaces']) > 5:
                    _log(f"           ... 還有 {len(todo['spaces']) - 5} 個")
        
        _log("\n" + "=" * 60)
        
        return {
            "success": True,
            "message": f"索引重建完成，共 {stats['total_memories']} 筆記憶",
            "stats": stats,
            "knowledge_graph": {
                "entities": entity_count,
                "relations": relation_count
            },
            "chat_info": chat_info,
            "todos": todos
        }
    
    elif action == "init":
        import shutil
        from timeless_memory.core import get_manager_factory
        
        data_dir = get_data_dir()
        index_dir = get_index_dir()
        db_path = get_db_path()
        
        cleared = False
        if clear:
            if data_dir.exists(): shutil.rmtree(data_dir)
            if index_dir.exists(): shutil.rmtree(index_dir)
            if db_path.exists(): db_path.unlink()
            cleared = True
            factory = get_manager_factory()
            factory.reset()
        
        # 建立目錄結構
        dirs = [
            data_dir / "記憶核心" / "語義記憶" / "偏好學習",
            data_dir / "記憶核心" / "語義記憶" / "知識庫",
            data_dir / "記憶核心" / "情節記憶" / "專案經歷",
            data_dir / "記憶核心" / "情節記憶" / "產品策略",
            data_dir / "記憶核心" / "情節記憶" / "其他",
            data_dir / "記憶核心" / "程序記憶",
            index_dir,
            index_dir / "聊天室",  # 月度摘要目錄
            db_path.parent,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        
        _get_managers()  # 初始化索引
        
        return {
            "success": True,
            "cleared": cleared,
            "home": str(get_home()),
            "data_dir": str(data_dir),
            "index_dir": str(index_dir),
            "db_path": str(db_path)
        }
    
    elif action == "clear":
        import shutil
        from timeless_memory.core import get_manager_factory
        
        data_dir = get_data_dir()
        index_dir = get_index_dir()
        db_path = get_db_path()
        
        deleted = []
        if data_dir.exists():
            shutil.rmtree(data_dir)
            deleted.append(str(data_dir))
        if index_dir.exists():
            shutil.rmtree(index_dir)
            deleted.append(str(index_dir))
        if db_path.exists():
            db_path.unlink()
            deleted.append(str(db_path))
        
        factory = get_manager_factory()
        factory.reset()
        
        return {
            "success": True,
            "message": "所有資料已清空",
            "deleted": deleted
        }
    
    else:
        return {
            "success": False,
            "error": f"未知的 action: {action}",
            "available_actions": ["stats", "tags", "categories", "rebuild", "init", "clear"]
        }


# ===== 7. CHAT 工具（Google Chat 整合） =====

@mcp.tool()
def chat(
    action: str,
    # sync 參數
    space_id: str = None,
    skip_dm: bool = True,
    max_workers: int = 5,
    full: bool = False,
    overlap_days: int = 1,
    # list_spaces 參數
    refresh: bool = False,
    # convert 參數
    space_name: str = None,
    # analyze 參數
    include_content: bool = False,
    # get_user_context 參數
    user_id: str = None,
    limit: int = 10,
    # get_month_data / save_summary 參數
    year_month: str = None,
    summary_content: str = None
) -> str:
    """
    Google Chat 整合管理
    
    Actions:
        - sync: 完整同步流程（下載 + 轉換 + 增量索引）
        - download: 只下載原始資料
        - convert: 只轉換已下載的資料
        - list_spaces: 列出所有 Spaces
        - status: 查看同步狀態
        - init_auth: 初始化 OAuth 認證
        - analyze: 分析聊天資料，提取人物和專案資訊
        - get_user_context: 取得特定 user_id 的上下文資訊
        - extract_users: 提取 user_id → Google 顯示名稱（注意：這只是 Google 帳號暱稱，不是真名！）
        - list_mentions: 列出所有被 @ 提及的名字（中文名/英文名）
        - search_mention: 搜尋 @特定人 的上下文（用 space_name 參數傳入名字）
        - list_months: 列出所有聊天室/月份，顯示哪些缺少摘要
        - get_month_data: 取得指定聊天室的月度資料（供 agent 生成摘要）
        - save_summary: 儲存 agent 生成的月度摘要
    
    ⚠️⚠️⚠️ 極重要：這些工具只提供「原始資料」，不會自動判斷人物身份！
    
    Agent 必須手動分析以下資訊來建立正確的人物實體：
    
    1. extract_users 輸出的是 Google 顯示名稱（如 "test", "aui"），不是真名
    2. list_mentions 輸出的是被 @ 的名字（如 "謝承緯", "JC"）
    3. 兩者沒有直接對應關係，需要 Agent 手動判斷！
    
    正確的建立人物實體流程：
    
    步驟 1：取得資料
        chat(action="extract_users") → user_id 與 Google 暱稱
        chat(action="list_mentions") → 被 @ 提及的中文名/英文名
    
    步驟 2：手動分析對應關係（Agent 必須做！）
        對每個 user_id：
        - chat(action="get_user_context", user_id="xxx") → 看發言內容判斷身份
        - 從發言內容判斷：這是誰？是真人還是機器人/測試帳號？
        
        對每個被提及的名字：
        - chat(action="search_mention", space_name="謝承緯") → 看上下文
        - 從 mentioned_by 推斷誰常提到這個人
        - 判斷這個名字對應哪個 user_id
    
    步驟 3：建立對應表（Agent 手動完成）
        過濾掉機器人和測試帳號（如 test, server, api, agent 等）
        合併同一人的不同別名（如 JC = JC Wang = 10056046）
        
    步驟 4：建立實體（合併後的正確資料）
        entity(action="batch_create", entities=[
            {
                "entity_type": "person",
                "name": "謝承緯",  # 真實姓名
                "aliases": ["10671516", "hsieh", "chenwei", "承緯"],  # 所有別名 + chat_id
                "properties": {"chat_id": "10671516", "role": "工程師"}
            }
        ])
    
    常見錯誤：
    ❌ 直接把 extract_users 的 Google 暱稱當人名建立實體
    ❌ 沒有過濾 test, server, api 等非真人帳號
    ❌ 沒有合併同一人的不同別名（JC 和 10056046 是同一人）
    ❌ 沒有使用 get_user_context 確認 user_id 對應的真實身份
    
    Args:
        action: 操作類型
        space_id: 指定 Space ID（None 則處理全部）
        skip_dm: 是否跳過 DM（私人對話）
        max_workers: 並行下載/轉換的線程數
        full: 是否全量下載（False 則增量更新）
        overlap_days: 增量下載時回溯天數（預設 1 天）
        refresh: 是否強制重新從 API 取得 Space 列表
        space_name: 指定 Space 名稱
        include_content: 是否包含詳細對應資料（用於 analyze）
        user_id: 指定 User ID（用於 get_user_context）
        limit: 結果數量上限
        year_month: 年月 YYYY-MM（用於 get_month_data, save_summary）
        summary_content: 摘要內容（用於 save_summary）
    
    Returns:
        操作結果（JSON 字串）
    """
    import json
    
    try:
        chat_manager = _get_chat_manager()
        
        if action == "sync":
            result = chat_manager.sync(
                space_id=space_id,
                skip_dm=skip_dm,
                max_workers=max_workers,
                full=full,
                overlap_days=overlap_days
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif action == "download":
            result = chat_manager.download(
                space_id=space_id,
                skip_dm=skip_dm,
                incremental=not full,
                max_workers=max_workers,
                overlap_days=overlap_days
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif action == "convert":
            result = chat_manager.convert(space_name=space_name)
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif action == "list_spaces":
            spaces = chat_manager.list_spaces(refresh=refresh)
            return json.dumps({
                "success": True,
                "count": len(spaces),
                "spaces": spaces
            }, ensure_ascii=False, indent=2)
        
        elif action == "status":
            status = chat_manager.status()
            return json.dumps(status, ensure_ascii=False, indent=2)
        
        elif action == "init_auth":
            result = chat_manager.init_auth()
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif action == "analyze":
            result = chat_manager.analyze(include_content=include_content)
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif action == "get_user_context":
            if not user_id:
                return json.dumps({
                    "success": False,
                    "error": "user_id 參數為必填"
                }, ensure_ascii=False, indent=2)
            result = chat_manager.get_user_context(user_id=user_id, limit=limit)
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif action == "list_mentions":
            result = chat_manager.list_mentions(limit=limit)
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif action == "search_mention":
            if not space_name:  # 重用 space_name 參數作為 name
                return json.dumps({
                    "success": False,
                    "error": "請用 space_name 參數提供要搜尋的名字"
                }, ensure_ascii=False, indent=2)
            result = chat_manager.search_mention(name=space_name, limit=limit)
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif action == "list_months":
            result = chat_manager.list_months()
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif action == "get_month_data":
            if not space_name or not year_month:
                return json.dumps({
                    "success": False,
                    "error": "space_name 和 year_month 參數為必填"
                }, ensure_ascii=False, indent=2)
            result = chat_manager.get_month_data(space_name=space_name, year_month=year_month)
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif action == "save_summary":
            if not space_name or not year_month or not summary_content:
                return json.dumps({
                    "success": False,
                    "error": "space_name, year_month, summary_content 參數為必填"
                }, ensure_ascii=False, indent=2)
            result = chat_manager.save_summary(
                space_name=space_name,
                year_month=year_month,
                summary_content=summary_content
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif action == "extract_users":
            result = chat_manager.extract_users_for_entities()
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        else:
            return json.dumps({
                "success": False,
                "error": f"未知的 action: {action}",
                "available_actions": ["sync", "download", "convert", "list_spaces", "status", "init_auth", "analyze", "get_user_context", "list_months", "get_month_data", "save_summary", "extract_users"]
            }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


def main():
    """MCP Server 入口點"""
    mcp.run()


if __name__ == "__main__":
    main()
