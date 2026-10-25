# Pango PDS & Logos-2 FPGA RAG Knowledge Base Toolkit (v1.0)

[![Release](https://img.shields.io/badge/Release-v1.0-blue.svg)](https://github.com/chippareyner-glitch/pds-logos2-rag-toolkit/releases/tag/v1.0)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-green.svg)](https://python.org)
[![VectorDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange.svg)](https://docs.trychroma.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-lightgrey.svg)](LICENSE)

专为 **紫光同创（Pango Micro）Logos-2（PG2L200H）FPGA、Pango Design Suite（PDS 2022.2-SP6.4）EDA 全流程、大模型端侧加速器（LLM Accelerator）、脉动阵列微架构与时序收敛（STA）** 打造的高精度本地 RAG 知识库与切片检索工具箱。

涵盖 **14 本官方权威参考手册与学术前沿论文**，并内置生产级 **Token-Aware 物理切片算法**、**Dense+BM25 双路混合检索引擎** 以及 **Codex / Claude Code 一键注册器**。

---

## 🌟 核心特性

- 🎯 **权威对齐（严禁凭空臆造）**：
  严格基于 PDS 2022.2-SP6.4 官方手册（包括 Pango Design Suite、ADS 综合、物理约束、时序分析 Timing Analyzer、Design Editor、IP Compiler）与芯片手册，标注对应官方手册名称与物理页码。绝不混淆 Xilinx Vivado 与 PDS 专属指令（例如位流生成严格使用 `gen_bit_stream -scbv high_voltage`，布线拥塞消减参数为 `-plc_decongestion <0-9>`）。
- ⚡ **Token-Aware 智能切片与指纹去重**：
  采用底层 Tokenizer 真实偏移映射（Offset Mapping）分块，杜绝乱码与公式/端口名截断。基于 SHA-256 内容散列，支持毫秒级增量检测。
- 🔍 **Dense + Sparse 多路混合检索（Hybrid Retrieval）**：
  结合 `intfloat/multilingual-e5-small` 稠密语义向量（权重 0.6）与 BM25 精准技术词召回（权重 0.4），采用倒数排名融合（RRF）重排，无论是查错误代码（如 `Place-0084`、`Route-2036`、`Flow-0009`）还是概念原语（`GTP_CLKBUFG`、`PAP_CLOCK_DEDICATED_ROUTE`、`FlightLLM DSP Cascade`），均可实现 Top-1 精准召回。
- 🤖 **一键注册给 Codex & Claude Code**：
  内置 `register_codex.py` 自动化注册脚本，一行命令即可为任意 FPGA 工程注入 Codex 提示词规范与 `AGENTS.md` 约束规则。

---

## 📂 项目结构

```text
pds-logos2-rag-toolkit/
├── search.py                  # 双路混合检索 CLI / JSON 输出（供 Codex/Claude 自动化调用）
├── register_codex.py          # Codex / Claude Code 一键注册脚本
├── build_index.py             # 向量索引构建器（支持增量更新、SHA256 去重）
├── rag_common.py              # 分词模型配置、Token-Aware 切片核心与 ChromaDB 连接
├── download_documents.py      # 官方手册与前沿论文 Release 资源自动下载器
├── DOCUMENTS_INDEX.md         # 14 本官方手册、硬件规格书与学术论文目录清单
├── SHA256SUMS.txt             # 所有文档及 Release 压缩包的完整性校验哈希
├── requirements.txt           # 基础运行依赖（chromadb, sentence-transformers, pymupdf 等）
├── documents/                 # 文档与语料目录
│   ├── practical_corpus/      # 实战工程语料（PDS 报错代码速查、底层原语调用规范等）
│   ├── academic_papers/       # 学术加速器论文精选（FlightLLM, AutoBridge, LATCH 等）
│   ├── pango_projects/        # 真实工程参考（RISC-V+NPU 异构 SoC, 脉动阵列实测等）
│   ├── pds_manuals/           # PDS 2022.2-SP6.4 官方 EDA 用户手册（从 Release 下载）
│   └── hardware/              # Logos-2 PG2L200H / 盘古 200Pro+ 硬件规格书（从 Release 下载）
└── database/                  # ChromaDB 本地持久化向量数据库（由 build_index.py 生成）
```

---

## 🚀 快速上手

### 1. 安装依赖

```bash
git clone https://github.com/chippareyner-glitch/pds-logos2-rag-toolkit.git
cd pds-logos2-rag-toolkit

pip install -r requirements.txt
```

### 2. 下载官方手册与学术论文（Release 资源）

官方 14 本原厂 PDF 与前沿论文已打包为 Release 压缩包 `pango_pds_logos2_knowledgebase_v1.0.zip`。运行以下脚本自动完成下载、校验与解压：

```bash
python download_documents.py
```

### 3. 构建向量索引

```bash
python build_index.py
```
> [!NOTE]
> 索引构建支持增量模式。若后续修改了语料或加入了新文档，直接再次运行 `python build_index.py` 即可自动增量索引。

### 4. 检索知识库

- **人机交互模式（彩色直观输出）**：
  ```bash
  python search.py "Route-2036 解决办法" --top-k 3
  ```

- **机器/AI 结构化读取模式（JSON 输出，含来源与页码）**：
  ```bash
  python search.py "PAP_CLOCK_DEDICATED_ROUTE" --top-k 3 --json
  ```

---

## 🦾 一键注册给 Codex & Claude Code

为了让 AI 编程助手（Codex、Claude Code、Cursor 等）在你的 FPGA 工程中具备紫光同创与 PDS 领域知识，直接在本项目中运行 `register_codex.py`：

```bash
# 为指定的 FPGA 工作区注册（例如 D:\Pangu）
python register_codex.py --workspace "D:\Pangu" --test
```

### 注册后生效的能力：
1. **自动生成/更新 `AGENTS.md`**：写入严密的多 Agent 协作规范与 RAG 检索规则，防止 AI 臆造 Vivado 命令。
2. **生成 `.codex/instructions.md`**：为 Codex 扩展直接提供系统提示词，在遇到 `.fdc` 约束修改、STA 报错或原语调用时自动执行 RAG。
3. **真实环境诊断**：自带 `--test` 机制，自测 Python 虚拟环境与向量检索引擎连通性。

---

## 📚 收录文档清单概览

详见完整目录文档：[DOCUMENTS_INDEX.md](DOCUMENTS_INDEX.md)。

| 分类 | 代表文档 / 论文 | 核心价值 |
| :--- | :--- | :--- |
| **EDA 手册** | `Pango_Design_Suite_User_Guide.pdf`<br>`Timing_Analyzer_User_Guide.pdf`<br>`Physical_Constraint_Editor_User_Guide.pdf` | PDS Tcl 流程控制、STA 静态时序分析、Pblock 区域锁定与物理约束 |
| **硬件规格** | `DS04001_Logos2系列FPGA器件数据手册.pdf`<br>`MES2L676-200HP硬件使用手册_v1.2.pdf`<br>`UG042003_HMIC_S_IP.pdf` | PG2L200H 芯片底层 CLM 架构、DDR3 硬核控制器 `HMIC_S` 协议与引脚分布 |
| **学术前沿** | `FlightLLM` (ACM FPGA 2024)<br>`AutoBridge` (ACM FPGA 2021)<br>`RapidStream IR` (2024)<br>`LATCH` (2026) | 大模型端侧稀疏 DSP 级联计算、粗粒度 Floorplanning、锚点寄存器、后布线时序修复 |
| **实战语料** | `pds_logos2_pnr_sta_chunks.jsonl`<br>`pango_projects_extracted.jsonl` | `Place-0084`/`Route-2036`/`Flow-0009` 排错手册、16x16 脉动阵列部署对比、异构 SoC 总线仲裁 |

---

## 📄 许可证

本项目采用 [Apache License 2.0](LICENSE) 开源协议。
官方手册版权归属于紫光同创微电子（Pango Micro），论文版权归属于各学术会议及作者。
