# Geographic Lens on Stories (GLOS): Project Overview

## Introduction

The Geographic Lens on Stories (GLOS) project explores how folklore and mythology—particularly motifs, tale types, and creation myths—can be analyzed computationally to reveal conceptual patterns, geographic variation, and cross-cultural resonance. Combining geographic information science, ontology modeling, and machine learning, GLOS aims to develop tools and structured data that enable new forms of distant reading and cultural analysis.

## Project Phases

The GLOS project is unfolding in two primary phases:

### Phase A: Folklore Index Digitization and Tooling

This phase focused on the digitization and exploration of:
- **Stith Thompson's Motif Index (TMI)** — over 43,000 motif entries categorized and structured
- **Aarne-Thompson-Uther Tale Type Index (ATU)** — with cross-references to motifs, cultures, and geographies

Key achievements:
- Normalized relational database schema
- Embedding generation for motifs and tale types
- Pilot web app enabling motif/tale-type search and nearest-neighbor retrieval
- Developed an interactive ATU/TMI interface within the GLOS Flask app:
  - Enables dual-direction search and browse between tale types and motifs
  - Handles ATU’s hierarchical structure and TMI’s complex category system
  - Provides visual feedback (autocomplete, badges, drill-down) to guide exploration
  - Currently in testing; feedback sought from folklore scholars

### Phase B: Creation Myth Schema and Ontology Work

In this phase, GLOS shifted focus to conceptual content:
- Digitized sample of **Barbara Sproul’s _Primal Myths_** (eventual full set of 144 myths)
- Began **event and entity extraction**, structuring myths into JSON-LD format
- Applied **LLM-based clustering and schema elicitation** to identify conceptual structures
- Developed foundational schema for comparative myth analysis across cultures

This track is currently paused as efforts return to Phase A due to renewed collaboration interest.

## Table of Contents

- [Phase A: TMI and ATU Tooling](phase-a.md)
- [Phase B: Creation Myths and Schema Development](phase-b.md)
