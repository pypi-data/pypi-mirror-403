from datetime import datetime, date
import re

def sort_logs_with_stacktrace(logs: str, reverse: bool = False) -> str:
    """
    按时间块排序日志，保持堆栈/详细信息与主日志在一起

    支持的时间戳格式：
    - 完整格式: 2025-07-18 15:46:02.330
    - 仅时间: 15:46:02.330

    支持的前缀格式：允许数字前缀加冒号，如 "209:2025-11-26 21:59:54.826"

    :param logs: 原始日志字符串
    :param reverse: 是否降序（True=最新在前）
    """

    TIMESTAMP_PATTERN = r'\d{2}:\d{2}:\d{2}\.\d{3}'
    FULL_TIMESTAMP_PATTERN = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}'
    
    def detect_format(logs: str) -> tuple[str, date | None]:
        """检测日志使用的时间戳格式"""
        for line in logs.split('\n'):
            # 优先匹配完整时间戳格式
            full_match = re.search(FULL_TIMESTAMP_PATTERN, line)
            if full_match:
                date_part = full_match.group(0).split(' ')[0]
                date_obj = datetime.strptime(date_part, '%Y-%m-%d').date()
                return 'full', date_obj

            # 匹配仅时间格式
            time_match = re.search(TIMESTAMP_PATTERN, line)
            if time_match:
                return 'time_only', None
        return 'unknown', None
    
    def parse_timestamp(line: str, format_type: str, default_date: date | None) -> datetime:
        """解析时间戳"""
        try:
            # 优先尝试完整时间戳格式
            full_match = re.search(FULL_TIMESTAMP_PATTERN, line)
            if full_match:
                time_str = full_match.group(0)
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')

            # 如果没有完整时间戳，尝试仅时间格式
            time_match = re.search(TIMESTAMP_PATTERN, line)
            if time_match and default_date:
                time_str = time_match.group(0)
                time_obj = datetime.strptime(time_str, '%H:%M:%S.%f')
                return datetime.combine(default_date, time_obj.time())

            return datetime.min

        except (ValueError, IndexError):
            return datetime.min
    
    # 检测格式并处理
    format_type, default_date = detect_format(logs)
    
    blocks = []
    current_block = None
    
    for line in logs.split('\n'):
        line = line.rstrip()
        if not line:
            continue
        
        has_timestamp = False
        if format_type == 'full':
            # 对于完整格式，允许完整时间戳或仅时间戳
            has_timestamp = (re.search(FULL_TIMESTAMP_PATTERN, line) is not None or
                            re.search(TIMESTAMP_PATTERN, line) is not None)
        elif format_type == 'time_only':
            has_timestamp = re.search(TIMESTAMP_PATTERN, line) is not None

        if has_timestamp:
            if current_block:
                blocks.append(current_block)
            
            current_block = {
                'timestamp': parse_timestamp(line, format_type, default_date),
                'lines': [line]
            }
        else:
            if current_block:
                current_block['lines'].append(line)
            else:
                current_block = {
                    'timestamp': datetime.min,
                    'lines': [line]
                }
    
    if current_block:
        blocks.append(current_block)
    
    sorted_blocks = sorted(blocks, key=lambda b: b['timestamp'], reverse=reverse)
    
    return '\n'.join(line for block in sorted_blocks for line in block['lines'])


