### GLOS Phase One: Motif and Tale Type Embeddings

**Updated: 9 June 2025**

Phase 1 of the Geographic Lens on Stories (GLOS) project has focused on computational representations of canonical folkloristic reference works: *The Types of International Folktales* (ATU) and *The Motif-Index of Folk-Literature* (TMI). This phase produced two working prototype tools for use by researchers and students of folklore:

#### 1. ATU/TMI Cross-Reference Tool
This browser-based tool allows users to explore relationships between ATU tale types and their associated Thompson motifs. Users may search or browse both tale types and motifs by keyword or identifier, and follow the cross-referencing relationships recorded in the ATU.  Features include:

- Bidirectional links between tale types and motifs
- Cultural reference terms displayed for both tale types and motifs
- Tooltip-enhanced indicators for motifs referenced in multiple tale types
- Interactive modals allowing contextual navigation

This tool reveals structural and conceptual linkages within the ATU-TMI framework and facilitates exploratory comparative analysis.

#### 2. Concept Matcher Tool
This prototype tool allows users to input any piece of text—such as a folktale, myth, or summary—and receive a ranked list of the most semantically similar motifs and/or tale types using sentence embeddings. The similarity is computed via vector search over precomputed LLM embeddings of motif and tale type descriptions.

This tool is designed to assist in exploratory indexing, interpretation, or thematic analysis of narrative material not yet formally cataloged.

➡️ Try the tools via the web interface or see source code and usage notes in this repository.