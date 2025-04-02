# Geographic Lens on Stories (GLOS) Project README

**Updated: 2 April 2025**

This document outlines the current methodology and workflow for the GLOS project, which uses computational techniques to explore the conceptual structures and cross-cultural patterns in a corpus of global creation myths.

---

## Overview

The project's objective is to model and analyze conceptual motifs, entities, events, and relationships within myths using a structured ontology and JSON-LD representation. A small sample of nine myths from Barbara Sproul's *Primal Myths* has been processed to date. The remaining 115 myths are currently being digitized.

---

## 🧭 Current Workflow (as of 2 April 2025)

### **1. Input Preparation**
- Clean and OCR each myth from the Sproul volume.
- Save as a plain text file with the following format:
  ```
  Line 1: Culture or society label
  Line 2: Title of the myth
  Lines 3+: Myth narrative text
  ```
- Store all text files in `data/myths/`.

### **2. Conceptual Extraction**
- Use an LLM to:
  - Identify entity and event **instances** and their **types**
  - Detect **relations** between them (e.g., agent, patient, location, transformation)
- Generate a **JSON-LD object** that represents the structured knowledge from the myth.

### **3. Ontology Management**
- If a new type (entity, event, role) is found:
  - Compare it against existing ontology terms
  - Propose **normalization** or **conflation** if overlapping
  - Update the ontology documentation (e.g., `ontology_scope_notes.csv`) with scope notes and usage frequency

### **4. Corpus Integration**
- Append each structured myth to the master file:
  - Currently: `sample9_all_normalized.jsonld`
  - Eventually: `corpus_all_normalized.jsonld`
- Maintain consistency of structure and term usage across myths

### **5. Conceptual Vectorization**
- Convert the JSON-LD structure of each myth into a **feature vector**:
  - Dimensions represent event types, entity types, and relational roles
  - Counts or normalized values are used for each dimension
- Store vectors in `Conceptual_Profile_Vectors.csv`
- Use this matrix for:
  - Similarity computation
  - Dimensionality reduction (PCA, UMAP)
  - Conceptual clustering and visualization

---

## 🕰 Recommended Milestone Checkpoints

To monitor progress and evolution of the corpus:
- Re-run full analysis (vectorization, visualization, normalization check) at:
  - ~50 myths
  - ~100 myths
  - Final full set (124 myths)

These checkpoints will help identify emergent conceptual clusters, ontology growth trends, and evolving visual landscapes.

---

## 📌 Notes and Next Steps
- Additional metadata (e.g., geography, cultural groupings) will be added to each myth to support regional comparisons and conceptual mapping.
- Scope notes are being developed to aid human interpretation of ontology terms.
- Conceptual density and normalization strategies will be evaluated after integration of longer myths.

---

For questions, roadmap planning, or ontology expansion, refer to this file as a living guide.
