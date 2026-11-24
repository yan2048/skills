#!/usr/bin/env python3
"""skill-lint — 校验 WorkBuddy skill 目录结构与 SKILL.md 是否合规。

只依赖标准库，Python 3.8+ 可运行。

用法：
    python3 skills/skill-lint/scripts/lint_skills.py skills/
    python3 skills/skill-lint/scripts/lint_skills.py skills/foo/SKILL.md
    python3 skills/skill-lint/scripts/lint_skills.py skills/ --strict --json

退出码：
    0  通过
    1  存在 error（--strict 模式下 warning 也算失败）
    2  参数或路径错误
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
NUMBERING_RE = re.compile(r"^(?:\d+[.、)]|[一二三四五六七八九十]+[、.])\s*")

# 推荐章节：缺失只报警告，不阻塞（不同 skill 可按需裁剪结构）
REQUIRED_SECTIONS: Tuple[str, ...] = ("何时使用", "工作流程", "约束")
# description 里应出现的触发标记，便于 AI 正确路由
TRIGGER_MARKERS: Tuple[str, ...] = ("关键词", "触发", "当", "when", "use")
DESCRIPTION_MIN = 20
DESCRIPTION_MAX = 200

EXIT_OK, EXIT_ERROR, EXIT_USAGE = 0, 1, 2


@dataclass
class Issue:
    level: str  # "error" | "warn"
    code: str
    message: str
    line: Optional[int] = None

    def as_dict(self) -> dict:
        return {"level": self.level, "code": self.code, "message": self.message, "line": self.line}


@dataclass
class Report:
    path: Path
    issues: List[Issue]

    @property
    def errors(self) -> int:
        return sum(1 for i in self.issues if i.level == "error")

    @property
    def warnings(self) -> int:
        return sum(1 for i in self.issues if i.level == "warn")


def normalize_lines(text: str) -> List[str]:
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1].strip()
    return value


def parse_frontmatter(lines: List[str]) -> Tuple[Optional[Dict[str, Tuple[str, int]]], int, bool]:
    """返回 (字段表, 正文起始行索引, 是否闭合)。不含 frontmatter 时字段表为 None。"""
    if not lines or lines[0].strip() != "---":
        return None, 0, True

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            end = i
            break
    if end is None:
        return None, 0, False

    fields: Dict[str, Tuple[str, int]] = {}
    i = 1
    while i < end:
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        # 缩进行视为上一字段的续行，已在折叠分支内消费
        if raw[0] in " \t":
            i += 1
            continue
        match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", raw)
        if not match:
            i += 1
            continue

        key, value = match.group(1), match.group(2).strip()
        lineno = i + 1
        if value in (">", "|", ">-", "|-", ">+", "|+"):
            chunks: List[str] = []
            j = i + 1
            while j < end and (not lines[j].strip() or lines[j][0] in " \t"):
                if lines[j].strip():
                    chunks.append(lines[j].strip())
                j += 1
            value, i = " ".join(chunks), j
        else:
            value, i = strip_quotes(value), i + 1
        fields[key] = (value, lineno)

    return fields, end + 1, True


def extract_headings(body: List[str], body_start: int) -> List[Tuple[int, str, int]]:
    """提取正文标题（跳过围栏代码块内的 # 行）。返回 [(级别, 标题, 行号)]。"""
    headings: List[Tuple[int, str, int]] = []
    in_fence = False
    for idx, raw in enumerate(body):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(raw)
        if match:
            headings.append((len(match.group(1)), match.group(2), body_start + idx + 1))
    return headings


def find_empty_sections(body: List[str], headings: List[Tuple[int, str, int]], body_start: int) -> List[Tuple[str, int]]:
    empty: List[Tuple[str, int]] = []
    for pos, (level, title, lineno) in enumerate(headings):
        # 一级标题后面直接跟二级标题是正常写法，只检查二级及以下的空章节
        if level < 2:
            continue
        start = lineno - body_start - 1
        end = (headings[pos + 1][2] - body_start - 1) if pos + 1 < len(headings) else len(body)
        if not any(line.strip() for line in body[start + 1:end]):
            empty.append((title, lineno))
    return empty


def check_skill(md_path: Path, expected_name: str) -> Report:
    issues: List[Issue] = []

    if not md_path.is_file():
        return Report(md_path, [Issue("error", "E001", f"缺少 SKILL.md（目录 {md_path.parent.name}/ 下未找到）")])

    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError as exc:
        return Report(md_path, [Issue("error", "E001", f"无法读取文件：{exc}")])

    lines = normalize_lines(text)
    fields, body_start, closed = parse_frontmatter(lines)

    if not closed:
        issues.append(Issue("error", "E002", "frontmatter 未以 --- 闭合，元数据无法解析", 1))
    elif fields is None:
        issues.append(Issue("error", "E002", "缺少 YAML frontmatter（文件首行应为 ---）", 1))

    fields = fields or {}

    # --- name ---
    if "name" not in fields:
        issues.append(Issue("error", "E003", "frontmatter 缺少 name 字段", 1))
    else:
        name, lineno = fields["name"]
        if not name:
            issues.append(Issue("error", "E003", "name 为空", lineno))
        elif not NAME_RE.match(name):
            issues.append(Issue("error", "E004", f"name「{name}」不合法：只允许小写字母、数字、中划线", lineno))
        elif name != expected_name:
            issues.append(
                Issue("error", "E005", f"name「{name}」与目录名「{expected_name}」不一致", lineno)
            )

    # --- description ---
    if "description" not in fields:
        issues.append(Issue("error", "E006", "frontmatter 缺少 description 字段（AI 路由的唯一依据）", 1))
    else:
        desc, lineno = fields["description"]
        if not desc:
            issues.append(Issue("error", "E006", "description 为空", lineno))
        else:
            if len(desc) < DESCRIPTION_MIN:
                issues.append(
                    Issue("warn", "W001", f"description 偏短（{len(desc)} 字符），建议写清触发场景", lineno)
                )
            if len(desc) > DESCRIPTION_MAX:
                issues.append(
                    Issue("warn", "W002", f"description 偏长（{len(desc)} 字符 > {DESCRIPTION_MAX}），可能稀释路由精度", lineno)
                )
            if not any(marker in desc.lower() for marker in TRIGGER_MARKERS):
                issues.append(
                    Issue("warn", "W003", "description 未见触发标记（如「关键词」「当……时」），路由命中率可能偏低", lineno)
                )

    # --- 正文 ---
    body = lines[body_start:]
    headings = extract_headings(body, body_start)

    if not any(level == 1 for level, _, _ in headings):
        issues.append(Issue("warn", "W004", "正文缺少一级标题（# 标题）", body_start + 1))

    titles = [NUMBERING_RE.sub("", title) for _, title, _ in headings]
    for section in REQUIRED_SECTIONS:
        if not any(section in title for title in titles):
            issues.append(
                Issue("warn", "W005", f"缺少推荐章节「{section}」（三段式骨架：何时使用 / 工作流程 / 约束）")
            )

    for title, lineno in find_empty_sections(body, headings, body_start):
        issues.append(Issue("warn", "W006", f"章节「{title}」没有内容", lineno))

    return Report(md_path, issues)


def collect_targets(raw_paths: List[str]) -> Tuple[List[Tuple[Path, str]], List[str]]:
    """把入口路径展开为 [(SKILL.md 路径, 期望目录名)]；同时返回路径级错误。"""
    targets: List[Tuple[Path, str]] = []
    problems: List[str] = []
    seen = set()

    for raw in raw_paths:
        path = Path(raw).expanduser()
        if not path.exists():
            problems.append(f"路径不存在：{path}")
            continue
        if path.is_file():
            if path.name != "SKILL.md":
                problems.append(f"跳过非 SKILL.md 文件：{path}")
            elif path.resolve() not in seen:
                seen.add(path.resolve())
                targets.append((path, path.parent.name))
            continue

        # 目录本身就是一个 skill：只校验它，不再把 references/、scripts/ 当成 skill
        if (path / "SKILL.md").is_file():
            if path.resolve() not in seen:
                seen.add(path.resolve())
                targets.append((path / "SKILL.md", path.name))
            continue

        candidates: List[Path] = []
        for child in sorted(path.iterdir()):
            if not child.is_dir() or child.name.startswith((".", "_")):
                continue
            candidates.append(child / "SKILL.md")
        for md in candidates:
            key = md.parent.resolve()
            if key in seen:
                continue
            seen.add(key)
            targets.append((md, md.parent.name))

    return targets, problems


def render_text(reports: List[Report]) -> str:
    out: List[str] = []
    for report in reports:
        try:
            shown = report.path.relative_to(Path.cwd())
        except ValueError:
            shown = report.path
        if not report.issues:
            out.append(f"✓ {shown}")
            continue
        out.append(f"✗ {shown}")
        for issue in sorted(report.issues, key=lambda i: (0, i.line) if i.line else (1, 0)):
            tag = "ERROR" if issue.level == "error" else "WARN "
            where = f"第 {issue.line} 行" if issue.line else "—"
            out.append(f"    {tag} {issue.code}  {where}  {issue.message}")
    return "\n".join(out)


def render_summary(reports: List[Report]) -> str:
    errors = sum(r.errors for r in reports)
    warnings = sum(r.warnings for r in reports)
    return f"共检查 {len(reports)} 个 skill：{errors} 错误，{warnings} 警告"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lint_skills.py",
        description="校验 skill 目录结构与 SKILL.md frontmatter 是否合规。",
    )
    parser.add_argument("paths", nargs="*", default=["skills"], help="skills 根目录或单个 SKILL.md，默认 skills")
    parser.add_argument("--strict", action="store_true", help="把 warning 也视为失败")
    parser.add_argument("--json", action="store_true", help="输出 JSON，便于 CI 或二次处理")
    parser.add_argument("--quiet", action="store_true", help="只输出汇总与失败项")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    targets, problems = collect_targets(args.paths)
    for problem in problems:
        print(problem, file=sys.stderr)
    if not targets:
        print("没有找到可校验的 skill", file=sys.stderr)
        return EXIT_USAGE

    reports = [check_skill(md, name) for md, name in targets]
    total_errors = sum(r.errors for r in reports)
    total_warnings = sum(r.warnings for r in reports)
    failed = total_errors > 0 or (args.strict and total_warnings > 0)

    if args.json:
        payload = {
            "summary": {
                "skills": len(reports),
                "errors": total_errors,
                "warnings": total_warnings,
                "strict": args.strict,
                "passed": not failed,
            },
            "reports": [
                {
                    "path": str(r.path),
                    "name": r.path.parent.name,
                    "issues": [i.as_dict() for i in r.issues],
                }
                for r in reports
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        visible = [r for r in reports if not args.quiet or r.issues]
        if visible:
            print(render_text(visible))
        print(render_summary(reports))

    return EXIT_ERROR if failed else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
