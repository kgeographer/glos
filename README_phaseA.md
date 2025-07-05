### GLOS Phase A: Motif and Tale Type Embeddings

**Updated: 11 June 2025**

Phase A of the Geographic Lens on Stories (GLOS) project has focused on computational representations of canonical folkloristic reference works: *The Types of International Folktales* (ATU) and *The Motif-Index of Folk-Literature* (TMI). This phase produced two working prototype tools for use by researchers and students of folklore.

---

## 1. ATU/TMI Cross-Reference Tool

This browser-based tool allows users to explore relationships between ATU tale types and their associated Thompson motifs. Users may search or browse both tale types and motifs by keyword or identifier, and follow the cross-referencing relationships recorded in the ATU.

### Features

- Bidirectional links between tale types and motifs
- Cultural reference terms displayed for both tale types and motifs
- Tooltip-enhanced indicators for motifs referenced in multiple tale types
- Interactive modals allowing contextual navigation

### 🧪 Technical Summary

- **Digitization and Schema Design**: The ATU and TMI indexes were digitized, normalized, and imported into a PostgreSQL database. Each tale type and motif was given a persistent identifier. A linking table was created for all tale type–motif cross-references found in ATU entries.
- **Cultural Labels**: Culture or region terms from the ATU or TMI entries were parsed and for display and potential filtering, analysis and visualization.
- **Frontend/Backend Design**: A lightweight Flask app serves JSON-formatted queries to a Bootstrap-based UI. Interactive elements (e.g., modals, tooltips) are powered by JavaScript and rendered dynamically from the database.
- **Navigation Logic**: Users can traverse between tale types and motifs using live links generated from cross-reference tables. Highlighting is used to distinguish shared motifs across types.

---

## 2. Concept Matcher Tool

This prototype tool allows users to input any piece of text—such as a folktale, myth, or summary—and receive a ranked list of the most semantically similar motifs and/or tale types using sentence embeddings. The system enables exploratory indexing, interpretation, and thematic analysis of narrative material not formally cataloged.

### Features

- Natural language input via text box
- Option to return nearest motifs, or tale types
- Ranked similarity results using dense vector search
- Lightweight interface for interpretive or pedagogical use

### 🧪 Technical Summary

- **Text Embedding**: We used OpenAI’s `text-embedding-3-small` model to compute vector embeddings for over 46,245 motif titles and 2,232 tale type summaries.
- **Vector Indexing**: Embeddings were stored in PostgreSQL using its _vector_ extension for fast nearest-neighbor retrieval. All vectors use cosine distance for similarity computation.
- **Query Pipeline**:
  1. User text input is sent to the OpenAI API to produce an embedding.
  2. The embedding is compared against the motif and/or tale type index.
  3. Top-k nearest entries are returned, ranked by similarity score.
- **Deployment**: A Flask-based API handles embedding and retrieval logic. The interface uses Bootstrap and vanilla JavaScript for lightweight client interaction. Tool outputs are designed to support experimental annotation and thematic discovery.

---

➡️ Try the tools via the [GLOS web interface](https://glos.kgeographer.org) or consult the [source code on GitHub](https://github.com/kgeographer/glos).