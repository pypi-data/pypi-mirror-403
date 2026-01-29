"""Credentials management for GoSend"""
import os
import json
from pathlib import Path
from typing import Dict, Optional


class CredentialsManager:
    """Manage GoSend credentials securely"""
    
    CREDENTIALS_DIR = Path.home() / ".gosend"
    CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
    
    @classmethod
    def ensure_dir(cls) -> None:
        """Create .gosend directory if needed"""
        cls.CREDENTIALS_DIR.mkdir(exist_ok=True, mode=0o700)
    
    @classmethod
    def save_credentials(
        cls,
        access_id: str,
        access_key: str,
        project: str,
        endpoint: str,
        region: str = "ap-southeast-5"
    ) -> None:
        """Save credentials to ~/.gosend/credentials.json"""
        cls.ensure_dir()
        
        credentials = {
            "access_id": access_id,
            "access_key": access_key,
            "project": project,
            "endpoint": endpoint,
            "region": region
        }
        
        with open(cls.CREDENTIALS_FILE, 'w') as f:
            json.dump(credentials, f, indent=2)
        
        # Make file readable only by owner
        os.chmod(cls.CREDENTIALS_FILE, 0o600)
        print(f"✅ Credentials saved to {cls.CREDENTIALS_FILE}")
    
    @classmethod
    def load_credentials(cls) -> Optional[Dict[str, str]]:
        """Load credentials from ~/.gosend/credentials.json"""
        if cls.CREDENTIALS_FILE.exists():
            with open(cls.CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        return None
    
    @classmethod
    def get_credentials(cls) -> Dict[str, str]:
        """Get credentials from file or environment"""
        # Priority: credentials.json > environment variables
        stored = cls.load_credentials()
        if stored:
            return stored
        
        # Fallback to environment variables
        credentials = {
            "access_id": os.getenv("MAXCOMPUTE_ACCESS_ID", ""),
            "access_key": os.getenv("MAXCOMPUTE_ACCESS_KEY", ""),
            "project": os.getenv("MAXCOMPUTE_PROJECT", ""),
            "endpoint": os.getenv("MAXCOMPUTE_ENDPOINT", "http://service.odps.aliyun.com/api"),
        }
        
        return credentials if all(credentials.values()) else None
    
    @classmethod
    def has_credentials(cls) -> bool:
        """Check if credentials exist"""
        return cls.load_credentials() is not None or all([
            os.getenv("MAXCOMPUTE_ACCESS_ID"),
            os.getenv("MAXCOMPUTE_ACCESS_KEY"),
            os.getenv("MAXCOMPUTE_PROJECT")
        ])
    
    @classmethod
    def delete_credentials(cls) -> None:
        """Delete saved credentials"""
        if cls.CREDENTIALS_FILE.exists():
            os.remove(cls.CREDENTIALS_FILE)
            print(f"✅ Credentials removed from {cls.CREDENTIALS_FILE}")
