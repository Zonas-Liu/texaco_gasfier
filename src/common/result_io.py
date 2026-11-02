"""两套界面共用的结果文本兼容与出口字段解析。"""
import re


def read_result_text(path):
    """新输出固定 UTF-8；仍支持历史 Windows GBK 文件。"""
    raw = path.read_bytes()
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return raw.decode('gbk')


def parse_outlet(text):
    # 按明确字段定位，不依赖结果位于文件末尾，也不把产汽量误判为转化率。
    number = r'([-+]?\d+(?:\.\d*)?(?:[eEdD][-+]?\d+)?)'
    match = re.search(r'出口温度:\s*' + number + r'\s*C\s+碳转化率:\s*' + number, text)
    if not match:
        return {}
    return dict(zip(('Temperature(C)', 'CarbonConversion'),
                    (float(v.replace('D', 'E').replace('d', 'e')) for v in match.groups())))
