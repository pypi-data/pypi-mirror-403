from _hydrogenlib_httpcache.cache_info import ControlInfo, ControlFlags
import datetime


def generate_cache_control_headers(cache_info: ControlInfo):
    headers = {}

    if cache_info.control_flags:
        flags = cache_info.control_flags
        flags -= {ControlFlags.max_age, }
        headers['Cache-Control'] = ', '.join(flags)

        if ControlFlags.max_age in cache_info.control_flags:
            headers['Cache-Control'] += f', max-age={cache_info.max_age}'

    if cache_info.etag:
        headers['ETag'] = cache_info.etag

    if cache_info.expires_at:
        headers['Expires'] = cache_info.expires_at

    if cache_info.vary:
        headers['Vary'] = cache_info.vary

    return headers


def parse_web_time(time_str):
    dt = datetime.datetime.strptime(time_str, "%a, %d %b %Y %H:%M:%S %Z")
    return dt
