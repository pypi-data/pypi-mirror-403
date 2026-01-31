"""
Google Chat 訊息轉換器 - 轉換 JSONL 為 Markdown 記憶（以天為單位）
"""
import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional, Set


def _log(msg: str):
    """輸出到 stderr（避免干擾 MCP stdio 通訊）"""
    print(msg, file=sys.stderr)


class ChatConverter:
    """Google Chat 訊息轉換器 - 以天為單位聚合對話"""
    
    def __init__(
        self,
        sources_dir: Path,
        data_dir: Path,
        min_messages: int = 1
    ):
        """
        Args:
            sources_dir: sources/google-chat/ 目錄（JSONL 原始資料）
            data_dir: data/google-chat/ 目錄（MD 記憶檔案）
            min_messages: 最少訊息數（天）
        """
        self.sources_dir = Path(sources_dir)
        self.data_dir = Path(data_dir)
        self.min_messages = min_messages
        self.sync_state_file = data_dir.parent / ".google-chat-sync.json"
    
    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """解析 ISO 時間字串"""
        if not time_str:
            return None
        try:
            time_str = time_str.replace("Z", "+00:00")
            if "." in time_str:
                base, rest = time_str.rsplit(".", 1)
                tz_idx = -1
                for i, c in enumerate(rest):
                    if c in "+-":
                        tz_idx = i
                        break
                if tz_idx > 0:
                    microsec = rest[:tz_idx][:6].ljust(6, "0")
                    tz = rest[tz_idx:]
                    time_str = f"{base}.{microsec}{tz}"
            return datetime.fromisoformat(time_str)
        except Exception:
            return None
    
    def _load_messages_by_day(self, space_dir: Path) -> Dict[str, List[Dict]]:
        """載入 Space 的訊息，按天分組"""
        messages_by_day = defaultdict(list)
        
        for jsonl_file in space_dir.glob("*.jsonl"):
            # JSONL 檔名格式: YYYY-MM-DD.jsonl
            date_str = jsonl_file.stem
            
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        msg = json.loads(line.strip())
                        dt = self._parse_time(msg.get("createTime", ""))
                        if dt:
                            msg["_dt"] = dt
                            msg["_date"] = date_str
                            messages_by_day[date_str].append(msg)
                    except Exception:
                        pass
        
        # 排序每天的訊息
        for date_str in messages_by_day:
            messages_by_day[date_str].sort(key=lambda x: x.get("_dt", datetime.min))
        
        return messages_by_day
    
    def _should_keep_day(self, messages: List[Dict]) -> bool:
        """判斷這一天的對話是否應該保留"""
        if len(messages) < self.min_messages:
            return False
        return True
    
    def _extract_participants(self, messages: List[Dict]) -> List[str]:
        """提取參與者（優先使用 displayName）"""
        participants = set()
        for msg in messages:
            sender = msg.get("sender", {})
            # 優先使用 displayName
            name = sender.get("displayName")
            if not name:
                # fallback 到 name，並簡化 ID
                name = sender.get("name", "")
                if name.startswith("users/"):
                    name = name.split("/")[-1][:8]
            if name:
                participants.add(name)
        return sorted(participants)
    
    def _generate_title(self, date_str: str, space_name: str) -> str:
        """生成標題"""
        return f"{space_name} - {date_str}"
    
    def _format_conversation(self, messages: List[Dict]) -> str:
        """格式化對話內容（完整日期時間 + displayName）"""
        lines = []
        
        for msg in messages:
            dt = msg.get("_dt")
            time_str = dt.strftime("%Y-%m-%d %H:%M") if dt else "?"
            
            sender = msg.get("sender", {})
            # 優先使用 displayName
            name = sender.get("displayName")
            if not name:
                name = sender.get("name", "")
                if name.startswith("users/"):
                    name = name.split("/")[-1][:8]
            
            text = msg.get("text", "") or ""
            lines.append(f"[{time_str}] {name}: {text}")
        
        return "\n".join(lines)
    
    def _generate_memory_id(self, date_str: str, space_name: str) -> str:
        """生成記憶 ID（基於日期和 space_name）"""
        content = f"{space_name}-{date_str}"
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:12]
        return f"daily-{date_str}-{hash_val}"
    
    def _convert_to_markdown(self, date_str: str, messages: List[Dict], space_name: str, space_id: str) -> str:
        """轉換為 Markdown 格式（以天為單位）"""
        participants = self._extract_participants(messages)
        title = self._generate_title(date_str, space_name)
        content = self._format_conversation(messages)
        memory_id = self._generate_memory_id(date_str, space_name)
        
        total_chars = sum(len(m.get("text", "") or "") for m in messages)
        
        tags = ["工作對話", space_name]
        
        yaml_lines = [
            "---",
            f"id: {memory_id}",
            f"title: \"{title}\"",
            f"speaker: external",
            f"authority: 5",
            f"quality: 4",
            f"date: \"{date_str}\"",
            f"space_name: \"{space_name}\"",
            f"space_id: \"{space_id}\"",
            f"participants: {json.dumps(participants, ensure_ascii=False)}",
            f"message_count: {len(messages)}",
            f"total_chars: {total_chars}",
            f"tags:",
        ]
        for tag in tags:
            yaml_lines.append(f"  - {tag}")
        yaml_lines.extend([
            f"source_type: google_chat",
            "# 預留欄位（未來可由 LLM 填入）",
            "summary: null",
            "keywords: []",
            "---",
            "",
        ])
        
        body_lines = [
            f"# {title}",
            "",
            f"**參與者**: {', '.join(participants)}",
            f"**訊息數**: {len(messages)}",
            f"**總字數**: {total_chars}",
            "",
            "---",
            "",
            "## 對話內容",
            "",
            "```",
            content,
            "```",
        ]
        
        return "\n".join(yaml_lines + body_lines)
    
    def _extract_space_name(self, space_dir: Path) -> str:
        """從目錄名稱提取 Space 名稱"""
        name = space_dir.name
        if "_" in name:
            return name.rsplit("_", 1)[0]
        return name
    
    def _get_existing_dates(self, space_output_dir: Path) -> Set[str]:
        """取得已存在的日期"""
        existing = set()
        if space_output_dir.exists():
            for md_file in space_output_dir.glob("daily-*.md"):
                # 檔名格式: daily-{space_name}-{YYYY-MM-DD}.md
                parts = md_file.stem.split("-")
                if len(parts) >= 4:
                    date_str = f"{parts[-3]}-{parts[-2]}-{parts[-1]}"
                    existing.add(date_str)
        return existing
    
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
    
    def convert_space(self, space_dir: Path, sync_state: Dict) -> Dict:
        """轉換單一 Space（以天為單位）"""
        space_id = space_dir.name.split("_")[-1] if "_" in space_dir.name else space_dir.name
        space_name = self._extract_space_name(space_dir)
        
        output_dir = self.data_dir / space_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        existing_dates = self._get_existing_dates(output_dir)
        
        _log(f"  處理: {space_name}")
        if existing_dates:
            _log(f"    已有 {len(existing_dates)} 天的記憶")
        
        # 載入訊息（按天分組）
        messages_by_day = self._load_messages_by_day(space_dir)
        if not messages_by_day:
            return {
                "space": space_name,
                "total_days": 0,
                "new_days": 0,
                "total_messages": 0,
                "new_files": [],
                "output_dir": str(output_dir)
            }
        
        # 轉換並儲存
        new_count = 0
        total_messages = 0
        latest_date = None
        new_files = []  # 收集新建立的檔案路徑
        
        for date_str in sorted(messages_by_day.keys()):
            messages = messages_by_day[date_str]
            total_messages += len(messages)
            
            # 跳過已存在的日期
            if date_str in existing_dates:
                continue
            
            # 判斷是否保留
            if not self._should_keep_day(messages):
                continue
            
            # 轉換為 Markdown
            md_content = self._convert_to_markdown(date_str, messages, space_name, space_id)
            
            # 檔名格式: daily-{space_name}-{YYYY-MM-DD}.md
            safe_space_name = space_name.replace(" ", "_").replace("/", "-")[:30]
            filename = f"daily-{safe_space_name}-{date_str}.md"
            file_path = output_dir / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            
            new_files.append(str(file_path))
            new_count += 1
            if latest_date is None or date_str > latest_date:
                latest_date = date_str
        
        # 更新同步狀態
        if latest_date:
            if "spaces" not in sync_state:
                sync_state["spaces"] = {}
            sync_state["spaces"][space_id] = {
                "space_name": space_name,
                "latest_date": latest_date,
                "total_days": len(existing_dates) + new_count
            }
        
        if new_count > 0:
            _log(f"    ✅ 新增 {new_count} 天的記憶")
        
        return {
            "space": space_name,
            "total_days": len(messages_by_day),
            "new_days": new_count,
            "total_messages": total_messages,
            "new_files": new_files,
            "output_dir": str(output_dir)
        }
    
    def convert(self, space_name: Optional[str] = None) -> Dict:
        """
        轉換 JSONL 為 Markdown 記憶
        
        Args:
            space_name: 指定 Space 名稱（None 則轉換全部）
        """
        if not self.sources_dir.exists():
            return {"success": False, "message": f"找不到來源目錄: {self.sources_dir}"}
        
        _log(f"\n{'='*60}")
        _log(f"📂 來源目錄: {self.sources_dir}")
        _log(f"📁 輸出目錄: {self.data_dir}")
        _log(f"📅 轉換單位: 以天為單位")
        _log(f"{'='*60}\n")
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        sync_state = self._load_sync_state()
        if sync_state.get("last_sync"):
            _log(f"📅 上次同步: {sync_state['last_sync']}\n")
        
        # 處理每個 Space
        stats = []
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
            
            result = self.convert_space(space_dir, sync_state)
            stats.append(result)
        
        self._save_sync_state(sync_state)
        
        # 收集所有新檔案並按聊天室分組
        all_new_files = []
        space_files = {}
        for s in stats:
            spc_name = s["space"]
            new_files = s.get("new_files", [])
            if new_files:
                all_new_files.extend(new_files)
                space_files[spc_name] = {
                    "count": len(new_files),
                    "dir": s.get("output_dir"),
                    "files": [f.name for f in new_files]
                }
        
        # 統計
        _log(f"\n{'='*60}")
        _log("📊 轉換完成\n")
        
        total_messages = sum(s["total_messages"] for s in stats)
        total_days = sum(s["total_days"] for s in stats)
        total_new = sum(s["new_days"] for s in stats)
        
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
