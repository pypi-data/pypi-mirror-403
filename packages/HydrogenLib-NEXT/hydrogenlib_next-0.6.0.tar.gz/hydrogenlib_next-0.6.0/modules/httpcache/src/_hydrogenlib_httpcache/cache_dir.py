from __future__ import annotations

import dataclasses
import pickle
from collections.abc import Buffer
from pathlib import Path

import urllib3.util

from _hydrogenlib_core.hash import Hash
from _hydrogenlib_core.utils import lazy_property
from _hydrogenlib_httpcache.cache_info import ControlInfo


@dataclasses.dataclass
class LocalCacheIndex:
    cache_control_info: ControlInfo
    files: dict[frozenset[str], Path]  # dict[Vary, Path]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def save(self, fp):
        pickle.dump(self.to_dict(), fp)

    @classmethod
    def load(cls, fp):
        return cls(**pickle.load(fp))


class _Cache:
    __slots__ = ('_url', '_cd')

    def __init__(self, cache_directory: CacheDirectory, url):
        self._url = url
        self._cd = cache_directory

    @lazy_property
    def hash(self):
        return self._cd.compute_hash(self.url)

    @lazy_property
    def index_file(self) -> Path:
        return self._cd.indexdir / self.hash

    @property
    def content_file(self):
        return self._cd.filedir / self.hash

    @property
    def url(self):
        return self._url

    @lazy_property
    def cacheinfo(self):
        with self.index_file.open('rb') as fp:
            return pickle.load(fp)

    @cacheinfo.setter
    def cacheinfo(self, value):
        with self.index_file.open('wb') as fp:
            pickle.dump(value, fp)

    def clear(self):
        self.index_file.unlink(True)
        self.content_file.unlink(True)

    def open_content(self, mode='rb'):
        return open(self.content_file, mode)

    def rewrite_content(self, content: Buffer):
        with self.open_content('wb') as fp:
            fp.write(content)

    def extend_content(self, content: Buffer):
        with self.open_content('ab') as fp:
            fp.write(content)

    def read_content(self, n: int = -1):
        with self.open_content('rb') as fp:
            return fp.read(n)


class CacheDirectory:
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.indexdir = self.cache_dir / 'index'
        self.filedir = self.cache_dir / 'files'

        self.indexdir.mkdir(parents=True, exist_ok=True)
        self.filedir.mkdir(parents=True, exist_ok=True)

    def get_cache(self, url: str) -> _Cache:
        return _Cache(self, url)

    def remove_cache(self, url: str):
        self.get_cache(url).clear()

    @staticmethod
    def compute_hash(url: str, hash_method: str | Hash = 'sha256'):
        hash_method: Hash = Hash[hash_method] if isinstance(hash_method, str) else hash_method
        # 1. 解析 URL
        urlinfo = urllib3.util.parse_url(url)
        # 2. 仅保留 Path
        path = urlinfo.path
        # 3. 计算 hash
        return hash_method.compute_str(path)
