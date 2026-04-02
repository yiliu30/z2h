# Model Architecture Patterns

Quick reference for how different model families structure their layers, which config fields matter, and what to watch out for when reducing them.

## Table of Contents

1. [Dense Transformer Models](#dense-transformer-models)
2. [Mixture-of-Experts (MoE) Models](#mixture-of-experts-moe-models)
3. [Mixed Dense + MoE Models](#mixed-dense--moe-models)
4. [Config Field Reference](#config-field-reference)
5. [Shard Layout Patterns](#shard-layout-patterns)
6. [Known Gotchas by Model Family](#known-gotchas-by-model-family)

---

## Dense Transformer Models

**Examples:** Llama 3, Llama 2, Mistral 7B, Gemma, Phi-3, Qwen2

**Layer structure:** All layers are identical dense transformer blocks with self-attention + MLP.

**Weight pattern per layer:**
```
model.layers.{i}.self_attn.q_proj.weight
model.layers.{i}.self_attn.k_proj.weight
model.layers.{i}.self_attn.v_proj.weight
model.layers.{i}.self_attn.o_proj.weight
model.layers.{i}.mlp.gate_proj.weight
model.layers.{i}.mlp.up_proj.weight
model.layers.{i}.mlp.down_proj.weight
model.layers.{i}.input_layernorm.weight
model.layers.{i}.post_attention_layernorm.weight
```

**Reduction notes:** Straightforward — any contiguous slice of layers works. Keeping the first N layers is standard. Shard files are typically smaller per layer since there are no expert weights.

---

## Mixture-of-Experts (MoE) Models

**Examples:** Qwen3-30B-A3B, Qwen2.5-MoE, Mixtral 8x7B, DBRX

**Layer structure:** Every layer has a router + multiple experts. Only a subset of experts activates per token.

**Weight pattern per layer (Qwen3 MoE style):**
```
model.layers.{i}.self_attn.q_proj.weight
model.layers.{i}.self_attn.k_proj.weight
model.layers.{i}.self_attn.v_proj.weight
model.layers.{i}.self_attn.o_proj.weight
model.layers.{i}.mlp.gate.weight                    # router
model.layers.{i}.mlp.experts.{j}.gate_proj.weight   # j = 0..num_experts-1
model.layers.{i}.mlp.experts.{j}.up_proj.weight
model.layers.{i}.mlp.experts.{j}.down_proj.weight
model.layers.{i}.input_layernorm.weight
model.layers.{i}.post_attention_layernorm.weight
```

**Key config fields:**
- `num_experts`: total expert count (e.g., 128 for Qwen3-30B-A3B)
- `num_experts_per_tok`: active experts per token (e.g., 8)
- `decoder_sparse_step`: which layers are MoE (1 = all layers, 2 = every other layer)

**Reduction notes:** MoE layers have many more weight entries per layer (num_experts × 3 projections). A 4-layer MoE model still has thousands of weight entries. Shard files are also much larger — each shard covers fewer layers.

---

## Mixed Dense + MoE Models

**Examples:** DeepSeek-R1, DeepSeek-V3, DeepSeek-MoE

**Layer structure:** First few layers are dense, remaining layers are MoE. This is controlled by `first_k_dense_replace` or similar config fields.

**Example (DeepSeek-R1):** 61 total layers, first 3 are dense, layers 3-60 are MoE.

**Reduction notes:** When choosing how many layers to keep, try to include at least one MoE layer to exercise the full architecture. For DeepSeek-R1 with `first_k_dense_replace=3`, keeping 4 layers gives you 3 dense + 1 MoE.

**Key config fields (DeepSeek-specific):**
- `first_k_dense_replace`: number of initial dense layers
- `n_routed_experts`: number of routed experts
- `num_experts_per_tok`: active experts per token
- `n_shared_experts`: shared experts (always active, in addition to routed ones)

---

## Config Field Reference

Fields to check in `config.json` when reducing a model:

| Field | What it controls | Action |
|-------|-----------------|--------|
| `num_hidden_layers` | Total layer count | **Change this** to the target |
| `model_type` | Architecture class | Don't change; verify transformers supports it |
| `num_attention_heads` | Q heads per layer | Don't change |
| `num_key_value_heads` | KV heads (GQA) | Don't change |
| `hidden_size` | Model dimension | Don't change |
| `intermediate_size` | MLP dimension | Don't change |
| `num_experts` | Expert count (MoE) | Don't change |
| `num_experts_per_tok` | Active experts (MoE) | Don't change |
| `decoder_sparse_step` | MoE layer frequency | Don't change |
| `max_window_layers` | Sliding window depth | May need capping if > num_hidden_layers |
| `tie_word_embeddings` | Whether embed/lm_head share weights | Don't change; affects which shards to download |

---

## Shard Layout Patterns

HuggingFace models shard weights across multiple `.safetensors` files. The mapping is in `model.safetensors.index.json`.

**Typical layout:**
- Shard 1: `model.embed_tokens` + first few layers
- Middle shards: 2-3 layers each
- Last shard: final layers + `model.norm` + `lm_head`

**What you always need to download:**
1. The shard containing `model.embed_tokens.weight`
2. Shards containing layers 0 through N-1
3. The shard containing `model.norm.weight` and `lm_head.weight`

**Don't rename shards.** Transformers resolves weight files by the `weight_map` in the index JSON, not by filename numbering. A file named `model-00001-of-00016.safetensors` works fine even if you only have 3 of the 16 shards.

**UNEXPECTED key warnings** are normal: if shard 2 contains layers 2-5 but you only need layers 2-3, transformers loads layers 2-3 and prints warnings about the unexpected layers 4-5 keys. These warnings are harmless.

---

## Known Gotchas by Model Family

### Qwen3 (MoE)
- Model type: `qwen3_moe`
- Requires `transformers >= 4.51.0` (older versions: `KeyError: 'qwen3_moe'`)
- `trust_remote_code=True` recommended
- Supports `enable_thinking` in chat template — set to `False` for smoke tests

### DeepSeek-R1 / V3
- Model type: `deepseek_v3` or similar
- Often requires `trust_remote_code=True`
- Mixed dense + MoE — check `first_k_dense_replace`
- Very large model (671B) — even reduced versions may be substantial

### Llama 3 / 3.1 / 3.2
- Model type: `llama`
- Well-supported in transformers, usually no special flags needed
- Dense architecture — straightforward reduction
- `trust_remote_code` typically not needed

### Mistral / Mixtral
- Mistral 7B: dense, model type `mistral`
- Mixtral 8x7B: MoE, model type `mixtral`
- Both well-supported in recent transformers

### Phi-3 / Phi-4
- May need `trust_remote_code=True`
- Check for custom attention implementations

### Gemma / Gemma 2
- Model type: `gemma` or `gemma2`
- Well-supported, usually no special flags
