"""
命令實作集合
統一實作所有 MCP/CLI 命令
"""
from typing import List, Optional, Dict, Any

from .base_command import (
    CommandResult,
    MemoryCommand,
    EntityCommand,
    RelationCommand,
    SourceCommand,
    IndexCommand,
    ReminderCommand,
    ResolverCommand
)
from .command_registry import register_command
from ..core import get_managers
from ..core.query_utils import (
    build_search_queries,
    build_search_filters,
    split_tags
)


# ===== 記憶管理命令 =====

@register_command
class CreateMemoryCommand(MemoryCommand):
    """建立新記憶"""
    
    name = "create_memory"
    description = "建立新記憶（同時更新雙索引）"
    
    def execute(
        self,
        content: str,
        speaker: str = "user",
        authority: int = 3,
        quality: int = 3,
        tags: List[str] = None,
        keywords: str = "",
        category: str = "情節記憶",
        context: str = ""
    ) -> CommandResult:
        memory_manager, *_ = get_managers(quiet=True)
        
        metadata = {
            "speaker": speaker,
            "authority": authority,
            "quality": quality,
            "tags": tags or [],
            "keywords": keywords,
            "context": context
        }
        
        result = memory_manager.create_memory(content, metadata, category)
        
        return CommandResult.success_result(
            message=f"記憶已建立: {result['id']}",
            data=result
        )


@register_command
class UpdateMemoryCommand(MemoryCommand):
    """更新記憶"""
    
    name = "update_memory"
    description = "更新記憶（同時更新雙索引）"
    
    def execute(
        self,
        memory_id: str,
        content: str = None,
        authority: int = None,
        quality: int = None,
        tags: List[str] = None,
        keywords: str = None
    ) -> CommandResult:
        memory_manager, *_ = get_managers(quiet=True)
        
        metadata = {}
        if authority is not None:
            metadata['authority'] = authority
        if quality is not None:
            metadata['quality'] = quality
        if tags is not None:
            metadata['tags'] = tags
        if keywords is not None:
            metadata['keywords'] = keywords
        
        success = memory_manager.update_memory(
            memory_id,
            content=content,
            metadata=metadata if metadata else None
        )
        
        if success:
            return CommandResult.success_result(
                message="記憶已更新",
                data={"memory_id": memory_id}
            )
        else:
            return CommandResult.error_result(
                error=f"找不到記憶: {memory_id}"
            )


@register_command
class DeleteMemoryCommand(MemoryCommand):
    """刪除記憶"""
    
    name = "delete_memory"
    description = "刪除記憶（同時從雙索引移除）"
    
    def execute(self, memory_id: str) -> CommandResult:
        memory_manager, *_ = get_managers(quiet=True)
        success = memory_manager.delete_memory(memory_id)
        
        if success:
            return CommandResult.success_result(
                message="記憶已刪除",
                data={"memory_id": memory_id}
            )
        else:
            return CommandResult.error_result(
                error=f"找不到記憶: {memory_id}"
            )


@register_command
class ListMemoriesCommand(MemoryCommand):
    """列出記憶"""
    
    name = "list_memories"
    description = "列出記憶"
    
    def execute(
        self,
        category: str = None,
        limit: int = 20
    ) -> CommandResult:
        memory_manager, *_ = get_managers(quiet=True)
        memories = memory_manager.list_memories(category=category, limit=limit)
        
        return CommandResult.success_result(
            message=f"找到 {len(memories)} 筆記憶",
            data={
                "memories": memories,
                "total": len(memories)
            }
        )


@register_command
class SearchMemoriesCommand(MemoryCommand):
    """搜尋記憶"""
    
    name = "search_memories"
    description = "搜尋記憶（支援別名展開）"
    
    def execute(
        self,
        query: str,
        speaker: str = None,
        authority_min: int = None,
        quality_min: int = None,
        tags: List[str] = None,
        date_after: str = None,
        date_before: str = None,
        limit: int = 20,
        index_mode: str = "both",
        expand_aliases: bool = True
    ) -> CommandResult:
        managers = get_managers(quiet=True)
        _, index_manager, markdown_index, retrieval_engine, _, entity_manager, _, _ = managers
        
        # 建立搜尋查詢（含別名展開）
        search_queries = build_search_queries(
            query, entity_manager, expand_aliases
        )
        
        # 建立過濾條件
        filters = build_search_filters(
            speaker=speaker,
            authority_min=authority_min,
            quality_min=quality_min,
            tags=tags,
            date_after=date_after,
            date_before=date_before
        )
        
        # 執行搜尋
        if index_mode == "markdown":
            results = markdown_index.search(search_queries[0])
            return CommandResult.success_result(
                message=f"找到 {len(results)} 筆結果（Markdown 索引）",
                data={
                    "results": results[:limit],
                    "total": len(results),
                    "index_mode": "markdown"
                }
            )
        
        # SQLite 或雙索引
        all_results = []
        seen_ids = set()
        
        for q in search_queries:
            results = retrieval_engine.search(
                query=q,
                filters=filters,
                limit=limit
            )
            for r in results:
                if r['id'] not in seen_ids:
                    seen_ids.add(r['id'])
                    all_results.append(r)
        
        return CommandResult.success_result(
            message=f"找到 {len(all_results)} 筆結果",
            data={
                "results": all_results[:limit],
                "total": len(all_results),
                "index_mode": index_mode,
                "expanded_aliases": search_queries[1:] if len(search_queries) > 1 else None
            }
        )


# ===== 實體管理命令 =====

@register_command
class EntityUpdateCommand(EntityCommand):
    """更新實體"""
    
    name = "entity_update"
    description = "更新實體資訊"
    
    def execute(
        self,
        entity_id: str,
        name: str = None,
        properties: dict = None
    ) -> CommandResult:
        _, _, _, _, _, entity_manager, _, _ = get_managers(quiet=True)
        result = entity_manager.update(entity_id, name, properties)
        
        if result.get("success"):
            return CommandResult.success_result(
                message=f"實體已更新: {entity_id}",
                data=result
            )
        else:
            return CommandResult.error_result(
                error=result.get("message", "更新失敗")
            )


@register_command
class EntityResolveCommand(EntityCommand):
    """解析實體名稱"""
    
    name = "entity_resolve"
    description = "根據名稱解析實體"
    
    def execute(self, name: str) -> CommandResult:
        _, _, _, _, _, entity_manager, _, _ = get_managers(quiet=True)
        result = entity_manager.resolve(name)
        
        if result:
            return CommandResult.success_result(
                message=f"找到實體: {result['name']}",
                data={**result, "found": True}
            )
        else:
            return CommandResult.success_result(
                message=f"找不到實體: {name}",
                data={"found": False, "name": name}
            )


@register_command
class EntitySearchCommand(EntityCommand):
    """搜尋實體"""
    
    name = "entity_search"
    description = "搜尋實體（模糊匹配）"
    
    def execute(
        self,
        query: str,
        entity_type: str = None
    ) -> CommandResult:
        _, _, _, _, _, entity_manager, _, _ = get_managers(quiet=True)
        results = entity_manager.search(query, entity_type)
        
        return CommandResult.success_result(
            message=f"找到 {len(results)} 個實體",
            data={
                "results": results,
                "total": len(results)
            }
        )


# ===== 關係管理命令 =====

@register_command
class RelationGetRelatedCommand(RelationCommand):
    """取得相關實體"""
    
    name = "relation_get_related"
    description = "取得實體的所有相關實體"
    
    def execute(
        self,
        entity_id: str,
        relation: str = None
    ) -> CommandResult:
        _, _, _, _, _, _, relation_manager, _ = get_managers(quiet=True)
        result = relation_manager.get_related(entity_id, relation)
        
        return CommandResult.success_result(
            message=f"找到相關實體",
            data=result
        )


@register_command
class MemoryLinkEntityCommand(MemoryCommand):
    """連結記憶與實體"""
    
    name = "memory_link_entity"
    description = "將記憶與實體關聯"
    
    def execute(
        self,
        memory_id: str,
        entity_id: str,
        relation: str = "mentions"
    ) -> CommandResult:
        _, _, _, _, _, _, relation_manager, _ = get_managers(quiet=True)
        result = relation_manager.link_memory(memory_id, entity_id, relation)
        
        if result.get("success"):
            return CommandResult.success_result(
                message="已連結記憶與實體",
                data=result
            )
        else:
            return CommandResult.error_result(
                error=result.get("message", "連結失敗")
            )


@register_command
class MemoryGetEntitiesCommand(MemoryCommand):
    """取得記憶相關實體"""
    
    name = "memory_get_entities"
    description = "取得記憶相關的所有實體"
    
    def execute(self, memory_id: str) -> CommandResult:
        _, _, _, _, _, _, relation_manager, _ = get_managers(quiet=True)
        entities = relation_manager.get_memory_entities(memory_id)
        
        return CommandResult.success_result(
            message=f"找到 {len(entities)} 個相關實體",
            data={
                "entities": entities,
                "total": len(entities)
            }
        )


@register_command
class EntityGetMemoriesCommand(EntityCommand):
    """取得實體相關記憶"""
    
    name = "entity_get_memories"
    description = "取得實體相關的所有記憶"
    
    def execute(
        self,
        entity_id: str,
        relation: str = None,
        limit: int = 50
    ) -> CommandResult:
        _, _, _, _, _, _, relation_manager, _ = get_managers(quiet=True)
        memories = relation_manager.get_entity_memories(entity_id, relation, limit)
        
        return CommandResult.success_result(
            message=f"找到 {len(memories)} 筆相關記憶",
            data={
                "memories": memories,
                "total": len(memories)
            }
        )


# ===== 實體解析命令 =====

@register_command
class ResolveNameCommand(ResolverCommand):
    """解析名稱"""
    
    name = "resolve_name"
    description = "解析名稱，找到對應實體或建立待確認項目"
    
    def execute(
        self,
        name: str,
        memory_id: str = None,
        context: str = None
    ) -> CommandResult:
        _, _, _, _, _, _, _, entity_resolver = get_managers(quiet=True)
        result = entity_resolver.auto_resolve(name, memory_id, context)
        
        return CommandResult.success_result(
            message="名稱解析完成",
            data=result
        )


@register_command
class GetPendingConfirmationsCommand(ResolverCommand):
    """取得待確認列表"""
    
    name = "get_pending_confirmations"
    description = "取得待確認項目列表"
    
    def execute(self, limit: int = 50) -> CommandResult:
        _, _, _, _, _, _, _, entity_resolver = get_managers(quiet=True)
        pending = entity_resolver.get_pending(limit)
        
        return CommandResult.success_result(
            message=f"共 {len(pending)} 個待確認項目",
            data={
                "pending": pending,
                "total": len(pending)
            }
        )


@register_command
class ConfirmEntityCommand(ResolverCommand):
    """確認實體"""
    
    name = "confirm_entity"
    description = "確認待確認項目"
    
    def execute(
        self,
        pending_id: int,
        entity_id: str = None,
        create_new: bool = False,
        new_entity_type: str = None,
        new_entity_name: str = None
    ) -> CommandResult:
        _, _, _, _, _, _, _, entity_resolver = get_managers(quiet=True)
        result = entity_resolver.confirm(
            pending_id, entity_id, create_new, new_entity_type, new_entity_name
        )
        
        if result.get("success"):
            return CommandResult.success_result(
                message="實體已確認",
                data=result
            )
        else:
            return CommandResult.error_result(
                error=result.get("message", "確認失敗")
            )


@register_command
class RejectPendingCommand(ResolverCommand):
    """拒絕待確認"""
    
    name = "reject_pending"
    description = "拒絕待確認項目（跳過不處理）"
    
    def execute(self, pending_id: int) -> CommandResult:
        _, _, _, _, _, _, _, entity_resolver = get_managers(quiet=True)
        result = entity_resolver.reject(pending_id)
        
        if result.get("success"):
            return CommandResult.success_result(
                message="已拒絕待確認項目",
                data=result
            )
        else:
            return CommandResult.error_result(
                error=result.get("message", "拒絕失敗")
            )


# 註：其他已存在的命令（entity_create, relation_create 等）
# 將在重構 mcp_server.py 和 cli.py 時一併轉換為命令類別
