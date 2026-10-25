# Pango PDS & Logos-2 Documentation & Academic Papers Index

This directory index categorizes all official reference manuals, hardware user guides, academic research papers, and curated engineering project corpora integrated into the **PDS Logos-2 RAG Knowledge Base**.

All original PDF files are packaged into the release archive `pango_pds_logos2_knowledgebase_v1.0.zip` available on [GitHub Releases v1.0](https://github.com/chippareyner-glitch/pds-logos2-rag-toolkit/releases/tag/v1.0).

---

## 1. PDS 2022.2-SP6.4 Official EDA Manuals (`documents/pds_manuals/`)

| File Name | Size | Version | Key Coverage & EDA Stage |
| :--- | :--- | :--- | :--- |
| `Pango_Design_Suite_User_Guide.pdf` | 8.58 MB | 2022.2-SP6.4 | 全流程主指南：工程创建、Flow 自动化、`pds_shell` Tcl 批处理、`dev_map`、`-plc_decongestion`、`gen_bit_stream` (Page 115, 167, 251) |
| `ADS_Synthesis_User_Guide.pdf` | 3.59 MB | 2022.2-SP6.4 | ADS 逻辑综合引擎、FSM 状态机编码、保留层次结构、跨层次优化与资源推断 |
| `User_Constraint_Editor_User_Guide.pdf` | 8.32 MB | 2022.2-SP6.4 | `.fdc` 约束语法详解、时钟与 I/O 延迟约束、多周期路径、时序例化属性 |
| `Physical_Constraint_Editor_User_Guide.pdf` | 8.28 MB | 2022.2-SP6.4 | 物理布局约束、Pblock 区域锁定、`PAP_LOC`、DSP/BRAM 紧密列排列与时序收敛 |
| `Route_Constraint_Editor_User_Guide.pdf` | 1.36 MB | 2022.2-SP6.4 | 物理布线约束、布线拥塞度消除、关键时钟专属走线与差分阻抗控制 |
| `Timing_Analyzer_User_Guide.pdf` | 3.35 MB | 2022.2-SP6.4 | 静态时序分析 (STA)、免重跑直接分析、Setup/Hold 时序违例定位与关键路径时钟歪斜计算 |
| `Design_Editor_User_Guide.pdf` | 3.91 MB | 2022.2-SP6.4 | 交互式布局布线设计器、局部拆线重布（Rip-up and Re-route）、网表微调与手动修违例 |
| `IP_Compiler_User_Guide.pdf` | 2.41 MB | 2022.2-SP6.4 | IP 核例化编译器：PLL/GPLL、DDR3 HMIC_S、FIFO、RAMB 宏模块配置向导 |

---

## 2. Logos-2 Hardware & IP Specifications (`documents/hardware/`)

| File Name | Size | Key Coverage |
| :--- | :--- | :--- |
| `DS04001_Logos2系列FPGA器件数据手册.pdf` | 0.75 MB | PG2L200H 芯片底层架构、CLMA/CLMS 控制集规则、LUT/FF 分布、DSP APM 算力单元规格 |
| `MES2L676-200HP硬件使用手册_v1.2.pdf` | 2.24 MB | 盘古 200Pro+ 评估板原理图说明、676 引脚分配、DDR3 接口拓扑、电源时序与外设定义 |
| `UG042003_HMIC_S_IP.pdf` | 1.42 MB | DDR3 硬核内存控制器 (`HMIC_S`) 原理、AXI 总线接口协议、仲裁配置与时序放宽原则 |
| `02_PDS快速使用手册.pdf` | 4.37 MB | 快速上手实验、从空白工程到实板 JTAG 烧录与调试流程 |

---

## 3. Academic LLM & Systolic Array Papers (`documents/academic_papers/`)

| Paper ID | Title & Publication | Tags | Extracted Focus |
| :--- | :--- | :--- | :--- |
| `PAPER-FLIGHTLLM-2024` | **FlightLLM**: Efficient Large Language Model Inference on FPGAs (ACM FPGA 2024) | LLM, Qwen_NPU, DSP_Cascade, APM, DRM | 稀疏 DSP 级联链设计、Logos-2 APM 原语映射、片上权重解压与多级存储层次构建 |
| `PAPER-AUTOBRIDGE-2021` | **AutoBridge**: Coupling Coarse-Grained Floorplanning and Pipelining (ACM FPGA 2021) | Floorplanning, Pblock, Pipelining, Congestion | 粗粒度岛屿布局划分、跨 SLR/超长走线 Latency-Insensitive FIFO 打拍插桩、DDR 控制器隔离 |
| `PAPER-RAPIDSTREAM-2024` | **RapidStream IR**: Infrastructure for FPGA Physical Synthesis (arXiv 2024) | Physical_Synthesis, Anchor_Registers, PnR | 锚点寄存器（Anchor Registers）物理插桩、大型数据流流水线与大模型加速器物理切分 |
| `PAPER-LATCH-2026` | **LATCH**: LLM-Assisted Timing Closure Harness for Post-Route FPGA Designs | LLM_Timing_Closure, Post_Route, STA | 后布线阶段自动化修复时序违例、STA 报文智能提取与约束动态重构 |
| `PAPER-FPGA-LLM-CODESIGN-2025` | **An FPGA Co-design of Large Language Model Inference Accelerator** | LLM_Accelerator, Transformer, Non_Linear | Transformer 前向计算图算子融合、Non-linear 激活函数查找表化、分块 Tiling 策略 |
| `PAPER-SSR-TRANSFORMER-2024` | **SSR**: Spatial Sequential Hybrid Architecture for Transformer Acceleration | Systolic_Array, Routability, Congestion | 空间流水与时序复用混合架构、布线拥塞度消除与高吞吐阵列折叠 |
| `PAPER-SYSTOLIC-PNR-2023` | **Place-and-Route Analysis of Nested Systolic Arrays on FPGAs** | Systolic_Array, PnR_Analysis, DSP_Alignment | 嵌套脉动阵列布局布线深度分析、DSP 列对齐、控制集（Control Sets）合并消减布线阻塞 |

---

## 4. Curated Practical Corpora (`documents/practical_corpus/` & `documents/pango_projects/`)

- `practical_corpus/pds_logos2_pnr_sta_chunks.jsonl`:
  - **PDS 权威报错代码与修复方案**：`Place-0084`（跨时钟域驱动违规）、`Route-2036`（时钟走线占用通用 Fabric 资源）、`Flow-0009`（内存不足 / OOM 崩溃）、`Flow-0189`（I/O 属性缺失）。
  - **Logos-2 芯片专用原语调用指南**：`GTP_CLKBUFG`、`GTP_INBUFGDS`、`GTP_APM_E2`、`GTP_DRM36K`、`CLMA`、`CLMS` 控制集。
  - **PDS 物理优化策略**：`-plc_decongestion <0-9>` 模式详解、STA 静态时序分析技巧、Design Editor 局部拆线重布。
- `pango_projects/pango_projects_extracted.jsonl`:
  - **PG2L RISC-V + NPU 异构 SoC 实战**：AXI 总线仲裁、双时钟域跨时钟桥接、时序收敛要点。
  - **16x16 脉动阵列在紫光同创与 Xilinx 双平台对比**：APM 级联布线对齐、资源占用对比。
  - **YOLOv2 CNN 视觉加速工程实践**：Ping-Pong 缓存、DDR3 DMA 猝发读写状态机。
  - **开源 RISC-V 处理器 PDS 工程与 FDC 约束参考**：JerryYin777 盘古工程结构与引脚约束规范。
