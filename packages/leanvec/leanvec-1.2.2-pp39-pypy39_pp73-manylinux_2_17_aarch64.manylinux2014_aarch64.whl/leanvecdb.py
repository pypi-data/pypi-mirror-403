import uuid
import os
import leanvec
import atexit
import gc
import time
import threading
import math
import orjson
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# --- Cross-Platform Locking Support ---
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

class CollectionLock:
    """File-based lock for a collection, providing both thread and process safety."""
    
    def __init__(self, collection_path: str):
        self.lock_path = os.path.join(collection_path, '.collection.lock')
        self.lock_file = None
        self._thread_lock = threading.RLock()
        self._ensure_lock_file()
    
    def _ensure_lock_file(self):
        """Ensure the lock file exists."""
        os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
        if not os.path.exists(self.lock_path):
            try:
                open(self.lock_path, 'a').close()
            except OSError:
                pass
    
    @contextmanager
    def read_lock(self):
        """Acquire a shared read lock."""
        with self._thread_lock:
            if HAS_FCNTL:
                self._ensure_lock_file()
                self.lock_file = open(self.lock_path, 'r')
                try:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_SH)
                    yield
                finally:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                    self.lock_file.close()
                    self.lock_file = None
            else:
                # Fallback for Windows (Thread safe, but Process safety relies on Rust internal locks)
                yield
    
    @contextmanager
    def write_lock(self):
        """Acquire an exclusive write lock."""
        with self._thread_lock:
            if HAS_FCNTL:
                self._ensure_lock_file()
                self.lock_file = open(self.lock_path, 'r')
                try:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)
                    yield
                finally:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                    self.lock_file.close()
                    self.lock_file = None
            else:
                yield


class NoOpLock:
    """No-op lock that does nothing - for single-threaded use."""
    @contextmanager
    def read_lock(self): yield
    @contextmanager
    def write_lock(self): yield


class VersionTracker:
    """Track collection version to detect changes from other processes."""
    
    def __init__(self, collection_path: str):
        self.version_path = os.path.join(collection_path, '.version')
        self._ensure_version_file()
    
    def _ensure_version_file(self):
        os.makedirs(os.path.dirname(self.version_path), exist_ok=True)
        if not os.path.exists(self.version_path):
            self._write_version(0)
    
    def _write_version(self, version: int):
        # Atomic write pattern to prevent reading partial integers
        tmp_path = self.version_path + ".tmp"
        with open(tmp_path, 'w') as f:
            f.write(str(version))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, self.version_path)
    
    def get_version(self) -> int:
        try:
            with open(self.version_path, 'r') as f:
                content = f.read().strip()
                return int(content) if content else 0
        except (FileNotFoundError, ValueError):
            return 0
    
    def increment_version(self):
        current = self.get_version()
        self._write_version(current + 1)


class NoOpVersionTracker:
    def get_version(self) -> int: return 0
    def increment_version(self): pass


class LeanVecDB:
    def __init__(self, base_path: str = 'leanvec_root', auto_persist: bool = True, thread_safe: bool = False):
        """Initialize LeanVecDB.
        
        Args:
            base_path: Directory to store database files
            auto_persist: Whether to automatically persist on exit
            thread_safe: If True, enables thread and process safety with locking and version tracking.
                        If False, disables all safety mechanisms for maximum performance in single-threaded scenarios.
        """
        self.base_path = base_path
        self.thread_safe = thread_safe
        
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        self.collections: Dict[str, leanvec.LeanDB] = {}
        self.dimensions: Dict[str, int] = {}
        self.collection_locks: Dict[str, CollectionLock] = {}
        self.version_trackers: Dict[str, VersionTracker] = {}
        self.local_versions: Dict[str, int] = {}
        
        # Global lock for managing the `self.collections` dict itself
        self._collections_lock = threading.RLock() if thread_safe else None
        
        self._load_existing_collections()

        self.start_time = time.time()
        self.last_access_time = time.time()
        self.maintenance_interval = 86400 
        self.idle_threshold = 3600
        self.stop_maintenance = False
        
        self.m_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self.m_thread.start()

        if auto_persist:
            atexit.register(self.persist_all)

    def _get_col_path(self, name: str) -> str:
        return os.path.join(self.base_path, name)

    def _get_collection_lock(self, name: str):
        if not self.thread_safe:
            return NoOpLock()
        
        with self._collections_lock:
            if name not in self.collection_locks:
                path = self._get_col_path(name)
                self.collection_locks[name] = CollectionLock(path)
            return self.collection_locks[name]
    
    def _get_version_tracker(self, name: str):
        if not self.thread_safe:
            return NoOpVersionTracker()
        
        with self._collections_lock:
            if name not in self.version_trackers:
                path = self._get_col_path(name)
                self.version_trackers[name] = VersionTracker(path)
            return self.version_trackers[name]

    def _load_existing_collections(self):
        if not os.path.exists(self.base_path):
            return
        for name in os.listdir(self.base_path):
            path = self._get_col_path(name)
            if os.path.isdir(path):
                cfg_path = os.path.join(path, 'config.json')
                if os.path.exists(cfg_path):
                    try:
                        with open(cfg_path, 'rb') as f:
                            self.dimensions[name] = orjson.loads(f.read()).get('dimension')
                    except: 
                        pass

    def _needs_reload(self, collection: str) -> bool:
        if not self.thread_safe:
            return False
        
        if collection not in self.local_versions:
            return True
        
        tracker = self._get_version_tracker(collection)
        disk_version = tracker.get_version()
        return disk_version > self.local_versions.get(collection, -1)

    def _reload_collection(self, collection: str):
        """Force a reload of the Rust object from disk."""
        if not self.thread_safe:
            return
        
        # Helper to do the actual reload logic
        def do_reload():
            if collection in self.collections:
                # Explicitly delete to drop Rust Arc reference immediately
                del self.collections[collection]
                gc.collect() 
            
            path = self._get_col_path(collection)
            self.collections[collection] = leanvec.LeanDB(path)
            
            tracker = self._get_version_tracker(collection)
            self.local_versions[collection] = tracker.get_version()

        if self._collections_lock:
            with self._collections_lock:
                do_reload()
        else:
            do_reload()

    def _ensure_collection(self, name: str) -> leanvec.LeanDB:
        self.last_access_time = time.time()
        
        # Helper to init collection
        def init_col():
            if name not in self.collections:
                path = self._get_col_path(name)
                if not os.path.exists(path):
                    os.makedirs(path)
                self.collections[name] = leanvec.LeanDB(path)
                if self.thread_safe:
                    tracker = self._get_version_tracker(name)
                    self.local_versions[name] = tracker.get_version()

        if self.thread_safe and self._collections_lock:
            with self._collections_lock:
                init_col()
        else:
            init_col()
        
        return self.collections[name]

    def list_collections(self) -> List[str]:
        keys = set(list(self.collections.keys()) + list(self.dimensions.keys()))
        return list(keys)

    def store_embedding(self, embedding: List[float], metadata_dict: Optional[Dict[str, Any]] = None, collection: str = "default", ttl: Optional[int] = None) -> str:
        metadatas = [metadata_dict] if metadata_dict is not None else None
        return self.store_embeddings_batch([embedding], metadatas, collection=collection, ttl=ttl)[0]

    def store_embeddings_batch(self, embeddings: List[List[float]], metadatas: Optional[List[Dict[str, Any]]] = None, collection: str = "default", ttl: Optional[int] = None) -> List[str]:
        if hasattr(embeddings, "tolist"):
            embeddings = embeddings.tolist()
        
        if not embeddings: 
            return []
        
        col_lock = self._get_collection_lock(collection)
        
        with col_lock.write_lock():
            if self.thread_safe and self._needs_reload(collection):
                self._reload_collection(collection)
            
            db = self._ensure_collection(collection)
            input_dim = len(embeddings[0])
            
            # Update Dimensions Config
            if collection not in self.dimensions:
                self.dimensions[collection] = input_dim
                path = self._get_col_path(collection)
                os.makedirs(path, exist_ok=True)
                with open(os.path.join(path, 'config.json'), 'wb') as f:
                    f.write(orjson.dumps({'dimension': input_dim}))
            elif input_dim != self.dimensions[collection]:
                raise ValueError(f"Dimension Mismatch: Expected {self.dimensions[collection]}, Got {input_dim}")

            if metadatas is None: 
                metadatas = [{} for _ in range(len(embeddings))]
            
            ids = []
            for i, vec in enumerate(embeddings):
                meta = metadatas[i] if i < len(metadatas) and metadatas[i] is not None else {}
                if not isinstance(meta, dict): meta = {}
                
                doc_id = str(meta.get("id") or meta.get("_id") or uuid.uuid4())
                meta["id"] = doc_id
                
                try:
                    meta_str = orjson.dumps(meta).decode('utf-8')
                except:
                    meta_str = '{"id":"' + doc_id + '"}'

                db.add(doc_id, vec, meta_str, ttl)
                ids.append(doc_id)
            
            if self.thread_safe:
                db.persist()
                tracker = self._get_version_tracker(collection)
                tracker.increment_version()
                self.local_versions[collection] = tracker.get_version()
                
            return ids
    
    def search(self, 
               query_embedding: List[float], 
               k: int = 5, 
               filters: Optional[Dict[str, Any]] = None, 
               collection: str = "default", 
               include_metadata: bool = True,
               force_fresh: bool = False) -> List[Dict[str, Any]]:
        
        col_lock = self._get_collection_lock(collection)
        
        # Use WRITE lock if we need to reload (to prevent race conditions during reload)
        # Use READ lock otherwise (allowing concurrent Python threads to search)
        requires_write = self.thread_safe and (force_fresh or self._needs_reload(collection))
        
        lock_manager = col_lock.write_lock() if requires_write else col_lock.read_lock()
        
        with lock_manager:
            if self.thread_safe and self._needs_reload(collection):
                self._reload_collection(collection)
            
            db = self._ensure_collection(collection)
            filter_str = orjson.dumps(filters).decode('utf-8') if filters else None
            
            # The Rust method releases GIL, allowing parallelism here
            raw_results = db.search(query_embedding, k, filter_str, include_metadata)
        
        # Formatting results does not need the lock
        formatted = []
        for r in raw_results:
            item = {"id": r[0], "score": r[1]}
            if include_metadata and len(r[2]) > 0:
                item["metadata"] = orjson.loads(r[2])
            elif include_metadata:
                item["metadata"] = {}
            formatted.append(item)
            
        return formatted

    def _calculate_autocut(self, scores: List[float]) -> Optional[int]:
        for i in range(1, len(scores)):
            if scores[i-1] > 0 and (scores[i] - scores[i-1]) / scores[i-1] > 0.2:
                return i
        return None

    def delete(self, metadata_filter: Dict[str, Any], collection: str = "default") -> int:
        if collection not in self.collections and collection not in self.dimensions:
            return 0
        
        col_lock = self._get_collection_lock(collection)
        
        with col_lock.write_lock():
            if self.thread_safe and self._needs_reload(collection):
                self._reload_collection(collection)
            
            db = self._ensure_collection(collection)
            count = db.delete_by_filter(orjson.dumps(metadata_filter).decode('utf-8'))
            
            if self.thread_safe:
                db.persist()
                tracker = self._get_version_tracker(collection)
                tracker.increment_version()
                self.local_versions[collection] = tracker.get_version()
            
            return count

    def count(self, collection: str = "default") -> int:
        if collection not in self.collections and collection not in self.dimensions:
            return 0
        
        col_lock = self._get_collection_lock(collection)
        
        requires_reload = self.thread_safe and self._needs_reload(collection)
        lock_manager = col_lock.write_lock() if requires_reload else col_lock.read_lock()

        with lock_manager:
            if requires_reload:
                self._reload_collection(collection)
            return self._ensure_collection(collection).count()

    def persist_all(self):
        if not os.path.exists(self.base_path): return
        names = list(self.collections.keys())
        for name in names:
            try:
                self.persist(name)
            except Exception:
                pass

    def persist(self, collection: str = "default"):
        if collection not in self.collections: return
        
        col_lock = self._get_collection_lock(collection)
        
        with col_lock.write_lock():
            # Minimal garbage collection to ensure cleaned up memory before persistence
            gc.collect() 
            self.collections[collection].persist()
            
            if self.thread_safe:
                tracker = self._get_version_tracker(collection)
                tracker.increment_version()
                self.local_versions[collection] = tracker.get_version()

    def vacuum(self, collection: str = "default"):
        """Compacts the database storage."""
        col_lock = self._get_collection_lock(collection)
        
        with col_lock.write_lock():
            # Must reload before vacuuming to ensure we have handles to current files
            if self.thread_safe and self._needs_reload(collection):
                self._reload_collection(collection)
            
            db = self._ensure_collection(collection)
            db.vacuum()
            
            if self.thread_safe:
                tracker = self._get_version_tracker(collection)
                tracker.increment_version()
                self.local_versions[collection] = tracker.get_version()

    def _maintenance_loop(self):
        while not self.stop_maintenance:
            time.sleep(1)
            uptime = time.time() - self.start_time
            idle_time = time.time() - self.last_access_time
            
            if uptime > self.maintenance_interval and idle_time > self.idle_threshold:
                try:
                    self.persist_all()
                except Exception:
                    pass
                self.start_time = time.time()

    def close(self):
        self.stop_maintenance = True
        if self.m_thread.is_alive():
            self.m_thread.join(timeout=5)
        self.persist_all()
