#!/usr/bin/env python3
"""小六壬占卜引擎 (Liuren Divination)

从 panpanmao domains/zhanbu/liuren/divination.ts + calculator.ts 移植。

stdin JSON: {method, params, datetime, question}
  method: "time" (默认) | "number" | "random"
  params: {numbers: [N]} for number method
  datetime: ISO8601, default = now

stdout JSON: {method, input, timing, result, knowledge_pointers}
"""
from __future__ import annotations
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    read_input, json_response, read_lookup, lunar_info_for,
)

# panpanmao LIUSHEN_NAMES order (index 0-5)
LIUSHEN_NAMES = ['大安', '留连', '速喜', '赤口', '小吉', '空亡']


def calculate_three_gongs(lunar_month: int, lunar_day: int, shichen_num: int) -> dict:
    """panpanmao calculateThreeGongs (time-based).

    Args:
        lunar_month: 农历月 (1-12)
        lunar_day: 农历日 (1-30)
        shichen_num: 时辰 1-12 (子=1, 丑=2, ..., 亥=12)
    """
    month_gong = (lunar_month - 1) % 6
    day_gong = (month_gong + lunar_day - 1) % 6
    hour_gong = (day_gong + shichen_num - 1) % 6
    return {
        'monthGong': month_gong,
        'dayGong': day_gong,
        'hourGong': hour_gong,
    }


def divine_by_time(lunar: dict) -> dict:
    """时间起卦：用农历月/日 + 时辰。"""
    return calculate_three_gongs(
        lunar['lunar_month'],
        lunar['lunar_day'],
        lunar['shichen_num'],
    )


def divine_by_number(num: int) -> dict:
    """报数起卦 — panpanmao divineByNumber 算法。

    与时间无关，纯数字驱动。
    monthGong = num % 6
    dayGong = (num*7 + 3) % 6
    hourGong = (num*11 + 5) % 6
    """
    seed = abs(num)
    return {
        'monthGong': seed % 6,
        'dayGong': (seed * 7 + 3) % 6,
        'hourGong': (seed * 11 + 5) % 6,
    }


def divine_random() -> dict:
    """随机起卦 — 每宫独立 0-5。"""
    return {
        'monthGong': random.randint(0, 5),
        'dayGong': random.randint(0, 5),
        'hourGong': random.randint(0, 5),
    }


def is_auspicious(name: str) -> bool:
    """6 神吉凶（panpanmao isAuspicious）。"""
    return name in {'大安', '速喜', '小吉'}


def main():
    inp = read_input()
    method = inp.get('method', 'time')
    params = inp.get('params', {})
    iso_dt = inp.get('datetime')
    question = inp.get('question', '')

    # default to now if no datetime
    if not iso_dt:
        iso_dt = datetime.now().astimezone().isoformat()

    lunar = lunar_info_for(iso_dt)
    liushen = read_lookup('liushen')

    if method == 'number':
        nums = params.get('numbers', [])
        if not nums:
            raise ValueError('number method requires params.numbers[0]')
        gongs_idx = divine_by_number(nums[0])
    elif method == 'random':
        gongs_idx = divine_random()
    else:  # time
        gongs_idx = divine_by_time(lunar)

    # 索引 → 名称
    month_name = LIUSHEN_NAMES[gongs_idx['monthGong']]
    day_name = LIUSHEN_NAMES[gongs_idx['dayGong']]
    hour_name = LIUSHEN_NAMES[gongs_idx['hourGong']]
    primary = hour_name  # 时宫为主卦
    main_info = liushen.get(primary, {})

    # 三宫吉凶 pattern
    pattern = ''.join('吉' if is_auspicious(n) else '凶'
                      for n in [month_name, day_name, hour_name])
    triple_same = month_name == day_name == hour_name

    ascii_chart = (
        f"小六壬 · 主卦【{primary}】({main_info.get('alias', '')})\n"
        f"┌────────┬────────┬────────┐\n"
        f"│  月宫  │  日宫  │  时宫  │\n"
        f"├────────┼────────┼────────┤\n"
        f"│  {month_name:<5}│  {day_name:<5}│  {hour_name:<5}│\n"
        f"└────────┴────────┴────────┘\n"
        f"  {'吉' if is_auspicious(month_name) else '凶'}    "
        f"  {'吉' if is_auspicious(day_name) else '凶'}    "
        f"  {'吉' if is_auspicious(hour_name) else '凶'}     pattern: {pattern}"
    )

    # knowledge pointers
    pointers = [
        f"data/liuren/liushen.md#{primary}",
        f"data/liuren/combinations.md",
    ]
    if main_info.get('classicVerse'):
        pointers.append(f"data/liuren/scenarios.md")

    json_response({
        'method': 'liuren',
        'input': inp,
        'timing': {
            'datetime_iso': iso_dt,
            'lunar': f"{lunar['lunar_year_ganzhi']}年农历{lunar['lunar_month']}月{lunar['lunar_day']}日",
            'shichen': lunar['shichen'] + '时',
            'shichen_num': lunar['shichen_num'],
        },
        'result': {
            'primary_keyword': primary,
            'secondary_keywords': [
                lunar['shichen'] + '时',
                main_info.get('element', ''),
                main_info.get('nature', ''),
            ],
            'ascii_chart': ascii_chart,
            'structured': {
                'mainResult': {
                    'name': primary,
                    'alias': main_info.get('alias'),
                    'nature': main_info.get('nature'),
                    'element': main_info.get('element'),
                    'direction': main_info.get('direction'),
                    'score': main_info.get('score'),
                    'state': main_info.get('state'),
                    'classicVerse': main_info.get('classicVerse'),
                    'coreSemantics': main_info.get('coreSemantics'),
                    'keyPoints': main_info.get('keyPoints', []),
                    'positiveTransform': main_info.get('positiveTransform'),
                },
                'threeGongs': {
                    '月宫': {'name': month_name, 'meaning': '天时/起因',
                             'type': '吉' if is_auspicious(month_name) else '凶'},
                    '日宫': {'name': day_name, 'meaning': '地利/过程',
                             'type': '吉' if is_auspicious(day_name) else '凶'},
                    '时宫': {'name': hour_name, 'meaning': '人和/结果（主卦）',
                             'type': '吉' if is_auspicious(hour_name) else '凶'},
                },
                'analysis': {
                    'pattern': pattern,
                    'tripleSame': triple_same,
                },
            },
        },
        'knowledge_pointers': pointers,
    })


if __name__ == '__main__':
    main()
