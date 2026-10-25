"""One-click registration tool for connecting PDS & Logos-2 RAG Knowledge Base to Codex and Claude Code.

Usage:
    python register_codex.py [--workspace <path>] [--python-bin <path>] [--mode all|agents_md|codex_config] [--test] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

RAG_ROOT = Path(__file__).resolve().parent

BANNER = r"""
================================================================================
  ____  ____  ____    _                                ____    ____    _    ____  
 |  _ \|  _ \/ ___|  | |    ___   __ _  ___  ___      |  _ \  / ___|  / \  | __ ) 
 | |_) | | | \___ \  | |   / _ \ / _` |/ _ \/ __|_____| |_) || |  _  / _ \ |  _ \ 
 |  __/| |_| |___) | | |__| (_) | (_| | (_) \__ \_____|  _ < | |_| |/ ___ \| |_) |
 |_|   |____/|____/  |_____\___/ \__, |\___/|___/      |_| \_\ \____/_/   \_\____/ 
                                 |___/                                             
     Codex & Claude Code Knowledge Base Auto-Registration Tool (v1.0)
================================================================================
"""

RULE_SNIPPET_TEMPLATE = """<!-- PDS_LOGOS2_RAG_START -->
## PDS 与芯片 RAG 知识库检索规则（必查项）

在修改 `.fdc` 约束、调整 PDS 综合/布局布线策略、处理时序违例（WNS/WHS）、调用底层原语或排查报错前，**必须优先检索本地 PDS & Logos-2 专用 RAG 知识库**：

### 检索调用命令

```powershell
& "{python_bin}" "{search_script}" "<查询关键词或错误代码>" --top-k 3 --max-chars 800 --json
```

- **机器读取模式**：加 `--json` 参数，返回结构化 JSON 结果（含 `source`、`pdf_page`、`error_code`、`entities`、`text`）。
- **高频排查支持**：
  - 错误代码直查：`Place-0084`、`Route-2036`、`Flow-0009`、`Flow-0189`
  - 专用约束属性：`PAP_CLOCK_DEDICATED_ROUTE`、`PAP_LOC`、`PAP_IO_STANDARD`
  - 底层芯片原语：`GTP_CLKBUFG`、`GTP_INBUFGDS`、`GTP_APM_E2`、`GTP_DRM36K`、`CLMA`、`CLMS`
  - 后端工具技巧：`Timing Analyzer` 免重跑 STA、`Design Editor` 局部拆线重布、DDR3 `HMIC_S` 时序放宽与 AXI 状态机
  - 前沿加速论文：`FlightLLM` (ACM FPGA 2024)、`AutoBridge` (ACM FPGA 2021)、`RapidStream IR` (2024)、`LATCH` (2026)
- **模式切换**：支持 `--mode hybrid`（默认，BM25 0.4 + 向量 0.6 混合）、`--mode keyword`（纯 BM25，超轻量极速）、`--mode semantic`（纯语义向量）。

### 引用规范
- 回答或修改代码时，须引用检索到的手册来源与物理页码（如 `Pango_Design_Suite_User_Guide.pdf Page 175`），严禁凭空臆造 PDS Tcl 参数或原语端口名。
- 严禁将 Xilinx Vivado 的专有属性（如 `CLOCK_DEDICATED_ROUTE`、`DONT_TOUCH`）直接套用在 PDS 上，必须使用 PDS 对应的 `PAP_*` 或 `syn_*` 属性。
<!-- PDS_LOGOS2_RAG_END -->"""

CODEX_INSTRUCTIONS_TEMPLATE = """# Codex Instructions - PDS & Logos-2 RAG Knowledge Base

This project uses the Pango Design Suite (PDS 2022.2-SP6.4) and Logos-2 (PG2L200H) RAG Knowledge Base.

Whenever you need to:
1. Write or verify `.fdc` physical and timing constraints
2. Diagnose PDS compile/PnR errors (`Place-0084`, `Route-2036`, `Flow-0009`)
3. Use Logos-2 FPGA primitives (`GTP_CLKBUFG`, `GTP_APM_E2`, `GTP_DRM36K`, `CLMA`, `CLMS`, `HMIC_S`)
4. Optimize systolic array, RISC-V, or LLM accelerators on FPGA (FlightLLM, AutoBridge, RapidStream, LATCH)

You MUST execute the local RAG search tool:

```powershell
& "{python_bin}" "{search_script}" "<keyword or error code>" --top-k 3 --max-chars 800 --json
```

Always cite the manual title and page number returned by RAG (e.g., `Pango_Design_Suite_User_Guide.pdf Page 115`).
"""

def detect_python() -> str:
    # 1. Active interpreter
    curr = sys.executable
    if curr and Path(curr).exists():
        # Check if current interpreter has chromadb
        try:
            import chromadb
            return str(Path(curr).resolve())
        except ImportError:
            pass

    # 2. Known virtual environments
    candidates = [
        r"D:\Vivado_RAG\.venv\Scripts\python.exe",
        str(RAG_ROOT / ".venv" / "Scripts" / "python.exe"),
        r"C:\Users\26633\.venv\Scripts\python.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return sys.executable

def test_rag_query(python_bin: str, search_script: Path) -> bool:
    print("\n[TEST] Running diagnostic search query on RAG knowledge base...")
    cmd = [python_bin, str(search_script), "PAP_CLOCK_DEDICATED_ROUTE", "--top-k", "1", "--json"]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=25)
        stdout = res.stdout.decode("utf-8", errors="replace")
        stderr = res.stderr.decode("utf-8", errors="replace")
        if res.returncode == 0 and "PAP_CLOCK_DEDICATED_ROUTE" in stdout:
            print("[TEST] Diagnostic query PASSED! Knowledge base returned valid chunks.")
            return True
        else:
            print(f"[TEST WARNING] Query finished with code {res.returncode}. Output:\n{stdout[:300]}\n{stderr[:300]}")
            return False
    except Exception as e:
        print(f"[TEST ERROR] Failed to run test query: {e}")
        return False

def update_agents_md(target_file: Path, snippet: str, dry_run: bool = False) -> bool:
    if target_file.exists():
        content = target_file.read_text(encoding="utf-8")
    else:
        content = "# Multi-Agent Coordination Rules\n\n"

    start_tag = "<!-- PDS_LOGOS2_RAG_START -->"
    end_tag = "<!-- PDS_LOGOS2_RAG_END -->"

    if start_tag in content and end_tag in content:
        prefix = content[:content.find(start_tag)]
        suffix = content[content.find(end_tag) + len(end_tag):]
        new_content = prefix + snippet + suffix
        action_msg = "Updated existing RAG section in"
    elif "## 4. PDS 与芯片 RAG 知识库检索规则" in content or "## PDS 与芯片 RAG 知识库检索规则" in content:
        # Replace existing section if headers match
        lines = content.splitlines(keepends=True)
        new_lines = []
        skip = False
        for line in lines:
            if "## 4. PDS 与芯片 RAG 知识库检索规则" in line or "## PDS 与芯片 RAG 知识库检索规则" in line:
                skip = True
                new_lines.append(snippet + "\n")
                continue
            if skip and line.startswith("## ") and not line.startswith("### "):
                skip = False
            if not skip:
                new_lines.append(line)
        new_content = "".join(new_lines)
        action_msg = "Replaced legacy RAG section in"
    else:
        new_content = content.rstrip() + "\n\n" + snippet + "\n"
        action_msg = "Appended RAG section to"

    if dry_run:
        print(f"[DRY-RUN] Would have {action_msg.lower()} {target_file}")
        return True

    target_file.write_text(new_content, encoding="utf-8")
    print(f"[SUCCESS] {action_msg} {target_file}")
    return True

def main() -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(BANNER)

    parser = argparse.ArgumentParser(description="Register PDS Logos-2 RAG KB for Codex / Claude Code.")
    parser.add_argument("--workspace", "-w", default=".", help="Target workspace path (default: current directory).")
    parser.add_argument("--python-bin", default=None, help="Explicit python executable path.")
    parser.add_argument("--mode", choices=["all", "agents_md", "codex_config"], default="all", help="Registration targets.")
    parser.add_argument("--test", action="store_true", help="Run diagnostic search test.")
    parser.add_argument("--dry-run", action="store_true", help="Preview modifications without saving.")
    args = parser.parse_args()

    search_script = (RAG_ROOT / "search.py").resolve()
    if not search_script.exists():
        print(f"[ERROR] search.py not found at {search_script}!")
        return 1

    python_bin = args.python_bin or detect_python()
    print(f"[*] RAG Root Directory : {RAG_ROOT}")
    print(f"[*] Search Script Path : {search_script}")
    print(f"[*] Python Executable  : {python_bin}")

    workspace = Path(args.workspace).resolve()
    print(f"[*] Target Workspace   : {workspace}")

    snippet = RULE_SNIPPET_TEMPLATE.format(
        python_bin=python_bin,
        search_script=str(search_script)
    )

    if args.test:
        test_rag_query(python_bin, search_script)

    if args.mode in ("all", "agents_md"):
        agents_md = workspace / "AGENTS.md"
        update_agents_md(agents_md, snippet, args.dry_run)

    if args.mode in ("all", "codex_config"):
        codex_dir = workspace / ".codex"
        codex_inst = codex_dir / "instructions.md"
        codex_text = CODEX_INSTRUCTIONS_TEMPLATE.format(
            python_bin=python_bin,
            search_script=str(search_script)
        )
        if args.dry_run:
            print(f"[DRY-RUN] Would create {codex_inst}")
        else:
            codex_dir.mkdir(parents=True, exist_ok=True)
            codex_inst.write_text(codex_text, encoding="utf-8")
            print(f"[SUCCESS] Wrote Codex instructions to {codex_inst}")

    print("\n" + "=" * 80)
    print("  Registration completed successfully! Codex is now armed with PDS RAG.")
    print("  Command format for Codex:")
    print(f'  & "{python_bin}" "{search_script}" "<keywords>" --top-k 3 --max-chars 800 --json')
    print("=" * 80 + "\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
