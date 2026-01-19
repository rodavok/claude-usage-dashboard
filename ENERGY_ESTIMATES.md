# Energy Consumption Estimates for LLM Inference

This document records the research and methodology behind the energy consumption estimates used in this dashboard.

## Summary of Estimates Used

| Model Tier | J/token | Wh/1K tokens | Rationale |
|------------|---------|--------------|-----------|
| Haiku      | 0.75    | 0.00021      | Small, fast model - range 0.5-1.0 J |
| Sonnet     | 3.0     | 0.00083      | Mid-tier, similar to GPT-4o estimates - range 2-4 J |
| Opus       | 11.5    | 0.0032       | Large model, based on ~4 Wh/query reports - range 8-15 J |

Default PUE (Power Usage Effectiveness) multiplier: **1.4** (accounts for cooling, networking overhead)

## Research Sources

### Primary Sources

1. **Muxup - Per-query energy consumption of LLMs** (2026)
   - https://muxup.com/2026q1/per-query-energy-consumption-of-llms
   - Measured Llama3-70B at ~0.39 J/token on H100 with FP8 quantization
   - DeepSeek-R1-0528: 0.96-3.74 Wh/query (8k input/1k output)

2. **TokenPowerBench (arXiv 2512.03024)** (December 2025)
   - https://arxiv.org/html/2512.03024v1
   - 32,500+ measurements across 21 GPU configurations and 155 model architectures
   - Key findings:
     - 70B parameters = ~7.3x energy vs 1B (not linear with params)
     - MoE architectures 2-3x more efficient than dense equivalents
     - Context doubling (2K->10K) increases per-token energy by ~3x
     - FP8 quantization reduces energy ~30%

3. **From Prompts to Power (arXiv 2511.05597)** (November 2025)
   - https://arxiv.org/html/2511.05597
   - OPT-30B on A100: 0.0137 Wh (short), 0.3 Wh (long output)
   - **Output tokens cost ~11x more** than input tokens

4. **LLM Tracker - Power Usage and Energy Efficiency**
   - https://llm-tracker.info/_TOORG/Power-Usage-and-Energy-Efficiency
   - Historical comparison:
     - GPT-3 baseline (pre-2023): ~48 J/token
     - Llama-65B (V100/A100): ~3.5 J/token
     - Llama3-70B (H100, FP8): ~0.39 J/token
     - Enterprise DGX H100 w/ overhead: ~120 J/token
   - Shows ~120x efficiency improvement from 2023 to 2025

### Claude-Specific Data

- **Claude 3 Opus**: ~4.05 Wh/query reported (one of highest among public models)
- **Claude 3.7 Sonnet**: considered "most eco-efficient" among tested frontier models
- **General modern LLMs**: 0.2-0.3 Wh for typical 300-500 token interactions

Anthropic does not publish official energy consumption figures. Pricing tiers suggest:
- Opus is ~60x more expensive than Haiku per token
- This correlates with but doesn't directly map to energy consumption

## Key Variables Affecting Energy

1. **Output vs Input tokens**: Output tokens ~11x more energy-intensive
2. **Context length**: Doubling context increases per-token energy ~3x
3. **Hardware**: H100 is ~10x more efficient than V100
4. **Quantization**: FP8 reduces energy ~30% vs FP16
5. **Batch size**: Higher batching improves efficiency
6. **MoE architecture**: 2-3x more efficient than dense models of equivalent quality

## Important Caveats

- **These are server-side only estimates** - excludes network, user device, data center cooling
- **Real-world variance is 10-100x** based on infrastructure efficiency
- **Cached/prompt-cached tokens** use ~10% of normal energy
- Anthropic doesn't publish official figures; these are educated estimates
- Energy efficiency improves rapidly - estimates may be outdated within months

## Calculation Method

```
Energy (Wh) = tokens * j_per_token * PUE / 3600

Where:
- j_per_token: Joules per token for model tier
- PUE: Power Usage Effectiveness (default 1.4)
- 3600: Joules per Watt-hour
```

## Equivalence References

- 1 phone charge: ~12 Wh
- 10W LED bulb for 1 hour: 10 Wh
- 1 kWh = 1000 Wh
- Average US household daily usage: ~30 kWh

## Future Updates

Energy efficiency for LLM inference is improving rapidly. Key trends to monitor:
- New GPU architectures (Blackwell B200/B300 claim 50x improvement)
- Improved quantization (FP4 emerging)
- Better inference frameworks (vLLM, TensorRT-LLM)
- MoE adoption

Consider re-researching estimates every 6-12 months as the field evolves.
