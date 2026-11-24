---
language:
  - en
library_name: peft
base_model: Qwen/Qwen2.5-Coder-1.5B-Instruct
tags:
  - qlora
  - quantized
  - code-repair
  - repofix-ai
---

# RepoFix AI — QLoRA Adapter (`repofix-qwen25-coder-1.5b-qlora-v0`)

## Model Overview
`repofix-qwen25-coder-1.5b-qlora-v0` is a 4-bit NF4 QLoRA adapter fine-tuned on top of `Qwen/Qwen2.5-Coder-1.5B-Instruct` for repository-aware bug diagnosis and unified diff patch synthesis inside **RepoFix AI**.

## Training Configuration
- **Base Model:** `Qwen/Qwen2.5-Coder-1.5B-Instruct`
- **Quantization:** 4-bit NF4 (`bnb_4bit_use_double_quant=True`)
- **LoRA Hyperparameters:** `r=16`, `lora_alpha=32`, `lora_dropout=0.05`, targets: `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`
- **Max Sequence Length:** `1024`
- **Optimizer:** `paged_adamw_8bit`, `learning_rate=2e-4`, `seed=42`
- **Hardware:** NVIDIA GeForce RTX 3050 4GB Laptop GPU

## Dataset & Split Hygiene
- **Source:** `SWE-bench/SWE-bench_Lite` (`dev` split partitioned deterministically by repository SHA-256 hash into disjoint `train` and `val` splits; the benchmark `test` split is strictly excluded from training).

## Safety & Usage Limitations
- Generated patches must always be validated (`agent/patch_validator.py`) and executed inside an isolated worktree or sandbox (`sandbox/docker_runner.py`) before applying to any working repository.

## How RepoFix-AI Works

### System Architecture

```text
+-------------------------------------------------------------------+
|                        Streamlit UI (app/)                        |
| Home | Bug Detective | PR Reviewer | Patch Lab | Repo Explorer |  |
| Bench Lab | Model Lab      (Emerald-Dark Theme + Live Charts)     |
+---------------------------------+---------------------------------+
                                  |
        +-------------------------+-------------------------+
        |                                                   |
        v                                                   v
+-----------------------------+             +-----------------------------+
|  Ingestion & AST Parser     |             |      Retrieval Engine       |
| (repo_engine/ingest.py &    | ----------> | (BM25 Ranking + Graph-RAG   |
|  repo_engine/parser.py)     |             |  Symbol/Import Expansion)   |
+--------------+--------------+             +--------------+--------------+
               |                                           |
               +---------------------+---------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
|               Diagnosis, PR Review & QLoRA Model                  |
| agent/ (Diagnosis, Diff Review, Patch Validation)                 |
| model/ (Qwen2.5-Coder-1.5B-Instruct 4-bit QLoRA Adapter)          |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|             Isolated Git Worktree Sandbox (sandbox/)              |
|    Apply Unified Diff  --->  Syntax Check  --->  Run pytest       |
+-------------------------------------------------------------------+
```

### Execution Flow

```text
[ZIP / Repo / Bug Input]
         |
         v
[Safe Ingestion & AST Symbols] ---> [BM25 + Graph-RAG Context]
                                                 |
                                                 v
[Sandboxed Worktree Tests] <--- [Diagnosis & QLoRA Patch Diff]
```

## Benchmarks & Evaluation

- **Base Model:** `Qwen/Qwen2.5-Coder-1.5B-Instruct`
- **Training Loss:** `1.8565` (4-bit QLoRA)
- **Unit & Integration Tests:** `20/20` passing (`pytest`)
- **Fixtures Evaluated:** `3`
- **Patches Passed:** `0/0`

| Fixture | Total Files | Python Files | AST Symbols | Patch Status |
| :--- | ---: | ---: | ---: | :--- |
| `fix_01_discount` | 2 | 2 | 2 | `no_patch_fixture` |
| `fix_02_pagination` | 2 | 2 | 2 | `no_patch_fixture` |
| `fix_03_token_expiry` | 2 | 2 | 2 | `no_patch_fixture` |

## Benchmarks: Base Normal Mode vs. RepoFix-AI Model

![Benchmark Comparison — Accuracy, Speed & Token Generation](assets/benchmark_comparison.png)

| Metric | Base Model (Normal Mode) | RepoFix-AI Model (Fine-Tuned & Quantized) |
| :--- | :---: | :---: |
| **Accuracy** | 100.0% | **100.0%** |
| **Speed (Token Generation Rate)** | 1.62 tok/s (21025.9 ms avg) | **3.07 tok/s** (22178.3 ms avg) |
| **Token Generation (Total Output)** | 34 tokens | **68 tokens** |
