"""
Google Chat 管理器 - 統一管理介面
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional

from timeless_memory import get_home

from .auth import ChatAuthManager
from .downloader import ChatDownloader
from .converter import ChatConverter
from .parallel_converter import ParallelChatConverter


def _log(msg: str):
    """輸出到 stderr（避免干擾 MCP stdio 通訊）"""
    print(msg, file=sys.stderr)


class ChatManager:
    """Google Chat 整合管理器"""
    
    def __init__(self, home_path: Optional[Path] = None):
        """
        Args:
            home_path: TIMELESS_HOME 路徑（None 則使用環境變數）
        """
        self.home = Path(home_path) if home_path else get_home()
        self.sources_dir = self.home / "sources" / "google-chat"
        self.data_dir = self.home / "data" / "google-chat"
        
        # 初始化子管理器
        self.auth_manager = ChatAuthManager(self.sources_dir)
        self.downloader = ChatDownloader(self.sources_dir, self.auth_manager)
        self.converter = ChatConverter(self.sources_dir, self.data_dir)
        self.parallel_converter = ParallelChatConverter(self.sources_dir, self.data_dir)
    
    def sync(
        self,
        space_id: Optional[str] = None,
        skip_dm: bool = True,
        max_workers: int = 5,
        full: bool = False,
        parallel: bool = True,
        overlap_days: int = 1
    ) -> Dict:
        """
        完整同步流程：下載 + 轉換 + 自動索引
        
        Args:
            space_id: 指定 Space ID（None 則處理全部）
            skip_dm: 是否跳過 DM
            max_workers: 並行線程數
            full: 是否全量下載（False 則增量更新）
            parallel: 是否使用並行轉換（預設 True）
            overlap_days: 增量下載時回溯天數（預設 1 天）
        
        Returns:
            dict: 同步結果（包含 agent_todos）
        """
        _log("\n" + "="*60)
        _log("🔄 開始 Google Chat 完整同步")
        _log("="*60)
        
        # 步驟 1: 下載（已經是並行）
        _log("\n📥 步驟 1/3: 下載訊息")
        download_result = self.download(
            space_id=space_id,
            skip_dm=skip_dm,
            incremental=not full,
            max_workers=max_workers,
            overlap_days=overlap_days
        )
        
        if not download_result.get("success"):
            return download_result
        
        # 步驟 2: 轉換（可選並行）
        _log("\n📝 步驟 2/3: 轉換為記憶")
        
        # 如果指定了 space_id，需要找到對應的 space_name
        space_name = None
        if space_id:
            spaces = self.downloader.list_spaces()
            for space in spaces:
                if space.get("space_id") == space_id:
                    space_name = space.get("display_name")
                    break
        
        # 選擇轉換器
        if parallel and not space_id:  # 多個 Space 才使用並行
            convert_result = self.parallel_converter.convert(
                space_name=space_name,
                max_workers=max_workers
            )
        else:
            convert_result = self.converter.convert(space_name=space_name)
        
        if not convert_result.get("success"):
            return convert_result
        
        # 步驟 3: 建立索引
        _log("\n🔍 步驟 3/3: 建立索引")
        
        # 優先使用增量索引（有 new_files 時）
        new_files = convert_result.get("new_files", [])
        new_memories = convert_result.get("new_memories", 0)
        
        if new_files:
            # 增量索引
            index_result = self._incremental_index(convert_result)
        elif new_memories > 0:
            # 沒有 new_files 但有新記憶，做完整重建索引
            _log("  ⚠️ 沒有新檔案列表，執行完整重建索引...")
            index_result = self._full_rebuild_index()
        else:
            # 沒有新記憶，跳過索引
            _log("  ⏭️ 無新記憶，跳過索引")
            index_result = {"success": True, "indexed_count": 0}
        
        # 合併結果
        _log("\n" + "="*60)
        _log("✅ 同步完成")
        _log("="*60)
        
        # 建立 Agent TODO 列表
        agent_todos = self._build_agent_todos(convert_result)
        
        # 顯示 TODO（console 輸出）
        self._print_agent_todos(agent_todos, convert_result)
        
        return {
            "success": True,
            "download": download_result,
            "convert": convert_result,
            "index": index_result,
            "message": f"同步完成：新增 {new_memories} 個記憶，索引 {index_result.get('indexed_count', 0)} 筆",
            "agent_todos": agent_todos
        }
    
    def _full_rebuild_index(self) -> Dict:
        """完整重建索引"""
        try:
            from timeless_memory.core import get_managers
            
            memory_manager, index_manager, _, _, _, _ = get_managers(quiet=True)
            
            _log("  重建完整索引...")
            index_manager.rebuild(memory_manager)
            stats = index_manager.get_stats()
            
            _log(f"  ✅ 完成重建，共 {stats.get('total_memories', 0)} 筆")
            
            return {
                "success": True,
                "indexed_count": stats.get("total_memories", 0),
                "method": "full_rebuild"
            }
        except Exception as e:
            _log(f"  ❌ 重建索引失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "indexed_count": 0
            }
    
    def _build_agent_todos(self, convert_result: Dict) -> List[Dict]:
        """建立 Agent TODO 列表"""
        from timeless_memory import get_home, get_index_dir
        
        todos = []
        home = get_home()
        index_dir = get_index_dir()
        data_dir = home / "data" / "google-chat"
        
        # TODO 1: 分析並建立知識圖譜
        todos.append({
            "id": 1,
            "task": "分析建立知識圖譜",
            "description": "從聊天記錄提取人物、專案資訊，建立實體和關聯",
            "steps": [
                "執行 chat(action='analyze') 分析聊天資料",
                "根據分析結果建立人物實體：entity(action='batch_create', entities=[...])",
                "建立專案實體：entity(action='batch_create', entities=[...])",
                "建立人物-專案關聯：relation(action='batch_create', relations=[...])"
            ],
            "priority": "high"
        })
        
        # TODO 2: 建立每月聊天室索引
        spaces = []
        if data_dir.exists():
            spaces = [d.name for d in data_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        
        chat_index_dir = index_dir / "聊天室"
        
        todos.append({
            "id": 2,
            "task": "建立每月聊天室索引",
            "description": f"為每個聊天室建立月度摘要索引檔案",
            "index_directory": str(chat_index_dir),
            "file_format": "monthly-summary-{聊天室名稱}-YYYY-MM.md",
            "spaces": spaces,
            "steps": [
                f"建立索引目錄: {chat_index_dir}",
                "對每個聊天室、每個月份：",
                "  - 讀取該月所有 daily-*.md 檔案",
                "  - 摘要重點討論內容",
                "  - 生成 monthly-summary-{space}-YYYY-MM.md"
            ],
            "priority": "medium"
        })
        
        return todos
    
    def _print_agent_todos(self, todos: List[Dict], convert_result: Dict):
        """輸出 Agent TODO 到 console"""
        from timeless_memory import get_index_dir
        
        _log("\n📋 Agent TODO（下一步工作）:\n")
        
        for todo in todos:
            _log(f"{todo['id']}️⃣ {todo['task']}:")
            _log(f"   {todo['description']}")
            
            if "steps" in todo:
                _log("   步驟:")
                for step in todo["steps"]:
                    _log(f"     - {step}")
            
            if "index_directory" in todo:
                _log(f"   索引目錄: {todo['index_directory']}")
            
            if "spaces" in todo and todo["spaces"]:
                _log(f"   聊天室: {', '.join(todo['spaces'][:5])}")
                if len(todo["spaces"]) > 5:
                    _log(f"           ... 還有 {len(todo['spaces']) - 5} 個")
            
            _log("")
    
    def _incremental_index(self, convert_result: Dict) -> Dict:
        """增量索引新轉換的記憶
        
        Args:
            convert_result: 轉換結果（包含新檔案列表）
        
        Returns:
            dict: 索引結果
        """
        try:
            from timeless_memory.core import get_managers
            
            # 取得管理器
            memory_manager, index_manager, _, _, _, _ = get_managers(quiet=True)
            
            # 取得新轉換的檔案
            new_files = convert_result.get("new_files", [])
            updated_files = convert_result.get("updated_files", [])
            all_files = new_files + updated_files
            
            if not all_files:
                _log("  ⏭️ 無新檔案需要索引")
                return {"success": True, "indexed_count": 0}
            
            _log(f"  找到 {len(all_files)} 個檔案需要索引")
            
            # 讀取並批次索引
            from concurrent.futures import ProcessPoolExecutor, as_completed
            from timeless_memory.core.index_manager import _read_memory_worker
            import multiprocessing
            
            workers = min(multiprocessing.cpu_count(), 8)
            _log(f"  使用 {workers} 個工作進程平行讀取")
            
            memories_data = []
            completed = 0
            total = len(all_files)
            
            with ProcessPoolExecutor(max_workers=workers) as executor:
                # 提交讀取任務
                future_to_file = {
                    executor.submit(_read_memory_worker, None, str(file_path)): file_path
                    for file_path in all_files
                }
                
                # 收集結果
                for future in as_completed(future_to_file):
                    completed += 1
                    if completed % 100 == 0:
                        _log(f"  已讀取 {completed} / {total} 筆...")
                    
                    try:
                        result = future.result()
                        if result:
                            memories_data.append(result)
                    except Exception as e:
                        file_path = future_to_file[future]
                        _log(f"  ⚠️ 讀取失敗: {file_path} - {e}")
            
            _log(f"  已讀取 {len(memories_data)} 筆記憶")
            
            # 批次寫入索引
            _log(f"  批次寫入索引...")
            index_manager.batch_update(memories_data, batch_size=100)
            
            _log(f"  ✅ 完成索引 {len(memories_data)} 筆")
            
            return {
                "success": True,
                "indexed_count": len(memories_data),
                "total_files": total
            }
        
        except Exception as e:
            _log(f"  ❌ 索引失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "indexed_count": 0
            }
    
    def download(
        self,
        space_id: Optional[str] = None,
        skip_dm: bool = True,
        incremental: bool = True,
        max_workers: int = 5,
        overlap_days: int = 1
    ) -> Dict:
        """
        下載原始資料
        
        Args:
            space_id: 指定 Space ID
            skip_dm: 是否跳過 DM
            incremental: 是否增量更新
            max_workers: 並行線程數
            overlap_days: 增量下載時回溯天數
        """
        return self.downloader.download(
            space_id=space_id,
            skip_dm=skip_dm,
            incremental=incremental,
            max_workers=max_workers,
            overlap_days=overlap_days
        )
    
    def convert(self, space_name: Optional[str] = None, parallel: bool = False, max_workers: int = 5) -> Dict:
        """
        轉換已下載的資料為記憶
        
        Args:
            space_name: 指定 Space 名稱
            parallel: 是否使用並行轉換
            max_workers: 並行線程數
        """
        if parallel and not space_name:
            return self.parallel_converter.convert(
                space_name=space_name,
                max_workers=max_workers
            )
        else:
            return self.converter.convert(space_name=space_name)
    
    def list_spaces(self, refresh: bool = False) -> List[Dict]:
        """
        列出所有 Spaces
        
        Args:
            refresh: 是否強制重新從 API 取得
        """
        return self.downloader.list_spaces(refresh=refresh)
    
    def status(self) -> Dict:
        """
        查看同步狀態
        
        Returns:
            dict: 狀態資訊
        """
        # 檢查認證狀態
        is_authenticated = self.auth_manager.is_authenticated()
        
        # 統計來源目錄
        source_spaces = []
        source_count = 0
        if self.sources_dir.exists():
            for item in self.sources_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    source_spaces.append(item.name)
                    source_count += 1
        
        # 統計記憶目錄
        memory_spaces = []
        memory_count = 0
        total_memories = 0
        if self.data_dir.exists():
            for item in self.data_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    memory_spaces.append(item.name)
                    memory_count += 1
                    # 計算記憶數量
                    md_files = list(item.glob("*.md"))
                    total_memories += len(md_files)
        
        # 讀取同步狀態
        sync_state_file = self.data_dir.parent / ".google-chat-sync.json"
        last_sync = None
        if sync_state_file.exists():
            import json
            with open(sync_state_file, "r") as f:
                state = json.load(f)
                last_sync = state.get("last_sync")
        
        return {
            "authenticated": is_authenticated,
            "sources_dir": str(self.sources_dir),
            "data_dir": str(self.data_dir),
            "source_spaces": source_count,
            "memory_spaces": memory_count,
            "total_memories": total_memories,
            "last_sync": last_sync,
            "credentials_file": str(self.auth_manager.credentials_file),
            "token_file": str(self.auth_manager.token_file)
        }
    
    def init_auth(self) -> Dict:
        """
        初始化 OAuth 認證
        
        Returns:
            dict: 認證結果
        """
        return self.auth_manager.init_auth()
    
    def analyze(self, include_content: bool = False) -> Dict:
        """
        分析 Google Chat 資料，提取人物和專案資訊
        用於輔助 agent 建立知識圖譜
        
        Args:
            include_content: 是否包含詳細的對應資料（較大）
        
        Returns:
            dict: 分析結果，包含 user_ids, user_mentions, projects
        """
        import re
        import yaml
        from collections import defaultdict, Counter
        
        if not self.data_dir.exists():
            return {
                "success": False,
                "error": "資料目錄不存在，請先執行 sync"
            }
        
        md_files = list(self.data_dir.rglob("*.md"))
        if not md_files:
            return {
                "success": False,
                "error": "沒有找到任何記憶檔案"
            }
        
        # 統計資料
        all_user_ids = set()
        user_id_speak_count = Counter()  # user_id 發言次數
        user_id_mention_names = defaultdict(Counter)  # user_id -> {提及的名字: 次數}
        mention_name_user_ids = defaultdict(set)  # 提及的名字 -> {發言者 user_ids}
        projects = {}
        space_participants = defaultdict(set)
        space_message_count = defaultdict(int)
        
        for md_file in md_files:
            try:
                text = md_file.read_text(encoding='utf-8')
                
                # 解析 frontmatter
                if not text.startswith('---'):
                    continue
                parts = text.split('---', 2)
                if len(parts) < 3:
                    continue
                
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                except:
                    continue
                
                content = parts[2]
                space_name = metadata.get('space_name', '')
                participants = metadata.get('participants', [])
                message_count = metadata.get('message_count', 0)
                
                # 收集 user_ids
                for uid in participants:
                    all_user_ids.add(str(uid))
                    space_participants[space_name].add(str(uid))
                
                space_message_count[space_name] += message_count
                
                # 分析專案（從 space_name）
                project_match = re.search(r'(P\d+)', space_name)
                if project_match:
                    project_code = project_match.group(1)
                    if project_code not in projects:
                        # 提取專案名稱
                        project_name = re.sub(r'P\d+[_\s]*', '', space_name).strip()
                        project_name = re.sub(r'_AAQA.*', '', project_name)
                        projects[project_code] = {
                            'code': project_code,
                            'name': project_name,
                            'spaces': set(),
                            'participants': set()
                        }
                    projects[project_code]['spaces'].add(space_name)
                    projects[project_code]['participants'].update([str(p) for p in participants])
                
                # 分析發言者和 @mentions 的對應
                # 格式: [時間] user_id: 訊息內容
                message_pattern = r'\[[\d\-:\s]+\]\s+(\d+):\s*(.+?)(?=\n\[[\d\-:\s]+\]|\Z)'
                messages = re.findall(message_pattern, content, re.DOTALL)
                
                for speaker_id, message_text in messages:
                    user_id_speak_count[speaker_id] += 1
                    all_user_ids.add(speaker_id)
                    
                    # 提取 @mentions
                    mention_pattern = r'@([a-zA-Z\u4e00-\u9fff][a-zA-Z\u4e00-\u9fff\s]{0,15}?)(?:\s|$|，|,|\n|：)'
                    mentions = re.findall(mention_pattern, message_text)
                    
                    for mention in mentions:
                        mention = mention.strip()
                        if mention and len(mention) >= 2:
                            user_id_mention_names[speaker_id][mention] += 1
                            mention_name_user_ids[mention].add(speaker_id)
            
            except Exception:
                continue
        
        # 推測 user_id -> 人名對應
        # 策略：如果一個名字被某個 user_id 特別常提及，可能是那個人的同事
        # 更好的策略：看誰「自稱」或在簽名中使用某個名字
        
        # 找出高信心度的對應（基於共現分析）
        high_confidence_mappings = {}
        for mention_name, speaker_ids in mention_name_user_ids.items():
            # 排除太短或太長的名字
            if len(mention_name) < 2 or len(mention_name) > 10:
                continue
            # 排除純數字
            if mention_name.isdigit():
                continue
            # 如果只有一個人提到這個名字，可能是內部群組
            if len(speaker_ids) == 1:
                # 可能是那個人自己的名字，或是只有一個人認識
                pass
        
        # 轉換結果
        result = {
            "success": True,
            "summary": {
                "total_files": len(md_files),
                "total_user_ids": len(all_user_ids),
                "total_mentions": len(mention_name_user_ids),
                "total_projects": len(projects),
                "total_spaces": len(space_participants)
            },
            "user_ids": sorted(list(all_user_ids)),
            "top_speakers": [
                {"user_id": uid, "message_count": count}
                for uid, count in user_id_speak_count.most_common(30)
            ],
            "projects": {
                k: {
                    'code': v['code'],
                    'name': v['name'],
                    'spaces': sorted(list(v['spaces'])),
                    'participant_count': len(v['participants']),
                    'participants': sorted(list(v['participants']))
                } for k, v in projects.items()
            },
            "spaces": {
                name: {
                    'participant_count': len(uids),
                    'message_count': space_message_count.get(name, 0)
                } for name, uids in space_participants.items()
            },
            "mention_names": sorted(list(mention_name_user_ids.keys()))
        }
        
        # 如果需要詳細資料
        if include_content:
            result["user_mention_details"] = {
                uid: dict(mentions) 
                for uid, mentions in user_id_mention_names.items()
            }
            result["mention_speakers"] = {
                name: sorted(list(uids))
                for name, uids in mention_name_user_ids.items()
            }
        
        return result
    
    def get_month_data(
        self,
        space_name: str,
        year_month: str
    ) -> Dict:
        """
        取得指定聊天室的月度資料（供 agent 生成摘要用）
        
        Agent 工作流程：
        1. 呼叫 chat(action='list_months') 取得可用的聊天室/月份列表
        2. 呼叫 chat(action='get_month_data', space_name=..., year_month=...) 取得該月資料
        3. Agent 用 LLM 生成摘要
        4. 呼叫 chat(action='save_summary', ...) 儲存摘要
        
        Args:
            space_name: 聊天室名稱
            year_month: 年月 (YYYY-MM 格式)
        
        Returns:
            dict: 該月的對話資料，供 agent 生成摘要
        """
        import re
        import yaml
        from pathlib import Path
        
        if not self.data_dir.exists():
            return {"success": False, "error": "資料目錄不存在，請先執行 sync"}
        
        # 找該聊天室該月的所有 daily 檔案
        space_dir = self.data_dir / space_name
        if not space_dir.exists():
            return {"success": False, "error": f"聊天室不存在: {space_name}"}
        
        pattern = f"daily-*-{year_month}-*.md"
        daily_files = sorted(space_dir.glob(pattern))
        
        if not daily_files:
            return {
                "success": False,
                "error": f"沒有找到 {space_name} 在 {year_month} 的資料"
            }
        
        # 收集資料
        days = []
        total_messages = 0
        all_participants = set()
        
        for daily_file in daily_files:
            text = daily_file.read_text(encoding='utf-8')
            
            # 解析 frontmatter
            metadata = {}
            content = text
            if text.startswith('---'):
                parts = text.split('---', 2)
                if len(parts) >= 3:
                    try:
                        metadata = yaml.safe_load(parts[1]) or {}
                    except:
                        pass
                    content = parts[2]
            
            msg_count = metadata.get('message_count', 0)
            total_messages += msg_count
            
            for p in metadata.get('participants', []):
                all_participants.add(str(p))
            
            # 提取日期
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', daily_file.name)
            date_str = date_match.group(1) if date_match else daily_file.name
            
            # 內容截斷（避免過長）
            content_lines = content.strip().split('\n')
            if len(content_lines) > 50:
                content = '\n'.join(content_lines[:50]) + f"\n\n... (還有 {len(content_lines) - 50} 行)"
            
            days.append({
                "date": date_str,
                "message_count": msg_count,
                "content": content.strip()
            })
        
        return {
            "success": True,
            "space_name": space_name,
            "year_month": year_month,
            "total_days": len(days),
            "total_messages": total_messages,
            "participant_count": len(all_participants),
            "participants": sorted(list(all_participants)),
            "days": days,
            "agent_instruction": "請根據以上每日對話內容，生成一份月度摘要，包含：重點討論主題、重要決策、待辦事項等。完成後呼叫 chat(action='save_summary') 儲存。"
        }
    
    def list_months(self, check_updates: bool = True) -> Dict:
        """
        列出所有可用的聊天室/月份組合，標記需要建立或更新摘要的項目
        
        增量更新邏輯：
        - missing: 完全沒有摘要的月份
        - outdated: 有摘要但資料有更新（daily 檔案比摘要新）
        
        Args:
            check_updates: 是否檢查需要更新的摘要（比較檔案時間）
        
        Returns:
            dict: 聊天室 -> 月份列表，以及需要處理的項目
        """
        import re
        import os
        from collections import defaultdict
        from timeless_memory import get_index_dir
        
        if not self.data_dir.exists():
            return {"success": False, "error": "資料目錄不存在"}
        
        # 收集所有 daily 檔案及其最後修改時間
        # space -> month -> latest_mtime
        space_month_mtime = defaultdict(lambda: defaultdict(float))
        space_months = defaultdict(set)
        
        for md_file in self.data_dir.rglob("daily-*.md"):
            match = re.match(r'daily-(.+)-(\d{4}-\d{2})-\d{2}\.md$', md_file.name)
            if match:
                space = md_file.parent.name
                month = match.group(2)
                space_months[space].add(month)
                
                if check_updates:
                    mtime = os.path.getmtime(md_file)
                    if mtime > space_month_mtime[space][month]:
                        space_month_mtime[space][month] = mtime
        
        # 檢查已存在的摘要及其生成時間
        index_dir = get_index_dir() / "聊天室"
        # (space, month) -> summary_mtime
        existing_summaries = {}
        
        if index_dir.exists():
            for summary_file in index_dir.glob("monthly-summary-*.md"):
                match = re.match(r'monthly-summary-(.+)-(\d{4}-\d{2})\.md$', summary_file.name)
                if match:
                    space = match.group(1)
                    month = match.group(2)
                    existing_summaries[(space, month)] = os.path.getmtime(summary_file)
        
        # 整理結果
        result = {}
        missing = []  # 完全沒有摘要
        outdated = []  # 有摘要但資料有更新
        
        for space, months in sorted(space_months.items()):
            month_status = {}
            for month in sorted(months):
                key = (space, month)
                if key not in existing_summaries:
                    month_status[month] = "missing"
                    missing.append({"space": space, "month": month})
                elif check_updates:
                    data_mtime = space_month_mtime[space][month]
                    summary_mtime = existing_summaries[key]
                    if data_mtime > summary_mtime:
                        month_status[month] = "outdated"
                        outdated.append({
                            "space": space,
                            "month": month,
                            "reason": "資料有更新"
                        })
                    else:
                        month_status[month] = "up_to_date"
                else:
                    month_status[month] = "exists"
            
            result[space] = {
                "months": month_status,
                "total_months": len(months)
            }
        
        # 合併需要處理的項目（missing + outdated）
        needs_update = missing + outdated
        
        return {
            "success": True,
            "spaces": result,
            "total_spaces": len(result),
            "missing_summaries": missing[:10],
            "outdated_summaries": outdated[:10],
            "needs_update": needs_update[:20],
            "total_missing": len(missing),
            "total_outdated": len(outdated),
            "total_needs_update": len(needs_update),
            "index_dir": str(index_dir),
            "agent_instruction": (
                "needs_update 列出需要建立或更新的摘要。"
                "使用 chat(action='get_month_data', space_name=..., year_month=...) 取得資料，"
                "生成摘要後用 chat(action='save_summary') 儲存。"
            )
        }
    
    def save_summary(
        self,
        space_name: str,
        year_month: str,
        summary_content: str
    ) -> Dict:
        """
        儲存 agent 生成的月度摘要
        
        Args:
            space_name: 聊天室名稱
            year_month: 年月 (YYYY-MM 格式)
            summary_content: 摘要內容（Markdown 格式）
        
        Returns:
            dict: 儲存結果
        """
        from pathlib import Path
        from datetime import datetime
        from timeless_memory import get_index_dir
        
        # 設定輸出目錄
        out_dir = get_index_dir() / "聊天室"
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成檔案
        summary_file = out_dir / f"monthly-summary-{space_name}-{year_month}.md"
        
        # 加上 frontmatter
        full_content = f"""---
space_name: {space_name}
month: {year_month}
generated_at: {datetime.now().isoformat()}
generated_by: agent
---

{summary_content}
"""
        
        summary_file.write_text(full_content, encoding='utf-8')
        
        return {
            "success": True,
            "file": str(summary_file),
            "space_name": space_name,
            "year_month": year_month,
            "message": f"已儲存摘要: {summary_file.name}"
        }
    
    def extract_users_for_entities(self) -> Dict:
        """
        從聊天記錄提取 user_id → 顯示名稱對應
        直接輸出可餵給 entity(batch_create) 的格式
        
        Returns:
            dict: 包含 entities 陣列，可直接用於 batch_create
        """
        import re
        import yaml
        from collections import defaultdict, Counter
        
        if not self.data_dir.exists():
            return {"success": False, "error": "資料目錄不存在"}
        
        md_files = list(self.data_dir.rglob("*.md"))
        if not md_files:
            return {"success": False, "error": "沒有找到任何記憶檔案"}
        
        # 分析資料
        user_id_names = defaultdict(Counter)  # user_id -> {可能的名字: 次數}
        user_id_spaces = defaultdict(set)  # user_id -> 參與的聊天室
        user_id_speak_count = Counter()  # user_id 發言次數
        
        for md_file in md_files:
            try:
                text = md_file.read_text(encoding='utf-8')
                
                if not text.startswith('---'):
                    continue
                parts = text.split('---', 2)
                if len(parts) < 3:
                    continue
                
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                except:
                    continue
                
                content = parts[2]
                space_name = metadata.get('space_name', '')
                participants = [str(p) for p in metadata.get('participants', [])]
                
                for uid in participants:
                    user_id_spaces[uid].add(space_name)
                
                # 分析訊息中的簽名模式
                # 很多人會在訊息結尾簽名，或在對話中自稱
                message_pattern = r'\[[\d\-:\s]+\]\s+(\d+):\s*(.+?)(?=\n\[[\d\-:\s]+\]|\Z)'
                messages = re.findall(message_pattern, content, re.DOTALL)
                
                for speaker_id, message_text in messages:
                    user_id_speak_count[speaker_id] += 1
                    
                    # 簽名模式：結尾有名字
                    # 例如：「好的，謝謝 - 小明」或「by 小明」
                    sig_patterns = [
                        r'[-—]\s*([a-zA-Z\u4e00-\u9fff]{2,8})\s*$',
                        r'by\s+([a-zA-Z\u4e00-\u9fff]{2,8})\s*$',
                        r'from\s+([a-zA-Z\u4e00-\u9fff]{2,8})\s*$',
                    ]
                    for pat in sig_patterns:
                        sig_match = re.search(pat, message_text.strip(), re.IGNORECASE)
                        if sig_match:
                            name = sig_match.group(1).strip()
                            if len(name) >= 2:
                                user_id_names[speaker_id][name] += 5  # 簽名權重較高
                
            except Exception:
                continue
        
        # 建立實體列表
        entities = []
        unmapped = []
        
        for user_id, speak_count in user_id_speak_count.most_common():
            possible_names = user_id_names.get(user_id, {})
            spaces = list(user_id_spaces.get(user_id, []))
            
            if possible_names:
                # 取最高分的名字
                best_name, score = possible_names.most_common(1)[0]
                confidence = min(score / 10, 1.0)  # 正規化到 0-1
                
                entities.append({
                    "entity_type": "person",
                    "name": best_name,
                    "aliases": [user_id],  # Chat ID 作為別名
                    "properties": {
                        "chat_id": user_id,
                        "speak_count": speak_count,
                        "confidence": confidence,
                        "spaces": spaces[:5]  # 只保留前 5 個
                    }
                })
            else:
                unmapped.append({
                    "user_id": user_id,
                    "speak_count": speak_count,
                    "spaces": spaces[:3]
                })
        
        return {
            "success": True,
            "entities": entities,
            "unmapped": unmapped[:30],  # 只顯示前 30 個未對應
            "summary": {
                "total_user_ids": len(user_id_speak_count),
                "mapped": len(entities),
                "unmapped": len(unmapped)
            },
            "usage": "使用 entity(action='batch_create', entities=<entities>) 建立實體"
        }

    def get_user_context(self, user_id: str, limit: int = 10) -> Dict:
        """
        取得特定 user_id 的上下文資訊
        用於輔助 agent 判斷這個 user_id 對應的人名
        
        Args:
            user_id: Google Chat User ID
            limit: 返回的訊息數量上限
        
        Returns:
            dict: 該 user_id 的上下文資訊
        """
        import re
        import yaml
        from collections import Counter
        
        if not self.data_dir.exists():
            return {"success": False, "error": "資料目錄不存在"}
        
        md_files = list(self.data_dir.rglob("*.md"))
        
        messages = []  # 該 user 的發言
        mentioned_by = Counter()  # 被誰提到
        mentioned_names = Counter()  # 提到的名字
        spaces = set()  # 參與的聊天室
        
        for md_file in md_files:
            try:
                text = md_file.read_text(encoding='utf-8')
                
                if not text.startswith('---'):
                    continue
                parts = text.split('---', 2)
                if len(parts) < 3:
                    continue
                
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                except:
                    continue
                
                content = parts[2]
                space_name = metadata.get('space_name', '')
                participants = [str(p) for p in metadata.get('participants', [])]
                
                if user_id in participants:
                    spaces.add(space_name)
                
                # 找這個 user 的發言
                message_pattern = rf'\[([\d\-:\s]+)\]\s+{user_id}:\s*(.+?)(?=\n\[[\d\-:\s]+\]|\Z)'
                user_messages = re.findall(message_pattern, content, re.DOTALL)
                
                for timestamp, msg_text in user_messages:
                    if len(messages) < limit:
                        messages.append({
                            "time": timestamp.strip(),
                            "space": space_name,
                            "text": msg_text.strip()[:200]  # 截斷
                        })
                    
                    # 這個 user 提到的名字
                    mention_pattern = r'@([a-zA-Z\u4e00-\u9fff][a-zA-Z\u4e00-\u9fff\s]{0,15}?)(?:\s|$|，|,|\n)'
                    mentions = re.findall(mention_pattern, msg_text)
                    for m in mentions:
                        m = m.strip()
                        if m and len(m) >= 2:
                            mentioned_names[m] += 1
                
                # 找誰提到這個 user（通過 ID 提及較少，這裡略過）
            
            except Exception:
                continue
        
        return {
            "success": True,
            "user_id": user_id,
            "spaces": sorted(list(spaces)),
            "space_count": len(spaces),
            "sample_messages": messages[:limit],
            "mentioned_names": [
                {"name": name, "count": count}
                for name, count in mentioned_names.most_common(20)
            ]
        }
    
    def list_mentions(self, limit: int = 50) -> Dict:
        """
        列出所有被 @ 提及的名字（供 agent 建立人物實體）
        
        這是給 agent 使用的工具：
        1. 列出所有 @ 提及的名字和次數
        2. Agent 根據結果建立人物實體
        
        Args:
            limit: 返回的名字數量上限
        
        Returns:
            dict: 所有被提及的名字及統計
        """
        import re
        import yaml
        from collections import Counter, defaultdict
        
        if not self.data_dir.exists():
            return {"success": False, "error": "資料目錄不存在，請先執行 sync"}
        
        md_files = list(self.data_dir.rglob("*.md"))
        if not md_files:
            return {"success": False, "error": "沒有找到任何記憶檔案"}
        
        # 統計 @ 提及
        mention_counts = Counter()  # 名字 -> 總次數
        mention_speakers = defaultdict(set)  # 名字 -> 提及者 user_ids
        mention_spaces = defaultdict(set)  # 名字 -> 出現的聊天室
        
        for md_file in md_files:
            try:
                text = md_file.read_text(encoding='utf-8')
                
                if not text.startswith('---'):
                    continue
                parts = text.split('---', 2)
                if len(parts) < 3:
                    continue
                
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                except:
                    continue
                
                content = parts[2]
                space_name = metadata.get('space_name', '')
                
                # 解析訊息：[時間] user_id: 內容
                message_pattern = r'\[[\d\-:\s]+\]\s+(\d+):\s*(.+?)(?=\n\[[\d\-:\s]+\]|\Z)'
                messages = re.findall(message_pattern, content, re.DOTALL)
                
                for speaker_id, message_text in messages:
                    # 提取 @ 提及（支援中英文）
                    mention_pattern = r'@([a-zA-Z\u4e00-\u9fff][a-zA-Z0-9\u4e00-\u9fff_\-\s]{0,20}?)(?:\s|$|，|,|\n|：|:|、)'
                    mentions = re.findall(mention_pattern, message_text)
                    
                    for name in mentions:
                        name = name.strip()
                        # 過濾無效名字
                        if not name or len(name) < 2 or len(name) > 15:
                            continue
                        if name.isdigit():
                            continue
                        # 排除常見非人名關鍵字
                        if name.lower() in ['all', 'here', 'channel', 'everyone']:
                            continue
                        
                        mention_counts[name] += 1
                        mention_speakers[name].add(speaker_id)
                        mention_spaces[name].add(space_name)
            
            except Exception:
                continue
        
        # 整理結果
        results = []
        for name, count in mention_counts.most_common(limit):
            results.append({
                "name": name,
                "mention_count": count,
                "mentioned_by_count": len(mention_speakers[name]),
                "space_count": len(mention_spaces[name]),
                "spaces": sorted(list(mention_spaces[name]))[:5]  # 只列前 5 個
            })
        
        return {
            "success": True,
            "total_unique_names": len(mention_counts),
            "mentions": results,
            "agent_instruction": (
                "以上是聊天記錄中被 @ 提及的名字。"
                "使用 chat(action='search_mention', name='xxx') 取得該名字的上下文，"
                "判斷對應的 user_id 後建立人物實體。"
            )
        }
    
    def search_mention(self, name: str, limit: int = 10) -> Dict:
        """
        搜尋特定 @ 名字的上下文（供 agent 判斷 user_id 對應）
        
        這是給 agent 使用的工具：
        1. 搜尋所有 @name 的訊息
        2. 顯示上下文（誰發言、在哪個聊天室）
        3. Agent 根據上下文推斷 user_id → 人名對應
        
        Args:
            name: 要搜尋的名字
            limit: 返回的訊息數量上限
        
        Returns:
            dict: 該名字的所有提及上下文
        """
        import re
        import yaml
        from collections import Counter
        
        if not self.data_dir.exists():
            return {"success": False, "error": "資料目錄不存在"}
        
        if not name:
            return {"success": False, "error": "請提供要搜尋的名字"}
        
        md_files = list(self.data_dir.rglob("*.md"))
        
        # 收集結果
        contexts = []  # 上下文列表
        speaker_counts = Counter()  # 誰提到這個名字
        spaces = set()  # 出現的聊天室
        
        for md_file in md_files:
            try:
                text = md_file.read_text(encoding='utf-8')
                
                if not text.startswith('---'):
                    continue
                parts = text.split('---', 2)
                if len(parts) < 3:
                    continue
                
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                except:
                    continue
                
                content = parts[2]
                space_name = metadata.get('space_name', '')
                date_str = metadata.get('date', '')
                
                # 解析訊息
                message_pattern = r'\[([\d\-:\s]+)\]\s+(\d+):\s*(.+?)(?=\n\[[\d\-:\s]+\]|\Z)'
                messages = re.findall(message_pattern, content, re.DOTALL)
                
                for timestamp, speaker_id, message_text in messages:
                    # 檢查是否提到這個名字
                    if f'@{name}' in message_text or f'@ {name}' in message_text:
                        speaker_counts[speaker_id] += 1
                        spaces.add(space_name)
                        
                        if len(contexts) < limit:
                            contexts.append({
                                "date": date_str,
                                "time": timestamp.strip(),
                                "space": space_name,
                                "speaker_id": speaker_id,
                                "message": message_text.strip()[:300]  # 截斷
                            })
            
            except Exception:
                continue
        
        # 分析：誰最常提到這個名字？
        top_speakers = [
            {"user_id": uid, "count": count}
            for uid, count in speaker_counts.most_common(10)
        ]
        
        return {
            "success": True,
            "name": name,
            "total_mentions": sum(speaker_counts.values()),
            "mentioned_by": top_speakers,
            "spaces": sorted(list(spaces)),
            "contexts": contexts,
            "agent_instruction": (
                f"以上是 @{name} 的所有提及上下文。"
                "分析 'mentioned_by' 可以推斷誰最常提到這個人。"
                "分析 'contexts' 中的對話內容，判斷這個名字對應的 user_id。"
                "確定後用 entity(action='create', ...) 建立人物實體。"
            )
        }
