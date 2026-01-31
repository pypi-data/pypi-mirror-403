<!--
Copyright 2026 The text-curation Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
-->

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)"
            srcset="https://dummyimage.com/720x140/0d1117/ffffff&text=text-curation">
    <source media="(prefers-color-scheme: light)"
            srcset="https://dummyimage.com/720x140/ffffff/000000&text=text-curation">
    <img alt="text-curation logo"
         src="https://dummyimage.com/720x140/ffffff/000000&text=text-curation"
         width="360"
         style="max-width: 100%">
  </picture>
  <br/>
  <br/>
</p>

<p align="center">
  <i>Profile-based, deterministic text curation pipelines for large-scale NLP datasets</i>
</p>

<p align="center">
  <a href="https://pypi.org/project/text-curation/">
    <img alt="PyPI version" src="https://img.shields.io/pypi/v/text-curation.svg">
  </a>
  <a href="https://pypi.org/project/text-curation/">
    <img alt="PyPI downloads" src="https://img.shields.io/pypi/dm/text-curation">
  </a>
  <a href="https://github.com/Dhiraj309/text-curation/releases">
    <img alt="GitHub release" src="https://img.shields.io/github/release/Dhiraj309/text-curation.svg">
  </a>
  <a href="https://pypi.org/project/text-curation/">
    <img alt="Python versions" src="https://img.shields.io/pypi/pyversions/text-curation.svg">
  </a>
  <a href="https://github.com/Dhiraj309/text-curation/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/Dhiraj309/text-curation.svg">
  </a>
</p>

---

**Documentation**: https://github.com/Dhiraj309/text-curation  
**Source Code**: https://github.com/Dhiraj309/text-curation

---

## Overview

**text-curation** is a Python library for building **structured, profile-driven text curation pipelines**
designed for **large-scale NLP datasets**, with first-class integration into the
**Hugging Face Datasets** ecosystem.

It focuses on **deterministic, inspectable, and conservative text transformations**
for preparing corpora used in LLM training, evaluation, and analysis.

Rather than relying on ad-hoc cleanup scripts, `text-curation` promotes
**explicit, versioned curation profiles** that make data preprocessing
**reproducible, auditable, and stable over time**.

---

## Design Principles

- **Profile-driven pipelines**  
  Reusable, declarative profiles define how text is curated for a given domain
  (e.g. web, wiki, forums).

- **Composable blocks**  
  Each transformation is implemented as an isolated block with a single,
  explicit responsibility.

- **Deterministic and conservative**  
  All transformations are rule-based and non-destructive by default,
  prioritizing semantic preservation.

- **Structure-aware processing**  
  Text is treated as structured content (paragraphs, lists, headers),
  not just raw strings.

- **Dataset-scale friendly**  
  Designed to run efficiently on large Hugging Face Datasets using `.map`.

---

## Scope & Stability (v1.3.4)

As of **v1.3.4**, `text-curation` provides a **stable and extensible core**
for structure-aware text curation of real-world, messy data.

The default behavior and semantics of the core blocks and built-in profiles
are considered **stable** and will not change without a major version bump.

Stability is enforced through **block-level unit tests and golden profile tests**,
which act as executable specifications.

The library intentionally focuses on **deterministic preprocessing**
rather than semantic classification or machine-learning-based filtering.

---

## Core Blocks (Stable)

The following blocks are part of the **stable core** in v1.3.4.

- **Normalization**  
  Canonicalizes Unicode and typography (quotes, dashes, ellipses),
  removes control and zero-width characters, and normalizes whitespace.

- **Formatting**  
  Reconstructs paragraph structure, normalizes punctuation spacing,
  and preserves indentation-sensitive content such as code blocks.
  Paragraph semantics are preserved by design.

- **Redaction**  
  Masks sensitive content such as emails, API tokens, and embedded credentials
  using explicit, non-destructive placeholders.

- **Structure**  
  Detects headers, lists, repetition, and boilerplate indicators,
  emitting inspectable signals without mutating text.

- **Filtering**  
  Applies conservative, signal-based removal of empty or low-value paragraphs.

- **Deduplication**  
  Performs exact, paragraph-level deduplication using normalization-safe keys.

More aggressive semantic filtering, fuzzy deduplication, or heuristic cleanup
are intentionally **not enabled by default** and may be introduced only via
explicit opt-in profiles in future releases.

---

## Non-Goals

`text-curation` intentionally does **not** attempt to:

- Perform semantic or topical classification
- Use machine learning or probabilistic heuristics
- Infer document quality or intent
- Preserve exact visual formatting of source text
- Aggressively remove all boilerplate or repetition by default

These constraints are **by design** and are critical to ensuring
predictable, reproducible dataset preprocessing.

---

## Installation

`text-curation` supports **Python ≥ 3.9**.

Install from PyPI:

```bash
pip install text-curation
````

Or install from source for development:

```bash
git clone https://github.com/Dhiraj309/text-curation.git
cd text-curation
pip install -e .
```

---

## Quickstart

### Curating a Hugging Face Dataset

```python
from datasets import load_dataset
from text_curation import TextCurator

dataset = load_dataset(
    "HuggingFaceFW/fineweb-edu",
    split="train",
)

curator = TextCurator.from_profile("web_common:v1")

cleaned = dataset.map(
    curator,
    batched=True,
    num_proc=4,
)
```

The curator is a **pure function**:
it takes a batch dictionary and returns a dictionary with the same schema,
making it fully compatible with Hugging Face Datasets.

---

## Profiles

Profiles define **which blocks are applied and in what order**.

Profiles are:

* Explicitly versioned
* Registered at import time
* Resolved via a global registry

Conceptual example:

```python
web_common_v1 = [
    RedactionBlock(),
    NormalizationBlock(),
    CodeSafeFormattingBlock(),
    ParagraphFormattingBlock(),
    BasicStructureBlock(),
    ExactParagraphDeduplicationBlock(),
]
```

Profiles are referenced using explicit version identifiers
(e.g. `web_common:v1`) to ensure **long-term reproducibility and auditability**.

Profiles may be deprecated, but are never silently changed.

---

## Designed For

* Web-scale datasets (C4-like, Common Crawl, scraped corpora)
* OCR- and PDF-derived text
* Forums, blogs, and user-generated content
* Dataset preprocessing prior to LLM training or evaluation

The library is intentionally **model-agnostic** and does not depend on
tokenizers, embeddings, or classifiers.

---

## Why text-curation?

* Cleaning text is not just normalization — **structure and repetition matter**
* Ad-hoc scripts do not scale or reproduce
* Dataset curation deserves the same rigor as model training
* Explicit pipelines make data decisions inspectable and debuggable

`text-curation` is designed to be the **data-side analogue**
of model-definition libraries in the Hugging Face ecosystem.

---

## When should you *not* use text-curation?

* If you only need a one-off regex cleanup
* If your data is already fully curated
* If you require ML-based content classification or scoring

---

## Versioning & Compatibility

This project follows **semantic versioning**.

* `1.x` releases guarantee stable default behavior
* Breaking changes require a major version bump
* Profiles are versioned independently of library versions
  to preserve long-term reproducibility

---

## Contributing

Contributions are welcome.

When adding new blocks or profiles:

* Keep transformations deterministic
* Avoid destructive defaults
* Include clear before/after examples
* Add or update tests to lock in behavior

See `CONTRIBUTING.md` for details.

---

## License

Apache 2.0. See [LICENSE](LICENSE).

---

## Acknowledgements

Inspired by large-scale dataset curation practices
in the Hugging Face ecosystem.
