#!/usr/bin/env python3
"""
antislop_lint.py —— 网文反 AI 味·词句层(桶1)确定性探测器

只做"桶1·词句层"的机械检测——网文编辑鉴 AI 的第一道关，纯确定性、最该 code 化。
不判"桶2 结构层(show-don't-tell 分层)"和"桶3 网文专属轴(爽点/钩子/毒点)"——那些需要语义，
由 reviewer(独立 LLM + rubric) 处理。本脚本只抓"固定频率反复出现的 AI 指纹"，避免误伤气势/铺垫。

判定原则：看【密度】不看【单次出现】。一篇出现一次排比不是 AI 味，每段都排比才是。
例外：`不是A而是B`(最毒★★★★★) 命中即记（不靠密度）——它几乎不会是合理修辞。

词表/句式借鉴 oh-story-claudecode/story-deslop 的 banned-words.md（MIT,
github.com/worldwonderer/oh-story-claudecode）并按本脚本的加权×密度模型重组；
`不是A而是B` 检测移植其 check-ai-patterns.js 的鲁棒分句逻辑（排除 是不是/只是/可是/
但是/还是/于是/就是/也是/不是A也不是B/…是吗）。

白名单：书目录下 `.deslop-whitelist`（一行一词，# 注释）——命中片段若是白名单词的真子串则跳过，
避免误伤世界观术语/角色绰号/专名（这是词表类检测的头号误报源）。

用法：
  python3 antislop_lint.py 某章正文.txt [--whitelist <book>/.deslop-whitelist]
  python3 antislop_lint.py --json 某章正文.txt
  cat 正文.txt | python3 antislop_lint.py -
退出码：0 = 通过(密度低)，1 = AI 味偏重(需 style/anti-slop-editor 处理)。阈值经验值，可 --max-score 调。
"""
import sys
import re
import json
import argparse
import os

# ---- 词表（借鉴 banned-words.md，按桶加权）----
CONNECTORS = ["然而", "与此同时", "随后", "最终", "不难发现", "值得注意的是",
              "综上所述", "总而言之", "换句话说", "不可否认", "某种程度上",
              "首先", "其次", "再者", "于是乎", "从而", "因而", "诚然"]
# 论文体/万能结论（oh-story 模式5）
THESIS = ["不难看出", "由此可见", "事实上", "综上所述", "可谓", "意义深远",
          "前所未有", "未来可期", "前途无量"]
TRANSLATIONESE = ["让我们", "不得不说", "堪称", "可以说是", "无疑", "在某种意义上",
                  "这一刻", "仿佛", "似乎", "彷佛", "宛如", "犹如", "宛若", "如同", "映入眼帘"]
PREACHY = ["这意味着", "本质上", "说白了", "在这个世界上", "或许", "也许，",
           "正是因为", "而这", "这一切", "之所以", "原来", "终于明白", "这才意识到"]
FILTER_WORDS = ["他看见", "她看见", "他听到", "她听到", "他感到", "她感到",
                "他意识到", "她意识到", "他知道", "她知道", "心中暗道", "心下了然"]
# 表情/心理模板（banned-words 一级禁用词，强 AI 指纹）
TEMPLATE_FACE = ["眼中闪过", "嘴角勾起", "眉头微皱", "眉眼低垂", "瞳孔微缩", "脸色一变",
                 "嘴角微扬", "心中一动", "心头一震", "心底泛起", "心中涌起", "深吸一口气"]
# 判断/情态虚词
JUDGE = ["不容置疑", "不容置喙", "不易察觉", "显而易见", "毫无疑问", "不可否认",
         "一丝", "一抹", "些许", "几分", "隐约"]
# 过渡套话
TRANSITION = ["不由自主", "情不自禁", "自然而然", "不由得", "不禁"]
# WebNovelOps ai_smell_lexicon 里真正新的具体短语
WNO_PHRASES = ["某种看不见的手", "说不清的感觉", "难以置信"]
# 弱化副词（oh-story 模式2：每千字 >3 = AI 签名）
WEAK_ADVERBS = ["微微", "淡淡", "缓缓", "轻轻"]

# ---- 句式正则 ----
FAKE_RANGE = re.compile(r"从.{1,12}?到.{1,12}?，")
ADJ_STACK = re.compile(r"(?:[一-龥]{2,4}的){3,}")
DASH_STACK = re.compile(r"(?:——|……).{0,30}?(?:——|……)")
SIMILE = re.compile(r"[像如]一?(?:[只头条道阵片])|仿佛.{0,8}?(?:一般|似的)|犹如|宛若|宛如")

# 不是A而是B 检测常量（移植 check-ai-patterns.js）
STOP = set("。！？!?\n")
SOFT_SEP = set("，,、；;：:")
HARD_SEP = set("。.！!？?")
TAG_PARTICLES = set("吗吧嘛")
EITHER_OR_PREV = set("不就也")
MAX_SPAN = 80


def _starts(text, i, needle):
    return text[i:i + len(needle)] == needle


def _skip_gap(text, i):
    while i < len(text) and text[i] in " \t\r":
        i += 1
    if i < len(text) and text[i] == "\n":
        i += 1
        while i < len(text) and text[i] in " \t\r":
            i += 1
    return i


def _flip_end(cand):
    """返回 '不是' 后肯定翻转项的结束下标，无则 -1。"""
    i, scanned, crossed = 2, 0, False
    while i < len(cand) and scanned <= MAX_SPAN:
        ch = cand[i]
        if _starts(cand, i, "而是"):
            return i + 2
        if ch in SOFT_SEP:
            nx = _skip_gap(cand, i + 1)
            if _starts(cand, nx, "而是"):
                return nx + 2
            if nx < len(cand) and cand[nx] == "是" and (nx + 1 >= len(cand) or cand[nx + 1] not in TAG_PARTICLES):
                return nx + 1
            crossed = True
        if ch in HARD_SEP:
            nx = _skip_gap(cand, i + 1)
            if nx < len(cand) and cand[nx] == "是" and (nx + 1 >= len(cand) or cand[nx + 1] not in TAG_PARTICLES):
                return nx + 1
            if ch != ".":
                break
            crossed = True
        if ch in STOP:
            break
        if ch == "是" and cand[i - 1] not in EITHER_OR_PREV and not crossed:
            return i + 1
        i += 1
        scanned += 1
    return -1


def find_not_is(text):
    """找所有 不是A(而)是B，排除 是不是 / 只是·可是·但是·还是·于是 等连词尾。"""
    hits, off = [], 0
    while off < len(text):
        s = text.find("不是", off)
        if s == -1:
            break
        if s > 0 and text[s - 1] == "是":  # 是不是
            off = s + 2
            continue
        cand = text[s:]
        end = _flip_end(cand)
        if end == -1:
            off = s + 2
            continue
        raw = re.sub(r"[\s|）)】\]]+$", "", cand[:_extract_end(cand, end)])
        if len(raw) >= 4:
            hits.append(raw[:40])
        off = s + max(len(raw), 2)
    return hits


def _extract_end(cand, marker_end):
    end = marker_end
    limit = min(len(cand), marker_end + MAX_SPAN)
    while end < limit and cand[end] not in STOP:
        end += 1
    return end


def load_whitelist(path):
    if not path or not os.path.exists(path):
        return set()
    out = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            t = line.strip()
            if t and not t.startswith("#"):
                out.add(t)
    return out


def count_any(text, words, whitelist):
    hits = []
    for w in words:
        # 白名单：若禁用词是某白名单词的真子串，跳过（如绰号"缓缓"）
        if any(w in wl and w != wl for wl in whitelist) or w in whitelist:
            continue
        c = text.count(w)
        if c:
            hits.append((w, c))
    return hits


def lint(text, whitelist=frozenset()):
    paras = [p for p in re.split(r"\n+", text.strip()) if p.strip()]
    n_para = max(len(paras), 1)
    chars = max(len(text), 1)
    findings = []
    score = 0.0

    def add(label, hits, weight):
        nonlocal score
        total = sum(c for _, c in hits) if hits else 0
        if total == 0:
            return
        contrib = total / chars * 1000 * weight
        score += contrib
        findings.append({"label": label, "total": total,
                         "density_per_1k": round(total / chars * 1000, 2),
                         "examples": [w for w, _ in hits[:6]], "weight": weight,
                         "contrib": round(contrib, 2)})

    add("机械连接词", count_any(text, CONNECTORS, whitelist), 2.5)
    add("论文体/万能结论", count_any(text, THESIS, whitelist), 3.0)
    add("翻译腔/文言腔", count_any(text, TRANSLATIONESE, whitelist), 2.0)
    add("说教升华/解释腔", count_any(text, PREACHY, whitelist), 1.5)
    add("滤镜词(告知非展示)", count_any(text, FILTER_WORDS, whitelist), 1.8)
    add("表情/心理模板", count_any(text, TEMPLATE_FACE, whitelist), 2.8)
    add("判断/情态虚词", count_any(text, JUDGE, whitelist), 1.5)
    add("过渡套话", count_any(text, TRANSITION, whitelist), 1.5)
    add("AI高频短语", count_any(text, WNO_PHRASES, whitelist), 2.5)

    # 弱化副词密度（oh-story 模式2：每千字 >3 = AI 签名）
    weak_hits = count_any(text, WEAK_ADVERBS, whitelist)
    weak_total = sum(c for _, c in weak_hits)
    weak_density = weak_total / chars * 1000
    if weak_density > 3:
        contrib = (weak_density - 3) * 2.0
        score += contrib
        findings.append({"label": "弱化副词泛滥(>3/千字=AI签名)", "total": weak_total,
                         "density_per_1k": round(weak_density, 2),
                         "examples": [w for w, _ in weak_hits], "weight": "density",
                         "contrib": round(contrib, 2)})

    # 不是A而是B（最毒★★★★★，命中即记，权重高）
    not_is = find_not_is(text)
    if not_is:
        contrib = len(not_is) * 4.0
        score += contrib
        findings.append({"label": "否定翻转(不是A而是B·最毒)", "total": len(not_is),
                         "density_per_1k": round(len(not_is) / chars * 1000, 2),
                         "examples": not_is[:5], "weight": 4.0, "contrib": round(contrib, 2)})

    for label, rx, w in [("虚假范围(从X到Y)", FAKE_RANGE, 2.0),
                         ("形容词叠罗汉(紫色文风)", ADJ_STACK, 3.0),
                         ("破折号/省略号堆叠", DASH_STACK, 1.5),
                         ("比喻信号(像/如/仿佛)", SIMILE, 1.2)]:
        m = rx.findall(text)
        if m:
            contrib = len(m) / chars * 1000 * w
            score += contrib
            findings.append({"label": label, "total": len(m),
                             "density_per_1k": round(len(m) / chars * 1000, 2),
                             "examples": [x if isinstance(x, str) else x[0] for x in m[:4]],
                             "weight": w, "contrib": round(contrib, 2)})

    # 节奏匀速：段落长度方差过低
    if len(paras) >= 4:
        lens = [len(p) for p in paras]
        mean = sum(lens) / len(lens)
        var = sum((x - mean) ** 2 for x in lens) / len(lens)
        cv = (var ** 0.5) / mean if mean else 0
        if cv < 0.35:
            contrib = (0.35 - cv) * 20
            score += contrib
            findings.append({"label": "节奏匀速(段落长度过于均匀)", "total": len(paras),
                             "density_per_1k": round(cv, 2),
                             "examples": [f"段落长度变异系数={round(cv,2)}<0.35"],
                             "weight": "structural", "contrib": round(contrib, 2)})

    # 长段落（>200 字/段，手机阅读卡顿；按镜头断段）—— 借鉴 oh-story check-ai-patterns
    long_paras = [len(p) for p in paras if len(p) > 200]
    if long_paras:
        contrib = len(long_paras) * 1.5
        score += contrib
        findings.append({"label": "长段落(>200字/段,按镜头断段)", "total": len(long_paras),
                         "density_per_1k": 0, "examples": [f"最长 {max(long_paras)} 字"],
                         "weight": "structural", "contrib": round(contrib, 2)})

    # 碎句号：连续 >=6 个短叙述句(可见<=5字)无呼吸（成片提纲感）—— 引号内对话/弹幕豁免
    stutter_runs, run = 0, 0
    for p in paras:
        narrative = re.sub(r"[「『【\"“].*?[」』】\"”]", "", p)
        for s in re.split(r"[。！？!?]", narrative):
            vis = len(re.findall(r"[一-鿿A-Za-z0-9]", s))
            if 0 < vis <= 5:
                run += 1
                if run == 6:
                    stutter_runs += 1
            else:
                run = 0
    if stutter_runs:
        contrib = stutter_runs * 2.0
        score += contrib
        findings.append({"label": "碎句号(连续≥6短句无呼吸,合并成中长句)", "total": stutter_runs,
                         "density_per_1k": 0, "examples": ["叙述句成片≤5字"],
                         "weight": "structural", "contrib": round(contrib, 2)})

    findings.sort(key=lambda f: f["contrib"], reverse=True)
    return round(score, 2), findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="章节正文文件，或 - 表示 stdin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--whitelist", help=".deslop-whitelist 路径（一行一词，# 注释）")
    ap.add_argument("--max-score", type=float, default=10.0, help="AI 味分数阈值（默认 10，经验值）")
    args = ap.parse_args()

    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    whitelist = load_whitelist(args.whitelist)
    score, findings = lint(text, whitelist)
    over = score > args.max_score
    # 有界机械扣分 penalty(0-20)，量纲对齐审校 rubric 0-100：final = weighted_total − penalty。
    penalty = min(20, max(0, round((score - 3) / 3)))

    if args.json:
        print(json.dumps({"ai_taste_score": score, "threshold": args.max_score,
                          "over_threshold": over, "penalty": penalty, "findings": findings},
                         ensure_ascii=False, indent=2))
    else:
        print(f"AI 味·词句层分数: {score}  (阈值 {args.max_score})  机械扣分 penalty={penalty}/20  ->  "
              f"{'偏重，建议过 style/anti-slop-editor' if over else '通过'}")
        for f in findings:
            print(f"  [{f['contrib']:>5}] {f['label']}  x{f['total']}  "
                  f"密度/千字={f['density_per_1k']}  例: {f['examples']}")
        if not findings:
            print("  (未命中词句层 AI 指纹)")
    sys.exit(1 if over else 0)


if __name__ == "__main__":
    main()
