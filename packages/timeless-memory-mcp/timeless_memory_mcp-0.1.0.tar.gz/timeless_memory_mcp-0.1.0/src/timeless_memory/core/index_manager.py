"""
索引管理器（架構 B）
使用 SQLite FTS5 進行全文檢索
"""
import sqlite3
import hashlib
import sys
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing


def _log(msg: str):
    """輸出到 stderr（避免干擾 MCP stdio 通訊）"""
    print(msg, file=sys.stderr)


class IndexManager:
    """
    SQLite FTS5 索引管理器（架構 B）
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._init_connection()
        self._init_tables()

    def _init_connection(self):
        """初始化資料庫連線"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def _init_tables(self):
        """建立索引表"""
        # 先建立基礎表
        self.conn.executescript("""
            -- 來源表（外部目錄註冊）
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE,
                source_type TEXT,
                category TEXT,
                recursive BOOLEAN DEFAULT 1,
                last_sync TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 記憶索引表（基礎結構）
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                title TEXT,
                file_path TEXT UNIQUE,
                speaker TEXT CHECK(speaker IN ('user', 'ai', 'external')),
                authority INTEGER CHECK(authority BETWEEN 1 AND 10),
                quality INTEGER CHECK(quality BETWEEN 1 AND 5),
                captured_at TIMESTAMP NOT NULL,
                updated TIMESTAMP NOT NULL,
                tags TEXT,
                keywords TEXT,
                content_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 全文檢索索引（FTS5）
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                id UNINDEXED,
                title,
                content,
                tokenize='unicode61 remove_diacritics 2'
            );

            -- 實體表（知識圖譜節點）
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                canonical_name TEXT NOT NULL,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 別名表（實體的多種稱呼）
            CREATE TABLE IF NOT EXISTS aliases (
                id INTEGER PRIMARY KEY,
                alias TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'user_confirmed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
            );

            -- 關係表（實體之間的連結）
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY,
                from_id TEXT NOT NULL,
                relation TEXT NOT NULL,
                to_id TEXT NOT NULL,
                properties TEXT,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'user_confirmed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_id) REFERENCES entities(id) ON DELETE CASCADE,
                FOREIGN KEY (to_id) REFERENCES entities(id) ON DELETE CASCADE
            );

            -- 記憶-實體關聯表
            CREATE TABLE IF NOT EXISTS memory_entities (
                memory_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                relation TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (memory_id, entity_id, relation),
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
            );

            -- 待確認佇列（實體解析用）
            CREATE TABLE IF NOT EXISTS pending_confirmations (
                id INTEGER PRIMARY KEY,
                memory_id TEXT,
                extracted_name TEXT NOT NULL,
                suggested_entity_id TEXT,
                suggested_type TEXT,
                context TEXT,
                confidence REAL DEFAULT 0.5,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
                FOREIGN KEY (suggested_entity_id) REFERENCES entities(id) ON DELETE SET NULL
            );

            -- 基礎複合索引
            CREATE INDEX IF NOT EXISTS idx_speaker_authority
                ON memories(speaker, authority DESC);
            CREATE INDEX IF NOT EXISTS idx_updated
                ON memories(updated DESC);
            CREATE INDEX IF NOT EXISTS idx_quality_updated
                ON memories(quality DESC, updated DESC);
            CREATE INDEX IF NOT EXISTS idx_tags
                ON memories(tags);
            
            -- 實體相關索引
            CREATE INDEX IF NOT EXISTS idx_entities_type
                ON entities(type);
            CREATE INDEX IF NOT EXISTS idx_entities_name
                ON entities(canonical_name);
            CREATE INDEX IF NOT EXISTS idx_aliases_alias
                ON aliases(alias);
            CREATE INDEX IF NOT EXISTS idx_aliases_entity
                ON aliases(entity_id);
            CREATE INDEX IF NOT EXISTS idx_relations_from
                ON relations(from_id);
            CREATE INDEX IF NOT EXISTS idx_relations_to
                ON relations(to_id);
            CREATE INDEX IF NOT EXISTS idx_relations_type
                ON relations(relation);
            CREATE INDEX IF NOT EXISTS idx_memory_entities_memory
                ON memory_entities(memory_id);
            CREATE INDEX IF NOT EXISTS idx_memory_entities_entity
                ON memory_entities(entity_id);
            CREATE INDEX IF NOT EXISTS idx_pending_status
                ON pending_confirmations(status);
            CREATE INDEX IF NOT EXISTS idx_pending_memory
                ON pending_confirmations(memory_id);
        """)
        self.conn.commit()
        
        # 遷移：為現有表新增欄位（如果不存在）
        self._migrate_tables()
    
    def _migrate_tables(self):
        """資料庫遷移：新增欄位"""
        cursor = self.conn.execute("PRAGMA table_info(memories)")
        columns = {row[1] for row in cursor.fetchall()}
        
        migrations = [
            ("source_id", "INTEGER"),
            ("storage_mode", "TEXT DEFAULT 'internal'"),
            ("mtime", "INTEGER"),
            ("remind_at", "TIMESTAMP"),
        ]
        
        for col_name, col_type in migrations:
            if col_name not in columns:
                try:
                    self.conn.execute(f"ALTER TABLE memories ADD COLUMN {col_name} {col_type}")
                    self.conn.commit()
                except sqlite3.OperationalError:
                    pass
        
        # 建立新欄位的索引（遷移後）
        try:
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_source_id ON memories(source_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_mode ON memories(storage_mode)")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def update(self, memory_id: str, file_path: str, metadata: Dict, content: str, auto_commit: bool = True):
        """更新索引（支援批次模式）
        
        Args:
            memory_id: 記憶 ID
            file_path: 檔案路徑
            metadata: 元資料
            content: 內容
            auto_commit: 是否自動 commit（批次模式設為 False）
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # 處理 keywords（可能是字串或列表）
        keywords = metadata.get('keywords', '')
        if isinstance(keywords, list):
            keywords = ','.join(str(k) for k in keywords if k)

        self.conn.execute("""
            INSERT OR REPLACE INTO memories
            (id, title, file_path, speaker, authority, quality, captured_at, updated, tags, keywords, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id,
            metadata.get('title', ''),
            file_path,
            metadata.get('speaker', 'external'),
            metadata.get('authority', 3),
            metadata.get('quality', 3),
            metadata.get('captured_at', ''),
            metadata.get('updated', ''),
            ','.join(metadata.get('tags', [])),
            keywords,
            content_hash
        ))

        self.conn.execute("""
            INSERT OR REPLACE INTO memories_fts (id, title, content)
            VALUES (?, ?, ?)
        """, (memory_id, metadata.get('title', ''), content))

        if auto_commit:
            self.conn.commit()
    
    def batch_update(self, memories: List[Tuple[str, str, Dict, str]], batch_size: int = 100):
        """批次更新索引
        
        Args:
            memories: [(memory_id, file_path, metadata, content), ...]
            batch_size: 每批次大小
        """
        total = len(memories)
        
        for i in range(0, total, batch_size):
            batch = memories[i:i+batch_size]
            
            for memory_id, file_path, metadata, content in batch:
                self.update(memory_id, file_path, metadata, content, auto_commit=False)
            
            self.conn.commit()
            
            if (i + batch_size) % 500 == 0 or (i + batch_size) >= total:
                _log(f"  已索引 {min(i + batch_size, total)} / {total} 筆...")

    def search(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[Dict]:
        """全文檢索（FTS5 優先，LIKE fallback 用於中文）"""
        results = self._search_fts(query, filters, limit)
        
        # FTS5 無結果時，嘗試 LIKE 查詢（支援中文）
        if not results:
            results = self._search_like(query, filters, limit)
        
        return results
    
    def _search_fts(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[Dict]:
        """FTS5 全文檢索"""
        sql = """
            SELECT
                m.*,
                snippet(memories_fts, 2, '<mark>', '</mark>', '...', 64) as snippet,
                rank
            FROM memories m
            JOIN memories_fts fts ON m.id = fts.id
            WHERE fts.content MATCH ?
        """
        params = [query]
        sql = self._add_filters(sql, params, filters)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        try:
            cursor = self.conn.execute(sql, params)
            rows = cursor.fetchall()
        except Exception as e:
            # FTS5 搜尋失敗（可能是中文查詢），返回空讓 LIKE fallback
            return []
        
        return self._rows_to_results(rows)
    
    def _search_like(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[Dict]:
        """LIKE 模糊搜尋（支援中文）"""
        sql = """
            SELECT
                m.*,
                '' as snippet,
                0 as rank
            FROM memories m
            JOIN memories_fts fts ON m.id = fts.id
            WHERE (fts.title LIKE ? OR fts.content LIKE ?)
        """
        like_pattern = f'%{query}%'
        params = [like_pattern, like_pattern]
        sql = self._add_filters(sql, params, filters)
        sql += " ORDER BY m.captured_at DESC LIMIT ?"
        params.append(limit)

        try:
            cursor = self.conn.execute(sql, params)
            rows = cursor.fetchall()
        except Exception as e:
            _log(f"LIKE search error: {e}")
            return []
        
        return self._rows_to_results(rows)
    
    def _add_filters(self, sql: str, params: list, filters: Optional[Dict]) -> str:
        """加入過濾條件到 SQL，返回修改後的 SQL"""
        if not filters:
            return sql
        
        if 'speaker' in filters:
            sql += " AND m.speaker = ?"
            params.append(filters['speaker'])

        if 'authority' in filters:
            if isinstance(filters['authority'], dict):
                if 'gte' in filters['authority']:
                    sql += " AND m.authority >= ?"
                    params.append(filters['authority']['gte'])
                if 'lte' in filters['authority']:
                    sql += " AND m.authority <= ?"
                    params.append(filters['authority']['lte'])
            else:
                sql += " AND m.authority >= ?"
                params.append(filters['authority'])

        if 'quality' in filters:
            if isinstance(filters['quality'], dict):
                if 'gte' in filters['quality']:
                    sql += " AND m.quality >= ?"
                    params.append(filters['quality']['gte'])
            else:
                sql += " AND m.quality >= ?"
                params.append(filters['quality'])

        if 'date_range' in filters:
            start, end = filters['date_range']
            sql += " AND m.captured_at BETWEEN ? AND ?"
            params.extend([start, end])

        if 'tags' in filters:
            for tag in filters['tags']:
                sql += " AND m.tags LIKE ?"
                params.append(f'%{tag}%')
        
        return sql
    
    def _rows_to_results(self, rows) -> List[Dict]:
        """轉換資料列為結果"""
        results = []
        for row in rows:
            results.append({
                'id': row['id'],
                'title': row['title'],
                'file_path': row['file_path'],
                'metadata': {
                    'speaker': row['speaker'],
                    'authority': row['authority'],
                    'quality': row['quality'],
                    'captured_at': row['captured_at'],
                    'updated': row['updated'],
                    'tags': row['tags'].split(',') if row['tags'] else [],
                    'keywords': row['keywords']
                },
                'snippet': row['snippet'] if len(row) > 12 else ''
            })
        return results

    def get_file_path(self, memory_id: str) -> Optional[str]:
        """取得記憶檔案路徑"""
        cursor = self.conn.execute(
            "SELECT file_path FROM memories WHERE id = ?",
            (memory_id,)
        )
        row = cursor.fetchone()
        return row['file_path'] if row else None

    def delete(self, memory_id: str):
        """刪除索引"""
        self.conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self.conn.execute("DELETE FROM memories_fts WHERE id = ?", (memory_id,))
        self.conn.commit()

    def rebuild(self, memory_manager, parallel: bool = True, workers: int = None):
        """重建索引（支援平行處理）
        
        Args:
            memory_manager: 記憶管理器
            parallel: 是否使用平行處理
            workers: 工作進程數（None 則自動）
        """
        _log("🗑️  清空現有索引...")
        self.conn.execute("DELETE FROM memories")
        self.conn.execute("DELETE FROM memories_fts")
        self.conn.commit()

        _log("📂 掃描記憶檔案...")
        memory_list = memory_manager.list_memories(limit=999999)
        total = len(memory_list)
        _log(f"   找到 {total} 筆記憶")
        
        if not memory_list:
            _log("索引重建完成：共 0 筆記憶")
            return

        if parallel and total > 100:
            _log(f"🚀 使用平行處理模式...")
            self._rebuild_parallel(memory_manager, memory_list, workers)
        else:
            _log(f"📝 使用循序處理模式...")
            self._rebuild_sequential(memory_manager, memory_list)

        _log(f"✅ 索引重建完成：共 {total} 筆記憶")
    
    def _rebuild_sequential(self, memory_manager, memory_list: List[Dict]):
        """循序重建索引"""
        total = len(memory_list)
        
        for i, mem in enumerate(memory_list, 1):
            full_memory = memory_manager.read_memory(mem['id'])
            if full_memory:
                self.update(
                    full_memory['id'],
                    full_memory['file_path'],
                    full_memory['metadata'],
                    full_memory['content'],
                    auto_commit=False
                )
            
            if i % 100 == 0 or i == total:
                self.conn.commit()
                _log(f"  已索引 {i} / {total} 筆...")
        
        self.conn.commit()
    
    def _rebuild_parallel(self, memory_manager, memory_list: List[Dict], workers: int = None):
        """平行重建索引
        
        策略：
        1. 多進程平行讀取檔案（I/O 密集）
        2. 主進程批次寫入 SQLite（單執行緒鎖定）
        """
        if workers is None:
            workers = min(multiprocessing.cpu_count(), 8)
        
        _log(f"   使用 {workers} 個工作進程")
        
        # 平行讀取檔案
        memories_data = []
        completed = 0
        total = len(memory_list)
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            # 提交所有讀取任務
            future_to_mem = {
                executor.submit(_read_memory_worker, mem['id'], mem['file_path']): mem
                for mem in memory_list
            }
            
            # 收集結果
            for future in as_completed(future_to_mem):
                completed += 1
                if completed % 500 == 0:
                    _log(f"  已讀取 {completed} / {total} 筆...")
                
                try:
                    result = future.result()
                    if result:
                        memories_data.append(result)
                except Exception as e:
                    mem = future_to_mem[future]
                    _log(f"  ⚠️  讀取失敗: {mem['id']} - {e}")
        
        _log(f"  已讀取 {len(memories_data)} 筆記憶")
        
        # 批次寫入索引
        _log(f"💾 批次寫入索引...")
        self.batch_update(memories_data, batch_size=100)

    def get_all_tags(self) -> Dict:
        """取得所有 tags"""
        cursor = self.conn.execute(
            "SELECT tags FROM memories WHERE tags != '' AND tags IS NOT NULL"
        )
        all_tags = set()
        for row in cursor:
            if row['tags']:
                for tag in row['tags'].split(','):
                    tag = tag.strip()
                    if tag:
                        all_tags.add(tag)
        
        return {
            'tags': sorted(list(all_tags)),
            'total': len(all_tags)
        }

    def browse_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """瀏覽分類"""
        sql = """
            SELECT id, title, file_path, speaker, authority, quality,
                   captured_at, updated, tags, keywords
            FROM memories
            WHERE tags LIKE ? OR file_path LIKE ?
            ORDER BY updated DESC
            LIMIT ?
        """
        pattern = f'%{category}%'
        cursor = self.conn.execute(sql, (pattern, pattern, limit))
        
        results = []
        for row in cursor:
            results.append({
                'id': row['id'],
                'title': row['title'],
                'file_path': row['file_path'],
                'metadata': {
                    'speaker': row['speaker'],
                    'authority': row['authority'],
                    'quality': row['quality'],
                    'captured_at': row['captured_at'],
                    'updated': row['updated'],
                    'tags': row['tags'].split(',') if row['tags'] else [],
                    'keywords': row['keywords']
                }
            })
        return results

    def get_categories(self) -> Dict:
        """取得所有分類"""
        cursor = self.conn.execute("""
            SELECT DISTINCT
                CASE
                    WHEN file_path LIKE '%語義記憶%' THEN '語義記憶'
                    WHEN file_path LIKE '%情節記憶%' THEN '情節記憶'
                    WHEN file_path LIKE '%程序記憶%' THEN '程序記憶'
                    ELSE '其他'
                END as category,
                COUNT(*) as count
            FROM memories
            GROUP BY category
        """)
        
        categories = {}
        for row in cursor:
            categories[row['category']] = row['count']
        
        return {
            'categories': list(categories.keys()),
            'counts': categories,
            'total': sum(categories.values())
        }

    def get_stats(self) -> Dict:
        """取得統計資訊"""
        cursor = self.conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN speaker = 'user' THEN 1 END) as user_memories,
                COUNT(CASE WHEN speaker = 'ai' THEN 1 END) as ai_memories,
                COUNT(CASE WHEN quality >= 4 THEN 1 END) as high_quality,
                AVG(authority) as avg_authority
            FROM memories
        """)
        row = cursor.fetchone()

        return {
            'total_memories': row['total'],
            'user_memories': row['user_memories'],
            'ai_memories': row['ai_memories'],
            'high_quality_memories': row['high_quality'],
            'avg_authority': round(row['avg_authority'], 2) if row['avg_authority'] else 0
        }

    # ===== 提醒功能 =====
    
    def set_reminder(self, memory_id: str, remind_at: str) -> bool:
        """
        設定記憶提醒時間
        
        Args:
            memory_id: 記憶 ID
            remind_at: 提醒時間（ISO 格式）
        
        Returns:
            是否成功
        """
        cursor = self.conn.execute(
            "SELECT id FROM memories WHERE id = ?", (memory_id,)
        )
        if not cursor.fetchone():
            return False
        
        self.conn.execute(
            "UPDATE memories SET remind_at = ? WHERE id = ?",
            (remind_at, memory_id)
        )
        self.conn.commit()
        return True
    
    def clear_reminder(self, memory_id: str) -> bool:
        """清除記憶提醒"""
        self.conn.execute(
            "UPDATE memories SET remind_at = NULL WHERE id = ?",
            (memory_id,)
        )
        self.conn.commit()
        return True
    
    def get_reminders(self, include_past: bool = False, limit: int = 50) -> List[Dict]:
        """
        取得待提醒事項
        
        Args:
            include_past: 是否包含過期提醒
            limit: 數量上限
        
        Returns:
            提醒列表
        """
        from datetime import datetime
        now = datetime.now().isoformat()
        
        if include_past:
            cursor = self.conn.execute("""
                SELECT id, title, file_path, remind_at, updated
                FROM memories
                WHERE remind_at IS NOT NULL
                ORDER BY remind_at ASC
                LIMIT ?
            """, (limit,))
        else:
            cursor = self.conn.execute("""
                SELECT id, title, file_path, remind_at, updated
                FROM memories
                WHERE remind_at IS NOT NULL AND remind_at >= ?
                ORDER BY remind_at ASC
                LIMIT ?
            """, (now, limit))
        
        results = []
        for row in cursor:
            remind_at = row['remind_at']
            is_past = remind_at < now if remind_at else False
            
            results.append({
                'id': row['id'],
                'title': row['title'],
                'file_path': row['file_path'],
                'remind_at': remind_at,
                'updated': row['updated'],
                'is_past': is_past
            })
        
        return results
    
    def get_due_reminders(self) -> List[Dict]:
        """取得已到期但尚未處理的提醒"""
        from datetime import datetime
        now = datetime.now().isoformat()
        
        cursor = self.conn.execute("""
            SELECT id, title, file_path, remind_at, updated
            FROM memories
            WHERE remind_at IS NOT NULL AND remind_at <= ?
            ORDER BY remind_at ASC
        """, (now,))
        
        results = []
        for row in cursor:
            results.append({
                'id': row['id'],
                'title': row['title'],
                'file_path': row['file_path'],
                'remind_at': row['remind_at'],
                'updated': row['updated']
            })
        
        return results

    def close(self):
        """關閉資料庫連線"""
        if self.conn:
            self.conn.close()

    def __del__(self):
        self.close()



# ===== 工作進程函數（必須在模組層級） =====

def _read_memory_worker(memory_id: str, file_path: str) -> Optional[Tuple[str, str, Dict, str]]:
    """工作進程：讀取單個記憶檔案
    
    Args:
        memory_id: 記憶 ID（可為 None，會從 metadata 中讀取）
        file_path: 檔案路徑
    
    Returns:
        (memory_id, file_path, metadata, content) 或 None
    """
    try:
        from pathlib import Path
        import yaml
        
        path = Path(file_path)
        if not path.exists():
            return None
        
        text = path.read_text(encoding='utf-8')
        
        # 解析 frontmatter
        if not text.startswith('---'):
            return None
        
        parts = text.split('---', 2)
        if len(parts) < 3:
            return None
        
        metadata = yaml.safe_load(parts[1]) or {}
        content = parts[2].strip()
        
        # 從 metadata 中取得 memory_id（如果未傳入）
        actual_memory_id = memory_id or metadata.get('id', '')
        if not actual_memory_id:
            return None
        
        return (actual_memory_id, file_path, metadata, content)
    
    except Exception:
        return None

