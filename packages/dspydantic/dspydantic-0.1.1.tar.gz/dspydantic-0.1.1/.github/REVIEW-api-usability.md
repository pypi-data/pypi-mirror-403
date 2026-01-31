# DSPydantic API Review: Usability & Production Readiness

**Review Date:** 2026-01-29
**Compared Against:** [LangStruct](https://langstruct.dev/), [LangExtract](https://github.com/google/langextract), [DSPy](https://dspy.ai/)

## Executive Summary

DSPydantic provides a solid foundation for optimizing Pydantic models with DSPy. Major improvements implemented:

### ✅ Implemented (2026-01-29)

| Issue | Feature | Status |
|-------|---------|--------|
| 1-2 | `run()` alias for `predict()` | ✅ |
| 3 | `model_id` parameter for simplified DSPy config | ✅ |
| 4 | `predict()` works without `optimize()` | ✅ |
| 5 | Confidence scores (`predict_with_confidence()`) | ✅ |
| 7 | Batch processing (`predict_batch()`) | ✅ |
| 8 | Async support (`apredict()`, `apredict_batch()`) | ✅ |
| 9 | Request caching (`cache=True`) | ✅ |
| 11 | Improved error messages | ✅ |
| 14 | Cost tracking (`result.api_calls`, `result.total_tokens`) | ✅ |

### Remaining Items

1. **Production features** - Rate limiting, streaming
2. **Competitive features** - Source grounding (citation support)

---

## Issue 1: Documentation Shows `run()` But Method Is `predict()`

**Labels:** `bug`, `documentation`, `high-priority`

**Description:**
The main documentation (`docs/index.md`) shows:
```python
data = prompter.run("JPMorgan executed $500K bond purchase...")
```

But the actual method in `prompter.py` is `predict()`. This breaks user code.

**Acceptance Criteria:**
- [ ] Either rename `predict()` to `run()` (shorter, more intuitive)
- [ ] Or update all documentation to use `predict()`
- [ ] Add deprecation alias if renaming

---

## Issue 2: Add `run()` Alias for `predict()` Method

**Labels:** `enhancement`, `api`

**Description:**
The name `run()` is more intuitive than `predict()` for an extraction task. LangExtract uses `extract()`, LangStruct uses `extract()`. Consider:
- `run()` - Simple, action-oriented
- `extract()` - Matches competitor APIs  
- `predict()` - DSPy terminology but less intuitive for extraction

**Acceptance Criteria:**
- [ ] Add `run()` as an alias for `predict()`
- [ ] Consider adding `extract()` as well for API compatibility
- [ ] Update documentation to prefer the shorter name

---

## Issue 3: Simplify DSPy Configuration with `model_id` Parameter

**Labels:** `enhancement`, `api`, `usability`

**Description:**
Currently users must:
```python
import dspy
lm = dspy.LM("openai/gpt-4o", api_key="...")
dspy.configure(lm=lm)

prompter = Prompter(model=MyModel)
```

This should be simplifiable to:
```python
prompter = Prompter(model=MyModel, model_id="openai/gpt-4o")
```

The Prompter class already has docs mentioning `model_id` but it's not implemented.

**Acceptance Criteria:**
- [ ] Add `model_id` and `api_key` parameters to `Prompter.__init__()`
- [ ] Auto-configure DSPy if `model_id` is provided
- [ ] Fall back to existing `dspy.settings.lm` if not provided
- [ ] Update documentation examples

---

## Issue 4: Add Quick Extraction Without Optimization

**Labels:** `enhancement`, `api`

**Description:**
For users who just want structured extraction without optimization, provide a simpler path:

```python
# Current: Requires optimization
prompter = Prompter(model=MyModel)
result = prompter.optimize(examples)  # Required even for basic use
data = prompter.predict(text)

# Proposed: Direct extraction
prompter = Prompter(model=MyModel)
data = prompter.predict(text)  # Works without optimization
```

**Acceptance Criteria:**
- [ ] Allow `predict()` to work without prior `optimize()` call
- [ ] Use original field descriptions if not optimized
- [ ] Add `Extractor` class as lightweight alternative (no optimization)

---

## Issue 5: Add Confidence Scores to Extraction Output

**Labels:** `enhancement`, `feature`

**Description:**
LangStruct provides confidence scores for extractions. DSPydantic should too.

```python
result = prompter.predict(text)
print(result.confidence)  # 0.95
print(result.field_confidences)  # {"name": 0.99, "age": 0.85}
```

**Acceptance Criteria:**
- [ ] Add confidence scoring to extraction output
- [ ] Per-field confidence scores
- [ ] Option to enable/disable (off by default for speed)

---

## Issue 6: Add Source Grounding (Citation Support)

**Labels:** `enhancement`, `feature`, `competitive`

**Description:**
LangExtract's main differentiator is character-level source tracking:
```python
result = extractor.extract(text)
print(result.sources)
# {"name": [CharSpan(0, 8, "John Doe")], ...}
```

This is valuable for:
- Compliance (audit trail)
- Debugging extraction errors
- RAG applications (citations)

**Acceptance Criteria:**
- [ ] Add optional source grounding to `predict()`
- [ ] Return character spans for each extracted value
- [ ] Add `sources` attribute to extraction result

---

## Issue 7: Add Batch Processing Support

**Labels:** `enhancement`, `production`

**Description:**
For production workloads, batch processing is essential:

```python
# Current: One at a time
for text in texts:
    result = prompter.predict(text)

# Proposed: Batch processing
results = prompter.predict_batch(texts, num_workers=4)
```

**Acceptance Criteria:**
- [ ] Add `predict_batch()` method
- [ ] Parallel processing with configurable workers
- [ ] Progress tracking (optional)
- [ ] Proper error handling per item

---

## Issue 8: Add Async Support

**Labels:** `enhancement`, `production`

**Description:**
Modern APIs need async for high throughput:

```python
# Current: Synchronous only
result = prompter.predict(text)

# Proposed: Async support
result = await prompter.apredict(text)
results = await prompter.apredict_batch(texts)
```

**Acceptance Criteria:**
- [ ] Add `apredict()` async method
- [ ] Add `apredict_batch()` for concurrent batch processing
- [ ] Use asyncer for sync/async compatibility

---

## Issue 9: Add Request Caching

**Labels:** `enhancement`, `production`

**Description:**
Repeated extractions with same input waste API calls:

```python
prompter = Prompter(model=MyModel, cache=True)
# or
prompter = Prompter(model=MyModel, cache_dir="~/.cache/dspydantic")
```

**Acceptance Criteria:**
- [ ] Add caching option to Prompter
- [ ] Cache based on input hash + model config
- [ ] Configurable cache directory
- [ ] Cache TTL support

---

## Issue 10: Add Rate Limiting Support

**Labels:** `enhancement`, `production`

**Description:**
Production deployments need rate limiting to avoid API quota issues:

```python
prompter = Prompter(
    model=MyModel,
    rate_limit=10,  # requests per second
)
```

**Acceptance Criteria:**
- [ ] Add rate limiting option
- [ ] Integrate with batch processing
- [ ] Support for different rate limit strategies

---

## Issue 11: Improve Error Messages for Common Issues

**Labels:** `enhancement`, `usability`

**Description:**
Current errors are not helpful:
```
ValueError: DSPy must be configured before optimization.
```

Should provide actionable guidance:
```
ValueError: DSPy must be configured before optimization.

To configure DSPy:
    import dspy
    lm = dspy.LM("openai/gpt-4o", api_key="your-api-key")
    dspy.configure(lm=lm)

Or use model_id parameter:
    prompter = Prompter(model=MyModel, model_id="openai/gpt-4o")
```

**Acceptance Criteria:**
- [ ] Improve error messages with examples
- [ ] Add common troubleshooting tips to errors
- [ ] Include links to relevant documentation

---

## Issue 12: Add Production Deployment Example

**Labels:** `documentation`

**Description:**
Documentation shows save/load but no real deployment example:

```python
# Complete production example needed:
# 1. Optimize locally
# 2. Save to file
# 3. Load in production (without optimization overhead)
# 4. Handle errors gracefully
# 5. Monitor performance
```

**Acceptance Criteria:**
- [ ] Add `examples/production_deployment.py`
- [ ] Add deployment guide to docs
- [ ] Include Docker example
- [ ] Show monitoring/logging best practices

---

## Competitive Analysis Summary

| Feature | DSPydantic | LangStruct | LangExtract |
|---------|-----------|------------|-------------|
| **Auto-optimization** | ✅ Multiple optimizers | ✅ MIPROv2 | ❌ Manual |
| **Schema Definition** | ✅ Pydantic | ✅ Examples/Pydantic | ⚠️ Prompt-based |
| **Source Grounding** | ❌ Missing | ✅ Character-level | ✅ Character-level |
| **Confidence Scores** | ❌ Missing | ✅ Built-in | ⚠️ Not surfaced |
| **Batch Processing** | ❌ Missing | ❌ Unknown | ❌ Single doc |
| **Async Support** | ❌ Missing | ❌ Unknown | ❌ No |
| **Save/Load** | ✅ Full support | ✅ Built-in | ⚠️ Unknown |
| **Judge Evaluation** | ✅ ScoreJudge | ❌ Unknown | ❌ No |
| **Without Examples** | ✅ Judge-based | ❌ Unknown | ❌ No |
| **Image/PDF Support** | ✅ Full | ❌ Unknown | ❌ Text only |
| **Production Ready** | ⚠️ Basic | ⚠️ Basic | ⚠️ Basic |

### DSPydantic Strengths
1. **Pydantic-native** - Best type safety and validation
2. **Multiple optimizers** - More optimization options than competitors
3. **Multi-modal** - Supports text, images, PDFs
4. **Judge evaluation** - Works without labeled examples
5. **Template prompts** - Dynamic context-aware extraction

### Priority Improvements
1. **Fix docs (Issue 1)** - Critical, broken user experience
2. **Add `run()` alias (Issue 2)** - Easy win for usability
3. **Simplify DSPy config (Issue 3)** - Reduces friction
4. **Batch processing (Issue 7)** - Production essential
5. **Source grounding (Issue 6)** - Competitive feature

---

## Execution Order (Phase 1 - Core)

1. **Issue 1** (bug fix) - Immediate ✅ DONE
2. **Issue 2** (alias) - Quick win ✅ DONE
3. **Issue 3** (model_id) - High impact
4. **Issue 4** (no-optimize) - High impact
5. **Issue 7** (batch) - Production
6. **Issue 8** (async) - Production
7. **Issue 5** (confidence) - Feature
8. **Issue 6** (grounding) - Feature
9. **Issue 9-10** (cache/rate) - Production
10. **Issue 11-12** (docs) - Ongoing

---

# Phase 2: Advanced Features

## Issue 13: Add Streaming Support

**Labels:** `enhancement`, `feature`

**Description:**
For long extractions or real-time applications, streaming is essential:

```python
async for chunk in prompter.stream(text):
    print(chunk.partial_result)  # Partial extraction as it's generated
```

**Acceptance Criteria:**
- [ ] Add `stream()` method for streaming extraction
- [ ] Support partial result emission
- [ ] Handle structured output assembly

---

## Issue 14: Add Cost Tracking and Optimization Budget

**Labels:** `enhancement`, `production`

**Description:**
Track API costs during optimization and enforce budgets:

```python
result = prompter.optimize(
    examples=examples,
    max_cost_usd=5.0,  # Stop if cost exceeds $5
    verbose=True,  # Shows cost per iteration
)
print(result.metrics["total_cost_usd"])  # 2.34
print(result.metrics["api_calls"])  # 127
```

**Acceptance Criteria:**
- [ ] Track token usage per optimization call
- [ ] Calculate estimated costs based on model pricing
- [ ] Add `max_cost_usd` budget parameter
- [ ] Include cost metrics in OptimizationResult

---

## Issue 15: Add Refinement/Best-of-N Sampling

**Labels:** `enhancement`, `quality`

**Description:**
LangStruct mentions "Best-of-N + iterative improvement". Add similar capability:

```python
result = prompter.predict(
    text,
    n=3,  # Generate 3 candidates
    refine=True,  # Iteratively improve best candidate
)
```

**Acceptance Criteria:**
- [ ] Add `n` parameter for multiple generations
- [ ] Add selection strategy (best score, majority vote)
- [ ] Add optional refinement pass
- [ ] Return all candidates if requested

---

## Issue 16: Add Validation Hooks and Post-Processing

**Labels:** `enhancement`, `api`

**Description:**
Allow custom validation and transformation of extracted data:

```python
def validate_email(data):
    if "@" not in data.get("email", ""):
        raise ValidationError("Invalid email")
    return data

def normalize_phone(data):
    data["phone"] = re.sub(r"[^\d]", "", data.get("phone", ""))
    return data

prompter = Prompter(
    model=User,
    validators=[validate_email],
    post_processors=[normalize_phone],
)
```

**Acceptance Criteria:**
- [ ] Add `validators` parameter for validation functions
- [ ] Add `post_processors` for data transformation
- [ ] Clear error messages on validation failure
- [ ] Option to retry on validation failure

---

## Issue 17: Add Progress Tracking During Optimization

**Labels:** `enhancement`, `usability`

**Description:**
Long optimizations need progress feedback:

```python
from rich.progress import Progress

with Progress() as progress:
    result = prompter.optimize(
        examples=examples,
        progress=progress,  # Or progress_callback=fn
    )
```

Or built-in progress:
```python
result = prompter.optimize(examples, show_progress=True)
# [=====>    ] 50% | Iteration 5/10 | Score: 0.85 | Cost: $1.23
```

**Acceptance Criteria:**
- [ ] Add `show_progress` parameter for built-in progress bar
- [ ] Add `progress_callback` for custom progress handling
- [ ] Show current score, iteration, estimated time remaining
- [ ] Support Rich progress bars

---

## Issue 18: Add Schema Inference from Examples

**Labels:** `enhancement`, `feature`, `competitive`

**Description:**
LangStruct can infer schema from examples. Add similar capability:

```python
# No Pydantic model needed - infer from examples
prompter = Prompter.from_examples([
    {"text": "John, 30", "output": {"name": "John", "age": 30}},
    {"text": "Jane, 25", "output": {"name": "Jane", "age": 25}},
])

# Or with type hints
prompter = Prompter.infer_schema(
    examples=examples,
    type_hints={"age": int, "date": "datetime"},
)
```

**Acceptance Criteria:**
- [ ] Add `from_examples()` class method
- [ ] Infer field types from example values
- [ ] Support type hint overrides
- [ ] Generate Pydantic model internally

---

## Issue 19: Add Partial/Lenient Extraction Mode

**Labels:** `enhancement`, `feature`

**Description:**
Sometimes you want to extract what you can, even if not all fields are found:

```python
result = prompter.predict(
    text,
    lenient=True,  # Don't fail on missing fields
    min_fields=2,  # But require at least 2 fields
)
print(result.extracted_fields)  # ["name", "email"]
print(result.missing_fields)  # ["phone", "address"]
```

**Acceptance Criteria:**
- [ ] Add `lenient` mode for partial extraction
- [ ] Track which fields were extracted vs missing
- [ ] Add `min_fields` threshold
- [ ] Return partial results with metadata

---

## Issue 20: Add Observability/Tracing Integration

**Labels:** `enhancement`, `production`

**Description:**
For production debugging, integrate with observability tools:

```python
from dspydantic import Prompter
import opentelemetry

prompter = Prompter(
    model=User,
    tracer=opentelemetry.trace.get_tracer(__name__),
)

# Or DSPy-native
import dspy
dspy.configure(lm=lm, trace=True)

# View traces
prompter.last_trace  # Full trace of last extraction
```

**Acceptance Criteria:**
- [ ] Add OpenTelemetry integration
- [ ] Add `last_trace` property for debugging
- [ ] Log extraction steps with timing
- [ ] Support custom trace exporters

---

## Issue 21: Add Pre-built Domain Extractors

**Labels:** `enhancement`, `ecosystem`

**Description:**
Provide ready-to-use extractors for common domains:

```python
from dspydantic.domains import (
    InvoiceExtractor,
    ResumeExtractor,
    ContractExtractor,
    MedicalRecordExtractor,
)

invoice = InvoiceExtractor().extract(pdf_path="invoice.pdf")
print(invoice.vendor, invoice.total, invoice.line_items)
```

**Acceptance Criteria:**
- [ ] Create `dspydantic.domains` package
- [ ] Add 3-5 common domain extractors
- [ ] Include pre-optimized prompts
- [ ] Document domain-specific features

---

## Issue 22: Add Comparison/Diff Tool for Prompts

**Labels:** `enhancement`, `developer-experience`

**Description:**
Compare original vs optimized prompts to understand what changed:

```python
result = prompter.optimize(examples)

# Show what changed
result.show_diff()
# Field: name
# - Original: "User name"
# + Optimized: "Full legal name of the person as it appears in the document"

# Or programmatically
for field, diff in result.diffs.items():
    print(f"{field}: {diff.original} -> {diff.optimized}")
```

**Acceptance Criteria:**
- [ ] Add `show_diff()` method to OptimizationResult
- [ ] Provide structured diff data
- [ ] Highlight significant changes
- [ ] Show improvement metrics per field

---

## Issue 23: Add Extraction Explanation/Reasoning

**Labels:** `enhancement`, `feature`

**Description:**
Understand why specific values were extracted:

```python
result = prompter.predict(text, explain=True)
print(result.name)  # "John Doe"
print(result.explanations["name"])  
# "Extracted 'John Doe' from 'My name is John Doe' at position 11-19"
```

**Acceptance Criteria:**
- [ ] Add `explain` parameter to predict
- [ ] Return reasoning for each field
- [ ] Include source text positions (ties into source grounding)
- [ ] Optional - can be disabled for performance

---

## Issue 24: Add Model Comparison Tool

**Labels:** `enhancement`, `developer-experience`

**Description:**
Compare extraction quality across different LLMs:

```python
results = prompter.compare_models(
    text=text,
    models=["gpt-4o", "gpt-4o-mini", "claude-3-sonnet"],
)
# Returns comparison table with scores, latency, cost per model
```

**Acceptance Criteria:**
- [ ] Add `compare_models()` method
- [ ] Run same extraction across multiple LLMs
- [ ] Compare accuracy, latency, cost
- [ ] Output comparison report

---

## Issue 25: Add Prompt Template Library

**Labels:** `enhancement`, `ecosystem`

**Description:**
Share and reuse optimized prompt templates:

```python
# Save optimized prompts to library
prompter.save_to_library("invoice-extraction-v1")

# Load from library
prompter = Prompter.from_library("invoice-extraction-v1")

# Browse community templates
templates = Prompter.list_templates(domain="finance")
```

**Acceptance Criteria:**
- [ ] Add local template storage
- [ ] Add template metadata (domain, version, metrics)
- [ ] Consider community template sharing (future)

---

# Phase 3: Ecosystem & Integration

## Issue 26: Add LangChain/LlamaIndex Integration

**Labels:** `enhancement`, `integration`

**Description:**
Make dspydantic work seamlessly with popular frameworks:

```python
# LangChain
from dspydantic.integrations import LangChainExtractor
chain = LangChainExtractor(prompter)

# LlamaIndex
from dspydantic.integrations import LlamaIndexExtractor
extractor = LlamaIndexExtractor(prompter)
```

**Acceptance Criteria:**
- [ ] Add LangChain Document loader integration
- [ ] Add LlamaIndex node parser integration
- [ ] Maintain compatibility with framework updates

---

## Issue 27: Add CLI Tool

**Labels:** `enhancement`, `developer-experience`

**Description:**
Command-line interface for quick extraction:

```bash
# Extract from file
dspydantic extract --model User --input data.txt --output result.json

# Optimize from examples
dspydantic optimize --examples train.jsonl --output optimized_prompter/

# Compare models
dspydantic compare --input test.txt --models gpt-4o,claude-3
```

**Acceptance Criteria:**
- [ ] Add `dspydantic` CLI command
- [ ] Support `extract`, `optimize`, `compare` subcommands
- [ ] Support file input/output
- [ ] Add `--verbose` and `--quiet` flags

---

## Issue 28: Add Benchmarking Suite

**Labels:** `enhancement`, `quality`

**Description:**
Standardized benchmarks to compare with competitors:

```python
from dspydantic.benchmarks import run_benchmarks

results = run_benchmarks(
    prompter=prompter,
    datasets=["invoice", "resume", "medical"],
)
# Compare against LangExtract, LangStruct baselines
```

**Acceptance Criteria:**
- [ ] Create benchmark datasets
- [ ] Add benchmark runner
- [ ] Document comparison with competitors
- [ ] Publish benchmark results

---

# Summary: Full Roadmap

## Phase 1: Core Improvements (High Impact)
| Issue | Description | Priority |
|-------|-------------|----------|
| 1-2 | Method naming (run/predict) | ✅ Done |
| 3 | Simplify DSPy config | High |
| 4 | Extract without optimize | High |
| 7-8 | Batch + Async | Production |
| 5-6 | Confidence + Grounding | Competitive |
| 9-10 | Cache + Rate limiting | Production |

## Phase 2: Advanced Features
| Issue | Description | Priority |
|-------|-------------|----------|
| 13 | Streaming | Medium |
| 14 | Cost tracking | High |
| 15 | Best-of-N / Refinement | Medium |
| 16 | Validation hooks | Medium |
| 17 | Progress tracking | High |
| 18 | Schema inference | Competitive |
| 19 | Partial extraction | Medium |
| 20 | Observability | Production |

## Phase 3: Ecosystem
| Issue | Description | Priority |
|-------|-------------|----------|
| 21 | Domain extractors | Medium |
| 22 | Diff tool | Low |
| 23 | Explanations | Medium |
| 24 | Model comparison | Low |
| 25 | Template library | Future |
| 26 | Framework integrations | Medium |
| 27 | CLI tool | Medium |
| 28 | Benchmarks | Marketing |

---

# Key Differentiators to Emphasize

## vs LangExtract
- ✅ **Auto-optimization** (LangExtract has none)
- ✅ **Multi-modal** (images, PDFs)
- ✅ **Judge evaluation** (works without labels)
- ⚠️ Need: Source grounding

## vs LangStruct
- ✅ **Multiple optimizers** (not just MIPROv2)
- ✅ **Pydantic-native** (better type safety)
- ⚠️ Need: Schema inference
- ⚠️ Need: Confidence scores
- ⚠️ Need: Refinement pipeline

## Unique Positioning
**"The production-grade prompt optimization library for structured extraction"**

- DSPy-powered optimization (best-in-class)
- Pydantic-native (developer-friendly)
- Multi-modal (text, images, PDFs)
- Production-ready (save/load, batch, async)
