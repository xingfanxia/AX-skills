#!/usr/bin/env python3
"""六爻引擎 (Liuyao Divination)

从 panpanmao domains/zhanbu/liuyao/algorithms/divination.ts 移植。

输入 stdin: {method, params, datetime, question}
  method: "coin" (默认) | "number" | "time"
  params:
    - coin: {tosses: [V1..V6]}  # V 为 6/7/8/9, 不给则随机摇
    - number: {numbers: [n1, n2]}  # 双数起卦
  datetime: ISO8601, default = now

输出 stdout: 完整排盘 JSON
"""
from __future__ import annotations
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    read_input, json_response, read_lookup, lunar_info_for,
    normalize_xiantian, normalize_dongyao,
)

XIANTIAN_TO_BAGUA = {1: '乾', 2: '兑', 3: '离', 4: '震', 5: '巽', 6: '坎', 7: '艮', 8: '坤'}


def toss_coin() -> int:
    """模拟一次三枚铜钱：每枚 字=2 / 背=3，总和 6/7/8/9。"""
    return sum(random.choice([2, 3]) for _ in range(3))


def coin_value_to_yao(v: int) -> tuple[str, bool]:
    """6/7/8/9 → (阴阳, 是否动爻)。

    6=老阴(动)，7=少阳(静)，8=少阴(静)，9=老阳(动)
    """
    if v == 6:
        return '阴', True
    if v == 7:
        return '阳', False
    if v == 8:
        return '阴', False
    if v == 9:
        return '阳', True
    raise ValueError(f"Invalid coin value: {v} (must be 6/7/8/9)")


def find_hexagram_by_binary(binary: str, hexagrams: dict) -> tuple[str, dict]:
    """根据 6-bit binary 找卦（panpanmao convention）。"""
    for name, hx in hexagrams.items():
        if hx.get('binary') == binary:
            return name, hx
    return None, None


def find_hexagram_by_gua(upper: str, lower: str, hexagrams: dict) -> tuple[str, dict]:
    for name, hx in hexagrams.items():
        if hx.get('upperGua') == upper and hx.get('lowerGua') == lower:
            return name, hx
    return None, None


def render_ascii_chart(ben_name: str, ben_hex: dict, dong_yaos: list[int],
                       bian_name: str, bian_hex: dict) -> str:
    """渲染 ASCII 卦象（本卦 6 爻 + 之卦 6 爻 并排）。"""
    if not ben_hex:
        return f"六爻（卦象未识别）"

    binary = ben_hex['binary']
    bian_binary = bian_hex['binary'] if bian_hex else None
    yaos = ben_hex.get('yaos', [])

    lines = [f"六爻 · {ben_name or '?'}" + (f" → {bian_name}" if bian_name else "")]
    lines.append("")
    lines.append(f"卦宫：{ben_hex.get('palace', '')}（{ben_hex.get('palaceWuXing', '')}）")
    lines.append(f"世爻：第 {ben_hex.get('shiYao', '?')} 爻   "
                 f"应爻：第 {ben_hex.get('yingYao', '?')} 爻")
    lines.append("")
    header = f"  本卦【{ben_name or '?'}】"
    if bian_name:
        header += f"               之卦【{bian_name}】"
    lines.append(header)

    for i in range(5, -1, -1):  # 上爻 → 初爻
        pos = i + 1
        ben_yy = '━━━━━━━' if binary[i] == '1' else '━━ ━━ ━━'

        # 六亲 + 五行 + 干支
        if i < len(yaos):
            y = yaos[i]
            yao_meta = f"{y.get('liuqin', ''):<4}{y.get('tiangan', '')}{y.get('dizhi', '')}({y.get('wuxing', '')})"
        else:
            yao_meta = ''

        marks = []
        if pos in dong_yaos:
            marks.append('动')
        if pos == ben_hex.get('shiYao'):
            marks.append('世')
        if pos == ben_hex.get('yingYao'):
            marks.append('应')
        mark_str = '/'.join(marks)
        mark_part = f' [{mark_str}]' if mark_str else ''

        if bian_binary:
            bian_yy = '━━━━━━━' if bian_binary[i] == '1' else '━━ ━━ ━━'
            lines.append(f"  {ben_yy}{mark_part:<10}    {bian_yy}    {yao_meta}")
        else:
            lines.append(f"  {ben_yy}{mark_part:<10}    {yao_meta}")
    return '\n'.join(lines)


def main():
    inp = read_input()
    method = inp.get('method', 'coin')
    params = inp.get('params', {})
    iso_dt = inp.get('datetime')
    if not iso_dt:
        iso_dt = datetime.now().astimezone().isoformat()

    hexagrams = read_lookup('hexagrams_64')
    lunar = lunar_info_for(iso_dt)

    # 1) 起卦：得到 6 爻 yinyang + 动爻位
    if method == 'coin':
        tosses = params.get('tosses')
        if not tosses:
            tosses = [toss_coin() for _ in range(6)]

        if len(tosses) != 6:
            raise ValueError(f"coin method requires 6 tosses, got {len(tosses)}")

        yaos_data = []
        binary = ''
        dong_yaos = []
        for i, v in enumerate(tosses):
            yy, is_dong = coin_value_to_yao(v)
            yaos_data.append({'position': i + 1, 'yinyang': yy,
                              'isDong': is_dong, 'tossValue': v})
            binary += '1' if yy == '阳' else '0'
            if is_dong:
                dong_yaos.append(i + 1)

    elif method == 'number':
        nums = params.get('numbers', [])
        if len(nums) < 2:
            raise ValueError('number method requires 2 numbers')
        n1, n2 = nums[0], nums[1]
        upper_num = normalize_xiantian(n1)
        lower_num = normalize_xiantian(n2)
        dong_yao = normalize_dongyao(n1 + n2)

        upper_gua = XIANTIAN_TO_BAGUA[upper_num]
        lower_gua = XIANTIAN_TO_BAGUA[lower_num]

        ben_name, ben_hex = find_hexagram_by_gua(upper_gua, lower_gua, hexagrams)
        if not ben_hex:
            raise ValueError(f'Hexagram not found: {upper_gua}-{lower_gua}')
        binary = ben_hex['binary']
        dong_yaos = [dong_yao]
        # 从 ben_hex.yaos 提取 yinyang
        yaos_data = []
        for i, y in enumerate(ben_hex.get('yaos', [])):
            yaos_data.append({
                'position': i + 1,
                'yinyang': y.get('yinyang'),
                'isDong': (i + 1) == dong_yao,
            })

    elif method == 'time':
        s1 = lunar['year_zhi_num'] + lunar['lunar_month'] + lunar['lunar_day']
        s2 = s1 + lunar['shichen_num']
        upper_num = normalize_xiantian(s1)
        lower_num = normalize_xiantian(s2)
        dong_yao = normalize_dongyao(s2)

        upper_gua = XIANTIAN_TO_BAGUA[upper_num]
        lower_gua = XIANTIAN_TO_BAGUA[lower_num]

        ben_name, ben_hex = find_hexagram_by_gua(upper_gua, lower_gua, hexagrams)
        if not ben_hex:
            raise ValueError(f'Hexagram not found: {upper_gua}-{lower_gua}')
        binary = ben_hex['binary']
        dong_yaos = [dong_yao]
        yaos_data = []
        for i, y in enumerate(ben_hex.get('yaos', [])):
            yaos_data.append({
                'position': i + 1,
                'yinyang': y.get('yinyang'),
                'isDong': (i + 1) == dong_yao,
            })

    else:
        raise ValueError(f'Unknown method: {method}')

    # 2) 本卦
    ben_name, ben_hex = find_hexagram_by_binary(binary, hexagrams)

    # 3) 之卦：动爻翻转
    bian_name, bian_hex = None, None
    if dong_yaos and ben_hex:
        bian_chars = list(binary)
        for pos in dong_yaos:
            bian_chars[pos - 1] = '0' if bian_chars[pos - 1] == '1' else '1'
        bian_binary = ''.join(bian_chars)
        bian_name, bian_hex = find_hexagram_by_binary(bian_binary, hexagrams)

    # 4) ASCII 渲染
    ascii_chart = render_ascii_chart(ben_name, ben_hex, dong_yaos, bian_name, bian_hex)

    # 5) knowledge pointers — 64 卦按位置分 3 part
    pointers = []
    if ben_hex:
        idx = ben_hex.get('id', 0)
        if idx > 0:
            part = 1 if idx <= 22 else (2 if idx <= 44 else 3)
        else:
            part = 1
        pointers.append(f"data/liuyao/hexagrams-{part}.md#{ben_name}")
    pointers.extend(["data/liuyao/liuqin.md", "data/liuyao/shiying.md"])

    json_response({
        'method': 'liuyao',
        'input': inp,
        'timing': {
            'datetime_iso': iso_dt,
            'lunar': f"{lunar['lunar_year_ganzhi']}年农历{lunar['lunar_month']}月{lunar['lunar_day']}日",
            'shichen': lunar['shichen'] + '时',
        },
        'result': {
            'primary_keyword': ben_name or '',
            'secondary_keywords': [
                bian_name or '',
                f"动爻：{','.join(map(str, dong_yaos)) if dong_yaos else '无'}",
                ben_hex.get('palace', '') if ben_hex else '',
            ],
            'ascii_chart': ascii_chart,
            'structured': {
                'binary': binary,
                'tosses': params.get('tosses') if method == 'coin' else None,
                'yaos': yaos_data,
                'dongYaos': dong_yaos,
                'benGua': ben_name,
                'bianGua': bian_name,
                'benDetail': ben_hex,
                'bianDetail': bian_hex,
            },
        },
        'knowledge_pointers': pointers,
    })


if __name__ == '__main__':
    main()
