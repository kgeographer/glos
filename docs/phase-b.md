# Phase B: Creation Myths and Schema Development

## Overview

Phase B of the GLOS project explored the use of large language models (LLMs) and embeddings to analyze and compare the conceptual content of creation myths across cultures. The long-term goal is to derive a flexible schema—or ultimately, an ontology—that enables rich comparison of mythological structures, themes, and worldviews.

## Initial Corpus and Methodology

The work began with the digitization of **20 creation myths** drawn from Barbara Sproul’s _Primal Myths_. While the sample was not globally representative (with roughly two-thirds from African traditions and the rest from the Middle East), the primary aim was methodological: to establish a proof of concept.

Two key efforts were pursued:

### 1. Structured Conceptual Extraction via LLMs

- Each myth was processed using an **elaborate prompt** designed to extract conceptual structure
- The LLM returned:
  - A set of **key-value attributes** grouped into thematic sections (e.g., *cosmic beginnings*, *origin of humanity*, etc.)
  - Each result was encoded as a **JSON-LD document**, yielding 20 structured representations
- The union of attributes across the myths forms the basis for a **working schema**, and potentially a cross-cultural **ontology of creation myths**
- These attributes are normalized but flexible; not every myth has all values, but many share common conceptual themes

### 2. Embedding Creation for Comparison

Multiple layers of text embeddings were generated:
- **Whole-myth embeddings** for gross similarity clustering
- **Event-level embeddings** based on extracted actions and their participants
- These support **faceted comparison** of myths: by event type, thematic roles, or conceptual sections

## Status and Reception

This line of work is currently **paused**, but its potential was affirmed in early presentations:
- Folklorists at Indiana University responded positively to the structure and conceptual categories derived via LLM
- The emerging schema was seen as promising, even without exhaustive validation
- The current pause is due to renewed interest in ATU/TMI tool development (Phase A)

---

*Return to [Project Overview](project-overview.md)*
