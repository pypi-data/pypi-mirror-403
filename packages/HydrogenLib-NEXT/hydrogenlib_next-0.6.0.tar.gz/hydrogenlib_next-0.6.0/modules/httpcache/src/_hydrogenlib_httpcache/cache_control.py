from .cache_dir import CacheDirectory, ControlInfo
from .utils import generate_cache_control_headers


class CacheControl:
    def __init__(self, cache_dir):
        self.cache_dir = CacheDirectory(cache_dir)

    def generate_headers_for(self, url):
        cache_info = self.cache_dir.get_cache(url).cacheinfo  # type: ControlInfo
        # cache_info = self.cache_dir.get_cache(url).cacheinfo

        return generate_cache_control_headers(
            cache_info
        )