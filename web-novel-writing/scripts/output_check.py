#!/usr/bin/env python3
"""
output_check.py —— 章节正文【输出侧】机械门（让"纯 code 硬门"声明落地）

state_check.py 校验【状态文件】的不变量；antislop_lint.py 算【词句层 AI 味】扣分；
本脚本补上对【章节正文本身】的那几个"纯 code、零 LLM"硬门——它们本就该由代码强制、
绝不该写进 prompt 当成已执行（伪约束=头号反模式）。对应 04-review-rubric.md 的硬门：
`wordcount_pov_format_ok` / `no_prompt_leak` / `no_poison_points`(词面层) + 开篇阈值。

它做的全是确定性正则/计数，不调任何 LLM：
  1. 字数区间（vs 章纲 word_budget 或 contract.config.chapter_length）
  2. 残留指令符号 / 标签 / 元叙述剥离检测（no_prompt_leak）
  3. POV 上帝插嘴启发式（"殊不知/另一边/与此同时，在…"）—— ⚠️启发式，只标记可疑
  4. 毒点【词面】黑名单扫描（默认网文毒词 + contract.forbidden）—— 语义毒点仍归 reviewer
  5. 开篇阈值（仅第1-3章）：冲突/金手指关键词是否在 contract.config.opening_rules 阈值前出现 —— ⚠️启发式

用法：
  python3 output_check.py 某章正文.txt --contract <book_dir>/contract.yaml [--outline ch.json] [--chapter 12]
  python3 output_check.py 正文.txt --contract contract.yaml --json
退出码：0 = 全部硬门通过；1 = 有硬门 false（必须改稿/人工）。
"""
import sys
import re
import json
import argparse

try:
    import yaml
except ImportError:
    yaml = None

# 残留指令符号 / 标签 / 元叙述 / 工程词（正文里绝不该出现）—— meta_terms 借鉴 oh-story
LEAK_PATTERNS = [
    (r"</?(reference|hard_rules|role|chapter_outline|canon_facts|characters_on_stage|"
     r"recent_summary|previous_tail|forbidden_reveals|due_foreshadows|style_anchors|task|task>)", "残留XML标签"),
    (r"\{[a-zA-Z_]+\}", "未替换的占位符"),
    (r"^(正文[:：]|第.{1,4}章[:：]|标题[:：])", "残留前缀/标题"),
    (r"(本章将|本章会|接下来.{0,4}将|根据设定|根据大纲|作为(一个)?AI|作为(一名)?写手|字数已达|以上就是|总结一下)", "元叙述/作者旁白"),
    (r"(VERDICT[:：]|must_happen|must_not_happen|sao_payoff|ending_hook)", "混入的字段名/指令"),
    # 工程词泄漏（degeneration_check 也查；这里抓 prompt 上下文术语漏进正文，硬门）
    (r"(context_pack|chapter_contract|本章任务|读者爽点|细纲|卷纲|功能标签|目标情绪|字数目标)", "混入的工程/上下文术语"),
]
# POV 上帝插嘴 / 解释腔 / 安排感（启发式，借鉴 oh-story Gate G / 模式8——最难察觉最像 AI 的一类）
POV_INTRUSION = ["殊不知", "却不知", "此时此刻，在", "与此同时，在", "另一边，", "镜头一转",
                 "山的另一边", "而在", "让我们把目光",
                 "她不知道的是", "他不知道的是", "多年以后", "冥冥之中", "仿佛预示着",
                 "之所以", "这意味着", "原来", "正是因为"]
# 默认网文毒点【词面】黑名单（语义毒点交 reviewer；这里只抓明显词面）
DEFAULT_POISON = ["绿帽", "戴绿帽", "送女", "送出去", "共享", "牛头人"]
# 网文正文标点纪律（借鉴 oh-story：正文产物禁用破折号/省略号停顿——平台一眼鉴 AI）
EM_DASH = re.compile(r"——|—|--+")
ELLIPSIS = re.compile(r"……|⋯⋯")


def load_yaml(p):
    if not p or not yaml:
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def load_whitelist(p):
    if not p or not os.path.exists(p):
        return set()
    out = set()
    with open(p, encoding="utf-8") as f:
        for line in f:
            t = line.strip()
            if t and not t.startswith("#"):
                out.add(t)
    return out


def _wl(word, whitelist):
    """命中词是否被白名单豁免（本身在白名单，或是某白名单词的真子串）。"""
    return word in whitelist or any(word in wl and word != wl for wl in whitelist)


def _spoiler_phrases(contract, outline):
    """从 contract.locked_reveals + outline.forbidden_reveals 抽【可词面扫描】的剧透短语。
    只取含中文且 >=4 字的（id 如 F003 不可扫描，跳过）。"""
    phrases = []
    for lr in (contract.get("locked_reveals") or []):
        v = lr if isinstance(lr, str) else (lr.get("reveal") or lr.get("text") or lr.get("desc") or "")
        if v and len(v) >= 4 and re.search(r"[一-龥]", v):
            phrases.append(v)
    for fr in ((outline or {}).get("forbidden_reveals") or []):
        if isinstance(fr, str) and len(fr) >= 4 and re.search(r"[一-龥]", fr):
            phrases.append(fr)
    return list(dict.fromkeys(phrases))  # 去重保序


def _mh_items(outline, key):
    """must_happen/must_not_happen 兼容新对象 [{text,keywords}] 与老字符串 []。返回 [(text, kws)]。"""
    out = []
    for it in (outline or {}).get(key, []) or []:
        if isinstance(it, dict):
            out.append((it.get("text", ""), it.get(
                "keywords" if key == "must_happen" else "forbidden_keywords", []) or []))
        else:
            out.append((str(it), []))
    return out


def check(text, contract, outline, chapter, whitelist=frozenset()):
    issues = []        # 硬门违规
    advisories = []    # 启发式/必要非充分，只报告不 fail
    tail = text[-300:]

    # 1. 字数
    cfg = (contract.get("config") or {})
    wb = (outline or {}).get("word_budget") or cfg.get("chapter_length") or {}
    wmin, wmax = wb.get("min", 2000), wb.get("max", 3200)
    n = len(re.sub(r"\s", "", text))
    wordcount_ok = wmin <= n <= wmax
    if not wordcount_ok:
        issues.append(("wordcount_pov_format_ok", f"字数 {n} 不在区间 [{wmin},{wmax}]"))

    # 2. 残留指令符号 / 元叙述 / 工程词
    leak = []
    for rx, label in LEAK_PATTERNS:
        for m in re.finditer(rx, text, re.MULTILINE):
            leak.append(f"{label}: {m.group(0)[:24]!r}")
    no_prompt_leak = not leak
    for l in leak[:8]:
        issues.append(("no_prompt_leak", l))

    # 3. POV 上帝插嘴 / 解释腔（启发式 → advisory，不 hard-fail，送 reviewer）
    pov_hits = [w for w in POV_INTRUSION if w in text and not _wl(w, whitelist)]
    if pov_hits:
        advisories.append(("pov_godview_hint", f"⚠️疑似上帝插嘴/解释腔/安排感(启发式,送 reviewer 判): {pov_hits}"))

    # 4. 毒点词面
    poison_lex = list(DEFAULT_POISON)
    for w in (contract.get("contract") or {}).get("forbidden", []) or []:
        for tok in re.findall(r"[一-龥]{2,4}", str(w)):
            if tok in ("绿帽", "送女", "种马", "圣母", "降智"):
                poison_lex.append(tok)
    poison_hits = sorted({w for w in poison_lex if w in text and not _wl(w, whitelist)})
    no_poison_surface = not poison_hits
    if poison_hits:
        issues.append(("no_poison_points", f"毒点词面命中(语义仍需reviewer判): {poison_hits}"))

    # 5. 标点纪律（网文正文禁用破折号；省略号停顿降级 advisory）
    em = EM_DASH.findall(text)
    no_em_dash = not em
    if em:
        issues.append(("punctuation_discipline", f"正文含破折号 ——/—/-- ×{len(em)}（网文正文禁用，平台一眼鉴 AI；改句号/逗号/动作断句）"))
    if ELLIPSIS.findall(text):
        advisories.append(("punctuation_hint", f"正文含省略号停顿 …… ×{len(ELLIPSIS.findall(text))}（建议改动作/短句承接）"))

    # 6. must_not 违规（硬门，blocker）：禁现具名词出现即违规
    mn_hits = []
    for txt, fkws in _mh_items(outline, "must_not_happen"):
        for kw in fkws:
            if kw and kw in text and not _wl(kw, whitelist):
                mn_hits.append(f"{kw}(属禁项「{txt[:18]}」)")
    must_not_absent = not mn_hits
    if mn_hits:
        issues.append(("must_not_absent", f"违反 must_not_happen 禁现词: {mn_hits}"))

    # 7. must_happen 关键词全 present（必要非充分 → advisory；缺 keywords 出 WARN）
    for txt, kws in _mh_items(outline, "must_happen"):
        if not kws:
            advisories.append(("must_happen_no_keywords", f"⚠️ must_happen「{txt[:18]}」未配 keywords（伪约束-by-omission，无法机检是否漏写）"))
            continue
        missing = [k for k in kws if k and k not in text]
        if missing:
            advisories.append(("must_happen_present", f"⚠️ must_happen「{txt[:18]}」关键词缺失 {missing}（必要非充分：疑似漏写，写没写对仍归 reviewer）"))

    # 8. 章末钩子落尾段（⚠️启发式 advisory，绝不 blocker，绝不自动切词）
    eh = (outline or {}).get("ending_hook") or {}
    eh_kws = eh.get("keywords") or []
    if eh_kws:
        if not any(k in tail for k in eh_kws if k):
            advisories.append(("ending_hook_in_tail", f"⚠️ 章末 300 字未见钩子关键词 {eh_kws}（启发式，钩子是否落位归 reviewer）"))

    # 9. 剧透-出（硬门，blocker）：正文泄漏 locked_reveals/forbidden_reveals 的词面
    spoiler_hits = [p for p in _spoiler_phrases(contract, outline) if p in text and not _wl(p, whitelist)]
    no_future_spoiler_out = not spoiler_hits
    if spoiler_hits:
        issues.append(("no_future_spoiler_out", f"正文泄漏未到揭晓时机的剧透词面: {[s[:20] for s in spoiler_hits]}（剧透-出闸；与 compile 的剧透-入过滤构成双闸）"))

    # 10. 开篇阈值（仅第 1-3 章，启发式 → advisory）
    if chapter and chapter <= 3:
        rules = cfg.get("opening_rules") or {}
        thr = rules.get("conflict_before_chars")
        if thr and not re.search(r"(冲突|危机|杀|逼|抢|追|败|辱|死|血|敌|战|逃|夺|押|跪|怒)", text[:thr]):
            advisories.append(("opening", f"⚠️前 {thr} 字未见明显冲突信号(启发式，第{chapter}章)"))

    gates = {
        "wordcount_pov_format_ok": wordcount_ok,
        "no_prompt_leak": no_prompt_leak,
        "no_poison_points": no_poison_surface,
        "punctuation_discipline": no_em_dash,
        "must_not_absent": must_not_absent,
        "no_future_spoiler_out": no_future_spoiler_out,
    }
    return gates, advisories, issues, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="章节正文文件，或 - 表示 stdin")
    ap.add_argument("--contract", help="contract.yaml 路径")
    ap.add_argument("--outline", help="chapter-outline.json 路径")
    ap.add_argument("--chapter", type=int, default=None)
    ap.add_argument("--whitelist", help=".deslop-whitelist 路径（豁免世界观术语/绰号/专名）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    contract = load_yaml(args.contract)
    outline = json.load(open(args.outline, encoding="utf-8")) if args.outline else {}
    chapter = args.chapter or (outline.get("chapter_id") if outline else None)
    whitelist = load_whitelist(args.whitelist)

    gates, advisories, issues, n = check(text, contract, outline, chapter, whitelist)
    ok = all(gates.values())

    if args.json:
        print(json.dumps({"chars": n, "hard_gates": gates, "ok": ok,
                          "issues": [{"gate": g, "msg": m} for g, m in issues],
                          "advisories": [{"gate": g, "msg": m} for g, m in advisories]},
                         ensure_ascii=False, indent=2))
    else:
        print(f"输出侧机械门 @ {n} 字： {'✅ 硬门全过' if ok else '❌ 有硬门未过'}")
        for g, v in gates.items():
            print(f"  {'✅' if v else '❌'} {g}")
        for g, m in issues:
            print(f"    - [{g}] {m}")
        if advisories:
            print("  ── 启发式/必要非充分（不 fail，送 reviewer）──")
            for g, m in advisories:
                print(f"    · [{g}] {m}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
