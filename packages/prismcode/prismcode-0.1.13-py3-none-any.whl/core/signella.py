"""
Signella - Super simple shared memory across Python scripts!

No server required - just pip install diskcache

Install: pip install diskcache
"""
import json
import threading
import time
from pathlib import Path
from typing import Any, Generator
from diskcache import Cache, Deque


class Signella:
    """Use shared memory like Python variables - data shared across all scripts!"""

    def __init__(self, path: str = '/tmp/signella'):
        self._cache = Cache(path)
        self._path = path

    # ============ SYNTAX OPTION 1: Dict-like with dot notation ============
    # Usage: store.container.status = "starting"
    #        status = store.container.status()

    def __getattr__(self, key):
        """Enable dot notation: store.container.status"""
        if key.startswith('_'):
            raise AttributeError(key)
        return _Namespace(self._cache, key)

    # ============ SYNTAX OPTION 2: Simple brackets ============
    # Usage: store['container:1:status'] = "starting"
    #        status = store['container:1:status']

    def __getitem__(self, key):
        """Get value with bracket notation"""
        if isinstance(key, tuple):
            key = ':'.join(str(k) for k in key)
        return self._cache.get(key)

    def __setitem__(self, key, value):
        """Set value with bracket notation"""
        if isinstance(key, tuple):
            key = ':'.join(str(k) for k in key)
        self._cache.set(key, value)

    def __delitem__(self, key):
        """Delete with bracket notation"""
        if isinstance(key, tuple):
            key = ':'.join(str(k) for k in key)
        self._cache.delete(key)

    def __contains__(self, key):
        """Check if key exists: 'mykey' in store"""
        if isinstance(key, tuple):
            key = ':'.join(str(k) for k in key)
        return key in self._cache

    # ============ SYNTAX OPTION 3: Simple methods ============
    # Usage: store.set('container', 1, 'status', 'starting')
    #        status = store.get('container', 1, 'status')

    def get(self, *keys, default=None):
        """Get value: store.get('container', 1, 'status')"""
        key = ':'.join(str(k) for k in keys)
        return self._cache.get(key, default)

    def set(self, *args, expire: float = None):
        """Set value: store.set('container', 1, 'status', 'starting')"""
        *keys, value = args
        key = ':'.join(str(k) for k in keys)
        self._cache.set(key, value, expire=expire)

    # ============ PUB/SUB ============

    def publish(self, channel: str, message: Any):
        """Publish message to channel"""
        deque = Deque(directory=f"{self._path}_channel_{channel}")
        deque.append({
            'data': message,
            'timestamp': time.time()
        })
        # Keep channel bounded
        while len(deque) > 1000:
            deque.popleft()

    def subscribe(self, *channels) -> Generator[dict, None, None]:
        """Subscribe to channels - yields messages as they arrive"""
        deques = {ch: Deque(directory=f"{self._path}_channel_{ch}") for ch in channels}
        positions = {ch: len(dq) for ch, dq in deques.items()}
        
        while True:
            for channel, deque in deques.items():
                current_len = len(deque)
                while positions[channel] < current_len:
                    msg = deque[positions[channel]]
                    positions[channel] += 1
                    yield {'channel': channel, 'data': msg['data']}
            time.sleep(0.01)  # Small sleep to prevent CPU spin

    # ============ Helpers ============

    def delete(self, *keys):
        """Delete keys"""
        key = ':'.join(str(k) for k in keys)
        self._cache.delete(key)

    def exists(self, *keys) -> bool:
        """Check if key exists"""
        key = ':'.join(str(k) for k in keys)
        return key in self._cache

    def keys(self, pattern: str = None) -> list:
        """List all keys, optionally filtered by prefix pattern"""
        all_keys = list(self._cache.iterkeys())
        if pattern:
            return [k for k in all_keys if k.startswith(pattern.rstrip('*'))]
        return all_keys

    def clear_all(self):
        """⚠️  WARNING: Deletes ALL data!"""
        self._cache.clear()

    def close(self):
        """Close the cache connection"""
        self._cache.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class _Namespace:
    """Helper for dot notation syntax"""

    def __init__(self, cache: Cache, prefix: str):
        object.__setattr__(self, '_cache', cache)
        object.__setattr__(self, '_prefix', prefix)

    def __getattr__(self, key):
        """Chain dot notation: store.container.status"""
        if key.startswith('_'):
            raise AttributeError(key)
        return _Namespace(self._cache, f"{self._prefix}:{key}")

    def __setattr__(self, key, value):
        """Set value with dot notation"""
        if key.startswith('_'):
            object.__setattr__(self, key, value)
        else:
            full_key = f"{self._prefix}:{key}"
            self._cache.set(full_key, value)

    def __call__(self, default=None):
        """Get value: store.container.status()"""
        return self._cache.get(self._prefix, default)

    def __repr__(self):
        value = self()
        return f"Signella({self._prefix}={value})"


# ============ QUICK START EXAMPLES ============

if __name__ == "__main__":
    store = Signella()

    print("🔥 Testing all syntax options:\n")

    # Option 1: Dict with tuples
    store['container', 1, 'status'] = 'starting'
    print(f"Option 1 (tuple key): {store['container', 1, 'status']}")

    # Option 2: Dict with string keys
    store['user:123:name'] = 'Jimmy'
    print(f"Option 2 (string key): {store['user:123:name']}")

    # Option 3: Simple methods
    store.set('container', 2, 'status', 'running')
    print(f"Option 3 (methods): {store.get('container', 2, 'status')}")

    # Option 4: Dot notation (need to call () to get value)
    store.container.three.status = 'stopped'
    print(f"Option 4 (dot notation): {store.container.three.status()}")

    # Complex data types - no serialization needed!
    store['chat', 178] = {'user_id': 2, 'messages': [1, 2, 3]}
    print(f"Complex dict: {store['chat', 178]}")

    # Check existence
    print(f"Exists check: {store.exists('container', 1, 'status')}")
    print(f"Contains check: {('container', 1, 'status') in store}")

    # List keys
    print(f"All keys: {store.keys()}")
    print(f"Container keys: {store.keys('container:*')}")

    # With expiration
    store.set('temp', 'value', 'expires_soon', expire=60)  # expires in 60 seconds

    print("\n✅ All syntax options work!")
    print("📁 Data persisted to /tmp/signella")
    print("🔄 Run this script again or from another terminal - data persists!")