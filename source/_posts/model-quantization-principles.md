---
title: 模型量化原理：从单个权重到逐层推理
date: 2026-09-24 15:00:00
layout: post
permalink: /2026/09/24/model-quantization-principles/
description: 用图解、交互实验和公式理解大模型权重、激活与 KV Cache 量化，并估算推理时的存储与显存占用。
excerpt: '<p>用图解、交互实验和公式理解大模型权重、激活与 KV Cache 量化，并估算推理时的存储与显存占用。</p>'
categories: [arch-notes]
tags: [llm, quantization, inference]
---

{% quant_visual hero %}

量化是一次**有损编码**：把高精度张量映射到更少的可表示数值，同时尽量保持模型的输出行为。它首先是数值近似问题，然后才是文件压缩和内核加速问题。

{% quant_visual overview %}

<div id="encode" class="quant-anchor"></div>

## 01 · 一个浮点数如何变成低位整数

先看最简单的对称、按组量化。它是理解 GPTQ、AWQ 和 GGUF 块量化的起点。

对于一组浮点权重，先选缩放因子 `s`。每个权重 `w` 被映射成有限范围内的整数 `q`；需要用它计算时，再得到近似值 `ŵ`。例如 INT4 的对称表示可以用 −7 到 +7 的 15 个级别。下面的实验采用这个约定；实际格式的范围可能不同。

{% quant_visual encode_formula %}

`b` 是编码位数。非对称量化还会引入 zero-point；不同方法可能采用更复杂的缩放与误差补偿。位数越低，可选刻度越少。同组若出现极大的离群值，它会拉大 `s`，使其他小权重更容易被舍入到同一刻度。缩小分组有时能缓解这个问题，但每组都要额外保存 scale。

{% quant_visual lab %}

{% quant_visual output_formula %}

单个权重误差 `|W − Ŵ|` 很小，并不代表乘上实际输入 `X` 后的输出误差一定小。量化方法通常要考虑权重对层输出的影响，而不仅是文件里每个数字的偏差。

<div id="layer" class="quant-anchor"></div>

## 02 · 同一层里，并非每个张量都用同一种精度

下面以典型的 GQA + SwiGLU 解码层为例。具体模型仍需查看实际的 `config` 和张量清单。

{% quant_visual layer_map %}

{% quant_visual layer_notes %}

权重量化通常首先覆盖线性层的大矩阵，例如注意力投影与 MLP 投影。Embedding、Norm 和输出头是否量化，要看方案、模型敏感性和运行时支持。激活量化发生在推理计算路径中；KV Cache 则是历史 token 的注意力状态，需要单独决定精度。

<div id="methods" class="quant-anchor"></div>

## 03 · 算法在解决哪一种误差

“INT4”描述目标格式；“GPTQ / AWQ”描述怎样把原模型变成这个格式。

{% quant_visual method_grid %}

**INT8 与 FP8** 都占 8 bit，但编码方式不同。INT8 用整数级别配合 scale；FP8 把位数分给符号、指数和尾数，也通常结合 scale。两者对极端数值、误差和硬件的要求不同。<a href="#ref-schemes">[4]</a>

**GGUF 的 Q3_K** 是另一套权重块编码命名。单个 Q3_K 的 256 权重块有 3 bit 权重编码及分级 scale，合计约 3.4375 bit/权重；`Q3_K_M` 是模型级混合档位，平均位数还会更高。<a href="#ref-gguf">[5]</a>

<div id="runtime" class="quant-anchor"></div>

## 04 · 压缩权重如何参与一次推理

磁盘格式、显存中的布局、算子实际使用的数据类型，是三个不同层次。

{% quant_visual runtime_flow %}

**仅权重量化**不意味着推理时把整份权重永久还原成 BF16。高效内核通常在计算过程中处理编码和 scale。不过，解包和转换有代价，因此文件更小不保证每个 batch 都更快。W8A8 有机会直接使用低精度矩阵乘法硬件，实际收益取决于芯片、形状、batch 与内核。<a href="#ref-guide">[6]</a>

{% quant_visual runtime_formula %}

W/A 描述权重与激活；KV 描述历史注意力状态。三者可以组合，但要分别确认框架支持。

<div id="memory" class="quant-anchor"></div>

## 05 · 文件大小和显存，要分开算

先估权重，再估 KV，最后给运行时工作区留空间。

{% quant_visual memory_grid %}

{% quant_visual capacity_formula %}

{% quant_visual memory_calc %}

一个实测参照：llama.cpp 给出的 Llama 3.1 8B 文件大小约为 **F16 14.96 GiB**、**Q4_K_M 4.58 GiB**。这只是模型文件口径，不能直接当成加载后的总显存。vLLM 等服务框架还可能预分配 KV Cache，使“启动后已占用显存”大于当下请求真正使用的 KV 数据。<a href="#ref-llama">[7]</a><a href="#ref-vllm">[8]</a>

<div id="sources" class="quant-anchor"></div>

## 06 · 资料与口径

公式中的容量例子是按明确假设推导的教学示例；量化算法、格式和运行时描述依据下列原始论文或项目文档。

1. <span id="ref-gptq"></span>Frantar et al., [GPTQ: Accurate Post-Training Quantization](https://arxiv.org/abs/2210.17323), 2022.
2. <span id="ref-awq"></span>Lin et al., [AWQ: Activation-aware Weight Quantization](https://arxiv.org/abs/2306.00978), 2023.
3. <span id="ref-sq"></span>Xiao et al., [SmoothQuant](https://arxiv.org/abs/2211.10438), 2022.
4. <span id="ref-schemes"></span>vLLM Project, [LLM Compressor: Compression Schemes](https://docs.vllm.ai/projects/llm-compressor/en/latest/guides/compression_schemes/).
5. <span id="ref-gguf"></span>llama.cpp, [Tensor Encoding Schemes](https://github.com/ggml-org/llama.cpp/wiki/Tensor-Encoding-Schemes).
6. <span id="ref-guide"></span>vLLM Project, [Choosing the Right Compression Scheme](https://docs.vllm.ai/projects/llm-compressor/en/latest/steps/choosing-scheme/).
7. <span id="ref-llama"></span>llama.cpp, [Quantization README](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md), model-size table.
8. <span id="ref-vllm"></span>vLLM Project, [KV Cache configuration](https://docs.vllm.ai/en/latest/api/vllm/config/cache/).
