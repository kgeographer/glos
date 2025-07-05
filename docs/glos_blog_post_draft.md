# GLOS: A Geographer’s Computational Journey into Story

_This post is co-authored with ChatGPT, as promised._

---

## I. Introduction

In a recent post, I described how large language models (LLMs) and chatbots like ChatGPT have begun playing a role in my work. This is the follow-up I promised—a deeper look into that work itself. It’s called **GLOS**, short for **Geographic Lens on Stories**. What began as an open-ended experiment in applying computational methods to cultural narrative has taken on shape, tools, and even a kind of mission.

As a retired geographer with a lifelong interest in folklore and myth, I approach this not as a trained folklorist but as an interloper—albeit a respectful one. GLOS isn’t a grant-funded lab project; it’s a post-career intellectual venture shaped by curiosity, technical skill, and the freedom to explore.

---

## II. What Is GLOS?

At its core, GLOS asks a set of simple but ambitious questions:

> Can computational methods help reveal cultural, geographic, and conceptual patterns in traditional stories?

To explore this, GLOS currently unfolds across **two interrelated phases**:

- **Phase A**: Digitizing and computationally modeling existing reference systems in folkloristics (ATU and TMI)
- **Phase B**: Building a structured, analyzable corpus of global **creation myths**

The two phases are not strictly sequential—they proceed in parallel, informing and shaping each other as they go.

---

## III. Phase A: Indexing the Indexes

The starting point was to bring structure and semantic accessibility to two foundational resources in folk narrative studies:

- **The Aarne–Thompson–Uther (ATU) Index**: classifying folktales by tale type
- **The Thompson Motif Index (TMI)**: a massive catalog of narrative elements, or motifs

These were digitized into a normalized relational database and enriched using machine learning techniques. Specifically, I generated **embeddings** for:

- **46,245 motifs**
- **2,232 tale types**

This opened the door to a set of early tools. The first was the **Concept Matcher**, which allows users to input a snippet of text and retrieve the nearest motifs or tale types in semantic space. While intriguing, it quickly became clear that:

- Motif descriptions are often too short to yield meaningful embeddings
- Precision and recall were mediocre—good enough for a demo, but not for serious inference

This led to a pivot. In response to feedback from academic folklorists, I developed a second tool:

- **The ATU–TMI Cross-Reference Tool**: lets users view tale types alongside the motifs they contain in a structured, explorable interface

This tool will soon be presented informally to folklorists for feedback and further refinement. Phase A, in that sense, is very much ongoing.

---

## IV. Phase B: Creation Myths and Conceptual Modeling

While Phase A engaged with reference systems, Phase B turns to narrative itself—specifically, the genre of **creation myths**.

Using Barbara Sproul’s _Primal Myths_ as a source, I built a curated corpus of myths from around the world. Each was scanned, OCR-processed, cleaned, and structured into JSON-LD files with key metadata. Then came the conceptual modeling.

Using LLMs, I extracted recurring elements from these myths to begin assembling a **draft structured vocabulary**. While not a formal ontology, this vocabulary attempts to identify:

- Key **events** (often sequenced)
- **Entities** and their roles (creator, transformer, rebel, etc.)
- **Cosmic structure** (sky, sea, underworld)
- **Thematic dualities** (order/chaos, male/female, light/dark)

It’s a speculative schema, and clearly only applicable—at this stage—to **creation myths**. But it lays groundwork for a kind of computational comparative mythology.

Much depends on future expert validation: the “smell test” from real comparativists will determine whether these structures resonate or miss the mark.

---

## V. Looking Ahead: Retrieval, Visualization, and Place

Two major directions are now shaping GLOS’s path forward.

### Retrieval-Augmented Generation (RAG)

RAG allows language models to incorporate external knowledge in real-time, and it’s a promising way to improve LLM reasoning across the GLOS corpus. Instead of relying purely on embedding similarity, RAG workflows can support question answering, summarization, or inference grounded in structured data.

### Geography and Visualization

The **geographic** component of GLOS—its namesake lens—is both central and complex. Cultural metadata for tales and myths varies widely: sometimes it's a country, sometimes a language family, a religion, or a historical polity.

While this diversity resists clean mapping, it doesn’t preclude it. There **will be** geographic maps—but they will be embedded in a **dashboard of visualizations**, including:

- Thematic clustering
- Narrative structure maps
- Motif density distributions
- Cross-cultural timelines

Together, these will offer multiple ways to “see” how stories are structured and shared across cultures and regions.

---

## VI. Why Do This?

Because it’s deeply interesting.

Because the stories people tell—about the beginning of the world, the meaning of death, the source of knowledge—are both universal and profoundly local.

Because stories may themselves be **dimensions of place**.

And because the tools now available to us—LLMs, embeddings, RAG, semantic visualization—create a new frontier for exploring these stories at scale.

GLOS is also becoming a **meta-project**, one that evaluates the performance of AI models in the humanities. Can LLMs meaningfully support cultural analysis? Where do they falter? This evaluative angle may become one of the project’s most significant contributions.

---

## VII. Co-Authoring with ChatGPT

This blog post—like much of GLOS—is co-authored with a chatbot. That’s not a gimmick, and it’s not outsourcing. It’s a method.

ChatGPT acts as an idea bouncer, a paragraph generator, a technical assistant, and sometimes a devil’s advocate. It doesn’t know what myths _mean_, but it can help me sort them, structure them, and propose ways to think about them.

This post was written through dialogue—my prompts, my revisions, my judgment—but its speed and shape were made possible by AI.

---

## VIII. What’s Next?

- Expand the myth corpus, especially with better cultural metadata
- Refine the conceptual schema with feedback from scholars
- Build out RAG-based tools for interacting with the data
- Develop the visualization dashboard, including geographic maps
- Continue probing the limits and affordances of AI in folklore research
- Invite collaborators from digital humanities, folklore, and geography

---

## IX. Closing

GLOS remains a speculative project, still early, still evolving. But it has already shown that traditional stories, approached computationally, yield surprising structures—and sometimes beautiful patterns.

For more, visit:

- 🌐 [gloss.kgeographer.org](https://gloss.kgeographer.org)  
- 🧾 [GLOS on GitHub](https://github.com/kgeographer/glos)

What comes next will depend not just on the machines, but on the humans—folklorists, comparativists, geographers—who read, question, and build alongside them.

