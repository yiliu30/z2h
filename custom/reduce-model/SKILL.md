---
name: reduce-model
description: Create a reduced (fewer-layer) version of a large HuggingFace model for fast testing and debugging. Use this skill whenever the user wants to reduce a model's layer count, create a small test model, download only part of a model's weights, debug quantization on a smaller model, speed up the testing-verification loop for large LLMs, or create a lightweight version of any HF model for rapid iteration. Trigger on phrases like "reduce model", "small test model", "fewer layers", "download partial model", "debug with smaller model", "shrink model for testing", even if the user doesn't use the exact term "reduce".
---

# Reduce Model

Create a reduced (fewer-layer) version of any HuggingFace model for fast end-to-end testing. The reduced model produces meaningless text but proves the full pipeline (download → load → generate) works with no runtime errors.

This is invaluable when working with large LLMs (hundreds of GB) where the testing-verification loop is painfully slow. Instead of downloading and loading the full model, you work with a 4-layer version that's a fraction of the size.

## When to Use This Skill

- User wants to test quantization workflows without waiting for the full model
- User needs a quick sanity check that a model loads and generates correctly
- User wants to reduce download size for development/debugging
- User mentions models like DeepSeek-R1, Qwen3, Llama, Mistral and needs a smaller version

## Workflow Overview

The process has 6 phases. Each phase builds on the previous one — don't skip ahead.

### Phase 1: Gather Information

Before writing any code, you need to understand the model and the environment.

**From the user, confirm:**
- The HuggingFace model ID (e.g., `Qwen/Qwen3-30B-A3B`)
- How many layers to keep (default: 4, which is enough for a smoke test)
- Where to save the reduced model (ask about available disk — models can be several GB even reduced)
- Whether to test on CPU or GPU (CPU is simpler and usually sufficient)

**From HuggingFace, fetch:**
1. The model card — to understand the architecture, any special loading requirements (`trust_remote_code`), and the minimum `transformers` version
2. `config.json` — to find `num_hidden_layers`, `model_type`, and architecture-specific fields. See `references/model-patterns.md` for common patterns across model families
3. `model.safetensors.index.json` — to map which layers live in which shard files. This is how you figure out what to download

**From the local environment, check:**
- Disk space at the target directory (`df -h`)
- Whether `hf` CLI is available (`which hf`)
- Whether a Python venv exists or needs to be created
- GPU availability if the user wants GPU testing (`nvidia-smi`)

### Phase 2: Create a Python Virtual Environment

The reduced model needs a working Python environment with the right packages. Use `uv` if available (faster), otherwise `python -m venv`.

```bash
uv venv .venv
source .venv/bin/activate
uv pip install "transformers>=<version-from-model-card>" torch safetensors accelerate
```

The `accelerate` package is easy to forget but required whenever you use `device_map` in `from_pretrained`. Install it upfront to avoid a confusing `ValueError` later.

The minimum `transformers` version matters — newer model architectures (like `qwen3_moe`) need recent transformers or you'll get a `KeyError` on the model type. Check the model card.

### Phase 3: Download Metadata Only

Download just the config, tokenizer, and index files — not the multi-GB weight files yet. This is the two-phase approach: get the metadata first, patch it, then download only the shards you actually need.

```bash
hf download <MODEL_ID> \
    --local-dir <OUTPUT_DIR> \
    --include "*.json" --include "*.txt" --include "*.model" --include "*.tiktoken"
```

For models that use `trust_remote_code=True` (like DeepSeek-R1), also download `*.py` files since they contain custom model code:

```bash
hf download <MODEL_ID> \
    --local-dir <OUTPUT_DIR> \
    --include "*.json" --include "*.txt" --include "*.model" --include "*.tiktoken" --include "*.py"
```

**Important gotcha:** Each glob pattern needs its own `--include` flag. Writing `--include "*.json" "*.txt"` silently downloads the wrong files. Always use `--include "*.json" --include "*.txt" --include ...`.

This typically downloads ~10-20MB: `config.json`, `generation_config.json`, `model.safetensors.index.json`, tokenizer files, and vocabulary files.

### Phase 4: Patch Config and Index

Write a Python script (`patch_model.py`) that modifies two files in-place:

**config.json:**
- Set `num_hidden_layers` to the target layer count (e.g., 48 → 4)
- Leave everything else unchanged — MoE config, attention heads, vocabulary size, etc. are all per-layer properties that don't depend on the total layer count

**model.safetensors.index.json:**
- Parse the `weight_map` dictionary
- Keep entries matching: `model.embed_tokens.*`, `model.layers.{0..N-1}.*`, `model.norm.*`, `lm_head.*`
- Remove all entries for layers ≥ N
- Leave `metadata.total_size` as-is (it's informational only, transformers ignores it)
- Don't rename shard files — transformers resolves files by the `weight_map`, not by filename numbering

The script should print the list of unique `.safetensors` filenames still referenced to stdout. The shell script captures this to know what to download next.

**Example output for Qwen3-30B-A3B with 4 layers:**
```
model-00001-of-00016.safetensors   # layers 0-1 + embeddings
model-00002-of-00016.safetensors   # layers 2-3
model-00016-of-00016.safetensors   # lm_head + model.norm
```

### Phase 5: Download Only Needed Shards

Using the shard list from Phase 4, download each file individually:

```bash
for shard in $SHARDS; do
    hf download <MODEL_ID> --local-dir <OUTPUT_DIR> --include "$shard"
done
```

This is where the big savings happen. For Qwen3-30B-A3B, this downloads ~8.7GB instead of ~60GB. The ratio depends on the model — models with more experts per layer have larger per-shard files.

### Phase 6: Smoke Test

Write a Python script (`test_generation.py`) that:

1. Loads the tokenizer from the reduced model directory
2. Loads the model with `torch_dtype="auto"`, `device_map="cpu"` (or `"auto"` for GPU), and `trust_remote_code=True` if the model card says so
3. Prepares a simple prompt like `"The capital of France is"` using `apply_chat_template`
4. Generates a small number of tokens (20 is enough)
5. Prints the output text and a `SUCCESS` marker

The output text will be meaningless from a 4-layer model — that's expected. The point is proving there are no runtime errors: no missing weights, no shape mismatches, no import failures.

**Model-specific considerations for the smoke test:**
- Some models support `enable_thinking` (like Qwen3) — set it to `False` for simpler output
- Some models need `trust_remote_code=True` — always check the model card
- "UNEXPECTED key" warnings during loading are normal and harmless — they come from shard files that contain weights for layers beyond your reduced set

### Orchestrator Script

Tie it all together with a shell script (`reduce.sh`) that runs phases 3-6 in sequence:

```bash
#!/bin/bash
set -euo pipefail

MODEL_ID="<model-id>"
OUTPUT_DIR="<output-dir>"
NUM_LAYERS=4
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Activate venv
source "$SCRIPT_DIR/.venv/bin/activate"

# Phase 3: Download metadata
hf download "$MODEL_ID" --local-dir "$OUTPUT_DIR" \
    --include "*.json" --include "*.txt" --include "*.model" --include "*.tiktoken"

# Phase 4: Patch
SHARDS=$(python "$SCRIPT_DIR/patch_model.py" --model-dir "$OUTPUT_DIR" --num-layers "$NUM_LAYERS")

# Phase 5: Download shards
for shard in $SHARDS; do
    hf download "$MODEL_ID" --local-dir "$OUTPUT_DIR" --include "$shard"
done

# Phase 6: Smoke test
python "$SCRIPT_DIR/test_generation.py" --model-dir "$OUTPUT_DIR"
```

## Verification Checklist

After the workflow completes, verify:

- [ ] Only the expected shard files are in the output directory (typically 2-4 files)
- [ ] `config.json` shows the reduced `num_hidden_layers` value
- [ ] `model.safetensors.index.json` has no entries for layers ≥ N
- [ ] The smoke test prints generated text and `SUCCESS`
- [ ] UNEXPECTED key warnings (if any) are for layers beyond the reduced set — these are harmless

## Common Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| `hf download` only fetches 1 file | Glob patterns space-separated after single `--include` | Use separate `--include` flags for each pattern |
| `ValueError: device_map requires accelerate` | `accelerate` package missing | `pip install accelerate` |
| `KeyError: '<model_type>'` | `transformers` version too old for this model | Upgrade to the version specified on the model card |
| `ImportError: cannot import name 'is_flash_attn_...'` | Model's custom code (e.g., DeepSeek-R1) incompatible with transformers 5.x | Use transformers 4.x (`pip install "transformers>=4.46,<5.0"`). Also download `*.py` files in Phase 3 for models with `trust_remote_code=True` |
| Shape mismatch errors during loading | Kept wrong layers or missed embedding/norm layers | Check `weight_map` filtering — must keep `embed_tokens`, `norm`, `lm_head` |
| Model generates nothing / hangs | Too few layers for the generation config | Set `max_new_tokens=20` explicitly; don't rely on model defaults |

## Reference Files

- `references/model-patterns.md` — Architecture patterns for common model families (dense vs MoE, layer naming conventions, which config fields to check). Read this when working with an unfamiliar model architecture.
