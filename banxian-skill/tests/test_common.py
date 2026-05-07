"""Tests for scripts/_common.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from _common import (
    normalize_xiantian, normalize_dongyao,
    get_shichen_by_hour, get_ganzhi_year, lunar_info_for,
)


def test_normalize_xiantian_余0取8():
    assert normalize_xiantian(8) == 8
    assert normalize_xiantian(16) == 8
    assert normalize_xiantian(7) == 7
    assert normalize_xiantian(1) == 1


def test_normalize_dongyao_余0取6():
    assert normalize_dongyao(6) == 6
    assert normalize_dongyao(12) == 6
    assert normalize_dongyao(5) == 5


def test_shichen_by_hour():
    assert get_shichen_by_hour(23) == ('子', 1)
    assert get_shichen_by_hour(0) == ('子', 1)
    assert get_shichen_by_hour(15) == ('申', 9)
    assert get_shichen_by_hour(16) == ('申', 9)
    assert get_shichen_by_hour(11) == ('午', 7)


def test_ganzhi_year_1992_壬申():
    """1992 年应为壬申年（panpanmao 算例验证基础）。"""
    g, z = get_ganzhi_year(1992)
    assert g == '壬'
    assert z == '申'


def test_ganzhi_year_2026_丙午():
    g, z = get_ganzhi_year(2026)
    assert g == '丙'
    assert z == '午'


def test_lunar_info_for_2026_05_06_15_30():
    info = lunar_info_for('2026-05-06T15:30:00+08:00')
    # 2026-05-06 = 农历 2026年3月20日
    assert info['lunar_year'] == 2026
    assert info['lunar_month'] == 3
    assert info['lunar_day'] == 20
    assert info['lunar_year_ganzhi'] == '丙午'
    assert info['shichen'] == '申'
    assert info['shichen_num'] == 9


def test_lunar_info_for_panpanmao_算例():
    """1992-05-13 15:00 = 壬申年四月十一日申时。

    panpanmao validateTimeQiGua 用了 巳时 (6)，这里用申时验证基础信息。
    """
    info = lunar_info_for('1992-05-13T15:00:00+08:00')
    assert info['lunar_year'] == 1992
    assert info['lunar_month'] == 4
    assert info['lunar_day'] == 11
    assert info['lunar_year_ganzhi'] == '壬申'
