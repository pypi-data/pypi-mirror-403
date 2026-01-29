# dotcausal

**Binary Knowledge Graph Format with Embedded Inference**

[![PyPI version](https://badge.fury.io/py/dotcausal.svg)](https://badge.fury.io/py/dotcausal)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The `.causal` format is a binary storage format for causal knowledge graphs with embedded deterministic inference rules. Designed for AI applications requiring zero-hallucination guarantees.

## Features

- **~60-80% smaller** than equivalent SQLite/JSON storage
- **50-100%+ fact amplification** through 3-pass inference (depends on graph density)
- **Zero hallucination** - pure deterministic logic, full provenance tracking
- **Single-file portable** - like SQLite, but optimized for knowledge graphs
- **Embedded inference** - pre-computed transitive chains, zero query-time cost

## Installation

```bash
pip install dotcausal
```

## Quick Start

### Python API

```python
from dotcausal import CausalFile, CausalWriter, CausalReader

# Create a new .causal file
writer = CausalWriter()
writer.add_triplet(
    trigger="SARS-CoV-2 infection",
    mechanism="causes",
    outcome="mitochondrial dysfunction",
    confidence=0.9,
    source="paper1.pdf"
)
writer.add_triplet(
    trigger="mitochondrial dysfunction",
    mechanism="leads to",
    outcome="chronic fatigue",
    confidence=0.85,
    source="paper2.pdf"
)
stats = writer.save("knowledge.causal")
print(f"Saved {stats['triplets']} triplets")

# Read and query with inference
reader = CausalReader("knowledge.causal")

# Get explicit facts only
explicit = reader.get_all_triplets(include_inferred=False)
print(f"Explicit: {len(explicit)}")

# Get amplified facts (explicit + inferred)
all_facts = reader.get_all_triplets(include_inferred=True)
print(f"Total with inference: {len(all_facts)}")

# Search
results = reader.search("COVID", field="all")
for r in results:
    print(f"{r['trigger']} → {r['mechanism']} → {r['outcome']}")
```

### Command Line

```bash
# Show file statistics
dotcausal stats knowledge.causal

# Query the graph
dotcausal query knowledge.causal "COVID" --limit 10

# Convert SQLite to .causal
dotcausal convert pipeline.db output.causal

# Export to JSON
dotcausal export knowledge.causal -o output.json

# Validate file integrity
dotcausal validate knowledge.causal
```

## The 3-Pass Inference Engine

The `.causal` format includes a deterministic inference engine that derives new facts from explicit ones:

| Pass | Method | Example |
|------|--------|---------|
| 1 | Exact keyword matching | A→activates→B + B→activates→C = A→activates→C |
| 2 | Semantic direction | positive×positive = positive chain |
| 3 | Jaro-Winkler fuzzy | "COVID-19" ↔ "SARS-CoV-2" (similarity 0.82) |

All inference is **deterministic** - same input always produces same output. Zero hallucination guaranteed.

## File Format

```
[HEADER 64 bytes]  → Magic "CAUSAL01", Version, CRC
[OFFSET TABLE]     → Section offsets
[ENTITIES]         → Deduplicated dictionary
[TRIPLETS]         → Explicit facts with metadata
[RULES]            → Inference rules
[CLUSTERS]         → Semantic groupings
[GAPS]             → Knowledge gaps
```

## Use Cases

- **RAG Enhancement**: Ground LLM responses in verified causal chains
- **Scientific Discovery**: Amplify weak signals through transitive inference
- **Knowledge Bases**: Portable, compressed storage for triplet data
- **AI Safety**: Zero-hallucination fact retrieval

## Citation

If you use `.causal` in your research, please cite:

```bibtex
@software{foss2026dotcausal,
  author = {Foss, David Tom},
  title = {dotcausal: Binary Knowledge Graph Format with Embedded Inference},
  year = {2026},
  url = {https://github.com/dotcausal/dotcausal}
}
```

## Links

- **Documentation**: https://dotcausal.com/docs
- **Whitepaper**: [Zenodo DOI](https://doi.org/10.5281/zenodo.XXXXXXX)
- **GitHub**: https://github.com/dotcausal/dotcausal

## License

MIT License - see [LICENSE](LICENSE) for details.
