"""
Persistent caching service for SignalPilot AI.
Handles OS-specific cache directory management and robust file operations.
"""

import hashlib
import json
import os
import platform
import shutil
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import controlled print function
from .log_utils import print


class CacheDirectoryManager:
    """OS-specific cache directory management with fallbacks"""
    
    @staticmethod
    def get_cache_directories() -> list[Path]:
        """Get ordered list of cache directories from most to least preferred"""
        system = platform.system().lower()
        directories = []
        
        try:
            if system == "windows":
                # Primary: AppData\Local
                appdata_local = os.environ.get('LOCALAPPDATA')
                if appdata_local:
                    directories.append(Path(appdata_local) / "SignalPilotAI" / "Cache")
                
                # Secondary: AppData\Roaming
                appdata_roaming = os.environ.get('APPDATA')
                if appdata_roaming:
                    directories.append(Path(appdata_roaming) / "SignalPilotAI" / "Cache")
                
                # Tertiary: User profile
                userprofile = os.environ.get('USERPROFILE')
                if userprofile:
                    directories.append(Path(userprofile) / ".signalpilot-cache")
                    
            elif system == "darwin":  # macOS
                # Primary: ~/Library/Caches
                home = Path.home()
                directories.append(home / "Library" / "Caches" / "SignalPilotAI")
                
                # Secondary: ~/Library/Application Support
                directories.append(home / "Library" / "Application Support" / "SignalPilotAI")
                
                # Tertiary: ~/.signalpilot-cache
                directories.append(home / ".signalpilot-cache")
                
            else:  # Linux and other Unix-like
                # Primary: XDG_CACHE_HOME or ~/.cache
                cache_home = os.environ.get('XDG_CACHE_HOME')
                if cache_home:
                    directories.append(Path(cache_home) / "signalpilot-ai")
                else:
                    directories.append(Path.home() / ".cache" / "signalpilot-ai")
                
                # Secondary: XDG_DATA_HOME or ~/.local/share
                data_home = os.environ.get('XDG_DATA_HOME')
                if data_home:
                    directories.append(Path(data_home) / "signalpilot-ai")
                else:
                    directories.append(Path.home() / ".local" / "share" / "signalpilot-ai")
                
                # Tertiary: ~/.signalpilot-cache
                directories.append(Path.home() / ".signalpilot-cache")
            
            # Final fallback: temp directory
            directories.append(Path(tempfile.gettempdir()) / f"signalpilot-ai-{os.getuid() if hasattr(os, 'getuid') else 'user'}")
            
        except Exception as e:
            print(f"ERROR: determining cache directories: {e}")
            # Emergency fallback
            directories.append(Path(tempfile.gettempdir()) / "signalpilot-ai-emergency")
        
        return directories
    
    @staticmethod
    def find_usable_cache_directory() -> Optional[Path]:
        """Find the first usable cache directory with write permissions"""
        for cache_dir in CacheDirectoryManager.get_cache_directories():
            try:
                # Create directory if it doesn't exist
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                # Test write permissions
                test_file = cache_dir / f"test_write_{uuid.uuid4().hex[:8]}.tmp"
                test_file.write_text("test")
                test_file.unlink()

                print(f"Using cache directory: {cache_dir}")
                return cache_dir
                
            except Exception as e:
                print(f"Cannot use cache directory {cache_dir}: {e}")
                continue
        
        print("ERROR: No usable cache directory found!")
        return None


class RobustFileOperations:
    """Extremely safe file operations with atomic writes and recovery"""
    
    @staticmethod
    def safe_write_json(file_path: Path, data: Any, max_retries: int = 3) -> bool:
        """Safely write JSON data with atomic operations and backups"""
        
        if not file_path.parent.exists():
            try:
                print(f"Creating parent directory: {file_path.parent}")
                file_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"ERROR: Failed to create directory {file_path.parent}: {e}")
                return False
        
        # Create backup if file exists and is valid, but only if last backup is older than 1 hour
        backup_path = None
        if file_path.exists():
            try:
                # Verify current file is valid JSON before backing up
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                
                # Check if we need a new backup (only if last backup is > 1 hour old)
                should_create_backup = RobustFileOperations._should_create_backup(file_path)
                
                if should_create_backup:
                    backup_path = file_path.with_suffix(f".backup.{int(time.time())}")
                    shutil.copy2(file_path, backup_path)
                    
                    # Keep only the most recent backup that's at least 1 hour old
                    RobustFileOperations._cleanup_backups(file_path)
                
            except Exception as e:
                print(f"Warning: Could not create backup for {file_path}: {e}")
        
        # Attempt atomic write with retries
        for attempt in range(max_retries):
            temp_path = file_path.with_suffix(f".tmp.{uuid.uuid4().hex[:8]}")
            
            try:
                # Write to temporary file first
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Verify the written data
                with open(temp_path, 'r', encoding='utf-8') as f:
                    verification_data = json.load(f)
                
                # Atomic move to final location
                if platform.system().lower() == "windows":
                    # Windows requires removing target first
                    if file_path.exists():
                        file_path.unlink()
                
                shutil.move(str(temp_path), str(file_path))
                
                return True
                
            except Exception as e:
                print(f"Write attempt {attempt + 1} failed for {file_path}: {e}")
                
                # Clean up temp file
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except:
                    pass
                
                if attempt == max_retries - 1:
                    # Restore from backup if all attempts failed
                    if backup_path and backup_path.exists():
                        try:
                            shutil.copy2(backup_path, file_path)
                            print(f"Restored {file_path} from backup")
                        except Exception as restore_error:
                            print(f"ERROR: Failed to restore backup: {restore_error}")
                    
                    return False
                
                # Wait before retry
                time.sleep(0.1 * (attempt + 1))
        
        return False
    
    @staticmethod
    def safe_read_json(file_path: Path, default: Any = None) -> Any:
        """Safely read JSON data with corruption recovery"""
        if not file_path.exists():
            return default
        
        # Try reading main file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to read {file_path}: {e}")
            
            # Try to recover from backup
            backup_files = sorted(
                file_path.parent.glob(f"{file_path.stem}.backup.*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            for backup_path in backup_files:
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    print(f"Recovered data from backup: {backup_path}")
                    
                    # Try to restore the main file
                    try:
                        shutil.copy2(backup_path, file_path)
                        print(f"Restored {file_path} from {backup_path}")
                    except Exception as restore_error:
                        print(f"ERROR: Could not restore main file: {restore_error}")
                    
                    return data
                    
                except Exception as backup_error:
                    print(f"Backup {backup_path} also corrupted: {backup_error}")
                    continue
            
            print(f"All recovery attempts failed for {file_path}, using default")
            return default
    
    @staticmethod
    def _should_create_backup(file_path: Path) -> bool:
        """Check if we should create a new backup (only if last backup is > 1 hour old)"""
        try:
            backup_files = sorted(
                file_path.parent.glob(f"{file_path.stem}.backup.*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if not backup_files:
                return True  # No backups exist, create first one
            
            # Check if the most recent backup is older than 1 hour
            most_recent_backup = backup_files[0]
            backup_age = time.time() - most_recent_backup.stat().st_mtime
            return backup_age > 3600  # 3600 seconds = 1 hour
            
        except Exception as e:
            print(f"ERROR: checking backup age: {e}")
            return True  # If we can't check, err on the side of creating a backup
    
    @staticmethod
    def _cleanup_backups(file_path: Path, keep_count: int = 1):
        """Keep only the most recent backup file (limit to 1 backup)"""
        try:
            backup_files = sorted(
                file_path.parent.glob(f"{file_path.stem}.backup.*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Keep only the most recent backup, delete all others
            for old_backup in backup_files[keep_count:]:
                try:
                    old_backup.unlink()
                    print(f"Cleaned up old backup: {old_backup}")
                except Exception as cleanup_error:
                    print(f"ERROR: Failed to cleanup backup {old_backup}: {cleanup_error}")
                    
        except Exception as e:
            print(f"ERROR: cleaning up backups: {e}")


class PersistentCacheService:
    """Extremely robust persistent caching service for SignalPilot AI"""

    def __init__(self):
        self.cache_dir = CacheDirectoryManager.find_usable_cache_directory()
        self.chat_histories_file = None
        self.chat_histories_dir = None
        self.app_values_file = None
        self._lock = threading.RLock()

        if self.cache_dir:
            print(f"Cache service initialized with directory: {self.cache_dir}")
            self.chat_histories_file = self.cache_dir / "chat_histories.json"
            self.chat_histories_dir = self.cache_dir / "chat-histories"
            self.app_values_file = self.cache_dir / "app_values.json"

            print(f"Chat histories file: {self.chat_histories_file}")
            print(f"Chat histories directory: {self.chat_histories_dir}")
            print(f"App values file: {self.app_values_file}")

            # Initialize files if they don't exist
            try:
                self._initialize_cache_files()
                print("Cache files initialized successfully")
            except Exception as e:
                print(f"ERROR: Failed to initialize cache files: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("WARNING: Cache service running without persistent storage!")
    
    def _initialize_cache_files(self):
        """Initialize cache files with empty structures if they don't exist"""
        try:
            if not self.chat_histories_file.exists():
                print(f"Creating new chat histories file: {self.chat_histories_file}")
                success = RobustFileOperations.safe_write_json(self.chat_histories_file, {})
                if not success:
                    print(f"ERROR: Failed to create chat histories file: {self.chat_histories_file}")
                else:
                    print(f"Successfully created chat histories file")
            else:
                print(f"Chat histories file already exists: {self.chat_histories_file}")

            # Create chat histories directory
            if self.chat_histories_dir:
                try:
                    self.chat_histories_dir.mkdir(parents=True, exist_ok=True)
                    print(f"Chat histories directory initialized: {self.chat_histories_dir}")
                    # Migrate existing chat history files from root cache dir to subdirectory
                    self._migrate_chat_history_files()
                except Exception as e:
                    print(f"ERROR: Failed to create chat histories directory: {e}")

            if not self.app_values_file.exists():
                print(f"Creating new app values file: {self.app_values_file}")
                success = RobustFileOperations.safe_write_json(self.app_values_file, {})
                if not success:
                    print(f"ERROR: Failed to create app values file: {self.app_values_file}")
                else:
                    print(f"Successfully created app values file")
            else:
                print(f"App values file already exists: {self.app_values_file}")
                # Migrate old last-thread-* keys to consolidated lastThreads object
                self._migrate_last_thread_keys()

        except Exception as e:
            print(f"ERROR: Exception in _initialize_cache_files: {e}")
            raise

    def _migrate_chat_history_files(self):
        """Migrate chat history files from root cache directory to chat-histories subdirectory"""
        if not self.cache_dir or not self.chat_histories_dir:
            return

        try:
            # Find all notebook_chat_*.json files in the root cache directory
            old_files = list(self.cache_dir.glob("notebook_chat_*.json"))
            old_backups = list(self.cache_dir.glob("notebook_chat_*.backup.*"))

            if not old_files and not old_backups:
                return

            migrated_count = 0
            for old_file in old_files:
                new_file = self.chat_histories_dir / old_file.name
                if not new_file.exists():
                    try:
                        shutil.move(str(old_file), str(new_file))
                        migrated_count += 1
                    except Exception as e:
                        print(f"ERROR: Failed to migrate {old_file.name}: {e}")

            # Also migrate backup files
            for old_backup in old_backups:
                new_backup = self.chat_histories_dir / old_backup.name
                if not new_backup.exists():
                    try:
                        shutil.move(str(old_backup), str(new_backup))
                    except Exception as e:
                        print(f"ERROR: Failed to migrate backup {old_backup.name}: {e}")

            if migrated_count > 0:
                print(f"Migrated {migrated_count} chat history files to {self.chat_histories_dir}")

        except Exception as e:
            print(f"ERROR: Failed to migrate chat history files: {e}")

    def _migrate_last_thread_keys(self):
        """Migrate old last-thread-* keys to consolidated lastThreads object"""
        if not self.app_values_file or not self.app_values_file.exists():
            return

        try:
            app_values = self.get_app_values()
            if not app_values:
                return

            # Find all last-thread-* keys
            last_thread_keys = [k for k in app_values.keys() if k.startswith('last-thread-')]
            if not last_thread_keys:
                return

            # Get or create the lastThreads object
            last_threads = app_values.get('lastThreads', {})
            if not isinstance(last_threads, dict):
                last_threads = {}

            migrated_count = 0
            for old_key in last_thread_keys:
                # Extract notebook ID from key (last-thread-{notebookId})
                notebook_id = old_key.replace('last-thread-', '')
                thread_id = app_values[old_key]

                # Only migrate if not already in lastThreads
                if notebook_id not in last_threads and thread_id:
                    last_threads[notebook_id] = thread_id
                    migrated_count += 1

                # Remove old key
                del app_values[old_key]

            if migrated_count > 0 or last_thread_keys:
                # Update lastThreads in app_values
                app_values['lastThreads'] = last_threads

                # Save updated app_values
                RobustFileOperations.safe_write_json(self.app_values_file, app_values)
                print(f"Migrated {migrated_count} last-thread keys to lastThreads object, removed {len(last_thread_keys)} old keys")

        except Exception as e:
            print(f"ERROR: Failed to migrate last-thread keys: {e}")
    
    def is_available(self) -> bool:
        """Check if cache service is available"""
        return self.cache_dir is not None and self.cache_dir.exists()
    
    def _is_notebook_chat_history_key(self, chat_id: str) -> bool:
        """Check if this is a notebook-specific chat history key"""
        return chat_id.startswith('chat-history-notebook-')
    
    def _get_notebook_chat_history_file(self, chat_id: str) -> Path:
        """Get the file path for a notebook-specific chat history"""
        if not self.chat_histories_dir:
            raise ValueError("Chat histories directory not available")

        # Extract notebook ID from the chat_id
        notebook_id = chat_id.replace('chat-history-notebook-', '')
        filename = f"notebook_chat_{notebook_id}.json"
        return self.chat_histories_dir / filename
    
    # Chat Histories Management
    def get_chat_histories(self) -> Dict[str, Any]:
        """Get all chat histories"""
        with self._lock:
            if not self.chat_histories_file:
                return {}
            return RobustFileOperations.safe_read_json(self.chat_histories_file, {})
    
    def get_chat_history(self, chat_id: str) -> Optional[Any]:
        """Get specific chat history"""
        # Handle notebook-specific chat histories
        if self._is_notebook_chat_history_key(chat_id):
            try:
                notebook_file = self._get_notebook_chat_history_file(chat_id)
                if notebook_file.exists():
                    print(f"Loading notebook chat history from: {notebook_file}")
                    return RobustFileOperations.safe_read_json(notebook_file, None)
                else:
                    print(f"Notebook chat history file does not exist: {notebook_file}")
                    return None
            except Exception as e:
                print(f"ERROR: Failed to get notebook chat history for {chat_id}: {e}")
                return None
        
        # Handle regular chat histories
        histories = self.get_chat_histories()
        return histories.get(chat_id)
    
    def set_chat_history(self, chat_id: str, history: Any) -> bool:
        """Set specific chat history"""
        with self._lock:
            # Handle notebook-specific chat histories
            if self._is_notebook_chat_history_key(chat_id):
                try:
                    notebook_file = self._get_notebook_chat_history_file(chat_id)
                    print(f"Saving notebook chat history to: {notebook_file}")
                    success = RobustFileOperations.safe_write_json(notebook_file, history)
                    if success:
                        print(f"Successfully saved notebook chat history for {chat_id}")
                    else:
                        print(f"ERROR: Failed to write notebook chat history for {chat_id}")
                    return success
                except Exception as e:
                    print(f"ERROR: Exception while saving notebook chat history for {chat_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            
            # Handle regular chat histories
            if not self.chat_histories_file:
                print(f"ERROR: Cannot save chat history for {chat_id} - no chat histories file configured")
                return False

            try:
                print(f"Attempting to save chat history for chat_id: {chat_id}")
                histories = self.get_chat_histories()
                print(f"Current histories count: {len(histories)}")

                histories[chat_id] = history
                print(f"Updated histories count: {len(histories)}")

                success = RobustFileOperations.safe_write_json(self.chat_histories_file, histories)
                if success:
                    print(f"Successfully saved chat history for {chat_id}")
                else:
                    print(f"ERROR: Failed to write chat history file for {chat_id}")

                return success
                
            except Exception as e:
                print(f"ERROR: Exception while saving chat history for {chat_id}: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    def delete_chat_history(self, chat_id: str) -> bool:
        """Delete specific chat history"""
        with self._lock:
            # Handle notebook-specific chat histories
            if self._is_notebook_chat_history_key(chat_id):
                try:
                    notebook_file = self._get_notebook_chat_history_file(chat_id)
                    if notebook_file.exists():
                        notebook_file.unlink()
                        print(f"Deleted notebook chat history file: {notebook_file}")
                    return True
                except Exception as e:
                    print(f"ERROR: Failed to delete notebook chat history for {chat_id}: {e}")
                    return False
            
            # Handle regular chat histories
            if not self.chat_histories_file:
                return False
            
            histories = self.get_chat_histories()
            if chat_id in histories:
                del histories[chat_id]
                return RobustFileOperations.safe_write_json(self.chat_histories_file, histories)
            return True
    
    def clear_chat_histories(self) -> bool:
        """Clear all chat histories"""
        with self._lock:
            if not self.chat_histories_file:
                return False
            return RobustFileOperations.safe_write_json(self.chat_histories_file, {})
    
    # App Values Management
    def get_app_values(self) -> Dict[str, Any]:
        """Get all app values"""
        with self._lock:
            if not self.app_values_file:
                return {}
            return RobustFileOperations.safe_read_json(self.app_values_file, {})
    
    def get_app_value(self, key: str, default: Any = None) -> Any:
        """Get specific app value"""
        values = self.get_app_values()
        return values.get(key, default)
    
    def set_app_value(self, key: str, value: Any) -> bool:
        """Set specific app value"""
        with self._lock:
            if not self.app_values_file:
                return False
            
            values = self.get_app_values()
            values[key] = value
            return RobustFileOperations.safe_write_json(self.app_values_file, values)
    
    def delete_app_value(self, key: str) -> bool:
        """Delete specific app value"""
        with self._lock:
            if not self.app_values_file:
                return False
            
            values = self.get_app_values()
            if key in values:
                del values[key]
                return RobustFileOperations.safe_write_json(self.app_values_file, values)
            return True
    
    def clear_app_values(self) -> bool:
        """Clear all app values"""
        with self._lock:
            if not self.app_values_file:
                return False
            return RobustFileOperations.safe_write_json(self.app_values_file, {})
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache service information"""
        info = {
            "available": self.is_available(),
            "cache_directory": str(self.cache_dir) if self.cache_dir else None,
            "chat_histories_directory": str(self.chat_histories_dir) if self.chat_histories_dir else None,
            "platform": platform.system(),
            "chat_histories_size": 0,
            "app_values_size": 0,
            "total_chat_histories": 0,
            "total_app_values": 0,
            "notebook_chat_files": 0,
            "notebook_chat_files_size": 0
        }

        if self.is_available():
            try:
                if self.chat_histories_file.exists():
                    info["chat_histories_size"] = self.chat_histories_file.stat().st_size
                    histories = self.get_chat_histories()
                    info["total_chat_histories"] = len(histories)

                if self.app_values_file.exists():
                    info["app_values_size"] = self.app_values_file.stat().st_size
                    values = self.get_app_values()
                    info["total_app_values"] = len(values)

                # Count notebook chat history files in the chat-histories subdirectory
                if self.chat_histories_dir and self.chat_histories_dir.exists():
                    notebook_files = list(self.chat_histories_dir.glob("notebook_chat_*.json"))
                    info["notebook_chat_files"] = len(notebook_files)
                    info["notebook_chat_files_size"] = sum(f.stat().st_size for f in notebook_files if f.exists())

            except Exception as e:
                info["error"] = str(e)

        return info


class CheckpointCacheManager:
    """Dedicated cache manager for notebook checkpoints with file-per-checkpoint storage.

    Storage structure:
    cache_dir/
      checkpoints/
        {notebook_id}/
          {checkpoint_id}.json
          ...
    """

    def __init__(self):
        self.cache_dir = CacheDirectoryManager.find_usable_cache_directory()
        self.checkpoints_dir = None
        self._lock = threading.RLock()

        if self.cache_dir:
            self.checkpoints_dir = self.cache_dir / "checkpoints"

            # Initialize checkpoints directory
            try:
                self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
                print(f"Checkpoint cache directory initialized: {self.checkpoints_dir}")
            except Exception as e:
                print(f"ERROR: Failed to create checkpoints directory: {e}")
                self.checkpoints_dir = None
        else:
            print("WARNING: Checkpoint cache manager running without persistent storage!")

    def is_available(self) -> bool:
        """Check if checkpoint cache is available"""
        return self.checkpoints_dir is not None and self.checkpoints_dir.exists()

    def _get_notebook_dir(self, notebook_id: str) -> Path:
        """Get the directory for a specific notebook's checkpoints"""
        if not self.checkpoints_dir:
            raise ValueError("Checkpoints directory not available")
        # Sanitize notebook_id for filesystem safety
        safe_id = notebook_id.replace('/', '_').replace('\\', '_').replace(':', '_')
        return self.checkpoints_dir / safe_id

    def _get_checkpoint_path(self, notebook_id: str, checkpoint_id: str) -> Path:
        """Get the file path for a specific checkpoint"""
        notebook_dir = self._get_notebook_dir(notebook_id)
        # Sanitize checkpoint_id for filesystem safety
        safe_checkpoint_id = checkpoint_id.replace('/', '_').replace('\\', '_').replace(':', '_')
        return notebook_dir / f"{safe_checkpoint_id}.json"

    def get_checkpoint(self, notebook_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Read a single checkpoint"""
        if not self.is_available():
            return None

        try:
            checkpoint_path = self._get_checkpoint_path(notebook_id, checkpoint_id)
            return RobustFileOperations.safe_read_json(checkpoint_path, None)
        except Exception as e:
            print(f"ERROR: reading checkpoint {checkpoint_id} for notebook {notebook_id}: {e}")
            return None

    def set_checkpoint(self, notebook_id: str, checkpoint_id: str, checkpoint_data: Dict[str, Any]) -> bool:
        """Write a single checkpoint"""
        if not self.is_available():
            return False

        with self._lock:
            try:
                notebook_dir = self._get_notebook_dir(notebook_id)
                notebook_dir.mkdir(parents=True, exist_ok=True)

                checkpoint_path = self._get_checkpoint_path(notebook_id, checkpoint_id)
                return RobustFileOperations.safe_write_json(checkpoint_path, checkpoint_data)
            except Exception as e:
                print(f"ERROR: writing checkpoint {checkpoint_id} for notebook {notebook_id}: {e}")
                return False

    def delete_checkpoint(self, notebook_id: str, checkpoint_id: str) -> bool:
        """Delete a single checkpoint"""
        if not self.is_available():
            return False

        with self._lock:
            try:
                checkpoint_path = self._get_checkpoint_path(notebook_id, checkpoint_id)
                if checkpoint_path.exists():
                    checkpoint_path.unlink()
                return True
            except Exception as e:
                print(f"ERROR: deleting checkpoint {checkpoint_id} for notebook {notebook_id}: {e}")
                return False

    def list_checkpoints(self, notebook_id: str) -> List[Dict[str, Any]]:
        """List all checkpoints for a notebook, sorted by timestamp"""
        if not self.is_available():
            return []

        try:
            notebook_dir = self._get_notebook_dir(notebook_id)
            if not notebook_dir.exists():
                return []

            checkpoints = []
            for checkpoint_file in notebook_dir.glob("*.json"):
                checkpoint_data = RobustFileOperations.safe_read_json(checkpoint_file, None)
                if checkpoint_data:
                    checkpoints.append(checkpoint_data)

            # Sort by timestamp
            checkpoints.sort(key=lambda x: x.get('timestamp', 0))
            return checkpoints
        except Exception as e:
            print(f"ERROR: listing checkpoints for notebook {notebook_id}: {e}")
            return []

    def list_notebook_ids(self) -> List[str]:
        """List all notebook IDs that have checkpoints"""
        if not self.is_available():
            return []

        try:
            notebook_ids = []
            for notebook_dir in self.checkpoints_dir.iterdir():
                if notebook_dir.is_dir():
                    notebook_ids.append(notebook_dir.name)
            return notebook_ids
        except Exception as e:
            print(f"ERROR: listing notebook IDs: {e}")
            return []

    def clear_checkpoints_for_notebook(self, notebook_id: str) -> bool:
        """Delete all checkpoints for a notebook"""
        if not self.is_available():
            return False

        with self._lock:
            try:
                notebook_dir = self._get_notebook_dir(notebook_id)
                if notebook_dir.exists():
                    shutil.rmtree(notebook_dir)
                return True
            except Exception as e:
                print(f"ERROR: clearing checkpoints for notebook {notebook_id}: {e}")
                return False

    def clear_checkpoints_after(self, notebook_id: str, checkpoint_id: str) -> bool:
        """Delete all checkpoints after a specific checkpoint (by timestamp)"""
        if not self.is_available():
            return False

        with self._lock:
            try:
                checkpoints = self.list_checkpoints(notebook_id)
                target_checkpoint = None
                for cp in checkpoints:
                    if cp.get('id') == checkpoint_id:
                        target_checkpoint = cp
                        break

                if not target_checkpoint:
                    return False

                target_timestamp = target_checkpoint.get('timestamp', 0)

                # Delete checkpoints with timestamps after the target
                for cp in checkpoints:
                    if cp.get('timestamp', 0) > target_timestamp:
                        self.delete_checkpoint(notebook_id, cp.get('id', ''))

                return True
            except Exception as e:
                print(f"ERROR: clearing checkpoints after {checkpoint_id} for notebook {notebook_id}: {e}")
                return False

    def get_all_checkpoints(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all checkpoints for all notebooks (for migration/export)"""
        if not self.is_available():
            return {}

        result = {}
        for notebook_id in self.list_notebook_ids():
            result[notebook_id] = self.list_checkpoints(notebook_id)
        return result

    def import_checkpoints(self, checkpoints_data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Import checkpoints from the old format (for migration)"""
        if not self.is_available():
            return False

        with self._lock:
            try:
                for notebook_id, checkpoint_list in checkpoints_data.items():
                    for checkpoint in checkpoint_list:
                        checkpoint_id = checkpoint.get('id')
                        if checkpoint_id:
                            self.set_checkpoint(notebook_id, checkpoint_id, checkpoint)
                return True
            except Exception as e:
                print(f"ERROR: importing checkpoints: {e}")
                return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return cache statistics"""
        stats = {
            "available": self.is_available(),
            "checkpoints_directory": str(self.checkpoints_dir) if self.checkpoints_dir else None,
            "total_notebooks": 0,
            "total_checkpoints": 0,
            "total_size_bytes": 0
        }

        if self.is_available():
            try:
                notebook_ids = self.list_notebook_ids()
                stats["total_notebooks"] = len(notebook_ids)

                total_checkpoints = 0
                total_size = 0

                for notebook_id in notebook_ids:
                    notebook_dir = self._get_notebook_dir(notebook_id)
                    checkpoint_files = list(notebook_dir.glob("*.json"))
                    total_checkpoints += len(checkpoint_files)
                    total_size += sum(f.stat().st_size for f in checkpoint_files if f.exists())

                stats["total_checkpoints"] = total_checkpoints
                stats["total_size_bytes"] = total_size

            except Exception as e:
                stats["error"] = str(e)

        return stats


class CellStateCacheManager:
    """Dedicated cache manager for notebook cell states with file-per-notebook storage.

    Storage structure:
    cache_dir/
      cell-states/
        {notebook_id}.json
        ...
    """

    def __init__(self):
        self.cache_dir = CacheDirectoryManager.find_usable_cache_directory()
        self.cell_states_dir = None
        self._lock = threading.RLock()

        if self.cache_dir:
            self.cell_states_dir = self.cache_dir / "cell-states"

            # Initialize cell states directory
            try:
                self.cell_states_dir.mkdir(parents=True, exist_ok=True)
                print(f"Cell state cache directory initialized: {self.cell_states_dir}")
            except Exception as e:
                print(f"ERROR: Failed to create cell states directory: {e}")
                self.cell_states_dir = None
        else:
            print("WARNING: Cell state cache manager running without persistent storage!")

    def is_available(self) -> bool:
        """Check if cell state cache is available"""
        return self.cell_states_dir is not None and self.cell_states_dir.exists()

    def _get_cell_state_path(self, notebook_id: str) -> Path:
        """Get the file path for a notebook's cell state"""
        if not self.cell_states_dir:
            raise ValueError("Cell states directory not available")
        # Sanitize notebook_id for filesystem safety
        safe_id = notebook_id.replace('/', '_').replace('\\', '_').replace(':', '_')
        return self.cell_states_dir / f"{safe_id}.json"

    def get_cell_state(self, notebook_id: str) -> Optional[Dict[str, Any]]:
        """Read cell state for a notebook"""
        if not self.is_available():
            return None

        try:
            cell_state_path = self._get_cell_state_path(notebook_id)
            return RobustFileOperations.safe_read_json(cell_state_path, None)
        except Exception as e:
            print(f"ERROR: reading cell state for notebook {notebook_id}: {e}")
            return None

    def set_cell_state(self, notebook_id: str, cell_state_data: Dict[str, Any]) -> bool:
        """Write cell state for a notebook"""
        if not self.is_available():
            return False

        with self._lock:
            try:
                cell_state_path = self._get_cell_state_path(notebook_id)
                return RobustFileOperations.safe_write_json(cell_state_path, cell_state_data)
            except Exception as e:
                print(f"ERROR: writing cell state for notebook {notebook_id}: {e}")
                return False

    def delete_cell_state(self, notebook_id: str) -> bool:
        """Delete cell state for a notebook"""
        if not self.is_available():
            return False

        with self._lock:
            try:
                cell_state_path = self._get_cell_state_path(notebook_id)
                if cell_state_path.exists():
                    cell_state_path.unlink()
                return True
            except Exception as e:
                print(f"ERROR: deleting cell state for notebook {notebook_id}: {e}")
                return False

    def list_notebook_ids(self) -> List[str]:
        """List all notebook IDs that have cell states"""
        if not self.is_available():
            return []

        try:
            notebook_ids = []
            for cell_state_file in self.cell_states_dir.glob("*.json"):
                # Remove .json extension to get notebook ID
                notebook_ids.append(cell_state_file.stem)
            return notebook_ids
        except Exception as e:
            print(f"ERROR: listing notebook IDs for cell states: {e}")
            return []

    def clear_all_cell_states(self) -> bool:
        """Delete all cell states"""
        if not self.is_available():
            return False

        with self._lock:
            try:
                for cell_state_file in self.cell_states_dir.glob("*.json"):
                    cell_state_file.unlink()
                return True
            except Exception as e:
                print(f"ERROR: clearing all cell states: {e}")
                return False

    def migrate_from_app_values(self, app_values: Dict[str, Any]) -> Dict[str, int]:
        """Migrate cell states from old app_values format to file-per-notebook"""
        if not self.is_available():
            return {"migrated": 0, "errors": 0}

        migrated = 0
        errors = 0
        prefix = "notebook-cell-state:"

        with self._lock:
            for key, value in list(app_values.items()):
                if key.startswith(prefix):
                    notebook_id = key[len(prefix):]
                    try:
                        if self.set_cell_state(notebook_id, value):
                            migrated += 1
                        else:
                            errors += 1
                    except Exception as e:
                        print(f"ERROR: migrating cell state for {notebook_id}: {e}")
                        errors += 1

        return {"migrated": migrated, "errors": errors}

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return cache statistics"""
        stats = {
            "available": self.is_available(),
            "cell_states_directory": str(self.cell_states_dir) if self.cell_states_dir else None,
            "total_notebooks": 0,
            "total_size_bytes": 0
        }

        if self.is_available():
            try:
                cell_state_files = list(self.cell_states_dir.glob("*.json"))
                stats["total_notebooks"] = len(cell_state_files)
                stats["total_size_bytes"] = sum(f.stat().st_size for f in cell_state_files if f.exists())
            except Exception as e:
                stats["error"] = str(e)

        return stats


class FileScanCacheManager:
    """Dedicated cache manager for file scanning operations with individual file caching"""

    def __init__(self):
        self.cache_dir = CacheDirectoryManager.find_usable_cache_directory()
        self.file_scans_dir = None
        self.scanned_directories_file = None
        self._lock = threading.RLock()

        if self.cache_dir:
            self.file_scans_dir = self.cache_dir / "file_scans"
            self.scanned_directories_file = self.file_scans_dir / "scanned_directories.json"
            
            # Initialize file scans directory
            try:
                self.file_scans_dir.mkdir(parents=True, exist_ok=True)
                print(f"File scan cache directory initialized: {self.file_scans_dir}")
            except Exception as e:
                print(f"ERROR: Failed to create file scans directory: {e}")
                self.file_scans_dir = None
                self.scanned_directories_file = None
        else:
            print("WARNING: File scan cache manager running without persistent storage!")
    
    def _get_file_cache_path(self, file_path: str) -> Path:
        """Generate cache file path using MD5 hash of absolute file path"""
        if not self.file_scans_dir:
            raise ValueError("File scans directory not available")
        
        # Create hash from absolute file path
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        return self.file_scans_dir / f"{file_hash}.json"
    
    def is_available(self) -> bool:
        """Check if file scan cache is available"""
        return self.file_scans_dir is not None and self.file_scans_dir.exists()
    
    def get_file_entry(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read individual file cache entry"""
        if not self.is_available():
            return None
        
        try:
            cache_path = self._get_file_cache_path(file_path)
            return RobustFileOperations.safe_read_json(cache_path, None)
        except Exception as e:
            print(f"ERROR: reading file cache for {file_path}: {e}")
            return None
    
    def set_file_entry(self, file_path: str, entry: Dict[str, Any]) -> bool:
        """Write individual file cache entry"""
        if not self.is_available():
            return False
        
        try:
            cache_path = self._get_file_cache_path(file_path)
            return RobustFileOperations.safe_write_json(cache_path, entry)
        except Exception as e:
            print(f"ERROR: writing file cache for {file_path}: {e}")
            return False
    
    def delete_file_entry(self, file_path: str) -> bool:
        """Delete individual file cache entry"""
        if not self.is_available():
            return False
        
        try:
            cache_path = self._get_file_cache_path(file_path)
            if cache_path.exists():
                cache_path.unlink()
                return True
            return True  # File doesn't exist, consider it deleted
        except Exception as e:
            print(f"ERROR: deleting file cache for {file_path}: {e}")
            return False
    
    def get_scanned_directories(self) -> List[Dict[str, Any]]:
        """Read scanned directories list"""
        if not self.scanned_directories_file:
            return []
        
        try:
            return RobustFileOperations.safe_read_json(self.scanned_directories_file, [])
        except Exception as e:
            print(f"ERROR: reading scanned directories: {e}")
            return []
    
    def set_scanned_directories(self, directories: List[Dict[str, Any]]) -> bool:
        """Write scanned directories list"""
        if not self.scanned_directories_file:
            return False
        
        try:
            return RobustFileOperations.safe_write_json(self.scanned_directories_file, directories)
        except Exception as e:
            print(f"ERROR: writing scanned directories: {e}")
            return False
    
    def clear_all_file_entries(self) -> bool:
        """Clear all cached file entries"""
        if not self.is_available():
            return False
        
        try:
            # Remove all .json files except scanned_directories.json
            for cache_file in self.file_scans_dir.glob("*.json"):
                if cache_file.name != "scanned_directories.json":
                    cache_file.unlink()
            return True
        except Exception as e:
            print(f"ERROR: clearing file entries: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Return cache statistics"""
        stats = {
            "available": self.is_available(),
            "file_scans_directory": str(self.file_scans_dir) if self.file_scans_dir else None,
            "total_file_entries": 0,
            "total_cache_size": 0,
            "scanned_directories_count": 0
        }
        
        if self.is_available():
            try:
                # Count file entries (excluding scanned_directories.json)
                file_entries = list(self.file_scans_dir.glob("*.json"))
                file_entries = [f for f in file_entries if f.name != "scanned_directories.json"]
                stats["total_file_entries"] = len(file_entries)
                stats["total_cache_size"] = sum(f.stat().st_size for f in file_entries if f.exists())
                
                # Count scanned directories
                directories = self.get_scanned_directories()
                stats["scanned_directories_count"] = len(directories)
                
            except Exception as e:
                stats["error"] = str(e)
        
        return stats


# Global cache service instances
_cache_service = None
_file_scan_cache_manager = None
_checkpoint_cache_manager = None
_cell_state_cache_manager = None


def get_cache_service() -> PersistentCacheService:
    """Get the global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = PersistentCacheService()
    return _cache_service


def get_file_scan_cache_manager() -> FileScanCacheManager:
    """Get the global file scan cache manager instance"""
    global _file_scan_cache_manager
    if _file_scan_cache_manager is None:
        _file_scan_cache_manager = FileScanCacheManager()
    return _file_scan_cache_manager


def get_checkpoint_cache_manager() -> CheckpointCacheManager:
    """Get the global checkpoint cache manager instance"""
    global _checkpoint_cache_manager
    if _checkpoint_cache_manager is None:
        _checkpoint_cache_manager = CheckpointCacheManager()
    return _checkpoint_cache_manager


def get_cell_state_cache_manager() -> CellStateCacheManager:
    """Get the global cell state cache manager instance"""
    global _cell_state_cache_manager
    if _cell_state_cache_manager is None:
        _cell_state_cache_manager = CellStateCacheManager()
    return _cell_state_cache_manager
