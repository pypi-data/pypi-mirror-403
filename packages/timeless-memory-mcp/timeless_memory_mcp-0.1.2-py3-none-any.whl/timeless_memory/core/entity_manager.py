"""
實體管理器
處理知識圖譜中的實體（人物、專案、主題等）
"""
import json
from datetime import datetime
from typing import Dict, List, Optional


class EntityManager:
    """知識圖譜實體管理"""

    # 預設實體類型
    ENTITY_TYPES = ["person", "project", "topic", "place", "event", "organization"]

    def __init__(self, conn):
        """
        Args:
            conn: SQLite 連線
        """
        self.conn = conn

    def create(
        self,
        entity_type: str,
        name: str,
        properties: Optional[Dict] = None,
        aliases: Optional[List[str]] = None
    ) -> Dict:
        """
        建立實體
        
        Args:
            entity_type: 類型（person, project, topic, place, event, organization）
            name: 正式名稱
            properties: 額外屬性（JSON）
            aliases: 別名列表
        
        Returns:
            建立的實體資訊
        """
        # 生成 ID
        entity_id = f"{entity_type}-{name}"
        
        # 檢查是否已存在
        cursor = self.conn.execute(
            "SELECT id FROM entities WHERE id = ?", (entity_id,)
        )
        if cursor.fetchone():
            return {
                "success": False,
                "message": f"實體已存在: {entity_id}"
            }
        
        now = datetime.now().isoformat()
        props_json = json.dumps(properties or {}, ensure_ascii=False)
        
        # 建立實體
        self.conn.execute("""
            INSERT INTO entities (id, type, canonical_name, properties, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (entity_id, entity_type, name, props_json, now, now))
        
        # 建立預設別名（正式名稱）
        self.conn.execute("""
            INSERT INTO aliases (alias, entity_id, confidence, source)
            VALUES (?, ?, 1.0, 'system')
        """, (name, entity_id))
        
        # 建立額外別名
        if aliases:
            for alias in aliases:
                if alias != name:
                    self.conn.execute("""
                        INSERT INTO aliases (alias, entity_id, confidence, source)
                        VALUES (?, ?, 1.0, 'user_confirmed')
                    """, (alias, entity_id))
        
        self.conn.commit()
        
        return {
            "success": True,
            "id": entity_id,
            "type": entity_type,
            "name": name,
            "properties": properties or {},
            "aliases": [name] + (aliases or [])
        }

    def get(self, entity_id: str) -> Optional[Dict]:
        """取得實體資訊"""
        cursor = self.conn.execute("""
            SELECT id, type, canonical_name, properties, created_at, updated_at
            FROM entities WHERE id = ?
        """, (entity_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # 取得別名
        alias_cursor = self.conn.execute(
            "SELECT alias, confidence, source FROM aliases WHERE entity_id = ?",
            (entity_id,)
        )
        aliases = [
            {"alias": r["alias"], "confidence": r["confidence"], "source": r["source"]}
            for r in alias_cursor
        ]
        
        # 取得關係
        rel_cursor = self.conn.execute("""
            SELECT r.relation, r.to_id, e.canonical_name as to_name
            FROM relations r
            JOIN entities e ON r.to_id = e.id
            WHERE r.from_id = ?
        """, (entity_id,))
        outgoing_relations = [
            {"relation": r["relation"], "to_id": r["to_id"], "to_name": r["to_name"]}
            for r in rel_cursor
        ]
        
        rel_cursor = self.conn.execute("""
            SELECT r.relation, r.from_id, e.canonical_name as from_name
            FROM relations r
            JOIN entities e ON r.from_id = e.id
            WHERE r.to_id = ?
        """, (entity_id,))
        incoming_relations = [
            {"relation": r["relation"], "from_id": r["from_id"], "from_name": r["from_name"]}
            for r in rel_cursor
        ]
        
        return {
            "id": row["id"],
            "type": row["type"],
            "name": row["canonical_name"],
            "properties": json.loads(row["properties"]) if row["properties"] else {},
            "aliases": aliases,
            "outgoing_relations": outgoing_relations,
            "incoming_relations": incoming_relations,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

    def update(
        self,
        entity_id: str,
        name: Optional[str] = None,
        properties: Optional[Dict] = None
    ) -> Dict:
        """更新實體"""
        entity = self.get(entity_id)
        if not entity:
            return {"success": False, "message": f"實體不存在: {entity_id}"}
        
        now = datetime.now().isoformat()
        
        if name:
            self.conn.execute(
                "UPDATE entities SET canonical_name = ?, updated_at = ? WHERE id = ?",
                (name, now, entity_id)
            )
        
        if properties:
            # 合併屬性
            current_props = entity.get("properties", {})
            current_props.update(properties)
            props_json = json.dumps(current_props, ensure_ascii=False)
            self.conn.execute(
                "UPDATE entities SET properties = ?, updated_at = ? WHERE id = ?",
                (props_json, now, entity_id)
            )
        
        self.conn.commit()
        
        return {"success": True, "message": f"實體已更新: {entity_id}"}

    def delete(self, entity_id: str) -> Dict:
        """刪除實體（會連帶刪除別名和關係）"""
        entity = self.get(entity_id)
        if not entity:
            return {"success": False, "message": f"實體不存在: {entity_id}"}
        
        # 刪除實體（CASCADE 會自動刪除別名、關係、記憶關聯）
        self.conn.execute("DELETE FROM entities WHERE id = ?", (entity_id,))
        self.conn.commit()
        
        return {"success": True, "message": f"實體已刪除: {entity_id}"}

    def list(
        self,
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """列出實體"""
        if entity_type:
            cursor = self.conn.execute("""
                SELECT id, type, canonical_name, properties, created_at
                FROM entities
                WHERE type = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (entity_type, limit))
        else:
            cursor = self.conn.execute("""
                SELECT id, type, canonical_name, properties, created_at
                FROM entities
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        results = []
        for row in cursor:
            results.append({
                "id": row["id"],
                "type": row["type"],
                "name": row["canonical_name"],
                "properties": json.loads(row["properties"]) if row["properties"] else {},
                "created_at": row["created_at"]
            })
        
        return results

    def add_alias(
        self,
        entity_id: str,
        alias: str,
        confidence: float = 1.0,
        source: str = "user_confirmed"
    ) -> Dict:
        """新增別名"""
        entity = self.get(entity_id)
        if not entity:
            return {"success": False, "message": f"實體不存在: {entity_id}"}
        
        # 檢查別名是否已存在
        cursor = self.conn.execute(
            "SELECT entity_id FROM aliases WHERE alias = ?", (alias,)
        )
        existing = cursor.fetchone()
        if existing:
            if existing["entity_id"] == entity_id:
                return {"success": False, "message": f"別名已存在: {alias}"}
            else:
                return {
                    "success": False,
                    "message": f"別名已被使用於: {existing['entity_id']}"
                }
        
        self.conn.execute("""
            INSERT INTO aliases (alias, entity_id, confidence, source)
            VALUES (?, ?, ?, ?)
        """, (alias, entity_id, confidence, source))
        self.conn.commit()
        
        return {"success": True, "message": f"已新增別名: {alias} → {entity_id}"}

    def remove_alias(self, alias: str) -> Dict:
        """移除別名"""
        cursor = self.conn.execute(
            "SELECT entity_id, source FROM aliases WHERE alias = ?", (alias,)
        )
        row = cursor.fetchone()
        
        if not row:
            return {"success": False, "message": f"別名不存在: {alias}"}
        
        if row["source"] == "system":
            return {"success": False, "message": "無法刪除系統別名（正式名稱）"}
        
        self.conn.execute("DELETE FROM aliases WHERE alias = ?", (alias,))
        self.conn.commit()
        
        return {"success": True, "message": f"已移除別名: {alias}"}

    def resolve(self, name: str) -> Optional[Dict]:
        """
        解析名稱，找到對應的實體
        
        Args:
            name: 要解析的名稱
        
        Returns:
            匹配的實體，或 None
        """
        # 精確匹配別名
        cursor = self.conn.execute("""
            SELECT e.*, a.confidence, a.alias
            FROM entities e
            JOIN aliases a ON e.id = a.entity_id
            WHERE a.alias = ?
            ORDER BY a.confidence DESC
            LIMIT 1
        """, (name,))
        row = cursor.fetchone()
        
        if row:
            return {
                "id": row["id"],
                "type": row["type"],
                "name": row["canonical_name"],
                "matched_alias": row["alias"],
                "confidence": row["confidence"]
            }
        
        return None

    def search(self, query: str, entity_type: Optional[str] = None) -> List[Dict]:
        """
        搜尋實體（模糊匹配）
        
        Args:
            query: 搜尋關鍵字
            entity_type: 類型過濾
        """
        pattern = f"%{query}%"
        
        if entity_type:
            cursor = self.conn.execute("""
                SELECT DISTINCT e.id, e.type, e.canonical_name, a.alias, a.confidence
                FROM entities e
                LEFT JOIN aliases a ON e.id = a.entity_id
                WHERE e.type = ? AND (e.canonical_name LIKE ? OR a.alias LIKE ?)
                ORDER BY a.confidence DESC
            """, (entity_type, pattern, pattern))
        else:
            cursor = self.conn.execute("""
                SELECT DISTINCT e.id, e.type, e.canonical_name, a.alias, a.confidence
                FROM entities e
                LEFT JOIN aliases a ON e.id = a.entity_id
                WHERE e.canonical_name LIKE ? OR a.alias LIKE ?
                ORDER BY a.confidence DESC
            """, (pattern, pattern))
        
        results = []
        seen = set()
        for row in cursor:
            if row["id"] not in seen:
                results.append({
                    "id": row["id"],
                    "type": row["type"],
                    "name": row["canonical_name"],
                    "matched_alias": row["alias"] if row["alias"] != row["canonical_name"] else None
                })
                seen.add(row["id"])
        
        return results

    def merge(self, source_id: str, target_id: str) -> Dict:
        """
        合併兩個實體（把 source 合併到 target）
        
        Args:
            source_id: 來源實體（將被刪除）
            target_id: 目標實體（將保留）
        """
        source = self.get(source_id)
        target = self.get(target_id)
        
        if not source:
            return {"success": False, "message": f"來源實體不存在: {source_id}"}
        if not target:
            return {"success": False, "message": f"目標實體不存在: {target_id}"}
        
        # 轉移別名
        self.conn.execute("""
            UPDATE aliases SET entity_id = ? WHERE entity_id = ?
        """, (target_id, source_id))
        
        # 轉移關係（from）
        self.conn.execute("""
            UPDATE relations SET from_id = ? WHERE from_id = ?
        """, (target_id, source_id))
        
        # 轉移關係（to）
        self.conn.execute("""
            UPDATE relations SET to_id = ? WHERE to_id = ?
        """, (target_id, source_id))
        
        # 轉移記憶關聯
        self.conn.execute("""
            UPDATE OR IGNORE memory_entities SET entity_id = ? WHERE entity_id = ?
        """, (target_id, source_id))
        
        # 刪除來源實體
        self.conn.execute("DELETE FROM entities WHERE id = ?", (source_id,))
        
        self.conn.commit()
        
        return {
            "success": True,
            "message": f"已合併 {source_id} → {target_id}",
            "merged_aliases": len(source.get("aliases", [])),
            "merged_relations": len(source.get("outgoing_relations", [])) + len(source.get("incoming_relations", []))
        }

    def get_stats(self) -> Dict:
        """取得實體統計"""
        cursor = self.conn.execute("""
            SELECT type, COUNT(*) as count
            FROM entities
            GROUP BY type
        """)
        
        type_counts = {}
        total = 0
        for row in cursor:
            type_counts[row["type"]] = row["count"]
            total += row["count"]
        
        alias_cursor = self.conn.execute("SELECT COUNT(*) as count FROM aliases")
        alias_count = alias_cursor.fetchone()["count"]
        
        relation_cursor = self.conn.execute("SELECT COUNT(*) as count FROM relations")
        relation_count = relation_cursor.fetchone()["count"]
        
        return {
            "total_entities": total,
            "by_type": type_counts,
            "total_aliases": alias_count,
            "total_relations": relation_count
        }
