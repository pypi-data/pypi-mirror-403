#!/usr/bin/env python3
"""
Timeless Memory CLI
完整功能，與 MCP Server 對等
"""
import argparse
import sys
import json
from pathlib import Path

from timeless_memory.core import get_managers


# ============ 記憶管理 ============

def cmd_memory_search(args):
    """搜尋記憶"""
    memory_manager, index_manager, retrieval_engine, entity_manager, *_ = get_managers()
    
    query = args.query
    limit = args.limit
    
    # 別名展開
    if query and query.startswith('@'):
        from timeless_memory.core.query_utils import resolve_query_with_aliases
        expanded_query, used_aliases = resolve_query_with_aliases(query, entity_manager)
        if used_aliases:
            print(f"📛 展開別名: {', '.join(used_aliases[:5])}")
            query = expanded_query
    
    # 搜尋
    results = index_manager.search(query, limit=limit) if query else []
    
    print(f"🔍 搜尋: '{query}'")
    print(f"   找到 {len(results)} 筆結果\n")
    
    for r in results:
        title = r.get('title', 'Untitled')
        score = r.get('score', 0)
        snippet = r.get('snippet', '')[:150]
        file_path = r.get('file_path', '')
        
        print(f"  📄 {title}")
        if score:
            print(f"     分數: {score:.2f}")
        if file_path:
            print(f"     路徑: {file_path}")
        if snippet:
            print(f"     {snippet}...")
        print()


def cmd_memory_create(args):
    """建立記憶"""
    memory_manager, *_ = get_managers()
    
    content = args.content
    if args.file:
        content = Path(args.file).read_text(encoding='utf-8')
    
    metadata = {
        'speaker': args.speaker or 'user',
        'category': args.category or '語義記憶',
        'authority': args.authority or 5,
    }
    if args.tags:
        metadata['tags'] = args.tags.split(',')
    
    result = memory_manager.create_memory(content, metadata)
    print(f"✅ 記憶已建立: {result['id']}")
    print(f"   檔案: {result['file_path']}")


def cmd_memory_read(args):
    """讀取記憶"""
    memory_manager, *_ = get_managers()
    
    memory = memory_manager.read_memory(args.memory_id)
    if not memory:
        print(f"❌ 找不到記憶: {args.memory_id}")
        return 1
    
    print(f"📄 {memory['title']}\n")
    print(f"ID: {memory['id']}")
    print(f"分類: {memory['category']}")
    print(f"說話者: {memory['speaker']}")
    print(f"權重: {memory['authority']}")
    if memory.get('tags'):
        print(f"標籤: {', '.join(memory['tags'])}")
    print(f"\n{memory['content']}")


def cmd_memory_update(args):
    """更新記憶"""
    memory_manager, *_ = get_managers()
    
    updates = {}
    if args.content:
        updates['content'] = args.content
    if args.category:
        updates['category'] = args.category
    if args.tags:
        updates['tags'] = args.tags.split(',')
    if args.authority:
        updates['authority'] = args.authority
    
    result = memory_manager.update_memory(args.memory_id, updates)
    print(f"✅ 記憶已更新: {result['id']}")


def cmd_memory_delete(args):
    """刪除記憶"""
    memory_manager, *_ = get_managers()
    
    if not args.yes:
        confirm = input(f"確定要刪除記憶 {args.memory_id}? (y/N): ")
        if confirm.lower() != 'y':
            print("已取消")
            return
    
    memory_manager.delete_memory(args.memory_id)
    print(f"✅ 記憶已刪除: {args.memory_id}")


def cmd_memory_list(args):
    """列出記憶"""
    memory_manager, *_ = get_managers()
    
    memories = memory_manager.list_memories(category=args.category, limit=args.limit)
    
    print(f"📋 共 {len(memories)} 筆記憶\n")
    for m in memories:
        print(f"  📄 {m['title']}")
        print(f"     ID: {m['id']}")
        if m.get('speaker'):
            print(f"     說話者: {m['speaker']}")
        print()


# ============ 實體管理 ============

def cmd_entity_create(args):
    """建立實體"""
    _, _, _, entity_manager, *_ = get_managers()
    
    properties = {'role': args.role} if args.role else None
    aliases = args.aliases.split(',') if args.aliases else None
    
    result = entity_manager.create(
        entity_type=args.entity_type,
        name=args.name,
        properties=properties,
        aliases=aliases
    )
    print(f"✅ 實體已建立: {result['id']}")
    print(f"   名稱: {result['name']}")
    if aliases:
        print(f"   別名: {', '.join(aliases)}")


def cmd_entity_read(args):
    """讀取實體"""
    _, _, _, entity_manager, *_ = get_managers()
    
    entity = entity_manager.get_entity(args.entity_id)
    if not entity:
        print(f"❌ 找不到實體: {args.entity_id}")
        return 1
    
    print(f"📋 {entity['name']}\n")
    print(f"ID: {entity['id']}")
    print(f"類型: {entity['type']}")
    if entity.get('aliases'):
        print(f"別名: {', '.join(entity['aliases'])}")
    if entity.get('metadata'):
        print(f"屬性: {json.dumps(entity['metadata'], ensure_ascii=False, indent=2)}")


def cmd_entity_list(args):
    """列出實體"""
    _, _, _, entity_manager, *_ = get_managers()
    
    entities = entity_manager.list(entity_type=args.entity_type, limit=args.limit)
    
    print(f"📋 共 {len(entities)} 個實體\n")
    for e in entities:
        print(f"  {e['type']}: {e['name']}")
        print(f"     ID: {e['id']}")
        if e.get('aliases'):
            print(f"     別名: {', '.join(e['aliases'])}")
        print()


def cmd_entity_search(args):
    """搜尋實體"""
    _, _, _, entity_manager, *_ = get_managers()
    
    entities = entity_manager.search(
        query=args.query,
        entity_type=args.entity_type
    )
    
    print(f"🔍 找到 {len(entities)} 個實體\n")
    for e in entities:
        print(f"  {e['type']}: {e['name']}")
        print(f"     ID: {e['id']}")
        print()


# ============ 關係管理 ============

def cmd_relation_create(args):
    """建立關係"""
    _, _, _, _, relation_manager, *_ = get_managers()
    
    result = relation_manager.create_relation(
        from_id=args.from_id,
        to_id=args.to_id,
        relation_type=args.relation_type
    )
    print(f"✅ 關係已建立")
    print(f"   {args.from_id} --[{args.relation_type}]--> {args.to_id}")


def cmd_relation_list(args):
    """列出關係"""
    _, _, _, _, relation_manager, *_ = get_managers()
    
    relations = relation_manager.get_relations(
        entity_id=args.entity_id,
        relation_type=args.relation_type
    )
    
    print(f"📋 共 {len(relations)} 個關係\n")
    for r in relations:
        print(f"  {r['from_name']} --[{r['type']}]--> {r['to_name']}")
        if r.get('metadata'):
            print(f"     {r['metadata']}")
        print()


# ============ Google Chat ============

def cmd_chat_sync(args):
    """同步 Google Chat"""
    from timeless_memory.integrations import ChatManager
    from timeless_memory import get_home
    
    chat_manager = ChatManager(str(get_home()))
    
    print("🔄 開始同步 Google Chat...")
    result = chat_manager.sync(
        space_id=None,
        skip_dm=True,
        max_workers=getattr(args, 'workers', 5),
        full=args.full,
        overlap_days=getattr(args, 'overlap_days', 1)
    )
    
    if result.get("success"):
        print(f"\n✅ 同步完成")
        print(f"   下載: {result.get('download', {}).get('total_messages', 0)} 則訊息")
        print(f"   轉換: {result.get('convert', {}).get('new_memories', 0)} 個記憶")
        print(f"   索引: {result.get('index', {}).get('indexed_count', 0)} 筆")
    else:
        print(f"\n❌ 同步失敗: {result.get('error', '未知錯誤')}")


def cmd_chat_list(args):
    """列出 Google Chat 聊天室"""
    from timeless_memory.integrations import ChatManager
    from timeless_memory import get_home
    
    chat_manager = ChatManager(str(get_home()))
    spaces = chat_manager.list_spaces()
    
    print(f"📋 共 {len(spaces)} 個聊天室\n")
    for s in spaces:
        print(f"  {s['display_name']}")
        print(f"     ID: {s['name']}")
        print()


def cmd_chat_status(args):
    """顯示 Google Chat 狀態"""
    from timeless_memory.integrations import ChatManager
    from timeless_memory import get_home
    
    chat_manager = ChatManager(str(get_home()))
    status = chat_manager.status()
    
    print("📊 Google Chat 狀態\n")
    print(f"  認證: {'✅ 已認證' if status['authenticated'] else '❌ 未認證'}")
    print(f"  聊天室數: {status.get('total_spaces', 0)}")
    print(f"  已下載: {status.get('downloaded_spaces', 0)}")


def cmd_chat_analyze(args):
    """分析 Google Chat 資料，提取人物和專案資訊"""
    from timeless_memory.integrations import ChatManager
    from timeless_memory import get_home
    
    chat_manager = ChatManager(str(get_home()))
    
    print("🔍 分析 Google Chat 資料...\n")
    result = chat_manager.analyze(include_content=args.verbose)
    
    if not result.get("success"):
        print(f"❌ 分析失敗: {result.get('error')}")
        return 1
    
    summary = result.get("summary", {})
    print("📊 分析摘要\n")
    print(f"  檔案數: {summary.get('total_files', 0)}")
    print(f"  User IDs: {summary.get('total_user_ids', 0)}")
    print(f"  提及名字: {summary.get('total_mentions', 0)}")
    print(f"  專案數: {summary.get('total_projects', 0)}")
    print(f"  聊天室數: {summary.get('total_spaces', 0)}")
    
    # 顯示前 N 個發言者
    print("\n📋 發言最多的 User IDs:")
    for speaker in result.get("top_speakers", [])[:args.limit]:
        print(f"  {speaker['user_id']:12s}: {speaker['message_count']:5d} 則訊息")
    
    # 顯示專案
    print("\n📋 專案:")
    for code, proj in result.get("projects", {}).items():
        print(f"  {code}: {proj['name']}")
        print(f"       參與者: {proj['participant_count']} 人")
        print(f"       聊天室: {', '.join(proj['spaces'][:2])}")
        print()
    
    # 如果有 --json 參數，輸出完整 JSON
    if args.json:
        print("\n📄 完整 JSON 結果:")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_chat_user_context(args):
    """取得特定 User ID 的上下文資訊"""
    from timeless_memory.integrations import ChatManager
    from timeless_memory import get_home
    
    chat_manager = ChatManager(str(get_home()))
    
    print(f"🔍 查詢 User ID: {args.user_id}...\n")
    result = chat_manager.get_user_context(user_id=args.user_id, limit=args.limit)
    
    if not result.get("success"):
        print(f"❌ 查詢失敗: {result.get('error')}")
        return 1
    
    print(f"📊 User ID: {result['user_id']}")
    print(f"   參與聊天室: {result['space_count']} 個")
    print(f"   聊天室: {', '.join(result['spaces'][:5])}")
    
    # 顯示提及的名字
    mentioned = result.get("mentioned_names", [])
    if mentioned:
        print(f"\n📋 提及的名字 (前 10 個):")
        for m in mentioned[:10]:
            print(f"  @{m['name']:15s}: {m['count']:3d} 次")
    
    # 顯示發言範例
    messages = result.get("sample_messages", [])
    if messages:
        print(f"\n📋 發言範例 (前 {len(messages)} 則):")
        for msg in messages[:args.limit]:
            print(f"\n  [{msg['time']}] @ {msg['space']}")
            print(f"  {msg['text'][:100]}{'...' if len(msg['text']) > 100 else ''}")


# ============ 系統管理 ============

def cmd_stats(args):
    """顯示統計"""
    _, index_manager, *_ = get_managers()
    
    stats = index_manager.get_stats()
    
    print("📊 統計資訊\n")
    print(f"  總記憶數: {stats.get('total_memories', 0)}")
    print(f"  用戶記憶: {stats.get('user_memories', 0)}")
    print(f"  AI 記憶: {stats.get('ai_memories', 0)}\n")
    
    categories = stats.get('categories', {})
    if categories:
        print("  分類:")
        for cat, count in categories.items():
            print(f"    - {cat}: {count} 筆")


def cmd_rebuild(args):
    """重建索引"""
    memory_manager, index_manager, _, entity_manager, relation_manager, _ = get_managers()
    
    print("🔄 重建 SQLite FTS5 索引...\n")
    index_manager.rebuild(memory_manager)
    
    # 取得統計
    stats = index_manager.get_stats()
    entity_count = len(entity_manager.list(limit=9999))
    relation_count = len(relation_manager.query(limit=9999))
    
    print(f"\n✅ 索引重建完成")
    print(f"   記憶數: {stats.get('total_memories', 0)}")
    print(f"   實體數: {entity_count}")
    print(f"   關聯數: {relation_count}")
    
    # 分析 Google Chat 資料
    try:
        from timeless_memory.integrations import ChatManager
        from timeless_memory import get_home, get_data_dir
        
        chat_manager = ChatManager(str(get_home()))
        analyze_result = chat_manager.analyze(include_content=False)
        
        if analyze_result.get("success"):
            summary = analyze_result.get("summary", {})
            user_ids = summary.get("total_user_ids", 0)
            projects = summary.get("total_projects", 0)
            spaces = summary.get("total_spaces", 0)
            
            print("\n" + "=" * 60)
            print("📋 索引重建後 TODO")
            print("=" * 60)
            
            # TODO 1: 建立人物實體
            if user_ids > entity_count:
                print(f"\n1. 建立人物實體")
                print(f"   目前有 {user_ids} 個 User IDs，已建立 {entity_count} 個實體")
                print(f"   指令: timeless-memory chat analyze")
                print(f"         timeless-memory chat user-context <user_id>")
            
            # TODO 2: 建立專案實體
            if projects > 0:
                print(f"\n2. 建立專案實體")
                print(f"   發現 {projects} 個專案")
                print(f"   指令: timeless-memory entity create project <專案名稱>")
            
            # TODO 3: 建立關聯
            if entity_count > 0:
                print(f"\n3. 建立人物-專案關聯")
                print(f"   指令: timeless-memory relation create <person-id> <project-id> works_on")
            
            # TODO 4: 每月摘要
            data_dir = get_data_dir()
            google_chat_dir = data_dir / "google-chat"
            if google_chat_dir.exists():
                space_dirs = [d.name for d in google_chat_dir.iterdir() if d.is_dir()]
                if space_dirs:
                    print(f"\n4. 建立每月聊天室摘要")
                    print(f"   {len(space_dirs)} 個聊天室需要建立 monthly-summary-YYYY-MM.md")
                    print(f"   聊天室: {', '.join(space_dirs[:5])}")
                    if len(space_dirs) > 5:
                        print(f"           ... 還有 {len(space_dirs) - 5} 個")
            
            print("\n" + "=" * 60)
    
    except Exception as e:
        pass  # 如果 Google Chat 分析失敗，不影響主要功能


# ============ 主程式 ============

def main():
    parser = argparse.ArgumentParser(
        description="Timeless Memory CLI - 完整功能",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='命令類型')
    
    # ===== 記憶管理 =====
    memory_parser = subparsers.add_parser('memory', help='記憶管理')
    memory_sub = memory_parser.add_subparsers(dest='action')
    
    # search
    search_parser = memory_sub.add_parser('search', help='搜尋記憶')
    search_parser.add_argument('query', help='搜尋關鍵字')
    search_parser.add_argument('--limit', type=int, default=10)
    search_parser.set_defaults(func=cmd_memory_search)
    
    # create
    create_parser = memory_sub.add_parser('create', help='建立記憶')
    create_parser.add_argument('content', help='記憶內容')
    create_parser.add_argument('--file', help='從檔案讀取')
    create_parser.add_argument('--speaker', help='說話者')
    create_parser.add_argument('--category', help='分類')
    create_parser.add_argument('--tags', help='標籤（逗號分隔）')
    create_parser.add_argument('--authority', type=int, help='權重')
    create_parser.set_defaults(func=cmd_memory_create)
    
    # read
    read_parser = memory_sub.add_parser('read', help='讀取記憶')
    read_parser.add_argument('memory_id', help='記憶 ID')
    read_parser.set_defaults(func=cmd_memory_read)
    
    # update
    update_parser = memory_sub.add_parser('update', help='更新記憶')
    update_parser.add_argument('memory_id', help='記憶 ID')
    update_parser.add_argument('--content', help='新內容')
    update_parser.add_argument('--category', help='新分類')
    update_parser.add_argument('--tags', help='新標籤')
    update_parser.add_argument('--authority', type=int, help='新權重')
    update_parser.set_defaults(func=cmd_memory_update)
    
    # delete
    delete_parser = memory_sub.add_parser('delete', help='刪除記憶')
    delete_parser.add_argument('memory_id', help='記憶 ID')
    delete_parser.add_argument('--yes', '-y', action='store_true', help='不詢問確認')
    delete_parser.set_defaults(func=cmd_memory_delete)
    
    # list
    list_parser = memory_sub.add_parser('list', help='列出記憶')
    list_parser.add_argument('--category', help='過濾分類')
    list_parser.add_argument('--limit', type=int, default=20)
    list_parser.set_defaults(func=cmd_memory_list)
    
    # ===== 實體管理 =====
    entity_parser = subparsers.add_parser('entity', help='實體管理')
    entity_sub = entity_parser.add_subparsers(dest='action')
    
    # create
    entity_create = entity_sub.add_parser('create', help='建立實體')
    entity_create.add_argument('entity_type', help='實體類型')
    entity_create.add_argument('name', help='實體名稱')
    entity_create.add_argument('--aliases', help='別名（逗號分隔）')
    entity_create.add_argument('--role', help='角色/職位')
    entity_create.set_defaults(func=cmd_entity_create)
    
    # read
    entity_read = entity_sub.add_parser('read', help='讀取實體')
    entity_read.add_argument('entity_id', help='實體 ID')
    entity_read.set_defaults(func=cmd_entity_read)
    
    # list
    entity_list = entity_sub.add_parser('list', help='列出實體')
    entity_list.add_argument('--type', dest='entity_type', help='過濾類型')
    entity_list.add_argument('--limit', type=int, default=50, help='結果數量')
    entity_list.set_defaults(func=cmd_entity_list)
    
    # search
    entity_search = entity_sub.add_parser('search', help='搜尋實體')
    entity_search.add_argument('query', help='搜尋關鍵字')
    entity_search.add_argument('--type', dest='entity_type', help='過濾類型')
    entity_search.set_defaults(func=cmd_entity_search)
    
    # ===== 關係管理 =====
    relation_parser = subparsers.add_parser('relation', help='關係管理')
    relation_sub = relation_parser.add_subparsers(dest='action')
    
    # create
    rel_create = relation_sub.add_parser('create', help='建立關係')
    rel_create.add_argument('from_id', help='來源實體 ID')
    rel_create.add_argument('to_id', help='目標實體 ID')
    rel_create.add_argument('relation_type', help='關係類型')
    rel_create.set_defaults(func=cmd_relation_create)
    
    # list
    rel_list = relation_sub.add_parser('list', help='列出關係')
    rel_list.add_argument('entity_id', help='實體 ID')
    rel_list.add_argument('--type', dest='relation_type', help='過濾關係類型')
    rel_list.set_defaults(func=cmd_relation_list)
    
    # ===== Google Chat =====
    chat_parser = subparsers.add_parser('chat', help='Google Chat 管理')
    chat_sub = chat_parser.add_subparsers(dest='action')
    
    # sync
    chat_sync = chat_sub.add_parser('sync', help='同步聊天記錄')
    chat_sync.add_argument('--spaces', help='指定聊天室（逗號分隔）')
    chat_sync.add_argument('--full', action='store_true', help='完整同步')
    chat_sync.add_argument('--overlap-days', type=int, default=1, help='增量下載回溯天數（預設 1）')
    chat_sync.add_argument('--workers', type=int, default=5, help='並行線程數（預設 5）')
    chat_sync.set_defaults(func=cmd_chat_sync)
    
    # list
    chat_list = chat_sub.add_parser('list', help='列出聊天室')
    chat_list.set_defaults(func=cmd_chat_list)
    
    # status
    chat_status = chat_sub.add_parser('status', help='顯示狀態')
    chat_status.set_defaults(func=cmd_chat_status)
    
    # analyze - 分析資料提取人物和專案（用於建立知識圖譜）
    chat_analyze = chat_sub.add_parser('analyze', help='分析資料，提取人物和專案資訊')
    chat_analyze.add_argument('--limit', type=int, default=20, help='顯示數量（預設 20）')
    chat_analyze.add_argument('--verbose', '-v', action='store_true', help='詳細模式')
    chat_analyze.add_argument('--json', action='store_true', help='輸出完整 JSON')
    chat_analyze.set_defaults(func=cmd_chat_analyze)
    
    # user-context - 取得特定 User ID 的上下文
    chat_user = chat_sub.add_parser('user-context', help='查詢特定 User ID 的上下文')
    chat_user.add_argument('user_id', help='User ID')
    chat_user.add_argument('--limit', type=int, default=5, help='訊息數量（預設 5）')
    chat_user.set_defaults(func=cmd_chat_user_context)
    
    # ===== 系統 =====
    stats_parser = subparsers.add_parser('stats', help='顯示統計')
    stats_parser.set_defaults(func=cmd_stats)
    
    rebuild_parser = subparsers.add_parser('rebuild', help='重建索引')
    rebuild_parser.set_defaults(func=cmd_rebuild)
    
    # 解析參數
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        args.func(args)
        return 0
    except Exception as e:
        print(f"❌ 錯誤: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
