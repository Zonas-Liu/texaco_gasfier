#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查维护文档并用AST生成源码符号索引；不导入模型、不运行界面。"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs/code_reference/10_CODE_INDEX.md"
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")


def source_paths():
    """仅列产品Python模块，排除环境、生成物及实验副本。"""
    return sorted({*ROOT.joinpath("src").rglob("*.py"),
                   *ROOT.joinpath("web_backend").rglob("*.py"),
                   ROOT / "app.py", ROOT / "run_app.py"})


class Symbols(ast.NodeVisitor):
    """记录类、函数、方法和嵌套函数的限定名称/定义行。"""

    def __init__(self):
        self.scope = []
        self.rows = []

    def add(self, node, kind, signature):
        qualified = ".".join([*self.scope, node.name])
        doc = (ast.get_docstring(node) or "").strip().splitlines()
        self.rows.append((node.lineno, kind, qualified, signature,
                          doc[0] if doc else "—"))
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_ClassDef(self, node):
        bases = ", ".join(ast.unparse(base) for base in node.bases)
        self.add(node, "类", f"{node.name}({bases})")

    def visit_FunctionDef(self, node):
        signature = f"{node.name}({ast.unparse(node.args)})"
        if node.returns is not None:
            signature += " -> " + ast.unparse(node.returns)
        self.add(node, "函数/方法", signature)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)


def table_text(text):
    return str(text).replace("|", "&#124;").replace("`", "&#96;").replace("\n", " ")


def build_index():
    modules = []
    for path in source_paths():
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        visitor = Symbols()
        visitor.visit(tree)
        modules.append((path.relative_to(ROOT).as_posix(), visitor.rows))
    total = sum(len(rows) for _, rows in modules)
    lines = ["# 10. 源码符号索引", "",
             "[手册首页](README.md) · [接口语义](04_API_REFERENCE.md)", "",
             "由 `scripts/check_docs.py --write-index` 从AST生成，请勿手改。"
             "包含src、web_backend及两入口模块的类、函数、方法、嵌套函数；"
             "不导入这些模块。签名与定义行来自源码，末列仅摘录docstring首行，"
             "不代替前9章的前置条件、单位、公式和适用边界。", "",
             f"范围：{len(modules)} 个Python文件，{total} 个定义。测试/实验脚本见"
             "[验证章](09_VALIDATION_AND_LIMITATIONS.md)，原生JS接口见第4章。", "",
             "## 模块导航", "", "| 文件 | 定义数 |", "|---|---:|"]
    for path, rows in modules:
        lines.append(f"| [{path}](../../{path}) | {len(rows)} |")
    for path, rows in modules:
        if not rows:
            continue
        lines.extend(["", f"## {path}", "", "| 定义/源码 | 类型 | 签名 | 源码摘要 |",
                      "|---|---|---|---|"])
        for number, kind, name, signature, doc in rows:
            lines.append(f"| [{table_text(name)}](../../{path}#L{number}) | {kind} | "
                         f"`{table_text(signature)}` | {table_text(doc)} |")
    return "\n".join(lines) + "\n", len(modules), total


def documentation_paths():
    # 只归档原文豁免，archive/README作为当前导航仍需检查。
    return sorted([ROOT / "README.md", ROOT / "AGENTS.md",
                   *(p for p in (ROOT / "docs").rglob("*.md")
                     if "archive" not in p.relative_to(ROOT / "docs").parts
                     or p == ROOT / "docs/archive/README.md")])


def check_markdown(path):
    errors, links = [], 0
    fence, math_start = None, None
    rel = path.relative_to(ROOT)
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        marker = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if marker:
            token, suffix = marker.groups()
            if fence is None:
                fence = (token, number)
            elif token[0] == fence[0][0] and len(token) >= len(fence[0]) and not suffix.strip():
                fence = None
            continue
        if fence:
            continue
        if line.strip() == "$$":
            math_start = None if math_start else number
            continue
        if math_start:
            continue
        for match in LINK.finditer(line):
            raw = match.group(1).strip()
            if raw.startswith("<"):
                raw = raw[1:raw.index(">")]
            else:
                raw = re.sub(r'\s+[\"\x27].*$', '', raw)
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            links += 1
            if not target.exists():
                errors.append(f"{rel}:{number}: missing link {raw}")
                continue
            fragment = re.fullmatch(r"L(\d+)(?:-L(\d+))?", parsed.fragment)
            if fragment and target.is_file():
                count = len(target.read_text(encoding="utf-8-sig").splitlines())
                start, end = int(fragment[1]), int(fragment[2] or fragment[1])
                if not 1 <= start <= end <= count:
                    errors.append(f"{rel}:{number}: invalid source line {raw}")
    if fence:
        errors.append(f"{rel}:{fence[1]}: unclosed code fence")
    if math_start:
        errors.append(f"{rel}:{math_start}: unclosed display math")
    return errors, links


def check_parameter_table():
    """核对第5章参数行号/顺序；从AST取字面量，不导入后端。"""
    tree = ast.parse((ROOT / "web_backend/dataparser.py").read_text(encoding="utf-8"))
    layouts = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name, value = node.target.id, node.value
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name, value = node.targets[0].id, node.value
        else:
            continue
        if name in ("PARAM_LINES", "OPTIONAL_LINES"):
            layouts[name] = ast.literal_eval(value)
    expected = [(str(i), name) for i, row in enumerate(
        layouts["PARAM_LINES"] + layouts["OPTIONAL_LINES"], 1) for name in row]
    text = (ROOT / "docs/code_reference/05_INPUT_OUTPUT.md").read_text(encoding="utf-8")
    actual = re.findall(r"^\|\s*(\d+)\s*\|\s*`([A-Z][A-Z_0-9]+)`\s*\|", text, re.M)
    return ([] if actual == expected else ["第5章输入参数表与PARAM_LINES/OPTIONAL_LINES行号或顺序不符"]), len(expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-index", action="store_true", help="先更新第10章，再检查文档")
    args = parser.parse_args()
    expected, modules, symbols = build_index()
    if args.write_index:
        INDEX.write_text(expected, encoding="utf-8")
    errors, parameters = check_parameter_table()
    if not INDEX.exists() or INDEX.read_text(encoding="utf-8") != expected:
        errors.append("源码索引过期；运行 python scripts/check_docs.py --write-index")
    paths, links = documentation_paths(), 0
    for path in paths:
        found, count = check_markdown(path)
        errors.extend(found)
        links += count
    for error in errors:
        print(error)
    print(f"Documents={len(paths)}, local_links={links}, source_files={modules}, "
          f"symbols={symbols}, parameters={parameters}, errors={len(errors)}")
    print("Scope: local targets/source lines, code/math fences, parameter layout, AST index freshness; "
          "external URLs, heading anchors, formula correctness need separate review.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
