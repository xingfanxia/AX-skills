#!/usr/bin/env bash
# test_lint_fixtures.sh —— 检测器 golden-fixture 回归（把脚本调到"敢用"的护栏）
#
# 借鉴 oh-story 的 test-ai-patterns 思路（但不抄它 21 个多平台 test-*.sh）：
# 用最小正反样本断言——正样本【必须命中】、负样本【必须静默】。
# 负样本专挑【最容易误伤】的合法网文形态：弹幕道歉刷屏×3 / 排比 / either-or(不是A就是B) /
# 句尾反问(是吗) / 连词尾(只是·但是·于是) / 纯对话短句。直击豪子"工具误伤多"痛点。
#
# 用法：bash scripts/test_lint_fixtures.sh  （退出码 0=全过，1=有回归）
set -u
cd "$(dirname "$0")/.."
PY="${PYBIN:-python3}"
F=scripts/fixtures
pass=0; fail=0
ok(){ echo "  ✅ $1"; pass=$((pass+1)); }
no(){ echo "  ❌ $1"; fail=$((fail+1)); }

# 正样本：必须命中（退出码 1）
$PY scripts/antislop_lint.py "$F/positive-antislop.txt" >/dev/null 2>&1 && no "antislop 漏报 positive-antislop" || ok "antislop 命中 positive-antislop"
$PY scripts/degeneration_check.py "$F/positive-degeneration.txt" >/dev/null 2>&1 && no "degeneration 漏报 positive-degeneration" || ok "degeneration 命中 positive-degeneration"

# 负样本：必须静默——degeneration 必须 0（合法弹幕/排比/either-or/句尾吗 不算退化）
$PY scripts/degeneration_check.py "$F/negative-clean.txt" >/dev/null 2>&1 && ok "degeneration 放过 negative-clean(无误伤)" || no "degeneration 误伤 negative-clean"
# 负样本：antislop 的【不是A而是B】检测器对 either-or/句尾吗/连词尾 必须 0 命中
hits=$($PY - <<PYEOF
from importlib import util
s=util.spec_from_file_location("a","scripts/antislop_lint.py");m=util.module_from_spec(s);s.loader.exec_module(m)
print(len(m.find_not_is(open("$F/negative-clean.txt",encoding="utf-8").read())))
PYEOF
)
[ "$hits" = "0" ] && ok "find_not_is 不误伤 either-or/是吗/连词尾(0 命中)" || no "find_not_is 误伤 negative-clean($hits 命中)"

echo "  ── fixtures: PASS=$pass FAIL=$fail ──"
[ "$fail" -eq 0 ]
