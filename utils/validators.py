import re
from typing import Optional
from datetime import timedelta

def parse_time(time_str: str) -> Optional[int]:
    """Парсит время в формате 10m, 1h, 1d в секунды"""
    if not time_str:
        return None
    
    time_str = time_str.lower()
    multiplier = 1
    
    if time_str.endswith('s'):
        multiplier = 1
        time_str = time_str[:-1]
    elif time_str.endswith('m'):
        multiplier = 60
        time_str = time_str[:-1]
    elif time_str.endswith('h'):
        multiplier = 3600
        time_str = time_str[:-1]
    elif time_str.endswith('d'):
        multiplier = 86400
        time_str = time_str[:-1]
    
    try:
        return int(time_str) * multiplier
    except ValueError:
        return None

def is_valid_url(url: str) -> bool:
    """Проверяет валидность URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)',  # path
        re.IGNORECASE
    )
    return re.match(url_pattern, url) is not None
