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

# 把另外 4 个脚本也纳入护栏（之前只覆盖 antislop+degeneration 2/6）
$PY scripts/state_apply.py --self-test >/dev/null 2>&1 && ok "state_apply --self-test 全过" || no "state_apply self-test 回归"

# output_check --whitelist 冒烟（专抓 import os 这类崩——非工程师的反误伤命脉路径）
TMP=$(mktemp -d)
printf 'config: {chapter_length: {min: 5, max: 9000}}\n' > "$TMP/c.yaml"
printf '缓缓\n' > "$TMP/wl.txt"
printf '林照缓缓抬头，转身走了。\n' > "$TMP/body.txt"
$PY scripts/output_check.py "$TMP/body.txt" --contract "$TMP/c.yaml" --whitelist "$TMP/wl.txt" >/dev/null 2>&1 \
  && ok "output_check --whitelist 不崩(import os)" || no "output_check --whitelist 崩了"

# compile_prompt 冒烟 + 钉死 F2：forbidden_reveals 的答案原文【绝不】出现在 prompt
printf 'config: {chapter_length: {target: 2500, min: 2000, max: 3200}}\nlocked_reveals:\n  - {reveal: "韩执事其实是主角生父", reveal_at_volume: 5}\n' > "$TMP/contract.yaml"
printf 'world_facts: []\npower_system: {ladder: []}\n' > "$TMP/state-world.yaml"
printf 'characters: []\n' > "$TMP/state-characters.yaml"
printf 'per_chapter: []\n' > "$TMP/rolling-summary.yaml"
printf '{"chapter_id":12,"pov":"x","word_budget":{"min":2000,"max":3200},"chapter_purpose":"x","scenes":[],"must_happen":[],"must_not_happen":[],"ending_hook":{"type":"悬念式"},"on_stage_characters":[],"relevant_canon_ids":[],"forbidden_reveals":["韩执事其实是主角生父"],"due_foreshadows":[]}\n' > "$TMP/ch.json"
out=$($PY scripts/compile_prompt.py "$TMP" "$TMP/ch.json" --current-volume 1 --current-chapter 12 2>/dev/null)
if [ $? -eq 0 ] && ! printf '%s' "$out" | grep -q "韩执事其实是主角生父"; then
  ok "compile_prompt 不泄漏 forbidden_reveals 答案(剧透-入闸)"; else no "compile_prompt 泄漏了剧透答案"; fi
rm -rf "$TMP"

echo "  ── fixtures: PASS=$pass FAIL=$fail ──"
[ "$fail" -eq 0 ]
