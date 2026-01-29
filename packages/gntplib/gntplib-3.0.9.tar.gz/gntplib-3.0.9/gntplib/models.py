#!/usr/bin/env python3

# File: gntplib/models.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: Core model classes for GNTP protocol.
# License: MIT

"""Core model classes for GNTP protocol.

This module defines the core data models used in GNTP communication:
- Resources: Binary data like icons and images
- Events: Notification type definitions
- Notifications: Individual notification instances
- Callbacks: Response handling
"""

import hashlib
import urllib.request
import urllib.error
import tempfile
import os
import time
from pathlib import Path
from typing import Optional, Callable, Any, Dict, Union, Tuple
from .constants import RESOURCE_URL_SCHEME
from .exceptions import GNTPValidationError
from .image_validator import ImageDetector

__all__ = [
    'Resource',
    'Event', 
    'Notification',
    'SocketCallback',
    'URLCallback'
]


# class Resource:
#     """Binary resource for GNTP messages (icons, images, etc).
    
#     Resources are binary data that can be embedded in GNTP messages
#     or referenced by URL. Each resource has a unique identifier based
#     on its content hash.
    
#     Attributes:
#         data: Binary content of the resource
#         url: Optional URL if resource is remote
#     """
    
#     def __init__(self, data: Optional[Union[bytes, str, 'Resource']] = None, url: Optional[str] = None):
#         """Initialize resource with binary data or URL.
        
#         Args:
#             data: Binary content, file path string, URL string, Resource instance, 
#                   or base64 string (for embedded resources)
#             url: URL string (for remote resources) - overrides URL in data parameter
            
#         Note:
#             Priority order:
#             1. If data is Resource instance: copy from it
#             2. If url parameter provided: use as URL resource
#             3. If data is string starting with 'http://' or 'https://': use as URL
#             4. If data is valid file path: load from file
#             5. If data is valid base64 string: decode it
#             6. If data is bytes: use directly
#             7. If data is string: encode to bytes
#             8. Otherwise: empty resource
            
#         Example:
#             >>> # URL from string
#             >>> Resource('http://example.com/icon.png')
#             >>> 
#             >>> # URL from parameter
#             >>> Resource(url='http://example.com/icon.png')
#             >>> 
#             >>> # File path
#             >>> Resource(r'c:\\images\\icon.png')
#             >>> Resource('/path/to/icon.png')
#             >>> 
#             >>> # Raw data
#             >>> Resource(b'raw bytes')
#             >>> Resource('raw string')
#             >>> 
#             >>> # Base64
#             >>> Resource('SGVsbG8gd29ybGQ=')
#             >>> 
#             >>> # Copy
#             >>> Resource(existing_resource)
#         """
#         self.data: Optional[bytes] = None
#         self.url: Optional[str] = None
#         self._unique_value: Optional[bytes] = None

#         # Case 1: Handle Resource instance (copy constructor)
#         if isinstance(data, Resource):
#             self.data = data.data
#             self.url = data.url
#             self._unique_value = data._unique_value
#             return

#         # Case 2: Explicit URL parameter (highest priority)
#         if url is not None:
#             self.url = url
#             return

#         # If no data provided, resource is empty
#         if data is None:
#             return

#         # Case 3: data is a string
#         if isinstance(data, str):
#             # Check if it's a URL
#             if data.startswith(('http://', 'https://')):
#                 self.url = data
#                 return
            
#             # Check if it's a file path
#             try:
#                 path = Path(data)
#                 if path.is_file():
#                     self.data = self._load_from_file(path)
#                     return
#             except Exception:
#                 pass
            
#             # Try to decode as base64
#             try:
#                 import base64
#                 if self._is_base64(data):
#                     self.data = base64.b64decode(data)
#                     return
#             except Exception:
#                 pass
            
#             # Default for strings: encode to bytes
#             self.data = data.encode('utf-8')
#             return
        
#         # Case 4: data is bytes
#         if isinstance(data, bytes):
#             # Try to validate as image first
#             try:
#                 if ImageDetector.validate_image(data, strict=True):
#                     self.data = data
#                     return
#             except Exception:
#                 pass
            
#             # If not an image or validation fails, use bytes directly
#             self.data = data
#             return
        
#         # If we reach here, data is of unsupported type
#         raise GNTPValidationError(f"Unsupported data type for Resource: {type(data)}")

#     def __call__(self) -> Optional[bytes]:
#         """Get resource data.
        
#         Returns:
#             Binary data of the resource or None if URL-based
            
#         Example:
#             >>> resource = Resource(b'binary data')
#             >>> data = resource()
#         """
#         return self.data
    
#     def _load_from_file(self, filepath: Path) -> bytes:
#         """Load binary data from file.
        
#         Args:
#             filepath: Path to file
            
#         Returns:
#             Binary content of file
            
#         Raises:
#             IOError: If file cannot be read
#         """
#         try:
#             with open(filepath, 'rb') as f:
#                 return f.read()
#         except Exception as e:
#             raise IOError(f"Cannot read file {filepath}: {e}")

#     @staticmethod
#     def _is_base64(data: Union[str, bytes]) -> bool:
#         """Check if data is valid base64 encoded.
        
#         Args:
#             data: Data to check (string or bytes)
            
#         Returns:
#             True if data is valid base64
            
#         Example:
#             >>> Resource._is_base64('SGVsbG8gd29ybGQ=')
#             True
#         """
#         import base64
        
#         try:
#             if isinstance(data, bytes):
#                 try:
#                     data = data.decode('ascii')
#                 except UnicodeDecodeError:
#                     return False
            
#             # Base64 strings should have length multiple of 4
#             if len(data) % 4 != 0:
#                 return False
                
#             # Check for valid base64 characters
#             import re
#             base64_pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
#             if not base64_pattern.match(data):
#                 return False
                
#             # Final validation by decoding
#             base64.b64decode(data, validate=True)
#             return True
#         except Exception:
#             return False

#     @classmethod
#     def from_file(cls, filepath: str) -> 'Resource':
#         """Create resource from file.
        
#         Args:
#             filepath: Path to file
            
#         Returns:
#             Resource instance with file contents
            
#         Raises:
#             IOError: If file cannot be read
            
#         Example:
#             >>> icon = Resource.from_file('icon.png')
#         """
#         return cls(data=filepath)
    
#     @classmethod
#     def from_url(cls, url: str) -> 'Resource':
#         """Create resource from URL.
        
#         Args:
#             url: URL to resource
            
#         Returns:
#             Resource instance referencing URL
            
#         Example:
#             >>> icon = Resource.from_url('https://example.com/icon.png')
#         """
#         return cls(url=url)
    
#     def unique_value(self) -> Optional[bytes]:
#         """Get unique hash identifier for resource content.
        
#         Returns MD5 hash of resource data as hex bytes.
        
#         Returns:
#             Hex-encoded MD5 hash or None if no data
            
#         Example:
#             >>> resource = Resource(b'test data')
#             >>> resource.unique_value()
#             b'eb733a00c0c9d336e65691a37ab54293'
#         """
#         if self.data is not None and self._unique_value is None:
#             self._unique_value = hashlib.md5(self.data).hexdigest().encode('utf-8')
#         return self._unique_value
    
#     def unique_id(self) -> Optional[bytes]:
#         """Get unique resource identifier with protocol scheme.
        
#         Returns:
#             Full resource identifier or None if no data
            
#         Example:
#             >>> resource = Resource(b'test')
#             >>> resource.unique_id()
#             b'x-growl-resource://098f6bcd4621d373cade4e832627b4f6'
#         """
#         unique_val = self.unique_value()
#         if unique_val is not None:
#             return RESOURCE_URL_SCHEME + unique_val
#         return None
    
#     def __repr__(self) -> str:
#         """Return string representation."""
#         if self.url:
#             return f"Resource(url={self.url!r})"
#         elif self.data:
#             return f"Resource(size={len(self.data)} bytes, hash={self.unique_value()})"
#         else:
#             return "Resource(empty)"
    
#     def __bool__(self) -> bool:
#         """Check if resource has content."""
#         return self.data is not None or self.url is not None

class Resource:
    """Binary resource for GNTP messages (icons, images, etc).
    
    Resources are binary data that can be embedded in GNTP messages
    or referenced by URL. Each resource has a unique identifier based
    on its content hash. Resources support automatic downloading from URLs
    and caching to avoid repeated network requests.
    
    Attributes:
        data: Binary content of the resource
        url: Optional URL if resource is remote
    """
    
    # Class-level cache storage
    _url_cache: Dict[str, Tuple[bytes, float, str]] = {}
    _cache_dir: Optional[str] = None
    _CACHE_MAX_AGE = 3600  # 1 hour in seconds
    _CACHE_MAX_SIZE = 50  # Maximum number of items in memory cache
    
    def __init__(self, data: Optional[Union[bytes, str, 'Resource']] = None, 
                 url: Optional[str] = None):
        """Initialize resource with binary data or URL.
        
        Args:
            data: Binary content, file path string, URL string, Resource instance, 
                  or base64 string (for embedded resources). If a URL string is provided,
                  the content will be automatically downloaded and cached.
            url: URL string (for remote resources) - takes precedence over URL in data parameter.
            
        Raises:
            GNTPValidationError: If data type is unsupported or URL download fails
            
        Note:
            Processing priority:
            1. If data is a Resource instance: copy from it
            2. If url parameter is provided: use as URL resource
            3. If data is a string starting with 'http://' or 'https://': use as URL
            4. If data is a valid file path: load from file
            5. If data is a valid base64 string: decode it
            6. If data is bytes: use directly
            7. If data is a string: encode to bytes
            8. Otherwise: create empty resource
            
        Example:
            >>> # URL from string (auto-downloads)
            >>> icon = Resource('http://example.com/icon.png')
            >>> 
            >>> # URL from parameter (auto-downloads)
            >>> icon = Resource(url='http://example.com/icon.png')
            >>> 
            >>> # File path
            >>> icon = Resource('/path/to/icon.png')
            >>> 
            >>> # Raw bytes
            >>> icon = Resource(b'raw image data')
            >>> 
            >>> # Base64 encoded
            >>> icon = Resource('SGVsbG8gd29ybGQ=')
            >>> 
            >>> # Copy existing resource
            >>> icon2 = Resource(icon)
        """
        self.data: Optional[bytes] = None
        self.url: Optional[str] = None
        self._unique_value: Optional[bytes] = None
        self._cache_key: Optional[str] = None
        
        # Initialize cache directory on first use
        if Resource._cache_dir is None:
            Resource._init_cache_dir()

        # Case 1: Handle Resource instance (copy constructor)
        if isinstance(data, Resource):
            self._copy_from_resource(data)
            return

        # Case 2: Explicit URL parameter
        if url is not None:
            self.url = url
            self.data = self._get_cached_url_data(url)
            if self.data is None and self.url:
                raise GNTPValidationError(f"Failed to download resource from URL: {url}")
            return

        # Handle None data
        if data is None:
            return

        # Case 3: data is a string
        if isinstance(data, str):
            self._process_string_data(data)
            return
        
        # Case 4: data is bytes
        if isinstance(data, bytes):
            self._process_bytes_data(data)
            return
        
        # Unsupported data type
        raise GNTPValidationError(
            f"Unsupported data type for Resource: {type(data)}. "
            f"Expected bytes, str, Resource, or None."
        )

    def _copy_from_resource(self, other: 'Resource') -> None:
        """Copy data from another Resource instance.
        
        Args:
            other: Resource instance to copy from
        """
        self.data = other.data
        self.url = other.url
        self._unique_value = other._unique_value
        self._cache_key = other._cache_key

    def _process_string_data(self, data: str) -> None:
        """Process string data based on its content type.
        
        Args:
            data: String data to process
        """
        # Check if it's a URL
        if data.startswith(('http://', 'https://')):
            self.url = data
            self.data = self._get_cached_url_data(data)
            if self.data is None:
                raise GNTPValidationError(f"Failed to download resource from URL: {data}")
            return
        
        # Check if it's a file path
        try:
            path = Path(data)
            if path.is_file():
                self.data = self._load_from_file(path)
                return
        except Exception as e:
            # Not a valid file path, continue to other options
            pass
        
        # Try to decode as base64
        try:
            import base64
            if self._is_base64(data):
                self.data = base64.b64decode(data)
                return
        except Exception:
            # Not base64, continue
            pass
        
        # Default: encode string to bytes
        self.data = data.encode('utf-8')

    def _process_bytes_data(self, data: bytes) -> None:
        """Process bytes data, validating if it's an image.
        
        Args:
            data: Bytes data to process
        """
        # Try to validate as image
        try:
            if ImageDetector.validate_image(data, strict=True):
                self.data = data
                return
        except Exception:
            # Not a valid image or validation failed, continue
            pass
        
        # Use bytes directly
        self.data = data

    @classmethod
    def _init_cache_dir(cls) -> None:
        """Initialize the cache directory in system temp location."""
        try:
            cache_base = tempfile.gettempdir()
            cls._cache_dir = os.path.join(cache_base, "gntplib_cache")
            os.makedirs(cls._cache_dir, exist_ok=True)
        except Exception as e:
            cls._cache_dir = None
            print(f"Warning: Could not create cache directory: {e}")

    def _get_cached_url_data(self, url: str) -> Optional[bytes]:
        """Retrieve URL data with caching support.
        
        Args:
            url: URL to retrieve data from
            
        Returns:
            Binary data from URL, or None if download fails
        """
        # Generate cache key from URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        self._cache_key = url_hash
        
        # 1. Check memory cache first
        if url_hash in Resource._url_cache:
            data, timestamp, _ = Resource._url_cache[url_hash]
            # Check if cache is still fresh
            if time.time() - timestamp < Resource._CACHE_MAX_AGE:
                return data
        
        # 2. Check disk cache
        disk_data = self._load_from_disk_cache(url_hash)
        if disk_data is not None:
            # Update memory cache
            Resource._url_cache[url_hash] = (disk_data, time.time(), '')
            return disk_data
        
        # 3. Download fresh data
        fresh_data = self._download_from_url(url)
        if fresh_data is not None:
            # Update caches
            self._update_caches(url_hash, fresh_data)
        
        return fresh_data

    def _load_from_disk_cache(self, cache_key: str) -> Optional[bytes]:
        """Load data from disk cache.
        
        Args:
            cache_key: Cache key identifying the resource
            
        Returns:
            Cached data if valid, None otherwise
        """
        if Resource._cache_dir is None:
            return None
        
        cache_file = os.path.join(Resource._cache_dir, f"{cache_key}.cache")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            # Check file age
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < Resource._CACHE_MAX_AGE:
                with open(cache_file, 'rb') as f:
                    return f.read()
            else:
                # Remove expired cache file
                os.remove(cache_file)
        except Exception:
            # Silently ignore cache read errors
            pass
        
        return None

    def _update_caches(self, cache_key: str, data: bytes) -> None:
        """Update both memory and disk caches with new data.
        
        Args:
            cache_key: Cache key for the data
            data: Binary data to cache
        """
        # Update memory cache with LRU eviction
        if len(Resource._url_cache) >= Resource._CACHE_MAX_SIZE:
            # Remove oldest entry (simple LRU simulation)
            oldest_key = min(Resource._url_cache.items(), 
                           key=lambda x: x[1][1])[0]
            del Resource._url_cache[oldest_key]
        
        Resource._url_cache[cache_key] = (data, time.time(), '')
        
        # Update disk cache
        self._save_to_disk_cache(cache_key, data)

    def _save_to_disk_cache(self, cache_key: str, data: bytes) -> None:
        """Save data to disk cache.
        
        Args:
            cache_key: Cache key for the data
            data: Binary data to save
        """
        if Resource._cache_dir is None:
            return
        
        try:
            cache_file = os.path.join(Resource._cache_dir, f"{cache_key}.cache")
            with open(cache_file, 'wb') as f:
                f.write(data)
        except Exception as e:
            # Non-fatal error, just log
            print(f"Warning: Could not save to disk cache: {e}")

    def _download_from_url(self, url: str) -> Optional[bytes]:
        """Download content from URL.
        
        Args:
            url: URL to download from
            
        Returns:
            Downloaded binary content, or None if download fails
        """
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'GNTPLib/1.0 Resource Fetcher',
                    'Accept': 'image/*,*/*;q=0.9'
                }
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read()
                
                # Validate content has reasonable size
                if len(content) == 0:
                    print(f"Warning: Empty content from {url}")
                    return None
                    
                return content
                
        except urllib.error.HTTPError as e:
            print(f"HTTP Error {e.code} for {url}: {e.reason}")
            return None
        except urllib.error.URLError as e:
            print(f"URL Error for {url}: {e.reason}")
            return None
        except Exception as e:
            print(f"Error downloading from {url}: {e}")
            return None

    def _load_from_file(self, filepath: Path) -> bytes:
        """Load binary data from file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Binary content of the file
            
        Raises:
            IOError: If the file cannot be read
        """
        try:
            with open(filepath, 'rb') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Cannot read file {filepath}: {e}")

    @staticmethod
    def _is_base64(data: Union[str, bytes]) -> bool:
        """Check if data is valid base64 encoded.
        
        Args:
            data: Data to check (string or bytes)
            
        Returns:
            True if data is valid base64, False otherwise
            
        Example:
            >>> Resource._is_base64('SGVsbG8gd29ybGQ=')
            True
        """
        import base64
        import re
        
        try:
            if isinstance(data, bytes):
                try:
                    data = data.decode('ascii')
                except UnicodeDecodeError:
                    return False
            
            # Remove whitespace
            data = data.strip()
            
            # Base64 strings should have length multiple of 4
            if len(data) % 4 != 0:
                return False
                
            # Check for valid base64 characters
            base64_pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
            if not base64_pattern.match(data):
                return False
                
            # Final validation by decoding
            base64.b64decode(data, validate=True)
            return True
        except Exception:
            return False

    def __call__(self) -> Optional[bytes]:
        """Get resource data.
        
        Returns:
            Binary data of the resource, or None if no data is available
            
        Example:
            >>> resource = Resource(b'data')
            >>> data = resource()
            >>> print(len(data))
            4
        """
        return self.data

    @classmethod
    def from_file(cls, filepath: str) -> 'Resource':
        """Create resource from file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Resource instance with file contents
            
        Raises:
            IOError: If the file cannot be read
            
        Example:
            >>> icon = Resource.from_file('icon.png')
        """
        return cls(data=filepath)
    
    @classmethod
    def from_url(cls, url: str) -> 'Resource':
        """Create resource from URL.
        
        Args:
            url: URL to the resource
            
        Returns:
            Resource instance with downloaded content
            
        Example:
            >>> icon = Resource.from_url('https://example.com/icon.png')
        """
        return cls(url=url)
    
    def unique_value(self) -> Optional[bytes]:
        """Get unique hash identifier for resource content.
        
        Returns MD5 hash of resource data as hex-encoded bytes.
        
        Returns:
            Hex-encoded MD5 hash, or None if no data is available
            
        Example:
            >>> resource = Resource(b'test data')
            >>> resource.unique_value()
            b'eb733a00c0c9d336e65691a37ab54293'
        """
        if self.data is not None and self._unique_value is None:
            self._unique_value = hashlib.md5(self.data).hexdigest().encode('utf-8')
        return self._unique_value
    
    def unique_id(self) -> Optional[bytes]:
        """Get unique resource identifier with protocol scheme.
        
        Returns:
            Full resource identifier with scheme prefix, or None if no data
            
        Example:
            >>> resource = Resource(b'test')
            >>> resource.unique_id()
            b'x-growl-resource://098f6bcd4621d373cade4e832627b4f6'
        """
        unique_val = self.unique_value()
        if unique_val is not None:
            return RESOURCE_URL_SCHEME + unique_val
        return None
    
    @classmethod
    def clear_cache(cls, older_than: Optional[float] = None) -> None:
        """Clear cache entries.
        
        Args:
            older_than: Clear entries older than this many seconds.
                        If None, clear all cache entries.
                        
        Example:
            >>> # Clear all cache
            >>> Resource.clear_cache()
            >>> 
            >>> # Clear cache entries older than 30 minutes
            >>> Resource.clear_cache(older_than=1800)
        """
        current_time = time.time()
        
        # Clear memory cache
        if older_than is None:
            cls._url_cache.clear()
        else:
            cutoff = current_time - older_than
            keys_to_delete = [
                key for key, (_, timestamp, _) in cls._url_cache.items()
                if timestamp < cutoff
            ]
            for key in keys_to_delete:
                del cls._url_cache[key]
        
        # Clear disk cache
        if cls._cache_dir and os.path.exists(cls._cache_dir):
            try:
                for filename in os.listdir(cls._cache_dir):
                    filepath = os.path.join(cls._cache_dir, filename)
                    if older_than is None:
                        os.remove(filepath)
                    else:
                        file_age = current_time - os.path.getmtime(filepath)
                        if file_age > older_than:
                            os.remove(filepath)
            except Exception as e:
                print(f"Warning: Could not clear disk cache: {e}")

    @classmethod
    def get_cache_info(cls) -> Dict[str, any]:
        """Get cache statistics and information.
        
        Returns:
            Dictionary containing cache statistics
            
        Example:
            >>> info = Resource.get_cache_info()
            >>> print(info['memory_cache_entries'])
            5
        """
        disk_files = 0
        if cls._cache_dir and os.path.exists(cls._cache_dir):
            try:
                disk_files = len([f for f in os.listdir(cls._cache_dir) 
                                if f.endswith('.cache')])
            except Exception:
                disk_files = 0
        
        return {
            'memory_cache_entries': len(cls._url_cache),
            'disk_cache_files': disk_files,
            'cache_dir': cls._cache_dir,
            'cache_max_age_seconds': cls._CACHE_MAX_AGE,
            'cache_max_size': cls._CACHE_MAX_SIZE
        }
    
    def __repr__(self) -> str:
        """Return string representation of the resource.
        
        Returns:
            Informative string representation
        """
        if self.url:
            if self.data:
                cache_status = " (cached)" if self._cache_key else ""
                return f"Resource(url={self.url!r}, size={len(self.data)} bytes{cache_status})"
            else:
                return f"Resource(url={self.url!r}, download_failed)"
        elif self.data:
            return f"Resource(size={len(self.data)} bytes)"
        else:
            return "Resource(empty)"
    
    def __bool__(self) -> bool:
        """Check if resource has content.
        
        Returns:
            True if resource has data or a URL, False otherwise
        """
        return self.data is not None or self.url is not None
    
    def __del__(self) -> None:
        """Cleanup method called when object is destroyed.
        
        Note: This is primarily for future cleanup if temporary files
        are used. Current implementation doesn't create temporary files
        that need explicit cleanup.
        """
        pass

class Event:
    """Notification type definition.
    
    Events define the types of notifications an application can send.
    Each event must be registered before notifications of that type can be sent.
    
    Attributes:
        name: Unique identifier for the notification type
        display_name: Human-readable name shown in preferences
        enabled: Whether notifications of this type are enabled by default
        icon: Optional icon for this notification type
    """
    
    def __init__(
        self,
        name: str,
        display_name: Optional[str] = None,
        enabled: bool = True,
        icon: Optional[Resource] = None
    ):
        """Initialize notification event definition.
        
        Args:
            name: Event identifier (required)
            display_name: Display name (defaults to name)
            enabled: Enable by default (default: True)
            icon: Optional icon resource
            
        Raises:
            GNTPValidationError: If name is empty
            
        Example:
            >>> event = Event('Update', 'Software Update', enabled=True)
        """
        if not name:
            raise GNTPValidationError("Event name cannot be empty")
        
        self.name = name
        self.display_name = display_name or name
        self.enabled = enabled
        self.icon = icon
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Event(name={self.name!r}, "
            f"display_name={self.display_name!r}, "
            f"enabled={self.enabled})"
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on name."""
        if isinstance(other, Event):
            return self.name == other.name
        return False
    
    def __hash__(self) -> int:
        """Make Event hashable based on name."""
        return hash(self.name)


class Notification:
    """Individual notification instance.
    
    Represents a single notification to be sent to the GNTP server.
    
    Attributes:
        name: Event name this notification belongs to
        title: Notification title
        text: Notification message body
        id_: Optional unique identifier
        sticky: Whether notification stays until dismissed
        priority: Priority level (-2 to 2)
        icon: Optional icon resource
        coalescing_id: ID for grouping/replacing notifications
        callback: Optional callback handler
    """
    
    def __init__(
        self,
        name: str,
        title: str,
        text: str = '',
        id_: Optional[str] = None,
        sticky: bool = False,
        priority: int = 0,
        icon: Optional[Resource] = None,
        coalescing_id: Optional[str] = None,
        callback: Optional['BaseCallback'] = None
    ):
        """Initialize notification.
        
        Args:
            name: Event name
            title: Notification title
            text: Message text (default: '')
            id_: Unique notification ID
            sticky: Keep visible until dismissed (default: False)
            priority: Priority from -2 to 2 (default: 0)
            icon: Optional icon
            coalescing_id: Group/replace ID
            callback: Optional callback handler
            
        Raises:
            GNTPValidationError: If name or title is empty
            
        Example:
            >>> notif = Notification(
            ...     'Update',
            ...     'New Version',
            ...     'Version 2.0 is available',
            ...     priority=1,
            ...     sticky=True
            ... )
        """
        if not name:
            raise GNTPValidationError("Notification name cannot be empty")
        if not title:
            raise GNTPValidationError("Notification title cannot be empty")
        
        self.name = name
        self.title = title
        self.text = text
        self.id_ = id_
        self.sticky = sticky
        self.priority = max(-2, min(2, priority or 0))  # Clamp to valid range
        self.icon = icon
        self.coalescing_id = coalescing_id
        self.callback = callback
    
    @property
    def socket_callback(self) -> Optional['SocketCallback']:
        """Get socket callback if callback is SocketCallback type."""
        if isinstance(self.callback, SocketCallback):
            return self.callback
        return None
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Notification(name={self.name!r}, title={self.title!r}, "
            f"priority={self.priority}, sticky={self.sticky})"
        )


class BaseCallback:
    """Base class for notification callbacks."""
    
    def write_into(self, writer: Any) -> None:
        """Write callback to message writer.
        
        Subclasses must implement this method.
        
        Args:
            writer: Message writer instance
        """
        raise NotImplementedError


class SocketCallback(BaseCallback):
    """Socket-based callback for notification responses.
    
    Handles different callback events (clicked, closed, timeout) via
    registered callback functions.
    
    Attributes:
        context: Callback context value
        context_type: Type of context
        on_click_callback: Called when notification is clicked
        on_close_callback: Called when notification is closed
        on_timeout_callback: Called when notification times out
    """
    
    def __init__(
        self,
        context: str = 'None',
        context_type: str = 'None',
        on_click: Optional[Callable] = None,
        on_close: Optional[Callable] = None,
        on_timeout: Optional[Callable] = None
    ):
        """Initialize socket callback.
        
        Args:
            context: Context value (default: 'None')
            context_type: Context type (default: 'None')
            on_click: Callback for click events
            on_close: Callback for close events
            on_timeout: Callback for timeout events
            
        Example:
            >>> def on_clicked(response):
            ...     print("Notification clicked!")
            >>> 
            >>> callback = SocketCallback(
            ...     context='notification_1',
            ...     on_click=on_clicked
            ... )
        """
        self.context = context
        self.context_type = context_type
        self.on_click_callback = on_click
        self.on_close_callback = on_close
        self.on_timeout_callback = on_timeout
    
    def on_click(self, response: Any) -> Any:
        """Handle click event."""
        if self.on_click_callback:
            return self.on_click_callback(response)
    
    def on_close(self, response: Any) -> Any:
        """Handle close event."""
        if self.on_close_callback:
            return self.on_close_callback(response)
    
    def on_timeout(self, response: Any) -> Any:
        """Handle timeout event."""
        if self.on_timeout_callback:
            return self.on_timeout_callback(response)
    
    def __call__(self, response: Any) -> Any:
        """Dispatch to appropriate handler based on callback result.
        
        Args:
            response: Response object with callback result
            
        Returns:
            Result from handler callback
        """
        result = response.headers.get('Notification-Callback-Result', '')
        
        # Map callback results to handlers
        handlers: Dict[str, Callable] = {
            'CLICKED': self.on_click,
            'CLICK': self.on_click,
            'CLOSED': self.on_close,
            'CLOSE': self.on_close,
            'TIMEDOUT': self.on_timeout,
            'TIMEOUT': self.on_timeout,
        }
        
        handler = handlers.get(result)
        if handler:
            return handler(response)
    
    def write_into(self, writer: Any) -> None:
        """Write socket callback headers."""
        writer.write_socket_callback(self)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"SocketCallback(context={self.context!r})"


class URLCallback(BaseCallback):
    """URL-based callback for notification responses.
    
    When notification is interacted with, GNTP server will request the URL.
    
    Attributes:
        url: Callback URL
    """
    
    def __init__(self, url: str):
        """Initialize URL callback.
        
        Args:
            url: URL to be called on notification interaction
            
        Example:
            >>> callback = URLCallback('https://example.com/callback')
        """
        if not url:
            raise GNTPValidationError("Callback URL cannot be empty")
        
        self.url = url
    
    def write_into(self, writer: Any) -> None:
        """Write URL callback headers."""
        writer.write_url_callback(self)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"URLCallback(url={self.url!r})"