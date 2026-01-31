"""Thread-safe cleanup manager."""

import asyncio
import os
import shutil
import threading
from typing import Set


class CleanupManager:
    """Thread-safe temp file/directory cleanup manager."""
    
    def __init__(self):
        """Initialize cleanup manager."""
        self._tracked_files: Set[str] = set()
        self._tracked_dirs: Set[str] = set()
        self._lock = threading.Lock()
    
    def track_file(self, file_path: str):
        """Track file for cleanup."""
        with self._lock:
            self._tracked_files.add(file_path)
    
    def track_directory(self, dir_path: str):
        """Track directory for cleanup."""
        with self._lock:
            self._tracked_dirs.add(dir_path)
    
    async def cleanup_file(self, file_path: str, ignore_errors: bool = True):
        """
        Clean up single file.
        
        Args:
            file_path: Path to file
            ignore_errors: Whether to ignore errors
        """
        def _cleanup():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                with self._lock:
                    self._tracked_files.discard(file_path)
            except Exception as e:
                if not ignore_errors:
                    raise
                # Silently ignore cleanup errors
                pass
        
        await asyncio.to_thread(_cleanup)
    
    async def cleanup_directory(self, dir_path: str, ignore_errors: bool = True):
        """
        Clean up directory and all contents.
        
        Args:
            dir_path: Path to directory
            ignore_errors: Whether to ignore errors
        """
        def _cleanup():
            try:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path, ignore_errors=ignore_errors)
                with self._lock:
                    self._tracked_dirs.discard(dir_path)
            except Exception as e:
                if not ignore_errors:
                    raise
                # Silently ignore cleanup errors
                pass
        
        await asyncio.to_thread(_cleanup)
    
    async def cleanup_all(self, ignore_errors: bool = True):
        """
        Clean up all tracked files and directories.
        
        Args:
            ignore_errors: Whether to ignore errors
        """
        # Copy sets to avoid modification during iteration
        with self._lock:
            files = list(self._tracked_files)
            dirs = list(self._tracked_dirs)
        
        # Clean up files
        await asyncio.gather(
            *[self.cleanup_file(f, ignore_errors) for f in files],
            return_exceptions=True
        )
        
        # Clean up directories
        await asyncio.gather(
            *[self.cleanup_directory(d, ignore_errors) for d in dirs],
            return_exceptions=True
        )
    
    async def __aenter__(self):
        """Enter async context."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and cleanup."""
        await self.cleanup_all(ignore_errors=True)
        return False


async def cleanup_files(file_paths: list):
    """
    Cleanup multiple files.
    
    Args:
        file_paths: List of file paths to clean up
    """
    manager = CleanupManager()
    await asyncio.gather(
        *[manager.cleanup_file(f) for f in file_paths],
        return_exceptions=True
    )

