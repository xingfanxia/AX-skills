#!/usr/bin/env python3
"""
state_apply.py —— 定稿后【确定性合并 state delta 进 canon】（关掉 state-mutation 侧伪约束）

借鉴 WebNovelOps apply_state_delta 的合并代数骨架（单写入路径 / 按 id 幂等 append /
结构化 set·add·remove·delta / audit-pass 提交闸 / checkpoint / compact 只快照不删），
但**字段绑定全部重写**以适配本 skill 的 YAML schema（Canon 五态 + 双时态 + 认知四桶 + 伏笔台账）。
抽取 delta 仍是 agent 驱动（state-updater 角色）；本脚本只做【零 LLM 的确定性 merge】。

为什么必须代码化：手动 merge YAML 是长篇里最会漂移的一步（重复/丢钩子/忘 bump 版本/
误删历史）。把它交给代码 = 关掉「靠 agent 自律」这个伪约束缺口。

铁律（全部 code 强制，见 templates/state-delta-template.yaml）：
  - canon_status: Inferred 由代码盖在 world_fact_changes.add 上；Canon 晋升只走人确认。
  - 章级幂等：cursor.applied_chapters 记账；同一 chapter_id 重跑整体 no-op（含数值 delta / 版本号）。
  - 只失效不删：world_fact 用 invalidate(写 valid_until_chapter) 而非 del。
  - 字段白名单：只写 current_state.* / cognition / 伏笔 status / 摘要 / cursor；
    canon_status / behavior_anchors / identity / role / visible_from_volume 一律拒写。
  - 力量阶位单调：level 写入前查 ladder，倒退则拒。
  - 冲突不静默：possible_conflicts 入 cursor.pending_conflicts 并返回给 driver 三选项呈人。
  - 原子写 (tmp+os.replace) + 收尾跑 state_check 不变量，破则非零退出、不算成功。

用法：
  python3 state_apply.py <book_dir> <delta.yaml> --final ch0012.txt --audit-passed
  python3 state_apply.py <book_dir> <delta.yaml> --audit-passed --json
  python3 state_apply.py <book_dir> <delta.yaml> --allow-failed   # 审校没过也强行提交（留痕）
  python3 state_apply.py <book_dir> <delta.yaml> --human-approved  # delta.requires_human 命中时放行
  python3 state_apply.py <book_dir> --self-test                    # 跑内置 golden fixture
退出码：0 = 已结算（或幂等 no-op），1 = 拒绝/校验失败，2 = 用法/IO 错误。
"""
import sys
import os
import json
import argparse
import tempfile
import shutil

try:
    import yaml
except ImportError:
    sys.stderr.write("需要 PyYAML：pip install pyyaml\n")
    sys.exit(2)

FORESHADOW_TYPES = {"身份", "语言", "场景", "数字", "主题", "物件"}
COGNITION_BUCKETS = {"knows", "does_not_know", "misbeliefs", "reader_knows_char_doesnt"}
# 脚本绝不写的人类门字段（写到这些 = 绕过 Canon 治理）
FORBIDDEN_CHAR_FIELDS = {"canon_status", "behavior_anchors", "identity", "role",
                         "visible_from_volume", "name", "flaw_personality", "arc"}
STATE_FILES = ["state-world.yaml", "state-characters.yaml", "state-plotline.yaml",
               "foreshadow-ledger.yaml", "emotion-debt.yaml", "rolling-summary.yaml"]


def load_yaml(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or (default if default is not None else {})


def dump_yaml(obj):
    return yaml.safe_dump(obj, allow_unicode=True, default_flow_style=False, sort_keys=False)


def atomic_write(path, text):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def find_by_id(items, _id, key="id"):
    for it in items:
        if it.get(key) == _id:
            return it
    return None


class ApplyError(Exception):
    pass


def apply_delta(book_dir, delta, final_text=None, human_approved=False):
    """纯确定性 merge。返回 (changed_files: dict[name->obj], result: dict)。不写盘（写盘在 main）。"""
    ch = delta.get("chapter_id")
    if not isinstance(ch, int):
        raise ApplyError(f"delta.chapter_id 必须是整数，得到 {ch!r}")

    world = load_yaml(os.path.join(book_dir, "state-world.yaml"))
    chars = load_yaml(os.path.join(book_dir, "state-characters.yaml"))
    plot = load_yaml(os.path.join(book_dir, "state-plotline.yaml"))
    fore = load_yaml(os.path.join(book_dir, "foreshadow-ledger.yaml"))
    emo = load_yaml(os.path.join(book_dir, "emotion-debt.yaml"))
    roll = load_yaml(os.path.join(book_dir, "rolling-summary.yaml"))

    cursor = plot.setdefault("cursor", {})
    applied = cursor.setdefault("applied_chapters", [])

    # --- 章级幂等闸（必须最先）：已结算的章整体 no-op，保护数值 delta 与版本号 ---
    if ch in applied:
        return None, {"chapter_id": ch, "status": "noop_already_applied",
                      "state_revision": cursor.get("state_revision", 0), "conflicts": []}

    # --- 人类门 ---
    req_human = delta.get("requires_human") or []
    if req_human and not human_approved:
        raise ApplyError(f"delta 触发人类门 {req_human}（contract.human_gate）——需 --human-approved 才能提交")

    notes = []

    # --- 世界事实（双时态，只失效不删，代码盖 Inferred）---
    wf = world.setdefault("world_facts", [])
    wf_ids = {x.get("id") for x in wf}
    for add in (delta.get("world_fact_changes") or {}).get("add", []) or []:
        wid = add.get("id")
        if not wid:
            raise ApplyError("world_fact_changes.add 条目缺 id")
        if wid in wf_ids:
            notes.append(f"world_fact {wid} 已存在，跳过 add（幂等）")
            continue
        if "visible_from_volume" not in add:
            raise ApplyError(f"world_fact {wid} 缺 visible_from_volume（防剧透必填）")
        wf.append({"id": wid, "fact": add.get("fact", ""),
                   "canon_status": "Inferred",  # 代码盖戳，不信 delta 自报
                   "visible_from_volume": add["visible_from_volume"],
                   "affects": add.get("affects", ""),
                   "valid_from_chapter": ch, "valid_until_chapter": None})
        wf_ids.add(wid)
    for inv in (delta.get("world_fact_changes") or {}).get("invalidate", []) or []:
        tgt = find_by_id(wf, inv.get("id"))
        if tgt is None:
            notes.append(f"invalidate 找不到 world_fact {inv.get('id')}，跳过")
            continue
        if tgt.get("valid_until_chapter") is None:
            tgt["valid_until_chapter"] = ch  # 只失效不删

    # --- 人物快变（字段白名单 + 阶位单调 + 资源 items/balances + 关系 upsert）---
    char_list = chars.setdefault("characters", [])
    ladder = ((world.get("power_system") or {}).get("ladder")) or []
    for cc in delta.get("character_changes", []) or []:
        cid = cc.get("id")
        c = find_by_id(char_list, cid)
        if c is None:
            raise ApplyError(f"character_changes 引用了 bible 里不存在的角色 {cid!r}（=连续性 bug，拒绝自动造卡）")
        cs = c.setdefault("current_state", {})
        for k, v in (cc.get("current_state") or {}).items():
            if k in FORBIDDEN_CHAR_FIELDS:
                raise ApplyError(f"拒写人类门字段 current_state.{k}（晋升 Canon/改人设需人确认）")
            if k == "level" and ladder and v:
                old = cs.get("level")
                if old in ladder and v in ladder and ladder.index(v) < ladder.index(old):
                    raise ApplyError(f"{cid} 境界倒退 {old}→{v}（power_system 单调，拒）")
                if v not in ladder:
                    notes.append(f"{cid} 新境界 {v!r} 不在 ladder（可能错字）")
            cs[k] = v
        # 资源：items[] + balances{}（兼容老的扁平 list）
        res = cs.get("resources")
        if not isinstance(res, dict):
            res = {"items": list(res) if isinstance(res, list) else [], "balances": {}}
            cs["resources"] = res
        res.setdefault("items", [])
        res.setdefault("balances", {})
        for it in cc.get("resources_items_add", []) or []:
            if it not in res["items"]:
                res["items"].append(it)
        for it in cc.get("resources_items_remove", []) or []:
            res["items"] = [x for x in res["items"] if x != it]
        for k, dv in (cc.get("resources_balances") or {}).items():
            res["balances"][k] = res["balances"].get(k, 0) + dv  # delta 累加（章级幂等保护）
        # 关系 upsert by with
        rels = cs.setdefault("relations", [])
        for r in cc.get("relations", []) or []:
            ex = find_by_id(rels, r.get("with"), key="with")
            if ex:
                ex.update(r)
            else:
                rels.append(r)

    # --- 认知四桶 ---
    for cg in delta.get("cognition_changes", []) or []:
        c = find_by_id(char_list, cg.get("id"))
        if c is None:
            raise ApplyError(f"cognition_changes 引用不存在的角色 {cg.get('id')!r}")
        bucket = cg.get("bucket")
        if bucket not in COGNITION_BUCKETS:
            raise ApplyError(f"非法 cognition bucket {bucket!r}，应为 {sorted(COGNITION_BUCKETS)}")
        cog = c.setdefault("cognition", {})
        lst = cog.setdefault(bucket, [])
        for v in cg.get("add", []) or []:
            if v not in lst:
                lst.append(v)
        for v in cg.get("remove", []) or []:
            cog[bucket] = [x for x in lst if x != v]
            lst = cog[bucket]

    # --- 伏笔台账（只收长程轻埋；缺 planned_payoff_ch 拒收；6 类型白名单）---
    fl = fore.setdefault("foreshadows", [])
    fl_ids = {x.get("id") for x in fl}
    fc = delta.get("foreshadow_changes") or {}
    for op in fc.get("open", []) or []:
        fid = op.get("id")
        if not fid:
            raise ApplyError("foreshadow open 缺 id")
        if fid in fl_ids:
            notes.append(f"伏笔 {fid} 已存在，跳过 open（幂等）")
            continue
        if not op.get("planned_payoff_ch"):
            raise ApplyError(f"伏笔 {fid} 无 planned_payoff_ch（没有回收计划=别埋，拒收）")
        if op.get("type") and op["type"] not in FORESHADOW_TYPES:
            raise ApplyError(f"伏笔 {fid} 类型 {op['type']!r} 不在六类 {sorted(FORESHADOW_TYPES)}")
        fl.append({"id": fid, "type": op.get("type", ""), "text": op.get("text", ""),
                   "planted_ch": op.get("planted_ch", ch),
                   "planned_payoff_ch": op["planned_payoff_ch"],
                   "status": "open",
                   "visible_payoff_volume": op.get("visible_payoff_volume", 0),
                   "note": op.get("note", "")})
        fl_ids.add(fid)
    for ad in fc.get("advance", []) or []:
        tgt = find_by_id(fl, ad.get("id"))
        if tgt and tgt.get("status") == "open":
            tgt["status"] = "微回应"  # 翻转状态，不只 append
            if ad.get("note"):
                tgt["note"] = (str(tgt.get("note", "")) + f" / ch{ch}:{ad['note']}").strip(" /")
    for cl in fc.get("close", []) or []:
        tgt = find_by_id(fl, cl.get("id"))
        if tgt and tgt.get("status") != "closed":
            tgt["status"] = "closed"
            if cl.get("note"):
                tgt["note"] = (str(tgt.get("note", "")) + f" / ch{ch}回收:{cl['note']}").strip(" /")

    # --- 情绪债 + 爽点排布 ---
    ec = delta.get("emotion_changes") or {}
    debts = emo.setdefault("emotion_debts", [])
    debt_ids = {x.get("debt_id") for x in debts}
    for inc in ec.get("incur", []) or []:
        did = inc.get("debt_id")
        if did and did not in debt_ids:
            debts.append({"debt_id": did, "text": inc.get("text", ""),
                          "intensity": inc.get("intensity", 0), "incurred_ch": inc.get("incurred_ch", ch),
                          "duration_chapters": 0, "release_ch": inc.get("release_ch", 0),
                          "release_intensity": 0, "released": False})
            debt_ids.add(did)
    for rel in ec.get("release", []) or []:
        tgt = find_by_id(debts, rel.get("debt_id"), key="debt_id")
        if tgt and not tgt.get("released"):
            tgt["released"] = True
            tgt["release_intensity"] = rel.get("release_intensity", 0)
            tgt["release_ch"] = rel.get("release_ch", ch)
    sao = emo.setdefault("sao_schedule", [])
    sao_keys = {(s.get("chapter"), s.get("type")) for s in sao}
    for s in delta.get("sao_logged", []) or []:
        if (s.get("chapter"), s.get("type")) not in sao_keys:
            sao.append({"chapter": s.get("chapter", ch), "type": s.get("type", ""),
                        "level": s.get("level", ""), "setup_chain": s.get("setup_chain", "")})

    # --- 滚动摘要（per_chapter by ch；previous_tail 取 final 尾段原文，不用 summary）---
    pc = roll.setdefault("per_chapter", [])
    if not find_by_id(pc, ch, key="ch"):
        pc.append({"ch": ch, "one_line": delta.get("chapter_summary", ""),
                   "sao": delta.get("sao_realized", ""), "hook": delta.get("hook_for_next", "")})
    if final_text:
        tail = "\n".join([ln for ln in final_text.strip().splitlines() if ln.strip()][-2:])
        roll["previous_tail"] = tail

    # --- 疑似冲突：不静默入库，进 pending_conflicts 队列 + 返回 ---
    conflicts = []
    pend = cursor.setdefault("pending_conflicts", [])
    for cf in delta.get("possible_conflicts", []) or []:
        desc = cf.get("description", "")
        if desc and not any(p.get("description") == desc for p in pend):
            entry = {"chapter": ch, "description": desc, "involves": cf.get("involves", []), "status": "open"}
            pend.append(entry)
            conflicts.append(entry)

    # --- cursor: 版本号 + 推进指针 + 记账（最后，确保前面没抛异常）---
    cursor["state_revision"] = int(cursor.get("state_revision", 0)) + 1
    cursor["last_chapter_done"] = max(int(cursor.get("last_chapter_done", 0) or 0), ch)
    applied.append(ch)

    changed = {"state-world.yaml": world, "state-characters.yaml": chars,
               "state-plotline.yaml": plot, "foreshadow-ledger.yaml": fore,
               "emotion-debt.yaml": emo, "rolling-summary.yaml": roll}
    result = {"chapter_id": ch, "status": "applied", "state_revision": cursor["state_revision"],
              "conflicts": conflicts, "notes": notes}
    return changed, result


def write_checkpoint(book_dir, ch, interval):
    if not interval or interval <= 0 or ch % interval != 0:
        return False
    cp = os.path.join(book_dir, "checkpoints", f"after_ch{ch:04d}")
    os.makedirs(cp, exist_ok=True)
    for name in STATE_FILES + ["contract.yaml"]:
        src = os.path.join(book_dir, name)
        if os.path.exists(src):  # glob/存在性，不硬编码（缺文件跳过不抛）
            shutil.copy2(src, os.path.join(cp, name))
    return True


def post_validate(book_dir, ch):
    """收尾跑 state_check 不变量，破则报错（F8 fail-loud）。"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from state_check import check as state_check
        _, issues = state_check(book_dir, ch)
        # 把"未决连续性冲突"剔出去——那是本脚本主动 queue 的【软信号·待人三选项】，
        # 不是代码破了硬不变量。它走独立 status(applied_with_pending_review)，不算 invariants_broken。
        return [m for lvl, m in issues if lvl == "error" and not m.startswith("未决连续性冲突")]
    except Exception as e:  # noqa: BLE001 — 校验器本身出错也要可见
        return [f"state_check 运行失败: {e}"]


def run(book_dir, delta_path, final_path, audit_passed, allow_failed, human_approved, as_json):
    if not audit_passed and not allow_failed:
        msg = "审校未过（无 --audit-passed），拒绝提交 canon。坏章不污染 canon；要强行提交加 --allow-failed。"
        _emit({"status": "refused", "reason": msg}, as_json)
        return 1
    delta = load_yaml(delta_path)
    final_text = None
    if final_path and os.path.exists(final_path):
        with open(final_path, encoding="utf-8") as f:
            final_text = f.read()

    try:
        changed, result = apply_delta(book_dir, delta, final_text, human_approved)
    except ApplyError as e:
        _emit({"status": "refused", "reason": str(e)}, as_json)
        return 1

    if changed is None:  # 幂等 no-op：重跑也要把仍 open 的未决冲突回读出来，别静默吞掉
        cursor = (load_yaml(os.path.join(book_dir, "state-plotline.yaml")).get("cursor") or {})
        result["conflicts"] = [c for c in (cursor.get("pending_conflicts") or []) if c.get("status", "open") == "open"]
        _emit(result, as_json)
        return 0

    # 原子写所有变更文件
    for name, obj in changed.items():
        atomic_write(os.path.join(book_dir, name), dump_yaml(obj))

    # checkpoint
    contract = load_yaml(os.path.join(book_dir, "contract.yaml"))
    interval = int((contract.get("config") or {}).get("checkpoint_interval", 5) or 5)
    result["checkpoint_written"] = write_checkpoint(book_dir, result["chapter_id"], interval)

    # 收尾自校验（F8）
    errors = post_validate(book_dir, result["chapter_id"])
    result["post_check_errors"] = errors

    # run_manifest（事务边界落到代码，不留散文空头保证）
    ch_dir = os.path.join(book_dir, "chapters", f"ch{result['chapter_id']:04d}")
    os.makedirs(ch_dir, exist_ok=True)
    atomic_write(os.path.join(ch_dir, "run_manifest.json"),
                 json.dumps({"chapter_id": result["chapter_id"], "audit_passed": audit_passed,
                             "state_revision": result["state_revision"],
                             "checkpoint_written": result["checkpoint_written"],
                             "conflicts": result["conflicts"], "post_check_errors": errors},
                            ensure_ascii=False, indent=2))

    if errors:
        result["status"] = "applied_but_invariants_broken"
        _emit(result, as_json)
        return 1  # 真·破硬不变量 = 非零退出，不算干净成功
    if result.get("conflicts"):
        # 已干净合并、但本章 queue 了待人裁决的疑似冲突——独立 status，exit 0（不是失败）
        result["status"] = "applied_with_pending_review"
        _emit(result, as_json)
        return 0
    _emit(result, as_json)
    return 0


def _emit(obj, as_json):
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
        return
    st = obj.get("status")
    if st == "refused":
        print(f"❌ 拒绝提交：{obj.get('reason')}")
    elif st == "noop_already_applied":
        print(f"↩️  第 {obj['chapter_id']} 章已结算过（章级幂等 no-op），state_revision={obj['state_revision']}")
    else:
        icon = "✅" if st == "applied" else "⚠️"
        print(f"{icon} 第 {obj['chapter_id']} 章 delta 已合并 · state_revision={obj['state_revision']} · "
              f"checkpoint={'是' if obj.get('checkpoint_written') else '否'}")
        for n in obj.get("notes", []):
            print(f"   · {n}")
        for cf in obj.get("conflicts", []):
            print(f"   ⚠️ 疑似冲突（需人三选项裁决）：{cf['description']} 涉及 {cf.get('involves')}")
        for e in obj.get("post_check_errors", []):
            print(f"   ❌ 收尾校验失败：{e}")


def self_test():
    """golden fixture：用本 skill schema 手写 2 章 delta，断言后态 + 幂等 + 拒绝闸。"""
    import tempfile as _tf
    here = os.path.dirname(os.path.abspath(__file__))
    tpl = os.path.join(here, "..", "templates")
    book = _tf.mkdtemp(prefix="wnw_selftest_")
    # 最小可用书目录
    atomic_write(os.path.join(book, "contract.yaml"),
                 dump_yaml({"config": {"checkpoint_interval": 5},
                            "human_gate": {"requires_approval_for": ["character_death"]}}))
    atomic_write(os.path.join(book, "state-world.yaml"),
                 dump_yaml({"world_facts": [{"id": "W001", "fact": "青铜铃是法器", "canon_status": "Canon",
                                             "visible_from_volume": 1, "valid_from_chapter": 1,
                                             "valid_until_chapter": None}],
                            "power_system": {"ladder": ["练气", "筑基", "金丹"]}}))
    atomic_write(os.path.join(book, "state-characters.yaml"),
                 dump_yaml({"characters": [{"id": "CHR_001", "name": "林照", "role": "主角",
                                            "canon_status": "Canon", "visible_from_volume": 1,
                                            "current_state": {"level": "练气", "resources": {"items": [], "balances": {"灵石": 100}}},
                                            "cognition": {"knows": [], "does_not_know": [], "misbeliefs": [], "reader_knows_char_doesnt": []}}]}))
    atomic_write(os.path.join(book, "state-plotline.yaml"), dump_yaml({"cursor": {"last_chapter_done": 0}}))
    atomic_write(os.path.join(book, "foreshadow-ledger.yaml"), dump_yaml({"foreshadows": []}))
    atomic_write(os.path.join(book, "emotion-debt.yaml"), dump_yaml({"emotion_debts": [], "sao_schedule": []}))
    atomic_write(os.path.join(book, "rolling-summary.yaml"), dump_yaml({"per_chapter": []}))

    d1 = {"chapter_id": 1, "chapter_summary": "林照得青铜铃", "hook_for_next": "铃发烫",
          "world_fact_changes": {"add": [{"id": "W002", "fact": "铃会发烫", "visible_from_volume": 1, "affects": "林照"}]},
          "character_changes": [{"id": "CHR_001", "current_state": {"level": "筑基"},
                                 "resources_balances": {"灵石": -30}}],
          "cognition_changes": [{"id": "CHR_001", "bucket": "knows", "add": ["铃会发烫"]}],
          "foreshadow_changes": {"open": [{"id": "F001", "type": "物件", "text": "铃来历", "planned_payoff_ch": 5}]}}
    failures = []
    _, r1 = apply_delta(book, d1)
    for name, obj in _.items():
        atomic_write(os.path.join(book, name), dump_yaml(obj))
    w = load_yaml(os.path.join(book, "state-world.yaml"))
    c = load_yaml(os.path.join(book, "state-characters.yaml"))
    newfact = find_by_id(w["world_facts"], "W002")
    if not newfact or newfact["canon_status"] != "Inferred":
        failures.append("W002 未盖 canon_status=Inferred")
    if c["characters"][0]["current_state"]["level"] != "筑基":
        failures.append("level 未更新")
    if c["characters"][0]["current_state"]["resources"]["balances"]["灵石"] != 70:
        failures.append(f"灵石 delta 错: {c['characters'][0]['current_state']['resources']['balances']['灵石']} != 70")
    if r1["state_revision"] != 1:
        failures.append("state_revision != 1")

    # 幂等：重跑同章 → no-op，灵石不再扣
    none_changed, r1b = apply_delta(book, d1)
    if none_changed is not None or r1b["status"] != "noop_already_applied":
        failures.append("章级幂等失效（重跑应 no-op）")

    # 拒绝闸：境界倒退
    try:
        apply_delta(book, {"chapter_id": 2, "character_changes": [{"id": "CHR_001", "current_state": {"level": "练气"}}]})
        failures.append("境界倒退未被拒")
    except ApplyError:
        pass
    # 拒绝闸：无 planned_payoff_ch 的伏笔
    try:
        apply_delta(book, {"chapter_id": 2, "foreshadow_changes": {"open": [{"id": "F002", "text": "无计划"}]}})
        failures.append("无回收计划伏笔未被拒")
    except ApplyError:
        pass
    # 拒绝闸：人类门
    try:
        apply_delta(book, {"chapter_id": 2, "requires_human": ["character_death"]})
        failures.append("人类门未拦截")
    except ApplyError:
        pass

    shutil.rmtree(book, ignore_errors=True)
    if failures:
        print("❌ self-test 失败：")
        for f in failures:
            print(f"   - {f}")
        return 1
    print("✅ state_apply self-test 全过（Inferred 盖戳 / 数值 delta / 章级幂等 / 阶位单调 / 伏笔计划闸 / 人类门）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("book_dir", nargs="?")
    ap.add_argument("delta", nargs="?", help="state delta yaml/json 路径")
    ap.add_argument("--final", help="本章定稿正文路径（取尾段做 previous_tail）")
    ap.add_argument("--audit-passed", action="store_true")
    ap.add_argument("--allow-failed", action="store_true")
    ap.add_argument("--human-approved", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())
    if not args.book_dir or not args.delta:
        ap.error("需要 <book_dir> <delta> 两个参数（或用 --self-test）")
    sys.exit(run(args.book_dir, args.delta, args.final, args.audit_passed,
                 args.allow_failed, args.human_approved, args.json))


if __name__ == "__main__":
    main()
