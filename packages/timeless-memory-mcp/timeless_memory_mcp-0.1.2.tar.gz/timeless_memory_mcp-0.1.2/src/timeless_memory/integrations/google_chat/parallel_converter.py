"""
Google Chat 訊息轉換器 - 並行版本
支援多 Space 並行轉換，大幅提升處理速度
"""
import json
import hashlib
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed


def _log(msg: str):
    """輸出到 stderr（避免干擾 MCP stdio 通訊）"""
    print(msg, file=sys.stderr)


class ParallelChatConverter:
    """Google Chat 並行轉換器"""
    
    def __init__(
        self,
        sources_dir: Path,
        data_dir: Path,
        min_messages: int = 1
    ):
        self.sources_dir = Path(sources_dir)
        self.data_dir = Path(data_dir)
        self.min_messages = min_messages
        self.sync_state_file = data_dir.parent / ".google-chat-sync.json"
        
        # 線程安全鎖
        self.print_lock = threading.Lock()
        self.state_lock = threading.Lock()
    
    def convert(
        self, 
        space_name: Optional[str] = None,
        max_workers: int = 5
    ) -> Dict:
        """
        並行轉換 JSONL 為 Markdown 記憶
        
        Args:
            space_name: 指定 Space 名稱（None 則轉換全部）
            max_workers: 並行轉換的線程數（預設 5）
        """
        if not self.sources_dir.exists():
            return {"success": False, "message": f"找不到來源目錄: {self.sources_dir}"}
        
        with self.print_lock:
            _log(f"\n{'='*60}")
            _log(f"📂 來源目錄: {self.sources_dir}")
            _log(f"📁 輸出目錄: {self.data_dir}")
            _log(f"🚀 並行數: {max_workers} 個線程")
            _log(f"{'='*60}\n")
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        sync_state = self._load_sync_state()
        if sync_state.get("last_sync"):
            with self.print_lock:
                _log(f"📅 上次同步: {sync_state['last_sync']}\n")
        
        # 收集要處理的 Space 目錄
        space_dirs = []
        for space_dir in sorted(self.sources_dir.iterdir()):
            if not space_dir.is_dir():
                continue
            if space_dir.name.startswith("."):
                continue
            if space_dir.name in ["token.json", "credentials.json", "all_spaces.json"]:
                continue
            
            # 過濾指定 Space
            if space_name:
                dir_name = self._extract_space_name(space_dir)
                if dir_name != space_name:
                    continue
            
            space_dirs.append(space_dir)
        
        if not space_dirs:
            return {"success": False, "message": "沒有找到要處理的 Space"}
        
        # 並行轉換
        stats = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任務
            future_to_space = {
                executor.submit(self._convert_space_safe, space_dir, sync_state): space_dir
                for space_dir in space_dirs
            }
            
            # 收集結果
            for future in as_completed(future_to_space):
                space_dir = future_to_space[future]
                try:
                    result = future.result()
                    stats.append(result)
                except Exception as e:
                    with self.print_lock:
                        _log(f"❌ 轉換失敗 {space_dir.name}: {e}")
                    stats.append({
                        "space": space_dir.name,
                        "total": 0,
                        "kept": 0,
                        "new": 0,
                        "messages": 0
                    })
        
        self._save_sync_state(sync_state)
        
        # 收集所有新檔案
        all_new_files = []
        space_files = {}
        for s in stats:
            new_files = s.get("new_files", [])
            if new_files:
                all_new_files.extend(new_files)
                space_files[s["space"]] = {
                    "count": len(new_files),
                    "dir": s.get("output_dir"),
                    "files": [f.name if hasattr(f, 'name') else str(f).split('/')[-1] for f in new_files]
                }
        
        # 統計
        with self.print_lock:
            _log(f"\n{'='*60}")
            _log("📊 轉換完成\n")
            
            total_messages = sum(s.get("total_messages", 0) for s in stats)
            total_days = sum(s.get("total_days", 0) for s in stats)
            total_new = sum(s.get("new_days", 0) for s in stats)
            
            _log(f"   總訊息數: {total_messages:,}")
            _log(f"   總天數: {total_days:,}")
            _log(f"   ✅ 新增天數: {total_new:,}\n")
            
            # 按聊天室顯示新增檔案
            if space_files:
                _log("📝 新增檔案:\n")
                for spc_name, info in space_files.items():
                    _log(f"   {spc_name}: {info['count']} 個檔案")
                    _log(f"   目錄: {info['dir']}")
                    for fname in info['files']:
                        _log(f"      - {fname}")
                    _log("")
        
        return {
            "success": True,
            "total_messages": total_messages,
            "total_days": total_days,
            "new_days": total_new,
            "new_memories": total_new,
            "updated_memories": 0,
            "output_dir": str(self.data_dir),
            "new_files": all_new_files,
            "updated_files": [],
            "space_files": space_files
        }
    
    def _convert_space_safe(self, space_dir: Path, sync_state: Dict) -> Dict:
        """線程安全的 Space 轉換"""
        from .converter import ChatConverter
        
        # 建立獨立的轉換器實例（避免共享狀態）
        # ChatConverter 只接受 (sources_dir, data_dir, min_messages)
        converter = ChatConverter(
            self.sources_dir,
            self.data_dir,
            self.min_messages
        )
        
        # 執行轉換（使用 print_lock 保護輸出）
        result = converter.convert_space(space_dir, sync_state)
        
        # 線程安全地更新 sync_state
        if result.get("new", 0) > 0:
            space_id = space_dir.name.split("_")[-1] if "_" in space_dir.name else space_dir.name
            with self.state_lock:
                if "spaces" not in sync_state:
                    sync_state["spaces"] = {}
                # 合併狀態更新
                if space_id in sync_state["spaces"]:
                    sync_state["spaces"][space_id].update({
                        "last_conversion": datetime.now().isoformat()
                    })
        
        return result
    
    def _extract_space_name(self, space_dir: Path) -> str:
        """從目錄名稱提取 Space 名稱"""
        name = space_dir.name
        if "_" in name:
            return name.rsplit("_", 1)[0]
        return name
    
    def _load_sync_state(self) -> Dict:
        """載入同步狀態"""
        if self.sync_state_file.exists():
            with open(self.sync_state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"spaces": {}, "last_sync": None}
    
    def _save_sync_state(self, state: Dict):
        """儲存同步狀態"""
        self.sync_state_file.parent.mkdir(parents=True, exist_ok=True)
        state["last_sync"] = datetime.now().isoformat()
        with open(self.sync_state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
