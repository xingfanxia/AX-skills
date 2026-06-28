#!/usr/bin/env python3
"""
state_check.py —— 状态层不变式校验器（把"靠勤奋 maintain"换成"靠代码强制"）

长篇崩坏的根因是 AI 自我一致性随篇幅衰减，靠模型自觉或人工 diligence 兜不住。
本脚本把"能用确定性代码判定的一致性不变式"机检出来，作为每卷边界/发布前的体检。
它不替代 LLM continuity-checker（语义级矛盾仍需 LLM），只抓【机械可判】的那部分。

校验项：
  1. Canon 状态枚举合法（Canon/Pending/Rejected/Idea/Inferred）
  2. visible_from_volume 是正整数
  3. 力量阶位单调：所有角色 current_state.level 必须在 power_system.ladder 中，
     且（若 monotonic=true）按章序不倒退——需配合历史，这里查"是否在阶位表内"
  4. 伏笔台账：逾期未回收(当前章 > planned_payoff_ch 仍 open)、临近回收、密度告警(open>>closed)
  5. 情绪债：released=false 且 拖过 N 章未释放；release_intensity < intensity（释放不解气）
  6. glossary 别名冲突：同一别名指向多个 canon_name；canon_name 缺失

用法：
  python3 state_check.py <book_state_dir>            # 目录含 contract.yaml + state-*.yaml + *-ledger.yaml
  python3 state_check.py --json <book_state_dir>
  python3 state_check.py --current-chapter 88 <dir>  # 覆盖"当前章"（否则读 contract.meta.current_chapter）

退出码：0 = 无 error（可有 warning），1 = 有 error（必须人工处理）。
"""
import sys
import os
import json
import argparse

try:
    import yaml
except ImportError:
    sys.stderr.write("需要 PyYAML：pip install pyyaml\n")
    sys.exit(2)

CANON_STATES = {"Canon", "Pending", "Rejected", "Idea", "Inferred"}


def load(d, name):
    p = os.path.join(d, name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def walk_canon(obj, path, issues):
    """递归找所有带 canon_status 的条目并校验枚举 + visible_from_volume。"""
    if isinstance(obj, dict):
        if "canon_status" in obj:
            cs = obj.get("canon_status")
            if cs not in CANON_STATES:
                issues.append(("error", f"{path}: 非法 canon_status={cs!r}，应为 {sorted(CANON_STATES)}"))
            v = obj.get("visible_from_volume")
            if v is not None and (not isinstance(v, int) or v < 1):
                issues.append(("error", f"{path}: visible_from_volume={v!r} 应为正整数"))
        for k, val in obj.items():
            walk_canon(val, f"{path}.{k}", issues)
    elif isinstance(obj, list):
        for i, val in enumerate(obj):
            walk_canon(val, f"{path}[{i}]", issues)


def check(d, current_chapter):
    issues = []
    contract = load(d, "contract.yaml") or {}
    world = load(d, "state-world.yaml") or {}
    chars = load(d, "state-characters.yaml") or {}
    fore = load(d, "foreshadow-ledger.yaml") or {}
    emo = load(d, "emotion-debt.yaml") or {}
    plot = load(d, "state-plotline.yaml") or {}

    cursor = plot.get("cursor") or {}
    if current_chapter is None:
        # 优先用 state_apply 维护的 cursor.last_chapter_done，回落到 contract.meta
        current_chapter = cursor.get("last_chapter_done") or (contract.get("meta") or {}).get("current_chapter", 0) or 0

    # 1+2 Canon 枚举 / 可见性
    for nm, obj in [("world", world), ("characters", chars)]:
        walk_canon(obj, nm, issues)

    # 3 力量阶位
    ladder = ((world.get("power_system") or {}).get("ladder")) or []
    ladder_set = set(ladder)
    if ladder:
        for c in (chars.get("characters") or []):
            lv = ((c.get("current_state") or {}).get("level")) or ""
            if lv and lv not in ladder_set:
                issues.append(("warning", f"角色 {c.get('id')} 当前境界 {lv!r} 不在阶位表 ladder 中（可能错字/越级）"))

    # 4 伏笔台账
    fl = fore.get("foreshadows") or []
    open_n = sum(1 for x in fl if x.get("status") == "open")
    closed_n = sum(1 for x in fl if x.get("status") == "closed")
    for x in fl:
        if x.get("status") in ("open", "微回应"):
            pp = x.get("planned_payoff_ch")
            if not pp:
                issues.append(("warning", f"伏笔 {x.get('id')} 无 planned_payoff_ch（埋了没回收计划=烂尾风险）"))
            elif isinstance(pp, int) and current_chapter > pp:
                issues.append(("error", f"伏笔 {x.get('id')} 逾期未回收（计划 {pp} 章，已到 {current_chapter} 章仍 {x.get('status')}）"))
            elif isinstance(pp, int) and 0 < pp - current_chapter <= 5:
                issues.append(("warning", f"伏笔 {x.get('id')} 临近回收（计划 {pp} 章，当前 {current_chapter}）"))
    if open_n > 0 and open_n >= 3 * (closed_n + 1):
        issues.append(("warning", f"伏笔密度告警：open={open_n} 远多于 closed={closed_n}（伏笔密度超过闭合速度，崩铁翁法罗斯式翻车风险）"))

    # 5 情绪债（duration 按当前章实时推算，单一真相在 incurred_ch；不读 state_apply 恒写 0 的死字段）
    for db in (emo.get("emotion_debts") or []):
        if not db.get("released", False):
            inc = db.get("incurred_ch") or 0
            dur = (current_chapter - inc) if (inc and current_chapter) else (db.get("duration_chapters", 0) or 0)
            if dur >= 5:
                issues.append(("warning", f"情绪债 {db.get('debt_id')} 已压抑 {dur} 章未释放（虐点久未补偿）"))
        inten = db.get("intensity", 0) or 0
        rel = db.get("release_intensity", 0) or 0
        if db.get("release_ch") and rel and rel < inten:
            issues.append(("warning", f"情绪债 {db.get('debt_id')} 释放强度 {rel} < 憋屈强度 {inten}（打脸不够解气）"))

    # 6.5 未决连续性冲突（state_apply 挂在 cursor.pending_conflicts，等人三选项裁决）
    for pc in (cursor.get("pending_conflicts") or []):
        if pc.get("status", "open") == "open":
            issues.append(("error", f"未决连续性冲突（需人三选项裁决 改新/降级旧/变剧情）@ch{pc.get('chapter')}："
                                    f"{pc.get('description')} 涉及 {pc.get('involves')}"))

    # 7 glossary
    alias_map = {}
    for g in (world.get("glossary") or []):
        cn = g.get("canon_name")
        if not cn and (g.get("term") or g.get("aliases")):
            issues.append(("warning", f"glossary 条目 {g.get('term')!r} 缺 canon_name"))
        for a in (g.get("aliases") or []):
            if a in alias_map and alias_map[a] != cn:
                issues.append(("error", f"glossary 别名冲突：{a!r} 同时指向 {alias_map[a]!r} 和 {cn!r}"))
            alias_map[a] = cn

    return current_chapter, issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", help="book state 目录")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--current-chapter", type=int, default=None)
    args = ap.parse_args()

    cur, issues = check(args.dir, args.current_chapter)
    errors = [m for lvl, m in issues if lvl == "error"]
    warns = [m for lvl, m in issues if lvl == "warning"]

    if args.json:
        print(json.dumps({"current_chapter": cur, "errors": errors, "warnings": warns,
                          "ok": len(errors) == 0}, ensure_ascii=False, indent=2))
    else:
        print(f"状态体检 @ 第 {cur} 章： {len(errors)} error / {len(warns)} warning")
        for m in errors:
            print(f"  ❌ {m}")
        for m in warns:
            print(f"  ⚠️  {m}")
        if not issues:
            print("  ✅ 机械不变式全部通过（语义级一致性仍需 LLM continuity-checker）")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
