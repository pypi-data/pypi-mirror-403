# First code by @LittleNightSong
# Edit by DeepSeek

import dataclasses
import datetime
import enum
from typing import Dict, Optional, Set, Union

from _hydrogenlib_core.time_ import DatetimeParser

web_time_parser = DatetimeParser("%a, %d %b %Y %H:%M:%S %Z")


class ControlFlags(str, enum.Enum):
    no_cache = "no-cache"
    no_store = "no-store"
    must_revalidate = 'must-revalidate'
    proxy_revalidate = 'proxy-revalidate'

    # 这些标志可能有值，不能简单作为枚举值
    max_age = 'max-age'
    s_maxage = 's-maxage'
    stale_while_revalidate = 'stale-while-revalidate'
    stale_if_error = 'stale-if-error'

    # 这些是布尔标志
    private = 'private'
    public = 'public'
    immutable = 'immutable'
    no_transform = 'no-transform'
    only_if_cached = 'only-if-cached'


@dataclasses.dataclass
class ControlInfo:
    timestamp: Optional[datetime.datetime] = None
    control_flags: Set[str] = dataclasses.field(default_factory=set)  # 改为字符串集合
    directives: Dict[str, Optional[int]] = dataclasses.field(default_factory=dict)  # 存储带值的指令
    expires_at: Optional[datetime.datetime] = None  # 改为 expires_at 更准确
    vary: Optional[str] = None
    etag: Optional[str] = None
    last_modified: Optional[datetime.datetime] = None

    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_headers(cls, headers: Dict[str, str],
                     now_date: Optional[datetime.datetime] = None) -> 'ControlInfo':
        self = cls()

        # 将headers键转换为小写以处理大小写不敏感
        headers_lower = {k.lower(): v for k, v in headers.items()}

        # 解析Date头
        if 'date' in headers_lower:
            try:
                self.timestamp = web_time_parser.parse(headers_lower['date'])
            except Exception:
                self.timestamp = now_date or datetime.datetime.now()
        else:
            self.timestamp = now_date or datetime.datetime.now()

        # 解析Cache-Control头
        cache_control = headers_lower.get('cache-control', '')
        for field in cache_control.split(','):
            field = field.strip().lower()
            if not field:
                continue

            # 处理带值的指令
            if '=' in field:
                key, value = field.split('=', 1)
                key = key.strip()
                try:
                    # 尝试解析为整数
                    if value.isdigit():
                        self.directives[key] = int(value)
                    elif value.startswith('"') and value.endswith('"'):
                        # 带引号的字符串值
                        self.directives[key] = value[1:-1]
                    else:
                        # 其他情况存储原始字符串
                        self.directives[key] = value
                except ValueError:
                    self.directives[key] = value
            else:
                # 布尔标志
                self.control_flags.add(field)

        # 解析Vary头
        self.vary = headers_lower.get('vary')

        # 解析ETag头
        self.etag = headers_lower.get('etag')

        # 解析Last-Modified头
        if 'last-modified' in headers_lower:
            try:
                self.last_modified = web_time_parser.parse(headers_lower['last-modified'])
            except Exception:
                pass

        # 解析Expires头
        if 'expires' in headers_lower:
            try:
                expires_str = headers_lower['expires']
                if expires_str.lower() == '0' or expires_str == '-1':
                    # 立即过期
                    self.expires_at = self.timestamp
                else:
                    self.expires_at = web_time_parser.parse(expires_str)
            except Exception:
                # 如果解析失败，设置立即过期
                self.expires_at = self.timestamp

        return self

    @property
    def max_age(self) -> Optional[int]:
        """获取max-age指令的值"""
        return self.directives.get('max-age')

    @property
    def s_maxage(self) -> Optional[int]:
        """获取s-maxage指令的值"""
        return self.directives.get('s-maxage')

    @property
    def no_cache(self) -> bool:
        """检查是否包含no-cache指令"""
        return 'no-cache' in self.control_flags

    @property
    def no_store(self) -> bool:
        """检查是否包含no-store指令"""
        return 'no-store' in self.control_flags

    @property
    def private(self) -> bool:
        """检查是否包含private指令"""
        return 'private' in self.control_flags

    @property
    def public(self) -> bool:
        """检查是否包含public指令"""
        return 'public' in self.control_flags

    @property
    def immutable(self) -> bool:
        """检查是否包含immutable指令"""
        return 'immutable' in self.control_flags

    @property
    def must_revalidate(self) -> bool:
        """检查是否包含must-revalidate指令"""
        return 'must-revalidate' in self.control_flags

    @property
    def proxy_revalidate(self) -> bool:
        """检查是否包含proxy-revalidate指令"""
        return 'proxy-revalidate' in self.control_flags

    @property
    def no_transform(self) -> bool:
        """检查是否包含no-transform指令"""
        return 'no-transform' in self.control_flags

    @property
    def expires_in(self) -> Optional[int]:
        """计算从现在到过期的秒数（如果已过期则为负数）"""
        if not self.expires_at:
            return None

        now = datetime.datetime.now()
        delta = self.expires_at - now
        return int(delta.total_seconds())

    @property
    def age(self) -> Optional[int]:
        """计算资源年龄（从响应时间到现在）"""
        if not self.timestamp:
            return None

        now = datetime.datetime.now()
        delta = now - self.timestamp
        return int(delta.total_seconds())

    @property
    def is_expired(self) -> bool:
        """检查资源是否已过期"""
        return self.time_until_expiry <= 0

    @property
    def time_until_expiry(self) -> int:
        """计算距离过期的秒数（正数表示未过期，负数表示已过期）"""
        # 优先级：no-store > no-cache > max-age > Expires

        if self.no_store:
            return -1  # 立即过期

        if self.no_cache:
            return -1  # 立即过期，需要重新验证

        # 检查max-age
        if self.max_age is not None:
            age = self.age or 0
            return max(0, self.max_age - age)

        # 检查Expires头
        if self.expires_at:
            now = datetime.datetime.now()
            delta = (self.expires_at - now).total_seconds()
            return int(max(0, delta))

        # 没有缓存控制信息，使用启发式缓存
        # 根据RFC，如果没有明确的过期时间，可以使用启发式算法
        # 这里简单返回0，表示需要重新验证
        return 0

    def if_need_revalidate_at(self, time: Union[datetime.datetime, int, float]) -> bool:
        """
        检查在指定时间是否需要重新验证

        Args:
            time: 检查的时间点，可以是datetime或时间戳

        Returns:
            bool: True表示需要重新验证
        """
        # 转换为datetime
        if isinstance(time, (int, float)):
            check_time = datetime.datetime.fromtimestamp(time)
        else:
            check_time = time

        # 特殊标志检查
        if self.no_store:
            return True

        if self.no_cache:
            return True

        if self.immutable:
            return False

        # 检查是否过期
        if self.max_age is not None and self.timestamp:
            expiry_time = self.timestamp + datetime.timedelta(seconds=self.max_age)
            if check_time >= expiry_time:
                # 已过期，检查是否需要强制重新验证
                return self.must_revalidate or True

        # 检查Expires头
        if self.expires_at and check_time >= self.expires_at:
            return True

        # 如果must-revalidate为True，即使未过期也可能需要验证
        # 但根据规范，未过期时不需要重新验证
        return False

    def __str__(self) -> str:
        """友好的字符串表示"""
        parts = []

        if self.control_flags:
            parts.append(f"flags: {', '.join(sorted(self.control_flags))}")

        if self.directives:
            dir_str = ', '.join(f"{k}={v}" for k, v in self.directives.items())
            parts.append(f"directives: {dir_str}")

        if self.max_age is not None:
            parts.append(f"max-age: {self.max_age}s")

        if self.expires_at:
            parts.append(f"expires: {self.expires_at}")

        if self.vary:
            parts.append(f"vary: {self.vary}")

        if self.etag:
            parts.append(f"etag: {self.etag[:20]}...")

        return f"CacheControlInfo({', '.join(parts)})"


# # 使用示例
# if __name__ == "__main__":
#     # 模拟HTTP响应头
#     headers = {
#         'Date': 'Tue, 15 Nov 2024 08:12:31 GMT',
#         'Cache-Control': 'public, max-age=3600, must-revalidate',
#         'Expires': 'Tue, 15 Nov 2024 09:12:31 GMT',
#         'ETag': '"abc123"',
#         'Vary': 'Accept-Encoding',
#         'Last-Modified': 'Tue, 15 Nov 2024 07:12:31 GMT'
#     }
#
#     cache_info = CacheControlInfo.from_headers(headers)
#     print(cache_info)
#     print(f"Expires in: {cache_info.expires_in} seconds")
#     print(f"Is expired: {cache_info.is_expired}")
#     print(f"Need revalidate now: {cache_info.if_need_revalidate_at(datetime.datetime.now())}")
