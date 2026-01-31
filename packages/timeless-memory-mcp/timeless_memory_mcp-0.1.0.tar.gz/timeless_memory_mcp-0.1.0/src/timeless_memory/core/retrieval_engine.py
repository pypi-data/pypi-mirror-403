"""
檢索引擎
使用 ripgrep + 權重排序
"""
import subprocess
import json
import sys
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


def _log(msg: str):
    """輸出到 stderr（避免干擾 MCP stdio 通訊）"""
    print(msg, file=sys.stderr)


class RetrievalEngine:
    """
    檢索引擎
    支援 SQLite FTS5 + ripgrep + 權重排序
    """

    def __init__(self, base_dir: str, index_manager, memory_manager):
        self.base_dir = Path(base_dir)
        self.index_manager = index_manager
        self.memory_manager = memory_manager

    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 10,
        use_ripgrep: bool = False
    ) -> List[Dict]:
        """全文檢索"""
        # 1. 分層搜尋
        results = self._layered_search(query, filters, use_ripgrep)

        # 2. 權重排序
        ranked = self._rank_results(results, query)

        # 3. 截斷
        return ranked[:limit]

    def _layered_search(
        self,
        query: str,
        filters: Optional[Dict],
        use_ripgrep: bool = False
    ) -> List[Dict]:
        """分層搜尋策略"""
        results = []

        # L1: SQLite FTS5 索引搜尋
        if self.index_manager and not use_ripgrep:
            index_results = self.index_manager.search(query, filters, limit=100)
            if index_results:
                for r in index_results:
                    memory = self.memory_manager.read_memory(r['id'])
                    if memory:
                        r['content'] = memory['content']
                        results.append(r)

        # L2: ripgrep 搜尋（備用）
        if not results or use_ripgrep:
            rg_results = self._ripgrep_search(query, filters)
            results.extend(rg_results)

        # 去重
        seen = set()
        unique = []
        for r in results:
            if r['id'] not in seen:
                seen.add(r['id'])
                unique.append(r)

        return unique

    def _ripgrep_search(self, query: str, filters: Optional[Dict]) -> List[Dict]:
        """使用 ripgrep 全文檢索"""
        cmd = ['rg', query, str(self.base_dir), '--json', '--ignore-case']

        if filters and filters.get('speaker') == 'user':
            cmd.extend(['--glob', '**/偏好學習/**'])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split('\n')

            matches = []
            for line in lines:
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get('type') == 'match':
                        matches.append({
                            'file': data['data']['path']['text'],
                            'line': data['data']['line_number'],
                            'snippet': data['data']['lines']['text'].strip()
                        })
                except json.JSONDecodeError:
                    continue

            memories = []
            seen_files = set()

            for match in matches:
                if match['file'] in seen_files:
                    continue
                seen_files.add(match['file'])

                memory = self._load_memory_from_file(match['file'])
                if memory and self._apply_filters(memory, filters):
                    memory['snippet'] = match['snippet']
                    memories.append(memory)

            return memories

        except subprocess.TimeoutExpired:
            _log("ripgrep timeout")
            return []
        except Exception as e:
            _log(f"ripgrep error: {e}")
            return []

    def _rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """權重排序"""
        now = datetime.now()

        for result in results:
            meta = result.get('metadata', {})

            # Authority 分數
            authority = meta.get('authority', 3)
            authority_score = authority / 10

            # 時間分數
            updated_str = meta.get('updated', '2020-01-01')
            try:
                if 'T' in updated_str:
                    updated = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                else:
                    updated = datetime.fromisoformat(updated_str)
            except Exception:
                updated = datetime(2020, 1, 1)

            days_ago = (now - updated).days

            if days_ago <= 7:
                time_score = 1.0
            elif days_ago <= 30:
                time_score = 0.8
            elif days_ago <= 180:
                time_score = 0.5
            else:
                time_score = 0.3

            # Quality 分數
            quality = meta.get('quality', 3)
            quality_score = quality / 5

            # 相關性分數
            relevance_score = self._calculate_relevance(result, query)

            # 綜合分數
            result['score'] = (
                authority_score * 0.4 +
                time_score * 0.3 +
                quality_score * 0.2 +
                relevance_score * 0.1
            )

            result['score_breakdown'] = {
                'authority': round(authority_score, 2),
                'time': round(time_score, 2),
                'quality': round(quality_score, 2),
                'relevance': round(relevance_score, 2)
            }

        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def _calculate_relevance(self, result: Dict, query: str) -> float:
        """計算相關性分數"""
        content = result.get('content', '').lower()
        title = result.get('title', '').lower()
        query_lower = query.lower()

        title_count = title.count(query_lower)
        content_count = content.count(query_lower)
        total_count = title_count * 3 + content_count

        return min(total_count / 10, 1.0)

    def _apply_filters(self, memory: Dict, filters: Optional[Dict]) -> bool:
        """套用過濾條件"""
        if not filters:
            return True

        meta = memory.get('metadata', {})

        if 'speaker' in filters and meta.get('speaker') != filters['speaker']:
            return False

        if 'authority' in filters:
            auth_filter = filters['authority']
            authority = meta.get('authority', 0)
            if isinstance(auth_filter, dict):
                if 'gte' in auth_filter and authority < auth_filter['gte']:
                    return False
                if 'lte' in auth_filter and authority > auth_filter['lte']:
                    return False
            else:
                if authority < auth_filter:
                    return False

        if 'quality' in filters:
            qual_filter = filters['quality']
            quality = meta.get('quality', 0)
            if isinstance(qual_filter, dict):
                if 'gte' in qual_filter and quality < qual_filter['gte']:
                    return False
            else:
                if quality < qual_filter:
                    return False

        if 'date_range' in filters:
            start, end = filters['date_range']
            updated = meta.get('updated', '')
            if not (start <= updated <= end):
                return False

        if 'tags' in filters:
            required_tags = set(filters['tags'])
            memory_tags = set(meta.get('tags', []))
            if not required_tags.issubset(memory_tags):
                return False

        return True

    def _load_memory_from_file(self, file_path: str) -> Optional[Dict]:
        """從檔案載入記憶"""
        try:
            import yaml
            file_path_obj = Path(file_path)
            text = file_path_obj.read_text(encoding='utf-8')

            if not text.startswith('---'):
                return None

            parts = text.split('---', 2)
            if len(parts) < 3:
                return None

            metadata = yaml.safe_load(parts[1])
            content = parts[2].strip()

            return {
                'id': metadata.get('id', ''),
                'title': metadata.get('title', ''),
                'metadata': metadata,
                'content': content,
                'file_path': str(file_path_obj)
            }
        except Exception as e:
            _log(f"Error loading {file_path}: {e}")
            return None
