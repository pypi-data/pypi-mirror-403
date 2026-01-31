"""
實體解析器
處理名稱解析和待確認佇列
"""
from datetime import datetime
from typing import Dict, List, Optional

from .entity_manager import EntityManager


class EntityResolver:
    """實體解析和確認佇列管理"""

    def __init__(self, conn, entity_manager: EntityManager):
        """
        Args:
            conn: SQLite 連線
            entity_manager: EntityManager 實例
        """
        self.conn = conn
        self.entity_manager = entity_manager

    def add_pending(
        self,
        extracted_name: str,
        memory_id: str = None,
        suggested_entity_id: str = None,
        suggested_type: str = None,
        context: str = None,
        confidence: float = 0.5
    ) -> Dict:
        """
        新增待確認項目
        
        Args:
            extracted_name: 從記憶中抽取的名稱
            memory_id: 來源記憶 ID
            suggested_entity_id: 建議的實體 ID（如果有匹配）
            suggested_type: 建議的實體類型
            context: 上下文（用於判斷）
            confidence: 信心度
        
        Returns:
            新增結果
        """
        now = datetime.now().isoformat()
        
        cursor = self.conn.execute("""
            INSERT INTO pending_confirmations 
            (memory_id, extracted_name, suggested_entity_id, suggested_type, context, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (memory_id, extracted_name, suggested_entity_id, suggested_type, context, confidence, now))
        
        self.conn.commit()
        
        return {
            "success": True,
            "id": cursor.lastrowid,
            "extracted_name": extracted_name,
            "suggested_entity_id": suggested_entity_id
        }

    def get_pending(self, limit: int = 50) -> List[Dict]:
        """取得待確認項目列表"""
        cursor = self.conn.execute("""
            SELECT p.*, e.canonical_name as suggested_name
            FROM pending_confirmations p
            LEFT JOIN entities e ON p.suggested_entity_id = e.id
            WHERE p.status = 'pending'
            ORDER BY p.created_at DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor:
            results.append({
                "id": row["id"],
                "memory_id": row["memory_id"],
                "extracted_name": row["extracted_name"],
                "suggested_entity_id": row["suggested_entity_id"],
                "suggested_name": row["suggested_name"],
                "suggested_type": row["suggested_type"],
                "context": row["context"],
                "confidence": row["confidence"],
                "created_at": row["created_at"]
            })
        
        return results

    def confirm(
        self,
        pending_id: int,
        entity_id: str = None,
        create_new: bool = False,
        new_entity_type: str = None,
        new_entity_name: str = None,
        add_alias: bool = True
    ) -> Dict:
        """
        確認待確認項目
        
        Args:
            pending_id: 待確認項目 ID
            entity_id: 確認的實體 ID（如果選擇現有實體）
            create_new: 是否建立新實體
            new_entity_type: 新實體類型
            new_entity_name: 新實體名稱
            add_alias: 是否將抽取名稱加為別名
        
        Returns:
            確認結果
        """
        # 取得待確認項目
        cursor = self.conn.execute(
            "SELECT * FROM pending_confirmations WHERE id = ?", (pending_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return {"success": False, "message": f"待確認項目不存在: {pending_id}"}
        
        if row["status"] != "pending":
            return {"success": False, "message": f"項目已處理: {row['status']}"}
        
        extracted_name = row["extracted_name"]
        memory_id = row["memory_id"]
        
        # 建立新實體或使用現有實體
        if create_new:
            if not new_entity_type or not new_entity_name:
                return {"success": False, "message": "建立新實體需要提供類型和名稱"}
            
            result = self.entity_manager.create(
                entity_type=new_entity_type,
                name=new_entity_name,
                aliases=[extracted_name] if extracted_name != new_entity_name else None
            )
            
            if not result.get("success"):
                return result
            
            entity_id = result["id"]
        elif entity_id:
            # 使用現有實體，加入別名
            if add_alias:
                self.entity_manager.add_alias(entity_id, extracted_name, confidence=1.0)
        else:
            return {"success": False, "message": "需要指定實體 ID 或建立新實體"}
        
        # 關聯記憶和實體
        if memory_id and entity_id:
            try:
                self.conn.execute("""
                    INSERT OR IGNORE INTO memory_entities (memory_id, entity_id, relation)
                    VALUES (?, ?, 'mentions')
                """, (memory_id, entity_id))
            except Exception:
                pass
        
        # 更新狀態
        now = datetime.now().isoformat()
        self.conn.execute("""
            UPDATE pending_confirmations 
            SET status = 'confirmed', resolved_at = ?
            WHERE id = ?
        """, (now, pending_id))
        
        self.conn.commit()
        
        return {
            "success": True,
            "message": f"已確認: {extracted_name} → {entity_id}",
            "entity_id": entity_id
        }

    def reject(self, pending_id: int) -> Dict:
        """
        拒絕待確認項目（跳過不處理）
        
        Args:
            pending_id: 待確認項目 ID
        """
        cursor = self.conn.execute(
            "SELECT status FROM pending_confirmations WHERE id = ?", (pending_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return {"success": False, "message": f"待確認項目不存在: {pending_id}"}
        
        if row["status"] != "pending":
            return {"success": False, "message": f"項目已處理: {row['status']}"}
        
        now = datetime.now().isoformat()
        self.conn.execute("""
            UPDATE pending_confirmations 
            SET status = 'rejected', resolved_at = ?
            WHERE id = ?
        """, (now, pending_id))
        
        self.conn.commit()
        
        return {"success": True, "message": f"已拒絕: {pending_id}"}

    def auto_resolve(self, extracted_name: str, memory_id: str = None, context: str = None) -> Dict:
        """
        自動解析名稱
        
        Args:
            extracted_name: 抽取的名稱
            memory_id: 記憶 ID
            context: 上下文
        
        Returns:
            解析結果（可能是自動匹配、建議、或新增待確認）
        """
        # 嘗試精確匹配
        entity = self.entity_manager.resolve(extracted_name)
        
        if entity and entity.get("confidence", 0) >= 0.9:
            # 高信心度，自動關聯
            if memory_id:
                try:
                    self.conn.execute("""
                        INSERT OR IGNORE INTO memory_entities (memory_id, entity_id, relation)
                        VALUES (?, ?, 'mentions')
                    """, (memory_id, entity["id"]))
                    self.conn.commit()
                except Exception:
                    pass
            
            return {
                "action": "auto_linked",
                "entity_id": entity["id"],
                "entity_name": entity["name"],
                "confidence": entity["confidence"]
            }
        
        # 嘗試模糊搜尋
        candidates = self.entity_manager.search(extracted_name)
        
        if len(candidates) == 1:
            # 只有一個候選，中等信心度
            candidate = candidates[0]
            self.add_pending(
                extracted_name=extracted_name,
                memory_id=memory_id,
                suggested_entity_id=candidate["id"],
                suggested_type=candidate["type"],
                context=context,
                confidence=0.7
            )
            
            return {
                "action": "pending_confirmation",
                "suggested_entity_id": candidate["id"],
                "suggested_name": candidate["name"],
                "confidence": 0.7
            }
        
        elif len(candidates) > 1:
            # 多個候選，需要用戶選擇
            self.add_pending(
                extracted_name=extracted_name,
                memory_id=memory_id,
                context=context,
                confidence=0.3
            )
            
            return {
                "action": "pending_confirmation",
                "candidates": candidates[:5],
                "confidence": 0.3
            }
        
        else:
            # 沒有候選，可能是新實體
            self.add_pending(
                extracted_name=extracted_name,
                memory_id=memory_id,
                context=context,
                confidence=0.1
            )
            
            return {
                "action": "pending_new_entity",
                "extracted_name": extracted_name,
                "confidence": 0.1
            }

    def get_stats(self) -> Dict:
        """取得待確認統計"""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected
            FROM pending_confirmations
        """)
        row = cursor.fetchone()
        
        return {
            "total": row["total"],
            "pending": row["pending"],
            "confirmed": row["confirmed"],
            "rejected": row["rejected"]
        }
