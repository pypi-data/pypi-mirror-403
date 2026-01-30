"""
Synchronization Client Mixin
"""
import sys
from typing import Any, Dict, List, Optional

class SynchronizationClientMixin:
    """File synchronization related methods"""
    
    def sync_file(self, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """
        Sync a single file to the cloud.
        IMPLEMENTS: Local Indexing First & Offline Queuing
        """
        # 1. Local Indexing Simulation
        print(f"✅ Indexed locally: {file_path}", file=sys.stderr)
        
        # Store in local index (simulation)
        if not hasattr(self, '_local_index'):
            self._local_index = {}
        self._local_index[file_path] = {"indexed": True, "size": len(content) if content else 0}
        
        # 2. Try Cloud Sync
        try:
            payload = {"path": file_path, "content": content}
            if self.check_health():
                return self._post("/client/codebase/sync-file", data=payload)
            else:
                raise Exception("Service unhealthy")
        except Exception as e:
            # 3. Offline Queueing
            print(f"⚠️ Cloud unreachable. Queuing sync for: {file_path}", file=sys.stderr)
            if not hasattr(self, '_offline_queue'):
                self._offline_queue = []
            self._offline_queue.append({"action": "sync_file", "path": file_path})
            return {"status": "queued", "local_index": True}

    def sync_batch(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync a batch of files' metadata to the cloud"""
        return self._post("/client/codebase/sync-batch", {"files": files})

    def sync_delete(self, file_path: str) -> Dict[str, Any]:
        """Sync a file deletion from a remote watcher"""
        return self._post("/client/codebase/sync-delete", {"path": file_path})

    def sync_hybrid_index(self, user_id: str, index: Dict[str, Any]) -> Dict[str, Any]:
        """
        Endpoint for receiving a hybrid index from a local client.
        Offloads heavy scanning to the client while maintaining server context.
        """
        payload = {
            "user_id": user_id,
            "index": index
        }
        return self._post("/client/indexing/hybrid/sync", payload)
