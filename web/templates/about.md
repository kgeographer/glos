### About GLOS: Geographic Lens on Stories

**GLOS** (Geographic Lens on Stories) is a digital humanities project that brings computational methods to the study of global folklore. Our aim is to facilitate new forms of inquiry into how cultural narratives—particularly folktales and creation myths—vary across geography and time, and how they may reflect shared human concerns or distinct cultural values.

GLOS output is currently in alpha release. The tools and methods are experimental, and we invite feedback and collaboration. Our initial audience includes folklorists, digital humanists, cultural geographers, and anyone interested in computational storytelling.

The GLOS project is proceeding in two major phases so far:

---

#### Phase I: Canonical Indexes as Computational Resources

The first phase focuses on digitizing and enriching two foundational reference works in folklore studies:

- The **Aarne-Thompson-Uther (ATU) Tale Type Index**, which classifies thousands of folk narratives into tale types based on recurring plot structures.
- The **Thompson Motif Index (TMI)**, which organizes tens of thousands of narrative motifs—smallest recognizable narrative elements—into a detailed taxonomy.

We have transformed these legacy resources into machine-readable formats, enabling new computational tools. The first tool released in this phase is the [**ATU-TMI Cross-Reference Tool**](/atu_tmi_v2), which supports exploration of tale types through their associated motifs, and vice versa. This tool is now live and available for testing and feedback from folklorists and researchers.

A second tool, [**Concept Matcher**](/explore), allows users to input any piece of text—such as a folktale, myth, or summary—and receive a ranked list of the most semantically similar motifs and/or tale types using sentence embeddings.

[Some technical details on Github](https://github.com/kgeographer/glos/blob/main/README_phase1.md)

---

#### Phase II: Analyzing Global Creation Myths

The second phase of GLOS turns to a different corpus: creation myths from diverse world cultures. Drawing initially on Barbara Sproul’s *Primal Myths* (1979), we are digitizing, cleaning, and enriching over 100 myths for structured analysis.

Our goals include:
- Extracting and normalizing core **entities**, **events**, and **themes** from each myth.
- Using **machine learning and language models** to identify cross-cultural patterns and divergences.
- Building an ontology of **mythic structures**, informed both by scholarly frameworks and empirical clustering of motifs and events.

Ultimately, we hope to create an open, extensible platform for cross-cultural myth analysis, and to contribute tools for scholars interested in cultural patterning, diffusion, and variation at scale.

[Some technical details on Github](https://github.com/kgeographer/glos/blob/main/README_myths.md)

---

The GLOS project is open source, with development hosted on [GitHub](https://github.com/kgeographer/glos). To learn more or to contribute, please reach out (karl[at]kgeorgapher[dot] org, or explore the available tools.

*All content © 2025 unless otherwise noted. GLOS is a joint effort of Karl Grossner and chatbot collaborators.*