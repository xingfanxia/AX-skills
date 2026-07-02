#!/usr/bin/env python3
"""深度调研报告的确定性引用校验门（citation integrity gate）。

把报告里的每条引用 URL 对到「来源池」——本次调研落盘的搜索结果和笔记
（tmp/tavily/*.json、tmp/<session_slug>/*.md 等）中出现过的 URL——
用 URL 签名（域名 + 前 3 段路径）做容错匹配，抓出模型虚构的引用。

用法:
    python3 verify_citations.py <报告.md> [--sources PATH ...] [--json] [--max-share 0.25]
    python3 verify_citations.py --self-test

来源池:
    --sources 接受文件或目录（可多个）；目录递归扫描 .json/.md/.txt 提取 URL。
    缺省扫描当前目录下 ./tmp/（同时覆盖 tavily 落盘结果和 session 笔记）。
    报告文件本身即使位于来源池目录下也会被排除，防止自我验证。

校验项:
    INVENTED_URL         critical  引用 URL 在来源池中找不到 —— 疑似虚构
    MALFORMED_CITATION   critical  空链接 [来源]()、缺 scheme 的链接、悬空 [来源]
    NO_CITATIONS         critical  正文没有任何 URL 引用
    DOMAIN_ONLY_MATCH    warning   仅域名命中来源池，具体文章路径对不上
    DANGLING_REFERENCE   warning   来源汇总里列出但正文从未引用
    MISSING_FROM_SUMMARY warning   正文引用了但来源汇总没收录
    NO_SUMMARY_SECTION   warning   报告缺少 来源汇总 段
    SOURCE_CONCENTRATION warning   单一来源占正文引用超过阈值（默认 25%）

退出码: 0 = 通过（可带 warning）；1 = 存在 critical；2 = 用法 / IO 错误。

URL 签名匹配思路借自 staruhub/ClaudeSkills (MIT)；代码为独立重写。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

TRACKING_KEYS = {"ref", "ref_src", "source", "fbclid", "gclid", "spm"}
POOL_SUFFIXES = {".json", ".md", ".markdown", ".txt"}

URL_RE = re.compile(r"https?://[^\s\"'<>\\)\]}（）】]+")
MD_LINK_RE = re.compile(
    r"!?\[([^\]]*)\]\(\s*([^()\s]*(?:\([^()\s]*\)[^()\s]*)*)\s*\)"
)
REF_HEADING_RE = re.compile(
    r"^#{1,6}\s*(?:来源汇总|来源列表|参考来源|参考文献|References|Sources)\b[^\n]*$",
    re.MULTILINE | re.IGNORECASE,
)
BARE_LABEL_RE = re.compile(r"\[(来源|原文|source|link)\](?!\()", re.IGNORECASE)
SCHEMELESS_RE = re.compile(
    r"^(?:www\.|[a-z0-9][a-z0-9.-]*\.(?:com|org|net|io|dev|ai|co|cn|edu|gov|app|info|me)(?:/|$))",
    re.IGNORECASE,
)


# ---------------------------------------------------------------- URL 匹配

def strip_trailing_punct(url: str) -> str:
    return url.rstrip(".,;:!?，。；：、")


def normalize_url(url: str) -> str:
    """去掉 scheme/www/追踪参数/尾斜杠后的可比较形式。"""
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in TRACKING_KEYS
    ]
    path = parsed.path.rstrip("/")
    return host + path + (("?" + urlencode(query)) if query else "")


def url_signature(url: str) -> tuple:
    """(域名, 前 3 段路径) —— 同一篇文章在不同变体 URL 下签名一致。"""
    parsed = urlparse(url.strip().lower())
    host = parsed.hostname or ""
    if host.startswith("www."):
        host = host[4:]
    segments = tuple(p for p in parsed.path.split("/") if p)[:3]
    return (host, segments)


class SourcePool:
    """来源池：调研过程中真实出现过的 URL 集合。"""

    def __init__(self, urls: set[str]):
        self.normalized = {normalize_url(u) for u in urls}
        self.signatures = {url_signature(u) for u in urls}
        self.domains = {sig[0] for sig in self.signatures}

    def __len__(self) -> int:
        return len(self.normalized)

    def match(self, url: str) -> str:
        """exact > signature > domain > none。前两档视为已验证。"""
        if normalize_url(url) in self.normalized:
            return "exact"
        sig = url_signature(url)
        if sig in self.signatures:
            return "signature"
        if sig[0] in self.domains:
            return "domain"
        return "none"


# ---------------------------------------------------------------- 报告解析

def line_at(text: str, pos: int, base_line: int = 1) -> int:
    return base_line + text.count("\n", 0, pos)


def split_report(text: str) -> tuple[str, str, int | None]:
    """切出正文与来源汇总段。返回 (正文, 汇总段, 汇总段起始行号或 None)。"""
    m = REF_HEADING_RE.search(text)
    if not m:
        return text, "", None
    return text[: m.start()], text[m.end():], line_at(text, m.end())


def make_issue(itype: str, severity: str, message: str,
               line: int | None = None, url: str | None = None) -> dict:
    return {"type": itype, "severity": severity, "message": message,
            "line": line, "url": url}


def extract_citations(text: str, base_line: int = 1) -> tuple[list, list]:
    """提取引用 URL 和畸形引用问题。

    返回 (citations, issues)，citations 为 [(url, 行号), ...]，
    覆盖 markdown 链接 [来源](URL) 和裸 URL（含 中文全角括号（URL） 格式）。
    """
    citations: list[tuple[str, int]] = []
    issues: list[dict] = []

    for m in MD_LINK_RE.finditer(text):
        label = m.group(1).strip()
        target = m.group(2).strip()
        line = line_at(text, m.start(), base_line)
        if target.startswith("#") or target.startswith("mailto:"):
            continue
        if not target:
            issues.append(make_issue(
                "MALFORMED_CITATION", "critical",
                f"空链接 [{label}]() —— 引用缺 URL", line=line))
        elif target.startswith(("http://", "https://")):
            citations.append((strip_trailing_punct(target), line))
        elif SCHEMELESS_RE.match(target):
            issues.append(make_issue(
                "MALFORMED_CITATION", "critical",
                f"[{label}]({target}) 缺少 http(s):// 前缀",
                line=line, url=target))
        # 其余相对路径 / 锚点不视为引用

    # 遮住 markdown 链接后再扫裸 URL 和悬空引用标签，避免重复计数
    masked = MD_LINK_RE.sub(lambda m: " " * len(m.group(0)), text)
    for m in URL_RE.finditer(masked):
        citations.append(
            (strip_trailing_punct(m.group(0)), line_at(text, m.start(), base_line)))
    for m in BARE_LABEL_RE.finditer(masked):
        issues.append(make_issue(
            "MALFORMED_CITATION", "critical",
            f"[{m.group(1)}] 后面没有跟链接 —— 悬空引用",
            line=line_at(text, m.start(), base_line)))

    return citations, issues


# ---------------------------------------------------------------- 来源池加载

def urls_from_text(text: str) -> set[str]:
    return {strip_trailing_punct(m.group(0)) for m in URL_RE.finditer(text)}


def collect_pool_urls(paths, exclude: Path | None = None) -> tuple[set[str], int]:
    """从文件/目录列表提取 URL 池。目录递归扫 .json/.md/.txt。"""
    urls: set[str] = set()
    files_scanned = 0
    exclude_resolved = exclude.resolve() if exclude else None

    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            candidates = [f for f in sorted(p.rglob("*"))
                          if f.is_file() and f.suffix.lower() in POOL_SUFFIXES]
        elif p.is_file():
            candidates = [p]
        else:
            raise FileNotFoundError(f"来源池路径不存在: {raw}")
        for f in candidates:
            if exclude_resolved and f.resolve() == exclude_resolved:
                continue
            urls |= urls_from_text(f.read_text(encoding="utf-8", errors="ignore"))
            files_scanned += 1

    return urls, files_scanned


# ---------------------------------------------------------------- 校验主逻辑

def run_checks(report_text: str, pool: SourcePool,
               max_share: float = 0.25,
               min_citations_for_share: int = 8) -> dict:
    body, summary_text, summary_base = split_report(report_text)
    body_cites, issues = extract_citations(body)

    summary_cites: list[tuple[str, int]] = []
    if summary_base is not None:
        summary_cites, summary_issues = extract_citations(summary_text, summary_base)
        issues.extend(summary_issues)
    else:
        issues.append(make_issue(
            "NO_SUMMARY_SECTION", "warning",
            "报告缺少来源汇总段（## 来源汇总 / 参考文献）"))

    if not body_cites:
        issues.append(make_issue(
            "NO_CITATIONS", "critical",
            "正文没有任何 URL 引用 —— 调研报告必须可追溯"))

    # 虚构 / 仅域名命中（同一 URL 只报一次）
    seen: set[str] = set()
    for url, line in body_cites + summary_cites:
        key = normalize_url(url)
        if key in seen:
            continue
        seen.add(key)
        level = pool.match(url)
        if level == "none":
            issues.append(make_issue(
                "INVENTED_URL", "critical",
                "来源池中找不到该 URL —— 疑似虚构引用，删除或替换为真实搜索结果",
                line=line, url=url))
        elif level == "domain":
            issues.append(make_issue(
                "DOMAIN_ONLY_MATCH", "warning",
                "仅域名命中来源池，具体文章路径对不上 —— 人工确认是否同一篇",
                line=line, url=url))

    body_sigs = {url_signature(u) for u, _ in body_cites}
    summary_sigs = {url_signature(u) for u, _ in summary_cites}

    if summary_base is not None:
        for url, line in summary_cites:
            if url_signature(url) not in body_sigs:
                issues.append(make_issue(
                    "DANGLING_REFERENCE", "warning",
                    "来源汇总里列出但正文从未引用", line=line, url=url))
        reported: set[tuple] = set()
        for url, line in body_cites:
            sig = url_signature(url)
            if sig not in summary_sigs and sig not in reported:
                reported.add(sig)
                issues.append(make_issue(
                    "MISSING_FROM_SUMMARY", "warning",
                    "正文引用了但来源汇总没收录", line=line, url=url))

    # 来源集中度：单一来源（同一签名）占正文引用比例过高
    total = len(body_cites)
    if total >= min_citations_for_share:
        counts = Counter(url_signature(u) for u, _ in body_cites)
        for (host, segments), n in counts.most_common():
            share = n / total
            if share <= max_share:
                break
            source = host + ("/" + "/".join(segments) if segments else "")
            issues.append(make_issue(
                "SOURCE_CONCENTRATION", "warning",
                f"单一来源 {source} 占正文引用 {n}/{total}（{share:.0%}）"
                f"—— 超过 {max_share:.0%} 阈值，考虑分散信源"))

    criticals = sum(1 for i in issues if i["severity"] == "critical")
    warnings = sum(1 for i in issues if i["severity"] == "warning")
    return {
        "summary": {
            "body_citations": total,
            "unique_sources": len(body_sigs),
            "summary_entries": len(summary_cites),
            "pool_urls": len(pool),
            "critical": criticals,
            "warning": warnings,
            "verdict": "FAIL" if criticals else "PASS",
        },
        "issues": sorted(
            issues,
            key=lambda i: (i["severity"] != "critical", i["line"] or 0)),
    }


def print_human(result: dict, report_path: str) -> None:
    s = result["summary"]
    print(f"== 引用校验: {report_path} ==")
    print(f"来源池 {s['pool_urls']} 个 URL | 正文引用 {s['body_citations']} 处"
          f"（独立来源 {s['unique_sources']}）| 来源汇总 {s['summary_entries']} 条")
    for issue in result["issues"]:
        tag = "CRITICAL" if issue["severity"] == "critical" else "WARNING "
        loc = f"L{issue['line']}" if issue["line"] else "-"
        url = f"  {issue['url']}" if issue["url"] else ""
        print(f"[{tag}] {issue['type']} {loc}{url}")
        print(f"           {issue['message']}")
    print(f"结论: {s['verdict']}（{s['critical']} critical, {s['warning']} warning）")


# ---------------------------------------------------------------- 自测

def self_test() -> int:
    import tempfile

    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(f"[{'PASS' if cond else 'FAIL'}] {name}"
              + (f" — {detail}" if detail and not cond else ""))
        if not cond:
            failures.append(name)

    pool = SourcePool({
        "https://www.example.com/blog/2026/great-post?utm_source=x",
        "https://github.com/acme/widget/issues/42",
        "https://docs.acme.dev/setup",
    })

    # 1. URL 签名容错匹配
    check("匹配: 协议/www/追踪参数/尾斜杠差异不影响命中",
          pool.match("http://example.com/blog/2026/great-post/?fbclid=1") == "exact")
    check("匹配: 同域不同文 → domain",
          pool.match("https://github.com/acme/another-repo") == "domain")
    check("匹配: 未知域名 → none",
          pool.match("https://unknown.example.net/x") == "none")

    # 2. 干净报告 → PASS 且 0 issue
    clean = """# 报告

判断一[来源](https://example.com/blog/2026/great-post)。
判断二（https://github.com/acme/widget/issues/42）

## 来源汇总
- [great post](https://example.com/blog/2026/great-post)
- https://github.com/acme/widget/issues/42
"""
    r = run_checks(clean, pool)
    check("干净报告: verdict PASS 且 0 issue",
          r["summary"]["verdict"] == "PASS" and not r["issues"],
          json.dumps(r["issues"], ensure_ascii=False))

    # 3. 虚构 URL → critical + FAIL
    invented = clean.replace("https://github.com/acme/widget/issues/42",
                             "https://github-fake.example.org/acme/widget")
    r = run_checks(invented, pool)
    check("虚构引用: 检出 INVENTED_URL 且 verdict FAIL",
          r["summary"]["verdict"] == "FAIL"
          and any(i["type"] == "INVENTED_URL" for i in r["issues"]))

    # 4. 畸形引用 + 悬空汇总条目
    malformed = """# 报告

空链接[来源]()，悬空[来源]，缺协议[x](www.foo.com)。

## 来源汇总
- https://docs.acme.dev/setup
"""
    r = run_checks(malformed, pool)
    n_malformed = sum(1 for i in r["issues"] if i["type"] == "MALFORMED_CITATION")
    check("畸形引用: 空链接/悬空标签/缺协议共检出 3 处",
          n_malformed == 3, f"实际 {n_malformed}")
    check("悬空条目: 汇总列出但正文未引用 → DANGLING_REFERENCE",
          any(i["type"] == "DANGLING_REFERENCE" for i in r["issues"]))

    # 5. 目录扫描来源池 + 来源集中度
    with tempfile.TemporaryDirectory() as td:
        notes = Path(td) / "notes"
        notes.mkdir()
        (notes / "search1.json").write_text(json.dumps({
            "results": [{"url": f"https://site{i}.example.com/post/a"}
                        for i in range(5)]
            + [{"url": "https://hot.example.com/only/article"}],
        }), encoding="utf-8")
        (notes / "scratchpad.md").write_text(
            "笔记 https://extra.example.com/note-source\n", encoding="utf-8")
        urls, n_files = collect_pool_urls([td])
        check("来源池: 目录递归扫描提取 7 个 URL",
              len(urls) == 7 and n_files == 2,
              f"urls={len(urls)} files={n_files}")

        body = ["引用（https://hot.example.com/only/article）"] * 5 + [
            f"引用（https://site{i}.example.com/post/a）" for i in range(4)]
        summary = [f"- https://site{i}.example.com/post/a" for i in range(4)] + [
            "- https://hot.example.com/only/article"]
        conc = "# 报告\n\n" + "\n".join(body) + "\n\n## 来源汇总\n" + "\n".join(summary) + "\n"
        r = run_checks(conc, SourcePool(urls))
        check("集中度: 单源 5/9 触发 SOURCE_CONCENTRATION，verdict 仍 PASS",
              r["summary"]["verdict"] == "PASS"
              and any(i["type"] == "SOURCE_CONCENTRATION" for i in r["issues"]))

    print(f"\n自测结果: {'全部通过' if not failures else f'{len(failures)} 项失败: {failures}'}")
    return 1 if failures else 0


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="verify_citations.py",
        description="深度调研报告引用完整性校验：虚构/悬空/畸形引用 + 来源集中度",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python3 verify_citations.py report.md                  # 来源池默认扫 ./tmp/\n"
            "  python3 verify_citations.py report.md --sources tmp/my-session/ tmp/tavily/\n"
            "  python3 verify_citations.py report.md --json\n"
            "  python3 verify_citations.py --self-test\n"
            "\n退出码: 0=通过  1=有 critical  2=用法/IO 错误"),
    )
    parser.add_argument("report", nargs="?", help="报告 .md 路径")
    parser.add_argument("--sources", nargs="+", metavar="PATH",
                        help="来源池文件或目录，可多个（默认 ./tmp/）")
    parser.add_argument("--max-share", type=float, default=0.25,
                        help="单一来源占比警告阈值（默认 0.25）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 结果")
    parser.add_argument("--self-test", action="store_true", help="运行内置自测")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.report:
        parser.error("需要报告路径（或 --self-test）")

    report_path = Path(args.report)
    try:
        report_text = report_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"错误: 无法读取报告 {report_path}: {exc}", file=sys.stderr)
        return 2

    source_paths = args.sources or (["tmp"] if Path("tmp").is_dir() else None)
    if not source_paths:
        print("错误: 未指定 --sources 且当前目录下没有 tmp/ —— 无来源池可比对",
              file=sys.stderr)
        return 2

    try:
        pool_urls, files_scanned = collect_pool_urls(source_paths, exclude=report_path)
    except FileNotFoundError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2
    if not pool_urls:
        print(f"错误: 来源池为空（扫描 {files_scanned} 个文件未发现 URL）"
              "—— 先把搜索结果落盘再校验", file=sys.stderr)
        return 2

    result = run_checks(report_text, SourcePool(pool_urls), max_share=args.max_share)
    result["summary"]["pool_files"] = files_scanned
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result, str(report_path))
    return 1 if result["summary"]["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
