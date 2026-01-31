"""
Google Chat 下載器 - 整合並行下載功能
"""
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict
from googleapiclient.errors import HttpError

from .auth import ChatAuthManager

# 台灣時區 UTC+8
TW_TZ = timezone(timedelta(hours=8))

# 線程安全的輸出鎖
print_lock = threading.Lock()


def _log(msg: str):
    """輸出到 stderr（避免干擾 MCP stdio 通訊）"""
    print(msg, file=sys.stderr)


class ChatReader:
    """Google Chat 訊息讀取器"""
    
    def __init__(self, auth_manager: ChatAuthManager):
        self.service = auth_manager.get_chat_service()
    
    def list_spaces(self, page_size: int = 1000) -> List[Dict]:
        """列出所有可存取的 Chat Spaces"""
        try:
            all_spaces = []
            page_token = None
            
            while True:
                params = {"pageSize": min(page_size, 1000)}
                if page_token:
                    params["pageToken"] = page_token
                
                response = self.service.spaces().list(**params).execute()
                spaces = response.get("spaces", [])
                all_spaces.extend(spaces)
                
                page_token = response.get("nextPageToken")
                if not page_token:
                    break
            
            return all_spaces
        except HttpError as e:
            return []
    
    def list_messages(
        self,
        space_id: str,
        page_size: int = 1000,
        page_token: Optional[str] = None,
        filter_query: Optional[str] = None
    ) -> Dict:
        """列出指定 Space 的訊息"""
        try:
            space_name = f"spaces/{space_id}"
            params = {
                "parent": space_name,
                "pageSize": min(page_size, 1000)
            }
            
            if page_token:
                params["pageToken"] = page_token
            if filter_query:
                params["filter"] = filter_query
            
            response = self.service.spaces().messages().list(**params).execute()
            return response
        except HttpError as e:
            return {"messages": [], "nextPageToken": None}
    
    def get_all_messages(
        self,
        space_id: str,
        filter_query: Optional[str] = None,
        quiet: bool = False
    ) -> List[Dict]:
        """取得指定 Space 的所有訊息（自動處理分頁）"""
        all_messages = []
        page_token = None
        
        if not quiet:
            with print_lock:
                _log(f"    開始讀取訊息...")
        
        while True:
            response = self.list_messages(
                space_id=space_id,
                page_token=page_token,
                filter_query=filter_query
            )
            
            messages = response.get("messages", [])
            all_messages.extend(messages)
            
            if not quiet:
                with print_lock:
                    _log(f"    已讀取 {len(all_messages)} 則訊息...")
            
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        
        if not quiet:
            with print_lock:
                _log(f"    完成！共讀取 {len(all_messages)} 則訊息")
        
        return all_messages
    
    def _sanitize_folder_name(self, name: str) -> str:
        """清理資料夾名稱"""
        import re
        unsafe_chars = r'[<>:"/\\|?*]'
        name = re.sub(unsafe_chars, '_', name)
        name = name.strip(' .')
        return name[:100] if len(name) > 100 else name
    
    def _parse_create_time_to_tw(self, create_time_str: str) -> datetime:
        """將 API 的 createTime (UTC) 轉換為台灣時間"""
        try:
            if create_time_str.endswith('Z'):
                create_time_str = create_time_str[:-1]
            dt_utc = datetime.fromisoformat(create_time_str).replace(tzinfo=timezone.utc)
            return dt_utc.astimezone(TW_TZ)
        except Exception:
            return datetime.now(TW_TZ)
    
    def export_to_jsonl(
        self,
        messages: List[Dict],
        space_id: str,
        output_dir: Path,
        space_name: str = None,
        append: bool = False
    ) -> List[Path]:
        """將訊息匯出為 JSONL 檔案，按日期分檔"""
        if space_name:
            safe_name = self._sanitize_folder_name(space_name)
            folder_name = f"{safe_name}_{space_id}"
        else:
            folder_name = f"未命名_{space_id}"
        
        space_dir = output_dir / folder_name
        space_dir.mkdir(parents=True, exist_ok=True)
        
        # 按日期分組訊息
        messages_by_date = defaultdict(list)
        for message in messages:
            create_time = message.get("createTime", "")
            tw_time = self._parse_create_time_to_tw(create_time)
            date_str = tw_time.strftime("%Y-%m-%d")
            messages_by_date[date_str].append(message)
        
        # 寫入各日期檔案
        output_files = []
        total_written = 0
        
        for date_str, day_messages in sorted(messages_by_date.items()):
            output_file = space_dir / f"{date_str}.jsonl"
            mode = "a" if append else "w"
            
            with open(output_file, mode, encoding="utf-8") as f:
                for message in day_messages:
                    f.write(json.dumps(message, ensure_ascii=False) + "\n")
            
            output_files.append(output_file)
            total_written += len(day_messages)
        
        return output_files


class ChatDownloader:
    """Google Chat 並行下載管理器"""
    
    def __init__(self, sources_dir: Path, auth_manager: ChatAuthManager):
        self.sources_dir = Path(sources_dir)
        self.auth_manager = auth_manager
        self.all_spaces_file = self.sources_dir / "all_spaces.json"
    
    def list_spaces(self, refresh: bool = False) -> List[Dict]:
        """
        列出所有 Spaces
        
        Args:
            refresh: 是否強制重新從 API 取得
        """
        # 如果快取存在且不強制刷新，使用快取
        if not refresh and self.all_spaces_file.exists():
            with open(self.all_spaces_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("spaces", [])
        
        # 從 API 取得
        reader = ChatReader(self.auth_manager)
        spaces = reader.list_spaces()
        
        # 轉換格式並儲存
        formatted_spaces = []
        for space in spaces:
            space_id = space.get("name", "").split("/")[-1]
            formatted_spaces.append({
                "space_id": space_id,
                "display_name": space.get("displayName", "未命名"),
                "type": space.get("spaceType", "UNKNOWN"),
                "raw_data": space
            })
        
        # 儲存快取
        with open(self.all_spaces_file, "w", encoding="utf-8") as f:
            json.dump({
                "spaces": formatted_spaces,
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        return formatted_spaces
    
    def _download_single_space(
        self,
        space_info: dict,
        incremental: bool,
        overlap_days: int,
        idx: int,
        total: int
    ) -> dict:
        """下載單一 Space 的訊息（線程安全）
        
        Args:
            space_info: Space 資訊
            incremental: 是否增量更新
            overlap_days: 增量更新時回溯天數（避免遺漏）
            idx: 當前索引
            total: 總數
        """
        space_id = space_info.get("space_id")
        display_name = space_info.get("display_name", "未命名")
        space_type = space_info.get("raw_data", {}).get("spaceType", "UNKNOWN")
        
        result = {
            "status": "success",
            "space_id": space_id,
            "display_name": display_name,
            "message_count": 0,
            "skipped": False,
            "error": None
        }
        
        try:
            reader = ChatReader(self.auth_manager)
            
            with print_lock:
                _log(f"\n[{idx}/{total}] {display_name}")
                _log(f"  Space ID: {space_id}")
                _log(f"  類型: {space_type}")
            
            # 增量更新邏輯（含 overlap 回溯）
            filter_query = None
            append = False
            
            if incremental:
                last_update = self._load_last_update_time(space_id)
                if last_update:
                    # 回溯 overlap_days 天，避免遺漏當天未完整下載的訊息
                    overlap_time = last_update - timedelta(days=overlap_days)
                    filter_query = f'createTime > "{overlap_time.isoformat()}Z"'
                    append = False  # 重寫 overlap 期間的檔案
                    with print_lock:
                        _log(f"  上次更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
                        if overlap_days > 0:
                            _log(f"  回溯 {overlap_days} 天至: {overlap_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 下載訊息
            messages = reader.get_all_messages(space_id, filter_query=filter_query, quiet=True)
            
            if messages:
                output_files = reader.export_to_jsonl(
                    messages,
                    space_id,
                    self.sources_dir,
                    space_name=display_name,
                    append=append
                )
                msg_count = len(messages)
                result["message_count"] = msg_count
                
                # 儲存更新時間
                self._save_last_update_time(space_id, datetime.now())
                
                action = "追加" if append else "寫入"
                with print_lock:
                    _log(f"  ✅ {action} {msg_count} 則訊息至 {len(output_files)} 個日期檔案")
            else:
                if incremental and append:
                    result["skipped"] = True
                    with print_lock:
                        _log(f"  ⏭️ 無新訊息，跳過")
                else:
                    with print_lock:
                        _log(f"  ⚠️ 沒有訊息")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            with print_lock:
                _log(f"  ❌ 失敗：{e}")
        
        return result
    
    def download(
        self,
        space_id: Optional[str] = None,
        skip_dm: bool = True,
        incremental: bool = True,
        max_workers: int = 5,
        overlap_days: int = 1
    ) -> Dict:
        """
        下載 Spaces 的訊息（支援並行）
        
        Args:
            space_id: 指定 Space ID（None 則下載全部）
            skip_dm: 是否跳過 DM
            incremental: 是否增量更新
            max_workers: 並行線程數
            overlap_days: 增量更新時回溯天數（預設 1 天，避免遺漏）
        """
        # 取得 Space 列表
        spaces = self.list_spaces()
        
        # 過濾 DM
        if skip_dm:
            spaces = [s for s in spaces if s.get("raw_data", {}).get("spaceType") != "DIRECT_MESSAGE"]
        
        # 過濾指定 Space
        if space_id:
            spaces = [s for s in spaces if s.get("space_id") == space_id]
            if not spaces:
                return {"success": False, "message": f"找不到 Space: {space_id}"}
        
        total = len(spaces)
        success = 0
        skipped = 0
        failed = []
        total_messages = 0
        
        mode_text = "增量更新" if incremental else "全量下載"
        _log(f"\n{'='*60}")
        _log(f"模式: {mode_text}")
        _log(f"並行數: {max_workers} 個線程")
        _log(f"開始處理 {total} 個 Space")
        _log(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        _log(f"{'='*60}\n")
        
        # 使用 ThreadPoolExecutor 並行處理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_space = {
                executor.submit(self._download_single_space, space_info, incremental, overlap_days, idx, total): space_info
                for idx, space_info in enumerate(spaces, 1)
            }
            
            for future in as_completed(future_to_space):
                result = future.result()
                
                if result["status"] == "success":
                    success += 1
                    total_messages += result["message_count"]
                    if result["skipped"]:
                        skipped += 1
                else:
                    failed.append({
                        "space_id": result["space_id"],
                        "display_name": result["display_name"],
                        "error": result["error"]
                    })
        
        # 統計報告
        _log(f"\n{'='*60}")
        _log(f"完成！")
        _log(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        _log(f"{'='*60}")
        _log(f"\n📊 統計:")
        _log(f"  成功: {success}/{total}")
        if incremental:
            _log(f"  跳過（無新訊息）: {skipped}")
        _log(f"  失敗: {len(failed)}")
        _log(f"  新訊息數: {total_messages}")
        _log(f"  儲存位置: {self.sources_dir}")
        
        return {
            "success": True,
            "total": total,
            "success_count": success,
            "skipped": skipped,
            "failed": failed,
            "total_messages": total_messages
        }
    
    def _get_last_update_file(self, space_id: str) -> Path:
        """取得上次更新時間的檔案路徑"""
        return self.sources_dir / f"last_update_{space_id}.json"
    
    def _load_last_update_time(self, space_id: str) -> Optional[datetime]:
        """載入上次更新時間"""
        state_file = self._get_last_update_file(space_id)
        if state_file.exists():
            with open(state_file, "r") as f:
                state = json.load(f)
                return datetime.fromisoformat(state["last_update_time"])
        return None
    
    def _save_last_update_time(self, space_id: str, update_time: datetime):
        """儲存上次更新時間"""
        state_file = self._get_last_update_file(space_id)
        with open(state_file, "w") as f:
            json.dump({
                "space_id": space_id,
                "last_update_time": update_time.isoformat()
            }, f, indent=2)
