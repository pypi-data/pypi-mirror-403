"""
關係管理器
處理知識圖譜中實體之間的關係
"""
import json
from datetime import datetime
from typing import Dict, List, Optional


class RelationManager:
    """知識圖譜關係管理"""

    # 預設關係類型
    RELATION_TYPES = [
        "teaches",      # person → topic
        "learns_from",  # person → person
        "works_on",     # person → project
        "member_of",    # person → project/organization
        "manages",      # person → project/organization
        "reports_to",   # person → person
        "client_of",    # person/organization → project
        "part_of",      # topic → topic (階層)
        "related_to",   # 通用關聯
        "located_at",   # event → place
        "attended_by",  # event → person
    ]

    def __init__(self, conn):
        """
        Args:
            conn: SQLite 連線
        """
        self.conn = conn

    def create(
        self,
        from_id: str,
        relation: str,
        to_id: str,
        properties: Optional[Dict] = None,
        confidence: float = 1.0,
        source: str = "user_confirmed"
    ) -> Dict:
        """
        建立關係
        
        Args:
            from_id: 來源實體 ID
            relation: 關係類型
            to_id: 目標實體 ID
            properties: 額外屬性
            confidence: 信心度
            source: 來源（user_confirmed, auto_detected）
        
        Returns:
            建立結果
        """
        # 檢查實體是否存在
        from_cursor = self.conn.execute(
            "SELECT id FROM entities WHERE id = ?", (from_id,)
        )
        if not from_cursor.fetchone():
            return {"success": False, "message": f"來源實體不存在: {from_id}"}
        
        to_cursor = self.conn.execute(
            "SELECT id FROM entities WHERE id = ?", (to_id,)
        )
        if not to_cursor.fetchone():
            return {"success": False, "message": f"目標實體不存在: {to_id}"}
        
        # 檢查關係是否已存在
        exist_cursor = self.conn.execute("""
            SELECT id FROM relations 
            WHERE from_id = ? AND relation = ? AND to_id = ?
        """, (from_id, relation, to_id))
        if exist_cursor.fetchone():
            return {"success": False, "message": f"關係已存在: {from_id} -{relation}→ {to_id}"}
        
        now = datetime.now().isoformat()
        props_json = json.dumps(properties or {}, ensure_ascii=False)
        
        cursor = self.conn.execute("""
            INSERT INTO relations (from_id, relation, to_id, properties, confidence, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (from_id, relation, to_id, props_json, confidence, source, now))
        
        self.conn.commit()
        
        return {
            "success": True,
            "id": cursor.lastrowid,
            "from_id": from_id,
            "relation": relation,
            "to_id": to_id
        }

    def delete(self, relation_id: int) -> Dict:
        """刪除關係"""
        cursor = self.conn.execute(
            "SELECT * FROM relations WHERE id = ?", (relation_id,)
        )
        if not cursor.fetchone():
            return {"success": False, "message": f"關係不存在: {relation_id}"}
        
        self.conn.execute("DELETE FROM relations WHERE id = ?", (relation_id,))
        self.conn.commit()
        
        return {"success": True, "message": f"關係已刪除: {relation_id}"}

    def delete_by_entities(self, from_id: str, relation: str, to_id: str) -> Dict:
        """根據實體和關係類型刪除"""
        cursor = self.conn.execute("""
            SELECT id FROM relations 
            WHERE from_id = ? AND relation = ? AND to_id = ?
        """, (from_id, relation, to_id))
        row = cursor.fetchone()
        
        if not row:
            return {"success": False, "message": f"關係不存在: {from_id} -{relation}→ {to_id}"}
        
        self.conn.execute("""
            DELETE FROM relations 
            WHERE from_id = ? AND relation = ? AND to_id = ?
        """, (from_id, relation, to_id))
        self.conn.commit()
        
        return {"success": True, "message": f"關係已刪除: {from_id} -{relation}→ {to_id}"}

    def query(
        self,
        from_id: Optional[str] = None,
        relation: Optional[str] = None,
        to_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        查詢關係
        
        Args:
            from_id: 來源實體（可選）
            relation: 關係類型（可選）
            to_id: 目標實體（可選）
            limit: 結果數量
        
        Returns:
            符合條件的關係列表
        """
        conditions = []
        params = []
        
        if from_id:
            conditions.append("r.from_id = ?")
            params.append(from_id)
        if relation:
            conditions.append("r.relation = ?")
            params.append(relation)
        if to_id:
            conditions.append("r.to_id = ?")
            params.append(to_id)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cursor = self.conn.execute(f"""
            SELECT 
                r.id, r.from_id, r.relation, r.to_id, 
                r.properties, r.confidence, r.source, r.created_at,
                e1.canonical_name as from_name, e1.type as from_type,
                e2.canonical_name as to_name, e2.type as to_type
            FROM relations r
            JOIN entities e1 ON r.from_id = e1.id
            JOIN entities e2 ON r.to_id = e2.id
            WHERE {where_clause}
            ORDER BY r.created_at DESC
            LIMIT ?
        """, params + [limit])
        
        results = []
        for row in cursor:
            results.append({
                "id": row["id"],
                "from_id": row["from_id"],
                "from_name": row["from_name"],
                "from_type": row["from_type"],
                "relation": row["relation"],
                "to_id": row["to_id"],
                "to_name": row["to_name"],
                "to_type": row["to_type"],
                "properties": json.loads(row["properties"]) if row["properties"] else {},
                "confidence": row["confidence"],
                "source": row["source"],
                "created_at": row["created_at"]
            })
        
        return results

    def get_related(
        self,
        entity_id: str,
        relation: Optional[str] = None,
        direction: str = "both"
    ) -> Dict:
        """
        取得實體的所有相關實體
        
        Args:
            entity_id: 實體 ID
            relation: 關係類型過濾（可選）
            direction: 方向 - outgoing/incoming/both
        
        Returns:
            相關實體列表
        """
        outgoing = []
        incoming = []
        
        if direction in ("outgoing", "both"):
            if relation:
                cursor = self.conn.execute("""
                    SELECT r.relation, r.to_id, e.canonical_name, e.type
                    FROM relations r
                    JOIN entities e ON r.to_id = e.id
                    WHERE r.from_id = ? AND r.relation = ?
                """, (entity_id, relation))
            else:
                cursor = self.conn.execute("""
                    SELECT r.relation, r.to_id, e.canonical_name, e.type
                    FROM relations r
                    JOIN entities e ON r.to_id = e.id
                    WHERE r.from_id = ?
                """, (entity_id,))
            
            for row in cursor:
                outgoing.append({
                    "relation": row["relation"],
                    "entity_id": row["to_id"],
                    "name": row["canonical_name"],
                    "type": row["type"]
                })
        
        if direction in ("incoming", "both"):
            if relation:
                cursor = self.conn.execute("""
                    SELECT r.relation, r.from_id, e.canonical_name, e.type
                    FROM relations r
                    JOIN entities e ON r.from_id = e.id
                    WHERE r.to_id = ? AND r.relation = ?
                """, (entity_id, relation))
            else:
                cursor = self.conn.execute("""
                    SELECT r.relation, r.from_id, e.canonical_name, e.type
                    FROM relations r
                    JOIN entities e ON r.from_id = e.id
                    WHERE r.to_id = ?
                """, (entity_id,))
            
            for row in cursor:
                incoming.append({
                    "relation": row["relation"],
                    "entity_id": row["from_id"],
                    "name": row["canonical_name"],
                    "type": row["type"]
                })
        
        return {
            "entity_id": entity_id,
            "outgoing": outgoing,
            "incoming": incoming
        }

    def get_path(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 3
    ) -> Optional[List[Dict]]:
        """
        找出兩個實體之間的路徑
        
        Args:
            from_id: 起點實體
            to_id: 終點實體
            max_depth: 最大深度
        
        Returns:
            路徑列表，或 None
        """
        if from_id == to_id:
            return []
        
        # BFS
        visited = {from_id}
        queue = [(from_id, [])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) >= max_depth:
                continue
            
            # 查詢當前節點的所有連結
            cursor = self.conn.execute("""
                SELECT relation, to_id, 'outgoing' as direction FROM relations WHERE from_id = ?
                UNION ALL
                SELECT relation, from_id, 'incoming' as direction FROM relations WHERE to_id = ?
            """, (current_id, current_id))
            
            for row in cursor:
                next_id = row["to_id"]
                if next_id in visited:
                    continue
                
                new_path = path + [{
                    "from": current_id,
                    "relation": row["relation"],
                    "to": next_id,
                    "direction": row["direction"]
                }]
                
                if next_id == to_id:
                    return new_path
                
                visited.add(next_id)
                queue.append((next_id, new_path))
        
        return None

    def link_memory(
        self,
        memory_id: str,
        entity_id: str,
        relation: str = "mentions"
    ) -> Dict:
        """
        將記憶與實體關聯
        
        Args:
            memory_id: 記憶 ID
            entity_id: 實體 ID
            relation: 關係類型（about, with, mentions）
        """
        # 檢查實體是否存在
        cursor = self.conn.execute(
            "SELECT id FROM entities WHERE id = ?", (entity_id,)
        )
        if not cursor.fetchone():
            return {"success": False, "message": f"實體不存在: {entity_id}"}
        
        # 檢查記憶是否存在
        cursor = self.conn.execute(
            "SELECT id FROM memories WHERE id = ?", (memory_id,)
        )
        if not cursor.fetchone():
            return {"success": False, "message": f"記憶不存在: {memory_id}"}
        
        now = datetime.now().isoformat()
        
        try:
            self.conn.execute("""
                INSERT INTO memory_entities (memory_id, entity_id, relation, created_at)
                VALUES (?, ?, ?, ?)
            """, (memory_id, entity_id, relation, now))
            self.conn.commit()
            
            return {"success": True, "message": f"已關聯: {memory_id} ← {relation} → {entity_id}"}
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                return {"success": False, "message": "關聯已存在"}
            raise

    def unlink_memory(self, memory_id: str, entity_id: str, relation: str = None) -> Dict:
        """解除記憶與實體的關聯"""
        if relation:
            self.conn.execute("""
                DELETE FROM memory_entities 
                WHERE memory_id = ? AND entity_id = ? AND relation = ?
            """, (memory_id, entity_id, relation))
        else:
            self.conn.execute("""
                DELETE FROM memory_entities 
                WHERE memory_id = ? AND entity_id = ?
            """, (memory_id, entity_id))
        
        self.conn.commit()
        return {"success": True, "message": "關聯已移除"}

    def get_memory_entities(self, memory_id: str) -> List[Dict]:
        """取得記憶相關的所有實體"""
        cursor = self.conn.execute("""
            SELECT me.relation, me.entity_id, e.canonical_name, e.type
            FROM memory_entities me
            JOIN entities e ON me.entity_id = e.id
            WHERE me.memory_id = ?
        """, (memory_id,))
        
        results = []
        for row in cursor:
            results.append({
                "relation": row["relation"],
                "entity_id": row["entity_id"],
                "name": row["canonical_name"],
                "type": row["type"]
            })
        
        return results

    def get_entity_memories(self, entity_id: str, relation: str = None, limit: int = 50) -> List[Dict]:
        """取得實體相關的所有記憶"""
        if relation:
            cursor = self.conn.execute("""
                SELECT me.relation, m.id, m.title, m.file_path, m.updated
                FROM memory_entities me
                JOIN memories m ON me.memory_id = m.id
                WHERE me.entity_id = ? AND me.relation = ?
                ORDER BY m.updated DESC
                LIMIT ?
            """, (entity_id, relation, limit))
        else:
            cursor = self.conn.execute("""
                SELECT me.relation, m.id, m.title, m.file_path, m.updated
                FROM memory_entities me
                JOIN memories m ON me.memory_id = m.id
                WHERE me.entity_id = ?
                ORDER BY m.updated DESC
                LIMIT ?
            """, (entity_id, limit))
        
        results = []
        for row in cursor:
            results.append({
                "relation": row["relation"],
                "memory_id": row["id"],
                "title": row["title"],
                "file_path": row["file_path"],
                "updated": row["updated"]
            })
        
        return results
