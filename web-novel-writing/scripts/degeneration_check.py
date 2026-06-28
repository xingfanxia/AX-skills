#!/usr/bin/env python3
"""
degeneration_check.py —— 模型退化 + 工程词泄漏检测（正文【输出侧】，零 LLM）

借鉴 oh-story-claudecode/story-deslop 的 check-degeneration.js（MIT，
github.com/worldwonderer/oh-story-claudecode），移植为 Python 并适配本 skill 的工程词表。

它抓的是「**退化的模型自己报不出来**」的指纹——和 antislop_lint（AI 味·密度）、
output_check（字数/泄漏/POV/剧透硬门）互补，专治长篇续写到后段模型打转/截断/漏元信息：
  1. 复读/打转：长句(可见≥12字)全文重复≥3次，或紧邻整行重复(可见≥8字) —— blocking
  2. 截断：正文末尾未以句末/收尾标点结束（疑似被模型中途切断） —— blocking
  3. 占位符/拒绝语：作为AI / 我无法继续 / 此处省略 / 乱码� / 英文 AI 腔 —— blocking
  4. 工程词泄漏：tier1 纯流水线术语(细纲/卷纲/章纲/情节点/爽点/毒点/金手指…)漏进正文 —— blocking
                tier2 章节结构/歧义词(第X章/本章/伏笔/读者…) —— advisory（角色故事内真讨论时合法）

保守设计：通俗网文故意用排比/复沓/弹幕刷屏/重复台词做节奏——所以**对话/引号内一律豁免**，
只数引号外叙述句，短句也豁免。blocking 是退化信号，**去 AI 味改不掉，应回去重新生成那一段**。

用法：
  python3 degeneration_check.py 正文.txt
  python3 degeneration_check.py --json --fail-on=blocking 正文.txt
退出码：0 = 无（--fail-on=blocking 时无 blocking）；1 = 命中；2 = IO/用法。
"""
import sys
import re
import json
import argparse

REPEAT_MIN_LEN = 12
REPEAT_MIN_COUNT = 3
ADJACENT_MIN_LEN = 8

# tier1：纯写作流水线术语，正文里几乎永不合法 → blocking
META_TIER1 = re.compile(r"细纲|卷纲|章纲|情节点|功能标签|目标情绪|字数目标|章首钩子|章尾钩子|"
                        r"爽点|毒点|金手指|伏笔池|must_happen|must_not_happen|sao_payoff|ending_hook|"
                        r"context_pack|chapter_contract|本章任务|读者爽点")
# tier2：章节结构/歧义词，角色在故事内真讨论创作/系统界面用语时可能合法 → advisory
META_TIER2 = re.compile(r"第[一二三四五六七八九十百千万两0-9]+章|本章|这一章|上一章|下一章|上章|下章|"
                        r"前文|后文|伏笔|读者|任务描述|大纲")

# 占位符/拒绝语：hard=任何行都判；soft=只在非对话叙述行判（AI 角色台词可能合法）
PLACEHOLDER = [
    (re.compile(r"作为(一个)?(AI|人工智能|大?语言模型|智能助手|聊天助手)(?=[，,。、；;：:！!？?\s）)」』\"】]|我|无法|不能|没法|$)"), "元信息泄漏(AI自指)", False),
    (re.compile(r"�"), "乱码(替换字符)", True),
    (re.compile(r"^(Sure|Certainly|Here'?s|As an AI|I (?:cannot|can't|am unable|apologize))"), "英文AI腔", True),
    (re.compile(r"[（(](此处|以下|这里|下文|后续)?\s*(省略|略)(去|过)?[^）)]{0,10}[）)]"), "占位符(括号省略)", True),
    (re.compile(r"(未完待续|TODO|占位符|placeholder)"), "占位符", True),
    (re.compile(r"我(无法|不能)(继续(写|创作|生成|下去)|生成(内容|文本|正文)?|创作|续写|完成(这个|本)?(章|篇|创作|请求))"), "生成拒绝语", False),
]

QUOTED = re.compile(r"「[^」]*」|『[^』]*』|【[^】]*】|“[^”]*”|‘[^’]*’|\"[^\"]*\"|'[^']*'")
DIALOGUE_MARK = re.compile(r"[“”\"'‘’「」『』【】]")
TERMINAL = re.compile(r"[。！？!?…”\"』」）)】]$")


def visible_len(s):
    return len(re.findall(r"[一-鿿Ａ-ｚA-Za-z0-9]", s))


def strip_quoted(s):
    return QUOTED.sub("", s)


def content_lines(text):
    """跳过 YAML front-matter 和 ``` 代码块，返回 [(lineno, trimmed)]，只留正文行。"""
    lines = text.split("\n")
    out = []
    in_fm = bool(lines and lines[0].strip() == "---")
    fence = None
    for i, raw in enumerate(lines):
        t = raw.strip()
        if in_fm:
            if i > 0 and t == "---":
                in_fm = False
            continue
        fm = re.match(r"^(`{3,}|~{3,})", t)
        if fence:
            if fm and t[0] == fence:
                fence = None
            continue
        if fm:
            fence = t[0]
            continue
        if t and not t.startswith("#") and not re.match(r"^-{3,}$", t):
            out.append((i + 1, t))
    return out


def check(text):
    body = content_lines(text)
    findings = []

    # 0 字节地板：正文过短疑似 Write 静默失败 / quota 中断 / 生成被掐断（退化的模型报不出来）
    if len(text.encode("utf-8")) < 200:
        findings.append((1, "blocking", "byte-floor",
                         f"正文仅 {len(text.encode('utf-8'))} 字节（<200）：疑似 Write 静默失败/生成被中断，回去重新生成整章"))

    # 1 复读：紧邻整行重复
    for i in range(1, len(body)):
        if body[i][1] == body[i - 1][1] and visible_len(strip_quoted(body[i][1])) >= ADJACENT_MIN_LEN:
            findings.append((body[i][0], "blocking", "verbatim-repeat",
                             f"逐行复读（紧邻整行重复）：疑似模型打转，重写删重复 — {body[i][1][:40]}"))
    # 1 复读：长句全文重复 ≥3 次（只数引号外叙述）
    counts = {}
    for _, t in body:
        for s in re.split(r"[。！？!?]", strip_quoted(t)):
            s = s.strip()
            if visible_len(s) >= REPEAT_MIN_LEN:
                counts[s] = counts.get(s, 0) + 1
    flagged = {s for s, c in counts.items() if c >= REPEAT_MIN_COUNT}
    seen = set()
    for ln, t in body:
        for s in re.split(r"[。！？!?]", strip_quoted(t)):
            s = s.strip()
            if s in flagged and s not in seen:
                seen.add(s)
                findings.append((ln, "blocking", "verbatim-repeat",
                                 f"长句复读（同句出现 {counts[s]} 次）：疑似模型打转，保留一处 — {s[:40]}"))

    # 2 截断
    if body and not TERMINAL.search(body[-1][1]):
        findings.append((body[-1][0], "blocking", "truncated",
                         f"疑似截断：正文末尾未以句末/收尾标点结束 — …{body[-1][1][-24:]}"))

    # 3 占位符/拒绝语
    for ln, t in body:
        dialogue = bool(DIALOGUE_MARK.search(t))
        for rx, label, hard in PLACEHOLDER:
            if not hard and dialogue:
                continue
            if rx.search(t):
                findings.append((ln, "blocking", "placeholder-leak",
                                 f"{label}：正文混入元信息/拒绝语/占位符，重写本段 — {t[:30]}"))
                break

    # 4 工程词泄漏
    first = True
    for ln, t in body:
        if first:
            first = False
            if re.match(r"^第[一二三四五六七八九十百千万两0-9]+章", t):
                continue  # 标题行豁免
        dialogue = bool(DIALOGUE_MARK.search(t))
        m1 = META_TIER1.search(t)
        if m1:
            findings.append((ln, "advisory" if dialogue else "blocking", "meta-leak",
                             f"工程词泄漏「{m1.group(0)}」是流水线术语，正文不该出现"
                             + ("（对话行：角色若为作者/编剧在故事内讨论创作可能合法）" if dialogue else "")))
            continue
        m2 = META_TIER2.search(t)
        if m2:
            findings.append((ln, "advisory", "meta-leak",
                             f"元信息泄漏「{m2.group(0)}」疑似章节结构词混入正文（例外：角色故事内真实阅读/讨论）"))

    findings.sort(key=lambda f: f[0])
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="正文文件，或 - 表示 stdin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", choices=["blocking", "all"], default="all")
    args = ap.parse_args()

    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    findings = check(text)
    has_blocking = any(f[1] == "blocking" for f in findings)

    if args.json:
        print(json.dumps({"findings": [{"line": ln, "severity": sev, "type": ty, "message": msg}
                                       for ln, sev, ty, msg in findings],
                          "has_blocking": has_blocking}, ensure_ascii=False, indent=2))
    else:
        if not findings:
            print("✅ 无模型退化/工程词泄漏指纹")
        else:
            print(f"模型退化检测：{sum(1 for f in findings if f[1]=='blocking')} blocking / "
                  f"{sum(1 for f in findings if f[1]=='advisory')} advisory")
            for ln, sev, ty, msg in findings:
                print(f"  {'❌' if sev=='blocking' else '⚠️ '} L{ln} [{ty}] {msg}")
            if has_blocking:
                print("  → blocking 是退化信号，去 AI 味改不掉：回去重新生成那一段，再 deslop。")

    fail = has_blocking if args.fail_on == "blocking" else bool(findings)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
