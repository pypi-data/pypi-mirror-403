"""
記憶管理器
負責記憶的 CRUD 操作，同時更新 SQLite 索引
"""
from typing import Dict, Optional, List, TYPE_CHECKING
from datetime import datetime
import yaml
from pathlib import Path

if TYPE_CHECKING:
    from .index_manager import IndexManager


class MemoryManager:
    """
    記憶管理器
    純檔案系統操作，支援雙索引（SQLite + Markdown）
    """

    def __init__(
        self, 
        base_dir: str, 
        index_manager: Optional["IndexManager"] = None
    ):
        self.base_dir = Path(base_dir)
        self.memory_core = self.base_dir / "記憶核心"
        self.index_manager = index_manager  # SQLite FTS5 索引

        self._init_directories()

    def _init_directories(self):
        """初始化目錄結構"""
        dirs = [
            self.memory_core / "語義記憶" / "偏好學習",
            self.memory_core / "語義記憶" / "知識庫",
            self.memory_core / "情節記憶" / "專案經歷",
            self.memory_core / "情節記憶" / "產品策略",
            self.memory_core / "程序記憶",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def create_memory(
        self,
        content: str,
        metadata: Dict,
        category: str = "情節記憶"
    ) -> Dict:
        """
        建立新記憶

        Args:
            content: 記憶內容（Markdown）
            metadata: 元資料（speaker, authority, quality, tags 等）
            category: 記憶類型（語義記憶/情節記憶/程序記憶）

        Returns:
            建立的記憶資訊
        """
        # 1. 生成 ID
        memory_id = self._generate_id(metadata)

        # 2. 補充必要的 metadata
        metadata = self._enrich_metadata(metadata, memory_id)

        # 3. 生成語義化檔名
        filename = self._generate_semantic_filename(metadata)

        # 4. 組裝完整檔案
        full_content = self._assemble_file(metadata, content)

        # 5. 決定儲存路徑
        file_path = self._get_file_path(category, metadata, filename)

        # 6. 寫入檔案
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(full_content, encoding='utf-8')

        # 更新索引
        if self.index_manager:
            self.index_manager.update(memory_id, str(file_path), metadata, content)

        return {
            "id": memory_id,
            "title": metadata.get('title', ''),
            "file_path": str(file_path),
            "metadata": metadata,
            "content": content
        }

    def read_memory(self, memory_id: str) -> Optional[Dict]:
        """讀取記憶"""
        # 從索引查詢檔案路徑
        file_path = None
        if self.index_manager:
            file_path_str = self.index_manager.get_file_path(memory_id)
            if file_path_str:
                file_path = Path(file_path_str)

        if not file_path:
            file_path = self._find_file_by_id(memory_id)

        if not file_path or not file_path.exists():
            return None

        text = file_path.read_text(encoding='utf-8')
        metadata, content = self._parse_frontmatter(text)

        return {
            "id": memory_id,
            "title": metadata.get('title', ''),
            "metadata": metadata,
            "content": content,
            "file_path": str(file_path)
        }

    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """更新記憶"""
        existing = self.read_memory(memory_id)
        if not existing:
            return False

        new_metadata = {**existing['metadata'], **(metadata or {})}
        new_content = content or existing['content']
        new_metadata['updated'] = datetime.now().isoformat()

        full_content = self._assemble_file(new_metadata, new_content)
        file_path = Path(existing['file_path'])
        file_path.write_text(full_content, encoding='utf-8')

        # 更新索引
        if self.index_manager:
            self.index_manager.update(memory_id, str(file_path), new_metadata, new_content)

        return True

    def delete_memory(self, memory_id: str) -> bool:
        """刪除記憶"""
        existing = self.read_memory(memory_id)
        if not existing:
            return False

        file_path = Path(existing['file_path'])

        if file_path.exists():
            file_path.unlink()

        # 從索引移除
        if self.index_manager:
            self.index_manager.delete(memory_id)

        return True

    def list_memories(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """列出記憶（掃描整個 data/ 目錄）"""
        memories = []

        # 如果指定 category，在記憶核心內搜尋
        # 否則掃描整個 data/ 目錄（包含 google-chat 等）
        if category:
            search_dir = self.memory_core / category
        else:
            search_dir = self.base_dir

        for md_file in search_dir.rglob("*.md"):
            try:
                text = md_file.read_text(encoding='utf-8')
                metadata, _ = self._parse_frontmatter(text)

                memories.append({
                    "id": metadata.get('id', ''),
                    "title": metadata.get('title', ''),
                    "speaker": metadata.get('speaker', ''),
                    "authority": metadata.get('authority', 0),
                    "updated": metadata.get('updated', ''),
                    "file_path": str(md_file)
                })

                if len(memories) >= limit:
                    break
            except Exception:
                continue

        memories.sort(key=lambda x: x.get('updated', ''), reverse=True)
        return memories

    # ===== 私有方法 =====

    def _generate_id(self, metadata: Dict) -> str:
        """生成唯一 ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        title = metadata.get('title', metadata.get('keywords', 'untitled'))
        title_slug = self._slugify(title)[:20]
        return f"{title_slug}-{timestamp}"

    def _slugify(self, text: str) -> str:
        """轉換為 slug"""
        return text.replace(' ', '-').replace(',', '-').replace('、', '-')

    def _enrich_metadata(self, metadata: Dict, memory_id: str) -> Dict:
        """補充必要的 metadata 欄位"""
        now = datetime.now().isoformat()

        return {
            "id": memory_id,
            "title": metadata.get('title', metadata.get('keywords', 'Untitled')[:50]),
            "speaker": metadata.get('speaker', 'external'),
            "authority": metadata.get('authority', 3),
            "quality": metadata.get('quality', 3),
            "source_type": metadata.get('source_type', 'conversation'),
            "captured_at": metadata.get('captured_at', now),
            "updated": metadata.get('updated', now),
            "tags": metadata.get('tags', []),
            "keywords": metadata.get('keywords', ''),
            "context": metadata.get('context', ''),
        }

    def _generate_semantic_filename(self, metadata: Dict) -> str:
        """生成語義化檔名"""
        keywords_str = metadata.get('keywords', '')
        if keywords_str:
            keywords = [k.strip() for k in keywords_str.split(',')[:3] if k.strip()]
        else:
            title = metadata.get('title', 'untitled')
            keywords = title.split()[:3]

        date_str = metadata.get('captured_at', datetime.now().isoformat())[:10]
        filename_parts = keywords + [date_str]
        filename = '-'.join(filename_parts) + '.md'
        filename = filename.replace('/', '-').replace('\\', '-')

        return filename

    def _assemble_file(self, metadata: Dict, content: str) -> str:
        """組裝 YAML frontmatter + Markdown"""
        frontmatter = yaml.dump(metadata, allow_unicode=True, sort_keys=False)
        return f"---\n{frontmatter}---\n\n{content}"

    def _parse_frontmatter(self, text: str) -> tuple:
        """解析 YAML frontmatter"""
        if not text.startswith('---'):
            return {}, text

        parts = text.split('---', 2)
        if len(parts) < 3:
            return {}, text

        try:
            metadata = yaml.safe_load(parts[1])
        except Exception:
            metadata = {}

        content = parts[2].strip()
        return metadata, content

    def _get_file_path(self, category: str, metadata: Dict, filename: str) -> Path:
        """決定儲存路徑"""
        base = self.memory_core / category

        if category == "語義記憶":
            if metadata.get('speaker') == 'user' and metadata.get('quality', 0) >= 4:
                subdir = "偏好學習"
            else:
                subdir = "知識庫"
        elif category == "情節記憶":
            tags = metadata.get('tags', [])
            if '專案' in tags:
                subdir = "專案經歷"
            elif '產品' in tags:
                subdir = "產品策略"
            else:
                subdir = "其他"
        else:
            subdir = ""

        return base / subdir / filename

    def _find_file_by_id(self, memory_id: str) -> Optional[Path]:
        """在檔案系統中搜尋記憶檔案（搜尋整個 data/ 目錄）"""
        for md_file in self.base_dir.rglob("*.md"):
            try:
                text = md_file.read_text(encoding='utf-8')
                metadata, _ = self._parse_frontmatter(text)
                if metadata.get('id') == memory_id:
                    return md_file
            except Exception:
                continue
        return None
