"""Tests for scripts/liuyao.py."""
import json
import subprocess
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / 'scripts' / 'liuyao.py')


def call(payload: dict) -> dict:
    r = subprocess.run(
        ['python3', SCRIPT],
        input=json.dumps(payload),
        capture_output=True, text=True, check=True,
    )
    return json.loads(r.stdout)


def test_coin_all_少阳_乾为天():
    """6 个 7（少阳）→ 全阳爻 → 乾为天，无动爻无之卦。"""
    r = call({
        "method": "coin",
        "params": {"tosses": [7, 7, 7, 7, 7, 7]},
        "datetime": "2026-05-06T15:30:00+08:00",
    })
    assert r['method'] == 'liuyao'
    assert r['result']['primary_keyword'] == '乾'
    s = r['result']['structured']
    assert s['binary'] == '111111'
    assert s['dongYaos'] == []
    assert s['bianGua'] is None


def test_coin_all_少阴_坤为地():
    """6 个 8（少阴）→ 全阴爻 → 坤为地，无动爻。"""
    r = call({"method": "coin", "params": {"tosses": [8, 8, 8, 8, 8, 8]},
              "datetime": "2026-05-06T15:30:00+08:00"})
    s = r['result']['structured']
    assert s['binary'] == '000000'
    assert r['result']['primary_keyword'] == '坤'
    assert s['dongYaos'] == []


def test_coin_with_老阳_动爻():
    """第一爻 9（老阳动），其余 7（少阳）→ 乾 + 初爻动 → 之卦履（panpanmao convention）。

    NB: panpanmao 内部 binary convention 下，乾(111111) 第一爻翻转为 011111，
    对应 panpanmao 的 天泽履（上乾下兑）。在 standard 易经里同样的操作得天风姤。
    本 skill mirror panpanmao 行为以保持知识库一致。
    """
    r = call({"method": "coin", "params": {"tosses": [9, 7, 7, 7, 7, 7]},
              "datetime": "2026-05-06T15:30:00+08:00"})
    s = r['result']['structured']
    assert s['binary'] == '111111'  # 第一爻 9 = 阳
    assert 1 in s['dongYaos']
    assert s['benGua'] == '乾'
    # 之卦：panpanmao convention 下 011111 = 履
    assert s['bianGua'] == '履'


def test_coin_with_老阴_动爻():
    """6 个 6（老阴，动）→ 坤 + 全爻动 → 之卦乾"""
    r = call({"method": "coin", "params": {"tosses": [6, 6, 6, 6, 6, 6]},
              "datetime": "2026-05-06T15:30:00+08:00"})
    s = r['result']['structured']
    assert s['binary'] == '000000'  # 老阴 = 阴
    assert s['benGua'] == '坤'
    assert s['dongYaos'] == [1, 2, 3, 4, 5, 6]
    # 全爻翻转：000000 → 111111 → 乾
    assert s['bianGua'] == '乾'


def test_coin_random_when_no_tosses():
    """不给 tosses 时应自动模拟。"""
    r = call({"method": "coin", "datetime": "2026-05-06T15:30:00+08:00"})
    s = r['result']['structured']
    assert len(s['yaos']) == 6
    assert s['benGua']  # should resolve to some hexagram


def test_yao_metadata_complete():
    """每爻应有 liuqin/wuxing/tiangan/dizhi（来自 hexagrams_64.json）。"""
    r = call({"method": "coin", "params": {"tosses": [7, 7, 7, 7, 7, 7]},
              "datetime": "2026-05-06T15:30:00+08:00"})
    ben_detail = r['result']['structured']['benDetail']
    assert ben_detail
    yaos = ben_detail['yaos']
    assert len(yaos) == 6
    for y in yaos:
        assert 'liuqin' in y
        assert 'wuxing' in y
        assert 'tiangan' in y
        assert 'dizhi' in y
        assert 'yaoCi' in y


def test_invalid_toss_value():
    """非法 toss 值应报错。"""
    import subprocess
    r = subprocess.run(
        ['python3', SCRIPT],
        input=json.dumps({"method": "coin", "params": {"tosses": [5, 7, 7, 7, 7, 7]}}),
        capture_output=True, text=True,
    )
    assert r.returncode != 0
    assert 'Invalid coin value' in r.stderr or 'Invalid' in r.stderr


def test_knowledge_pointers():
    r = call({"method": "coin", "params": {"tosses": [7, 7, 7, 7, 7, 7]}})
    pts = r['knowledge_pointers']
    assert any('hexagrams-' in p for p in pts)
    assert any('liuqin' in p for p in pts)
    assert any('shiying' in p for p in pts)


def test_shi_ying_present():
    """世应位置应在 ascii_chart 中标注。"""
    r = call({"method": "coin", "params": {"tosses": [7, 7, 7, 7, 7, 7]}})
    chart = r['result']['ascii_chart']
    assert '世' in chart
    assert '应' in chart
