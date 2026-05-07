"""Tests for scripts/meihua.py。

panpanmao 验证算例：壬申年四月十一日巳时。
  yearZhi(申)=9, lunarMonth=4, lunarDay=11, shichen(巳)=6
  sum1 = 9+4+11 = 24, sum1%8 = 0 → 8 (坤)
  sum2 = 24+6 = 30, sum2%8 = 6 (坎)
  dongYao = 30%6 = 0 → 6 (上爻)
  应得：地水师卦，上爻动
"""
import json
import subprocess
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / 'scripts' / 'meihua.py')


def call(payload: dict) -> dict:
    r = subprocess.run(
        ['python3', SCRIPT],
        input=json.dumps(payload),
        capture_output=True, text=True, check=True,
    )
    return json.loads(r.stdout)


def test_triple_number_basic():
    r = call({
        "method": "triple_number",
        "params": {"numbers": [3, 7, 11]},
        "datetime": "2026-05-06T15:30:00+08:00",
    })
    assert r['method'] == 'meihua'
    s = r['result']['structured']
    assert s['benGua']
    assert s['bianGua']
    assert 1 <= s['dongYao'] <= 6


def test_panpanmao_validation_case_壬申年():
    """1992-05-13 巳时 (lunar 4月11日, year_zhi=申=9, shichen=巳=6).

    panpanmao validateTimeQiGua 预期：上卦坤=8, 下卦坎=6, 动爻=6。
    """
    r = call({
        "method": "raw",
        "params": {"yearZhi": 9, "lunarMonth": 4, "lunarDay": 11, "shichen": 6},
        "datetime": "1992-05-13T09:00:00+08:00",
    })
    s = r['result']['structured']
    assert s['upperNum'] == 8, f"expected upperNum=8 (坤), got {s['upperNum']}"
    assert s['lowerNum'] == 6, f"expected lowerNum=6 (坎), got {s['lowerNum']}"
    assert s['dongYao'] == 6, f"expected dongYao=6, got {s['dongYao']}"
    assert s['upperGua'] == '坤'
    assert s['lowerGua'] == '坎'
    # 应是地水师卦
    assert s['benGua'] == '师'


def test_乾为天_triple():
    """三数全 8 → upper=8(坤), lower=8(坤), dongYao=8%6=2 → 坤为地, 动爻 2"""
    r = call({"method": "triple_number", "params": {"numbers": [8, 8, 8]}})
    s = r['result']['structured']
    assert s['upperGua'] == '坤'
    assert s['lowerGua'] == '坤'
    assert s['benGua'] == '坤'
    assert s['dongYao'] == 2


def test_knowledge_pointers():
    r = call({"method": "triple_number", "params": {"numbers": [3, 7, 11]}})
    assert any('hexagrams' in p for p in r['knowledge_pointers'])
    assert any('biangua-rule' in p for p in r['knowledge_pointers'])


def test_bian_gua_computed():
    """动爻翻转后应得到不同卦。"""
    r = call({"method": "triple_number", "params": {"numbers": [1, 1, 3]}})
    s = r['result']['structured']
    # upper=1(乾), lower=1(乾) → 乾为天 binary=111111
    # dongYao=3 → 翻转第 3 位：111111 → 111011 (panpanmao convention)
    # 之卦应非 乾
    assert s['benGua'] == '乾'
    assert s['bianGua'] is not None
    assert s['bianGua'] != '乾'
