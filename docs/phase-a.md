# Phase A: Folklore Index Digitization and Tooling

## Overview

Phase A of the GLOS project focuses on the digitization, structuring, and exploration of two canonical folklore indexes:

- **Stith Thompson's Motif Index (TMI)** — a typology of over 43,000 motifs categorized into 23 thematic classes
- **Aarne-Thompson-Uther Tale Type Index (ATU)** — a system of tale types grouped into 7 primary sections, often linked to motifs

These indexes were normalized into a PostgreSQL relational schema, and embeddings were generated for experimental retrieval and clustering. A pilot web app was also created for nearest-neighbor comparison.

## ATU/TMI Exploration Tool

A major recent development is a dedicated **ATU/TMI interface** within the GLOS Flask application. This tool enables bidirectional navigation and linking between tale types and motifs.

### Key Features

#### 🔍 Search Functionality

- **Toggleable Direction:** Users select either **ATU → TMI** or **TMI → ATU**
- **Tabbed Interface:** A left-hand panel with tabs for *Search* and *Browse*
- **Smart Search:** Accepts either free-text or ID input with live autocomplete
- **Interactive Results:** Display full entry text and cross-references in the right-hand panel

#### 📚 Browse Functionality – ATU Index

- Accordion interface organized by ATU’s 7 major sections
- Expands into ID-based subsections (e.g., 1–99, 100–149)
- Clickable tale type links display full entries and associated motifs

#### 📚 Browse Functionality – Thompson Motif Index

- Organized by 23 top-level categories (A–Z), e.g., *A – Mythological Motifs*
- Subsections grouped by ID ranges (e.g., A0–A99), with **badge counters** indicating how many motifs are linked to tale types
- Two-level deep navigation handles Thompson’s complex hierarchy
- Leaf nodes display motif details and provide links to associated tale types

This tool represents a significant step toward making these rich indexes more usable and analyzable by folklorists, particularly in collaborative academic settings.

---

*Return to [Project Overview](project-overview.md)*
