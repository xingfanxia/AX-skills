#!/usr/bin/env python3
"""梅花易数引擎 (Meihua Yishu Divination)

从 panpanmao domains/zhanbu/meihua/qigua-algorithms.ts 移植。

支持起卦法:
  - triple_number  : 三数起卦（最稳）
  - single_number  : 单数起卦（数字 + 当前时辰）
  - time           : 时间起卦（年支+月+日+时辰）
  - raw            : 直接给数学组件（测试用）

stdout JSON: {method, input, timing, result, knowledge_pointers}
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    read_input, json_response, read_lookup, lunar_info_for,
    normalize_xiantian, normalize_dongyao,
)

# panpanmao XIANTIAN_NUM_TO_GUA 映射
XIANTIAN_TO_BAGUA = {1: '乾', 2: '兑', 3: '离', 4: '震', 5: '巽', 6: '坎', 7: '艮', 8: '坤'}


def qigua_by_triple(n1: int, n2: int, n3: int) -> dict:
    """三数起卦 — panpanmao qiGuaByTripleNumber。"""
    return {
        'upperNum': normalize_xiantian(n1),
        'lowerNum': normalize_xiantian(n2),
        'dongYao': normalize_dongyao(n3),
    }


def qigua_by_single(n: int, shichen_num: int) -> dict:
    """单数起卦 — panpanmao qiGuaBySingleNumber。"""
    s = n + shichen_num
    return {
        'upperNum': normalize_xiantian(n),
        'lowerNum': normalize_xiantian(s),
        'dongYao': normalize_dongyao(s),
    }


def qigua_by_time(year_zhi_num: int, lunar_month: int, lunar_day: int, shichen_num: int) -> dict:
    """时间起卦 — panpanmao qiGuaByTime。"""
    s1 = year_zhi_num + lunar_month + lunar_day
    s2 = s1 + shichen_num
    return {
        'upperNum': normalize_xiantian(s1),
        'lowerNum': normalize_xiantian(s2),
        'dongYao': normalize_dongyao(s2),
    }


def find_hexagram_by_gua(upper_gua: str, lower_gua: str, hexagrams: dict) -> tuple[str, dict]:
    """根据上下卦名找 64 卦中对应卦。"""
    for name, hx in hexagrams.items():
        if hx.get('upperGua') == upper_gua and hx.get('lowerGua') == lower_gua:
            return name, hx
    return None, None


def find_hexagram_by_binary(binary: str, hexagrams: dict) -> tuple[str, dict]:
    """根据 6-bit binary 找卦（panpanmao convention）。"""
    for name, hx in hexagrams.items():
        if hx.get('binary') == binary:
            return name, hx
    return None, None


def flip_yao_in_binary(binary: str, yao_pos: int) -> str:
    """变爻：在 binary[yao_pos-1] 位翻转。"""
    chars = list(binary)
    idx = yao_pos - 1
    chars[idx] = '0' if chars[idx] == '1' else '1'
    return ''.join(chars)


def render_ascii_chart(ben_name: str, ben_hex: dict, dong_yao: int,
                       bian_name: str, bagua: dict) -> str:
    """渲染 ASCII 卦象图（本卦 + 之卦并排）。"""
    if not ben_hex:
        return f"梅花易数（卦象未识别）"

    binary = ben_hex['binary']
    bian_binary = flip_yao_in_binary(binary, dong_yao) if bian_name else None

    lines = [f"梅花易数 · {ben_name or '?'}" + (f" → {bian_name}" if bian_name else "")]
    lines.append("")
    upper_gua = ben_hex.get('upperGua', '')
    lower_gua = ben_hex.get('lowerGua', '')
    lines.append(f"上卦：{upper_gua}({bagua.get(upper_gua, {}).get('symbol', '')})")
    lines.append(f"下卦：{lower_gua}({bagua.get(lower_gua, {}).get('symbol', '')})")
    lines.append(f"动爻：第 {dong_yao} 爻")
    lines.append("")
    lines.append(f"本卦【{ben_name}】" + (f"     之卦【{bian_name}】" if bian_name else ""))
    for i in range(5, -1, -1):  # 从上爻往下渲染
        ben_yy = '━━━━━━━' if binary[i] == '1' else '━━ ━━ ━━'
        mark = ''
        if (i + 1) == dong_yao:
            mark = ' ←动'
        if bian_binary:
            bian_yy = '━━━━━━━' if bian_binary[i] == '1' else '━━ ━━ ━━'
            lines.append(f"  {ben_yy}{mark:<5}    {bian_yy}")
        else:
            lines.append(f"  {ben_yy}{mark}")
    return '\n'.join(lines)


def main():
    inp = read_input()
    method = inp.get('method', 'time')
    params = inp.get('params', {})
    iso_dt = inp.get('datetime')
    if not iso_dt:
        iso_dt = datetime.now().astimezone().isoformat()

    bagua = read_lookup('bagua')
    hexagrams = read_lookup('hexagrams_64')

    if method == 'triple_number':
        nums = params.get('numbers', [])
        if len(nums) < 3:
            raise ValueError('triple_number requires 3 numbers')
        gua = qigua_by_triple(nums[0], nums[1], nums[2])
        lunar = lunar_info_for(iso_dt)
    elif method == 'single_number':
        n = params.get('number') or (params.get('numbers') or [1])[0]
        lunar = lunar_info_for(iso_dt)
        gua = qigua_by_single(n, lunar['shichen_num'])
    elif method == 'raw':
        # 测试用直接给参数
        lunar = lunar_info_for(iso_dt) if iso_dt else None
        if 'upperNum' in params:
            gua = {
                'upperNum': params['upperNum'],
                'lowerNum': params['lowerNum'],
                'dongYao': params['dongYao'],
            }
        else:
            # raw with year/month/day/shichen components
            gua = qigua_by_time(
                params['yearZhi'], params['lunarMonth'],
                params['lunarDay'], params['shichen'],
            )
    else:  # time (default)
        lunar = lunar_info_for(iso_dt)
        gua = qigua_by_time(
            lunar['year_zhi_num'], lunar['lunar_month'],
            lunar['lunar_day'], lunar['shichen_num'],
        )

    upper_gua = XIANTIAN_TO_BAGUA[gua['upperNum']]
    lower_gua = XIANTIAN_TO_BAGUA[gua['lowerNum']]
    dong_yao = gua['dongYao']

    ben_name, ben_hex = find_hexagram_by_gua(upper_gua, lower_gua, hexagrams)

    bian_name, bian_hex = None, None
    if ben_hex:
        bian_binary = flip_yao_in_binary(ben_hex['binary'], dong_yao)
        bian_name, bian_hex = find_hexagram_by_binary(bian_binary, hexagrams)

    ascii_chart = render_ascii_chart(ben_name, ben_hex, dong_yao, bian_name, bagua)

    pointers = []
    if ben_name:
        pointers.append(f"data/meihua/hexagrams.md#{ben_name}")
    pointers.extend([
        "data/meihua/biangua-rule.md",
        "data/meihua/bagua.md",
    ])

    timing = {'datetime_iso': iso_dt}
    if lunar:
        timing.update({
            'lunar': f"{lunar['lunar_year_ganzhi']}年农历{lunar['lunar_month']}月{lunar['lunar_day']}日",
            'shichen': lunar['shichen'] + '时',
        })

    json_response({
        'method': 'meihua',
        'input': inp,
        'timing': timing,
        'result': {
            'primary_keyword': ben_name or '',
            'secondary_keywords': [
                bian_name or '',
                f'第{dong_yao}爻动',
                upper_gua + '/' + lower_gua,
            ],
            'ascii_chart': ascii_chart,
            'structured': {
                'upperGua': upper_gua,
                'lowerGua': lower_gua,
                'dongYao': dong_yao,
                'upperNum': gua['upperNum'],
                'lowerNum': gua['lowerNum'],
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
