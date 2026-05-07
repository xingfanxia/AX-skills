#!/usr/bin/env python3
"""共享工具：农历转换、八卦、五行、JSON IO。

本文件被 liuren.py / meihua.py / liuyao.py 共享。
唯一外部依赖：lunardate（农历转换）。
"""
from __future__ import annotations
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from lunardate import LunarDate

LOOKUP_DIR = Path(__file__).parent / "_lookup"

DIZHI_ORDER = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

# 时辰 → (name, number 1-12)。子时 23-01 跨日。
SHICHEN_RANGES = [
    ('子', 1, [23, 0]),
    ('丑', 2, [1, 2]),
    ('寅', 3, [3, 4]),
    ('卯', 4, [5, 6]),
    ('辰', 5, [7, 8]),
    ('巳', 6, [9, 10]),
    ('午', 7, [11, 12]),
    ('未', 8, [13, 14]),
    ('申', 9, [15, 16]),
    ('酉', 10, [17, 18]),
    ('戌', 11, [19, 20]),
    ('亥', 12, [21, 22]),
]

TIANGAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']

DIZHI_WUXING = {
    '子':'水','亥':'水','丑':'土','辰':'土','未':'土','戌':'土',
    '寅':'木','卯':'木','巳':'火','午':'火','申':'金','酉':'金',
}

WUXING_SHENG = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
WUXING_KE = {'木':'土','土':'水','水':'火','火':'金','金':'木'}


def normalize_xiantian(n: int) -> int:
    """正整数 → 1-8 先天数，余 0 取 8（坤）。"""
    r = n % 8
    return 8 if r == 0 else r


def normalize_dongyao(n: int) -> int:
    """正整数 → 1-6 动爻位，余 0 取 6（上爻）。"""
    r = n % 6
    return 6 if r == 0 else r


def get_shichen_by_hour(hour: int) -> tuple[str, int]:
    """小时 (0-23) → (时辰名, 时辰数 1-12)。"""
    for name, num, hrs in SHICHEN_RANGES:
        if hour in hrs:
            return name, num
    raise ValueError(f"Invalid hour: {hour}")


def get_ganzhi_year(year: int) -> tuple[str, str]:
    """公元年份 → (天干, 地支)。公元 4 年 = 甲子年 (offset 0)。"""
    offset = (year - 4) % 60
    return TIANGAN[offset % 10], DIZHI_ORDER[offset % 12]


def lunar_info_for(iso_datetime: str) -> dict:
    """ISO datetime 字符串 → 农历完整信息。"""
    dt = datetime.fromisoformat(iso_datetime)
    lunar = LunarDate.fromSolarDate(dt.year, dt.month, dt.day)

    yg, yz = get_ganzhi_year(lunar.year)
    shichen_name, shichen_num = get_shichen_by_hour(dt.hour)

    return {
        'datetime_iso': iso_datetime,
        'lunar_year': lunar.year,
        'lunar_month': lunar.month,
        'lunar_day': lunar.day,
        'lunar_year_ganzhi': yg + yz,
        'shichen': shichen_name,
        'shichen_num': shichen_num,
        'year_zhi_num': DIZHI_ORDER.index(yz) + 1,
    }


def read_lookup(name: str) -> Any:
    """读 _lookup/<name>.json"""
    return json.loads((LOOKUP_DIR / f"{name}.json").read_text(encoding='utf-8'))


def json_response(payload: dict) -> None:
    """统一输出到 stdout"""
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def read_input() -> dict:
    """从 stdin 读 JSON"""
    return json.loads(sys.stdin.read())
