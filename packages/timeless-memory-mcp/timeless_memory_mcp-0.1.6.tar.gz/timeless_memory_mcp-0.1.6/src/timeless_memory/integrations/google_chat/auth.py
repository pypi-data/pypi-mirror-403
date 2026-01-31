"""
Google OAuth 認證處理
"""
import os
import json
import sys
import tempfile
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def _log(msg: str):
    """輸出到 stderr（避免干擾 MCP stdio 通訊）"""
    print(msg, file=sys.stderr)

# Google Chat API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/chat.messages.readonly",
    "https://www.googleapis.com/auth/chat.spaces.readonly"
]


class ChatAuthManager:
    """Google Chat OAuth 認證管理"""
    
    def __init__(self, sources_dir: Path):
        """
        Args:
            sources_dir: sources/google-chat/ 目錄路徑
        """
        self.sources_dir = Path(sources_dir)
        self.sources_dir.mkdir(parents=True, exist_ok=True)
        
        # 優先使用環境變數，其次使用檔案
        self.credentials_file = self._get_credentials_path()
        self.token_file = self.sources_dir / "token.json"
    
    def _get_credentials_path(self) -> Path:
        """
        取得 credentials.json 路徑
        優先順序：
        1. 環境變數 GOOGLE_CHAT_CREDENTIALS（JSON 字串）
        2. 環境變數 GOOGLE_CHAT_CREDENTIALS_FILE（檔案路徑）
        3. 預設檔案路徑
        """
        # 方式 1: 從環境變數讀取 JSON 字串
        credentials_json = os.getenv("GOOGLE_CHAT_CREDENTIALS")
        if credentials_json:
            try:
                # 驗證是否為有效 JSON
                json.loads(credentials_json)
                # 建立臨時檔案
                temp_file = tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.json',
                    delete=False,
                    dir=self.sources_dir
                )
                temp_file.write(credentials_json)
                temp_file.close()
                return Path(temp_file.name)
            except json.JSONDecodeError:
                _log(f"⚠️  GOOGLE_CHAT_CREDENTIALS 不是有效的 JSON，使用預設路徑")
        
        # 方式 2: 從環境變數讀取檔案路徑
        credentials_file = os.getenv("GOOGLE_CHAT_CREDENTIALS_FILE")
        if credentials_file:
            path = Path(credentials_file)
            if path.exists():
                return path
            else:
                _log(f"⚠️  GOOGLE_CHAT_CREDENTIALS_FILE 指定的檔案不存在: {credentials_file}")
        
        # 方式 3: 預設路徑
        return self.sources_dir / "credentials.json"
    
    def get_credentials(self) -> Credentials:
        """
        取得或重新整理 OAuth 認證憑證
        
        Returns:
            Credentials: Google OAuth 憑證
        """
        creds = None
        
        # 檢查是否已有儲存的 token
        if self.token_file.exists():
            creds = Credentials.from_authorized_user_file(
                str(self.token_file), SCOPES
            )
        
        # 如果沒有有效憑證，進行 OAuth 流程
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # 重新整理過期憑證
                creds.refresh(Request())
            else:
                # 首次認證
                if not self.credentials_file.exists():
                    raise FileNotFoundError(
                        f"找不到認證檔案: {self.credentials_file}\n"
                        f"請從 Google Cloud Console 下載 OAuth 2.0 憑證並儲存至:\n"
                        f"{self.credentials_file}"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), SCOPES
                )
                creds = flow.run_local_server(port=8080)
            
            # 儲存憑證供下次使用
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        
        return creds
    
    def get_chat_service(self):
        """
        建立 Google Chat API 服務
        
        Returns:
            Resource: Google Chat API 服務物件
        """
        creds = self.get_credentials()
        service = build("chat", "v1", credentials=creds)
        return service
    
    def is_authenticated(self) -> bool:
        """檢查是否已認證"""
        return self.token_file.exists()
    
    def init_auth(self) -> dict:
        """
        初始化認證（引導使用者完成 OAuth）
        
        Returns:
            dict: 認證結果
        """
        try:
            if not self.credentials_file.exists():
                env_hint = "\n\n可透過以下方式之一設定 credentials.json：\n"
                env_hint += "1. 將檔案放至: {}\n".format(self.sources_dir / "credentials.json")
                env_hint += "2. 設定環境變數: GOOGLE_CHAT_CREDENTIALS_FILE=/path/to/credentials.json\n"
                env_hint += "3. 設定環境變數: GOOGLE_CHAT_CREDENTIALS='{{...JSON...}}'"
                
                return {
                    "success": False,
                    "message": f"找不到 credentials.json{env_hint}"
                }
            
            # 觸發認證流程
            self.get_credentials()
            
            return {
                "success": True,
                "message": "認證成功",
                "token_file": str(self.token_file),
                "credentials_source": self._get_credentials_source()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"認證失敗: {str(e)}"
            }
    
    def _get_credentials_source(self) -> str:
        """取得憑證來源說明"""
        if os.getenv("GOOGLE_CHAT_CREDENTIALS"):
            return "環境變數 GOOGLE_CHAT_CREDENTIALS"
        elif os.getenv("GOOGLE_CHAT_CREDENTIALS_FILE"):
            return f"環境變數 GOOGLE_CHAT_CREDENTIALS_FILE: {os.getenv('GOOGLE_CHAT_CREDENTIALS_FILE')}"
        else:
            return f"檔案: {self.sources_dir / 'credentials.json'}"
