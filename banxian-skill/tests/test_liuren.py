"""Tests for scripts/liuren.py。

算例验证：复现 panpanmao divineByNumber 与 divine 的预期输出。
"""
import json
import subprocess
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / 'scripts' / 'liuren.py')


def call(payload: dict) -> dict:
    r = subprocess.run(
        ['python3', SCRIPT],
        input=json.dumps(payload),
        capture_output=True, text=True, check=True,
    )
    return json.loads(r.stdout)


def test_basic_number_divination():
    r = call({
        "method": "number",
        "params": {"numbers": [3]},
        "datetime": "2026-05-06T15:30:00+08:00",
        "question": "财运如何",
    })
    assert r['method'] == 'liuren'
    assert r['result']['primary_keyword'] in ['大安', '留连', '速喜', '赤口', '小吉', '空亡']
    assert r['timing']['shichen'] == '申时'


def test_panpanmao_number_algo_consistency():
    """panpanmao divineByNumber: monthGong = num%6, dayGong = (num*7+3)%6, hourGong = (num*11+5)%6.

    For num=7:
      monthGong = 7%6 = 1 → 留连
      dayGong = (49+3)%6 = 52%6 = 4 → 小吉
      hourGong = (77+5)%6 = 82%6 = 4 → 小吉
    """
    r = call({"method": "number", "params": {"numbers": [7]},
              "datetime": "2026-05-06T15:30:00+08:00"})
    s = r['result']['structured']
    assert s['threeGongs']['月宫']['name'] == '留连'
    assert s['threeGongs']['日宫']['name'] == '小吉'
    assert s['threeGongs']['时宫']['name'] == '小吉'
    assert r['result']['primary_keyword'] == '小吉'


def test_panpanmao_time_algo_consistency():
    """panpanmao calculateThreeGongs (time-based) for 1992-05-13 15:00 (壬申年四月十一日申时):
      lunar_month=4, lunar_day=11, shichen_num=9 (申时)
      monthGong = (4-1)%6 = 3 → 赤口
      dayGong = (3 + 11 - 1)%6 = 13%6 = 1 → 留连
      hourGong = (1 + 9 - 1)%6 = 9%6 = 3 → 赤口
    """
    r = call({"method": "time", "datetime": "1992-05-13T15:00:00+08:00"})
    s = r['result']['structured']
    assert s['threeGongs']['月宫']['name'] == '赤口'
    assert s['threeGongs']['日宫']['name'] == '留连'
    assert s['threeGongs']['时宫']['name'] == '赤口'
    assert r['result']['primary_keyword'] == '赤口'


def test_knowledge_pointers_present():
    r = call({"method": "random", "datetime": "2026-05-06T15:30:00+08:00"})
    assert any('liushen' in p for p in r['knowledge_pointers'])


def test_main_info_loaded():
    """主卦信息（来自 liushen.json）应附在 structured.mainResult。"""
    r = call({"method": "number", "params": {"numbers": [7]},
              "datetime": "2026-05-06T15:30:00+08:00"})
    main = r['result']['structured']['mainResult']
    assert main['name'] == '小吉'
    assert main['alias'] == '六合'  # panpanmao knowledge data
    assert main['element'] == '木'
