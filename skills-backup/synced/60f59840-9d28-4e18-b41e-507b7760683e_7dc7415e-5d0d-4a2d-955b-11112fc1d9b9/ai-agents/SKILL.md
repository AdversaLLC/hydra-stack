---
name: ai-agents
description: AI agent development patterns and advisory for claude.ai. Triggers on "AI agent", "LangChain", "LangGraph", "Swarm", "PydanticAI", "RAG", "tool calling", "function calling", "Tree of Thoughts", "ToT", "MCTS", "PSO", "DeepSearcher", "build an agent", "agent framework", "vector DB", "embeddings". This skill provides design guidance, code patterns, and runnable demo snippets in the bash sandbox — it does NOT spin up a production agent inside claude.ai. The Claude Code original assumed local Ollama, Milvus, sentence-transformers, and persistent disk for vector stores; this version uses what's installable per-session in /home/claude (NumPy, scikit-learn, optionally chromadb in-memory, optionally sentence-transformers if the wait is acceptable).
---

# AI Agents — claude.ai Pattern Library + Demos

The job: when a user wants to design, debug, or learn agent patterns, give them solid guidance plus runnable demos. Not pretend to BE the production agent — give them the patterns and code so they can build it themselves on their own infrastructure.

The Claude Code v2 had Tree of Thoughts via `tot` library, DeepSearcher with Milvus, SwarmAgentic PSO, Agent-R MCTS reflection, ROSE diversity, page-by-page PDF reading. Most patterns transfer; the infrastructure (Milvus, persistent disk, Ollama backends) doesn't. Demos here use in-memory equivalents.

---

## Patterns covered

### 1. Function calling / tool use

The core pattern: model decides which tool to call from a schema, model calls it, model uses result.

For Anthropic models specifically, read `product-self-knowledge` SKILL.md for the current Claude API tool-use format. Don't guess parameter names from training data — they may have changed.

For OpenAI / other providers: see their docs via `web_fetch`. For LangChain wrappers: `web_fetch` on `python.langchain.com/docs/`.

Common pitfall: schemas that are too permissive. Make required fields actually required. Use `enum` for fixed choices. Validate the model's output before calling the tool.

### 2. Retrieval-Augmented Generation (RAG)

Standard recipe:
1. Chunk source documents (overlap 10–33% to prevent boundary loss)
2. Embed chunks (sentence-transformers, OpenAI embeddings, Cohere, Voyage)
3. Store in vector DB (Pinecone / Milvus / Weaviate / Qdrant for prod; Chroma / FAISS / in-memory for dev)
4. At query time: embed query → retrieve top-K → pass to LLM as context

Demo in bash sandbox:

```python
# pip install --break-system-packages sentence-transformers chromadb
from sentence_transformers import SentenceTransformer
import chromadb

client = chromadb.Client()  # in-memory
collection = client.create_collection("docs")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

chunks = ["Paris is the capital of France.", "Tokyo is the capital of Japan.", ...]
embeddings = embedder.encode(chunks).tolist()
collection.add(documents=chunks, embeddings=embeddings, ids=[f"d{i}" for i in range(len(chunks))])

q = "What's the capital of France?"
q_emb = embedder.encode([q]).tolist()
results = collection.query(query_embeddings=q_emb, n_results=2)
print(results['documents'])
```

Caveat: `sentence-transformers` install + first-use download takes 30–90 seconds in the sandbox. For demos to a user who just wants to *see the pattern*, often a synthetic embedding (`numpy.random.randn(384)` per chunk) is fine and runs instantly. State which you're doing.

### 3. Tree of Thoughts (ToT)

Original ToT: generate N candidate thoughts per step, score each, keep top-K, expand. Useful for problems where exploration of branches actually helps (math, planning, code architecture decisions).

In claude.ai (one Claude, no subagents), a true ToT search isn't running — but the *technique* of writing 3–5 candidate approaches before committing is valuable on its own. Demo by listing branches, scoring each on a simple rubric, picking the best, and explaining why.

For an actual Python ToT demo: `pip install --break-system-packages tree-of-thoughts-llm` works, but the library calls real LLM APIs which need API keys the sandbox doesn't have. Show the structure; tell the user to wire their own API key when they run it.

### 4. MCTS-style self-reflection

Pattern from Agent-R: an agent tries something, fails, finds the *first* error step (not the last), backtracks to before it, tries differently. Useful for code-fix loops.

Implementation in claude.ai is just: write code → run it → on failure, locate the first failing step (not the symptom), fix that, retry. Sequential, one Claude. The MCTS search-tree is conceptual.

### 5. Multi-agent (Swarm, PSO, etc.)

In claude.ai, "multi-agent" is metaphorical. There are no subagents. What works:
- Sequential perspective shifts (do the redteam-style 5–8 perspectives sequentially)
- Persona framing within phases (chatdev-vm pattern: CEO, CTO, Programmer, Reviewer, Tester)
- Acknowledging when a problem genuinely needs production multi-agent (e.g., parallel research across 100 papers) and pointing the user to a real multi-agent framework (LangGraph, CrewAI, AutoGen) for that use case

Don't claim parallelism that isn't happening. The user often actually wants to build the multi-agent system on their own infra; help them design it, don't fake-execute it.

### 6. LangChain / LangGraph

LangChain is a library; we don't run it inside claude.ai for the user. We help design the chain or graph, write the code, and explain the patterns.

For LangGraph specifically (the state-machine pattern): the design step matters most. Sketch the state object, the nodes, the edges, the interrupts. Write the `StateGraph` definition. The user runs it.

### 7. PydanticAI / Instructor / structured output

Pattern: define a Pydantic schema, the LLM is constrained to output JSON matching it, you parse the result.

Demo runs in sandbox if Pydantic + an LLM client are installable (Pydantic is fine; the LLM client needs an API key the user provides).

### 8. Local AI stack (Ollama, llama.cpp, vLLM)

The user runs these on their machine; we help design and explain. Bash sandbox can install Ollama in principle but model weights are multi-GB downloads that won't fit reliably in a per-session sandbox.

What works: write the `ollama pull` and `ollama run` commands, write the API client code, explain the trade-offs of model size vs latency vs quality. Don't claim to "spin up" Ollama in claude.ai.

---

## What got stripped from v2

- **Tree-of-thoughts-llm library actually executing** — needs API keys; show the structure, user runs it
- **DeepSearcher with Milvus** — Milvus isn't a per-session install; suggest user runs DeepSearcher locally or replaces Milvus with an in-memory backend for prototyping
- **SwarmAgentic PSO multi-agent execution** — needs subagents or a real LLM swarm runtime; design help yes, fake execution no
- **Agent-R MCTS execution** — same; pattern is implementable, search-tree-with-real-rollouts requires multiple actors
- **ROSE diversity via sentence-transformers** — possible in sandbox but slow first-use; for demos, often a simpler diversity check (token Jaccard) is fine
- **Page-by-page PDF reading** — claude.ai has the `pdf-reading` skill which does exactly this; route there instead of reimplementing
- **Overlap chunking** — the *insight* (1/3 overlap reduces boundary loss) is in the RAG section above; the implementation is a few lines, no library

---

## Anti-patterns

- **Pretending to be the agent**: claude.ai is one Claude in a chat. We help design agents; we are not the production deployment.
- **Library-cargo-culting**: don't recommend LangChain because "it's the AI agent thing". For simple cases, a few hundred lines of plain Python is clearer than a chain.
- **Vector DB premature optimization**: for under ~10K chunks, in-memory cosine similarity is fast enough. Don't suggest Milvus for a demo.
- **Embeddings for everything**: sometimes the right answer is keyword search, BM25, or just a good prompt. Embeddings have failure modes (out-of-domain queries, abstract concepts, multilingual).
- **Agent framework choice paralysis**: pick one framework that fits, build a small thing end-to-end, then consider scaling. Don't compare 8 frameworks before writing any code.

---

## Tool reference

| Need | Tool |
|---|---|
| Pattern advisory / design | claude.ai conversation directly |
| Live code demo | `bash_tool` in `/home/claude/` |
| Read framework docs | `web_fetch` on the framework's docs |
| Anthropic API specifics | read `/mnt/skills/public/product-self-knowledge/SKILL.md` |
| RAG demo | `pip install` chromadb / sentence-transformers in sandbox |
| Diagram of agent flow | `visualize:show_widget` (diagram module) |
| Save full demo as runnable file | `create_file` to `/mnt/user-data/outputs/`, `present_files` |
